#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Send a notification message to Microsoft Teams

Usage:
  notifications.py --matches <matches-file> [--run-url <run-url>] [--dry-run] [--verbose] [--no-verify]
  notifications.py (-h | --help)
  notifications.py --version

Options:
  -h, --help                    Show this screen.
  --version                     Show version.
  -m, --matches <matches-file>  Path to the JSONL file containing the matches.
  -r, --run-url <run-url>       URL to the current GitHub run.
  -d, --dry-run                 Only a dry run, no MS Teams notifications are sent.
  --verbose                     Option to enable more verbose output.
"""  # noqa: E501

import os
import sys
import logging
import jsonlines
from datetime import datetime
import pymsteams
from docopt import docopt
from dotenv import load_dotenv, find_dotenv
import time
from rich.table import Table
from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.text import Text

load_dotenv(find_dotenv())


arguments = docopt(
    __doc__, version="Send a notification message to Microsoft Teams 2.0"
)

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

try:  # noqa
    matches_path = arguments["--matches"]
    github_run_url = arguments["--run-url"]

    team_webhook_url = os.getenv("MS_TEAMS_WEBHOOK_URL")
    assert team_webhook_url, "MS_TEAMS_WEBHOOK_URL is not set"

    date_str = datetime.now().strftime("%d.%m.%Y")
    entries = {}
    # iterate over matches
    with jsonlines.open(matches_path) as reader:
        for r in reader:
            group = r["group"]
            if group not in entries:
                entries[group] = {
                    "title": f"🟢 «{group}» Änderungen {date_str}",
                    "facts": [],
                }

            match = r["matches"][0]
            fact = {
                "keyword": f"«{match['keyword']}»",
                "text": f"[{r['label']}]({r['url']}) ({r['type']}): {match['texts'][0]}",  # noqa
                "url": r["url"],
            }
            if fact not in entries[group]["facts"]:
                entries[group]["facts"].append(fact)

    # sort facts
    for k, v in entries.items():
        sorted_facts = sorted(v["facts"], key=lambda d: d["keyword"].lower())
        entries[k]["facts"] = sorted_facts

    # Sort entries by key
    entries = dict(sorted(entries.items(), key=lambda i: i[0]))

    # Log all notifications
    console = Console(force_terminal=True)
    for k, v in entries.items():
        table = Table(title=v["title"], caption_justify="left")
        table.add_column("Keyword", style="magenta", no_wrap=True)
        table.add_column("Text", style="green")
        table.add_column("URL", style="green", overflow="fold")
        num_rows = 0
        for f in v["facts"]:
            table.add_row(f["keyword"], Markdown(f["text"]), f["url"])
            num_rows += 1

        caption_text = Text(f"{num_rows} Entries", style="bold blue")
        table.caption = Padding(caption_text, (0, 0, 2, 0))
        console.print(table)

    # create cards
    cards = {}
    for k, v in entries.items():
        if k in cards:
            card = cards[k]["card"]
            section = cards[k]["section"]
        else:
            card = pymsteams.connectorcard(team_webhook_url)
            card.title(v["title"])
            card.summary(v["title"])

            section = pymsteams.cardsection()
            card.addSection(section)
            cards[k] = {
                "card": card,
                "section": section,
            }

        for fact in v["facts"]:
            if len(section.dumpSection().get("facts", [])) < 50:
                section.addFact(fact["keyword"], fact["text"])
            elif len(section.dumpSection().get("facts", [])) == 50:
                section.addFact("...", "mehr als 50 Matches vorhanden...")
            else:
                log.info("Can't add more facts to section, skipping.")

    if arguments["--dry-run"]:
        log.info("Only a dry run, stopping...")
        sys.exit(0)

    failed = False
    for group, msg in cards.items():
        try:
            if github_run_url:
                msg["card"].addLinkButton("Logs anschauen", github_run_url)

            msg["card"].color("3AB660")

            # Send the notification
            msg["card"].send()
            log.info(f'Send notification for "{group}"')
            time.sleep(5)
        except (pymsteams.TeamsWebhookException, requests.exceptions.RequestException):
            # catch this exception here, so that all valid messages will be sent
            # re-raise later
            log.exception(f"Error when sending group {group}")
            failed = True
            time.sleep(5)
            continue

    if failed:
        raise Exception("There was an error sending a teams message, see above")

except Exception:
    log.exception("Error in notifications.py")
    sys.exit(1)
