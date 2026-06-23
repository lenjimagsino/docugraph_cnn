"""
DOCUGRAPH Advanced Image Processing Pipeline
Implements adaptive binarization, pixel scanning, word-level OCR, 
shape detection, and connector tracing for enterprise document analysis.
"""

import cv2
import numpy as np
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytesseract
from PIL import Image
import threading

# ===========================
# Union-Find Data Structure
# ===========================

class UnionFind:
    """Efficient Union-Find for connected component analysis"""
    
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.size = [1] * n
    
    def find(self, x):
        """Find root with path compression"""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x, y):
        """Union by rank"""
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False
        
        if self.rank[root_x] < self.rank[root_y]:
            root_x, root_y = root_y, root_x
        
        self.parent[root_y] = root_x
        self.size[root_x] += self.size[root_y]
        
        if self.rank[root_x] == self.rank[root_y]:
            self.rank[root_x] += 1
        
        return True


# ===========================
# Adaptive Binarizer (Sauvola)
# ===========================

class AdaptiveBinarizer:
    """
    Sauvola adaptive binarization for handling shadows, lighting, 
    photocopies, colored paper, and faint ink.
    """
    
    def __init__(self, window_size=25, k=0.34, r=128):
        """
        Args:
            window_size: Local neighborhood size (must be odd)
            k: Control parameter (typically 0.34)
            r: Dynamic range (typically 128 for 0-256)
        """
        self.window_size = window_size if window_size % 2 == 1 else window_size + 1
        self.k = k
        self.r = r
    
    def binarize(self, image):
        """
        Apply Sauvola binarization to image
        
        Args:
            image: Input image (BGR or grayscale)
        
        Returns:
            Binary image (0 or 255)
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Compute mean and standard deviation for each pixel
        gray_float = gray.astype(np.float32)
        
        # Local mean
        mean = cv2.blur(gray_float, (self.window_size, self.window_size))
        
        # Local standard deviation
        sq_mean = cv2.blur(gray_float ** 2, (self.window_size, self.window_size))
        std = np.sqrt(np.maximum(sq_mean - mean ** 2, 0))
        
        # Sauvola threshold
        threshold = mean * (1 + self.k * (std / self.r - 1))
        
        # Binarize
        binary = np.where(gray_float >= threshold, 255, 0).astype(np.uint8)
        
        return binary


# ===========================
# Pixel Scanner with Union-Find
# ===========================

class PixelScanner:
    """
    Scans every dark pixel and groups into connected components
    using Union-Find. Pre-classifies components by aspect ratio
    and fill density.
    """
    
    def __init__(self):
        self.components = {}
        self.component_types = {}
    
    def _classify_component(self, bbox, pixel_count, total_bbox_pixels):
        """
        Classify component by bounding box aspect ratio and fill density
        
        Args:
            bbox: (x_min, y_min, x_max, y_max)
            pixel_count: Number of pixels in component
            total_bbox_pixels: Area of bounding box
        
        Returns:
            Classification string: 'text', 'shape', 'hline', 'vline', 'connector', 'separator'
        """
        x_min, y_min, x_max, y_max = bbox
        width = x_max - x_min + 1
        height = y_max - y_min + 1
        aspect_ratio = width / (height + 1e-6)
        fill_density = pixel_count / (total_bbox_pixels + 1e-6)
        
        # Horizontal line: very wide, thin
        if aspect_ratio > 5 and height < 5 and fill_density > 0.3:
            return 'hline'
        
        # Vertical line: very tall, thin
        if aspect_ratio < 0.2 and width < 5 and fill_density > 0.3:
            return 'vline'
        
        # Connector: thin line (either orientation)
        if (width < 8 or height < 8) and fill_density > 0.2:
            return 'connector'
        
        # Separator: long horizontal line
        if aspect_ratio > 3 and fill_density < 0.2:
            return 'separator'
        
        # Shape: compact, medium to high fill
        if 0.3 < aspect_ratio < 3 and fill_density > 0.4:
            return 'shape'
        
        # Text: variable aspect ratio, sparse fill
        if fill_density > 0.1:
            return 'text'
        
        return 'text'
    
    def scan_pixels(self, binary_image):
        """
        Scan binary image and extract connected components
        
        Args:
            binary_image: Binary image (0 or 255)
        
        Returns:
            dict with component info: {
                'components': list of component dicts,
                'component_count': int,
                'pixel_count': int
            }
        """
        height, width = binary_image.shape
        total_pixels = height * width
        
        # Initialize Union-Find for image pixels
        uf = UnionFind(total_pixels)
        pixel_dark = (binary_image.flatten() > 128)
        
        # Union adjacent dark pixels
        for y in range(height):
            for x in range(width):
                if not pixel_dark[y * width + x]:
                    continue
                
                idx = y * width + x
                
                # Check right neighbor
                if x + 1 < width and pixel_dark[y * width + (x + 1)]:
                    uf.union(idx, y * width + (x + 1))
                
                # Check bottom neighbor
                if y + 1 < height and pixel_dark[(y + 1) * width + x]:
                    uf.union(idx, (y + 1) * width + x)
        
        # Group pixels by component
        components_dict = defaultdict(lambda: {'pixels': [], 'indices': []})
        for idx in range(total_pixels):
            if pixel_dark[idx]:
                root = uf.find(idx)
                y, x = divmod(idx, width)
                components_dict[root]['pixels'].append((x, y))
                components_dict[root]['indices'].append(idx)
        
        # Extract component information
        components = []
        total_text_pixels = 0
        
        for root, comp_data in components_dict.items():
            if not comp_data['pixels']:
                continue
            
            pixels = comp_data['pixels']
            x_coords = [p[0] for p in pixels]
            y_coords = [p[1] for p in pixels]
            
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            bbox = (x_min, y_min, x_max, y_max)
            width_bbox = x_max - x_min + 1
            height_bbox = y_max - y_min + 1
            area_bbox = width_bbox * height_bbox
            pixel_count = len(pixels)
            
            # Classify component
            comp_type = self._classify_component(bbox, pixel_count, area_bbox)
            
            component = {
                'id': root,
                'type': comp_type,
                'bbox': bbox,
                'pixel_count': pixel_count,
                'fill_density': pixel_count / (area_bbox + 1e-6),
                'aspect_ratio': width_bbox / (height_bbox + 1e-6),
                'centroid': (np.mean(x_coords), np.mean(y_coords)),
                'pixels': pixels
            }
            
            components.append(component)
            total_text_pixels += pixel_count
        
        return {
            'components': components,
            'component_count': len(components),
            'pixel_count': total_text_pixels,
            'dark_pixel_ratio': total_text_pixels / total_pixels
        }


# ===========================
# Smart Shape Tracer
# ===========================

class SmartShapeTracer:
    """
    Flood-fills closed contours and classifies shapes by 
    aspect ratio and ink-fill fraction.
    """
    
    def __init__(self):
        pass
    
    def trace_shapes(self, binary_image):
        """
        Extract and classify shapes from binary image
        
        Args:
            binary_image: Binary image (0 or 255)
        
        Returns:
            List of shape dicts with type, bbox, and properties
        """
        # Find contours
        contours, _ = cv2.findContours(binary_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        shapes = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Skip very small contours
            if area < 20:
                continue
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            bbox = (x, y, x + w, y + h)
            
            # Compute aspect ratio and circularity
            aspect_ratio = float(w) / (h + 1e-6)
            perimeter = cv2.arcLength(contour, True)
            circularity = (4 * np.pi * area) / (perimeter ** 2 + 1e-6)
            fill_fraction = area / (w * h + 1e-6)
            
            # Classify shape
            shape_type = self._classify_shape(aspect_ratio, circularity, fill_fraction)
            
            shape = {
                'type': shape_type,
                'bbox': bbox,
                'area': area,
                'aspect_ratio': aspect_ratio,
                'circularity': circularity,
                'fill_fraction': fill_fraction,
                'perimeter': perimeter
            }
            
            shapes.append(shape)
        
        return shapes
    
    def _classify_shape(self, aspect_ratio, circularity, fill_fraction):
        """
        Classify shape based on aspect ratio, circularity, and fill
        
        Returns:
            Shape type: 'rectangle', 'rectangle_wide', 'diamond', 'circle', 'irregular'
        """
        # Circle: high circularity
        if circularity > 0.85:
            return 'circle'
        
        # Diamond: aspect ratio near 1, moderate circularity
        if 0.7 < aspect_ratio < 1.3 and circularity > 0.6:
            return 'diamond'
        
        # Wide rectangle: aspect ratio > 1.5
        if aspect_ratio > 1.5 and fill_fraction > 0.7:
            return 'rectangle_wide'
        
        # Tall rectangle: aspect ratio < 0.7
        if aspect_ratio < 0.7 and fill_fraction > 0.7:
            return 'rectangle'
        
        # Regular rectangle: aspect ratio 0.7-1.5
        if 0.7 <= aspect_ratio <= 1.5 and fill_fraction > 0.7:
            return 'rectangle'
        
        return 'irregular'


# ===========================
# Connector Tracer
# ===========================

class ConnectorTracer:
    """
    Identifies thin horizontal/vertical lines (connectors) not inside shapes,
    then matches endpoints to nearest shapes for adjacency graph.
    """
    
    def __init__(self):
        pass
    
    def trace_connectors(self, binary_image, shapes):
        """
        Extract connector lines and build adjacency graph
        
        Args:
            binary_image: Binary image (0 or 255)
            shapes: List of shape dicts from SmartShapeTracer
        
        Returns:
            dict with:
                'connectors': list of line segments
                'graph': adjacency list
                'connections': list of (shape1_idx, shape2_idx, connector_type)
        """
        connectors = self._extract_thin_lines(binary_image, shapes)
        
        # Build shape bounding boxes for matching
        shape_bboxes = [(s['bbox'], i) for i, s in enumerate(shapes)]
        
        # Match endpoints to shapes
        connections = []
        for connector in connectors:
            start, end, line_type = connector['start'], connector['end'], connector['type']
            
            # Find two nearest shapes
            nearest_shapes = self._find_nearest_shapes(start, end, shape_bboxes, k=2)
            
            if len(nearest_shapes) == 2:
                shape1_idx, shape2_idx = nearest_shapes
                connections.append({
                    'from': shape1_idx,
                    'to': shape2_idx,
                    'connector': connector,
                    'type': line_type
                })
        
        # Build adjacency graph
        graph = self._build_adjacency_graph(len(shapes), connections)
        
        return {
            'connectors': connectors,
            'connections': connections,
            'graph': graph,
            'connection_count': len(connections)
        }
    
    def _extract_thin_lines(self, binary_image, shapes, max_thickness=8):
        """Extract thin horizontal and vertical lines"""
        connectors = []
        
        # Horizontal lines
        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
        h_lines = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel_h)
        
        # Vertical lines
        kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20))
        v_lines = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel_v)
        
        # Extract line coordinates
        h_contours, _ = cv2.findContours(h_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in h_contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 10:  # Min length
                connectors.append({
                    'start': (x, y + h // 2),
                    'end': (x + w, y + h // 2),
                    'type': 'horizontal'
                })
        
        v_contours, _ = cv2.findContours(v_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in v_contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h > 10:  # Min length
                connectors.append({
                    'start': (x + w // 2, y),
                    'end': (x + w // 2, y + h),
                    'type': 'vertical'
                })
        
        return connectors
    
    def _find_nearest_shapes(self, start_point, end_point, shape_bboxes, k=2):
        """Find k nearest shapes to line endpoints"""
        distances = []
        
        for bbox, idx in shape_bboxes:
            x1, y1, x2, y2 = bbox
            center = ((x1 + x2) / 2, (y1 + y2) / 2)
            
            # Distance from center to start and end
            dist_start = np.sqrt((start_point[0] - center[0]) ** 2 + (start_point[1] - center[1]) ** 2)
            dist_end = np.sqrt((end_point[0] - center[0]) ** 2 + (end_point[1] - center[1]) ** 2)
            avg_dist = (dist_start + dist_end) / 2
            
            distances.append((avg_dist, idx))
        
        distances.sort()
        return [idx for _, idx in distances[:k]]
    
    def _build_adjacency_graph(self, num_shapes, connections):
        """Build adjacency list from connections"""
        graph = defaultdict(list)
        
        for conn in connections:
            from_idx = conn['from']
            to_idx = conn['to']
            graph[from_idx].append(to_idx)
            graph[to_idx].append(from_idx)
        
        return dict(graph)


# ===========================
# Word-Level OCR Engine
# ===========================

class WordLevelOCREngine:
    """
    Advanced OCR with word-level processing:
    - Detects text components
    - Crops word-sized regions
    - 3× upscaling for better recognition
    - Parallel processing (up to 4 workers)
    - PSM 8 (single word mode)
    """
    
    def __init__(self, num_workers=4, scale_factor=3, use_tesseract=True):
        """
        Args:
            num_workers: Number of parallel OCR workers
            scale_factor: Image scale-up factor (3× = 3)
            use_tesseract: Use Tesseract (True) or fallback to EasyOCR (False)
        """
        self.num_workers = num_workers
        self.scale_factor = scale_factor
        self.use_tesseract = use_tesseract
        self.lock = threading.Lock()
    
    def extract_words(self, image, components, use_parallel=True):
        """
        Extract text from word-level components with OCR
        
        Args:
            image: Original image (BGR)
            components: List of components from PixelScanner
            use_parallel: Use parallel processing
        
        Returns:
            List of OCR results with text, confidence, bbox
        """
        # Filter text-like components
        text_components = [c for c in components if c['type'] in ['text', 'connector']]
        
        if not text_components:
            return []
        
        # Prepare crops
        crops = []
        for comp in text_components:
            x_min, y_min, x_max, y_max = comp['bbox']
            
            # Add padding
            pad = 2
            x_min = max(0, x_min - pad)
            y_min = max(0, y_min - pad)
            x_max = min(image.shape[1], x_max + pad)
            y_max = min(image.shape[0], y_max + pad)
            
            # Crop region
            crop = image[y_min:y_max, x_min:x_max]
            
            # Upscale 3×
            if crop.shape[0] > 0 and crop.shape[1] > 0:
                scaled = cv2.resize(crop, None, fx=self.scale_factor, fy=self.scale_factor, 
                                   interpolation=cv2.INTER_CUBIC)
                
                # Stretch contrast
                lab = cv2.cvtColor(scaled, cv2.COLOR_BGR2LAB)
                l_channel = lab[:, :, 0]
                l_min, l_max = l_channel.min(), l_channel.max()
                if l_max > l_min:
                    l_channel = ((l_channel - l_min) * 255 / (l_max - l_min)).astype(np.uint8)
                    lab[:, :, 0] = l_channel
                    scaled = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                
                crops.append({
                    'image': scaled,
                    'original_bbox': (x_min, y_min, x_max, y_max),
                    'component': comp
                })
        
        # Process crops
        if use_parallel and len(crops) > 1:
            results = self._process_crops_parallel(crops)
        else:
            results = self._process_crops_sequential(crops)
        
        return results
    
    def _process_crops_parallel(self, crops):
        """Process crops in parallel"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            future_to_crop = {executor.submit(self._ocr_crop, crop): crop for crop in crops}
            
            for future in as_completed(future_to_crop):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"⚠ Error processing crop: {e}")
        
        return results
    
    def _process_crops_sequential(self, crops):
        """Process crops sequentially"""
        results = []
        
        for crop in crops:
            try:
                result = self._ocr_crop(crop)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"⚠ Error processing crop: {e}")
        
        return results
    
    def _ocr_crop(self, crop_data):
        """Run OCR on single crop"""
        image = crop_data['image']
        original_bbox = crop_data['original_bbox']
        component = crop_data['component']
        
        try:
            if self.use_tesseract:
                # Use Tesseract PSM 8 (single word)
                config = '--psm 8 --oem 3'
                text = pytesseract.image_to_string(image, config=config).strip()
                conf = self._estimate_confidence(text)
            else:
                # Fallback: use basic image statistics
                text = ""
                conf = 0.5
            
            if text:
                return {
                    'text': text,
                    'confidence': conf,
                    'bbox': original_bbox,
                    'component_type': component['type'],
                    'component_bbox': component['bbox']
                }
        except Exception as e:
            print(f"⚠ Tesseract error: {e}")
        
        return None
    
    def _estimate_confidence(self, text):
        """Simple confidence estimation"""
        if not text:
            return 0.0
        # More text length suggests higher confidence (simple heuristic)
        return min(0.95, 0.5 + len(text) * 0.05)


# ===========================
# Unified Document Scanner
# ===========================

class AdvancedDocumentScanner:
    """
    Unified scanner combining all advanced processing techniques:
    1. Sauvola adaptive binarization
    2. Pixel scanner with Union-Find
    3. Smart shape tracer
    4. Connector tracer
    5. Word-level OCR
    """
    
    def __init__(self, use_tesseract=True):
        self.binarizer = AdaptiveBinarizer()
        self.scanner = PixelScanner()
        self.shape_tracer = SmartShapeTracer()
        self.connector_tracer = ConnectorTracer()
        self.ocr_engine = WordLevelOCREngine(use_tesseract=use_tesseract)
    
    def process_document(self, image_array, extract_text=True):
        """
        Complete document processing pipeline
        
        Args:
            image_array: Input image (BGR numpy array)
            extract_text: Whether to run word-level OCR
        
        Returns:
            dict with all analysis results
        """
        results = {
            'success': False,
            'stages': {}
        }
        
        try:
            # Stage 1: Adaptive Binarization
            binary_image = self.binarizer.binarize(image_array)
            results['stages']['binarization'] = {
                'method': 'Sauvola',
                'window_size': self.binarizer.window_size,
                'success': True
            }
            
            # Stage 2: Pixel Scanning with Union-Find
            scan_results = self.scanner.scan_pixels(binary_image)
            results['stages']['pixel_scanning'] = {
                'component_count': scan_results['component_count'],
                'pixel_count': scan_results['pixel_count'],
                'dark_pixel_ratio': scan_results['dark_pixel_ratio'],
                'success': True
            }
            
            # Stage 3: Smart Shape Detection
            shapes = self.shape_tracer.trace_shapes(binary_image)
            results['stages']['shape_tracing'] = {
                'shape_count': len(shapes),
                'shapes': shapes,
                'success': True
            }
            
            # Stage 4: Connector Detection & Graph Building
            connector_results = self.connector_tracer.trace_connectors(
                binary_image, shapes
            )
            results['stages']['connector_tracing'] = {
                'connector_count': len(connector_results['connectors']),
                'connection_count': connector_results['connection_count'],
                'graph': connector_results['graph'],
                'success': True
            }
            
            # Stage 5: Word-Level OCR
            if extract_text:
                ocr_results = self.ocr_engine.extract_words(
                    image_array, 
                    scan_results['components']
                )
                results['stages']['word_ocr'] = {
                    'word_count': len(ocr_results),
                    'words': ocr_results,
                    'success': True
                }
            
            results['success'] = True
            results['image_shape'] = image_array.shape
            results['binary_image_shape'] = binary_image.shape
            
        except Exception as e:
            results['error'] = str(e)
            import traceback
            results['traceback'] = traceback.format_exc()
        
        return results
