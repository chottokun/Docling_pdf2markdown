import argparse
from pathlib import Path
import sys
import logging

from .extraction import extract_markdown
from .refinement import refine_markdown

# Configure logging for the CLI tool
logger = logging.getLogger(__name__)

def main(args=None):
    """
    Main function for the command-line interface.
    Parses arguments and runs the PDF processing workflow.
    """
    parser = argparse.ArgumentParser(
        description="Extract markdown and figures from a PDF, then refine the output."
    )
    parser.add_argument(
        "pdf_file",
        type=Path,
        help="Path to the input PDF file."
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory to save the output files (default: 'output')."
    )

    parsed_args = parser.parse_args(args if args is not None else sys.argv[1:])

    print(f"Starting workflow for PDF: {parsed_args.pdf_file}")
    print(f"Output will be saved to: {parsed_args.output_dir}")

    print("\nStep 1: Extracting markdown and images...")
    md_path = extract_markdown(parsed_args.pdf_file, parsed_args.output_dir)
    if not md_path:
        print("\nError during extraction step. Aborting.")
        return 1

    print(f"Extraction successful. Markdown saved to: {md_path}")

    print("\nStep 2: Refining markdown...")
    refined_md_path = refine_markdown(md_path)
    if not refined_md_path:
        print("\nError during refinement step. Aborting.")
        return 1

    print(f"Refinement successful. Refined markdown saved to: {refined_md_path}")

    print("\nWorkflow completed successfully!")
    return 0

def entry_point():
    """Encapsulates the CLI entry point logic for testability."""
    try:
        # We call main with no arguments, so it uses sys.argv
        sys.exit(main())
    except SystemExit as e:
        # Let SystemExit from argparse propagate
        sys.exit(e.code)
    except Exception:
        # Catch any other unexpected error
        logger.exception("An unexpected error occurred in the CLI.")
        sys.exit(1)

if __name__ == "__main__":
    entry_point()