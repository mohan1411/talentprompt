// Direct email extraction - simpler approach
window.extractEmailDirect = function(modal) {
  console.log('=== Direct Email Extraction ===');
  
  let email = '';
  
  // Method 1: Get all text content and find email pattern
  const modalText = modal.innerText || modal.textContent || '';
  console.log('Modal text length:', modalText.length);
  
  // Look for email pattern
  const emailRegex = /[\w\.\-]+@[\w\.\-]+\.[a-zA-Z]{2,}/g;
  const matches = modalText.match(emailRegex);
  
  if (matches && matches.length > 0) {
    email = matches[0];
    console.log('Found email via regex:', email);
  }
  
  // Method 2: Check specific elements that might contain email
  if (!email) {
    // LinkedIn often uses these structures
    const possibleContainers = [
      'div.pv-contact-info__ci-container',
      'div.pv-contact-info__contact-item',
      'section.pv-contact-info__contact-type',
      'div[class*="contact-info"]',
      'section[class*="ci-email"]',
      'div[id*="email"]'
    ];
    
    for (const selector of possibleContainers) {
      const elements = modal.querySelectorAll(selector);
      console.log(`Checking ${selector}: found ${elements.length} elements`);
      
      elements.forEach((el, idx) => {
        const text = el.innerText || el.textContent || '';
        const emailMatch = text.match(emailRegex);
        if (emailMatch && !email) {
          email = emailMatch[0];
          console.log(`Found email in ${selector}[${idx}]:`, email);
        }
      });
      
      if (email) break;
    }
  }
  
  // Method 3: Look at all anchor tags
  if (!email) {
    const links = modal.querySelectorAll('a');
    console.log(`Checking ${links.length} links`);
    
    links.forEach((link, idx) => {
      // Check href
      if (link.href && link.href.includes('@')) {
        console.log(`Link ${idx} has @ in href:`, link.href);
        const match = link.href.match(emailRegex);
        if (match && !email) {
          email = match[0];
        }
      }
      
      // Check text content
      const text = link.innerText || link.textContent || '';
      const textMatch = text.match(emailRegex);
      if (textMatch && !email) {
        email = textMatch[0];
        console.log(`Link ${idx} has email in text:`, email);
      }
    });
  }
  
  // Method 4: Check all text nodes
  if (!email) {
    console.log('Checking all text nodes...');
    const walker = document.createTreeWalker(
      modal,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );
    
    let node;
    let nodeCount = 0;
    while (node = walker.nextNode()) {
      const text = node.textContent || '';
      const match = text.match(emailRegex);
      if (match) {
        nodeCount++;
        console.log(`Text node ${nodeCount} contains:`, text.trim());
        if (!email) email = match[0];
      }
    }
  }
  
  return email;
};