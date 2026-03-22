# Docling Markdown Generator

Doclingを使ってドキュメントを高精度にMarkdownへ変換し、図や表を適切に抽出するプロジェクトです。

本プロジェクトは、PDF、Word（.docx）、PowerPoint（.pptx）、およびExcel（.xlsx）ファイルを構造化されたMarkdown形式へ変換するためのPythonライブラリ、コマンドラインツール（CLI）、およびコンテナ化されたFastAPIサーバーを提供します。最新の `docling`（v2.x）を利用し、高精度なドキュメントのレイアウト解析とデータ抽出を実現しています。

## ドキュメント

詳細については、以下のドキュメント（`docs/` 配下）を参照してください：

- **[Markdown出力仕様 (MARKDOWN_SPEC.md)](docs/MARKDOWN_SPEC.md)**: 画像、表、およびドキュメントの構造化に関する詳細。
- **[APIリファレンス (API_REFERENCE.md)](docs/API_REFERENCE.md)**: サーバーとして利用する際のエンドポイントの詳細や例。
- **[本プロジェクト独自の強み (FEATURES.md)](docs/FEATURES.md)**: 標準のDoclingに加え、セキュリティ、パフォーマンス、安定性をどのように向上させているかの解説。
- **[デプロイメント・ガイド (DEPLOYMENT.md)](docs/DEPLOYMENT.md)**: 環境変数、スケーリング、本番運用に向けたガイドライン。

## 主な機能

- **複数フォーマットのサポート**: PDF、DOCX、PPTX、およびXLSXファイルからテキスト、表、図を高精度に抽出します。
- **ネイティブ変換**: Doclingの実装により、Officeファイルの変換にLibreOfficeなどの外部依存は不要です。
- **高度なレイアウト解析と抽出**: 
  - 表（テーブル）構造を理解し、セル結合を維持できるHTML形式のテーブルとして出力します。
  - 図（画像）をPNGとして抽出し、可能であればキャプションを関連づけた上でMarkdownにリンクとして埋め込みます。
  - LaTeX形式での数式抽出（Docling標準のVLM機能）をサポートしています。
- **パフォーマンスと設計**: エンジンの使い回しによる初期化コストの低減や、並行処理時のスレッドセーフ設計（非同期ブロッキングI/Oの最適化）を行っています。
- **セキュリティの強化**: パスラバーサル（Path Traversal）や情報漏洩などの脆弱性に対する保護が組み込まれています。
- **APIとDocker対応**: 外部から変換処理を呼び出せるFastAPIサーバーが組み込まれており、DockerやDocker Composeで簡単に立ち上げられます。

## 前提条件

- Python 3.11 以上
- [uv](https://github.com/astral-sh/uv) （パッケージ管理として推奨）
- Docker および Docker Compose（サーバー起動を行う場合）

## インストール

本プロジェクトは依存関係の管理に `uv` を使用しています。

1.  **仮想環境の作成と有効化:**
    ```bash
    uv venv
    source .venv/bin/activate  # macOS/Linux
    # .venv\Scripts\activate  # Windows
    ```

2.  **ライブラリのインストール:**
    ```bash
    uv pip install -e ".[test]"
    ```

## 使い方

### コマンドラインツール (CLI)

`docling_converter_cli` コマンドを使用して、ターミナルから直接ファイルを変換できます。

```bash
docling_converter_cli [入力ファイル] -o [出力ディレクトリ]
```

**引数:**

- `[入力ファイル]`: 変換元のファイルパス (.pdf, .docx, .pptx, .xlsx)
- `-o, --output-dir`: 変換結果（Markdownおよび画像）を保存するディレクトリ。デフォルトは `output/`。

**実行例:**
```bash
docling_converter_cli sample.pptx -o results/
```

### Dockerを用いたサーバー実行

変換機能を継続的に提供する場合は、コンテナ化されたFastAPIサーバーの実行が最も簡単です。

1.  **サーバーの起動:**
    ```bash
    docker-compose up --build
    ```
    サーバーは `http://localhost:8000` で起動します。

2.  **APIの利用例 (変換リクエスト):**
    `/convert/` エンドポイントに対してPOSTリクエストを送信します。
    ```bash
    curl -X POST -F "file=@/path/to/document.pdf" http://localhost:8000/convert/
    ```
    変換されたMarkdownファイルと画像のダウンロードリンクを含むJSONレスポンスが返却されます。

## 開発とテスト

本プロジェクトではTDD (テスト駆動開発) のアプローチを採用しており、実際のファイルを用いたEnd-to-End (E2E) テストを含む強力なテスト環境を運用しています。

詳細なテストの実行方法（軽量なユニットテストと重いE2Eテストの使い分けなど）については、**[テスト実行ガイド (docs/pytest_exec.md)](docs/pytest_exec.md)** を参照してください。

- **基本的なユニットテストの実行:**
  ```bash
  uv run pytest
  ```
- **カバレッジの計測:**
  ```bash
  uv run pytest --cov=src
  ```

## ライセンスのご案内

本リポジトリを利用・改変する際は、依存する各プロジェクトのライセンスに従ってください：
- **docling**: MIT License
- **docling-core**: MIT License
- **FastAPI**: MIT License