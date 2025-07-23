# Promtitude TODO List

### Task: Registration Page ✅ COMPLETED - July 21, 2025
**Platforms:** Web
**Priority:** High
**Status:** ✅ COMPLETED
**Description:**
Implement Captcha and email verification when user register through email and password
- [x] Added Google reCAPTCHA v3 integration
- [x] Created email verification system
- [x] Added verification endpoints
- [x] Created verification pending and success pages
- [x] Updated registration flow to send verification emails
- [x] Added success message on login page after verification


### Dashboard Improvements ✅ COMPLETED - July 21, 2025
```
### Task: Improve Dashboard UX for New Users
**Platforms:** Web
**Priority:** High
**Status:** ✅ COMPLETED
**Description:** 

- Dashboard
    - [x] Show an information in Dashboard, what the tool does - Added "Find the Right Candidate with Natural Language Search" welcome section
    - [x] When logged in first time and/or no source for the resumes are mentioned - Added "No resumes available to screen" empty state
    - [x] Give a hint, a resume source can be a local folder, google drive etc - Added resume source hints (Local Folder, Google Drive, ATS Systems)
    - [x] Show a bar chart - Added interactive bar chart with daily/weekly/monthly/yearly filters for resume upload trends

- Profile
  - [x] When the Profile button is clicked on the menu side bar, the site is crashing (Safari) - Fixed by creating profile page
    - [x] Console Log: Failed to load resource: the server responded with a status of 404 () - Profile page now exists at /dashboard/profile
```

## 🔴 CRITICAL SECURITY FIXES (DO THESE FIRST!)

### User Data Isolation - PRIVACY BREACH ✅ COMPLETELY FIXED! 
- [x] **FIX SEARCH TO FILTER BY USER** - Fixed critical issue where ALL users could see ALL resumes!
  - [x] Update search service to filter by user_id
  - [x] Update vector search to include user_id in metadata
  - [x] Update all search endpoints to pass current_user.id
  - [x] Fix similar resumes endpoint to only show user's own resumes
  - [x] Fix popular tags to only show from user's resumes
  - [x] Created reindex script (backend/scripts/reindex_vectors.py)
  - [x] **✅ COMPLETED**: Ran reindex script in production (50 resumes reindexed successfully)
  - [x] Tested in local environment - confirmed working
- [x] Audit all other endpoints for data leakage - all secure
- [ ] Add integration tests to prevent regression
- [x] **SECURITY FIX DEPLOYED** - July 19, 2025

## 🚀 Immediate Priorities

### Chrome Extension Publishing ✅ PUBLISHED - July 23, 2025
- [x] Create 128x128px PNG icon for Chrome Web Store
- [x] Take 3-4 screenshots of extension in action
- [x] Pay $5 Chrome Web Store developer fee
- [x] Create production ZIP file from `/chrome-extension/`
- [x] Write store description (132 char summary + full description)
- [x] Submit to Chrome Web Store for review
- [x] **STATUS**: Published and available in Chrome Web Store!
- [x] OAuth user authentication implemented for extension users

### Critical Fixes
- [x] Test all features in production after recent deployments - ✅ All working
- [x] Email verification system - ✅ WORKING in production with Gmail SMTP
- [ ] Verify GDPR compliance features are working
- [ ] Check if analytics dashboard is showing real data
- [ ] Monitor OpenAI usage dashboard daily

## 🔧 Configuration Needed

### Environment Variables
- [ ] Add ASSEMBLYAI_API_KEY to backend .env for interview transcription
  - Sign up at https://www.assemblyai.com/
  - Free tier includes 5 hours/month
  - Without key, uses mock transcription for testing

## 📈 Growth & Marketing

### User Acquisition
- [ ] Create demo video showing core features
- [ ] Write blog post: "How AI is Revolutionizing Recruitment"
- [ ] Set up Google Analytics
- [ ] Create LinkedIn company page
- [ ] Reach out to 10 HR professionals for feedback
- [ ] Add "Product Hunt" launch preparation

### SEO & Content
- [ ] Add meta tags to all pages
- [ ] Create sitemap.xml
- [ ] Write 5 keyword-focused landing pages
- [ ] Set up Google Search Console

## 🛠️ Technical Improvements

### Performance
- [ ] Implement caching for common searches
- [ ] Add pagination to resume list (currently loading all)
- [ ] Optimize bundle size (check with `npm run analyze`)
- [ ] Add loading skeletons for better perceived performance

### Features (Next Sprint)
- [x] Email verification for new users - ✅ COMPLETED
- [ ] Password reset functionality
- [ ] User profile completion flow
- [ ] Resume bulk operations UI improvements
- [ ] Advanced search filters UI
- [ ] Export search results to CSV

### Security & Monitoring
- [ ] Add rate limiting (when you have 10+ users)
- [ ] Implement basic usage analytics
- [ ] Set up error tracking (Sentry)
- [ ] Add health check endpoint monitoring
- [ ] Create admin dashboard for user management

## 💼 Business Development

### Revenue (After 100+ Active Users)
- [ ] Track usage patterns to inform pricing
- [ ] Design pricing tiers based on actual usage data
- [ ] Implement Stripe payment integration
- [ ] Create pricing page
- [ ] Add subscription management
- [ ] Grandfather early users with lifetime deals

### Legal/Compliance
- [ ] Register business entity
- [ ] Get business insurance
- [x] Create customer service email - Using promtitude@gmail.com for now
- [x] Add cookie consent functionality - ✅ COMPLETED
- [ ] Create data processing agreement template
- [ ] Set up professional email addresses (@promtitude.com)

## 🐛 Known Issues to Fix

### Bugs
- [x] Google OAuth login - ✅ WORKING in local and production (July 20, 2025)
- [x] LinkedIn OAuth login - ✅ WORKING in local and production (July 21, 2025)
- [ ] Contact form doesn't actually send emails
- [ ] Marketing opt-in checkbox doesn't save preference
- [ ] Password reset link doesn't work

### UX Improvements
- [ ] Add tooltips for complex features
- [ ] Improve error messages
- [ ] Add success notifications after actions
- [ ] Mobile responsive testing and fixes
- [ ] Dark mode inconsistencies

## 📊 Analytics & Tracking

### Setup
- [ ] Implement proper event tracking
- [ ] Create conversion funnel tracking
- [ ] Set up user behavior analytics
- [ ] Create weekly metrics dashboard
- [ ] Define and track KPIs

### Metrics to Track
- [ ] User signups per day
- [ ] Search queries per user
- [ ] Resume uploads per user
- [ ] Feature adoption rates
- [ ] User retention (1, 7, 30 days)

## 🎯 Long-term Vision

### Platform Expansion
- [ ] Mobile app (React Native)
- [ ] API for enterprise customers
- [ ] Webhook integrations
- [ ] ATS integrations (Greenhouse, Lever)
- [ ] Slack bot for notifications

### AI Enhancements
- [ ] Resume scoring algorithm
- [ ] Automated candidate matching
- [ ] Interview scheduling assistant
- [ ] Salary prediction model
- [ ] Skills gap analysis

## 📝 Documentation

### Technical
- [ ] API documentation
- [ ] Deployment guide
- [ ] Contributing guidelines
- [ ] Architecture diagram
- [ ] Database schema documentation

### User-Facing
- [ ] User guide/manual
- [ ] Video tutorials
- [ ] Best practices guide
- [ ] FAQ expansion
- [ ] Integration guides

---

**Last Updated**: July 23, 2025  
**Priority Levels**: 🔴 Critical | 🟡 Important | 🟢 Nice-to-have

## Notes

### Completed Recently
- ✅ Modern registration/login pages with social login UI
- ✅ Google OAuth authentication (fully working in production) - July 20, 2025
- ✅ LinkedIn OAuth authentication (fully working in production) - July 21, 2025
- ✅ Promtitude logo integration across the application - July 21, 2025
- ✅ Dashboard improvements for new user experience - July 21, 2025
  - Profile page creation (fixed 404 error)
  - Empty state for no resumes
  - Welcome section explaining natural language search
  - Resume source hints
  - Interactive resume statistics chart
- ✅ Registration security enhancements - July 21, 2025
  - Google reCAPTCHA v3 integration
  - Email verification system
  - Verification pending and success pages
  - Secure token-based verification flow
- ✅ Chrome Extension submitted to Chrome Web Store - July 21, 2025
- ✅ GDPR compliance (Privacy Policy, Terms, Cookie Consent)
- ✅ AI Outreach Message Generator
- ✅ LinkedIn Chrome Extension (local and prod versions)
- ✅ Basic Analytics Dashboard
- ✅ FAQ Page
- ✅ Contact Page
- ✅ Landing page updates with new features

### Current Focus
Focus on user acquisition and Chrome extension publishing to start building user base. Monitor costs carefully with $20 OpenAI limit.

### Today's Achievements - July 21, 2025
- ✅ Implemented Google reCAPTCHA v3 (invisible bot protection)
- ✅ Built complete email verification system with secure tokens
- ✅ Fixed login to require email verification
- ✅ Set up Gmail SMTP for free email sending (500/day limit)
- ✅ Fixed production database with auto-migration script
- ✅ Submitted Chrome Extension to Chrome Web Store
- ✅ Created professional screenshots and icons for extension
- ✅ Removed debug features from production extension

**Production Status**: All systems operational! Email verification working perfectly.

### Updates - July 22, 2025
- ✅ Updated FAQ Pricing section to reflect free early access model
- ✅ Clarified early user grandfather benefits (lifetime discounts, priority features)
- ✅ Fixed FAQ hosting information (Railway instead of AWS)
- ✅ Corrected GDPR compliance status to be transparent about current state
- ✅ Updated all email addresses to promtitude@gmail.com (contact, FAQ, privacy, terms, brand guide)
- ✅ Implemented interview recording upload feature with transcription
  - Added upload endpoint for audio/video files (up to 500MB)
  - Created transcription service with speaker diarization
  - Built upload UI in interview session page
  - Added automatic speaker role detection (interviewer vs candidate)
- ✅ Implemented flexible interview workflow (Phase 1)
  - Added interview mode selection (In-Person, Virtual, Phone)
  - Separated interview type (mode) from interview category (general, technical, etc)
  - Allow upload recording button for IN_PROGRESS interviews
  - Added "Complete Without Recording" button for flexible interview completion
  - Updated database schema to support both mode and category
  - Added mode-aware UI elements in interview session page
- ✅ Fixed speaker confidence display in transcript analysis
  - Updated transcription service to calculate average confidence per speaker
  - Separated role assignment confidence from transcription confidence
  - Now correctly displays AssemblyAI's actual transcription confidence values
- ✅ Implemented AI transcript analysis with interview scorecard
  - Added automatic Q&A extraction from interview transcripts
  - Created comprehensive scorecard generation with ratings and recommendations
  - Built visual scorecard UI component with skills assessment
  - Added Analysis tab to interview session page
  - Automatic analysis triggers after recording upload
  - Manual analysis available via "Generate Analysis" button
- ✅ Added manual transcript entry for testing (July 22, 2025)
  - Created Manual Entry tab for typing/pasting transcripts
  - Added sample Betty Taylor Frontend Developer interview
  - Enables testing AI analysis without audio recordings
- ✅ Implemented dual-track analysis (Human vs AI)
  - Side-by-side comparison of human ratings and AI analysis
  - Automatic discrepancy detection with alerts
  - Transparency for EU AI Act compliance
  - Helps identify potential interviewer bias
  - Recommended actions based on assessment alignment

### Strategic Decision - July 22, 2025
**Removed 14-day trial language** - Following the successful startup playbook:
- Give users full access for free initially
- Focus on user growth over early monetization
- Learn what features users actually value
- Implement pricing only after product-market fit
- Current approach: "Start free" with no restrictions

This reduces friction and accelerates user acquisition at this critical early stage.

### Updates - July 23, 2025

#### Interview Scorecard Improvements ✅ COMPLETED
- ✅ Fixed scoring scale inconsistency (standardized to 5-point scale)
- ✅ Implemented proper handling for audio mismatch detection
- ✅ Enabled interview results display for human-only assessments (without audio)
- ✅ Fixed manual transcript parsing to handle variable speaker tag formatting
- ✅ Resolved scorecard showing wrong ratings (human vs AI confusion)
- ✅ Fixed duplicate sections in scorecard display
- ✅ Improved AI Insights to show appropriate content based on assessment type
- ✅ Added clear distinction between Human and AI ratings throughout the application

#### Chrome Extension OAuth Authentication ✅ COMPLETED
**Major Feature**: Enable OAuth users (Google/LinkedIn) to use the Chrome extension
- ✅ Implemented Redis-based temporary access code system
  - 6-character alphanumeric codes (excluding confusing characters)
  - One-time use only for security
  - 10-minute expiration
  - Rate limiting (3 attempts per hour)
- ✅ Created extension token service with comprehensive security features
- ✅ Modified login endpoint to accept both passwords and access codes
- ✅ Built dedicated extension-auth page for code generation
  - Visual countdown timer
  - Copy-to-clipboard functionality
  - Clear instructions for users
- ✅ Enhanced profile page with Chrome Extension section
  - Different UI for OAuth vs regular users
  - Direct access to code generation
- ✅ Configured CORS to support Chrome extension origins
  - Added regex pattern for chrome-extension://* URLs
- ✅ Implemented JWT token persistence in extension
  - Stores JWT for 8 days (no need for new codes during this period)
  - Validates token on extension startup
  - Graceful handling of expired tokens
- ✅ Created comprehensive deployment documentation

#### AI Interview Features
- ✅ Verified AI-generated interview questions are unique per session
- ✅ Confirmed job requirements textbox is used by AI for question generation

**Production Deployment**: All OAuth authentication features deployed and working!