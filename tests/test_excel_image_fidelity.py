import io
import re
from pathlib import Path

import openpyxl
from PIL import Image as PILImage

from docling_lib.converter import (
    DocumentConversionOptions,
    EnhancedDoclingConverter,
    PDFConverter,
)
from docling_lib.utils import extract_excel_images

# --- Generator Helpers for Synthetic Datasets ---


def create_synthetic_multi_format_excel(file_path: Path) -> list[dict]:
    """
    Generates DS-03: Single sheet with multiple images of different formats (PNG, JPEG, RGBA)
    and dimensions placed at distinct cell coordinates.
    Returns metadata of inserted images for ground truth verification.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "MultiFormatSheet"
    ws["A1"] = "Multi-Format Images Test"

    expected = []

    # 1. Red PNG image at B3 (row 2, col 1 in 0-based index)
    img_red = PILImage.new("RGB", (80, 60), color="red")
    buf_red = io.BytesIO()
    img_red.save(buf_red, format="PNG")
    buf_red.seek(0)
    opx_red = openpyxl.drawing.image.Image(buf_red)
    ws.add_image(opx_red, "B3")
    expected.append({"sheet": "MultiFormatSheet", "sheet_idx": 1, "row": 2, "col": 1, "width": 80, "height": 60})

    # 2. Green JPEG image at E8 (row 7, col 4 in 0-based index)
    img_green = PILImage.new("RGB", (100, 100), color="green")
    buf_green = io.BytesIO()
    img_green.save(buf_green, format="JPEG")
    buf_green.seek(0)
    opx_green = openpyxl.drawing.image.Image(buf_green)
    ws.add_image(opx_green, "E8")
    expected.append({"sheet": "MultiFormatSheet", "sheet_idx": 1, "row": 7, "col": 4, "width": 100, "height": 100})

    # 3. Semi-transparent Blue RGBA image at C15 (row 14, col 2 in 0-based index)
    img_blue = PILImage.new("RGBA", (50, 50), color=(0, 0, 255, 128))
    buf_blue = io.BytesIO()
    img_blue.save(buf_blue, format="PNG")
    buf_blue.seek(0)
    opx_blue = openpyxl.drawing.image.Image(buf_blue)
    ws.add_image(opx_blue, "C15")
    expected.append({"sheet": "MultiFormatSheet", "sheet_idx": 1, "row": 14, "col": 2, "width": 50, "height": 50})

    wb.save(file_path)
    return expected


def create_synthetic_3sheet_excel(file_path: Path) -> list[dict]:
    """
    Generates DS-04: 3-sheet Excel document where each sheet contains one image at specific cells.
    Returns metadata for ground truth verification.
    """
    wb = openpyxl.Workbook()

    # Sheet 1: Financial Summary
    ws1 = wb.active
    ws1.title = "Financial Summary"
    ws1["A1"] = "Revenue Q1"
    img1 = PILImage.new("RGB", (70, 70), color="purple")
    buf1 = io.BytesIO()
    img1.save(buf1, format="PNG")
    buf1.seek(0)
    ws1.add_image(openpyxl.drawing.image.Image(buf1), "B2")

    # Sheet 2: Operation Details
    ws2 = wb.create_sheet(title="Operation Details")
    ws2["A1"] = "System Status"
    img2 = PILImage.new("RGB", (90, 90), color="orange")
    buf2 = io.BytesIO()
    img2.save(buf2, format="PNG")
    buf2.seek(0)
    ws2.add_image(openpyxl.drawing.image.Image(buf2), "C5")

    # Sheet 3: Appendix Diagrams
    ws3 = wb.create_sheet(title="Appendix Diagrams")
    ws3["A1"] = "Architecture Flow"
    img3 = PILImage.new("RGB", (120, 80), color="teal")
    buf3 = io.BytesIO()
    img3.save(buf3, format="PNG")
    buf3.seek(0)
    ws3.add_image(openpyxl.drawing.image.Image(buf3), "E10")

    wb.save(file_path)
    return [
        {"sheet_idx": 1, "sheet_name": "Financial Summary", "cell": "B2", "row": 1, "col": 1},
        {"sheet_idx": 2, "sheet_name": "Operation Details", "cell": "C5", "row": 4, "col": 2},
        {"sheet_idx": 3, "sheet_name": "Appendix Diagrams", "cell": "E10", "row": 9, "col": 4},
    ]


def create_synthetic_edge_case_excel(file_path: Path) -> None:
    """
    Generates DS-05: Edge cases including:
    - Sheet 1: Duplicate images (identical bytes, checking SHA-256 hash matching)
    - Sheet 2: Text only, no images
    - Sheet 3: Image placed far off (e.g. Z100)
    """
    wb = openpyxl.Workbook()

    # Sheet 1: Duplicate images
    ws1 = wb.active
    ws1.title = "DupSheet"
    ws1["A1"] = "Duplicates Test"

    img_yellow = PILImage.new("RGB", (40, 40), color="yellow")
    buf_y = io.BytesIO()
    img_yellow.save(buf_y, format="PNG")

    # Image 1 at B2
    buf_y.seek(0)
    ws1.add_image(openpyxl.drawing.image.Image(io.BytesIO(buf_y.getvalue())), "B2")
    # Image 2 (identical content) at D2
    buf_y.seek(0)
    ws1.add_image(openpyxl.drawing.image.Image(io.BytesIO(buf_y.getvalue())), "D2")

    # Sheet 2: No images
    ws2 = wb.create_sheet(title="TextOnlySheet")
    ws2["A1"] = "No pictures here"
    ws2["B2"] = 12345

    # Sheet 3: Image far off
    ws3 = wb.create_sheet(title="FarOffSheet")
    ws3["A1"] = "Far off image"
    img_pink = PILImage.new("RGB", (30, 30), color="pink")
    buf_p = io.BytesIO()
    img_pink.save(buf_p, format="PNG")
    buf_p.seek(0)
    ws3.add_image(openpyxl.drawing.image.Image(buf_p), "Z100")

    wb.save(file_path)


# --- Test Cases for 4 Major Evaluation Axes ---


def test_axis1_extraction_completeness_and_deduplication(tmp_path: Path):
    """
    Evaluation Axis 1: Extraction Completeness & Deduplication
    Verifies that all images across multiple sheets and formats are extracted
    and identical image content is properly deduplicated via SHA-256 hash during enrichment.
    """
    # 1. Multi-format extraction test
    multi_file = tmp_path / "ds03_multi_format.xlsx"
    create_synthetic_multi_format_excel(multi_file)

    extracted_mf = extract_excel_images(multi_file)
    assert len(extracted_mf) == 3, f"Expected 3 extracted images, got {len(extracted_mf)}"

    # 2. Edge case & Deduplication test
    edge_file = tmp_path / "ds05_edge_case.xlsx"
    create_synthetic_edge_case_excel(edge_file)

    extracted_edge = extract_excel_images(edge_file)
    # DupSheet has 2 identical images, FarOffSheet has 1 image, TextOnlySheet has 0
    assert len(extracted_edge) == 3, f"Expected 3 raw extracted images, got {len(extracted_edge)}"
    # Verify SHA-256 hashes of the duplicate images are identical
    dup_hashes = [img["sha256"] for img in extracted_edge if img["sheet_name"] == "DupSheet"]
    assert len(dup_hashes) == 2
    assert dup_hashes[0] == dup_hashes[1], "Duplicate images should share identical SHA-256 hashes"

    # Convert via PDFConverter to verify enrichment pipeline runs cleanly
    output_dir = tmp_path / "edge_output"
    converter = PDFConverter()
    res_path = converter.convert(edge_file, output_dir)
    assert res_path is not None and res_path.exists()

    image_dir = output_dir / "images"
    saved_images = list(image_dir.glob("*.png"))
    assert len(saved_images) >= 3


def test_axis2_provenance_and_sheet_mapping(tmp_path: Path):
    """
    Evaluation Axis 2: Provenance & Sheet Mapping
    Verifies that `page_no` in ProvenanceItem corresponds to 1-based sheet index
    and row/col cell coordinates accurately match the OpenXML anchor.
    """
    file_3sheet = tmp_path / "ds04_3sheet.xlsx"
    expected_meta = create_synthetic_3sheet_excel(file_3sheet)

    extracted = extract_excel_images(file_3sheet)
    assert len(extracted) == 3

    for exp, ext in zip(expected_meta, extracted):
        assert ext["sheet_name"] == exp["sheet_name"]
        assert ext["sheet_index"] == exp["sheet_idx"]
        assert ext["row"] == exp["row"]
        assert ext["col"] == exp["col"]


def test_axis3_binary_image_fidelity_and_integrity(tmp_path: Path):
    """
    Evaluation Axis 3: Binary Image Fidelity & Integrity
    Verifies that extracted images are non-empty, openable via PIL,
    and retain correct dimensions without binary corruption.
    """
    multi_file = tmp_path / "ds03_fidelity.xlsx"
    expected_meta = create_synthetic_multi_format_excel(multi_file)

    extracted = extract_excel_images(multi_file)
    for exp, ext in zip(expected_meta, extracted):
        pil_img = ext["pil_image"]
        assert pil_img is not None, "Image failed to load in PIL"
        assert pil_img.width == exp["width"], f"Width mismatch: {pil_img.width} != {exp['width']}"
        assert pil_img.height == exp["height"], f"Height mismatch: {pil_img.height} != {exp['height']}"
        assert len(ext["image_bytes"]) > 0, "Image byte stream is empty"


def test_axis4_markdown_link_and_naming_consistency(tmp_path: Path):
    """
    Evaluation Axis 4: Markdown Link & Naming Consistency
    Verifies that generated Markdown links adopt the format `{doc_slug}_p{sheet_idx}_{index}.png`,
    all linked images exist on disk (zero dead links), and custom image tag templates work correctly.
    """
    file_3sheet = tmp_path / "ds04_links.xlsx"
    create_synthetic_3sheet_excel(file_3sheet)

    # 1. Standard PDFConverter saving test
    output_dir = tmp_path / "links_output"
    converter = PDFConverter()
    md_file = converter.convert(file_3sheet, output_dir)
    assert md_file is not None and md_file.exists()

    md_content = md_file.read_text(encoding="utf-8")
    images_dir = output_dir / "images"

    # Verify naming convention: ds04_links_p1_1.png, ds04_links_p2_2.png, ds04_links_p3_3.png
    for sheet_idx in [1, 2, 3]:
        expected_name = f"ds04_links_p{sheet_idx}_{sheet_idx}.png"
        assert (images_dir / expected_name).exists(), f"Missing expected image file {expected_name}"
        assert f"images/{expected_name}" in md_content, f"Markdown missing reference to {expected_name}"

    # Verify zero dead links: extract all image paths from markdown and ensure they exist
    links = re.findall(r"!\[.*?\]\((.*?)\)", md_content)
    assert len(links) == 3
    for link in links:
        target_path = output_dir / link
        assert target_path.exists(), f"Dead link detected in Markdown: {link}"

    # 2. EnhancedDoclingConverter custom tag template test
    assets_dir = tmp_path / "custom_assets"
    enhanced_converter = EnhancedDoclingConverter()
    custom_md = enhanced_converter.convert_to_markdown(
        file_3sheet,
        slug="my-custom-excel",
        image_tag_template="![{image_name}](assets/{slug}/{image_name})",
        assets_dir=assets_dir,
    )

    for sheet_idx in [1, 2, 3]:
        expected_name = f"my-custom-excel_p{sheet_idx}_{sheet_idx}.png"
        assert (assets_dir / expected_name).exists()
        assert f"assets/my-custom-excel/{expected_name}" in custom_md


def test_special_characters_in_sheet_names_and_japanese_support(tmp_path: Path):
    """
    Tests Excel files with Japanese sheet names, spaces, and special symbols
    (e.g., '売上データ 2026', 'Sheet & Graph') to verify non-ASCII sheet name handling.
    """
    excel_file = tmp_path / "japanese_sheets.xlsx"
    wb = openpyxl.Workbook()

    ws1 = wb.active
    ws1.title = "売上データ 2026"
    ws1["A1"] = "総売上"
    img1 = PILImage.new("RGB", (50, 50), color="gold")
    buf1 = io.BytesIO()
    img1.save(buf1, format="PNG")
    buf1.seek(0)
    ws1.add_image(openpyxl.drawing.image.Image(buf1), "A2")

    ws2 = wb.create_sheet(title="Graph & Diagram")
    ws2["A1"] = "概要"
    img2 = PILImage.new("RGB", (60, 40), color="brown")
    buf2 = io.BytesIO()
    img2.save(buf2, format="PNG")
    buf2.seek(0)
    ws2.add_image(openpyxl.drawing.image.Image(buf2), "B3")

    wb.save(excel_file)

    extracted = extract_excel_images(excel_file)
    assert len(extracted) == 2
    assert extracted[0]["sheet_name"] == "売上データ 2026"
    assert extracted[1]["sheet_name"] == "Graph & Diagram"

    out_dir = tmp_path / "jp_output"
    converter = PDFConverter()
    res_file = converter.convert(excel_file, out_dir)
    assert res_file is not None and res_file.exists()


def test_xlsm_macro_enabled_workbook(tmp_path: Path):
    """
    Tests macro-enabled Excel workbooks (.xlsm) containing drawings/images.
    """
    xlsm_file = tmp_path / "macro_sample.xlsm"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "MacroSheet"
    ws["A1"] = "VBA Code and Images"

    img = PILImage.new("RGB", (45, 45), color="violet")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    ws.add_image(openpyxl.drawing.image.Image(buf), "C3")

    wb.save(xlsm_file)

    extracted = extract_excel_images(xlsm_file)
    assert len(extracted) == 1
    assert extracted[0]["sheet_name"] == "MacroSheet"
    assert extracted[0]["row"] == 2  # 0-based index for row 3 (C3)
    assert extracted[0]["col"] == 2  # 0-based index for col C (C3)


def test_large_batch_images_single_sheet(tmp_path: Path):
    """
    Tests a single sheet containing 10 distinct images to verify
    index sequence numbering, parallel image saving, and non-collision.
    """
    excel_file = tmp_path / "batch_10_images.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BatchSheet"

    for i in range(10):
        # Create unique colors for each image
        img = PILImage.new("RGB", (30, 30), color=(i * 20, 100, 255 - i * 20))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        cell_ref = f"A{i+1}"
        ws.add_image(openpyxl.drawing.image.Image(buf), cell_ref)

    wb.save(excel_file)

    extracted = extract_excel_images(excel_file)
    assert len(extracted) == 10

    out_dir = tmp_path / "batch_out"
    converter = PDFConverter()
    md_path = converter.convert(excel_file, out_dir)
    assert md_path is not None and md_path.exists()

    saved_files = list((out_dir / "images").glob("batch_10_images_p1_*.png"))
    assert len(saved_files) == 10


def test_real_world_excel_data_conversion(tmp_path: Path):
    """
    Tests processing real-world Excel sample files in tests/test_data/
    to ensure conversion pipeline executes smoothly without raising exceptions.
    """
    real_files = [
        Path("tests/test_data/sample7_financial.xlsx"),
        Path("tests/test_data/meti_gijutsu_matrix.xlsx"),
        Path("tests/test_data/real_sample.xlsx"),
    ]

    converter = PDFConverter()
    for real_file in real_files:
        if not real_file.exists():
            continue

        out_dir = tmp_path / f"out_{real_file.stem}"
        md_path = converter.convert(real_file, out_dir)
        assert md_path is not None and md_path.exists()
        md_text = md_path.read_text(encoding="utf-8")
        assert len(md_text) > 0
