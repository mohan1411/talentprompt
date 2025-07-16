// Validate and fix common data issues
window.validateProfileData = function(data) {
  console.log('=== Data Validation ===');
  
  // Check for suspicious experience years
  if (data.years_experience > 50) {
    console.warn(`Experience of ${data.years_experience} years seems too high. Recalculating...`);
    
    // Filter out company-level totals from experience array
    const filteredExperiences = data.experience.filter(exp => {
      // Skip if duration looks like company total
      if (exp.duration && exp.duration.match(/^[A-Za-z\s&]+\s+at\s+\d+\s*yrs?/i)) {
        console.log(`Filtering out company total: ${exp.duration}`);
        return false;
      }
      return true;
    });
    
    // Recalculate with filtered experiences
    if (window.calculateTotalExperience) {
      const recalculated = window.calculateTotalExperience(filteredExperiences);
      console.log(`Recalculated from ${data.experience.length} to ${filteredExperiences.length} experiences: ${recalculated} years`);
      data.years_experience = recalculated;
      data.experience = filteredExperiences;
    }
  }
  
  // Ensure email field exists
  if (!data.hasOwnProperty('email')) {
    data.email = '';
  }
  
  // Ensure professional summary exists
  if (!data.about || data.about.length < 10) {
    console.log('Professional summary missing or too short');
    // Try to find it again
    const aboutSection = document.querySelector('#about')?.closest('section');
    if (aboutSection) {
      const aboutText = aboutSection.querySelector('span[aria-hidden="true"]:not(.visually-hidden)')?.textContent?.trim();
      if (aboutText && aboutText.length > 20) {
        data.about = aboutText;
        console.log('Found professional summary:', aboutText.substring(0, 50) + '...');
      }
    }
  }
  
  // Log validation results
  console.log('Validation complete:', {
    name: data.name || 'MISSING',
    email: data.email || 'MISSING',
    years_experience: data.years_experience,
    experience_count: data.experience.length,
    has_about: !!data.about && data.about.length > 10
  });
  
  return data;
};