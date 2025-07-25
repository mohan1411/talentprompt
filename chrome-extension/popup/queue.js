// Queue management
let authToken = null;
let isProcessing = false;
let shouldPause = false;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  await loadAuthToken();
  await loadQueue();
  setupEventListeners();
  
  // Check if processing is already running
  const statusResponse = await chrome.runtime.sendMessage({ action: 'getProcessingStatus' });
  if (statusResponse.isProcessing) {
    isProcessing = true;
    document.getElementById('process-queue-btn').style.display = 'none';
    document.getElementById('pause-queue-btn').style.display = 'inline-block';
    document.getElementById('queue-progress').style.display = 'block';
    monitorProgress();
  }
});

// Listen for progress updates from service worker
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'queueProgress') {
    // Update stats if the popup is open
    loadQueue();
  }
});

// Load auth token
async function loadAuthToken() {
  const stored = await chrome.storage.local.get(['authToken']);
  authToken = stored.authToken;
  
  if (!authToken) {
    showError('Please login first');
    setTimeout(() => window.close(), 2000);
  }
}

// Setup event listeners
function setupEventListeners() {
  document.getElementById('back-btn').addEventListener('click', () => {
    window.location.href = 'popup.html';
  });
  
  document.getElementById('process-queue-btn').addEventListener('click', startProcessing);
  document.getElementById('pause-queue-btn').addEventListener('click', pauseProcessing);
  document.getElementById('clear-completed-btn').addEventListener('click', clearCompleted);
  document.getElementById('clear-pending-btn').addEventListener('click', clearPending);
  document.getElementById('clear-all-btn').addEventListener('click', clearAll);
}

// Load and display queue
async function loadQueue() {
  const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
  
  // Update stats
  const stats = {
    pending: 0,
    processing: 0,
    completed: 0,
    failed: 0
  };
  
  linkedinImportQueue.forEach(item => {
    stats[item.status] = (stats[item.status] || 0) + 1;
  });
  
  document.getElementById('pending-count').textContent = stats.pending;
  document.getElementById('processing-count').textContent = stats.processing;
  document.getElementById('completed-count').textContent = stats.completed;
  document.getElementById('failed-count').textContent = stats.failed;
  
  // Render queue items
  const queueList = document.getElementById('queue-list');
  const emptyState = document.getElementById('empty-state');
  
  if (linkedinImportQueue.length === 0) {
    queueList.innerHTML = '';
    emptyState.style.display = 'block';
    return;
  }
  
  emptyState.style.display = 'none';
  queueList.innerHTML = linkedinImportQueue.map(item => {
    // Check if it's a duplicate error
    const isDuplicate = item.error && (
      item.error.includes('already been imported') || 
      item.error.includes('Duplicate') ||
      item.error.includes('already exists')
    );
    
    return `
      <div class="queue-item ${item.status}" data-id="${item.id}">
        <div class="queue-item-info">
          <div class="queue-item-name">${item.profileName || 'Unknown Profile'}</div>
          <div class="queue-item-url">${item.profileUrl}</div>
          ${item.error ? `
            <div style="
              color: ${isDuplicate ? '#f59e0b' : '#dc2626'}; 
              font-size: 13px; 
              margin-top: 6px;
              padding: 4px 8px;
              background: ${isDuplicate ? '#fef3c7' : '#fee2e2'};
              border-radius: 4px;
              border: 1px solid ${isDuplicate ? '#fbbf24' : '#f87171'};
              font-weight: 500;
            ">
              ${isDuplicate ? '⚠️ ' : '❌ '}${item.error}
            </div>
          ` : ''}
        </div>
        <div class="queue-item-status status-${item.status}">
          ${isDuplicate ? 'duplicate' : item.status}
        </div>
      </div>
    `;
  }).join('');
  
  // Update badge
  chrome.runtime.sendMessage({
    action: 'updateQueueBadge',
    count: stats.pending
  });
}

// Start processing queue
async function startProcessing() {
  try {
    // First, wake up the service worker with a simple ping
    try {
      await chrome.runtime.sendMessage({ action: 'ping' });
    } catch (e) {
      // Service worker might be inactive, that's okay
    }
    
    // Small delay to ensure service worker is ready
    await delay(100);
    
    // Start processing in background with timeout
    let response;
    try {
      response = await Promise.race([
        chrome.runtime.sendMessage({ action: 'startQueueProcessing' }),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Request timeout')), 8000) // Increased timeout
        )
      ]);
    } catch (timeoutError) {
      // Try one more time after waking up the service worker
      await delay(500);
      try {
        response = await chrome.runtime.sendMessage({ action: 'startQueueProcessing' });
      } catch (retryError) {
        throw new Error('Background service not responding. Please close and reopen the extension.');
      }
    }
    
    if (!response) {
      throw new Error('No response from background script');
    }
    
    if (response.success) {
      isProcessing = true;
      
      // Update UI
      document.getElementById('process-queue-btn').style.display = 'none';
      document.getElementById('pause-queue-btn').style.display = 'inline-block';
      document.getElementById('queue-progress').style.display = 'block';
      
      // Start monitoring progress
      monitorProgress();
    } else {
      showError('Failed to start processing: ' + (response.error || 'Unknown error'));
    }
  } catch (error) {
    console.error('Error starting queue processing:', error);
    showError(error.message);
  }
}

// Pause processing
async function pauseProcessing() {
  try {
    await chrome.runtime.sendMessage({ action: 'stopQueueProcessing' });
    isProcessing = false;
    resetProcessingUI();
  } catch (error) {
    console.error('Failed to stop processing:', error);
  }
}

// Monitor progress
function monitorProgress() {
  if (!isProcessing) return;
  
  // Check progress every second
  const progressInterval = setInterval(async () => {
    try {
      // Check if still processing
      const statusResponse = await chrome.runtime.sendMessage({ action: 'getProcessingStatus' });
      
      if (!statusResponse.isProcessing) {
        clearInterval(progressInterval);
        resetProcessingUI();
        await loadQueue();
        return;
      }
      
      // Update queue display
      await loadQueue();
      
      // Update progress bar
      const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
      const total = linkedinImportQueue.length;
      const completed = linkedinImportQueue.filter(item => 
        item.status === 'completed' || item.status === 'failed'
      ).length;
      
      if (total > 0) {
        updateProgress(completed, total);
      }
      
    } catch (error) {
      console.error('Progress monitoring error:', error);
      clearInterval(progressInterval);
    }
  }, 1000);
}

// Reset processing UI
function resetProcessingUI() {
  isProcessing = false;
  document.getElementById('process-queue-btn').style.display = 'inline-block';
  document.getElementById('pause-queue-btn').style.display = 'none';
  document.getElementById('queue-progress').style.display = 'none';
}

// Update progress
function updateProgress(current, total) {
  const percent = Math.round((current / total) * 100);
  document.getElementById('progress-fill').style.width = `${percent}%`;
  document.getElementById('progress-text').textContent = `${current} / ${total}`;
}

// Update item status
async function updateItemStatus(itemId, status, error = null) {
  const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
  
  const item = linkedinImportQueue.find(i => i.id === itemId);
  if (item) {
    item.status = status;
    if (error) {
      item.error = error;
    }
    
    await chrome.storage.local.set({ linkedinImportQueue });
    await loadQueue(); // Refresh display
  }
}

// Note: Profile extraction and import are now handled by the background service worker

// Clear completed items
async function clearCompleted() {
  const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
  
  const filtered = linkedinImportQueue.filter(item => 
    item.status !== 'completed' && item.status !== 'failed'
  );
  
  await chrome.storage.local.set({ linkedinImportQueue: filtered });
  await loadQueue();
}

// Clear pending items
async function clearPending() {
  // Check if processing is running
  const statusResponse = await chrome.runtime.sendMessage({ action: 'getProcessingStatus' });
  if (statusResponse.isProcessing) {
    const confirmStop = confirm('Queue processing is currently running. Do you want to stop processing and clear pending items?');
    if (!confirmStop) {
      return;
    }
    
    // Stop processing first
    await chrome.runtime.sendMessage({ action: 'stopQueueProcessing' });
    resetProcessingUI();
  }
  
  // Confirm before clearing
  const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
  const pendingCount = linkedinImportQueue.filter(item => item.status === 'pending').length;
  
  if (pendingCount === 0) {
    showError('No pending items to clear');
    return;
  }
  
  const confirmClear = confirm(`Are you sure you want to clear ${pendingCount} pending profiles from the queue?`);
  
  if (confirmClear) {
    const filtered = linkedinImportQueue.filter(item => item.status !== 'pending');
    await chrome.storage.local.set({ linkedinImportQueue: filtered });
    
    // Update badge
    chrome.runtime.sendMessage({
      action: 'updateQueueBadge',
      count: 0
    });
    
    await loadQueue();
  }
}

// Clear all items
async function clearAll() {
  // Check if processing is running
  const statusResponse = await chrome.runtime.sendMessage({ action: 'getProcessingStatus' });
  if (statusResponse.isProcessing) {
    const confirmStop = confirm('Queue processing is currently running. Do you want to stop processing and clear all items?');
    if (!confirmStop) {
      return;
    }
    
    // Stop processing first
    await chrome.runtime.sendMessage({ action: 'stopQueueProcessing' });
    resetProcessingUI();
  }
  
  // Confirm before clearing
  const { linkedinImportQueue = [] } = await chrome.storage.local.get('linkedinImportQueue');
  
  if (linkedinImportQueue.length === 0) {
    showError('Queue is already empty');
    return;
  }
  
  const confirmClear = confirm(`Are you sure you want to clear all ${linkedinImportQueue.length} profiles from the queue? This action cannot be undone.`);
  
  if (confirmClear) {
    await chrome.storage.local.set({ linkedinImportQueue: [] });
    
    // Update badge
    chrome.runtime.sendMessage({
      action: 'updateQueueBadge',
      count: 0
    });
    
    await loadQueue();
  }
}

// Utility function for delays
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Show error message with clickable URLs
function showError(message) {
  const errorEl = document.getElementById('error-message');
  
  if (!errorEl) {
    // If error element doesn't exist, fall back to alert
    alert(message);
    return;
  }
  
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