"""
Reads in the broken, skipped, and sources conf files in the scripts folder, to
output a yaml formatted database file. Read in even commented out lines, but label
them as deprecated.

This database file will become the source of truth, from which the json files for
the website, and the contribs.txt file for the contribution manager are derivatives.

the script build_contribs.py was used as a reference.
"""
from operator import itemgetter
import re
from pathlib import Path

from ruamel.yaml import YAML
from tenacity import RetryError

from parse_and_validate_properties_txt import read_properties_txt, parse_text
from scripts.parse_and_validate_properties_txt import validate_text

def read_sources_file(sources_file):
  sources_dict = {}

  # extract id and source url from sources.conf
  with open(sources_file, 'r') as sources:
    type_ = ''
    for line in sources.readlines():
      # if header, pull type, and category
      line = line.strip()
      if line.startswith('['):
        line_split = line[1:-1].split(':')
        type_ = line_split[0].strip().lower()
        this_category = ''
        if len(line_split) == 2 and line_split[1].strip():
          this_category = line_split[1].strip()

      result = url_pattern.findall(line)
      if result:
        notes_msg = ''
        is_commented_out = False
        index_str, props_url = result[0]

        if index_str.startswith('#'):
          is_commented_out = True
          index_str = index_str[1:].strip()

          props_split = props_url.split('#')
          if len(props_split) > 1:
            props_url, msg = props_split
            notes_msg += f'commented out with {msg}; '
          else:
            props_url = props_url.strip()
            notes_msg += f'commented out; '

        else:
          index_str = index_str.strip()
          props_url = props_url.strip()

        if index_str not in sources_dict:
          sources_dict[index_str] = {
            'props': props_url,
            'is_commented_out': is_commented_out,
            'type': type_,
          }
          if is_commented_out:
            sources_dict[index_str]['commented_msg'] = notes_msg

        # add this category to list of categories
        if this_category:
          if 'categories' not in sources_dict[index_str]:
            sources_dict[index_str]['categories'] = []
          sources_dict[index_str]['categories'].append(this_category)
  return sources_dict

if __name__ == "__main__":
  sources_file = 'sources.conf'
  broken_file = 'broken.conf'
  skipped_file = 'skipped.conf'
  database_file = '../contributions.yaml'
  log_file = 'from_sources_conf.log'

  # read in sources.conf, and create dict of id to url
  url_pattern = re.compile(r"(.*)\\(.*)")

  # broken.conf are contributions that are legacy
  broken_ids = [line.rstrip('\n') for line in open(broken_file)]
  # skipped.conf are contributions to omit
  skipped_ids = [line.rstrip('\n') for line in open(skipped_file)]

  sources_dict = read_sources_file(sources_file)
  index_str_list = sorted(list(sources_dict.keys()))

  contribs_list = []
  with open(log_file, 'w') as log:
    for index_str in index_str_list:
      source_dict = sources_dict[index_str]
      props_url = source_dict['props']
      type_ = source_dict['type']
      log_msg = []

      if source_dict['is_commented_out']:
        log.write(f'{index_str}, {props_url}, {source_dict["commented_msg"]}\n')

      try:
        properties_raw = read_properties_txt(props_url)
      except (FileNotFoundError) as e:
        log_msg.append(f'file not found, {e}')
        log.write(f'{index_str}, {props_url}, file not found: {e}\n')
        contribs_list.append(
          {
            'id': index_str,
            'source': props_url,
            'type': type_,
            'status': 'BROKEN',
            'log': log_msg
          }
        )
        continue
      except Exception as e:
        log_msg.append(f'url timeout')
        log.write(f'{index_str}, {props_url}, url timeout\n')
        contribs_list.append(
          {
            'id': index_str,
            'source': props_url,
            'type': type_,
            'status': 'BROKEN',
            'log': log_msg
          }
        )
        continue

      props, msg = parse_text(properties_raw)
      if msg:
        log_msg.append(f'parse found unexpected line, {msg}')
        log.write(f'{index_str}, {props_url}, parse found unexpected line: {msg}\n')

      msgs = validate_text(props)

      if msgs:
        log_msg.append(f'invalid file, {msgs}')
        log.write(f'{index_str}, {props_url}, invalid file: {msgs}\n')
        contribs_list.append(
          {
            'id': index_str,
            'source': props_url,
            'type': type_,
            'status': 'BROKEN',
            'log': log_msg
          }
        )
        continue

      props['source'] = props_url
      props['id'] = index_str
      props['status'] = 'VALID'
      props['type'] = type_

      # process category list
      if props['categories']:
        props['categories'] = sorted(props['categories'].strip('"').split(','))
      else:
        props['categories'] = None

      if 'download' not in props:
        props['download'] = props_url[:props_url.rfind('.')] + '.zip'

      if source_dict['is_commented_out']:
        props['status'] = 'DEPRECATED'

      if index_str in broken_ids:
        log_msg.append(f'in broken conf')
        log.write(f'{index_str}, {props_url}, in broken conf\n')
        props['override'] = {'maxRevision': '228'}

      if index_str in skipped_ids:
        log_msg.append(f'in skipped conf')
        log.write(f'{index_str}, {props_url}, in skipped conf\n')
        props['status'] = 'BROKEN'

      # these are categories dictated by sources.conf. override what is in the properties file
      if 'categories' in source_dict:
        if 'override' in props:
          props['override']['categories'] =source_dict['categories']
        else:
          props['override'] = {'categories': source_dict['categories']}

      if log_msg:
        props['log'] = log_msg

      contribs_list.append(dict(props))


  contribs_list = sorted(contribs_list, key=itemgetter('id'))

  # write all contributions to database file
  yaml = YAML()
  with open(database_file, 'w') as outfile:
    yaml.dump({"contributions": contribs_list}, outfile)
