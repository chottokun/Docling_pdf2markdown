import pytest
from pathlib import Path
import os
import shutil
from unittest.mock import patch

from src.docling_lib.refinement import refine_markdown, normalize_alt_text

# --- Test Fixtures ---
@pytest.fixture
def sample_md_content():
    """Provides a sample markdown content with an image and caption."""
    return """\
# This is a title

![An image alt text](images/image1.png)
Figure 1: This is the caption for the first image.

![Another image](images/image2.png)
*This is another caption format.*
"""

@pytest.fixture
def md_file(tmp_path, sample_md_content) -> Path:
    """Creates a sample markdown file in a temporary directory."""
    d = tmp_path / "md_dir"
    d.mkdir()
    p = d / "test.md"
    p.write_text(sample_md_content, encoding="utf-8")
    return p

# --- Test Cases for refine_markdown ---

def test_refine_markdown_happy_path(md_file):
    """
    Given: A markdown file with images and captions.
    When: refine_markdown is called.
    Then: A new, refined markdown file should be created with <figure> and <figcaption>.
    """
    refined_path = refine_markdown(md_file)
    assert refined_path is not None
    assert refined_path.name == "test_refined.md"
    assert refined_path.exists()
    content = refined_path.read_text(encoding="utf-8")
    assert '<figure id="fig-001">' in content
    assert '<img src="images/image1.png" alt="An image alt text"' in content
    assert '<figcaption>This is the caption for the first image.</figcaption>' in content
    assert '<figure id="fig-002">' in content
    assert '<figcaption>This is another caption format.</figcaption>' in content

def test_refine_markdown_no_caption(tmp_path):
    """
    Given: A markdown file with an image but no subsequent caption.
    When: refine_markdown is called.
    Then: The image should be wrapped in a <figure> tag, but without a <figcaption>.
    """
    content = "![image without caption](images/no_caption.png)\n\nJust some text."
    md_path = tmp_path / "no_caption.md"
    md_path.write_text(content)
    refined_path = refine_markdown(md_path)
    assert refined_path is not None
    content = refined_path.read_text(encoding="utf-8")
    assert "<figure" in content
    assert "<figcaption>" not in content

def test_refine_markdown_file_not_found():
    """
    Given: A path to a non-existent markdown file.
    When: refine_markdown is called.
    Then: It should return None.
    """
    assert refine_markdown(Path("non_existent_file.md")) is None

def test_refine_markdown_no_images(tmp_path):
    """
    Given: A markdown file with no image links.
    When: refine_markdown is called.
    Then: It should still produce a refined file, but with no changes.
    """
    content = "This markdown has no images."
    md_path = tmp_path / "no_images.md"
    md_path.write_text(content)
    refined_path = refine_markdown(md_path)
    assert refined_path is not None
    assert refined_path.read_text() == content

def test_refine_markdown_no_write_permission(md_file):
    """
    Given: A directory where the refined file cannot be written.
    When: refine_markdown is called.
    Then: It should fail gracefully and return None.
    """
    output_dir = md_file.parent
    os.chmod(output_dir, 0o555) # Read and execute
    assert refine_markdown(md_file) is None
    os.chmod(output_dir, 0o777) # Cleanup

@patch('pathlib.Path.read_text', side_effect=Exception("Unexpected I/O error"))
def test_refine_markdown_read_fails(mock_read, md_file):
    """
    Given: An unexpected error occurs during file reading.
    When: refine_markdown is called.
    Then: It should catch the exception and return None.
    """
    assert refine_markdown(md_file) is None

# --- Test Cases for helper functions ---

def test_normalize_alt_text_empty_alt():
    """
    Given: An empty alt text string.
    When: normalize_alt_text is called.
    Then: It should return a sanitized version of the image filename.
    """
    alt = normalize_alt_text("", "images/some_image-name.png")
    assert alt == "some image name"