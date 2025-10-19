import pytest
from pathlib import Path
from unittest.mock import patch
import os

from src.docling_lib.extraction import extract_markdown

# --- Test Fixtures & Constants ---
TEST_DATA_DIR = Path(__file__).parent / "test_data"
VALID_PDF = TEST_DATA_DIR / "1706.03762.pdf"

# --- Test Cases ---

def test_extract_markdown_happy_path(tmp_path):
    """
    Given: A valid PDF file and an empty, writable output directory.
    When: extract_markdown is called.
    Then: It should return the path to the new markdown file, and the output directory
          should contain the markdown file and an 'images' subdirectory with images.
    """
    out_dir = tmp_path
    result_path = extract_markdown(VALID_PDF, out_dir)
    assert result_path is not None
    assert result_path.name.endswith(".md")
    assert result_path.exists()
    images_dir = out_dir / "images"
    assert images_dir.exists()
    assert images_dir.is_dir()
    image_files = list(images_dir.glob("*.png"))
    assert len(image_files) > 0

def test_extract_markdown_output_dir_does_not_exist(tmp_path):
    """
    Given: A valid PDF file and a non-existent output directory path.
    When: extract_markdown is called.
    Then: The output directory should be created, and the extraction should succeed.
    """
    out_dir = tmp_path / "new_output"
    result_path = extract_markdown(VALID_PDF, out_dir)
    assert out_dir.exists()
    assert result_path is not None
    assert result_path.exists()
    assert (out_dir / "images").exists()

def test_extract_markdown_pdf_not_found():
    """
    Given: A path to a non-existent PDF file.
    When: extract_markdown is called.
    Then: It should return None and not raise an error.
    """
    result = extract_markdown(Path("non_existent_file.pdf"), Path("any_dir"))
    assert result is None

def test_extract_markdown_corrupted_pdf(tmp_path):
    """
    Given: A corrupted or non-PDF file.
    When: extract_markdown is called.
    Then: It should handle the error gracefully, return None, and not crash.
    """
    corrupted_file = tmp_path / "corrupted.pdf"
    corrupted_file.write_text("This is not a valid PDF content.")
    out_dir = tmp_path / "output"
    result = extract_markdown(corrupted_file, out_dir)
    assert result is None

@patch('src.docling_lib.extraction.pymupdf4llm.to_markdown')
def test_extract_markdown_pymupdf4llm_type_error_fallback(mock_to_markdown, tmp_path):
    """
    Given: pymupdf4llm raises a TypeError (e.g., use_getText_options unsupported).
    When: extract_markdown is called.
    Then: It should fall back to basic extraction.
    """
    # Simulate the TypeError on the first call, and success on the second (fallback)
    mock_to_markdown.side_effect = [
        TypeError("use_getText_options not supported"),
        "Fallback successful text"
    ]
    out_dir = tmp_path
    result_path = extract_markdown(VALID_PDF, out_dir)
    assert result_path is not None
    assert result_path.read_text() == "Fallback successful text"
    assert mock_to_markdown.call_count == 2

@patch('src.docling_lib.extraction.pymupdf4llm.to_markdown', side_effect=Exception("Extraction failed"))
def test_extract_markdown_pymupdf4llm_fails_gracefully(mock_to_markdown, tmp_path):
    """
    Given: The underlying pymupdf4llm library fails completely.
    When: extract_markdown is called.
    Then: It should return None.
    """
    out_dir = tmp_path
    result = extract_markdown(VALID_PDF, out_dir)
    assert result is None

def test_extract_markdown_no_write_permission_to_create_dir(tmp_path):
    """
    Given: An output directory path that cannot be created due to permissions.
    When: extract_markdown is called.
    Then: It should fail gracefully and return None.
    """
    # Create a read-only directory and try to create a subdirectory within it
    read_only_dir = tmp_path
    os.chmod(read_only_dir, 0o444)
    out_dir = read_only_dir / "sub"
    result = extract_markdown(VALID_PDF, out_dir)
    assert result is None
    # Cleanup
    os.chmod(read_only_dir, 0o777)

@patch('pathlib.Path.write_text', side_effect=Exception("Disk is full"))
def test_extract_markdown_write_fails(mock_write_text, tmp_path):
    """
    Given: The final markdown file cannot be written to disk.
    When: extract_markdown is called.
    Then: It should fail gracefully and return None.
    """
    out_dir = tmp_path
    result = extract_markdown(VALID_PDF, out_dir)
    assert result is None