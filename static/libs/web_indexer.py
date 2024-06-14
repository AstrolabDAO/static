import os
import argparse
import datetime
from pathlib import Path
import re
from jinja2 import Template
import requests

EXT_EMOJIS = {
  "folder": "📁",
  "archive": "📦",
  "image": "🖼️",
  "3d": "🕸️",
  "font": "🇦",
  "table": "田",
  "data": "{}",
  "sound": "💿",
  "video": "🎞️",
  "config": "🛠️",
  "code": "<>",
  "storage": "💾",
  "docs": "📖",
  "text": "🗒️"
}

EXT_BY_TYPE = {
  "archive": {".zip", ".gz", ".tar", ".7z", ".rar", ".bz2", ".lz"},
  "image": {".jpg", ".jpeg", ".bmp", ".png", ".svg", ".ps", ".lottie", ".riv",
            ".psd", ".gif", ".tiff", ".webp", ".ico", ".jxr", ".heic", ".bpg", ".avif"},
  "3d": {".glsl", ".gltf", ".obj", ".fbx", ".stl", ".amf", ".stp"},
  "font": {".ttf", ".otf", ".woff", ".woff2", ".eot", ".afm", ".dfont", ".pfa", ".pfb",
           ".pfm", ".suit", ".mf", ".cff", ".cid", ".otc", ".ttc", ".fnt", ".fon", ".bdf",
           ".pfr", ".sfd", ".otb", ".ttx", ".amfm", ".acfm"},
  "data": {".json", ".pickle", ".proto", ".xml"},
  "table": {".csv", ".tsv", ".tab", ".xls", ".xlsx", ".xlsm", ".ods", ".db", ".dbf",
            ".sqlite", ".sqlite3", ".sql", ".mdb", ".accdb", ".dta", ".sav", ".sas7bdat",
            ".rds", ".rdata", ".feather", ".arrow", ".hdf5", ".h5", ".nc", ".nc4", ".nc4c",
            ".zarr", ".grb", ".grib", ".grib2", ".orc", ".pqt", ".parquet", ".avro"},
  "sound": {".mp3", ".wav", ".aiff", ".au", ".flac", ".m4a", ".ogg", ".wma", ".aac", ".alac",
            ".aif", ".ra", ".ram", ".opus", ".mp2", ".amr", ".dss", ".gsm", ".m3u", ".pls",
            ".mid", ".midi", ".rmi", ".vqf"},
  "video": {".mp4", ".avi", ".mkv", ".webm", ".mov", ".flv", ".vob", ".ogv", ".ogg", ".drc",
            ".mng", ".qt", ".wmv", ".yuv", ".rm", ".rmvb", ".viv", ".asf", ".amv", ".m4p",
            ".m4v", ".mpg", ".mp2", ".mpeg", ".mpe", ".mpv", ".m2v", ".svi", ".3gp", ".3g2",
            ".mxf", ".roq", ".nsv", ".f4v", ".f4p", ".f4a", ".f4b", ".mts", ".m2ts",
            ".divx", ".xvid", ".vcd", ".svcd"},
  "config": {".yaml", ".yml", ".toml", ".cfg", ".ini", ".env", ".conf", ".properties"},
  "code": {".py", ".js", ".ts", ".java", ".c", ".cpp", ".rs", ".go", ".h", ".hpp", ".html",
           ".pug", ".jsx", ".tsx", ".vue", ".css", ".sass", ".pcss", ".scss", ".php", ".rb",
           ".pl", ".sh", ".bash", ".bat", ".ps1", ".ipynb", ".sol", ".sql", ".r", ".swift",
           ".kt", ".cs", ".erl", ".ex", ".exs", ".f90", ".fs", ".hs", ".jl", ".lua", ".m",
           ".mli", ".nim", ".pm", ".rake", ".tsql", ".vhd", ".vhdl"},
  "docs": {".md", ".markdown", ".tex", ".rst", ".pdf", ".epub", ".mobi", ".djvu", ".fb2",
           ".lit", ".pdb", ".azw", ".azw3", ".ibooks"},
  "text": {".txt", ".docx", ".odt", ".doc", ".rtf", ".asc"}
}

DEFAULT_EXCLUDES = {".git", ".vscode", ".idea", "node_modules", "__pycache__", "__init__.py", ".DS_Store", ".gitignore", ".gitattributes", ".gitmodules", ".gitkeep", "setup.bash"}

def get_type_and_emoji(filename):
  if os.path.isdir(filename):
    return "folder", EXT_EMOJIS["folder"]
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

def create_index_html(root, git_root, parent, template, missing_alts={}):
  files = os.listdir(root)
  files.sort(key=lambda f: (os.path.isdir(os.path.join(root, f)), -os.path.getsize(os.path.join(root, f)), f.lower()))  # Sort folders first, then by size desc, then name asc
  index_root = git_root
  index_tree = str(root).rsplit(f"{parent}", maxsplit=1)[1] or "/"
  index_dir = index_root + (index_tree if index_tree != "/" else "")

  file_rows = ""
  for file in files:
    if file in DEFAULT_EXCLUDES:
      continue
    file_path = os.path.join(root, file)
    if file == "index.html":
      continue
    file_type, emoji = get_type_and_emoji(file_path)
    alt = f"https://github.com/AstrolabDAO/{parent}/tree/main{index_dir}/{file}" if file_type == "folder" else\
          f"https://raw.githubusercontent.com/AstrolabDAO/{parent}/main{index_dir}/{file}"
    # alt_tag = "" if requests.get(alt).status_code == 404 else f" <a href=\"{alt}\">git</a>"
    alt_tag = "" if file_path in missing_alts else f" <a href=\"{alt}\">git</a>"
    file_name = f'<span class="icon">{emoji}</span><a href="./{file + "/index.html" if os.path.isdir(file_path) else file}">{file}</a>'
    file_ext = os.path.splitext(file)[1]
    file_ext = f" ({file_ext})" if file_ext else ""
    file_size = os.path.getsize(file_path)
    file_creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M')
    file_rows += f"<tr><td>{file_name}</td><td>{alt_tag}</td><td>{file_type}</td><td>{humanize_bytes(file_size)}</td><td>{file_creation_time}</td></tr>"

  print(f"Creating index file: {index_dir}")
  prev = "./index.html"
  if index_dir != index_root:
    prev = "." + prev
  html_content = template.render(prev_route=prev, directory=index_dir, file_rows=file_rows)

  path = os.path.join(root, "index.html")
  with open(path, "w") as f:
    f.write(html_content)
  return path

def generate_index_files(root, git_root="/", parent=None, template=None, template_path="index_tpl.html", missing_alts={}):
  indexed = []
  is_root = False
  stem = str(root).split("/")[-1]
  parent = parent or stem
  if stem in DEFAULT_EXCLUDES:
    return indexed

  if not template:
    is_root = True
    if template_path.startswith("http"):
      tpl = requests.get(template_path).text # eg. https://cdn.astrolab.fi/libs/index_tpl.html
    else:
      template_path = (Path(__file__).parent / template_path) if not template_path.startswith("/") else template_path
      with open(template_path, "r") as f:
        tpl = f.read()
    template = Template(tpl)

  indexed.append(create_index_html(root=root, git_root=git_root, parent=parent, template=template, missing_alts=missing_alts))

  for dirpath, dirnames, filenames in os.walk(root): # selective recursion (os.walk traverses excluded subfolders)
    dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDES]
    for dirname in dirnames:
      sub_dir = os.path.join(dirpath, dirname)
      indexed += generate_index_files(
        root=sub_dir,
        git_root=git_root,
        parent=parent,
        template=template,
        missing_alts=missing_alts)

  if is_root:
    print(f"Indexed {len(indexed)} directories")
  return indexed


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Generate index files for directories")
  parser.add_argument("-d", "--directory", type=str, help="The root directory to start indexing")
  args = parser.parse_args()
  generate_index_files(args.directory)
