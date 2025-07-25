// Filter out company-level total durations
window.filterCompanyTotals = function(experiences) {
  console.log('=== Filtering Company Totals ===');
  console.log(`Input: ${experiences.length} experiences`);
  
  const filtered = [];
  const companyTotals = [];
  
  experiences.forEach((exp, idx) => {
    let isCompanyTotal = false;
    
    // Pattern 1: Company name with "at X years" or "· X years"
    if (exp.company && exp.company.match(/\s+(at|·)\s+\d+\s*yrs?/i)) {
      console.log(`Experience ${idx + 1}: Company contains duration: "${exp.company}"`);
      isCompanyTotal = true;
    }
    
    // Pattern 2: Duration that starts with company name
    if (exp.duration && exp.duration.match(/^[A-Za-z\s&.,]+\s+(at|·)\s+\d+\s*yrs?/i)) {
      console.log(`Experience ${idx + 1}: Duration contains company total: "${exp.duration}"`);
      isCompanyTotal = true;
    }
    
    // Pattern 3: Title that looks like a company name with duration
    if (exp.title && exp.title.match(/^[A-Z][A-Za-z\s&.,]+\s+(at|·)\s+\d+\s*yrs?/i)) {
      console.log(`Experience ${idx + 1}: Title contains company total: "${exp.title}"`);
      isCompanyTotal = true;
    }
    
    // Pattern 4: Company name matches a known company total
    // Check if this company name appears in another experience with a duration attached
    const companyBase = exp.company ? exp.company.split(/\s+(at|·)\s+/)[0].trim() : '';
    if (companyBase) {
      const hasDuplicateWithDuration = experiences.some((other, otherIdx) => {
        if (idx === otherIdx) return false;
        const otherCompany = other.company || '';
        return otherCompany.startsWith(companyBase) && otherCompany.includes(' at ');
      });
      
      if (hasDuplicateWithDuration) {
        console.log(`Experience ${idx + 1}: Appears to be individual role for company "${companyBase}"`);
        // This is likely an individual role, not a total
      }
    }
    
    // Pattern 5: No title or generic title with company duration
    if ((!exp.title || exp.title === exp.company) && exp.duration && exp.duration.match(/\d+\s*yrs?\s*\d*\s*mos?/)) {
      // Check if there are other experiences with the same company
      const sameCompanyCount = experiences.filter(e => 
        e.company && exp.company && 
        (e.company === exp.company || e.company.includes(exp.company) || exp.company.includes(e.company))
      ).length;
      
      if (sameCompanyCount > 1) {
        console.log(`Experience ${idx + 1}: Likely company total (no specific title, ${sameCompanyCount} roles at same company)`);
        isCompanyTotal = true;
      }
    }
    
    if (isCompanyTotal) {
      companyTotals.push({
        index: idx,
        experience: exp
      });
      console.log(`FILTERED OUT: ${exp.title || 'No Title'} at ${exp.company} (${exp.duration})`);
    } else {
      filtered.push(exp);
    }
  });
  
  console.log(`\nFiltered out ${companyTotals.length} company totals`);
  console.log(`Remaining: ${filtered.length} individual experiences`);
  
  // Additional validation: if we filtered out too many, we might be too aggressive
  if (companyTotals.length > experiences.length / 2) {
    console.warn('WARNING: Filtered out more than half of experiences. This might be too aggressive.');
  }
  
  return filtered;
};