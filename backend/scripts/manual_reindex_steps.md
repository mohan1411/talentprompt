# Manual Steps to Run Security Reindex

Since the automated scripts are having connection issues, here are manual steps:

## Option 1: Using Browser Developer Tools

1. **Login to your Promtitude app** at https://talentprompt-production.up.railway.app

2. **Open Browser Developer Tools** (F12)

3. **Go to the Network tab**

4. **Do any action** (like viewing resumes) to see a request

5. **Find the Authorization header** in any API request:
   - Look for a request to `/api/v1/...`
   - Click on it
   - Go to Headers tab
   - Copy the `Authorization: Bearer ...` value

6. **Open the Console tab** and run this JavaScript:
```javascript
fetch('https://talentprompt-production.up.railway.app/api/v1/admin/security-reindex-vectors', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN_HERE',  // Replace with your actual token
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log('Reindex result:', data))
.catch(error => console.error('Error:', error));
```

## Option 2: Using Postman or Thunder Client

1. **Login via API**:
   - POST to: `https://talentprompt-production.up.railway.app/api/v1/auth/login`
   - Body type: `x-www-form-urlencoded`
   - Body:
     ```
     username: your-email@example.com
     password: your-password
     ```

2. **Copy the access_token** from the response

3. **Call reindex endpoint**:
   - POST to: `https://talentprompt-production.up.railway.app/api/v1/admin/security-reindex-vectors`
   - Headers:
     ```
     Authorization: Bearer YOUR_ACCESS_TOKEN
     Content-Type: application/json
     ```

## Option 3: Direct Database Fix (Last Resort)

If vector reindexing fails, at minimum the database searches are already secure. You can verify this:

1. Create two test user accounts
2. Upload resumes to each account
3. Login as user 1 and search - you should only see user 1's resumes
4. Login as user 2 and search - you should only see user 2's resumes

The database search is already filtering by user_id, so basic security is in place even without the vector search fix.

## What the Reindex Does

The reindex adds `user_id` to all resume vectors in Qdrant, ensuring that:
- Vector/semantic searches also filter by user
- AI-powered search respects user boundaries
- Performance is optimized with proper indexing

## Verification

After reindexing, test that:
1. Each user only sees their own resumes
2. Search results are properly filtered
3. Similar resumes only shows user's own data
4. Popular tags only shows user's own tags