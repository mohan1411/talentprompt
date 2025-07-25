// Debug script to find all experiences on the page
window.debugAllExperiences = function() {
  console.log('=== DEBUG ALL EXPERIENCES ===');
  
  const expSection = document.querySelector('#experience')?.closest('section');
  if (!expSection) {
    console.log('Experience section not found!');
    return;
  }
  
  console.log('Experience section found. Looking for all text containing job titles...');
  
  // Find all list items in experience section
  const allListItems = expSection.querySelectorAll('li');
  console.log(`Found ${allListItems.length} list items in experience section`);
  
  // Look for "Senior Engineer" specifically
  console.log('\n=== Searching for "Senior Engineer" ===');
  let foundCount = 0;
  
  allListItems.forEach((item, idx) => {
    const itemText = item.textContent || '';
    if (itemText.includes('Senior Engineer') || itemText.includes('Process Control')) {
      foundCount++;
      console.log(`\n--- Found in item ${idx} ---`);
      console.log('Full text:', itemText.trim().substring(0, 300));
      
      // Get all spans in this item
      const spans = item.querySelectorAll('span[aria-hidden="true"]');
      console.log(`Spans in this item (${spans.length}):`);
      spans.forEach((span, spanIdx) => {
        console.log(`  ${spanIdx}: "${span.textContent.trim()}"`);
      });
      
      // Check if it's in a grouped experience
      const parentUL = item.closest('ul');
      const grandparentLI = parentUL ? parentUL.closest('li') : null;
      if (grandparentLI && grandparentLI !== item) {
        console.log('This is a SUB-ROLE in a grouped experience!');
        console.log('Parent company item text:', grandparentLI.textContent.substring(0, 200));
      }
    }
  });
  
  if (foundCount === 0) {
    console.log('No items found containing "Senior Engineer" or "Process Control"');
  }
  
  // Look for all roles with "Engineer" in title
  console.log('\n=== All Engineer roles ===');
  const engineerRoles = [];
  
  allListItems.forEach((item) => {
    const spans = item.querySelectorAll('span[aria-hidden="true"]');
    const firstSpan = spans[0]?.textContent.trim() || '';
    
    if (firstSpan.includes('Engineer')) {
      engineerRoles.push({
        title: firstSpan,
        fullText: item.textContent.trim().substring(0, 200)
      });
    }
  });
  
  console.log(`Found ${engineerRoles.length} Engineer roles:`);
  engineerRoles.forEach((role, idx) => {
    console.log(`${idx + 1}. ${role.title}`);
  });
};

console.log('Experience debugger loaded. Run window.debugAllExperiences()');