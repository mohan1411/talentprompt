// Service worker for Promtitude Chrome Extension

// API configuration
const API_BASE_URL = 'https://talentprompt-production.up.railway.app/api/v1';
const DEV_API_URL = 'http://localhost:8000/api/v1';

// Use production backend
const API_URL = API_BASE_URL;

// Rate limiting configuration
const RATE_LIMIT_CONFIG = {
  MIN_DELAY: 5000,    // Minimum 5 seconds between requests
  MAX_DELAY: 10000,   // Maximum 10 seconds between requests
  BULK_IMPORT_DELAY: 3000  // 3 seconds between profiles in bulk import
};

// Queue processor class (integrated directly to avoid importScripts issues)
class QueueProcessor {
  constructor() {
    this.isProcessing = false;
    this.shouldStop = false;
    this.currentTab = null;
    this.keepAliveInterval = null;
  }

  async start() {
    if (this.isProcessing) {
      return;
    }
    
    this.isProcessing = true;
    this.shouldStop = false;
    
    // Start keepalive to prevent service worker from sleeping
    this.startKeepAlive();
    
    try {
      await this.processQueue();
    } catch (error) {
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
    // Get current user
    const { userEmail, authToken } = await chrome.storage.local.get(['userEmail', 'authToken']);
    if (!userEmail || !authToken) {
      return;
    }
    
    const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
    // Filter for current user's pending items only
    const pendingItems = linkedinImportQueue.filter(item => 
      item.status === 'pending' && 
      item.userEmail === userEmail
    );
    
    if (pendingItems.length === 0) {
      return;
    }

    // Create a hidden processing tab
    let processingTab;
    try {
      processingTab = await this.createHiddenTab();
      this.currentTab = processingTab;
    } catch (error) {
      throw new Error('Failed to create processing tab: ' + error.message);
    }

    // Track processing stats
    let successCount = 0;
    let duplicateCount = 0;
    let failedCount = 0;

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
        
        
        // Verify the import was successful by checking for candidate_id
        if (result && result.candidate_id && !result.is_duplicate) {
          // Successfully imported new profile
          await this.updateItemStatus(item.id, 'completed');
          successCount++;
        } else if (result && result.is_duplicate) {
          // This is a duplicate (shouldn't happen with new logic, but just in case)
          await this.updateItemStatus(item.id, 'failed', 'Duplicate - Already imported');
          duplicateCount++;
        } else {
          // Import failed - no candidate_id returned
          throw new Error('Import failed - no candidate ID returned');
        }
        
        // Send progress update
        await this.sendProgressUpdate();
        
      } catch (error) {
        
        // Check error type
        if (error.message && error.message.includes('You have already imported')) {
          // User's own duplicate
          await this.updateItemStatus(item.id, 'failed', 'Duplicate - You already imported this profile');
          duplicateCount++;
        } else if (error.message && (
          error.message.includes('imported by another user') ||
          error.message.includes('423') ||
          error.message.includes('Profile Locked')
        )) {
          // Another user's profile (constraint issue)
          await this.updateItemStatus(item.id, 'failed', 'Locked - Imported by another user');
          failedCount++;
        } else if (error.message && (
          error.message.includes('already been imported') || 
          error.message.includes('updated existing') ||
          error.message.includes('Profile Updated') ||
          error.message.toLowerCase().includes('duplicate') ||
          error.message.includes('409')
        )) {
          // Generic duplicate (fallback)
          await this.updateItemStatus(item.id, 'failed', 'Duplicate - Already imported');
          duplicateCount++;
        } else {
          await this.updateItemStatus(item.id, 'failed', error.message || 'Unknown error');
          failedCount++;
        }
      }
      
      // Delay between profiles to avoid detection
      if (!this.shouldStop) {
        const delay = RATE_LIMIT_CONFIG.MIN_DELAY + Math.random() * (RATE_LIMIT_CONFIG.MAX_DELAY - RATE_LIMIT_CONFIG.MIN_DELAY);
        await this.delay(delay);
      }
    }
    
    // Close the processing tab
    if (processingTab) {
      chrome.tabs.remove(processingTab.id);
    }
    
    // Show summary notification
    const totalProcessed = successCount + duplicateCount + failedCount;
    if (totalProcessed > 0) {
      let message = `Processed ${totalProcessed} profiles:\n`;
      message += `✓ Imported: ${successCount}\n`;
      if (duplicateCount > 0) message += `⚠ Duplicates: ${duplicateCount}\n`;
      if (failedCount > 0) message += `✗ Failed: ${failedCount}`;
      
      chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('assets/icons/icon-48.png'),
        title: 'Import Queue Complete',
        message: message
      });
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
      
      return tab;
    } catch (error) {
      
      // Fallback: Create a normal background tab
      try {
        const tab = await chrome.tabs.create({
          url: 'about:blank',
          active: false
        });
        return tab;
      } catch (fallbackError) {
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
          
          // Use the ultra-clean extractor if available
          if (window.extractUltraCleanProfile) {
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
  
  cleanup() {
    if (this.currentTab) {
      chrome.tabs.remove(this.currentTab.id).catch(() => {});
      this.currentTab = null;
    }
    this.stopKeepAlive();
  }
  
  startKeepAlive() {
    // Send a message every 20 seconds to keep service worker alive
    this.keepAliveInterval = setInterval(() => {
      chrome.runtime.sendMessage({ action: 'keepAlive' }).catch(() => {});
    }, 20000);
  }
  
  stopKeepAlive() {
    if (this.keepAliveInterval) {
      clearInterval(this.keepAliveInterval);
      this.keepAliveInterval = null;
    }
  }
}

const queueProcessor = new QueueProcessor();

// Handle extension installation
chrome.runtime.onInstalled.addListener((details) => {
  
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
      .then(result => {
        sendResponse({ success: true, data: result });
      })
      .catch(error => {
        sendResponse({ success: false, error: error.message });
      });
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
    queueProcessor.start()
      .then(() => {
        sendResponse({ success: true });
      })
      .catch(error => {
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
    handleAddToQueue(request.profiles)
      .then(result => {
        sendResponse(result);
      })
      .catch(error => {
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }
  
  if (request.action === 'ping') {
    sendResponse({ success: true, pong: true });
    return true;
  }
  
  // Echo back for other messages
  sendResponse({ received: true, action: request.action });
  return true;
});

// Import profile to backend
async function handleImportProfile(profileData, authToken) {
  
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
  
  // Check if profile already exists before importing
  try {
    const existsResult = await checkProfileExists(profileData.linkedin_url, authToken);
    
    if (existsResult.exists) {
      // Don't pre-check, let the backend handle it and return proper duplicate response
    }
  } catch (error) {
  }
  
  // Use the correct import endpoint
  const url = `${API_URL}/linkedin/import-profile`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(profileData)
    });
    
    
    if (!response.ok) {
      const errorText = await response.text();
      
      let errorMessage = `Import failed: ${response.statusText}`;
      
      // Handle specific error codes
      if (response.status === 404) {
        errorMessage = 'Import endpoint not found. Please check if the backend is running.';
      } else if (response.status === 401) {
        errorMessage = 'Authentication failed. Please login again.';
      } else if (response.status === 422) {
        errorMessage = 'Invalid profile data. Please check if all required fields are present.';
      } else if (response.status === 409) {
        // Conflict - duplicate profile for current user
        await updateDuplicateCounter();
        
        // Send notification
        chrome.notifications.create({
          type: 'basic',
          iconUrl: chrome.runtime.getURL('assets/icons/icon-48.png'),
          title: 'Duplicate Profile',
          message: `You have already imported ${profileData.name || 'this profile'}`
        });
        
        throw new Error('You have already imported this profile');
      } else if (response.status === 423) {
        // Locked - profile imported by another user (old constraint issue)
        errorMessage = 'This profile has been imported by another user. Multiple users cannot import the same profile due to a database constraint.';
        
        // Send notification with different message
        chrome.notifications.create({
          type: 'basic',
          iconUrl: chrome.runtime.getURL('assets/icons/icon-48.png'),
          title: 'Profile Locked',
          message: `${profileData.name || 'This profile'} has been imported by another user`
        });
        
        throw new Error(errorMessage);
      }
      
      try {
        const error = JSON.parse(errorText);
        if (error.detail) {
          if (typeof error.detail === 'string') {
            errorMessage = error.detail;
            
            // Check for duplicate-related messages
            if (errorMessage.toLowerCase().includes('already exists') || 
                errorMessage.toLowerCase().includes('duplicate')) {
              await updateDuplicateCounter();
              
              // Send notification
              chrome.notifications.create({
                type: 'basic',
                iconUrl: chrome.runtime.getURL('assets/icons/icon-48.png'),
                title: 'Duplicate Profile',
                message: errorMessage
              });
            }
          } else if (Array.isArray(error.detail)) {
            errorMessage = error.detail.map(e => e.msg || e.message).join(', ');
          }
        }
      } catch (e) {
        // If error text is not JSON, use it as is
        if (errorText && errorText.length < 200) {
          errorMessage = errorText;
        }
      }
      throw new Error(errorMessage);
    }
    
    const result = await response.json();
    
    // Validate the response has required fields
    if (!result.candidate_id) {
      throw new Error('Import failed - no candidate ID returned from server');
    }
    
    // Check if the response indicates this was a duplicate
    if (result.is_duplicate === true || result.action === 'updated' || result.status === 'updated' || result.updated === true) {
      await updateDuplicateCounter();
      
      // Send notification
      chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('assets/icons/icon-48.png'),
        title: 'Duplicate Profile',
        message: result.message || `${profileData.name || 'Profile'} was already in database and has been updated`
      });
      
      // Return the result but mark it as duplicate
      return {
        ...result,
        is_duplicate: true,
        message: 'This profile has already been imported'
      };
    }
    
    // Update import counter only for new imports
    await updateImportCounter();
    
    return result;
  } catch (error) {
    
    // Re-throw our duplicate error
    if (error.message && (error.message.includes('already been imported') || error.message.includes('updated existing'))) {
      throw error;
    }
    
    if (error.message && error.message.includes('Failed to fetch')) {
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
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ linkedin_url: linkedinUrl })
    });
    
    
    if (response.status === 404) {
      return { exists: false };
    }
    
    if (response.ok) {
      const data = await response.json();
      return data;
    }
    
    return { exists: false };
  } catch (error) {
    return { exists: false };
  }
}

// Handle adding profiles to queue
async function handleAddToQueue(profiles) {
  try {
    if (!profiles || !Array.isArray(profiles)) {
      throw new Error('Invalid profiles data');
    }
    
    // Get current user
    const { userEmail } = await chrome.storage.local.get('userEmail');
    if (!userEmail) {
      throw new Error('No user logged in');
    }
    
    const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
    
    let addedCount = 0;
    
    profiles.forEach(profile => {
      // Validate profile data
      if (!profile.profileUrl || !profile.profileName) {
        return;
      }
      
      // Check if profile already exists in queue for this user
      if (!linkedinImportQueue.some(item => 
        item.profileUrl === profile.profileUrl && 
        item.userEmail === userEmail
      )) {
        linkedinImportQueue.push({
          id: Date.now() + '_' + Math.random(),
          profileUrl: profile.profileUrl,
          profileName: profile.profileName,
          status: 'pending',
          addedAt: new Date().toISOString(),
          userEmail: userEmail // Track which user added this
        });
        addedCount++;
      }
    });
    
    // Save updated queue
    await chrome.storage.local.set({ linkedinImportQueue });
    
    // Update badge - only count current user's pending items
    const pendingCount = linkedinImportQueue.filter(item => 
      item.status === 'pending' && 
      item.userEmail === userEmail
    ).length;
    updateBadgeFromStorage();
    
    return {
      success: true,
      addedCount: addedCount,
      pendingCount: pendingCount
    };
  } catch (error) {
    throw error;
  }
}

// Extract and import current profile
async function handleExtractAndImportCurrentProfile(authToken, tabId) {
  try {
    
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
    
    
    // Import the profile
    const result = await handleImportProfile(profileData, authToken);
    return result;
  } catch (error) {
    throw error;
  }
}

// Update badge from storage
async function updateBadgeFromStorage() {
  try {
    const { linkedinImportQueue = [], userEmail } = await chrome.storage.local.get(['linkedinImportQueue', 'userEmail']);
    
    // Only count current user's pending items
    const pendingCount = linkedinImportQueue.filter(item => 
      item.status === 'pending' && 
      item.userEmail === userEmail
    ).length;
    
    if (pendingCount > 0) {
      chrome.action.setBadgeText({ text: pendingCount.toString() });
      chrome.action.setBadgeBackgroundColor({ color: '#0a66c2' });
    } else {
      chrome.action.setBadgeText({ text: '' });
    }
  } catch (error) {
  }
}

// Update duplicate counter
async function updateDuplicateCounter() {
  try {
    const today = new Date().toDateString();
    const { importStats = {}, userEmail } = await chrome.storage.local.get(['importStats', 'userEmail']);
    
    if (!userEmail) {
      return;
    }
    
    if (!importStats[today]) {
      importStats[today] = {};
    }
    
    if (!importStats[today][userEmail]) {
      importStats[today][userEmail] = { imported: 0, duplicates: 0 };
    }
    
    importStats[today][userEmail].duplicates += 1;
    await chrome.storage.local.set({ importStats });
    
    // Notify popup if it's open
    chrome.runtime.sendMessage({
      action: 'statsUpdated',
      stats: importStats[today][userEmail]
    }).catch(() => {
      // Ignore errors if popup is not open
    });
  } catch (error) {
  }
}

// Update import counter
async function updateImportCounter() {
  try {
    const today = new Date().toDateString();
    const { importStats = {}, userEmail } = await chrome.storage.local.get(['importStats', 'userEmail']);
    
    if (!userEmail) {
      return;
    }
    
    if (!importStats[today]) {
      importStats[today] = {};
    }
    
    if (!importStats[today][userEmail]) {
      importStats[today][userEmail] = { imported: 0, duplicates: 0 };
    }
    
    importStats[today][userEmail].imported += 1;
    await chrome.storage.local.set({ importStats });
    
    // Notify popup if it's open
    chrome.runtime.sendMessage({
      action: 'statsUpdated',
      stats: importStats[today][userEmail]
    }).catch(() => {
      // Ignore errors if popup is not open
    });
  } catch (error) {
  }
}

// Migrate existing data to include userEmail
async function migrateExistingData() {
  try {
    const { linkedinImportQueue = [], userEmail, dataMigrated } = await chrome.storage.local.get(['linkedinImportQueue', 'userEmail', 'dataMigrated']);
    
    // Skip if already migrated or no user logged in
    if (dataMigrated || !userEmail) {
      return;
    }
    
    let needsMigration = false;
    
    // Check if any items don't have userEmail
    const updatedQueue = linkedinImportQueue.map(item => {
      if (!item.userEmail) {
        needsMigration = true;
        // Assign current user to items without userEmail
        return { ...item, userEmail };
      }
      return item;
    });
    
    if (needsMigration) {
      await chrome.storage.local.set({ 
        linkedinImportQueue: updatedQueue,
        dataMigrated: true 
      });
    } else {
      // Mark as migrated even if no changes needed
      await chrome.storage.local.set({ dataMigrated: true });
    }
  } catch (error) {
  }
}

// Initialize badge on startup
chrome.runtime.onStartup.addListener(async () => {
  await migrateExistingData();
  updateBadgeFromStorage();
});

// Also run migration on install/update
chrome.runtime.onInstalled.addListener(async () => {
  await migrateExistingData();
  updateBadgeFromStorage();
});

// Set up periodic queue processing reminder
chrome.alarms.create('queueReminder', {
  periodInMinutes: 60 // Check every hour
});

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === 'queueReminder') {
    try {
      const { linkedinImportQueue = [], userEmail } = await chrome.storage.local.get(['linkedinImportQueue', 'userEmail']);
      
      // Only count current user's pending items
      const pendingCount = linkedinImportQueue.filter(item => 
        item.status === 'pending' && 
        item.userEmail === userEmail
      ).length;
      
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
    }
  }
});