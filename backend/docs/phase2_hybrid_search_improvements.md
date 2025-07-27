# Phase 2: Hybrid Search Optimization

## Overview

Phase 2 enhances the Mind Reader search system with hybrid search capabilities, combining the strengths of keyword search (BM25 algorithm) with vector semantic search. This improvement addresses edge cases where pure vector search might miss obvious keyword matches.

## Key Components Implemented

### 1. Skill Synonyms Service (`app/services/skill_synonyms.py`)
Comprehensive database of technology abbreviations and synonyms:
- **Abbreviation Expansion**: ML → Machine Learning, K8s → Kubernetes
- **Role Synonyms**: developer → engineer, programmer, coder
- **Compound Term Handling**: "machine learning engineer" variations
- **Bidirectional Mapping**: Both abbreviation-to-full and full-to-abbreviation

Key features:
```python
# Expands "ML engineer with K8s" to multiple variations:
# ["ML engineer with K8s", "Machine Learning engineer with K8s", 
#  "ML engineer with Kubernetes", "Machine Learning engineer with Kubernetes"]
```

### 2. Hybrid Search Service (`app/services/hybrid_search.py`)
Implements BM25 keyword search combined with vector search:
- **BM25 Algorithm**: Classic information retrieval scoring
- **Dynamic Weight Adjustment**: Based on query type
- **Parallel Execution**: Keyword and vector searches run concurrently
- **Smart Result Merging**: Combines scores intelligently

Weight configurations by query type:
- Technical queries: 40% keyword, 60% vector
- Soft skills queries: 20% keyword, 80% vector
- Exact match queries: 70% keyword, 30% vector
- Exploratory queries: 30% keyword, 70% vector

### 3. Enhanced Query Analyzer (`app/services/gpt4_query_analyzer.py`)
Added query type detection to optimize search weights:
- **Query Type Detection**: Identifies technical, soft skills, experience, exact match, or exploratory queries
- **Improved Analysis**: Better understanding of search intent
- **Weight Optimization**: Automatically adjusts hybrid search weights

### 4. Fuzzy Matching Service (`app/services/fuzzy_matcher.py`)
Handles typos and variations in skill matching:
- **Typo Correction**: "pyton" → "python", "reactjs" → "react"
- **Similarity Scoring**: Uses SequenceMatcher for fuzzy comparison
- **Configurable Threshold**: Default 80% similarity for matches
- **Common Pattern Recognition**: Detects abbreviations and variations

### 5. PostgreSQL Full-Text Search Indexes
Created comprehensive indexes for performance:
- **GIN Indexes**: For full-text search on resume content
- **Trigram Indexes**: For fuzzy string matching
- **Composite Indexes**: For multi-field searches
- **Materialized Views**: For pre-computed statistics

## Integration with Progressive Search

The hybrid search is integrated into Stage 2 of the progressive search:

1. **Stage 1**: Quick cache/keyword matches (unchanged)
2. **Stage 2**: Now uses hybrid search instead of pure vector search
3. **Stage 3**: AI enhancement with GPT-4.1-mini (unchanged)

## Performance Improvements

### Search Quality
- **Better Keyword Matching**: No longer misses obvious keyword matches
- **Typo Tolerance**: Handles common misspellings gracefully
- **Synonym Understanding**: Recognizes technical term variations
- **Context-Aware Ranking**: Adjusts scoring based on query type

### Search Speed
- **Parallel Execution**: Keyword and vector searches run simultaneously
- **PostgreSQL Indexes**: Full-text GIN indexes for fast keyword search
- **Smart Caching**: Expanded query variations are cached
- **Target Performance**: Stage 2 still completes in <200ms

## Usage Examples

### Skill Synonym Expansion
```python
from app.services.skill_synonyms import skill_synonyms

# Expand a query
variations = skill_synonyms.expand_query("ML engineer with K8s")
# Returns: ["ML engineer with K8s", "Machine Learning engineer with K8s", ...]

# Normalize a skill
normalized = skill_synonyms.normalize_skill("JS")
# Returns: "javascript"
```

### Fuzzy Matching
```python
from app.services.fuzzy_matcher import fuzzy_matcher

# Correct typos
corrections = fuzzy_matcher.suggest_corrections(["pyton", "reactjs"])
# Returns: {"pyton": "python", "reactjs": "react"}

# Match skills with tolerance
matched, missing, score = fuzzy_matcher.match_skills(
    ["Python", "Machine Learning"],
    ["Python", "ML", "Django"]
)
# Returns: matched=["Python", "Machine Learning"], missing=[], score=1.0
```

### Hybrid Search
```python
from app.services.hybrid_search import hybrid_search

# Adjust weights for query type
hybrid_search.adjust_weights("technical")  # 40% keyword, 60% vector

# Perform search
results = await hybrid_search.search(
    db=db,
    query="Senior Python developer AWS",
    user_id=user_id,
    limit=10,
    use_synonyms=True
)
```

## Testing

Run the comprehensive test suite:
```bash
cd backend
python scripts/test_hybrid_search.py
```

This tests:
- Skill synonym expansion
- Fuzzy matching capabilities
- Query type detection
- Hybrid search performance
- Progressive search integration

## Migration

Apply the database migration for full-text indexes:
```bash
cd backend
alembic upgrade head
```

This creates:
- GIN indexes for full-text search
- Trigram indexes for fuzzy matching
- Helper functions for BM25 scoring
- Materialized view for document statistics

## Benefits

1. **Improved Accuracy**: Catches both semantic and keyword matches
2. **Typo Tolerance**: No more missed candidates due to typos
3. **Synonym Recognition**: Understands ML = Machine Learning
4. **Query-Adaptive**: Optimizes for different search intents
5. **Fast Performance**: Still meets <200ms target for Stage 2

## Next Steps

Potential future enhancements:
1. **Learning from Feedback**: Adjust weights based on click-through rates
2. **Custom Synonyms**: Allow users to define domain-specific synonyms
3. **Multi-language Support**: Extend fuzzy matching to other languages
4. **Advanced Scoring**: Incorporate more signals (recency, popularity)

The hybrid search optimization makes Promtitude's Mind Reader search even more intelligent, catching candidates that pure vector search might miss while maintaining the semantic understanding that makes it special.