// Skills extraction debugger
window.debugSkillsExtraction = function() {
  console.log('=== SKILLS DEBUG ===');
  
  // Find skills section
  const skillsSection = document.querySelector('#skills')?.closest('section');
  if (!skillsSection) {
    console.log('Skills section not found!');
    return;
  }
  
  console.log('Skills section found. HTML preview:');
  console.log(skillsSection.innerHTML.substring(0, 1000));
  
  // Check various selectors
  const selectors = [
    '.mr1.t-bold span[aria-hidden="true"]',
    '.pvs-entity__supplementary-info span[aria-hidden="true"]',
    '[data-field="skill_name"]',
    'div[data-field="skill_card_skill_topic"] span[aria-hidden="true"]',
    '.pvs-list__item--three-column span[aria-hidden="true"]',
    '.pvs-entity .mr1.hoverable-link-text span[aria-hidden="true"]',
    'ul[aria-label*="skills"] li span[aria-hidden="true"]',
    '.pv-skill-category-entity__name span',
    // More generic
    '.t-bold span',
    '.hoverable-link-text span',
    'li .t-bold'
  ];
  
  selectors.forEach(selector => {
    try {
      const elements = skillsSection.querySelectorAll(selector);
      if (elements.length > 0) {
        console.log(`\nSelector: ${selector}`);
        console.log(`Found ${elements.length} elements:`);
        elements.forEach((el, idx) => {
          if (idx < 10) { // Show first 10
            console.log(`  ${idx + 1}. "${el.textContent.trim()}"`);
          }
        });
      }
    } catch (e) {
      console.log(`Selector ${selector} failed: ${e.message}`);
    }
  });
  
  // Look for text that might be skills
  console.log('\n=== All bold text in skills section ===');
  const boldTexts = skillsSection.querySelectorAll('.t-bold');
  boldTexts.forEach((el, idx) => {
    const text = el.textContent.trim();
    if (text && !text.match(/^\d+$/) && text.length > 2 && text.length < 50) {
      console.log(`Bold text ${idx}: "${text}"`);
    }
  });
  
  // Check for "Top skills" section specifically
  console.log('\n=== Looking for Top Skills ===');
  const topSkillsHeader = Array.from(skillsSection.querySelectorAll('*')).find(el => 
    el.textContent.includes('Top skills')
  );
  if (topSkillsHeader) {
    console.log('Found Top Skills header');
    const parent = topSkillsHeader.parentElement?.parentElement;
    if (parent) {
      console.log('Top Skills parent HTML:');
      console.log(parent.innerHTML.substring(0, 1000));
      
      // Look for bullet points or list items near Top Skills
      const listItems = parent.querySelectorAll('li, .pvs-list__item, .pv2');
      console.log(`\nFound ${listItems.length} list items near Top Skills:`);
      listItems.forEach((item, idx) => {
        console.log(`${idx + 1}. "${item.textContent.trim()}"`);
      });
    }
  }
  
  // Look for skills with bullet separators
  console.log('\n=== Looking for skills with bullet separators ===');
  const bulletTexts = Array.from(skillsSection.querySelectorAll('*')).filter(el => 
    el.textContent.includes('•') || el.textContent.includes('·')
  );
  bulletTexts.forEach((el, idx) => {
    if (idx < 5) {
      console.log(`Bullet text ${idx}: "${el.textContent.trim()}"`);
    }
  });
};

console.log('Skills debugger loaded. Run window.debugSkillsExtraction() to debug');