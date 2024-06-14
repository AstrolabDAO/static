from pathlib import Path
from static.libs import converters, web_indexer

if __name__ == "__main__":
  root = Path.cwd() / "static"
  git_root = "/static"
  converted = converters.convert_all(root / "data", {
    "csv": ["json"],
    "yaml": ["json"],
    "json": [],
    "md": ["html"]
  })
  indexed = web_indexer.generate_index_files(root=root, git_root=git_root, missing_alts=converted)
