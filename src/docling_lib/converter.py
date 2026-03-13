import logging
from pathlib import Path
from typing import Optional

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    WordFormatOption,
    PowerpointFormatOption,
)
from docling_core.types.doc import ImageRefMode

from .config import MD_OUTPUT_NAME, IMAGE_DIR_NAME, IMAGE_RESOLUTION_SCALE

# Configure logging for this module
logger = logging.getLogger(__name__)


class PDFConverter:
    """
    A class to manage a reusable DocumentConverter instance for performance optimization.

    Initializing the Docling DocumentConverter can be expensive. This class wraps it
    to allow reuse across multiple conversion requests.
    """

    def __init__(self, image_scale: float = IMAGE_RESOLUTION_SCALE):
        """
        Initializes the PDFConverter with specific pipeline options.

        Args:
            image_scale (float): The resolution scale for extracted images.
        """
        pipeline_options = PdfPipelineOptions()
        pipeline_options.generate_picture_images = True
        pipeline_options.images_scale = image_scale

        # Initialize the core Docling converter with supported formats
        self.doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
                InputFormat.DOCX: WordFormatOption(),
                InputFormat.PPTX: PowerpointFormatOption(),
            }
        )
        self.image_scale = image_scale

    def convert(
        self,
        input_path: Path,
        output_dir: Path,
        image_dir_name: str = IMAGE_DIR_NAME,
        md_output_name: str = MD_OUTPUT_NAME,
    ) -> Optional[Path]:
        """
        Converts a single document to Markdown and extracts images.

        Args:
            input_path (Path): Path to the input document (PDF, DOCX, PPTX).
            output_dir (Path): Directory where the conversion results will be saved.
            image_dir_name (str): Name of the sub-directory for extracted images.
            md_output_name (str): Filename for the output Markdown file.

        Returns:
            Optional[Path]: The path to the generated Markdown file, or None if conversion failed.

        Raises:
            OSError, PermissionError: If there are filesystem-related issues.
        """
        try:
            # Step 1: Perform actual conversion using Docling
            result = self.doc_converter.convert(input_path)
            doc = result.document

            # Step 2: Prepare output structure
            output_dir.mkdir(parents=True, exist_ok=True)
            images_dir = output_dir / image_dir_name
            images_dir.mkdir(parents=True, exist_ok=True)

            # Step 3: Save results
            # The artifacts_dir is where images referenced in the markdown will be stored.
            md_path = output_dir / md_output_name
            doc.save_as_markdown(
                filename=md_path,
                artifacts_dir=images_dir,
                image_mode=ImageRefMode.REFERENCED,
            )

            logger.info(f"Successfully processed {input_path}")
            return md_path

        except (OSError, PermissionError) as e:
            # Propagate filesystem errors as they might need special handling by the caller
            raise e
        except Exception as e:
            logger.error(f"Error converting document {input_path}: {e}")
            return None


# Global shared converter instance for reuse (caching mechanism)
_default_pdf_converter: Optional[PDFConverter] = None


def process_pdf(
    pdf_path: Path,
    output_dir: Path,
    image_dir_name: str = IMAGE_DIR_NAME,
    md_output_name: str = MD_OUTPUT_NAME,
    image_scale: float = IMAGE_RESOLUTION_SCALE,
    converter: Optional[DocumentConverter] = None,
) -> Optional[Path]:
    """
    High-level entry point to process a document (PDF, DOCX, etc.).
    This function handles validation, security, and coordinates the conversion.

    Args:
        pdf_path (Path): Path to the input file.
        output_dir (Path): Directory for results.
        image_dir_name (str): Name for image directory.
        md_output_name (str): Name for markdown file.
        image_scale (float): Scale for image resolution.
        converter (Optional[DocumentConverter]): Optional pre-configured converter.

    Returns:
        Optional[Path]: Path to the output markdown file.
    """
    # 1. Input Validation
    if not pdf_path.exists():
        logger.error(f"Input file not found: {pdf_path}")
        return None

    # 2. Security Check: Path Traversal Prevention
    # Ensures that the output directory does not attempt to escape the intended path.
    try:
        Path(output_dir).resolve()
        # Explicit check for ".." in path parts as an extra layer of security
        if ".." in output_dir.parts:
             logger.error(f"Security Error: Traversal detected in output directory {output_dir}")
             return None
            
    except Exception as e:
        logger.error(f"Security Error during path resolution: {e}")
        return None

    # 3. Processing Logic
    try:
        if converter:
            # Case A: An explicit converter was provided (often for testing or custom needs)
            result = converter.convert(pdf_path)
            doc = result.document

            output_dir.mkdir(parents=True, exist_ok=True)
            images_dir = output_dir / image_dir_name
            images_dir.mkdir(parents=True, exist_ok=True)

            md_path = output_dir / md_output_name
            doc.save_as_markdown(
                filename=md_path,
                artifacts_dir=images_dir,
                image_mode=ImageRefMode.REFERENCED,
            )
            return md_path

        # Case B: Use the shared/singleton PDFConverter instance
        global _default_pdf_converter
        # Re-initialize if the scale has changed or if it hasn't been initialized yet
        if (
            _default_pdf_converter is None
            or _default_pdf_converter.image_scale != image_scale
        ):
            _default_pdf_converter = PDFConverter(image_scale=image_scale)

        return _default_pdf_converter.convert(
            pdf_path, output_dir, image_dir_name, md_output_name
        )

    except (OSError, PermissionError) as e:
        logger.error(f"Could not create output directory: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected workflow error: {e}")
        return None
