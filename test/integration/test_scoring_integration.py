#!/usr/bin/env python3
"""
Integration test for image quality scoring and ranking.

This test evaluates and ranks all converted dithered images based on 
quality metrics, providing insights into which images convert best.
"""

import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

import scoring


def test_image_scoring_integration():
    """Test the complete image scoring and ranking system"""
    
    print("🎯 ePaper Image Quality Scoring Test")
    print("=" * 60)
    
    # Get rankings for all dithered images
    rankings = scoring.rank_dithering_outputs()
    
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
        if 'color_diversity' in scores:
            breakdown.append(f"Diversity: {scores['color_diversity']}")
        if 'color_balance' in scores:
            breakdown.append(f"Balance: {scores['color_balance']}")
        if 'contrast' in scores:
            breakdown.append(f"Contrast: {scores['contrast']}")
        if 'detail_preservation' in scores:
            breakdown.append(f"Detail: {scores['detail_preservation']}")
            
        if breakdown:
            print(f"   📋 Breakdown: {', '.join(breakdown)}")
            
        # Add quality assessment
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