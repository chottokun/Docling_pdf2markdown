import argparse
from pathlib import Path
import sys
import logging
import subprocess
import tempfile

# Import the new high-accuracy processor
from .converter import process_pdf

# Configure logging for the CLI tool
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main(args=None):
    """
    Main function for the command-line interface.
    Parses arguments and runs the high-accuracy PDF processing workflow.
    """
    parser = argparse.ArgumentParser(
        description="Extract markdown, figures, and tables from a PDF with high accuracy."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the input PDF or Office file."
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory to save the output files (default: 'output')."
    )

    parsed_args = parser.parse_args(args if args is not None else sys.argv[1:])

    input_file = parsed_args.input_file
    output_dir = parsed_args.output_dir

    # Supported Office document formats
    office_formats = ['.docx', '.pptx', '.xlsx']

    if input_file.suffix.lower() in office_formats:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            logger.info(f"Converting Office file to PDF: {input_file}")

            try:
                subprocess.run(
                    [
                        "libreoffice",
                        "--headless",
                        "--convert-to", "pdf",
                        str(input_file),
                        "--outdir", str(temp_dir_path)
                    ],
                    check=True,
                    capture_output=True,
                    text=True
                )
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.error(f"Failed to convert {input_file} to PDF. Ensure LibreOffice is installed.")
                logger.error(e)
                if isinstance(e, subprocess.CalledProcessError):
                    logger.error(f"Stderr: {e.stderr}")
                return 1

            pdf_file = temp_dir_path / f"{input_file.stem}.pdf"
            if not pdf_file.exists():
                logger.error("Converted PDF file not found.")
                return 1

            logger.info(f"Successfully converted to {pdf_file}")
            processing_file = pdf_file

            logger.info(f"Starting high-accuracy workflow for: {processing_file}")
            result_path = process_pdf(processing_file, output_dir)
    else:
        processing_file = input_file
        logger.info(f"Starting high-accuracy workflow for: {processing_file}")
        # Call the new, unified processing function
        result_path = process_pdf(processing_file, output_dir)

    if result_path:
        logger.info(f"Workflow completed successfully! Output saved in {parsed_args.output_dir}")
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