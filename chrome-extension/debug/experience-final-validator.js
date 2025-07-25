// Final validation to ensure no company totals slip through
window.validateAndFixExperiences = function(experiences) {
  console.log('=== FINAL EXPERIENCE VALIDATION ===');
  console.log(`Input: ${experiences.length} experiences`);
  
  const validated = [];
  const removed = [];
  
  // First pass: identify all companies
  const companies = new Set();
  experiences.forEach(exp => {
    if (exp.company) {
      // Extract base company name (without duration info)
      const baseCompany = exp.company.split(/\s+(at|·)\s+\d+/)[0].trim();
      companies.add(baseCompany);
    }
  });
  
  console.log('Identified companies:', Array.from(companies));
  
  // Second pass: validate each experience
  experiences.forEach((exp, idx) => {
    let shouldRemove = false;
    const reasons = [];
    
    // Check 1: Title equals company
    if (exp.title === exp.company) {
      shouldRemove = true;
      reasons.push('Title equals company');
    }
    
    // Check 2: No specific job title
    const hasJobTitle = exp.title && exp.title.match(
      /Manager|Director|Engineer|Developer|Analyst|Lead|Senior|Junior|Executive|Officer|Consultant|Specialist|Architect|Designer|Administrator|Coordinator|Assistant|Advisor|Head|VP|Vice President|Chief|Partner|Associate|Intern|Accountant|Auditor|Programmer|Scientist|Researcher|Strategist|Planner|Expert|Professional/i
    );
    
    if (!hasJobTitle && exp.duration) {
      // Check if other experiences have this as their company
      const isCompanyForOthers = experiences.some((other, otherIdx) => {
        if (idx === otherIdx) return false;
        const otherCompanyBase = other.company?.split(/\s+(at|·)\s+\d+/)[0].trim();
        const thisBase = exp.title?.split(/\s+(at|·)\s+\d+/)[0].trim();
        return otherCompanyBase === thisBase;
      });
      
      if (isCompanyForOthers) {
        shouldRemove = true;
        reasons.push('No job title and matches company of other experiences');
      }
    }
    
    // Check 3: Duration in company field
    if (exp.company && exp.company.match(/\s+(at|·)\s+\d+\s*yrs?/i)) {
      shouldRemove = true;
      reasons.push('Company field contains duration');
    }
    
    // Check 4: Suspiciously long duration for a single role
    if (exp.duration) {
      const yearsMatch = exp.duration.match(/(\d+)\s*yrs?/);
      if (yearsMatch) {
        const years = parseInt(yearsMatch[1]);
        if (years > 20 && !hasJobTitle) {
          shouldRemove = true;
          reasons.push(`Duration of ${years} years without specific job title`);
        }
      }
    }
    
    // Check 5: Pattern matching for known company totals
    const companyTotalPatterns = [
      /^ANZ\s*$/i,
      /^ANZ\s*·\s*\d+/i,
      /^[A-Z][A-Za-z\s&]+\s*·\s*Full-time\s*·\s*\d+/i
    ];
    
    const matchesCompanyTotal = companyTotalPatterns.some(pattern => 
      pattern.test(exp.title) || pattern.test(exp.company)
    );
    
    if (matchesCompanyTotal) {
      shouldRemove = true;
      reasons.push('Matches company total pattern');
    }
    
    if (shouldRemove) {
      removed.push({
        experience: exp,
        reasons: reasons
      });
      console.log(`REMOVING Experience ${idx + 1}:`, reasons.join(', '));
      console.log(`  Title: "${exp.title}"`);
      console.log(`  Company: "${exp.company}"`);
      console.log(`  Duration: "${exp.duration}"`);
    } else {
      validated.push(exp);
    }
  });
  
  console.log(`\nValidation complete:`);
  console.log(`  Kept: ${validated.length} experiences`);
  console.log(`  Removed: ${removed.length} potential company totals`);
  
  // Final sanity check
  if (validated.length === 0 && experiences.length > 0) {
    console.error('WARNING: All experiences were removed! This might be too aggressive.');
    // Return at least some experiences
    return experiences.slice(0, Math.min(3, experiences.length));
  }
  
  return validated;
};

// Calculate experience with final validation
window.calculateExperienceWithValidation = function(experiences) {
  console.log('\n=== CALCULATING WITH VALIDATION ===');
  
  // Step 1: Deduplicate experiences
  let processed = experiences;
  if (window.deduplicateExperiences) {
    processed = window.deduplicateExperiences(processed);
  }
  
  // Step 2: Validate experiences
  const validated = window.validateAndFixExperiences(processed);
  
  // Step 3: Calculate using validated experiences
  let years = 0;
  if (window.calculateTotalExperienceAdvanced) {
    years = window.calculateTotalExperienceAdvanced(validated);
  } else if (window.calculateTotalExperience) {
    years = window.calculateTotalExperience(validated);
  }
  
  console.log(`Final calculation: ${years} years from ${validated.length} validated experiences`);
  
  // Step 4: Final reasonability check
  if (years > 40) {
    console.warn(`WARNING: ${years} years seems unusually high. Capping at 40.`);
    years = 40;
  }
  
  return years;
};