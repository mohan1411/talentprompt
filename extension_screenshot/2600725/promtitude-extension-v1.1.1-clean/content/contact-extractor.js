// Extract contact information from LinkedIn profile
window.extractContactInfo = async function() {
  try {
    
    const contactInfo = {
      email: '',
      phone: '',
      linkedin: window.location.href.split('?')[0],
      website: '',
      address: ''
    };
    
    // Quick DOM check
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
          break;
        }
      } catch (e) {
        // Some selectors might not be valid, continue
      }
    }
    
    if (!contactButton) {
    }
    
    if (contactButton) {
      // Contact button found
      
      // Check if contact info is locked/premium
      const isLocked = contactButton.querySelector('[data-test-icon="lock"]') || 
                      contactButton.querySelector('.premium-icon') ||
                      contactButton.textContent.toLowerCase().includes('unlock');
      
      if (isLocked) {
      }
      
      // First, close any messaging modals that might be open
      const messagingModals = document.querySelectorAll('.msg-overlay-conversation-bubble, [class*="msg-overlay"]');
      messagingModals.forEach(modal => {
        const closeBtn = modal.querySelector('button[aria-label*="Close"]') || 
                        modal.querySelector('button[data-control-name="overlay.close"]');
        if (closeBtn) closeBtn.click();
      });
      
      // Check if contact modal is already open - exclude messaging modals
      let contactModal = null;
      
      // First try specific contact modal selectors
      const modalSelectors = [
        '.pv-profile-modal__content',
        '.pv-overlay__content',
        '[aria-label*="contact info" i]',
        '[aria-label*="Contact information" i]',
        '.artdeco-modal__content:has(.ci-vanity-url)',
        '.artdeco-modal__content:has(section[class*="ci-email"])',
        '[data-test-modal]:has(a[href^="mailto:"])'
      ];
      
      for (const selector of modalSelectors) {
        try {
          const modal = document.querySelector(selector);
          if (modal) {
            // Verify it's not a messaging modal
            const modalText = modal.textContent || '';
            if (!modalText.includes('msg-overlay') && 
                !modalText.includes('conversation-bubble')) {
              contactModal = modal;
              break;
            }
          }
        } catch (e) {
          // Some selectors might fail
        }
      }
      
      // If still not found, check generic dialog but verify content
      if (!contactModal) {
        const dialogs = document.querySelectorAll('[role="dialog"]');
        for (const dialog of dialogs) {
          const dialogText = dialog.textContent || '';
          // Check if it contains contact-related content
          if ((dialogText.includes('@') || 
               dialogText.toLowerCase().includes('email') ||
               dialogText.toLowerCase().includes('phone') ||
               dialogText.toLowerCase().includes('contact')) &&
              !dialogText.includes('msg-overlay')) {
            contactModal = dialog;
            break;
          }
        }
      }
      
      if (!contactModal) {
        
        // Close all modals first to ensure clean state
        const allModals = document.querySelectorAll('[role="dialog"], .artdeco-modal, .msg-overlay-container');
        allModals.forEach(modal => {
          const closeBtn = modal.querySelector('button[aria-label*="Close"]') || 
                          modal.querySelector('button[aria-label*="Dismiss"]');
          if (closeBtn) {
            closeBtn.click();
          }
        });
        
        // Wait a bit for modals to close
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // Click the button to open modal
        contactButton.click();
        
        // Wait for modal to appear with multiple attempts
        for (let i = 0; i < 5; i++) {
          await new Promise(resolve => setTimeout(resolve, 500));
          
          // Try specific contact modal selectors
          for (const selector of modalSelectors) {
            try {
              const modal = document.querySelector(selector);
              if (modal) {
                const modalText = modal.textContent || '';
                if (!modalText.includes('msg-overlay') && 
                    !modalText.includes('conversation-bubble')) {
                  contactModal = modal;
                  break;
                }
              }
            } catch (e) {
              // Continue
            }
          }
          
          if (contactModal) break;
          
          // Check generic dialogs
          if (!contactModal) {
            const dialogs = document.querySelectorAll('[role="dialog"]');
            for (const dialog of dialogs) {
              const dialogText = dialog.textContent || '';
              if ((dialogText.includes('@') || 
                   dialogText.toLowerCase().includes('email') ||
                   dialogText.toLowerCase().includes('phone') ||
                   dialogText.toLowerCase().includes('contact')) &&
                  !dialogText.includes('msg-overlay')) {
                contactModal = dialog;
                break;
              }
            }
          }
          
          if (contactModal) {
            break;
          }
        }
      } else {
      }
      
      if (contactModal) {
        
        // Log modal content for debugging
        
        // Enhanced modal debugging
        
        // Log all text content in modal
        const allText = contactModal.innerText || contactModal.textContent || '';
        
        // Check for email patterns in the entire modal
        const emailPattern = /[\w.-]+@[\w.-]+\.\w+/g;
        const allEmailMatches = allText.match(emailPattern);
        if (allEmailMatches) {
        } else {
        }
        
        // Log all sections in modal
        const sections = contactModal.querySelectorAll('section');
        sections.forEach((section, idx) => {
          const sectionText = section.innerText || section.textContent || '';
          // Process section
        });
        
        // Extract email - try multiple methods
        const emailSelectors = [
          // Most common patterns
          'a[href^="mailto:"]',
          'a[href*="mailto:"]',
          
          // Section-based selectors
          'section:has(svg[type="email-icon"]) a',
          'section:has(path[d*="M3 8l7"]) a', // Email icon path
          'div:has(svg[aria-label*="Email"]) + div a',
          
          // Text-based selectors
          'section:contains("Email") a',
          'div:contains("Email") + div a',
          
          // Class-based selectors
          '.pv-contact-info__contact-type a',
          '.pv-contact-info__ci-container a',
          'section[class*="email"] a',
          '[data-field="email"] a',
          '.ci-email a'
        ];
        
        let emailFound = false;
        for (const selector of emailSelectors) {
          try {
            const emailElements = contactModal.querySelectorAll(selector);
            
            emailElements.forEach(element => {
              if (element.href && element.href.includes('mailto:')) {
                contactInfo.email = element.href.replace('mailto:', '').trim();
                emailFound = true;
              }
            });
            
            if (emailFound) break;
          } catch (e) {
            // Some selectors might fail
          }
        }
        
        // If no email link found, look for email in text content
        if (!contactInfo.email) {
          
          // Look for sections that might contain email
          const sections = contactModal.querySelectorAll('section');
          sections.forEach((section, idx) => {
            const text = section.textContent || '';
            
            // Look for email pattern
            const emailMatch = text.match(/[\w.-]+@[\w.-]+\.\w+/);
            if (emailMatch && !contactInfo.email) {
              contactInfo.email = emailMatch[0];
            }
          });
        }
        
        // Debug: Log all links in modal
        if (!contactInfo.email) {
          const allLinks = contactModal.querySelectorAll('a');
          allLinks.forEach((link, idx) => {
              href: link.href,
              text: link.textContent.trim(),
              parent: link.parentElement?.tagName
            });
          });
          
          // Use advanced email finder
          if (window.findEmailInModal) {
            window.findEmailInModal(contactModal);
          }
        }
        
        // If still no email, it might be plain text (not a link)
        if (!contactInfo.email) {
          
          // Look for divs that contain email addresses
          const allDivs = contactModal.querySelectorAll('div');
          allDivs.forEach((div, idx) => {
            const text = div.textContent || '';
            const emailMatch = text.match(/[\w.-]+@[\w.-]+\.\w+/);
            
            if (emailMatch && div.children.length === 0) { // Only leaf nodes
              if (!contactInfo.email) {
                contactInfo.email = emailMatch[0];
              }
            }
          });
        }
        
        // Try the direct email extractor as a last resort
        if (!contactInfo.email && window.extractEmailDirect) {
          const directEmail = window.extractEmailDirect(contactModal);
          if (directEmail) {
            contactInfo.email = directEmail;
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
        const closeButtonSelectors = [
          'button[aria-label*="Dismiss"]',
          'button[data-test-modal-close-btn]',
          'button[aria-label*="Close"]',
          '.artdeco-modal__dismiss',
          'button[type="cancel"]',
          'button.artdeco-button--circle',
          'button[data-control-name="overlay.close"]'
        ];
        
        let closeButton = null;
        for (const selector of closeButtonSelectors) {
          closeButton = contactModal.querySelector(selector);
          if (closeButton) {
            break;
          }
        }
        
        if (closeButton) {
          closeButton.click();
          // Wait for modal to close
          await new Promise(resolve => setTimeout(resolve, 300));
        } else {
          // Try clicking outside the modal or pressing Escape
          document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', keyCode: 27 }));
          await new Promise(resolve => setTimeout(resolve, 300));
        }
      } else {
      }
    } else {
      
      // Debug: Look for all links and buttons that might be contact info
      
      // Check all links
      const allLinks = document.querySelectorAll('a');
      allLinks.forEach(link => {
        const text = link.textContent.trim().toLowerCase();
        const href = link.href || '';
        if (text.includes('contact') || href.includes('contact')) {
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
    
  // Method 4: Try finding email in specific profile sections
  if (!contactInfo.email) {
    
    // Look in the entire profile for email-like patterns
    const profileMain = document.querySelector('main') || document.body;
    const allText = profileMain.innerText || profileMain.textContent || '';
    
    // More permissive email regex
    const emailMatches = allText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g);
    if (emailMatches) {
      // Filter out common non-personal emails
      const personalEmail = emailMatches.find(email => 
        !email.includes('linkedin.com') && 
        !email.includes('example.com') &&
        !email.includes('support@') &&
        !email.includes('noreply@') &&
        !email.includes('@2x.png') && // Avoid image names
        !email.includes('@3x.png') &&
        email.length < 50
      );
      
      if (personalEmail) {
        contactInfo.email = personalEmail;
      }
    }
  }
  
  // Final summary
  
  // Ensure we always return an object with email property
  const result = {
    email: contactInfo.email || '',
    phone: contactInfo.phone || '',
    linkedin: contactInfo.linkedin || window.location.href.split('?')[0],
    website: contactInfo.website || '',
    address: contactInfo.address || ''
  };
  
  return result;
  
  } catch (error) {
    
    // Return empty contact info to prevent complete failure
    return {
      email: '',
      phone: '',
      linkedin: window.location.href.split('?')[0],
      website: '',
      address: ''
    };
  }
};