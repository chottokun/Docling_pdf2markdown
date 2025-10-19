# Test Design for `refine_markdown` function

This document outlines the test cases for the `refine_markdown` function.

## Function Signature
```python
from pathlib import Path
from typing import Optional

def refine_markdown(md_path: Path) -> Optional[Path]:
    ...
```

## Test Cases Table

| Category | Test Case | Given | When | Then |
| --- | --- | --- | --- | --- |
| **正常系 (Happy Path)** | **画像とキャプションが1つ** | - `![alt text](images/img.png)` の形式の行<br>- その直後にキャプション `Figure 1: Caption text` があるMarkdownファイル | `refine_markdown` を呼び出す | - `<figure>` タグで囲まれた `<img>` タグが生成される<br>- `<img>` タグの後に `<figcaption>Caption text</figcaption>` が生成される<br>- 元の画像リンクとキャプション行は削除される<br>- `_refined.md` という名前の新しいファイルが生成され、そのパスが返される |
| | **画像とキャプションが複数** | - 複数の画像リンクと、それぞれの直後にキャプションがあるMarkdownファイル | `refine_markdown` を呼び出す | - すべての画像とキャプションのペアが正しく `<figure>` と `<figcaption>` に変換される |
| | **キャプションがない画像** | - 画像リンクはあるが、後続の行にキャプションに一致するパターンがない | `refine_markdown` を呼び出す | - `<figure>` と `<img>` タグは生成される<br>- `<figcaption>` は生成されない |
| | **多様なキャプション形式** | - `図 1:`, `Fig. 1.`, `*Caption*` など、異なる形式のキャプション | `refine_markdown` を呼び出す | - すべての形式のキャプションが正しく抽出され、`<figcaption>` に変換される |
| **異常系 (Edge Cases)** | **Markdownファイルが存在しない** | - 存在しないMarkdownファイルのパス | `refine_markdown` を呼び出す | - `None` を返す<br>- エラーがログに出力される |
| | **画像リンクがない** | - 画像リンク `![]()` が一つも含まれないMarkdownファイル | `refine_markdown` を呼び出す | - ファイルの内容は変更されず、新しい `_refined.md` ファイルにそのままコピーされる |
| | **空のMarkdownファイル** | - 0バイトの空のMarkdownファイル | `refine_markdown` を呼び出す | - 空の `_refined.md` ファイルが生成され、そのパスが返される |
| | **書き込み権限がない** | - Markdownファイルは存在するが、そのディレクトリに書き込み権限がない | `refine_markdown` を呼び出す | - `None` を返し、`PermissionError` がログに出力される |
| | **画像とキャプションの間に空行** | - `![...](...)` の行とキャプションの行の間に1行以上の空行がある | `refine_markdown` を呼び出す | - キャプションとして認識されず、`<figcaption>` は生成されない（仕様確認） |