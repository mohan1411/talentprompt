"""Bulk import service for LinkedIn profiles with compliance and rate limiting."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID
import random
import pandas as pd
import zipfile
import json
import io

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.user import User
from app.models.resume import Resume
from app.models.import_queue import ImportQueueItem, ImportHistory
from app.services.linkedin_parser import LinkedInParser
from app.services.vector_search import vector_search
from app.services.reindex_service import ReindexService
from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for LinkedIn imports to ensure compliance."""
    
    def __init__(self):
        self.limits = {
            'profiles_per_hour': 100,
            'profiles_per_day': 500,
            'profiles_per_minute': 10,
            'min_delay_seconds': 3,
            'max_delay_seconds': 6
        }
    
    async def check_rate_limit(self, db: AsyncSession, user_id: UUID) -> bool:
        """Check if user can import more profiles."""
        now = datetime.utcnow()
        
        # Check minute limit
        minute_ago = now - timedelta(minutes=1)
        minute_count = await self._get_import_count(db, user_id, minute_ago)
        if minute_count >= self.limits['profiles_per_minute']:
            logger.warning(f"User {user_id} hit minute rate limit")
            return False
        
        # Check hourly limit
        hour_ago = now - timedelta(hours=1)
        hourly_count = await self._get_import_count(db, user_id, hour_ago)
        if hourly_count >= self.limits['profiles_per_hour']:
            logger.warning(f"User {user_id} hit hourly rate limit")
            return False
        
        # Check daily limit
        day_ago = now - timedelta(days=1)
        daily_count = await self._get_import_count(db, user_id, day_ago)
        if daily_count >= self.limits['profiles_per_day']:
            logger.warning(f"User {user_id} hit daily rate limit")
            return False
        
        return True
    
    async def _get_import_count(self, db: AsyncSession, user_id: UUID, since: datetime) -> int:
        """Get import count since a specific time."""
        stmt = select(func.count(ImportHistory.id)).where(
            and_(
                ImportHistory.user_id == user_id,
                ImportHistory.imported_at >= since,
                ImportHistory.status == 'completed'
            )
        )
        result = await db.execute(stmt)
        return result.scalar() or 0
    
    def get_human_delay(self) -> float:
        """Get a randomized human-like delay in seconds."""
        return self.limits['min_delay_seconds'] + random.random() * (
            self.limits['max_delay_seconds'] - self.limits['min_delay_seconds']
        )


class LinkedInExportProcessor:
    """Process LinkedIn export files."""
    
    def __init__(self):
        self.parser = LinkedInParser()
    
    async def process_export_file(self, file_content: bytes, filename: str) -> List[Dict[str, Any]]:
        """Process a LinkedIn export file and return profile data."""
        profiles = []
        
        if filename.endswith('.zip'):
            profiles = await self._process_zip_archive(file_content)
        elif filename.endswith('.csv'):
            profiles = await self._process_csv_export(file_content)
        elif filename.endswith(('.xlsx', '.xls')):
            profiles = await self._process_excel_export(file_content)
        else:
            raise ValueError(f"Unsupported file format: {filename}")
        
        return profiles
    
    async def _process_zip_archive(self, zip_content: bytes) -> List[Dict[str, Any]]:
        """Process LinkedIn personal data archive (ZIP)."""
        profiles = []
        
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
            # Look for profile data in the archive
            for file_info in zip_file.filelist:
                if 'Profile.csv' in file_info.filename:
                    csv_content = zip_file.read(file_info.filename)
                    df = pd.read_csv(io.BytesIO(csv_content))
                    
                    # Extract profile information
                    profile = {
                        'first_name': df.get('First Name', [''])[0],
                        'last_name': df.get('Last Name', [''])[0],
                        'headline': df.get('Headline', [''])[0],
                        'summary': df.get('Summary', [''])[0],
                        'linkedin_url': df.get('Profile URL', [''])[0],
                    }
                    profiles.append(profile)
                
                elif 'Positions.csv' in file_info.filename:
                    # Extract experience data
                    csv_content = zip_file.read(file_info.filename)
                    positions_df = pd.read_csv(io.BytesIO(csv_content))
                    # Process positions...
                
                elif 'Skills.csv' in file_info.filename:
                    # Extract skills data
                    csv_content = zip_file.read(file_info.filename)
                    skills_df = pd.read_csv(io.BytesIO(csv_content))
                    # Process skills...
        
        return profiles
    
    async def _process_csv_export(self, csv_content: bytes) -> List[Dict[str, Any]]:
        """Process LinkedIn Recruiter CSV export."""
        df = pd.read_csv(io.BytesIO(csv_content))
        profiles = []
        
        # Map common LinkedIn Recruiter export columns
        column_mapping = {
            'First Name': 'first_name',
            'Last Name': 'last_name',
            'Current Company': 'current_company',
            'Current Title': 'current_title',
            'Location': 'location',
            'LinkedIn URL': 'linkedin_url',
            'Years in Current Position': 'years_in_position',
            'Total Years of Experience': 'years_experience',
            'Skills': 'skills',
            'Email': 'email',
            'Phone': 'phone'
        }
        
        for _, row in df.iterrows():
            profile = {}
            for csv_col, profile_key in column_mapping.items():
                if csv_col in df.columns:
                    value = row.get(csv_col)
                    if pd.notna(value):
                        if profile_key == 'skills' and isinstance(value, str):
                            # Parse skills if they're comma-separated
                            profile[profile_key] = [s.strip() for s in value.split(',')]
                        else:
                            profile[profile_key] = value
            
            # Generate headline from title and company
            if 'current_title' in profile and 'current_company' in profile:
                profile['headline'] = f"{profile['current_title']} at {profile['current_company']}"
            
            profiles.append(profile)
        
        return profiles
    
    async def _process_excel_export(self, excel_content: bytes) -> List[Dict[str, Any]]:
        """Process LinkedIn Recruiter Excel export."""
        df = pd.read_excel(io.BytesIO(excel_content))
        # Use same logic as CSV processing
        return await self._process_csv_export(excel_content)


class BulkImportService:
    """Service for managing bulk imports with compliance."""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.export_processor = LinkedInExportProcessor()
        self.reindex_service = ReindexService()
        self.processing_tasks = {}  # Track active processing tasks per user
    
    async def add_to_queue(
        self,
        db: AsyncSession,
        user_id: UUID,
        profiles: List[Dict[str, Any]],
        source: str = 'manual'
    ) -> Dict[str, Any]:
        """Add profiles to import queue."""
        added = 0
        duplicates = 0
        errors = 0
        
        for profile_data in profiles:
            try:
                # Check if profile already exists
                linkedin_url = profile_data.get('linkedin_url')
                if linkedin_url:
                    existing = await db.execute(
                        select(Resume).where(
                            Resume.linkedin_url == linkedin_url,
                            Resume.status != 'deleted'  # Don't count soft-deleted as duplicates
                        )
                    )
                    if existing.scalar_one_or_none():
                        duplicates += 1
                        continue
                
                # Create queue item
                queue_item = ImportQueueItem(
                    user_id=user_id,
                    profile_data=profile_data,
                    source=source,
                    status='pending'
                )
                db.add(queue_item)
                added += 1
                
            except Exception as e:
                logger.error(f"Error adding profile to queue: {e}")
                errors += 1
        
        await db.commit()
        
        return {
            'added': added,
            'duplicates': duplicates,
            'errors': errors,
            'total': len(profiles)
        }
    
    async def process_queue(
        self,
        db: AsyncSession,
        user_id: UUID,
        max_items: Optional[int] = None
    ) -> Dict[str, Any]:
        """Process import queue for a user with rate limiting."""
        
        # Check if already processing for this user
        if user_id in self.processing_tasks and not self.processing_tasks[user_id].done():
            return {
                'status': 'already_processing',
                'message': 'Queue processing already in progress'
            }
        
        # Start processing in background
        task = asyncio.create_task(self._process_queue_async(db, user_id, max_items))
        self.processing_tasks[user_id] = task
        
        return {
            'status': 'processing_started',
            'message': 'Queue processing started in background'
        }
    
    async def _process_queue_async(
        self,
        db: AsyncSession,
        user_id: UUID,
        max_items: Optional[int] = None
    ):
        """Async queue processing with compliance delays."""
        processed = 0
        
        try:
            while True:
                # Check rate limit
                if not await self.rate_limiter.check_rate_limit(db, user_id):
                    logger.info(f"Rate limit reached for user {user_id}")
                    break
                
                # Get next pending item
                stmt = select(ImportQueueItem).where(
                    and_(
                        ImportQueueItem.user_id == user_id,
                        ImportQueueItem.status == 'pending'
                    )
                ).order_by(ImportQueueItem.created_at).limit(1)
                
                result = await db.execute(stmt)
                queue_item = result.scalar_one_or_none()
                
                if not queue_item:
                    logger.info(f"No more items in queue for user {user_id}")
                    break
                
                # Process the item
                try:
                    queue_item.status = 'processing'
                    queue_item.started_at = datetime.utcnow()
                    await db.commit()
                    
                    # Import the profile
                    resume = await self._import_profile(db, user_id, queue_item.profile_data)
                    
                    # Update queue item
                    queue_item.status = 'completed'
                    queue_item.completed_at = datetime.utcnow()
                    queue_item.resume_id = resume.id
                    
                    # Create import history record
                    history = ImportHistory(
                        user_id=user_id,
                        resume_id=resume.id,
                        source=queue_item.source,
                        status='completed',
                        imported_at=datetime.utcnow()
                    )
                    db.add(history)
                    
                    await db.commit()
                    processed += 1
                    
                    # Re-index for search
                    await self.reindex_service.reindex_resume(db, resume)
                    
                except Exception as e:
                    logger.error(f"Error processing queue item {queue_item.id}: {e}")
                    queue_item.status = 'failed'
                    queue_item.error_message = str(e)
                    queue_item.attempts += 1
                    await db.commit()
                
                # Human-like delay
                delay = self.rate_limiter.get_human_delay()
                logger.info(f"Waiting {delay:.1f} seconds before next import")
                await asyncio.sleep(delay)
                
                # Check if we've reached max items
                if max_items and processed >= max_items:
                    break
                
        except Exception as e:
            logger.error(f"Error in queue processing for user {user_id}: {e}")
        
        finally:
            # Remove from active tasks
            if user_id in self.processing_tasks:
                del self.processing_tasks[user_id]
        
        logger.info(f"Queue processing completed for user {user_id}. Processed: {processed}")
    
    async def _import_profile(
        self,
        db: AsyncSession,
        user_id: UUID,
        profile_data: Dict[str, Any]
    ) -> Resume:
        """Import a single profile."""
        parser = LinkedInParser()
        parsed_data = await parser.parse_linkedin_data(profile_data)
        
        # Create resume
        resume = Resume(
            user_id=user_id,
            first_name=parsed_data.get('first_name', ''),
            last_name=parsed_data.get('last_name', ''),
            email=profile_data.get('email', ''),
            phone=profile_data.get('phone', ''),
            location=profile_data.get('location', ''),
            current_title=profile_data.get('current_title', ''),
            summary=profile_data.get('summary', ''),
            years_experience=profile_data.get('years_experience', 0),
            skills=profile_data.get('skills', []),
            linkedin_url=profile_data.get('linkedin_url', ''),
            linkedin_data=profile_data,
            status='active',
            parse_status='completed',
            parsed_at=datetime.utcnow()
        )
        
        db.add(resume)
        await db.flush()
        
        return resume
    
    async def get_queue_status(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get queue status for a user."""
        # Count by status
        stmt = select(
            ImportQueueItem.status,
            func.count(ImportQueueItem.id)
        ).where(
            ImportQueueItem.user_id == user_id
        ).group_by(ImportQueueItem.status)
        
        result = await db.execute(stmt)
        status_counts = dict(result.all())
        
        # Get recent items
        recent_stmt = select(ImportQueueItem).where(
            ImportQueueItem.user_id == user_id
        ).order_by(ImportQueueItem.created_at.desc()).limit(10)
        
        recent_result = await db.execute(recent_stmt)
        recent_items = recent_result.scalars().all()
        
        # Check if processing
        is_processing = user_id in self.processing_tasks and not self.processing_tasks[user_id].done()
        
        # Get rate limit status
        rate_limit_ok = await self.rate_limiter.check_rate_limit(db, user_id)
        
        # Get import counts for rate limits
        now = datetime.utcnow()
        hourly_count = await self.rate_limiter._get_import_count(
            db, user_id, now - timedelta(hours=1)
        )
        daily_count = await self.rate_limiter._get_import_count(
            db, user_id, now - timedelta(days=1)
        )
        
        return {
            'status_counts': {
                'pending': status_counts.get('pending', 0),
                'processing': status_counts.get('processing', 0),
                'completed': status_counts.get('completed', 0),
                'failed': status_counts.get('failed', 0)
            },
            'total': sum(status_counts.values()),
            'is_processing': is_processing,
            'rate_limit_ok': rate_limit_ok,
            'rate_limits': {
                'hourly': {
                    'current': hourly_count,
                    'limit': self.rate_limiter.limits['profiles_per_hour']
                },
                'daily': {
                    'current': daily_count,
                    'limit': self.rate_limiter.limits['profiles_per_day']
                }
            },
            'recent_items': [
                {
                    'id': str(item.id),
                    'status': item.status,
                    'created_at': item.created_at.isoformat(),
                    'profile_name': f"{item.profile_data.get('first_name', '')} {item.profile_data.get('last_name', '')}".strip() or 'Unknown'
                }
                for item in recent_items
            ]
        }
    
    async def clear_queue(
        self,
        db: AsyncSession,
        user_id: UUID,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Clear queue items for a user."""
        stmt = select(ImportQueueItem).where(
            ImportQueueItem.user_id == user_id
        )
        
        if status:
            stmt = stmt.where(ImportQueueItem.status == status)
        
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        deleted_count = len(items)
        for item in items:
            await db.delete(item)
        
        await db.commit()
        
        return {
            'deleted': deleted_count,
            'status': 'success'
        }
    
    async def get_import_stats(
        self,
        db: AsyncSession,
        user_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get import statistics for a user."""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Get daily import counts
        stmt = text("""
            SELECT 
                DATE(imported_at) as date,
                COUNT(*) as count,
                source
            FROM import_history
            WHERE user_id = :user_id
            AND imported_at >= :since
            AND status = 'completed'
            GROUP BY DATE(imported_at), source
            ORDER BY date DESC
        """)
        
        result = await db.execute(stmt, {'user_id': user_id, 'since': since})
        daily_stats = result.all()
        
        # Group by date
        stats_by_date = {}
        for date, count, source in daily_stats:
            if date not in stats_by_date:
                stats_by_date[date] = {'total': 0, 'sources': {}}
            stats_by_date[date]['total'] += count
            stats_by_date[date]['sources'][source] = count
        
        # Get total counts by source
        source_stmt = select(
            ImportHistory.source,
            func.count(ImportHistory.id)
        ).where(
            and_(
                ImportHistory.user_id == user_id,
                ImportHistory.status == 'completed'
            )
        ).group_by(ImportHistory.source)
        
        source_result = await db.execute(source_stmt)
        source_totals = dict(source_result.all())
        
        return {
            'daily_stats': stats_by_date,
            'source_totals': source_totals,
            'total_imports': sum(source_totals.values())
        }


# Create singleton instance
bulk_import_service = BulkImportService()