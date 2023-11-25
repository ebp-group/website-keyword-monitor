#!/usr/bin/env python
# coding: utf-8
"""Download latest artifact from GitHub Actions

Usage:
  download_data_from_github.py [-n <artifact-name>]
  download_data_from_github.py (-h | --help)
  download_data_from_github.py --version

Options:
  -h, --help                   Show this screen.
  --version                    Show version.
  -n, --name <artifact-name>   Download artifact with this name [default: matches].
"""

import os
import io
import sys
import zipfile
from pprint import pprint

from docopt import docopt
from ghapi.all import GhApi
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
arguments = docopt(__doc__, version='download_data_from_github.py 1.0')
name = arguments['--name']

# read data.pkl from GitHub Actions Artifacts
github_token = os.environ['GITHUB_TOKEN']
owner = os.getenv('GITHUB_REPO_OWNER', 'ebp-group')
repo = os.getenv('GITHUB_REPO', 'website-keyword-monitor')
api = GhApi(owner=owner, repo=repo, token=github_token)
artifacts = api.actions.list_artifacts_for_repo()['artifacts']

latest_artificat = next(filter(lambda x: x['name'] == name, artifacts), {})
if not latest_artificat:
    print(f"ERROR: could not find artifact with name '{name}'.", file=sys.stderr)
    sys.exit(1)

download = api.actions.download_artifact(artifact_id=latest_artificat['id'], archive_format="zip")

with zipfile.ZipFile(io.BytesIO(download)) as zip_ref:
    zip_ref.extractall('.')

#df = pd.read_pickle(f"data-{city}.pkl")
#print(df[['name', 'wikidata', 'id', 'type']])

