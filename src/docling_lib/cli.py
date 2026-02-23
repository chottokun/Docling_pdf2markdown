import argparse
from pathlib import Path
import sys
import logging

# Import the new high-accuracy processor
from .converter import process_pdf, IMAGE_RESOLUTION_SCALE

# Configure logging for the CLI tool
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main(args=None):
    """
    Main function for the command-line interface.
    Parses arguments and runs the high-accuracy PDF processing workflow.
    """
    parser = argparse.ArgumentParser(
        description="Extract markdown, figures, and tables from a PDF with high accuracy."
    )
    parser.add_argument("pdf_file", type=Path, help="Path to the input PDF file.")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory to save the output files (default: 'output').",
    )
    parser.add_argument(
        "--image-scale",
        type=float,
        default=IMAGE_RESOLUTION_SCALE,
        help=f"Scale factor for image resolution (default: {IMAGE_RESOLUTION_SCALE}).",
    )

    parsed_args = parser.parse_args(args if args is not None else sys.argv[1:])

    logger.info(f"Starting high-accuracy workflow for PDF: {parsed_args.pdf_file}")

    # Call the new, unified processing function
    result_path = process_pdf(
        parsed_args.pdf_file,
        parsed_args.output_dir,
        image_scale=parsed_args.image_scale,
    )

    if result_path:
        logger.info(
            f"Workflow completed successfully! Output saved in {parsed_args.output_dir}"
        )
        return 0
    else:
        logger.error("Workflow failed. Please check the logs for details.")
        return 1


def entry_point():
    """Encapsulates the CLI entry point logic for testability."""
    try:
        sys.exit(main())
    except SystemExit as e:
        sys.exit(e.code)
    except Exception as e:
        logger.exception(f"An unexpected error occurred in the CLI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    entry_point()
