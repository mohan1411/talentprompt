// Detect and classify experience patterns
window.detectExperiencePattern = function(texts) {
  if (!texts || texts.length < 2) return { type: 'unknown', confidence: 0 };
  
  const patterns = {
    // Pattern 1: Company with total duration (e.g., "ANZ · 14 yrs 7 mos")
    companyTotal: {
      check: () => {
        // First text is company name, second has duration
        if (texts[0] && texts[1]) {
          const firstText = texts[0];
          const secondText = texts[1];
          
          // Check if first text looks like company name (starts with capital, no job keywords)
          const looksLikeCompany = /^[A-Z]/.test(firstText) && 
            !firstText.match(/Manager|Director|Engineer|Developer|Analyst|Lead|Senior|Junior|Executive|Consultant|Specialist/i);
          
          // Check if second text is just employment type + duration
          const isEmploymentPlusDuration = secondText.match(/^(Full-time|Part-time|Contract|Freelance)\\s*·?\\s*\\d+\\s*yrs?/i);
          
          // Check if we have company followed by duration without a proper job title
          const hasDirectDuration = texts.some(t => t.match(/^\\d+\\s*yrs?\\s*\\d*\\s*mos?$/i));
          
          return looksLikeCompany && (isEmploymentPlusDuration || hasDirectDuration);
        }
        return false;
      },
      confidence: 0.9
    },
    
    // Pattern 2: Individual role (has specific job title)
    individualRole: {
      check: () => {
        // First text contains job-related keywords
        const hasJobTitle = texts[0] && texts[0].match(
          /Manager|Director|Engineer|Developer|Analyst|Lead|Senior|Junior|Executive|Officer|Consultant|Specialist|Architect|Designer|Administrator|Coordinator|Assistant|Advisor|Head of|VP|Vice President|Chief|Partner|Associate|Intern/i
        );
        
        return !!hasJobTitle;
      },
      confidence: 0.85
    },
    
    // Pattern 3: Grouped header (company name only, no duration in first few texts)
    groupedHeader: {
      check: () => {
        // Company name without immediate duration
        const firstThreeTexts = texts.slice(0, 3).join(' ');
        const hasNoDuration = !firstThreeTexts.match(/\\d+\\s*yrs?\\s*\\d*\\s*mos?/i);
        const looksLikeCompany = texts[0] && /^[A-Z]/.test(texts[0]) && texts[0].length < 50;
        
        return hasNoDuration && looksLikeCompany;
      },
      confidence: 0.7
    }
  };
  
  // Check each pattern
  for (const [patternName, pattern] of Object.entries(patterns)) {
    if (pattern.check()) {
      console.log(`Detected pattern: ${patternName} (confidence: ${pattern.confidence})`);
      return { type: patternName, confidence: pattern.confidence };
    }
  }
  
  return { type: 'unknown', confidence: 0 };
};

// Enhanced experience text processor
window.processExperienceTextsEnhanced = function(texts, itemId, overrideCompany = null) {
  console.log(`\\n=== Processing Experience ${itemId} ===`);
  console.log('Texts:', texts);
  
  // Detect pattern
  const pattern = window.detectExperiencePattern(texts);
  console.log('Pattern detection:', pattern);
  
  // If high confidence it's a company total, skip it
  if (pattern.type === 'companyTotal' && pattern.confidence > 0.8) {
    console.log('SKIPPING: Detected as company total with high confidence');
    return null;
  }
  
  // Process as normal experience
  const exp = {
    title: '',
    company: overrideCompany || '',
    duration: '',
    location: '',
    description: ''
  };
  
  let textIndex = 0;
  
  // Extract title
  if (pattern.type === 'individualRole' || overrideCompany) {
    exp.title = texts[textIndex++];
  } else if (pattern.type === 'groupedHeader') {
    // This might be a company header, skip
    return null;
  } else {
    // Uncertain, try to extract
    exp.title = texts[textIndex++];
  }
  
  // Extract company if not provided
  if (!overrideCompany && textIndex < texts.length) {
    const text = texts[textIndex];
    if (text.includes('·')) {
      const parts = text.split('·').map(p => p.trim());
      exp.company = parts[0];
      // Don't increment if the second part is duration
      if (!parts[1]?.match(/\\d+\\s*yrs?/i)) {
        textIndex++;
      }
    } else if (!text.match(/\\d{4}|\\d+\\s*yrs?/i)) {
      exp.company = text;
      textIndex++;
    }
  }
  
  // Extract duration
  for (let i = textIndex; i < texts.length; i++) {
    const text = texts[i];
    if (text.match(/\\d{4}|Present|Current|\\d+\\s*yrs?\\s*\\d*\\s*mos?/i)) {
      exp.duration = text;
      
      // Check for calculated duration in next text
      if (i + 1 < texts.length && texts[i + 1].match(/^\\d+\\s*yrs?\\s*\\d*\\s*mos?$/i)) {
        exp.duration += ' · ' + texts[i + 1];
      }
      break;
    }
  }
  
  // Final validation
  if (!exp.title || exp.title === exp.company) {
    console.log('WARNING: No valid title found, might be company total');
    if (!overrideCompany) {
      return null;
    }
  }
  
  console.log('Extracted experience:', exp);
  return exp;
};