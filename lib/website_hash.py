#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hashes of a website selector

Usage:
  website_hash.py --url <url-of-website> --file <path> [--selector <css-selector>] [--output <path>] [--type <type>] [--verbose] [--no-verify]
  website_hash.py (-h | --help)
  website_hash.py --version

Options:
  -h, --help                    Show this screen.
  --version                     Show version.
  -u, --url <url-of-website>    URL of the website to monitor.
  -f, --file <path>             Save the hashes of the selector output in file.
  -s, --selector <css-selector> CSS selector to check for changes [default: body].
  -t, --type <type>             Type of website, one [default: static].
  -o, --output <path>           Save the selector output to a file.
  --verbose                     Option to enable more verbose output.
  --no-verify                   Option to disable SSL verification for requests.
"""

import os
import hashlib
import logging
import re
import sys
from pprint import pformat
from bs4 import BeautifulSoup
from docopt import docopt
import urllib3
import download as dl

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
log = logging.getLogger(__name__)


def get_texts_from_selector(url, selector, verify, dl_type='static'):
    if dl_type == "static":
        content = dl.download_content(url, verify=verify)
    elif dl_type == "dynamic":
        content = dl.download_with_selenium(url, selector)
    else:
        raise Exception(f"Invalid type: {dl_type}")
    soup = BeautifulSoup(content, "html.parser")
    as_list = soup.select(selector)
    if not as_list:
        log.error(f"Selector {selector} not found in {url}")
        sys.exit(1)

    source_list = []
    for elem in as_list:
        text = elem.get_text(strip=True)
        text = text.replace("\n\n", "\n")
        text = text.replace("\n", " ")
        text = text.replace("  ", " ")
        if re.search(r"\w", text):
            source_list.append(text)

    unique_source_list = list(set(source_list))
    log.debug("Unique list:")
    log.debug(pformat(unique_source_list))

    return unique_source_list


def load_keywords():
    keywords = []
    with open(os.path.join(__location__, '..', 'keywords.txt')) as f:
        keywords = [line.strip() for line in f]
    
    regex_keywords = [re.compile(rf'.*{k}.*', re.IGNORECASE) for k in keywords]
    return regex_keywords


def load_old_hashes(path):
    old_hashes = []
    try:
        with open(path) as f:
            old_hashes = [line.strip() for line in f]
    except IOError:
        log.info(f"Hash-File at {path} does not exist.")
    
    return old_hashes


def match_texts(texts, keywords, old_hashes):
    matched = []
    for text in texts:
        if any([p.match(text) for p in keywords]):
            text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if text_hash not in old_hashes:
                matched.append(text)
   
    return matched


def get_text_hashes(texts):
    hashes = []
    for text in texts:
        new_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        hashes.append(new_hash)
 
    return hashes


if __name__ == "__main__":
    arguments = docopt(__doc__, version="Get hash of website 2.0")

    loglevel = logging.INFO
    if arguments["--verbose"]:
        loglevel = logging.DEBUG

    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=loglevel,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.captureWarnings(True)

    url = arguments["--url"]
    file_path = arguments["--file"]
    selector = arguments["--selector"]
    dl_type = arguments["--type"]
    verify = not arguments["--no-verify"]
    output = arguments["--output"]

    if not verify:
        urllib3.disable_warnings()

    texts = get_texts_from_selector(url, selector, verify, dl_type)

    source_text = " ".join(texts)
    if output:
        with open(output, "w") as f:
            f.write(source_text)

    keywords = load_keywords()
    old_hashes = load_old_hashes(file_path)

    # find matches, where a match is defined as:
    # - contains one or more of the defined keywords
    # - the hash of the text is not in the hash-file (i.e. it's something new)
    matches = match_texts(texts, keywords, old_hashes)

    if matches:
        match_str = "\n".join(matches)
        log.info(f"Matches: {match_str}")
        print(match_str)

        log.info("Write new hash file...")
        hashes = get_text_hashes(texts)
        hashes_str = "\n".join(hashes)
        with open(file_path, "w") as f:
            f.write(hashes_str)

        log.info(f"Hashes: {hashes_str}")
    else:
        log.info("No matches found.")