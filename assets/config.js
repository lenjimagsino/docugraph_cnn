/**
 * DOCUGRAPH CNN-Only Configuration
 * Running locally - Backend on http://localhost:5000
 */

window.CONFIG = {
  BACKEND_URL: 'http://localhost:5000',
  ANALYSIS_MODE: 'cnn-only',
  API_TIMEOUT: 30000
};

// Set window.BACKEND_URL for compatibility with existing code
window.BACKEND_URL = window.CONFIG.BACKEND_URL;
