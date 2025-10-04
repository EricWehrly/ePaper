"""
ePaper Image Quality Scoring Package

Provides modular scoring for converted e-paper images with specialized
analysis for skin tones, structural similarity, color fidelity, and edge preservation.
"""

from .core import ImageQualityScorer, rank_dithering_outputs, sort_images_by_quality

__all__ = ['ImageQualityScorer', 'rank_dithering_outputs', 'sort_images_by_quality']