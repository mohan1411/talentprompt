# LinkedIn Integration Documentation

## Overview

The Promtitude LinkedIn integration allows recruiters to import candidate profiles directly from LinkedIn into the system using a Chrome extension.

## Components

### 1. Chrome Extension
- **Location**: `/chrome-extension/`
- **Manifest Version**: 3
- **Key Files**:
  - `manifest.json` - Extension configuration
  - `popup.html/js` - Extension UI
  - `content.js` - LinkedIn page scraper
  - `background.js` - Service worker for API communication

### 2. Backend API
- **Endpoints**: `/api/v1/linkedin/*`
- **Key Endpoints**:
  - `POST /import-profile` - Import a single LinkedIn profile
  - `POST /check-exists` - Check if profile already exists
  - `POST /bulk-import` - Import multiple profiles
  - `GET /import-stats` - Get import statistics

### 3. Database Schema
- **New Fields in Resume Model**:
  - `linkedin_url` - Unique LinkedIn profile URL
  - `linkedin_data` - Raw LinkedIn data (JSON)
  - `last_linkedin_sync` - Last sync timestamp
- **New Table**:
  - `linkedin_import_history` - Track all import attempts

### 4. LinkedIn Parser Service
- **Location**: `app/services/linkedin_parser.py`
- **Features**:
  - Parse LinkedIn profile data into structured format
  - Calculate years of experience
  - Extract keywords from profile
  - Build searchable text for vector search

## Installation & Setup

### Chrome Extension Setup
1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `/chrome-extension/` directory
5. The Promtitude icon should appear in your extensions

### Backend Setup
1. Run database migration:
   ```bash
   cd backend
   alembic upgrade head
   ```

2. Ensure the LinkedIn router is included in the API (already done)

## Usage

### Importing a Profile
1. Navigate to a LinkedIn profile page
2. Click the Promtitude extension icon
3. Review the extracted data in the popup
4. Click "Import to Promtitude"
5. The profile will be added to your candidate database

### Features
- **Duplicate Detection**: Prevents importing the same profile twice
- **Data Extraction**: Extracts name, headline, experience, education, skills
- **Experience Calculation**: Automatically calculates total years of experience
- **Keyword Extraction**: Identifies key technologies and skills
- **Vector Search Integration**: Profiles are indexed for semantic search

## API Examples

### Import a Profile
```bash
POST /api/v1/linkedin/import-profile
{
  "linkedin_url": "https://www.linkedin.com/in/johndoe",
  "name": "John Doe",
  "headline": "Senior Software Engineer",
  "location": "San Francisco, CA",
  "experience": [...],
  "education": [...],
  "skills": ["Python", "React", "AWS"]
}
```

### Check if Profile Exists
```bash
POST /api/v1/linkedin/check-exists
{
  "linkedin_url": "https://www.linkedin.com/in/johndoe"
}
```

## Security Considerations
- Chrome extension only has permissions for LinkedIn domains
- All data is transmitted over HTTPS
- Authentication required for all API endpoints
- No LinkedIn credentials are stored

## Future Enhancements
1. Automated profile sync/updates
2. Bulk import from LinkedIn search results
3. LinkedIn recruiter integration
4. Connection tracking
5. Activity monitoring