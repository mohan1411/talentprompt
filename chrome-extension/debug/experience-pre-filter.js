// Pre-filter to identify and skip company totals before they're added to experience array
window.shouldSkipExperienceItem = function(texts, isGroupedParent = false) {
  if (!texts || texts.length === 0) return true;
  
  console.log('Pre-filter checking:', texts.slice(0, 3));
  
  // If this is a grouped parent item (has sub-roles), skip it
  if (isGroupedParent) {
    console.log('  -> Skipping: Grouped parent item');
    return true;
  }
  
  // Pattern 1: First text is company name with duration
  // e.g., ["ANZ", "Full-time · 14 yrs 7 mos"]
  if (texts.length >= 2) {
    const firstText = texts[0];
    const secondText = texts[1];
    
    // Check if second text is employment type + duration without a role
    if (secondText.match(/^(Full-time|Part-time|Contract|Freelance|Internship)\s*[·•]?\s*\d+\s*yrs?/i)) {
      // And first text doesn't look like a job title
      if (!firstText.match(/Manager|Director|Engineer|Developer|Analyst|Lead|Senior|Junior|Executive|Consultant|Specialist|Officer|Head|VP|President|Architect|Administrator|Coordinator/i)) {
        console.log('  -> Skipping: Company with employment type + duration (no role)');
        return true;
      }
    }
  }
  
  // Pattern 2: Single company name with duration attached
  if (texts[0] && texts[0].match(/^[A-Z][A-Za-z\s&.,]+\s+(at|·)\s+\d+\s*yrs?/i)) {
    console.log('  -> Skipping: Company name with duration attached');
    return true;
  }
  
  // Pattern 3: No job title, just company and duration
  if (texts.length === 2 || texts.length === 3) {
    const hasJobTitle = texts.some(text => 
      text.match(/Manager|Director|Engineer|Developer|Analyst|Lead|Senior|Junior|Executive|Consultant|Specialist|Officer|Head|VP|President|Architect|Administrator|Coordinator|Designer|Accountant|Advisor|Associate|Intern|Trainee/i)
    );
    
    const hasDuration = texts.some(text => 
      text.match(/\d+\s*yrs?\s*\d*\s*mos?/i)
    );
    
    if (!hasJobTitle && hasDuration) {
      console.log('  -> Skipping: No job title found, only company and duration');
      return true;
    }
  }
  
  // Pattern 4: Title equals company (often indicates a summary)
  if (texts.length >= 2 && texts[0] === texts[1]) {
    console.log('  -> Skipping: Title equals company');
    return true;
  }
  
  console.log('  -> Including: Appears to be individual role');
  return false;
};

// Enhanced experience item analyzer
window.analyzeExperienceItem = function(item, index) {
  const analysis = {
    index: index,
    isGrouped: false,
    isCompanyTotal: false,
    parentTexts: [],
    roleCount: 0,
    roles: []
  };
  
  // Check if grouped
  const groupedContainer = item.querySelector('ul.pvs-list');
  analysis.isGrouped = !!groupedContainer;
  
  if (analysis.isGrouped) {
    // For grouped experiences, extract parent-level text (company info)
    const parentSpans = [];
    item.querySelectorAll('span[aria-hidden="true"]').forEach(span => {
      // Only get spans that are NOT inside the sub-list
      if (!span.closest('ul.pvs-list')) {
        parentSpans.push(span);
      }
    });
    
    parentSpans.forEach(span => {
      const text = span.textContent.trim();
      if (text && text.length > 1) {
        analysis.parentTexts.push(text);
      }
    });
    
    // Count sub-roles
    const subItems = groupedContainer.querySelectorAll('li');
    analysis.roleCount = subItems.length;
    
    // The parent item itself is likely just company info, not a role
    analysis.isCompanyTotal = true;
    
    console.log(`Item ${index + 1}: GROUPED with ${analysis.roleCount} roles`);
    console.log(`  Parent texts:`, analysis.parentTexts);
  } else {
    // For non-grouped, check if it's a company total
    const texts = [];
    item.querySelectorAll('span[aria-hidden="true"]').forEach(span => {
      if (!span.closest('.visually-hidden')) {
        const text = span.textContent.trim();
        if (text && text.length > 1) {
          texts.push(text);
        }
      }
    });
    
    analysis.parentTexts = texts;
    analysis.isCompanyTotal = window.shouldSkipExperienceItem(texts, false);
    
    console.log(`Item ${index + 1}: SINGLE ${analysis.isCompanyTotal ? '(COMPANY TOTAL)' : '(ROLE)'}`);
    console.log(`  Texts:`, texts.slice(0, 3));
  }
  
  return analysis;
};