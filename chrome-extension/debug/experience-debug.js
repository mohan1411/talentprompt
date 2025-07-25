// Debug script specifically for experience extraction
(function() {
  'use strict';
  
  console.log('=== Experience Extraction Debug ===');
  
  // Method 1: Find experience section by ID
  const expById = document.querySelector('#experience');
  console.log('Experience by ID:', expById);
  
  if (expById) {
    console.log('Experience section parent:', expById.parentElement);
    console.log('Experience section grandparent:', expById.parentElement?.parentElement);
    
    // Look for list items in various ways
    const parent = expById.parentElement?.parentElement || expById.parentElement;
    if (parent) {
      console.log('\n--- Searching for experience items ---');
      
      // Try different selectors
      const selectors = [
        'li.artdeco-list__item',
        'li',
        '.pvs-entity',
        'div.pvs-entity',
        '[data-view-name="profile-component-entity"]',
        'div.display-flex.flex-column.full-width'
      ];
      
      selectors.forEach(selector => {
        const items = parent.querySelectorAll(selector);
        console.log(`${selector}: found ${items.length} items`);
        
        if (items.length > 0 && items.length < 10) {
          console.log(`First item preview for ${selector}:`);
          const firstItem = items[0];
          
          // Get all text content
          const texts = [];
          firstItem.querySelectorAll('span[aria-hidden="true"]').forEach(span => {
            const text = span.textContent.trim();
            if (text) texts.push(text);
          });
          
          console.log('Texts found:', texts);
          
          // Log HTML structure
          console.log('HTML structure (first 500 chars):', firstItem.innerHTML.substring(0, 500));
        }
      });
    }
  }
  
  // Method 2: Search for experience-related text
  console.log('\n--- Text-based search ---');
  const allSpans = document.querySelectorAll('span');
  const experienceRelated = [];
  
  allSpans.forEach(span => {
    const text = span.textContent.trim();
    if (text && (
      text.includes('System Engineer') ||
      text.includes('Valyue Consulting') ||
      text.includes('Robert Bosch') ||
      text.includes('Specialist at')
    )) {
      experienceRelated.push({
        text: text,
        parent: span.parentElement?.tagName,
        grandparent: span.parentElement?.parentElement?.tagName,
        classes: span.className
      });
    }
  });
  
  console.log('Experience-related texts found:', experienceRelated);
  
  // Method 3: Look for specific patterns
  console.log('\n--- Pattern search ---');
  document.querySelectorAll('div').forEach(div => {
    const text = div.textContent.trim();
    if (text.startsWith('System Engineer at') || text.includes('Specialist at Robert')) {
      console.log('Found experience div:', {
        text: text.substring(0, 100),
        className: div.className,
        childCount: div.children.length
      });
    }
  });
  
  console.log('=== End Experience Debug ===');
})();