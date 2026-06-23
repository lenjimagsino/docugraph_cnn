/**
 * DOCUGRAPH CNN-Only Configuration
 * Update BACKEND_URL with your deployed backend URL
 */

window.CONFIG = {
  // Production backend URL on Railway
  BACKEND_URL_PRODUCTION: 'https://docugraphcnn-production.up.railway.app',
  
  // Local development URL (used when running on localhost)
  BACKEND_URL_LOCAL: 'http://localhost:5000',
  
  // Analysis mode
  ANALYSIS_MODE: 'cnn-only',
  
  // API timeout in milliseconds
  API_TIMEOUT: 30000,
  
  // Get the appropriate backend URL based on environment
  getBackendURL() {
    const hostname = window.location.hostname;
    
    // Use local backend for local development
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return this.BACKEND_URL_LOCAL;
    }
    
    // Use production backend for GitHub Pages and other deployments
    return this.BACKEND_URL_PRODUCTION;
  },
  
  // Check if backend is configured
  isBackendConfigured() {
    return this.BACKEND_URL_PRODUCTION !== 'https://docugraph-cnn-api.up.railway.app' 
      || window.location.hostname === 'localhost';
  }
};

// Set window.BACKEND_URL for compatibility with existing code
window.BACKEND_URL = window.CONFIG.getBackendURL();
