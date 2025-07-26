# Chrome Extension v1.1.1 Release Notes

## Critical Privacy Fix 🔒
This update addresses a critical privacy issue where users on the same browser could see each other's import queue and statistics. All data is now properly isolated per user.

## Bug Fixes
- **Fixed duplicate detection**: "Already in Promtitude" error now shows immediately on first click
- **Fixed sidebar behavior**: Bulk import sidebar now properly closes when logging out
- **Fixed JavaScript error**: Resolved "originalText is not defined" error during imports

## What's New
- User-specific queue management - each user only sees their own imported profiles
- Per-user statistics tracking for better privacy
- Improved error messaging for duplicate profiles
- Enhanced stability and performance

## Important
Users who share browsers should update immediately to ensure data privacy.

## Technical Details
- Added userEmail tracking to all queue items
- Implemented user-specific data filtering
- Added data migration for existing queue items
- Removed all console.log statements for production