// LinkedIn Profile Integration
(function() {
  'use strict';
  
  // Forward declare functions
  let handleImport;
  
  // Global state - accessible from message listener
  let profileExistsStatus = null;
  let isCheckingDuplicate = false;
  
  // Listen for messages from popup (always register this)
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    
    if (request.action === 'importProfile') {
      // Store the auth token if provided
      if (request.authToken) {
        chrome.storage.local.set({ authToken: request.authToken });
      }
      
      // Check if we're on a profile page
      if (!window.location.pathname.includes('/in/')) {
        sendResponse({ success: false, error: 'Please navigate to a LinkedIn profile page' });
        return true;
      }
      
      // Check if we're on a details page
      if (window.location.pathname.includes('/details/')) {
        sendResponse({ success: false, error: 'Please navigate to the main profile page (not details page)' });
        return true;
      }
      
      // If we're still checking for duplicates, wait for it to complete
      if (isCheckingDuplicate) {
        const checkInterval = setInterval(() => {
          if (!isCheckingDuplicate) {
            clearInterval(checkInterval);
            
            // Now check if it's a duplicate
            if (profileExistsStatus && profileExistsStatus.exists) {
              sendResponse({ success: false, error: 'This profile has already been imported' });
            } else {
              // Continue with normal import flow
              proceedWithImport();
            }
          }
        }, 100);
        return true;
      }
      
      // Check if we already know this profile exists (before any import action)
      if (profileExistsStatus && profileExistsStatus.exists) {
        sendResponse({ success: false, error: 'This profile has already been imported' });
        return true;
      }
      
      const proceedWithImport = () => {
        // Handle import - use function if available, otherwise extract and send
        if (typeof handleImport === 'function') {
          handleImport().then((result) => {
            // Check if result is null (duplicate that was handled gracefully)
            if (result === null) {
              sendResponse({ success: false, error: 'This profile has already been imported' });
            } else {
              sendResponse({ success: true, data: result });
            }
          }).catch(error => {
            sendResponse({ success: false, error: error.message });
          });
        } else {
          // Simplified import for when called from popup
          handleSimpleImport(request.authToken).then(result => {
            // Pass through the result as-is, including duplicate status
            sendResponse(result);
          }).catch(error => {
            sendResponse({ success: false, error: error.message });
          });
        }
      };
      
      // If not waiting or duplicate, proceed with import
      proceedWithImport();
      return true; // Indicates async response
    }
  });
  
  // Simple import function for popup - now extracting data locally
  async function handleSimpleImport(authToken) {
    
    // Wait for any early duplicate check to complete
    if (window.__duplicateCheckPromise) {
      try {
        await window.__duplicateCheckPromise;
      } catch (err) {
      }
    }
    
    // Check if we already know this profile exists
    if (profileExistsStatus && profileExistsStatus.exists) {
      return { success: false, error: 'This profile has already been imported' };
    }
    
    // If still checking, wait for it (with timeout)
    if (isCheckingDuplicate) {
      await new Promise((resolve) => {
        let waitTime = 0;
        const maxWaitTime = 5000; // 5 seconds max
        const checkInterval = setInterval(() => {
          waitTime += 100;
          if (!isCheckingDuplicate || waitTime >= maxWaitTime) {
            clearInterval(checkInterval);
            if (waitTime >= maxWaitTime) {
            }
            resolve();
          }
        }, 100);
      });
      
      // Check again after waiting
      if (profileExistsStatus && profileExistsStatus.exists) {
        return { success: false, error: 'This profile has already been imported' };
      }
    }
    
    try {
      // If we have a button on the page, click it instead of using messaging
      // This is more reliable when extension context is problematic
      if (importButton && typeof handleImport === 'function') {
        await handleImport();
        return { success: true, data: { message: 'Profile import initiated' } };
      }
      
      // Otherwise fall back to the original approach
      // Extract profile data locally
      let profileData;
      
      // Use ultra-clean extractor if available
      if (window.extractUltraCleanProfile) {
        profileData = window.extractUltraCleanProfile();
      } else {
        profileData = extractProfileData();
      }
      
      // Validate we have minimum required data
      if (!profileData || !profileData.linkedin_url) {
        throw new Error('Failed to extract LinkedIn URL');
      }
      
      if (!profileData.name && !profileData.headline) {
        throw new Error('Failed to extract profile information. Please ensure you are on a LinkedIn profile page.');
      }
      
      // For now, just do a direct import like before since that was working
      // Send the profile data directly to the background script for import
      const response = await chrome.runtime.sendMessage({
        action: 'importProfile',
        data: profileData,
        authToken: authToken
      });
      
      // Return the response as-is
      return response || { success: false, error: 'No response from background script' };
    } catch (error) {
      console.error('Import error:', error);
      // If messaging fails, try clicking the button on the page
      if (importButton && typeof handleImport === 'function') {
        try {
          await handleImport();
          return { success: true, data: { message: 'Profile import initiated via button' } };
        } catch (btnError) {
          console.error('Button click also failed:', btnError);
        }
      }
      return { success: false, error: error.message || 'Import failed' };
    }
  }
  
  // Check if we're on a profile page for the UI elements
  const pathname = window.location.pathname;
  if (!pathname.includes('/in/')) {
    return;
  }
  
  
  // Don't run UI elements on detail pages (experience, education, etc)
  if (pathname.includes('/details/')) {
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
  
  // Also check immediately for popup requests
  // This ensures duplicate check starts ASAP
  const earlyCheckPromise = checkIfProfileExists().then(() => {
  }).catch(err => {
  });
  
  // Store the promise globally so handleSimpleImport can wait for it
  window.__duplicateCheckPromise = earlyCheckPromise;
  
  // Initialize the integration
  async function init() {
    // Reset profile exists status on new page
    profileExistsStatus = null;
    isCheckingDuplicate = false;
    
    // Start checking for duplicates immediately and wait for it
    try {
      await checkIfProfileExists();
    } catch (err) {
    }
    
    // Wait a bit for LinkedIn to render
    setTimeout(async () => {
      addImportButton();
      
      // Update button state based on duplicate check result
      if (importButton && profileExistsStatus && profileExistsStatus.exists) {
        updateButtonState('exists', profileExistsStatus.candidate_id);
      } else if (importButton) {
        const buttonText = importButton.querySelector('span');
        if (buttonText) {
          buttonText.textContent = 'Import to Promtitude';
        }
      }
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
    
    // Find the profile actions section - try multiple selectors
    const actionsSection = document.querySelector('.pvs-profile-actions') || 
                          document.querySelector('.pv-top-card-v2-ctas') ||
                          document.querySelector('[class*="artdeco-dropdown"]')?.parentElement ||
                          document.querySelector('.pv-top-card-v3__cta-container');
    
    if (!actionsSection) {
      // Retry after a delay
      setTimeout(addImportButton, 1000);
      return;
    }
    
    
    // Create import button
    importButton = document.createElement('button');
    importButton.className = 'talentprompt-import-btn artdeco-button artdeco-button--2 artdeco-button--primary';
    importButton.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 4px;">
        <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
      </svg>
      <span class="artdeco-button__text">Import to Promtitude</span>
    `;
    
    // Style the button to match LinkedIn's style
    const style = document.createElement('style');
    style.textContent = `
      .talentprompt-import-btn {
        margin-left: 8px !important;
        background: #2563eb !important;
        border-color: #2563eb !important;
        color: white !important;
      }
      
      .talentprompt-import-btn:hover:not(:disabled) {
        background: #1d4ed8 !important;
        border-color: #1d4ed8 !important;
      }
      
      .talentprompt-import-btn:disabled {
        background: #9ca3af !important;
        border-color: #9ca3af !important;
        cursor: not-allowed !important;
      }
      
      .talentprompt-import-btn.exists {
        background: #10b981 !important;
        border-color: #10b981 !important;
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
    isCheckingDuplicate = true;
    try {
      const profileData = extractProfileData();
      if (!profileData.linkedin_url) {
        isCheckingDuplicate = false;
        return;
      }
      
      const authToken = await getAuthToken();
      if (!authToken) {
        isCheckingDuplicate = false;
        return;
      }
      
      // Send through background script to avoid CORS - use Promise style
      const response = await new Promise((resolve) => {
        chrome.runtime.sendMessage({
          action: 'checkProfileExists',
          linkedin_url: profileData.linkedin_url,
          authToken: authToken
        }, (response) => {
          resolve(response || { exists: false });
        });
      });
      
      
      if (response && response.exists) {
        profileExistsStatus = {
          exists: true,
          candidate_id: response.candidate_id
        };
        updateButtonState('exists', response.candidate_id);
      } else {
        profileExistsStatus = {
          exists: false
        };
      }
    } catch (error) {
      profileExistsStatus = { exists: false };
    } finally {
      isCheckingDuplicate = false;
    }
  }
  
  // Handle import button click
  handleImport = async function() {
    
    if (isProcessing) return;
    
    // Check if we already know this profile exists
    if (profileExistsStatus && profileExistsStatus.exists) {
      showStatus('This profile has already been imported', 'exists');
      if (importButton) {
        updateButtonState('exists', profileExistsStatus.candidate_id);
      }
      return;
    }
    
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
      
      // Add a small delay to ensure all scripts are loaded
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // FIRST: Extract profile data (including experience) BEFORE opening any modals
      let profileData;
      if (window.extractUltraCleanProfile) {
        profileData = window.extractUltraCleanProfile();
        
        // Check if extraction returned an error
        if (profileData.error === 'wrong_page') {
          showStatus('Please navigate to the main profile page to import', 'error');
          if (importButton) {
            importButton.disabled = false;
            const buttonText = importButton.querySelector('span');
            if (buttonText) {
              buttonText.textContent = 'Import to Promtitude';
            }
          }
          return;
        }
        
      } else {
        profileData = extractProfileData();
      }
      
      // SECOND: Extract contact info (this may open/close modals)
      let contactInfo = {};
      
      
      // Try enhanced email extraction first
      if (window.extractEmailEnhanced) {
        try {
          const enhancedEmail = window.extractEmailEnhanced();
          if (enhancedEmail) {
            contactInfo.email = enhancedEmail;
          }
        } catch (err) {
        }
      }
      
      // Try inline extraction if no email found yet
      if (!contactInfo.email && window.extractInlineContactInfo) {
        try {
          const inlineInfo = window.extractInlineContactInfo();
          
          if (inlineInfo && typeof inlineInfo === 'object') {
            contactInfo = inlineInfo;
            if (inlineInfo.email) {
            } else {
            }
          } else {
          }
        } catch (err) {
        }
      } else if (!window.extractInlineContactInfo) {
      }
      
      // Only try modal extraction if inline didn't find email
      if (!contactInfo.email && window.extractContactInfo) {
        
        // Check connection level
        const connectionDegree = document.querySelector('.dist-value')?.textContent || 
                                document.querySelector('.distance-badge')?.textContent || '';
        
        if (connectionDegree.includes('3rd') || connectionDegree.includes('3°')) {
        }
        
        try {
          const modalContactInfo = await window.extractContactInfo();
          
          if (modalContactInfo && modalContactInfo.email) {
            contactInfo = modalContactInfo;
          } else {
          }
        } catch (err) {
        }
      } else if (!window.extractContactInfo) {
      }
      
      
      // Ensure email and phone fields exist in profile data
      if (!profileData.hasOwnProperty('email')) {
        profileData.email = '';
      }
      if (!profileData.hasOwnProperty('phone')) {
        profileData.phone = '';
      }
      
      // Add contact info to profile data
      
      if (contactInfo.email) {
        profileData.email = contactInfo.email;
      } else {
      }
      
      if (contactInfo.phone) {
        profileData.phone = contactInfo.phone;
      } else {
      }
      
      // Verify experience data wasn't lost
      
      // Force recalculation of years if needed
      if (profileData.experience && profileData.experience.length > 0) {
        let recalculated;
        
        if (window.calculateTotalExperienceAdvanced) {
          recalculated = window.calculateTotalExperienceAdvanced(profileData.experience);
        } else if (window.calculateTotalExperience) {
          recalculated = window.calculateTotalExperience(profileData.experience);
        }
        
        if (recalculated !== undefined) {
          
          if (recalculated !== profileData.years_experience) {
            profileData.years_experience = recalculated;
            
            // Apply manual override after recalculation
            if (window.applyManualOverride) {
              const overrideYears = window.applyManualOverride(profileData.linkedin_url, profileData.years_experience);
              if (overrideYears !== profileData.years_experience) {
                profileData.years_experience = overrideYears;
              }
            }
          }
        }
      }
      
      // Verify the data is clean
      if (window.verifyCleanData) {
        const isClean = window.verifyCleanData(profileData);
        if (!isClean) {
        }
      }
      
      // Final validation and email preservation
      if (!profileData.email && contactInfo && contactInfo.email) {
        profileData.email = contactInfo.email;
      }
      
      // Double-check email field exists
      if (!profileData.hasOwnProperty('email')) {
        profileData.email = '';
      }
      
      // If we still don't have email, log what we tried
      if (!profileData.email) {
      }
      
      // Validate and fix data before sending
      if (window.validateProfileData) {
        profileData = window.validateProfileData(profileData);
      }
      
      
      
      // Send the request through the background script to avoid CORS issues
      const response = await chrome.runtime.sendMessage({
        action: 'importProfile',
        data: profileData,
        authToken: authToken
      });
      
      
      if (!response || !response.success) {
        // Check if it's a duplicate error
        const errorMsg = response?.error || 'Import failed';
        if (errorMsg.includes('already been imported') || errorMsg.includes('already exists')) {
          showStatus('This profile has already been imported', 'exists');
          if (importButton) {
            updateButtonState('exists');
          }
          // Don't throw error for duplicates, just return
          return null;
        }
        throw new Error(errorMsg);
      }
      
      const result = response.data;
      
      // Check if the successful response indicates a duplicate
      if (result.is_duplicate) {
        showStatus('This profile has already been imported', 'exists');
        if (importButton) {
          updateButtonState('exists');
        }
      } else {
        showStatus('Profile imported successfully!', 'success');
        if (importButton) {
          updateButtonState('imported', result.candidate_id);
        }
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
      skills: [],
      years_experience: 0,
      email: '',
      phone: ''
    };
    
    // Extract name - updated selectors for 2025 LinkedIn
    const nameElement = document.querySelector('h1.text-heading-xlarge') || 
                       document.querySelector('h1') ||
                       document.querySelector('[aria-label*="Name"]');
    if (nameElement) {
      data.name = nameElement.textContent.trim();
    }
    
    // Extract headline - updated selectors
    const headlineElement = document.querySelector('.text-body-medium.break-words') ||
                           document.querySelector('div.text-body-medium:not(.t-black--light)') ||
                           document.querySelector('[data-generated-suggestion-target]');
    if (headlineElement) {
      data.headline = headlineElement.textContent.trim();
    }
    
    // Extract location - updated selectors
    const locationElement = document.querySelector('.text-body-small.inline.t-black--light.break-words') ||
                           document.querySelector('span.text-body-small.inline.t-black--light') ||
                           document.querySelector('[aria-label*="Location"]');
    if (locationElement) {
      data.location = locationElement.textContent.trim();
    }
    
    // Extract about section - updated selectors
    const aboutSection = document.querySelector('#about')?.parentElement;
    if (aboutSection) {
      const aboutText = aboutSection.querySelector('.display-flex.full-width span[aria-hidden="true"]') ||
                       aboutSection.querySelector('.inline-show-more-text span[aria-hidden="true"]') ||
                       aboutSection.querySelector('.pv-shared-text-with-see-more span');
      if (aboutText) {
        data.about = aboutText.textContent.trim();
      }
    }
    
    // Extract experience - more robust approach
    const experienceSection = document.querySelector('#experience')?.parentElement?.parentElement;
    if (experienceSection) {
      
      // Method 1: Try the most common structure first
      const experienceList = experienceSection.querySelector('ul') || experienceSection.querySelector('div > div > ul');
      if (experienceList) {
        const items = experienceList.querySelectorAll('li');
        
        items.forEach((item, index) => {
          try {
            // Get all visible text content
            const visibleSpans = item.querySelectorAll('span[aria-hidden="true"]:not(.visually-hidden)');
            const texts = Array.from(visibleSpans)
              .map(span => span.textContent.trim())
              .filter(t => t && t.length > 1);
            
            
            if (texts.length >= 2) {
              const exp = {
                title: '',
                company: '',
                duration: '',
                description: '',
                location: ''
              };
              
              // Pattern 1: Role title is usually the first bold text
              const boldText = item.querySelector('.t-bold span[aria-hidden="true"]');
              if (boldText) {
                exp.title = boldText.textContent.trim();
              } else if (texts[0]) {
                exp.title = texts[0];
              }
              
              // Pattern 2: Company info usually follows the title
              let companyIndex = exp.title ? 1 : 0;
              if (texts[companyIndex]) {
                const companyText = texts[companyIndex];
                if (companyText.includes(' · ')) {
                  const parts = companyText.split(' · ');
                  exp.company = parts[0].trim();
                  exp.employment_type = parts[1].trim();
                } else {
                  exp.company = companyText;
                }
              }
              
              // Pattern 3: Look for dates
              for (let i = companyIndex + 1; i < texts.length; i++) {
                const text = texts[i];
                if (text.match(/\d{4}|Present|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec/i)) {
                  exp.duration = text;
                  // Check if location follows duration
                  if (i + 1 < texts.length && texts[i + 1].includes(',')) {
                    exp.location = texts[i + 1];
                  }
                  break;
                }
              }
              
              // Pattern 4: Description is usually after duration/location
              const durationIndex = texts.indexOf(exp.duration);
              if (durationIndex !== -1 && durationIndex + 1 < texts.length) {
                const remainingTexts = texts.slice(durationIndex + 1);
                // Skip location if it's next
                const descTexts = exp.location && remainingTexts[0] === exp.location ? 
                                 remainingTexts.slice(1) : remainingTexts;
                exp.description = descTexts.join(' ').substring(0, 500);
              }
              
              // Only add if we have meaningful data
              if (exp.title || exp.company) {
                data.experience.push(exp);
              }
            }
          } catch (e) {
          }
        });
      }
      
      // Method 2: If no list found, try alternative structure
      if (data.experience.length === 0) {
        const experienceItems = experienceSection.querySelectorAll('[data-view-name="profile-component-entity"]') ||
                               experienceSection.querySelectorAll('.pvs-entity');
        
        
        experienceItems.forEach((item, index) => {
          try {
            const texts = [];
            item.querySelectorAll('span[aria-hidden="true"]').forEach(span => {
              const text = span.textContent.trim();
              if (text && !texts.includes(text)) texts.push(text);
            });
            
            if (texts.length >= 2) {
              data.experience.push({
                title: texts[0],
                company: texts[1].split(' · ')[0],
                duration: texts.find(t => t.match(/\d{4}|Present/i)) || '',
                description: texts.slice(3).join(' ').substring(0, 300)
              });
            }
          } catch (e) {
          }
        });
      }
      
      // Method 3: Last resort - extract from section text
      if (data.experience.length === 0) {
        const sectionText = experienceSection.innerText || experienceSection.textContent || '';
        
        // Look for common patterns in the text
        const lines = sectionText.split('\n').map(l => l.trim()).filter(l => l);
        let currentExp = null;
        
        lines.forEach(line => {
          // Skip the "Experience" header
          if (line === 'Experience') return;
          
          // Check for job titles (usually don't contain "at" and are not too long)
          if (line.length > 5 && line.length < 100 && 
              !line.toLowerCase().includes(' at ') && 
              !line.match(/\d{4}/) &&
              /^[A-Z]/.test(line)) {
            if (currentExp) data.experience.push(currentExp);
            currentExp = {
              title: line,
              company: '',
              duration: '',
              description: ''
            };
          } else if (currentExp) {
            if (line.toLowerCase().includes(' at ') || 
                line.includes('GmbH') || 
                line.includes('Ltd') || 
                line.includes('Inc')) {
              currentExp.company = line.replace(/^at\s+/i, '');
            } else if (line.match(/\d{4}|Present|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec/i)) {
              currentExp.duration = line;
            }
          }
        });
        
        if (currentExp) data.experience.push(currentExp);
      }
    }
    
    // Extract education - updated selectors
    const educationSection = document.querySelector('#education')?.parentElement;
    if (educationSection) {
      const educationItems = educationSection.querySelectorAll('li.artdeco-list__item') ||
                            educationSection.querySelectorAll('.pvs-entity');
      
      educationItems.forEach(item => {
        const schoolEl = item.querySelector('.mr1.hoverable-link-text span[aria-hidden="true"]') ||
                        item.querySelector('[data-field="education_school_name"]');
        
        const degreeEl = item.querySelector('.t-14.t-normal span[aria-hidden="true"]') ||
                        item.querySelector('[data-field="education_degree_name"]');
        
        const datesEl = item.querySelector('.t-14.t-normal.t-black--light span[aria-hidden="true"]') ||
                       item.querySelector('[data-field="education_date_range"]');
        
        if (schoolEl) {
          const edu = {
            school: schoolEl.textContent.trim(),
            degree: degreeEl ? degreeEl.textContent.trim() : '',
            dates: datesEl ? datesEl.textContent.trim() : ''
          };
          
          if (edu.school) {
            data.education.push(edu);
          }
        }
      });
    }
    
    // Extract skills - updated selectors
    const skillsSection = document.querySelector('#skills')?.parentElement;
    if (skillsSection) {
      const skillElements = skillsSection.querySelectorAll('.mr1.t-bold span[aria-hidden="true"]') ||
                           skillsSection.querySelectorAll('[data-field="skill_name"]');
      
      skillElements.forEach(skill => {
        const skillName = skill.textContent.trim();
        if (skillName && !data.skills.includes(skillName)) {
          data.skills.push(skillName);
        }
      });
    }
    
    // DO NOT build full_text here - let aggressive cleaning handle it completely
    data.full_text = ''; // Will be built by aggressive cleaning
    
    // Profile data extracted
    
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
  
  
})();