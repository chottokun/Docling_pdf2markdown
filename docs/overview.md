## 1. 概要
このファイルは、`docs/docling_pdf_sample.py` の実装を踏まえて、PDF から Markdown と画像を抽出するワークフロー、設定項目、主要関数、依存関係、実行方法、注意点を明確化するために更新したものです。ACE と RAG の統合は次フェーズとして計画します。

## 2. PDF→Markdown ワークフロー（実装に基づく要点）

- 入力: PDF ファイル（例: `sample_arxiv.pdf`）
- 出力:
  - Markdown ファイル（例: `extracted_output/extracted_document.md`）
  - 画像フォルダ（例: `extracted_output/images/`）
  - 洗練済み Markdown（画像を <figure> タグに変換した `*_refined.md`）
  - 出力 ZIP（例: `extracted_output/extracted_output.zip`）
- 主な処理:
  1. PDF のダウンロード（存在しない場合）: `download_pdf(url, pdf_path)`
  2. PyMuPDF の安全なテキスト抽出フラグの選定: `choose_safe_flag()`
  3. `pymupdf4llm.to_markdown` を用いた Markdown と画像の抽出: `extract_markdown_with_images(...)`
  4. 画像参照を HTML の <figure> に変換してキャプションを検出・付与: `refine_markdown(...)`
  5. Markdown と画像を ZIP にまとめる: `create_zip_output(...)`
  6. Colab 環境では `files.download` でダウンロード可能にする（フォールバックあり）

## 3. 主要構成・設定値（`docs/docling_pdf_sample.py` 由来）

- 設定変数（デフォルト）:
  - `PDF_PATH = Path("sample_arxiv.pdf")`
  - `OUT_DIR = Path("extracted_output")`
  - `MD_OUTPUT_NAME = "extracted_document.md"`
  - `IMAGE_DIR_NAME = "images"`
  - `ZIP_PATH = "extracted_output.zip"`
  - `DPI = 300` （画像抽出品質、必要に応じて下げると処理が速くなる）
  - `VERBOSE = True` （ログ出力制御）

- ロギング: 標準出力と `pdf_to_markdown_{pdf_stem}.log` の 2 方向に出力する。

## 4. 依存関係

実装で使用している主要パッケージ（最低限）:

- `pymupdf`（fitz）: PDF 操作・テキスト抽出
- `pymupdf4llm`: PDF → Markdown 変換ユーティリティ（画像出力対応）
- `Pillow`: 画像処理
- `requests`: PDF ダウンロード
- `python` 3.8+ を想定

導入例（pip）:

pip install pymupdf pymupdf4llm pillow requests

また Colab 環境での利用を考える場合、ノートブック向けの追加コマンドが含まれているが、ローカル環境では通常の pip インストールで十分です。

## 5. 主要関数の説明（要約）

- `download_pdf(url: str, pdf_path: Path) -> bool`:
  - URL から PDF をダウンロード（既存ファイルがあればスキップ）。HTTP ステータスチェックと例外処理あり。
- `choose_safe_flag() -> int`:
  - PyMuPDF のテキスト抽出フラグを安全に選択するヘルパー。互換性のあるフラグを探索し、なければデフォルト値を返す。
- `extract_markdown_with_images(pdf_path: Path, out_dir: Path, flags_int: int = 1) -> Optional[Path]`:
  - `pymupdf4llm.to_markdown` を呼び出して Markdown テキストと画像を生成。
  - 画像パスを相対パス（`images/`）へ補正する処理を含む。
  - `use_getText_options` が使えない場合のフォールバックと、失敗時は PyMuPDF の生テキスト抽出へフォールバックする実装。
- `normalize_alt_text(alt: str, src: str) -> str`:
  - 画像の alt テキストを正規化して HTML エスケープするユーティリティ。
- `refine_markdown(md_path: Path) -> Optional[Path]`:
  - Markdown 内の `![]()` 画像参照を `<figure>` タグに変換し、直後の行から図キャプションを探索して `<figcaption>` を付与する。
- `create_zip_output(out_dir: Path, md_path: Path) -> Optional[Path]`:
  - Markdown と images ディレクトリ内の PNG を ZIP にまとめる。

## 6. 実行方法（サンプル）

プロジェクトルートで依存をインストールし、スクリプトを実行します（PowerShell の例）:

# 仮想環境作成（推奨）
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt  # または個別インストール

# スクリプト実行
python docs\docling_pdf_sample.py

スクリプトはデフォルトで `ARXIV_PDF_URL` から PDF をダウンロードして処理を行います。ローカルの別 PDF を使う場合は `PDF_PATH` を変更してください。

## 7. 注意点とエラーハンドリング

- `pymupdf4llm` のオプション互換性により、`use_getText_options` がサポートされない場合があるため例外ハンドリングが入っています。
- 画像パスの補正ロジックは生成されるパスのパターンに依存するため、別の `image_path` 指定やバージョン差で調整が必要になる場合があります。
- 大きな PDF（ページ数が多く画像が多い）ではメモリやディスクが急速に消費されるため注意。DPI を下げる・ページ単位で分割処理するなどの対策を推奨します。

## 8. 次のステップ（推奨タスク）

1. ACE フレームワークへの組込: 抽出した Markdown と画像を断片化（チャンク化）してコンテキスト化するパイプラインを実装。
2. streamlit フロントエンド: 抽出結果のプレビュー、図のキャプション編集、RAG 用のメタデータ付与 UI を作成。
3. ユニットテスト: `download_pdf`, `extract_markdown_with_images`, `refine_markdown` のハッピーパスとエッジケース（空画像、壊れた PDF）をカバーする簡易テストの追加。
4. 依存管理: `pyproject.toml` か `requirements.txt` を整備し、再現性を保証する。

---

この更新は `docs/docling_pdf_sample.py` の現在の実装（ワークフロー）に基づいています。スクリプト側を変更した場合は本ドキュメントも併せて更新してください。
'@ | Set-Content -Path $path -Encoding UTF8 -Force