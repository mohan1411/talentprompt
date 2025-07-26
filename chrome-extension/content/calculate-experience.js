// Calculate total years of experience from experience array
window.calculateTotalExperience = function(experiences) {
  if (!experiences || !Array.isArray(experiences)) return 0;
  
  
  let totalMonths = 0;
  let processedCount = 0;
  
  experiences.forEach((exp, index) => {
      title: exp.title,
      company: exp.company,
      duration: exp.duration
    });
    
    if (!exp.duration) {
      return;
    }
    
    const duration = exp.duration;
    let expMonths = 0;
    
    // Clean the duration string first
    const cleanDuration = duration.replace(/[·•]/g, ' ').trim();
    
    // Skip if this looks like a company total duration (e.g., "Company Name at 14 yrs 7 mos")
    if (cleanDuration.match(/^[A-Za-z\s&]+\s+at\s+\d+\s*yrs?/i)) {
      return;
    }
    
    // Method 1: Try to extract from LinkedIn's calculated duration (e.g., "11 yrs 7 mos")
    const calcDurationMatch = cleanDuration.match(/(\d+)\s*yrs?\s*(\d+)?\s*mos?/i);
    if (calcDurationMatch) {
      const years = parseInt(calcDurationMatch[1]) || 0;
      const months = parseInt(calcDurationMatch[2]) || 0;
      expMonths = (years * 12) + months;
    } else {
      // Method 2: Extract years and months separately
      const yearsMatch = cleanDuration.match(/(\d+)\s*(?:yrs?|years?)/i);
      const years = yearsMatch ? parseInt(yearsMatch[1]) : 0;
      
      const monthsMatch = cleanDuration.match(/(\d+)\s*(?:mos?|months?)/i);
      const months = monthsMatch ? parseInt(monthsMatch[1]) : 0;
      
      expMonths = (years * 12) + months;
    }
    
    // Method 3: If still 0, try to calculate from date range
    if (expMonths === 0 && duration.includes('-')) {
      
      // Extract dates like "Jan 2020 - Present" or "2019 - 2021"
      const dateRangeMatch = duration.match(/(\w+\s*\d{4}|\d{4})\s*[-–]\s*(\w+\s*\d{4}|\d{4}|Present|Current)/i);
      if (dateRangeMatch) {
        const startDate = dateRangeMatch[1];
        const endDate = dateRangeMatch[2];
        
        // Simple year extraction for now
        const startYearMatch = startDate.match(/\d{4}/);
        const endYearMatch = endDate.match(/\d{4}/);
        
        if (startYearMatch) {
          const startYear = parseInt(startYearMatch[0]);
          const endYear = endDate.toLowerCase().includes('present') || endDate.toLowerCase().includes('current')
            ? new Date().getFullYear()
            : (endYearMatch ? parseInt(endYearMatch[0]) : startYear);
          
          const yearsDiff = endYear - startYear;
          expMonths = yearsDiff * 12;
        }
      }
    }
    
    if (expMonths > 0) {
      totalMonths += expMonths;
      processedCount++;
    } else {
    }
  });
  
  // Calculate years with better rounding (round up if >= 0.5 years)
  const exactYears = totalMonths / 12;
  const totalYears = Math.round(exactYears);
  
  // Sanity check - if calculation seems way off, warn
  if (totalYears > 50) {
  }
  
  
  // Log any experiences that couldn't be parsed
  const unparsedCount = experiences.length - processedCount;
  if (unparsedCount > 0) {
    experiences.forEach((exp, idx) => {
      if (!exp.duration || exp.duration.trim() === '') {
      }
    });
  }
  
  return totalYears;
};