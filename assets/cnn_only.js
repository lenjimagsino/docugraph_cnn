/**
 * DOCUGRAPH CNN-Only Analysis Handler
 * Handles document upload, CNN-only analysis, and OCR extraction
 */

let currentFile = null;
let currentAnalysisData = null;
let startTime = null;

// ===== Page State Management =====
function showState(stateName) {
  const processingState = document.getElementById('processing-state');
  const resultsState = document.getElementById('results-state');
  const ocrState = document.getElementById('ocr-state');
  const initialState = document.getElementById('initial-state');

  // Hide all states
  if (processingState) processingState.style.display = 'none';
  if (resultsState) resultsState.style.display = 'none';
  if (ocrState) ocrState.style.display = 'none';
  if (initialState) initialState.style.display = 'none';

  // Show requested state
  if (stateName === 'processing' && processingState) processingState.style.display = 'block';
  if (stateName === 'results' && resultsState) resultsState.style.display = 'block';
  if (stateName === 'ocr' && ocrState) ocrState.style.display = 'block';
  if (stateName === 'initial' && initialState) initialState.style.display = 'block';
}

// ===== File Upload Handling =====
document.addEventListener('DOMContentLoaded', () => {
  // File input
  const fileInput = document.getElementById('file-input');
  const browseBtn = document.getElementById('browse-btn');
  const cameraBtn = document.getElementById('camera-btn');
  const removeBtn = document.getElementById('remove-file');
  const analyzeBtn = document.getElementById('analyze-btn');
  const ocrBtn = document.getElementById('ocr-btn');
  const newAnalysisBtn = document.getElementById('new-analysis-btn');
  const dropzone = document.getElementById('dropzone');
  const cameraModal = document.getElementById('camera-modal');
  const cameraClose = document.getElementById('camera-close');
  const cameraCloseFromBtn = document.querySelector('[id="camera-close"]');

  // Browse button
  if (browseBtn) {
    browseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });
  }

  // File input change
  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        handleFileSelected(e.target.files[0]);
      }
    });
  }

  // Drag and drop
  if (dropzone) {
    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.style.background = 'var(--green-50)';
      dropzone.style.borderColor = 'var(--green-500)';
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.style.background = '';
      dropzone.style.borderColor = '';
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.style.background = '';
      dropzone.style.borderColor = '';
      if (e.dataTransfer.files.length > 0) {
        handleFileSelected(e.dataTransfer.files[0]);
      }
    });

    dropzone.addEventListener('click', (e) => {
      // Don't trigger if clicking on a button inside the dropzone
      if (e.target.closest('button')) return;
      fileInput.click();
    });
  }

  // Remove file
  if (removeBtn) {
    removeBtn.addEventListener('click', () => {
      currentFile = null;
      document.getElementById('file-info').style.display = 'none';
      document.getElementById('action-buttons').style.display = 'none';
      if (fileInput) fileInput.value = '';
    });
  }

  // Analyze button
  if (analyzeBtn) {
    analyzeBtn.addEventListener('click', () => {
      if (currentFile) {
        performCNNAnalysis();
      }
    });
  }

  // OCR button
  if (ocrBtn) {
    ocrBtn.addEventListener('click', () => {
      performOCR();
    });
  }

  // New analysis button
  if (newAnalysisBtn) {
    newAnalysisBtn.addEventListener('click', () => {
      location.reload();
    });
  }

  // Camera functionality
  if (cameraBtn) {
    cameraBtn.addEventListener('click', () => {
      if (cameraModal) cameraModal.classList.add('active');
      initCamera();
    });
  }

  if (cameraClose || cameraCloseFromBtn) {
    const closeBtn = cameraClose || cameraCloseFromBtn;
    closeBtn?.addEventListener('click', () => {
      if (cameraModal) cameraModal.classList.remove('active');
      stopCamera();
    });
  }

  // Copy text button
  const copyTextBtn = document.getElementById('copy-text-btn');
  if (copyTextBtn) {
    copyTextBtn.addEventListener('click', () => {
      const textContent = document.getElementById('scanned-text-container')?.innerText || '';
      navigator.clipboard.writeText(textContent).then(() => {
        copyTextBtn.innerText = '✓ Copied!';
        setTimeout(() => {
          copyTextBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg> Copy Text';
        }, 2000);
      });
    });
  }

  // Comparison button
  const compareBtn = document.getElementById('compare-btn');
  if (compareBtn) {
    compareBtn.addEventListener('click', () => {
      window.location.href = 'comparison.html';
    });
  }
});

// Handle file selection
function handleFileSelected(file) {
  if (!file.type.startsWith('image/')) {
    alert('Please select an image file');
    return;
  }

  currentFile = file;
  document.getElementById('file-name').textContent = file.name;
  document.getElementById('file-size').textContent = (file.size / 1024 / 1024).toFixed(2) + ' MB';
  document.getElementById('file-info').style.display = 'block';
  document.getElementById('action-buttons').style.display = 'flex';
}

// ===== CNN Analysis =====
async function performCNNAnalysis() {
  if (!currentFile) return;

  startTime = Date.now();
  showState('processing');
  updateProgressStatus(0);

  const formData = new FormData();
  formData.append('image', currentFile);  // Backend expects 'image' field
  formData.append('mode', 'cnn-only');

  // Simulate progress updates
  const progressInterval = setInterval(() => {
    updateProgressStatus(Math.floor(Math.random() * 3));
  }, 500);

  try {
    // Create fetch with 30-second timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    console.log('🔄 Sending to backend:', window.BACKEND_URL);
    const response = await fetch(`${window.BACKEND_URL}/api/analyze`, {
      method: 'POST',
      body: formData,
      signal: controller.signal
    });

    clearTimeout(timeoutId);
    clearInterval(progressInterval);

    if (!response.ok) {
      throw new Error(`Analysis failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✓ Backend response:', data);
    
    if (!data.success && data.error) {
      throw new Error(data.error);
    }

    currentAnalysisData = data;

    // Simulate final steps
    for (let i = 0; i < 5; i++) {
      updateProgressStatus(i);
      await new Promise(r => setTimeout(r, 100));
    }

    displayAnalysisResults(data);
    showState('results');

    // Update elapsed time
    const elapsed = Math.round((Date.now() - startTime) / 1000);
    document.getElementById('analysis-time').textContent = (elapsed * 1000) + 'ms';

    // Save to session storage for results page
    sessionStorage.setItem('cnnAnalysisResults', JSON.stringify(data));

  } catch (error) {
    console.error('❌ Analysis error:', error);
    clearInterval(progressInterval);
    
    // Better error messaging
    let errorMsg = error.message;
    if (error.name === 'AbortError') {
      errorMsg = 'Request timeout (>30s). Backend may be unavailable or processing is taking too long.';
    } else if (errorMsg.includes('Failed to fetch')) {
      errorMsg = `Cannot connect to backend at ${window.BACKEND_URL}. Make sure the backend server is running.`;
    }
    
    alert('⚠️ Analysis Error:\n\n' + errorMsg + '\n\n✓ Tip: Start the backend with:\npython backend/app.py');
    showState('initial');
  }
}

// Update progress status
function updateProgressStatus(step) {
  const statusItems = document.querySelectorAll('#status li');
  const statusList = document.getElementById('status');
  
  if (statusItems && statusItems.length > 0) {
    statusItems.forEach((item, idx) => {
      if (idx <= step && step < statusItems.length) {
        item.classList.add('done');
        const checkSpan = item.querySelector('.check');
        if (checkSpan) checkSpan.textContent = '✓';
      }
    });
  }

  // Update elapsed time
  if (startTime) {
    const seconds = Math.floor((Date.now() - startTime) / 1000);
    const elapsedSpan = document.getElementById('elapsed');
    if (elapsedSpan) {
      elapsedSpan.textContent = 
        String(Math.floor(seconds / 60)).padStart(2, '0') + ':' + 
        String(seconds % 60).padStart(2, '0');
    }
  }
}

// Display analysis results
function displayAnalysisResults(data) {
  // Display input image
  if (currentFile) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = document.getElementById('input-image');
      if (img) {
        img.src = e.target.result;
        img.style.display = 'block';
      }
    };
    reader.readAsDataURL(currentFile);
  }

  // Display bounding boxes
  if (data.predictions && data.predictions.length > 0) {
    displayBoundingBoxes(data.predictions);
    const placeholder = document.getElementById('preview-placeholder');
    if (placeholder) placeholder.style.display = 'none';
  }

  // Update statistics
  const stats = data.statistics || {};
  const totalBlocks = stats.total_blocks || 0;
  const avgConf = stats.avg_confidence || 0;
  const typeDistribution = stats.type_distribution || {};

  // Update count elements
  const regionCountEl = document.getElementById('region-count');
  const confScoreEl = document.getElementById('confidence-score');
  const cnnConfEl = document.getElementById('cnn-confidence');
  const headerCountEl = document.getElementById('header-count');
  const paraCountEl = document.getElementById('para-count');
  const tableCountEl = document.getElementById('table-count');
  const cnnRegionsEl = document.getElementById('cnn-regions');
  const cnnAvgConfEl = document.getElementById('cnn-avg-conf');
  const cnnFeaturesEl = document.getElementById('cnn-features');

  if (regionCountEl) regionCountEl.textContent = totalBlocks;
  if (confScoreEl) confScoreEl.textContent = Math.round(avgConf * 100) + '%';
  if (cnnConfEl) cnnConfEl.textContent = Math.round(avgConf * 100) + '%';
  if (headerCountEl) headerCountEl.textContent = typeDistribution['Title'] || 0;
  if (paraCountEl) paraCountEl.textContent = typeDistribution['Text'] || 0;
  if (tableCountEl) tableCountEl.textContent = (typeDistribution['Table'] || 0) + (typeDistribution['Figure'] || 0);

  // Update metrics panel
  if (cnnRegionsEl) cnnRegionsEl.textContent = totalBlocks;
  if (cnnAvgConfEl) cnnAvgConfEl.textContent = Math.round(avgConf * 100) + '%';
  if (cnnFeaturesEl) cnnFeaturesEl.textContent = Object.keys(typeDistribution).length;
}

// Display bounding boxes
function displayBoundingBoxes(predictions) {
  const container = document.getElementById('bbox-container');
  if (!container) return;

  container.innerHTML = '';

  predictions.forEach((pred, idx) => {
    const bbox = document.createElement('div');
    const typeStr = (pred.type || 'para').toLowerCase();
    bbox.className = 'bbox ' + typeStr;
    
    const [x1, y1, x2, y2] = pred.bbox;
    const width = x2 - x1;
    const height = y2 - y1;
    const confidence = pred.confidence || 0;

    // Apply coordinates as percentages
    bbox.style.left = x1 + '%';
    bbox.style.top = y1 + '%';
    bbox.style.width = width + '%';
    bbox.style.height = height + '%';

    bbox.textContent = `${pred.type} (${(confidence * 100).toFixed(0)}%)`;
    container.appendChild(bbox);
  });
}

// ===== OCR Extraction =====
async function performOCR() {
  if (!currentAnalysisData) return;

  document.getElementById('scanned-text-container').innerHTML = '<p style="text-align:center;">Extracting text...</p>';

  try {
    // Use Tesseract.js for OCR
    if (typeof Tesseract !== 'undefined') {
      const { createWorker } = Tesseract;
      const worker = await createWorker();

      // Get image from current file
      const reader = new FileReader();
      reader.onload = async (e) => {
        const result = await worker.recognize(e.target.result);
        const extractedText = result.data.text;

        document.getElementById('scanned-text-container').textContent = extractedText;
        await worker.terminate();

        // Save OCR result
        currentAnalysisData.ocrText = extractedText;

        showState('ocr');
      };
      reader.readAsDataURL(currentFile);
    } else {
      throw new Error('Tesseract.js not loaded');
    }
  } catch (error) {
    console.error('OCR error:', error);
    document.getElementById('scanned-text-container').innerHTML = 
      '<p style="color:var(--red-700);">Error during OCR: ' + error.message + '</p>';
  }
}

// ===== Camera Functionality =====
let cameraStream = null;

async function initCamera() {
  const cameraSetup = document.getElementById('camera-setup');
  const cameraLive = document.getElementById('camera-live');
  const cameraError = document.getElementById('camera-error');

  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    const video = document.getElementById('camera-video');
    video.srcObject = cameraStream;

    cameraSetup.style.display = 'none';
    cameraLive.style.display = 'block';
    cameraError.style.display = 'none';

    // Snap button
    document.getElementById('camera-snap')?.addEventListener('click', snapPhoto);

  } catch (error) {
    console.error('Camera error:', error);
    cameraSetup.style.display = 'none';
    cameraError.style.display = 'block';
    cameraLive.style.display = 'none';
  }
}

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(track => track.stop());
    cameraStream = null;
  }
}

function snapPhoto() {
  const video = document.getElementById('camera-video');
  const canvas = document.getElementById('camera-canvas');
  const ctx = canvas.getContext('2d');

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  ctx.drawImage(video, 0, 0);

  const imageData = canvas.toDataURL('image/jpeg');
  document.getElementById('camera-captured').src = imageData;

  document.getElementById('camera-live').style.display = 'none';
  document.getElementById('camera-review').style.display = 'block';

  // Buttons
  document.getElementById('camera-retake')?.addEventListener('click', () => {
    document.getElementById('camera-live').style.display = 'block';
    document.getElementById('camera-review').style.display = 'none';
  });

  document.getElementById('camera-confirm')?.addEventListener('click', () => {
    // Convert data URL to file
    fetch(imageData)
      .then(res => res.blob())
      .then(blob => {
        currentFile = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' });
        document.getElementById('file-name').textContent = 'camera-capture.jpg';
        document.getElementById('file-size').textContent = (blob.size / 1024 / 1024).toFixed(2) + ' MB';
        document.getElementById('file-info').style.display = 'block';
        document.getElementById('action-buttons').style.display = 'flex';

        // Close camera modal
        document.getElementById('camera-modal').classList.remove('active');
        stopCamera();
      });
  });
}

// ===== Results Page Functionality =====
if (window.location.pathname.includes('results_cnn.html')) {
  document.addEventListener('DOMContentLoaded', () => {
    // Load results from session storage or localStorage
    const savedResults = sessionStorage.getItem('cnnAnalysisResults');
    if (savedResults) {
      const data = JSON.parse(savedResults);
      loadResultsPage(data);
    }
  });
}

function loadResultsPage(data) {
  // Display metrics
  const stats = data.statistics || {};
  document.getElementById('cnn-regions').textContent = stats.total_blocks || 0;
  document.getElementById('cnn-avg-conf').textContent = Math.round(stats.avg_confidence * 100) + '%';
  
  document.getElementById('total-regions').textContent = stats.total_blocks || 0;
  document.getElementById('avg-confidence').textContent = Math.round(stats.avg_confidence * 100) + '%';

  const typeDistribution = stats.type_distribution || {};
  document.getElementById('header-count').textContent = typeDistribution['Title'] || 0;
  document.getElementById('para-count').textContent = typeDistribution['Text'] || 0;
  document.getElementById('table-count').textContent = (typeDistribution['Table'] || 0) + (typeDistribution['Figure'] || 0);

  // Display extracted text
  if (data.ocrText) {
    document.getElementById('extracted-text').textContent = data.ocrText;
  }
}

// Save results before leaving page
window.addEventListener('beforeunload', () => {
  if (currentAnalysisData) {
    sessionStorage.setItem('cnnAnalysisResults', JSON.stringify(currentAnalysisData));
  }
});
