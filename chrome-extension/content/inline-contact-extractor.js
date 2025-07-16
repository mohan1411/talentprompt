// Extract contact info that might be visible inline on the profile
window.extractInlineContactInfo = function() {
  console.log('=== Inline Contact Extraction ===');
  
  const contactInfo = {
    email: '',
    phone: '',
    linkedin: window.location.href.split('?')[0]
  };
  
  // First, search the entire page for email patterns
  const pageText = document.body.innerText || document.body.textContent || '';
  console.log('Page text length:', pageText.length);
  
  const emailRegex = /[\w.-]+@[\w.-]+\.\w+/g;
  const allEmails = pageText.match(emailRegex);
  
  if (allEmails && allEmails.length > 0) {
    console.log('Found emails on page:', allEmails);
    // Filter out common non-personal emails
    const personalEmail = allEmails.find(email => 
      !email.includes('linkedin.com') && 
      !email.includes('example.com') &&
      !email.includes('support@') &&
      !email.includes('help@')
    );
    
    if (personalEmail) {
      contactInfo.email = personalEmail;
      console.log('Selected personal email:', personalEmail);
      return contactInfo;
    }
  }
  
  // Method 1: Check the intro card for any visible contact info
  const introCard = document.querySelector('.pv-top-card') || 
                    document.querySelector('.pv-text-details__left-panel');
  
  if (introCard) {
    const introText = introCard.textContent || '';
    
    // Look for email pattern
    const emailMatch = introText.match(/[\w.-]+@[\w.-]+\.\w+/);
    if (emailMatch) {
      contactInfo.email = emailMatch[0];
      console.log('Found email in intro card:', contactInfo.email);
    }
    
    // Look for phone pattern
    const phoneMatch = introText.match(/[\+]?[\d\s\-\(\)]+[\d]/);
    if (phoneMatch && phoneMatch[0].length > 9) {
      contactInfo.phone = phoneMatch[0].trim();
      console.log('Found phone in intro card:', contactInfo.phone);
    }
  }
  
  // Method 2: Check contact info section if it exists inline
  const contactSection = document.querySelector('.pv-contact-info') ||
                        document.querySelector('[class*="contact-info"]');
  
  if (contactSection) {
    console.log('Found inline contact section');
    const sectionText = contactSection.textContent || '';
    
    if (!contactInfo.email) {
      const emailMatch = sectionText.match(/[\w.-]+@[\w.-]+\.\w+/);
      if (emailMatch) {
        contactInfo.email = emailMatch[0];
        console.log('Found email in contact section:', contactInfo.email);
      }
    }
  }
  
  // Method 3: Check for mailto links anywhere on the profile
  if (!contactInfo.email) {
    const mailtoLinks = document.querySelectorAll('a[href^="mailto:"]');
    if (mailtoLinks.length > 0) {
      contactInfo.email = mailtoLinks[0].href.replace('mailto:', '');
      console.log('Found mailto link:', contactInfo.email);
    }
  }
  
  console.log('Inline extraction result:', contactInfo);
  return contactInfo;
};