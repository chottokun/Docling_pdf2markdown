# Docling Markdown Generator

Doclingを使って図を埋め込んだmarkdownに変換します。

This project provides a Python library and command-line tool to convert PDF and Microsoft Office files (.docx, .pptx, .xlsx) into Markdown documents with embedded, captioned figures. It leverages the `docling` library to extract content and intelligently format it.

## Features

- Extracts text, tables, and figures from PDF files.
- Supports conversion from Microsoft Office formats (.docx, .pptx, .xlsx) by leveraging LibreOffice.
- Converts tables into Markdown table format.
- Converts figures into HTML `<figure>` tags with associated captions.
- Provides a simple command-line interface (CLI) for easy use.
- Built with Test-Driven Development (TDD) for robustness.

## Prerequisites

To convert Microsoft Office files, **LibreOffice must be installed** on the system where this tool is run. The tool invokes the `libreoffice` command-line interface to perform the conversion to PDF.

Please see the official [LibreOffice installation instructions](https://www.libreoffice.org/get-help/install-howto/) for your operating system. On Debian/Ubuntu-based systems, it can typically be installed with:
```bash
sudo apt-get update && sudo apt-get install -y libreoffice
```

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
pdf2md_cli [INPUT_FILE] -o [OUTPUT_DIRECTORY]
```

**Arguments:**

- `INPUT_FILE`: (Required) The path to the input file. Supported formats are `.pdf`, `.docx`, `.pptx`, and `.xlsx`.
- `-o, --output-dir`: (Optional) The directory where the output files will be saved. Defaults to `output/`.

**Example:**

```bash
# For a PDF file
pdf2md_cli tests/test_data/1706.03762.pdf -o my_document

# For a Word document
pdf2md_cli my_report.docx -o my_report_markdown
```

This will create an output directory containing the processed `.md` file and an `images/` subdirectory with any extracted figures.

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

## Running with Docker

This project includes a `Dockerfile` and `docker-compose.yml` to run the application as a containerized server. This is the recommended way to run the application, as it includes all necessary dependencies, including LibreOffice.

### Building and Running the Server

1.  **Build and start the services:**
    ```bash
    docker-compose up --build
    ```
    This command will build the Docker image and start the FastAPI server. The server will be accessible at `http://localhost:8000`.

2.  **Using the API:**
    You can send a POST request to `http://localhost:8000/convert/` with a file to be converted. For example, using `curl`:
    ```bash
    curl -X POST -F "file=@/path/to/your/document.docx" http://localhost:8000/convert/ -o output.zip
    ```

### Docker Hub Rate Limiting

To avoid Docker Hub's rate limits, it is recommended to configure the Docker daemon to use a registry mirror. Google Cloud provides a mirror at `mirror.gcr.io`.

To configure the mirror, add the following to `/etc/docker/daemon.json`:
```json
{
  "registry-mirrors": [
    "https://mirror.gcr.io"
  ]
}
```
Then, restart the Docker daemon.

## License

The licenses of the third-party libraries used in this project are as follows:

- **docling**: MIT License
- **docling-core**: MIT License
- **pytest**: MIT License
- **pytest-cov**: MIT License

Please ensure compliance with all applicable licenses.