# Hybrid Search with BM25 Algorithm

## Table of Contents
1. [How Hybrid Search Works](#how-hybrid-search-works)
2. [BM25 Algorithm Explained](#bm25-algorithm-explained)
3. [Combining Keyword and Vector Search](#combining-keyword-and-vector-search)
4. [Query Type Detection](#query-type-detection)
5. [Implementation Details](#implementation-details)
6. [Performance Optimization](#performance-optimization)
7. [Real-World Examples](#real-world-examples)

## How Hybrid Search Works

Hybrid search combines the precision of keyword matching (BM25) with the semantic understanding of vector search to deliver superior results.

### Why Hybrid Search?

**Keyword Search Alone**:
- ✅ Finds exact matches
- ❌ Misses semantic variations
- Example: "Python developer" won't find "Python engineer"

**Vector Search Alone**:
- ✅ Understands meaning
- ❌ May miss exact technical terms
- Example: Might rank "software developer" over "Python developer" for "Python" query

**Hybrid Search**:
- ✅ Best of both worlds
- ✅ Precise for technical terms
- ✅ Flexible for semantic meaning

### Visual Representation
```
Query: "Senior Python Developer with AWS"
                    │
          ┌─────────┴─────────┐
          │                   │
    Keyword Search      Vector Search
    (BM25 Algorithm)    (Embeddings)
          │                   │
    Find exact:         Find similar:
    - "Python"          - "Python programmer"
    - "AWS"             - "Cloud engineer"
    - "Senior"          - "Lead developer"
          │                   │
          └─────────┬─────────┘
                    │
            Fusion Algorithm
                    │
            Final Results
```

## BM25 Algorithm Explained

### The Formula

BM25 (Best Matching 25) is a probabilistic ranking function:

```
BM25(D, Q) = Σ IDF(qi) × (f(qi, D) × (k1 + 1)) / (f(qi, D) + k1 × (1 - b + b × |D|/avgdl))
```

Where:
- **D** = Document (resume)
- **Q** = Query
- **qi** = Query term i
- **f(qi, D)** = Frequency of term qi in document D
- **|D|** = Length of document D
- **avgdl** = Average document length
- **k1** = Term frequency saturation (typically 1.2)
- **b** = Length normalization (typically 0.75)

### IDF (Inverse Document Frequency)

```
IDF(qi) = log((N - df + 0.5) / (df + 0.5))
```

Where:
- **N** = Total number of documents
- **df** = Number of documents containing the term

### Implementation

```python
def calculate_bm25_score(self, resume: Resume, terms: Set[str], 
                        doc_count: int, avg_doc_length: float) -> float:
    """Calculate BM25 score for a resume"""
    
    # Combine searchable text
    doc_text = self._get_searchable_text(resume).lower()
    doc_length = len(doc_text.split())
    
    if doc_length == 0:
        return 0.0
    
    score = 0.0
    
    for term in terms:
        # Term frequency in document
        tf = doc_text.count(term.lower())
        if tf == 0:
            continue
        
        # Document frequency (simplified - in production, use actual counts)
        df = max(1, doc_count / 10)  # Assume 10% of docs contain term
        
        # IDF calculation
        idf = math.log((doc_count - df + 0.5) / (df + 0.5))
        
        # BM25 term score
        term_score = idf * (tf * (self.k1 + 1)) / (
            tf + self.k1 * (1 - self.b + self.b * doc_length / avg_doc_length)
        )
        
        score += term_score
    
    return score
```

### Example Calculation

```python
# Document: "Senior Python Developer with 5 years AWS experience"
# Query: "Python AWS"

# Term: "Python"
tf_python = 1  # Appears once
df_python = 100  # In 100 out of 1000 docs
idf_python = log((1000 - 100 + 0.5) / (100 + 0.5)) = 2.19

# Term: "AWS"  
tf_aws = 1
df_aws = 50  # Less common
idf_aws = log((1000 - 50 + 0.5) / (50 + 0.5)) = 2.94

# Document length = 8 words, average = 100 words
# k1 = 1.2, b = 0.75

# BM25 score = sum of term scores
score_python = 2.19 * (1 * 2.2) / (1 + 1.2 * (1 - 0.75 + 0.75 * 8/100))
            = 2.19 * 2.2 / 1.96 = 2.46

score_aws = 2.94 * 2.2 / 1.96 = 3.30

total_score = 5.76
```

## Combining Keyword and Vector Search

### Weight Adjustment Strategy

```python
class HybridSearchService:
    def __init__(self):
        # Default weights
        self.keyword_weight = 0.3
        self.vector_weight = 0.7
    
    def adjust_weights(self, query_type: str):
        """Dynamically adjust weights based on query type"""
        
        if query_type == "technical":
            # Technical queries need precise matching
            self.keyword_weight = 0.4
            self.vector_weight = 0.6
            
        elif query_type == "soft_skills":
            # Soft skills benefit from semantic understanding
            self.keyword_weight = 0.2
            self.vector_weight = 0.8
            
        elif query_type == "exact_match":
            # Looking for specific terms
            self.keyword_weight = 0.7
            self.vector_weight = 0.3
            
        else:
            # Balanced approach
            self.keyword_weight = 0.3
            self.vector_weight = 0.7
```

### Result Fusion Algorithm

```python
def _combine_results(self, keyword_results: List[Tuple[Dict, float]], 
                    vector_results: List[Dict[str, Any]], 
                    limit: int) -> List[Tuple[Dict, float]]:
    """Fuse keyword and vector search results"""
    
    # Normalize scores to [0, 1]
    keyword_max = max(r[1] for r in keyword_results) if keyword_results else 1.0
    vector_max = max(r["score"] for r in vector_results) if vector_results else 1.0
    
    # Build unified score map
    all_scores = {}
    
    # Add keyword scores
    for resume_data, score in keyword_results:
        resume_id = resume_data["id"]
        normalized_score = score / keyword_max if keyword_max > 0 else 0
        all_scores[resume_id] = {
            "data": resume_data,
            "keyword_score": normalized_score,
            "vector_score": 0
        }
    
    # Add vector scores
    for result in vector_results:
        resume_id = result["resume_id"]
        normalized_score = result["score"] / vector_max if vector_max > 0 else 0
        
        if resume_id in all_scores:
            all_scores[resume_id]["vector_score"] = normalized_score
        else:
            all_scores[resume_id] = {
                "data": result.get("metadata", {}),
                "keyword_score": 0,
                "vector_score": normalized_score
            }
    
    # Calculate hybrid scores
    hybrid_results = []
    for resume_id, scores in all_scores.items():
        hybrid_score = (
            self.keyword_weight * scores["keyword_score"] +
            self.vector_weight * scores["vector_score"]
        )
        
        # Add search metadata
        scores["data"]["search_metadata"] = {
            "hybrid_score": hybrid_score,
            "keyword_score": scores["keyword_score"],
            "vector_score": scores["vector_score"],
            "keyword_weight": self.keyword_weight,
            "vector_weight": self.vector_weight
        }
        
        hybrid_results.append((scores["data"], hybrid_score))
    
    # Sort by hybrid score
    hybrid_results.sort(key=lambda x: x[1], reverse=True)
    
    return hybrid_results[:limit]
```

## Query Type Detection

### Automatic Query Classification

```python
def detect_query_type(self, query: str) -> str:
    """Detect the type of search query"""
    
    query_lower = query.lower()
    
    # Check for technical indicators
    technical_terms = ['python', 'java', 'aws', 'docker', 'api', 'sql']
    technical_count = sum(1 for term in technical_terms if term in query_lower)
    
    # Check for soft skill indicators
    soft_terms = ['leadership', 'communication', 'team', 'manage', 'collaborate']
    soft_count = sum(1 for term in soft_terms if term in query_lower)
    
    # Check for exact match indicators
    if '"' in query or query.isupper() or len(query.split()) == 1:
        return "exact_match"
    
    # Classify based on counts
    if technical_count > soft_count:
        return "technical"
    elif soft_count > technical_count:
        return "soft_skills"
    else:
        return "balanced"
```

### Query Expansion

```python
async def expand_query_with_synonyms(self, query: str) -> List[str]:
    """Expand query with synonyms and variations"""
    
    expanded = [query]
    terms = self._tokenize_query(query)
    
    for term in terms:
        # Get synonyms
        synonyms = skill_synonyms.get_synonyms(term)
        
        # Create variations
        for synonym in synonyms[:3]:  # Limit expansion
            variation = query.replace(term, synonym)
            if variation not in expanded:
                expanded.append(variation)
    
    # Example:
    # Input: "ML engineer"
    # Output: ["ML engineer", "Machine Learning engineer", "AI engineer"]
    
    return expanded
```

## Implementation Details

### Complete Hybrid Search Flow

```python
async def search(self, db: AsyncSession, query: str, user_id: str, 
                limit: int = 10, filters: Optional[Dict] = None) -> List[Tuple[Dict, float]]:
    """
    Perform hybrid search combining BM25 and vector search
    """
    # 1. Detect query type and adjust weights
    query_type = self.detect_query_type(query)
    self.adjust_weights(query_type)
    
    logger.info(f"Query type: {query_type}, weights: keyword={self.keyword_weight}, vector={self.vector_weight}")
    
    # 2. Expand query with synonyms
    expanded_queries = await self.expand_query_with_synonyms(query)
    
    # 3. Perform searches in parallel
    keyword_task = self._keyword_search_bm25(db, expanded_queries, user_id, limit * 2, filters)
    vector_task = vector_search.search_similar(query, user_id, limit * 2, filters)
    
    keyword_results, vector_results = await asyncio.gather(keyword_task, vector_task)
    
    # 4. Apply fuzzy matching corrections
    keyword_results = await self._apply_fuzzy_corrections(keyword_results, query)
    
    # 5. Combine results
    combined_results = self._combine_results(keyword_results, vector_results, limit)
    
    # 6. Post-process results
    final_results = self._post_process_results(combined_results, query)
    
    return final_results
```

### PostgreSQL Full-Text Search Integration

```python
async def _keyword_search_bm25(self, db: AsyncSession, queries: List[str], 
                              user_id: str, limit: int, filters: Optional[Dict] = None):
    """Enhanced BM25 search using PostgreSQL"""
    
    # Extract all unique terms
    all_terms = set()
    for query in queries:
        terms = self._tokenize_query(query)
        all_terms.update(terms)
    
    # Build search conditions with proper indexing
    conditions = [Resume.user_id == user_id]
    
    # Create text search conditions
    text_conditions = []
    for term in all_terms:
        term_lower = term.lower()
        
        # Search in multiple fields with different weights
        term_conditions = or_(
            # Highest weight for exact title match
            func.lower(Resume.current_title).contains(term_lower),
            
            # High weight for skills match
            func.cast(Resume.skills, sa.Text).ilike(f'%{term_lower}%'),
            
            # Medium weight for summary
            func.lower(Resume.summary).contains(term_lower),
            
            # Lower weight for full text
            func.lower(Resume.raw_text).contains(term_lower)
        )
        text_conditions.append(term_conditions)
    
    if text_conditions:
        conditions.append(or_(*text_conditions))
    
    # Execute query
    stmt = select(Resume).where(and_(*conditions)).limit(limit)
    result = await db.execute(stmt)
    resumes = result.scalars().all()
    
    # Calculate BM25 scores with field weighting
    scored_results = []
    for resume in resumes:
        score = self._calculate_weighted_bm25_score(resume, all_terms)
        resume_dict = self._resume_to_dict(resume)
        scored_results.append((resume_dict, score))
    
    # Sort by score
    scored_results.sort(key=lambda x: x[1], reverse=True)
    
    return scored_results
```

### Field-Weighted BM25

```python
def _calculate_weighted_bm25_score(self, resume: Resume, terms: Set[str]) -> float:
    """Calculate BM25 with different weights for different fields"""
    
    field_weights = {
        "title": 2.0,      # Title matches are most important
        "skills": 1.5,     # Skills are very important
        "summary": 1.0,    # Summary is baseline
        "full_text": 0.5   # Full text has lower weight
    }
    
    total_score = 0.0
    
    for field, weight in field_weights.items():
        field_text = self._get_field_text(resume, field).lower()
        field_score = self._calculate_field_bm25(field_text, terms)
        total_score += field_score * weight
    
    return total_score
```

## Performance Optimization

### 1. Caching Strategy

```python
class HybridSearchCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1 hour
    
    async def get_or_search(self, query: str, user_id: str, search_func):
        """Cache hybrid search results"""
        cache_key = f"hybrid:{user_id}:{hashlib.md5(query.encode()).hexdigest()}"
        
        # Try cache first
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Perform search
        results = await search_func(query, user_id)
        
        # Cache results
        await self.redis.setex(
            cache_key, 
            self.ttl,
            json.dumps(self._serialize_results(results))
        )
        
        return results
```

### 2. Index Optimization

```sql
-- Create indexes for BM25 search
CREATE INDEX idx_resume_title_gin ON resumes USING gin(to_tsvector('english', current_title));
CREATE INDEX idx_resume_summary_gin ON resumes USING gin(to_tsvector('english', summary));
CREATE INDEX idx_resume_skills_gin ON resumes USING gin(skills);

-- Create composite index for common queries
CREATE INDEX idx_resume_user_status ON resumes(user_id, status);

-- Analyze tables for query optimization
ANALYZE resumes;
```

### 3. Parallel Processing

```python
async def parallel_search_shards(self, query: str, user_id: str):
    """Search across sharded data in parallel"""
    
    # Divide search space into shards
    shards = self._get_user_shards(user_id)
    
    # Search each shard in parallel
    tasks = []
    for shard in shards:
        tasks.append(self._search_shard(query, user_id, shard))
    
    # Gather results
    shard_results = await asyncio.gather(*tasks)
    
    # Merge and re-rank
    return self._merge_shard_results(shard_results)
```

## Real-World Examples

### Example 1: Technical Search

```python
# Query: "Senior Python Developer with AWS and Docker experience"

# Query Analysis:
query_type = "technical"
keyword_weight = 0.4
vector_weight = 0.6

# Keyword Search finds:
1. Resume with exact "Python", "AWS", "Docker" → BM25 score: 8.5
2. Resume with "Python", "AWS" → BM25 score: 6.2
3. Resume with "Python Developer" → BM25 score: 4.1

# Vector Search finds:
1. "Cloud Engineer with Python" → Vector score: 0.85
2. "DevOps Engineer - Python, Kubernetes" → Vector score: 0.82
3. "Full-stack Developer - Python/React" → Vector score: 0.78

# Hybrid Results:
1. "Python Developer with AWS" → Hybrid: 0.88
2. "Cloud Engineer with Python" → Hybrid: 0.84
3. "DevOps Engineer - Python, K8s" → Hybrid: 0.80
```

### Example 2: Soft Skills Search

```python
# Query: "Team leader with strong communication skills"

# Query Analysis:
query_type = "soft_skills"
keyword_weight = 0.2
vector_weight = 0.8

# Results emphasize semantic understanding:
1. "Engineering Manager - Built high-performing teams"
2. "Tech Lead - Excellent stakeholder management"
3. "Senior Developer - Mentored junior developers"
```

### Example 3: Exact Match Search

```python
# Query: "\"React Native\" developer"

# Query Analysis:
query_type = "exact_match"
keyword_weight = 0.7
vector_weight = 0.3

# Results prioritize exact phrase matches:
1. "React Native Developer" → Exact match
2. "Mobile Developer - React Native & Flutter"
3. "React Native Engineer"
```

## Monitoring and Tuning

### Search Quality Metrics

```python
class SearchQualityMonitor:
    def track_search_metrics(self, query: str, results: List[Tuple[Dict, float]]):
        """Track search quality metrics"""
        
        metrics = {
            "query": query,
            "result_count": len(results),
            "avg_hybrid_score": sum(r[1] for r in results) / len(results),
            "keyword_contribution": self._calculate_keyword_contribution(results),
            "vector_contribution": self._calculate_vector_contribution(results),
            "score_distribution": self._calculate_score_distribution(results),
            "skill_coverage": self._calculate_skill_coverage(query, results)
        }
        
        # Log to monitoring system
        self.log_metrics(metrics)
        
        # Adjust weights if needed
        if metrics["skill_coverage"] < 0.5:
            logger.warning(f"Low skill coverage for query: {query}")
```

### A/B Testing Framework

```python
async def ab_test_search_weights(self, query: str, user_id: str):
    """A/B test different weight configurations"""
    
    # Define test variants
    variants = [
        {"keyword": 0.3, "vector": 0.7},  # Control
        {"keyword": 0.4, "vector": 0.6},  # Test A
        {"keyword": 0.2, "vector": 0.8},  # Test B
    ]
    
    # Run searches with different weights
    results = []
    for variant in variants:
        self.keyword_weight = variant["keyword"]
        self.vector_weight = variant["vector"]
        
        variant_results = await self.search(db, query, user_id)
        results.append({
            "variant": variant,
            "results": variant_results,
            "quality_score": self._calculate_quality_score(variant_results)
        })
    
    # Return best performing variant
    return max(results, key=lambda x: x["quality_score"])
```

## Future Enhancements

### 1. Learning to Rank

```python
class LearnedRanker:
    """Use ML to learn optimal ranking from user interactions"""
    
    def train_ranker(self, search_logs: List[SearchLog]):
        features = self._extract_ranking_features(search_logs)
        labels = self._extract_relevance_labels(search_logs)
        
        # Train gradient boosting model
        self.model = LGBMRanker()
        self.model.fit(features, labels)
    
    def rerank_results(self, query: str, results: List[Dict]):
        features = self._extract_features(query, results)
        scores = self.model.predict(features)
        
        return sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
```

### 2. Query Understanding

```python
async def enhanced_query_understanding(self, query: str):
    """Deep query analysis using NLP"""
    
    # Extract entities
    entities = await self.extract_entities(query)
    
    # Identify intent
    intent = await self.classify_intent(query)
    
    # Generate query variations
    variations = await self.generate_semantic_variations(query)
    
    return {
        "entities": entities,
        "intent": intent,
        "variations": variations,
        "optimal_weights": self.calculate_optimal_weights(intent)
    }
```

This hybrid search implementation combines the precision of BM25 keyword matching with the semantic understanding of vector search, delivering superior results that understand both exact terms and meaning.