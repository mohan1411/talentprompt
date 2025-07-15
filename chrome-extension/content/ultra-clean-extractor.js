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
      /^at\s*\d+/i // "at 3 endorsements"
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
  
  // Extract experience - ultra clean
  const expSection = document.querySelector('#experience')?.closest('section');
  if (expSection) {
    console.log('Processing experience section...');
    const expList = expSection.querySelector('ul');
    if (expList) {
      const items = expList.querySelectorAll('li');
      console.log(`Found ${items.length} potential experience items`);
      
      items.forEach((item, idx) => {
        const texts = [];
        item.querySelectorAll('span[aria-hidden="true"]').forEach(span => {
          const text = span.textContent.trim();
          if (text && !isIrrelevant(text) && text.length > 2) {
            texts.push(text);
          }
        });
        
        if (texts.length >= 2) {
          const exp = {
            title: texts[0],
            company: '',
            duration: '',
            location: '',
            description: ''
          };
          
          // Parse company
          if (texts[1] && texts[1].includes('·')) {
            const parts = texts[1].split('·').map(p => p.trim());
            exp.company = parts[0];
          } else if (texts[1]) {
            exp.company = texts[1];
          }
          
          // Find duration
          for (let i = 2; i < texts.length; i++) {
            if (texts[i].match(/\d{4}|Present|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec/i)) {
              exp.duration = texts[i];
              if (i + 1 < texts.length && texts[i + 1].includes(',')) {
                exp.location = texts[i + 1];
              }
              break;
            }
          }
          
          // Verify this is a real experience
          if (!isIrrelevant(exp.title) && !isIrrelevant(exp.company)) {
            data.experience.push(exp);
            console.log(`Added experience ${idx + 1}:`, exp.title, 'at', exp.company);
          } else {
            console.log(`Skipped irrelevant item ${idx + 1}:`, texts[0]);
          }
        }
      });
    }
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