// Enhanced email extraction with multiple fallback methods
window.extractEmailEnhanced = function() {
  
  const emails = new Set();
  
  // Method 1: Look for all mailto links
  document.querySelectorAll('a[href^="mailto:"]').forEach(link => {
    const email = link.href.replace('mailto:', '').split('?')[0].trim();
    if (email && !email.includes('linkedin.com')) {
      emails.add(email);
    }
  });
  
  // Method 2: Look for email patterns in all text
  const emailRegex = /[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}/g;
  const allText = document.body.innerText || document.body.textContent || '';
  const matches = allText.match(emailRegex) || [];
  
  matches.forEach(email => {
    // Filter out common non-personal emails and false positives
    if (!email.includes('linkedin.com') && 
        !email.includes('example.com') &&
        !email.includes('support@') &&
        !email.includes('noreply@') &&
        !email.includes('@2x.') &&
        !email.includes('@3x.') &&
        !email.includes('github.com') &&
        email.length < 50) {
      emails.add(email);
    }
  });
  
  // Method 3: Check specific areas where email might appear
  const targetSelectors = [
    '.pv-contact-info',
    '.pv-top-card',
    '.pv-profile-section',
    'section[data-section="contact"]',
    '.contact-info',
    '[aria-label*="contact"]',
    '[aria-label*="email"]'
  ];
  
  targetSelectors.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    elements.forEach(element => {
      const text = element.textContent || '';
      const emailMatch = text.match(emailRegex);
      if (emailMatch) {
        emailMatch.forEach(email => {
          if (!email.includes('linkedin.com') && email.length < 50) {
            emails.add(email);
          }
        });
      }
    });
  });
  
  // Method 4: Check data attributes
  document.querySelectorAll('[data-email], [data-contact-email]').forEach(element => {
    const email = element.getAttribute('data-email') || element.getAttribute('data-contact-email');
    if (email && email.includes('@')) {
      emails.add(email);
    }
  });
  
  // Return the first valid email found
  const emailArray = Array.from(emails);
  
  // Prefer emails that look more personal (contain name parts from profile)
  const profileName = document.querySelector('h1')?.textContent?.toLowerCase() || '';
  const nameParts = profileName.split(' ').filter(part => part.length > 2);
  
  const personalEmail = emailArray.find(email => {
    const emailLower = email.toLowerCase();
    return nameParts.some(namePart => emailLower.includes(namePart));
  });
  
  const result = personalEmail || emailArray[0] || '';
  return result;
};