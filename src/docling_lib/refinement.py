import re
import html
import logging
from pathlib import Path
from typing import Optional, List, Tuple

# --- Logging Setup ---
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def normalize_alt_text(alt: str, src: str) -> str:
    """
    Normalizes image alt text. Uses the filename if alt text is empty.
    """
    alt_clean = " ".join((alt or "").split()).strip()
    if not alt_clean:
        filename = Path(src).name
        alt_clean = re.sub(r"[_\-]+", " ", filename.rsplit(".", 1)[0])
    return html.escape(alt_clean)

def find_caption_after(lines: List[str], idx: int) -> Tuple[str, int]:
    """
    Finds a caption in the lines following an image reference.
    A caption is identified by specific patterns.
    """
    caption_patterns = [
        re.compile(r'^\s*(Figure|Fig\.|図)\s*\d*[:：\-]\s*(.+)', re.I),
        re.compile(r'^\s*\*(.+)\*\s*$'), # Italicized captions
        re.compile(r'^\s*<figcaption>(.+)</figcaption>\s*$', re.I) # Existing figcaption
    ]

    for offset in range(1, 4):
        if idx + offset >= len(lines):
            break

        candidate = lines[idx + offset].strip()
        if not candidate:
            continue

        for pat in caption_patterns:
            m = pat.match(candidate)
            if m:
                caption = m.group(2) if len(m.groups()) >= 2 and m.group(2) else m.group(1)
                return (caption.strip(), offset)

    # Fallback for general capitalized sentences has been removed to avoid false positives.
    return ("", 0)

# --- Main Refinement Function ---

def refine_markdown(md_path: Path) -> Optional[Path]:
    """
    Refines a Markdown file by converting image references to <figure> tags
    with captions and saves it to a new file with a `_refined` suffix.
    """
    try:
        if not md_path.exists():
            logger.error(f"Markdown file not found: {md_path}")
            return None

        logger.info(f"Refining Markdown: {md_path}")

        raw_text = md_path.read_text(encoding="utf-8")
        lines = raw_text.splitlines()

        output_lines = []
        img_pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
        fig_counter = 1
        i = 0

        while i < len(lines):
            line = lines[i]
            match = img_pattern.search(line)

            if not match:
                output_lines.append(line)
                i += 1
                continue

            alt_raw = match.group(1)
            src = match.group(2).strip()

            if not src.startswith("images/"):
                src = f"images/{Path(src).name}"

            alt_norm = normalize_alt_text(alt_raw, src)
            fig_id = f"fig-{fig_counter:03d}"
            fig_counter += 1

            img_html = f'<img src="{html.escape(src)}" alt="{alt_norm}" />'
            caption_text, offset = find_caption_after(lines, i)

            if caption_text:
                figcap_html = f'<figcaption>{html.escape(caption_text)}</figcaption>'
                figure_html = f'<figure id="{fig_id}">{img_html}{figcap_html}</figure>'
                logger.info(f"Caption detected for image {src}: {caption_text}")
                i += offset + 1
            else:
                figure_html = f'<figure id="{fig_id}">{img_html}</figure>'
                i += 1

            output_lines.append(figure_html)

        refined_text = "\n".join(output_lines)
        refined_path = md_path.with_name(md_path.stem + "_refined.md")

        refined_path.write_text(refined_text, encoding="utf-8")
        logger.info(f"Refined Markdown saved to: {refined_path}")
        return refined_path

    except PermissionError:
        logger.error(f"Permission denied when trying to read or write in {md_path.parent}")
        return None
    except Exception as e:
        logger.error(f"Failed to refine Markdown file {md_path}: {e}", exc_info=True)
        return None