from pathlib import Path
from static.libs import converters, web_indexer

if __name__ == "__main__":
  root = Path.cwd() / "static"
  converted = converters.convert_all(root / "data", {
    "csv": ["json"],
    "yaml": ["json"],
    "json": [],
    "md": ["html"]
  })
  indexed = web_indexer.generate_index_files(root)
