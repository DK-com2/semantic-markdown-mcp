import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from langchain_text_splitters import MarkdownHeaderTextSplitter
from sentence_transformers import SentenceTransformer

from config import TARGET_DIR, DB_PERSIST_DIR, COLLECTION_NAME, EMBEDDING_MODEL_NAME

class MarkdownIndexer:
    def __init__(self, target_dir: str = str(TARGET_DIR)):
        self.target_dir = Path(target_dir).resolve()
        
        # ChromaDB Client
        self.chroma_client = chromadb.PersistentClient(path=str(DB_PERSIST_DIR))
        self.collection = self.chroma_client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Sentence Transformer Model Setup
        self.encoder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    def get_all_md_files(self) -> List[Path]:
        if not self.target_dir.exists():
            return []
        
        md_files = []
        for root, _, files in os.walk(self.target_dir):
            for file in files:
                if file.endswith(".md"):
                    md_files.append(Path(root) / file)
        return md_files

    def chunk_markdown(self, text: str) -> List[Any]:
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        return markdown_splitter.split_text(text)

    def is_safe_path(self, path: str) -> bool:
        """パストラバーサルを防止し、TARGET_DIR以下のファイルのみアクセスを許可する"""
        try:
            requested_path = Path(path).resolve()
            return str(requested_path).startswith(str(self.target_dir))
        except Exception:
            return False

    def index_all(self, force: bool = False):
        """ディレクトリ内の全ファイルをインデックス化する"""
        md_files = self.get_all_md_files()
        
        # すでにインデックス済みのメタデータから各ファイルの最終更新日時を取得する
        # chroma_client などの仕様上、全てのメタデータを取得してmtimeを突き合わせるか、
        # sqlite3のような別DBにファイル状態を持たせるのが定石ですが、
        # ここでは collection.get() で既存データのファイルパスとmtimeの情報を取ります。
        
        existing_docs = self.collection.get(include=["metadatas"])
        
        # ファイルパスごとの最新の登録済みタイムスタンプを抽出
        indexed_mtime_map = {}
        if existing_docs and "metadatas" in existing_docs and existing_docs["metadatas"]:
            for meta in existing_docs["metadatas"]:
                if meta and "file_path" in meta and "file_mtime" in meta:
                    fp = meta["file_path"]
                    fm = float(meta["file_mtime"])
                    if fp not in indexed_mtime_map or fm > indexed_mtime_map[fp]:
                        indexed_mtime_map[fp] = fm
        
        for file_path in md_files:
            current_mtime = file_path.stat().st_mtime
            
            # インデックス済みであり、かつファイルが更新されていなければスキップ
            if not force and str(file_path) in indexed_mtime_map:
                if current_mtime <= indexed_mtime_map[str(file_path)]:
                    continue
                    
            print(f"Updating index for: {file_path}")
            self.index_file(file_path, current_mtime)
            
    def index_file(self, file_path: Path, current_mtime: float = None):
        if current_mtime is None:
            current_mtime = file_path.stat().st_mtime
            
        try:
            # 既に該当ファイルのチャンクが存在する場合は削除してから追加（完全置き換え）
            # 注意: ChromaDBのdeleteは少しコストがかかる場合があります。
            self.collection.delete(where={"file_path": str(file_path)})

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Markdownをチャンク化
            chunks = self.chunk_markdown(content)
            
            ids = []
            embeddings = []
            metadatas = []
            documents = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{file_path}_{i}"
                text = chunk.page_content
                
                # エンベディングの生成 (multilingual-e5 の場合は passage: を付与)
                doc_text = f"passage: {text}"
                vector = self.encoder.encode(doc_text).tolist()
                
                meta = chunk.metadata.copy()
                meta["file_path"] = str(file_path)
                meta["file_mtime"] = current_mtime
                
                # Noneや複雑な値はChromaDB登録のため文字列にする
                for key in meta:
                    if meta[key] is None:
                        meta[key] = ""

                
                ids.append(chunk_id)
                embeddings.append(vector)
                metadatas.append(meta)
                documents.append(text)
            
            if ids:
                self.collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents
                )
                print(f"Indexed: {file_path}")
        except Exception as e:
            print(f"Failed to index {file_path}: {e}")

    def search(self, query: str, limit: int = 5):
        query_text = f"query: {query}"
        query_embedding = self.encoder.encode(query_text).tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )
        
        return results
