"""
given properties, add a new contribution to the contributions.yaml database file.
"""
import json
from sys import argv

from ruamel.yaml import YAML

if __name__ == "__main__":
    if len(argv) < 2:
        print("script takes json string as argument.\nStopping...")
        raise ValueError

    props = json.loads(argv[1])

    # open database
    database_file = '../contributions.yaml'

    yaml = YAML()
    with open(database_file, 'r') as db:
        data = yaml.load(db)

    contributions_list = list(data['contributions'])

    # find max index
    max_index = max([int(contribution["id"]) for contribution in contributions_list])

    # append new contribution with next index
    props["id"] = f"{(max_index + 1):03d}"
    contributions_list.append(props)

    # write all contributions to database file
    with open(database_file, 'w') as db:
        yaml.dump({"contributions": contributions_list}, db)
