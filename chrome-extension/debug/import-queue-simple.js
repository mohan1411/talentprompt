/**
 * Simplified bulk import for LinkedIn search results
 */

(function() {
  'use strict';
  
  console.log('🎯 Simple Bulk Import: Initializing...');
  
  // Wait for page to load
  setTimeout(() => {
    injectSimpleUI();
  }, 2000);
  
  function injectSimpleUI() {
    // Only run on search pages
    if (!window.location.pathname.includes('/search/results/')) {
      return;
    }
    
    console.log('🎯 Injecting checkboxes on search results...');
    
    // Find all search result cards
    const resultCards = document.querySelectorAll('.entity-result');
    console.log(`Found ${resultCards.length} result cards`);
    
    resultCards.forEach((card, index) => {
      // Skip if already has checkbox
      if (card.querySelector('.simple-import-checkbox')) return;
      
      // Create checkbox overlay
      const checkboxOverlay = document.createElement('div');
      checkboxOverlay.className = 'simple-import-checkbox';
      checkboxOverlay.style.cssText = `
        position: absolute;
        top: 10px;
        left: 10px;
        background: white;
        border: 2px solid #0a66c2;
        border-radius: 4px;
        padding: 4px;
        z-index: 100;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      `;
      
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.style.cssText = `
        width: 24px;
        height: 24px;
        cursor: pointer;
        margin: 0;
        accent-color: #0a66c2;
      `;
      
      // Get profile URL
      const profileLink = card.querySelector('a[href*="/in/"]');
      if (profileLink) {
        checkbox.dataset.profileUrl = profileLink.href.split('?')[0];
        
        // Get name
        const nameSpan = card.querySelector('.entity-result__title-text');
        checkbox.dataset.profileName = nameSpan ? nameSpan.textContent.trim() : 'Unknown';
      }
      
      checkboxOverlay.appendChild(checkbox);
      
      // Make card relative positioned
      card.style.position = 'relative';
      card.appendChild(checkboxOverlay);
    });
    
    // Update select all functionality
    const selectAllBtn = document.querySelector('.bulk-import-button-floating button');
    if (selectAllBtn) {
      selectAllBtn.onclick = () => {
        const allCheckboxes = document.querySelectorAll('.simple-import-checkbox input');
        const allChecked = Array.from(allCheckboxes).every(cb => cb.checked);
        
        allCheckboxes.forEach(cb => {
          cb.checked = !allChecked;
        });
      };
    }
    
    // Update add to queue functionality
    const addBtn = document.querySelector('.bulk-import-button-floating button:last-child');
    if (addBtn) {
      addBtn.onclick = async () => {
        const checkedBoxes = document.querySelectorAll('.simple-import-checkbox input:checked');
        console.log(`Adding ${checkedBoxes.length} profiles to queue`);
        
        // Get existing queue
        const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
        
        let addedCount = 0;
        checkedBoxes.forEach(checkbox => {
          const profileUrl = checkbox.dataset.profileUrl;
          const profileName = checkbox.dataset.profileName;
          
          // Check if already in queue
          const exists = linkedinImportQueue.some(item => item.profileUrl === profileUrl);
          if (!exists) {
            linkedinImportQueue.push({
              id: Date.now().toString() + Math.random(),
              profileUrl: profileUrl,
              profileName: profileName,
              status: 'pending',
              addedAt: new Date().toISOString()
            });
            addedCount++;
          }
          
          // Uncheck after adding
          checkbox.checked = false;
        });
        
        // Save updated queue
        await chrome.storage.local.set({ linkedinImportQueue });
        
        // Show notification
        const notification = document.createElement('div');
        notification.style.cssText = `
          position: fixed;
          top: 100px;
          right: 20px;
          background: #0a66c2;
          color: white;
          padding: 16px 24px;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
          z-index: 10000;
          font-weight: 600;
        `;
        notification.textContent = `✅ Added ${addedCount} profiles to import queue`;
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 3000);
        
        // Update badge
        chrome.runtime.sendMessage({
          action: 'updateQueueBadge',
          count: linkedinImportQueue.filter(item => item.status === 'pending').length
        });
      };
    }
  }
  
  // Re-inject when page updates
  const observer = new MutationObserver(() => {
    if (window.location.pathname.includes('/search/results/')) {
      setTimeout(injectSimpleUI, 1000);
    }
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
  
  console.log('🎯 Simple Bulk Import: Ready!');
})();