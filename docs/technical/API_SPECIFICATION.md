# Promtitude API Specification

## 1. API Overview

The Promtitude API provides programmatic access to our AI-powered resume search platform. This document describes the REST API v1.0.

### Base URL
```
Production: https://api.promtitude.ai/v1
Staging: https://staging-api.promtitude.ai/v1
```

### Authentication
All API requests require authentication using Bearer tokens:
```http
Authorization: Bearer <your-api-token>
```

### Rate Limiting
- **Free tier**: 100 requests/hour
- **Pro tier**: 1,000 requests/hour
- **Enterprise**: Custom limits

Rate limit headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## 2. Common Patterns

### Request Format
```http
Content-Type: application/json
Accept: application/json
```

### Response Format
```json
{
  "success": true,
  "data": {},
  "meta": {
    "request_id": "req_123abc",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "query",
        "message": "Query cannot be empty"
      }
    ]
  },
  "meta": {
    "request_id": "req_123abc",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Pagination
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

## 3. Authentication Endpoints

### POST /auth/login
Login with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1...",
    "refresh_token": "eyJ0eXAiOiJKV2...",
    "expires_in": 3600,
    "user": {
      "id": "usr_123abc",
      "email": "user@example.com",
      "role": "recruiter"
    }
  }
}
```

### POST /auth/refresh
Refresh access token.

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV2..."
}
```

### POST /auth/logout
Logout and invalidate tokens.

## 4. Search Endpoints

### POST /search
Perform a prompt-based search for candidates.

**Request:**
```json
{
  "query": "Senior Python developer with AWS experience and leadership skills",
  "filters": {
    "location": ["San Francisco", "Remote"],
    "experience_years": {
      "min": 5,
      "max": 10
    },
    "skills": {
      "required": ["Python", "AWS"],
      "preferred": ["Docker", "Kubernetes"]
    },
    "availability": "immediate"
  },
  "options": {
    "include_internal": true,
    "include_external": true,
    "page": 1,
    "per_page": 20,
    "sort_by": "relevance",
    "explain": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "res_456def",
        "type": "external",
        "score": 0.95,
        "confidence": "high",
        "candidate": {
          "name": "John Doe",
          "email": "john.doe@email.com",
          "location": "San Francisco, CA",
          "experience_years": 7,
          "current_role": "Senior Software Engineer",
          "skills": ["Python", "AWS", "Docker", "PostgreSQL"],
          "summary": "Experienced software engineer with strong Python and AWS skills..."
        },
        "match_explanation": {
          "strengths": [
            "7 years of Python experience matches requirement",
            "AWS certified with 5 years hands-on experience",
            "Led team of 5 engineers at previous company"
          ],
          "gaps": [
            "No explicit Kubernetes experience mentioned"
          ],
          "overall": "Strong match for senior Python developer role"
        },
        "resume_url": "https://storage.promtitude.ai/resumes/res_456def.pdf"
      }
    ],
    "facets": {
      "locations": [
        {"value": "San Francisco", "count": 45},
        {"value": "Remote", "count": 32}
      ],
      "skills": [
        {"value": "Python", "count": 67},
        {"value": "AWS", "count": 54}
      ]
    },
    "search_id": "srch_789ghi",
    "processing_time_ms": 245
  },
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 67,
    "total_pages": 4
  }
}
```

### GET /search/{search_id}
Retrieve a previous search by ID.

### POST /search/refine
Refine an existing search with additional criteria.

**Request:**
```json
{
  "search_id": "srch_789ghi",
  "refinement": "Also must have experience with microservices"
}
```

### POST /search/explain
Get detailed explanation of search logic.

**Request:**
```json
{
  "query": "Python developer with ML experience"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "interpretation": {
      "intent": "find_candidates",
      "primary_skill": "Python",
      "secondary_skills": ["Machine Learning", "ML"],
      "experience_level": "not_specified",
      "expanded_terms": [
        "Python programmer",
        "Python engineer",
        "Machine Learning engineer",
        "Data Scientist"
      ]
    },
    "search_strategy": {
      "methods": ["semantic_search", "keyword_match", "skill_taxonomy"],
      "weights": {
        "semantic": 0.5,
        "keyword": 0.3,
        "skills": 0.2
      }
    }
  }
}
```

## 5. Transparency & Compliance Endpoints (NEW for EU AI Act)

### GET /transparency/decision/{decision_id}
Get detailed explanation of an AI decision.

**Response:**
```json
{
  "success": true,
  "data": {
    "decision_id": "dec_123abc",
    "type": "candidate_ranking",
    "timestamp": "2025-07-07T10:00:00Z",
    "ai_model": "o4-mini",
    "factors": [
      {
        "name": "skill_match",
        "weight": 0.4,
        "score": 0.92,
        "explanation": "Candidate has 9/10 required skills"
      },
      {
        "name": "experience",
        "weight": 0.3,
        "score": 0.85,
        "explanation": "7 years relevant experience"
      }
    ],
    "bias_check": {
      "status": "PASSED",
      "protected_attributes_considered": ["gender", "age", "ethnicity"],
      "fairness_score": 0.94
    },
    "human_reviewable": true,
    "contestable": true
  }
}
```

### POST /transparency/contest
Contest an AI decision.

**Request:**
```json
{
  "decision_id": "dec_123abc",
  "reason": "Incorrect skill assessment",
  "evidence": "Candidate has AWS certification not recognized"
}
```

### GET /compliance/audit-trail
Get audit trail for compliance reporting.

**Request:**
```http
GET /v1/compliance/audit-trail?start_date=2025-07-01&end_date=2025-07-07&type=ai_decisions
```

## 6. Resume Management Endpoints

### POST /resumes/upload
Upload a single resume.

**Request:**
```http
POST /v1/resumes/upload
Content-Type: multipart/form-data

file: resume.pdf
metadata: {"source": "upload", "tags": ["engineering"]}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "resume_id": "res_123abc",
    "status": "processing",
    "file_name": "resume.pdf",
    "size_bytes": 245632,
    "processing_eta_seconds": 30
  }
}
```

### POST /resumes/bulk-upload
Upload multiple resumes.

**Request:**
```http
POST /v1/resumes/bulk-upload
Content-Type: multipart/form-data

files[]: resume1.pdf
files[]: resume2.pdf
metadata: {"source": "bulk_import", "folder": "Q1_2024"}
```

### GET /resumes/{resume_id}
Get resume details and parsed data.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "res_123abc",
    "status": "processed",
    "file_name": "john_doe_resume.pdf",
    "uploaded_at": "2024-01-01T00:00:00Z",
    "processed_at": "2024-01-01T00:00:30Z",
    "parsed_data": {
      "contact": {
        "name": "John Doe",
        "email": "john.doe@email.com",
        "phone": "+1-555-0123",
        "location": "San Francisco, CA",
        "linkedin": "linkedin.com/in/johndoe"
      },
      "experience": [
        {
          "company": "Tech Corp",
          "role": "Senior Software Engineer",
          "duration": "2020-2023",
          "description": "Led development of microservices..."
        }
      ],
      "education": [...],
      "skills": [...],
      "summary": "..."
    },
    "analysis": {
      "experience_years": 7,
      "skill_categories": {
        "programming": ["Python", "JavaScript"],
        "cloud": ["AWS", "GCP"],
        "databases": ["PostgreSQL", "MongoDB"]
      },
      "seniority_level": "senior",
      "specializations": ["backend", "cloud", "devops"]
    }
  }
}
```

### DELETE /resumes/{resume_id}
Delete a resume.

### POST /resumes/{resume_id}/reprocess
Reprocess a resume with latest AI models.

## 6. Analytics Endpoints

### GET /analytics/search
Get search analytics.

**Request:**
```http
GET /v1/analytics/search?start_date=2024-01-01&end_date=2024-01-31
```

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_searches": 1543,
      "unique_users": 87,
      "avg_results_per_search": 23.4,
      "avg_response_time_ms": 312
    },
    "top_queries": [
      {"query": "Python developer", "count": 234},
      {"query": "Full stack engineer", "count": 189}
    ],
    "search_trends": [
      {"date": "2024-01-01", "count": 45},
      {"date": "2024-01-02", "count": 52}
    ],
    "user_engagement": {
      "avg_refinements_per_search": 2.3,
      "result_click_rate": 0.67,
      "save_rate": 0.23
    }
  }
}
```

### GET /analytics/talent-pool
Get talent pool insights.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_candidates": 10543,
    "by_location": [...],
    "by_experience_level": {
      "junior": 2341,
      "mid": 4532,
      "senior": 2876,
      "lead": 794
    },
    "top_skills": [
      {"skill": "Python", "count": 3421},
      {"skill": "JavaScript", "count": 2987}
    ],
    "skill_combinations": [
      {"skills": ["Python", "AWS"], "count": 1876},
      {"skills": ["React", "Node.js"], "count": 1654}
    ],
    "market_insights": {
      "emerging_skills": ["Rust", "Web3", "AI/ML"],
      "declining_skills": ["jQuery", "SVN"],
      "salary_trends": {...}
    }
  }
}
```

## 7. Collaboration Endpoints

### POST /lists
Create a candidate list.

**Request:**
```json
{
  "name": "Senior Python Developers - Q1 2024",
  "description": "Shortlist for senior Python role",
  "visibility": "team",
  "candidate_ids": ["res_123", "res_456"]
}
```

### GET /lists/{list_id}
Get candidate list details.

### POST /lists/{list_id}/candidates
Add candidates to a list.

### POST /lists/{list_id}/share
Share a list with team members.

**Request:**
```json
{
  "user_ids": ["usr_789", "usr_012"],
  "permission": "view",
  "message": "Please review these candidates"
}
```

## 8. Webhook Events

### Webhook Payload Format
```json
{
  "event": "resume.processed",
  "data": {
    "resume_id": "res_123abc",
    "status": "completed"
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "signature": "sha256=..."
}
```

### Available Events
- `resume.uploaded`
- `resume.processed`
- `resume.failed`
- `search.completed`
- `candidate.matched`
- `list.shared`

## 9. WebSocket API

### Connection
```javascript
const ws = new WebSocket('wss://api.promtitude.ai/v1/ws');
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your-api-token'
}));
```

### Live Search
```javascript
// Subscribe to live search
ws.send(JSON.stringify({
  type: 'search.subscribe',
  data: {
    query: 'Python developer',
    stream: true
  }
}));

// Receive results
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'search.result') {
    console.log('New result:', message.data);
  }
};
```

## 10. GraphQL API

### Endpoint
```
POST https://api.promtitude.ai/graphql
```

### Example Query
```graphql
query SearchCandidates($query: String!, $filters: SearchFilters) {
  search(query: $query, filters: $filters) {
    results {
      id
      score
      candidate {
        name
        email
        skills
        experience {
          company
          role
          duration
        }
      }
      explanation {
        strengths
        gaps
      }
    }
    facets {
      skills {
        value
        count
      }
    }
  }
}
```

## 11. SDK Examples

### Python
```python
from promtitude import PromtitudeAPI

api = PromtitudeAPI(api_key="your-api-key")

# Search for candidates
results = api.search(
    query="Senior Python developer with AWS",
    filters={
        "location": ["San Francisco", "Remote"],
        "experience_years": {"min": 5}
    }
)

for candidate in results:
    print(f"{candidate.name} - Score: {candidate.score}")
```

### JavaScript/TypeScript
```typescript
import { Promtitude } from '@promtitude/sdk';

const client = new Promtitude({ apiKey: 'your-api-key' });

// Search with async/await
const results = await client.search({
  query: 'Senior Python developer with AWS',
  filters: {
    location: ['San Francisco', 'Remote'],
    experienceYears: { min: 5 }
  }
});

// Stream results
const stream = client.searchStream({
  query: 'Frontend developer with React'
});

for await (const candidate of stream) {
  console.log(`${candidate.name} - Score: ${candidate.score}`);
}
```

## 12. Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `AUTH_INVALID` | Invalid authentication token | 401 |
| `AUTH_EXPIRED` | Token has expired | 401 |
| `PERMISSION_DENIED` | Insufficient permissions | 403 |
| `RATE_LIMIT_EXCEEDED` | Too many requests | 429 |
| `VALIDATION_ERROR` | Invalid request parameters | 400 |
| `RESOURCE_NOT_FOUND` | Requested resource not found | 404 |
| `PROCESSING_ERROR` | Error processing request | 500 |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable | 503 |

---

**API Version**: 1.0
**Last Updated**: [Date]
**OpenAPI Spec**: [https://api.promtitude.ai/v1/openapi.json](https://api.promtitude.ai/v1/openapi.json)
**Status Page**: [https://status.promtitude.ai](https://status.promtitude.ai)