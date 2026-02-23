# Doclingを用いた図埋め込み型markdownファイルの生成ライブラリの構築

## 0. 目的・背景

## 1. はじめに

本ドキュメントは、Doclingを用いた図埋め込み型markdownファイルの生成ライブラリを構築する。`Docs/`でのドキュメント・サンプルコードを参考に本システムを構築するための指針を示す。既存の複雑なドキュメント（PDFなど）をLLMに理解させる「読み取り」の文脈で、DoclingはPDFをMarkdownに変換するツールとして利用できる。

## 2. 実装について

### 2.1. 実装のルールと手順

- 汎用的に利用しやすいコードを構築すること。
- 入力・出力が関数としてふさわしく、実用に耐えうる構造とすること。
- TDD手法を採用し、`docs\pytest_exec.md`も参考にして進めること。
- CLIでPDFファイルを指定するとpdfから指定したディレクトリにmarkdownファイルと画像ファイルが保存されるようにすること。
- 最終的には、Doclingはバージョン依存性がGPUの利用も可能である点に注意しつつ、docker composeを利用したFAST APIとしても利用できるように実装すること。

### 2.2. Doclingにおける図の方法

- 図からMermaidへの変換: Doclingの関連エコシステム（docling-graphなど）では、抽出した図の構造を解析し、Mermaid形式のフローチャートとして再構築する技術も導入されています。自動修復機能: LLM（を介して、変換時に壊れたMermaid構文を自動修正する仕組みを組み合わせることで、精度の高い「コードとしての図解」へと昇華させるワークフローも提案されています 。

## 3. 環境構築について

### 3.1. セットアップ手順

`uv` を用いてPythonの仮想環境を構築し、パッケージを管理する。

1.  **仮想環境の作成**
    ```bash
    uv venv
    ```
2.  **仮想環境のアクティベート**
    ```bash
    # macOS / Linux
    source .venv/bin/activate
    # Windows
    .venv\Scripts\activate
    ```
3.  **依存関係のインストール**

依存関係は`pyproject.toml`に記述します：

```toml
[project.dependencies]
openai = "^1.3.5"
requests = "^2.31.0"
```
パッケージの追加

```bash
uv pip install <package-name>
uv pip add <package-name>  # pyproject.tomlに追記
```

# 参考URL
- https://docling-project.github.io/docling/

# ライセンス
利用したライブラリのライセンスをREADME.mdに表記すること。