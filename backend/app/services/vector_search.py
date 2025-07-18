"""Vector search service using Qdrant."""

import os
from typing import List, Dict, Any, Optional
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, 
    VectorParams, 
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest
)
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Handle vector search operations using Qdrant."""
    
    def __init__(self):
        """Initialize Qdrant client and OpenAI."""
        # Initialize Qdrant client
        qdrant_url = settings.QDRANT_URL
        qdrant_api_key = settings.QDRANT_API_KEY
        
        if qdrant_url and "localhost" not in qdrant_url and "127.0.0.1" not in qdrant_url:
            # Cloud Qdrant
            self.client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
                timeout=30
            )
        else:
            # Local Qdrant
            self.client = QdrantClient(
                host="localhost",
                port=6333,
                timeout=30
            )
        
        # Collection name
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        
        # Initialize async OpenAI client
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Ensure collection exists
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure the collection exists in Qdrant."""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)
            
            if not exists:
                # Create collection with OpenAI embedding dimensions
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI ada-002 embeddings
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Qdrant collection exists: {self.collection_name}")
                
        except Exception as e:
            logger.warning(f"Could not ensure Qdrant collection: {e}")
            # Continue anyway - will fail on actual operations if Qdrant is not available
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI."""
        if not self.openai_client:
            logger.warning("OpenAI API key not configured - returning empty embedding")
            return [0.0] * 1536
        
        try:
            response = await self.openai_client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            # Return empty embedding on error to allow the app to continue
            return [0.0] * 1536
    
    async def index_resume(self, resume_id: str, text: str, metadata: Dict[str, Any]):
        """Index a resume in Qdrant."""
        try:
            # Get embedding
            embedding = await self.get_embedding(text)
            
            # Create point
            point = PointStruct(
                id=resume_id,
                vector=embedding,
                payload={
                    "resume_id": resume_id,
                    **metadata
                }
            )
            
            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Indexed resume {resume_id} in Qdrant")
            return embedding
            
        except Exception as e:
            logger.error(f"Error indexing resume {resume_id}: {e}")
            # Return None but don't fail - allows app to work without vector search
            return None
    
    async def search_similar(
        self, 
        query: str, 
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar resumes using vector similarity."""
        try:
            # Get query embedding
            query_embedding = await self.get_embedding(query)
            
            # Build filter if provided
            qdrant_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    qdrant_filter = Filter(must=conditions)
            
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=qdrant_filter,
                limit=limit,
                with_payload=True
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "resume_id": result.payload.get("resume_id"),
                    "score": result.score,
                    "metadata": result.payload
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching similar resumes: {e}")
            # Return empty list but don't fail
            return []
    
    async def delete_resume(self, resume_id: str):
        """Delete a resume from Qdrant."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[resume_id]
            )
            logger.info(f"Deleted resume {resume_id} from Qdrant")
        except Exception as e:
            logger.error(f"Error deleting resume {resume_id}: {e}")
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            # Try to get basic info without full collection details
            collections = self.client.get_collections()
            collection_exists = any(c.name == self.collection_name for c in collections.collections)
            
            if collection_exists:
                # Try to count points
                try:
                    count_result = self.client.count(
                        collection_name=self.collection_name,
                        exact=False  # Approximate count is faster
                    )
                    points_count = count_result.count
                except:
                    points_count = "unknown"
                
                return {
                    "status": "connected",
                    "points_count": points_count,
                    "collection": self.collection_name
                }
            else:
                return {
                    "status": "connected",
                    "points_count": 0,
                    "collection": f"{self.collection_name} (not created yet)"
                }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_all_ids(self) -> set:
        """Get all resume IDs from the vector search index."""
        try:
            if not await self.ensure_collection_exists():
                return set()
            
            # Scroll through all points to get IDs
            all_ids = set()
            offset = None
            limit = 100
            
            while True:
                result = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=limit,
                    offset=offset,
                    with_payload=False,
                    with_vectors=False
                )
                
                points, next_offset = result
                
                for point in points:
                    all_ids.add(str(point.id))
                
                if next_offset is None:
                    break
                    
                offset = next_offset
            
            return all_ids
        except Exception as e:
            logger.error(f"Error getting all IDs from vector search: {e}")
            return set()


# Singleton instance
vector_search = VectorSearchService()