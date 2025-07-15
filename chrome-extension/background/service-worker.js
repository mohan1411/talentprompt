// Service worker for Promtitude Chrome Extension

console.log('Promtitude service worker loaded');

// API configuration
const API_BASE_URL = 'https://talentprompt-production.up.railway.app/api/v1';
const DEV_API_URL = 'http://localhost:8000/api/v1';

// Use production backend
const API_URL = API_BASE_URL;

// Handle extension installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('Promtitude LinkedIn Integration installed');
});

// Message handler for communication with popup and content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Received message:', request);
  
  if (request.action === 'importProfile') {
    // Handle the API request in the background script to avoid CORS issues
    handleImportProfile(request.data, request.authToken)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Keep the message channel open for async response
  }
  
  // Echo back for other messages
  sendResponse({ received: true, action: request.action });
  return true;
});

// Import profile to backend
async function handleImportProfile(profileData, authToken) {
  console.log('Background script importing profile...');
  
  if (!authToken) {
    throw new Error('Not authenticated');
  }
  
  const url = `${API_URL}/linkedin/import-profile`;
  console.log('Making request to:', url);
  console.log('Request body:', profileData);
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(profileData)
  });
  
  console.log('Response status:', response.status);
  console.log('Response status text:', response.statusText);
  
  if (!response.ok) {
    const errorText = await response.text();
    console.error('Error response:', errorText);
    
    try {
      const error = JSON.parse(errorText);
      throw new Error(error.detail || `Import failed: ${response.statusText}`);
    } catch (e) {
      throw new Error(`Import failed: ${response.statusText} - ${errorText}`);
    }
  }
  
  return await response.json();
}