// Simple LinkedIn data extractor with fallback methods
function extractProfileDataSimple() {
  const data = {
    linkedin_url: window.location.href.split('?')[0],
    name: '',
    headline: '',
    location: '',
    about: '',
    experience: [],
    education: [],
    skills: [],
    raw_text: '' // Fallback for when structured extraction fails
  };
  
  try {
    // Method 1: Try to get name from the most common location
    const nameH1 = document.querySelector('h1');
    if (nameH1) {
      data.name = nameH1.textContent.trim();
    }
    
    // Method 2: Get the first text-body-medium that's not location
    const textMediums = document.querySelectorAll('.text-body-medium');
    for (let elem of textMediums) {
      const text = elem.textContent.trim();
      if (text && !text.includes('·') && text.length > 10 && text.length < 200) {
        data.headline = text;
        break;
      }
    }
    
    // Method 3: Get location from elements with location-like text
    const textSmalls = document.querySelectorAll('.text-body-small');
    for (let elem of textSmalls) {
      const text = elem.textContent.trim();
      // Look for patterns like "City, State" or "City, Country"
      if (text && text.match(/^[A-Za-z\s]+,\s*[A-Za-z\s]+$/)) {
        data.location = text;
        break;
      }
    }
    
    // Method 4: Extract sections by ID and get all text
    const sections = ['about', 'experience', 'education', 'skills'];
    sections.forEach(sectionId => {
      const section = document.querySelector(`#${sectionId}`)?.parentElement;
      if (section) {
        // Get all visible text in the section
        const allText = [];
        const walker = document.createTreeWalker(
          section,
          NodeFilter.SHOW_TEXT,
          {
            acceptNode: function(node) {
              // Skip hidden elements
              const parent = node.parentElement;
              if (parent && window.getComputedStyle(parent).display !== 'none') {
                return NodeFilter.FILTER_ACCEPT;
              }
              return NodeFilter.FILTER_REJECT;
            }
          }
        );
        
        let node;
        while (node = walker.nextNode()) {
          const text = node.textContent.trim();
          if (text.length > 2) { // Skip very short text
            allText.push(text);
          }
        }
        
        const sectionText = allText.join(' ').replace(/\s+/g, ' ').trim();
        
        if (sectionId === 'about' && sectionText) {
          // Remove the "About" heading if present
          data.about = sectionText.replace(/^About\s*/i, '').trim();
        } else if (sectionId === 'experience' && sectionText) {
          // Try to parse experience items
          // Look for patterns like "Title at Company"
          const lines = sectionText.split('\n').map(l => l.trim()).filter(l => l);
          let currentExp = null;
          
          lines.forEach(line => {
            // Check if this looks like a job title (usually starts with capital letter and is not too long)
            if (line.length > 5 && line.length < 100 && /^[A-Z]/.test(line) && !line.includes('·')) {
              if (currentExp) {
                data.experience.push(currentExp);
              }
              currentExp = {
                title: line,
                company: '',
                duration: '',
                description: ''
              };
            } else if (currentExp) {
              // Check if it's a company name (often contains "at" or specific keywords)
              if (line.toLowerCase().includes(' at ') || line.includes('GmbH') || line.includes('Ltd') || line.includes('Inc')) {
                currentExp.company = line;
              } else if (line.match(/\d{4}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec/)) {
                currentExp.duration = line;
              } else if (line.length > 20) {
                currentExp.description = (currentExp.description + ' ' + line).trim();
              }
            }
          });
          
          if (currentExp) {
            data.experience.push(currentExp);
          }
          
          // If no structured experience found, add raw text
          if (data.experience.length === 0) {
            data.experience.push({
              raw_text: sectionText.substring(0, 1000)
            });
          }
        } else if (sectionId === 'education' && sectionText) {
          data.education.push({
            raw_text: sectionText.substring(0, 500)
          });
        } else if (sectionId === 'skills' && sectionText) {
          // Extract individual skills
          const skillMatches = sectionText.match(/([A-Za-z][A-Za-z\s\+\#\.]+?)(?:\s+\d+|$)/g);
          if (skillMatches) {
            data.skills = skillMatches.map(s => s.trim()).filter(s => s.length > 2 && s.length < 50);
          }
        }
      }
    });
    
    // Fallback: Get raw text from main content area
    const mainContent = document.querySelector('main');
    if (mainContent) {
      const textNodes = [];
      const walker = document.createTreeWalker(
        mainContent,
        NodeFilter.SHOW_TEXT,
        null,
        false
      );
      
      let node;
      while (node = walker.nextNode()) {
        const text = node.textContent.trim();
        if (text.length > 10) {
          textNodes.push(text);
        }
      }
      
      data.raw_text = textNodes.slice(0, 100).join(' ').substring(0, 5000); // Limit size
    }
    
  } catch (error) {
    console.error('Error in simple extraction:', error);
  }
  
  console.log('Simple extraction result:', {
    name: data.name,
    headline: data.headline ? data.headline.substring(0, 50) + '...' : '',
    location: data.location,
    aboutLength: data.about.length,
    experienceItems: data.experience.length,
    educationItems: data.education.length,
    skillsCount: data.skills.length,
    rawTextLength: data.raw_text.length
  });
  
  return data;
}

// Export for use in main script
window.extractProfileDataSimple = extractProfileDataSimple;