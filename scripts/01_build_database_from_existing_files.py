"""
Reads in the json files in the sources folder of processing/processing-contributions,
as well as the contribs.txt to output a yaml formatted database file. This is purely to make sure
the content is exactly the same as the contribs.txt file, and json files. This important, because
scripts will be written to go from this database file back to contribs.txt, and source json files.
If the content is the same, then the output of the scripts can be compared with the originals.
"""

import re
import json
import pathlib
from operator import attrgetter, itemgetter

from ruamel.yaml import YAML
from collections import defaultdict


def read_contribs_text(filepath):
  contribs_list = []
  this_contrib = {}
  contrib_empty = True
  contrib_field_counts = defaultdict(int)

  with open(filepath, 'r') as f:
    for line in f.readlines():
      if line.strip() == "":
        if not contrib_empty:
          for key in list(this_contrib.keys()):
            contrib_field_counts[key] += 1
          contribs_list.append(this_contrib)
          this_contrib = {}
          contrib_empty = True

      str_index = line.find("=")  # capture first equals,
      if str_index >= 0:
        field, value = line.split("=", 1)
        this_contrib[field.strip()] = value.strip()
        contrib_empty = False

  with open("contribs_txt_field_counts.json", 'w') as f:
    json.dump(contrib_field_counts, f)

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
  sources_dir = '../sources_original'
  contribs_text_file = '../pde_original/contribs.txt'
  database_file = '../contributions_01.yaml'

  # read in from source files
  sources_dict = read_sources_folder(sources_dir)
  contribs_list = read_contribs_text(contribs_text_file)

  # since desired output is a list of objects, use contribs_list as base, and add missing
  # information, which is props
  for contrib in contribs_list:
    source_contrib = sources_dict[contrib["id"]]
    contrib["props"] = source_contrib["packages"][0]["props"]

  contribs_list = sorted(contribs_list, key=itemgetter('id'))

  yaml = YAML()
  with open(database_file, 'w') as outfile:
    yaml.dump({"contributions": contribs_list}, outfile)

