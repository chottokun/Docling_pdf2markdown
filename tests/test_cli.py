import pytest
from pathlib import Path
from unittest.mock import patch

from docling_lib.cli import main, entry_point

# --- Test Cases for main() ---

@patch('docling_lib.cli.process_pdf')
def test_main_happy_path(mock_process_pdf, tmp_path, pdf_downloader):
    """
    Given: Valid CLI arguments.
    When: main() is called.
    Then: It should call the core process_pdf function with the correct arguments.
    """
    pdf_path = pdf_downloader("https://arxiv.org/pdf/1706.03762.pdf")
    output_dir = tmp_path / "cli_output"
    mock_process_pdf.return_value = output_dir / "processed.md" # Simulate success

    result = main([str(pdf_path), "--output-dir", str(output_dir)])

    assert result == 0
    mock_process_pdf.assert_called_once_with(pdf_path, output_dir)

def test_main_missing_pdf_argument(capsys):
    """
    Given: CLI arguments without the required PDF file.
    When: main() is called.
    Then: It should exit with a status code 2.
    """
    with pytest.raises(SystemExit) as e:
        main([])
    assert e.value.code == 2
    captured = capsys.readouterr()
    assert "the following arguments are required: input_file" in captured.err

@patch('docling_lib.cli.process_pdf', return_value=None)
def test_main_processing_fails(mock_process_pdf, tmp_path, caplog, pdf_downloader):
    """
    Given: The core processing function fails (returns None).
    When: main() is called.
    Then: It should return an error code and log an error message.
    """
    pdf_path = pdf_downloader("https://arxiv.org/pdf/1706.03762.pdf")
    result = main([str(pdf_path), "-o", str(tmp_path)])
    assert result == 1
    assert "Workflow failed" in caplog.text

# --- Tests for entry_point() ---

@patch('docling_lib.cli.sys')
@patch('docling_lib.cli.main')
def test_entry_point_success(mock_main, mock_sys):
    mock_main.return_value = 0
    entry_point()
    mock_main.assert_called_once_with()
    mock_sys.exit.assert_called_once_with(0)

@patch('docling_lib.cli.sys')
@patch('docling_lib.cli.main', side_effect=SystemExit(2))
def test_entry_point_system_exit(mock_main, mock_sys):
    entry_point()
    mock_main.assert_called_once_with()
    mock_sys.exit.assert_called_once_with(2)

@patch('docling_lib.cli.logger')
@patch('docling_lib.cli.sys')
@patch('docling_lib.cli.main', side_effect=Exception("Unexpected Error"))
def test_entry_point_unexpected_exception(mock_main, mock_sys, mock_logger):
    entry_point()
    mock_main.assert_called_once_with()
    mock_logger.exception.assert_called_once()
    mock_sys.exit.assert_called_once_with(1)

@pytest.mark.parametrize("file_extension", ["docx", "pptx", "xlsx"])
@patch('docling_lib.cli.subprocess.run')
@patch('docling_lib.cli.process_pdf')
def test_main_office_input_happy_path(mock_process_pdf, mock_subprocess_run, tmp_path, file_extension):
    """
    Given: An Office file (.docx, .pptx, .xlsx) as input.
    When: main() is called.
    Then: It should convert the file to a temporary PDF and call process_pdf.
    """
    input_filename = f"test.{file_extension}"
    input_path = tmp_path / input_filename
    input_path.touch()
    output_dir = tmp_path / "cli_output"

    mock_subprocess_run.return_value.returncode = 0
    mock_process_pdf.return_value = output_dir / "processed.md"

    with patch('docling_lib.cli.tempfile.TemporaryDirectory', return_value=tmp_path):
        pdf_in_temp = tmp_path / f"{input_path.stem}.pdf"
        pdf_in_temp.touch()

        result = main([str(input_path), "--output-dir", str(output_dir)])

    assert result == 0

    mock_subprocess_run.assert_called_once()
    args, kwargs = mock_subprocess_run.call_args
    assert "libreoffice" in args[0]
    assert str(input_path) in args[0]

    mock_process_pdf.assert_called_once()
    call_args, _ = mock_process_pdf.call_args
    processed_path = call_args[0]
    assert processed_path.suffix == ".pdf"
    assert processed_path.name.startswith(input_path.stem)
    assert call_args[1] == output_dir