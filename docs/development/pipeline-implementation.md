# Pipeline & Workflow Management Implementation

## Overview

This document describes the implementation of the Candidate Pipeline & Workflow Management system for Promtitude. This feature transforms Promtitude from a search tool into a complete recruiting operations platform.

## What Was Implemented

### 1. Database Schema (`backend/create_pipeline_tables.sql`)

Created comprehensive tables for pipeline management:

- **pipelines** - Pipeline templates with customizable stages
- **candidate_pipeline_states** - Tracks candidates' current position in pipelines
- **pipeline_activities** - Audit log of all actions
- **candidate_notes** - Collaborative notes and comments
- **candidate_evaluations** - Interview feedback and ratings
- **candidate_communications** - Email/communication tracking
- **pipeline_automations** - Automation rules configuration
- **pipeline_team_members** - Team permissions per pipeline

### 2. SQLAlchemy Models (`backend/app/models/pipeline.py`)

Implemented all models with:
- Proper relationships between entities
- Enum types for stage types and activity types
- Timestamps and audit fields
- Constraints for data integrity

### 3. Pipeline Service (`backend/app/services/pipeline.py`)

Core business logic including:
- Pipeline CRUD operations
- Candidate workflow management (add, move, assign)
- Collaboration features (notes, evaluations)
- Activity tracking and timeline
- Notification triggers
- Analytics data collection

### 4. API Endpoints (`backend/app/api/v1/endpoints/pipelines.py`)

Complete REST API with endpoints for:

#### Pipeline Management
- `POST /api/v1/workflow/` - Create pipeline
- `GET /api/v1/workflow/` - List pipelines
- `GET /api/v1/workflow/default` - Get default pipeline
- `GET /api/v1/workflow/{id}` - Get specific pipeline
- `PUT /api/v1/workflow/{id}` - Update pipeline
- `DELETE /api/v1/workflow/{id}` - Delete pipeline

#### Candidate Workflow
- `POST /api/v1/workflow/candidates/add` - Add candidate to pipeline
- `PUT /api/v1/workflow/candidates/{id}/move` - Move to different stage
- `PUT /api/v1/workflow/candidates/{id}/assign` - Assign to team member
- `GET /api/v1/workflow/candidates/{pipeline_id}` - Get candidates in pipeline

#### Collaboration
- `POST /api/v1/workflow/candidates/{id}/notes` - Add note
- `GET /api/v1/workflow/candidates/{id}/notes` - Get notes
- `POST /api/v1/workflow/candidates/{id}/evaluations` - Add evaluation
- `GET /api/v1/workflow/candidates/{id}/timeline` - Get activity timeline

#### Analytics
- `GET /api/v1/workflow/{id}/analytics` - Pipeline analytics

## Key Features

### 1. Flexible Pipeline Configuration
- Customizable stages with colors and types
- Default pipeline templates
- Team-specific or global pipelines

### 2. Comprehensive Tracking
- Time in each stage
- Complete activity history
- User assignments with timestamps
- Rejection/withdrawal reasons

### 3. Collaboration Tools
- Notes with @mentions
- Private vs public notes
- Interview evaluations with ratings
- Email thread tracking

### 4. Smart Features
- Stage-based automations (prepared for future implementation)
- Analytics on conversion rates and bottlenecks
- Bulk operations support

## How to Use

### 1. Apply Database Migrations

```bash
cd backend
# Connect to your database and run:
psql -U postgres -d promtitude -f create_pipeline_tables.sql
```

### 2. Start the Backend

```bash
cd backend
uvicorn app.main:app --reload
```

### 3. Test the API

Visit http://localhost:8000/docs and look for the "workflow" tag to see all endpoints.

### 4. Create Your First Pipeline

```bash
curl -X POST "http://localhost:8000/api/v1/workflow/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Engineering Hiring",
    "description": "Standard process for engineering roles",
    "stages": [
      {"id": "sourced", "name": "Sourced", "order": 1, "color": "#94a3b8"},
      {"id": "screening", "name": "Screening", "order": 2, "color": "#60a5fa"},
      {"id": "technical", "name": "Technical Interview", "order": 3, "color": "#a78bfa"},
      {"id": "onsite", "name": "Onsite", "order": 4, "color": "#c084fc"},
      {"id": "offer", "name": "Offer", "order": 5, "color": "#34d399"}
    ],
    "is_default": true
  }'
```

### 5. Add a Candidate to Pipeline

```bash
curl -X POST "http://localhost:8000/api/v1/workflow/candidates/add" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": "RESUME_UUID",
    "pipeline_id": "PIPELINE_UUID"
  }'
```

## Next Steps

### Frontend Implementation (Pending)

1. **Kanban Board View**
   - Drag-and-drop interface
   - Stage columns with candidate cards
   - Quick actions per stage

2. **Candidate Detail View**
   - Timeline of all activities
   - Notes and evaluation tabs
   - Stage progression history

3. **Pipeline Configuration UI**
   - Visual stage builder
   - Automation rules setup
   - Team permissions management

### Future Enhancements

1. **Email Integration**
   - Sync with Gmail/Outlook
   - Track communication threads
   - Auto-capture replies

2. **Calendar Integration**
   - Schedule interviews from pipeline
   - Sync with Google Calendar
   - Automated reminders

3. **Advanced Automations**
   - Auto-progress based on evaluations
   - Scheduled follow-ups
   - Bulk stage transitions

4. **Mobile App**
   - Review candidates on the go
   - Quick evaluation forms
   - Push notifications

## Technical Notes

- The implementation uses PostgreSQL-specific features (UUID, JSONB)
- All timestamps are in UTC
- Soft deletes are used (is_active flag)
- The system supports multiple active pipelines per candidate
- Rate limiting should be added to prevent abuse
- WebSocket support could be added for real-time updates

## Security Considerations

- All endpoints require authentication
- User can only see candidates they have access to
- Team permissions are enforced at the pipeline level
- Private notes are only visible to the author
- Audit trail is maintained for compliance