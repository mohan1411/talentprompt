import { makeRequest } from './client'

export const authApi = {
  // Extension token methods
  async generateExtensionToken(): Promise<{
    access_token: string
    expires_in: number
    message: string
  }> {
    return await makeRequest('/auth/generate-extension-token', {
      method: 'POST'
    })
  },
  
  async getExtensionTokenStatus(): Promise<{
    has_token: boolean
    ttl: number
    is_oauth_user: boolean
  }> {
    return await makeRequest('/auth/extension-token-status')
  },
  
  async revokeExtensionToken(): Promise<{ message: string }> {
    return await makeRequest('/auth/revoke-extension-token', {
      method: 'DELETE'
    })
  }
}