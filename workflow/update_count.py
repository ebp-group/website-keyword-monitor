#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Update website count

Usage:
  update_count.py --db <path-to-db-file> --slug <slug> [--verbose]
  update_count.py (-h | --help)
  update_count.py --version

Options:
  -h, --help                    Show this screen.
  --version                     Show version.
  -d, --db <path-to-db-file>    Path to the SQLite DB.
  -s, --slug <slug>             aWebsite slug
  --verbose                     Option to enable more verbose output.
"""


import sys
import logging
import sqlite3
import traceback
from docopt import docopt
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())
arguments = docopt(__doc__, version='Update website count 1.0')

loglevel = logging.INFO
if arguments['--verbose']:
    loglevel = logging.DEBUG

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=loglevel,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.captureWarnings(True)
log = logging.getLogger(__name__)

conn = None
try:
    conn = sqlite3.connect(arguments['--db'])
    conn.row_factory = sqlite3.Row
    
    slug = arguments['--slug']

    cur = conn.cursor()
    try:
        update_sql = ('UPDATE website set error_count = 0 WHERE slug = ?')
        cur.execute(update_sql, [slug])
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.commit()
except Exception as e:
    print("Error: %s" % e, file=sys.stderr)
    print(traceback.format_exc(), file=sys.stderr)
    sys.exit(1)
