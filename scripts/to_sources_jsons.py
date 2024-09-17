"""
Creates the json files in the sources folder from the contributions.yaml file.
"""

import re
import json
import pathlib
from ruamel.yaml import YAML
import shutil
from string import punctuation
from collections import defaultdict


json_fields_library = [
    'name', 'authors', 'url', 'categories', 'sentence', 'paragraph', 'imports',
    'id', 'type'
]
json_fields_example = [
    'name', 'authors', 'url', 'categories', 'sentence', 'modes', 'paragraph', 'imports',
    'id', 'type'
]
json_fields_tool = [
    'name', 'authors', 'url', 'categories', 'sentence', 'paragraph', 'imports',
    'id', 'type'
]
json_fields_mode = [
    'name', 'authors', 'url', 'sentence', 'paragraph', 'imports',
    'id', 'type', 'categories'
]
json_package_fields_list = ['mode', 'minRevision', 'maxRevision', 'props', 'download']


def to_sources_dict(contribution_dict):
  if contribution_dict['type'] == 'library':
    sources_dict = {
      field: contribution_dict[field]
      for field in json_fields_library if field in contribution_dict
    }
  elif contribution_dict['type'] == 'examples':
    sources_dict = {
        field: contribution_dict[field]
        for field in json_fields_example if field in contribution_dict
    }
  elif contribution_dict['type'] == 'tool':
    sources_dict = {
      field: contribution_dict[field]
      for field in json_fields_tool if field in contribution_dict
    }
  else:
    sources_dict = {
      field: contribution_dict[field]
      for field in json_fields_mode if field in contribution_dict
    }

  # put authors and categories in list
  sources_dict['authors'] = [sources_dict['authors']] if sources_dict['authors'] else sources_dict['authors']
  sources_dict['categories'] = [
    category for category in sources_dict['categories'].split(',')
  ] if sources_dict['categories'] else None

  sources_dict['packages'] = [
    {
      field:('java' if field == 'mode' else contribution_dict[field])
      for field in json_package_fields_list
    }
  ]

  return sources_dict


if __name__ == "__main__":
  sources_folder = pathlib.Path(__file__).parent.parent / 'sources/'
  database_file = '../contributions.yaml'

  yaml = YAML()
  with open(database_file, 'r') as db:
    data = yaml.load(db)

  if sources_folder.is_dir():
    shutil.rmtree(sources_folder)
  sources_folder.mkdir(parents=True, exist_ok=True)

  for contribution in data['contributions']:
    filename = contribution['name'].replace(':','').replace('/','').replace(' ','_') + '.json'
    this_filepath = sources_folder / filename
    with open(this_filepath, 'w') as f:
      json.dump(to_sources_dict(contribution),f,indent=2)


