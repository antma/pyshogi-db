#!/usr/bin/python3
# -*- coding: UTF8 -*-
import logging
import os
import sys

PROJECT_PATH = os.getcwd()
SOURCE_PATH = os.path.join(PROJECT_PATH, '..', "src")
sys.path.append(SOURCE_PATH)

import log
from shogi import position

log.init_logging(None, logging.DEBUG)
with open(sys.argv[1], 'r', encoding = 'UTF8') as f:
  for sfen in f:
    pos = position.Position(sfen.rstrip())
