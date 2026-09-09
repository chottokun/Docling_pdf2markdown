# Markdown Output Specification

Language: [English](MARKDOWN_SPEC.md) | [日本語](../MARKDOWN_SPEC.md)

This library generates highly structured Markdown optimized for Retrieval-Augmented Generation (RAG) and LLM comprehension using Docling.

---

## 0. Metadata (YAML Frontmatter)

Generated Markdown documents begin with a YAML frontmatter block containing metadata:
```yaml
---
title: Document Title
# page_count: 10
---
```
This metadata enables LLMs to establish document context immediately during parsing.

---

## 1. Figures and Images

### Embeddings
Figures are referenced using CommonMark / GFM standard syntax (compatible with VS Code, GitHub, and standard Markdown renderers):
```markdown
![doc-slug_p1_1.png](assets/doc-slug/doc-slug_p1_1.png)
```
- **Naming Convention**: `{doc_slug}_p{page}_{index}.png` (e.g. `report_p3_1.png`). Prevents filename collisions and overwrite issues during batch conversions, and preserves document and page context for RAG ingestion.
- **Storage**: Saved to the specified `assets_dir` or output directory.
- **Custom Links**: When using `EnhancedDoclingConverter`, custom tag templates like Obsidian syntax (`![[assets/{slug}/{image_name}]]`) can be configured via `image_tag_template`.

### Caption Extraction
Extracted text surrounding figures (figure numbers, captions, descriptions) is automatically linked to the image item.

---

## 2. Tables

Complex tables (including merged cells in PDFs and Excel files) are converted into **HTML (`<table>`) elements** embedded in Markdown:
- **Structural Integrity**: Preserves merged cells accurately using `rowspan` and `colspan`.
- **LLM Friendliness**: LLMs parse complex matrix relationships more accurately from HTML tables than ASCII Markdown tables.

---

## 3. Document Structure

- **Headers**: Hierarchical headings (`#`, `##`, `###`) generated according to logical document structure.
- **Formulas (LaTeX)**: Scientific formulas are extracted into high-precision **LaTeX code blocks**.

  ### ⚙️ Math Formatting Options
  Configurable via API parameters, CLI options, or `DocumentConversionOptions`:

  | Option Name | Default | Description | Allowed Values |
  | :--- | :--- | :--- | :--- |
  | `math_inline_delim` | `"auto"` | Inline math delimiter | `"auto"`, `"$"` or custom string |
  | `math_block_delim` | `"auto"` | Block math delimiter | `"auto"`, `"$$"`, `"\["` or custom string |
  | `math_block_newline` | `"auto"` | Inner newlines for math blocks | `"auto"`, `true` / `"true"`, `false` / `"false"` |

  ### 🧠 Automatic Resolution (`"auto"`) Rules
  - **LaTeX Source Files (`.tex`, `.latex`)**: Uses standard bracket delimiters (`\(` / `\)` for inline, `\[` / `\]` for blocks).
  - **Other Documents (PDF, Office, HTML)**: Uses standard dollar delimiters (`$` for inline, `$$` for blocks).
  - **Block Newline Insertion**: Inserts interior newlines for complex formulas (e.g., containing `\\`, `\begin`, `\end`, or formula length > 60 characters).

---

## 4. RAG Optimization Features

### Key Information (Markdown KV)
Enabling `include_kv_extraction` appends a structured key-value list section to the document.

### Page Break Markers
Enabling `include_page_breaks` inserts page markers (`<!-- PAGE_BREAK: Page N -->`) to facilitate document chunking and segmentation.

---

## 5. Supported Formats
- **PDF**: Layout and structure analysis.
- **Office (DOCX, PPTX)**: Style-based structural hierarchy.
- **Excel (XLSX)**: Per-sheet table extraction.
