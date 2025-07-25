// Debug script - paste this in Chrome DevTools console while on LinkedIn

// Check if profiles are being marked as duplicates locally
async function debugImport() {
    console.log('=== DEBUG IMPORT ISSUE ===');
    
    // Check storage
    const storage = await chrome.storage.local.get();
    console.log('Chrome storage:', storage);
    
    // Check auth token
    console.log('Auth token:', storage.authToken ? 'Present' : 'Missing');
    
    // Try to manually call the import
    const testProfile = {
        linkedin_url: 'https://www.linkedin.com/in/yeshaswini-k-p-0252b2131',
        name: 'Yeshaswini K P',
        headline: 'Test',
        location: 'Test',
        about: '',
        experience: [],
        education: [],
        skills: [],
        years_experience: 0
    };
    
    console.log('Sending import request for:', testProfile.linkedin_url);
    
    try {
        const response = await chrome.runtime.sendMessage({
            action: 'importProfile',
            data: testProfile,
            authToken: storage.authToken
        });
        
        console.log('Import response:', response);
    } catch (error) {
        console.error('Import error:', error);
    }
}

// Run the debug
debugImport();