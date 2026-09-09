#!/usr/bin/env python3
"""
Docling Model Pre-downloader & Offline Verifier Script

This script downloads and caches all required Docling AI models (Layout, TableFormer,
OCR, Code/Formula, Chart extraction, VLM, etc.) to a local directory (.cache_models)
on the host machine to enable completely offline execution in CLI, tests, and Docker.

Usage:
    # Download standard production models (Layout, TableFormer v1/v2, CodeFormula, PictureClassifier, RapidOCR, EasyOCR)
    uv run python scripts/download_models.py

    # Download ALL available models including charts, VLMs, and experimental models
    uv run python scripts/download_models.py --all
    # or
    uv run python scripts/download_models.py --profile full

    # Download only specific models
    uv run python scripts/download_models.py -m layout tableformer rapidocr

    # Verify offline operation using cached models
    uv run python scripts/download_models.py --verify-offline
"""

import argparse
import logging
import os
import sys
from collections.abc import Sequence
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("download_models")

# Available model identifiers
MODEL_CHOICES = [
    "layout",
    "tableformer",
    "tableformer_v2",
    "code_formula",
    "picture_classifier",
    "rapidocr",
    "easyocr",
    "nemotron_ocr",
    "granite_chart_extraction",
    "granite_chart_extraction_v4",
    "smolvlm",
    "granitedocling",
    "granitedocling_mlx",
    "granitedocling_2stage",
    "smoldocling",
    "smoldocling_mlx",
    "granite_vision",
]

# Profiles mapped to model combinations
PROFILES = {
    "standard": [
        "layout",
        "tableformer",
        "tableformer_v2",
        "code_formula",
        "picture_classifier",
        "rapidocr",
    ],
    "full": MODEL_CHOICES,
    "minimal": [
        "layout",
        "tableformer",
        "picture_classifier",
    ],
    "ocr": [
        "rapidocr",
        "easyocr",
        "nemotron_ocr",
    ],
    "chart": [
        "granite_chart_extraction",
        "granite_chart_extraction_v4",
    ],
    "formula": [
        "code_formula",
    ],
}

DEFAULT_MODELS = PROFILES["standard"]


def _is_package_available(pkg_name: str) -> bool:
    """Checks if a python package is installed and importable."""
    import importlib.util

    return importlib.util.find_spec(pkg_name) is not None


def get_dir_size(path: Path) -> tuple[int, int]:
    """Returns total size in bytes and file count in a directory."""
    if not path.exists():
        return 0, 0
    total_bytes = 0
    file_count = 0
    for p in path.rglob("*"):
        if p.is_file():
            total_bytes += p.stat().st_size
            file_count += 1
    return total_bytes, file_count


def format_bytes(size: int) -> str:
    """Formats bytes into human readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def download_selected_models(
    output_dir: Path,
    selected_models: Sequence[str],
    force: bool = False,
    progress: bool = True,
) -> Path:
    """
    Downloads the selected Docling models into the specified output directory.
    """
    from docling.utils.model_downloader import download_models

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set HF_HOME and DOCLING_CACHE_DIR environment to harmonize caching
    os.environ.setdefault("HF_HOME", str(output_dir))
    os.environ.setdefault("DOCLING_ARTIFACTS_PATH", str(output_dir))

    # Validate optional dependencies
    with_easyocr = "easyocr" in selected_models
    if with_easyocr and not _is_package_available("easyocr"):
        logger.warning(
            "Skipping EasyOCR model download: 'easyocr' package is not installed. "
            "To install, run: uv add easyocr"
        )
        with_easyocr = False

    logger.info(f"Target model directory: {output_dir}")
    logger.info(f"Selected models ({len(selected_models)}): {', '.join(selected_models)}")

    kwargs = {
        "output_dir": output_dir,
        "force": force,
        "progress": progress,
        "with_layout": "layout" in selected_models,
        "with_tableformer": "tableformer" in selected_models,
        "with_tableformer_v2": "tableformer_v2" in selected_models,
        "with_code_formula": "code_formula" in selected_models,
        "with_picture_classifier": "picture_classifier" in selected_models,
        "with_smolvlm": "smolvlm" in selected_models,
        "with_granitedocling": "granitedocling" in selected_models,
        "with_granitedocling_mlx": "granitedocling_mlx" in selected_models,
        "with_granitedocling_2stage": "granitedocling_2stage" in selected_models,
        "with_smoldocling": "smoldocling" in selected_models,
        "with_smoldocling_mlx": "smoldocling_mlx" in selected_models,
        "with_granite_vision": "granite_vision" in selected_models,
        "with_granite_chart_extraction": "granite_chart_extraction" in selected_models,
        "with_granite_chart_extraction_v4": "granite_chart_extraction_v4" in selected_models,
        "with_rapidocr": "rapidocr" in selected_models,
        "with_easyocr": with_easyocr,
        "with_nemotron_ocr": "nemotron_ocr" in selected_models,
    }

    result_path = download_models(**kwargs)

    size, count = get_dir_size(output_dir)
    logger.info("=" * 60)
    logger.info(f"Download complete! Models saved to: {result_path}")
    logger.info(f"Total files: {count}, Total size: {format_bytes(size)}")
    logger.info("=" * 60)
    logger.info("\nTo use these cached models in offline environments:")
    logger.info(f"  export DOCLING_ARTIFACTS_PATH={output_dir}")
    logger.info(f"  export HF_HOME={output_dir}")
    logger.info("  export HF_HUB_OFFLINE=1")
    logger.info("  export TRANSFORMERS_OFFLINE=1\n")

    return result_path


def verify_offline_mode(artifacts_path: Path) -> bool:
    """
    Verifies that the DocumentConverter pipeline can be successfully initialized
    and loaded completely offline using the cached artifacts.
    """
    logger.info("=" * 60)
    logger.info(f"Verifying offline initialization with artifacts at: {artifacts_path}")
    logger.info("=" * 60)

    # Force offline environment variables
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["DOCLING_ARTIFACTS_PATH"] = str(artifacts_path)
    os.environ["HF_HOME"] = str(artifacts_path)

    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption

        pipeline_options = PdfPipelineOptions(artifacts_path=artifacts_path)
        pipeline_options.do_ocr = True
        pipeline_options.do_formula_enrichment = True
        pipeline_options.do_code_enrichment = True

        format_options = {
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }

        logger.info("Initializing DocumentConverter in offline mode...")
        converter = DocumentConverter(format_options=format_options)
        logger.info("Successfully initialized DocumentConverter completely offline!")
        return True
    except Exception as e:
        logger.error(f"Offline verification failed: {e}", exc_info=True)
        return False


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(
        description="Pre-download and cache Docling AI models locally for offline and container use.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path(".cache_models"),
        help="Directory where models will be saved and cached.",
    )
    parser.add_argument(
        "--profile",
        choices=list(PROFILES.keys()),
        help=f"Predefined model profile to download: {', '.join(PROFILES.keys())}",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download ALL available models (equivalent to --profile full).",
    )
    parser.add_argument(
        "-m",
        "--models",
        nargs="+",
        choices=MODEL_CHOICES,
        help=f"Specific models to download. Choices: {', '.join(MODEL_CHOICES)}",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force re-download even if models already exist.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Disable progress bars and detailed download logs.",
    )
    parser.add_argument(
        "--verify-offline",
        action="store_true",
        help="Verify that models can be initialized completely offline without network access.",
    )

    return parser.parse_args(args)


def main():
    args = parse_args()
    if args.quiet:
        logger.setLevel(logging.WARNING)

    output_dir = args.output_dir.resolve()

    if args.verify_offline:
        success = verify_offline_mode(output_dir)
        sys.exit(0 if success else 1)

    if args.all:
        selected_models = PROFILES["full"]
    elif args.profile:
        selected_models = PROFILES[args.profile]
    elif args.models:
        selected_models = args.models
    else:
        selected_models = DEFAULT_MODELS

    try:
        download_selected_models(
            output_dir=output_dir,
            selected_models=selected_models,
            force=args.force,
            progress=not args.quiet,
        )
    except Exception as e:
        logger.error(f"Failed to download models: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
