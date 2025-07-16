// Comprehensive experience calculation tracer
window.traceExperienceCalculation = function() {
  console.log('%c🔍 EXPERIENCE CALCULATION TRACE', 'color: white; background: red; font-size: 16px; padding: 5px;');
  
  // Step 1: Raw DOM extraction
  console.log('\n%c1. RAW DOM EXTRACTION', 'color: white; background: blue; font-size: 14px; padding: 3px;');
  
  const expSection = document.querySelector('#experience')?.closest('section');
  if (!expSection) {
    console.error('❌ No experience section found!');
    return;
  }
  
  const allExperienceTexts = [];
  const expList = expSection.querySelector('ul.pvs-list') || expSection.querySelector('ul');
  
  if (expList) {
    const items = expList.querySelectorAll('li');
    console.log(`Found ${items.length} experience items in DOM`);
    
    items.forEach((item, idx) => {
      const texts = [];
      const spans = item.querySelectorAll('span[aria-hidden="true"]');
      
      // Check if it's a grouped experience
      const isGrouped = !!item.querySelector('ul.pvs-list');
      
      spans.forEach(span => {
        if (!span.closest('.visually-hidden')) {
          const text = span.textContent.trim();
          if (text && text.length > 1) {
            // Only add if not from sub-list (for grouped experiences)
            if (!isGrouped || !span.closest('ul.pvs-list')) {
              texts.push(text);
            }
          }
        }
      });
      
      allExperienceTexts.push({
        index: idx,
        isGrouped: isGrouped,
        texts: texts,
        raw: item.innerText.substring(0, 200)
      });
      
      console.log(`\nItem ${idx + 1} ${isGrouped ? '(GROUPED)' : ''}:`);
      console.log('Texts:', texts.slice(0, 5));
      
      // If grouped, also get sub-items
      if (isGrouped) {
        const subList = item.querySelector('ul.pvs-list');
        const subItems = subList.querySelectorAll('li');
        console.log(`  Has ${subItems.length} sub-roles`);
      }
    });
  }
  
  // Step 2: Run extraction
  console.log('\n%c2. EXTRACTION PROCESS', 'color: white; background: green; font-size: 14px; padding: 3px;');
  
  let extractedData = null;
  if (window.extractUltraCleanProfile) {
    extractedData = window.extractUltraCleanProfile();
    console.log(`Extracted ${extractedData.experience.length} experiences`);
    
    extractedData.experience.forEach((exp, idx) => {
      console.log(`\n📋 Experience ${idx + 1}:`);
      console.log(`   Title: "${exp.title}"`);
      console.log(`   Company: "${exp.company}"`);
      console.log(`   Duration: "${exp.duration}"`);
      
      // Check if this looks like a company total
      const patterns = {
        'Title = Company': exp.title === exp.company,
        'Company has duration': exp.company?.includes(' at ') || exp.company?.includes(' · '),
        'Title has duration': exp.title?.includes(' at ') || exp.title?.includes(' · '),
        'Duration has company': exp.duration?.includes(' at ') || exp.duration?.startsWith(exp.company)
      };
      
      const suspiciousPatterns = Object.entries(patterns).filter(([_, value]) => value);
      if (suspiciousPatterns.length > 0) {
        console.log(`   ⚠️  SUSPICIOUS PATTERNS:`, suspiciousPatterns.map(p => p[0]).join(', '));
      }
    });
  }
  
  // Step 3: Show filtering
  console.log('\n%c3. FILTERING PROCESS', 'color: white; background: orange; font-size: 14px; padding: 3px;');
  
  if (window.filterCompanyTotals && extractedData) {
    const beforeCount = extractedData.experience.length;
    const filtered = window.filterCompanyTotals(extractedData.experience);
    const afterCount = filtered.length;
    
    console.log(`Before filtering: ${beforeCount} experiences`);
    console.log(`After filtering: ${afterCount} experiences`);
    console.log(`Removed: ${beforeCount - afterCount} company totals`);
  }
  
  // Step 4: Detailed calculation
  console.log('\n%c4. CALCULATION BREAKDOWN', 'color: white; background: purple; font-size: 14px; padding: 3px;');
  
  if (window.calculateTotalExperienceAdvanced && extractedData) {
    console.log('\n--- Running Advanced Calculator with Extra Logging ---');
    
    // Temporarily enhance logging
    const originalLog = console.log;
    const calculationLog = [];
    console.log = function(...args) {
      calculationLog.push(args.join(' '));
      originalLog.apply(console, args);
    };
    
    const result = window.calculateTotalExperienceAdvanced(extractedData.experience);
    
    // Restore original logging
    console.log = originalLog;
    
    console.log(`\n%cFINAL CALCULATED RESULT: ${result} years`, 'color: white; background: red; font-size: 16px; padding: 5px;');
    
    // Analyze the calculation log
    const addedMonths = calculationLog.filter(log => log.includes('Added') && log.includes('months'));
    const skipped = calculationLog.filter(log => log.includes('SKIPPING'));
    
    console.log('\n📊 Calculation Summary:');
    console.log(`   Experiences that contributed months: ${addedMonths.length}`);
    console.log(`   Experiences skipped: ${skipped.length}`);
    
    // Show what was added
    console.log('\n✅ COUNTED EXPERIENCES:');
    addedMonths.forEach((log, idx) => {
      const monthsMatch = log.match(/(\d+)\s*months/);
      if (monthsMatch) {
        console.log(`   ${idx + 1}. ${monthsMatch[1]} months`);
      }
    });
    
    // Calculate total from log
    let logTotal = 0;
    addedMonths.forEach(log => {
      const monthsMatch = log.match(/(\d+)\s*months/);
      if (monthsMatch) {
        logTotal += parseInt(monthsMatch[1]);
      }
    });
    console.log(`\n   Total months from log: ${logTotal} (${(logTotal/12).toFixed(1)} years)`);
  }
  
  // Step 5: Specific ANZ analysis
  console.log('\n%c5. ANZ SPECIFIC ANALYSIS', 'color: white; background: brown; font-size: 14px; padding: 3px;');
  
  if (extractedData) {
    const anzExperiences = extractedData.experience.filter(exp => 
      exp.company?.includes('ANZ') || exp.title?.includes('ANZ')
    );
    
    console.log(`Found ${anzExperiences.length} ANZ-related experiences:`);
    anzExperiences.forEach((exp, idx) => {
      console.log(`\n${idx + 1}. ANZ Experience:`);
      console.log(`   Title: "${exp.title}"`);
      console.log(`   Company: "${exp.company}"`);
      console.log(`   Duration: "${exp.duration}"`);
      
      // Try to parse duration
      if (exp.duration) {
        const yearsMatch = exp.duration.match(/(\d+)\s*yrs?/);
        const monthsMatch = exp.duration.match(/(\d+)\s*mos?/);
        const years = yearsMatch ? parseInt(yearsMatch[1]) : 0;
        const months = monthsMatch ? parseInt(monthsMatch[1]) : 0;
        const totalMonths = (years * 12) + months;
        console.log(`   Parsed: ${years} years + ${months} months = ${totalMonths} months`);
      }
    });
    
    // Check for the problematic "ANZ · 14 yrs 7 mos" entry
    const problematicEntry = anzExperiences.find(exp => 
      exp.duration?.includes('14 yrs') || 
      exp.company?.includes('14 yrs') ||
      exp.title?.includes('14 yrs')
    );
    
    if (problematicEntry) {
      console.log('\n🚨 FOUND PROBLEMATIC ENTRY WITH 14 YEARS:');
      console.log(JSON.stringify(problematicEntry, null, 2));
    }
  }
  
  console.log('\n%c🔍 END TRACE', 'color: white; background: red; font-size: 16px; padding: 5px;');
};

// Auto-run on the problematic profile
if (window.location.href.includes('anil-narasimhappa')) {
  console.log('%c🎯 AUTO-RUNNING TRACE FOR ANIL PROFILE', 'color: yellow; background: black; font-size: 14px; padding: 5px;');
  setTimeout(() => {
    window.traceExperienceCalculation();
  }, 3500);
}