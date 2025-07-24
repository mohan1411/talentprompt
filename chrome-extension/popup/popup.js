// API configuration
const API_BASE_URL = 'https://talentprompt-production.up.railway.app/api/v1';
const DEV_API_URL = 'http://localhost:8001/api/v1';

// Use development URL for local testing
const API_URL = DEV_API_URL;

// State management
let authToken = null;
let currentUser = null;

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  console.log('Popup initialized');
  await checkAuthStatus();
  setupEventListeners();
  updateUIState();
  updateQueueBadge();
});

// Check if user is authenticated
async function checkAuthStatus() {
  const stored = await chrome.storage.local.get(['authToken', 'userEmail']);
  console.log('Checking stored auth:', stored);
  
  if (stored.authToken) {
    authToken = stored.authToken;
    currentUser = stored.userEmail;
    console.log('Found stored token for:', currentUser);
    
    // Verify token is still valid by making a test request
    try {
      const response = await fetch(`${API_URL}/users/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      if (response.ok) {
        console.log('Token is still valid');
        await loadStats();
      } else if (response.status === 401) {
        console.log('Token expired, clearing auth');
        await handleLogout();
      }
    } catch (error) {
      console.error('Failed to verify token:', error);
    }
  } else {
    console.log('No stored auth token found');
  }
}

// Setup event listeners
function setupEventListeners() {
  document.getElementById('login-btn').addEventListener('click', handleLogin);
  document.getElementById('logout-btn').addEventListener('click', handleLogout);
  document.getElementById('import-current').addEventListener('click', handleImportCurrent);
  document.getElementById('bulk-import').addEventListener('click', handleBulkImport);
  document.getElementById('view-queue').addEventListener('click', openQueueManager);
  document.getElementById('settings-link').addEventListener('click', openSettings);
  document.getElementById('help-link').addEventListener('click', openHelp);
}

// Handle login
async function handleLogin() {
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const errorEl = document.getElementById('error-message');
  
  if (!email || !password) {
    showError('Please enter email and password');
    return;
  }
  
  try {
    console.log('Attempting login with:', email);
    
    // Use FormData like the web app does
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json();
      console.error('Login failed:', error);
      
      // Check if this is an OAuth user error with URL
      if (error.detail && error.detail.includes('extension-auth')) {
        // Extract URL from error message
        const urlMatch = error.detail.match(/https?:\/\/[^\s]+/);
        if (urlMatch) {
          throw new Error(`OAuth users: Please get an access code from ${urlMatch[0]}`);
        }
      }
      
      throw new Error(error.detail || 'Login failed');
    }
    
    const data = await response.json();
    authToken = data.access_token;
    currentUser = email;
    
    // Store auth data
    await chrome.storage.local.set({
      authToken: authToken,
      userEmail: email
    });
    
    // Clear form
    document.getElementById('email').value = '';
    document.getElementById('password').value = '';
    errorEl.classList.add('hidden');
    
    await loadStats();
    updateUIState();
    
  } catch (error) {
    showError(error.message);
  }
}

// Handle logout
async function handleLogout() {
  console.log('Logging out user:', currentUser);
  authToken = null;
  currentUser = null;
  await chrome.storage.local.remove(['authToken', 'userEmail']);
  console.log('Cleared stored credentials');
  updateUIState();
}

// Load statistics
async function loadStats() {
  try {
    // For now, use mock data. Will implement real API later
    document.getElementById('imported-today').textContent = '0';
    document.getElementById('duplicates-found').textContent = '0';
  } catch (error) {
    console.error('Failed to load stats:', error);
  }
}

// Handle import current profile
async function handleImportCurrent() {
  console.log('Import button clicked');
  try {
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    console.log('Current tab:', tab.url);
    
    if (!tab.url || !tab.url.includes('linkedin.com/in/')) {
      showError('Please navigate to a LinkedIn profile');
      return;
    }
    
    // Try to send message to content script
    console.log('Sending message to content script...');
    let response;
    try {
      response = await chrome.tabs.sendMessage(tab.id, {
        action: 'importProfile',
        authToken: authToken
      });
    } catch (error) {
      console.log('Content script not loaded, injecting scripts...');
      
      // Get all content scripts from manifest
      const manifest = chrome.runtime.getManifest();
      const contentScripts = manifest.content_scripts[0].js;
      
      // Inject all scripts in order
      for (const script of contentScripts) {
        try {
          await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: [script]
          });
        } catch (injectError) {
          console.error(`Failed to inject ${script}:`, injectError);
        }
      }
      
      // Also inject the CSS
      try {
        await chrome.scripting.insertCSS({
          target: { tabId: tab.id },
          files: ['content/styles.css']
        });
      } catch (cssError) {
        console.error('Failed to inject CSS:', cssError);
      }
      
      // Wait a bit for scripts to initialize
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Try sending the message again
      try {
        response = await chrome.tabs.sendMessage(tab.id, {
          action: 'importProfile',
          authToken: authToken
        });
      } catch (retryError) {
        throw new Error('Failed to communicate with page. Please refresh the LinkedIn page and try again.');
      }
    }
    
    console.log('Response from content script:', response);
    
    if (response && response.success) {
      // Update stats
      const imported = parseInt(document.getElementById('imported-today').textContent) + 1;
      document.getElementById('imported-today').textContent = imported;
      
      showSuccess('Profile imported successfully!');
    } else {
      showError(response?.error || 'Import failed');
    }
    
  } catch (error) {
    console.error('Import error:', error);
    showError('Failed to import profile: ' + error.message);
  }
}

// Handle bulk import
async function handleBulkImport() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab.url.includes('linkedin.com/search/')) {
      showError('Please navigate to LinkedIn search results');
      return;
    }
    
    // Send message to content script
    let response;
    try {
      response = await chrome.tabs.sendMessage(tab.id, {
        action: 'bulkImport',
        authToken: authToken
      });
    } catch (error) {
      console.log('Content script not loaded for bulk import, injecting scripts...');
      
      // Get all content scripts from manifest
      const manifest = chrome.runtime.getManifest();
      const contentScripts = manifest.content_scripts[0].js;
      
      // Inject all scripts in order
      for (const script of contentScripts) {
        try {
          await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: [script]
          });
        } catch (injectError) {
          console.error(`Failed to inject ${script}:`, injectError);
        }
      }
      
      // Also inject CSS
      try {
        await chrome.scripting.insertCSS({
          target: { tabId: tab.id },
          files: ['content/styles.css']
        });
      } catch (cssError) {
        console.error('Failed to inject CSS:', cssError);
      }
      
      // Wait for initialization
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Try again
      try {
        response = await chrome.tabs.sendMessage(tab.id, {
          action: 'bulkImport',
          authToken: authToken
        });
      } catch (retryError) {
        throw new Error('Failed to communicate with page. Please refresh and try again.');
      }
    }
    
    if (response.success) {
      showSuccess(`Imported ${response.count} profiles`);
      
      // Update stats
      const imported = parseInt(document.getElementById('imported-today').textContent) + response.count;
      document.getElementById('imported-today').textContent = imported;
    } else {
      showError(response.error || 'Bulk import failed');
    }
    
  } catch (error) {
    showError('Failed to bulk import');
  }
}

// Update UI based on auth state
function updateUIState() {
  const loginForm = document.getElementById('login-form');
  const loggedIn = document.getElementById('logged-in');
  const statsSection = document.getElementById('stats-section');
  const actionsSection = document.getElementById('actions-section');
  
  if (authToken) {
    loginForm.classList.add('hidden');
    loggedIn.classList.remove('hidden');
    statsSection.classList.remove('hidden');
    actionsSection.classList.remove('hidden');
    
    document.getElementById('user-email').textContent = currentUser;
    
    // Enable action buttons
    document.getElementById('import-current').disabled = false;
    document.getElementById('bulk-import').disabled = false;
  } else {
    loginForm.classList.remove('hidden');
    loggedIn.classList.add('hidden');
    statsSection.classList.add('hidden');
    actionsSection.classList.add('hidden');
  }
}

// Show error message
function showError(message) {
  const errorEl = document.getElementById('error-message');
  
  // Check if this is an OAuth error with a URL
  if (message.includes('OAuth users') && message.includes('http')) {
    // Extract URL from the message
    const urlMatch = message.match(/https?:\/\/[^\s]+/);
    if (urlMatch) {
      const url = urlMatch[0];
      
      // Create a more helpful message with a clickable link
      errorEl.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: start;">
          <div>
            <div style="margin-bottom: 8px;">OAuth users need an access code to login.</div>
            <a href="#" id="oauth-link">
              Get your access code here →
            </a>
          </div>
          <button id="close-error" style="background: none; border: none; color: #6b7280; cursor: pointer; padding: 0; font-size: 18px; line-height: 1;">×</button>
        </div>
      `;
      
      // Add click handlers
      setTimeout(() => {
        const link = document.getElementById('oauth-link');
        if (link) {
          link.addEventListener('click', (e) => {
            e.preventDefault();
            chrome.tabs.create({ url: url });
          });
        }
        
        const closeBtn = document.getElementById('close-error');
        if (closeBtn) {
          closeBtn.addEventListener('click', () => {
            errorEl.classList.add('hidden');
          });
        }
      }, 0);
      
      errorEl.classList.remove('hidden');
      // Don't auto-hide OAuth errors - user needs time to click
      return;
    }
  }
  
  // Regular error handling
  errorEl.textContent = message;
  errorEl.classList.remove('hidden');
  setTimeout(() => errorEl.classList.add('hidden'), 5000);
}

// Show success message
function showSuccess(message) {
  // For now, use alert. Can implement toast later
  alert(message);
}

// Open settings
function openSettings() {
  // Open settings in a new tab since we don't have an options page yet
  chrome.tabs.create({
    url: 'https://talentprompt-production.up.railway.app/settings'
  });
}

// Open help
function openHelp() {
  chrome.tabs.create({
    url: 'https://promtitude.com/help/chrome-extension'
  });
}

// Open queue manager
function openQueueManager() {
  window.location.href = 'queue.html';
}

// Update queue badge
async function updateQueueBadge() {
  const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
  const pendingCount = linkedinImportQueue.filter(item => item.status === 'pending').length;
  
  const badge = document.getElementById('queue-badge');
  if (badge) {
    if (pendingCount > 0) {
      badge.textContent = pendingCount;
      badge.style.display = 'inline-block';
    } else {
      badge.style.display = 'none';
    }
  }
}