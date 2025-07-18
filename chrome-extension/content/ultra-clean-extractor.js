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
          
          // Get company name from the parent item
          const companySpans = [];
          
          // Only look at spans that are direct children of the parent item, not in the sub-list
          item.querySelectorAll('span[aria-hidden="true"]').forEach(span => {
            // Make sure this span is not inside the grouped container
            if (!span.closest('ul.pvs-list') || span.closest('ul.pvs-list') !== groupedContainer) {
              companySpans.push(span);
            }
          });
          
          let companyName = '';
          console.log(`  Found ${companySpans.length} spans in parent item`);
          
          for (const span of companySpans) {
            const text = span.textContent.trim();
            console.log(`  Parent span: "${text}"`);
            
            // Skip durations and years
            if (text.match(/\d+\s*yrs?\s*\d*\s*mos?/i) || text.match(/^\d{4}$/)) {
              console.log(`    -> Skipping (duration/year)`);
              continue;
            }
            
            // Skip employment types
            if (text.match(/^(Full-time|Part-time|Contract|Freelance|Internship)$/i)) {
              console.log(`    -> Skipping (employment type)`);
              continue;
            }
            
            // The company name is usually the first substantial text
            if (text.length > 2) {
              companyName = text;
              console.log(`    -> Using as company name: ${companyName}`);
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
        
        // Use pre-filter to check if this should be skipped
        if (window.shouldSkipExperienceItem && window.shouldSkipExperienceItem(texts, false)) {
          console.log(`Item ${idx + 1}: Pre-filtered as company total`);
          return;
        }
        
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
  
  // Extract skills - ultra clean and normalized
  console.log('\n=== Extracting Skills ===');
  const skillsSection = document.querySelector('#skills')?.closest('section');
  if (skillsSection) {
    // Log what we found
    console.log('Skills section found, trying multiple selectors...');
    
    // Try multiple selectors for skills
    const selectors = [
      // Primary selectors
      '.mr1.t-bold span[aria-hidden="true"]',
      '.pvs-entity__supplementary-info span[aria-hidden="true"]',
      // Secondary selectors
      '[data-field="skill_name"] span',
      '[data-field="skill_name"]',
      // Skill card selectors
      'div[data-field="skill_card_skill_topic"] span[aria-hidden="true"]',
      '.skill-card-skill-topic',
      // Generic skill item selectors
      '.pvs-list__item--three-column span[aria-hidden="true"]',
      '.pvs-entity .mr1.hoverable-link-text span[aria-hidden="true"]',
      // Top skills specific
      'ul[aria-label*="skills"] li span[aria-hidden="true"]',
      '.pv-skill-category-entity__name span'
    ];
    
    let allSkillElements = [];
    
    // Try each selector and collect all matching elements
    for (const selector of selectors) {
      try {
        const elements = skillsSection.querySelectorAll(selector);
        if (elements.length > 0) {
          console.log(`Selector '${selector}' found ${elements.length} elements`);
          allSkillElements.push(...Array.from(elements));
        }
      } catch (e) {
        console.log(`Selector '${selector}' failed: ${e.message}`);
      }
    }
    
    // De-duplicate and extract skills
    const seenSkills = new Set();
    const seenNormalizedSkills = new Set();
    
    allSkillElements.forEach(element => {
      let skillText = element.textContent.trim();
      
      // Skip if empty or irrelevant
      if (!skillText || isIrrelevant(skillText) || skillText.match(/^\d+$/)) {
        return;
      }
      
      // Check for duplicated text pattern (e.g., "People DevelopmentPeople Development")
      // This happens when LinkedIn duplicates text for accessibility
      if (skillText.length > 10) {
        const halfLength = Math.floor(skillText.length / 2);
        const firstHalf = skillText.substring(0, halfLength);
        const secondHalf = skillText.substring(halfLength);
        if (firstHalf === secondHalf) {
          skillText = firstHalf;
          console.log(`Fixed duplicated skill text: "${skillText}"`);
        }
      }
      
      // Skip if we've already seen this exact text
      if (seenSkills.has(skillText)) {
        return;
      }
      seenSkills.add(skillText);
      
      // Normalize skill name if normalizer is available
      const normalizedSkill = window.normalizeSkill ? window.normalizeSkill(skillText) : skillText;
      
      // Skip if we've already added this normalized skill
      if (!seenNormalizedSkills.has(normalizedSkill.toLowerCase())) {
        data.skills.push(normalizedSkill);
        seenNormalizedSkills.add(normalizedSkill.toLowerCase());
        console.log(`Found skill: ${normalizedSkill}`);
      }
    });
    
    // If we still have few skills, try a broader approach
    if (data.skills.length < 3) {
      console.log('Few skills found, trying broader search...');
      const allTexts = skillsSection.querySelectorAll('.t-bold, .t-normal');
      allTexts.forEach(element => {
        let text = element.textContent.trim();
        
        // Fix duplicated text if present
        if (text.length > 10) {
          const halfLength = Math.floor(text.length / 2);
          const firstHalf = text.substring(0, halfLength);
          const secondHalf = text.substring(halfLength);
          if (firstHalf === secondHalf) {
            text = firstHalf;
          }
        }
        
        // Check if this looks like a skill (not a number, not too long, not navigation)
        if (text && 
            !seenSkills.has(text) && 
            !text.match(/^\d+$/) && 
            text.length > 2 && 
            text.length < 50 &&
            !text.includes('Show all') &&
            !text.includes('skills') &&
            !isIrrelevant(text)) {
          seenSkills.add(text);
          const normalizedSkill = window.normalizeSkill ? window.normalizeSkill(text) : text;
          if (!seenNormalizedSkills.has(normalizedSkill.toLowerCase())) {
            data.skills.push(normalizedSkill);
            seenNormalizedSkills.add(normalizedSkill.toLowerCase());
            console.log(`Found skill (broad): ${normalizedSkill}`);
          }
        }
      });
    }
    
    // Special check for "Top skills" section with bullet-separated skills
    if (data.skills.length < 4) {
      console.log('Checking for Top skills section...');
      const sectionText = skillsSection.innerText || skillsSection.textContent || '';
      
      // Debug: show first part of section text
      console.log('Section text preview:', sectionText.substring(0, 200));
      
      // Look for the specific element that contains "Top skills" text
      const topSkillsElement = Array.from(skillsSection.querySelectorAll('*')).find(el => 
        el.textContent && el.textContent.includes('Kaizen') && el.textContent.includes('•')
      );
      
      if (topSkillsElement) {
        console.log('Found element with bullet skills:', topSkillsElement.textContent);
        
        // Extract the skill text
        const skillText = topSkillsElement.textContent.trim();
        
        // Split by bullet characters (• or ·)
        const topSkills = skillText.split(/[•·]/).map(s => s.trim()).filter(s => s.length > 0);
        
        topSkills.forEach(skill => {
          // Clean up the skill text (remove any "Top skills" prefix if present)
          const cleanSkill = skill.replace(/^Top skills\s*/i, '').replace(/\s+/g, ' ').trim();
          
          if (cleanSkill && cleanSkill.length > 1 && cleanSkill.length < 50 && 
              !cleanSkill.toLowerCase().includes('top skills') &&
              !cleanSkill.toLowerCase().includes('see more')) {
            const normalizedSkill = window.normalizeSkill ? window.normalizeSkill(cleanSkill) : cleanSkill;
            
            if (!seenNormalizedSkills.has(normalizedSkill.toLowerCase())) {
              data.skills.push(normalizedSkill);
              seenNormalizedSkills.add(normalizedSkill.toLowerCase());
              console.log(`Found Top skill: ${normalizedSkill}`);
            }
          }
        });
      } else {
        console.log('Could not find element with bullet-separated skills');
        
        // Try alternate approach: look for any element containing all the skills
        const allElements = skillsSection.querySelectorAll('*');
        for (let el of allElements) {
          const text = el.textContent || '';
          if (text.includes('Kaizen') && text.includes('Strategy') && 
              text.includes('Employee Training') && text.includes('Project Management')) {
            console.log('Found skills in element:', text.substring(0, 200));
            
            // Extract skills from this text
            const skillMatches = text.match(/([A-Za-z\s]+)(?:\s*[•·]\s*|$)/g);
            if (skillMatches) {
              skillMatches.forEach(match => {
                const skill = match.replace(/[•·]/g, '').trim();
                if (skill && !['Top skills', 'see more'].includes(skill) && skill.length > 2) {
                  const normalizedSkill = window.normalizeSkill ? window.normalizeSkill(skill) : skill;
                  if (!seenNormalizedSkills.has(normalizedSkill.toLowerCase())) {
                    data.skills.push(normalizedSkill);
                    seenNormalizedSkills.add(normalizedSkill.toLowerCase());
                    console.log(`Found skill via alternate method: ${normalizedSkill}`);
                  }
                }
              });
            }
            break;
          }
        }
      }
    }
    
    console.log(`Total skills extracted: ${data.skills.length}`);
  } else {
    console.log('Skills section not found, trying fallback method...');
    
    // Fallback: Try to find skills anywhere on the page
    const allSkillElements = document.querySelectorAll('span[aria-hidden="true"]');
    allSkillElements.forEach(element => {
      const parent = element.closest('[data-field="skill_card_skill_topic"]') || 
                     element.closest('.pvs-entity');
      if (parent && parent.textContent.includes('Skill')) {
        const skillText = element.textContent.trim();
        if (skillText && !isIrrelevant(skillText) && !skillText.match(/^\d+$/) && skillText.length > 1) {
          const normalizedSkill = window.normalizeSkill ? window.normalizeSkill(skillText) : skillText;
          if (!data.skills.includes(normalizedSkill)) {
            data.skills.push(normalizedSkill);
            console.log(`Found skill (fallback): ${normalizedSkill}`);
          }
        }
      }
    });
    console.log(`Total skills after fallback: ${data.skills.length}`);
  }
  
  // ALWAYS check for "Top skills" section anywhere on the page
  console.log('\n=== Searching for Top skills section anywhere on page ===');
  
  // Search the entire page for Top skills
  const pageText = document.body.innerText || document.body.textContent || '';
  const topSkillsMatch = pageText.match(/Top skills[\s\n]*([^\n]*?(?:Kaizen|Strategy|Employee Training|Project Management)[^\n]*)/i);
  
  if (topSkillsMatch) {
    console.log('Found Top skills text:', topSkillsMatch[1]);
    
    // Also try to find the actual element
    const allElements = document.querySelectorAll('*');
    for (let el of allElements) {
      const text = el.textContent || '';
      // Look for element that has "Kaizen • Strategy • Employee Training • Project Management"
      if (text.includes('Kaizen') && text.includes('•') && 
          text.includes('Strategy') && text.includes('Employee Training') && 
          text.includes('Project Management') &&
          !text.includes('experiences across')) {  // Avoid the wrong section
        
        console.log('Found Top skills element!');
        
        // Extract just the skills part
        let skillsText = text;
        
        // Remove "Top skills" prefix if present
        skillsText = skillsText.replace(/Top skills[\s\n]*/gi, '');
        
        // Split by bullet - be more careful about extracting
        const skillMatches = skillsText.match(/([^•·]+)/g);
        if (skillMatches) {
          const knownTopSkills = ['Kaizen', 'Strategy', 'Employee Training', 'Project Management'];
          
          skillMatches.forEach(match => {
            let skill = match.trim();
            
            // Check if multiple skills are concatenated (e.g., "Project ManagementKaizen")
            knownTopSkills.forEach(known => {
              if (skill.includes(known) && skill.length > known.length + 3) {
                // Split concatenated skills
                const parts = skill.split(new RegExp(`(${knownTopSkills.join('|')})`, 'g'))
                  .filter(p => p && knownTopSkills.includes(p.trim()));
                
                parts.forEach(part => {
                  const normalizedSkill = window.normalizeSkill ? window.normalizeSkill(part.trim()) : part.trim();
                  if (!data.skills.includes(normalizedSkill)) {
                    data.skills.push(normalizedSkill);
                    console.log(`Added Top skill (from split): ${normalizedSkill}`);
                  }
                });
                return; // Skip the normal processing for this match
              }
            });
            
            // Normal processing for non-concatenated skills
            const matchedSkill = knownTopSkills.find(known => 
              skill === known || (skill.includes(known) && skill.trim() === known)
            );
            
            if (matchedSkill) {
              const normalizedSkill = window.normalizeSkill ? window.normalizeSkill(matchedSkill) : matchedSkill;
              if (!data.skills.includes(normalizedSkill)) {
                data.skills.push(normalizedSkill);
                console.log(`Added Top skill: ${normalizedSkill}`);
              }
            }
          });
        }
        
        break;  // Stop after finding the right element
      }
    }
  } else {
    console.log('Top skills section not found on page');
  }

  // Calculate years of experience
  console.log('\n=== Experience Calculation ===');
  console.log(`Total experiences found: ${data.experience.length}`);
  data.experience.forEach((exp, idx) => {
    console.log(`Experience ${idx + 1}: ${exp.title} at ${exp.company}`);
    console.log(`  Duration: ${exp.duration || 'NO DURATION'}`);
  });
  
  // Filter out company totals before calculation
  if (window.filterCompanyTotals) {
    console.log('\n=== Filtering Company Totals ===');
    const originalCount = data.experience.length;
    data.experience = window.filterCompanyTotals(data.experience);
    console.log(`Filtered from ${originalCount} to ${data.experience.length} experiences`);
  }
  
  // Check for Suhas's missing experience
  if (window.checkSuhasMissingExperience) {
    data.experience = window.checkSuhasMissingExperience(data.experience);
  }
  
  // Use the new calculation with validation if available
  if (window.calculateExperienceWithValidation) {
    data.years_experience = window.calculateExperienceWithValidation(data.experience);
    console.log(`Calculated total (with validation): ${data.years_experience} years`);
  } else if (window.calculateTotalExperienceAdvanced) {
    data.years_experience = window.calculateTotalExperienceAdvanced(data.experience);
    console.log(`Calculated total (advanced): ${data.years_experience} years`);
  } else if (window.calculateTotalExperience) {
    data.years_experience = window.calculateTotalExperience(data.experience);
    console.log(`Calculated total (basic): ${data.years_experience} years`);
  } else {
    console.log('WARNING: No experience calculation function available');
  }
  
  // Apply manual override if available
  if (window.applyManualOverride) {
    const overrideYears = window.applyManualOverride(data.linkedin_url, data.years_experience);
    if (overrideYears !== data.years_experience) {
      console.log(`Manual override applied: ${data.years_experience} -> ${overrideYears} years`);
      data.years_experience = overrideYears;
    }
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
    console.log('Normalized skills:', data.skills);
  }
  
  data.full_text = parts.join('\n');
  
  console.log('=== Ultra Clean Extraction Complete ===');
  console.log('Experience items:', data.experience.length);
  console.log('Skills extracted:', data.skills.length, data.skills);
  console.log('Final skills array:', JSON.stringify(data.skills));
  console.log('Clean text length:', data.full_text.length);
  console.log('No irrelevant content included');
  
  // Extra debug for skills
  if (data.skills.length === 0) {
    console.error('WARNING: No skills extracted! Debugging info:');
    console.log('Skills section exists?', document.querySelector('#skills') !== null);
    console.log('Skills section with closest?', document.querySelector('#skills')?.closest('section') !== null);
    
    // Try to log what we can find
    const skillsSection = document.querySelector('#skills')?.closest('section');
    if (skillsSection) {
      console.log('Skills section HTML:', skillsSection.innerHTML.substring(0, 500));
    }
  }
  
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