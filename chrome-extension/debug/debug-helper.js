// Debug helper for LinkedIn data extraction
(function() {
  'use strict';
  
  // Only run on LinkedIn profile pages
  if (!window.location.pathname.includes('/in/')) {
    return;
  }
  
  console.log('=== LinkedIn Profile Debug Helper ===');
  console.log('URL:', window.location.href);
  
  // Function to safely get text content
  function safeText(element) {
    return element ? element.textContent.trim() : '[Not Found]';
  }
  
  // Check for main profile sections
  console.log('\n--- Profile Structure ---');
  console.log('Name h1:', document.querySelector('h1.text-heading-xlarge'));
  console.log('About section:', document.querySelector('#about')?.parentElement);
  console.log('Experience section:', document.querySelector('#experience')?.parentElement);
  console.log('Education section:', document.querySelector('#education')?.parentElement);
  console.log('Skills section:', document.querySelector('#skills')?.parentElement);
  
  // Test name extraction
  console.log('\n--- Name Extraction ---');
  const nameSelectors = [
    'h1.text-heading-xlarge',
    'h1',
    '[aria-label*="Name"]'
  ];
  nameSelectors.forEach(selector => {
    const el = document.querySelector(selector);
    console.log(`${selector}:`, el ? safeText(el) : 'Not found');
  });
  
  // Test headline extraction
  console.log('\n--- Headline Extraction ---');
  const headlineSelectors = [
    '.text-body-medium.break-words',
    'div.text-body-medium:not(.t-black--light)',
    '[data-generated-suggestion-target]'
  ];
  headlineSelectors.forEach(selector => {
    const el = document.querySelector(selector);
    console.log(`${selector}:`, el ? safeText(el).substring(0, 50) + '...' : 'Not found');
  });
  
  // Test experience extraction
  console.log('\n--- Experience Items ---');
  const experienceSection = document.querySelector('#experience')?.parentElement;
  if (experienceSection) {
    const items = experienceSection.querySelectorAll('li.artdeco-list__item');
    console.log(`Found ${items.length} experience items`);
    
    if (items.length > 0) {
      console.log('First experience item structure:');
      const firstItem = items[0];
      
      // Log the HTML structure of the first item
      console.log('HTML Preview:', firstItem.innerHTML.substring(0, 200) + '...');
      
      // Try to find title
      const titleSelectors = [
        '.mr1.t-bold span[aria-hidden="true"]',
        '.display-flex.align-items-center span[aria-hidden="true"]',
        'span.t-bold span',
        'div[data-field="experience_title"]'
      ];
      
      titleSelectors.forEach(selector => {
        const el = firstItem.querySelector(selector);
        console.log(`Title ${selector}:`, el ? safeText(el) : 'Not found');
      });
    }
  }
  
  // Test education extraction
  console.log('\n--- Education Items ---');
  const educationSection = document.querySelector('#education')?.parentElement;
  if (educationSection) {
    const items = educationSection.querySelectorAll('li.artdeco-list__item');
    console.log(`Found ${items.length} education items`);
  }
  
  // Test skills extraction
  console.log('\n--- Skills Items ---');
  const skillsSection = document.querySelector('#skills')?.parentElement;
  if (skillsSection) {
    const skills = skillsSection.querySelectorAll('.mr1.t-bold span[aria-hidden="true"]');
    console.log(`Found ${skills.length} skills`);
    if (skills.length > 0) {
      console.log('First 5 skills:', Array.from(skills).slice(0, 5).map(s => safeText(s)));
    }
  }
  
  console.log('\n=== End Debug Info ===');
})();