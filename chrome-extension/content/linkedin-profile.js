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
      
      // Send through background script to avoid CORS
      chrome.runtime.sendMessage({
        action: 'checkProfileExists',
        linkedin_url: profileData.linkedin_url,
        authToken: authToken
      }, response => {
        if (response && response.exists) {
          updateButtonState('exists', response.candidate_id);
        }
      });
    } catch (error) {
      console.error('Error checking profile:', error);
    }
  }
  
  // Handle import button click
  async function handleImport() {
    console.log('=== Import Handler v2 - Enhanced Email Extraction ===');
    
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
      
      // Add a small delay to ensure all scripts are loaded
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // FIRST: Extract profile data (including experience) BEFORE opening any modals
      let profileData;
      if (window.extractUltraCleanProfile) {
        console.log('Using ultra clean extraction for profile data...');
        profileData = window.extractUltraCleanProfile();
        console.log('Profile extracted with', profileData.experience?.length || 0, 'experiences');
        console.log('Years of experience from profile:', profileData.years_experience);
      } else {
        console.log('Ultra clean extractor not available, using standard extraction');
        profileData = extractProfileData();
      }
      
      // SECOND: Extract contact info (this may open/close modals)
      let contactInfo = {};
      
      // Try inline extraction first (doesn't modify DOM)
      if (window.extractInlineContactInfo) {
        console.log('Trying inline contact extraction first...');
        try {
          const inlineInfo = window.extractInlineContactInfo();
          console.log('Inline extraction returned:', JSON.stringify(inlineInfo));
          if (inlineInfo && inlineInfo.email) {
            contactInfo = inlineInfo;
            console.log('Inline extraction found email:', contactInfo.email);
          } else {
            console.log('Inline extraction did not find email');
          }
        } catch (err) {
          console.error('Error in inline extraction:', err);
        }
      } else {
        console.log('Inline contact extractor not available');
      }
      
      // Only try modal extraction if inline didn't find email
      if (!contactInfo.email && window.extractContactInfo) {
        console.log('No inline email found, attempting modal extraction...');
        console.log('Contact extractor available:', typeof window.extractContactInfo);
        try {
          const modalContactInfo = await window.extractContactInfo();
          console.log('Modal extraction raw result:', modalContactInfo);
          console.log('Modal contact info stringified:', JSON.stringify(modalContactInfo));
          console.log('Modal result type:', typeof modalContactInfo);
          console.log('Modal result keys:', modalContactInfo ? Object.keys(modalContactInfo) : 'null');
          
          if (modalContactInfo && modalContactInfo.email) {
            contactInfo = modalContactInfo;
            console.log('Modal extraction found email:', contactInfo.email);
          } else {
            console.log('Modal extraction did not find email');
          }
        } catch (err) {
          console.error('Error during modal contact extraction:', err);
          console.error('Error stack:', err.stack);
        }
      } else if (!window.extractContactInfo) {
        console.error('Contact extractor function not available!');
      }
      
      // Ensure email and phone fields exist in profile data
      if (!profileData.hasOwnProperty('email')) {
        profileData.email = '';
      }
      if (!profileData.hasOwnProperty('phone')) {
        profileData.phone = '';
      }
      
      // Add contact info to profile data
      console.log('Profile data before adding contact info:', {
        email: profileData.email,
        phone: profileData.phone,
        years_experience: profileData.years_experience,
        experience_count: profileData.experience?.length || 0
      });
      
      if (contactInfo.email) {
        profileData.email = contactInfo.email;
        console.log('Added email to profile data:', contactInfo.email);
      } else {
        console.log('No email in contact info to add');
      }
      
      if (contactInfo.phone) {
        profileData.phone = contactInfo.phone;
        console.log('Added phone to profile data:', contactInfo.phone);
      } else {
        console.log('No phone in contact info to add');
      }
      
      // Verify experience data wasn't lost
      console.log('Profile data after adding contact info:', {
        email: profileData.email,
        phone: profileData.phone,
        years_experience: profileData.years_experience,
        experience_count: profileData.experience?.length || 0
      });
      
      console.log('Profile data after adding contact info:', {
        email: profileData.email,
        phone: profileData.phone
      });
      
      // Verify the data is clean
      if (window.verifyCleanData) {
        const isClean = window.verifyCleanData(profileData);
        if (!isClean) {
          console.warn('WARNING: Profile data contains irrelevant content!');
        }
      }
      
      // Final validation and email preservation
      if (!profileData.email && contactInfo && contactInfo.email) {
        console.error('Email was lost! Recovering from contactInfo');
        profileData.email = contactInfo.email;
      }
      
      // Double-check email field exists
      if (!profileData.hasOwnProperty('email')) {
        console.error('Email field missing from profileData! Adding it.');
        profileData.email = '';
      }
      
      // If we still don't have email, log what we tried
      if (!profileData.email) {
        console.log('=== Email Extraction Debug ===');
        console.log('ContactInfo object:', JSON.stringify(contactInfo));
        console.log('ContactInfo has email property:', contactInfo.hasOwnProperty('email'));
        console.log('ContactInfo.email value:', contactInfo.email);
        console.log('ProfileData has email property:', profileData.hasOwnProperty('email'));
        console.log('ProfileData.email value:', profileData.email);
      }
      
      console.log('Final profile data to import:', profileData);
      console.log('Email in final data:', profileData.email || 'MISSING');
      console.log('All profile data keys:', Object.keys(profileData));
      
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
      console.log('Found experience section, attempting extraction...');
      
      // Method 1: Try the most common structure first
      const experienceList = experienceSection.querySelector('ul') || experienceSection.querySelector('div > div > ul');
      if (experienceList) {
        const items = experienceList.querySelectorAll('li');
        console.log(`Found ${items.length} experience items in list`);
        
        items.forEach((item, index) => {
          try {
            // Get all visible text content
            const visibleSpans = item.querySelectorAll('span[aria-hidden="true"]:not(.visually-hidden)');
            const texts = Array.from(visibleSpans)
              .map(span => span.textContent.trim())
              .filter(t => t && t.length > 1);
            
            console.log(`Item ${index + 1} texts:`, texts);
            
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
                console.log(`Added experience ${data.experience.length}:`, exp);
              }
            }
          } catch (e) {
            console.error(`Error parsing experience item ${index + 1}:`, e);
          }
        });
      }
      
      // Method 2: If no list found, try alternative structure
      if (data.experience.length === 0) {
        const experienceItems = experienceSection.querySelectorAll('[data-view-name="profile-component-entity"]') ||
                               experienceSection.querySelectorAll('.pvs-entity');
        
        console.log(`Trying alternative method, found ${experienceItems.length} items`);
        
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
            console.error('Error in alternative experience parsing:', e);
          }
        });
      }
      
      // Method 3: Last resort - extract from section text
      if (data.experience.length === 0) {
        console.log('No structured experience found, extracting from text');
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
    
    // Log what we found for debugging
    console.log('Extracted LinkedIn data:', {
      name: data.name,
      headline: data.headline,
      location: data.location,
      aboutLength: data.about.length,
      experienceCount: data.experience.length,
      educationCount: data.education.length,
      skillsCount: data.skills.length,
      fullTextLength: data.full_text.length
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