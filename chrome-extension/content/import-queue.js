/**
 * LinkedIn Import Queue Manager
 * Manages a queue of LinkedIn profiles for compliant bulk import
 */

(function() {
  'use strict';
  
  console.log('🚀 Promtitude Import Queue: Initializing...');

  if (window.__linkedInImportQueue) {
    console.log('Import queue already initialized');
    return;
  }

  class LinkedInImportQueue {
    constructor() {
      this.STORAGE_KEY = 'linkedinImportQueue';
      this.MAX_QUEUE_SIZE = 100;
      this.MIN_DELAY_MS = 3000; // 3 seconds minimum between imports
      this.MAX_DELAY_MS = 6000; // 6 seconds maximum
      this.queue = [];
      this.isProcessing = false;
      this.currentProfile = null;
      
      this.init();
    }

    async init() {
      await this.loadQueue();
      
      // Wait for page to be ready
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
          this.injectQueueUI();
        });
      } else {
        // Small delay to ensure LinkedIn's React has rendered
        setTimeout(() => {
          this.injectQueueUI();
        }, 1500);
      }
      
      this.setupEventListeners();
      
      // Check if we should continue processing
      if (this.shouldContinueProcessing()) {
        setTimeout(() => this.processNext(), 1000);
      }
    }

    async loadQueue() {
      try {
        const result = await chrome.storage.local.get(this.STORAGE_KEY);
        this.queue = result[this.STORAGE_KEY] || [];
        this.updateBadge();
      } catch (error) {
        console.error('Failed to load queue:', error);
        this.queue = [];
      }
    }

    async saveQueue() {
      try {
        await chrome.storage.local.set({
          [this.STORAGE_KEY]: this.queue
        });
        this.updateBadge();
      } catch (error) {
        console.error('Failed to save queue:', error);
      }
    }

    updateBadge() {
      const pendingCount = this.queue.filter(item => item.status === 'pending').length;
      chrome.runtime.sendMessage({
        action: 'updateQueueBadge',
        count: pendingCount
      }).catch(() => {
        // Extension might not be ready
      });
    }

    injectQueueUI() {
      console.log('Injecting Queue UI...');
      
      // Always inject floating queue status first
      this.injectQueueStatus();
      
      // Check if we're on a LinkedIn profile page
      if (this.isProfilePage()) {
        this.injectProfileButton();
        // Also inject a floating button as fallback
        this.injectFloatingProfileButton();
      }
      
      // Check if we're on search results
      if (this.isSearchResultsPage()) {
        this.injectSearchResultsUI();
      }
    }

    isProfilePage() {
      return window.location.pathname.includes('/in/');
    }

    isSearchResultsPage() {
      // LinkedIn uses different URLs for search
      const searchPaths = [
        '/search/results/',
        '/search/results/people/',
        '/search/results/all/',
        '/people/search/'
      ];
      
      const currentPath = window.location.pathname;
      const isSearch = searchPaths.some(path => currentPath.includes(path));
      
      console.log(`Is search page check: ${currentPath} = ${isSearch}`);
      return isSearch;
    }

    injectProfileButton() {
      console.log('Injecting profile button...');
      let attempts = 0;
      
      // Wait for profile actions to load
      const checkInterval = setInterval(() => {
        attempts++;
        
        // Try multiple selectors for different LinkedIn layouts
        const actionsSelectors = [
          '.pvs-profile-actions',
          '.pv-top-card-v2-ctas',
          '.pv-top-card__actions',
          '.pv-top-card-v3__actions',
          '.pv-top-card-section__actions',
          '.pv-s-profile-actions',
          'div[class*="profile-actions"]',
          'section[class*="top-card"] div[class*="actions"]',
          // More specific selectors
          'main section:first-child .pvs-profile-actions',
          'main section:first-child div[class*="mt2"]',
          // Find where Message/More buttons are
          'div:has(> button[aria-label*="Message"])',
          'div:has(> button[aria-label*="More actions"])',
          'div:has(> button:contains("Message"))'
        ];
        
        let actionsContainer = null;
        
        // First try the selectors
        for (const selector of actionsSelectors) {
          try {
            const element = document.querySelector(selector);
            if (element) {
              actionsContainer = element;
              console.log('Found container with selector:', selector);
              break;
            }
          } catch (e) {
            // Some selectors might fail, that's ok
          }
        }
        
        // If still not found, look for Message button and use its parent
        if (!actionsContainer) {
          const messageBtn = Array.from(document.querySelectorAll('button')).find(
            btn => btn.textContent?.includes('Message') || btn.getAttribute('aria-label')?.includes('Message')
          );
          if (messageBtn) {
            actionsContainer = messageBtn.parentElement;
            console.log('Found container via Message button');
          }
        }
        
        if (actionsContainer && !document.querySelector('.import-queue-btn')) {
          clearInterval(checkInterval);
          console.log('Found actions container:', actionsContainer);
          
          const button = document.createElement('button');
          button.className = 'import-queue-btn artdeco-button artdeco-button--2 artdeco-button--secondary';
          button.style.cssText = 'margin-left: 8px; display: inline-flex; align-items: center;';
          
          const profileUrl = window.location.href.split('?')[0];
          const isQueued = this.isProfileQueued(profileUrl);
          
          button.innerHTML = isQueued ? 
            '<span>✓ In Import Queue</span>' : 
            '<span>+ Add to Import Queue</span>';
          
          button.disabled = isQueued;
          
          button.addEventListener('click', (e) => {
            e.preventDefault();
            this.addCurrentProfile();
          });
          
          actionsContainer.appendChild(button);
          console.log('Profile button injected successfully');
        } else if (attempts > 10) {
          clearInterval(checkInterval);
          console.log('Could not find actions container after 10 attempts');
        }
      }, 1000);
    }

    injectFloatingProfileButton() {
      if (document.querySelector('.import-queue-floating-btn')) return;
      
      const profileUrl = window.location.href.split('?')[0];
      const isQueued = this.isProfileQueued(profileUrl);
      
      const floatingBtn = document.createElement('button');
      floatingBtn.className = 'import-queue-floating-btn';
      floatingBtn.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: ${isQueued ? '#057642' : '#0a66c2'};
        color: white;
        padding: 12px 20px;
        border-radius: 24px;
        border: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        cursor: pointer;
        z-index: 10000;
        font-family: -apple-system, sans-serif;
        font-size: 14px;
        font-weight: 600;
        transition: all 0.2s;
      `;
      
      floatingBtn.innerHTML = isQueued ? 
        '✓ In Import Queue' : 
        '+ Add to Import Queue';
      
      floatingBtn.disabled = isQueued;
      
      if (!isQueued) {
        floatingBtn.onmouseover = () => {
          floatingBtn.style.transform = 'scale(1.05)';
          floatingBtn.style.boxShadow = '0 6px 16px rgba(0,0,0,0.2)';
        };
        floatingBtn.onmouseout = () => {
          floatingBtn.style.transform = 'scale(1)';
          floatingBtn.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        };
      }
      
      floatingBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        await this.addCurrentProfile();
        // Update button state
        floatingBtn.style.background = '#057642';
        floatingBtn.innerHTML = '✓ In Import Queue';
        floatingBtn.disabled = true;
      });
      
      document.body.appendChild(floatingBtn);
      console.log('Floating profile button injected');
    }

    injectSearchResultsUI() {
      console.log('Injecting search results UI...');
      
      // Function to add checkboxes
      const addCheckboxes = () => {
        // Try multiple selectors for search results
        const resultSelectors = [
          '.entity-result__item',
          '.reusable-search__result-container',
          'li[class*="reusable-search__result"]',
          'div[data-view-name="search-entity-result-universal-template"]',
          '.search-results__list > li',
          'ul.reusable-search__entity-result-list > li'
        ];
        
        let results = [];
        for (const selector of resultSelectors) {
          results = document.querySelectorAll(selector);
          if (results.length > 0) {
            console.log(`Found ${results.length} results with selector: ${selector}`);
            break;
          }
        }
        
        results.forEach((result, index) => {
          if (!result.querySelector('.import-queue-checkbox')) {
            const checkbox = this.createResultCheckbox(result);
            
            // Try multiple insertion points
            const insertionSelectors = [
              '.entity-result__title-text',
              '.entity-result__title-line',
              'span[aria-hidden="true"]',
              '.app-aware-link',
              'a[class*="app-aware-link"]'
            ];
            
            let inserted = false;
            for (const selector of insertionSelectors) {
              const element = result.querySelector(selector);
              if (element && element.parentElement) {
                element.parentElement.insertBefore(checkbox, element);
                inserted = true;
                break;
              }
            }
            
            // If no good insertion point, just prepend to result
            if (!inserted) {
              result.insertBefore(checkbox, result.firstChild);
            }
          }
        });
        
        // Add bulk import button if we have results
        if (results.length > 0 && !document.querySelector('.bulk-import-button')) {
          setTimeout(() => this.injectBulkImportButton(), 500);
        }
      };
      
      // Initial injection
      setTimeout(addCheckboxes, 1000);
      
      // Watch for changes
      const observer = new MutationObserver(() => {
        addCheckboxes();
      });
      
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    }

    createResultCheckbox(resultElement) {
      const wrapper = document.createElement('div');
      wrapper.className = 'import-queue-checkbox';
      wrapper.style.cssText = `
        display: inline-block; 
        margin-right: 12px; 
        vertical-align: middle;
        position: relative;
      `;
      
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.style.cssText = `
        width: 20px; 
        height: 20px; 
        cursor: pointer;
        accent-color: #0a66c2;
        position: relative;
        z-index: 10;
      `;
      
      // Find profile link - try multiple selectors
      const linkSelectors = [
        'a[href*="/in/"]',
        '.entity-result__title-link',
        '.app-aware-link[href*="/in/"]',
        'a.app-aware-link'
      ];
      
      let profileLink = null;
      for (const selector of linkSelectors) {
        profileLink = resultElement.querySelector(selector);
        if (profileLink && profileLink.href && profileLink.href.includes('/in/')) {
          break;
        }
      }
      
      if (profileLink) {
        const profileUrl = profileLink.href.split('?')[0];
        checkbox.checked = this.isProfileQueued(profileUrl);
        checkbox.dataset.profileUrl = profileUrl;
        
        // Extract name - try multiple selectors
        const nameSelectors = [
          '.entity-result__title-text',
          '.entity-result__title',
          'span[aria-hidden="true"]',
          '.sr-only'
        ];
        
        let name = 'Unknown';
        for (const selector of nameSelectors) {
          const nameElement = resultElement.querySelector(selector);
          if (nameElement && nameElement.textContent) {
            name = nameElement.textContent.trim();
            break;
          }
        }
        
        checkbox.dataset.profileName = name;
        console.log(`Created checkbox for: ${name} - ${profileUrl}`);
      }
      
      wrapper.appendChild(checkbox);
      return wrapper;
    }

    injectBulkImportButton() {
      console.log('Injecting bulk import button...');
      
      // Try multiple locations for the button
      const headerSelectors = [
        '.search-results-container header',
        '.scaffold-layout__list-header',
        '.search-results__total',
        '.pb2.t-black--light.t-14',
        'div[class*="search-results__cluster-title"]',
        '.artdeco-card'
      ];
      
      let searchHeader = null;
      for (const selector of headerSelectors) {
        searchHeader = document.querySelector(selector);
        if (searchHeader) {
          console.log(`Found header with selector: ${selector}`);
          break;
        }
      }
      
      // If no header found, create a floating button
      if (!searchHeader) {
        console.log('No header found, creating floating bulk button');
        const floatingContainer = document.createElement('div');
        floatingContainer.className = 'bulk-import-button-floating';
        floatingContainer.style.cssText = `
          position: fixed;
          top: 120px;
          right: 20px;
          z-index: 10000;
          background: white;
          padding: 16px;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        
        const buttonContainer = floatingContainer;
        this.createBulkButtons(buttonContainer);
        document.body.appendChild(floatingContainer);
      } else {
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'bulk-import-button';
        buttonContainer.style.cssText = `
          margin: 16px 0; 
          padding: 12px;
          background: #f3f6f8;
          border-radius: 8px;
          display: flex;
          justify-content: flex-end;
          gap: 8px;
        `;
        
        this.createBulkButtons(buttonContainer);
        searchHeader.parentElement.insertBefore(buttonContainer, searchHeader.nextSibling);
      }
    }
    
    createBulkButtons(container) {
      const selectAllBtn = document.createElement('button');
      selectAllBtn.className = 'artdeco-button artdeco-button--2 artdeco-button--secondary';
      selectAllBtn.style.cssText = `
        padding: 8px 16px;
        font-weight: 600;
        border: 2px solid #0a66c2;
        background: white;
        color: #0a66c2;
        border-radius: 24px;
        cursor: pointer;
      `;
      selectAllBtn.textContent = 'Select All';
      selectAllBtn.addEventListener('click', () => this.toggleSelectAll());
      
      const addSelectedBtn = document.createElement('button');
      addSelectedBtn.className = 'artdeco-button artdeco-button--2 artdeco-button--primary';
      addSelectedBtn.style.cssText = `
        padding: 8px 16px;
        font-weight: 600;
        background: #0a66c2;
        color: white;
        border: none;
        border-radius: 24px;
        cursor: pointer;
      `;
      addSelectedBtn.innerHTML = '<span>Add Selected to Import Queue</span>';
      addSelectedBtn.addEventListener('click', () => this.addSelectedToQueue());
      
      container.appendChild(selectAllBtn);
      container.appendChild(addSelectedBtn);
      
      console.log('Bulk import buttons created');
    }

    injectQueueStatus() {
      if (document.querySelector('.import-queue-status')) return;
      
      console.log('Injecting queue status UI...');
      
      const statusDiv = document.createElement('div');
      statusDiv.className = 'import-queue-status';
      statusDiv.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: white;
        border: 2px solid #0a66c2;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        z-index: 10001;
        min-width: 280px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      `;
      
      this.updateQueueStatusUI(statusDiv);
      document.body.appendChild(statusDiv);
      console.log('Queue status UI injected');
      
      // Update status every second when processing
      setInterval(() => {
        this.updateQueueStatusUI(statusDiv);
      }, 1000);
    }

    updateQueueStatusUI(container) {
      const pendingCount = this.queue.filter(item => item.status === 'pending').length;
      const completedCount = this.queue.filter(item => item.status === 'completed').length;
      const failedCount = this.queue.filter(item => item.status === 'failed').length;
      
      container.innerHTML = `
        <div style="font-weight: bold; margin-bottom: 12px; color: #0a66c2; font-size: 16px;">
          🚀 Promtitude Import Queue
        </div>
        <div style="font-size: 14px; color: #333; line-height: 1.6;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span>⏳ Pending:</span>
            <span style="font-weight: bold;">${pendingCount}</span>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span>✅ Completed:</span>
            <span style="font-weight: bold; color: #057642;">${completedCount}</span>
          </div>
          ${failedCount > 0 ? `
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
              <span>❌ Failed:</span>
              <span style="font-weight: bold; color: #d93025;">${failedCount}</span>
            </div>
          ` : ''}
          ${this.isProcessing ? `
            <div style="color: #1a73e8; margin-top: 12px; text-align: center;">
              <div style="display: inline-block; animation: spin 1s linear infinite;">⚡</div>
              Processing...
            </div>
          ` : ''}
        </div>
        <div style="margin-top: 12px; display: flex; gap: 8px;">
          ${pendingCount > 0 && !this.isProcessing ? `
            <button class="start-import-btn" style="
              flex: 1;
              padding: 8px 16px;
              background: #0a66c2;
              color: white;
              border: none;
              border-radius: 6px;
              cursor: pointer;
              font-size: 14px;
              font-weight: 600;
              transition: background 0.2s;
            ">Start Import</button>
          ` : ''}
          ${this.queue.length > 0 ? `
            <button class="view-queue-btn" style="
              flex: 1;
              padding: 8px 16px;
              background: #fff;
              color: #0a66c2;
              border: 2px solid #0a66c2;
              border-radius: 6px;
              cursor: pointer;
              font-size: 14px;
              font-weight: 600;
              transition: all 0.2s;
            ">View Details</button>
          ` : ''}
        </div>
        ${this.queue.length === 0 ? `
          <div style="text-align: center; color: #666; margin-top: 12px; font-size: 13px;">
            No profiles in queue.<br>
            Browse LinkedIn to add profiles!
          </div>
        ` : ''}
      `;
      
      // Add event listeners
      const startBtn = container.querySelector('.start-import-btn');
      if (startBtn) {
        startBtn.addEventListener('click', () => this.startProcessing());
      }
      
      const viewBtn = container.querySelector('.view-queue-btn');
      if (viewBtn) {
        viewBtn.addEventListener('click', () => this.openQueueManager());
      }
    }

    async addCurrentProfile() {
      const profileUrl = window.location.href.split('?')[0];
      
      // Extract profile data
      const nameElement = document.querySelector('.pv-text-details__left-panel h1') ||
                         document.querySelector('.text-heading-xlarge');
      const name = nameElement ? nameElement.textContent.trim() : 'Unknown';
      
      await this.addToQueue({
        url: profileUrl,
        name: name
      });
      
      // Update button
      const button = document.querySelector('.import-queue-btn');
      if (button) {
        button.innerHTML = '<span>✓ In Import Queue</span>';
        button.disabled = true;
      }
      
      // Show notification
      this.showNotification(`Added ${name} to import queue`);
    }

    async addToQueue(profileData) {
      if (this.queue.length >= this.MAX_QUEUE_SIZE) {
        this.showNotification('Queue is full. Please process existing items first.', 'error');
        return false;
      }
      
      // Check if already in queue
      if (this.isProfileQueued(profileData.url)) {
        this.showNotification('Profile already in queue', 'warning');
        return false;
      }
      
      const queueItem = {
        id: Date.now().toString(),
        profileUrl: profileData.url,
        profileName: profileData.name,
        status: 'pending',
        addedAt: new Date().toISOString(),
        attempts: 0
      };
      
      this.queue.push(queueItem);
      await this.saveQueue();
      
      return true;
    }

    isProfileQueued(profileUrl) {
      return this.queue.some(item => 
        item.profileUrl === profileUrl && 
        ['pending', 'processing'].includes(item.status)
      );
    }

    toggleSelectAll() {
      const checkboxes = document.querySelectorAll('.import-queue-checkbox input');
      const allChecked = Array.from(checkboxes).every(cb => cb.checked);
      
      checkboxes.forEach(checkbox => {
        checkbox.checked = !allChecked;
      });
    }

    async addSelectedToQueue() {
      const checkboxes = document.querySelectorAll('.import-queue-checkbox input:checked');
      let addedCount = 0;
      
      for (const checkbox of checkboxes) {
        if (this.queue.length >= this.MAX_QUEUE_SIZE) {
          this.showNotification(`Queue full. Added ${addedCount} profiles.`, 'warning');
          break;
        }
        
        const profileData = {
          url: checkbox.dataset.profileUrl,
          name: checkbox.dataset.profileName
        };
        
        if (await this.addToQueue(profileData)) {
          addedCount++;
          checkbox.checked = false;
        }
      }
      
      if (addedCount > 0) {
        this.showNotification(`Added ${addedCount} profiles to import queue`);
      }
    }

    async startProcessing() {
      if (this.isProcessing) {
        this.showNotification('Already processing queue', 'warning');
        return;
      }
      
      this.isProcessing = true;
      await this.processNext();
    }

    shouldContinueProcessing() {
      // Check if we were processing before page reload
      const processingItem = this.queue.find(item => item.status === 'processing');
      return processingItem && this.isProfilePage() && 
             window.location.href.includes(processingItem.profileUrl);
    }

    async processNext() {
      if (!this.isProcessing) return;
      
      const pending = this.queue.find(item => item.status === 'pending');
      if (!pending) {
        this.isProcessing = false;
        this.showNotification('Import queue completed!');
        return;
      }
      
      // Check if we need to navigate
      if (!window.location.href.includes(pending.profileUrl)) {
        // Mark as processing before navigation
        pending.status = 'processing';
        await this.saveQueue();
        
        // Navigate to profile
        window.location.href = pending.profileUrl;
        return; // Page will reload
      }
      
      // We're on the right profile, extract and import
      try {
        pending.status = 'processing';
        await this.saveQueue();
        
        // Wait a bit for page to fully load
        await this.delay(2000);
        
        // Use the existing extraction logic
        const extractBtn = document.querySelector('.extract-profile-btn');
        if (extractBtn) {
          extractBtn.click();
          
          // Wait for extraction to complete
          await this.waitForExtraction();
          
          pending.status = 'completed';
          pending.completedAt = new Date().toISOString();
        } else {
          throw new Error('Extract button not found');
        }
      } catch (error) {
        console.error('Import failed:', error);
        pending.status = 'failed';
        pending.error = error.message;
        pending.attempts++;
        
        if (pending.attempts < 3) {
          // Retry later
          pending.status = 'pending';
        }
      }
      
      await this.saveQueue();
      
      // Human-speed delay before next profile
      const delay = this.MIN_DELAY_MS + Math.random() * (this.MAX_DELAY_MS - this.MIN_DELAY_MS);
      await this.delay(delay);
      
      // Process next
      await this.processNext();
    }

    async waitForExtraction() {
      return new Promise((resolve, reject) => {
        let attempts = 0;
        const maxAttempts = 30; // 30 seconds timeout
        
        const checkInterval = setInterval(() => {
          attempts++;
          
          // Check if extraction completed (button text changed)
          const extractBtn = document.querySelector('.extract-profile-btn');
          if (extractBtn && extractBtn.textContent.includes('✓')) {
            clearInterval(checkInterval);
            resolve();
          } else if (attempts >= maxAttempts) {
            clearInterval(checkInterval);
            reject(new Error('Extraction timeout'));
          }
        }, 1000);
      });
    }

    delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    }

    showNotification(message, type = 'success') {
      const notification = document.createElement('div');
      notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'error' ? '#d93025' : type === 'warning' ? '#f9ab00' : '#0f9d58'};
        color: white;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        z-index: 10000;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        animation: slideIn 0.3s ease;
      `;
      notification.textContent = message;
      
      document.body.appendChild(notification);
      
      setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
      }, 3000);
    }

    openQueueManager() {
      chrome.runtime.sendMessage({
        action: 'openQueueManager'
      });
    }

    setupEventListeners() {
      // Listen for messages from popup/background
      chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === 'getQueueStatus') {
          sendResponse({
            queue: this.queue,
            isProcessing: this.isProcessing
          });
        } else if (request.action === 'startProcessing') {
          this.startProcessing();
          sendResponse({ success: true });
        } else if (request.action === 'clearQueue') {
          this.queue = [];
          this.saveQueue();
          sendResponse({ success: true });
        }
        return true;
      });
    }
  }

  // Add CSS animations
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
      from { transform: translateX(0); opacity: 1; }
      to { transform: translateX(100%); opacity: 0; }
    }
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    .import-queue-status button:hover {
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
  `;
  document.head.appendChild(style);

  // Initialize
  window.__linkedInImportQueue = new LinkedInImportQueue();
  console.log('✅ Promtitude Import Queue: Ready!');
})();