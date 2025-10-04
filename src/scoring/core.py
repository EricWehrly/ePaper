"""
Core scoring orchestration for ePaper image quality.
"""

import logging
from pathlib import Path
from typing import List, Dict, Tuple
from .skin import calculate_skin_tone_score
from .structure import calculate_structural_similarity
from .color import calculate_color_fidelity_score
from .edges import calculate_edge_preservation_score
from .utils import find_original_image
from .cache import ScoringCache

logger = logging.getLogger(__name__)


class ImageQualityScorer:
    def __init__(self):
        self._cache = ScoringCache()

    def score_converted_image(self, image_path: Path) -> Dict[str, float]:
        """Calculate comprehensive quality score by comparing converted image to original."""
        if not image_path.exists():
            return {
                'total_score': 999,
                'error': 'File not found'
            }
        
        # Find the original image
        original_path = find_original_image(image_path)
        if not original_path:
            logger.warning(f"No original image found for {image_path.name}")
            return {
                'total_score': 999,
                'error': 'Original image not found'
            }

        # Check for cached scores first
        cached_scores = self._cache.get_cached_score(image_path, original_path)
        if cached_scores:
            return cached_scores
        
        # Calculate comparative scores
        structural_score = calculate_structural_similarity(original_path, image_path)
        color_fidelity_score = calculate_color_fidelity_score(original_path, image_path)
        edge_preservation_score = calculate_edge_preservation_score(original_path, image_path)
        
        # Calculate skin tone specific scores
        skin_scores = calculate_skin_tone_score(original_path, image_path)
        
        # Weighted total score (golf scoring - lower is better)
        total_score = (
            structural_score * 0.4 +      # Overall structural similarity is key
            color_fidelity_score * 0.3 +  # Color preservation important  
            edge_preservation_score * 0.3  # Edge/detail preservation matters
        )

        result = {
            'total_score': round(total_score, 2),
            'structural_similarity': round(structural_score, 2),
            'color_fidelity': round(color_fidelity_score, 2),
            'edge_preservation': round(edge_preservation_score, 2),
            'skin_tone_score': skin_scores['skin_tone_score'],
            'skin_coverage_percent': skin_scores['skin_coverage_percent'],
            'weighted_skin_score': skin_scores['weighted_skin_score'],
            'original_image': str(original_path.name)
        }

        # Store result in cache for future use
        self._cache.store_score(image_path, original_path, result)

        return result


    def rank_images(self, image_paths: List[Path]) -> List[Tuple[Path, Dict[str, float]]]:
        """Score and rank multiple images."""
        scored_images = []
        
        for image_path in image_paths:
            scores = self.score_converted_image(image_path)
            scored_images.append((image_path, scores))
        
        # Sort by total score (lower is better)
        scored_images.sort(key=lambda x: x[1].get('total_score', 999))
        
        return scored_images


def sort_images_by_quality(image_paths: List[Path]) -> List[Path]:
    """Sort images by quality score (best first)"""
    if not image_paths:
        return []
        
    logger.info("Scoring images for optimal display order...")
    
    try:
        scorer = ImageQualityScorer()
        scored_images = []
        
        for image_path in image_paths:
            scores = scorer.score_converted_image(image_path)
            total_score = scores.get('total_score', 999)
            scored_images.append((image_path, total_score))
            
        # Sort by score (lower is better - golf scoring)
        scored_images.sort(key=lambda x: x[1])
        
        # Extract just the paths in sorted order
        sorted_paths = [path for path, score in scored_images]
        
        logger.info(f"Images sorted by quality - best: {sorted_paths[0].name} ({scored_images[0][1]:.1f}), worst: {sorted_paths[-1].name} ({scored_images[-1][1]:.1f})")
        
        return sorted_paths
        
    except Exception as e:
        logger.error(f"Error scoring images: {e}")
        logger.info("Falling back to original order")
        return image_paths


def rank_dithering_outputs() -> List[Tuple[Path, Dict[str, float]]]:
    """Rank all dithered images in the test outputs directory."""
    # Find dithering comparison directory
    project_root = Path(__file__).parent.parent.parent
    comparison_dir = project_root / 'test' / 'outputs' / 'dithering_comparison'
    
    if not comparison_dir.exists():
        logger.warning(f"Comparison directory not found: {comparison_dir}")
        return []
    
    # Find all dithered BMP files
    dithered_files = list(comparison_dir.glob('*_dithered.bmp'))
    
    if not dithered_files:
        logger.warning("No dithered BMP files found in comparison directory")
        return []
    
    # Score and rank images
    scorer = ImageQualityScorer()
    rankings = scorer.rank_images(dithered_files)
    
    return rankings
