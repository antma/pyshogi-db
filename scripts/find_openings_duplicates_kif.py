#!/usr/bin/python3
# -*- coding: UTF8 -*-
from collections import defaultdict
import glob
import logging
import os
import sys

PROJECT_PATH = os.path.join(os.getcwd(), '..')
SOURCE_PATH = os.path.join(PROJECT_PATH, "src")
sys.path.append(SOURCE_PATH)

import log

def duplicates(path):
  d = defaultdict(list)
  for fn in glob.glob(os.path.join(TEST_PATH, path, '*.kif')):
    t = os.path.basename(fn)
    i = t.index('-')
    suffix = t[i+1:]
    suffix, ext = os.path.splitext(suffix)
    logging.debug('%s: %s, fn', fn, suffix)
    d[suffix].append(os.path.join(path, t))
  for suffix, l in d.items():
    if len(l) > 1:
      logging.warning('%s: %s', suffix, l)

log.init_logging(None, logging.INFO)
TEST_PATH = os.path.join(PROJECT_PATH, 'tests')
duplicates('openings')
duplicates('castles')
