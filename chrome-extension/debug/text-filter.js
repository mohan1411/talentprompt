// Filter out irrelevant content from LinkedIn profile text
window.filterLinkedInText = function(text) {
  if (!text) return '';
  
  // List of patterns to remove
  const removePatterns = [
    // Remove follower counts and social proof
    /\d+(?:,\d+)*\s*followers?/gi,
    /\d+(?:,\d+)*\s*connections?/gi,
    
    // Remove "People also viewed" type content
    /People also viewed[\s\S]*?(?=\n\n|EXPERIENCE|EDUCATION|SKILLS|$)/gi,
    /People you may know[\s\S]*?(?=\n\n|EXPERIENCE|EDUCATION|SKILLS|$)/gi,
    
    // Remove specific names and titles that are not the profile owner
    /Narendra Modi[\s\S]*?Prime Minister of India/gi,
    /Jeff Weiner[\s\S]*?\d+.*followers/gi,
    /Bill Gates[\s\S]*?\d+.*followers/gi,
    /Satya Nadella[\s\S]*?\d+.*followers/gi,
    
    // Remove company follower sections
    /Google\s+\d+(?:,\d+)*\s*followers/gi,
    /Amazon\s+\d+(?:,\d+)*\s*followers/gi,
    /Microsoft\s+\d+(?:,\d+)*\s*followers/gi,
    /Facebook\s+\d+(?:,\d+)*\s*followers/gi,
    /Apple\s+\d+(?:,\d+)*\s*followers/gi,
    
    // Remove newsletter/blog recommendations
    /The world of startups[\s\S]*?Shekhar Kirani/gi,
    /Newsletter[\s\S]*?subscribers/gi,
    
    // Remove "· 3rd" type connection indicators
    /·\s*\d+(?:st|nd|rd|th)\s*(?:connection)?/gi,
    
    // Remove promoted content
    /Promoted/gi,
    
    // Clean up endorsements but keep the skill
    /Endorsed by \d+ colleagues[\s\S]*?(?=\n|$)/gi,
    /\d+ endorsements?/gi,
    
    // Remove entire endorsement lines
    /^.*Endorsed by.*$/gm,
    /^.*\d+\s*endorsements.*$/gm,
    
    // Remove lines that are just follower counts
    /^\d+(?:,\d+)*\s*followers?\s*$/gm,
    
    // Remove lines with "at" followed by endorsement info
    /^at\s+\d+\s+endorsements?\s*$/gm,
    
    // Remove standalone company names with follower counts
    /^[A-Za-z\s&]+\n\d+(?:,\d+)*\s*followers?\s*$/gm
  ];
  
  let cleanedText = text;
  
  // Apply all removal patterns
  removePatterns.forEach(pattern => {
    cleanedText = cleanedText.replace(pattern, '');
  });
  
  // Clean up extra whitespace
  cleanedText = cleanedText
    .replace(/\n{3,}/g, '\n\n')  // Replace multiple newlines with double
    .replace(/[ \t]+/g, ' ')      // Replace multiple spaces with single
    .trim();
  
  return cleanedText;
};