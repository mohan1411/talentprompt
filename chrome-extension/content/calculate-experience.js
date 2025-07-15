// Calculate total years of experience from experience array
window.calculateTotalExperience = function(experiences) {
  if (!experiences || !Array.isArray(experiences)) return 0;
  
  let totalMonths = 0;
  
  experiences.forEach(exp => {
    if (!exp.duration) return;
    
    const duration = exp.duration;
    console.log('Processing duration:', duration);
    
    // Extract years - handle various formats
    const yearsMatch = duration.match(/(\d+)\s*(?:yrs?|years?)/i);
    const years = yearsMatch ? parseInt(yearsMatch[1]) : 0;
    
    // Extract months - handle various formats
    const monthsMatch = duration.match(/(\d+)\s*(?:mos?|months?)/i);
    const months = monthsMatch ? parseInt(monthsMatch[1]) : 0;
    
    const expMonths = (years * 12) + months;
    console.log(`Duration "${duration}" = ${years} years + ${months} months = ${expMonths} total months`);
    
    totalMonths += expMonths;
  });
  
  const totalYears = Math.round(totalMonths / 12);
  console.log(`Total experience: ${totalMonths} months = ${totalYears} years`);
  
  return totalYears;
};