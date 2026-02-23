from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
import tempfile
import logging
import os

from .converter import process_pdf
from .config import setup_logging

# --- Logging Setup ---
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Docling Markdown Conversion Server")

# Temporary directory for processing
# In a production environment, this should be managed carefully.
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("output")

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


@app.post("/convert/")
async def convert_file(file: UploadFile = File(...)):
    """
    Endpoint to upload a document and convert it to Markdown.
    """
    # Security: Validate file extension
    allowed_extensions = {".pdf", ".docx", ".pptx", ".xlsx"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported: {allowed_extensions}",
        )

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        tmp_path = Path(tmp_file.name)

    try:
        # Create a unique output directory for this request
        request_id = os.urandom(8).hex()
        request_output_dir = OUTPUT_DIR / request_id
        request_output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Processing file: {file.filename}")
        
        # Use our process_pdf function (which now supports DOCX/PPTX)
        result_path = process_pdf(tmp_path, request_output_dir)

        if not result_path or not result_path.exists():
            raise HTTPException(status_code=500, detail="Conversion failed.")

        # For simplicity, we return the main markdown file.
        # Images are saved in request_output_dir/images
        return {
            "message": "Conversion successful",
            "markdown_file": result_path.name,
            "output_id": request_id,
            "download_url": f"/download/{request_id}/{result_path.name}",
        }

    except Exception as e:
        logger.exception(f"An error occurred during conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temporary input file
        if tmp_path.exists():
            tmp_path.unlink()


@app.get("/download/{request_id}/{filename}")
async def download_file(request_id: str, filename: str):
    """
    Endpoint to download converted files.
    """
    file_path = OUTPUT_DIR / request_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path)


@app.get("/")
async def root():
    return {"message": "Welcome to the Docling Markdown Conversion Server"}
