"""
Command-line interface for ph_coder_docstr.
"""

import sys
import argparse
from .config import Config
from .processor import DocumentationProcessor


def main():
    """Main entry point for the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Automatically add documentation to code files using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --project ./my_project
  %(prog)s --project /path/to/project
  %(prog)s --project ./my_project --clean-backups
  %(prog)s --project ./my_project --clean-backups --dry-run

Environment Variables:
  OPENAI_API_KEY      API key for OpenAI-compatible service (required)
  OPENAI_URL          Base URL for API (default: https://api.openai.com/v1)
  OPENAI_MODELS_LIST  Comma-separated list of models to use (default: gpt-4o-mini)
"""
    )
    
    parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="Path to the project directory to process"
    )
    
    parser.add_argument(
        "--clean-backups",
        action="store_true",
        help="Clean all backup files (*.backup) in the project"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting (use with --clean-backups)"
    )
    
    args = parser.parse_args()
    
    try:
        # Handle clean-backups mode
        if args.clean_backups:
            # For cleaning backups, we don't need API configuration
            processor = DocumentationProcessor(args.project)
            processor.clean_backups(dry_run=args.dry_run)
            sys.exit(0)
        
        # Normal processing mode - Load configuration
        print("Loading configuration...")
        config = Config()
        
        # Create processor
        processor = DocumentationProcessor(args.project, config)
        
        # Process the project
        processor.process_project()
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nPlease ensure you have set the required environment variables:")
        print("  OPENAI_API_KEY - Your API key")
        print("  OPENAI_URL - API base URL (optional)")
        print("  OPENAI_MODELS_LIST - Comma-separated model names (optional)")
        print("\nYou can also create a .env file in the current directory with these variables.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

