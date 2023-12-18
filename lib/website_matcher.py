#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Match keywords against a website content

Usage:
  website_matcher.py --url <url-of-website> --label <label> --group <group> --file <path> --keywords <path> --new <path> [--wait <seconds>] [--output <path>] [--type <type>] [--verbose] [--no-verify]
  website_matcher.py (-h | --help)
  website_matcher.py --version

Options:
  -h, --help                    Show this screen.
  --version                     Show version.
  -u, --url <url-of-website>    URL of the website to monitor.
  -l, --label <label>           Label of the URL.
  -g, --group <group>           Label of the group of URLs.
  -f, --file <path>             Load the hashes of the output from file.
  -k, --keywords <path>         Load the keywords from file.
  -n, --new <path>              Save the new hashes of the output in file.
  -w, --wait <seconds>          Number of seconds to wait for the page to load [default: 3].
  -t, --type <type>             Type of website, one [default: static].
  -o, --output <path>           Save the matched output to a file.
  --verbose                     Option to enable more verbose output.
  --no-verify                   Option to disable SSL verification for requests.
"""  # noqa: E501

import os
import hashlib
import logging
import re
import sys
import urllib.parse
from pprint import pformat
from bs4 import BeautifulSoup
from docopt import docopt
import jsonlines
import urllib3
from requests.exceptions import RequestException
from selenium.common.exceptions import WebDriverException
import download as dl

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
log = logging.getLogger(__name__)


def load_keywords(path):
    keywords = []
    with open(path) as f:
        keywords = [line.strip() for line in f if line.strip()]

    regex_keywords = [
        {"re": re.compile(rf"\b({k})\b", re.IGNORECASE), "keyword": k} for k in keywords
    ]
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
    matches = []
    for text in texts:
        matched_keywords = list(filter(lambda k: k["re"].search(text), keywords))
        if not matched_keywords:
            continue

        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        log.debug(f"Check against hash list to see if it's new: {text_hash}")

        if text_hash in old_hashes:
            log.debug("Text already known, no new match.")
            continue

        log.info("New match found!")
        # add highlights to text
        for k in matched_keywords:
            m = k["re"].search(text)
            short_text = text[max(0, m.start() - 70) : m.end() + 70]
            hl_text = k["re"].sub(r"**\1**", short_text)
            matches.append(
                {
                    "keyword": k["keyword"],
                    "texts": [f"…{hl_text}…"],
                    "hashes": [text_hash],
                }
            )

    return matches


def match_html(soup, keywords, old_hashes):
    matches = []
    for kw_re in keywords:
        log.info(f"Check keyword: {kw_re['keyword']}")
        texts = soup.find_all(string=kw_re["re"])

        source_list = []
        source_hashes = []
        for elem in texts:
            text = elem.get_text(strip=True)
            text = text.replace("\n\n", "\n")
            text = text.replace("\n", " ")
            text = text.replace("  ", " ")
            text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            log.debug(f"Check against hash list to see if it's new: {text_hash}")
            if text_hash in old_hashes:
                log.info("Text already known, no new match.")
                continue

            if not re.search(r"\w", text):
                log.info("Text has no word-characters in it, skipping...")
                continue

            log.info(f"New match found in {url}!")
            # add highlights to text
            m = kw_re["re"].search(text)
            short_text = text[max(0, m.start() - 70) : m.end() + 70]
            hl_text = kw_re["re"].sub(r"**\1**", short_text)
            source_list.append(f"…{hl_text}…")
            source_hashes.append(text_hash)

        unique_source_list = list(set(source_list))
        if len(unique_source_list) > 0:
            log.debug("Unique list:")
            log.debug(pformat(unique_source_list))
            matches.append(
                {
                    "keyword": kw_re["keyword"],
                    "texts": unique_source_list,
                    "hashes": source_hashes,
                }
            )
    return matches


def get_content(url, timeout, dl_type, verify):
    log.info(f"Get content from URL {url}")
    try:
        content_type = dl.get_content_type(url, verify=verify)
        if "application/pdf" in content_type:
            content = dl.pdfdownload(url)
            return (content_type, content)

        if "text" not in content_type:
            raise ValueError(
                f"Unsupported content type: {content_type}, skipping URL {url}"
            )
        if dl_type == "static":
            content = dl.download_content(url, verify=verify)
        elif dl_type == "dynamic":
            content = dl.download_with_selenium(url, timeout)
        else:
            raise Exception(f"Invalid type: {dl_type}")
        return (content_type, content)
    except (RequestException, WebDriverException, ValueError):
        log.exception(f"Error when trying to request from URL: {url}")
        raise ValueError(f"Error when trying to request from URL: {url}")


def get_title(soup, label):
    try:
        return soup.title.string.strip() or label
    except AttributeError:
        return label


def crawl_urls(
    url, label, group, timeout, level, dl_type, keywords, old_hashes, verify=True
):
    if level >= 2 or not url:
        log.debug(f"Level: {level}, URL: {url}, skipping..")
        return

    global all_urls
    if url in all_urls:
        log.debug(f"URL '{url}' already crawled. Skipping...")
        return
    all_urls.append(url)

    try:
        content_type, content = get_content(url, timeout, dl_type, verify)
    except ValueError:
        if level == 0:
            raise
        # if a sub-page returns an error, silently ignore it
        return

    if "application/pdf" in content_type:
        split_text = content.split("\n\n")
        matches = match_texts(split_text, keywords, old_hashes)
        log.debug(f"Matches: {matches}")

        source_type = "PDF"
        title = label

        # create empty soup for PDFs
        soup = BeautifulSoup("", "html.parser")
    else:
        soup = BeautifulSoup(content, "html.parser")
        matches = match_html(soup, keywords, old_hashes)
        source_type = "HTML"
        title = get_title(soup, label)

    if matches:
        yield {
            "type": source_type,
            "group": group,
            "url": url,
            "label": title,
            "matches": matches,
        }

    # find all links with href attribute, limit to 500 results
    for link in soup.find_all("a", href=True, limit=500):
        href = link["href"]
        # skip empty or anchor links
        if not href or href.startswith("#") or href.startswith("mailto:"):
            continue
        absolute_url = urllib.parse.urljoin(url, href)

        link_text = link.string or label
        yield from crawl_urls(
            absolute_url,
            link_text.strip(),
            group,
            timeout,
            level + 1,
            dl_type,
            keywords,
            old_hashes,
            verify,
        )


try:
    arguments = docopt(__doc__, version="Match website 2.0")

    loglevel = logging.INFO
    if arguments["--verbose"]:
        log.setLevel(logging.DEBUG)

    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=loglevel,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.captureWarnings(True)

    url = arguments["--url"]
    file_path = arguments["--file"]
    label = arguments["--label"]
    group = arguments["--group"]
    keywords_path = arguments["--keywords"]
    new_path = arguments["--new"]
    timeout = int(arguments["--wait"])
    dl_type = arguments["--type"]
    verify = not arguments["--no-verify"]
    output = arguments["--output"]

    if not verify:
        urllib3.disable_warnings()

    keywords = load_keywords(keywords_path)
    hashes = load_old_hashes(file_path)

    all_urls = []

    with jsonlines.open(output, mode="w") as writer:
        for result in crawl_urls(
            url, label, group, timeout, 0, dl_type, keywords, hashes, verify
        ):
            texts = []
            for match in result["matches"]:
                hashes.extend(match["hashes"])

            log.debug("Match result:")
            log.debug(pformat(result))
            writer.write(result)

    log.info("Write new hash file...")
    hashes = list(set(hashes))
    hashes.sort()
    hashes_str = "\n".join(hashes)
    with open(new_path, "w") as f:
        f.write(hashes_str)
    log.info(f"Hashes: {hashes_str}")

    url_str = "\n".join(all_urls)
    log.info(f"All checked URLs: {url_str}")

except Exception:
    log.exception("Error in website_matcher.py")
    sys.exit(1)
