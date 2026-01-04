import fastapi
from fastapi import UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import tempfile
import shutil
from pathlib import Path
import zipfile
import logging

from .cli import main as cli_main

app = fastapi.FastAPI()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@app.post("/convert/")
async def convert_file(file: UploadFile = File(...)):
    """
    Accepts a file (PDF, DOCX, PPTX, XLSX), converts it to Markdown,
    zips the output (Markdown file and images directory), and returns the zip archive.
    """
    # Create a temporary directory to store the uploaded file and the output
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Define paths for input and output within the temporary directory
        input_file_path = temp_dir_path / file.filename
        output_dir_path = temp_dir_path / "output"
        output_dir_path.mkdir()

        # Save the uploaded file to the temporary directory
        try:
            with open(input_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logger.info(f"Uploaded file saved to: {input_file_path}")
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to save uploaded file.")
        finally:
            file.file.close()

        # Use the existing CLI logic to process the file
        # The CLI logic handles both PDF and Office files (with LibreOffice)
        cli_args = [str(input_file_path), "-o", str(output_dir_path)]

        try:
            return_code = cli_main(cli_args)
            if return_code != 0:
                logger.error(f"File conversion failed with return code {return_code}.")
                raise HTTPException(status_code=500, detail="File conversion process failed.")
        except Exception as e:
            logger.error(f"An exception occurred during file conversion: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred during conversion: {str(e)}")

        # Check if output was actually created
        # The CLI creates a directory with a standard name inside the output dir.
        # Let's find the generated markdown file. The converter saves it as 'processed_document.md'.
        markdown_files = list(output_dir_path.glob("**/processed_document.md"))
        if not markdown_files:
            logger.error(f"Conversion succeeded, but the output markdown file is missing.")
            raise HTTPException(status_code=500, detail="Conversion failed to produce an output file.")

        # Zip the contents of the output directory
        zip_file_path = temp_dir_path / "converted_output.zip"
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for entry in output_dir_path.rglob('*'):
                zipf.write(entry, entry.relative_to(output_dir_path))

        logger.info(f"Successfully created zip archive at {zip_file_path}")

        # Return the zip file
        return FileResponse(
            path=zip_file_path,
            media_type='application/zip',
            filename=f"{input_file_path.stem}_converted.zip"
        )

@app.get("/")
def read_root():
    return {"message": "Welcome to the Docling Markdown Conversion Server"}
