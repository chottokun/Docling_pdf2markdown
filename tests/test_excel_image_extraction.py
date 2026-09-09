import io
from pathlib import Path
import openpyxl
from PIL import Image as PILImage
import pytest

from docling_lib.converter import PDFConverter, DocumentConversionOptions, EnhancedDoclingConverter
from docling_lib.utils import extract_excel_images


def create_test_excel_with_image(file_path: Path) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"] = "Sample Title"
    ws["A2"] = "Sample Data"

    img = PILImage.new("RGB", (80, 80), color="blue")
    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    img_buf.seek(0)

    opx_img = openpyxl.drawing.image.Image(img_buf)
    ws.add_image(opx_img, "C2")

    wb.save(file_path)


def test_extract_excel_images(tmp_path: Path):
    excel_file = tmp_path / "test_extract.xlsx"
    create_test_excel_with_image(excel_file)

    extracted = extract_excel_images(excel_file)
    assert len(extracted) >= 1
    item = extracted[0]
    assert "filename" in item
    assert "image_bytes" in item
    assert item["pil_image"] is not None
    assert item["pil_image"].size == (80, 80)


def test_extract_excel_images_invalid_file(tmp_path: Path):
    dummy_file = tmp_path / "not_an_excel.xlsx"
    dummy_file.write_text("not a zip archive", encoding="utf-8")

    extracted = extract_excel_images(dummy_file)
    assert extracted == []


def test_excel_image_enrichment_and_conversion(tmp_path: Path):
    excel_file = tmp_path / "test_enrich.xlsx"
    create_test_excel_with_image(excel_file)

    output_dir = tmp_path / "output"
    options = DocumentConversionOptions(
        image_dir_name="images",
        md_output_name="output.md",
    )

    converter = PDFConverter(options=options)
    result_path = converter.convert(excel_file, output_dir)
    assert result_path is not None
    assert result_path.exists()

    md_content = result_path.read_text(encoding="utf-8")
    assert "Sample Title" in md_content
    # Check that image tag or reference is present
    image_dir = output_dir / "images"
    assert image_dir.exists()
    saved_images = list(image_dir.glob("picture_*.png"))
    assert len(saved_images) >= 1


def test_enhanced_docling_converter_excel_images(tmp_path: Path):
    excel_file = tmp_path / "test_enhanced.xlsx"
    create_test_excel_with_image(excel_file)

    assets_dir = tmp_path / "assets"
    enhanced_converter = EnhancedDoclingConverter()
    markdown_output = enhanced_converter.convert_to_markdown(
        excel_file,
        slug="custom-slug",
        image_tag_template="![{image_name}](assets/{slug}/{image_name})",
        assets_dir=assets_dir,
    )

    assert "Sample Title" in markdown_output
    assert "assets/custom-slug/picture_1.png" in markdown_output
    saved_images = list(assets_dir.glob("picture_*.png"))
    assert len(saved_images) >= 1
