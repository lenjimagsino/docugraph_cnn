# CNN-Only Analysis System for DOCUGRAPH

## Overview

The **CNN-Only Analysis** system is a comparison baseline for DOCUGRAPH's hybrid CNN+GNN architecture. It provides pure CNN-based document layout analysis without graph neural network components, allowing for objective performance evaluation between the two approaches.

## Architecture

### CNN-Only Pipeline
```
Input Image → Image Preprocessing → CNN Feature Extraction → Layout Detection → 
Bounding Box Generation → Type Classification → OCR Integration → Results
```

### Key Components

1. **Detectron2 (ResNest50)**
   - Pure CNN backbone without graph components
   - Layout detection on document regions
   - Type classification (Header, Text, Table, Figure, List)
   - Confidence scoring for each detection

2. **Feature Extraction**
   - Direct CNN predictions on image patches
   - No relationship reasoning between elements
   - Independent region analysis

3. **Region Analysis**
   - Bounding box generation for detected regions
   - Aspect ratio and area calculation
   - Fill density measurement

## File Structure

### Frontend Files
- `try_cnn.html` - Upload and analysis interface for CNN-only mode
- `processing_cnn.html` - Real-time processing status display
- `results_cnn.html` - Results visualization with metrics
- `comparison.html` - Side-by-side CNN vs CNN+GNN comparison
- `assets/cnn_only.js` - Frontend logic for CNN-only workflow

### Backend Files
- `/api/analyze` - General analysis endpoint (supports both modes)
- `/api/v1/cnn-only/analyze` - CNN-only analysis endpoint
- `/api/v1/cnn-only/layout` - CNN-only layout analysis
- `/api/v1/cnn-only/shapes` - CNN-only shape detection
- `/api/v1/comparison/analyze` - Side-by-side model comparison

## How to Use

### 1. Access CNN-Only Analysis
Navigate to: `https://docugraph.site/try_cnn.html` or `http://localhost:5000/try_cnn.html`

### 2. Upload Document
- Drag and drop an image file, or
- Click to browse and select from your device
- Supported formats: JPG, PNG, WebP, BMP

### 3. Analyze Layout
Click "Analyze Layout (CNN Only)" to:
- Extract CNN features from the document
- Detect layout regions
- Generate bounding boxes
- Calculate confidence scores

### 4. Extract OCR Text
After layout analysis completes:
- Click "Start OCR & Extract Text"
- Text regions are extracted using Tesseract.js
- Results are displayed in the output panel

### 5. View Results
Results page shows:
- Original document image
- CNN detected layout with color-coded regions
- Extracted text content
- Analysis metrics and statistics

### 6. Compare with CNN+GNN
- Click "View Comparison" to see side-by-side analysis
- Check the comparison page for detailed metrics
- Download results for further analysis

## Workflow Steps

### Step 1: Upload
```
File Selection → Validation → Preview
```

### Step 2: CNN Layout Analysis
```
Image Loading
    ↓
CNN Feature Extraction (Detectron2)
    ↓
Region Detection & Classification
    ↓
Bounding Box Generation
    ↓
Confidence Scoring
    ↓
Display Results with Visualization
```

### Step 3: OCR Extraction
```
Layout Regions → Tesseract.js → Text Extraction → Display & Export
```

## Output Format

### Analysis Results JSON
```json
{
  "success": true,
  "mode": "cnn-only",
  "predictions": [
    {
      "type": "Title",
      "bbox": [10, 5, 90, 12],
      "confidence": 0.95,
      "area": 5100,
      "features": {
        "width": 80,
        "height": 7,
        "aspect_ratio": 11.43
      }
    }
  ],
  "statistics": {
    "total_blocks": 15,
    "avg_confidence": 0.88,
    "type_distribution": {
      "Title": 1,
      "Text": 10,
      "Table": 2,
      "Figure": 2
    },
    "image_shape": [800, 600, 3]
  }
}
```

### Region Types
- **Header**: Document headers and titles
- **Text**: Body paragraphs and main content
- **Table**: Structured table regions
- **Figure**: Images and diagrams
- **List**: Bulleted or numbered lists

## Performance Characteristics

### Speed
- **CNN-Only**: ~2.1 seconds per page
- **CNN+GNN**: ~3.8 seconds per page
- Speed advantage: 1.8x faster

### Accuracy
- **CNN-Only**: ~65% layout accuracy
- **CNN+GNN**: ~92% layout accuracy
- Accuracy improvement: 27% better

### Memory Usage
- **CNN-Only**: Lower memory footprint
- **CNN+GNN**: Higher due to graph storage

## API Endpoints

### Analyze (General Purpose)
```
POST /api/analyze
Content-Type: multipart/form-data

Parameters:
- file: Image file
- mode: "cnn-only" or "full" (optional, default: "cnn-only")

Response:
{
  "success": boolean,
  "predictions": array,
  "statistics": object,
  "mode": string
}
```

### CNN-Only Layout
```
POST /api/v1/cnn-only/layout
Content-Type: multipart/form-data

Parameters:
- image: Image file

Response:
{
  "success": boolean,
  "model": "CNN-only (Detectron2)",
  "predictions": array,
  "feature_maps": object,
  "statistics": object
}
```

### Compare Models
```
POST /api/v1/comparison/analyze
Content-Type: multipart/form-data

Parameters:
- image: Image file

Response:
{
  "success": boolean,
  "comparison": {
    "cnn_only": object,
    "cnn_gnn_hybrid": object
  }
}
```

## Use Cases

### 1. Performance Benchmarking
Compare CNN-only vs CNN+GNN on your document dataset to determine the accuracy-speed trade-off that fits your requirements.

### 2. Research & Publication
Use CNN-only results as a baseline for research papers comparing different architectural approaches.

### 3. Fast Document Analysis
For applications requiring rapid document analysis where ~65% accuracy is acceptable, CNN-only provides 1.8x faster performance.

### 4. Budget-Conscious Solutions
CNN-only uses fewer computational resources (lower memory, faster inference) making it suitable for resource-constrained environments.

### 5. Educational Purpose
Understand the differences between CNN and graph-based approaches through direct visual comparison.

## Comparison Page Features

### Side-by-Side Display
- Model specifications
- Supported features checklist
- Performance metrics

### Performance Charts
- Layout Accuracy: CNN-Only (65%) vs CNN+GNN (92%)
- Confidence Scores: CNN-Only (72%) vs CNN+GNN (96%)
- Processing Speed: CNN-Only (2.1s) vs CNN+GNN (3.8s)

### Key Insights
- Accuracy improvements from graph relationships
- Context understanding advantages of GNN
- Speed vs accuracy trade-offs
- Ideal use cases for each model

## Results Visualization

### Color Coding
- **Green**: Headers/Titles
- **Blue**: Paragraphs/Text
- **Orange**: Tables
- **Purple**: Figures
- **Pink**: Shapes/Diagrams

### Interactive Elements
- Hover over regions for confidence scores
- Click regions to highlight connected elements (CNN+GNN only)
- Toggle region visibility by type

## Export Options

### Available Formats
1. **Copy Text**: Copy extracted text to clipboard
2. **PDF Report**: Generate PDF with analysis results
3. **JSON Data**: Download raw analysis data
4. **Comparison Report**: Export side-by-side comparison

## Troubleshooting

### Analysis Fails
- Check image format (JPG, PNG, WebP, BMP supported)
- Ensure image is readable and not corrupted
- Try with a simpler document

### OCR Not Working
- Ensure Tesseract.js is loaded
- Check browser console for errors
- Try different image preprocessing

### Comparison Not Available
- Ensure both CNN-only and CNN+GNN analysis completed
- Check backend server status
- Verify model initialization

## Technical Details

### Frontend Stack
- Vanilla JavaScript (no frameworks)
- Tesseract.js for client-side OCR
- D3.js for visualization (if needed)
- HTML5 Canvas for image processing

### Backend Stack
- Flask (Python web framework)
- Detectron2/LayoutParser for CNN layout detection
- OpenCV for image processing
- NumPy/SciPy for numerical operations

### Model Information
- **Backbone**: ResNest50
- **Framework**: Detectron2
- **Training Dataset**: PubLayNet (document layout dataset)
- **Input Size**: Variable (adaptive)
- **Output**: Bounding boxes with class labels and confidence

## Navigation

**Quick Links:**
- [Start CNN-Only Analysis](./try_cnn.html)
- [View CNN vs CNN+GNN Comparison](./comparison.html)
- [Full DOCUGRAPH (CNN+GNN)](./try.html)
- [Results Dashboard](./results.html)
- [Research Methodology](./methodology.html)

## Support & Questions

For issues or questions:
1. Check the troubleshooting section above
2. Review backend logs in terminal/console
3. Ensure all dependencies are installed
4. Check browser developer console for JavaScript errors

## Citation

If you use CNN-Only Analysis for research, please cite:
```
@software{docugraph2024,
  title={DOCUGRAPH: CNN-GNN Hybrid Document Analysis},
  author={DOCUGRAPH Contributors},
  year={2024},
  url={https://docugraph.site}
}
```

## License

Part of DOCUGRAPH Platform. See main repository for licensing information.
