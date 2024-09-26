"""
Reads a properties txt file from a library's release artifacts,
and validates the contents. If valid, it returns the contents
as an object.

TODO: write tests for validation
"""
import json
from collections import defaultdict
from sys import argv

import requests
from tenacity import retry, stop_after_attempt, wait_fixed

import re
import os


@retry(stop=stop_after_attempt(3),
       wait=wait_fixed(2))
def read_properties_txt(properties_url):
    r = requests.get(properties_url)

    if r.status_code != 200:
        return {
            "status": "failure",
            "error": f"url returning status code: {r.status_code}"
        }

    return {
            "status": "success",
            "text": r.text
        }

def parse_and_validate_text(properties_raw):
    # PARSE
    field_pattern = re.compile(r"^[a-zA-z]+\s*=.*")

    properties = defaultdict()
    field_name = ""
    field_value = ""
    properties_lines = properties_raw.split('\n')
    for line in properties_lines:
        if line.startswith('#') or not line.strip():
            continue
        if field_pattern.match(line):
            if field_name:
                properties[field_name] = field_value
            field_name, field_value = line.split('=')
            field_name = field_name.strip()
            field_value = field_value.split('#')[0].strip()
        else:
            field_value += " " + line.strip()

    if field_name:
        properties[field_name] = field_value

    # VALIDATE
    msgs = []
    if not str(properties['name']).strip():
        msgs.append('name is empty')

    if not str(properties['authors']).strip():
        msgs.append('authors is empty')

    if not str(properties['version']):
        msgs.append('version is empty')
    elif not str(properties['version']).isdigit():
        msgs.append('version is not an integer')

    if not str(properties['url']).strip():
        msgs.append('url is empty')
    elif not (str(properties['url']).strip().startswith('https://') or
        str(properties['url']).strip().startswith('http://')):
        msgs.append('url is not a valid url')

    if not str(properties['sentence']).strip():
        msgs.append('sentence is empty')

    if not str(properties['categories']).strip():
        properties['categories'] = "Other"

    if not str(properties['minRevision']):
        msgs.append('minRevision is empty')
    elif not str(properties['minRevision']).isdigit():
        msgs.append('minRevision is not an integer')

    if not str(properties['maxRevision']):
        msgs.append('maxRevision is empty')
    elif not str(properties['maxRevision']).isdigit():
        msgs.append('maxRevision is not an integer')

    if msgs:
        return {
            "status": "failure",
            "message": msgs,
            "data": properties
        }

    return {
        "status": "success",
        "message": msgs,
        "data": properties
    }

def set_output(output_object):
    with open(os.environ['GITHUB_OUTPUT'],'a') as f:
        f.write(f'result={json.dumps(output_object)}')


if __name__ == "__main__":
    github_output = {"status": "failure", "message": "", "data": {}}
    if len(argv) < 2:
        print("script takes url as argument.\nStopping...")
        github_output["message"] = "url not provided."
        set_output(github_output)
        exit(1)

    url = argv[1]
    if not url.startswith("http"):
        print(f"Url not valid: {url}.\nStopping...")
        github_output["message"] = "url not valid."
        set_output(github_output)
        exit(1)

    print(f"processing url: {url}")  # just for debugging, should do this via logging levels

    try:
        result = read_properties_txt(url)
    except Exception as e:
        print(f'Unable to access url: {url}.\nStopping...')
        github_output["message"] = f"Unable to access url: {url}."
        set_output(github_output)
        exit(1)

    if result['status'] == 'failure':
        print(f"{result['error']}\nStopping...")
        github_output["message"] = result['error']
        set_output(github_output)
        exit(1)

    properties_raw = result['text']
    github_output = parse_and_validate_text(properties_raw)
    set_output(github_output)
    if github_output["status"] == "failure":
        exit(1)