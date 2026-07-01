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
                extra_config=[["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5], ["MODEL.DEVICE", "cpu"]],
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
            
            # Extract CNN predictions with normalized bboxes
            h, w = image_array.shape[:2]
            cnn_predictions = []
            for block in layout:
                norm_bbox = self._normalize_bbox(block.x_1, block.y_1, block.x_2, block.y_2, w, h)
                bw = block.x_2 - block.x_1
                bh = block.y_2 - block.y_1
                pred = {
                    'type': block.type,
                    'bbox': norm_bbox,
                    'bbox_px': [block.x_1, block.y_1, block.x_2, block.y_2],
                    'confidence': float(block.score) if hasattr(block, 'score') else 0.95,
                    'area': bw * bh,
                    'features': {
                        'width': bw,
                        'height': bh,
                        'aspect_ratio': bw / bh if bh > 0 else 0
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
                    'layout_accuracy': self._calculate_layout_accuracy(cnn_predictions),
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
    
    def _calculate_layout_accuracy(self, predictions: List[Dict]) -> float:
        """
        Calculate layout accuracy as a function of:
        - Average confidence of detected regions
        - Region count (more regions = better detection)
        - Confidence distribution variance
        
        Returns: accuracy score 0-1
        """
        if not predictions:
            return 0.0
        
        # Get confidence scores
        confidences = [p.get('confidence', 0.5) for p in predictions]
        avg_conf = np.mean(confidences) if confidences else 0.5
        
        # Region count factor (logarithmic scale, capped)
        region_count = len(predictions)
        region_factor = min(1.0, np.log(region_count + 1) / 4.0)  # Scales 0-1 with diminishing returns
        
        # Confidence stability (lower variance = more stable)
        conf_std = np.std(confidences) if len(confidences) > 1 else 0.0
        stability_factor = 1.0 - (conf_std * 0.3)  # Down-weight high variance
        stability_factor = max(0.5, stability_factor)
        
        # Combine factors: average confidence + region detection boost + stability
        layout_accuracy = (avg_conf * 0.6 + region_factor * 0.25 + stability_factor * 0.15)
        
        return float(min(1.0, max(0.0, layout_accuracy)))
    
    @staticmethod
    def _normalize_bbox(x1: float, y1: float, x2: float, y2: float, img_w: int, img_h: int) -> List[float]:
        """Convert pixel coords to 0-100 percentage values for the JS renderer."""
        if img_w <= 0 or img_h <= 0:
            return [0.0, 0.0, 100.0, 100.0]
        return [
            round(x1 / img_w * 100, 4),
            round(y1 / img_h * 100, 4),
            round(x2 / img_w * 100, 4),
            round(y2 / img_h * 100, 4),
        ]
    
    def _fallback_analysis(self, image_array: np.ndarray) -> Dict:
        """
        Fallback CNN analysis when LayoutParser not available
        Uses grid-based layout detection and contour analysis
        """
        h, w = image_array.shape[:2]
        
        # Convert to grayscale for edge detection
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
        else:
            gray = image_array
        
        # Detect edges
        edges = cv2.Canny(gray, 100, 200)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        predictions = []
        
        # Extract largest contours as blocks
        for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
            x, y, bw, bh = cv2.boundingRect(contour)
            
            # Filter small contours
            if bw < 20 or bh < 20:
                continue
            
            # Normalize bbox to percentages
            norm_bbox = self._normalize_bbox(x, y, x + bw, y + bh, w, h)
            
            # Heuristic confidence scoring for fallback:
            # - area_ratio: contour area relative to image area (larger blocks -> higher confidence)
            # - solidity: contour area divided by bounding-box area (more filled -> higher confidence)
            # - edge_strength: average Canny response inside the bbox (stronger edges -> higher confidence)
            area = float(bw * bh)
            area_ratio = area / float(w * h) if (w * h) > 0 else 0.0
            bbox_area = float(bw * bh) if (bw * bh) > 0 else 1.0
            contour_area = float(cv2.contourArea(contour))
            solidity = (contour_area / bbox_area) if bbox_area > 0 else 0.0

            # Edge strength within bbox
            try:
                roi = edges[y:y+bh, x:x+bw]
                edge_strength = float(roi.mean() / 255.0) if roi.size > 0 else 0.0
            except Exception:
                edge_strength = 0.0

            # Normalize area_ratio to a 0-1 scale (heuristic): multiply by 8 and clamp
            norm_area = min(1.0, area_ratio * 8.0)

            # Weighted combination
            score = 0.5 * norm_area + 0.3 * solidity + 0.2 * edge_strength
            # Map to reasonable confidence range [0.4, 0.95]
            confidence = float(max(0.0, min(1.0, score)))
            confidence = 0.4 + (confidence * 0.55)

            predictions.append({
                'type': 'Text',
                'bbox': norm_bbox,
                'bbox_px': [x, y, x + bw, y + bh],
                'confidence': confidence,
                'area': bw * bh,
                'features': {
                    'width': bw,
                    'height': bh,
                    'aspect_ratio': bw / bh if bh > 0 else 0,
                    'solidity': solidity,
                    'edge_strength': edge_strength,
                    'area_ratio': area_ratio
                }
            })
        
        # If no contours detected, use full page
        if not predictions:
            norm_bbox = self._normalize_bbox(0, 0, w, h, w, h)
            # Heuristic for full-page confidence: based on overall edge density
            try:
                edge_strength = float(edges.mean() / 255.0) if edges.size > 0 else 0.0
            except Exception:
                edge_strength = 0.0
            # Map to range [0.45, 0.7]
            confidence = 0.45 + (edge_strength * 0.25)
            predictions.append({
                'type': 'Text',
                'bbox': norm_bbox,
                'bbox_px': [0, 0, w, h],
                'confidence': confidence,
                'area': h * w,
                'features': {
                    'width': w,
                    'height': h,
                    'aspect_ratio': w / h if h > 0 else 0,
                    'edge_strength': edge_strength
                }
            })
        
        avg_confidence = np.mean([p['confidence'] for p in predictions]) if predictions else 0.5
        
        return {
            'success': True,
            'model': 'CNN-only (Fallback - Edge Detection)',
            'predictions': predictions,
            'prediction_count': len(predictions),
            'feature_maps': {},
                'statistics': {
                    'total_blocks': len(predictions),
                    'avg_confidence': float(avg_confidence),
                    'layout_accuracy': self._calculate_layout_accuracy(predictions),
                    'type_distribution': {'Text': len(predictions)},
                    'image_shape': list(image_array.shape),
                    'fallback': True,
                    'fallback_confidence_method': 'area_ratio*0.5 + solidity*0.3 + edge_strength*0.2 (mapped to 0.4-0.95)'
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
    
    def analyze_layout_cnn_only(self, image_array: np.ndarray) -> Dict[str, Any]:
        """
        CNN-only layout analysis (wrapper for API compatibility)
        
        Args:
            image_array: Input image
        
        Returns:
            Dict with CNN-only layout analysis
        """
        return self.layout_analyzer.analyze_layout_cnn_only(image_array)
    
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
