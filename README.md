# Docling Markdown Generator

This project provides a Python library and command-line tool to convert PDF files into Markdown documents with embedded, captioned figures. It leverages the `docling` library to extract content and intelligently format it.

## Features

- Extracts text and images from PDF files.
- Extracts text, tables, and figures from PDF files using a structured approach.
- Converts tables into Markdown table format.
- Converts figures into HTML `<figure>` tags with associated captions.
- Provides a simple command-line interface (CLI) for easy use.
- Built with Test-Driven Development (TDD) for robustness.

## Installation

This project uses `uv` for package management.

1.  **Create a virtual environment:**
    ```bash
    uv venv
    ```

2.  **Activate the environment:**
    ```bash
    # For macOS / Linux
    source .venv/bin/activate

    # For Windows
    .venv\Scripts\activate
    ```

3.  **Install the library:**
    The project is defined by `pyproject.toml`. To install it in editable mode along with its test dependencies, run:
    ```bash
    uv pip install -e ".[test]"
    ```

## Usage

The library can be used via its command-line interface.

```bash
pdf2md_cli [PDF_FILE] -o [OUTPUT_DIRECTORY]
```

**Arguments:**

- `PDF_FILE`: (Required) The path to the input PDF file.
- `-o, --output-dir`: (Optional) The directory where the output files will be saved. Defaults to `output/`.

**Example:**

```bash
pdf2md_cli tests/test_data/1706.03762.pdf -o my_document
```

This will create a `my_document/` directory containing the extracted `extracted_document.md` file, a refined `extracted_document_refined.md` file, and an `images/` subdirectory with the extracted figures.

## Development

This project follows a strict Test-Driven Development (TDD) methodology. All code is expected to be accompanied by tests.

-   **Run tests:**
    ```bash
    pytest
    ```
-   **Run tests with coverage:**
    ```bash
    pytest --cov=src
    ```

## License

The licenses of the third-party libraries used in this project are as follows:

- **docling**: MIT License
- **docling-core**: MIT License
- **pytest**: MIT License
- **pytest-cov**: MIT License

Please ensure compliance with all applicable licenses.