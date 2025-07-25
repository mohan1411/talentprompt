// API configuration
const API_BASE_URL = 'https://talentprompt-production.up.railway.app/api/v1';
const DEV_API_URL = 'http://localhost:8000/api/v1';

// Use production URL
const API_URL = API_BASE_URL;

// State management
let authToken = null;
let currentUser = null;

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  // console.log('Popup initialized');
  await checkAuthStatus();
  setupEventListeners();
  await updateUIState();
  updateQueueBadge();
  
  // Check if we have a stored email (for better UX)
  const stored = await chrome.storage.local.get(['lastEmail', 'hasSeenWelcome']);
  if (stored.lastEmail && !authToken) {
    document.getElementById('email').value = stored.lastEmail;
    // Auto-check OAuth status for returning users
    checkUserType();
  }
  
  // Show welcome screen for first-time users
  if (!authToken && !stored.hasSeenWelcome) {
    showWelcomeScreen();
  }
});

// Listen for stats updates from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'statsUpdated' && request.stats) {
    document.getElementById('imported-today').textContent = request.stats.imported;
    document.getElementById('duplicates-found').textContent = request.stats.duplicates;
  }
});

// Update UI when active tab changes
chrome.tabs.onActivated.addListener(async () => {
  if (authToken) {
    await updateUIState();
  }
});

// Check if user is authenticated
async function checkAuthStatus() {
  const stored = await chrome.storage.local.get(['authToken', 'userEmail']);
  console.log('Checking stored auth:', stored);
  
  if (stored.authToken) {
    authToken = stored.authToken;
    currentUser = stored.userEmail;
    // console.log('Found stored token for:', currentUser);
    
    // Verify token is still valid by making a test request
    try {
      const response = await fetch(`${API_URL}/users/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      if (response.ok) {
        // console.log('Token is still valid');
        await loadStats();
      } else if (response.status === 401) {
        // console.log('Token expired, clearing auth');
        await handleLogout();
      }
    } catch (error) {
      console.error('Failed to verify token:', error);
    }
  } else {
    // console.log('No stored auth token found');
  }
}

// Setup event listeners
function setupEventListeners() {
  document.getElementById('login-btn').addEventListener('click', handleLogin);
  document.getElementById('logout-btn').addEventListener('click', handleLogout);
  document.getElementById('import-action').addEventListener('click', handleImportAction);
  document.getElementById('view-queue').addEventListener('click', openQueueManager);
  document.getElementById('settings-link').addEventListener('click', openSettings);
  document.getElementById('help-link').addEventListener('click', openHelp);
  
  // Welcome screen listeners
  const createAccountBtn = document.getElementById('create-account-btn');
  const showLoginLink = document.getElementById('show-login');
  const createAccountLink = document.getElementById('create-account-link');
  
  if (createAccountBtn) {
    createAccountBtn.addEventListener('click', openRegistration);
  }
  if (showLoginLink) {
    showLoginLink.addEventListener('click', (e) => {
      e.preventDefault();
      showLoginForm();
    });
  }
  if (createAccountLink) {
    createAccountLink.addEventListener('click', (e) => {
      e.preventDefault();
      openRegistration();
    });
  }
  
  // OAuth-specific listeners
  const emailInput = document.getElementById('email');
  const getCodeBtn = document.getElementById('get-code-btn');
  const accessCodeInput = document.getElementById('access-code');
  
  // Check user type when email loses focus
  emailInput.addEventListener('blur', checkUserType);
  
  // Handle get code button
  if (getCodeBtn) {
    getCodeBtn.addEventListener('click', handleGetAccessCode);
  }
  
  // Auto-uppercase access code input
  if (accessCodeInput) {
    accessCodeInput.addEventListener('input', (e) => {
      e.target.value = e.target.value.toUpperCase();
    });
  }
}

// Check if user is OAuth user
async function checkUserType() {
  const email = document.getElementById('email').value;
  
  if (!email || !email.includes('@')) return;
  
  // Store email for next time
  chrome.storage.local.set({ lastEmail: email });
  
  try {
    const url = `${API_URL}/auth/check-oauth-user?email=${encodeURIComponent(email)}`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      updateAuthUI(data.is_oauth_user, data.oauth_provider);
    }
  } catch (error) {
    // Silently fail - user can still manually enter password
  }
}

// Update UI based on auth type
function updateAuthUI(isOAuthUser, provider) {
  const passwordContainer = document.getElementById('password-container');
  const oauthContainer = document.getElementById('oauth-container');
  const oauthProvider = document.getElementById('oauth-provider');
  const oauthIcon = document.getElementById('oauth-icon');
  
  if (!passwordContainer || !oauthContainer) {
    return;
  }
  
  if (isOAuthUser) {
    passwordContainer.classList.add('hidden');
    oauthContainer.classList.remove('hidden');
    oauthProvider.textContent = provider || 'OAuth';
    
    // Set provider icon
    if (provider === 'google') {
      oauthIcon.src = 'https://www.google.com/favicon.ico';
      oauthIcon.alt = 'Google';
    } else if (provider === 'linkedin') {
      oauthIcon.src = 'https://www.linkedin.com/favicon.ico';
      oauthIcon.alt = 'LinkedIn';
    }
  } else {
    passwordContainer.classList.remove('hidden');
    oauthContainer.classList.add('hidden');
  }
}

// Handle get access code button
async function handleGetAccessCode() {
  const email = document.getElementById('email').value;
  if (!email) {
    showError('Please enter your email first');
    return;
  }
  
  // Open the web app's extension auth page
  const authUrl = `https://promtitude.com/extension-auth?email=${encodeURIComponent(email)}`;
  chrome.tabs.create({ url: authUrl });
}

// Handle login
async function handleLogin() {
  const email = document.getElementById('email').value;
  const passwordEl = document.getElementById('password');
  const accessCodeEl = document.getElementById('access-code');
  const errorEl = document.getElementById('error-message');
  const isOAuthLogin = !document.getElementById('oauth-container').classList.contains('hidden');
  
  // Get auth value based on login type
  const authValue = isOAuthLogin ? accessCodeEl.value : passwordEl.value;
  
  if (!email || !authValue) {
    showError(isOAuthLogin ? 'Please enter email and access code' : 'Please enter email and password');
    return;
  }
  
  // Validate access code format for OAuth users
  if (isOAuthLogin && authValue.length !== 6) {
    showError('Access code must be exactly 6 characters');
    return;
  }
  
  try {
    // console.log('Attempting login with:', email);
    
    // Use FormData like the web app does
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', authValue); // This works for both password and access code
    
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json();
      
      // Check if this is an OAuth user error
      if (error.detail && error.detail.includes('OAuth users')) {
        // For OAuth users, we should have already shown the proper UI
        // This error might occur if they're trying with an old/invalid code
        if (error.detail.includes('Invalid access code')) {
          throw new Error('Invalid or expired access code. Please generate a new one.');
        }
        throw new Error(error.detail);
      }
      
      // Check for access code specific errors
      if (error.detail && error.detail.includes('access code')) {
        throw new Error(error.detail);
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
    document.getElementById('access-code').value = '';
    errorEl.classList.add('hidden');
    
    await loadStats();
    await updateUIState();
    
  } catch (error) {
    showError(error.message);
  }
}

// Handle logout
async function handleLogout() {
  // console.log('Logging out user:', currentUser);
  authToken = null;
  currentUser = null;
  await chrome.storage.local.remove(['authToken', 'userEmail']);
  // console.log('Cleared stored credentials');
  await updateUIState();
}

// Load statistics
async function loadStats() {
  try {
    const today = new Date().toDateString();
    const { importStats = {} } = await chrome.storage.local.get('importStats');
    
    const todayStats = importStats[today] || { imported: 0, duplicates: 0 };
    
    document.getElementById('imported-today').textContent = todayStats.imported;
    document.getElementById('duplicates-found').textContent = todayStats.duplicates;
  } catch (error) {
    console.error('Failed to load stats:', error);
  }
}

// Handle import action (context-aware)
async function handleImportAction() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab || !tab.url) {
      showError('No active tab found');
      return;
    }
    
    if (tab.url.includes('linkedin.com/in/')) {
      // On a profile page - do import
      await handleImportProfile(tab);
    } else if (tab.url.includes('linkedin.com/search/results/')) {
      // On a search page - focus the bulk import toolbar
      await handleOpenBulkImport(tab);
    } else {
      showError('Navigate to a LinkedIn profile or search page');
    }
  } catch (error) {
    console.error('Import action error:', error);
    showError('Failed to perform action: ' + error.message);
  }
}

// Handle import current profile
async function handleImportProfile(tab) {
  console.log('Import profile clicked');
  try {
    console.log('Current tab:', tab.url);
    
    if (!tab.url || !tab.url.includes('linkedin.com/in/')) {
      showError('Please navigate to a LinkedIn profile');
      return;
    }
    
    // Show loading state
    const importBtn = document.getElementById('import-action');
    const originalText = importBtn.textContent;
    importBtn.textContent = 'Importing...';
    importBtn.disabled = true;
    
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
    
    if (response && response.success) {
      // Check if it's a duplicate
      if (response.data && response.data.is_duplicate) {
        // Don't update stats for duplicates
        showInfo('This profile has already been imported');
        // Don't close popup for duplicates, let user see the message
        setTimeout(() => {
          window.close();
        }, 3000);
      } else {
        // Update stats only for new imports
        const imported = parseInt(document.getElementById('imported-today').textContent) + 1;
        document.getElementById('imported-today').textContent = imported;
        
        showSuccess('Profile imported successfully!');
        // Close popup after showing message
        setTimeout(() => {
          window.close();
        }, 1500);
      }
    } else {
      const errorMessage = response?.error || 'Import failed';
      
      // Check if it's a duplicate error
      if (errorMessage.includes('already been imported') || 
          errorMessage.includes('already exists') ||
          errorMessage.includes('duplicate')) {
        // Show as info instead of error for duplicates
        showInfo('This profile has already been imported');
        // Give more time to read duplicate message
        setTimeout(() => {
          window.close();
        }, 3000);
      } else {
        showError(errorMessage);
      }
    }
    
  } catch (error) {
    console.error('Import error:', error);
    showError('Failed to import profile: ' + error.message);
  } finally {
    // Restore button state
    const importBtn = document.getElementById('import-action');
    importBtn.textContent = originalText;
    importBtn.disabled = false;
  }
}

// Handle opening bulk import tool on search page
async function handleOpenBulkImport(tab) {
  console.log('Opening bulk import tool');
  try {
    // Show loading state
    const importBtn = document.getElementById('import-action');
    const originalText = importBtn.textContent;
    importBtn.textContent = 'Opening...';
    importBtn.disabled = true;
    
    // Send message to content script to show/focus the bulk import toolbar
    let response;
    try {
      console.log('Attempting to focus bulk import tool...');
      response = await chrome.tabs.sendMessage(tab.id, {
        action: 'showBulkImportSidebar'
      });
      
      if (response && response.success) {
        console.log('Bulk import tool opened successfully');
        // Close the popup immediately
        window.close();
      } else {
        console.error('Failed to open bulk import tool:', response);
        showError(response?.error || 'Failed to open bulk import tool');
      }
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
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Try again
      try {
        console.log('Retrying focusBulkImportTool message...');
        const retryResponse = await chrome.tabs.sendMessage(tab.id, {
          action: 'showBulkImportSidebar'
        });
        
        if (retryResponse && retryResponse.success) {
          console.log('Bulk import tool opened successfully on retry');
          // Close the popup immediately
          window.close();
        } else {
          showError(retryResponse?.error || 'Bulk import tool not ready. Please refresh the page.');
        }
      } catch (retryError) {
        console.error('Retry failed:', retryError);
        showError('Please refresh the LinkedIn page and try again');
      }
    }
  } catch (error) {
    console.error('Failed to open bulk import tool:', error);
    showError('Failed to open bulk import tool: ' + error.message);
  } finally {
    // Restore button state
    const importBtn = document.getElementById('import-action');
    importBtn.textContent = originalText;
    importBtn.disabled = false;
  }
}

// Update UI based on auth state
async function updateUIState() {
  const welcomeScreen = document.getElementById('welcome-screen');
  const loginForm = document.getElementById('login-form');
  const loggedIn = document.getElementById('logged-in');
  const statsSection = document.getElementById('stats-section');
  const actionsSection = document.getElementById('actions-section');
  
  if (authToken) {
    welcomeScreen.classList.add('hidden');
    loginForm.classList.add('hidden');
    loggedIn.classList.remove('hidden');
    statsSection.classList.remove('hidden');
    actionsSection.classList.remove('hidden');
    
    document.getElementById('user-email').textContent = currentUser;
    
    // Check current tab to determine context
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const importBtn = document.getElementById('import-action');
      const importInfo = document.getElementById('import-action-info');
      
      if (!tab || !tab.url || !tab.url.includes('linkedin.com')) {
        // Not on LinkedIn
        importBtn.textContent = 'Import Profile';
        importBtn.disabled = true;
        importBtn.title = 'Navigate to a LinkedIn profile to import';
        importInfo.classList.add('hidden');
      } else if (tab.url.includes('linkedin.com/in/')) {
        // On a profile page
        importBtn.textContent = 'Import Current Profile';
        importBtn.disabled = false;
        importBtn.title = 'Import this LinkedIn profile';
        importInfo.classList.add('hidden');
      } else if (tab.url.includes('linkedin.com/search/results/')) {
        // On a search page
        importBtn.textContent = 'Open Bulk Import Tool';
        importBtn.disabled = false;
        importBtn.title = 'Open the bulk import sidebar';
        
        // Show helpful info
        importInfo.textContent = 'Opens a sidebar to select and import multiple profiles';
        importInfo.classList.remove('hidden');
      } else {
        // On LinkedIn but not a supported page
        importBtn.textContent = 'Import Profile';
        importBtn.disabled = true;
        importBtn.title = 'Navigate to a profile or search results';
        importInfo.classList.add('hidden');
      }
    } catch (error) {
      console.error('Failed to check current tab:', error);
      document.getElementById('import-action').disabled = true;
    }
  } else {
    // Not authenticated - check if we should show welcome or login
    const stored = await chrome.storage.local.get(['hasSeenWelcome']);
    
    if (stored.hasSeenWelcome) {
      welcomeScreen.classList.add('hidden');
      loginForm.classList.remove('hidden');
    } else {
      welcomeScreen.classList.remove('hidden');
      loginForm.classList.add('hidden');
    }
    
    loggedIn.classList.add('hidden');
    statsSection.classList.add('hidden');
    actionsSection.classList.add('hidden');
  }
}

// Show error message
function showError(message) {
  const errorEl = document.getElementById('error-message');
  
  // Check if message contains a URL and make it clickable
  if (message.includes('http://') || message.includes('https://')) {
    // Replace URLs with clickable links
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const messageWithLinks = message.replace(urlRegex, (url) => {
      return `<a href="#" data-url="${url}" style="color: inherit; text-decoration: underline;">${url}</a>`;
    });
    errorEl.innerHTML = messageWithLinks;
    
    // Add click handlers for links
    setTimeout(() => {
      errorEl.querySelectorAll('a[data-url]').forEach(link => {
        link.addEventListener('click', (e) => {
          e.preventDefault();
          chrome.tabs.create({ url: link.getAttribute('data-url') });
        });
      });
    }, 0);
  } else {
    errorEl.textContent = message;
  }
  
  errorEl.classList.remove('hidden');
  setTimeout(() => errorEl.classList.add('hidden'), 5000);
}

// Show success message
function showSuccess(message) {
  // For now, use alert. Can implement toast later
  alert(message);
}

// Show info message (for duplicates, etc)
function showInfo(message) {
  const errorEl = document.getElementById('error-message');
  
  if (errorEl) {
    errorEl.style.background = '#fef3c7';
    errorEl.style.border = '1px solid #fbbf24';
    errorEl.style.color = '#92400e';
    errorEl.style.padding = '10px';
    errorEl.style.borderRadius = '6px';
    errorEl.innerHTML = '⚠️ ' + message;
    errorEl.classList.remove('hidden');
    
    // Don't auto-hide for important messages like duplicates
    // User will see it until popup closes
  } else {
    alert(message);
  }
}

// Open settings
function openSettings() {
  // Open settings in a new tab since we don't have an options page yet
  chrome.tabs.create({
    url: 'https://promtitude.com/settings'
  });
}

// Open help
function openHelp() {
  chrome.tabs.create({
    url: 'https://promtitude.com/help'
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

// Show welcome screen
function showWelcomeScreen() {
  document.getElementById('welcome-screen').classList.remove('hidden');
  document.getElementById('login-form').classList.add('hidden');
}

// Show login form
function showLoginForm() {
  document.getElementById('welcome-screen').classList.add('hidden');
  document.getElementById('login-form').classList.remove('hidden');
  // Mark that user has seen welcome
  chrome.storage.local.set({ hasSeenWelcome: true });
}

// Open registration page
function openRegistration() {
  chrome.tabs.create({
    url: 'https://promtitude.com/register'
  });
}