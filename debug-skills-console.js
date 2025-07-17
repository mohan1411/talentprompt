// Paste this directly into the browser console on Suhas's LinkedIn profile

(() => {
  console.log('=== SKILLS DEBUG ===');
  
  const skillsSection = document.querySelector('#skills')?.closest('section');
  if (!skillsSection) {
    console.log('Skills section not found!');
    return;
  }
  
  console.log('Skills section found.');
  
  // Look for "Top skills" text
  console.log('\n=== Looking for Top Skills ===');
  const allElements = skillsSection.querySelectorAll('*');
  let topSkillsElement = null;
  
  for (let el of allElements) {
    if (el.textContent && el.textContent.includes('Top skills') && el.textContent.length < 100) {
      topSkillsElement = el;
      console.log('Found element with "Top skills":', el.tagName, el.className);
      console.log('Text:', el.textContent);
      break;
    }
  }
  
  if (topSkillsElement) {
    // Look for the container with all skills
    let current = topSkillsElement;
    for (let i = 0; i < 5; i++) {
      current = current.parentElement;
      if (current && current.textContent.includes('•')) {
        console.log(`\nParent level ${i + 1} contains bullet points:`);
        console.log('HTML:', current.innerHTML.substring(0, 500));
        console.log('Text:', current.textContent.trim().substring(0, 200));
        
        // Look for specific skill text
        const skillTexts = current.textContent.match(/[^•]+/g);
        if (skillTexts) {
          console.log('\nSkills found by splitting on bullets:');
          skillTexts.forEach((skill, idx) => {
            const trimmed = skill.trim();
            if (trimmed && trimmed.length > 1 && trimmed.length < 50) {
              console.log(`${idx + 1}. "${trimmed}"`);
            }
          });
        }
        break;
      }
    }
  }
  
  // Look for any text with bullets
  console.log('\n=== All elements with bullet separators ===');
  const bulletElements = Array.from(allElements).filter(el => 
    el.textContent.includes('•') && el.textContent.length < 200
  );
  
  bulletElements.slice(0, 5).forEach((el, idx) => {
    console.log(`\n${idx + 1}. ${el.tagName}.${el.className}:`);
    console.log(el.textContent.trim());
  });
  
  // Try to find skills by common patterns
  console.log('\n=== Searching for skill patterns ===');
  const potentialSkills = new Set();
  
  // Look for these specific skills
  const targetSkills = ['Kaizen', 'Strategy', 'Employee Training', 'Project Management'];
  targetSkills.forEach(skill => {
    const found = Array.from(allElements).find(el => 
      el.textContent.includes(skill) && el.textContent.length < 100
    );
    if (found) {
      console.log(`Found "${skill}" in:`, found.tagName, found.textContent.trim());
      potentialSkills.add(skill);
    }
  });
  
  console.log('\n=== Summary ===');
  console.log('Target skills found:', Array.from(potentialSkills));
})();