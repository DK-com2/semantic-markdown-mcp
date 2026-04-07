import os
from pathlib import Path

# Наレッジの対象となるMarkdownディレクトリ (未指定の場合はカレントディレクトリ直下の ./notes など)
TARGET_DIR_ENV = os.environ.get("TARGET_DIR", "./notes")
TARGET_DIR = Path(TARGET_DIR_ENV).resolve()

# ChromaDBの永続化先ディレクトリ
DB_PERSIST_DIR = Path("./.chromadb").resolve()

# ChromaDBのコレクション名
COLLECTION_NAME = "markdown_knowledge"

# エンベディングモデル設定
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-small"
