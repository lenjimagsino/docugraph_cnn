"""
DOCUGRAPH Comparison Utilities
Analyze and compare CNN-only vs CNN+GNN model performance
"""

import numpy as np
from typing import Dict, List, Tuple, Any
import json


class ModelComparator:
    """
    Compare CNN-only and CNN+GNN model predictions and performance metrics
    """
    
    def __init__(self):
        """Initialize comparator"""
        self.metrics = {}
    
    def compare_predictions(self, cnn_only_pred: Dict, gnn_pred: Dict) -> Dict[str, Any]:
        """
        Compare predictions from both models
        
        Args:
            cnn_only_pred: CNN-only model predictions
            gnn_pred: CNN+GNN model predictions
        
        Returns:
            Comparison metrics and analysis
        """
        comparison = {
            'overall': self._compare_overall_stats(cnn_only_pred, gnn_pred),
            'spatial_analysis': self._compare_spatial_properties(cnn_only_pred, gnn_pred),
            'type_analysis': self._compare_type_distributions(cnn_only_pred, gnn_pred),
            'confidence_analysis': self._compare_confidence_scores(cnn_only_pred, gnn_pred),
            'alignment': self._analyze_bounding_box_alignment(cnn_only_pred, gnn_pred),
            'feature_differences': self._extract_feature_differences(cnn_only_pred, gnn_pred)
        }
        
        return comparison
    
    def _compare_overall_stats(self, cnn_only_pred: Dict, gnn_pred: Dict) -> Dict:
        """Compare overall statistics"""
        cnn_blocks = cnn_only_pred.get('predictions', [])
        gnn_blocks = gnn_pred.get('blocks', []) or gnn_pred.get('predictions', [])
        
        return {
            'cnn_only_block_count': len(cnn_blocks),
            'gnn_block_count': len(gnn_blocks),
            'block_count_difference': abs(len(cnn_blocks) - len(gnn_blocks)),
            'block_count_difference_percent': (
                abs(len(cnn_blocks) - len(gnn_blocks)) / max(len(gnn_blocks), 1)
            ) * 100 if gnn_blocks else 0,
            'model_agreement': self._calculate_agreement(cnn_blocks, gnn_blocks)
        }
    
    def _compare_spatial_properties(self, cnn_only_pred: Dict, gnn_pred: Dict) -> Dict:
        """Compare spatial coverage and properties"""
        cnn_blocks = cnn_only_pred.get('predictions', [])
        gnn_blocks = gnn_pred.get('blocks', []) or gnn_pred.get('predictions', [])
        
        cnn_coverage = self._calculate_coverage(cnn_blocks)
        gnn_coverage = self._calculate_coverage(gnn_blocks)
        
        return {
            'cnn_only_coverage': cnn_coverage,
            'gnn_coverage': gnn_coverage,
            'coverage_difference': abs(cnn_coverage - gnn_coverage),
            'cnn_only_avg_block_size': np.mean([
                b['area'] for b in cnn_blocks if 'area' in b
            ]) if cnn_blocks else 0,
            'gnn_avg_block_size': np.mean([
                (b['bbox'][2] - b['bbox'][0]) * (b['bbox'][3] - b['bbox'][1])
                for b in gnn_blocks if 'bbox' in b
            ]) if gnn_blocks else 0
        }
    
    def _compare_type_distributions(self, cnn_only_pred: Dict, gnn_pred: Dict) -> Dict:
        """Compare type distributions"""
        cnn_blocks = cnn_only_pred.get('predictions', [])
        gnn_blocks = gnn_pred.get('blocks', []) or gnn_pred.get('predictions', [])
        
        cnn_types = {}
        for block in cnn_blocks:
            btype = block.get('type', 'unknown')
            cnn_types[btype] = cnn_types.get(btype, 0) + 1
        
        gnn_types = {}
        for block in gnn_blocks:
            btype = block.get('type', 'unknown')
            gnn_types[btype] = gnn_types.get(btype, 0) + 1
        
        # Normalize by total
        cnn_types_norm = {k: v / len(cnn_blocks) for k, v in cnn_types.items()} if cnn_blocks else {}
        gnn_types_norm = {k: v / len(gnn_blocks) for k, v in gnn_types.items()} if gnn_blocks else {}
        
        return {
            'cnn_only_type_distribution': cnn_types,
            'gnn_type_distribution': gnn_types,
            'cnn_only_type_normalized': cnn_types_norm,
            'gnn_type_normalized': gnn_types_norm,
            'type_agreement': self._calculate_type_agreement(cnn_types_norm, gnn_types_norm)
        }
    
    def _compare_confidence_scores(self, cnn_only_pred: Dict, gnn_pred: Dict) -> Dict:
        """Compare confidence distributions"""
        cnn_blocks = cnn_only_pred.get('predictions', [])
        gnn_blocks = gnn_pred.get('blocks', []) or gnn_pred.get('predictions', [])
        
        cnn_confs = [b.get('confidence', 0) for b in cnn_blocks if 'confidence' in b]
        gnn_confs = [b.get('confidence', 0) for b in gnn_blocks if 'confidence' in b]
        
        return {
            'cnn_only_conf_mean': np.mean(cnn_confs) if cnn_confs else 0,
            'cnn_only_conf_std': np.std(cnn_confs) if cnn_confs else 0,
            'gnn_conf_mean': np.mean(gnn_confs) if gnn_confs else 0,
            'gnn_conf_std': np.std(gnn_confs) if gnn_confs else 0,
            'confidence_correlation': self._calculate_correlation(cnn_confs, gnn_confs)
        }
    
    def _analyze_bounding_box_alignment(self, cnn_only_pred: Dict, gnn_pred: Dict) -> Dict:
        """Analyze bounding box alignment between predictions"""
        cnn_blocks = cnn_only_pred.get('predictions', [])
        gnn_blocks = gnn_pred.get('blocks', []) or gnn_pred.get('predictions', [])
        
        if not cnn_blocks or not gnn_blocks:
            return {'alignment_score': 0, 'iou_scores': []}
        
        iou_matrix = self._calculate_iou_matrix(cnn_blocks, gnn_blocks)
        
        # Calculate alignment metrics
        best_ious = np.max(iou_matrix, axis=1) if iou_matrix.size > 0 else []
        mean_iou = np.mean(best_ious) if best_ious.size > 0 else 0
        
        return {
            'mean_iou': float(mean_iou),
            'best_match_count': np.sum(best_ious > 0.5),
            'alignment_quality': 'high' if mean_iou > 0.7 else ('medium' if mean_iou > 0.4 else 'low'),
            'iou_distribution': {
                'high_overlap': np.sum(best_ious > 0.7),
                'medium_overlap': np.sum((best_ious > 0.4) & (best_ious <= 0.7)),
                'low_overlap': np.sum(best_ious <= 0.4)
            }
        }
    
    def _extract_feature_differences(self, cnn_only_pred: Dict, gnn_pred: Dict) -> Dict:
        """Extract key differences between model features"""
        differences = {
            'cnn_only_has_graphs': False,
            'cnn_only_has_connectors': False,
            'gnn_has_graph_structure': True,
            'cnn_features': cnn_only_pred.get('features', {}),
            'cnn_only_architecture': cnn_only_pred.get('architecture', 'N/A'),
            'analysis_focus': {
                'cnn_only': 'Spatial features, geometric properties, CNN receptive fields',
                'gnn': 'Document structure, graph relationships, connector analysis, hierarchy'
            }
        }
        
        return differences
    
    def _calculate_agreement(self, cnn_blocks: List, gnn_blocks: List) -> float:
        """Calculate overall agreement between predictions"""
        if not cnn_blocks and not gnn_blocks:
            return 1.0
        if not cnn_blocks or not gnn_blocks:
            return 0.0
        
        # Simple agreement based on count similarity
        count_diff = abs(len(cnn_blocks) - len(gnn_blocks))
        max_count = max(len(cnn_blocks), len(gnn_blocks))
        
        agreement = 1.0 - (count_diff / max_count)
        return float(max(0, agreement))
    
    def _calculate_coverage(self, blocks: List) -> float:
        """Calculate spatial coverage percentage"""
        if not blocks:
            return 0.0
        
        # Estimate total area covered
        total_area = 0
        for block in blocks:
            if 'area' in block:
                total_area += block['area']
            elif 'bbox' in block:
                bbox = block['bbox']
                total_area += (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        
        # Assume 1000x1000 typical page size
        coverage = total_area / 1_000_000.0
        return min(float(coverage), 1.0)
    
    def _calculate_type_agreement(self, cnn_types: Dict, gnn_types: Dict) -> float:
        """Calculate agreement in type distributions"""
        all_types = set(cnn_types.keys()) | set(gnn_types.keys())
        
        if not all_types:
            return 1.0
        
        # Calculate KL divergence approximation
        total_diff = 0
        for t in all_types:
            cnn_pct = cnn_types.get(t, 0)
            gnn_pct = gnn_types.get(t, 0)
            total_diff += abs(cnn_pct - gnn_pct)
        
        agreement = 1.0 - (total_diff / 2.0)
        return float(max(0, min(1, agreement)))
    
    def _calculate_iou_matrix(self, cnn_blocks: List, gnn_blocks: List) -> np.ndarray:
        """Calculate Intersection over Union matrix between bounding boxes"""
        if not cnn_blocks or not gnn_blocks:
            return np.array([])
        
        iou_matrix = np.zeros((len(cnn_blocks), len(gnn_blocks)))
        
        for i, cnn_block in enumerate(cnn_blocks):
            if 'bbox' not in cnn_block:
                continue
            
            cnn_bbox = cnn_block['bbox']
            
            for j, gnn_block in enumerate(gnn_blocks):
                if 'bbox' not in gnn_block:
                    continue
                
                gnn_bbox = gnn_block['bbox']
                iou = self._calculate_iou(cnn_bbox, gnn_bbox)
                iou_matrix[i, j] = iou
        
        return iou_matrix
    
    def _calculate_iou(self, bbox1: List, bbox2: List) -> float:
        """Calculate IoU between two bounding boxes"""
        x1_min, y1_min, x1_max, y1_max = bbox1
        x2_min, y2_min, x2_max, y2_max = bbox2
        
        # Intersection
        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)
        
        if inter_x_max <= inter_x_min or inter_y_max <= inter_y_min:
            return 0.0
        
        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
        
        # Union
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = area1 + area2 - inter_area
        
        if union_area == 0:
            return 0.0
        
        iou = inter_area / union_area
        return float(iou)
    
    def _calculate_correlation(self, list1: List, list2: List) -> float:
        """Calculate Pearson correlation between two lists"""
        if len(list1) < 2 or len(list2) < 2:
            return 0.0
        
        # Pad shorter list
        max_len = max(len(list1), len(list2))
        list1_padded = list1 + [np.mean(list1)] * (max_len - len(list1))
        list2_padded = list2 + [np.mean(list2)] * (max_len - len(list2))
        
        correlation = np.corrcoef(list1_padded, list2_padded)[0, 1]
        return float(correlation) if not np.isnan(correlation) else 0.0


class PerformanceAnalyzer:
    """
    Analyze and report performance differences between models
    """
    
    def __init__(self):
        """Initialize analyzer"""
        self.comparator = ModelComparator()
    
    def generate_report(self, cnn_only_analysis: Dict, hybrid_analysis: Dict) -> Dict:
        """
        Generate comprehensive comparison report
        
        Args:
            cnn_only_analysis: CNN-only model full analysis
            hybrid_analysis: CNN+GNN hybrid model analysis
        
        Returns:
            Comprehensive comparison report
        """
        cnn_pred = cnn_only_analysis.get('layout_analysis', {})
        gnn_pred = hybrid_analysis.get('layout', hybrid_analysis)
        
        comparison = self.comparator.compare_predictions(cnn_pred, gnn_pred)
        
        report = {
            'summary': self._generate_summary(comparison),
            'detailed_comparison': comparison,
            'recommendations': self._generate_recommendations(comparison),
            'use_cases': self._generate_use_cases(comparison)
        }
        
        return report
    
    def _generate_summary(self, comparison: Dict) -> Dict:
        """Generate summary findings"""
        overall = comparison.get('overall', {})
        spatial = comparison.get('spatial_analysis', {})
        alignment = comparison.get('alignment', {})
        
        summary = {
            'block_detection_difference': overall.get('block_count_difference', 0),
            'spatial_coverage_agreement': 1.0 - abs(
                spatial.get('cnn_only_coverage', 0) - spatial.get('gnn_coverage', 0)
            ),
            'bounding_box_alignment': alignment.get('mean_iou', 0),
            'overall_model_agreement': overall.get('model_agreement', 0),
            'key_finding': self._determine_key_finding(comparison)
        }
        
        return summary
    
    def _generate_recommendations(self, comparison: Dict) -> List[str]:
        """Generate usage recommendations based on comparison"""
        alignment = comparison.get('alignment', {}).get('alignment_quality', 'low')
        cnn_count = comparison.get('overall', {}).get('cnn_only_block_count', 0)
        gnn_count = comparison.get('overall', {}).get('gnn_block_count', 0)
        
        recommendations = []
        
        if alignment == 'high':
            recommendations.append("Models show strong agreement - either can be used")
        elif alignment == 'medium':
            recommendations.append("Models show moderate agreement - verify results on validation set")
        else:
            recommendations.append("Models show significant differences - use CNN+GNN for complex documents")
        
        if abs(cnn_count - gnn_count) > 5:
            recommendations.append("CNN+GNN detects more structural elements - consider for comprehensive analysis")
        
        recommendations.append("Use CNN-only for faster inference on simple documents")
        recommendations.append("Use CNN+GNN for documents with complex structure and relationships")
        
        return recommendations
    
    def _generate_use_cases(self, comparison: Dict) -> Dict:
        """Generate recommended use cases for each model"""
        return {
            'cnn_only': {
                'description': 'Pure CNN feature extraction without graph analysis',
                'best_for': [
                    'Simple document layout analysis',
                    'Fast inference requirements',
                    'Memory-constrained environments',
                    'Baseline performance comparison',
                    'Visual element detection only'
                ],
                'characteristics': [
                    'Faster processing',
                    'Lower memory footprint',
                    'Direct CNN predictions',
                    'No graph relationship analysis'
                ]
            },
            'cnn_gnn_hybrid': {
                'description': 'CNN+GNN for comprehensive document understanding',
                'best_for': [
                    'Complex document structure analysis',
                    'Flowchart and diagram understanding',
                    'Multi-level document hierarchies',
                    'Connector and relationship detection',
                    'Document section ordering'
                ],
                'characteristics': [
                    'Graph-based reasoning',
                    'Relationship detection',
                    'Hierarchical structure understanding',
                    'Connector and flow analysis',
                    'More comprehensive features'
                ]
            }
        }
    
    def _determine_key_finding(self, comparison: Dict) -> str:
        """Determine main finding from comparison"""
        agreement = comparison.get('overall', {}).get('model_agreement', 0)
        
        if agreement > 0.9:
            return "Models are highly aligned - similar performance expected"
        elif agreement > 0.7:
            return "Models show good agreement on block detection"
        elif agreement > 0.5:
            return "Models detect different numbers of blocks - GNN adds structural analysis"
        else:
            return "Significant model differences - GNN provides enhanced structure detection"


# Export main classes
__all__ = ['ModelComparator', 'PerformanceAnalyzer']
