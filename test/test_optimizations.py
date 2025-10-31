"""
Test runner for conversion optimizations.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from test.test_conversion_performance import ConversionPerformanceTester
from test.optimized_conversion import (
    convert_image_to_6color_dithered_optimized,
    convert_image_to_6color_dithered_ultra_optimized
)


def main():
    """Test both optimized versions against baseline."""
    tester = ConversionPerformanceTester()
    
    # Load baseline if it exists
    if not Path("test/outputs/baseline").exists():
        print("❌ No baseline found. Run test_conversion_performance.py first.")
        return
    
    # Load baseline data
    tester.establish_baseline()
    
    print("\n" + "="*60)
    print("🚀 TESTING OPTIMIZED VERSION 1")
    print("="*60)
    
    results_v1 = tester.test_optimized_version(convert_image_to_6color_dithered_optimized)
    tester.print_summary(results_v1)
    
    print("\n" + "="*60)
    print("🚀 TESTING ULTRA-OPTIMIZED VERSION 2") 
    print("="*60)
    
    results_v2 = tester.test_optimized_version(convert_image_to_6color_dithered_ultra_optimized)
    tester.print_summary(results_v2)
    
    # Compare both optimized versions
    print("\n" + "="*60)
    print("⚖️  OPTIMIZATION COMPARISON")
    print("="*60)
    
    if results_v1 and results_v2:
        for img_name in results_v1.keys():
            if img_name in results_v2:
                v1_time = results_v1[img_name]['optimized_time']
                v2_time = results_v2[img_name]['optimized_time']
                v1_speedup = results_v1[img_name]['speedup']
                v2_speedup = results_v2[img_name]['speedup']
                
                print(f"{img_name}:")
                print(f"  Version 1: {v1_speedup:.2f}x speedup ({v1_time:.3f}s)")
                print(f"  Version 2: {v2_speedup:.2f}x speedup ({v2_time:.3f}s)")
                
                if v2_time < v1_time:
                    improvement = v1_time / v2_time
                    print(f"  → Version 2 is {improvement:.2f}x faster than Version 1")
                else:
                    degradation = v2_time / v1_time
                    print(f"  → Version 1 is {degradation:.2f}x faster than Version 2")


if __name__ == "__main__":
    main()