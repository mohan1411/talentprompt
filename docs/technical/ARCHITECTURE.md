# TalentPrompt System Architecture

## 1. Overview

TalentPrompt is built on a modern microservices architecture designed for scalability, performance, and AI/ML workloads. The system prioritizes real-time processing, semantic understanding, and EU AI Act compliance.

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                           Frontend Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  Next.js 15 SSR    │    React 19 SPA    │   Mobile PWA         │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API Gateway                             │
├─────────────────────────────────────────────────────────────────┤
│  Kong/Nginx    │    Rate Limiting    │    Auth    │    WAF     │
└─────────────────────────────────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Core API      │    │   Search API    │    │   AI Service    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│  FastAPI        │    │  FastAPI        │    │  FastAPI        │
│  - Users        │    │  - Query Parse  │    │  - Inference    │
│  - Jobs         │    │  - Ranking      │    │  - Embeddings   │
│  - Candidates   │    │  - Filtering    │    │  - NLP          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        └────────────────────────┴────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                    AI Compliance & Transparency Layer            │
├─────────────────────────────────────────────────────────────────┤
│  • Decision Logging      • Bias Detection    • Audit Trail      │
│  • Transparency API      • Human Oversight   • Risk Assessment  │
└─────────────────────────────────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  PostgreSQL 16  │    │   Qdrant        │    │   Redis 7.0     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│  - Core Data    │    │  - Vectors      │    │  - Cache        │
│  - Audit Logs   │    │  - Embeddings   │    │  - Sessions     │
│  - AI Decisions │    │  - Similarity   │    │  - Rate Limits  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 3. Component Details

### 3.1 Frontend Layer

**Next.js 15 Application**
- Server-side rendering for SEO and performance
- React Server Components for optimal loading
- Turbopack for fast development builds
- Progressive Web App capabilities

**Key Features:**
- Real-time updates via WebSocket
- Offline-first architecture
- Responsive design system
- Accessibility (WCAG 2.1 AAA)

### 3.2 API Gateway

**Kong/Nginx Gateway**
- Request routing and load balancing
- API rate limiting and throttling
- Authentication and authorization
- Request/response transformation
- Web Application Firewall (WAF)

### 3.3 Microservices

**Core API Service**
- User management and authentication
- Job posting management
- Candidate profile management
- Application tracking
- Team collaboration

**Search API Service**
- Natural language query parsing
- Semantic search execution
- Result ranking and filtering
- Search analytics
- Query expansion

**AI Service**
- LLM inference (OpenAI o4-mini, Claude 4)
- Document embedding generation
- Skills extraction
- Resume parsing
- Bias detection

### 3.4 AI Compliance Layer (EU AI Act)

**Transparency Service**
- Decision explanation generation
- Audit trail management
- Bias monitoring
- Human review workflows
- Contestability handling

**Key Compliance Features:**
- Every AI decision is logged with explanation
- Real-time bias detection on protected attributes
- Human-in-the-loop for high-stakes decisions
- API endpoints for decision transparency
- Automated compliance reporting

### 3.5 Data Layer

**PostgreSQL 16**
- Primary data store
- JSONB for flexible schemas
- pgvector for embeddings
- Full-text search with pg_trgm
- Row-level security

**Qdrant Vector Database**
- High-performance vector similarity search
- HNSW indexing for fast queries
- Distributed architecture
- Real-time index updates
- Filtering with payload

**Redis 7.0**
- Session management
- API response caching
- Rate limiting counters
- Pub/sub for real-time features
- Background job queues

## 4. Data Flow

### 4.1 Search Flow

```
User Query → API Gateway → Search API → Query Parser
                                           ↓
                                    Embedding Service
                                           ↓
                                    Vector Search (Qdrant)
                                           ↓
                                    Result Ranking
                                           ↓
                                    Bias Check
                                           ↓
                                    Response Cache → User
```

### 4.2 Resume Processing Flow

```
Resume Upload → API Gateway → Core API → File Storage
                                           ↓
                                    AI Service (Parsing)
                                           ↓
                                    Data Extraction
                                           ↓
                                    Embedding Generation
                                           ↓
                                    Vector Storage → Search Index
```

## 5. Security Architecture

### 5.1 Network Security
- VPC with private subnets
- Network segmentation
- TLS 1.3 everywhere
- DDoS protection (Cloudflare)

### 5.2 Application Security
- JWT-based authentication
- OAuth 2.0 / SAML SSO
- Role-based access control (RBAC)
- API key management
- Input validation and sanitization

### 5.3 Data Security
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Key management (AWS KMS)
- PII tokenization
- Secure file storage (S3 with encryption)

## 6. Scalability & Performance

### 6.1 Horizontal Scaling
- Kubernetes orchestration
- Auto-scaling based on metrics
- Load balancing across instances
- Database read replicas
- Distributed caching

### 6.2 Performance Optimization
- CDN for static assets
- Database query optimization
- Connection pooling
- Lazy loading and pagination
- Event-driven architecture

### 6.3 Monitoring & Observability
- Distributed tracing (OpenTelemetry)
- Metrics collection (Prometheus)
- Log aggregation (ELK stack)
- Real-time alerting (PagerDuty)
- Performance monitoring (DataDog)

## 7. Infrastructure

### 7.1 Cloud Platform
- **Primary**: AWS (us-east-1)
- **Secondary**: AWS (eu-west-1)
- **CDN**: CloudFront
- **DNS**: Route 53

### 7.2 Container Orchestration
- Kubernetes (EKS)
- Docker containers
- Helm charts for deployment
- GitOps with ArgoCD

### 7.3 CI/CD Pipeline
- GitHub Actions
- Automated testing
- Security scanning
- Blue-green deployments
- Rollback capabilities

## 8. Development Practices

### 8.1 Code Organization
```
talentprompt/
├── services/
│   ├── core-api/
│   ├── search-api/
│   ├── ai-service/
│   └── compliance-service/
├── frontend/
│   ├── web/
│   └── mobile/
├── infrastructure/
│   ├── terraform/
│   └── kubernetes/
└── shared/
    ├── proto/
    └── libs/
```

### 8.2 API Design
- RESTful principles
- OpenAPI 3.0 specification
- Versioned endpoints
- Consistent error handling
- HATEOAS where applicable

### 8.3 Testing Strategy
- Unit tests (>80% coverage)
- Integration tests
- End-to-end tests
- Performance tests
- Security tests

## 9. Disaster Recovery

### 9.1 Backup Strategy
- Automated daily backups
- Point-in-time recovery
- Cross-region replication
- 30-day retention

### 9.2 High Availability
- Multi-AZ deployments
- Health checks and auto-recovery
- Circuit breakers
- Graceful degradation

### 9.3 RTO/RPO Targets
- Recovery Time Objective: < 1 hour
- Recovery Point Objective: < 15 minutes

---

**Document Version**: 1.0
**Last Updated**: July 2025
**Architecture Review**: Quarterly