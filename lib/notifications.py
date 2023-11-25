#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Send a notification message to Microsoft Teams

Usage:
  notifications.py --location <location> --matches <matches-file> [--run-url <run-url>] [--verbose] [--no-verify]
  notifications.py (-h | --help)
  notifications.py --version

Options:
  -h, --help                    Show this screen.
  --version                     Show version.
  -l, --location <location>     Label of the location.
  -m, --matches <matches-file>  Path to the file containing the matches.
  -r, --run-url <run-url>       URL to the current GitHub run.
  --verbose                     Option to enable more verbose output.
"""

import os
import logging
import csv
from datetime import datetime
import pymsteams
from docopt import docopt
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


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
location = arguments['--location']
matches_path = arguments['--matches']
github_run_url = arguments['--run-url']

# Create the connector card

teams_msg = pymsteams.connectorcard(team_webhook_url)

# Set the content
teams_msg.title(f"🟢 Standort «{location}» hat Änderungen")
teams_msg.summary(f"🟢 Standort «{location}» hat Änderungen")


# add sections
match_section = pymsteams.cardsection()

teams_msg.addSection(match_section)

with open(matches_path, encoding='utf-8', newline='') as f:
    dr = csv.DictReader(f)
    for r in dr:
        print(r)
        match_date = datetime.fromisoformat(r['date']).strftime('%d.%m.%Y')
        match_section.addFact(f"Match vom {match_date}", f"[{r['label']}]({r['url']}): {r['match']}")

if github_run_url:
    teams_msg.addLinkButton("Logs anschauen", github_run_url)

teams_msg.color("3AB660")

# Send the notification
teams_msg.send()
