// Advanced email finder for LinkedIn contact modal
window.findEmailInModal = function(modal) {
  console.log('=== Advanced Email Search ===');
  
  // Method 1: Find by email icon SVG
  const svgIcons = modal.querySelectorAll('svg');
  svgIcons.forEach((svg, idx) => {
    const svgHTML = svg.outerHTML;
    // Email icon often has specific path data
    if (svgHTML.includes('envelope') || svgHTML.includes('mail') || svgHTML.includes('M3 8l7')) {
      console.log(`Found potential email icon at SVG ${idx}`);
      
      // Look for email in parent containers
      let parent = svg.parentElement;
      for (let i = 0; i < 5 && parent; i++) {
        const links = parent.querySelectorAll('a');
        links.forEach(link => {
          if (link.href && link.href.includes('mailto:')) {
            console.log('Found email via icon parent:', link.href);
          }
        });
        
        // Check text content
        const text = parent.textContent || '';
        const emailMatch = text.match(/[\w.-]+@[\w.-]+\.\w+/);
        if (emailMatch) {
          console.log('Found email via icon parent text:', emailMatch[0]);
        }
        
        parent = parent.parentElement;
      }
    }
  });
  
  // Method 2: Find by structure - LinkedIn often uses section > div > div > a
  const sections = modal.querySelectorAll('section');
  sections.forEach((section, idx) => {
    const structure = [];
    let current = section;
    
    // Build structure path
    while (current && current !== modal) {
      structure.unshift(current.tagName + (current.className ? '.' + current.className.split(' ')[0] : ''));
      current = current.parentElement;
    }
    
    console.log(`Section ${idx} structure:`, structure.join(' > '));
    
    // Look for email patterns in this section
    const anchors = section.querySelectorAll('a');
    anchors.forEach(anchor => {
      console.log(`Section ${idx} anchor:`, {
        href: anchor.href,
        text: anchor.textContent.trim()
      });
    });
  });
  
  // Method 3: Find by traversing all elements with email-like content
  const allElements = modal.querySelectorAll('*');
  const emailRegex = /[\w.-]+@[\w.-]+\.\w+/;
  
  allElements.forEach((element, idx) => {
    const text = element.textContent || '';
    if (emailRegex.test(text) && element.children.length === 0) {
      console.log(`Element ${idx} contains email:`, {
        tag: element.tagName,
        class: element.className,
        text: text.trim(),
        parent: element.parentElement?.tagName
      });
    }
  });
  
  // Method 4: Look for specific LinkedIn patterns
  // LinkedIn might use data attributes or specific classes
  const dataAttributes = ['data-field', 'data-test-id', 'data-control-name'];
  dataAttributes.forEach(attr => {
    const elements = modal.querySelectorAll(`[${attr}*="email"]`);
    elements.forEach(el => {
      console.log(`Element with ${attr}:`, {
        value: el.getAttribute(attr),
        tag: el.tagName,
        text: el.textContent.trim()
      });
    });
  });
};