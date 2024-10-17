"""
Reads in the contributions.yaml file, and updates the entries by hitting the 'source' url.
"""
from collections import OrderedDict
from ruamel.yaml import YAML


def reorder(contribution):
  contribution = OrderedDict(contribution)
  contribution.move_to_end('type', last=False)
  contribution.move_to_end('status', last=False)
  contribution.move_to_end('source', last=False)
  contribution.move_to_end('id', last=False)
  return dict(contribution)

if __name__ == "__main__":
  database_file = '../contributions.yaml'

  # read in database yaml file
  yaml = YAML()
  with open(database_file, 'r') as db:
    data = yaml.load(db)

  contributions_list = data['contributions']

  # update all contributions
  contributions_list = [reorder(contribution) for contribution in contributions_list]

  # write all contributions to database file
  yaml = YAML()
  with open(database_file, 'w') as outfile:
    yaml.dump({"contributions": contributions_list}, outfile)
