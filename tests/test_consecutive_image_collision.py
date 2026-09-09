from pathlib import Path

from docling_core.types.doc import (
    BoundingBox,
    CoordOrigin,
    DoclingDocument,
    ImageRef,
    ProvenanceItem,
)
from PIL import Image

from docling_lib.converter import DocumentConversionOptions, PDFConverter


def test_consecutive_processing_images_do_not_collide(tmp_path: Path):
    """
    同一出力ディレクトリ（output_dir）に対して複数の異なる文書を連続処理した際、
    画像ファイル名（{doc_slug}_p{page}_{index}.png）が重複せず、
    各文書の画像が上書きされずに両方保存されることを検証する。
    """
    output_dir = tmp_path / "shared_output"
    options = DocumentConversionOptions(
        image_dir_name="images",
        md_output_name="output.md",
    )
    converter = PDFConverter(options=options)

    # 1. Document A (doc_a) の作成
    doc_a = DoclingDocument(name="document_a")
    img_a = Image.new("RGB", (20, 20), color="red")
    bbox = BoundingBox.from_tuple((0, 0, 20, 20), origin=CoordOrigin.TOPLEFT)
    doc_a.add_picture(
        image=ImageRef.from_pil(img_a, dpi=72),
        prov=ProvenanceItem(page_no=1, charspan=(0, 0), bbox=bbox),
    )

    # 2. Document B (doc_b) の作成
    doc_b = DoclingDocument(name="document_b")
    img_b = Image.new("RGB", (20, 20), color="blue")
    doc_b.add_picture(
        image=ImageRef.from_pil(img_b, dpi=72),
        prov=ProvenanceItem(page_no=2, charspan=(0, 0), bbox=bbox),
    )

    # Document A を保存
    converter._save_markdown(doc_a, output_dir, options=options, slug="doc_a")
    images_dir = output_dir / "images"
    expected_img_a = images_dir / "doc_a_p1_1.png"
    assert expected_img_a.exists(), f"Expected {expected_img_a} to exist"

    # Document B を同じ output_dir に連続して保存
    converter._save_markdown(doc_b, output_dir, options=options, slug="doc_b")
    expected_img_b = images_dir / "doc_b_p2_1.png"
    assert expected_img_b.exists(), f"Expected {expected_img_b} to exist"

    # 両方の画像が共存しており、doc_a の画像が上書きされていないことを確認
    all_images = sorted([f.name for f in images_dir.glob("*.png")])
    assert "doc_a_p1_1.png" in all_images
    assert "doc_b_p2_1.png" in all_images
    assert len(all_images) == 2
