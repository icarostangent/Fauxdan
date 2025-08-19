// Hardcode the API base URL for production
export const API_BASE_URL = process.env.VUE_APP_API_URL || 'not configured'

export const API_ENDPOINTS = {
  hosts: `${API_BASE_URL}/api/hosts`,
  search: `${API_BASE_URL}/api/search`,
}
