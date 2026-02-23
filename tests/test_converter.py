import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from docling_lib.converter import convert_document
from docling.document_converter import PdfFormatOption, WordFormatOption
from docling_core.types.doc import ImageRefMode
from docling.datamodel.base_models import InputFormat

# --- Test Cases ---

@patch('docling_lib.converter.DocumentConverter')
def test_convert_document_calls_docling_api_correctly(MockDocumentConverter, tmp_path, pdf_downloader):
    """
    Given: A valid document path.
    When: convert_document is called.
    Then: It should initialize DocumentConverter with correct image options and
          call `save_as_markdown` with correct parameters for both standard and refined files.
    """
    # Arrange
    pdf_path = pdf_downloader("https://arxiv.org/pdf/2406.12430.pdf")
    mock_doc = MagicMock()
    mock_converter_instance = MockDocumentConverter.return_value
    mock_converter_instance.convert.return_value.document = mock_doc

    output_dir = tmp_path
    images_dir = output_dir / "images"
    expected_md_path = output_dir / "extracted_document.md"
    expected_refined_md_path = output_dir / "extracted_document_refined.md"

    # Act
    result_path = convert_document(pdf_path, output_dir)

    # Assert
    # Verify that the converter was initialized with pipeline options
    init_args, init_kwargs = MockDocumentConverter.call_args
    assert 'format_options' in init_kwargs
    format_options = init_kwargs['format_options']
    assert InputFormat.PDF in format_options
    pipeline_opts = format_options[InputFormat.PDF].pipeline_options
    assert pipeline_opts.generate_picture_images is True

    # Verify it was used to convert
    mock_converter_instance.convert.assert_called_once_with(pdf_path)

    # Verify that the save method was called correctly for both files
    save_calls = [
        call(filename=expected_md_path, artifacts_dir=images_dir, image_mode=ImageRefMode.REFERENCED),
        call(filename=expected_refined_md_path, artifacts_dir=images_dir, image_mode=ImageRefMode.REFERENCED)
    ]
    mock_doc.save_as_markdown.assert_has_calls(save_calls, any_order=True)

    assert result_path == expected_md_path

def test_convert_document_e2e_happy_path(tmp_path, pdf_downloader):
    """
    Given: A real PDF file containing text, figures, and tables.
    When: The `convert_document` function is called (end-to-end).
    Then: It should generate non-empty Markdown files and associated image files.
    """
    pdf_path = pdf_downloader("https://arxiv.org/pdf/2406.12430.pdf")
    output_dir = tmp_path
    result_path = convert_document(pdf_path, output_dir)

    assert result_path is not None
    assert result_path.exists()
    assert (output_dir / "extracted_document_refined.md").exists()

    content = result_path.read_text(encoding="utf-8")
    assert len(content) > 100
    assert "| " in content

    images_dir = output_dir / "images"
    assert images_dir.exists()
    image_files = list(images_dir.glob("*.png"))
    assert len(image_files) > 0

def test_convert_document_file_not_found(tmp_path):
    """
    Given: A path to a non-existent file.
    When: `convert_document` is called.
    Then: It should return None.
    """
    assert convert_document(Path("non_existent.pdf"), tmp_path) is None

@patch('docling_lib.converter.DocumentConverter')
def test_convert_document_conversion_fails(MockDocumentConverter, tmp_path, pdf_downloader):
    """
    Given: The docling conversion process itself fails.
    When: `convert_document` is called.
    Then: It should log an error and return None.
    """
    pdf_path = pdf_downloader("https://arxiv.org/pdf/2406.12430.pdf")
    mock_converter_instance = MockDocumentConverter.return_value
    mock_converter_instance.convert.side_effect = Exception("Conversion Error")
    result = convert_document(pdf_path, tmp_path)
    assert result is None

def test_convert_document_docx_happy_path(tmp_path, file_downloader):
    """
    Given: A real DOCX file.
    When: The `convert_document` function is called.
    Then: It should generate non-empty Markdown files.
    """
    docx_url = "https://raw.githubusercontent.com/DS4SD/docling/main/tests/data/docx/word_sample.docx"
    docx_path = file_downloader(docx_url)
    output_dir = tmp_path
    result_path = convert_document(docx_path, output_dir)

    assert result_path is not None
    assert result_path.exists()

    content = result_path.read_text(encoding="utf-8")
    assert len(content) > 10
