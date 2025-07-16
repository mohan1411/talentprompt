// Ultra clean extractor - filters at source, no unfiltered content ever
window.extractUltraCleanProfile = function() {
  console.log('=== Ultra Clean Extraction Starting ===');
  
  // Validate we're on the main profile page, not a details page
  const pathname = window.location.pathname;
  if (pathname.includes('/details/')) {
    console.log('WARNING: Cannot extract from details page. Please navigate to main profile page.');
    return {
      error: 'wrong_page',
      message: 'Please navigate to the main LinkedIn profile page to import'
    };
  }
  
  try {
  
  const data = {
    linkedin_url: window.location.href.split('?')[0],
    name: '',
    headline: '',
    location: '',
    about: '',
    experience: [],
    education: [],
    skills: [],
    years_experience: 0,
    email: '',
    phone: '',
    full_text: ''
  };
  
  // Helper to check if text is irrelevant
  const isIrrelevant = (text) => {
    if (!text) return true;
    const patterns = [
      /\d+\s*followers?/i,
      /\d+\s*connections?/i,
      /endorsed by/i,
      /\d+\s*endorsements?/i,
      /people also viewed/i,
      /people you may know/i,
      /· 3rd|· 2nd|· 1st/i,
      /newsletter|subscribe/i,
      /Prime Minister|Narendra Modi|Jeff Weiner|Bill Gates/i,
      /The world of startups/i,
      /^\d+$/, // Just numbers
      /^at\s*\d+/i, // "at 3 endorsements"
      /^Endorsed by \d+ colleagues/i,
      /^at Endorsed by/i,
      /^Google$/i, // Just company names without context
      /^Amazon$/i,
      /^Microsoft$/i,
      /^Apple$/i,
      /^Facebook$/i
    ];
    return patterns.some(p => p.test(text));
  };
  
  // Extract basic info
  const nameEl = document.querySelector('h1.text-heading-xlarge') || document.querySelector('h1');
  if (nameEl && !isIrrelevant(nameEl.textContent)) {
    data.name = nameEl.textContent.trim();
  }
  
  const headlineEl = document.querySelector('.text-body-medium.break-words');
  if (headlineEl && !isIrrelevant(headlineEl.textContent)) {
    data.headline = headlineEl.textContent.trim();
  }
  
  const locationEl = document.querySelector('.text-body-small.inline.t-black--light.break-words');
  if (locationEl && !isIrrelevant(locationEl.textContent)) {
    data.location = locationEl.textContent.trim();
  }
  
  // Extract about - clean it
  const aboutSection = document.querySelector('#about')?.closest('section');
  if (aboutSection) {
    console.log('Found about section, extracting...');
    
    // Try multiple selectors for about text
    const aboutSelectors = [
      '.inline-show-more-text span[aria-hidden="true"]',
      '.display-flex.full-width span[aria-hidden="true"]',
      '.pv-shared-text-with-see-more span[aria-hidden="true"]',
      'div[class*="line-clamp"] span[aria-hidden="true"]',
      'span[aria-hidden="true"]'
    ];
    
    let aboutText = '';
    for (const selector of aboutSelectors) {
      const aboutEl = aboutSection.querySelector(selector);
      if (aboutEl && aboutEl.textContent && aboutEl.textContent.trim().length > 20) {
        aboutText = aboutEl.textContent.trim();
        console.log(`Found about text with selector: ${selector}`);
        break;
      }
    }
    
    // If still no about text, try getting all visible text
    if (!aboutText) {
      const allSpans = aboutSection.querySelectorAll('span[aria-hidden="true"]');
      allSpans.forEach(span => {
        if (!span.closest('.visually-hidden') && span.textContent.trim().length > 50) {
          aboutText = span.textContent.trim();
        }
      });
    }
    
    if (aboutText && !isIrrelevant(aboutText)) {
      data.about = aboutText;
      console.log(`About section length: ${aboutText.length} chars`);
    } else {
      console.log('No valid about text found');
    }
  } else {
    console.log('No about section found on profile');
  }
  
  // Helper function to process experience texts - moved outside to fix scoping
  const processExperienceTexts = (texts, itemId, overrideCompany, isGroupedRole = false) => {
    if (!texts || texts.length < 2) {
      console.log(`Experience ${itemId}: Insufficient texts`);
      return;
    }
    
    console.log(`\n=== Experience Item ${itemId} ${isGroupedRole ? '(Grouped Role)' : ''} ===`);
    console.log('All texts found:', texts);
    console.log('Text count:', texts.length);
    
    const exp = {
      title: '',
      company: overrideCompany || '',
      duration: '',
      location: '',
      description: ''
    };
    
    // If we have an override company (from grouped experiences), title is first text
    if (overrideCompany) {
      exp.title = texts[0];
    } else {
      // Check if first text looks like a company name with total duration
      if (texts[0] && texts[0].match(/\s+at\s+\d+\s*yrs?/i)) {
        console.log('  -> Detected company with total duration format');
        // This is a company-level total, skip this entire item
        console.log('  -> SKIPPING: This appears to be a company total duration, not an individual role');
        return;
      } else {
        // Standard format: title first, then company
        exp.title = texts[0];
        
        if (texts[1]) {
          if (texts[1].includes('·')) {
            const parts = texts[1].split('·').map(p => p.trim());
            exp.company = parts[0];
          } else {
            exp.company = texts[1];
          }
        }
      }
    }
    
    // Find duration - look for date patterns
    console.log('Looking for duration in all texts...');
    for (let i = 1; i < texts.length; i++) {
      const text = texts[i];
      console.log(`  Checking text[${i}]: "${text}"`);
      
      if (text.match(/\d{4}|Present|Current|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d+\s*yr|\d+\s*mo/i)) {
        console.log(`  -> Matched date pattern!`);
        exp.duration = text;
        
        if (i + 1 < texts.length) {
          const nextText = texts[i + 1];
          console.log(`  -> Next text: "${nextText}"`);
          
          if (nextText.match(/\d+\s*yrs?\s*\d*\s*mos?/i)) {
            exp.duration = text + ' · ' + nextText;
            console.log(`  -> Combined with calculated duration: ${exp.duration}`);
            i++;
          } else if (nextText.includes(',')) {
            exp.location = nextText;
            console.log(`  -> Next text is location: ${nextText}`);
          }
        }
        console.log(`  -> Final duration: "${exp.duration}"`);
        break;
      }
    }
    
    if (!exp.duration) {
      console.log('  -> No duration found for this experience!');
    }
    
    // Verify this is a real experience
    if (!isIrrelevant(exp.title) && !isIrrelevant(exp.company)) {
      data.experience.push(exp);
      console.log(`Added experience ${data.experience.length}:`, {
        title: exp.title,
        company: exp.company,
        duration: exp.duration || 'NO DURATION FOUND'
      });
    } else {
      console.log(`Skipped item ${itemId} - title: "${exp.title}" company: "${exp.company}"`);
    }
  };
  
  // Extract experience - ultra clean with better selectors
  const expSection = document.querySelector('#experience')?.closest('section') || 
                    document.querySelector('#experience')?.parentElement?.parentElement;
  if (expSection) {
    console.log('Processing experience section...');
    
    // Try multiple ways to find the list
    const expList = expSection.querySelector('ul') || 
                   expSection.querySelector('.pvs-list') ||
                   expSection.querySelector('div > div > ul');
                   
    if (expList) {
      const items = expList.querySelectorAll('li') || expList.children;
      console.log(`Found ${items.length} potential experience items`);
      
      Array.from(items).forEach((item, idx) => {
        // Skip if not a list item
        if (item.tagName !== 'LI' && !item.classList.contains('pvs-entity')) {
          return;
        }
        
        // Check if this is a grouped experience (multiple roles at same company)
        const groupedContainer = item.querySelector('ul.pvs-list');
        if (groupedContainer) {
          console.log(`\nItem ${idx + 1} is a GROUPED EXPERIENCE (multiple roles at same company)`);
          
          // Get company name - it's usually the first span in the parent item
          const companySpans = item.querySelectorAll('span[aria-hidden="true"]');
          let companyName = '';
          let foundCompanyTotal = false;
          
          for (const span of companySpans) {
            const text = span.textContent.trim();
            console.log(`  Checking span: "${text}"`);
            
            // Skip if this is the total duration
            if (text.match(/\d+\s*yrs?\s*\d*\s*mos?/i)) {
              console.log(`  -> This is total duration, skipping: ${text}`);
              foundCompanyTotal = true;
              continue;
            }
            
            // The company name is usually before the total duration
            if (!foundCompanyTotal && text && !text.match(/\d{4}/) && text.length > 2) {
              companyName = text;
              console.log(`  -> Found company name: ${companyName}`);
              break;
            }
          }
          
          console.log(`Company group final name: ${companyName}`);
          
          // Process each role within the company
          const roleItems = groupedContainer.querySelectorAll('li');
          console.log(`Found ${roleItems.length} roles in this company`);
          
          roleItems.forEach((roleItem, roleIdx) => {
            const roleTexts = [];
            roleItem.querySelectorAll('span[aria-hidden="true"]').forEach(span => {
              if (!span.closest('.visually-hidden')) {
                const text = span.textContent.trim();
                if (text && !isIrrelevant(text) && text.length > 2 && !roleTexts.includes(text)) {
                  roleTexts.push(text);
                }
              }
            });
            
            if (roleTexts.length >= 2) {
              console.log(`  Role ${roleIdx + 1} texts:`, roleTexts);
              // Process as a separate experience
              processExperienceTexts(roleTexts, idx + '-' + roleIdx, companyName, true);
            }
          });
          return; // Skip regular processing for this item
        }
        
        // Regular single experience processing
        const texts = [];
        // Get all visible text - LinkedIn uses aria-hidden="true" for visible text
        const spans = item.querySelectorAll('span[aria-hidden="true"]');
        spans.forEach(span => {
          // Skip if parent is visually hidden
          if (span.closest('.visually-hidden')) return;
          
          const text = span.textContent.trim();
          if (text && !isIrrelevant(text) && text.length > 2 && !texts.includes(text)) {
            texts.push(text);
          }
        });
        
        if (texts.length >= 2) {
          processExperienceTexts(texts, idx, null);
        } else {
          console.log(`Item ${idx + 1} has insufficient text (${texts.length} items)`);
        }
      });
    } else {
      console.log('No experience list found, trying alternative structure...');
      // Try to find experience items without a list
      const expItems = expSection.querySelectorAll('[data-view-name="profile-component-entity"]') ||
                      expSection.querySelectorAll('.pvs-entity');
      console.log(`Found ${expItems.length} experience items with alternative method`);
    }
  } else {
    console.log('No experience section found!');
  }
  
  // Extract education - ultra clean
  const eduSection = document.querySelector('#education')?.closest('section');
  if (eduSection) {
    const eduList = eduSection.querySelector('ul');
    if (eduList) {
      const items = eduList.querySelectorAll('li');
      items.forEach(item => {
        const texts = [];
        item.querySelectorAll('span[aria-hidden="true"]').forEach(span => {
          const text = span.textContent.trim();
          if (text && !isIrrelevant(text)) {
            texts.push(text);
          }
        });
        
        if (texts.length >= 1 && !isIrrelevant(texts[0])) {
          const edu = {
            school: texts[0],
            degree: texts[1] || '',
            field: '',
            dates: ''
          };
          
          // Parse degree
          if (edu.degree && edu.degree.includes(',')) {
            const parts = edu.degree.split(',');
            edu.degree = parts[0].trim();
            edu.field = parts[1].trim();
          }
          
          data.education.push(edu);
        }
      });
    }
  }
  
  // Extract skills - ultra clean
  const skillsSection = document.querySelector('#skills')?.closest('section');
  if (skillsSection) {
    skillsSection.querySelectorAll('.mr1.t-bold span[aria-hidden="true"]').forEach(skill => {
      const skillText = skill.textContent.trim();
      if (skillText && !isIrrelevant(skillText) && !skillText.match(/^\d+$/)) {
        data.skills.push(skillText);
      }
    });
  }
  
  // Calculate years of experience
  console.log('\n=== Experience Calculation ===');
  console.log(`Total experiences found: ${data.experience.length}`);
  data.experience.forEach((exp, idx) => {
    console.log(`Experience ${idx + 1}: ${exp.title} at ${exp.company}`);
    console.log(`  Duration: ${exp.duration || 'NO DURATION'}`);
  });
  
  // Try advanced calculator first, fall back to basic if not available
  if (window.calculateTotalExperienceAdvanced) {
    data.years_experience = window.calculateTotalExperienceAdvanced(data.experience);
    console.log(`Calculated total (advanced): ${data.years_experience} years`);
  } else if (window.calculateTotalExperience) {
    data.years_experience = window.calculateTotalExperience(data.experience);
    console.log(`Calculated total (basic): ${data.years_experience} years`);
  } else {
    console.log('WARNING: No experience calculation function available');
  }
  
  // Build ultra clean full text
  const parts = [];
  if (data.name) parts.push(data.name);
  if (data.headline) parts.push(data.headline);
  if (data.location) parts.push(data.location);
  if (data.years_experience > 0) parts.push(`${data.years_experience} years of experience`);
  
  if (data.about) {
    parts.push('\nABOUT\n' + data.about);
  }
  
  if (data.experience.length > 0) {
    parts.push('\nEXPERIENCE');
    data.experience.forEach(exp => {
      parts.push('\n' + exp.title);
      if (exp.company) parts.push(exp.company);
      if (exp.duration) parts.push(exp.duration);
      if (exp.location) parts.push(exp.location);
    });
  }
  
  if (data.education.length > 0) {
    parts.push('\nEDUCATION');
    data.education.forEach(edu => {
      parts.push('\n' + edu.school);
      if (edu.degree && edu.field) {
        parts.push(`${edu.degree}, ${edu.field}`);
      } else if (edu.degree) {
        parts.push(edu.degree);
      }
    });
  }
  
  if (data.skills.length > 0) {
    parts.push('\nSKILLS\n' + data.skills.join(', '));
  }
  
  data.full_text = parts.join('\n');
  
  console.log('=== Ultra Clean Extraction Complete ===');
  console.log('Experience items:', data.experience.length);
  console.log('Clean text length:', data.full_text.length);
  console.log('No irrelevant content included');
  
  return data;
  
  } catch (error) {
    console.error('Error in ultra clean extraction:', error);
    console.error('Stack:', error.stack);
    
    // Return minimal data to prevent complete failure
    return {
      linkedin_url: window.location.href.split('?')[0],
      name: '',
      headline: '',
      location: '',
      about: '',
      experience: [],
      education: [],
      skills: [],
      years_experience: 0,
      email: '',
      phone: '',
      full_text: '',
      error: error.message
    };
  }
};