// Validate and fix common data issues
window.validateProfileData = function(data) {
  
  // Check for suspicious experience years
  if (data.years_experience > 50) {
    
    // Filter out company-level totals from experience array
    const filteredExperiences = data.experience.filter(exp => {
      // Skip if duration looks like company total
      if (exp.duration && exp.duration.match(/^[A-Za-z\s&]+\s+at\s+\d+\s*yrs?/i)) {
        return false;
      }
      return true;
    });
    
    // Recalculate with filtered experiences
    let recalculated;
    if (window.calculateTotalExperienceAdvanced) {
      recalculated = window.calculateTotalExperienceAdvanced(filteredExperiences);
    } else if (window.calculateTotalExperience) {
      recalculated = window.calculateTotalExperience(filteredExperiences);
    }
    
    if (recalculated !== undefined) {
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
    // Try to find it again
    const aboutSection = document.querySelector('#about')?.closest('section');
    if (aboutSection) {
      const aboutText = aboutSection.querySelector('span[aria-hidden="true"]:not(.visually-hidden)')?.textContent?.trim();
      if (aboutText && aboutText.length > 20) {
        data.about = aboutText;
      }
    }
  }
  
  // Additional validation checks
  if (data.years_experience > 0) {
    // Age-based validation (assuming work starts at 18)
    const maxReasonableExperience = 50; // 68 years old with 50 years experience
    if (data.years_experience > maxReasonableExperience) {
    }
    
    // Check if experience exceeds profile age hints
    if (data.education && data.education.length > 0) {
      // Try to estimate age from education dates
      const graduationYears = data.education
        .map(edu => {
          const yearMatch = edu.dates?.match(/\d{4}/);
          return yearMatch ? parseInt(yearMatch[0]) : null;
        })
        .filter(year => year !== null);
      
      if (graduationYears.length > 0) {
        const earliestGraduation = Math.min(...graduationYears);
        const currentYear = new Date().getFullYear();
        const yearsSinceGraduation = currentYear - earliestGraduation;
        
        // If experience significantly exceeds years since earliest education
        if (data.years_experience > yearsSinceGraduation + 5) {
        }
      }
    }
    
    // Check for common calculation errors
    const avgYearsPerRole = data.years_experience / data.experience.length;
    if (avgYearsPerRole > 15) {
    }
  }
  
  // Validation complete
  
  return data;
};