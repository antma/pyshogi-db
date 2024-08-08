# -*- coding: UTF8 -*-
''' functions for raising exceptions and logging '''

import logging
import sys
from logging import (DEBUG, INFO)

def raise_value_error(msg):
  '''log error and raise ValueError'''
  logging.error(msg)
  raise ValueError(msg)

def init_logging(log_filename, logging_level = logging.INFO):
  fmt = '%(asctime)s %(levelname)s [%(module)s] %(message)s'
  if log_filename is None:
    logging.basicConfig(level=logging_level, format=fmt, stream=sys.stdout)
  else:
    logging.basicConfig(level=logging_level, format=fmt, filename=log_filename, filemode='w')
