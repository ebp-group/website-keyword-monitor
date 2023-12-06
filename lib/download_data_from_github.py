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
  -n, --name <artifact-name>   Download artifact with this name [default: output].
"""

import os
import io
import sys
import zipfile
import logging
from pprint import pprint

from docopt import docopt
from ghapi.all import GhApi
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
arguments = docopt(__doc__, version='download_data_from_github.py 1.0')
name = arguments['--name']

log = logging.getLogger(__name__)
loglevel = logging.INFO

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=loglevel,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.captureWarnings(True)


def filter_artifacts(d):
    return d['name'] == name and d['workflow_run']['head_branch'] == branch

try:
    github_token = os.environ['GITHUB_TOKEN']
    owner = os.getenv('GITHUB_REPO_OWNER', 'ebp-group')
    repo = os.getenv('GITHUB_REPO', 'website-keyword-monitor')
    branch = os.getenv('GITHUB_BRANCH', 'main')
    api = GhApi(owner=owner, repo=repo, token=github_token)
    artifacts = api.actions.list_artifacts_for_repo()['artifacts']

    latest_artificat = next(filter(filter_artifacts, artifacts), {})
    if not latest_artificat:
        log.error(f"ERROR: could not find artifact with name '{name}'.")
        sys.exit(1)

    download = api.actions.download_artifact(artifact_id=latest_artificat['id'], archive_format="zip")

    with zipfile.ZipFile(io.BytesIO(download)) as zip_ref:
        zip_ref.extractall('.')

except Exception as e:
    log.exception("Error in download_data_from_github.py")
    sys.exit(1)
