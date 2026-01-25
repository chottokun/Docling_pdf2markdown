import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import io
import zipfile
from unittest.mock import patch, MagicMock

from docling_lib.server import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Docling Markdown Conversion Server"}

@patch('docling_lib.server.cli_main')
def test_convert_file_success(mock_cli_main, tmp_path):
    # Setup: Mock the CLI main to "create" a markdown file in the temporary output directory
    def side_effect(args):
        # args[2] is the output directory
        out_dir = Path(args[2])
        md_file = out_dir / "extracted_document.md"
        md_file.parent.mkdir(parents=True, exist_ok=True)
        md_file.write_text("# Test Markdown")
        return 0

    mock_cli_main.side_effect = side_effect

    # Create a dummy PDF to upload
    file_content = b"%PDF-1.4 dummy content"
    file_name = "test.pdf"

    response = client.post(
        "/convert/",
        files={"file": (file_name, file_content, "application/pdf")}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    # Verify the zip content
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        assert "extracted_document.md" in z.namelist()
        assert z.read("extracted_document.md") == b"# Test Markdown"

@patch('docling_lib.server.cli_main')
def test_convert_file_cli_failure(mock_cli_main):
    mock_cli_main.return_value = 1

    file_content = b"dummy content"
    file_name = "test.pdf"

    response = client.post(
        "/convert/",
        files={"file": (file_name, file_content, "application/pdf")}
    )

    assert response.status_code == 500
    assert "File conversion process failed" in response.json()["detail"]

@patch('docling_lib.server.cli_main')
def test_convert_file_missing_output(mock_cli_main):
    # CLI returns 0 but doesn't create the file
    mock_cli_main.return_value = 0

    file_content = b"dummy content"
    file_name = "test.pdf"

    response = client.post(
        "/convert/",
        files={"file": (file_name, file_content, "application/pdf")}
    )

    assert response.status_code == 500
    assert "output markdown file is missing" in response.json()["detail"]
