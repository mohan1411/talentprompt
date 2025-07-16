// Extract contact info that might be visible inline on the profile
window.extractInlineContactInfo = function() {
  try {
    console.log('=== Inline Contact Extraction ===');
  
  const contactInfo = {
    email: '',
    phone: '',
    linkedin: window.location.href.split('?')[0]
  };
  
  // First, search the entire page for email patterns
  const pageText = document.body.innerText || document.body.textContent || '';
  console.log('Page text length:', pageText.length);
  
  // More comprehensive email regex
  const emailRegex = /[a-zA-Z0-9][a-zA-Z0-9._-]*@[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}/g;
  const allEmails = pageText.match(emailRegex);
  
  if (allEmails && allEmails.length > 0) {
    console.log('Found emails on page:', allEmails);
    // Filter out common non-personal emails
    const personalEmail = allEmails.find(email => 
      !email.includes('linkedin.com') && 
      !email.includes('example.com') &&
      !email.includes('support@') &&
      !email.includes('help@') &&
      !email.includes('noreply@') &&
      !email.includes('no-reply@') &&
      email.length < 50 // Avoid long malformed strings
    );
    
    if (personalEmail) {
      contactInfo.email = personalEmail;
      console.log('Selected personal email:', personalEmail);
      return contactInfo;
    } else {
      console.log('All emails were filtered out as non-personal');
    }
  } else {
    console.log('No email patterns found on page');
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
  
  // Method 4: Check the profile header for contact info badge
  if (!contactInfo.email) {
    const profileHeader = document.querySelector('.pv-top-card') || document.querySelector('section.pv-profile-section');
    if (profileHeader) {
      const links = profileHeader.querySelectorAll('a');
      links.forEach(link => {
        const href = link.href || '';
        if (href.includes('mailto:')) {
          contactInfo.email = href.replace('mailto:', '');
          console.log('Found email in profile header link:', contactInfo.email);
        }
      });
    }
  }
  
  // Method 5: Look for email in any visible text that contains @ symbol
  if (!contactInfo.email) {
    const allElements = document.querySelectorAll('*');
    for (const element of allElements) {
      // Skip script and style elements
      if (element.tagName === 'SCRIPT' || element.tagName === 'STYLE') continue;
      
      // Check only direct text nodes
      const textNodes = Array.from(element.childNodes).filter(node => node.nodeType === 3);
      for (const textNode of textNodes) {
        const text = textNode.textContent || '';
        const emailMatch = text.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
        if (emailMatch && !emailMatch[0].includes('linkedin.com')) {
          contactInfo.email = emailMatch[0];
          console.log('Found email in text node:', contactInfo.email);
          break;
        }
      }
      if (contactInfo.email) break;
    }
  }
  
  console.log('Inline extraction result:', contactInfo);
  return contactInfo;
  
  } catch (error) {
    console.error('Error in inline contact extraction:', error);
    return {
      email: '',
      phone: '',
      linkedin: window.location.href.split('?')[0]
    };
  }
};