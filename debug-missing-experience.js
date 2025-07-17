// Paste this directly in the console to debug missing experience

(() => {
  console.log('=== SEARCHING FOR SENIOR ENGINEER - PROCESS CONTROL ===');
  
  const expSection = document.querySelector('#experience')?.closest('section');
  if (!expSection) {
    console.log('Experience section not found!');
    return;
  }
  
  // Search all text in experience section
  const fullText = expSection.innerText || expSection.textContent || '';
  
  // Look for "Senior Engineer"
  if (fullText.includes('Senior Engineer')) {
    console.log('✓ Found "Senior Engineer" in experience section');
    
    // Find where it appears
    const index = fullText.indexOf('Senior Engineer');
    const snippet = fullText.substring(index - 50, index + 200);
    console.log('Context around "Senior Engineer":');
    console.log(snippet);
  } else {
    console.log('✗ "Senior Engineer" NOT found in experience section');
  }
  
  // Look for "Process Control"
  if (fullText.includes('Process Control')) {
    console.log('\n✓ Found "Process Control" in experience section');
    
    const index = fullText.indexOf('Process Control');
    const snippet = fullText.substring(index - 50, index + 200);
    console.log('Context around "Process Control":');
    console.log(snippet);
  } else {
    console.log('✗ "Process Control" NOT found in experience section');
  }
  
  // Look for all list items
  console.log('\n=== ALL EXPERIENCE LIST ITEMS ===');
  const allLI = expSection.querySelectorAll('li');
  console.log(`Total list items: ${allLI.length}`);
  
  // Find items with "Engineer" in them
  let engineerCount = 0;
  allLI.forEach((li, idx) => {
    const text = li.textContent || '';
    if (text.includes('Engineer')) {
      engineerCount++;
      console.log(`\n--- LI #${idx} contains "Engineer" ---`);
      
      // Get first few spans
      const spans = li.querySelectorAll('span[aria-hidden="true"]');
      console.log(`First 5 spans:`);
      for (let i = 0; i < Math.min(5, spans.length); i++) {
        console.log(`  ${i}: "${spans[i].textContent.trim()}"`);
      }
      
      // Check if it's nested
      const parentLI = li.parentElement?.closest('li');
      if (parentLI && parentLI !== li) {
        console.log('⚠️ This is a NESTED list item (sub-role)');
      }
    }
  });
  
  console.log(`\nTotal items with "Engineer": ${engineerCount}`);
  
  // Look specifically in grouped experiences
  console.log('\n=== CHECKING GROUPED EXPERIENCES ===');
  const groupedULs = expSection.querySelectorAll('li > ul');
  console.log(`Found ${groupedULs.length} grouped experience sections`);
  
  groupedULs.forEach((ul, idx) => {
    const parentLI = ul.closest('li');
    const companyText = parentLI.querySelector('span[aria-hidden="true"]')?.textContent || 'Unknown';
    console.log(`\nGroup ${idx + 1} - Company: ${companyText}`);
    
    const subRoles = ul.querySelectorAll('li');
    console.log(`  Sub-roles: ${subRoles.length}`);
    
    subRoles.forEach((role, roleIdx) => {
      const roleTitle = role.querySelector('span[aria-hidden="true"]')?.textContent || '';
      console.log(`    ${roleIdx + 1}. ${roleTitle}`);
      
      if (roleTitle.includes('Senior Engineer') || roleTitle.includes('Process Control')) {
        console.log('    ⭐ THIS IS THE MISSING ROLE!');
      }
    });
  });
})();