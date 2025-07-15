// Log experience details for debugging
window.logExperienceDetails = function(experiences) {
  if (!experiences || !Array.isArray(experiences)) {
    console.log('No experiences to log');
    return;
  }
  
  console.log('=== Experience Details ===');
  console.log(`Total positions: ${experiences.length}`);
  
  experiences.forEach((exp, index) => {
    console.log(`\nPosition ${index + 1}:`);
    console.log(`  Title: ${exp.title || '[No title]'}`);
    console.log(`  Company: ${exp.company || '[No company]'}`);
    console.log(`  Duration: ${exp.duration || '[No duration]'}`);
    console.log(`  Location: ${exp.location || '[No location]'}`);
    console.log(`  Employment Type: ${exp.employment_type || '[Not specified]'}`);
    
    // Check if this looks like a valid experience entry
    if (!exp.duration) {
      console.log('  ⚠️  WARNING: No duration found for this position');
    }
  });
  
  console.log('\n=== End Experience Details ===');
};