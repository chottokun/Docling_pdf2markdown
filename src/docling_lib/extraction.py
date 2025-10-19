import re
import logging
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
import pymupdf4llm

# --- Constants ---
MD_OUTPUT_NAME = "extracted_document.md"
IMAGE_DIR_NAME = "images"
DPI = 300

# --- Logging Setup ---
# Configure logger to be used by the library
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def extract_markdown(pdf_path: Path, out_dir: Path) -> Optional[Path]:
    """
    Extracts Markdown and images from a PDF using pymupdf4llm.

    Args:
        pdf_path (Path): Path to the input PDF file.
        out_dir (Path): Directory to save the Markdown file and images.

    Returns:
        Optional[Path]: The path to the generated Markdown file, or None if extraction fails.
    """
    # 1. Validate PDF existence
    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        return None

    # 2. Ensure output directory exists and is writable
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        images_dir = out_dir / IMAGE_DIR_NAME
        images_dir.mkdir(exist_ok=True)
    except PermissionError:
        logger.error(f"No write permission for output directory: {out_dir}")
        return None
    except Exception as e:
        logger.error(f"Failed to create output directory {out_dir}: {e}")
        return None

    md_output_path = out_dir / MD_OUTPUT_NAME

    # 3. Extract content using pymupdf4llm
    try:
        logger.info(f"Extracting Markdown from {pdf_path}...")
        # Use a safe flag for text extraction, similar to the sample code's logic
        flags = getattr(fitz, "TEXTFLAGS_TEXT", 1)

        md_text = pymupdf4llm.to_markdown(
            doc=str(pdf_path.resolve()),
            write_images=True,
            image_path=str(images_dir.resolve()),
            image_format="png",
            dpi=DPI,
            page_chunks=False,
            use_getText_options={'flags': int(flags)}
        )
    except TypeError:
        logger.warning("`use_getText_options` not supported. Falling back to basic extraction.")
        try:
            md_text = pymupdf4llm.to_markdown(
                doc=str(pdf_path.resolve()),
                write_images=True,
                image_path=str(images_dir.resolve()),
                image_format="png",
                dpi=DPI,
                page_chunks=False
            )
        except Exception as e:
            logger.error(f"pymupdf4llm basic extraction failed: {e}")
            return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during pymupdf4llm extraction: {e}")
        # This catches errors from corrupted PDFs or other library issues.
        return None

    # 4. Post-process to ensure relative image paths
    # This regex handles different path separators and ensures a clean relative path.
    # It looks for `![...](anything/images/filename.png)` and converts it to `![...](images/filename.png)`
    pattern = re.compile(r'!\[(.*?)\]\((?:.*?/)?' + re.escape(IMAGE_DIR_NAME) + r'[\\/](.*?)\)')
    md_text = pattern.sub(r'![[\1]](' + IMAGE_DIR_NAME + r'/\2)', md_text)


    # 5. Write the final markdown to a file
    try:
        md_output_path.write_text(md_text, encoding="utf-8")
        logger.info(f"Markdown extracted successfully to: {md_output_path}")
        return md_output_path
    except Exception as e:
        logger.error(f"Failed to write Markdown to {md_output_path}: {e}")
        return None