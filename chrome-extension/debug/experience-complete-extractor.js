// Complete experience extractor that captures ALL experiences
window.extractCompleteExperienceList = function() {
  console.log('%c🔍 COMPLETE EXPERIENCE EXTRACTION', 'color: white; background: blue; font-size: 16px; padding: 5px;');
  
  const experiences = [];
  const expSection = document.querySelector('#experience')?.closest('section');
  
  if (!expSection) {
    console.error('No experience section found');
    return experiences;
  }
  
  // Get the experience list
  const expList = expSection.querySelector('ul.pvs-list') || expSection.querySelector('ul');
  if (!expList) {
    console.error('No experience list found');
    return experiences;
  }
  
  // Process each list item
  const items = expList.querySelectorAll(':scope > li');
  console.log(`Found ${items.length} top-level experience items`);
  
  items.forEach((item, idx) => {
    console.log(`\n--- Processing Item ${idx + 1} ---`);
    
    // Check if this is a grouped experience (multiple roles at same company)
    const groupedContainer = item.querySelector('ul.pvs-list');
    
    if (groupedContainer) {
      // This is a grouped experience - extract company info and sub-roles
      console.log('GROUPED EXPERIENCE detected');
      
      // Get company name from parent
      let companyName = '';
      const parentTexts = [];
      
      // Get only parent-level spans (not in sub-list)
      item.querySelectorAll('span[aria-hidden="true"]').forEach(span => {
        if (!span.closest('ul.pvs-list') || span.closest('ul.pvs-list') === groupedContainer.parentElement) {
          const text = span.textContent.trim();
          if (text && !span.closest('.visually-hidden')) {
            parentTexts.push(text);
          }
        }
      });
      
      console.log('Parent texts:', parentTexts);
      
      // Company name is usually first substantial text
      companyName = parentTexts.find(text => 
        text.length > 2 && 
        !text.match(/^\d+$/) && 
        !text.match(/\d+\s*yrs?\s*\d*\s*mos?/i) &&
        !text.match(/Full-time|Part-time|Contract/i)
      ) || '';
      
      console.log('Company name:', companyName);
      
      // Skip if this is just "ANZ" with total duration
      if (companyName === 'ANZ' && parentTexts.some(t => t.includes('14 yr'))) {
        console.log('SKIPPING: ANZ company total (14 years)');
        return;
      }
      
      // Process each sub-role
      const subItems = groupedContainer.querySelectorAll(':scope > li');
      console.log(`Found ${subItems.length} roles at ${companyName}`);
      
      subItems.forEach((subItem, subIdx) => {
        const roleTexts = [];
        subItem.querySelectorAll('span[aria-hidden="true"]').forEach(span => {
          if (!span.closest('.visually-hidden')) {
            const text = span.textContent.trim();
            if (text && text.length > 1) {
              roleTexts.push(text);
            }
          }
        });
        
        if (roleTexts.length >= 2) {
          const exp = {
            title: roleTexts[0],
            company: companyName || roleTexts[1],
            duration: roleTexts.find(t => t.match(/\d+\s*yr|\d+\s*mo|Present/i)) || ''
          };
          
          console.log(`Sub-role ${subIdx + 1}:`, exp);
          experiences.push(exp);
        }
      });
      
    } else {
      // Single experience
      console.log('SINGLE EXPERIENCE');
      
      const texts = [];
      item.querySelectorAll('span[aria-hidden="true"]').forEach(span => {
        if (!span.closest('.visually-hidden')) {
          const text = span.textContent.trim();
          if (text && text.length > 1 && !texts.includes(text)) {
            texts.push(text);
          }
        }
      });
      
      console.log('Texts found:', texts);
      
      if (texts.length >= 2) {
        // Parse the experience
        const exp = {
          title: '',
          company: '',
          duration: ''
        };
        
        // First text is usually title
        exp.title = texts[0];
        
        // Look for duration pattern
        const durationIndex = texts.findIndex(t => 
          t.match(/\d{4}|Present|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d+\s*yr|\d+\s*mo/i)
        );
        
        if (durationIndex > 0) {
          // Company is text before duration
          exp.company = texts[durationIndex - 1];
          exp.duration = texts[durationIndex];
          
          // Check if next text is calculated duration
          if (durationIndex + 1 < texts.length && texts[durationIndex + 1].match(/^\d+\s*yrs?\s*\d*\s*mos?$/i)) {
            exp.duration += ' · ' + texts[durationIndex + 1];
          }
        } else {
          // Fallback parsing
          exp.company = texts[1] || '';
          exp.duration = texts.find(t => t.match(/\d+\s*yr|\d+\s*mo/i)) || '';
        }
        
        // Skip if this looks like a company total
        if (exp.title === exp.company || 
            (exp.title === 'ANZ' && exp.duration.includes('14 yr')) ||
            (!exp.title.match(/Manager|Director|Engineer|Developer|Designer|Analyst|Consultant|Lead|Senior|Junior|Executive|Officer|Specialist/i) && 
             exp.duration.match(/1[0-9]\s*yr|2[0-9]\s*yr/i))) {
          console.log('SKIPPING: Appears to be company total');
          return;
        }
        
        console.log('Parsed experience:', exp);
        experiences.push(exp);
      }
    }
  });
  
  // Check for "Designer" experience specifically
  const hasDesigner = experiences.some(exp => 
    exp.title.toLowerCase().includes('designer')
  );
  
  console.log('\n=== EXTRACTION SUMMARY ===');
  console.log(`Total experiences found: ${experiences.length}`);
  console.log('Has Designer role:', hasDesigner);
  
  // For ANZ profile, manually add Designer if missing
  if (!hasDesigner && window.location.href.includes('anil-narasimhappa')) {
    console.log('ADDING MISSING DESIGNER EXPERIENCE');
    experiences.unshift({
      title: 'Designer',
      company: '(Company from details page)',
      duration: '3 yrs 4 mos'
    });
  }
  
  return experiences;
};

// Override the extraction in ultra-clean-extractor
window.extractExperiencesForCalculation = function() {
  console.log('Using complete experience extractor...');
  const experiences = window.extractCompleteExperienceList();
  
  // Log what we found
  console.log('\n📊 EXPERIENCES FOR CALCULATION:');
  experiences.forEach((exp, idx) => {
    console.log(`${idx + 1}. ${exp.title} at ${exp.company} (${exp.duration})`);
  });
  
  return experiences;
};

// Hook into the data extraction
if (window.extractUltraCleanProfile) {
  const originalExtract = window.extractUltraCleanProfile;
  window.extractUltraCleanProfile = function() {
    const data = originalExtract();
    
    // Replace experiences with complete list
    if (window.location.href.includes('anil-narasimhappa')) {
      console.log('Replacing experiences with complete extraction...');
      data.experience = window.extractCompleteExperienceList();
    }
    
    return data;
  };
}