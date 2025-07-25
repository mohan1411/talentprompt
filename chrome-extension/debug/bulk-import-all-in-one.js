/**
 * All-in-one bulk import solution
 * Single file to avoid conflicts
 */

(function() {
  'use strict';
  
  // Prevent multiple initializations
  if (window.__bulkImportInitialized) return;
  window.__bulkImportInitialized = true;
  
  console.log('🎯 Bulk Import: Initializing...');
  
  // Wait for page to settle
  setTimeout(initBulkImport, 2000);
  
  // Also try again after 4 seconds in case LinkedIn loads slowly
  setTimeout(initBulkImport, 4000);
  
  function initBulkImport() {
    // Only run on search pages
    if (!window.location.pathname.includes('/search/results/')) {
      return;
    }
    
    console.log('🎯 Initializing bulk import on search page');
    
    // Remove any existing UI elements first
    document.querySelectorAll('.bulk-import-ui-element').forEach(el => el.remove());
    
    // Inject checkboxes
    injectCheckboxes();
    
    // Create control panel
    createControlPanel();
    
    // Watch for new results
    observeResults();
    
    // Add debug mode to see what's happening
    addDebugMode();
  }
  
  function injectCheckboxes() {
    // Find all search results using the confirmed selector
    const results = document.querySelectorAll('li.reusable-search__result-container');
    console.log(`🎯 Processing ${results.length} search results`);
    
    results.forEach((result, index) => {
      // Skip if already processed
      if (result.querySelector('.bulk-import-checkbox-container')) return;
      
      // Create a very visible checkbox container
      const container = document.createElement('div');
      container.className = 'bulk-import-checkbox-container';
      container.style.cssText = `
        position: absolute;
        top: 10px;
        left: 10px;
        width: 40px;
        height: 40px;
        background: white;
        border: 3px solid #0a66c2;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
      `;
      
      // Create checkbox
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.className = 'bulk-import-checkbox';
      checkbox.style.cssText = `
        width: 24px;
        height: 24px;
        cursor: pointer;
        margin: 0;
        accent-color: #0a66c2;
      `;
      
      // Get profile data
      const profileLink = result.querySelector('a[href*="/in/"]');
      if (profileLink) {
        checkbox.dataset.profileUrl = profileLink.href.split('?')[0];
        
        // Get name from the span with aria-hidden="true"
        const nameElement = result.querySelector('span[aria-hidden="true"]');
        checkbox.dataset.profileName = nameElement ? nameElement.textContent.trim() : `Profile ${index + 1}`;
      }
      
      container.appendChild(checkbox);
      
      // Try multiple approaches to ensure visibility
      
      // Approach 1: Make result container relative and prepend
      result.style.position = 'relative';
      result.style.paddingLeft = '60px'; // Make space for checkbox
      result.insertBefore(container, result.firstChild);
      
      // Approach 2: If there's an image container, put it there
      const imageContainer = result.querySelector('.entity-result__image, .presence-entity__image');
      if (imageContainer) {
        imageContainer.style.position = 'relative';
        const imageCheckbox = container.cloneNode(true);
        imageCheckbox.querySelector('input').className = 'bulk-import-checkbox';
        imageCheckbox.querySelector('input').dataset.profileUrl = checkbox.dataset.profileUrl;
        imageCheckbox.querySelector('input').dataset.profileName = checkbox.dataset.profileName;
        imageContainer.appendChild(imageCheckbox);
      }
      
      console.log(`✅ Added checkbox for: ${checkbox.dataset.profileName}`);
    });
    
    // Also add a visual indicator that checkboxes were added
    if (results.length > 0 && !document.querySelector('.checkbox-indicator')) {
      const indicator = document.createElement('div');
      indicator.className = 'checkbox-indicator bulk-import-ui-element';
      indicator.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: #10b981;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        z-index: 10000;
        font-weight: bold;
      `;
      indicator.textContent = `✅ ${results.length} checkboxes added`;
      document.body.appendChild(indicator);
      
      setTimeout(() => indicator.remove(), 3000);
    }
  }
  
  function createControlPanel() {
    // Create floating control panel
    const panel = document.createElement('div');
    panel.className = 'bulk-import-ui-element';
    panel.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: white;
      border: 2px solid #0a66c2;
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.2);
      z-index: 10000;
      min-width: 300px;
      max-width: 400px;
    `;
    
    panel.innerHTML = `
      <h3 style="margin: 0 0 16px 0; color: #0a66c2; font-size: 18px; font-weight: bold;">
        🚀 Bulk Import Controls
      </h3>
      <div style="margin-bottom: 16px;">
        <span id="selection-count" style="font-size: 14px; color: #666;">
          0 profiles selected
        </span>
      </div>
      <div style="display: flex; gap: 10px;">
        <button id="select-all-btn" style="
          flex: 1;
          padding: 10px;
          background: white;
          color: #0a66c2;
          border: 2px solid #0a66c2;
          border-radius: 8px;
          font-weight: bold;
          cursor: pointer;
          font-size: 14px;
        ">
          Select All
        </button>
        <button id="add-to-queue-btn" style="
          flex: 1;
          padding: 10px;
          background: #0a66c2;
          color: white;
          border: none;
          border-radius: 8px;
          font-weight: bold;
          cursor: pointer;
          font-size: 14px;
        ">
          Add to Queue
        </button>
      </div>
      <div id="import-message" style="
        margin-top: 12px;
        padding: 8px;
        border-radius: 6px;
        font-size: 13px;
        display: none;
      "></div>
    `;
    
    document.body.appendChild(panel);
    
    // Add event listeners
    document.getElementById('select-all-btn').addEventListener('click', toggleSelectAll);
    document.getElementById('add-to-queue-btn').addEventListener('click', addSelectedToQueue);
    
    // Update count when checkboxes change
    document.addEventListener('change', updateSelectionCount);
    updateSelectionCount();
  }
  
  function toggleSelectAll() {
    const checkboxes = document.querySelectorAll('.bulk-import-checkbox');
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    
    checkboxes.forEach(cb => {
      cb.checked = !allChecked;
    });
    
    updateSelectionCount();
  }
  
  function updateSelectionCount() {
    const checked = document.querySelectorAll('.bulk-import-checkbox:checked').length;
    const total = document.querySelectorAll('.bulk-import-checkbox').length;
    
    document.getElementById('selection-count').textContent = 
      `${checked} of ${total} profiles selected`;
  }
  
  async function addSelectedToQueue() {
    const selected = document.querySelectorAll('.bulk-import-checkbox:checked');
    
    if (selected.length === 0) {
      showMessage('Please select at least one profile', 'error');
      return;
    }
    
    // Get existing queue
    const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
    
    let addedCount = 0;
    selected.forEach(checkbox => {
      const profileUrl = checkbox.dataset.profileUrl;
      const profileName = checkbox.dataset.profileName;
      
      // Check if already in queue
      if (!linkedinImportQueue.some(item => item.profileUrl === profileUrl)) {
        linkedinImportQueue.push({
          id: Date.now() + '_' + Math.random(),
          profileUrl: profileUrl,
          profileName: profileName,
          status: 'pending',
          addedAt: new Date().toISOString()
        });
        addedCount++;
      }
      
      // Uncheck
      checkbox.checked = false;
    });
    
    // Save queue
    await chrome.storage.local.set({ linkedinImportQueue });
    
    // Update badge
    chrome.runtime.sendMessage({
      action: 'updateQueueBadge',
      count: linkedinImportQueue.filter(item => item.status === 'pending').length
    });
    
    showMessage(`✅ Added ${addedCount} profiles to import queue`, 'success');
    updateSelectionCount();
  }
  
  function showMessage(text, type) {
    const messageEl = document.getElementById('import-message');
    messageEl.textContent = text;
    messageEl.style.display = 'block';
    messageEl.style.background = type === 'success' ? '#d1fae5' : '#fee2e2';
    messageEl.style.color = type === 'success' ? '#065f46' : '#991b1b';
    
    setTimeout(() => {
      messageEl.style.display = 'none';
    }, 3000);
  }
  
  function observeResults() {
    // Watch for new results being loaded
    const observer = new MutationObserver(() => {
      injectCheckboxes();
      updateSelectionCount();
    });
    
    const container = document.querySelector('.reusable-search__entity-result-list') ||
                     document.querySelector('main');
    
    if (container) {
      observer.observe(container, {
        childList: true,
        subtree: true
      });
    }
  }
  
  // Reinitialize when navigating to search pages
  let lastUrl = location.href;
  new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
      lastUrl = url;
      if (url.includes('/search/results/')) {
        setTimeout(initBulkImport, 2000);
      }
    }
  }).observe(document, { subtree: true, childList: true });
  
  function addDebugMode() {
    // Create a debug button
    const debugBtn = document.createElement('button');
    debugBtn.textContent = '🔍 Debug Mode';
    debugBtn.className = 'bulk-import-ui-element';
    debugBtn.style.cssText = `
      position: fixed;
      top: 100px;
      right: 20px;
      padding: 10px 20px;
      background: #f59e0b;
      color: white;
      border: none;
      border-radius: 8px;
      font-weight: bold;
      cursor: pointer;
      z-index: 10000;
    `;
    
    debugBtn.onclick = () => {
      const results = document.querySelectorAll('li.reusable-search__result-container');
      results.forEach((result, index) => {
        // Highlight the result
        result.style.border = '3px solid red';
        result.style.backgroundColor = 'rgba(255,0,0,0.1)';
        
        // Add a label
        const label = document.createElement('div');
        label.style.cssText = `
          position: absolute;
          top: 0;
          right: 0;
          background: red;
          color: white;
          padding: 4px 8px;
          font-size: 12px;
          z-index: 10000;
        `;
        label.textContent = `Result ${index + 1}`;
        result.style.position = 'relative';
        result.appendChild(label);
      });
      
      alert(`Found ${results.length} search results. They are now highlighted in red. If you see red borders, the checkboxes should be appearing in the top-left of each result.`);
    };
    
    document.body.appendChild(debugBtn);
  }
  
  console.log('🎯 Bulk Import: Ready');
})();