#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Send a notification message to Microsoft Teams

Usage:
  notifications.py --url <url-of-website> --label <label> --matches <matches-file> [--run-url <run-url>] [--verbose] [--no-verify]
  notifications.py (-h | --help)
  notifications.py --version

Options:
  -h, --help                    Show this screen.
  --version                     Show version.
  -u, --url <url-of-website>    URL of the website.
  -l, --label <label>           Label of the website.
  -m, --matches <matches-file>  Path to the file containing the matches.
  -r, --run-url <run-url>       URL to the current GitHub run.
  --verbose                     Option to enable more verbose output.
"""

import os
import logging
import pymsteams
from docopt import docopt


arguments = docopt(__doc__, version="Send a notification message to Microsoft Teams 1.0")

log = logging.getLogger(__name__)
loglevel = logging.INFO
if arguments["--verbose"]:
    loglevel = logging.DEBUG

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=loglevel,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.captureWarnings(True)

team_webhook_url = os.getenv('MS_TEAMS_WEBHOOK_URL')
url = arguments['--url']
label = arguments['--label']
matches_path = arguments['--matches']
github_run_url = arguments['--run-url']

# Create the connector card

teams_msg = pymsteams.connectorcard(team_webhook_url)

# Set the content

teams_msg.title(f"🟢 Webseite «${label}» hat Änderungen")
teams_msg.summary(f"🟢 Webseite «${label}» hat Änderungen")

with open(matches_path) as f:
    matches = f.read()

teams_msg.text(f"[${label}](${url}): ${matches}")

teams_msg.addLinkButton("Webseite anschauen", url)
if github_run_url:
    teams_msg.addLinkButton("Logs anschauen", github_run_url)

teams_msg.color("3AB660")

# Send the notification
teams_msg.send()
