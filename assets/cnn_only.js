/**
 * DOCUGRAPH CNN-Only Analysis Handler
 * Handles document upload, CNN-only analysis, and OCR extraction
 */

let currentFile = null;
let currentAnalysisData = null;
let startTime = null;
let usePdfConversion = false;
let currentConvertedPages = [];
let selectedConvertedPageIndex = null;
// Separate state for PDF-only conversion panel
let currentPdfOnlyFile = null;
let currentPdfOnlyConvertedPages = [];
let selectedPdfOnlyPageIndex = null;
// Track the source info for the current analysis (original filename, page, pdf flag)
let currentAnalysisSource = null;

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
  const imageYesBtn = document.getElementById('image-yes-btn');
  const imageNoBtn = document.getElementById('image-no-btn');
  const imageChoiceText = document.getElementById('image-choice-text');
  const pdfConverterPanel = document.getElementById('pdf-converter-panel');

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

  // Image/PDF choice buttons
  if (imageYesBtn) {
    imageYesBtn.addEventListener('click', () => setUsePdfConversion(false));
  }
  if (imageNoBtn) {
    imageNoBtn.addEventListener('click', () => setUsePdfConversion(true));
  }

  // Initialize upload mode
  setUsePdfConversion(false);

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

  const convertBtn = document.getElementById('convert-btn');
  const downloadAllZipBtn = document.getElementById('download-all-zip-btn');

  // Convert PDF pages button
  if (convertBtn) {
    convertBtn.addEventListener('click', () => {
      convertPdfPages();
    });
  }

  if (downloadAllZipBtn) {
    downloadAllZipBtn.addEventListener('click', () => {
      downloadAllConvertedPagesZip();
    });
  }

  // PDF-only panel elements
  const pdfOnlyInput = document.getElementById('pdf-only-input');
  const pdfOnlyConvertBtn = document.getElementById('pdf-only-convert-btn');
  const pdfOnlyDownloadZipBtn = document.getElementById('pdf-only-download-zip-btn');

  if (pdfOnlyInput) {
    pdfOnlyInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        currentPdfOnlyFile = e.target.files[0];
        // Show convert button when a PDF is selected
        if (pdfOnlyConvertBtn) pdfOnlyConvertBtn.style.display = 'inline-flex';
        if (pdfOnlyDownloadZipBtn) pdfOnlyDownloadZipBtn.style.display = 'none';
        const panel = document.getElementById('pdf-only-conversion-results');
        if (panel) panel.style.display = 'none';
      }
    });
  }

  if (pdfOnlyConvertBtn) {
    pdfOnlyConvertBtn.addEventListener('click', () => {
      convertPdfOnlyPages();
    });
  }

  if (pdfOnlyDownloadZipBtn) {
    pdfOnlyDownloadZipBtn.addEventListener('click', () => {
      downloadAllPdfOnlyConvertedPagesZip();
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

  const { predictions = [], statistics = {}, model = 'CNN-only', features = {}, metadata = {} } = unwrapData(currentAnalysisData);
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
    `Tables/Figures: ${(statistics.type_distribution?.Table || 0) + (statistics.type_distribution?.Figure || 0)}`,
    `Analysis Type: ${metadata.analysis_type || 'CNN-only'}`,
    `Image Shape: ${metadata.image_shape?.join('×') || 'N/A'}`,
    `Adjacency Count: ${features.connectivity_features?.adjacency_count || 0}`,
    `Reading Order Blocks: ${features.connectivity_features?.reading_order?.length || 0}`
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

// File helper utilities
function isPdf(file) {
  return Boolean(file && (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')));
}

function isImageFile(file) {
  return Boolean(file && (file.type.startsWith('image/') || /\.(jpg|jpeg|png|webp|bmp)$/i.test(file.name)));
}

function setUsePdfConversion(enabled) {
  usePdfConversion = enabled;

  const yesBtn = document.getElementById('image-yes-btn');
  const noBtn = document.getElementById('image-no-btn');
  const choiceText = document.getElementById('image-choice-text');
  const converterPanel = document.getElementById('pdf-converter-panel');
  const fileInputEl = document.getElementById('file-input');

  if (yesBtn && noBtn) {
    yesBtn.classList.toggle('active', !enabled);
    noBtn.classList.toggle('active', enabled);
  }

  if (choiceText) {
    choiceText.textContent = enabled
      ? 'Upload a PDF and convert pages into images for download or CNN analysis.'
      : 'Upload a JPG / PNG / WebP / BMP image directly for analysis.';
  }

  if (converterPanel) {
    converterPanel.style.display = enabled ? 'block' : 'none';
  }

  if (fileInputEl) {
    fileInputEl.accept = enabled ? '.pdf' : '.jpg,.jpeg,.png,.webp,.bmp';
    fileInputEl.value = '';
  }

  // Clear any previously selected file or conversion state when switching mode
  currentFile = null;
  currentConvertedPages = [];
  selectedConvertedPageIndex = null;

  const fileInfo = document.getElementById('file-info');
  const actionButtons = document.getElementById('action-buttons');
  const conversionResults = document.getElementById('conversion-results');
  const convertBtn = document.getElementById('convert-btn');
  const analyzeBtn = document.getElementById('analyze-btn');
  const downloadAllZipBtn = document.getElementById('download-all-zip-btn');

  if (fileInfo) fileInfo.style.display = 'none';
  if (actionButtons) actionButtons.style.display = 'none';
  if (conversionResults) conversionResults.style.display = 'none';
  if (convertBtn) convertBtn.style.display = enabled ? 'inline-flex' : 'none';
  if (analyzeBtn) analyzeBtn.style.display = enabled ? 'none' : 'inline-flex';
  if (downloadAllZipBtn) downloadAllZipBtn.style.display = 'none';
}

async function ensurePdfjs() {
  if (window.pdfjsLib) return window.pdfjsLib;

  const src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.122/pdf.min.js';
  if (!document.querySelector(`script[src="${src}"]`)) {
    await new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = src;
      s.crossOrigin = 'anonymous';
      s.onload = resolve;
      s.onerror = () => reject(new Error('Failed to load PDF.js from CDN'));
      document.head.appendChild(s);
    });
  }

  if (window.pdfjsLib) {
    if (window.pdfjsLib.GlobalWorkerOptions) {
      window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.122/pdf.worker.min.js';
    }
    return window.pdfjsLib;
  }

  return null;
}

// Handle file selection
async function handleFileSelected(file, options = {}) {
  if (usePdfConversion) {
    if (!isPdf(file)) {
      alert('Please select a PDF file for conversion.');
      return;
    }
  } else {
    if (!isImageFile(file)) {
      alert('Please select an image file.');
      return;
    }
  }

  currentFile = file;
  currentConvertedPages = [];
  selectedConvertedPageIndex = null;
  // Record source metadata for analysis traceability
  currentAnalysisSource = {
    filename: file.name,
    size: file.size,
    type: file.type || (isPdf(file) ? 'application/pdf' : 'image/*'),
    isPdf: isPdf(file),
    uploadedAt: new Date().toISOString()
  };
  document.getElementById('file-name').textContent = file.name;
  document.getElementById('file-size').textContent = (file.size / 1024 / 1024).toFixed(2) + ' MB';
  document.getElementById('file-info').style.display = 'block';
  // Show action buttons when a file is selected
  const actionButtonsEl = document.getElementById('action-buttons');
  if (actionButtonsEl) actionButtonsEl.style.display = 'flex';
  document.getElementById('file-info').style.borderColor = usePdfConversion ? 'var(--green-500)' : '';
  document.getElementById('file-info').style.background = usePdfConversion ? 'var(--green-50)' : '';

  const convertBtn = document.getElementById('convert-btn');
  const analyzeBtn = document.getElementById('analyze-btn');
  const downloadAllZipBtn = document.getElementById('download-all-zip-btn');

  if (usePdfConversion) {
    if (convertBtn) convertBtn.style.display = 'inline-flex';
    if (analyzeBtn) analyzeBtn.style.display = 'none';
    if (downloadAllZipBtn) downloadAllZipBtn.style.display = 'none';
    document.getElementById('conversion-results').style.display = 'none';
  } else {
    if (convertBtn) convertBtn.style.display = 'none';
    if (analyzeBtn) analyzeBtn.style.display = 'inline-flex';
    if (downloadAllZipBtn) downloadAllZipBtn.style.display = 'none';
    document.getElementById('conversion-results').style.display = 'none';
  }
}

async function ensureJSZip() {
  if (window.JSZip) return window.JSZip;
  const src = 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';
  if (!document.querySelector(`script[src="${src}"]`)) {
    await new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = src;
      s.crossOrigin = 'anonymous';
      s.onload = resolve;
      s.onerror = () => reject(new Error('Failed to load JSZip from CDN'));
      document.head.appendChild(s);
    });
  }
  return window.JSZip;
}

async function renderConvertedPagesList() {
  const container = document.getElementById('converted-pages-list');
  const conversionResults = document.getElementById('conversion-results');
  const downloadAllZipBtn = document.getElementById('download-all-zip-btn');
  const analyzeBtn = document.getElementById('analyze-btn');

  if (!container) return;
  if (!currentConvertedPages.length) {
    container.innerHTML = '<p style="color:#6b7280;">No converted pages to display yet. Press Convert PDF Pages to start.</p>';
    if (conversionResults) conversionResults.style.display = 'none';
    if (downloadAllZipBtn) downloadAllZipBtn.style.display = 'none';
    if (analyzeBtn) analyzeBtn.style.display = 'none';
    return;
  }

  if (conversionResults) conversionResults.style.display = 'block';
  if (downloadAllZipBtn) downloadAllZipBtn.style.display = 'inline-flex';
  if (analyzeBtn) analyzeBtn.style.display = selectedConvertedPageIndex !== null ? 'inline-flex' : 'none';

  container.innerHTML = currentConvertedPages.map((page, idx) => {
    const selectedClass = idx === selectedConvertedPageIndex ? 'selected' : '';
    return `
      <article class="page-card ${selectedClass}" data-index="${idx}">
        <img src="${page.image}" alt="Converted page ${page.page}" loading="lazy">
        <div class="page-card-info">
          <div>
            <strong>Page ${page.page}</strong>
            <span>${page.filename}</span>
          </div>
          <div class="page-card-actions">
            <button type="button" class="btn btn-primary select-page-btn" data-index="${idx}">Select for Analysis</button>
            <a href="${page.image}" download="${page.filename}" class="btn btn-ghost">Download</a>
          </div>
        </div>
      </article>
    `;
  }).join('');

  container.querySelectorAll('.select-page-btn').forEach((button) => {
    button.addEventListener('click', async (event) => {
      const index = Number(event.currentTarget.dataset.index);
      await selectConvertedPage(index);
    });
  });
}

async function selectConvertedPage(index) {
  if (index < 0 || index >= currentConvertedPages.length) return;

  selectedConvertedPageIndex = index;
  const page = currentConvertedPages[index];
  currentFile = await dataUrlToFile(page.image, page.filename);

  // Track that analysis source is a converted page and include original info
  currentAnalysisSource = {
    filename: page.filename,
    page: page.page,
    fromPdf: true,
    originalPdf: page.original_pdf || null,
    uploadedAt: new Date().toISOString()
  };

  document.getElementById('file-name').textContent = page.filename;
  document.getElementById('file-size').textContent = 'Converted page selected';
  document.getElementById('file-info').style.display = 'block';
  document.getElementById('action-buttons').style.display = 'flex';
  document.getElementById('analyze-btn').style.display = 'inline-flex';
  document.getElementById('convert-btn').style.display = 'none';
  const downloadAllZipBtn = document.getElementById('download-all-zip-btn');
  if (downloadAllZipBtn) downloadAllZipBtn.style.display = 'inline-flex';

  renderConvertedPagesList();
}

async function convertPdfPages() {
  if (!currentFile || !isPdf(currentFile)) {
    alert('Please upload a PDF file before converting pages.');
    return;
  }

  const convertBtn = document.getElementById('convert-btn');
  if (convertBtn) {
    convertBtn.disabled = true;
    convertBtn.textContent = 'Converting…';
  }

  try {
    const formData = new FormData();
    formData.append('pdf', currentFile);

    const response = await fetch(`${window.BACKEND_URL}/api/convert/pdf`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorPayload = await response.text();
      throw new Error(`Conversion failed: ${response.status} ${response.statusText} - ${errorPayload}`);
    }

    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'PDF conversion returned an error');
    }

    currentConvertedPages = data.pages || [];
    selectedConvertedPageIndex = null;

    if (!currentConvertedPages.length) {
      throw new Error('No pages were converted from the PDF file.');
    }

    renderConvertedPagesList();
  } catch (error) {
    console.error('PDF conversion error:', error);
    alert('⚠️ PDF Conversion Error:\n' + error.message);
  } finally {
    if (convertBtn) {
      convertBtn.disabled = false;
      convertBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 14l2 2 4-4"/><path d="M4 4h16v16H4z"/></svg> Convert PDF Pages';
    }
  }
}

// --- PDF-only conversion (separate from CNN analysis flow) ---
async function convertPdfOnlyPages() {
  if (!currentPdfOnlyFile || !isPdf(currentPdfOnlyFile)) {
    alert('Please select a PDF file in the PDF → Images section before converting pages.');
    return;
  }

  const convertBtn = document.getElementById('pdf-only-convert-btn');
  if (convertBtn) {
    convertBtn.disabled = true;
    convertBtn.textContent = 'Converting…';
  }

  try {
    const formData = new FormData();
    formData.append('pdf', currentPdfOnlyFile);

    const response = await fetch(`${window.BACKEND_URL}/api/convert/pdf`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorPayload = await response.text();
      throw new Error(`Conversion failed: ${response.status} ${response.statusText} - ${errorPayload}`);
    }

    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'PDF conversion returned an error');
    }

    currentPdfOnlyConvertedPages = data.pages || [];
    selectedPdfOnlyPageIndex = null;

    if (!currentPdfOnlyConvertedPages.length) {
      throw new Error('No pages were converted from the PDF file.');
    }

    renderPdfOnlyConvertedPagesList();
  } catch (error) {
    console.error('PDF-only conversion error:', error);
    alert('⚠️ PDF Conversion Error:\n' + error.message);
  } finally {
    if (convertBtn) {
      convertBtn.disabled = false;
      convertBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 14l2 2 4-4"/><path d="M4 4h16v16H4z"/></svg> Convert PDF Pages';
    }
  }
}

async function renderPdfOnlyConvertedPagesList() {
  const container = document.getElementById('pdf-only-converted-pages-list');
  const resultsPanel = document.getElementById('pdf-only-conversion-results');
  const downloadBtn = document.getElementById('pdf-only-download-zip-btn');

  if (!container) return;
  if (!currentPdfOnlyConvertedPages.length) {
    container.innerHTML = '<p style="color:#6b7280;">No converted pages to display yet.</p>';
    if (resultsPanel) resultsPanel.style.display = 'none';
    if (downloadBtn) downloadBtn.style.display = 'none';
    return;
  }

  if (resultsPanel) resultsPanel.style.display = 'block';
  if (downloadBtn) downloadBtn.style.display = 'inline-flex';

  container.innerHTML = currentPdfOnlyConvertedPages.map((page, idx) => {
    const selectedClass = idx === selectedPdfOnlyPageIndex ? 'selected' : '';
    return `
      <article class="page-card ${selectedClass}" data-index="${idx}">
        <img src="${page.image}" alt="Converted page ${page.page}" loading="lazy">
        <div class="page-card-info">
          <div>
            <strong>Page ${page.page}</strong>
            <span>${page.filename}</span>
          </div>
          <div class="page-card-actions">
            <a href="${page.image}" download="${page.filename}" class="btn btn-ghost">Download</a>
          </div>
        </div>
      </article>
    `;
  }).join('');
}

async function downloadAllPdfOnlyConvertedPagesZip() {
  if (!currentPdfOnlyConvertedPages.length) {
    alert('No converted pages available to download.');
    return;
  }

  const JSZipConstructor = await ensureJSZip();
  if (!JSZipConstructor) {
    alert('ZIP export requires JSZip. Please check your network connection.');
    return;
  }

  const zip = new JSZipConstructor();
  currentPdfOnlyConvertedPages.forEach((page) => {
    const base64Data = extractBase64(page.image);
    zip.file(page.filename, base64Data, { base64: true });
  });

  const blob = await zip.generateAsync({ type: 'blob' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `pdf-only-converted-pages-${new Date().toISOString().slice(0, 10)}.zip`;
  document.body.appendChild(link);
  link.click();
  URL.revokeObjectURL(link.href);
  link.remove();
}

function extractBase64(dataUrl) {
  const parts = dataUrl.split(',');
  return parts.length > 1 ? parts[1] : '';
}

async function downloadAllConvertedPagesZip() {
  if (!currentConvertedPages.length) {
    alert('No converted pages available to download.');
    return;
  }

  const JSZipConstructor = await ensureJSZip();
  if (!JSZipConstructor) {
    alert('ZIP export requires JSZip. Please check your network connection.');
    return;
  }

  const zip = new JSZipConstructor();
  currentConvertedPages.forEach((page) => {
    const base64Data = extractBase64(page.image);
    zip.file(page.filename, base64Data, { base64: true });
  });

  const blob = await zip.generateAsync({ type: 'blob' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `converted-pages-${new Date().toISOString().slice(0, 10)}.zip`;
  document.body.appendChild(link);
  link.click();
  URL.revokeObjectURL(link.href);
  link.remove();
}

async function dataUrlToFile(dataUrl, filename) {
  const [header, base64Data] = dataUrl.split(',');
  const mimeMatch = header.match(/:(.*?);/);
  const mimeType = mimeMatch ? mimeMatch[1] : 'application/octet-stream';
  const byteString = atob(base64Data);
  const byteNumbers = new Array(byteString.length);
  for (let i = 0; i < byteString.length; i += 1) {
    byteNumbers[i] = byteString.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNumbers);
  return new File([byteArray], filename, { type: mimeType });
}

async function performCNNAnalysis() {
  if (!currentFile) {
    alert('Please select a file before running analysis.');
    return;
  }

  if (usePdfConversion && isPdf(currentFile)) {
    alert('Please select a converted PDF page from the list before running analysis.');
    return;
  }

  if (!usePdfConversion && !isImageFile(currentFile)) {
    alert('Image mode is enabled. Please upload an image file first.');
    return;
  }

  startTime = Date.now();
  showState('processing');
  updateProgressStatus(0);

  const formData = new FormData();
  formData.append('image', currentFile);  // Backend expects 'image' field
  formData.append('mode', 'cnn-only');
  // Attach source metadata so backend results are traceable to the uploaded file
  if (!currentAnalysisSource && currentFile) {
    currentAnalysisSource = {
      filename: currentFile.name,
      size: currentFile.size,
      isPdf: isPdf(currentFile) || false,
      uploadedAt: new Date().toISOString()
    };
  }
  formData.append('source', JSON.stringify(currentAnalysisSource || {}));

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

    if (!response.ok) {
      throw new Error(`Analysis failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✓ Backend response:', data);
    
    if (!data.success && data.error) {
      throw new Error(data.error);
    }

    currentAnalysisData = data;

    // Mark progress complete
    updateProgressStatus(3);

    displayAnalysisResults(data);
    showState('results');

    // Update elapsed time
    const elapsed = Math.round((Date.now() - startTime) / 1000);
    const analysisTimeMs = elapsed * 1000;
    const analysisTimeEl = document.getElementById('analysis-time');
    if (analysisTimeEl) analysisTimeEl.textContent = `${analysisTimeMs}ms`;

    // Preserve runtime analysis time in saved result data
    data.statistics = data.statistics || {};
    data.statistics.analysis_time_ms = analysisTimeMs;

    // Save to session storage for results page
    sessionStorage.setItem('cnnAnalysisResults', JSON.stringify(data));

  } catch (error) {
    console.error('❌ Analysis error:', error);
    
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
      success:      inner.success,
      predictions:  inner.predictions || [],
      statistics:   inner.statistics  || {},
      model:        inner.model       || raw.model_variant || 'CNN-only',
      architecture: raw.architecture || '',
      feature_maps: inner.feature_maps || {},
      shape_detection: raw.shape_detection,
      features:         raw.features,
      metadata:         raw.metadata || {},
      ocrText:          raw.ocrText || ''
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
  const readingOrderCountEl = document.getElementById('reading-order-count');
  const layoutAccuracyEl = document.getElementById('layout-accuracy');
  const cnnRegionsEl = document.getElementById('cnn-regions');
  const cnnAvgConfEl = document.getElementById('cnn-avg-conf');
  const cnnFeaturesEl = document.getElementById('cnn-features');

  const readingOrder = data.features?.connectivity_features?.reading_order || [];
  const layoutAccuracy = stats.layout_accuracy || 0;

  if (regionCountEl) regionCountEl.textContent = totalBlocks;
  if (confScoreEl) confScoreEl.textContent = Math.round(avgConf * 100) + '%';
  if (cnnConfEl) cnnConfEl.textContent = Math.round(avgConf * 100) + '%';
  if (headerCountEl) headerCountEl.textContent = typeDistribution['Title'] || 0;
  if (paraCountEl) paraCountEl.textContent = typeDistribution['Text'] || 0;
  if (tableCountEl) tableCountEl.textContent = (typeDistribution['Table'] || 0) + (typeDistribution['Figure'] || 0);
  if (readingOrderCountEl) readingOrderCountEl.textContent = readingOrder.length || 0;
  if (layoutAccuracyEl) layoutAccuracyEl.textContent = formatPercent(layoutAccuracy);

  // Update metrics panel
  if (cnnRegionsEl) cnnRegionsEl.textContent = totalBlocks;
  if (cnnAvgConfEl) cnnAvgConfEl.textContent = Math.round(avgConf * 100) + '%';
  if (cnnFeaturesEl) cnnFeaturesEl.textContent = Object.keys(typeDistribution).length;

  renderCnnResultTabs(rawData);
}

function initResultTabs() {
  const buttons = document.querySelectorAll('.result-output .tabs button');
  buttons.forEach((button) => {
    button.addEventListener('click', () => setActiveResultTab(button.dataset.tab));
  });
}

function setActiveResultTab(tabId) {
  const buttons = document.querySelectorAll('.result-output .tabs button');
  const panes = document.querySelectorAll('.result-output .tab-body > div');
  buttons.forEach((button) => {
    button.classList.toggle('active', button.dataset.tab === tabId);
  });
  panes.forEach((pane) => {
    pane.style.display = pane.id === `tab-${tabId}` ? 'block' : 'none';
  });
}

function safeJsonString(value) {
  return JSON.stringify(value, null, 2)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function renderCnnResultTabs(rawData) {
  const data = unwrapData(rawData);
  const features = data.features || {};
  const connectivity = features.connectivity_features || {};
  const metadata = data.metadata || {};

  const structureEl = document.getElementById('structure-graph-content');
  if (structureEl) {
    const orderList = connectivity.reading_order || [];
    structureEl.innerHTML = `
      <div style="display:grid; gap:12px;">
        <div><strong>Total Regions:</strong> ${data.predictions.length}</div>
        <div><strong>Layout Accuracy:</strong> ${formatPercent(data.statistics.layout_accuracy || 0)}</div>
        <div><strong>Adjacency Relationships:</strong> ${connectivity.adjacency_count || 0}</div>
        <div><strong>Reading order:</strong> ${orderList.length ? 'Detected' : 'Unavailable'}</div>
      </div>
    `;

    if (orderList.length) {
      const rows = orderList.map((item) => `
        <tr>
          <td>${item.order + 1}</td>
          <td>${item.type || 'Unknown'}</td>
          <td>${formatPercent(item.confidence || 0)}</td>
        </tr>`).join('');
      structureEl.innerHTML += `
        <table style="width:100%; margin-top:14px; border-collapse:collapse;">
          <thead><tr><th style="text-align:left; padding:8px; border:1px solid #e5e7eb;">Order</th><th style="text-align:left; padding:8px; border:1px solid #e5e7eb;">Region Type</th><th style="text-align:left; padding:8px; border:1px solid #e5e7eb;">Confidence</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      `;
    }
  }

  const regionEl = document.getElementById('region-analysis-content');
  if (regionEl) {
    const rows = (data.predictions || []).slice(0, 12).map((pred, idx) => {
      const bbox = Array.isArray(pred.bbox) ? pred.bbox.map((c) => Math.round(c)).join(', ') : 'N/A';
      return `
        <tr>
          <td>${idx + 1}</td>
          <td>${pred.type || 'Unknown'}</td>
          <td>${formatPercent(pred.confidence || 0)}</td>
          <td>${bbox}</td>
        </tr>`;
    }).join('');

    regionEl.innerHTML = data.predictions.length
      ? `
        <table style="width:100%; border-collapse:collapse;">
          <thead><tr><th style="text-align:left; padding:8px; border:1px solid #e5e7eb;">#</th><th style="text-align:left; padding:8px; border:1px solid #e5e7eb;">Type</th><th style="text-align:left; padding:8px; border:1px solid #e5e7eb;">Confidence</th><th style="text-align:left; padding:8px; border:1px solid #e5e7eb;">BBox</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
        <p style="margin-top:12px; color:#6b7280; font-size:13px;">Showing ${Math.min(data.predictions.length, 12)} of ${data.predictions.length} regions.</p>
      `
      : '<p style="color:#6b7280;">No region predictions available.</p>';
  }

  const connectivityEl = document.getElementById('connectivity-content');
  if (connectivityEl) {
    const gaps = Array.isArray(connectivity.spatial_gaps) ? connectivity.spatial_gaps : [];
    const gapStats = gaps.length ? {
      min: Math.min(...gaps).toFixed(0),
      max: Math.max(...gaps).toFixed(0),
      avg: (gaps.reduce((sum, v) => sum + v, 0) / gaps.length).toFixed(0)
    } : { min: 'N/A', max: 'N/A', avg: 'N/A' };

    connectivityEl.innerHTML = `
      <div style="display:grid; gap:12px;">
        <div><strong>Adjacency Count:</strong> ${connectivity.adjacency_count || 0}</div>
        <div><strong>Spatial Gaps:</strong> ${gapStats.min} / ${gapStats.avg} / ${gapStats.max} px</div>
        <div><strong>Reading Order Blocks:</strong> ${connectivity.reading_order?.length || 0}</div>
      </div>
    `;
  }

  const metricsEl = document.getElementById('detailed-metrics-content');
  if (metricsEl) {
    const stats = data.statistics || {};
    const types = stats.type_distribution || {};
    const shapeDetection = data.shape_detection || {};
    const shapeTypes = Array.isArray(shapeDetection.shapes)
      ? [...new Set(shapeDetection.shapes.map((s) => s.type || 'Unknown'))].slice(0, 10)
      : [];
    const firstShapes = Array.isArray(shapeDetection.shapes) ? shapeDetection.shapes.slice(0, 5) : [];
    console.debug('Rendering detailed metrics', { stats, types, shapeDetection, data });

    const objectRows = [
      ['Model', data.model || 'CNN-only'],
      ['Architecture', data.architecture || metadata.architecture || 'Unknown'],
      ['Analysis Type', metadata.analysis_type || data.analysis_type || 'CNN-only'],
      ['Image Shape', metadata.image_shape ? metadata.image_shape.join('×') : 'Unknown'],
      ['Includes Graphs', metadata.includes_graphs ? 'Yes' : 'No'],
      ['Includes Connectors', metadata.includes_connectors ? 'Yes' : 'No'],
      ['Total Regions', stats.total_blocks || 0],
      ['Average Confidence', formatPercent(stats.avg_confidence || 0)],
      ['Header Count', types.Title || 0],
      ['Paragraph Count', types.Text || 0],
      ['Tables/Figures', (types.Table || 0) + (types.Figure || 0)],
      ['Feature Types', Object.keys(types).length]
    ];

    const rows = objectRows.map(([label, value]) => `
      <tr>
        <td style="padding:8px; border:1px solid #e5e7eb; font-weight:600; width:40%;">${label}</td>
        <td style="padding:8px; border:1px solid #e5e7eb;">${value}</td>
      </tr>`).join('');

    const shapeSampleRows = firstShapes.map((shape, idx) => {
      const bbox = Array.isArray(shape.bbox) ? shape.bbox.map((c) => Math.round(c)).join(', ') : 'N/A';
      return `
        <tr>
          <td style="padding:8px; border:1px solid #e5e7eb;">${idx + 1}</td>
          <td style="padding:8px; border:1px solid #e5e7eb;">${shape.type || 'Unknown'}</td>
          <td style="padding:8px; border:1px solid #e5e7eb;">${shape.area || 'N/A'}</td>
          <td style="padding:8px; border:1px solid #e5e7eb;">${bbox}</td>
        </tr>`;
    }).join('');

    const rawDetails = {
      shape_detection: shapeDetection,
      metadata,
      connectivity
    };
    const escapedRawDetails = safeJsonString(rawDetails);

    metricsEl.innerHTML = `
      <table style="width:100%; border-collapse:collapse; margin-bottom:14px;">
        <tbody>${rows}</tbody>
      </table>
      <div style="font-size:13px; color:#6b7280; margin-bottom:14px;">If some fields are blank, it means this analysis did not return that statistic.</div>
      <div style="display:grid; gap:14px;">
        <div style="background:#f8fafc; border:1px solid #e5e7eb; border-radius:12px; padding:14px;">
          <strong style="display:block; margin-bottom:8px; color:#111827;">Shape Detection Summary</strong>
          <div style="display:grid; gap:8px; font-size:13px; color:#334155;">
            <div><strong>Model:</strong> ${shapeDetection.model || 'Unknown'}</div>
            <div><strong>Shape Count:</strong> ${shapeDetection.shape_count || 0}</div>
            <div><strong>Shape Types:</strong> ${shapeTypes.length ? shapeTypes.join(', ') : 'Unavailable'}</div>
          </div>
        </div>
        ${shapeSampleRows ? `
        <div style="background:#fff; border:1px solid #e5e7eb; border-radius:12px; padding:14px;">
          <strong style="display:block; margin-bottom:8px; color:#111827;">Sample Detected Shapes</strong>
          <table style="width:100%; border-collapse:collapse; font-size:13px;">
            <thead>
              <tr>
                <th style="padding:8px; border:1px solid #e5e7eb; text-align:left;">#</th>
                <th style="padding:8px; border:1px solid #e5e7eb; text-align:left;">Type</th>
                <th style="padding:8px; border:1px solid #e5e7eb; text-align:left;">Area</th>
                <th style="padding:8px; border:1px solid #e5e7eb; text-align:left;">BBox</th>
              </tr>
            </thead>
            <tbody>${shapeSampleRows}</tbody>
          </table>
        </div>` : `
        <div style="background:#fff; border:1px solid #e5e7eb; border-radius:12px; padding:14px; color:#475569; font-size:13px;">
          No sample shape details available.
        </div>`}
        <details style="background:#f8fafc; border:1px solid #e5e7eb; border-radius:12px; padding:14px;">
          <summary style="font-weight:600; cursor:pointer; color:#0f172a;">Show raw detailed JSON data</summary>
          <pre style="background:#ffffff; border:1px solid #e5e7eb; border-radius:8px; padding:14px; overflow-x:auto; max-height:320px; overflow-y:auto; margin-top:12px;">${escapedRawDetails}</pre>
        </details>
      </div>
    `;
  }

  setActiveResultTab('structure');
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
document.addEventListener('DOMContentLoaded', initResultTabs);

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
  document.getElementById('layout-accuracy').textContent = formatPercent(stats.layout_accuracy || 0);
  const readingOrder = data.features?.connectivity_features?.reading_order || [];
  document.getElementById('reading-order-count').textContent = readingOrder.length || 0;

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
