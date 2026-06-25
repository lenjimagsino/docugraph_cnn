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

  // Download PDF button
  const downloadPdfBtn = document.getElementById('download-pdf-btn');
  if (downloadPdfBtn) {
    downloadPdfBtn.addEventListener('click', () => {
      downloadResultsPdf();
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

function formatPercent(value) {
  return `${Math.round(value * 100)}%`;
}

function formatReportDate() {
  return new Date().toLocaleString([], {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

async function downloadResultsPdf() {
  if (!currentAnalysisData) {
    // Try to load results from sessionStorage (results page flow)
    const saved = sessionStorage.getItem('cnnAnalysisResults');
    if (saved) {
      currentAnalysisData = JSON.parse(saved);
    }

    if (!currentAnalysisData) {
      alert('Please run the analysis first before downloading the PDF report.');
      return;
    }
  }

  const { predictions = [], statistics = {}, model = 'CNN-only' } = unwrapData(currentAnalysisData);
  const title = 'DOCUGRAPH CNN-Only Report';
  const filename = `docugraph-cnn-report-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.pdf`;

  // Ensure jsPDF is available (works with UMD build where constructor may be at window.jspdf.jsPDF)
  async function ensureJsPDF() {
    if (typeof window.jsPDF === 'function') return window.jsPDF;
    if (window.jspdf && typeof window.jspdf.jsPDF === 'function') return window.jspdf.jsPDF;

    // Try to load from CDN as a fallback
    const src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
    if (!document.querySelector(`script[src="${src}"]`)) {
      await new Promise((resolve, reject) => {
        const s = document.createElement('script');
        s.src = src;
        s.crossOrigin = 'anonymous';
        s.onload = resolve;
        s.onerror = () => reject(new Error('Failed to load jsPDF from CDN'));
        document.head.appendChild(s);
      }).catch((e) => {
        console.warn('Could not load jsPDF dynamically:', e);
      });
    }

    if (typeof window.jsPDF === 'function') return window.jsPDF;
    if (window.jspdf && typeof window.jspdf.jsPDF === 'function') return window.jspdf.jsPDF;
    return null;
  }

  const jsPDFCtor = await ensureJsPDF();
  if (!jsPDFCtor) {
    alert('PDF library (jsPDF) is not available. Please check network or include the library.');
    return;
  }

  const doc = new jsPDFCtor({ unit: 'pt', format: 'letter' });
  const margin = 40;
  let y = margin;

  doc.setFontSize(18);
  doc.setTextColor('#1f2937');
  doc.text(title, margin, y);

  doc.setFontSize(10);
  doc.setTextColor('#6b7280');
  doc.text(`Generated: ${formatReportDate()}`, margin, y + 20);
  doc.text(`Backend URL: ${window.BACKEND_URL}`, margin, y + 36);

  y += 60;
  doc.setFontSize(14);
  doc.setTextColor('#111827');
  doc.text('Analysis Summary', margin, y);

  y += 20;
  doc.setFontSize(10);
  const summaryLines = [
    `Analysis Mode: ${model}`,
    `Regions Detected: ${statistics.total_blocks || 0}`,
    `Average Confidence: ${formatPercent(statistics.avg_confidence || 0)}`,
    `Headers: ${statistics.type_distribution?.Title || 0}`,
    `Paragraphs: ${statistics.type_distribution?.Text || 0}`,
    `Tables/Figures: ${(statistics.type_distribution?.Table || 0) + (statistics.type_distribution?.Figure || 0)}`
  ];
  summaryLines.forEach((line) => {
    doc.text(line, margin, y);
    y += 16;
  });

  y += 10;
  doc.setDrawColor('#d1d5db');
  doc.setLineWidth(0.5);
  doc.line(margin, y, 555, y);
  y += 20;

  doc.setFontSize(14);
  doc.setTextColor('#111827');
  doc.text('Detected Regions', margin, y);
  y += 18;

  doc.setFontSize(9);
  doc.setTextColor('#374151');
  doc.text('Type', margin, y);
  doc.text('Confidence', 180, y);
  doc.text('BBox', 300, y);
  y += 12;
  doc.setDrawColor('#e5e7eb');
  doc.line(margin, y, 555, y);
  y += 10;

  const maxRows = 18;
  const regionRows = predictions.slice(0, maxRows);
  regionRows.forEach((pred) => {
    const type = pred.type || 'Unknown';
    const confidence = formatPercent(pred.confidence || 0);
    const bbox = Array.isArray(pred.bbox) ? pred.bbox.map((coord) => Math.round(coord)).join(', ') : 'N/A';

    doc.text(type, margin, y);
    doc.text(confidence, 180, y);
    doc.text(bbox, 300, y);
    y += 14;

    if (y > 720) {
      doc.addPage();
      y = margin;
    }
  });

  if (predictions.length > maxRows) {
    doc.setTextColor('#6b7280');
    doc.text(`...and ${predictions.length - maxRows} more regions`, margin, y + 10);
  }

  const textBlock = document.getElementById('scanned-text-container')?.innerText.trim();
  if (textBlock) {
    y += 28;
    if (y > 720) {
      doc.addPage();
      y = margin;
    }

    doc.setFontSize(14);
    doc.setTextColor('#111827');
    doc.text('Extracted Text', margin, y);
    y += 18;
    doc.setFontSize(10);
    doc.setTextColor('#374151');

    const splitText = doc.splitTextToSize(textBlock, 515);
    doc.text(splitText, margin, y);
  }

  // Try embed preview image (input image + bbox overlay) at the top of the report
  try {
    const previewData = await capturePreviewImage();
    if (previewData) {
      // Insert image at top of first page (scale to fit width)
      const imgProps = doc.getImageProperties(previewData);
      const pdfWidth = doc.internal.pageSize.getWidth() - margin * 2;
      const aspect = imgProps.height / imgProps.width;
      const imgHeight = Math.min(300, pdfWidth * aspect);

      // Move existing content down if we're still on first page
      // Create a new page to place the image at the top for simpler layout
      doc.addPage();
      doc.setPage(doc.getNumberOfPages());
      doc.addImage(previewData, 'JPEG', margin, margin, pdfWidth, imgHeight);
      // Return to page 1 to keep textual summary as before
      doc.setPage(1);
    }
  } catch (e) {
    console.warn('Could not embed preview image into PDF:', e);
  }

  doc.save(filename);
}

// Capture input image and draw bounding boxes onto a canvas, return dataURL
async function capturePreviewImage() {
  try {
    // Prefer using the currentFile if available
    let dataUrl;
    if (currentFile) dataUrl = await fileToDataUrl(currentFile);
    else {
      const imgEl = document.getElementById('input-image');
      if (imgEl && imgEl.src) dataUrl = imgEl.src;
    }

    if (!dataUrl) return null;

    const img = await new Promise((res, rej) => {
      const i = new Image();
      i.onload = () => res(i);
      i.onerror = rej;
      i.src = dataUrl;
    });

    // Determine canvas size (limit to reasonable width)
    const maxWidth = 1200;
    const scale = Math.min(1, maxWidth / img.width);
    const cw = Math.round(img.width * scale);
    const ch = Math.round(img.height * scale);

    const canvas = document.createElement('canvas');
    canvas.width = cw;
    canvas.height = ch;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, cw, ch);
    ctx.drawImage(img, 0, 0, cw, ch);

    // Draw bounding boxes if available
    const raw = unwrapData(currentAnalysisData || {});
    const preds = raw.predictions || [];
    if (preds.length > 0) {
      // Heuristic whether bbox are percent (0-100) or pixels
      const maxCoord = preds.reduce((m, p) => Math.max(m, ...(p.bbox || [])), 0);
      const usePercent = maxCoord <= 100;

      preds.forEach((p) => {
        const bbox = p.bbox || [0,0,0,0];
        let x1 = bbox[0], y1 = bbox[1], x2 = bbox[2], y2 = bbox[3];
        if (usePercent) {
          x1 = (x1 / 100) * cw;
          x2 = (x2 / 100) * cw;
          y1 = (y1 / 100) * ch;
          y2 = (y2 / 100) * ch;
        } else {
          const imgW = raw.statistics?.image_shape?.[1] || img.width;
          const imgH = raw.statistics?.image_shape?.[0] || img.height;
          const sx = cw / imgW;
          const sy = ch / imgH;
          x1 = x1 * sx; y1 = y1 * sy; x2 = x2 * sx; y2 = y2 * sy;
        }

        const w = x2 - x1;
        const h = y2 - y1;
        ctx.lineWidth = Math.max(2, Math.round(Math.min(cw, ch) / 200));
        ctx.strokeStyle = 'rgba(124,58,237,0.95)';
        ctx.fillStyle = 'rgba(124,58,237,0.08)';
        ctx.strokeRect(x1, y1, w, h);
        ctx.fillRect(x1, y1, w, h);

        // Label
        const label = (p.type || 'region') + ' ' + Math.round((p.confidence||0)*100) + '%';
        ctx.fillStyle = 'rgba(0,0,0,0.7)';
        ctx.font = '14px sans-serif';
        const textW = ctx.measureText(label).width + 8;
        ctx.fillRect(x1, Math.max(0, y1 - 20), textW, 18);
        ctx.fillStyle = '#fff';
        ctx.fillText(label, x1 + 4, Math.max(0, y1 - 6));
      });
    }

    return canvas.toDataURL('image/jpeg', 0.9);
  } catch (e) {
    console.warn('capturePreviewImage failed', e);
    return null;
  }
}

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
    // Create fetch with 60-second timeout (Detectron2 model loads on first run)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    console.log('🔄 Sending to backend:', window.BACKEND_URL);
    const endpoint = `${window.BACKEND_URL}/api/analyze/cnn`;
    let response;
    try {
      response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
        signal: controller.signal
      });
    } catch (e) {
      // Fallback to /api/analyze if /api/analyze/cnn doesn't exist
      console.log('ℹ Endpoint /api/analyze/cnn not found, falling back to /api/analyze');
      response = await fetch(`${window.BACKEND_URL}/api/analyze`, {
        method: 'POST',
        body: formData,
        signal: controller.signal
      });
    }

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
    const analysisTimeEl = document.getElementById('analysis-time');
    if (analysisTimeEl) analysisTimeEl.textContent = (elapsed * 1000) + 'ms';

    // Save to session storage for results page
    sessionStorage.setItem('cnnAnalysisResults', JSON.stringify(data));

  } catch (error) {
    console.error('❌ Analysis error:', error);
    clearInterval(progressInterval);
    
    // Better error messaging
    let errorMsg = error.message;
    if (error.name === 'AbortError') {
      errorMsg = 'Request timeout (>60s). The Detectron2 model is still loading or the backend is processing. Try again in a moment.';
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

// ── FIX: unpack nested layout_analysis wrapper if present ──
function unwrapData(raw) {
  // If the backend returns the full CNNOnlyAnalyzer dict, pull the inner layout result
  if (raw.layout_analysis) {
    const inner = raw.layout_analysis;
    return {
      success:     inner.success,
      predictions: inner.predictions || [],
      statistics:  inner.statistics  || {},
      model:       inner.model       || raw.model_variant || 'CNN-only',
      feature_maps: inner.feature_maps || {},
      shape_detection: raw.shape_detection,
      features:        raw.features,
      ocrText:         raw.ocrText || ''
    };
  }
  // Already flat (direct endpoint response)
  return raw;
}

// Display analysis results
function displayAnalysisResults(rawData) {
  const data = unwrapData(rawData);
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
    // Get image dimensions from statistics (needed to normalize pixel coords)
    const imgShape = data.statistics.image_shape || [];
    const imgH = imgShape[0] || 0;
    const imgW = imgShape[1] || 0;
    displayBoundingBoxes(data.predictions, imgW, imgH);
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

// Display bounding boxes with proper coordinate normalization
function displayBoundingBoxes(predictions, imgW, imgH) {
  const container = document.getElementById('bbox-container');
  if (!container) return;

  container.innerHTML = '';

  // Determine if coords are already 0-100 (%) or raw pixels
  // Heuristic: if max coordinate > 100, treat as pixels
  const maxCoord = predictions.reduce((m, p) => Math.max(m, ...p.bbox), 0);
  const usePercent = maxCoord <= 100;

  predictions.forEach((pred) => {
    const bbox = document.createElement('div');
    const typeStr = (pred.type || 'para').toLowerCase();
    bbox.className = 'bbox ' + typeStr;
    
    const [x1, y1, x2, y2] = pred.bbox;
    let left, top, width, height;

    if (usePercent) {
      // Already normalized to %
      left = x1;
      top = y1;
      width = x2 - x1;
      height = y2 - y1;
    } else {
      // Convert raw pixels to % using image dimensions
      if (imgW > 0 && imgH > 0) {
        left = (x1 / imgW) * 100;
        top = (y1 / imgH) * 100;
        width = ((x2 - x1) / imgW) * 100;
        height = ((y2 - y1) / imgH) * 100;
      } else {
        // Fallback if dimensions not available
        left = x1;
        top = y1;
        width = x2 - x1;
        height = y2 - y1;
      }
    }

    const confidence = pred.confidence || 0;

    bbox.style.left = left + '%';
    bbox.style.top = top + '%';
    bbox.style.width = width + '%';
    bbox.style.height = height + '%';

    bbox.textContent = `${pred.type} (${(confidence * 100).toFixed(0)}%)`;
    container.appendChild(bbox);
  });
}

// ===== OCR Extraction =====
async function performOCR() {
  if (!currentAnalysisData) return;

  const container = document.getElementById('scanned-text-container');
  if (container) container.innerHTML = '<p style="text-align:center; color:var(--ink-500);">Extracting text with Tesseract…</p>';

  try {
    if (typeof Tesseract === 'undefined') {
      throw new Error('Tesseract.js not loaded');
    }

    const imageDataUrl = await fileToDataUrl(currentFile);

    const { createWorker } = Tesseract;
    const worker = await createWorker('eng');

    const result = await worker.recognize(imageDataUrl);
    await worker.terminate();

    const extractedText = result.data.text || '(No text detected)';

    if (container) {
      container.textContent = extractedText;
    }
    currentAnalysisData.ocrText = extractedText;

    // ── now switch state, after everything is done ──
    showState('ocr');

  } catch (error) {
    console.error('OCR error:', error);
    if (container) {
      container.innerHTML = '<p style="color:var(--red-700);">Error during OCR: ' + error.message + '</p>';
    }
  }
}

// Helper: FileReader as a Promise
function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload  = (e) => resolve(e.target.result);
    reader.onerror = ()  => reject(new Error('Could not read file'));
    reader.readAsDataURL(file);
  });
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

    // Wire download button on results page
    const downloadResultsBtn = document.getElementById('download-results-btn');
    if (downloadResultsBtn) {
      downloadResultsBtn.addEventListener('click', () => {
        // Ensure currentAnalysisData is populated for the PDF generator
        const saved = sessionStorage.getItem('cnnAnalysisResults');
        if (saved) currentAnalysisData = JSON.parse(saved);
        downloadResultsPdf();
      });
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
