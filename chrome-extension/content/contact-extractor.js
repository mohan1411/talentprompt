// Extract contact information from LinkedIn profile
window.extractContactInfo = async function() {
  const contactInfo = {
    email: '',
    phone: '',
    linkedin: window.location.href.split('?')[0],
    website: '',
    address: ''
  };
  
  try {
    // Method 1: Look for Contact Info button in the profile
    const contactButton = document.querySelector('a[id*="contact-info"]') ||
                         document.querySelector('button[aria-label*="Contact info"]') ||
                         document.querySelector('[data-control-name="contact_see_more"]') ||
                         document.querySelector('.pv-top-card-v2-ctas a[href*="overlay/contact-info"]');
    
    if (contactButton) {
      console.log('Found contact info button, attempting to extract...');
      
      // Check if contact modal is already open
      let contactModal = document.querySelector('.pv-profile-modal__content') ||
                        document.querySelector('[data-test-modal]') ||
                        document.querySelector('.artdeco-modal__content');
      
      if (!contactModal) {
        // Click the button to open modal
        contactButton.click();
        
        // Wait for modal to appear
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        contactModal = document.querySelector('.pv-profile-modal__content') ||
                      document.querySelector('[data-test-modal]') ||
                      document.querySelector('.artdeco-modal__content');
      }
      
      if (contactModal) {
        // Extract email
        const emailSection = contactModal.querySelector('section[class*="email"]') ||
                           contactModal.querySelector('[href^="mailto:"]');
        if (emailSection) {
          const emailLink = emailSection.querySelector('a[href^="mailto:"]');
          if (emailLink) {
            contactInfo.email = emailLink.href.replace('mailto:', '').trim();
          } else {
            const emailText = emailSection.textContent.match(/[\w.-]+@[\w.-]+\.\w+/);
            if (emailText) {
              contactInfo.email = emailText[0];
            }
          }
        }
        
        // Extract phone
        const phoneSection = contactModal.querySelector('section[class*="phone"]') ||
                           contactModal.querySelector('[href^="tel:"]');
        if (phoneSection) {
          const phoneLink = phoneSection.querySelector('a[href^="tel:"]');
          if (phoneLink) {
            contactInfo.phone = phoneLink.href.replace('tel:', '').trim();
          } else {
            const phoneText = phoneSection.textContent.match(/[\+\d\s\-\(\)]+/);
            if (phoneText && phoneText[0].length > 6) {
              contactInfo.phone = phoneText[0].trim();
            }
          }
        }
        
        // Extract website
        const websiteSection = contactModal.querySelector('section[class*="website"]') ||
                             contactModal.querySelector('[data-field="websites"]');
        if (websiteSection) {
          const websiteLink = websiteSection.querySelector('a[href]');
          if (websiteLink) {
            contactInfo.website = websiteLink.href;
          }
        }
        
        // Extract address
        const addressSection = contactModal.querySelector('section[class*="address"]');
        if (addressSection) {
          const addressText = addressSection.querySelector('.pv-contact-info__ci-container');
          if (addressText) {
            contactInfo.address = addressText.textContent.trim();
          }
        }
        
        // Close modal
        const closeButton = contactModal.querySelector('button[aria-label*="Dismiss"]') ||
                          contactModal.querySelector('button[data-test-modal-close-btn]');
        if (closeButton) {
          closeButton.click();
        }
      }
    }
    
    // Method 2: Check profile intro section for any visible contact info
    const introSection = document.querySelector('.pv-text-details__left-panel') ||
                        document.querySelector('.pv-top-card-v2-section__info');
    
    if (introSection && !contactInfo.email) {
      // Sometimes email is visible in the intro
      const emailMatch = introSection.textContent.match(/[\w.-]+@[\w.-]+\.\w+/);
      if (emailMatch) {
        contactInfo.email = emailMatch[0];
      }
    }
    
  } catch (error) {
    console.error('Error extracting contact info:', error);
  }
  
  console.log('Extracted contact info:', contactInfo);
  return contactInfo;
};