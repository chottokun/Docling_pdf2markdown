from pathlib import Path
from unittest.mock import patch, MagicMock

from src.docling_lib.converter import process_pdf
from docling_core.types.doc import ImageRefMode
from docling.datamodel.base_models import InputFormat

# --- Test Cases ---


@patch("src.docling_lib.converter.DocumentConverter")
def test_process_pdf_calls_docling_api_correctly(
    MockDocumentConverter, tmp_path, pdf_downloader
):
    """
    Given: A valid PDF path.
    When: process_pdf is called.
    Then: It should initialize DocumentConverter with correct image options and
          call `save_as_markdown` with correct parameters.
    """
    # Arrange
    pdf_path = pdf_downloader("https://arxiv.org/pdf/2406.12430.pdf")
    mock_doc = MagicMock()
    mock_converter_instance = MockDocumentConverter.return_value
    mock_converter_instance.convert.return_value.document = mock_doc

    output_dir = tmp_path
    images_dir = output_dir / "images"
    expected_md_path = output_dir / "processed_document.md"

    # Act
    result_path = process_pdf(pdf_path, output_dir)

    # Assert
    # Verify that the converter was initialized with pipeline options
    init_args, init_kwargs = MockDocumentConverter.call_args
    assert "format_options" in init_kwargs
    format_options = init_kwargs["format_options"]
    assert InputFormat.PDF in format_options
    pipeline_opts = format_options[InputFormat.PDF].pipeline_options
    assert pipeline_opts.generate_picture_images is True

    # Verify it was used to convert
    mock_converter_instance.convert.assert_called_once_with(pdf_path)

    # Verify that the save method was called correctly
    mock_doc.save_as_markdown.assert_called_once_with(
        filename=expected_md_path,
        artifacts_dir=images_dir,
        image_mode=ImageRefMode.REFERENCED,
    )

    assert result_path == expected_md_path


@patch("src.docling_lib.converter.DocumentConverter")
def test_process_pdf_uses_custom_image_scale(
    MockDocumentConverter, tmp_path, pdf_downloader
):
    """
    Given: A custom image scale.
    When: process_pdf is called with that scale.
    Then: It should initialize DocumentConverter with the provided image scale.
    """
    # Arrange
    pdf_path = pdf_downloader("https://arxiv.org/pdf/2406.12430.pdf")
    custom_scale = 3.5
    mock_doc = MagicMock()
    mock_converter_instance = MockDocumentConverter.return_value
    mock_converter_instance.convert.return_value.document = mock_doc

    # Act
    process_pdf(pdf_path, tmp_path, image_scale=custom_scale)

    # Assert
    init_args, init_kwargs = MockDocumentConverter.call_args
    pipeline_opts = init_kwargs["format_options"][InputFormat.PDF].pipeline_options
    assert pipeline_opts.images_scale == custom_scale


def test_process_pdf_e2e_happy_path(tmp_path, pdf_downloader):
    """
    Given: A real PDF file containing text, figures, and tables.
    When: The `process_pdf` function is called (end-to-end).
    Then: It should generate a non-empty Markdown file and associated image files.
    """
    pdf_path = pdf_downloader("https://arxiv.org/pdf/2406.12430.pdf")
    output_dir = tmp_path
    result_path = process_pdf(pdf_path, output_dir)

    assert result_path is not None
    assert result_path.exists()

    content = result_path.read_text(encoding="utf-8")
    assert len(content) > 100
    assert "| " in content

    images_dir = output_dir / "images"
    assert images_dir.exists()
    image_files = list(images_dir.glob("*.png"))
    assert len(image_files) > 0


def test_process_pdf_file_not_found(tmp_path):
    """
    Given: A path to a non-existent PDF file.
    When: `process_pdf` is called.
    Then: It should return None.
    """
    assert process_pdf(Path("non_existent.pdf"), tmp_path) is None


@patch("src.docling_lib.converter.DocumentConverter")
def test_process_pdf_conversion_fails(MockDocumentConverter, tmp_path, pdf_downloader):
    """
    Given: The docling conversion process itself fails.
    When: `process_pdf` is called.
    Then: It should log an error and return None.
    """
    pdf_path = pdf_downloader("https://arxiv.org/pdf/2406.12430.pdf")
    mock_converter_instance = MockDocumentConverter.return_value
    mock_converter_instance.convert.side_effect = Exception("Conversion Error")
    result = process_pdf(pdf_path, tmp_path)
    assert result is None
