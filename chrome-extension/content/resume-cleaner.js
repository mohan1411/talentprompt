// Clean resume text to only include relevant information
window.cleanResumeText = function(experiences, education, skills) {
  const parts = [];
  
  // Add experience section
  if (experiences && experiences.length > 0) {
    parts.push('EXPERIENCE\n');
    
    experiences.forEach(exp => {
      if (exp.title) {
        parts.push(exp.title);
      }
      if (exp.company) {
        let companyLine = exp.company;
        if (exp.employment_type && !exp.company.includes(exp.employment_type)) {
          companyLine += ` · ${exp.employment_type}`;
        }
        parts.push(companyLine);
      }
      if (exp.duration) {
        parts.push(exp.duration);
      }
      if (exp.location) {
        parts.push(exp.location);
      }
      if (exp.description && exp.description.length > 10) {
        parts.push(exp.description);
      }
      parts.push(''); // Empty line between experiences
    });
  }
  
  // Add education section
  if (education && education.length > 0) {
    parts.push('\nEDUCATION\n');
    
    education.forEach(edu => {
      if (edu.school || edu.raw_text) {
        parts.push(edu.school || edu.raw_text);
      }
      if (edu.degree && edu.field) {
        parts.push(`${edu.degree}, ${edu.field}`);
      } else if (edu.degree) {
        parts.push(edu.degree);
      }
      if (edu.dates) {
        parts.push(edu.dates);
      }
      parts.push(''); // Empty line between education items
    });
  }
  
  // Add skills section
  if (skills && skills.length > 0) {
    parts.push('\nSKILLS\n');
    parts.push(skills.join(', '));
  }
  
  return parts.join('\n').trim();
};