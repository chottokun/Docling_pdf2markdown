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

# Initialize FastAPI application
app = FastAPI(
    title="Docling Markdown Conversion Server",
    description="A REST API to convert documents to Markdown using Docling."
)

# Directories for server-side file management
# UPLOAD_DIR: Temporary storage for uploaded files (before conversion)
# OUTPUT_DIR: Persistent storage for conversion results (Markdown, images)
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("output")

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


@app.post("/convert/")
async def convert_file(file: UploadFile = File(...)):
    """
    Endpoint to upload a document and initiate the conversion process.

    The process involves:
    1. Validating the file extension.
    2. Saving the uploaded stream to a temporary local file.
    3. Creating a unique request ID and output directory.
    4. Invoking the core Docling conversion logic.
    5. Returning a JSON response with metadata and a download link.
    """
    # 1. Security: Validate file extension
    allowed_extensions = {".pdf", ".docx", ".pptx", ".xlsx"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported: {allowed_extensions}",
        )

    # 2. Save uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        tmp_path = Path(tmp_file.name)

    try:
        # 3. Create a unique isolation directory for this request
        request_id = os.urandom(8).hex()
        request_output_dir = OUTPUT_DIR / request_id
        request_output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Processing conversion request for: {file.filename} (ID: {request_id})")
        
        # 4. Invoke core library logic (process_pdf handles various formats)
        result_path = process_pdf(tmp_path, request_output_dir)

        if not result_path or not result_path.exists():
            raise HTTPException(status_code=500, detail="Conversion failed.")

        # 5. Construct response
        return {
            "message": "Conversion successful",
            "markdown_file": result_path.name,
            "output_id": request_id,
            "download_url": f"/download/{request_id}/{result_path.name}",
        }

    except Exception as e:
        logger.exception(f"An error occurred during conversion for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup: Remove the temporary input file
        if tmp_path.exists():
            tmp_path.unlink()


@app.get("/download/{request_id}/{filename}")
async def download_file(request_id: str, filename: str):
    """
    Endpoint to retrieve converted files (Markdown or extracted images).

    The file is identified by a unique request ID and the target filename.
    """
    # Security: Path resolution and existence check
    file_path = OUTPUT_DIR / request_id / filename
    if not file_path.exists():
        logger.warning(f"Download requested for non-existent file: {request_id}/{filename}")
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(file_path)


@app.get("/")
async def root():
    """Simple health check / welcome endpoint."""
    return {"message": "Welcome to the Docling Markdown Conversion Server"}
