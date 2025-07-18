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
      // First, inject the necessary scripts for advanced extraction
      await chrome.scripting.executeScript({
        target: { tabId },
        files: [
          'content/calculate-experience.js',
          'content/calculate-experience-advanced.js',
          'content/manual-experience-override.js',
          'content/data-validator.js',
          'content/ultra-clean-extractor.js'
        ]
      });
      
      // Now execute the extraction using the ultra-clean extractor
      const [result] = await chrome.scripting.executeScript({
        target: { tabId },
        func: () => {
          console.log('Extracting profile data using ultra-clean extractor from:', window.location.href);
          
          // Use the ultra-clean extractor if available
          if (window.extractUltraCleanProfile) {
            console.log('Using ultra-clean extractor for comprehensive extraction');
            const profileData = window.extractUltraCleanProfile();
            
            // Ensure we have the required fields for the backend
            if (!profileData.email) profileData.email = null;
            if (!profileData.phone) profileData.phone = null;
            if (!profileData.years_experience) profileData.years_experience = null;
            
            // Convert experience format if needed
            if (profileData.experience && Array.isArray(profileData.experience)) {
              profileData.experience = profileData.experience.map(exp => ({
                title: exp.title || '',
                company: exp.company || '',
                dates: exp.duration || exp.dates || '',
                location: exp.location || '',
                description: exp.description || ''
              }));
            }
            
            return profileData;
          }
          
          // Fallback to inline extraction if ultra-clean extractor is not available
          console.log('WARNING: Ultra-clean extractor not available, using fallback extraction');
          
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
          
          // For experience and skills, delegate to advanced functions if available
          if (window.calculateTotalExperienceAdvanced || window.calculateTotalExperience) {
            console.log('Advanced experience calculation functions are available');
          }
          
          // Basic experience extraction (will be overridden by ultra-clean if available)
          const experienceSection = Array.from(document.querySelectorAll('section')).find(s => 
            s.querySelector('h2')?.textContent.includes('Experience')
          );
          if (experienceSection) {
            const expList = experienceSection.querySelector('ul') || experienceSection.querySelector('.pvs-list');
            if (expList) {
              const items = expList.querySelectorAll('li');
              items.forEach(item => {
                const texts = Array.from(item.querySelectorAll('span[aria-hidden="true"]'))
                  .map(span => span.textContent.trim()).filter(t => t);
                
                if (texts.length >= 2) {
                  data.experience.push({
                    title: texts[0] || '',
                    company: texts[1] || '',
                    dates: texts.find(t => t.match(/\d{4}|Present/i)) || '',
                    location: '',
                    description: ''
                  });
                }
              });
            }
          }
          
          // Default experience calculation if no advanced function available
          if (data.experience.length > 0 && !data.years_experience) {
            data.years_experience = 1; // Conservative default
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