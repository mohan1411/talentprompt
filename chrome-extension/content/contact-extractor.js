// Extract contact information from LinkedIn profile
window.extractContactInfo = async function() {
  console.log('=== Starting Contact Info Extraction ===');
  
  const contactInfo = {
    email: '',
    phone: '',
    linkedin: window.location.href.split('?')[0],
    website: '',
    address: ''
  };
  
  try {
    // Method 1: Look for Contact Info button with multiple selectors
    const contactButtonSelectors = [
      'a[id*="contact-info"]',
      'button[aria-label*="Contact info"]',
      'button[aria-label*="contact info" i]',
      '[data-control-name="contact_see_more"]',
      '.pv-top-card a[href*="contact-info"]',
      '.pv-top-card-v2-ctas a[href*="contact-info"]',
      '.pv-top-card-v3-ctas a[href*="contact-info"]',
      'a[href*="/overlay/contact-info/"]',
      'button:has-text("Contact info")',
      '.pvs-profile-actions a[href*="contact-info"]',
      '[data-test-id="contact-info"]'
    ];
    
    let contactButton = null;
    for (const selector of contactButtonSelectors) {
      try {
        contactButton = document.querySelector(selector);
        if (contactButton) {
          console.log(`Found contact button with selector: ${selector}`);
          break;
        }
      } catch (e) {
        // Some selectors might not be valid, continue
      }
    }
    
    if (contactButton) {
      console.log('Contact info button found, attempting to click...');
      
      // Check if contact modal is already open
      let contactModal = document.querySelector('.pv-profile-modal__content') ||
                        document.querySelector('[data-test-modal]') ||
                        document.querySelector('.artdeco-modal__content') ||
                        document.querySelector('[role="dialog"]');
      
      if (!contactModal) {
        console.log('Modal not open, clicking button...');
        // Click the button to open modal
        contactButton.click();
        
        // Wait for modal to appear with multiple attempts
        for (let i = 0; i < 5; i++) {
          await new Promise(resolve => setTimeout(resolve, 500));
          
          contactModal = document.querySelector('.pv-profile-modal__content') ||
                        document.querySelector('[data-test-modal]') ||
                        document.querySelector('.artdeco-modal__content') ||
                        document.querySelector('[role="dialog"]') ||
                        document.querySelector('.pv-overlay__content');
          
          if (contactModal) {
            console.log(`Modal appeared after ${i + 1} attempts`);
            break;
          }
        }
      } else {
        console.log('Modal already open');
      }
      
      if (contactModal) {
        console.log('Modal found, extracting contact info...');
        
        // Extract email - try multiple methods
        const emailSelectors = [
          'a[href^="mailto:"]',
          'section[class*="email"] a',
          '[data-field="email"] a',
          '.pv-contact-info__contact-type:has(svg[data-test-icon="envelope"]) a',
          '.ci-email a'
        ];
        
        for (const selector of emailSelectors) {
          const emailElement = contactModal.querySelector(selector);
          if (emailElement) {
            if (emailElement.href && emailElement.href.startsWith('mailto:')) {
              contactInfo.email = emailElement.href.replace('mailto:', '').trim();
              console.log(`Found email with selector: ${selector}`);
              break;
            }
          }
        }
        
        // If no email link found, try regex on modal text
        if (!contactInfo.email) {
          const modalText = contactModal.textContent || '';
          const emailMatch = modalText.match(/[\w.-]+@[\w.-]+\.\w+/);
          if (emailMatch) {
            contactInfo.email = emailMatch[0];
            console.log('Found email via regex');
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
                          contactModal.querySelector('button[data-test-modal-close-btn]') ||
                          contactModal.querySelector('button[aria-label*="Close"]') ||
                          contactModal.querySelector('.artdeco-modal__dismiss');
        if (closeButton) {
          console.log('Closing modal');
          closeButton.click();
        }
      } else {
        console.log('WARNING: Contact modal did not appear after clicking button');
      }
    } else {
      console.log('WARNING: No contact info button found on profile');
      
      // Debug: Look for all links and buttons that might be contact info
      console.log('=== Debugging Contact Button Search ===');
      
      // Check all links
      const allLinks = document.querySelectorAll('a');
      allLinks.forEach(link => {
        const text = link.textContent.trim().toLowerCase();
        const href = link.href || '';
        if (text.includes('contact') || href.includes('contact')) {
          console.log('Found potential contact link:', {
            text: link.textContent.trim(),
            href: href,
            classes: link.className
          });
        }
      });
      
      // Check all buttons
      const allButtons = document.querySelectorAll('button');
      allButtons.forEach(button => {
        const text = button.textContent.trim().toLowerCase();
        if (text.includes('contact')) {
          console.log('Found potential contact button:', {
            text: button.textContent.trim(),
            classes: button.className,
            ariaLabel: button.getAttribute('aria-label')
          });
        }
      });
      
      // Check the profile actions area specifically
      const profileActions = document.querySelector('.pvs-profile-actions') || 
                           document.querySelector('.pv-s-profile-actions') ||
                           document.querySelector('[data-view-name="profile-actions"]');
      if (profileActions) {
        console.log('Profile actions area found, links:', profileActions.querySelectorAll('a').length);
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
  
  // Final summary
  console.log('=== Contact Extraction Results ===');
  console.log('Email:', contactInfo.email || 'Not found');
  console.log('Phone:', contactInfo.phone || 'Not found');
  console.log('Website:', contactInfo.website || 'Not found');
  console.log('Address:', contactInfo.address || 'Not found');
  console.log('Full contact info:', contactInfo);
  
  return contactInfo;
};