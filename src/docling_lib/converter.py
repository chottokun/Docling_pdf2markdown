from pathlib import Path
from typing import Optional
import logging

# Docling's high-level API
from docling.document_converter import (
    DocumentConverter,
    ConversionResult,
    PdfFormatOption,
)
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.types.doc import ImageRefMode
from docling.datamodel.base_models import InputFormat

from .config import MD_OUTPUT_NAME, IMAGE_DIR_NAME, IMAGE_RESOLUTION_SCALE

# --- Logging Setup ---
logger = logging.getLogger(__name__)


class PDFConverter:
    """
    A class that manages a DocumentConverter instance for PDF processing.
    Encapsulating the converter allows for reuse and better performance.
    """

    def __init__(
        self,
        converter: Optional[DocumentConverter] = None,
        image_scale: float = IMAGE_RESOLUTION_SCALE,
    ):
        if converter is None:
            logger.info("Initializing DocumentConverter with latest Docling options...")
            # Configure pipeline to generate and keep images of pictures and pages
            pipeline_options = PdfPipelineOptions()
            pipeline_options.images_scale = image_scale
            pipeline_options.generate_page_images = True
            pipeline_options.generate_picture_images = True

            self.doc_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
        else:
            self.doc_converter = converter

    def process_pdf(
        self,
        pdf_path: Path,
        out_dir: Path,
        image_dir_name: str = IMAGE_DIR_NAME,
        md_output_name: str = MD_OUTPUT_NAME,
    ) -> Optional[Path]:
        """
        Processes a PDF file using the internal DocumentConverter instance.
        """
        # Security: Validate that the input path is a file and has a .pdf extension
        if not pdf_path.is_file():
            logger.error(f"PDF file not found or is not a file: {pdf_path}")
            return None

        if pdf_path.suffix.lower() != ".pdf":
            logger.error(f"Input file is not a PDF: {pdf_path}")
            return None

        # --- Security Check: Prevent Path Traversal ---
        try:
            resolved_out_dir = out_dir.resolve()
            cwd = Path.cwd().resolve()
            if not resolved_out_dir.is_relative_to(cwd):
                logger.error(
                    f"Security Error: Output directory {out_dir} is outside the intended working directory {cwd}"
                )
                return None
        except Exception as e:
            logger.error(
                f"Security Error: Could not validate output directory {out_dir}: {e}"
            )
            return None

        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            images_dir = out_dir / image_dir_name
            images_dir.mkdir(exist_ok=True)
        except Exception as e:
            logger.error(f"Could not create output directory {out_dir}: {e}")
            return None

        logger.info(f"Converting {pdf_path}...")
        try:
            conv_res: ConversionResult = self.doc_converter.convert(pdf_path)
            doc = conv_res.document
        except Exception as e:
            logger.error(f"Docling failed to convert the document: {e}", exc_info=True)
            return None

        output_path = out_dir / md_output_name

        try:
            # Save the document as Markdown, referencing the externally saved images.
            doc.save_as_markdown(
                filename=output_path,
                artifacts_dir=images_dir,
                image_mode=ImageRefMode.REFERENCED,
            )
            logger.info(f"Successfully generated Markdown and images at {out_dir}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save document as markdown: {e}", exc_info=True)
            return None


# --- Shared Default Instance ---
_default_pdf_converter: Optional[PDFConverter] = None


def get_default_converter(image_scale: float = IMAGE_RESOLUTION_SCALE) -> PDFConverter:
    """Returns a shared default PDFConverter instance."""
    global _default_pdf_converter
    # If a different scale is requested, we recreate it (or we could manage a cache)
    # For now, we just check if it's already there
    if _default_pdf_converter is None:
        _default_pdf_converter = PDFConverter(image_scale=image_scale)
    return _default_pdf_converter


def process_pdf(
    pdf_path: Path,
    out_dir: Path,
    image_dir_name: str = IMAGE_DIR_NAME,
    md_output_name: str = MD_OUTPUT_NAME,
    image_scale: float = IMAGE_RESOLUTION_SCALE,
    converter: Optional[DocumentConverter] = None,
) -> Optional[Path]:
    """
    Processes a PDF file to extract text, figures, and tables using the
    DocumentConverter API, and generates a high-accuracy Markdown file.

    If `converter` is provided, it uses that instance. Otherwise, it uses
    a shared default instance for better performance.
    """
    if converter is not None:
        return PDFConverter(converter=converter).process_pdf(
            pdf_path,
            out_dir,
            image_dir_name=image_dir_name,
            md_output_name=md_output_name,
        )

    return get_default_converter(image_scale=image_scale).process_pdf(
        pdf_path, out_dir, image_dir_name=image_dir_name, md_output_name=md_output_name
    )
