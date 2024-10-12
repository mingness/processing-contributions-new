"""
Reads a properties txt file from a library's release artifacts,
and validates the contents. If valid, it returns the contents
as an object.

TODO: write tests for validation
"""
import json
import argparse

import requests
from tenacity import retry, stop_after_attempt, wait_fixed
import re
import os


@retry(stop=stop_after_attempt(3),
       wait=wait_fixed(2),
       reraise=True)
def read_properties_txt(properties_url):
    r = requests.get(properties_url)

    if r.status_code != 200:
        raise FileNotFoundError(f"status code {r.status_code} returned for url {r.url}")

    return r.text

def parse_text(properties_raw):
    msg = ''
    field_pattern = re.compile(r"^[a-zA-z]+\s*=.*")

    properties = {}
    field_name = ""
    field_value = ""
    properties_lines = properties_raw.split('\n')
    for line in properties_lines:
        if line.startswith('#') or not line.strip():
            continue
        if field_pattern.match(line):
            # store previous key-value pair
            if field_name:
                properties[field_name] = field_value
            # process current line
            line_split = line.split('=')
            if len(line_split) != 2:
                msg += f'split not equal to 2 for line {line}'
                field_value += " " + line.strip()
                continue
            field_name, field_value = line_split
            field_name = field_name.strip()
            field_value = field_value.split('#')[0].strip()
        else:
            field_value += " " + line.strip()

    if field_name:
        properties[field_name] = field_value

    # manual fixes
    if 'authorList' in properties:
        properties['authors'] = properties.pop('authorList')

    if 'categories' not in properties or not str(properties['categories']).strip():
        properties['categories'] = "Other"

    if 'minRevision' not in properties or not str(properties['minRevision']).strip():
        properties['minRevision'] = '0'

    if 'maxRevision' not in properties or not str(properties['maxRevision']).strip():
        properties['maxRevision'] = '0'

    return properties, msg

def validate_text(properties: dict):
    msgs = []
    if 'name' not in properties or not str(properties['name']).strip():
        msgs.append('name is empty')

    if 'authors' not in properties or not str(properties['authors']).strip():
        msgs.append('authors is empty')

    if 'version' not in properties or not str(properties['version']):
        msgs.append('version is empty')
    elif not str(properties['version']).isdigit():
        msgs.append(f'version, {properties["version"]}, is not an integer')

    if 'url' not in properties or not str(properties['url']).strip():
        msgs.append('url is empty')
    elif not (str(properties['url']).strip().startswith('https://') or
        str(properties['url']).strip().startswith('http://')):
        msgs.append(f'url, {properties["url"]}, is not a valid url')

    if 'sentence' not in properties or not str(properties['sentence']).strip():
        msgs.append('sentence is empty')

    if 'minRevision' not in properties or not str(properties['minRevision']):
        msgs.append('minRevision is empty')
    elif not str(properties['minRevision']).isdigit():
        msgs.append(f'minRevision, {properties["minRevision"]}, is not an integer')

    if 'maxRevision' not in properties or not str(properties['maxRevision']):
        msgs.append('maxRevision is empty')
    elif not str(properties['maxRevision']).isdigit():
        msgs.append(f'maxRevision, {properties["maxRevision"]}, is not an integer')

    return msgs


def parse_and_validate_text(properties_raw):
    properties, _ = parse_text(properties_raw)
    msgs = validate_text(properties)

    if msgs:
        raise ValueError(";".join(msgs))

    return properties


def set_output(output_object):
    with open(os.environ['GITHUB_OUTPUT'],'a') as f:
        if isinstance(output_object, str):
            f.write(f'props={output_object}')
        else:
            f.write(f'props={json.dumps(output_object)}')


if __name__ == "__main__":
    # this is used by github workflow. Add type to object
    parser = argparse.ArgumentParser()
    parser.add_argument('type')
    parser.add_argument('url')
    args = parser.parse_args()

    type_ = args.type
    url = args.url
    if not url.startswith("http"):
        print(f"Url not valid: {url}.\nStopping...")
        set_output(f"Url is not valid. It should start with http(s).")
        raise AssertionError

    print(f"url: {url}")  # just for debugging, should do this via logging levels

    try:
        properties_raw = read_properties_txt(url)
    except FileNotFoundError as e:
        set_output(f'Error: {e}')
        raise e

    print(f"properties text: {properties_raw}")  # just for debugging, should do this via logging levels

    try:
        props = parse_and_validate_text(properties_raw)
    except Exception as e:
        set_output(f'Error(s) when parsing file: {e}')
        raise e

    props["props"] = url
    props["type"] = type_
    print(f"properties dict: {props}")  # just for debugging, should do this via logging levels
    set_output(props)
