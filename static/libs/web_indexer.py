import os
import argparse
import datetime
from pathlib import Path
import re
from jinja2 import Template

EXT_EMOJIS = {
  "folder": "📁",
  "archive": "📦",
  "image": "🖼️",
  "3d": "🕸️",
  "data": "🔢",
  "sound": "💿",
  "video": "🎞️",
  "config": "🛠️",
  "code": "🧩",
  "storage": "💾",
  "docs": "📖",
  "text": "🗒️"
}

EXT_BY_TYPE = {
  "archive": {".zip", ".gz", ".tar", ".7z", ".rar", ".bz2", ".lz"},
  "image": {".jpg", ".jpeg", ".bmp", ".png", ".svg", ".lottie", ".riv", ".psd", ".gif", ".tiff"},
  "3d": {".glsl", ".gltf", ".obj", ".fbx", ".stl", ".amf", ".stp"},
  "data": {".csv", ".json", ".pickle", ".orc", ".proto", ".pqt", ".parquet", ".avro", ".xml", ".xls", ".xlsx", ".xlsm"},
  "sound": {".mp3", ".wav", ".aiff", ".au"},
  "video": {".mp4", ".avi", ".mkv", ".webm", ".mov", ".flv"},
  "config": {".yaml", ".yml", ".toml", ".cfg", ".ini", ".env"},
  "code": {".py", ".js", ".ts", ".java", ".c", ".cpp", ".rs", ".go", ".h", ".hpp", ".html",
           ".pug", ".jsx", ".tsx", ".vue", ".css", ".sass", ".pcss", ".scss", ".php", ".rb",
           ".pl", ".sh", ".bash", ".bat", ".ps1", ".ipynb", ".sol"},
  "storage": {".db", ".sqlite", ".sqlite3", ".sql", ".mdb", ".accdb"},
  "docs": {".md", ".markdown", ".tex", ".rst", ".pdf", ".epub", ".mobi", ".djvu", ".fb2", ".lit", ".pdb", ".azw", ".azw3", ".ibooks"},
  "text": {".txt", ".docx", ".odt", ".doc", ".rtf", ".asc"}
}

DEFAULT_EXCLUDES = {".git", ".vscode", ".idea", "node_modules", "__pycache__", "__init__.py", ".DS_Store", ".gitignore", ".gitattributes", ".gitmodules", ".gitkeep"}

def get_type_and_emoji(filename):
  if os.path.isdir(filename):
    return None, EXT_EMOJIS["folder"]
  ext = os.path.splitext(filename)[1].lower()
  for file_type, extensions in EXT_BY_TYPE.items():
    if ext in extensions:
      return file_type, EXT_EMOJIS[file_type]
  return "???", EXT_EMOJIS["text"]

def humanize_bytes(size, precision=2):
  """Converts bytes to human-readable format (KB, MB, GB, etc.)."""
  power = 2**10
  n = 0
  power_labels = {0 : '', 1: 'k', 2: 'm', 3: 'g', 4: 't'}
  while size > power:
    size /= power
    n += 1
  if power_labels[n] == '':
    precision = 0
  return f"{size:.{precision}f}{power_labels[n]}b"

def create_index_html(directory, template):
  files = os.listdir(directory)
  files.sort(key=lambda f: (os.path.isdir(os.path.join(directory, f)), -os.path.getsize(os.path.join(directory, f)), f.lower()))  # Sort folders first, then by size desc, then name asc
  index_dir = "./static" + directory.rsplit("/static", maxsplit=1)[1]

  file_rows = ""
  for file in files:
    if file in DEFAULT_EXCLUDES:
      continue
    file_path = os.path.join(directory, file)
    if file == "index.html":
      continue
    file_type, emoji = get_type_and_emoji(file_path)
    file_name = f'{emoji} <a href="./{file + "/index.html" if os.path.isdir(file_path) else file}">{file}</a>'
    file_ext = os.path.splitext(file)[1]
    file_ext = f" ({file_ext})" if file_ext else ""
    file_size = os.path.getsize(file_path)
    file_creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M')
    file_rows += f"<tr><td>{file_name}</td><td>{file_type or 'folder'}{file_ext}</td><td>{humanize_bytes(file_size)}</td><td>{file_creation_time}</td></tr>"

  print(f"Creating index file: {index_dir}")
  prev = "./index.html"
  if index_dir != "./static":
    prev = "." + prev # not root
  html_content = template.render(prev_route=prev, directory=index_dir, file_rows=file_rows)

  path = os.path.join(directory, "index.html")
  with open(path, "w") as f:
    f.write(html_content)
  return path

def generate_index_files(root, template=None):
  indexed = []
  is_root = False
  if not template:
    is_root = True
    with open(Path(__file__).parent / "index_tpl.html", "r") as f:
      template = Template(f.read())
  for dirpath, dirnames, filenames in os.walk(root):
    if os.path.basename(dirpath) in DEFAULT_EXCLUDES:
      continue
    indexed.append(create_index_html(dirpath, template))
    for dirname in dirnames:
      sub_dir = os.path.join(dirpath, dirname)
      indexed += generate_index_files(sub_dir, template)
  if is_root:
    print(f"Indexed {len(indexed)} directories")
  return indexed

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Generate index files for directories")
  parser.add_argument("-d", "--directory", type=str, help="The root directory to start indexing")
  args = parser.parse_args()
  generate_index_files(args.directory)
