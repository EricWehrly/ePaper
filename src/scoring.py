"""
Image Quality Scoring Module

Evaluates the quality of converted e-paper images by comparing them to their originals
and ranking them based on how well the conversion preserves the original image quality.
"""

import logging
import numpy as np
from PIL import Image, ImageStat, ImageFilter
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import math

logger = logging.getLogger(__name__)


class ImageQualityScorer:
    """
    Scorer for evaluating e-paper image conversion quality by comparing to originals.
    
    Lower scores are better (golf scoring system).
    """
    
    def __init__(self):
        self.palette_6color = np.array([
            [0, 0, 0],        # BLACK
            [255, 255, 255],  # WHITE  
            [255, 243, 56],   # YELLOW
            [191, 0, 0],      # RED
            [100, 64, 255],   # BLUE
            [67, 138, 28],    # GREEN
        ], dtype=np.float32)
        
    def find_original_image(self, converted_path: Path) -> Optional[Path]:
        """
        Find the original image that corresponds to a converted BMP file.
        
        Args:
            converted_path: Path to converted BMP file
            
        Returns:
            Path to original image or None if not found
        """
        # Extract base name (remove _dithered.bmp suffix)
        base_name = converted_path.stem.replace('_dithered', '').replace('_simple', '')
        
        # Look in pic-raw directory for PNG or JPG versions
        # Handle different directory structures
        if 'test' in str(converted_path):
            # Test output directory - go up to project root
            # test/outputs/dithering_comparison -> go up 3 levels to project root
            pic_raw_dir = converted_path.parent.parent.parent.parent / 'pic-raw'
        else:
            # Regular pic directory - go up one level then to pic-raw
            pic_raw_dir = converted_path.parent.parent / 'pic-raw'
        
        for ext in ['.png', '.jpg', '.jpeg']:
            original_path = pic_raw_dir / f"{base_name}{ext}"
            if original_path.exists():
                return original_path
                
        return None
        
    def calculate_structural_similarity(self, original_path: Path, converted_path: Path) -> float:
        """
        Calculate structural similarity between original and converted images.
        
        Args:
            original_path: Path to original image
            converted_path: Path to converted image
            
        Returns:
            float: Penalty score (lower = more similar)
        """
        try:
            with Image.open(original_path) as orig, Image.open(converted_path) as conv:
                # Resize original to match converted (400x600)
                orig_resized = orig.resize((400, 600), Image.Resampling.LANCZOS)
                
                # Convert both to grayscale for structural comparison
                orig_gray = np.array(orig_resized.convert('L'), dtype=np.float32)
                conv_gray = np.array(conv.convert('L'), dtype=np.float32)
                
                # Calculate mean squared error
                mse = np.mean((orig_gray - conv_gray) ** 2)
                
                # Convert MSE to penalty score (0-100 scale)
                # MSE of 0 = perfect match, MSE of 10000+ = very different
                penalty = min(mse / 100, 100)
                
                return penalty
                
        except Exception as e:
            logger.error(f"Error calculating structural similarity: {e}")
            return 100
            
    def calculate_color_fidelity_score(self, original_path: Path, converted_path: Path) -> float:
        """
        Score how well the converted image preserves the original's color characteristics.
        
        Args:
            original_path: Path to original image  
            converted_path: Path to converted image
            
        Returns:
            float: Penalty score for poor color preservation
        """
        try:
            with Image.open(original_path) as orig, Image.open(converted_path) as conv:
                # Resize original to match converted
                orig_resized = orig.resize((400, 600), Image.Resampling.LANCZOS)
                
                # Get color statistics
                orig_stat = ImageStat.Stat(orig_resized)
                conv_stat = ImageStat.Stat(conv)
                
                # Compare mean brightness across RGB channels
                orig_means = orig_stat.mean[:3] if len(orig_stat.mean) >= 3 else orig_stat.mean
                conv_means = conv_stat.mean[:3] if len(conv_stat.mean) >= 3 else conv_stat.mean
                
                # Calculate difference in mean values
                mean_diff = sum(abs(o - c) for o, c in zip(orig_means, conv_means)) / len(orig_means)
                
                # Convert to penalty score (0-100 scale)
                penalty = min(mean_diff / 2.55, 100)  # Normalize to 0-100
                
                return penalty
                
        except Exception as e:
            logger.error(f"Error calculating color fidelity: {e}")
            return 100
            
    def calculate_edge_preservation_score(self, original_path: Path, converted_path: Path) -> float:
        """
        Score how well edges and details are preserved in the conversion.
        
        Args:
            original_path: Path to original image
            converted_path: Path to converted image  
            
        Returns:
            float: Penalty score for poor edge preservation
        """
        try:
            with Image.open(original_path) as orig, Image.open(converted_path) as conv:
                # Resize original to match converted
                orig_resized = orig.resize((400, 600), Image.Resampling.LANCZOS)
                
                # Apply edge detection to both images
                orig_edges = orig_resized.convert('L').filter(ImageFilter.FIND_EDGES)
                conv_edges = conv.convert('L').filter(ImageFilter.FIND_EDGES)
                
                # Convert to numpy arrays
                orig_edge_array = np.array(orig_edges, dtype=np.float32)
                conv_edge_array = np.array(conv_edges, dtype=np.float32)
                
                # Calculate correlation between edge maps
                # Higher correlation = better edge preservation
                orig_flat = orig_edge_array.flatten()
                conv_flat = conv_edge_array.flatten()
                
                # Avoid division by zero
                if np.std(orig_flat) == 0 or np.std(conv_flat) == 0:
                    return 50  # Moderate penalty for flat images
                
                correlation = np.corrcoef(orig_flat, conv_flat)[0, 1]
                
                # Convert correlation to penalty (1.0 correlation = 0 penalty)
                penalty = (1.0 - max(correlation, 0)) * 100
                
                return penalty
                
        except Exception as e:
            logger.error(f"Error calculating edge preservation: {e}")
            return 100
        """
        return 100

    def score_converted_image(self, image_path: Path) -> Dict[str, float]:
        """
        try:
            with Image.open(image_path) as img:
                # Convert to numpy for analysis
                img_array = np.array(img)
                pixels = img_array.reshape(-1, 3)
                total_pixels = len(pixels)
                
                # Count usage of each palette color
                color_counts = {}
                for color in self.palette_6color:
                    color_tuple = tuple(color.astype(int))
                    count = np.sum(np.all(pixels == color, axis=1))
                    if count > 0:
                        color_counts[color_tuple] = count / total_pixels
                
                if not color_counts:
                    return 100  # No valid colors found
                
                # Calculate entropy of color distribution
                # Higher entropy = more balanced usage = better
                entropy = -sum(prob * math.log2(prob) for prob in color_counts.values())
                max_entropy = math.log2(len(color_counts))  # Perfect balance entropy
                
                # Convert to penalty score (lower entropy = higher penalty)
                if max_entropy > 0:
                    balance_score = (1 - entropy / max_entropy) * 30
                else:
                    balance_score = 30
                    
                return balance_score
                
        except Exception as e:
            logger.error(f"Error calculating color balance for {image_path}: {e}")
            return 100
    
    def calculate_contrast_score(self, image_path: Path) -> float:
        """
        Score based on image contrast and dynamic range.
        
        Args:
            image_path: Path to converted BMP image
            
        Returns:
            float: Penalty score for poor contrast
        """
        try:
            with Image.open(image_path) as img:
                # Convert to grayscale for contrast analysis
                gray_img = img.convert('L')
                
                # Calculate image statistics
                stat = ImageStat.Stat(gray_img)
                
                # Standard deviation indicates contrast level
                contrast = stat.stddev[0]
                
                # Penalty for low contrast (flat, boring images)
                if contrast < 30:
                    contrast_penalty = (30 - contrast) * 2
                elif contrast < 50:
                    contrast_penalty = (50 - contrast) * 0.5
                else:
                    contrast_penalty = 0
                    
                # Additional penalty for extreme values (blown out or too dark)
                mean_brightness = stat.mean[0]
                if mean_brightness < 50 or mean_brightness > 200:
                    contrast_penalty += 20
                    
                return contrast_penalty
                
        except Exception as e:
            logger.error(f"Error calculating contrast for {image_path}: {e}")
            return 100
    
    def calculate_detail_preservation_score(self, image_path: Path) -> float:
        """
        Score based on apparent detail preservation and edge definition.
        
        Args:
            image_path: Path to converted BMP image
            
        Returns:
            float: Penalty score for poor detail preservation
        """
        try:
            with Image.open(image_path) as img:
                # Convert to grayscale for edge detection
                gray_img = img.convert('L')
                img_array = np.array(gray_img, dtype=np.float32)
                
                # Simple edge detection using gradients
                grad_x = np.abs(np.diff(img_array, axis=1))
                grad_y = np.abs(np.diff(img_array, axis=0))
                
                # Calculate edge strength
                edge_strength = np.mean(grad_x) + np.mean(grad_y)
                
                # Score based on edge preservation
                # Too low = lost detail, too high = artifacts
                optimal_edge_strength = 15  # Experimentally determined
                detail_penalty = abs(edge_strength - optimal_edge_strength)
                
                # Additional penalty for very smooth images (likely over-simplified)
                if edge_strength < 5:
                    detail_penalty += 30
                    
                return detail_penalty
                
        except Exception as e:
            logger.error(f"Error calculating detail preservation for {image_path}: {e}")
            return 100
    
    def score_converted_image(self, image_path: Path) -> Dict[str, float]:
        """
        Calculate comprehensive quality score by comparing converted image to original.
        
        Args:
            image_path: Path to converted BMP image
            
        Returns:
            dict: Breakdown of scoring components and total score
        """
        if not image_path.exists():
            return {
                'total_score': 999,
                'error': 'File not found'
            }
        
        # Find the original image
        original_path = self.find_original_image(image_path)
        if not original_path:
            logger.warning(f"No original image found for {image_path.name}")
            return {
                'total_score': 999,
                'error': 'Original image not found'
            }
        
        # Calculate comparative scores
        structural_score = self.calculate_structural_similarity(original_path, image_path)
        color_fidelity_score = self.calculate_color_fidelity_score(original_path, image_path)
        edge_preservation_score = self.calculate_edge_preservation_score(original_path, image_path)
        
        # Weighted total score (golf scoring - lower is better)
        total_score = (
            structural_score * 0.4 +      # Overall structural similarity is key
            color_fidelity_score * 0.3 +  # Color preservation important  
            edge_preservation_score * 0.3  # Edge/detail preservation matters
        )
        
        return {
            'total_score': round(total_score, 2),
            'structural_similarity': round(structural_score, 2),
            'color_fidelity': round(color_fidelity_score, 2),
            'edge_preservation': round(edge_preservation_score, 2),
            'original_image': str(original_path.name)
        }
    
    def rank_images(self, image_paths: List[Path]) -> List[Tuple[Path, Dict[str, float]]]:
        """
        Score and rank multiple images.
        
        Args:
            image_paths: List of paths to converted BMP images
            
        Returns:
            List of (path, scores) tuples sorted by quality (best first)
        """
        scored_images = []
        
        for image_path in image_paths:
            scores = self.score_converted_image(image_path)
            scored_images.append((image_path, scores))
        
        # Sort by total score (lower is better)
        scored_images.sort(key=lambda x: x[1].get('total_score', 999))
        
        return scored_images


def rank_dithering_outputs() -> List[Tuple[Path, Dict[str, float]]]:
    """
    Rank all dithered images in the test outputs directory.
    
    Returns:
        List of ranked images with their scores
    """
    # Find dithering comparison directory
    project_root = Path(__file__).parent.parent
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


if __name__ == "__main__":
    """Test the scoring system directly"""
    import sys
    
    if len(sys.argv) > 1:
        # Score specific image
        image_path = Path(sys.argv[1])
        scorer = ImageQualityScorer()
        scores = scorer.score_converted_image(image_path)
        
        print(f"Quality scores for {image_path.name}:")
        print(f"  Total Score: {scores.get('total_score', 'N/A')}")
        print(f"  Color Diversity: {scores.get('color_diversity', 'N/A')}")
        print(f"  Color Balance: {scores.get('color_balance', 'N/A')}")
        print(f"  Contrast: {scores.get('contrast', 'N/A')}")
        print(f"  Detail Preservation: {scores.get('detail_preservation', 'N/A')}")
    else:
        # Rank all dithered outputs
        rankings = rank_dithering_outputs()
        
        if rankings:
            print("🏆 Image Quality Rankings (Best to Worst):")
            print("=" * 60)
            
            for i, (image_path, scores) in enumerate(rankings, 1):
                print(f"{i}. {image_path.name}")
                print(f"   Total Score: {scores.get('total_score', 'N/A')}")
                print(f"   Breakdown: Diversity={scores.get('color_diversity', 'N/A')}, "
                      f"Balance={scores.get('color_balance', 'N/A')}, "
                      f"Contrast={scores.get('contrast', 'N/A')}, "
                      f"Detail={scores.get('detail_preservation', 'N/A')}")
                print()
        else:
            print("No images found to rank")
            sys.exit(1)