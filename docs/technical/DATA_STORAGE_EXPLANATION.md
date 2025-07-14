# Promtitude: Data Storage Explanation

## Hybrid Storage Approach: Traditional + Vector

Promtitude uses a **hybrid storage approach** that combines traditional relational database storage with vector embeddings. This gives us the best of both worlds.

## How Data is Stored

### 1. Traditional Relational Data (PostgreSQL)
All resume information is stored in standard database columns:

```sql
-- Traditional columns in the resumes table
first_name         VARCHAR(100)    -- "John"
last_name          VARCHAR(100)    -- "Doe"
email              VARCHAR(255)    -- "john.doe@email.com"
phone              VARCHAR(50)     -- "+1-555-123-4567"
current_title      VARCHAR(255)    -- "Senior Software Engineer"
location           VARCHAR(255)    -- "New York, NY"
years_experience   INTEGER         -- 8
summary            TEXT            -- "Experienced developer with..."
skills             TEXT[]          -- ["Python", "AWS", "Docker"]
raw_text           TEXT            -- Full resume text
job_position       VARCHAR(255)    -- "Backend Developer"
```

**This traditional data is used for:**
- Displaying resume details
- Filtering by exact criteria (location, years of experience)
- Traditional SQL queries
- Data export/reporting
- User interface display

### 2. Vector Embeddings (pgvector extension)
In ADDITION to traditional data, we store a vector representation:

```sql
-- Vector column in the same resumes table
embedding          vector(1536)    -- [0.0023, -0.0341, 0.0892, ...]
```

**The vector is used ONLY for:**
- Semantic/similarity search
- Finding "similar" resumes
- Natural language query matching

## Why Both?

### Traditional Database Benefits:
✅ **Exact matching**: Find all resumes with location = "New York"
✅ **Range queries**: Find resumes with 5-10 years experience  
✅ **Structured data**: Easy to display, filter, sort
✅ **Standard SQL**: JOIN with other tables, aggregations
✅ **Human readable**: Can directly query and understand data

### Vector Embedding Benefits:
✅ **Semantic search**: "Find me a Python developer" matches resumes even if they say "Django developer" or "Flask expert"
✅ **Similarity matching**: Find resumes similar to a top performer
✅ **Natural language**: Understands context and meaning
✅ **Fuzzy matching**: Handles variations in terminology

## Example: How Search Works

When you search for "Senior Python developer with cloud experience":

### Step 1: Vector Search (Primary)
```sql
-- Convert search query to vector using OpenAI
query_embedding = [0.0156, -0.0234, 0.0445, ...] 

-- Find similar resumes using vector distance
SELECT *, 1 - (embedding <=> query_embedding) AS similarity
FROM resumes
WHERE embedding IS NOT NULL
ORDER BY similarity DESC
```

### Step 2: Traditional Filters (Secondary)
```sql
-- Apply additional filters using traditional columns
AND location LIKE '%New York%'
AND years_experience >= 5
AND 'Python' = ANY(skills)
```

### Step 3: Display Results
```python
# Use traditional columns for display
for resume in results:
    print(f"{resume.first_name} {resume.last_name}")
    print(f"Title: {resume.current_title}")
    print(f"Experience: {resume.years_experience} years")
    print(f"Skills: {', '.join(resume.skills)}")
```

## Storage Example

Here's what a single resume looks like in the database:

```json
{
  // Traditional columns
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "first_name": "Sarah",
  "last_name": "Johnson",
  "email": "sarah.j@email.com",
  "current_title": "Senior Backend Engineer",
  "location": "San Francisco, CA",
  "years_experience": 7,
  "skills": ["Python", "Django", "AWS", "PostgreSQL", "Docker"],
  "summary": "Experienced backend engineer specializing in scalable Python applications...",
  
  // Vector representation (simplified - actually 1536 dimensions)
  "embedding": [0.0234, -0.0156, 0.0892, 0.0445, -0.0623, ...]
}
```

## Benefits of Hybrid Approach

1. **Best Search Experience**
   - Natural language queries use vectors
   - Precise filters use traditional columns
   - Combined for powerful search

2. **Flexibility**
   - Can do exact matches (SQL) OR fuzzy matches (vectors)
   - Can sort by traditional fields (experience, date)
   - Can find similar profiles using vectors

3. **Performance**
   - Traditional indexes for fast filtering
   - Vector indexes for fast similarity search
   - Can optimize each independently

4. **Maintainability**
   - Traditional data is human-readable
   - Easy to debug and modify
   - Standard SQL tools work normally

## Common Misconceptions

❌ **"Everything is stored as vectors"**
✅ **Reality**: Vectors are ADDITIONAL to traditional storage

❌ **"Can't do regular database queries"**
✅ **Reality**: All normal SQL operations work perfectly

❌ **"Vectors replace the database"**
✅ **Reality**: Vectors enhance the database with AI capabilities

## Technical Architecture

```
PostgreSQL Database
├── Traditional Tables & Columns (95% of data)
│   ├── users table
│   ├── resumes table (with all fields)
│   └── Standard indexes
│
└── pgvector Extension (5% of data)
    ├── vector column in resumes table
    └── IVFFlat index for similarity search
```

## Summary

Promtitude stores data in a **traditional PostgreSQL database** with all the normal columns and features you'd expect. The vector embeddings are simply an additional column that enables AI-powered semantic search. 

Think of it like adding a "search helper" column that makes finding relevant resumes much smarter, while keeping all the benefits of a traditional database.