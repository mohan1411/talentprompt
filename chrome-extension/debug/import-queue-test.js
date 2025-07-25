/**
 * Test version to verify the import queue is loading
 */

console.log('🔥 IMPORT QUEUE TEST: Script loaded at', new Date().toISOString());

// Simple test - inject a visible element
setTimeout(() => {
  console.log('🔥 IMPORT QUEUE TEST: Attempting to inject test UI...');
  
  // Create a test badge
  const testBadge = document.createElement('div');
  testBadge.id = 'import-queue-test-badge';
  testBadge.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: #0a66c2;
    color: white;
    padding: 10px 20px;
    border-radius: 8px;
    z-index: 99999;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  `;
  testBadge.textContent = '✅ Import Queue Active';
  testBadge.onclick = () => {
    alert('Import Queue is working! Check console for logs.');
  };
  
  document.body.appendChild(testBadge);
  console.log('🔥 IMPORT QUEUE TEST: Badge injected');
  
  // Also log current page info
  console.log('Current URL:', window.location.href);
  console.log('Is Profile Page:', window.location.pathname.includes('/in/'));
  console.log('Is Search Page:', window.location.pathname.includes('/search/'));
  
}, 2000);