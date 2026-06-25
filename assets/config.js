/**
 * DOCUGRAPH CNN-Only Configuration
 * Backend running locally on http://localhost:5000
 */

window.CONFIG = {
  BACKEND_URL: 'http://localhost:5000',
  BACKEND_URL_PRODUCTION: 'https://docugraph-cnn-api.up.railway.app',
  ANALYSIS_MODE: 'cnn-only',
  API_TIMEOUT: 30000,

  getBackendURL() {
    const isLocalhost = ['localhost', '127.0.0.1'].includes(window.location.hostname);
    const isFileProtocol = window.location.protocol === 'file:';

    if (isFileProtocol || isLocalhost) {
      return this.BACKEND_URL;
    }

    return this.BACKEND_URL_PRODUCTION || this.BACKEND_URL;
  }
};

// Set window.BACKEND_URL for compatibility with existing code
window.BACKEND_URL = window.CONFIG.getBackendURL();
