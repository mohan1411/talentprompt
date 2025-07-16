// Advanced debugging for experience calculation
window.debugExperienceCalculation = function() {
  console.log('%c=== EXPERIENCE CALCULATION DEBUGGER ===', 'color: blue; font-weight: bold; font-size: 14px');
  console.log('Profile URL:', window.location.href);
  console.log('Debug time:', new Date().toISOString());
  
  // Extract experience data
  const expSection = document.querySelector('#experience')?.closest('section');
  if (!expSection) {
    console.error('Experience section not found!');
    return;
  }
  
  console.log('\n%c1. RAW DOM ANALYSIS', 'color: green; font-weight: bold');
  
  // Find all experience items
  const expList = expSection.querySelector('ul.pvs-list') || expSection.querySelector('ul');
  if (!expList) {
    console.error('Experience list not found!');
    return;
  }
  
  const items = expList.querySelectorAll('li');
  console.log(`Found ${items.length} list items`);
  
  // Analyze each item in detail
  items.forEach((item, idx) => {
    console.log(`\n%cItem ${idx + 1}:`, 'color: blue; font-weight: bold');
    
    // Check if it's a grouped experience
    const isGrouped = !!item.querySelector('ul.pvs-list');
    console.log('Is grouped experience:', isGrouped);
    
    // Extract all visible text
    const allTexts = [];
    item.querySelectorAll('span[aria-hidden="true"]').forEach(span => {
      if (!span.closest('.visually-hidden')) {
        const text = span.textContent.trim();
        if (text) allTexts.push(text);
      }
    });
    
    console.log('All texts found:', allTexts);
    
    // Try to identify patterns
    allTexts.forEach((text, i) => {
      const analysis = [];
      
      if (text.match(/\d+\s*yrs?\s*\d*\s*mos?/i)) {
        analysis.push('DURATION');
      }
      if (text.match(/\d{4}/)) {
        analysis.push('YEAR');
      }
      if (text.match(/Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec/i)) {
        analysis.push('MONTH');
      }
      if (text.match(/Present|Current/i)) {
        analysis.push('PRESENT');
      }
      if (text.includes('·')) {
        analysis.push('SEPARATOR');
      }
      if (text.match(/^[A-Z]/)) {
        analysis.push('CAPITALIZED');
      }
      if (text.includes(',')) {
        analysis.push('LOCATION?');
      }
      if (text.match(/\s+(at|@)\s+/i)) {
        analysis.push('COMPANY_TOTAL?');
      }
      
      console.log(`  [${i}] "${text}" - ${analysis.join(', ') || 'TEXT'}`);
    });
    
    // If grouped, analyze sub-items
    if (isGrouped) {
      const subList = item.querySelector('ul.pvs-list');
      const subItems = subList.querySelectorAll('li');
      console.log(`  Contains ${subItems.length} sub-roles`);
      
      subItems.forEach((subItem, subIdx) => {
        const subTexts = [];
        subItem.querySelectorAll('span[aria-hidden="true"]').forEach(span => {
          if (!span.closest('.visually-hidden')) {
            const text = span.textContent.trim();
            if (text) subTexts.push(text);
          }
        });
        console.log(`    Sub-role ${subIdx + 1}:`, subTexts.slice(0, 4).join(' | '));
      });
    }
  });
  
  // Now run the extraction and calculation
  console.log('\n%c2. EXTRACTION RESULTS', 'color: green; font-weight: bold');
  
  if (window.extractUltraCleanProfile) {
    const profileData = window.extractUltraCleanProfile();
    
    console.log('\nExtracted experiences:');
    profileData.experience.forEach((exp, idx) => {
      console.log(`\nExperience ${idx + 1}:`);
      console.log('  Title:', exp.title);
      console.log('  Company:', exp.company);
      console.log('  Duration:', exp.duration || 'NO DURATION');
      console.log('  Location:', exp.location || 'N/A');
    });
    
    console.log('\n%c3. CALCULATION DETAILS', 'color: green; font-weight: bold');
    
    if (window.calculateTotalExperienceAdvanced) {
      console.log('\nRunning advanced calculator with detailed logging...');
      const years = window.calculateTotalExperienceAdvanced(profileData.experience);
      console.log(`\n%cFINAL RESULT: ${years} years`, 'color: red; font-weight: bold; font-size: 16px');
    }
  }
  
  console.log('\n%c=== END DEBUG ===', 'color: blue; font-weight: bold; font-size: 14px');
};

// Auto-run debugger on specific problematic profiles
if (window.location.href.includes('anil-narasimhappa-64000518')) {
  console.log('%cDETECTED PROBLEMATIC PROFILE - Running debugger', 'color: orange; font-weight: bold');
  setTimeout(() => {
    window.debugExperienceCalculation();
    
    // Also run a specific check for ANZ experiences
    console.log('\n%cANZ SPECIFIC DEBUG', 'color: purple; font-weight: bold');
    const allText = document.body.innerText || '';
    const anzMatches = allText.match(/ANZ[^\\n]*\\d+\\s*yrs?[^\\n]*/gi);
    if (anzMatches) {
      console.log('Found ANZ-related text with durations:');
      anzMatches.forEach((match, idx) => {
        console.log(`  ${idx + 1}: "${match}"`);
      });
    }
  }, 3000);
}