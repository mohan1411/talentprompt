// Clean LinkedIn profile extractor - focused on main content only
window.extractCleanProfileData = function() {
  const data = {
    linkedin_url: window.location.href.split('?')[0],
    name: '',
    headline: '',
    location: '',
    about: '',
    experience: [],
    education: [],
    skills: [],
    full_text: ''
  };
  
  try {
    // 1. Extract basic info from the profile header
    const profileSection = document.querySelector('.ph5.pb5') || 
                          document.querySelector('.pv-top-card') ||
                          document.querySelector('[data-member-id]');
    
    if (profileSection) {
      // Name
      const nameEl = profileSection.querySelector('h1');
      if (nameEl) data.name = nameEl.textContent.trim();
      
      // Headline
      const headlineEl = profileSection.querySelector('.text-body-medium.break-words');
      if (headlineEl) data.headline = headlineEl.textContent.trim();
      
      // Location
      const locationEl = profileSection.querySelector('.text-body-small.inline.t-black--light');
      if (locationEl) data.location = locationEl.textContent.trim();
    }
    
    // 2. Extract About section
    const aboutSection = document.querySelector('#about')?.closest('section');
    if (aboutSection) {
      const aboutContent = aboutSection.querySelector('.inline-show-more-text span[aria-hidden="true"]') ||
                          aboutSection.querySelector('.pv-shared-text-with-see-more span[aria-hidden="true"]');
      if (aboutContent) {
        data.about = aboutContent.textContent.trim();
      }
    }
    
    // 3. Extract Experience - Focus on the experience section only
    const experienceSection = document.querySelector('#experience')?.closest('section');
    if (experienceSection) {
      // Get only the list within the experience section
      const expList = experienceSection.querySelector('.pvs-list') || 
                     experienceSection.querySelector('ul');
      
      if (expList) {
        const expItems = expList.children;
        
        for (let item of expItems) {
          // Skip if it's not a list item
          if (item.tagName !== 'LI') continue;
          
          const exp = {
            title: '',
            company: '',
            duration: '',
            location: '',
            description: ''
          };
          
          // Extract texts from this specific item only
          const itemTexts = [];
          item.querySelectorAll('span[aria-hidden="true"]').forEach(span => {
            const text = span.textContent.trim();
            if (text && text.length > 1 && !itemTexts.includes(text)) {
              itemTexts.push(text);
            }
          });
          
          console.log('Experience item texts:', itemTexts);
          
          // Parse the texts
          if (itemTexts.length >= 2) {
            // First text is usually the title
            exp.title = itemTexts[0];
            
            // Second text often contains company and employment type
            if (itemTexts[1].includes(' · ')) {
              const parts = itemTexts[1].split(' · ');
              exp.company = parts[0];
              exp.employment_type = parts[1];
            } else {
              exp.company = itemTexts[1];
            }
            
            // Look for duration (contains months/years)
            for (let i = 2; i < itemTexts.length; i++) {
              if (itemTexts[i].match(/\d{4}|Present|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec/i)) {
                exp.duration = itemTexts[i];
                // Next item might be location
                if (i + 1 < itemTexts.length && itemTexts[i + 1].includes(',')) {
                  exp.location = itemTexts[i + 1];
                }
                break;
              }
            }
            
            data.experience.push(exp);
          }
        }
      }
    }
    
    // 4. Extract Skills
    const skillsSection = document.querySelector('#skills')?.closest('section');
    if (skillsSection) {
      skillsSection.querySelectorAll('.mr1.t-bold span[aria-hidden="true"]').forEach(skill => {
        const skillName = skill.textContent.trim();
        if (skillName && !data.skills.includes(skillName)) {
          data.skills.push(skillName);
        }
      });
    }
    
    // 5. Extract Education
    const educationSection = document.querySelector('#education')?.closest('section');
    if (educationSection) {
      const eduList = educationSection.querySelector('.pvs-list') || 
                     educationSection.querySelector('ul');
      
      if (eduList) {
        const eduItems = eduList.children;
        
        for (let item of eduItems) {
          if (item.tagName !== 'LI') continue;
          
          const edu = {
            school: '',
            degree: '',
            field: '',
            dates: ''
          };
          
          const itemTexts = [];
          item.querySelectorAll('span[aria-hidden="true"]').forEach(span => {
            const text = span.textContent.trim();
            if (text && text.length > 1 && !itemTexts.includes(text)) {
              itemTexts.push(text);
            }
          });
          
          if (itemTexts.length >= 1) {
            edu.school = itemTexts[0];
            if (itemTexts[1]) {
              // Parse degree and field
              const degreeText = itemTexts[1];
              if (degreeText.includes(',')) {
                const parts = degreeText.split(',');
                edu.degree = parts[0].trim();
                edu.field = parts[1].trim();
              } else {
                edu.degree = degreeText;
              }
            }
            
            data.education.push(edu);
          }
        }
      }
    }
    
    // 6. Calculate years of experience
    let totalMonths = 0;
    data.experience.forEach(exp => {
      if (exp.duration) {
        // Extract years and months
        const yearsMatch = exp.duration.match(/(\d+)\s*(?:yrs?|years?)/i);
        const monthsMatch = exp.duration.match(/(\d+)\s*(?:mos?|months?)/i);
        
        const years = yearsMatch ? parseInt(yearsMatch[1]) : 0;
        const months = monthsMatch ? parseInt(monthsMatch[1]) : 0;
        
        totalMonths += (years * 12) + months;
      }
    });
    
    const totalYears = Math.round(totalMonths / 12);
    
    // 7. Build clean full text (without irrelevant content)
    const textParts = [];
    
    // Add basic info
    if (data.name) textParts.push(data.name);
    if (data.headline) textParts.push(data.headline);
    if (data.location) textParts.push(data.location);
    if (totalYears > 0) textParts.push(`${totalYears} years of experience`);
    
    // Add about
    if (data.about) {
      textParts.push('\nABOUT\n' + data.about);
    }
    
    // Add experience
    if (data.experience.length > 0) {
      textParts.push('\nEXPERIENCE');
      data.experience.forEach(exp => {
        textParts.push(`\n${exp.title}`);
        if (exp.company) textParts.push(exp.company);
        if (exp.duration) textParts.push(exp.duration);
        if (exp.location) textParts.push(exp.location);
        if (exp.description) textParts.push(exp.description);
      });
    }
    
    // Add education
    if (data.education.length > 0) {
      textParts.push('\nEDUCATION');
      data.education.forEach(edu => {
        textParts.push(`\n${edu.school}`);
        if (edu.degree && edu.field) {
          textParts.push(`${edu.degree}, ${edu.field}`);
        } else if (edu.degree) {
          textParts.push(edu.degree);
        }
      });
    }
    
    // Add skills
    if (data.skills.length > 0) {
      textParts.push('\nSKILLS\n' + data.skills.join(', '));
    }
    
    data.full_text = textParts.join('\n');
    data.years_experience = totalYears;
    
  } catch (error) {
    console.error('Clean extraction error:', error);
  }
  
  return data;
};