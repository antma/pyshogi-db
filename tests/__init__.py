# -*- coding: UTF8 -*-
import logging
import os
import sys

PROJECT_PATH = os.getcwd()
SOURCE_PATH = os.path.join(PROJECT_PATH,"src")
sys.path.append(SOURCE_PATH)

import log
log.init_logging(None, logging.DEBUG)
