/**
 * Bulk import with a sidebar approach
 * This will definitely work as it doesn't modify LinkedIn's content
 */

(function() {
  'use strict';
  
  if (window.__bulkImportSidebar) {
    return;
  }
  window.__bulkImportSidebar = true;
  
  // Check if we have access to Chrome APIs
  if (typeof chrome === 'undefined' || !chrome.storage) {
    return;
  }
  
  // Helper function to check if extension context is still valid
  function isExtensionContextValid() {
    try {
      // Try to access chrome.runtime to check if context is valid
      return chrome.runtime && chrome.runtime.id;
    } catch (e) {
      return false;
    }
  }
  
  const selectedProfiles = new Set();
  
  // Listen for messages from popup
  try {
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.action === 'showBulkImportSidebar') {
        // Only allow on search results pages (specifically people search)
        if (!window.location.pathname.includes('/search/results/')) {
          sendResponse({ success: false, error: 'Bulk import is only available on search results pages' });
          return true;
        }
        
        try {
          // Initialize the sidebar if not already done
          if (!document.querySelector('#bulk-import-sidebar')) {
            init();
          } else {
            // Show and highlight existing sidebar
            const sidebar = document.querySelector('#bulk-import-sidebar');
            sidebar.style.display = 'flex';
            sidebar.style.boxShadow = '0 4px 20px rgba(10, 102, 194, 0.8)';
            setTimeout(() => {
              sidebar.style.boxShadow = '0 4px 20px rgba(0,0,0,0.2)';
            }, 2000);
          }
          sendResponse({ success: true });
        } catch (error) {
          sendResponse({ success: false, error: error.message });
        }
        return true;
      }
      
      // Handle logout message
      if (request.action === 'userLoggedOut') {
        const sidebar = document.querySelector('#bulk-import-sidebar');
        if (sidebar) {
          sidebar.remove();
        }
        // Clear any stored state
        selectedProfiles.clear();
        return true;
      }
    });
  } catch (error) {
  }
  
  // Auto-initialize disabled - sidebar only opens when user clicks button
  // if (window.location.pathname.includes('/search/results/')) {
  //   setTimeout(init, 2000);
  // }
  
  // Monitor URL changes to hide sidebar when leaving search pages
  let lastUrl = window.location.href;
  const urlObserver = new MutationObserver(() => {
    const currentUrl = window.location.href;
    if (currentUrl !== lastUrl) {
      lastUrl = currentUrl;
      
      // Hide sidebar if we're no longer on a search results page
      if (!window.location.pathname.includes('/search/results/')) {
        const sidebar = document.querySelector('#bulk-import-sidebar');
        if (sidebar) {
          sidebar.style.display = 'none';
        }
      }
    }
  });
  
  // Start observing URL changes
  urlObserver.observe(document, { subtree: true, childList: true });
  
  function init() {
    if (!window.location.pathname.includes('/search/results/')) {
      return;
    }
    
    // Remove any existing sidebar
    document.querySelector('#bulk-import-sidebar')?.remove();
    
    createSidebar();
    
    // Try updating profile list multiple times as LinkedIn loads dynamically
    updateProfileList();
    setTimeout(updateProfileList, 1000);
    setTimeout(updateProfileList, 2000);
    setTimeout(updateProfileList, 3000);
    
    observeResults();
  }
  
  function createSidebar() {
    const sidebar = document.createElement('div');
    sidebar.id = 'bulk-import-sidebar';
    sidebar.style.cssText = `
      position: fixed;
      top: 80px;
      right: 20px;
      width: 350px;
      max-height: 80vh;
      background: white;
      border: 2px solid #0a66c2;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.2);
      z-index: 10000;
      display: flex;
      flex-direction: column;
      font-family: -apple-system, sans-serif;
    `;
    
    sidebar.innerHTML = `
      <div style="
        padding: 16px 20px;
        background: #0a66c2;
        color: white;
        border-radius: 10px 10px 0 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
      ">
        <h3 style="margin: 0; font-size: 18px; font-weight: bold;">
          🚀 Bulk Import Profiles
        </h3>
        <button id="sidebar-toggle" style="
          background: none;
          border: none;
          color: white;
          font-size: 20px;
          cursor: pointer;
          padding: 0;
          width: 30px;
          height: 30px;
        ">−</button>
      </div>
      
      <div id="sidebar-content" style="flex: 1; display: flex; flex-direction: column;">
        <div style="padding: 16px 20px; border-bottom: 1px solid #e5e7eb;">
          <div style="margin-bottom: 12px;">
            <span id="selection-count" style="font-size: 16px; font-weight: bold; color: #059669;">
              0 profiles selected
            </span>
          </div>
          <div style="display: flex; gap: 8px;">
            <button id="select-all-btn" style="
              flex: 1;
              padding: 8px 12px;
              background: white;
              color: #0a66c2;
              border: 2px solid #0a66c2;
              border-radius: 6px;
              font-weight: 600;
              cursor: pointer;
              font-size: 13px;
              transition: all 0.2s;
            ">Select All</button>
            <button id="clear-all-btn" style="
              flex: 1;
              padding: 8px 12px;
              background: white;
              color: #dc2626;
              border: 2px solid #dc2626;
              border-radius: 6px;
              font-weight: 600;
              cursor: pointer;
              font-size: 13px;
              transition: all 0.2s;
            ">Clear All</button>
          </div>
        </div>
        
        <div id="profile-list" style="
          flex: 1;
          overflow-y: auto;
          padding: 12px;
          max-height: 400px;
        ">
          <div style="text-align: center; color: #9ca3af; padding: 20px;">
            Loading profiles...
          </div>
        </div>
        
        <div style="padding: 16px 20px; border-top: 1px solid #e5e7eb;">
          <button id="add-to-queue-btn" style="
            width: 100%;
            padding: 12px;
            background: #0a66c2;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            font-size: 15px;
            transition: all 0.2s;
          ">Add Selected to Import Queue</button>
          <div id="status-message" style="
            margin-top: 12px;
            padding: 10px;
            border-radius: 6px;
            font-size: 13px;
            text-align: center;
            display: none;
          "></div>
        </div>
      </div>
    `;
    
    document.body.appendChild(sidebar);
    
    // Add hover effects
    const buttons = sidebar.querySelectorAll('button');
    buttons.forEach(btn => {
      if (btn.id !== 'sidebar-toggle') {
        btn.onmouseover = () => {
          btn.style.transform = 'translateY(-1px)';
          btn.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
        };
        btn.onmouseout = () => {
          btn.style.transform = 'translateY(0)';
          btn.style.boxShadow = 'none';
        };
      }
    });
    
    // Event listeners
    document.getElementById('sidebar-toggle').onclick = toggleSidebar;
    document.getElementById('select-all-btn').onclick = selectAll;
    document.getElementById('clear-all-btn').onclick = clearAll;
    document.getElementById('add-to-queue-btn').onclick = addToQueue;
  }
  
  function updateProfileList() {
    
    // First, let's debug what's on the page
    const debugSelectors = [
      'li.reusable-search__result-container',
      'div.entity-result',
      'div[data-view-name="search-entity-result-universal-template"]',
      'li[data-view-name="search-entity-result-item"]',
      'div.search-result__wrapper',
      'li.search-result__occluded-item',
      'div.scaffold-finite-scroll__content > ul > li',
      'li[class*="reusable-search__result"]',
      'div[class*="entity-result"]',
      '[data-test-search-result]',
      '.search-results-container li',
      'main li[class*="result"]'
    ];
    
    let results = [];
    let foundSelector = null;
    
    // Try each selector and log what we find
    for (const selector of debugSelectors) {
      const elements = document.querySelectorAll(selector);
      if (elements.length > 0 && !foundSelector) {
        // Verify these are profile results by checking for profile links
        const validResults = Array.from(elements).filter(el => 
          el.querySelector('a[href*="/in/"]')
        );
        if (validResults.length > 0) {
          results = validResults;
          foundSelector = selector;
          break;
        }
      }
    }
    
    // If still no results, try a more general approach
    if (results.length === 0) {
      const allProfileLinks = document.querySelectorAll('a[href*="/in/"]:not([href*="/company/"]):not([href*="/school/"])');
      const uniqueContainers = new Set();
      
      allProfileLinks.forEach(link => {
        // Find the closest list item or result container
        let container = link.closest('li');
        if (!container) {
          container = link.closest('div[class*="result"]');
        }
        if (!container) {
          container = link.closest('[class*="entity"]');
        }
        if (container && container.contains(link)) {
          uniqueContainers.add(container);
        }
      });
      
      results = Array.from(uniqueContainers);
    }
    
    const profileList = document.getElementById('profile-list');
    
    if (!profileList) {
      return;
    }
    
    
    if (results.length === 0) {
      profileList.innerHTML = `
        <div style="text-align: center; color: #9ca3af; padding: 20px;">
          <div style="margin-bottom: 10px;">No profiles detected</div>
          <div style="font-size: 12px; line-height: 1.5;">
            Make sure you're on a LinkedIn people search page.<br>
            Try refreshing the page or scrolling to load more results.
          </div>
        </div>
      `;
      
      // Log page structure for debugging
      return;
    }
    
    profileList.innerHTML = '';
    
    results.forEach((result, index) => {
      const profileLink = result.querySelector('a[href*="/in/"]');
      if (!profileLink) {
        return;
      }
      
      const profileUrl = profileLink.href.split('?')[0];
      
      // Try multiple selectors for name - expanded list
      let name = `Profile ${index + 1}`;
      const nameSelectors = [
        'span[aria-hidden="true"]',
        'span.entity-result__title-text',
        'a.app-aware-link span[aria-hidden="true"]',
        'span.entity-result__title-line span[aria-hidden="true"]',
        '.entity-result__title-text a span',
        '.entity-result__title',
        '.entity-result__title-line',
        '.actor-name',
        '.search-result__title',
        'h3.search-results__total',
        'span[data-anonymize="person-name"]',
        'a[data-control-name="search_srp_result"] span',
        '[class*="name"] span[aria-hidden="true"]',
        'h3 span[dir="ltr"]',
        '[class*="title"] span[aria-hidden="true"]'
      ];
      
      for (const selector of nameSelectors) {
        const element = result.querySelector(selector);
        if (element) {
          const text = element.textContent.trim();
          if (text && text.length > 0 && !text.includes('LinkedIn Member')) {
            name = text.split('\n')[0].trim(); // Take first line only
            break;
          }
        }
      }
      
      // Try to get title and location with expanded selectors
      const titleSelectors = [
        '.entity-result__primary-subtitle',
        'div[class*="primary-subtitle"]',
        '.entity-result__summary',
        'span[class*="headline"]',
        '.search-result__truncate',
        'div.linked-area + div',
        '[data-anonymize="title"]'
      ];
      
      const locationSelectors = [
        '.entity-result__secondary-subtitle',
        'div[class*="secondary-subtitle"]',
        '.entity-result__summary + div',
        'span[class*="location"]',
        '[data-anonymize="location"]',
        '.search-result__snippets + div'
      ];
      
      let title = '';
      for (const selector of titleSelectors) {
        const element = result.querySelector(selector);
        if (element && element.textContent.trim()) {
          title = element.textContent.trim();
          break;
        }
      }
      
      let location = '';
      for (const selector of locationSelectors) {
        const element = result.querySelector(selector);
        if (element && element.textContent.trim()) {
          location = element.textContent.trim();
          break;
        }
      }
      
      
      const profileItem = document.createElement('div');
      profileItem.style.cssText = `
        padding: 12px;
        margin-bottom: 8px;
        background: #f9fafb;
        border: 2px solid ${selectedProfiles.has(profileUrl) ? '#059669' : '#e5e7eb'};
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
      `;
      
      profileItem.innerHTML = `
        <div style="display: flex; align-items: start; gap: 12px;">
          <input type="checkbox" 
            id="profile-${index}"
            ${selectedProfiles.has(profileUrl) ? 'checked' : ''}
            style="
              width: 20px;
              height: 20px;
              margin-top: 2px;
              cursor: pointer;
              accent-color: #0a66c2;
            "
          />
          <div style="flex: 1;">
            <div style="font-weight: 600; color: #1f2937; margin-bottom: 2px;">
              ${name}
            </div>
            ${title ? `<div style="font-size: 13px; color: #6b7280;">${title}</div>` : ''}
            ${location ? `<div style="font-size: 12px; color: #9ca3af;">${location}</div>` : ''}
          </div>
        </div>
      `;
      
      const checkbox = profileItem.querySelector('input');
      
      // Store data on the profile item
      profileItem.dataset.profileUrl = profileUrl;
      profileItem.dataset.profileName = name;
      
      // Click handler
      const handleClick = (e) => {
        if (e.target.type !== 'checkbox') {
          checkbox.checked = !checkbox.checked;
        }
        
        if (checkbox.checked) {
          selectedProfiles.add(profileUrl);
          profileItem.style.border = '2px solid #059669';
          profileItem.style.background = '#d1fae5';
        } else {
          selectedProfiles.delete(profileUrl);
          profileItem.style.border = '2px solid #e5e7eb';
          profileItem.style.background = '#f9fafb';
        }
        
        updateSelectionCount();
      };
      
      profileItem.onclick = handleClick;
      
      // Hover effect
      profileItem.onmouseover = () => {
        if (!checkbox.checked) {
          profileItem.style.background = '#f3f4f6';
        }
      };
      profileItem.onmouseout = () => {
        if (!checkbox.checked) {
          profileItem.style.background = '#f9fafb';
        }
      };
      
      profileList.appendChild(profileItem);
    });
    
    updateSelectionCount();
  }
  
  function selectAll() {
    const checkboxes = document.querySelectorAll('#profile-list input[type="checkbox"]');
    checkboxes.forEach(cb => {
      if (!cb.checked) {
        cb.click();
      }
    });
  }
  
  function clearAll() {
    const checkboxes = document.querySelectorAll('#profile-list input[type="checkbox"]');
    checkboxes.forEach(cb => {
      if (cb.checked) {
        cb.click();
      }
    });
  }
  
  function updateSelectionCount() {
    const count = selectedProfiles.size;
    const countEl = document.getElementById('selection-count');
    if (countEl) {
      countEl.textContent = `${count} profile${count !== 1 ? 's' : ''} selected`;
    }
  }
  
  async function addToQueue() {
    
    if (selectedProfiles.size === 0) {
      showMessage('Please select at least one profile', 'error');
      return;
    }
    
    try {
      // Prepare profiles to add
      const profilesToAdd = [];
      const profileItems = document.querySelectorAll('#profile-list > div');
      
      profileItems.forEach(item => {
        const checkbox = item.querySelector('input[type="checkbox"]');
        if (checkbox?.checked) {
          const profileUrl = item.dataset.profileUrl;
          const profileName = item.dataset.profileName;
          
          
          if (profileUrl) {
            profilesToAdd.push({
              profileUrl: profileUrl,
              profileName: profileName || 'Unknown Profile'
            });
          }
        }
      });
      
      if (profilesToAdd.length === 0) {
        showMessage('No valid profiles selected', 'error');
        return;
      }
      
      // Check if extension context is still valid before sending message
      if (!isExtensionContextValid()) {
        throw new Error('Extension context invalidated. Please refresh the page.');
      }
      
      // Send message to background script to add to queue
      const response = await chrome.runtime.sendMessage({
        action: 'addToQueue',
        profiles: profilesToAdd
      });
      
      if (response.success) {
        
        // Update badge
        try {
          await chrome.runtime.sendMessage({
            action: 'updateQueueBadge',
            count: response.pendingCount
          });
        } catch (e) {
        }
        
        if (response.addedCount > 0) {
          showMessage(`✅ Added ${response.addedCount} profiles to import queue!`, 'success');
          clearAll();
        } else {
          showMessage('All selected profiles are already in queue', 'error');
        }
      } else {
        throw new Error(response.error || 'Failed to add profiles');
      }
    } catch (error) {
      
      // Handle extension context invalidated error
      if (error.message && error.message.includes('Extension context invalidated')) {
        showMessage('Extension was updated. Please refresh the page and try again.', 'error');
        
        // Optionally, try to reload the page automatically after a delay
        setTimeout(() => {
          if (confirm('The extension was updated. Would you like to refresh the page now?')) {
            window.location.reload();
          }
        }, 1000);
      } else {
        const errorMessage = error.message || 'Error adding profiles to queue';
        showMessage(`Error: ${errorMessage}`, 'error');
      }
    }
  }
  
  function showMessage(text, type) {
    const msg = document.getElementById('status-message');
    if (msg) {
      msg.textContent = text;
      msg.style.display = 'block';
      msg.style.background = type === 'success' ? '#d1fae5' : '#fee2e2';
      msg.style.color = type === 'success' ? '#065f46' : '#991b1b';
      msg.style.border = `2px solid ${type === 'success' ? '#059669' : '#dc2626'}`;
      
      setTimeout(() => {
        msg.style.display = 'none';
      }, 4000);
    }
  }
  
  function toggleSidebar() {
    const content = document.getElementById('sidebar-content');
    const toggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('bulk-import-sidebar');
    
    if (content.style.display === 'none') {
      content.style.display = 'flex';
      toggle.textContent = '−';
      sidebar.style.width = '350px';
    } else {
      content.style.display = 'none';
      toggle.textContent = '+';
      sidebar.style.width = 'auto';
    }
  }
  
  function observeResults() {
    const observer = new MutationObserver(() => {
      setTimeout(updateProfileList, 500);
    });
    
    // Try multiple container selectors
    const containerSelectors = [
      '.scaffold-finite-scroll__content',
      '.reusable-search__entity-result-list',
      '.search-results-container',
      'div[role="main"]',
      'main',
      '.application-outlet'
    ];
    
    let container = null;
    for (const selector of containerSelectors) {
      container = document.querySelector(selector);
      if (container) {
        break;
      }
    }
    
    if (container) {
      observer.observe(container, {
        childList: true,
        subtree: true,
        characterData: true
      });
    } else {
      // Fallback: observe the entire body
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    }
  }
  
  // Reinitialize on navigation
  let lastNavigationUrl = location.href;
  new MutationObserver(() => {
    const url = location.href;
    if (url !== lastNavigationUrl) {
      lastNavigationUrl = url;
      if (url.includes('/search/results/')) {
        selectedProfiles.clear();
        setTimeout(init, 2000);
      }
    }
  }).observe(document, { subtree: true, childList: true });
  
  // Add debug button for troubleshooting
  function addDebugButton() {
    const debugBtn = document.createElement('button');
    debugBtn.id = 'bulk-import-debug';
    debugBtn.style.cssText = `
      position: fixed;
      top: 140px;
      right: 20px;
      padding: 10px 20px;
      background: #dc2626;
      color: white;
      border: none;
      border-radius: 8px;
      font-weight: bold;
      cursor: pointer;
      z-index: 10001;
      font-size: 14px;
    `;
    debugBtn.textContent = '🐛 Debug Profiles';
    
    debugBtn.onclick = () => {
      
      // Check profile items in sidebar
      const profileItems = document.querySelectorAll('#profile-list > div');
      profileItems.forEach((item, i) => {
        const checkbox = item.querySelector('input[type="checkbox"]');
      });
      
      // Check for various profile containers
      const selectors = [
        'li.reusable-search__result-container',
        'div.entity-result',
        'li[class*="result"]',
        'a[href*="/in/"]'
      ];
      
      selectors.forEach(sel => {
        const elements = document.querySelectorAll(sel);
        if (elements.length > 0 && elements.length < 5) {
          elements.forEach((el, i) => {
          });
        }
      });
      
      // Try to manually trigger profile list update
      updateProfileList();
      
      // Test Chrome storage
      chrome.storage.local.get('linkedinImportQueue', (result) => {
      });
      
    };
    
    document.body.appendChild(debugBtn);
  }
  
  // Debug button disabled for production
  // setTimeout(addDebugButton, 3000);
  
})();