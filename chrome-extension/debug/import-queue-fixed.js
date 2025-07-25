/**
 * Fixed bulk import for LinkedIn search results
 * Targets the correct selectors based on debug results
 */

(function() {
  'use strict';
  
  console.log('✨ Bulk Import Fixed: Starting...');
  
  // Main injection function
  function injectCheckboxes() {
    // Use the selector that works: li.reusable-search__result-container
    const results = document.querySelectorAll('li.reusable-search__result-container');
    console.log(`✨ Found ${results.length} search results`);
    
    if (results.length === 0) {
      // Try alternative selector from debug
      const altResults = document.querySelectorAll('.reusable-search__entity-result-list > li');
      if (altResults.length > 0) {
        console.log(`✨ Using alternative selector, found ${altResults.length} results`);
        processResults(altResults);
      }
    } else {
      processResults(results);
    }
  }
  
  function processResults(results) {
    results.forEach((result, index) => {
      // Skip if already has checkbox
      if (result.querySelector('.bulk-import-checkbox-fixed')) return;
      
      // Find the content area - look for the image/avatar area
      const imgContainer = result.querySelector('.entity-result__image') || 
                          result.querySelector('.presence-entity__image') ||
                          result.querySelector('[class*="image"]');
      
      if (!imgContainer) {
        console.log(`No image container found for result ${index}, trying alternative approach`);
        // Alternative: just prepend to the result
        addCheckboxToResult(result, result);
        return;
      }
      
      // Add checkbox near the image
      addCheckboxToResult(result, imgContainer);
    });
    
    console.log('✨ Checkboxes injected successfully');
  }
  
  function addCheckboxToResult(resultElement, targetContainer) {
    // Create checkbox container
    const checkboxContainer = document.createElement('div');
    checkboxContainer.className = 'bulk-import-checkbox-fixed';
    checkboxContainer.style.cssText = `
      position: absolute;
      top: 16px;
      left: 16px;
      background: white;
      border: 3px solid #0a66c2;
      border-radius: 6px;
      padding: 2px;
      z-index: 10;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    `;
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.style.cssText = `
      width: 24px;
      height: 24px;
      cursor: pointer;
      margin: 0;
      display: block;
    `;
    
    // Get profile data
    const profileLink = resultElement.querySelector('a[href*="/in/"]');
    if (profileLink) {
      checkbox.dataset.profileUrl = profileLink.href.split('?')[0];
      
      // Try multiple selectors for the name
      let profileName = 'Unknown';
      const nameSelectors = [
        '.entity-result__title-text',
        'span[aria-hidden="true"]',
        '.entity-result__title-line span:first-child',
        '[class*="entity-result__title"] span'
      ];
      
      for (const selector of nameSelectors) {
        const nameElement = resultElement.querySelector(selector);
        if (nameElement && nameElement.textContent.trim()) {
          profileName = nameElement.textContent.trim();
          break;
        }
      }
      
      checkbox.dataset.profileName = profileName;
      console.log(`Added checkbox for: ${profileName}`);
    }
    
    checkboxContainer.appendChild(checkbox);
    
    // Make sure the parent is relatively positioned
    if (targetContainer === resultElement) {
      resultElement.style.position = 'relative';
      resultElement.insertBefore(checkboxContainer, resultElement.firstChild);
    } else {
      targetContainer.style.position = 'relative';
      targetContainer.appendChild(checkboxContainer);
    }
  }
  
  // Update button handlers
  function setupButtonHandlers() {
    // Wait a bit for buttons to be created
    setTimeout(() => {
      // Find select all button
      const buttons = document.querySelectorAll('.bulk-import-button-floating button, .bulk-import-button button');
      
      if (buttons.length >= 2) {
        // First button is Select All
        buttons[0].onclick = (e) => {
          e.preventDefault();
          const checkboxes = document.querySelectorAll('.bulk-import-checkbox-fixed input[type="checkbox"]');
          const allChecked = Array.from(checkboxes).every(cb => cb.checked);
          
          checkboxes.forEach(cb => {
            cb.checked = !allChecked;
          });
          
          console.log(`✨ Toggled ${checkboxes.length} checkboxes`);
        };
        
        // Second button is Add to Queue
        buttons[1].onclick = async (e) => {
          e.preventDefault();
          const checkedBoxes = document.querySelectorAll('.bulk-import-checkbox-fixed input[type="checkbox"]:checked');
          
          if (checkedBoxes.length === 0) {
            alert('Please select at least one profile');
            return;
          }
          
          console.log(`✨ Adding ${checkedBoxes.length} profiles to queue`);
          
          // Get existing queue from the import queue manager
          const queue = window.__linkedInImportQueue?.queue || [];
          let addedCount = 0;
          
          for (const checkbox of checkedBoxes) {
            const profileUrl = checkbox.dataset.profileUrl;
            const profileName = checkbox.dataset.profileName;
            
            if (profileUrl) {
              // Use the import queue manager's addToQueue method
              if (window.__linkedInImportQueue) {
                const added = await window.__linkedInImportQueue.addToQueue({
                  url: profileUrl,
                  name: profileName
                });
                if (added) addedCount++;
              }
              
              // Uncheck after adding
              checkbox.checked = false;
            }
          }
          
          // Show success message
          if (window.__linkedInImportQueue) {
            window.__linkedInImportQueue.showNotification(
              `Added ${addedCount} profiles to import queue`
            );
          }
        };
        
        console.log('✨ Button handlers setup complete');
      }
    }, 1000);
  }
  
  // Run injection after page loads
  setTimeout(() => {
    if (window.location.pathname.includes('/search/results/')) {
      injectCheckboxes();
      setupButtonHandlers();
      
      // Re-inject when results update
      const observer = new MutationObserver(() => {
        injectCheckboxes();
      });
      
      const resultsContainer = document.querySelector('.reusable-search__entity-result-list') ||
                              document.querySelector('[class*="search-results"]');
      
      if (resultsContainer) {
        observer.observe(resultsContainer, {
          childList: true,
          subtree: true
        });
      }
    }
  }, 3000);
  
  console.log('✨ Bulk Import Fixed: Ready');
})();