# Test Design for `extract_markdown` function

This document outlines the test cases for the `extract_markdown` function based on the TDD guidelines in `docs/pytest_exec.md`.

## Function Signature
```python
from pathlib import Path
from typing import Optional

def extract_markdown(pdf_path: Path, out_dir: Path) -> Optional[Path]:
    ...
```

## Test Cases Table

| Category | Test Case | Given | When | Then |
| --- | --- | --- | --- | --- |
| **正常系 (Happy Path)** | **正常なPDFと出力先** | - 有効なPDFファイル (`1706.03762.pdf`)<br>- 空の出力ディレクトリ | `extract_markdown` を呼び出す | - Markdownファイルのパスを返す<br>- 出力ディレクトリに `.md` ファイルが生成される<br>- 出力ディレクトリに `images` サブディレクトリが生成される<br>- `images` ディレクトリに画像ファイルが生成される |
| | **出力ディレクトリが存在しない** | - 有効なPDFファイル<br>- 存在しない出力ディレクトリのパス | `extract_markdown` を呼び出す | - 出力ディレクトリと `images` サブディレクトリが自動生成される<br>- Markdownファイルのパスを返す |
| **異常系 (Edge Cases)** | **PDFファイルが存在しない** | - 存在しないPDFファイルのパス | `extract_markdown` を呼び出す | - `None` を返す<br>- エラーがログに出力される |
| | **不正または破損したPDF** | - PDFではない、または破損したファイル | `extract_markdown` を呼び出す (内部で`pymupdf`が例外を発生させる) | - `None` を返す<br>- エラーがログに出力される |
| | **`pymupdf4llm` 抽出失敗 (フォールバック)** | - 有効なPDFファイル<br>- `pymupdf4llm.to_markdown` が失敗するようにモックする | `extract_markdown` を呼び出す | - テキストのみの基本的なMarkdownファイルが生成される (フォールバック処理)<br>- 画像は抽出されない |
| | **出力ディレクトリへの書き込み権限がない** | - 有効なPDFファイル<br>- 書き込み権限のない出力ディレクトリ | `extract_markdown` を呼び出す | - `PermissionError` が発生するか、`None` を返してエラーをログに出力する |
| | **画像パスの相対パス変換** | - `pymupdf4llm` が絶対パスで画像リンクを生成した場合 | `extract_markdown` を呼び出す | - Markdown内の画像パスが `images/filename.png` のような相対パスに正しく修正されている |