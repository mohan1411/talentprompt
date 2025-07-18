// Service worker for Promtitude Chrome Extension

console.log('Promtitude service worker loaded');

// API configuration
const API_BASE_URL = 'https://talentprompt-production.up.railway.app/api/v1';
const DEV_API_URL = 'http://localhost:8000/api/v1';

// Use production backend
const API_URL = API_BASE_URL;

// Queue processor class (integrated directly to avoid importScripts issues)
class QueueProcessor {
  constructor() {
    this.isProcessing = false;
    this.shouldStop = false;
    this.currentTab = null;
  }

  async start() {
    if (this.isProcessing) {
      console.log('Queue processor is already running');
      return;
    }
    
    this.isProcessing = true;
    this.shouldStop = false;
    
    console.log('Queue processor started');
    
    try {
      await this.processQueue();
    } catch (error) {
      console.error('Queue processing error:', error);
      throw error;  // Re-throw to let caller handle it
    } finally {
      this.isProcessing = false;
      this.cleanup();
    }
  }

  stop() {
    this.shouldStop = true;
  }

  async processQueue() {
    const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
    const pendingItems = linkedinImportQueue.filter(item => item.status === 'pending');
    
    if (pendingItems.length === 0) {
      console.log('No pending items to process');
      return;
    }

    // Create a hidden processing tab
    let processingTab;
    try {
      processingTab = await this.createHiddenTab();
      this.currentTab = processingTab;
    } catch (error) {
      console.error('Failed to create processing tab:', error);
      throw new Error('Failed to create processing tab: ' + error.message);
    }

    for (const item of pendingItems) {
      if (this.shouldStop) break;

      try {
        // Update status
        await this.updateItemStatus(item.id, 'processing');
        
        // Navigate to profile
        await chrome.tabs.update(processingTab.id, { url: item.profileUrl });
        
        // Wait for page to load
        await this.waitForTabComplete(processingTab.id);
        
        // Additional wait for dynamic content
        await this.delay(3000);
        
        // Extract profile data
        const profileData = await this.extractProfileData(processingTab.id);
        
        if (!profileData) {
          throw new Error('Failed to extract profile data');
        }
        
        // Import profile
        const result = await handleImportProfile(profileData, (await chrome.storage.local.get('authToken')).authToken);
        
        // Update status
        await this.updateItemStatus(item.id, 'completed');
        
        // Send progress update
        await this.sendProgressUpdate();
        
      } catch (error) {
        console.error(`Failed to process ${item.profileUrl}:`, error);
        await this.updateItemStatus(item.id, 'failed', error.message);
      }
      
      // Delay between profiles
      if (!this.shouldStop) {
        const delay = 3000 + Math.random() * 3000;
        await this.delay(delay);
      }
    }
    
    // Close the processing tab
    if (processingTab) {
      chrome.tabs.remove(processingTab.id);
    }
  }

  async createHiddenTab() {
    try {
      // Create a tab in the background (not active)
      const tab = await chrome.tabs.create({
        url: 'about:blank',
        active: false,
        pinned: true  // Make it pinned to reduce visual impact
      });
      
      console.log('Created processing tab:', tab.id);
      return tab;
    } catch (error) {
      console.error('Failed to create pinned tab:', error);
      
      // Fallback: Create a normal background tab
      try {
        const tab = await chrome.tabs.create({
          url: 'about:blank',
          active: false
        });
        console.log('Created fallback processing tab:', tab.id);
        return tab;
      } catch (fallbackError) {
        console.error('All tab creation methods failed:', fallbackError);
        throw new Error('Unable to create processing tab. Please ensure you have at least one Chrome window open.');
      }
    }
  }

  async waitForTabComplete(tabId) {
    return new Promise((resolve) => {
      const listener = (updatedTabId, changeInfo) => {
        if (updatedTabId === tabId && changeInfo.status === 'complete') {
          chrome.tabs.onUpdated.removeListener(listener);
          resolve();
        }
      };
      chrome.tabs.onUpdated.addListener(listener);
    });
  }

  async extractProfileData(tabId) {
    try {
      const [result] = await chrome.scripting.executeScript({
        target: { tabId },
        func: () => {
          console.log('Extracting profile data (improved version) from:', window.location.href);
          
          const data = {
            linkedin_url: window.location.href.split('?')[0],
            name: '',
            headline: '',
            location: '',
            about: '',
            experience: [],
            education: [],
            skills: [],
            email: null,
            phone: null,
            years_experience: null
          };
          
          // Helper function to get text content safely
          const getText = (el) => el?.textContent?.trim() || '';
          
          // Extract name - updated selectors
          const nameSelectors = [
            'h1.text-heading-xlarge',
            '.pv-text-details__left-panel h1',
            'h1[class*="inline t-24"]',
            'h1'
          ];
          for (const selector of nameSelectors) {
            const nameEl = document.querySelector(selector);
            if (nameEl && getText(nameEl)) {
              data.name = getText(nameEl);
              break;
            }
          }
          
          // Extract headline - try multiple selectors
          const headlineSelectors = [
            '.text-body-medium.break-words',
            '.pv-text-details__left-panel .text-body-medium',
            'div[data-generated-suggestion-target] .text-body-medium'
          ];
          for (const selector of headlineSelectors) {
            const headlineEl = document.querySelector(selector);
            if (headlineEl && headlineEl.textContent.trim()) {
              data.headline = headlineEl.textContent.trim();
              break;
            }
          }
          
          // Extract location - try multiple selectors
          const locationSelectors = [
            '.text-body-small.inline.t-black--light.break-words',
            '.pv-text-details__left-panel .text-body-small',
            'span.text-body-small.inline'
          ];
          for (const selector of locationSelectors) {
            const locationEl = document.querySelector(selector);
            if (locationEl && locationEl.textContent.trim()) {
              data.location = locationEl.textContent.trim();
              break;
            }
          }
          
          // Extract about
          const aboutSection = Array.from(document.querySelectorAll('section')).find(s => 
            s.querySelector('h2')?.textContent.includes('About')
          );
          if (aboutSection) {
            const aboutSelectors = [
              '.inline-show-more-text__text',
              '[class*="line-clamp"]',
              '.pv-shared-text-with-see-more span[aria-hidden="true"]'
            ];
            for (const selector of aboutSelectors) {
              const aboutText = aboutSection.querySelector(selector);
              if (aboutText && aboutText.textContent.trim()) {
                data.about = aboutText.textContent.trim();
                break;
              }
            }
          }
          
          // Extract experience with more detail
          const experienceSection = Array.from(document.querySelectorAll('section')).find(s => 
            s.querySelector('h2')?.textContent.includes('Experience')
          );
          if (experienceSection) {
            const experienceSelectors = [
              'li.artdeco-list__item',
              '.experience-item',
              'div.pvs-list__item--line-separated',
              'li.pvs-list__paged-list-item'
            ];
            
            for (const selector of experienceSelectors) {
              const items = experienceSection.querySelectorAll(selector);
              if (items.length > 0) {
                items.forEach(item => {
                  const exp = {
                    title: '',
                    company: '',
                    dates: '',
                    location: '',
                    description: ''
                  };
                  
                  // Title
                  const titleSelectors = [
                    '[data-field="experience_title"]',
                    '.t-bold span[aria-hidden="true"]',
                    '.display-flex.align-items-center span[aria-hidden="true"]'
                  ];
                  for (const sel of titleSelectors) {
                    const el = item.querySelector(sel);
                    if (el && el.textContent.trim()) {
                      exp.title = el.textContent.trim();
                      break;
                    }
                  }
                  
                  // Company
                  const companySelectors = [
                    '[data-field="experience_company_name"]',
                    '.t-14.t-normal:not(.t-black--light) span[aria-hidden="true"]',
                    'span.t-14.t-normal span[aria-hidden="true"]'
                  ];
                  for (const sel of companySelectors) {
                    const el = item.querySelector(sel);
                    if (el && el.textContent.trim() && !el.textContent.includes('·')) {
                      exp.company = el.textContent.trim().split(' · ')[0];
                      break;
                    }
                  }
                  
                  // Dates and Duration - Look for both date range and duration
                  const dateSelectors = [
                    '.t-14.t-normal.t-black--light span[aria-hidden="true"]',
                    '.pvs-entity__caption-wrapper span[aria-hidden="true"]',
                    'span.t-14.t-normal.t-black--light span[aria-hidden="true"]',
                    '.pvs-list__item--no-padding-in-columns .t-14.t-normal span[aria-hidden="true"]'
                  ];
                  
                  // Collect all date-like texts
                  const dateTexts = [];
                  for (const sel of dateSelectors) {
                    item.querySelectorAll(sel).forEach(el => {
                      const text = el.textContent.trim();
                      if (text && (text.includes(' - ') || text.includes(' – ') || text.includes(' yr') || text.includes(' mo'))) {
                        dateTexts.push(text);
                      }
                    });
                  }
                  
                  // Find the most complete date string (with duration)
                  exp.dates = dateTexts.find(t => t.includes('·')) || dateTexts[0] || '';
                  
                  // Also try to find duration separately if not in dates
                  if (!exp.dates.includes('·')) {
                    const durationText = dateTexts.find(t => t.match(/\d+\s*yr|\d+\s*mo/));
                    if (durationText && exp.dates) {
                      exp.dates = exp.dates + ' · ' + durationText;
                    }
                  }
                  
                  if (exp.title || exp.company) {
                    data.experience.push(exp);
                    console.log(`Extracted experience: ${exp.title} at ${exp.company}, dates: ${exp.dates}`);
                  }
                });
                break;
              }
            }
          }
          
          // Extract skills - improved version
          const skillsSection = Array.from(document.querySelectorAll('section')).find(s => {
            const h2 = s.querySelector('h2');
            return h2 && h2.textContent.toLowerCase().includes('skill');
          });
          
          if (skillsSection) {
            const skillElements = skillsSection.querySelectorAll('.pvs-list__paged-list-item, li.pvs-list__item--line-separated, .pvs-list__item--no-padding-in-columns');
            const skills = new Set();
            
            skillElements.forEach(item => {
              // Try multiple selectors for skill names
              const skillSelectors = [
                'div[data-field="skill_card_skill_topic"] span[aria-hidden="true"]',
                '.t-bold span[aria-hidden="true"]:first-of-type',
                '.skill-item__title',
                '.pvs-entity__text-container span[aria-hidden="true"]:first-of-type',
                '.pvs-list__item--no-padding-in-columns span[aria-hidden="true"]:first-of-type'
              ];
              
              for (const selector of skillSelectors) {
                const skillEl = item.querySelector(selector);
                if (skillEl) {
                  const skillText = skillEl.textContent.trim();
                  if (skillText && !skillText.includes('endorsement') && skillText.length < 50 && !skillText.includes('·')) {
                    skills.add(skillText);
                    break;
                  }
                }
              }
            });
            
            data.skills = Array.from(skills);
          }
          
          // If no skills found in skills section, try to find "Top Skills" in other locations
          if (data.skills.length === 0) {
            const topSkillsSelectors = [
              '.pv-skill-categories-section .pv-skill-category-entity__name span',
              '[class*="skill"] .t-bold span[aria-hidden="true"]',
              '.pv-top-card-v3-section__list-item span[aria-hidden="true"]'
            ];
            
            const skills = new Set();
            for (const selector of topSkillsSelectors) {
              document.querySelectorAll(selector).forEach(el => {
                const text = el.textContent.trim();
                if (text && text.length < 50 && !text.includes(':') && !text.includes('·')) {
                  skills.add(text);
                }
              });
            }
            data.skills = Array.from(skills).slice(0, 15); // Limit to top 15
          }
          
          // Calculate years of experience - improved version
          if (data.experience.length > 0) {
            let totalMonths = 0;
            let calculatedFromDuration = false;
            
            // First try to calculate from duration strings
            data.experience.forEach(exp => {
              // Look for duration in the dates field (e.g., "Jan 2020 - Present · 3 yrs 2 mos")
              if (exp.dates && exp.dates.includes('·')) {
                const parts = exp.dates.split('·');
                if (parts.length > 1) {
                  const duration = parts[1].trim();
                  const years = duration.match(/(\d+)\s*yr/);
                  const months = duration.match(/(\d+)\s*mo/);
                  
                  let expMonths = 0;
                  if (years) {
                    expMonths += parseInt(years[1]) * 12;
                    calculatedFromDuration = true;
                  }
                  if (months) {
                    expMonths += parseInt(months[1]);
                    calculatedFromDuration = true;
                  }
                  
                  if (expMonths > 0) {
                    totalMonths += expMonths;
                    console.log(`Experience: ${exp.title} at ${exp.company} - Duration: ${duration} = ${expMonths} months`);
                  }
                }
              }
            });
            
            if (calculatedFromDuration) {
              console.log(`Total experience calculated from durations: ${totalMonths} months = ${Math.round(totalMonths / 12)} years`);
            }
            
            // If we couldn't calculate from duration, try date parsing
            if (!calculatedFromDuration && totalMonths === 0) {
              const experienceDates = [];
              
              data.experience.forEach(exp => {
                if (exp.dates && exp.dates.includes(' - ')) {
                  const dateParts = exp.dates.split(' - ')[0].split('·')[0].trim();
                  const endPart = exp.dates.split(' - ')[1].split('·')[0].trim();
                  
                  try {
                    // Parse start date
                    const startDate = new Date(dateParts);
                    const endDate = endPart.toLowerCase() === 'present' ? new Date() : new Date(endPart);
                    
                    if (!isNaN(startDate.getTime()) && !isNaN(endDate.getTime())) {
                      experienceDates.push({ start: startDate, end: endDate });
                    }
                  } catch (e) {
                    console.log('Error parsing dates:', e);
                  }
                }
              });
              
              // Calculate total experience from parsed dates
              if (experienceDates.length > 0) {
                // Sort by start date
                experienceDates.sort((a, b) => a.start - b.start);
                
                // Find earliest start and latest end
                const earliestStart = experienceDates[0].start;
                const latestEnd = experienceDates.reduce((latest, exp) => 
                  exp.end > latest ? exp.end : latest, experienceDates[0].end);
                
                totalMonths = Math.floor((latestEnd - earliestStart) / (1000 * 60 * 60 * 24 * 30.44));
              }
            }
            
            // Set years of experience (must be integer for backend)
            if (totalMonths > 0) {
              // Round to nearest integer
              data.years_experience = Math.round(totalMonths / 12);
            } else {
              // Default to 1 year if we can't calculate
              data.years_experience = 1;
            }
          }
          
          // Additional experience extraction for grouped experiences
          // LinkedIn sometimes shows total company duration separately
          const allExpTexts = experienceSection ? Array.from(experienceSection.querySelectorAll('span[aria-hidden="true"]')).map(s => s.textContent.trim()) : [];
          const additionalDurations = allExpTexts.filter(text => 
            text.match(/^\d+\s*yrs?\s*\d*\s*mos?$/) && 
            !data.experience.some(exp => exp.dates && exp.dates.includes(text))
          );
          
          if (additionalDurations.length > 0) {
            console.log('Found additional duration texts that might be totals:', additionalDurations);
          }
          
          // Log extraction results for debugging
          console.log('Extracted profile data:', {
            name: data.name,
            headline: data.headline,
            location: data.location,
            'skills_count': data.skills.length,
            'skills': data.skills,
            'experience_count': data.experience.length,
            'experience_details': data.experience.map(e => ({ title: e.title, company: e.company, dates: e.dates })),
            'years_experience': data.years_experience,
            'linkedin_url': data.linkedin_url
          });
          
          // Add warning if no skills found
          if (data.skills.length === 0) {
            console.warn('No skills were extracted from the profile. The skills section might have a different structure.');
          }
          
          return data;
        }
      });
      
      return result.result;
    } catch (error) {
      console.error('Failed to extract profile data:', error);
      return null;
    }
  }

  async updateItemStatus(itemId, status, error = null) {
    const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
    
    const item = linkedinImportQueue.find(i => i.id === itemId);
    if (item) {
      item.status = status;
      if (error) {
        item.error = error;
      }
      item.updatedAt = new Date().toISOString();
      
      await chrome.storage.local.set({ linkedinImportQueue });
    }
  }

  async sendProgressUpdate() {
    const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
    
    const stats = {
      pending: 0,
      processing: 0,
      completed: 0,
      failed: 0
    };
    
    linkedinImportQueue.forEach(item => {
      stats[item.status] = (stats[item.status] || 0) + 1;
    });
    
    // Send message to popup if it's open
    chrome.runtime.sendMessage({
      action: 'queueProgress',
      stats: stats
    }).catch(() => {
      // Popup might not be open, ignore error
    });
    
    // Update badge
    chrome.action.setBadgeText({ 
      text: stats.pending > 0 ? stats.pending.toString() : '' 
    });
  }

  async cleanup() {
    // Close any tabs we created
    if (this.currentTab) {
      try {
        await chrome.tabs.remove(this.currentTab.id);
      } catch (e) {
        // Tab might already be closed
      }
    }
    
    // Close any minimized windows we created
    const windows = await chrome.windows.getAll();
    for (const window of windows) {
      if (window.state === 'minimized' && window.tabs.length === 1 && 
          window.tabs[0].url === 'about:blank') {
        try {
          await chrome.windows.remove(window.id);
        } catch (e) {
          // Window might already be closed
        }
      }
    }
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

const queueProcessor = new QueueProcessor();

// Handle extension installation
chrome.runtime.onInstalled.addListener((details) => {
  console.log('Promtitude LinkedIn Integration installed');
  
  if (details.reason === 'install') {
    // Initialize storage
    chrome.storage.local.set({
      linkedinImportQueue: [],
      importStats: {
        total: 0,
        completed: 0,
        failed: 0
      }
    });
  }
  
  // Initialize badge
  updateBadgeFromStorage();
});

// Message handler for communication with popup and content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Received message:', request);
  
  if (request.action === 'importProfile') {
    // Handle the API request in the background script to avoid CORS issues
    handleImportProfile(request.data, request.authToken)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Keep the message channel open for async response
  }
  
  if (request.action === 'extractAndImportCurrentProfile') {
    // Extract full profile data from current tab and import
    handleExtractAndImportCurrentProfile(request.authToken, sender.tab?.id)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  
  if (request.action === 'importFromQueue') {
    // Import profile from queue (used by queue processor)
    handleImportProfile(request.data, request.authToken)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
  
  if (request.action === 'checkProfileExists') {
    checkProfileExists(request.linkedin_url, request.authToken)
      .then(result => sendResponse(result))
      .catch(error => sendResponse({ exists: false, error: error.message }));
    return true;
  }
  
  if (request.action === 'updateQueueBadge') {
    const count = request.count || 0;
    
    if (count > 0) {
      chrome.action.setBadgeText({ text: count.toString() });
      chrome.action.setBadgeBackgroundColor({ color: '#0a66c2' });
    } else {
      chrome.action.setBadgeText({ text: '' });
    }
    
    sendResponse({ success: true });
    return true;
  }
  
  if (request.action === 'openQueueManager') {
    // Open the extension popup or a dedicated queue management page
    chrome.action.openPopup();
    sendResponse({ success: true });
    return true;
  }
  
  if (request.action === 'getQueueStatus') {
    // Forward to content script to get queue status
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, request, (response) => {
          sendResponse(response);
        });
      }
    });
    return true;
  }
  
  if (request.action === 'startQueueProcessing') {
    console.log('Received startQueueProcessing request');
    queueProcessor.start()
      .then(() => {
        console.log('Queue processing started successfully');
        sendResponse({ success: true });
      })
      .catch(error => {
        console.error('Failed to start queue processing:', error);
        sendResponse({ success: false, error: error.message || 'Failed to start processing' });
      });
    return true;
  }
  
  if (request.action === 'stopQueueProcessing') {
    queueProcessor.stop();
    sendResponse({ success: true });
    return true;
  }
  
  if (request.action === 'getProcessingStatus') {
    sendResponse({ 
      isProcessing: queueProcessor.isProcessing,
      success: true 
    });
    return true;
  }
  
  if (request.action === 'addToQueue') {
    console.log('Received addToQueue request with profiles:', request.profiles);
    handleAddToQueue(request.profiles)
      .then(result => {
        console.log('AddToQueue success:', result);
        sendResponse(result);
      })
      .catch(error => {
        console.error('AddToQueue error:', error);
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }
  
  // Echo back for other messages
  sendResponse({ received: true, action: request.action });
  return true;
});

// Import profile to backend
async function handleImportProfile(profileData, authToken) {
  console.log('Background script importing profile...');
  console.log('Profile data to import:', profileData);
  
  if (!authToken) {
    throw new Error('Not authenticated');
  }
  
  // Validate profile data
  if (!profileData.linkedin_url) {
    throw new Error('Missing LinkedIn URL');
  }
  
  if (!profileData.name && !profileData.headline) {
    throw new Error('Unable to extract profile information. Please ensure you are on a LinkedIn profile page.');
  }
  
  // Use the simple import endpoint to avoid async issues
  const url = `${API_URL}/linkedin-fix/simple-import`;
  console.log('Making request to:', url);
  console.log('Auth token present:', !!authToken);
  console.log('Request body:', JSON.stringify(profileData, null, 2));
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(profileData)
    });
    
    console.log('Response status:', response.status);
    console.log('Response status text:', response.statusText);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Error response body:', errorText);
      console.error('Response headers:', response.headers);
      
      let errorMessage = `Import failed: ${response.statusText}`;
      
      // Handle specific error codes
      if (response.status === 404) {
        errorMessage = 'Import endpoint not found. Please check if the backend is running.';
      } else if (response.status === 401) {
        errorMessage = 'Authentication failed. Please login again.';
      } else if (response.status === 422) {
        errorMessage = 'Invalid profile data. Please check if all required fields are present.';
      }
      
      try {
        const error = JSON.parse(errorText);
        if (error.detail) {
          if (typeof error.detail === 'string') {
            errorMessage = error.detail;
          } else if (Array.isArray(error.detail)) {
            errorMessage = error.detail.map(e => e.msg || e.message).join(', ');
          }
        }
        console.error('Parsed error:', error);
      } catch (e) {
        // If error text is not JSON, use it as is
        if (errorText && errorText.length < 200) {
          errorMessage = errorText;
        }
      }
      throw new Error(errorMessage);
    }
    
    const result = await response.json();
    console.log('Import successful:', result);
    return result;
  } catch (error) {
    console.error('Fetch error:', error);
    if (error.message.includes('Failed to fetch')) {
      throw new Error('Unable to connect to backend. Please ensure the backend is running.');
    }
    throw error;
  }
}

// Check if profile exists
async function checkProfileExists(linkedinUrl, authToken) {
  if (!authToken) {
    return { exists: false };
  }
  
  const url = `${API_URL}/linkedin/check-exists`;
  console.log('Checking if profile exists:', linkedinUrl);
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ linkedin_url: linkedinUrl })
    });
    
    if (response.ok) {
      const data = await response.json();
      return data;
    }
    
    return { exists: false };
  } catch (error) {
    console.error('Error checking profile existence:', error);
    return { exists: false };
  }
}

// Handle adding profiles to queue
async function handleAddToQueue(profiles) {
  try {
    if (!profiles || !Array.isArray(profiles)) {
      throw new Error('Invalid profiles data');
    }
    
    const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
    
    let addedCount = 0;
    
    profiles.forEach(profile => {
      // Validate profile data
      if (!profile.profileUrl || !profile.profileName) {
        console.warn('Skipping invalid profile:', profile);
        return;
      }
      
      // Check if profile already exists in queue
      if (!linkedinImportQueue.some(item => item.profileUrl === profile.profileUrl)) {
        linkedinImportQueue.push({
          id: Date.now() + '_' + Math.random(),
          profileUrl: profile.profileUrl,
          profileName: profile.profileName,
          status: 'pending',
          addedAt: new Date().toISOString()
        });
        addedCount++;
      }
    });
    
    // Save updated queue
    await chrome.storage.local.set({ linkedinImportQueue });
    
    // Update badge
    const pendingCount = linkedinImportQueue.filter(item => item.status === 'pending').length;
    updateBadgeFromStorage();
    
    return {
      success: true,
      addedCount: addedCount,
      pendingCount: pendingCount
    };
  } catch (error) {
    console.error('Error adding to queue:', error);
    throw error;
  }
}

// Extract and import current profile
async function handleExtractAndImportCurrentProfile(authToken, tabId) {
  try {
    console.log('Extracting and importing current profile');
    
    // Get the active tab if not provided
    if (!tabId) {
      const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!activeTab) {
        throw new Error('No active tab found');
      }
      tabId = activeTab.id;
    }
    
    // Extract profile data using the same method as queue processor
    const queueProcessor = new QueueProcessor();
    const profileData = await queueProcessor.extractProfileData(tabId);
    
    if (!profileData) {
      throw new Error('Failed to extract profile data');
    }
    
    console.log('Extracted profile data for import:', profileData);
    
    // Import the profile
    const result = await handleImportProfile(profileData, authToken);
    return result;
  } catch (error) {
    console.error('Failed to extract and import profile:', error);
    throw error;
  }
}

// Update badge from storage
async function updateBadgeFromStorage() {
  try {
    const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
    const pendingCount = linkedinImportQueue.filter(item => item.status === 'pending').length;
    
    if (pendingCount > 0) {
      chrome.action.setBadgeText({ text: pendingCount.toString() });
      chrome.action.setBadgeBackgroundColor({ color: '#0a66c2' });
    } else {
      chrome.action.setBadgeText({ text: '' });
    }
  } catch (error) {
    console.error('Error updating badge:', error);
  }
}

// Initialize badge on startup
chrome.runtime.onStartup.addListener(() => {
  updateBadgeFromStorage();
});

// Set up periodic queue processing reminder
chrome.alarms.create('queueReminder', {
  periodInMinutes: 60 // Check every hour
});

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === 'queueReminder') {
    try {
      const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
      const pendingCount = linkedinImportQueue.filter(item => item.status === 'pending').length;
      
      if (pendingCount > 10) {
        // Create notification if many items are pending
        chrome.notifications.create({
          type: 'basic',
          iconUrl: 'assets/icons/icon-128.png',
          title: 'LinkedIn Import Queue',
          message: `You have ${pendingCount} profiles waiting to be imported.`
        });
      }
    } catch (error) {
      console.error('Error checking queue:', error);
    }
  }
});