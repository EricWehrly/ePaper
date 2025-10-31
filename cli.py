#!/usr/bin/env python3
"""
ePaper CLI Entry Point

Unified command-line interface for all ePaper functionality.
Replaces scattered __main__ blocks throughout the codebase.

Usage:
    python cli.py main [args]           # Main application (same as src/main.py)
    python cli.py convert <input>       # Convert single image
    python cli.py test-display          # Test display hardware  
    python cli.py test-filesystem       # Test filesystem operations
    python cli.py test-scoring          # Run scoring integration test
    python cli.py test-convert          # Run conversion integration test
    python cli.py setup-paths          # Show path setup info
"""

import sys
import logging
import argparse
from pathlib import Path

# Setup project paths for all commands
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.path_utils import setup_project_paths
setup_project_paths()


def setup_logging(level=logging.INFO, debug=False):
    """Standardized logging setup for all CLI commands."""
    if debug:
        level = logging.DEBUG
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def cmd_main(args):
    """Run main application (same as src/main.py)"""
    # Import and run the main application
    from src.main import main
    
    # Replace sys.argv so main() sees the right arguments
    original_argv = sys.argv
    try:
        # Get main args - these should NOT include the 'main' subcommand itself
        main_args = getattr(args, 'main_args', [])
        
        # Remove the '--' separator if present (added by argparse.REMAINDER)
        if main_args and main_args[0] == '--':
            main_args = main_args[1:]
        
        # Set sys.argv to just the script name + the arguments (no 'main' subcommand)
        sys.argv = ['main.py'] + main_args
        return main()
    finally:
        sys.argv = original_argv


def cmd_convert(args):
    """Convert single image using conversion module"""
    from src import convert
    
    if not args.input:
        print("Error: input image required")
        return 1
    
    input_file = Path(args.input)
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return 1
    
    output_dir = Path(args.output) if args.output else Path("comparison_output")
    output_dir.mkdir(exist_ok=True)
    
    # Run conversion comparison
    try:
        from src.convert.core import convert_image_to_6color_dithered
        
        output_path = output_dir / f"{input_file.stem}.bmp"
        success = convert_image_to_6color_dithered(input_file, output_path)
        
        if success:
            print(f"✅ Converted: {input_file} -> {output_path}")
            return 0
        else:
            print(f"❌ Conversion failed: {input_file}")
            return 1
            
    except Exception as e:
        print(f"❌ Conversion error: {e}")
        return 1


def cmd_test_display(args):
    """Test display functionality"""
    from src.display.manager import DisplayManager
    
    try:
        display = DisplayManager()
        display.initialize()
        
        info = display.get_display_info()
        print(f"✅ Display info: {info}")
        
        if args.test_image:
            print(f"Testing with image: {args.test_image}")
            display.show_image(args.test_image)
        
        display.cleanup()
        return 0
        
    except Exception as e:
        print(f"❌ Display test failed: {e}")
        return 1


def cmd_test_filesystem(args):
    """Test filesystem operations"""
    from src import filesystem
    
    test_dir = Path("test_fs")
    try:
        filesystem.ensure_directory(test_dir)
        
        test_files = filesystem.scan_directory(test_dir, {'.txt', '.py'})
        print(f"✅ Found {len(test_files)} files in {test_dir}")
        
        # Cleanup
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
            print(f"✅ Cleaned up {test_dir}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Filesystem test failed: {e}")
        return 1


def cmd_test_scoring(args):
    """Run scoring integration test"""
    try:
        from src.scoring import rank_dithering_outputs
        
        output_dir = Path("test/outputs/dithering_comparison")
        if not output_dir.exists():
            print(f"❌ Test output directory not found: {output_dir}")
            return 1
        
        # Run scoring test
        results = rank_dithering_outputs(output_dir)
        
        if results:
            print(f"✅ Scored {len(results)} images")
            return 0
        else:
            print("❌ No scoring results")
            return 1
            
    except Exception as e:
        print(f"❌ Scoring test failed: {e}")
        return 1


def cmd_test_convert(args):
    """Run conversion integration test"""
    try:
        from src import convert
        from PIL import Image
        
        # Create test image if needed
        test_dir = Path("test/resources")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        test_image = test_dir / "test_image.png"
        if not test_image.exists():
            # Create simple test image
            img = Image.new('RGB', (400, 300), color='blue')
            img.save(test_image)
            print(f"Created test image: {test_image}")
        
        # Test conversion
        output_dir = Path("test/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        from src.convert.core import convert_image_to_6color_dithered
        output_path = output_dir / "test_conversion.bmp"
        
        success = convert_image_to_6color_dithered(test_image, output_path)
        
        if success and output_path.exists():
            print(f"✅ Conversion test passed: {output_path}")
            return 0
        else:
            print("❌ Conversion test failed")
            return 1
            
    except Exception as e:
        print(f"❌ Conversion test failed: {e}")
        return 1


def cmd_setup_paths(args):
    """Show path setup information"""
    from src.path_utils import get_project_root, get_lib_path
    
    print("📁 Project path information:")
    print(f"  Project root: {get_project_root()}")
    print(f"  Lib directory: {get_lib_path()}")
    print(f"  Current working directory: {Path.cwd()}")
    
    print(f"\n🐍 Python path entries:")
    for i, path in enumerate(sys.path[:10]):  # Show first 10 entries
        print(f"  {i}: {path}")
    
    return 0


def main():
    """Main CLI entry point"""
    
    # Check if we're being called with main app arguments directly (Docker compatibility)
    # Only trigger if the FIRST argument starts with -- (not a subcommand)
    main_app_args = ['--mode', '--host', '--port', '--ssl', '--help', '-h']
    if len(sys.argv) > 1 and sys.argv[1].startswith(tuple(main_app_args)):
        # Called with main app arguments directly - forward to main app
        class MainArgs:
            command = 'main'
            main_args = sys.argv[1:]  # All arguments after script name
            debug = '--debug' in sys.argv
        
        setup_logging(debug=getattr(MainArgs(), 'debug', False))
        return cmd_main(MainArgs())
    
    parser = argparse.ArgumentParser(description='ePaper CLI - Unified interface for all functionality')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Main application
    main_parser = subparsers.add_parser('main', help='Run main application')
    main_parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    main_parser.add_argument('main_args', nargs=argparse.REMAINDER, help='Arguments for main application')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert single image')
    convert_parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    convert_parser.add_argument('input', help='Input image path')
    convert_parser.add_argument('-o', '--output', help='Output directory (default: comparison_output)')
    
    # Test commands
    test_display_parser = subparsers.add_parser('test-display', help='Test display hardware')
    test_display_parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    test_display_parser.add_argument('--test-image', help='Test with specific image')
    
    test_fs_parser = subparsers.add_parser('test-filesystem', help='Test filesystem operations')
    test_fs_parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    test_scoring_parser = subparsers.add_parser('test-scoring', help='Run scoring integration test')
    test_scoring_parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    test_convert_parser = subparsers.add_parser('test-convert', help='Run conversion integration test')
    test_convert_parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    setup_paths_parser = subparsers.add_parser('setup-paths', help='Show path setup information')
    setup_paths_parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Setup logging
    setup_logging(debug=getattr(args, 'debug', False))
    
    # Route to appropriate command
    commands = {
        'main': cmd_main,
        'convert': cmd_convert,
        'test-display': cmd_test_display,
        'test-filesystem': cmd_test_filesystem,
        'test-scoring': cmd_test_scoring,
        'test-convert': cmd_test_convert,
        'setup-paths': cmd_setup_paths,
    }
    
    if args.command in commands:
        return commands[args.command](args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())