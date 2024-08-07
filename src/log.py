# -*- coding: UTF8 -*-
''' functions for raising exceptions and logging '''

import logging

def raise_value_error(msg):
  '''log error and raise ValueError'''
  logging.error(msg)
  raise ValueError(msg)
