# -*- coding: UTF8 -*-

import json
import logging
import subprocess
from typing import Optional

import log

_INFO_INT_PARAM_S = set(['cp', 'depth', 'seldepth', 'multipv', 'nodes', 'nps', 'time', 'score.cp', 'score.mate'])
_INFO_NO_PARAM_S = set(['lowerbound', 'upperbound'])

class InfoMessage:
  def __init__(self, s: str):
    it = iter(s.split())
    if next(it) != 'info':
      log.raise_value_error(f"'info' is not found in '{s}'")
    d = {}
    key = None
    pv = []
    for s in it:
      if key is None:
        key = s
      elif key in _INFO_INT_PARAM_S:
        d[key] = int(s)
        key = None
      elif key in _INFO_NO_PARAM_S:
        d[key] = None
        key = None
      elif key == 'pv':
        pv.append(s)
      elif key == 'score':
        key += '.' + s
      else:
        log.raise_value_error(f"Unknown key '{key}' in info line '{s}'")
    if key == 'pv':
      d[key] = pv
      key = None
    if not key is None:
      log.raise_value_error(f"Incomplete key '{key}' in info line '{s}'")
    self._d = d
    logging.debug("%s", self.json())
  def json(self) -> str:
    return json.dumps(self._d)

class USIEngine:
  def __init__(self, args, options):
    self._args = args
    self._options = options
    self._p = None
    self.name = None
  def send(self, cmd):
    logging.debug('SEND %s', cmd)
    self._p.stdin.write((cmd + '\n').encode('ascii'))
    self._p.stdin.flush()
  def recv(self) -> str:
    s = self._p.stdout.readline().decode('ascii').rstrip('\n')
    logging.debug('RECV %s', s)
    return s
  def quit(self):
    if self._p is None:
      return None
    self.send('quit')
    try:
      self._p.wait(5.0)
      return True
    except subprocess.TimeoutExpired:
      self._p.terminate()
    return False
  def ping(self) -> list[str]:
    self.send('isready')
    a = []
    while True:
      s = self.recv()
      if s == 'readyok':
        break
      a.append(s)
    return a
  def __enter__(self):
    self._p = subprocess.Popen(self._args, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
    self.send('usi')
    a = []
    while True:
      s = self.recv()
      if s == 'usiok':
        break
      a.append(s)
    for s in a:
      b = s.split()
      if len(b) == 3 and b[0] == 'id' and b[1] == 'name':
        self.name = b[2]
        logging.info('Engine %s', self.name)
    for name, value in self._options.items():
      cmd = f'setoption name {name}'
      if not value is None:
        cmd += f' value {value}'
      self.send(cmd)
    self.ping()
    return self
  def __exit__(self, exl_type, exc_value, traceback):
    if not self._p is None:
      self.quit()
      self._p = None
  def new_game(self):
    self.send('usinewgame')
  def analyse(self, start_position_sfen: Optional[str], usi_moves: Optional[list[str]], time_in_seconds: float):
    s = 'position '
    if start_position_sfen is None:
      s += 'startpos'
    else:
      s += 'sfen ' + start_position_sfen
    if (not usi_moves is None) and (len(usi_moves) > 0):
      s += ' moves'
      for m in usi_moves:
        s += ' ' + m
    self.send(s)
    self.ping()
    t = round(time_in_seconds * 1000.0)
    self.send(f'go movetime {t}')
    infos = []
    while True:
      s = self.recv()
      if s.startswith('info '):
        infos.append(s)
      elif s.startswith('bestmove'):
        break
      else:
        log.raise_value_error(f'Unknown engine line: {s}')
    #TODO: optimization don't parse InfoMessage for all list
    return [ InfoMessage(s) for s in infos]
