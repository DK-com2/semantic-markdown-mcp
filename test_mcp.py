import time
import indexer
from mcp_server import semantic_search, read_markdown_file, list_markdown_files

print("=== Test: list_markdown_files ===")
files = list_markdown_files()
print("Files:", files)

print("\n=== Test: semantic_search ===")
results = semantic_search("セマンティック検索の意味を教えてください", 2)
print(results)

print("\n=== Test: read_markdown_file ===")
if files:
    try:
        content = read_markdown_file(files[0])
        print("Read success, length:", len(content))
    except Exception as e:
        print("Error reading file:", e)

    print("\n=== Test: Path Traversal Protection ===")
    traversal_path = "../" + files[0]
    error_res = read_markdown_file(traversal_path)
    print("Traversal test result:", error_res)
