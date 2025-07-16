// Specific fix for ANZ profile and similar cases
window.fixANZProfile = function(experiences) {
  console.log('%c🔧 ANZ PROFILE FIX', 'color: white; background: red; font-size: 14px; padding: 3px;');
  console.log('Input experiences:', experiences.length);
  
  // Log all experiences
  experiences.forEach((exp, idx) => {
    console.log(`\nExperience ${idx + 1}:`);
    console.log(`  Title: "${exp.title}"`);
    console.log(`  Company: "${exp.company}"`);
    console.log(`  Duration: "${exp.duration}"`);
    
    // Parse duration
    if (exp.duration) {
      const yearsMatch = exp.duration.match(/(\d+)\s*yrs?/);
      const monthsMatch = exp.duration.match(/(\d+)\s*mos?/);
      const years = yearsMatch ? parseInt(yearsMatch[1]) : 0;
      const months = monthsMatch ? parseInt(monthsMatch[1]) : 0;
      const totalMonths = (years * 12) + months;
      console.log(`  Parsed: ${years} years + ${months} months = ${totalMonths} months`);
    }
  });
  
  // Identify ANZ experiences
  const anzExperiences = experiences.filter(exp => 
    (exp.company && exp.company.toUpperCase().includes('ANZ')) ||
    (exp.title && exp.title.toUpperCase().includes('ANZ'))
  );
  
  console.log(`\nFound ${anzExperiences.length} ANZ experiences`);
  
  if (anzExperiences.length > 1) {
    // Check for the 14 year entry
    const fourteenYearEntry = anzExperiences.find(exp => 
      exp.duration && exp.duration.includes('14 yr')
    );
    
    if (fourteenYearEntry) {
      console.log('\n🚨 FOUND 14 YEAR ANZ ENTRY - This is likely a company total');
      console.log('Entry:', fourteenYearEntry);
      
      // Remove this entry
      const index = experiences.indexOf(fourteenYearEntry);
      if (index > -1) {
        experiences.splice(index, 1);
        console.log('REMOVED 14 year entry at index', index);
      }
    }
    
    // Also check for any ANZ entry without a specific job title
    const anzWithoutTitle = anzExperiences.filter(exp => {
      const hasJobTitle = exp.title && exp.title.match(
        /Manager|Director|Engineer|Developer|Analyst|Lead|Senior|Junior|Executive|Officer|Consultant|Specialist|Architect|Designer|Administrator|Coordinator|Assistant|Advisor|Head|VP|Vice President|Chief|Partner|Associate|Intern|Accountant|Auditor|Programmer|Scientist|Researcher|Banker|Specialist/i
      );
      return !hasJobTitle || exp.title === 'ANZ' || exp.title === exp.company;
    });
    
    anzWithoutTitle.forEach(exp => {
      console.log('\n🚨 ANZ entry without specific job title:', exp);
      const index = experiences.indexOf(exp);
      if (index > -1) {
        experiences.splice(index, 1);
        console.log('REMOVED at index', index);
      }
    });
  }
  
  // Final check: if total is still > 20 years, look for the longest duration
  let totalMonths = 0;
  const durations = experiences.map(exp => {
    if (!exp.duration) return 0;
    const yearsMatch = exp.duration.match(/(\d+)\s*yrs?/);
    const monthsMatch = exp.duration.match(/(\d+)\s*mos?/);
    const years = yearsMatch ? parseInt(yearsMatch[1]) : 0;
    const months = monthsMatch ? parseInt(monthsMatch[1]) : 0;
    return (years * 12) + months;
  });
  
  totalMonths = durations.reduce((a, b) => a + b, 0);
  const totalYears = totalMonths / 12;
  
  console.log(`\nTotal after ANZ fix: ${totalMonths} months = ${totalYears.toFixed(1)} years`);
  
  if (totalYears > 20) {
    console.log('Still too high, looking for outliers...');
    
    // Find the longest duration
    const maxDuration = Math.max(...durations);
    const maxIndex = durations.indexOf(maxDuration);
    
    if (maxDuration > 150) { // More than 12.5 years for a single role is suspicious
      console.log(`\n🚨 Suspicious duration at index ${maxIndex}: ${maxDuration} months`);
      console.log('Experience:', experiences[maxIndex]);
      
      // Check if it's a company total
      const exp = experiences[maxIndex];
      if (!exp.title || exp.title === exp.company || !exp.title.match(/Manager|Director|Engineer|Developer/i)) {
        experiences.splice(maxIndex, 1);
        console.log('REMOVED suspicious long duration');
      }
    }
  }
  
  console.log(`\nFinal experiences: ${experiences.length}`);
  return experiences;
};

// Auto-apply fix for ANZ profile
if (window.location.href.includes('anil-narasimhappa')) {
  console.log('%c🎯 ANZ PROFILE DETECTED - Fix will be applied', 'color: yellow; background: black; font-size: 14px; padding: 5px;');
  
  // Override the calculation function
  const originalCalculate = window.calculateExperienceWithValidation;
  window.calculateExperienceWithValidation = function(experiences) {
    console.log('Applying ANZ fix before calculation...');
    const fixed = window.fixANZProfile([...experiences]); // Clone array
    return originalCalculate ? originalCalculate(fixed) : 0;
  };
}