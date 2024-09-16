"""
Creates the contribs.txt file from the contributions.yaml file.
"""

import re
import json
import pathlib
from ruamel.yaml import YAML
from collections import defaultdict


type_list = ['library', 'examples', 'tool', 'mode']
contribs_fields_list = [
    'name', 'authors', 'url', 'categories', 'sentence', 'paragraph',
    'version', 'prettyVersion', 'minRevision', 'maxRevision', 'imports',
    'modes', 'id', 'type', 'download'
]


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


if __name__ == "__main__":
  contribs_text_file = '../pde/contribs.txt'
  database_file = '../contributions.yaml'

  yaml = YAML()
  with open(database_file, 'r') as db:
    data = yaml.load(db)

  with open(contribs_text_file, 'w+') as f:
    for contribution in data['contributions']:
      f.write(contribution['type']+'\n')
      for field in contribs_fields_list:
        if field in contribution:
          f.write(f'{field}={contribution[field]}\n')
        elif field == 'categories':
          f.write(f'{field}=\n')
      f.write('\n')


