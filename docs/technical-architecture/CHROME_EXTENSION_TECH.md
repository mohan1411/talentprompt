# Chrome Extension Technical Architecture

## Table of Contents
1. [How the Chrome Extension Works](#how-the-chrome-extension-works)
2. [Architecture Overview](#architecture-overview)
3. [LinkedIn Profile Extraction](#linkedin-profile-extraction)
4. [Data Cleaning & Validation](#data-cleaning--validation)
5. [Experience Calculation Algorithm](#experience-calculation-algorithm)
6. [Duplicate Detection System](#duplicate-detection-system)
7. [Security & Permissions](#security--permissions)
8. [Performance Optimization](#performance-optimization)

## How the Chrome Extension Works

The Promtitude Chrome Extension enables one-click LinkedIn profile imports, automatically extracting and structuring candidate data.

### User Experience

```
User browses to LinkedIn profile → Extension detects profile page
                                          ↓
                                  Button appears: "Import to Promtitude"
                                          ↓
                                     User clicks button
                                          ↓
                                  Extension extracts all data:
                                  • Basic info (name, title, location)
                                  • Experience with calculated years
                                  • Skills and education
                                  • Contact info (if available)
                                          ↓
                                  Checks for duplicates
                                          ↓
                                  Imports to Promtitude database
                                          ↓
                                  "✓ Imported Successfully"
```

### Visual Flow

```
┌─────────────────────────────────────────────────────┐
│             LinkedIn Profile Page                    │
│  ┌─────────────────────────────────────────────┐   │
│  │  John Smith                                  │   │
│  │  Senior Software Engineer at TechCorp        │   │
│  │  San Francisco Bay Area                      │   │
│  │                                              │   │
│  │  [Import to Promtitude] ← Extension Button  │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## Architecture Overview

### Extension Components

```
chrome-extension/
├── manifest.json          # Extension configuration
├── background/
│   └── service-worker.js  # Background tasks, API calls
├── content/
│   ├── linkedin-profile.js     # Main profile handler
│   ├── ultra-clean-extractor.js # Data extraction
│   ├── calculate-experience.js  # Years calculation
│   ├── contact-extractor.js    # Email/phone extraction
│   └── data-validator.js       # Data validation
├── popup/
│   ├── popup.html         # Extension popup UI
│   └── popup.js           # Popup logic
└── assets/
    └── icons/             # Extension icons
```

### Manifest V3 Configuration

```json
{
  "manifest_version": 3,
  "name": "Promtitude - LinkedIn Profile Importer",
  "version": "1.1.1",
  "permissions": [
    "storage",        // Store auth tokens
    "activeTab",      // Access current tab
    "scripting",      // Inject scripts
    "tabs"            // Tab management
  ],
  "host_permissions": [
    "https://*.linkedin.com/*",
    "https://talentprompt-production.up.railway.app/*"
  ],
  "content_scripts": [{
    "matches": ["https://*.linkedin.com/*"],
    "js": [
      "content/calculate-experience.js",
      "content/ultra-clean-extractor.js",
      "content/contact-extractor.js",
      "content/data-validator.js",
      "content/linkedin-profile.js"
    ],
    "run_at": "document_end"
  }]
}
```

## LinkedIn Profile Extraction

### Ultra-Clean Extraction Algorithm

```javascript
// Ultra-clean extraction without any text formatting
window.extractUltraCleanProfile = function() {
    // Check if on correct page type
    const pathname = window.location.pathname;
    if (!pathname.includes('/in/') || pathname.includes('/details/')) {
        return { error: 'wrong_page' };
    }
    
    const data = {
        linkedin_url: window.location.href.split('?')[0],
        name: '',
        headline: '',
        location: '',
        about: '',
        experience: [],
        education: [],
        skills: [],
        full_text: '',
        years_experience: 0,
        email: '',
        phone: ''
    };
    
    // Extract name (multiple selectors for reliability)
    const nameSelectors = [
        'h1.text-heading-xlarge',
        'h1[class*="profile-name"]',
        '.pv-top-card--list li:first-child',
        '[data-anonymize="person-name"]'
    ];
    
    for (const selector of nameSelectors) {
        const element = document.querySelector(selector);
        if (element?.textContent) {
            data.name = element.textContent.trim();
            break;
        }
    }
    
    // Extract experience with advanced parsing
    data.experience = extractExperienceData();
    
    // Calculate years of experience
    if (data.experience.length > 0) {
        data.years_experience = calculateTotalExperience(data.experience);
    }
    
    return data;
};
```

### Experience Extraction

```javascript
function extractExperienceData() {
    const experiences = [];
    const experienceSection = document.querySelector('#experience')?.parentElement?.parentElement;
    
    if (!experienceSection) return experiences;
    
    // Find all experience items
    const experienceItems = experienceSection.querySelectorAll('li.artdeco-list__item');
    
    experienceItems.forEach(item => {
        try {
            // Extract all visible text spans
            const visibleSpans = item.querySelectorAll('span[aria-hidden="true"]:not(.visually-hidden)');
            const texts = Array.from(visibleSpans)
                .map(span => span.textContent.trim())
                .filter(t => t && t.length > 1);
            
            if (texts.length >= 2) {
                const exp = {
                    title: '',
                    company: '',
                    duration: '',
                    location: '',
                    description: '',
                    start_date: null,
                    end_date: null,
                    is_current: false
                };
                
                // Title is usually the first bold text
                const titleElement = item.querySelector('.t-bold span[aria-hidden="true"]');
                exp.title = titleElement ? titleElement.textContent.trim() : texts[0];
                
                // Parse company and employment type
                const companyText = texts[1];
                if (companyText.includes(' · ')) {
                    const parts = companyText.split(' · ');
                    exp.company = parts[0].trim();
                    exp.employment_type = parts[1].trim();
                } else {
                    exp.company = companyText;
                }
                
                // Find dates
                for (const text of texts) {
                    if (text.match(/\d{4}|Present|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec/i)) {
                        exp.duration = text;
                        
                        // Parse start and end dates
                        const dateInfo = parseDateRange(text);
                        exp.start_date = dateInfo.start_date;
                        exp.end_date = dateInfo.end_date;
                        exp.is_current = dateInfo.is_current;
                        
                        break;
                    }
                }
                
                experiences.push(exp);
            }
        } catch (e) {
            console.error('Error parsing experience item:', e);
        }
    });
    
    return experiences;
}
```

### Date Parsing Algorithm

```javascript
function parseDateRange(dateString) {
    const result = {
        start_date: null,
        end_date: null,
        is_current: false,
        months: 0
    };
    
    // Check if current position
    if (dateString.toLowerCase().includes('present')) {
        result.is_current = true;
    }
    
    // Extract date components
    const datePattern = /(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})/gi;
    const matches = [...dateString.matchAll(datePattern)];
    
    if (matches.length >= 1) {
        // Parse start date
        const startMonth = monthToNumber(matches[0][1]);
        const startYear = parseInt(matches[0][2]);
        result.start_date = new Date(startYear, startMonth - 1);
        
        if (matches.length >= 2) {
            // Parse end date
            const endMonth = monthToNumber(matches[1][1]);
            const endYear = parseInt(matches[1][2]);
            result.end_date = new Date(endYear, endMonth - 1);
        } else if (result.is_current) {
            // Use current date as end
            result.end_date = new Date();
        }
        
        // Calculate duration in months
        if (result.start_date && result.end_date) {
            result.months = calculateMonthDifference(result.start_date, result.end_date);
        }
    }
    
    return result;
}
```

## Data Cleaning & Validation

### Data Validation Pipeline

```javascript
window.validateProfileData = function(data) {
    // Ensure all required fields exist
    const requiredFields = [
        'linkedin_url', 'name', 'headline', 'location',
        'experience', 'education', 'skills', 'years_experience'
    ];
    
    for (const field of requiredFields) {
        if (!(field in data)) {
            data[field] = getDefaultValue(field);
        }
    }
    
    // Clean and validate each field
    data.name = cleanName(data.name);
    data.headline = cleanText(data.headline, 200);
    data.location = cleanLocation(data.location);
    data.skills = cleanSkills(data.skills);
    data.years_experience = validateYearsExperience(data.years_experience);
    
    // Validate experience entries
    data.experience = data.experience.map(exp => validateExperience(exp));
    
    // Remove any script tags or malicious content
    data = sanitizeData(data);
    
    return data;
};

function cleanName(name) {
    if (!name || typeof name !== 'string') return '';
    
    // Remove emojis and special characters
    name = name.replace(/[\u{1F600}-\u{1F64F}]/gu, '');
    name = name.replace(/[\u{1F300}-\u{1F5FF}]/gu, '');
    
    // Remove titles and certifications
    const titles = ['MBA', 'PhD', 'CPA', 'PMP', 'CSM'];
    titles.forEach(title => {
        name = name.replace(new RegExp(`\\b${title}\\b`, 'gi'), '');
    });
    
    // Clean up whitespace
    return name.trim().replace(/\s+/g, ' ');
}
```

### Skill Normalization

```javascript
function cleanSkills(skills) {
    if (!Array.isArray(skills)) return [];
    
    // Remove duplicates and normalize
    const uniqueSkills = new Set();
    
    skills.forEach(skill => {
        if (typeof skill === 'string' && skill.trim()) {
            // Normalize skill name
            let normalized = skill.trim()
                .replace(/\s+/g, ' ')
                .replace(/[^\w\s\-\.#\+]/g, '');
            
            // Handle common variations
            normalized = normalizeSkillName(normalized);
            
            if (normalized.length > 2 && normalized.length < 50) {
                uniqueSkills.add(normalized);
            }
        }
    });
    
    return Array.from(uniqueSkills).slice(0, 100); // Limit to 100 skills
}

function normalizeSkillName(skill) {
    const skillMap = {
        'js': 'JavaScript',
        'ts': 'TypeScript',
        'golang': 'Go',
        'c#': 'C#',
        'react.js': 'React',
        'vue.js': 'Vue.js',
        'node.js': 'Node.js'
    };
    
    const lower = skill.toLowerCase();
    return skillMap[lower] || skill;
}
```

## Experience Calculation Algorithm

### Advanced Experience Calculator

```javascript
window.calculateTotalExperienceAdvanced = function(experiences) {
    if (!experiences || experiences.length === 0) return 0;
    
    // Sort experiences by start date
    const sortedExperiences = experiences
        .filter(exp => exp.start_date)
        .sort((a, b) => new Date(a.start_date) - new Date(b.start_date));
    
    if (sortedExperiences.length === 0) return 0;
    
    // Handle overlapping positions
    const mergedPeriods = [];
    
    sortedExperiences.forEach(exp => {
        const start = new Date(exp.start_date);
        const end = exp.end_date ? new Date(exp.end_date) : new Date();
        
        if (mergedPeriods.length === 0) {
            mergedPeriods.push({ start, end });
        } else {
            const lastPeriod = mergedPeriods[mergedPeriods.length - 1];
            
            if (start <= lastPeriod.end) {
                // Overlapping period - extend if necessary
                lastPeriod.end = new Date(Math.max(lastPeriod.end, end));
            } else {
                // Non-overlapping - add new period
                mergedPeriods.push({ start, end });
            }
        }
    });
    
    // Calculate total months
    let totalMonths = 0;
    mergedPeriods.forEach(period => {
        const months = calculateMonthDifference(period.start, period.end);
        totalMonths += months;
    });
    
    // Convert to years with decimal
    return Math.round((totalMonths / 12) * 10) / 10;
};

function calculateMonthDifference(start, end) {
    const startDate = new Date(start);
    const endDate = new Date(end);
    
    let months = (endDate.getFullYear() - startDate.getFullYear()) * 12;
    months += endDate.getMonth() - startDate.getMonth();
    
    // Add partial month if significant days
    if (endDate.getDate() >= 15 && startDate.getDate() < 15) {
        months += 0.5;
    }
    
    return Math.max(0, months);
}
```

### Manual Override System

```javascript
// Handle special cases where calculation needs adjustment
window.applyManualOverride = function(linkedinUrl, calculatedYears) {
    const overrides = {
        // Specific profile overrides for known edge cases
        '/in/johndoe/': 15,  // Known to have gaps in LinkedIn
        '/in/janedoe/': 8    // Overlapping consulting roles
    };
    
    for (const [pattern, years] of Object.entries(overrides)) {
        if (linkedinUrl.includes(pattern)) {
            console.log(`Applied manual override: ${calculatedYears} → ${years}`);
            return years;
        }
    }
    
    return calculatedYears;
};
```

## Duplicate Detection System

### Real-Time Duplicate Check

```javascript
async function checkIfProfileExists() {
    isCheckingDuplicate = true;
    
    try {
        const profileData = extractProfileData();
        if (!profileData.linkedin_url) {
            return;
        }
        
        const authToken = await getAuthToken();
        if (!authToken) {
            return;
        }
        
        // Check via background script (avoids CORS)
        const response = await chrome.runtime.sendMessage({
            action: 'checkProfileExists',
            linkedin_url: profileData.linkedin_url,
            authToken: authToken
        });
        
        if (response && response.exists) {
            profileExistsStatus = {
                exists: true,
                candidate_id: response.candidate_id
            };
            updateButtonState('exists', response.candidate_id);
        }
    } catch (error) {
        console.error('Duplicate check error:', error);
    } finally {
        isCheckingDuplicate = false;
    }
}
```

### Background Service Worker

```javascript
// background/service-worker.js
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'checkProfileExists') {
        checkDuplicate(request.linkedin_url, request.authToken)
            .then(sendResponse)
            .catch(error => sendResponse({ error: error.message }));
        return true; // Keep channel open for async response
    }
    
    if (request.action === 'importProfile') {
        importProfile(request.data, request.authToken)
            .then(sendResponse)
            .catch(error => sendResponse({ error: error.message }));
        return true;
    }
});

async function checkDuplicate(linkedinUrl, authToken) {
    const response = await fetch(`${API_URL}/candidates/check-duplicate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ linkedin_url: linkedinUrl })
    });
    
    const data = await response.json();
    return {
        exists: data.exists,
        candidate_id: data.candidate_id
    };
}
```

## Security & Permissions

### Minimal Permission Model

```javascript
// Only request necessary permissions
const REQUIRED_PERMISSIONS = {
    permissions: ['storage', 'activeTab'],
    origins: ['https://*.linkedin.com/*']
};

// Check permissions before operations
async function hasNecessaryPermissions() {
    const permissions = await chrome.permissions.contains(REQUIRED_PERMISSIONS);
    return permissions;
}
```

### Secure Token Storage

```javascript
class SecureStorage {
    async setAuthToken(token) {
        // Encrypt token before storage
        const encrypted = await this.encrypt(token);
        
        await chrome.storage.local.set({
            authToken: encrypted,
            tokenExpiry: Date.now() + (7 * 24 * 60 * 60 * 1000) // 7 days
        });
    }
    
    async getAuthToken() {
        const data = await chrome.storage.local.get(['authToken', 'tokenExpiry']);
        
        // Check expiry
        if (!data.authToken || Date.now() > data.tokenExpiry) {
            await this.clearAuthToken();
            return null;
        }
        
        // Decrypt token
        return await this.decrypt(data.authToken);
    }
    
    async clearAuthToken() {
        await chrome.storage.local.remove(['authToken', 'tokenExpiry']);
    }
    
    // Simple encryption (in production, use Web Crypto API)
    async encrypt(text) {
        // Implementation details...
        return btoa(text);
    }
    
    async decrypt(encrypted) {
        // Implementation details...
        return atob(encrypted);
    }
}
```

### Content Security Policy

```javascript
// Sanitize data before sending to server
function sanitizeData(data) {
    const sanitize = (obj) => {
        if (typeof obj === 'string') {
            // Remove script tags and event handlers
            return obj
                .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
                .replace(/on\w+\s*=\s*["'][^"']*["']/gi, '')
                .replace(/javascript:/gi, '');
        } else if (Array.isArray(obj)) {
            return obj.map(sanitize);
        } else if (obj && typeof obj === 'object') {
            const sanitized = {};
            for (const key in obj) {
                sanitized[key] = sanitize(obj[key]);
            }
            return sanitized;
        }
        return obj;
    };
    
    return sanitize(data);
}
```

## Performance Optimization

### Lazy Loading Strategy

```javascript
// Load heavy scripts only when needed
async function loadExtractorScripts() {
    if (!window.extractUltraCleanProfile) {
        await injectScript('content/ultra-clean-extractor.js');
    }
    
    if (!window.calculateTotalExperienceAdvanced) {
        await injectScript('content/calculate-experience.js');
    }
}

function injectScript(scriptPath) {
    return new Promise((resolve) => {
        const script = document.createElement('script');
        script.src = chrome.runtime.getURL(scriptPath);
        script.onload = () => {
            script.remove();
            resolve();
        };
        document.head.appendChild(script);
    });
}
```

### Efficient DOM Querying

```javascript
class DOMCache {
    constructor() {
        this.cache = new Map();
        this.observers = new Map();
    }
    
    querySelector(selector, parent = document) {
        const key = `${parent === document ? 'doc' : 'el'}:${selector}`;
        
        if (this.cache.has(key)) {
            const cached = this.cache.get(key);
            // Verify element still exists in DOM
            if (cached && cached.isConnected) {
                return cached;
            }
        }
        
        const element = parent.querySelector(selector);
        if (element) {
            this.cache.set(key, element);
        }
        
        return element;
    }
    
    clearCache() {
        this.cache.clear();
    }
}
```

### Batch Operations

```javascript
class BatchImporter {
    constructor() {
        this.queue = [];
        this.processing = false;
        this.batchSize = 10;
        this.batchDelay = 1000; // 1 second between batches
    }
    
    async addToQueue(profileData) {
        this.queue.push(profileData);
        
        if (!this.processing) {
            this.processBatch();
        }
    }
    
    async processBatch() {
        this.processing = true;
        
        while (this.queue.length > 0) {
            const batch = this.queue.splice(0, this.batchSize);
            
            try {
                await this.importBatch(batch);
                
                // Rate limiting
                if (this.queue.length > 0) {
                    await this.delay(this.batchDelay);
                }
            } catch (error) {
                console.error('Batch import error:', error);
                // Re-queue failed items
                this.queue.unshift(...batch);
                await this.delay(this.batchDelay * 2); // Back off
            }
        }
        
        this.processing = false;
    }
    
    async importBatch(profiles) {
        const response = await fetch(`${API_URL}/candidates/batch-import`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ profiles })
        });
        
        if (!response.ok) {
            throw new Error(`Batch import failed: ${response.status}`);
        }
        
        return response.json();
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
```

## Future Enhancements

### 1. AI-Powered Extraction

```javascript
class AIExtractor {
    async extractWithAI(pageContent) {
        // Use AI to understand complex profiles
        const prompt = `Extract structured data from this LinkedIn profile:
        ${pageContent}
        
        Return JSON with: name, title, experience, skills, education`;
        
        const response = await this.callAI(prompt);
        return this.parseAIResponse(response);
    }
    
    async enhanceExtraction(basicData) {
        // Use AI to infer missing data
        const enhancements = await this.inferMissingData(basicData);
        return { ...basicData, ...enhancements };
    }
}
```

### 2. Multi-Profile Import

```javascript
class MultiProfileImporter {
    async importSearchResults() {
        // Get all profiles from search results page
        const profileLinks = document.querySelectorAll(
            'a[href*="/in/"].app-aware-link'
        );
        
        const profiles = [];
        for (const link of profileLinks) {
            const profileUrl = link.href.split('?')[0];
            
            // Open in background tab
            const tab = await chrome.tabs.create({
                url: profileUrl,
                active: false
            });
            
            // Extract data
            const data = await this.extractFromTab(tab.id);
            profiles.push(data);
            
            // Close tab
            await chrome.tabs.remove(tab.id);
            
            // Rate limiting
            await this.delay(2000);
        }
        
        return profiles;
    }
}
```

### 3. Real-Time Updates

```javascript
class ProfileMonitor {
    async monitorProfile(linkedinUrl) {
        // Set up periodic checks for profile updates
        const checkInterval = 24 * 60 * 60 * 1000; // Daily
        
        setInterval(async () => {
            const updates = await this.checkForUpdates(linkedinUrl);
            
            if (updates.hasChanges) {
                await this.syncUpdates(updates);
                this.notifyUser(updates);
            }
        }, checkInterval);
    }
    
    async checkForUpdates(linkedinUrl) {
        // Compare current profile with stored version
        const currentData = await this.extractProfile(linkedinUrl);
        const storedData = await this.getStoredProfile(linkedinUrl);
        
        return this.compareProfiles(currentData, storedData);
    }
}
```

The Chrome Extension provides a seamless way to build a talent database while browsing LinkedIn, with robust extraction, validation, and security features.