import pytest
import requests
from pathlib import Path

TEST_DATA_DIR = Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def pdf_downloader():
    """
    A pytest fixture that provides a function to download test PDFs.
    The downloaded files are cached in the 'test_data' directory to avoid
    re-downloading during the same test session.
    """
    TEST_DATA_DIR.mkdir(exist_ok=True)

    def _downloader(url: str) -> Path:
        filename = url.split("/")[-1]
        pdf_path = TEST_DATA_DIR / filename

        if not pdf_path.exists():
            response = requests.get(url)
            response.raise_for_status()
            with open(pdf_path, "wb") as f:
                f.write(response.content)

        return pdf_path

    return _downloader
