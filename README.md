# Semantic Markdown Knowledge MCP Server

ローカルのMarkdownファイル群をナレッジベースとして読み込み、意味（セマンティック）検索を可能にするModel Context Protocol (MCP) サーバーです。
Gemini CLI等のMCPクライアントから自然言語を使って抽象的なクエリを投げ、関連するドキュメントのパラグラフをコンテキストとして引き出すことができます。

## 特徴
- **ローカル完結**: エンベディングモデルおよびベクトルデータベースはすべてローカル（ChromaDB）で独立して動作します。外部APIへの通信は行われずプライバシーが保たれます。
- **セマンティック検索**: `intfloat/multilingual-e5-small` モデルを用い、日本語の文脈を高精度に理解した意味検索を実現します。
- **効率的な差分更新**: ファイルのタイムスタンプ(`mtime`)を監視し、起動時に更新または追加されたファイルのみ即座に再インデックス化します。
- **Markdown構造の維持**: `langchain-text-splitters` により、見出しなどMarkdownの階層を維持したまま、意味を持つブロック単位でチャンク化します。

## 必要要件
- Python 3.9 以上
- `fastmcp`
- `chromadb`
- `langchain-text-splitters`
- `sentence-transformers`
- `torch`

## インストールと起動手順

1. **仮想環境の構築と依存関係のインストール**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. **サーバーの単体起動 (動作確認・インデックス作成用)**
```powershell
python mcp_server.py
```
*※初回起動時にはエンベディングモデル（e5-small）のダウンロードや全ファイルのインデックス化が行われるため、初回のみ数分程度かかります。*

## 設定・カスタマイズ
ナレッジ取得元などの設定は `config.py` 内、または環境変数で指定可能です。
- `TARGET_DIR` : 読み込むMarkdownファイルが配置されている対象ディレクトリ（デフォルト: `./notes`）

## 提供される MCP ツール (Tools)
本サーバーは以下の機能をMCPクライアント向けに公開します:
- `semantic_search(query: str, limit: int = 5) -> str`: 自然言語のクエリを受け取り、関連性の高いチャンク本文を見出し情報とともに返します。
- `read_markdown_file(file_path: str) -> str`: 検索結果等から特定のMarkdownの全体を読みたい場合に、全文を取得します。（不正なパス参照を防ぐパストラバーサル対策済み）
- `list_markdown_files() -> List[str]`: 現在DBにインデックス化されている全ファイルリストを返します。

## セルフドキュメンテーション
`notes` フォルダには本プロジェクト内で使用している各種技術 (`FastMCP`, `ChromaDB` 等) や、差分更新・セマンティック検索等のロジック概要を記したテスト用のMarkdownノートが含まれています。
インデックス化後、テスト用としてシステム自身に「このシステムのベクトル抽出はどうやってる？」と質問して動作確認を行うことができます。

## ライセンス
MIT License
# semantic-markdown-mcp
