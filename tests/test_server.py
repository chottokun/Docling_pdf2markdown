from fastapi.testclient import TestClient
from pathlib import Path
import zipfile
import io

from docling_lib.server import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Docling Markdown Conversion Server"}

def test_convert_file():
    # Path to the test document
    file_path = Path("tests/test_data/test_document.docx")
    assert file_path.exists(), "Test document not found at tests/test_data/test_document.docx"

    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        response = client.post("/convert/", files=files)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    # Verify the contents of the zip file
    zip_data = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_data, 'r') as zf:
        # Check for the existence of the markdown file
        assert "processed_document.md" in zf.namelist()

        # Check for the existence of the images directory (optional, might not always be present)
        image_files = [name for name in zf.namelist() if name.startswith("images/")]
        # For this specific test document, we expect at least one image.
        # This might need to be adjusted if the test document changes.
        assert len(image_files) > 0, "The zip file should contain an 'images' directory with extracted images."
