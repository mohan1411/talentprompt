// Final verification to ensure no irrelevant content
window.verifyCleanData = function(profileData) {
  console.log('=== Final Data Verification ===');
  
  const issues = [];
  const irrelevantPatterns = [
    /\d+\s*followers?/i,
    /\d+\s*connections?/i,
    /endorsed by/i,
    /\d+\s*endorsements?/i,
    /Narendra Modi/i,
    /Jeff Weiner/i,
    /Prime Minister/i,
    /newsletter/i,
    /· 3rd|· 2nd|· 1st/i
  ];
  
  // Check full_text
  if (profileData.full_text) {
    irrelevantPatterns.forEach(pattern => {
      if (pattern.test(profileData.full_text)) {
        issues.push(`Found irrelevant content in full_text: ${pattern}`);
      }
    });
  }
  
  // Check experience
  if (profileData.experience) {
    profileData.experience.forEach((exp, idx) => {
      Object.entries(exp).forEach(([key, value]) => {
        if (value && typeof value === 'string') {
          irrelevantPatterns.forEach(pattern => {
            if (pattern.test(value)) {
              issues.push(`Found irrelevant content in experience[${idx}].${key}: ${pattern}`);
            }
          });
        }
      });
    });
  }
  
  // Log results
  if (issues.length > 0) {
    console.error('❌ VERIFICATION FAILED - Irrelevant content found:');
    issues.forEach(issue => console.error('  - ' + issue));
  } else {
    console.log('✅ VERIFICATION PASSED - No irrelevant content found');
  }
  
  console.log('Final stats:');
  console.log('- Name:', profileData.name || 'Not found');
  console.log('- Email:', profileData.email || 'Not found');
  console.log('- Experience count:', profileData.experience?.length || 0);
  console.log('- Years of experience:', profileData.years_experience || 0);
  console.log('- Full text length:', profileData.full_text?.length || 0);
  
  return issues.length === 0;
};