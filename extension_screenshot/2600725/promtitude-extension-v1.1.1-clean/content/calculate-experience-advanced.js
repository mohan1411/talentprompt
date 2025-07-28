// Advanced experience calculator with overlap detection and precise date parsing
window.calculateTotalExperienceAdvanced = function(experiences) {
  if (!experiences || !Array.isArray(experiences)) return 0;
  
  
  // Month mapping for parsing
  const monthMap = {
    'jan': 0, 'january': 0,
    'feb': 1, 'february': 1,
    'mar': 2, 'march': 2,
    'apr': 3, 'april': 3,
    'may': 4,
    'jun': 5, 'june': 5,
    'jul': 6, 'july': 6,
    'aug': 7, 'august': 7,
    'sep': 8, 'september': 8, 'sept': 8,
    'oct': 9, 'october': 9,
    'nov': 10, 'november': 10,
    'dec': 11, 'december': 11
  };
  
  // Parse a date string into a Date object
  const parseDate = (dateStr) => {
    if (!dateStr) return null;
    
    const normalized = dateStr.trim().toLowerCase();
    
    // Handle "Present" or "Current"
    if (normalized.includes('present') || normalized.includes('current')) {
      return new Date();
    }
    
    // Try to parse "Jan 2020" format
    const monthYearMatch = normalized.match(/(\w+)\s+(\d{4})/);
    if (monthYearMatch) {
      const monthStr = monthYearMatch[1];
      const year = parseInt(monthYearMatch[2]);
      const month = monthMap[monthStr];
      
      if (month !== undefined) {
        return new Date(year, month, 1);
      }
    }
    
    // Try to parse year-only format
    const yearOnlyMatch = normalized.match(/^\d{4}$/);
    if (yearOnlyMatch) {
      // Assume January for year-only dates
      return new Date(parseInt(yearOnlyMatch[0]), 0, 1);
    }
    
    return null;
  };
  
  // Calculate months between two dates
  const monthsBetween = (start, end) => {
    if (!start || !end) return 0;
    
    const months = (end.getFullYear() - start.getFullYear()) * 12 + 
                  (end.getMonth() - start.getMonth());
    
    // Add 1 month to include the starting month
    return Math.max(0, months + 1);
  };
  
  // Store all time periods with their details
  const timePeriods = [];
  let skippedCount = 0;
  
  experiences.forEach((exp, index) => {
    // Process experience entry
    
    if (!exp.duration) {
      skippedCount++;
      return;
    }
    
    const duration = exp.duration;
    
    // Skip company totals - enhanced detection
    if (duration.match(/^[A-Za-z\s&.,]+\s+(at|@|·)\s+\d+\s*yrs?/i) ||
        exp.company?.match(/\s+(at|@|·)\s+\d+\s*yrs?/i) ||
        exp.title?.match(/^[A-Z][A-Za-z\s&.,]+\s+(at|@|·)\s+\d+\s*yrs?/i)) {
      skippedCount++;
      return;
    }
    
    let startDate = null;
    let endDate = null;
    let calculatedMonths = null;
    
    // Method 1: Try to extract LinkedIn's pre-calculated duration
    const calcDurationMatch = duration.match(/(\d+)\s*yrs?\s*(\d+)?\s*mos?/i);
    if (calcDurationMatch) {
      const years = parseInt(calcDurationMatch[1]) || 0;
      const months = parseInt(calcDurationMatch[2]) || 0;
      calculatedMonths = (years * 12) + months;
    }
    
    // Method 2: Parse date range
    const dateRangeMatch = duration.match(/(\w+\s*\d{4}|\d{4})\s*[-–]\s*(\w+\s*\d{4}|\d{4}|Present|Current)/i);
    if (dateRangeMatch) {
      startDate = parseDate(dateRangeMatch[1]);
      endDate = parseDate(dateRangeMatch[2]);
      
      if (startDate && endDate) {
        const rangeMonths = monthsBetween(startDate, endDate);
        
        // If we have both calculated and parsed, use the more specific one
        if (calculatedMonths && Math.abs(calculatedMonths - rangeMonths) > 6) {
          // Trust LinkedIn's calculation if available
        } else if (!calculatedMonths) {
          calculatedMonths = rangeMonths;
        }
      }
    }
    
    // Method 3: Handle special cases
    if (!calculatedMonths && duration.toLowerCase().includes('less than')) {
      calculatedMonths = 6; // Assume 6 months for "less than a year"
    }
    
    // Additional check: if title equals company name and has duration, likely a total
    if (exp.title === exp.company && calculatedMonths > 0) {
      skippedCount++;
      return;
    }
    
    if (calculatedMonths && calculatedMonths > 0) {
      timePeriods.push({
        index: index,
        title: exp.title,
        company: exp.company,
        startDate: startDate,
        endDate: endDate,
        months: calculatedMonths,
        hasDateRange: !!(startDate && endDate)
      });
    } else {
      skippedCount++;
    }
  });
  
  
  // Sort by whether we have date ranges (prioritize those with dates for overlap detection)
  timePeriods.sort((a, b) => {
    if (a.hasDateRange && !b.hasDateRange) return -1;
    if (!a.hasDateRange && b.hasDateRange) return 1;
    return 0;
  });
  
  // Detect overlaps if we have date ranges
  const periodsWithDates = timePeriods.filter(p => p.hasDateRange);
  const periodsWithoutDates = timePeriods.filter(p => !p.hasDateRange);
  
  let totalMonths = 0;
  
  if (periodsWithDates.length > 0) {
    
    // Create a timeline of all months worked
    const timeline = new Map();
    
    periodsWithDates.forEach(period => {
      const start = new Date(period.startDate);
      const end = new Date(period.endDate);
      
      // Mark each month in the timeline
      let current = new Date(start);
      while (current <= end) {
        const key = `${current.getFullYear()}-${current.getMonth()}`;
        if (!timeline.has(key)) {
          timeline.set(key, []);
        }
        timeline.get(key).push({
          title: period.title,
          company: period.company
        });
        
        // Move to next month
        current.setMonth(current.getMonth() + 1);
      }
    });
    
    // Count unique months
    const uniqueMonths = timeline.size;
    
    // Log any overlapping periods
    let overlapCount = 0;
    timeline.forEach((jobs, monthKey) => {
      if (jobs.length > 1) {
        overlapCount++;
        if (overlapCount <= 5) { // Only log first 5 overlaps
        }
      }
    });
    
    if (overlapCount > 0) {
    }
    
    totalMonths = uniqueMonths;
    
    // Add experiences without dates (but reduce if they seem to overlap)
    if (periodsWithoutDates.length > 0) {
      const monthsWithoutDates = periodsWithoutDates.reduce((sum, p) => sum + p.months, 0);
      
      // Heuristic: if we have many dated experiences, undated ones likely overlap
      if (periodsWithDates.length > 3) {
        const overlapFactor = 0.5; // Assume 50% overlap
        const adjustedMonths = Math.round(monthsWithoutDates * overlapFactor);
        totalMonths += adjustedMonths;
      } else {
        totalMonths += monthsWithoutDates;
      }
    }
  } else {
    // No date ranges available, sum all months
    totalMonths = timePeriods.reduce((sum, period) => sum + period.months, 0);
  }
  
  // Calculate years with proper rounding
  const exactYears = totalMonths / 12;
  const totalYears = Math.round(exactYears);
  
  
  // Sanity checks
  if (totalYears > 50) {
  }
  
  if (totalYears === 0 && experiences.length > 0) {
  }
  
  return totalYears;
};