#!/usr/bin/env python3
"""
Integration test for image quality scoring and ranking.

This test evaluates and ranks all converted dithered images based on 
quality metrics, providing insights into which images convert best.

To use, run from the project root:
    cd /home/eric/Projects/ePaper
    python test/integration/test_scoring_integration.py

The test will:
1. Score all dithered images in test/outputs/dithering_comparison/
2. Compare them against their originals in pic-raw/
3. Provide both general quality scores and specialized skin tone analysis
4. Rank images from best to worst conversion quality
5. Save detailed logs to test/outputs/scoring_results.log
"""

import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.scoring import rank_dithering_outputs


def test_image_scoring_integration():
    """Test the complete image scoring and ranking system"""
    
    print("🎯 ePaper Image Quality Scoring Test")
    print("=" * 60)
    
    # Get rankings for all dithered images
    rankings = rank_dithering_outputs()
    
    if not rankings:
        print("❌ No dithered images found to score")
        return False
    
    print(f"📊 Scoring {len(rankings)} dithered images...\n")
    
    # Log detailed results
    logger = logging.getLogger(__name__)
    
    for i, (image_path, scores) in enumerate(rankings, 1):
        # Log the scores (as requested)
        logger.info(f"Rank #{i}: {image_path.name} - Score: {scores.get('total_score', 'N/A')}")
        
        # Also print for human readability
        print(f"🏅 Rank #{i}: {image_path.name}")
        print(f"   📈 Total Score: {scores.get('total_score', 'N/A')} (lower is better)")
        
        # Show score breakdown
        breakdown = []
        if 'structural_similarity' in scores:
            breakdown.append(f"Structural: {scores['structural_similarity']}")
        if 'color_fidelity' in scores:
            breakdown.append(f"Color: {scores['color_fidelity']}")
        if 'edge_preservation' in scores:
            breakdown.append(f"Edges: {scores['edge_preservation']}")
            
        if breakdown:
            print(f"   📋 Breakdown: {', '.join(breakdown)}")
            
        # Show skin tone analysis
        if 'skin_coverage_percent' in scores and scores['skin_coverage_percent'] > 0:
            print(f"   👤 Skin Tone Analysis:")
            print(f"      Coverage: {scores['skin_coverage_percent']}% of image")
            print(f"      Skin Quality Score: {scores['skin_tone_score']}")
            print(f"      Weighted Skin Score: {scores['weighted_skin_score']}")
        else:
            print(f"   👤 Skin Tone Analysis: No skin tones detected")
            
        # Show skin tone specific scoring
        if 'skin_tone_score' in scores and 'skin_coverage' in scores:
            skin_score = scores['skin_tone_score']
            skin_coverage = scores['skin_coverage']
            if skin_coverage > 0:
                print(f"   � Skin Tones: Score {skin_score}, Coverage {skin_coverage}%")
            else:
                print("   👤 Skin Tones: None detected")        # Add quality assessment
        total_score = scores.get('total_score', 999)
        if total_score < 20:
            quality = "🌟 Excellent"
        elif total_score < 40:
            quality = "✅ Good"  
        elif total_score < 60:
            quality = "⚠️ Fair"
        else:
            quality = "❌ Poor"
            
        print(f"   🎯 Assessment: {quality}")
        print()
    
    # Summary statistics
    total_scores = [scores.get('total_score', 999) for _, scores in rankings]
    valid_scores = [s for s in total_scores if s < 999]
    
    if valid_scores:
        avg_score = sum(valid_scores) / len(valid_scores)
        best_score = min(valid_scores)
        worst_score = max(valid_scores)
        
        print("📈 Summary Statistics:")
        print(f"   Best Score: {best_score:.1f}")
        print(f"   Worst Score: {worst_score:.1f}")
        print(f"   Average Score: {avg_score:.1f}")
        
        # Identify the best and worst performers
        best_image = rankings[0][0].name
        worst_image = rankings[-1][0].name
        
        print(f"\n🏆 Best Performer: {best_image}")
        print(f"🔻 Worst Performer: {worst_image}")
        
        logger.info(f"Scoring complete - Best: {best_image} ({best_score:.1f}), "
                   f"Worst: {worst_image} ({worst_score:.1f}), Average: {avg_score:.1f}")
    
    return True


def main():
    """Run the scoring integration test"""
    # Set up logging to capture the requested logger.info() calls
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(project_root / 'test' / 'outputs' / 'scoring_results.log', mode='w')
        ]
    )
    
    try:
        success = test_image_scoring_integration()
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 Image scoring integration test completed successfully!")
            print(f"📝 Detailed logs saved to: test/outputs/scoring_results.log")
        else:
            print("\n❌ Image scoring test failed")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())