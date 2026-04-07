import os
from pathlib import Path
from typing import List

from fastmcp import FastMCP
from indexer import MarkdownIndexer
from config import TARGET_DIR

# サーバーの初期化
mcp = FastMCP("Semantic Markdown Knowledge Server")

# インデクサーの初期化
indexer = MarkdownIndexer()

@mcp.tool()
def semantic_search(query: str, limit: int = 5) -> str:
    """
    自然言語のクエリを受け取り、ベクトルデータベース内で類似度検索を実行する。
    類似度の高い順に、該当するチャンクのテキスト内容、元のファイルパス、見出し情報をフォーマットして文字列として返す。
    """
    try:
        results = indexer.search(query, limit)
        
        if not results['ids'] or len(results['ids'][0]) == 0:
            return "条件に一致するドキュメントが見つかりませんでした。"
        
        formatted_results = []
        for i in range(len(results['ids'][0])):
            doc = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            
            file_path = meta.pop("file_path", "Unknown")
            headers = ", ".join([f"{k}: {v}" for k, v in meta.items()])
            
            res_str = f"## File: {file_path}\n"
            if headers:
                res_str += f"### Headers: {headers}\n"
            res_str += f"### Text:\n{doc}\n"
            formatted_results.append(res_str)
            
        return "\n\n---\n\n".join(formatted_results)
    except Exception as e:
        return f"Error during search: {e}"


@mcp.tool()
def read_markdown_file(file_path: str) -> str:
    """
    指定されたファイルの全文を返す。（セマンティック検索の結果から全体像を確認したい場合などに使用）
    ファイルパスはルートディレクトリ以下のもののみ許可される。
    """
    if not indexer.is_safe_path(file_path):
        return "Error: Invalid file path or path traversal detected."
        
    try:
        path = Path(file_path)
        if not path.is_file():
            return "Error: File not found."
            
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


@mcp.tool()
def list_markdown_files() -> List[str]:
    """
    現在インデックス化されている、ルートディレクトリ以下のMarkdownファイルパスのリストを返す。
    """
    files = indexer.get_all_md_files()
    return [str(f) for f in files]


if __name__ == "__main__":
    # サーバー起動時にインデックスを初期化・更新
    print(f"Target directory: {TARGET_DIR}")
    print("Indexing markdown files...")
    indexer.index_all()
    print("Indexing complete. Starting MCP server...")
    
    # 標準入出力トランスポートで起動
    mcp.run()
