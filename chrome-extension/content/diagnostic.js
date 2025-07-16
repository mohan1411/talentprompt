// Diagnostic script to verify extension is updated
console.log('=== Promtitude Extension Diagnostic ===');
console.log('Version: 2.2 - Email & Experience Fix');
console.log('Loaded modules:');
console.log('- findEmailInModal:', typeof window.findEmailInModal);
console.log('- extractEmailDirect:', typeof window.extractEmailDirect);
console.log('- extractContactInfo:', typeof window.extractContactInfo);
console.log('- extractUltraCleanProfile:', typeof window.extractUltraCleanProfile);
console.log('- calculateTotalExperience:', typeof window.calculateTotalExperience);
console.log('- verifyCleanData:', typeof window.verifyCleanData);

// Quick test of contact extraction
if (window.extractContactInfo) {
  console.log('Contact extraction function is available');
} else {
  console.error('WARNING: Contact extraction function NOT loaded!');
}

console.log('=== End Diagnostic ===');