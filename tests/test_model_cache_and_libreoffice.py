import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from docling_lib.converter import (
    DocumentConversionOptions,
    PDFConverter,
    is_libreoffice_available,
)
from scripts.download_models import (
    download_selected_models,
    format_bytes,
    get_dir_size,
    parse_args,
)


def test_parse_args_defaults():
    args = parse_args([])
    assert args.output_dir == Path(".cache_models")
    assert args.all is False
    assert args.models is None
    assert args.force is False
    assert args.quiet is False


def test_parse_args_all_and_custom_dir():
    args = parse_args(["--all", "-o", "custom_models_dir", "--force", "--quiet"])
    assert args.output_dir == Path("custom_models_dir")
    assert args.all is True
    assert args.force is True
    assert args.quiet is True


def test_parse_args_specific_models():
    args = parse_args(["-m", "layout", "tableformer", "rapidocr"])
    assert args.models == ["layout", "tableformer", "rapidocr"]


def test_format_bytes():
    assert format_bytes(500) == "500.00 B"
    assert format_bytes(1024) == "1.00 KB"
    assert format_bytes(1024 * 1024 * 5) == "5.00 MB"
    assert format_bytes(1024 * 1024 * 1024 * 2) == "2.00 GB"


def test_get_dir_size():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Empty directory
        size, count = get_dir_size(tmp_path)
        assert size == 0
        assert count == 0

        # Create files
        f1 = tmp_path / "test1.bin"
        f1.write_bytes(b"12345")
        f2 = tmp_path / "sub" / "test2.bin"
        f2.parent.mkdir(parents=True)
        f2.write_bytes(b"1234567890")

        size, count = get_dir_size(tmp_path)
        assert size == 15
        assert count == 2


@patch("docling.utils.model_downloader.download_models")
def test_download_selected_models(mock_download_models):
    mock_download_models.return_value = Path("/tmp/mock_models")
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir) / "models"
        res = download_selected_models(
            output_dir=out_dir,
            selected_models=["layout", "rapidocr"],
            force=True,
            progress=False,
        )
        assert res == Path("/tmp/mock_models")
        assert mock_download_models.called
        kwargs = mock_download_models.call_args.kwargs
        assert kwargs["output_dir"] == out_dir.resolve()
        assert kwargs["with_layout"] is True
        assert kwargs["with_rapidocr"] is True
        assert kwargs["with_tableformer"] is False
        assert kwargs["force"] is True


def test_parse_args_profiles():
    for profile_name in ["standard", "full", "minimal", "ocr", "chart", "formula"]:
        args = parse_args(["--profile", profile_name])
        assert args.profile == profile_name


def test_parse_args_verify_offline():
    args = parse_args(["--verify-offline", "-o", "my_models"])
    assert args.verify_offline is True
    assert args.output_dir == Path("my_models")


@patch("docling.document_converter.DocumentConverter")
def test_verify_offline_mode_success(mock_doc_converter):
    from scripts.download_models import verify_offline_mode
    with tempfile.TemporaryDirectory() as tmpdir:
        res = verify_offline_mode(Path(tmpdir))
        assert res is True
        assert os.environ.get("HF_HUB_OFFLINE") == "1"
        assert os.environ.get("TRANSFORMERS_OFFLINE") == "1"


@patch("docling.document_converter.DocumentConverter", side_effect=RuntimeError("Offline model not found"))
def test_verify_offline_mode_failure(mock_doc_converter):
    from scripts.download_models import verify_offline_mode
    with tempfile.TemporaryDirectory() as tmpdir:
        res = verify_offline_mode(Path(tmpdir))
        assert res is False


def test_is_libreoffice_available():
    # Test boolean response
    available = is_libreoffice_available()
    assert isinstance(available, bool)

    with patch("shutil.which", return_value="/usr/bin/libreoffice"):
        assert is_libreoffice_available() is True

    with patch("shutil.which", return_value=None):
        assert is_libreoffice_available() is False


def test_document_conversion_options_artifacts_path():
    opts = DocumentConversionOptions(artifacts_path="/custom/path/models")
    assert str(opts.artifacts_path) == "/custom/path/models"


@patch("docling_lib.converter.DocumentConverter")
def test_pdf_converter_sets_artifacts_path(mock_doc_converter):
    opts = DocumentConversionOptions(artifacts_path="/my/cached/models")
    converter = PDFConverter(options=opts)
    assert converter.options.artifacts_path == "/my/cached/models"
    assert mock_doc_converter.called


@patch("docling_lib.converter.DocumentConverter")
def test_pipeline_options_matrix_model_usage(mock_doc_converter):
    """
    Critically test that toggling features (OCR, Formula, Code, Chart)
    strictly propagates to PdfPipelineOptions so that unnecessary models are not loaded.
    """
    from docling.datamodel.base_models import InputFormat

    # Case 1: Minimal - OCR, formula, code, chart disabled
    opts_minimal = DocumentConversionOptions(
        do_ocr=False,
        do_formula=False,
        do_code=False,
        do_chart=False,
        artifacts_path="/cache/minimal",
    )
    converter1 = PDFConverter(options=opts_minimal)
    call_kwargs1 = mock_doc_converter.call_args.kwargs
    format_opts1 = call_kwargs1["format_options"]
    pdf_opts1 = format_opts1[InputFormat.PDF].pipeline_options

    assert pdf_opts1.do_ocr is False
    assert pdf_opts1.do_formula_enrichment is False
    assert pdf_opts1.do_code_enrichment is False
    assert pdf_opts1.do_chart_extraction is False
    assert str(pdf_opts1.artifacts_path) == "/cache/minimal"

    # Case 2: Standard OCR + Formula
    opts_standard = DocumentConversionOptions(
        do_ocr=True,
        do_formula=True,
        do_code=False,
        do_chart=False,
        artifacts_path="/cache/standard",
    )
    converter2 = PDFConverter(options=opts_standard)
    call_kwargs2 = mock_doc_converter.call_args.kwargs
    format_opts2 = call_kwargs2["format_options"]
    pdf_opts2 = format_opts2[InputFormat.PDF].pipeline_options

    assert pdf_opts2.do_ocr is True
    assert pdf_opts2.do_formula_enrichment is True
    assert pdf_opts2.do_code_enrichment is False
    assert pdf_opts2.do_chart_extraction is False
    assert str(pdf_opts2.artifacts_path) == "/cache/standard"

    # Case 3: Full Features (Code + Chart + OCR + Formula)
    opts_full = DocumentConversionOptions(
        do_ocr=True,
        do_formula=True,
        do_code=True,
        do_chart=True,
        artifacts_path="/cache/full",
    )
    converter3 = PDFConverter(options=opts_full)
    call_kwargs3 = mock_doc_converter.call_args.kwargs
    format_opts3 = call_kwargs3["format_options"]
    pdf_opts3 = format_opts3[InputFormat.PDF].pipeline_options

    assert pdf_opts3.do_ocr is True
    assert pdf_opts3.do_formula_enrichment is True
    assert pdf_opts3.do_code_enrichment is True
    assert pdf_opts3.do_chart_extraction is True
    assert str(pdf_opts3.artifacts_path) == "/cache/full"
