// Aggressive filter to clean LinkedIn profile data
window.aggressiveClean = {
  // Check if text contains irrelevant content
  isIrrelevant: function(text) {
    if (!text) return true;
    
    const irrelevantPatterns = [
      /\d+\s*followers?/i,
      /\d+\s*connections?/i,
      /endorsed by/i,
      /\d+\s*endorsements?/i,
      /people also viewed/i,
      /people you may know/i,
      /promoted/i,
      /· 3rd/i,
      /· 2nd/i,
      /· 1st/i,
      /newsletter/i,
      /subscribe/i,
      /Prime Minister of India/i,
      /Narendra Modi/i,
      /Jeff Weiner/i,
      /Bill Gates/i,
      /The world of startups/i
    ];
    
    return irrelevantPatterns.some(pattern => pattern.test(text));
  },
  
  // Clean experience item
  cleanExperience: function(exp) {
    if (!exp) return null;
    
    // Check if this is a real experience entry
    if (this.isIrrelevant(exp.title) || this.isIrrelevant(exp.company)) {
      return null;
    }
    
    // Clean the description
    if (exp.description) {
      // Remove endorsement mentions from description
      exp.description = exp.description
        .replace(/Endorsed by.*?(?:\.|$)/gi, '')
        .replace(/\d+\s*endorsements?/gi, '')
        .replace(/Skills:.*?(?:\n|$)/gi, '')
        .trim();
    }
    
    return exp;
  },
  
  // Clean education item
  cleanEducation: function(edu) {
    if (!edu) return null;
    
    // Check if this is a real education entry
    if (this.isIrrelevant(edu.school) || this.isIrrelevant(edu.degree)) {
      return null;
    }
    
    return edu;
  },
  
  // Filter skills to remove endorsed counts
  cleanSkills: function(skills) {
    if (!skills || !Array.isArray(skills)) return [];
    
    return skills
      .filter(skill => !this.isIrrelevant(skill))
      .map(skill => skill.replace(/\s*\(\d+.*?\)/g, '').trim());
  },
  
  // Clean the entire profile data
  cleanProfileData: function(data) {
    const cleaned = { ...data };
    
    // Clean experience array
    if (cleaned.experience && Array.isArray(cleaned.experience)) {
      cleaned.experience = cleaned.experience
        .map(exp => this.cleanExperience(exp))
        .filter(exp => exp !== null);
    }
    
    // Clean education array
    if (cleaned.education && Array.isArray(cleaned.education)) {
      cleaned.education = cleaned.education
        .map(edu => this.cleanEducation(edu))
        .filter(edu => edu !== null);
    }
    
    // Clean skills
    if (cleaned.skills) {
      cleaned.skills = this.cleanSkills(cleaned.skills);
    }
    
    return cleaned;
  },
  
  // Build clean full text
  buildCleanText: function(name, headline, location, about, experience, education, skills, yearsExp) {
    const parts = [];
    
    // Header
    if (name) parts.push(name);
    if (headline) parts.push(headline);
    if (location) parts.push(location);
    if (yearsExp && yearsExp > 0) parts.push(`${yearsExp} years of experience`);
    
    // About
    if (about && !this.isIrrelevant(about)) {
      parts.push('\nABOUT');
      parts.push(about);
    }
    
    // Experience
    if (experience && experience.length > 0) {
      parts.push('\nEXPERIENCE');
      experience.forEach(exp => {
        if (exp && !this.isIrrelevant(exp.title)) {
          parts.push('');
          if (exp.title) parts.push(exp.title);
          if (exp.company && !this.isIrrelevant(exp.company)) {
            parts.push(exp.company);
          }
          if (exp.duration) parts.push(exp.duration);
          if (exp.location) parts.push(exp.location);
          if (exp.description && exp.description.length > 10) {
            parts.push(exp.description);
          }
        }
      });
    }
    
    // Education
    if (education && education.length > 0) {
      parts.push('\nEDUCATION');
      education.forEach(edu => {
        if (edu && !this.isIrrelevant(edu.school || edu.raw_text)) {
          parts.push('');
          if (edu.school) parts.push(edu.school);
          if (edu.degree && edu.field) {
            parts.push(`${edu.degree}, ${edu.field}`);
          } else if (edu.degree) {
            parts.push(edu.degree);
          }
          if (edu.dates) parts.push(edu.dates);
        }
      });
    }
    
    // Skills
    if (skills && skills.length > 0) {
      const cleanSkills = skills.filter(skill => !this.isIrrelevant(skill));
      if (cleanSkills.length > 0) {
        parts.push('\nSKILLS');
        parts.push(cleanSkills.join(', '));
      }
    }
    
    return parts.join('\n').trim();
  }
};