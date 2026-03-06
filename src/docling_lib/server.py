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
    # Security: Prevent path traversal
    try:
        # Resolve the intended base directory for the request
        abs_output_dir = OUTPUT_DIR.resolve()
        base_dir = (abs_output_dir / request_id).resolve()
        # Resolve the requested file path
        file_path = (base_dir / filename).resolve()

        # Verify that the base_dir itself is within OUTPUT_DIR
        # This protects against traversal via request_id
        if not base_dir.is_relative_to(abs_output_dir):
            logger.warning(f"Path traversal attempt via request_id: {request_id}")
            raise HTTPException(status_code=400, detail="Invalid request ID.")

        # Verify that the file_path is within the base_dir
        # This protects against traversal via filename
        if not file_path.is_relative_to(base_dir):
            logger.warning(f"Path traversal attempt via filename: {filename} in {request_id}")
            raise HTTPException(status_code=403, detail="Access denied.")

    except (ValueError, RuntimeError) as e:
        logger.error(f"Error validating path: {e}")
        raise HTTPException(status_code=400, detail="Invalid path.")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(file_path)


@app.get("/")
async def root():
    return {"message": "Welcome to the Docling Markdown Conversion Server"}
