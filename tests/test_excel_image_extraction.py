import io
from pathlib import Path

import openpyxl
from PIL import Image as PILImage

from docling_lib.converter import (
    DocumentConversionOptions,
    EnhancedDoclingConverter,
    PDFConverter,
)
from docling_lib.utils import extract_excel_images


def create_multi_sheet_excel_with_images(file_path: Path) -> None:
    wb = openpyxl.Workbook()

    # Sheet 1
    ws1 = wb.active
    ws1.title = "FirstSheet"
    ws1["A1"] = "Sheet 1 Title"
    img1 = PILImage.new("RGB", (60, 60), color="red")
    buf1 = io.BytesIO()
    img1.save(buf1, format="PNG")
    buf1.seek(0)
    opx_img1 = openpyxl.drawing.image.Image(buf1)
    ws1.add_image(opx_img1, "B5")

    # Sheet 2
    ws2 = wb.create_sheet(title="SecondSheet")
    ws2["A1"] = "Sheet 2 Title"
    img2 = PILImage.new("RGB", (60, 60), color="blue")
    buf2 = io.BytesIO()
    img2.save(buf2, format="PNG")
    buf2.seek(0)
    opx_img2 = openpyxl.drawing.image.Image(buf2)
    ws2.add_image(opx_img2, "D10")

    wb.save(file_path)


def test_extract_excel_images_multi_sheet(tmp_path: Path):
    excel_file = tmp_path / "multi_sheet.xlsx"
    create_multi_sheet_excel_with_images(excel_file)

    extracted = extract_excel_images(excel_file)
    assert len(extracted) >= 2

    sheet1_imgs = [item for item in extracted if item["sheet_name"] == "FirstSheet"]
    sheet2_imgs = [item for item in extracted if item["sheet_name"] == "SecondSheet"]

    assert len(sheet1_imgs) >= 1
    assert sheet1_imgs[0]["sheet_index"] == 1
    assert sheet1_imgs[0]["row"] == 4  # 0-based index for row 5 (B5)
    assert sheet1_imgs[0]["col"] == 1  # 0-based index for col B (B5)

    assert len(sheet2_imgs) >= 1
    assert sheet2_imgs[0]["sheet_index"] == 2
    assert sheet2_imgs[0]["row"] == 9  # 0-based index for row 10 (D10)
    assert sheet2_imgs[0]["col"] == 3  # 0-based index for col D (D10)


def test_sha256_deduplication(tmp_path: Path):
    excel_file = tmp_path / "dedup.xlsx"
    create_multi_sheet_excel_with_images(excel_file)

    extracted = extract_excel_images(excel_file)
    hashes = set(item["sha256"] for item in extracted)
    # The two images are red vs blue, so their hashes are distinct
    assert len(hashes) == len(extracted)


def test_extract_excel_images_invalid_file(tmp_path: Path):
    dummy_file = tmp_path / "not_an_excel.xlsx"
    dummy_file.write_text("not a zip archive", encoding="utf-8")

    extracted = extract_excel_images(dummy_file)
    assert extracted == []


def test_excel_image_enrichment_and_conversion(tmp_path: Path):
    excel_file = tmp_path / "test_enrich.xlsx"
    create_multi_sheet_excel_with_images(excel_file)

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
    assert "Sheet 1 Title" in md_content
    assert "![image](images/test_enrich_p1_1.png)" in md_content

    image_dir = output_dir / "images"
    assert image_dir.exists()
    saved_images = list(image_dir.glob("test_enrich_p*.png"))
    assert len(saved_images) >= 2


def test_enhanced_docling_converter_excel_images(tmp_path: Path):
    excel_file = tmp_path / "test_enhanced.xlsx"
    create_multi_sheet_excel_with_images(excel_file)

    assets_dir = tmp_path / "assets"
    enhanced_converter = EnhancedDoclingConverter()
    markdown_output = enhanced_converter.convert_to_markdown(
        excel_file,
        slug="custom-slug",
        image_tag_template="![{image_name}](assets/{slug}/{image_name})",
        assets_dir=assets_dir,
    )

    assert "Sheet 1 Title" in markdown_output
    assert "assets/custom-slug/custom-slug_p1_1.png" in markdown_output
    saved_images = list(assets_dir.glob("custom-slug_p*.png"))
    assert len(saved_images) >= 2
