# Chrome Extension Changelog

## Version 1.1.1 - July 25, 2025

### 🔒 Critical Privacy Fix
- **Fixed user data isolation issue**: Previously, all users on the same browser could see each other's import queue and statistics. Now each user only sees their own data.
  - Queue items now track which user added them
  - Statistics are stored per user
  - Badge counts only show current user's pending items

### 🐛 Bug Fixes
- **Fixed duplicate error message not showing on first click**: The duplicate detection now works immediately when trying to import an already-imported profile
- **Fixed bulk import sidebar not closing on logout**: The sidebar now properly closes when a user logs out
- **Fixed JavaScript error**: Resolved "originalText is not defined" error that occurred when importing profiles

### 🛠️ Technical Improvements
- Added data migration for existing queue items to assign them to the current user
- Improved duplicate detection reliability with early checking
- Enhanced message display in popup for better user feedback
- Removed all console.log statements for production release

### 📝 Notes
This update is critical for users who share browsers. Please update immediately to ensure your import data remains private.

---

## Version 1.1.0 - July 23, 2025

### ✨ New Features
- **OAuth-Friendly Login UI**: Dynamic form switching based on user type
- **Welcome Screen**: Beautiful onboarding for new users
- **Access Code System**: OAuth users can now use the extension with temporary access codes

### 🐛 Bug Fixes
- Fixed access code reuse issue for OAuth users
- Fixed bulk import sidebar duplicate URL errors
- Improved duplicate import error messages

### 🧹 Code Cleanup
- Removed all console.log statements
- Cleaned up debug files
- Updated to production endpoints

---

## Version 1.0.0 - July 21, 2025

### 🎉 Initial Release
- One-click LinkedIn profile import
- Bulk import from search results
- Smart duplicate detection
- Import queue management
- Daily import statistics
- Secure authentication