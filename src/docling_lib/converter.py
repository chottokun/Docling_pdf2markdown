from pathlib import Path
from typing import Optional
import logging

# Docling's high-level API
from docling.document_converter import DocumentConverter, ConversionResult, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.types.doc import ImageRefMode
from docling.datamodel.base_models import InputFormat

# --- Logging Setup ---
logger = logging.getLogger(__name__)

# --- Constants ---
MD_OUTPUT_NAME = "processed_document.md"
IMAGE_DIR_NAME = "images"
IMAGE_RESOLUTION_SCALE = 2.0 # Higher value for better image quality

def process_pdf(pdf_path: Path, out_dir: Path) -> Optional[Path]:
    """
    Processes a PDF file to extract text, figures, and tables using the
    DocumentConverter API, and generates a high-accuracy Markdown file.
    """
    # Security: Validate that the input path is a file and has a .pdf extension
    if not pdf_path.is_file():
        logger.error(f"PDF file not found or is not a file: {pdf_path}")
        return None

    if pdf_path.suffix.lower() != ".pdf":
        logger.error(f"Input file is not a PDF: {pdf_path}")
        return None

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        images_dir = out_dir / IMAGE_DIR_NAME
        images_dir.mkdir(exist_ok=True)
    except Exception as e:
        logger.error(f"Could not create output directory {out_dir}: {e}")
        return None

    logger.info("Initializing DocumentConverter with image generation options...")

    # Configure pipeline to generate and keep images of pictures and pages
    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    logger.info(f"Converting {pdf_path}...")
    try:
        conv_res: ConversionResult = doc_converter.convert(pdf_path)
        doc = conv_res.document
    except Exception as e:
        logger.error(f"Docling failed to convert the document: {e}", exc_info=True)
        return None

    output_path = out_dir / MD_OUTPUT_NAME

    try:
        # Save the document as Markdown, referencing the externally saved images.
        doc.save_as_markdown(
            filename=output_path,
            artifacts_dir=images_dir,
            image_mode=ImageRefMode.REFERENCED
        )
        logger.info(f"Successfully generated Markdown and images at {out_dir}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to save document as markdown: {e}", exc_info=True)
        return None