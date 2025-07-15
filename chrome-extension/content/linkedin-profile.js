// LinkedIn Profile Integration
(function() {
  'use strict';
  
  // Check if we're on a profile page
  if (!window.location.pathname.includes('/in/')) {
    return;
  }
  
  // Configuration - Always use production URL
  const API_URL = 'https://talentprompt-production.up.railway.app/api/v1';
  
  // State
  let importButton = null;
  let isProcessing = false;
  
  // Initialize when page loads
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
  // Initialize the integration
  function init() {
    // Wait a bit for LinkedIn to render
    setTimeout(() => {
      addImportButton();
      checkIfProfileExists();
    }, 2000);
    
    // Re-initialize on navigation (LinkedIn is a SPA)
    observeUrlChanges();
  }
  
  // Add import button to profile
  function addImportButton() {
    // Remove existing button if any
    if (importButton) {
      importButton.remove();
    }
    
    // Find the profile actions section
    const actionsSection = document.querySelector('.pvs-profile-actions') || 
                          document.querySelector('.pv-top-card-v2-ctas');
    
    if (!actionsSection) {
      // Retry after a delay
      setTimeout(addImportButton, 1000);
      return;
    }
    
    // Create import button
    importButton = document.createElement('button');
    importButton.className = 'talentprompt-import-btn';
    importButton.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
      </svg>
      <span>Import to Promtitude</span>
    `;
    
    // Style the button
    const style = document.createElement('style');
    style.textContent = `
      .talentprompt-import-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        margin-left: 8px;
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;
      }
      
      .talentprompt-import-btn:hover {
        background: #1d4ed8;
      }
      
      .talentprompt-import-btn:disabled {
        background: #9ca3af;
        cursor: not-allowed;
      }
      
      .talentprompt-status {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
      }
      
      .talentprompt-status.success {
        border-left: 4px solid #10b981;
      }
      
      .talentprompt-status.error {
        border-left: 4px solid #ef4444;
      }
      
      .talentprompt-status.exists {
        border-left: 4px solid #f59e0b;
      }
      
      @keyframes slideIn {
        from {
          transform: translateX(100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }
    `;
    document.head.appendChild(style);
    
    // Add click handler
    importButton.addEventListener('click', handleImport);
    
    // Insert button
    actionsSection.appendChild(importButton);
  }
  
  // Check if profile already exists in database
  async function checkIfProfileExists() {
    try {
      const profileData = extractProfileData();
      if (!profileData.linkedin_url) return;
      
      const authToken = await getAuthToken();
      if (!authToken) return;
      
      const response = await fetch(`${API_URL}/linkedin/check-exists`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          linkedin_url: profileData.linkedin_url
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.exists) {
          updateButtonState('exists', data.candidate_id);
        }
      }
    } catch (error) {
      console.error('Error checking profile:', error);
    }
  }
  
  // Handle import button click
  async function handleImport() {
    if (isProcessing) return;
    
    isProcessing = true;
    
    // Update button state if it exists
    if (importButton) {
      importButton.disabled = true;
      const buttonText = importButton.querySelector('span');
      if (buttonText) {
        buttonText.textContent = 'Importing...';
      }
    }
    
    try {
      const authToken = await getAuthToken();
      if (!authToken) {
        showStatus('Please login to Promtitude', 'error');
        return;
      }
      
      const profileData = extractProfileData();
      console.log('Extracted profile data:', profileData);
      
      console.log('Sending import request through background script...');
      console.log('Auth token:', authToken ? 'Present' : 'Missing');
      
      // Send the request through the background script to avoid CORS issues
      const response = await chrome.runtime.sendMessage({
        action: 'importProfile',
        data: profileData,
        authToken: authToken
      });
      
      console.log('Background script response:', response);
      
      if (!response || !response.success) {
        throw new Error(response?.error || 'Import failed');
      }
      
      const result = response.data;
      showStatus('Profile imported successfully!', 'success');
      
      if (importButton) {
        updateButtonState('imported', result.candidate_id);
      }
      
      return result;
      
    } catch (error) {
      showStatus(error.message, 'error');
      
      if (importButton) {
        importButton.disabled = false;
        const buttonText = importButton.querySelector('span');
        if (buttonText) {
          buttonText.textContent = 'Import to Promtitude';
        }
      }
      
      throw error;
    } finally {
      isProcessing = false;
    }
  }
  
  // Extract profile data from the page
  function extractProfileData() {
    const data = {
      linkedin_url: window.location.href.split('?')[0],
      name: '',
      headline: '',
      location: '',
      about: '',
      experience: [],
      education: [],
      skills: []
    };
    
    // Extract name
    const nameElement = document.querySelector('.pv-text-details__left-panel h1');
    if (nameElement) {
      data.name = nameElement.textContent.trim();
    }
    
    // Extract headline
    const headlineElement = document.querySelector('.pv-text-details__left-panel .text-body-medium');
    if (headlineElement) {
      data.headline = headlineElement.textContent.trim();
    }
    
    // Extract location
    const locationElement = document.querySelector('.pv-text-details__left-panel .text-body-small:last-child');
    if (locationElement) {
      data.location = locationElement.textContent.trim();
    }
    
    // Extract about section
    const aboutSection = document.querySelector('.pv-about-section .pv-about__summary-text');
    if (aboutSection) {
      data.about = aboutSection.textContent.trim();
    }
    
    // Extract experience
    const experienceItems = document.querySelectorAll('.pv-profile-section__card-item-v2');
    experienceItems.forEach(item => {
      const titleEl = item.querySelector('.pv-entity__summary-info h3');
      const companyEl = item.querySelector('.pv-entity__secondary-title');
      const durationEl = item.querySelector('.pv-entity__date-range span:nth-child(2)');
      const descriptionEl = item.querySelector('.pv-entity__description');
      
      if (titleEl && companyEl) {
        data.experience.push({
          title: titleEl.textContent.trim(),
          company: companyEl.textContent.trim(),
          duration: durationEl ? durationEl.textContent.trim() : '',
          description: descriptionEl ? descriptionEl.textContent.trim() : ''
        });
      }
    });
    
    // Extract skills (if visible)
    const skillElements = document.querySelectorAll('.pv-skill-category-entity__name-text');
    skillElements.forEach(skill => {
      data.skills.push(skill.textContent.trim());
    });
    
    return data;
  }
  
  // Get auth token from storage
  async function getAuthToken() {
    return new Promise((resolve) => {
      chrome.storage.local.get(['authToken'], (result) => {
        resolve(result.authToken);
      });
    });
  }
  
  // Update button state
  function updateButtonState(state, candidateId) {
    if (!importButton) return;
    
    switch (state) {
      case 'exists':
        importButton.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
          </svg>
          <span>Already in Promtitude</span>
        `;
        importButton.style.background = '#10b981';
        importButton.disabled = true;
        break;
        
      case 'imported':
        importButton.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
          </svg>
          <span>Imported Successfully</span>
        `;
        importButton.style.background = '#10b981';
        importButton.disabled = true;
        
        // Add view button
        const viewButton = document.createElement('button');
        viewButton.className = 'talentprompt-import-btn';
        viewButton.style.marginLeft = '8px';
        viewButton.innerHTML = '<span>View in Promtitude</span>';
        viewButton.onclick = () => {
          window.open(`https://promtitude.com/candidates/${candidateId}`, '_blank');
        };
        importButton.parentNode.appendChild(viewButton);
        break;
    }
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
  
  // Observe URL changes (LinkedIn is a SPA)
  function observeUrlChanges() {
    let lastUrl = location.href;
    new MutationObserver(() => {
      const url = location.href;
      if (url !== lastUrl) {
        lastUrl = url;
        if (url.includes('/in/')) {
          setTimeout(init, 1000);
        }
      }
    }).observe(document, { subtree: true, childList: true });
  }
  
  // Listen for messages from popup
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Content script received message:', request);
    
    if (request.action === 'importProfile') {
      // Store the auth token if provided
      if (request.authToken) {
        chrome.storage.local.set({ authToken: request.authToken });
      }
      
      handleImport().then(() => {
        sendResponse({ success: true });
      }).catch(error => {
        console.error('Import error in content script:', error);
        sendResponse({ success: false, error: error.message });
      });
      return true; // Indicates async response
    }
  });
  
})();