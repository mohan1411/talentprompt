// LinkedIn Search Results Integration
(function() {
  'use strict';
  
  // Check if we're on a search page
  if (!window.location.pathname.includes('/search/')) {
    return;
  }
  
  console.log('[Promtitude] LinkedIn search content script loaded at:', window.location.href);
  
  // State
  let selectedProfiles = new Set();
  let topToolbar = null;
  
  // LinkedIn selectors (with fallbacks)
  const SELECTORS = {
    searchResults: [
      'li.reusable-search__result-container',
      'div.search-result__wrapper',
      'div[data-view-name="search-entity-result-universal-template"]',
      'li[data-chameleon-result-urn]',
      'li[class*="result-container"]',
      'div.entity-result',
      '.entity-result__item'
    ],
    profileLink: [
      'a[href*="/in/"].app-aware-link',
      'a[href*="/in/"][data-test-app-aware-link]',
      'span.entity-result__title-text a[href*="/in/"]',
      'a.entity-result__title-link',
      'a[class*="entity-result__link"]'
    ],
    profileName: [
      'span.entity-result__title-text span[aria-hidden="true"]',
      'span.entity-result__title-line span[aria-hidden="true"]',
      'span[data-anonymize="person-name"]',
      '.entity-result__title-text',
      'span.entity-result__title-line-text'
    ],
    searchContainer: [
      '.search-results-container',
      'div[class*="search-results"]',
      'div.search-results',
      'main[class*="search-results"]'
    ]
  };
  
  // Initialize when page loads
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  function init() {
    console.log('[Promtitude] Starting initialization');
    
    // Add a visible indicator that the script is running
    const indicator = document.createElement('div');
    indicator.textContent = 'Promtitude Loading...';
    indicator.style.cssText = `
      position: fixed;
      top: 10px;
      right: 10px;
      background: #2563eb;
      color: white;
      padding: 8px 16px;
      border-radius: 4px;
      z-index: 9999;
      font-size: 14px;
    `;
    document.body.appendChild(indicator);
    
    setTimeout(() => {
      addTopToolbar();
      enhanceSearchResults();
      observeSearchResults();
      
      // Try enhancing again after a delay in case results loaded late
      setTimeout(() => {
        const checkboxCount = document.querySelectorAll('.promtitude-select-checkbox').length;
        if (checkboxCount === 0) {
          console.log('[Promtitude] No checkboxes found, trying again...');
          enhanceSearchResults();
        }
      }, 3000);
      
      // Remove loading indicator
      indicator.textContent = 'Promtitude Ready!';
      indicator.style.background = '#10b981';
      
      setTimeout(() => {
        indicator.remove();
      }, 2000);
    }, 2000);
  }
  
  // Helper to find element with multiple selectors
  function findElement(parent, selectors) {
    for (const selector of selectors) {
      const element = parent.querySelector(selector);
      if (element) return element;
    }
    return null;
  }
  
  // Helper to find all elements with multiple selectors
  function findAllElements(parent, selectors) {
    for (const selector of selectors) {
      const elements = parent.querySelectorAll(selector);
      if (elements.length > 0) return elements;
    }
    return [];
  }
  
  // Add top toolbar above search results
  function addTopToolbar() {
    if (topToolbar) {
      console.log('[Promtitude] Toolbar already exists');
      return;
    }
    
    // Find search container
    const searchContainer = findElement(document, SELECTORS.searchContainer);
    if (!searchContainer) {
      console.log('[Promtitude] Search container not found, trying alternative selectors...');
      
      // Try alternative approach - find any element that contains search results
      const alternativeContainer = document.querySelector('main') || 
                                   document.querySelector('.scaffold-layout__main') ||
                                   document.querySelector('[role="main"]');
      
      if (!alternativeContainer) {
        console.error('[Promtitude] No suitable container found for toolbar');
        return;
      }
      
      // Use the alternative container
      console.log('[Promtitude] Using alternative container:', alternativeContainer);
      createToolbar(alternativeContainer);
      return;
    }
    
    createToolbar(searchContainer);
  }
  
  function createToolbar(container) {
    console.log('[Promtitude] Creating toolbar in container:', container);
    
    topToolbar = document.createElement('div');
    topToolbar.className = 'promtitude-top-toolbar';
    topToolbar.innerHTML = `
      <div style="background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin: 16px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
          <div style="display: flex; align-items: center; gap: 16px;">
            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
              <input type="checkbox" id="select-all-checkbox" style="width: 18px; height: 18px;">
              <span style="font-weight: 600;">Select All</span>
            </label>
            <span style="color: #6b7280;">
              <span id="selected-count">0</span> of <span id="total-count">0</span> profiles selected
            </span>
          </div>
          <div style="display: flex; gap: 12px;">
            <button id="import-selected-btn" class="promtitude-btn-primary" disabled>
              Import Selected (<span id="import-count">0</span>)
            </button>
          </div>
        </div>
        <div id="import-progress" style="margin-top: 12px; display: none;">
          <div style="background: #e5e7eb; height: 8px; border-radius: 4px; overflow: hidden;">
            <div id="progress-bar" style="background: #2563eb; height: 100%; width: 0%; transition: width 0.3s;"></div>
          </div>
          <p style="margin: 8px 0 0 0; font-size: 12px; color: #6b7280; text-align: center;">
            Importing <span id="current-import">0</span> of <span id="total-import">0</span>
          </p>
        </div>
      </div>
    `;
    
    // Find the best place to insert the toolbar
    const firstResult = container.querySelector('ul');
    const resultsContainer = container.querySelector('.search-results-container');
    
    if (firstResult && firstResult.parentElement) {
      console.log('[Promtitude] Inserting toolbar before results list');
      firstResult.parentElement.insertBefore(topToolbar, firstResult);
    } else if (resultsContainer) {
      console.log('[Promtitude] Prepending toolbar to results container');
      resultsContainer.prepend(topToolbar);
    } else {
      console.log('[Promtitude] Prepending toolbar to container');
      container.prepend(topToolbar);
    }
    
    // Add event listeners
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    const importBtn = document.getElementById('import-selected-btn');
    
    if (selectAllCheckbox) {
      selectAllCheckbox.addEventListener('change', handleSelectAll);
    } else {
      console.error('[Promtitude] Select all checkbox not found');
    }
    
    if (importBtn) {
      importBtn.addEventListener('click', bulkImportProfiles);
    } else {
      console.error('[Promtitude] Import button not found');
    }
    
    console.log('[Promtitude] Toolbar created successfully');
  }
  
  // Enhance search result items
  function enhanceSearchResults() {
    console.log('[Promtitude] Enhancing search results...');
    
    // Try all possible selectors
    let resultItems = findAllElements(document, SELECTORS.searchResults);
    
    // If no results found with primary selectors, try a more general approach
    if (resultItems.length === 0) {
      console.log('[Promtitude] No results with primary selectors, trying alternative approach...');
      
      // Approach 1: Look for any list items that contain profile links
      const allListItems = document.querySelectorAll('li');
      resultItems = Array.from(allListItems).filter(li => {
        const hasProfileLink = li.querySelector('a[href*="/in/"]');
        const hasNoControl = !li.querySelector('.promtitude-profile-control');
        const hasContent = li.textContent.length > 50; // Filter out navigation items
        return hasProfileLink && hasNoControl && hasContent;
      });
      
      // Approach 2: If still no results, look for divs with profile images
      if (resultItems.length === 0) {
        console.log('[Promtitude] Still no results, trying image-based approach...');
        const profileImages = document.querySelectorAll('img[class*="presence-entity__image"], img[class*="entity-image"]');
        resultItems = Array.from(profileImages).map(img => {
          // Find the parent container that likely represents the whole profile card
          let parent = img.parentElement;
          while (parent && parent.parentElement) {
            if (parent.querySelector('a[href*="/in/"]') && 
                !parent.querySelector('.promtitude-profile-control')) {
              return parent;
            }
            parent = parent.parentElement;
          }
          return null;
        }).filter(Boolean);
      }
    }
    
    console.log(`[Promtitude] Found ${resultItems.length} search results`);
    
    let enhancedCount = 0;
    
    resultItems.forEach(item => {
      // Skip if already processed
      if (item.querySelector('.promtitude-profile-control')) return;
      
      // Get profile link - try multiple approaches
      let profileLink = findElement(item, SELECTORS.profileLink);
      
      // If not found, try a more direct approach
      if (!profileLink) {
        profileLink = item.querySelector('a[href*="/in/"]');
      }
      
      if (!profileLink || !profileLink.href) {
        console.log('[Promtitude] No profile link found in item:', item);
        return;
      }
      
      const profileUrl = profileLink.href.split('?')[0];
      const profileId = profileUrl.split('/in/')[1]?.split('/')[0];
      
      if (!profileId) {
        console.log('[Promtitude] No profile ID found in URL:', profileUrl);
        return;
      }
      
      // Find name element
      const nameEl = findElement(item, SELECTORS.profileName);
      const name = nameEl?.textContent.trim() || 'Unknown';
      
      // Create control container
      const controlContainer = document.createElement('div');
      controlContainer.className = 'promtitude-profile-control';
      controlContainer.style.cssText = `
        position: absolute;
        top: 8px;
        right: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
        z-index: 100;
        background: white;
        padding: 4px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
      `;
      
      // Add checkbox
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.className = 'promtitude-select-checkbox';
      checkbox.dataset.profileId = profileId;
      checkbox.dataset.profileUrl = profileUrl;
      checkbox.dataset.profileName = name;
      checkbox.style.cssText = 'width: 18px; height: 18px; cursor: pointer;';
      
      // Add import button (initially hidden)
      const importBtn = document.createElement('button');
      importBtn.className = 'promtitude-import-btn';
      importBtn.textContent = 'Import';
      importBtn.style.cssText = `
        display: none;
        padding: 6px 12px;
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 12px;
        cursor: pointer;
      `;
      
      // Add status indicator
      const statusIndicator = document.createElement('div');
      statusIndicator.className = 'promtitude-status-indicator';
      statusIndicator.style.cssText = `
        display: none;
        padding: 4px 8px;
        background: #10b981;
        color: white;
        border-radius: 4px;
        font-size: 11px;
      `;
      statusIndicator.textContent = '✓ Imported';
      
      controlContainer.appendChild(checkbox);
      controlContainer.appendChild(importBtn);
      controlContainer.appendChild(statusIndicator);
      
      // Add hover effect to show import button
      item.addEventListener('mouseenter', () => {
        if (!checkbox.checked && statusIndicator.style.display === 'none') {
          importBtn.style.display = 'block';
        }
      });
      
      item.addEventListener('mouseleave', () => {
        importBtn.style.display = 'none';
      });
      
      // Checkbox handler
      checkbox.addEventListener('change', () => {
        toggleProfileSelection(profileId, checkbox.checked);
        updateSelectionCount();
      });
      
      // Import button handler
      importBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        await importSingleProfile(profileUrl, name);
        importBtn.style.display = 'none';
        statusIndicator.style.display = 'block';
      });
      
      // Make result item relatively positioned
      if (!item.style.position || item.style.position === 'static') {
        item.style.position = 'relative';
      }
      
      // Try to find a better container within the item
      const cardContainer = item.querySelector('.entity-result__content') || 
                           item.querySelector('[class*="entity-result"]') ||
                           item;
                           
      // Ensure the container is positioned
      if (cardContainer !== item && (!cardContainer.style.position || cardContainer.style.position === 'static')) {
        cardContainer.style.position = 'relative';
      }
      
      cardContainer.appendChild(controlContainer);
      
      // Check if already imported
      checkProfileExists(profileUrl, statusIndicator, checkbox);
      
      enhancedCount++;
      
      // Debug log
      console.log(`[Promtitude] Enhanced profile ${enhancedCount}: ${name} (${profileId})`);
    });
    
    console.log(`[Promtitude] Enhanced ${enhancedCount} profiles total`);
    updateSelectionCount();
  }
  
  // Toggle profile selection
  function toggleProfileSelection(profileId, isSelected) {
    if (isSelected) {
      selectedProfiles.add(profileId);
    } else {
      selectedProfiles.delete(profileId);
    }
  }
  
  // Handle select all
  function handleSelectAll(e) {
    const isChecked = e.target.checked;
    const checkboxes = document.querySelectorAll('.promtitude-select-checkbox:not(:disabled)');
    
    checkboxes.forEach(checkbox => {
      checkbox.checked = isChecked;
      toggleProfileSelection(checkbox.dataset.profileId, isChecked);
    });
    
    updateSelectionCount();
  }
  
  // Update selection count
  function updateSelectionCount() {
    const totalCheckboxes = document.querySelectorAll('.promtitude-select-checkbox').length;
    const selectedCount = selectedProfiles.size;
    
    // Update counts
    const selectedEl = document.getElementById('selected-count');
    const totalEl = document.getElementById('total-count');
    const importCountEl = document.getElementById('import-count');
    const importBtn = document.getElementById('import-selected-btn');
    
    if (selectedEl) selectedEl.textContent = selectedCount;
    if (totalEl) totalEl.textContent = totalCheckboxes;
    if (importCountEl) importCountEl.textContent = selectedCount;
    
    // Enable/disable import button
    if (importBtn) {
      importBtn.disabled = selectedCount === 0;
    }
    
    // Update select all checkbox state
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    if (selectAllCheckbox) {
      const nonDisabledCheckboxes = document.querySelectorAll('.promtitude-select-checkbox:not(:disabled)').length;
      selectAllCheckbox.checked = nonDisabledCheckboxes > 0 && selectedCount === nonDisabledCheckboxes;
      selectAllCheckbox.indeterminate = selectedCount > 0 && selectedCount < nonDisabledCheckboxes;
    }
  }
  
  // Bulk import profiles
  async function bulkImportProfiles() {
    if (selectedProfiles.size === 0) return;
    
    const authToken = await getAuthToken();
    if (!authToken) {
      showStatus('Please login to Promtitude', 'error');
      return;
    }
    
    // Show progress
    const progressDiv = document.getElementById('import-progress');
    const progressBar = document.getElementById('progress-bar');
    const currentImportEl = document.getElementById('current-import');
    const totalImportEl = document.getElementById('total-import');
    
    if (progressDiv) progressDiv.style.display = 'block';
    if (totalImportEl) totalImportEl.textContent = selectedProfiles.size;
    
    // Disable buttons
    const importBtn = document.getElementById('import-selected-btn');
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    if (importBtn) importBtn.disabled = true;
    if (selectAllCheckbox) selectAllCheckbox.disabled = true;
    
    let imported = 0;
    let failed = 0;
    
    // Get profile data from checkboxes
    const profilesToImport = [];
    document.querySelectorAll('.promtitude-select-checkbox:checked').forEach(checkbox => {
      profilesToImport.push({
        profileId: checkbox.dataset.profileId,
        profileUrl: checkbox.dataset.profileUrl,
        profileName: checkbox.dataset.profileName
      });
    });
    
    // Import profiles one by one
    for (const profile of profilesToImport) {
      if (currentImportEl) currentImportEl.textContent = imported + 1;
      
      try {
        await importProfile({
          linkedin_url: profile.profileUrl,
          name: profile.profileName
        });
        
        imported++;
        
        // Update UI to show imported status
        const checkbox = document.querySelector(`[data-profile-id="${profile.profileId}"]`);
        if (checkbox) {
          checkbox.checked = false;
          checkbox.disabled = true;
          const statusIndicator = checkbox.parentElement.querySelector('.promtitude-status-indicator');
          if (statusIndicator) statusIndicator.style.display = 'block';
        }
        
      } catch (error) {
        failed++;
        console.error(`Failed to import ${profile.profileName}:`, error);
      }
      
      // Update progress
      const progress = (imported + failed) / profilesToImport.length * 100;
      if (progressBar) progressBar.style.width = `${progress}%`;
      
      // Delay between imports (2-4 seconds)
      const delay = 2000 + Math.random() * 2000;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
    
    // Clear selection
    selectedProfiles.clear();
    updateSelectionCount();
    
    // Hide progress
    setTimeout(() => {
      if (progressDiv) progressDiv.style.display = 'none';
      if (progressBar) progressBar.style.width = '0%';
    }, 2000);
    
    // Re-enable buttons
    if (importBtn) importBtn.disabled = false;
    if (selectAllCheckbox) selectAllCheckbox.disabled = false;
    
    // Show result
    showStatus(`Imported ${imported} profiles successfully!`, 'success');
  }
  
  // Import single profile
  async function importProfile(profileData) {
    const authToken = await getAuthToken();
    const API_URL = 'https://talentprompt-production.up.railway.app/api/v1';
    
    const response = await fetch(`${API_URL}/linkedin/import-profile`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(profileData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Import failed');
    }
    
    return await response.json();
  }
  
  // Import single profile (for individual import button)
  async function importSingleProfile(profileUrl, profileName) {
    const authToken = await getAuthToken();
    if (!authToken) {
      showStatus('Please login to Promtitude', 'error');
      return;
    }
    
    try {
      await importProfile({
        linkedin_url: profileUrl,
        name: profileName
      });
      showStatus(`${profileName} imported successfully!`, 'success');
    } catch (error) {
      showStatus(`Failed to import ${profileName}`, 'error');
    }
  }
  
  // Check if profile exists
  async function checkProfileExists(profileUrl, statusIndicator, checkbox) {
    try {
      chrome.runtime.sendMessage({
        action: 'checkProfileExists',
        linkedin_url: profileUrl,
        authToken: await getAuthToken()
      }, response => {
        if (response && response.exists) {
          if (statusIndicator) statusIndicator.style.display = 'block';
          if (checkbox) {
            checkbox.disabled = true;
            checkbox.title = 'Already imported';
          }
        }
      });
    } catch (error) {
      console.error('Error checking profile:', error);
    }
  }
  
  // Get auth token
  async function getAuthToken() {
    return new Promise((resolve) => {
      chrome.storage.local.get(['authToken'], (result) => {
        resolve(result.authToken);
      });
    });
  }
  
  // Show status notification
  function showStatus(message, type) {
    const status = document.createElement('div');
    status.className = `talentprompt-status ${type}`;
    status.textContent = message;
    document.body.appendChild(status);
    
    setTimeout(() => {
      status.remove();
    }, 5000);
  }
  
  // Observe search results for dynamic loading
  function observeSearchResults() {
    const observer = new MutationObserver((mutations) => {
      // Check if new search results were added
      const hasNewResults = mutations.some(mutation => {
        return Array.from(mutation.addedNodes).some(node => {
          if (node.nodeType === 1) { // Element node
            return node.matches && (
              SELECTORS.searchResults.some(selector => node.matches(selector)) ||
              node.querySelector && SELECTORS.searchResults.some(selector => node.querySelector(selector))
            );
          }
          return false;
        });
      });
      
      if (hasNewResults) {
        console.log('[Promtitude] New search results detected');
        enhanceSearchResults();
      }
    });
    
    // Try to find the results container
    const container = findElement(document, SELECTORS.searchContainer);
    if (container) {
      console.log('[Promtitude] Observing search results container');
      observer.observe(container, { 
        childList: true, 
        subtree: true,
        attributes: false 
      });
    } else {
      // Fallback: observe the entire main content area
      const main = document.querySelector('main');
      if (main) {
        console.log('[Promtitude] Observing main content area');
        observer.observe(main, { 
          childList: true, 
          subtree: true,
          attributes: false 
        });
      }
    }
  }
  
  // Listen for messages from popup
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('[Promtitude] Received message:', request.action);
    
    if (request.action === 'bulkImport') {
      // For direct bulk import from popup, select all non-imported profiles first
      const checkboxes = document.querySelectorAll('.promtitude-select-checkbox:not(:disabled)');
      checkboxes.forEach(checkbox => {
        checkbox.checked = true;
        toggleProfileSelection(checkbox.dataset.profileId, true);
      });
      
      updateSelectionCount();
      
      // Start bulk import
      bulkImportProfiles().then(() => {
        sendResponse({ success: true, count: selectedProfiles.size });
      }).catch(error => {
        sendResponse({ success: false, error: error.message });
      });
      
      return true;
    }
    
    if (request.action === 'getImportableCount') {
      const count = document.querySelectorAll('.promtitude-select-checkbox:not(:disabled)').length;
      sendResponse({ count: count });
      return true;
    }
    
    if (request.action === 'focusBulkImportTool') {
      console.log('[Promtitude] Focus bulk import tool requested');
      
      // Make sure toolbar exists
      if (!topToolbar) {
        console.log('[Promtitude] Toolbar not found, creating it...');
        addTopToolbar();
        enhanceSearchResults();
      }
      
      // Give it time to render
      setTimeout(() => {
        if (topToolbar) {
          console.log('[Promtitude] Scrolling to toolbar');
          topToolbar.scrollIntoView({ behavior: 'smooth', block: 'start' });
          
          // Add highlight effect
          const toolbar = topToolbar.querySelector('div');
          if (toolbar) {
            toolbar.style.boxShadow = '0 0 20px rgba(37, 99, 235, 0.8)';
            toolbar.style.transform = 'scale(1.02)';
            
            setTimeout(() => {
              toolbar.style.boxShadow = '';
              toolbar.style.transform = '';
            }, 2000);
          }
          
          sendResponse({ success: true });
        } else {
          console.error('[Promtitude] Failed to create toolbar');
          sendResponse({ success: false, error: 'Failed to create toolbar' });
        }
      }, 500);
      
      return true; // Async response
    }
  });
  
})();