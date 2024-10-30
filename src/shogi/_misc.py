# -*- coding: UTF8 -*-

from os import getenv

def iter_is_empty(it):
  for _ in it:
    return False
  return True

def lang() -> str:
  l = getenv('LANG')
  if isinstance(l, str) and l.startswith('ru'):
    return 'ru'
  return 'en'
