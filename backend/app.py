"""
DOCUGRAPH Phase 6: Python Backend API Server
Enterprise-grade document analysis with LayoutParser and Detectron2
"""

import os
import json
import base64
import time
from io import BytesIO
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import cv2
import numpy as np
from PIL import Image
from transformers import AutoTokenizer, AutoModel

# Import advanced image processing
from advanced_image_processing import (
    AdvancedDocumentScanner,
    AdaptiveBinarizer,
    PixelScanner,
    SmartShapeTracer,
    ConnectorTracer
)

# Optional imports with graceful fallback
try:
    import layoutparser as lp
    HAS_LAYOUTPARSER = True
except ImportError:
    HAS_LAYOUTPARSER = False
    print("⚠ Warning: layoutparser not installed. Using fallback layout analysis.")

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("⚠ Warning: PyTorch not installed. Using CPU mode.")

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Enhanced CORS configuration for production and development
cors_origins = [
    'https://docugraph.site',
    'https://www.docugraph.site',
    'http://localhost',
    'http://localhost:3000',
    'http://localhost:5000',
    'http://127.0.0.1',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5000',
]

CORS(app, resources={
    r"/api/*": {
        "origins": cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 3600
    }
})

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===========================
# Phase 6: LayoutParser Integration
# ===========================

class LayoutAnalyzer:
    """Advanced layout analysis using LayoutParser + Detectron2"""
    
    def __init__(self):
        """Initialize LayoutParser models"""
        if not HAS_LAYOUTPARSER:
            print("ℹ LayoutParser not available. Using fallback layout analysis.")
            self.initialized = False
            self.model = None
            return
            
        try:
            # PubLayNet model for document layout detection
            self.model = lp.Detectron2LayoutModel(
                config_path="lp://PubLayNet/faster_rcnn_ResNest50_fpn_3x",
                model_path="lp://PubLayNet/faster_rcnn_ResNest50_fpn_3x/model_final.pth",
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
                label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
            )
            self.initialized = True
            print("✓ LayoutParser model loaded")
        except Exception as e:
            print(f"⚠ LayoutParser initialization failed: {e}")
            print("  Using fallback layout analysis instead")
            self.initialized = False
            self.model = None
    
    def analyze_layout(self, image_array):
        """
        Analyze document layout using LayoutParser
        
        Args:
            image_array: numpy array (H×W×C)
        
        Returns:
            dict with layout blocks, hierarchy, and confidence scores
        """
        if not self.initialized or self.model is None:
            return self._fallback_layout_analysis(image_array)
        
        try:
            # Convert to PIL Image for LayoutParser
            if isinstance(image_array, np.ndarray):
                image = Image.fromarray(image_array.astype('uint8'))
            else:
                image = image_array
            
            # Run detection
            layout = self.model.detect(image)
            
            # Extract blocks with hierarchy
            blocks = []
            for block in layout:
                block_info = {
                    'type': block.type,
                    'bbox': [block.x_1, block.y_1, block.x_2, block.y_2],
                    'confidence': float(block.score) if hasattr(block, 'score') else 0.95,
                    'text': block.text if hasattr(block, 'text') else None,
                    'category': self._categorize_block(block.type)
                }
                blocks.append(block_info)
            
            # Build hierarchy (reading order)
            hierarchy = self._build_hierarchy(blocks, image_array.shape)
            
            return {
                'success': True,
                'blocks': blocks,
                'hierarchy': hierarchy,
                'page_info': {
                    'width': image_array.shape[1],
                    'height': image_array.shape[0],
                    'block_count': len(blocks)
                }
            }
        
        except Exception as e:
            print(f"Layout analysis error: {e}")
            return self._fallback_layout_analysis(image_array)
    
    def _fallback_layout_analysis(self, image_array):
        """Fallback to basic layout analysis"""
        height, width = image_array.shape[:2]
        
        # Basic grid-based layout detection
        blocks = [
            {
                'type': 'Text',
                'bbox': [0, 0, width, height],
                'confidence': 0.7,
                'category': 'paragraph'
            }
        ]
        
        return {
            'success': True,
            'blocks': blocks,
            'hierarchy': blocks,
            'page_info': {
                'width': width,
                'height': height,
                'block_count': 1
            }
        }
    
    def _categorize_block(self, block_type):
        """Map LayoutParser types to DOCUGRAPH categories"""
        mapping = {
            'Text': 'paragraph',
            'Title': 'header',
            'List': 'list',
            'Table': 'table',
            'Figure': 'figure'
        }
        return mapping.get(block_type, 'paragraph')
    
    def _build_hierarchy(self, blocks, image_shape):
        """Build reading order hierarchy"""
        # Sort by position (top-to-bottom, left-to-right)
        sorted_blocks = sorted(blocks, key=lambda b: (b['bbox'][1], b['bbox'][0]))
        
        # Add reading order
        for idx, block in enumerate(sorted_blocks):
            block['reading_order'] = idx
        
        return sorted_blocks


class SemanticEmbeddingEngine:
    """Cross-lingual semantic embedding generation"""
    
    def __init__(self):
        """Initialize embedding model"""
        try:
            self.model_name = "sentence-transformers/xlm-r-large-v1"
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
            self.model.eval()
            print("✓ Semantic embedding model loaded")
        except Exception as e:
            print(f"⚠ Embedding model initialization failed: {e}")
            self.model = None
    
    def get_embedding(self, text, language='en'):
        """Generate 768-dimensional semantic embedding"""
        if self.model is None:
            return [0.0] * 768
        
        try:
            with torch.no_grad():
                inputs = self.tokenizer(
                    text,
                    return_tensors='pt',
                    padding=True,
                    truncation=True,
                    max_length=512
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                outputs = self.model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1)
                
                return embeddings[0].cpu().tolist()
        except Exception as e:
            print(f"Embedding error: {e}")
            return [0.0] * 768
    
    def compute_similarity(self, text1, text2):
        """Compute cosine similarity between two texts"""
        emb1 = np.array(self.get_embedding(text1))
        emb2 = np.array(self.get_embedding(text2))
        
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2) + 1e-8)
        return float(similarity)


class OCREngine:
    """Enterprise OCR with EasyOCR and text extraction"""
    
    def __init__(self):
        """Initialize OCR engine"""
        try:
            import easyocr
            # Determine GPU availability safely
            use_gpu = False
            if HAS_TORCH:
                try:
                    use_gpu = torch.cuda.is_available()
                except:
                    use_gpu = False
            
            print(f"🔧 Initializing OCR engine (GPU: {use_gpu})...")
            self.reader = easyocr.Reader(['en'], gpu=use_gpu, verbose=False)
            self.initialized = True
            print("✓ OCR engine initialized successfully")
        except ImportError as e:
            print(f"⚠ EasyOCR not installed: {e}")
            print("  Install with: pip install easyocr")
            self.reader = None
            self.initialized = False
        except Exception as e:
            print(f"⚠ OCR engine initialization failed: {e}")
            import traceback
            traceback.print_exc()
            self.reader = None
            self.initialized = False
    
    def extract_text(self, image_array, languages=['en']):
        """
        Extract text from image using EasyOCR
        
        Args:
            image_array: numpy array (H×W×C)
            languages: list of language codes (e.g., ['en', 'es'])
        
        Returns:
            dict with OCR results including text, confidence, and bounding boxes
        """
        if not self.initialized or self.reader is None:
            return {
                'success': False,
                'error': 'OCR engine not available',
                'regions': []
            }
        
        try:
            # Run OCR
            results = self.reader.readtext(image_array)
            
            regions = []
            full_text = []
            
            for (bbox, text, confidence) in results:
                # Extract bounding box coordinates
                # bbox is a list of 4 points (top-left, top-right, bottom-right, bottom-left)
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                
                x_min = min(x_coords)
                y_min = min(y_coords)
                x_max = max(x_coords)
                y_max = max(y_coords)
                
                # Convert to percentage coordinates
                img_height, img_width = image_array.shape[:2]
                x1_pct = (x_min / img_width) * 100
                y1_pct = (y_min / img_height) * 100
                x2_pct = (x_max / img_width) * 100
                y2_pct = (y_max / img_height) * 100
                
                region = {
                    'type': 'text',
                    'bbox': [x1_pct, y1_pct, x2_pct, y2_pct],
                    'text': text,
                    'confidence': float(confidence)
                }
                
                regions.append(region)
                full_text.append(text)
            
            return {
                'success': True,
                'full_text': '\n'.join(full_text),
                'regions': regions,
                'region_count': len(regions),
                'average_confidence': np.mean([r['confidence'] for r in regions]) if regions else 0,
                'languages': languages
            }
        
        except Exception as e:
            print(f"OCR extraction error: {e}")
            return {
                'success': False,
                'error': str(e),
                'regions': []
            }


# ===========================
# API Endpoints
# ===========================

# Initialize models
layout_analyzer = LayoutAnalyzer()
embedding_engine = SemanticEmbeddingEngine()
ocr_engine = OCREngine()

# Initialize advanced document scanner
print("🔧 Initializing Advanced Document Scanner...")
try:
    # Try Tesseract, fallback to EasyOCR
    use_tesseract = True
    try:
        import pytesseract
        # Test if Tesseract is available
        pytesseract.get_tesseract_version()
    except:
        print("⚠ Tesseract not available, using EasyOCR fallback for word-level OCR")
        use_tesseract = False
    
    document_scanner = AdvancedDocumentScanner(use_tesseract=use_tesseract)
    print("✓ Advanced Document Scanner initialized")
except Exception as e:
    print(f"⚠ Failed to initialize Advanced Document Scanner: {e}")
    document_scanner = None


@app.route('/', methods=['GET'])
def root():
    """Root endpoint - API welcome message"""
    return jsonify({
        'service': 'DOCUGRAPH Backend API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'diagnostics': '/diagnostics',
            'layout_analyze': '/api/v1/layout/analyze',
            'ocr_extract': '/api/v1/ocr/extract',
            'embeddings_generate': '/api/v1/embeddings/generate',
            'embeddings_similarity': '/api/v1/embeddings/similarity',
            'batch_analyze': '/api/v1/batch/analyze'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '6.0.0',
        'phase': 'Phase 6: Python Backend',
        'models': {
            'layoutparser': layout_analyzer.initialized,
            'embeddings': embedding_engine.model is not None,
            'ocr': ocr_engine.initialized
        }
    })


@app.route('/diagnostics', methods=['GET'])
def diagnostics():
    """Diagnostics endpoint - returns detailed system information"""
    import sys
    
    diagnostics_data = {
        'python_version': sys.version,
        'installed_packages': {},
        'models': {
            'layoutparser': {
                'available': HAS_LAYOUTPARSER,
                'initialized': layout_analyzer.initialized if HAS_LAYOUTPARSER else False
            },
            'torch': {
                'available': HAS_TORCH,
                'cuda_available': torch.cuda.is_available() if HAS_TORCH else False
            },
            'ocr': {
                'available': True,
                'initialized': ocr_engine.initialized,
                'reason': 'Check server logs for initialization details'
            },
            'embeddings': {
                'available': True,
                'initialized': embedding_engine.model is not None
            }
        },
        'recommendations': []
    }
    
    # Check package versions
    packages_to_check = ['easyocr', 'torch', 'cv2', 'layoutparser', 'transformers']
    for pkg_name in packages_to_check:
        try:
            if pkg_name == 'cv2':
                import cv2
                diagnostics_data['installed_packages']['opencv'] = cv2.__version__
            else:
                mod = __import__(pkg_name)
                if hasattr(mod, '__version__'):
                    diagnostics_data['installed_packages'][pkg_name] = mod.__version__
                else:
                    diagnostics_data['installed_packages'][pkg_name] = 'installed (version unknown)'
        except ImportError:
            diagnostics_data['installed_packages'][pkg_name] = 'NOT INSTALLED'
            if pkg_name == 'easyocr':
                diagnostics_data['recommendations'].append('Install EasyOCR: pip install easyocr')
            elif pkg_name == 'torch':
                diagnostics_data['recommendations'].append('Install PyTorch: pip install torch torchvision (optional for GPU)')
    
    if not ocr_engine.initialized:
        diagnostics_data['recommendations'].append('OCR engine failed to initialize - check logs')
    
    return jsonify(diagnostics_data)


@app.route('/api/v1/layout/analyze', methods=['POST'])
def analyze_layout():
    """Analyze document layout using LayoutParser"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        image_file = request.files['image']
        
        # Read image
        image_bytes = image_file.read()
        image_array = cv2.imdecode(
            np.frombuffer(image_bytes, np.uint8),
            cv2.IMREAD_COLOR
        )
        
        if image_array is None:
            return jsonify({'error': 'Invalid image'}), 400
        
        # Analyze layout
        result = layout_analyzer.analyze_layout(image_array)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/ocr/extract', methods=['POST'])
def extract_ocr():
    """Extract text from document using OCR"""
    try:
        if 'image' not in request.files:
            print("❌ No image file provided")
            return jsonify({'error': 'No image provided', 'success': False}), 400
        
        image_file = request.files['image']
        languages = request.form.getlist('languages', ['en'])
        
        print(f"📄 Processing image: {image_file.filename}, Languages: {languages}")
        
        # Read image
        image_bytes = image_file.read()
        image_array = cv2.imdecode(
            np.frombuffer(image_bytes, np.uint8),
            cv2.IMREAD_COLOR
        )
        
        if image_array is None:
            print("❌ Invalid image data")
            return jsonify({'error': 'Invalid image format', 'success': False}), 400
        
        print(f"✓ Image loaded: {image_array.shape}")
        
        # Check if OCR engine is initialized
        if not ocr_engine.initialized:
            print("⚠ OCR engine not initialized")
            return jsonify({
                'error': 'OCR engine not available. Please ensure easyocr is installed: pip install easyocr',
                'success': False
            }), 503
        
        # Extract OCR
        print("🔄 Running OCR extraction...")
        result = ocr_engine.extract_text(image_array, languages)
        
        if result.get('success'):
            print(f"✓ OCR completed: {result.get('region_count', 0)} regions detected")
        else:
            print(f"⚠ OCR failed: {result.get('error', 'Unknown error')}")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"❌ OCR error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'OCR processing failed: {str(e)}', 'success': False}), 500


@app.route('/api/v1/embeddings/generate', methods=['POST'])
def generate_embeddings():
    """Generate semantic embeddings for text"""
    try:
        data = request.json
        text = data.get('text', '')
        language = data.get('language', 'en')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        embedding = embedding_engine.get_embedding(text, language)
        
        return jsonify({
            'text': text,
            'language': language,
            'embedding': embedding,
            'dimension': len(embedding)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/embeddings/similarity', methods=['POST'])
def compute_similarity():
    """Compute semantic similarity between two texts"""
    try:
        data = request.json
        text1 = data.get('text1', '')
        text2 = data.get('text2', '')
        
        if not text1 or not text2:
            return jsonify({'error': 'Both texts required'}), 400
        
        similarity = embedding_engine.compute_similarity(text1, text2)
        
        return jsonify({
            'text1': text1,
            'text2': text2,
            'similarity': similarity,
            'interpretation': 'high' if similarity > 0.7 else ('medium' if similarity > 0.4 else 'low')
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/batch/analyze', methods=['POST'])
def batch_analyze():
    """Batch process multiple documents"""
    try:
        data = request.json
        documents = data.get('documents', [])
        
        if not documents:
            return jsonify({'error': 'No documents provided'}), 400
        
        results = []
        for doc in documents:
            result = {
                'id': doc.get('id'),
                'layout': layout_analyzer.analyze_layout(np.frombuffer(base64.b64decode(doc['image']), dtype=np.uint8).reshape(doc['height'], doc['width'], 3)),
                'embedding': embedding_engine.get_embedding(doc.get('text', ''))
            }
            results.append(result)
        
        return jsonify({
            'success': True,
            'processed': len(results),
            'results': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===========================
# Advanced Document Scanning Endpoints
# ===========================

@app.route('/api/v1/scan/advanced', methods=['POST'])
def advanced_document_scan():
    """
    Advanced document scanning with:
    - Sauvola adaptive binarization
    - Pixel scanner (Union-Find)
    - Smart shape detection
    - Connector tracing
    - Word-level OCR
    """
    try:
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image provided'
            }), 400
        
        image_file = request.files['image']
        extract_text = request.form.get('extract_text', 'true').lower() == 'true'
        
        print(f"📊 Advanced document scan: {image_file.filename}")
        
        # Read image
        image_bytes = image_file.read()
        image_array = cv2.imdecode(
            np.frombuffer(image_bytes, np.uint8),
            cv2.IMREAD_COLOR
        )
        
        if image_array is None:
            return jsonify({
                'success': False,
                'error': 'Invalid image format'
            }), 400
        
        print(f"✓ Image loaded: {image_array.shape}")
        
        if document_scanner is None:
            return jsonify({
                'success': False,
                'error': 'Advanced document scanner not available'
            }), 503
        
        # Process document
        print("🔄 Running advanced document scan...")
        result = document_scanner.process_document(image_array, extract_text=extract_text)
        
        if result.get('success'):
            print(f"✓ Scan completed")
            print(f"  - Components: {result['stages']['pixel_scanning']['component_count']}")
            print(f"  - Shapes: {result['stages']['shape_tracing']['shape_count']}")
            print(f"  - Connectors: {result['stages']['connector_tracing']['connection_count']}")
            if extract_text:
                print(f"  - Words: {result['stages']['word_ocr']['word_count']}")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"❌ Advanced scan error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v1/scan/binarize', methods=['POST'])
def binarize_image():
    """
    Apply Sauvola adaptive binarization
    Returns binary image as base64
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        image_file = request.files['image']
        window_size = int(request.form.get('window_size', 25))
        k = float(request.form.get('k', 0.34))
        
        # Read image
        image_bytes = image_file.read()
        image_array = cv2.imdecode(
            np.frombuffer(image_bytes, np.uint8),
            cv2.IMREAD_COLOR
        )
        
        if image_array is None:
            return jsonify({'error': 'Invalid image format'}), 400
        
        # Binarize
        binarizer = AdaptiveBinarizer(window_size=window_size, k=k)
        binary = binarizer.binarize(image_array)
        
        # Encode as PNG
        _, buffer = cv2.imencode('.png', binary)
        binary_b64 = base64.b64encode(buffer).decode()
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{binary_b64}',
            'shape': binary.shape,
            'method': 'Sauvola',
            'parameters': {
                'window_size': window_size,
                'k': k
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/scan/components', methods=['POST'])
def scan_components():
    """
    Extract connected components using Union-Find
    Returns component information with classification
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        image_file = request.files['image']
        
        # Read image
        image_bytes = image_file.read()
        image_array = cv2.imdecode(
            np.frombuffer(image_bytes, np.uint8),
            cv2.IMREAD_COLOR
        )
        
        if image_array is None:
            return jsonify({'error': 'Invalid image format'}), 400
        
        # Binarize first
        binarizer = AdaptiveBinarizer()
        binary = binarizer.binarize(image_array)
        
        # Scan components
        scanner = PixelScanner()
        scan_results = scanner.scan_pixels(binary)
        
        # Convert pixel lists to summary
        components_summary = []
        for comp in scan_results['components'][:100]:  # Limit to first 100
            comp_summary = {
                'id': comp['id'],
                'type': comp['type'],
                'bbox': comp['bbox'],
                'pixel_count': comp['pixel_count'],
                'fill_density': float(comp['fill_density']),
                'aspect_ratio': float(comp['aspect_ratio']),
                'centroid': comp['centroid']
            }
            components_summary.append(comp_summary)
        
        return jsonify({
            'success': True,
            'component_count': scan_results['component_count'],
            'pixel_count': scan_results['pixel_count'],
            'dark_pixel_ratio': float(scan_results['dark_pixel_ratio']),
            'components': components_summary,
            'component_types': {
                'text': sum(1 for c in scan_results['components'] if c['type'] == 'text'),
                'shape': sum(1 for c in scan_results['components'] if c['type'] == 'shape'),
                'hline': sum(1 for c in scan_results['components'] if c['type'] == 'hline'),
                'vline': sum(1 for c in scan_results['components'] if c['type'] == 'vline'),
                'connector': sum(1 for c in scan_results['components'] if c['type'] == 'connector'),
                'separator': sum(1 for c in scan_results['components'] if c['type'] == 'separator')
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/scan/shapes', methods=['POST'])
def detect_shapes():
    """
    Detect and classify shapes
    Returns shape information with types and properties
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        image_file = request.files['image']
        
        # Read image
        image_bytes = image_file.read()
        image_array = cv2.imdecode(
            np.frombuffer(image_bytes, np.uint8),
            cv2.IMREAD_COLOR
        )
        
        if image_array is None:
            return jsonify({'error': 'Invalid image format'}), 400
        
        # Binarize
        binarizer = AdaptiveBinarizer()
        binary = binarizer.binarize(image_array)
        
        # Trace shapes
        tracer = SmartShapeTracer()
        shapes = tracer.trace_shapes(binary)
        
        return jsonify({
            'success': True,
            'shape_count': len(shapes),
            'shapes': [
                {
                    'type': s['type'],
                    'bbox': s['bbox'],
                    'area': float(s['area']),
                    'aspect_ratio': float(s['aspect_ratio']),
                    'circularity': float(s['circularity']),
                    'fill_fraction': float(s['fill_fraction'])
                }
                for s in shapes
            ],
            'shape_types': {
                'rectangle': sum(1 for s in shapes if s['type'] == 'rectangle'),
                'rectangle_wide': sum(1 for s in shapes if s['type'] == 'rectangle_wide'),
                'circle': sum(1 for s in shapes if s['type'] == 'circle'),
                'diamond': sum(1 for s in shapes if s['type'] == 'diamond'),
                'irregular': sum(1 for s in shapes if s['type'] == 'irregular')
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/scan/connectors', methods=['POST'])
def detect_connectors():
    """
    Detect connector lines and build adjacency graph
    Useful for flowchart and diagram analysis
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        image_file = request.files['image']
        
        # Read image
        image_bytes = image_file.read()
        image_array = cv2.imdecode(
            np.frombuffer(image_bytes, np.uint8),
            cv2.IMREAD_COLOR
        )
        
        if image_array is None:
            return jsonify({'error': 'Invalid image format'}), 400
        
        # Binarize
        binarizer = AdaptiveBinarizer()
        binary = binarizer.binarize(image_array)
        
        # Detect shapes first
        tracer = SmartShapeTracer()
        shapes = tracer.trace_shapes(binary)
        
        # Trace connectors
        connector_tracer = ConnectorTracer()
        connector_results = connector_tracer.trace_connectors(binary, shapes)
        
        # Convert graph to JSON-serializable format
        graph_json = {str(k): v for k, v in connector_results['graph'].items()}
        
        return jsonify({
            'success': True,
            'connector_count': len(connector_results['connectors']),
            'connection_count': connector_results['connection_count'],
            'shape_count': len(shapes),
            'graph': graph_json,
            'graph_nodes': len(shapes),
            'graph_edges': connector_results['connection_count'],
            'connectors': [
                {
                    'start': c['start'],
                    'end': c['end'],
                    'type': c['type']
                }
                for c in connector_results['connectors']
            ]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False') == 'True'
    
    # Print startup configuration
    print("\n" + "="*80)
    print("🚀 DOCUGRAPH Backend API Server - Startup (with Advanced Document Scanning)")
    print("="*80)
    print(f"\n📡 CORS Configuration (Production Domains):")
    for origin in cors_origins:
        print(f"   ✓ {origin}")
    print(f"\n🔌 Server Configuration:")
    print(f"   Host: 0.0.0.0")
    print(f"   Port: {port}")
    print(f"   Debug Mode: {debug}")
    print(f"\n🌐 Access URLs:")
    print(f"   Local: http://localhost:{port}")
    print(f"   Network: http://0.0.0.0:{port}")
    print(f"   Production: https://docugraph.site:{port}")
    print(f"\n📋 Core API Endpoints:")
    print(f"   Health: http://localhost:{port}/health")
    print(f"   Diagnostics: http://localhost:{port}/diagnostics")
    print(f"   Layout Analysis: http://localhost:{port}/api/v1/layout/analyze")
    print(f"   OCR Extract: http://localhost:{port}/api/v1/ocr/extract")
    print(f"\n🎯 Advanced Document Scanning Endpoints:")
    print(f"   Full Scan: http://localhost:{port}/api/v1/scan/advanced")
    print(f"     → Sauvola binarization + pixel scanner + shapes + connectors + OCR")
    print(f"   Binarize: http://localhost:{port}/api/v1/scan/binarize")
    print(f"     → Adaptive Sauvola binarization")
    print(f"   Components: http://localhost:{port}/api/v1/scan/components")
    print(f"     → Union-Find connected component analysis")
    print(f"   Shapes: http://localhost:{port}/api/v1/scan/shapes")
    print(f"     → Smart shape detection and classification")
    print(f"   Connectors: http://localhost:{port}/api/v1/scan/connectors")
    print(f"     → Connector tracing and adjacency graph")
    print(f"\n✨ Features:")
    print(f"   • Sauvola adaptive binarization for shadows and lighting")
    print(f"   • Union-Find pixel scanner for precise component detection")
    print(f"   • Word-level OCR with 3× scaling and parallel processing")
    print(f"   • Smart shape tracer for flowcharts and diagrams")
    print(f"   • Connector tracer for graph adjacency building")
    print(f"\n💡 Press CTRL+C to stop the server\n")
    print("="*80 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
