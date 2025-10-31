"""
Comprehensive optimization testing.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from test.test_conversion_performance import ConversionPerformanceTester
from test.optimized_conversion import (
    convert_image_to_6color_dithered_optimized,
    convert_image_to_6color_dithered_ultra_optimized,
    convert_image_to_6color_dithered_extreme_optimized
)


def main():
    """Test all optimization levels."""
    tester = ConversionPerformanceTester()
    
    # Load baseline
    tester.establish_baseline()
    
    optimization_levels = [
        ("Vectorized Output", convert_image_to_6color_dithered_optimized),
        ("Optimized Dithering", convert_image_to_6color_dithered_ultra_optimized),
        ("Extreme Manual", convert_image_to_6color_dithered_extreme_optimized),
    ]
    
    all_results = {}
    
    for name, func in optimization_levels:
        print(f"\n{'='*60}")
        print(f"🚀 TESTING: {name}")
        print('='*60)
        
        results = tester.test_optimized_version(func)
        all_results[name] = results
        tester.print_summary(results)
    
    # Final comparison
    print(f"\n{'='*60}")
    print("🏆 FINAL OPTIMIZATION COMPARISON")
    print('='*60)
    
    baseline_time = tester.baseline_times['test_image.png']['avg_time']
    
    print(f"Baseline time: {baseline_time:.3f}s")
    
    for name, results in all_results.items():
        if 'test_image.png' in results:
            result = results['test_image.png']
            time = result['optimized_time']
            speedup = result['speedup']
            quality = "✅" if result['quality_match'] else "❌"
            
            print(f"{quality} {name}: {time:.3f}s ({speedup:.2f}x speedup)")


if __name__ == "__main__":
    main()