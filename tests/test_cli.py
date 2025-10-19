import pytest
from pathlib import Path
from unittest.mock import patch

from src.docling_lib.cli import main, entry_point

# --- Test Fixtures ---
TEST_DATA_DIR = Path(__file__).parent / "test_data"
VALID_PDF = TEST_DATA_DIR / "1706.03762.pdf"

# --- Test Cases for main() ---

@patch('src.docling_lib.cli.refine_markdown')
@patch('src.docling_lib.cli.extract_markdown')
def test_main_happy_path(mock_extract, mock_refine, tmp_path, capsys):
    output_dir = tmp_path / "cli_output"
    dummy_md_path = output_dir / "dummy.md"
    mock_extract.return_value = dummy_md_path

    result = main([str(VALID_PDF), "--output-dir", str(output_dir)])

    assert result == 0
    mock_extract.assert_called_once_with(VALID_PDF, output_dir)
    mock_refine.assert_called_once_with(dummy_md_path)
    captured = capsys.readouterr()
    assert "Workflow completed successfully!" in captured.out

def test_main_missing_pdf_argument(capsys):
    with pytest.raises(SystemExit) as e:
        main([])
    assert e.value.code == 2
    captured = capsys.readouterr()
    assert "the following arguments are required: pdf_file" in captured.err

@patch('src.docling_lib.cli.extract_markdown', return_value=None)
def test_main_extraction_fails(mock_extract, tmp_path, capsys):
    output_dir = tmp_path
    result = main([str(VALID_PDF), "-o", str(output_dir)])
    assert result == 1
    captured = capsys.readouterr()
    assert "Error during extraction step." in captured.out

@patch('src.docling_lib.cli.refine_markdown', return_value=None)
@patch('src.docling_lib.cli.extract_markdown')
def test_main_refinement_fails(mock_extract, mock_refine, tmp_path, capsys):
    dummy_md_path = tmp_path / "dummy.md"
    mock_extract.return_value = dummy_md_path
    output_dir = tmp_path
    result = main([str(VALID_PDF), "-o", str(output_dir)])
    assert result == 1
    captured = capsys.readouterr()
    assert "Error during refinement step." in captured.out

# --- Tests for entry_point() ---

@patch('src.docling_lib.cli.sys')
@patch('src.docling_lib.cli.main')
def test_entry_point_success(mock_main, mock_sys):
    mock_main.return_value = 0
    entry_point()
    mock_main.assert_called_once_with()
    mock_sys.exit.assert_called_once_with(0)

@patch('src.docling_lib.cli.sys')
@patch('src.docling_lib.cli.main', side_effect=SystemExit(2))
def test_entry_point_system_exit(mock_main, mock_sys):
    entry_point()
    mock_main.assert_called_once_with()
    mock_sys.exit.assert_called_once_with(2)

@patch('src.docling_lib.cli.logger')
@patch('src.docling_lib.cli.sys')
@patch('src.docling_lib.cli.main', side_effect=Exception("Unexpected Error"))
def test_entry_point_unexpected_exception(mock_main, mock_sys, mock_logger):
    entry_point()
    mock_main.assert_called_once_with()
    mock_logger.exception.assert_called_once()
    mock_sys.exit.assert_called_once_with(1)