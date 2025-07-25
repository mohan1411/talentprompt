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
      // console.log('No pending items to process');
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
        
        console.log('[IMPORT RESULT] Full result:', result);
        console.log('[IMPORT RESULT] Has candidate_id:', !!result?.candidate_id);
        console.log('[IMPORT RESULT] Is duplicate:', result?.is_duplicate);
        
        // Verify the import was successful by checking for candidate_id
        if (result && result.candidate_id && !result.is_duplicate) {
          // Successfully imported new profile
          await this.updateItemStatus(item.id, 'completed');
          successCount++;
          console.log(`[IMPORT SUCCESS] Profile imported with ID: ${result.candidate_id}`);
        } else if (result && result.is_duplicate) {
          // This is a duplicate (shouldn't happen with new logic, but just in case)
          await this.updateItemStatus(item.id, 'failed', 'Duplicate - Already imported');
          duplicateCount++;
          console.log('[IMPORT DUPLICATE] Profile was marked as duplicate');
        } else {
          // Import failed - no candidate_id returned
          throw new Error('Import failed - no candidate ID returned');
        }
        
        // Send progress update
        await this.sendProgressUpdate();
        
      } catch (error) {
        console.error(`[IMPORT ERROR] Failed to process ${item.profileUrl}:`, error);
        console.log('[IMPORT ERROR] Error type:', error.constructor.name);
        console.log('[IMPORT ERROR] Error message:', error.message);
        console.log('[IMPORT ERROR] Error stack:', error.stack);
        
        // Check error type
        if (error.message && error.message.includes('You have already imported')) {
          // User's own duplicate
          await this.updateItemStatus(item.id, 'failed', 'Duplicate - You already imported this profile');
          duplicateCount++;
          console.log('[IMPORT ERROR] Marked as duplicate (user already imported)');
        } else if (error.message && (
          error.message.includes('imported by another user') ||
          error.message.includes('423') ||
          error.message.includes('Profile Locked')
        )) {
          // Another user's profile (constraint issue)
          await this.updateItemStatus(item.id, 'failed', 'Locked - Imported by another user');
          failedCount++;
          console.log('[IMPORT ERROR] Profile locked by another user');
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
          console.log('[IMPORT ERROR] Marked as duplicate (generic)');
        } else {
          await this.updateItemStatus(item.id, 'failed', error.message || 'Unknown error');
          failedCount++;
          console.log('[IMPORT ERROR] Marked as failed');
        }
      }
      
      // Delay between profiles to avoid detection
      if (!this.shouldStop) {
        const delay = RATE_LIMIT_CONFIG.MIN_DELAY + Math.random() * (RATE_LIMIT_CONFIG.MAX_DELAY - RATE_LIMIT_CONFIG.MIN_DELAY);
        // console.log(`Waiting ${Math.round(delay/1000)} seconds before next profile...`);
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
      
      // console.log('Created processing tab:', tab.id);
      return tab;
    } catch (error) {
      console.error('Failed to create pinned tab:', error);
      
      // Fallback: Create a normal background tab
      try {
        const tab = await chrome.tabs.create({
          url: 'about:blank',
          active: false
        });
        // console.log('Created fallback processing tab:', tab.id);
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
          // console.log('Extracting profile data using ultra-clean extractor from:', window.location.href);
          
          // Use the ultra-clean extractor if available
          if (window.extractUltraCleanProfile) {
            // console.log('Using ultra-clean extractor for comprehensive extraction');
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
  // console.log('Received message:', request);
  
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
        console.log('[SERVICE WORKER] Import success, result:', result);
        sendResponse({ success: true, data: result });
      })
      .catch(error => {
        console.log('[SERVICE WORKER] Import failed, error:', error.message);
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
    // console.log('Received startQueueProcessing request');
    queueProcessor.start()
      .then(() => {
        // console.log('Queue processing started successfully');
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
    // console.log('Received addToQueue request with profiles:', request.profiles);
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
  // console.log('Background script importing profile...');
  // console.log('Profile data to import:', profileData);
  
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
    console.log('[DUPLICATE DEBUG] Profile exists check result:', existsResult);
    
    if (existsResult.exists) {
      // Don't pre-check, let the backend handle it and return proper duplicate response
      console.log('Profile may already exist, but letting backend handle it');
    }
  } catch (error) {
    console.warn('[DUPLICATE DEBUG] Error checking profile existence (will continue with import):', error);
  }
  
  // Use the correct import endpoint
  const url = `${API_URL}/linkedin/import-profile`;
  console.log('[DUPLICATE DEBUG] Making import request to:', url);
  console.log('[DUPLICATE DEBUG] Profile URL:', profileData.linkedin_url);
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(profileData)
    });
    
    console.log('[DUPLICATE DEBUG] Response status:', response.status);
    console.log('[DUPLICATE DEBUG] Response status text:', response.statusText);
    
    if (!response.ok) {
      console.log('[DUPLICATE DEBUG] Response not OK, status:', response.status);
      const errorText = await response.text();
      console.error('[DUPLICATE DEBUG] Error response body:', errorText);
      console.error('Response headers:', response.headers);
      
      let errorMessage = `Import failed: ${response.statusText}`;
      console.log('[DUPLICATE DEBUG] Initial error message:', errorMessage);
      console.log('[DUPLICATE DEBUG] Response statusText:', response.statusText);
      
      // Handle specific error codes
      if (response.status === 404) {
        console.log('[DUPLICATE DEBUG] Got 404 response');
        errorMessage = 'Import endpoint not found. Please check if the backend is running.';
      } else if (response.status === 401) {
        errorMessage = 'Authentication failed. Please login again.';
      } else if (response.status === 422) {
        errorMessage = 'Invalid profile data. Please check if all required fields are present.';
      } else if (response.status === 409) {
        // Conflict - duplicate profile for current user
        console.log('[DUPLICATE] Got 409 response - duplicate profile detected');
        await updateDuplicateCounter();
        
        // Send notification
        chrome.notifications.create({
          type: 'basic',
          iconUrl: chrome.runtime.getURL('assets/icons/icon-48.png'),
          title: 'Duplicate Profile',
          message: `You have already imported ${profileData.name || 'this profile'}`
        });
        
        console.log('[DUPLICATE] Throwing duplicate error');
        throw new Error('You have already imported this profile');
      } else if (response.status === 423) {
        // Locked - profile imported by another user (old constraint issue)
        console.log('[LOCKED] Got 423 response - profile imported by another user');
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
    console.log('[IMPORT RESPONSE] Full response:', result);
    console.log('[IMPORT RESPONSE] Status:', response.status);
    console.log('[IMPORT RESPONSE] Has candidate_id:', !!result.candidate_id);
    console.log('[IMPORT RESPONSE] Success flag:', result.success);
    
    // Validate the response has required fields
    if (!result.candidate_id) {
      console.error('[IMPORT ERROR] No candidate_id in response:', result);
      throw new Error('Import failed - no candidate ID returned from server');
    }
    
    // Check if the response indicates this was a duplicate
    if (result.is_duplicate === true || result.action === 'updated' || result.status === 'updated' || result.updated === true) {
      console.log('[IMPORT DUPLICATE] Profile is duplicate:', result);
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
    console.log('[IMPORT SUCCESS] New profile imported successfully');
    
    return result;
  } catch (error) {
    console.error('Fetch error:', error);
    
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
  console.log('[DUPLICATE DEBUG] Checking if profile exists:', linkedinUrl, 'at URL:', url);
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ linkedin_url: linkedinUrl })
    });
    
    console.log('[DUPLICATE DEBUG] Check exists response status:', response.status);
    
    if (response.status === 404) {
      console.warn('[DUPLICATE DEBUG] Check-exists endpoint not found (404), will check during import');
      return { exists: false };
    }
    
    if (response.ok) {
      const data = await response.json();
      console.log('[DUPLICATE DEBUG] Check exists response data:', data);
      return data;
    }
    
    console.warn('[DUPLICATE DEBUG] Check exists failed with status:', response.status);
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

// Update duplicate counter
async function updateDuplicateCounter() {
  try {
    const today = new Date().toDateString();
    const { importStats = {} } = await chrome.storage.local.get('importStats');
    
    if (!importStats[today]) {
      importStats[today] = { imported: 0, duplicates: 0 };
    }
    
    importStats[today].duplicates += 1;
    await chrome.storage.local.set({ importStats });
    
    // Notify popup if it's open
    chrome.runtime.sendMessage({
      action: 'statsUpdated',
      stats: importStats[today]
    }).catch(() => {
      // Ignore errors if popup is not open
    });
  } catch (error) {
    console.error('Error updating duplicate counter:', error);
  }
}

// Update import counter
async function updateImportCounter() {
  try {
    const today = new Date().toDateString();
    const { importStats = {} } = await chrome.storage.local.get('importStats');
    
    if (!importStats[today]) {
      importStats[today] = { imported: 0, duplicates: 0 };
    }
    
    importStats[today].imported += 1;
    await chrome.storage.local.set({ importStats });
    
    // Notify popup if it's open
    chrome.runtime.sendMessage({
      action: 'statsUpdated',
      stats: importStats[today]
    }).catch(() => {
      // Ignore errors if popup is not open
    });
  } catch (error) {
    console.error('Error updating import counter:', error);
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