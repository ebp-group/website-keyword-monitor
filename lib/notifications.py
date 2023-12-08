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
import sys
import logging
import jsonlines
from datetime import datetime
import pymsteams
from docopt import docopt
from dotenv import load_dotenv, find_dotenv
import time
load_dotenv(find_dotenv())


arguments = docopt(__doc__, version="Send a notification message to Microsoft Teams 2.0")

log = logging.getLogger(__name__)
loglevel = logging.INFO
if arguments["--verbose"]:
    log.setLevel(logging.DEBUG)

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=loglevel,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.captureWarnings(True)

try:
    matches_path = arguments['--matches']
    github_run_url = arguments['--run-url']
  
    team_webhook_url = os.getenv('MS_TEAMS_WEBHOOK_URL')
    assert team_webhook_url, "MS_TEAMS_WEBHOOK_URL is not set"

    date_str = datetime.now().strftime('%d.%m.%Y')
    cards = {}
    # iterate over matches
    with jsonlines.open(matches_path) as reader:
        for r in reader:
            print(r)
            group = r['group']
            if group in cards:
                card = cards[group]['card']
                section = cards[group]['section']
            else:
                card = pymsteams.connectorcard(team_webhook_url)
                card.title(f"🟢 «{group}» Änderungen {date_str}")
                card.summary(f"🟢 «{group}» Änderungen {date_str}")

                section = pymsteams.cardsection()
                card.addSection(section)
                cards[group] = {
                    'card': card,
                    'section': section,
                }

            match = r['matches'][0]
            # stop after 50 facts
            if len(section.dumpSection().get('facts', [])) < 50:
                section.addFact(f"«{match['keyword']}»", f"[{r['label']}]({r['url']}) ({r['type']}): {match['texts'][0]}")
            elif len(section.dumpSection().get('facts', [])) == 50:
                section.addFact("...", "mehr als 50 Matches vorhanden...")
            else:
                log.info("Can't add more facts to section, skipping.")

    # Sort dict by key
    cards = dict(sorted(cards.items(), key=lambda i: i[0]))

    failed = False
    for group, msg in cards.items():
        try:
            if github_run_url:
                msg['card'].addLinkButton("Logs anschauen", github_run_url)
    
            msg['card'].color("3AB660")
    
            # Send the notification
            msg['card'].send()
            log.info(f"Send notification for \"{group}\"")
            time.sleep(10)
        except pymsteams.TeamsWebhookException as e:
            # catch this exception here, so that all valid messages will be sent, re-raise later
            log.exception(f"Error when sending group {group}")
            failed = True
            continue

    if failed:
        raise Exception("There was an error sending a teams message, see above")

except Exception as e:
    log.exception("Error in notifications.py")
    sys.exit(1)
