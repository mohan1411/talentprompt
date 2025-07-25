/**
 * Bulk import with buttons instead of checkboxes
 * More visible and reliable approach
 */

(function() {
  'use strict';
  
  if (window.__bulkImportButtons) return;
  window.__bulkImportButtons = true;
  
  console.log('🎯 Bulk Import Buttons: Starting...');
  
  // Selected profiles storage
  const selectedProfiles = new Set();
  const selectedProfilesData = new Map();
  
  setTimeout(initBulkImport, 2000);
  
  function initBulkImport() {
    if (!window.location.pathname.includes('/search/results/')) return;
    
    console.log('🎯 Initializing bulk import buttons');
    
    // Clear existing UI
    document.querySelectorAll('.bulk-import-ui').forEach(el => el.remove());
    
    injectButtons();
    createControlPanel();
    observeResults();
  }
  
  function injectButtons() {
    const results = document.querySelectorAll('li.reusable-search__result-container');
    console.log(`🎯 Adding buttons to ${results.length} results`);
    
    results.forEach((result, index) => {
      if (result.querySelector('.bulk-select-btn')) return;
      
      // Get profile info
      const profileLink = result.querySelector('a[href*="/in/"]');
      if (!profileLink) {
        console.log(`No profile link found in result ${index}`);
        return;
      }
      
      const profileUrl = profileLink.href.split('?')[0];
      const nameElement = result.querySelector('span[aria-hidden="true"]');
      const profileName = nameElement ? nameElement.textContent.trim() : `Profile ${index + 1}`;
      
      // Method 1: Add button to the main content area
      const contentArea = result.querySelector('.entity-result__content') || 
                         result.querySelector('.entity-result__item') ||
                         result;
      
      // Create floating button
      const selectBtn = document.createElement('button');
      selectBtn.className = 'bulk-select-btn';
      selectBtn.dataset.profileUrl = profileUrl;
      selectBtn.dataset.profileName = profileName;
      selectBtn.style.cssText = `
        position: absolute;
        top: 10px;
        right: 10px;
        padding: 6px 14px;
        background: ${selectedProfiles.has(profileUrl) ? '#059669' : '#0a66c2'};
        color: white;
        border: none;
        border-radius: 20px;
        font-weight: bold;
        font-size: 13px;
        cursor: pointer;
        z-index: 1000;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        transition: all 0.2s;
      `;
      selectBtn.textContent = selectedProfiles.has(profileUrl) ? '✓ Selected' : '+ Select';
      
      // Method 2: Also add an overlay button
      const overlay = document.createElement('div');
      overlay.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 10;
      `;
      
      const overlayBtn = selectBtn.cloneNode(true);
      overlayBtn.style.pointerEvents = 'all';
      overlay.appendChild(overlayBtn);
      
      // Add click handlers to both buttons
      [selectBtn, overlayBtn].forEach(btn => {
        btn.onclick = (e) => {
          e.preventDefault();
          e.stopPropagation();
          
          const url = btn.dataset.profileUrl;
          const name = btn.dataset.profileName;
          
          if (selectedProfiles.has(url)) {
            selectedProfiles.delete(url);
            document.querySelectorAll(`.bulk-select-btn[data-profile-url="${url}"]`).forEach(b => {
              b.style.background = '#0a66c2';
              b.textContent = '+ Select';
            });
          } else {
            selectedProfiles.add(url);
            selectedProfilesData.set(url, { name, url });
            document.querySelectorAll(`.bulk-select-btn[data-profile-url="${url}"]`).forEach(b => {
              b.style.background = '#059669';
              b.textContent = '✓ Selected';
            });
          }
          
          updateSelectionCount();
        };
        
        btn.onmouseover = () => {
          btn.style.transform = 'scale(1.1)';
          btn.style.boxShadow = '0 4px 12px rgba(0,0,0,0.4)';
        };
        
        btn.onmouseout = () => {
          btn.style.transform = 'scale(1)';
          btn.style.boxShadow = '0 2px 8px rgba(0,0,0,0.3)';
        };
      });
      
      // Make container relative
      result.style.position = 'relative';
      contentArea.style.position = 'relative';
      
      // Add both buttons
      result.appendChild(overlay);
      contentArea.appendChild(selectBtn);
      
      console.log(`✅ Added button for: ${profileName}`);
    });
    
    // Show indicator
    if (results.length > 0) {
      const indicator = document.createElement('div');
      indicator.className = 'bulk-import-ui';
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
        animation: fadeIn 0.3s;
      `;
      indicator.textContent = `✅ Added ${results.length} select buttons`;
      document.body.appendChild(indicator);
      
      setTimeout(() => indicator.remove(), 3000);
    }
  }
  
  function createControlPanel() {
    const panel = document.createElement('div');
    panel.className = 'bulk-import-ui';
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
    `;
    
    panel.innerHTML = `
      <h3 style="margin: 0 0 16px 0; color: #0a66c2; font-size: 18px; font-weight: bold;">
        🚀 Bulk Import
      </h3>
      <div style="margin-bottom: 16px;">
        <span id="selection-count" style="font-size: 16px; font-weight: bold; color: #333;">
          0 profiles selected
        </span>
      </div>
      <div style="display: flex; gap: 10px; margin-bottom: 12px;">
        <button id="select-all-btn" style="
          flex: 1;
          padding: 12px;
          background: white;
          color: #0a66c2;
          border: 2px solid #0a66c2;
          border-radius: 8px;
          font-weight: bold;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s;
        ">
          Select All
        </button>
        <button id="clear-btn" style="
          flex: 1;
          padding: 12px;
          background: white;
          color: #dc2626;
          border: 2px solid #dc2626;
          border-radius: 8px;
          font-weight: bold;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s;
        ">
          Clear All
        </button>
      </div>
      <button id="add-to-queue-btn" style="
        width: 100%;
        padding: 14px;
        background: #0a66c2;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        cursor: pointer;
        font-size: 16px;
        transition: all 0.2s;
      ">
        Add Selected to Import Queue
      </button>
      <div id="import-message" style="
        margin-top: 12px;
        padding: 10px;
        border-radius: 6px;
        font-size: 14px;
        text-align: center;
        display: none;
      "></div>
    `;
    
    document.body.appendChild(panel);
    
    // Add hover effects
    const buttons = panel.querySelectorAll('button');
    buttons.forEach(btn => {
      btn.onmouseover = () => {
        btn.style.transform = 'translateY(-1px)';
        btn.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
      };
      btn.onmouseout = () => {
        btn.style.transform = 'translateY(0)';
        btn.style.boxShadow = 'none';
      };
    });
    
    // Event listeners
    document.getElementById('select-all-btn').onclick = selectAll;
    document.getElementById('clear-btn').onclick = clearAll;
    document.getElementById('add-to-queue-btn').onclick = addToQueue;
    
    updateSelectionCount();
  }
  
  function selectAll() {
    document.querySelectorAll('.bulk-select-btn button').forEach(btn => {
      if (btn.textContent === '+ Select') {
        btn.click();
      }
    });
  }
  
  function clearAll() {
    document.querySelectorAll('.bulk-select-btn button').forEach(btn => {
      if (btn.textContent === '✓ Selected') {
        btn.click();
      }
    });
  }
  
  function updateSelectionCount() {
    const count = selectedProfiles.size;
    const countEl = document.getElementById('selection-count');
    if (countEl) {
      countEl.textContent = `${count} profile${count !== 1 ? 's' : ''} selected`;
      countEl.style.color = count > 0 ? '#059669' : '#333';
    }
  }
  
  async function addToQueue() {
    if (selectedProfiles.size === 0) {
      showMessage('Please select at least one profile', 'error');
      return;
    }
    
    // Get existing queue
    const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
    
    let addedCount = 0;
    
    selectedProfiles.forEach(profileUrl => {
      const profileData = selectedProfilesData.get(profileUrl);
      if (profileData && !linkedinImportQueue.some(item => item.profileUrl === profileUrl)) {
        linkedinImportQueue.push({
          id: Date.now() + '_' + Math.random(),
          profileUrl: profileUrl,
          profileName: profileData.name,
          status: 'pending',
          addedAt: new Date().toISOString()
        });
        addedCount++;
      }
    });
    
    // Save queue
    await chrome.storage.local.set({ linkedinImportQueue });
    
    // Update badge
    chrome.runtime.sendMessage({
      action: 'updateQueueBadge',
      count: linkedinImportQueue.filter(item => item.status === 'pending').length
    });
    
    showMessage(`✅ Added ${addedCount} profiles to import queue!`, 'success');
    
    // Clear selections
    clearAll();
  }
  
  function showMessage(text, type) {
    const messageEl = document.getElementById('import-message');
    if (messageEl) {
      messageEl.textContent = text;
      messageEl.style.display = 'block';
      messageEl.style.background = type === 'success' ? '#d1fae5' : '#fee2e2';
      messageEl.style.color = type === 'success' ? '#065f46' : '#991b1b';
      messageEl.style.border = `2px solid ${type === 'success' ? '#059669' : '#dc2626'}`;
      
      setTimeout(() => {
        messageEl.style.display = 'none';
      }, 4000);
    }
  }
  
  function observeResults() {
    const observer = new MutationObserver(() => {
      setTimeout(injectButtons, 500);
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
  
  // Reinitialize on navigation
  let lastUrl = location.href;
  new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
      lastUrl = url;
      if (url.includes('/search/results/')) {
        selectedProfiles.clear();
        setTimeout(initBulkImport, 2000);
      }
    }
  }).observe(document, { subtree: true, childList: true });
  
  // Add CSS for animations
  const style = document.createElement('style');
  style.textContent = `
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(-10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    .bulk-select-btn {
      animation: fadeIn 0.3s ease-out;
    }
    
    /* Force button visibility */
    button.bulk-select-btn {
      display: inline-block !important;
      visibility: visible !important;
      opacity: 1 !important;
    }
  `;
  document.head.appendChild(style);
  
  console.log('🎯 Bulk Import Buttons: Ready');
})();