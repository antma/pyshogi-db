# -*- coding: UTF8 -*-
import glob
import os
import sys

DIR = os.path.dirname(sys.argv[0])
PROJECT_PATH = os.path.join(DIR, '..')
GAMES_PATH = os.path.join(PROJECT_PATH, 'tests', 'wars')

n = 0
for fn in glob.glob(os.path.join(GAMES_PATH, '*.kif')):
  f, _ = os.path.splitext(fn)
  n = max(n, int(os.path.basename(f)))
n += 1
print(f'{n:04d}')
