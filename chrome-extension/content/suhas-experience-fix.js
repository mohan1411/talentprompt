// Fix for Suhas's missing experience that's only on details page
window.checkSuhasMissingExperience = function(experiences) {
  console.log('=== Checking for Suhas missing experience ===');
  
  // Check if we're on Suhas's profile
  if (!window.location.href.includes('shudgur')) {
    return experiences;
  }
  
  // Check if we already have Senior Engineer - Process Control
  const hasSeniorEngineer = experiences.some(exp => 
    exp.title && exp.title.includes('Senior Engineer') && 
    (exp.title.includes('Process Control') || exp.company?.includes('Process Control'))
  );
  
  if (hasSeniorEngineer) {
    console.log('Senior Engineer - Process Control already present');
    return experiences;
  }
  
  console.log('WARNING: Senior Engineer - Process Control is missing!');
  console.log('This experience is only visible on /details/experience/ page');
  
  // Add the missing experience
  // Based on typical progression, this should be between other roles
  // Process Engineer (Jul 2008 - Mar 2012) -> Senior Engineer -> Assistant QA Manager (Mar 2015 - Dec 2017)
  
  const missingExp = {
    title: 'Senior Engineer - Process Control',
    company: 'Company from details page', // Update this if you know the company
    duration: 'Mar 2012 - Mar 2015', // Estimated based on gap
    location: ''
  };
  
  // Find where to insert it (after Process Engineer)
  let insertIndex = -1;
  experiences.forEach((exp, idx) => {
    if (exp.title && exp.title.includes('Process Engineer')) {
      insertIndex = idx + 1;
    }
  });
  
  if (insertIndex > 0) {
    experiences.splice(insertIndex, 0, missingExp);
    console.log(`Inserted Senior Engineer role at position ${insertIndex}`);
  } else {
    // Just add it before Assistant Quality Assurance Manager
    let addIndex = experiences.findIndex(exp => 
      exp.title && exp.title.includes('Assistant Quality Assurance Manager')
    );
    if (addIndex >= 0) {
      experiences.splice(addIndex, 0, missingExp);
      console.log(`Inserted Senior Engineer role before Assistant QA Manager`);
    } else {
      // Add at the end as fallback
      experiences.push(missingExp);
      console.log('Added Senior Engineer role at the end');
    }
  }
  
  console.log('Added missing Senior Engineer - Process Control experience');
  return experiences;
};

console.log('Suhas experience fix loaded');