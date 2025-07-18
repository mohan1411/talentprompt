/**
 * Debug script to understand LinkedIn search results structure
 */

console.log('🔍 DEBUG: LinkedIn Search Structure Analysis');

setTimeout(() => {
  console.log('🔍 Current URL:', window.location.href);
  console.log('🔍 Is search page:', window.location.pathname.includes('/search/'));
  
  // Try different selectors
  const selectors = [
    '.entity-result',
    '.reusable-search__entity-result-list > li',
    'div[data-chameleon-result-urn]',
    '.scaffold-finite-scroll__content > ul > li',
    'li.reusable-search__result-container',
    '[class*="entity-result"]',
    'div[class*="search-result"]',
    'ul > li[class*="result"]',
    '.artdeco-list__item',
    'main ul > li'
  ];
  
  console.log('🔍 Testing selectors...');
  selectors.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    if (elements.length > 0) {
      console.log(`✅ Found ${elements.length} elements with selector: "${selector}"`);
      
      // Log first element structure
      if (elements[0]) {
        console.log('First element HTML preview:');
        console.log(elements[0].outerHTML.substring(0, 500) + '...');
        
        // Check for profile links
        const links = elements[0].querySelectorAll('a[href*="/in/"]');
        console.log(`   - Contains ${links.length} profile links`);
        
        // Check for name elements
        const names = elements[0].querySelectorAll('[class*="title"], [class*="name"], span[aria-hidden="true"]');
        console.log(`   - Contains ${names.length} potential name elements`);
      }
    }
  });
  
  // Also log the general page structure
  console.log('\n🔍 Page structure analysis:');
  const main = document.querySelector('main');
  if (main) {
    console.log('Main element found');
    const lists = main.querySelectorAll('ul');
    console.log(`Found ${lists.length} UL elements in main`);
    
    lists.forEach((list, index) => {
      const items = list.children.length;
      if (items > 5) {
        console.log(`UL #${index}: ${items} items (likely search results)`);
        console.log('First item:', list.children[0]?.outerHTML.substring(0, 300) + '...');
      }
    });
  }
  
  // Create visual indicator
  const indicator = document.createElement('div');
  indicator.style.cssText = `
    position: fixed;
    top: 200px;
    right: 20px;
    background: #ff6b6b;
    color: white;
    padding: 12px;
    border-radius: 8px;
    z-index: 10000;
    max-width: 300px;
  `;
  indicator.innerHTML = `
    <strong>Debug Mode Active</strong><br>
    Check console for results<br>
    <small>This will help us find the right selectors</small>
  `;
  document.body.appendChild(indicator);
  
}, 3000);