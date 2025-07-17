// Simple debug script - paste this in console on Suhas's profile

console.log('=== SIMPLE SKILLS DEBUG ===');

// Find all text containing "Top skills"
const allText = document.body.innerText;
const topSkillsIndex = allText.indexOf('Top skills');

if (topSkillsIndex !== -1) {
  console.log('Found "Top skills" in page text');
  // Get 500 characters after "Top skills"
  const snippet = allText.substring(topSkillsIndex, topSkillsIndex + 500);
  console.log('Text around Top skills:');
  console.log(snippet);
}

// Look for bullet character
console.log('\n=== Looking for bullet character • ===');
const bulletIndex = allText.indexOf('•');
if (bulletIndex !== -1) {
  // Find all occurrences of bullet
  let index = 0;
  let count = 0;
  while ((index = allText.indexOf('•', index)) !== -1 && count < 10) {
    const context = allText.substring(index - 50, index + 50);
    console.log(`\nBullet ${count + 1}:`);
    console.log(context);
    index++;
    count++;
  }
}

// Look for specific skills
console.log('\n=== Looking for specific skills ===');
const skills = ['Kaizen', 'Strategy', 'Employee Training', 'Project Management'];
skills.forEach(skill => {
  if (allText.includes(skill)) {
    console.log(`Found "${skill}"`);
    const skillIndex = allText.indexOf(skill);
    const context = allText.substring(skillIndex - 50, skillIndex + 50);
    console.log('Context:', context);
  }
});

// Check the skills section
console.log('\n=== Skills Section Check ===');
const skillsSection = document.querySelector('#skills');
if (skillsSection) {
  console.log('Skills section element found');
  const section = skillsSection.closest('section');
  if (section) {
    console.log('Skills section text (first 1000 chars):');
    console.log(section.innerText.substring(0, 1000));
  }
}