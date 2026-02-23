import pytest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

from docling_lib.converter import process_pdf
from docling_core.types.doc import ImageRefMode
from docling.datamodel.base_models import InputFormat

# --- Fixtures ---


@pytest.fixture(autouse=True)
def reset_shared_converter():
    """Resets the shared default converter before and after each test."""
    import docling_lib.converter as converter_mod

    converter_mod._default_pdf_converter = None
    yield
    converter_mod._default_pdf_converter = None


# --- Test Cases ---


@patch("docling_lib.converter.DocumentConverter")
def test_process_pdf_calls_docling_api_correctly(
    MockDocumentConverter, tmp_path, pdf_downloader, monkeypatch
):
    """
    Given: A valid PDF path.
    When: process_pdf is called.
    Then: It should initialize DocumentConverter with correct image options and
          call `save_as_markdown` with correct parameters.
    """
    monkeypatch.chdir(tmp_path)
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
    assert pipeline_opts.images_scale == 2.0

    # Verify it was used to convert
    mock_converter_instance.convert.assert_called_once_with(pdf_path)

    # Verify that the save method was called correctly
    mock_doc.save_as_markdown.assert_called_once_with(
        filename=expected_md_path,
        artifacts_dir=images_dir,
        image_mode=ImageRefMode.REFERENCED,
    )

    assert result_path == expected_md_path


@patch("docling_lib.converter.DocumentConverter")
def test_process_pdf_uses_custom_image_scale(
    MockDocumentConverter, tmp_path, pdf_downloader, monkeypatch
):
    """
    Given: A custom image scale.
    When: process_pdf is called with that scale.
    Then: The DocumentConverter should be initialized with that scale.
    """
    monkeypatch.chdir(tmp_path)
    # Arrange
    pdf_path = pdf_downloader("https://arxiv.org/pdf/2406.12430.pdf")
    custom_scale = 1.5

    # Act
    process_pdf(pdf_path, tmp_path, image_scale=custom_scale)

    # Assert
    init_args, init_kwargs = MockDocumentConverter.call_args
    pipeline_opts = init_kwargs["format_options"][InputFormat.PDF].pipeline_options
    assert pipeline_opts.images_scale == custom_scale


def test_process_pdf_e2e_happy_path(tmp_path, pdf_downloader, monkeypatch):
    """
    Given: A real PDF file containing text, figures, and tables.
    When: The `process_pdf` function is called (end-to-end).
    Then: It should generate a non-empty Markdown file and associated image files.
    """
    monkeypatch.chdir(tmp_path)
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


def test_process_pdf_file_not_found(tmp_path, monkeypatch):
    """
    Given: A path to a non-existent PDF file.
    When: `process_pdf` is called.
    Then: It should return None.
    """
    monkeypatch.chdir(tmp_path)
    assert process_pdf(Path("non_existent.pdf"), tmp_path) is None


@patch("docling_lib.converter.DocumentConverter")
def test_process_pdf_conversion_fails(
    MockDocumentConverter, tmp_path, pdf_downloader, monkeypatch
):
    """
    Given: The docling conversion process itself fails.
    When: `process_pdf` is called.
    Then: It should log an error and return None.
    """
    monkeypatch.chdir(tmp_path)
    pdf_path = pdf_downloader("https://arxiv.org/pdf/2406.12430.pdf")
    mock_converter_instance = MockDocumentConverter.return_value
    mock_converter_instance.convert.side_effect = Exception("Conversion Error")
    result = process_pdf(pdf_path, tmp_path)
    assert result is None


@patch("docling_lib.converter.DocumentConverter")
def test_process_pdf_reuses_converter(
    MockDocumentConverter, tmp_path, pdf_downloader, monkeypatch
):
    """
    Verify that multiple calls to process_pdf use the same DocumentConverter instance
    when using the default behavior.
    """
    monkeypatch.chdir(tmp_path)
    pdf_path = pdf_downloader("https://arxiv.org/pdf/2406.12430.pdf")

    # Mock the return value for convert
    mock_converter_instance = MockDocumentConverter.return_value
    mock_converter_instance.convert.return_value.document = MagicMock()

    # First call
    process_pdf(pdf_path, tmp_path / "out1")
    
    # Second call
    process_pdf(pdf_path, tmp_path / "out2")

    # With the scale optimization in process_pdf, this should be exactly 1
    assert MockDocumentConverter.call_count == 1


@patch("docling_lib.converter.DocumentConverter")
def test_process_pdf_with_explicit_converter(
    MockDocumentConverter, tmp_path, pdf_downloader, monkeypatch
):
    """
    Verify that process_pdf uses the provided converter instance if given.
    """
    monkeypatch.chdir(tmp_path)
    pdf_path = pdf_downloader("https://arxiv.org/pdf/2406.12430.pdf")
    mock_explicit_converter = MagicMock()
    mock_explicit_converter.convert.return_value.document = MagicMock()

    # Call with explicit converter
    process_pdf(pdf_path, tmp_path, converter=mock_explicit_converter)

    # The explicit converter should be used
    mock_explicit_converter.convert.assert_called_once()
    # The default DocumentConverter class should NOT be instantiated
    assert MockDocumentConverter.call_count == 0


def test_process_pdf_output_dir_creation_fails(tmp_path, caplog, monkeypatch):
    """
    Given: The output directory cannot be created (e.g., PermissionError).
    When: `process_pdf` is called.
    Then: It should log an error and return None.
    """
    monkeypatch.chdir(tmp_path)
    # Arrange
    pdf_path = tmp_path / "test.pdf"
    pdf_path.touch()
    out_dir = tmp_path / "restricted_dir"

    # Mock Path.mkdir to raise an OSError
    with patch("docling_lib.converter.Path.mkdir") as mock_mkdir:
        mock_mkdir.side_effect = OSError("Mocked Permission Error")

        # Act
        with caplog.at_level("ERROR"):
            result = process_pdf(pdf_path, out_dir)

    # Assert
    assert result is None
    assert "Could not create output directory" in caplog.text


@patch("docling_lib.converter.DocumentConverter")
def test_process_pdf_save_as_markdown_fails(
    MockDocumentConverter, tmp_path, pdf_downloader, caplog, monkeypatch
):
    """
    Given: The save_as_markdown method fails with an exception.
    When: `process_pdf` is called.
    Then: It should log an error and return None.
    """
    monkeypatch.chdir(tmp_path)
    # Arrange
    pdf_path = pdf_downloader("https://arxiv.org/pdf/2406.12430.pdf")
    mock_doc = MagicMock()
    mock_converter_instance = MockDocumentConverter.return_value
    mock_converter_instance.convert.return_value.document = mock_doc

    # Simulate failure in save_as_markdown
    mock_doc.save_as_markdown.side_effect = Exception("Save Error")

    # Act
    with caplog.at_level(logging.ERROR):
        result = process_pdf(pdf_path, tmp_path)

    # Assert
    assert result is None
    assert any("Save Error" in record.message for record in caplog.records)


@patch("docling_lib.converter.DocumentConverter")
def test_process_pdf_with_custom_image_dir(
    MockDocumentConverter, tmp_path, pdf_downloader, monkeypatch
):
    """
    Given: A custom image directory name.
    When: process_pdf is called with image_dir_name.
    Then: It should create the custom directory and save images there.
    """
    monkeypatch.chdir(tmp_path)
    pdf_path = pdf_downloader("https://arxiv.org/pdf/2406.12430.pdf")
    mock_doc = MagicMock()
    mock_converter_instance = MockDocumentConverter.return_value
    mock_converter_instance.convert.return_value.document = mock_doc

    custom_image_dir = "custom_assets"
    output_dir = tmp_path
    expected_images_dir = output_dir / custom_image_dir
    expected_md_path = output_dir / "processed_document.md"

    result_path = process_pdf(pdf_path, output_dir, image_dir_name=custom_image_dir)

    assert expected_images_dir.exists()
    mock_doc.save_as_markdown.assert_called_once_with(
        filename=expected_md_path,
        artifacts_dir=expected_images_dir,
        image_mode=ImageRefMode.REFERENCED,
    )
    assert result_path == expected_md_path


@patch("docling_lib.converter.DocumentConverter")
def test_process_pdf_with_custom_output_name(
    MockDocumentConverter, tmp_path, pdf_downloader, monkeypatch
):
    """
    Given: A custom output Markdown filename.
    When: process_pdf is called with md_output_name.
    Then: It should save the Markdown file with the specified name.
    """
    monkeypatch.chdir(tmp_path)
    pdf_path = pdf_downloader("https://arxiv.org/pdf/2406.12430.pdf")
    mock_doc = MagicMock()
    mock_converter_instance = MockDocumentConverter.return_value
    mock_converter_instance.convert.return_value.document = mock_doc

    custom_output_name = "my_doc.md"
    output_dir = tmp_path
    expected_md_path = output_dir / custom_output_name
    images_dir = output_dir / "images"

    result_path = process_pdf(pdf_path, output_dir, md_output_name=custom_output_name)

    mock_doc.save_as_markdown.assert_called_once_with(
        filename=expected_md_path,
        artifacts_dir=images_dir,
        image_mode=ImageRefMode.REFERENCED,
    )
    assert result_path == expected_md_path


def test_process_pdf_path_traversal_prevention(tmp_path, pdf_downloader, monkeypatch):
    """
    Given: An output directory with traversal components.
    When: process_pdf is called.
    Then: It should log a security error and return None.
    """
    monkeypatch.chdir(tmp_path)
    pdf_path = pdf_downloader("https://arxiv.org/pdf/2406.12430.pdf")

    # Attempt to save using traversal
    traversal_dir = tmp_path / ".." / "outside"

    result = process_pdf(pdf_path, traversal_dir)

    assert result is None


@patch("docling_lib.converter.DocumentConverter")
def test_process_docx_happy_path(
    MockDocumentConverter, tmp_path, monkeypatch
):
    """
    Given: A valid DOCX path.
    When: process_pdf is called.
    Then: It should call convert with the DOCX path.
    """
    monkeypatch.chdir(tmp_path)
    docx_path = tmp_path / "test.docx"
    docx_path.touch()
    mock_doc = MagicMock()
    MockDocumentConverter.return_value.convert.return_value.document = mock_doc

    result = process_pdf(docx_path, tmp_path)

    assert result is not None
    MockDocumentConverter.return_value.convert.assert_called_once_with(docx_path)