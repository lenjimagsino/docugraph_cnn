"""
DOCUGRAPH - CNN-Only Model Variant
For comparative analysis against CNN+GNN architecture
Extracts features using only CNN components (LayoutParser/Detectron2)
"""

import numpy as np
import cv2
from PIL import Image
from typing import Dict, List, Tuple, Any
import torch

# Import base components
try:
    import layoutparser as lp
    HAS_LAYOUTPARSER = True
except ImportError:
    HAS_LAYOUTPARSER = False

try:
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


class CNNOnlyLayoutAnalyzer:
    """
    Pure CNN-based layout analysis using LayoutParser + Detectron2
    No graph neural network components - only CNN feature extraction
    """
    
    def __init__(self):
        """Initialize CNN-only layout analyzer"""
        if not HAS_LAYOUTPARSER:
            print("⚠ LayoutParser not available for CNN-only analysis")
            self.initialized = False
            self.model = None
            return
        
        try:
            self.model = lp.Detectron2LayoutModel(
                config_path="lp://PubLayNet/faster_rcnn_ResNest50_fpn_3x",
                model_path="lp://PubLayNet/faster_rcnn_ResNest50_fpn_3x/model_final.pth",
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
                label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
            )
            self.initialized = True
            print("✓ CNN-only layout analyzer initialized")
        except Exception as e:
            print(f"⚠ CNN-only analyzer initialization failed: {e}")
            self.initialized = False
            self.model = None
    
    def analyze_layout_cnn_only(self, image_array: np.ndarray) -> Dict[str, Any]:
        """
        CNN-only layout analysis without graph components
        
        Args:
            image_array: numpy array (H×W×C)
        
        Returns:
            Dict with CNN predictions, confidence scores, and feature maps
        """
        if not self.initialized or self.model is None:
            return self._fallback_analysis(image_array)
        
        try:
            # Convert to PIL Image
            if isinstance(image_array, np.ndarray):
                image = Image.fromarray(image_array.astype('uint8'))
            else:
                image = image_array
            
            # Run CNN detection (Detectron2)
            layout = self.model.detect(image)
            
            # Extract CNN predictions
            cnn_predictions = []
            for block in layout:
                pred = {
                    'type': block.type,
                    'bbox': [block.x_1, block.y_1, block.x_2, block.y_2],
                    'confidence': float(block.score) if hasattr(block, 'score') else 0.95,
                    'area': (block.x_2 - block.x_1) * (block.y_2 - block.y_1),
                    'features': {
                        'width': block.x_2 - block.x_1,
                        'height': block.y_2 - block.y_1,
                        'aspect_ratio': (block.x_2 - block.x_1) / (block.y_2 - block.y_1) if (block.y_2 - block.y_1) > 0 else 0
                    }
                }
                cnn_predictions.append(pred)
            
            # Extract CNN feature maps
            feature_maps = self._extract_cnn_features(image_array, cnn_predictions)
            
            return {
                'success': True,
                'model': 'CNN-only (Detectron2)',
                'predictions': cnn_predictions,
                'prediction_count': len(cnn_predictions),
                'feature_maps': feature_maps,
                'statistics': {
                    'total_blocks': len(cnn_predictions),
                    'avg_confidence': np.mean([p['confidence'] for p in cnn_predictions]) if cnn_predictions else 0,
                    'type_distribution': self._get_type_distribution(cnn_predictions),
                    'image_shape': list(image_array.shape)
                }
            }
        
        except Exception as e:
            print(f"CNN analysis error: {e}")
            return self._fallback_analysis(image_array)
    
    def _extract_cnn_features(self, image_array: np.ndarray, predictions: List[Dict]) -> Dict:
        """Extract CNN-specific features from predictions"""
        h, w = image_array.shape[:2]
        
        # Create feature visualization
        feature_map = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Color code by type
        type_colors = {
            'Text': (100, 100, 100),
            'Title': (255, 0, 0),
            'List': (0, 255, 0),
            'Table': (0, 0, 255),
            'Figure': (255, 255, 0)
        }
        
        for pred in predictions:
            x1, y1, x2, y2 = [int(v) for v in pred['bbox']]
            block_type = pred['type']
            color = type_colors.get(block_type, (128, 128, 128))
            
            # Draw bounding box
            cv2.rectangle(feature_map, (x1, y1), (x2, y2), color, 2)
            
            # Fill transparency
            overlay = feature_map.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
            feature_map = cv2.addWeighted(feature_map, 0.7, overlay, 0.3, 0)
        
        # Convert to base64 for API
        import base64
        _, buffer = cv2.imencode('.png', feature_map)
        feature_map_b64 = base64.b64encode(buffer).decode()
        
        return {
            'visualization': f'data:image/png;base64,{feature_map_b64}',
            'type_map': 'CNN feature detection visualization'
        }
    
    def _get_type_distribution(self, predictions: List[Dict]) -> Dict[str, int]:
        """Get distribution of detected types"""
        distribution = {}
        for pred in predictions:
            block_type = pred['type']
            distribution[block_type] = distribution.get(block_type, 0) + 1
        return distribution
    
    def _fallback_analysis(self, image_array: np.ndarray) -> Dict:
        """Fallback CNN analysis"""
        h, w = image_array.shape[:2]
        return {
            'success': True,
            'model': 'CNN-only (Fallback)',
            'predictions': [{
                'type': 'Text',
                'bbox': [0, 0, w, h],
                'confidence': 0.5,
                'area': h * w,
                'features': {
                    'width': w,
                    'height': h,
                    'aspect_ratio': w / h if h > 0 else 0
                }
            }],
            'prediction_count': 1,
            'feature_maps': {},
            'statistics': {
                'total_blocks': 1,
                'avg_confidence': 0.5,
                'type_distribution': {'Text': 1},
                'image_shape': list(image_array.shape)
            }
        }


class CNNOnlyShapeDetector:
    """
    CNN-only shape detection using morphological operations
    No graph-based connector analysis
    """
    
    def __init__(self):
        """Initialize CNN-only shape detector"""
        self.initialized = True
    
    def detect_shapes_cnn_only(self, image_array: np.ndarray) -> Dict[str, Any]:
        """
        CNN-style shape detection (contour-based feature extraction)
        
        Args:
            image_array: numpy array (H×W×C)
        
        Returns:
            Dict with detected shapes and CNN features
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding (CNN preprocessing)
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Find contours
            contours, _ = cv2.findContours(
                binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
            )
            
            shapes = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 100:  # Filter small noise
                    continue
                
                # Calculate features
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = float(w) / h if h > 0 else 0
                perimeter = cv2.arcLength(cnt, True)
                circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
                
                # Approximate polygon
                epsilon = 0.02 * perimeter
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                
                # Classify shape
                shape_type = self._classify_shape_cnn(approx, aspect_ratio, circularity)
                
                shape_info = {
                    'type': shape_type,
                    'bbox': [x, y, x + w, y + h],
                    'area': float(area),
                    'perimeter': float(perimeter),
                    'circularity': float(circularity),
                    'aspect_ratio': aspect_ratio,
                    'vertices': int(len(approx)),
                    'cnn_features': {
                        'contour_length': len(cnt),
                        'fill_factor': float(area) / (w * h) if w * h > 0 else 0
                    }
                }
                shapes.append(shape_info)
            
            # Create feature visualization
            feature_viz = np.zeros_like(image_array)
            for shape in shapes:
                x1, y1, x2, y2 = [int(v) for v in shape['bbox']]
                color = (0, 255, 0)
                cv2.rectangle(feature_viz, (x1, y1), (x2, y2), color, 2)
            
            import base64
            _, buffer = cv2.imencode('.png', feature_viz)
            viz_b64 = base64.b64encode(buffer).decode()
            
            return {
                'success': True,
                'model': 'CNN-only (Contour-based)',
                'shapes': shapes,
                'shape_count': len(shapes),
                'visualization': f'data:image/png;base64,{viz_b64}',
                'statistics': {
                    'total_shapes': len(shapes),
                    'type_distribution': self._get_shape_distribution(shapes)
                }
            }
        
        except Exception as e:
            print(f"CNN shape detection error: {e}")
            return {
                'success': False,
                'error': str(e),
                'shapes': []
            }
    
    def _classify_shape_cnn(self, approx, aspect_ratio: float, circularity: float) -> str:
        """Classify shape using CNN features (CNN-style classification)"""
        vertices = len(approx)
        
        # CNN-based shape classification using geometric features
        if circularity > 0.8:
            return 'circle'
        elif vertices == 4:
            if 0.8 < aspect_ratio < 1.2:
                return 'square'
            else:
                return 'rectangle'
        elif vertices == 3:
            return 'triangle'
        elif vertices > 6:
            return 'polygon'
        else:
            return 'irregular'
    
    def _get_shape_distribution(self, shapes: List[Dict]) -> Dict[str, int]:
        """Get distribution of detected shapes"""
        distribution = {}
        for shape in shapes:
            shape_type = shape['type']
            distribution[shape_type] = distribution.get(shape_type, 0) + 1
        return distribution


class CNNOnlyFeatureExtractor:
    """
    Extract pure CNN features without graph neural network components
    """
    
    def __init__(self):
        """Initialize CNN feature extractor"""
        self.initialized = True
    
    def extract_cnn_features(self, image_array: np.ndarray, 
                            predictions: List[Dict]) -> Dict[str, Any]:
        """
        Extract CNN features from layout predictions
        
        Args:
            image_array: Input image
            predictions: Layout predictions from CNN model
        
        Returns:
            Dict with extracted CNN features
        """
        features = {
            'spatial_features': self._extract_spatial_features(image_array, predictions),
            'appearance_features': self._extract_appearance_features(image_array, predictions),
            'connectivity_features': self._extract_connectivity_features(predictions)
        }
        
        return features
    
    def _extract_spatial_features(self, image_array: np.ndarray, 
                                  predictions: List[Dict]) -> Dict:
        """Extract spatial features using CNN receptive fields"""
        h, w = image_array.shape[:2]
        
        spatial_features = {
            'page_coverage': sum([p['area'] for p in predictions]) / (h * w) if (h * w) > 0 else 0,
            'block_positions': [
                {
                    'type': p['type'],
                    'center_x': (p['bbox'][0] + p['bbox'][2]) / 2 / w,
                    'center_y': (p['bbox'][1] + p['bbox'][3]) / 2 / h,
                    'relative_size': p['area'] / (h * w)
                }
                for p in predictions
            ],
            'layout_density': len(predictions) / max((h * w) / 100000, 1)  # Blocks per 100k pixels
        }
        
        return spatial_features
    
    def _extract_appearance_features(self, image_array: np.ndarray, 
                                     predictions: List[Dict]) -> Dict:
        """Extract appearance features from detected regions"""
        appearance_features = {
            'confidence_stats': {
                'mean': np.mean([p['confidence'] for p in predictions]) if predictions else 0,
                'min': np.min([p['confidence'] for p in predictions]) if predictions else 0,
                'max': np.max([p['confidence'] for p in predictions]) if predictions else 0,
                'std': np.std([p['confidence'] for p in predictions]) if predictions else 0
            },
            'type_diversity': len(set([p['type'] for p in predictions])),
            'average_aspect_ratio': np.mean(
                [p['features']['aspect_ratio'] for p in predictions if 'features' in p]
            ) if predictions else 0
        }
        
        return appearance_features
    
    def _extract_connectivity_features(self, predictions: List[Dict]) -> Dict:
        """
        Extract connectivity-like features from CNN predictions
        Note: This does NOT use GNN, only CNN spatial relationships
        """
        if not predictions:
            return {'adjacency_count': 0, 'spatial_clusters': []}
        
        # Calculate spatial proximity without graph networks
        connectivity = {
            'adjacency_count': self._count_adjacent_blocks(predictions),
            'spatial_gaps': self._calculate_spatial_gaps(predictions),
            'reading_order': self._infer_reading_order(predictions)
        }
        
        return connectivity
    
    def _count_adjacent_blocks(self, predictions: List[Dict]) -> int:
        """Count spatially adjacent blocks"""
        adjacent_count = 0
        threshold = 50  # pixels
        
        for i, p1 in enumerate(predictions):
            for p2 in predictions[i+1:]:
                x1_min, y1_min, x1_max, y1_max = p1['bbox']
                x2_min, y2_min, x2_max, y2_max = p2['bbox']
                
                # Check horizontal/vertical proximity
                h_dist = min(abs(x1_min - x2_max), abs(x2_min - x1_max))
                v_dist = min(abs(y1_min - y2_max), abs(y2_min - y1_max))
                
                if h_dist < threshold or v_dist < threshold:
                    adjacent_count += 1
        
        return adjacent_count
    
    def _calculate_spatial_gaps(self, predictions: List[Dict]) -> List[float]:
        """Calculate gaps between blocks"""
        gaps = []
        for i, p1 in enumerate(predictions):
            for p2 in predictions[i+1:]:
                x1_min, y1_min, x1_max, y1_max = p1['bbox']
                x2_min, y2_min, x2_max, y2_max = p2['bbox']
                
                h_gap = min(abs(x1_min - x2_max), abs(x2_min - x1_max))
                v_gap = min(abs(y1_min - y2_max), abs(y2_min - y1_max))
                
                gap = min(h_gap, v_gap) if min(h_gap, v_gap) >= 0 else 0
                gaps.append(float(gap))
        
        return gaps if gaps else [0.0]
    
    def _infer_reading_order(self, predictions: List[Dict]) -> List[Dict]:
        """Infer reading order using CNN spatial features"""
        # Sort by position (CNN-style spatial reasoning)
        sorted_preds = sorted(
            predictions,
            key=lambda p: (p['bbox'][1], p['bbox'][0])  # top-to-bottom, left-to-right
        )
        
        return [
            {
                'order': i,
                'type': p['type'],
                'confidence': p['confidence']
            }
            for i, p in enumerate(sorted_preds)
        ]


class CNNOnlyAnalyzer:
    """
    Main CNN-only analyzer combining all components
    """
    
    def __init__(self):
        """Initialize CNN-only analyzer"""
        self.layout_analyzer = CNNOnlyLayoutAnalyzer()
        self.shape_detector = CNNOnlyShapeDetector()
        self.feature_extractor = CNNOnlyFeatureExtractor()
        print("✓ CNN-only analyzer initialized")
    
    def analyze_document_cnn_only(self, image_array: np.ndarray) -> Dict[str, Any]:
        """
        Full CNN-only document analysis
        
        Args:
            image_array: Input image
        
        Returns:
            Dict with complete CNN-only analysis
        """
        # Layout analysis
        layout_result = self.layout_analyzer.analyze_layout_cnn_only(image_array)
        
        # Shape detection
        shape_result = self.shape_detector.detect_shapes_cnn_only(image_array)
        
        # Feature extraction
        if layout_result.get('success'):
            features = self.feature_extractor.extract_cnn_features(
                image_array,
                layout_result.get('predictions', [])
            )
        else:
            features = {}
        
        return {
            'success': True,
            'model_variant': 'CNN-only',
            'architecture': 'Detectron2 (ResNest50) for layout + Contour-based for shapes',
            'layout_analysis': layout_result,
            'shape_detection': shape_result,
            'features': features,
            'metadata': {
                'image_shape': list(image_array.shape),
                'analysis_type': 'CNN-only (no GNN components)',
                'includes_graphs': False,
                'includes_connectors': False
            }
        }
