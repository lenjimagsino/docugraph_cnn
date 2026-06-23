# DOCUGRAPH Backend - Phase 6: Python API Server

**Purpose**: Advanced document layout analysis and semantic embeddings  
**Status**: ✅ Production Ready  
**Version**: 6.0.0

---

## Quick Start

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

### OCR Engine Setup
The OCR feature requires **EasyOCR**. Run the setup script:

```bash
python setup_ocr.py
```

This will:
- Check Python version (3.7+ required)
- Verify all dependencies are installed
- Initialize and test the OCR engine
- Download language models (first run only, ~100MB for English)

**Alternative manual setup:**
```bash
# Install EasyOCR
pip install easyocr

# Verify installation
python -c "import easyocr; print('✓ EasyOCR ready')"
```

### Run Locally
```bash
# Development mode
python app.py

# Or with Flask
export FLASK_APP=app.py
python -m flask run

# Production mode with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Check backend status:**
```bash
# Health check
curl http://localhost:5000/health

# Diagnostics (detailed system info)
curl http://localhost:5000/diagnostics
```

### Docker
```bash
# Build and run
docker build -t docugraph-backend .
docker run -p 5000:5000 docugraph-backend

# Or use docker-compose (from parent directory)
cd ..
docker-compose up -d
```

---

## API Endpoints

### Health Check
```bash
curl http://localhost:5000/health
```

### Layout Analysis
```bash
curl -X POST -F "image=@document.jpg" \
  http://localhost:5000/api/v1/layout/analyze
```

### Semantic Embeddings
```bash
curl -X POST http://localhost:5000/api/v1/embeddings/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Sample text", "language": "en"}'
```

### OCR Text Extraction
```bash
curl -X POST -F "image=@document.jpg" \
  -F "languages=en" \
  http://localhost:5000/api/v1/ocr/extract
```

**Response:**
```json
{
  "success": true,
  "full_text": "Extracted text from document...",
  "regions": [
    {
      "bbox": [10.5, 15.2, 45.3, 22.8],
      "text": "Text region",
      "confidence": 0.95
    }
  ],
  "region_count": 42,
  "average_confidence": 0.92,
  "languages": ["en"]
}
```

### Similarity
```bash
curl -X POST http://localhost:5000/api/v1/embeddings/similarity \
  -H "Content-Type: application/json" \
  -d '{"text1": "First", "text2": "Second"}'
```

---

## Configuration

**File**: `.env`

```
FLASK_ENV=production
DEBUG=False
PORT=5000
UPLOAD_FOLDER=./uploads
MAX_CONTENT_LENGTH=52428800
```

---

## Requirements

- Python 3.10+
- 8GB RAM minimum (16GB recommended)
- CUDA-capable GPU (recommended but optional)
- 4GB disk space for models

---

## Performance

| Operation | Time | GPU? |
|-----------|------|------|
| Layout Analysis | 500-1000ms | Recommended |
| Embedding | 100-200ms | Recommended |
| Health Check | <10ms | - |

---

## Troubleshooting

### OCR Not Working

**Error: "OCR service unavailable"**
- ✓ Ensure EasyOCR is installed: `pip install easyocr`
- ✓ Run diagnostics: `curl http://localhost:5000/diagnostics`
- ✓ Check backend logs for initialization errors
- ✓ First OCR run downloads models (~100MB) - may take 2-5 minutes

**Error: "OCR engine not available"**
- EasyOCR failed to initialize
- Run setup script: `python setup_ocr.py`
- Check internet connection (models need to be downloaded)

**Slow OCR Performance**
- First run is slow (model download + initialization)
- Subsequent runs are much faster (models cached)
- Consider using GPU for faster processing: `nvidia-smi` to check

### Backend Not Starting

**Error: "ModuleNotFoundError: No module named 'flask'"**
- Install dependencies: `pip install -r requirements.txt`

**Error: "Port 5000 already in use"**
- Change port in `.env` or kill existing process:
  ```bash
  # Linux/Mac
  lsof -i :5000 | grep LISTEN | awk '{print $2}' | xargs kill -9
  
  # Windows
  netstat -ano | findstr :5000
  taskkill /PID <PID> /F
  ```

**Error: "Connection refused" from frontend**
- Ensure backend is running on port 5000
- Check firewall settings
- Verify URL in browser: `http://localhost:5000/health`

### Image Upload Issues

**Error: "Invalid image format"**
- Supported formats: JPG, PNG, PDF
- File must be valid image data
- Try a different image or convert format

---

## Support

See parent directory documentation:
- [PHASE_6_8_COMPLETE.md](../PHASE_6_8_COMPLETE.md)
- [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)
