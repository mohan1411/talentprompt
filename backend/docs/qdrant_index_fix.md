# Qdrant Index Configuration Fix

## Issue

When performing vector searches with user_id filtering, Qdrant returns a 400 Bad Request error:

```
Index required but not found for "user_id" of one of the following types: [uuid, keyword]. 
Help: Create an index for this key or use a different filter.
```

## Root Cause

Qdrant requires explicit indexes on fields used in filters for performance and query optimization. The `user_id` field is used to filter search results (for security - users should only see their own resumes), but the index wasn't created when the collection was initialized.

## Solution

### 1. Automatic Index Creation

Updated `vector_search.py` to automatically create indexes when initializing the collection:

```python
def _create_indexes(self):
    """Create necessary indexes on the collection."""
    # Create index on user_id field - CRITICAL for filtering
    self.client.create_payload_index(
        collection_name=self.collection_name,
        field_name="user_id",
        field_schema=KeywordIndexParams(
            type=PayloadSchemaType.KEYWORD,
            is_tenant=True  # Optimize for tenant isolation
        )
    )
```

### 2. Manual Fix Script

Created `scripts/fix_qdrant_indexes.py` to fix existing collections:

```bash
cd backend
python scripts/fix_qdrant_indexes.py
```

This script:
- Creates indexes on `user_id` and `resume_id` fields
- Verifies the indexes are working
- Optionally allows recreating the collection if needed

### 3. Prevention

The vector search service now:
- Automatically creates indexes when creating a new collection
- Ensures indexes exist when connecting to an existing collection
- Handles index creation errors gracefully

## Impact

Without these indexes:
- Vector searches with user_id filtering fail with 400 error
- The Mind Reader search cannot retrieve results
- Users see "No results found" even when matches exist

With the fix:
- Searches work correctly with user_id filtering
- Performance is optimized for tenant isolation
- No manual intervention needed for new deployments

## Testing

After applying the fix, test with:

```bash
cd backend
python scripts/test_vector_search.py
```

The search should now return results without the index error.