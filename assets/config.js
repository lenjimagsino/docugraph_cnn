/**
 * DOCUGRAPH CNN-Only Configuration
 * Backend running locally on http://localhost:5000
 */

window.CONFIG = {
  BACKEND_URL: 'http://localhost:5000',
  ANALYSIS_MODE: 'cnn-only',
  API_TIMEOUT: 30000,
  
  getBackendURL() {
    return this.BACKEND_URL;
  }
};

// Set window.BACKEND_URL for compatibility with existing code
window.BACKEND_URL = window.CONFIG.BACKEND_URL;
