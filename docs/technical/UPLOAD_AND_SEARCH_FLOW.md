# Promtitude: Upload and Search Flow Documentation

## Table of Contents
1. [Resume Upload Flow](#resume-upload-flow)
2. [Resume Processing Pipeline](#resume-processing-pipeline)
3. [Search Flow](#search-flow)
4. [Find Similar Flow](#find-similar-flow)
5. [Technical Architecture](#technical-architecture)

---

## Resume Upload Flow

### Overview
The resume upload feature supports both individual file uploads and bulk uploads via ZIP files. The system processes resumes asynchronously to extract structured data and generate embeddings for AI-powered search.

### Upload Stages

#### Stage 1: File Selection and Validation (Frontend)
1. **User selects files** via drag-and-drop or file picker
   - Supported formats: PDF, DOCX, DOC, TXT
   - Single files or ZIP archives containing multiple resumes
   - Maximum file size: 10MB per file

2. **Frontend validation**
   - File type checking
   - File size validation
   - ZIP file extraction (if applicable)

3. **Optional metadata** 
   - Job position assignment (for bulk tagging)

#### Stage 2: Upload to Backend
1. **API Request** (`POST /api/v1/resumes/`)
   - Multipart form data with file
   - Optional job_position parameter
   - JWT authentication required

2. **Backend validation**
   - File type verification
   - User authentication check
   - Storage quota validation

3. **Initial database record creation**
   ```python
   # Resume record created with:
   - status: 'active'
   - parse_status: 'pending'
   - original_filename
   - file_size
   - file_type
   - user_id
   - job_position (if provided)
   ```

#### Stage 3: File Storage
1. **Local file storage**
   - File saved to `uploads/resumes/{user_id}/{uuid}_{filename}`
   - Original filename preserved in database
   - File permissions set appropriately

2. **Response to frontend**
   - Resume ID returned
   - Initial status information
   - File can be tracked for processing progress

---

## Resume Processing Pipeline

### Overview
Resume processing happens asynchronously in the background after upload. The pipeline extracts text, uses AI to parse structured data, and generates embeddings for search.

### Processing Stages

#### Stage 1: Text Extraction
1. **File type detection and parsing**
   - PDF: Using PyPDF2 library
   - DOCX: Using python-docx library
   - TXT: Direct text reading

2. **Raw text extraction**
   - Full document text extracted
   - Encoding issues handled
   - Empty document detection

3. **Status update**
   - `parse_status` → 'processing'

#### Stage 2: AI-Powered Data Extraction
1. **OpenAI API call** (using GPT-4 or similar)
   - Raw text sent with structured extraction prompt
   - Prompt requests specific fields:
     ```
     - First name & Last name
     - Email & Phone
     - Location
     - Current job title
     - Years of experience
     - Professional summary
     - Skills list
     - Keywords
     ```

2. **Response parsing**
   - JSON response validated
   - Missing fields handled gracefully
   - Data type conversions applied

3. **Database update**
   - Structured fields populated
   - `parsed_data` JSON stored for reference
   - `parsed_at` timestamp recorded

#### Stage 3: Embedding Generation
1. **Text preparation**
   - Combine relevant fields (title, summary, skills)
   - Create searchable text representation
   - Limit to embedding model token limits

2. **OpenAI Embeddings API** (text-embedding-ada-002)
   - 1536-dimensional vector generated
   - Represents semantic meaning of resume

3. **Vector storage**
   - Embedding stored in PostgreSQL pgvector column
   - Enables similarity search
   - Indexed for performance

#### Stage 4: Final Status Update
1. **Success path**
   - `parse_status` → 'completed'
   - All fields populated
   - Ready for search

2. **Failure handling**
   - `parse_status` → 'failed'
   - Error logged
   - Partial data retained if available

---

## Search Flow

### Overview
The search feature uses natural language processing to understand queries and vector similarity search to find relevant candidates.

### Search Stages

#### Stage 1: Query Processing (Frontend)
1. **User input**
   - Natural language query entered
   - Optional filters applied (location, experience, skills)
   - Limit extraction from query (e.g., "top 5 candidates")

2. **Query enhancement**
   - Patterns detected: "top N", "first N", "show N"
   - Limit extracted and query cleaned
   - Default limit: 10 results

#### Stage 2: API Request
1. **Search request** (`POST /api/v1/search/`)
   ```json
   {
     "query": "senior python developer with AWS",
     "limit": 10,
     "filters": {
       "location": "New York",
       "min_experience": 5,
       "skills": ["Python", "AWS"]
     }
   }
   ```

#### Stage 3: Backend Processing
1. **Query embedding generation**
   - Natural language query → OpenAI Embeddings API
   - Same model as resume embeddings (text-embedding-ada-002)
   - 1536-dimensional vector created

2. **Database query construction**
   ```sql
   SELECT 
     r.*,
     1 - (r.embedding <=> query_embedding) AS similarity
   FROM resumes r
   WHERE 
     r.status = 'active'
     AND r.parse_status = 'completed'
     AND r.embedding IS NOT NULL
     -- Additional filters applied
   ORDER BY similarity DESC
   LIMIT :limit
   ```

3. **Filter application**
   - Location: Case-insensitive partial match
   - Experience: Range filter (min/max years)
   - Skills: Array overlap check

#### Stage 4: Result Enhancement
1. **Highlight generation**
   - Query terms matched against resume content
   - Relevant sentences extracted
   - Limited to 3 highlights per result

2. **Summary snippet creation**
   - First 200 characters of summary
   - Truncated with ellipsis if needed

3. **Scoring**
   - Similarity score (0-1) converted to percentage
   - Results ordered by relevance

#### Stage 5: Response and Display
1. **API response**
   - Array of search results
   - Each result includes score and highlights
   - Search appearance count updated

2. **Frontend rendering**
   - Results displayed as cards
   - Match percentage shown
   - Skills and highlights visible
   - "Find Similar" and "View Details" actions

---

## Find Similar Flow

### Overview
The "Find Similar" feature uses vector similarity to find candidates with similar profiles to a selected resume.

### Similar Search Stages

#### Stage 1: Initiation
1. **User action**
   - Click "Find Similar" button on resume card
   - Available from search results or resume list
   - Resume ID captured

2. **Navigation**
   - Route to `/dashboard/search/similar/{resume_id}`
   - Candidate name passed as query parameter

#### Stage 2: Similarity Search
1. **API request** (`GET /api/v1/search/similar/{resume_id}`)
   - Resume ID provided
   - Optional limit parameter (default: 5)

2. **Reference embedding retrieval**
   ```sql
   SELECT embedding 
   FROM resumes 
   WHERE id = :resume_id
   ```

3. **Similarity calculation**
   ```sql
   SELECT 
     r.*,
     1 - (r.embedding <=> reference_embedding) AS similarity
   FROM resumes r
   WHERE 
     r.id != :resume_id
     AND r.status = 'active'
   ORDER BY similarity DESC
   LIMIT :limit
   ```

#### Stage 3: Results Display
1. **Similar candidates shown**
   - Similarity percentage displayed
   - Same card format as search results
   - Recursive similarity search enabled

---

## Technical Architecture

### Key Components

#### 1. File Processing Service
```python
class FileParserService:
    - extract_text_from_pdf()
    - extract_text_from_docx()
    - extract_text_from_txt()
    - parse_file() # Main entry point
```

#### 2. AI Processing Service
```python
class AIService:
    - extract_resume_data() # Structured data extraction
    - generate_embedding() # Vector embedding creation
```

#### 3. Resume Processor Service
```python
class ResumeProcessorService:
    - process_resume() # Orchestrates full pipeline
    - process_resume_background() # Async task handler
```

#### 4. Search Service
```python
class SearchService:
    - search_resumes() # Natural language search
    - get_similar_resumes() # Vector similarity search
```

### Database Schema

#### Resumes Table
```sql
CREATE TABLE resumes (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    
    -- Basic info
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    
    -- Professional info
    current_title VARCHAR(255),
    location VARCHAR(255),
    years_experience INTEGER,
    summary TEXT,
    
    -- AI/Search fields
    embedding vector(1536),
    raw_text TEXT,
    parsed_data JSONB,
    skills TEXT[],
    keywords TEXT[],
    
    -- Metadata
    status VARCHAR(50),
    parse_status VARCHAR(50),
    job_position VARCHAR(255),
    
    -- Tracking
    view_count INTEGER DEFAULT 0,
    search_appearance_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    parsed_at TIMESTAMP
);

-- Vector similarity index
CREATE INDEX resumes_embedding_idx ON resumes 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### External Services

#### 1. OpenAI API
- **Model for parsing**: GPT-4 or GPT-3.5-turbo
- **Embedding model**: text-embedding-ada-002
- **Rate limiting**: Handled with retries
- **Error handling**: Graceful degradation

#### 2. PostgreSQL with pgvector
- **Vector storage**: 1536-dimensional embeddings
- **Similarity search**: Cosine distance operator (<=>)
- **Performance**: IVFFlat index for fast search
- **Scaling**: Supports millions of vectors

### Performance Considerations

1. **Asynchronous Processing**
   - Background tasks for resume parsing
   - Non-blocking file uploads
   - Progress tracking available

2. **Database Optimization**
   - Vector indexes for fast similarity search
   - Connection pooling (40 connections)
   - Batch processing for bulk uploads

3. **Caching Strategy**
   - Redis for frequently accessed data
   - Embedding cache for repeated queries
   - Search result caching (future enhancement)

### Error Handling

1. **Upload failures**
   - Retry mechanism for transient errors
   - Partial data preservation
   - User notification system

2. **AI service failures**
   - Fallback to basic text extraction
   - Manual review queue (future)
   - Error logging and monitoring

3. **Search failures**
   - Graceful degradation
   - Empty result handling
   - Error messages to users