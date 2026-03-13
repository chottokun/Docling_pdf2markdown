import logging

# --- Default Constants ---
# MD_OUTPUT_NAME: The default name for the generated Markdown file.
MD_OUTPUT_NAME = "processed_document.md"

# IMAGE_DIR_NAME: The default sub-directory name for extracted images.
IMAGE_DIR_NAME = "images"

# IMAGE_RESOLUTION_SCALE: Default scale factor for image resolution.
# Higher values (e.g., 2.0) provide better quality for OCR/downstream tasks,
# but result in larger file sizes.
IMAGE_RESOLUTION_SCALE = 2.0

def setup_logging():
    """
    Configures the global logging behavior for the library, CLI, and server.

    Standardizes the log level and format across all components.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
