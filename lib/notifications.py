#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Send a notification message to Microsoft Teams

Usage:
  notifications.py --matches <matches-file> [--run-url <run-url>] [--verbose] [--no-verify]
  notifications.py (-h | --help)
  notifications.py --version

Options:
  -h, --help                    Show this screen.
  --version                     Show version.
  -m, --matches <matches-file>  Path to the JSONL file containing the matches.
  -r, --run-url <run-url>       URL to the current GitHub run.
  --verbose                     Option to enable more verbose output.
"""

import os
import logging
import jsonlines
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


cards = {}
# iterate over matches
with jsonlines.open(matches_path) as reader:
    for r in reader:
        group = r['group']
        if group in cards:
            card = cards[group]['card']
            section = cards[group]['section']
        else:
            card = pymsteams.connectorcard(team_webhook_url)
            card.title(f"🟢 Standort «{group}» hat Änderungen")
            card.summary(f"🟢 Standort «{group}» hat Änderungen")

            section = pymsteams.cardsection()
            card.addSection(section)
            card[group] = {
                'card': card,
                'section': section,
            }


        match = r['matches'][0]
        section.addFact(f"«{match['keyword']}»", f"[{r['label']}]({r['url']}) ({r['type']}): {match['texts'][0]}")

for group, msg in cards.items():
    if github_run_url:
        msg['card'].addLinkButton("Logs anschauen", github_run_url)

    msg['card'].color("3AB660")

    # Send the notification
    msg['card'].send()
