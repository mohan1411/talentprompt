// Override the experience calculator to show exactly what's happening
(function() {
  console.log('🔄 Installing experience calculator override...');
  
  // Store original function
  const originalAdvancedCalc = window.calculateTotalExperienceAdvanced;
  
  // Override with detailed logging
  window.calculateTotalExperienceAdvanced = function(experiences) {
    console.log('%c📊 EXPERIENCE CALCULATOR OVERRIDE', 'color: white; background: blue; font-size: 16px; padding: 5px;');
    console.log('Processing', experiences.length, 'experiences');
    
    // Show each experience
    const breakdown = [];
    let totalMonths = 0;
    
    experiences.forEach((exp, idx) => {
      console.log(`\n===== Experience ${idx + 1} =====`);
      console.log('Title:', exp.title);
      console.log('Company:', exp.company);
      console.log('Duration:', exp.duration);
      
      // Check if this should be skipped
      const skipReasons = [];
      
      // Check 1: Title equals company
      if (exp.title === exp.company) {
        skipReasons.push('Title equals company');
      }
      
      // Check 2: No job title
      if (!exp.title || exp.title.match(/^[A-Z][a-z]+(\s[A-Z][a-z]+)*$/)) {
        if (!exp.title?.match(/Manager|Director|Engineer|Developer|Analyst|Lead|Senior|Junior|Executive|Officer|Consultant|Specialist|Architect|Designer|Administrator|Coordinator|Assistant|Advisor|Head|VP|Vice President|Chief|Partner|Associate|Intern|Accountant|Auditor|Programmer|Scientist|Researcher|Banker/i)) {
          skipReasons.push('No specific job title');
        }
      }
      
      // Check 3: ANZ without title
      if ((exp.company?.includes('ANZ') || exp.title?.includes('ANZ')) && exp.title === 'ANZ') {
        skipReasons.push('ANZ company total');
      }
      
      // Check 4: 14 year duration (specific to ANZ case)
      if (exp.duration?.includes('14 yr')) {
        skipReasons.push('14 year duration (likely company total)');
      }
      
      if (skipReasons.length > 0) {
        console.log('⚠️  SHOULD SKIP:', skipReasons.join(', '));
        console.log('❌ SKIPPING THIS ENTRY');
        return;
      }
      
      // Parse duration
      let months = 0;
      if (exp.duration) {
        const yearsMatch = exp.duration.match(/(\d+)\s*yrs?/);
        const monthsMatch = exp.duration.match(/(\d+)\s*mos?/);
        const years = yearsMatch ? parseInt(yearsMatch[1]) : 0;
        const monthsOnly = monthsMatch ? parseInt(monthsMatch[1]) : 0;
        months = (years * 12) + monthsOnly;
        
        console.log(`Parsed: ${years} years + ${monthsOnly} months = ${months} months`);
      }
      
      if (months > 0) {
        totalMonths += months;
        breakdown.push({
          title: exp.title,
          company: exp.company,
          months: months,
          years: (months / 12).toFixed(1)
        });
        console.log('✅ COUNTED:', months, 'months');
      } else {
        console.log('❌ NO DURATION FOUND');
      }
    });
    
    console.log('\n%c📊 CALCULATION BREAKDOWN', 'color: white; background: green; font-size: 14px; padding: 3px;');
    console.table(breakdown);
    
    const totalYears = Math.round(totalMonths / 12);
    console.log(`\nTOTAL: ${totalMonths} months = ${(totalMonths/12).toFixed(1)} years (rounded to ${totalYears})`);
    
    // If still too high, show warning
    if (totalYears > 20) {
      console.warn('%c⚠️  WARNING: Total seems high. Possible issues:', 'color: orange; font-weight: bold');
      console.warn('1. Company totals not filtered');
      console.warn('2. Overlapping experiences counted separately');
      console.warn('3. Data extraction issues');
      
      // Try to identify the problem
      const longExperiences = breakdown.filter(b => b.months > 150); // > 12.5 years
      if (longExperiences.length > 0) {
        console.warn('\nSuspiciously long experiences:');
        console.table(longExperiences);
      }
    }
    
    return totalYears;
  };
  
  console.log('✅ Calculator override installed');
})();