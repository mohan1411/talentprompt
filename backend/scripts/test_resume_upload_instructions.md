
# Test Resume Upload Instructions

## Files Generated:
1. `test_resumes_100.json` - Full resume data for upload
2. `test_resumes_names_only.txt` - Simple list of names for quick reference

## How to Upload to Production:

### Option 1: Using the Web Interface
1. Go to your Promtitude dashboard
2. Navigate to Resume Management or Bulk Import
3. Upload the `test_resumes_100.json` file
4. Select user: promtitude@gmail.com
5. Click Import

### Option 2: Using API (if available)
```bash
curl -X POST https://your-domain.com/api/v1/resumes/bulk-import   -H "Authorization: Bearer YOUR_TOKEN"   -H "Content-Type: application/json"   -d @test_resumes_100.json
```

### Option 3: Direct Database Script
1. Copy `test_resumes_100.json` to your backend folder
2. Run: `python scripts/import_test_resumes.py`

## Special Test Cases:
- **William Alves** - Perfect Python + AWS match
- **Sarah Chen** - Senior Python with AWS, Azure
- **Michael Johnson** - Python without AWS
- **Emily Williams** - AWS without Python
- **David Brown** - Junior Python developer

## Search Queries to Test:
1. "Senior Python developer with AWS" - Should rank William Alves and Sarah Chen highest
2. "Python" - Should return all Python developers
3. "AWS" - Should return all AWS professionals
4. "DevOps" - Should return DevOps engineers
5. "Machine Learning" - Should return data scientists

## Verification:
After upload, verify with:
- Total count should be 100
- Search for "William Alves" should return 1 result
- All resumes should be associated with promtitude@gmail.com
