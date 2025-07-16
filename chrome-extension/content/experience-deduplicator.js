// Deduplicate experiences by detecting company totals vs individual roles
window.deduplicateExperiences = function(experiences) {
  console.log('=== EXPERIENCE DEDUPLICATION ===');
  console.log(`Input: ${experiences.length} experiences`);
  
  // Group by company
  const byCompany = {};
  
  experiences.forEach((exp, idx) => {
    // Extract base company name
    let baseCompany = exp.company || exp.title || '';
    
    // Remove duration info from company name
    baseCompany = baseCompany.split(/\s+(at|·)\s+\d+/)[0].trim();
    
    // Remove employment type
    baseCompany = baseCompany.replace(/\s*[-–]\s*(Full-time|Part-time|Contract|Freelance|Internship).*$/i, '').trim();
    
    if (!baseCompany) return;
    
    if (!byCompany[baseCompany]) {
      byCompany[baseCompany] = [];
    }
    
    byCompany[baseCompany].push({
      index: idx,
      experience: exp
    });
  });
  
  console.log('Grouped by company:', Object.keys(byCompany));
  
  // Analyze each company group
  const toRemove = new Set();
  
  Object.entries(byCompany).forEach(([company, items]) => {
    console.log(`\nAnalyzing ${company}: ${items.length} entries`);
    
    if (items.length > 1) {
      // Multiple entries for same company - check for totals
      
      // Find potential company totals
      const potentialTotals = items.filter(item => {
        const exp = item.experience;
        
        // Check if this looks like a company total
        const isTotal = 
          // No specific job title
          (!exp.title || exp.title === company || exp.title.match(/^[A-Z][A-Za-z\s&]+$/)) &&
          // Has duration
          exp.duration &&
          // No job-specific keywords
          !exp.title?.match(/Manager|Director|Engineer|Developer|Analyst|Lead|Senior|Junior|Executive|Consultant/i);
        
        if (isTotal) {
          console.log(`  Potential total at index ${item.index}:`, {
            title: exp.title,
            company: exp.company,
            duration: exp.duration
          });
        }
        
        return isTotal;
      });
      
      // Find individual roles
      const individualRoles = items.filter(item => {
        const exp = item.experience;
        return exp.title && exp.title.match(/Manager|Director|Engineer|Developer|Analyst|Lead|Senior|Junior|Executive|Consultant|Specialist|Officer|Architect|Designer|Administrator|Coordinator|Assistant|Advisor|Head|VP|President|Partner|Associate|Intern|Accountant|Auditor|Programmer|Scientist|Researcher/i);
      });
      
      console.log(`  Found ${potentialTotals.length} potential totals, ${individualRoles.length} individual roles`);
      
      // If we have both totals and individual roles, remove the totals
      if (potentialTotals.length > 0 && individualRoles.length > 0) {
        potentialTotals.forEach(item => {
          toRemove.add(item.index);
          console.log(`  REMOVING total at index ${item.index}`);
        });
      }
      
      // Special case: If one entry has much longer duration than others, it's likely a total
      if (items.length > 2) {
        const durations = items.map(item => {
          const exp = item.experience;
          if (!exp.duration) return 0;
          
          const yearsMatch = exp.duration.match(/(\d+)\s*yrs?/);
          const monthsMatch = exp.duration.match(/(\d+)\s*mos?/);
          const years = yearsMatch ? parseInt(yearsMatch[1]) : 0;
          const months = monthsMatch ? parseInt(monthsMatch[1]) : 0;
          
          return (years * 12) + months;
        });
        
        const maxDuration = Math.max(...durations);
        const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
        
        // If one duration is more than 2x the average, it's likely a total
        items.forEach((item, idx) => {
          if (durations[idx] > avgDuration * 2 && durations[idx] === maxDuration) {
            const exp = item.experience;
            if (!exp.title?.match(/Manager|Director|Engineer|Developer/i)) {
              toRemove.add(item.index);
              console.log(`  REMOVING outlier duration at index ${item.index} (${durations[idx]} months vs avg ${avgDuration})`);
            }
          }
        });
      }
    }
  });
  
  // Filter out removed items
  const deduplicated = experiences.filter((_, idx) => !toRemove.has(idx));
  
  console.log(`\nDeduplication complete:`);
  console.log(`  Removed: ${toRemove.size} company totals`);
  console.log(`  Remaining: ${deduplicated.length} experiences`);
  
  return deduplicated;
};