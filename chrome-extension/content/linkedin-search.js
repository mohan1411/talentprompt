// LinkedIn Search Results Integration
(function() {
  'use strict';
  
  // Check if we're on a search page
  if (!window.location.pathname.includes('/search/')) {
    return;
  }
  
  // State
  let selectedProfiles = new Set();
  let bulkToolbar = null;
  
  // Initialize when page loads
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  function init() {
    setTimeout(() => {
      addBulkToolbar();
      enhanceSearchResults();
    }, 2000);
    
    // Re-initialize on scroll (LinkedIn loads results dynamically)
    observeSearchResults();
  }
  
  // Add bulk import toolbar
  function addBulkToolbar() {
    if (bulkToolbar) return;
    
    bulkToolbar = document.createElement('div');
    bulkToolbar.className = 'talentprompt-bulk-toolbar';
    bulkToolbar.innerHTML = `
      <h3>Promtitude Bulk Import</h3>
      <p style="margin: 0 0 12px 0; color: #6b7280; font-size: 14px;">
        <span id="selected-count">0</span> profiles selected
      </p>
      <button id="select-all-btn" class="talentprompt-import-btn" style="width: 100%; margin: 0 0 8px 0;">
        Select All Visible
      </button>
      <button id="bulk-import-btn" class="talentprompt-import-btn" style="width: 100%; margin: 0;" disabled>
        Import Selected Profiles
      </button>
      <div id="import-progress" style="margin-top: 12px; display: none;">
        <div style="background: #e5e7eb; height: 8px; border-radius: 4px; overflow: hidden;">
          <div id="progress-bar" style="background: #2563eb; height: 100%; width: 0%; transition: width 0.3s;"></div>
        </div>
        <p style="margin: 8px 0 0 0; font-size: 12px; color: #6b7280; text-align: center;">
          Importing <span id="current-import">0</span> of <span id="total-import">0</span>
        </p>
      </div>
      <div style="margin-top: 12px; padding: 8px; background: #fef3c7; border-radius: 6px; border: 1px solid #fbbf24;">
        <p style="margin: 0; font-size: 11px; color: #78350f; line-height: 1.4;">
          <strong>⚠️ Note:</strong> Use responsibly for professional recruiting. You are responsible for complying with LinkedIn's Terms of Service.
        </p>
      </div>
    `;
    
    document.body.appendChild(bulkToolbar);
    
    // Add event listeners
    document.getElementById('select-all-btn').addEventListener('click', selectAllProfiles);
    document.getElementById('bulk-import-btn').addEventListener('click', bulkImportProfiles);
  }
  
  // Enhance search result items
  function enhanceSearchResults() {
    const resultItems = document.querySelectorAll('.entity-result__item');
    
    resultItems.forEach(item => {
      // Skip if already processed
      if (item.querySelector('.talentprompt-profile-indicator')) return;
      
      // Get profile link
      const profileLink = item.querySelector('.entity-result__title-text a');
      if (!profileLink) return;
      
      const profileUrl = profileLink.href.split('?')[0];
      const profileId = profileUrl.split('/in/')[1]?.split('/')[0];
      
      if (!profileId) return;
      
      // Add indicator
      const indicator = document.createElement('div');
      indicator.className = 'talentprompt-profile-indicator';
      indicator.innerHTML = 'T';
      indicator.dataset.profileId = profileId;
      indicator.dataset.profileUrl = profileUrl;
      
      // Extract basic info
      const nameEl = item.querySelector('.entity-result__title-text');
      const titleEl = item.querySelector('.entity-result__primary-subtitle');
      const locationEl = item.querySelector('.entity-result__secondary-subtitle');
      
      indicator.dataset.name = nameEl?.textContent.trim() || '';
      indicator.dataset.headline = titleEl?.textContent.trim() || '';
      indicator.dataset.location = locationEl?.textContent.trim() || '';
      
      // Add click handler
      indicator.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleProfileSelection(indicator);
      });
      
      // Check if exists in database
      checkProfileExists(profileUrl, indicator);
      
      // Add to result item
      item.style.position = 'relative';
      item.appendChild(indicator);
    });
  }
  
  // Toggle profile selection
  function toggleProfileSelection(indicator) {
    const profileId = indicator.dataset.profileId;
    
    if (selectedProfiles.has(profileId)) {
      selectedProfiles.delete(profileId);
      indicator.classList.remove('selected');
    } else {
      selectedProfiles.add(profileId);
      indicator.classList.add('selected');
    }
    
    updateSelectionCount();
  }
  
  // Select all visible profiles
  function selectAllProfiles() {
    const indicators = document.querySelectorAll('.talentprompt-profile-indicator:not(.exists)');
    
    indicators.forEach(indicator => {
      const profileId = indicator.dataset.profileId;
      selectedProfiles.add(profileId);
      indicator.classList.add('selected');
    });
    
    updateSelectionCount();
  }
  
  // Update selection count
  function updateSelectionCount() {
    document.getElementById('selected-count').textContent = selectedProfiles.size;
    document.getElementById('bulk-import-btn').disabled = selectedProfiles.size === 0;
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
    
    progressDiv.style.display = 'block';
    totalImportEl.textContent = selectedProfiles.size;
    
    // Disable buttons
    document.getElementById('select-all-btn').disabled = true;
    document.getElementById('bulk-import-btn').disabled = true;
    
    let imported = 0;
    let failed = 0;
    
    // Import profiles one by one
    for (const profileId of selectedProfiles) {
      const indicator = document.querySelector(`[data-profile-id="${profileId}"]`);
      if (!indicator) continue;
      
      currentImportEl.textContent = imported + 1;
      
      try {
        const profileData = {
          linkedin_url: indicator.dataset.profileUrl,
          name: indicator.dataset.name,
          headline: indicator.dataset.headline,
          location: indicator.dataset.location
        };
        
        await importProfile(profileData);
        
        imported++;
        indicator.classList.remove('selected');
        indicator.classList.add('exists');
        indicator.innerHTML = '✓';
        
      } catch (error) {
        failed++;
        console.error(`Failed to import ${profileId}:`, error);
      }
      
      // Update progress
      const progress = (imported + failed) / selectedProfiles.size * 100;
      progressBar.style.width = `${progress}%`;
      
      // Small delay between imports
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    // Clear selection
    selectedProfiles.clear();
    updateSelectionCount();
    
    // Hide progress
    setTimeout(() => {
      progressDiv.style.display = 'none';
      progressBar.style.width = '0%';
    }, 2000);
    
    // Re-enable buttons
    document.getElementById('select-all-btn').disabled = false;
    
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
  
  // Check if profile exists
  async function checkProfileExists(profileUrl, indicator) {
    try {
      chrome.runtime.sendMessage({
        action: 'checkExists',
        linkedin_url: profileUrl
      }, response => {
        if (response && response.success && response.exists) {
          indicator.classList.add('exists');
          indicator.innerHTML = '✓';
          indicator.title = 'Already in Promtitude';
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
    const observer = new MutationObserver(() => {
      enhanceSearchResults();
    });
    
    const resultsContainer = document.querySelector('.search-results-container');
    if (resultsContainer) {
      observer.observe(resultsContainer, { childList: true, subtree: true });
    }
  }
  
  // Listen for messages from popup
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'bulkImport') {
      const count = document.querySelectorAll('.talentprompt-profile-indicator:not(.exists)').length;
      
      // Select all non-imported profiles
      selectAllProfiles();
      
      // Start bulk import
      bulkImportProfiles().then(() => {
        sendResponse({ success: true, count: selectedProfiles.size });
      }).catch(error => {
        sendResponse({ success: false, error: error.message });
      });
      
      return true;
    }
  });
  
})();