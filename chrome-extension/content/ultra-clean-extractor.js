// Ultra clean extractor - filters at source, no unfiltered content ever
window.extractUltraCleanProfile = function() {
  console.log('=== Ultra Clean Extraction Starting ===');
  
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
    const aboutEl = aboutSection.querySelector('.inline-show-more-text span[aria-hidden="true"]') ||
                   aboutSection.querySelector('span[aria-hidden="true"]');
    if (aboutEl && !isIrrelevant(aboutEl.textContent)) {
      data.about = aboutEl.textContent.trim();
    }
  }
  
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
        
        console.log(`Item ${idx + 1} texts:`, texts);
        
        if (texts.length >= 2) {
          const exp = {
            title: texts[0],
            company: '',
            duration: '',
            location: '',
            description: ''
          };
          
          // Parse company - handle various formats
          if (texts[1]) {
            if (texts[1].includes('·')) {
              const parts = texts[1].split('·').map(p => p.trim());
              exp.company = parts[0];
            } else {
              exp.company = texts[1];
            }
          }
          
          // Find duration - look for date patterns
          for (let i = 2; i < texts.length; i++) {
            const text = texts[i];
            // Check for duration patterns
            if (text.match(/\d{4}|Present|Current|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d+\s*yr|\d+\s*mo/i)) {
              exp.duration = text;
              
              // LinkedIn sometimes shows duration on next line (e.g., "11 yrs 7 mos")
              if (i + 1 < texts.length) {
                const nextText = texts[i + 1];
                if (nextText.match(/\d+\s*yrs?\s*\d*\s*mos?/i)) {
                  exp.duration = text + ' · ' + nextText;
                  console.log(`Combined duration: ${exp.duration}`);
                  i++; // Skip the next item since we used it
                }
                // Check if next item is location
                else if (nextText.includes(',')) {
                  exp.location = nextText;
                }
              }
              break;
            }
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
            console.log(`Skipped item ${idx + 1} - title: "${texts[0]}" company: "${texts[1] || 'none'}"`);
          }
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
  if (window.calculateTotalExperience) {
    data.years_experience = window.calculateTotalExperience(data.experience);
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
};