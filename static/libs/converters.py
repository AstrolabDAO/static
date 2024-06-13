import argparse
import csv
import json
import os
import markdown
import re
import ruamel.yaml as yaml
from io import StringIO

CSV_DELIMITERS = ",;|"

def get_data(data):
  if os.path.isfile(str(data)):
    with open(data, 'r') as f:
      return f.read()
  return data

def first_delimiter(s, delimiters=CSV_DELIMITERS):
  match = re.search(f"[{re.escape(delimiters)}]", s)
  return match.group() if match else None

def parse(s):
  if type(s) in (dict, list, tuple):
    return parse_nested(s)
  if type(s) in (int, float, bool) or str(s).lower() in ('none', 'null', ''):
    return s
  try:
    return int(s)
  except Exception:
    try:
      return float(s)
    except Exception:
      if len(s) > 1 and s[0] + s[-1] in ('""', "''"):
        s = s[1:-1]
      if len(s) > 1 and s[0] in ('[', '{'):
        return parse_nested(s)
      return s

def parse_nested(s, delimiter=None):
  """Parses nested lists/dicts from a string representation."""
  if type(s) is dict:
    return {k: parse(v) for k, v in s.items()}
  if type(s) is list:
    return [parse(x) for x in s]
  try:
    return json.loads(s)
  except (json.JSONDecodeError, TypeError):
    if s[0] == "[":
      s = s[1:-1]
    delimiter, newlines = first_delimiter(s), s.count("\n")
    if not newlines:
      return [parse(s)] if not delimiter else [parse(x) for x in s.split(delimiter)]
    return [parse(x) for x in csv.reader(StringIO(s), delimiter=delimiter).__next__() if x]

def csv_to_json(csv_data, headers=[]):
  """Converts CSV (file or string) to JSON, respecting the header row."""
  csv_data = get_data(csv_data)
  reader = csv.DictReader(StringIO(csv_data))
  if not headers:
    headers = reader.fieldnames # should be the first row!
  result = []
  for row in reader:
    parsed_row = {}
    for key, value in row.items():
      parts = key.split(".")
      current = parsed_row
      for part in parts[:-1]:
        current.setdefault(part, {})
        current = current[part]
      current[parts[-1]] = parse(value)
    result.append(parsed_row)
  return json.dumps(result, indent=2)

def json_to_csv(json_data):
  """Converts JSON (file or string) to CSV, flattening nested fields."""
  json_data = get_data(json_data)
  data = json.loads(json_data) if isinstance(json_data, str) else json_data

  def flatten(data, prefix=''):
    flattened = {}
    for key, value in data.items():
      if isinstance(value, dict):
        flattened.update(flatten(value, prefix + key + '.'))
      else:
        flattened[prefix + key] = value
    return flattened

  flat_data = [flatten(row) for row in data]
  output = StringIO()
  writer = csv.DictWriter(output, fieldnames=flat_data[0].keys())
  writer.writeheader()
  writer.writerows(flat_data)
  return output.getvalue()

def yaml_to_json(yaml_data):
  """Converts YAML (file or string) to JSON."""
  yaml_data = get_data(yaml_data)
  parser = yaml.YAML(typ='safe', pure=True)
  yaml_data = parser.load(yaml_data)
  return json.dumps(yaml_data, indent=2)

def json_to_yaml(json_data):
  """Converts JSON (file or string) to YAML."""
  json_data = get_data(json_data)
  data = json.loads(json_data) if isinstance(json_data, str) else json_data
  return yaml.dump(parse(data), default_style='|', default_flow_style=False)

def markdown_to_html(md_data, extensions=[]):
  """Converts Markdown text to HTML using the python-markdown library."""
  md_data = get_data(md_data)
  md = markdown.Markdown(extensions=extensions)
  html = md.convert(md_data)
  return html

EXT_BY_ALIAS = {
  "json": "json",
  "csv": "csv",
  "yml": "yaml",
  "yaml": "yaml",
  "md": "md",
  "markdown": "md"
}

CONVERTERS = {
  "csv": {"json": csv_to_json, "yaml": lambda x: json_to_yaml(csv_to_json(x)), "md": lambda x: markdown_to_html(csv_to_json(x))},
  "json": {"csv": json_to_csv, "yaml": json_to_yaml, "md": lambda x: markdown_to_html(json_to_yaml(x))},
  "yaml": {"json": yaml_to_json, "csv": json_to_csv, "md": lambda x: markdown_to_html(json_to_yaml(x))},
  "md": {"html": markdown_to_html}
}

def convert_all(path, conversion_map={
  "csv": ["json", "yaml"],
  "json": ["csv", "yaml"],
  "yaml": ["json", "csv"],
  "md": ["html"]
}):

  """Crawls a directory and converts files based on the mapping."""
  created = []
  print(f"Converting files in {path}...")
  for root, _, files in os.walk(path):
    for file in files:
      src = os.path.join(root, file)
      ext = EXT_BY_ALIAS.get(os.path.splitext(file)[1].lower()[1:], "unsupported")

      if ext in conversion_map:
        for target_ext in conversion_map[ext]:
          dst = os.path.splitext(src)[0] + "." + target_ext # create the output file name
          print(f"Converting {src} to {dst}...")
          try:
            convert = CONVERTERS[ext][target_ext]
            with open(dst, "w") as f:
              f.write(convert(src))
            created.append(dst)
          except Exception as e: # catch any conversion errors
            print(f"Error converting {src}: {e}")
            continue # log and move on to the next file
  print(f"Converted {len(created)} files.")
  return created

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Convert files in a directory")
  parser.add_argument("-d", "--directory", type=str, help="The root directory to start converting")
  args = parser.parse_args()
  convert_all(args.directory)
