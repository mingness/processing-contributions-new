"""
Reads in the json files in the sources folder of processing/processing-contributions,
as well as the contribs.txt to output a yaml formatted database file. This is purely to make sure
the content is exactly the same as the contribs.txt file, and json files. This important, because
scripts will be written to go from this database file back to to contribs.txt, and source json files.
If the content is the same, then the output of the scripts can be compared with the originals.
"""

import re
import json
import pathlib
from ruamel.yaml import YAML


def read_contribs_text(filepath):
  contribs_list = []
  this_contrib = {}
  contrib_empty = True

  url_pattern = re.compile(r"(.*)=(.*)")

  with open(filepath, 'r') as f:
    for line in f.readlines():
      if line.strip() == "" and not contrib_empty:
        contribs_list.append(this_contrib)
        this_contrib = {}
        contrib_empty = True
      result = url_pattern.findall(line)
      if result:
        field, value = result[0]
        this_contrib[field] = value
        contrib_empty = False

  return contribs_list


def read_sources_folder(folderpath):
  sources_dict = {}

  sources_folder_path = pathlib.Path(folderpath)
  for json_file in sources_folder_path.glob('*.json'):
    with open(json_file, 'r') as f:
      this_dict = json.loads(f.read())
      sources_dict[this_dict["id"]] = this_dict

  return sources_dict


if __name__ == "__main__":
  sources_dir = '../sources'
  contribs_text_file = '../pde/contribs.txt'
  database_file = '../contributions.yaml'

  # read in from source files
  sources_dict = read_sources_folder(sources_dir)
  # print(sources_dict)
  contribs_list = read_contribs_text(contribs_text_file)
  # print(contribs_list)

  # since desired output is a list of objects, use contribs_list as base, and add missing
  # information, which is props
  for contrib in contribs_list:
    source_contrib = sources_dict[contrib["id"]]
    contrib["props"] = source_contrib["packages"][0]["props"]

  # print(contribs_list)

  yaml = YAML()
  with open(database_file, 'w') as outfile:
    yaml.dump({"contributions": contribs_list}, outfile)

