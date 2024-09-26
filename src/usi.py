# -*- coding: UTF8 -*-

from datetime import datetime
from itertools import chain
import json
import logging
import os
import subprocess
import time
from typing import Optional

import log
from shogi import kifu, openings
from shogi.position import Position

_INFO_BOUND_L = ['lowerbound', 'upperbound']
_INFO_SCORE_L = ['score.' + s for s in ['cp', 'mate']]
_INFO_INT_PARAM_S = set(['cp', 'depth', 'seldepth', 'multipv', 'nodes', 'nps', 'time', 'hashfull'] + _INFO_SCORE_L)
_INFO_NO_PARAM_S = set(_INFO_BOUND_L)
_BOOLEAN_S = set(['true','false'])
_MATE_SCORE_I16 = 32000

class USIEngineOption:
  def __init__(self, a: list[str]):
    logging.debug('Parsing option: %s', ' '.join(a))
    it = iter(a)
    if next(it) != 'option':
      log.raise_value_error("Expected 'option'")
    if next(it) != 'name':
      log.raise_value_error("Expected 'name'")
    self.name = next(it)
    if next(it) != 'type':
      log.raise_value_error("Expected 'type'")
    self.type = next(it)
    self.default = None
    self.min = None
    self.max = None
    if self.type == 'button':
      return
    if next(it) != 'default':
      log.raise_value_error("Expected 'default'")
    try:
      self.default = next(it)
    except StopIteration:
      if self.type != 'string':
        log.raise_value_error("Empty default allowed only for string option type")
      return
    if self.type != 'spin':
      return
    self.default = int(self.default)
    if next(it) != 'min':
      log.raise_value_error("Expected 'min'")
    self.min = int(next(it))
    if next(it) != 'max':
      log.raise_value_error("Expected 'max'")
    self.max = int(next(it))
  def check_value(self, value) -> bool:
    if self.type == 'spin':
      return self.min <= value <= self.max
    if self.type == 'filename':
      return isinstance(value, str) and os.path.lexists(value)
    if self.type == 'string':
      return isinstance(value, str)
    if self.type == 'button':
      return value is None
    if self.type == 'check':
      return value in _BOOLEAN_S
    return True

def _short_name(s: str) -> str:
  r = ''
  for c in s:
    if c.isalpha():
      r += c
    else:
      break
  return r

class USIEngineSearchParameters:
  def __init__(self, args: list[str], time_ms: int, hash_size: int, threads: int, extra_options):
    self._args = args
    self.engine_name = None
    self.engine_short_name = None
    self.time_ms = time_ms
    self.hash_size = hash_size
    self.threads = threads
    self.extra_options = extra_options
  def set_engine_name(self, engine_name, suffix_name):
    if not suffix_name is None:
      e = engine_name[:]
      e.append(suffix_name)
    else:
      e = engine_name
    logging.info('Engine %s', e)
    self.engine_name = ' '.join(e)
    self.engine_short_name = _short_name(self.engine_name)

def _info_message_parse(message: str) -> dict:
  it = iter(message.split())
  if next(it) != 'info':
    log.raise_value_error(f"'info' is not found in '{message}'")
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
      log.raise_value_error(f"Unknown key '{key}' in info line '{message}'")
  if key == 'pv':
    d[key] = pv
    key = None
  if not key is None:
    log.raise_value_error(f"Incomplete key '{key}' in info line '{message}'")
  return d

class InfoMessage:
  def __init__(self, param):
    if isinstance(param, str):
      self._d = _info_message_parse(param)
    else:
      assert isinstance(param, dict)
      self._d = param
    logging.debug("%s", self.json())
  def set_score(self, score_i16: int):
    if abs(score_i16) < _MATE_SCORE_I16:
      self._d['score.cp'] = score_i16
    else:
      self._d['score.mate'] = score_i16 - _MATE_SCORE_I16 if score_i16 > 0 else score_i16 + _MATE_SCORE_I16
  def json(self) -> str:
    return json.dumps(self._d)
  def has_score(self) -> bool:
    return any(s in self._d for s in _INFO_SCORE_L)
  def exact_score(self) -> Optional[bool]:
    if not self.has_score():
      return None
    return not any(s in self._d for s in _INFO_BOUND_L)
  def score_i16(self) -> int:
    p = self._d.get('score.cp')
    if not p is None:
      assert abs(p) < _MATE_SCORE_I16
      return p
    p = self._d['score.mate']
    assert abs(p) < 100
    return p + _MATE_SCORE_I16 if p > 0 else p - _MATE_SCORE_I16
  def get(self, key: str):
    return self._d.get(key)
  def score_to_short_str(self, side_to_move: int) -> str:
    p = self._d.get('score.cp')
    if not p is None:
      return str(p * side_to_move)
    p = self._d['score.mate']
    return 'm' + str(p * side_to_move)

class USIEngine:
  def __init__(self, params: USIEngineSearchParameters, suffix_name: Optional[str] = None, logfile: bool = False):
    self.params = params
    self._p = None
    self._logfile = logfile
    self._suffix_name = suffix_name
  def send(self, cmd):
    logging.debug('SEND[%s] %s', self.params.engine_short_name, cmd)
    self._p.stdin.write((cmd + '\n').encode('ascii'))
    self._p.stdin.flush()
  def recv(self) -> str:
    s = self._p.stdout.readline().decode('ascii').rstrip('\n')
    logging.debug('RECV[%s] %s', self.params.engine_short_name, s)
    return s
  def quit(self, timeout = 5.0):
    if self._p is None:
      return None
    self.send('quit')
    try:
      self._p.wait(timeout)
      return True
    except subprocess.TimeoutExpired:
      self._p.terminate()
    return False
  def ping(self, weak: bool = True) -> list[str]:
    if weak and self.params.engine_short_name == 'YaneuraOu':
      logging.debug('Skip sending ping to YaneuraOu (it clears hash)')
      return
    t = time.time()
    self.send('isready')
    a = []
    while True:
      s = self.recv()
      if s == 'readyok':
        break
      a.append(s)
    logging.debug('ping: elapsed time %d ms.', round(time.time() - t) * 1000.0)
    return a
  def __enter__(self):
    params = self.params
    cwd = os.path.dirname(params._args[0])
    stderr = None
    if self._logfile:
      stderr = open(params._args[0] + '.log', 'w')
    self._p = subprocess.Popen(params._args, stdin = subprocess.PIPE, stdout = subprocess.PIPE, cwd = cwd, stderr = stderr)
    self.send('usi')
    a = []
    while True:
      s = self.recv()
      if s == 'usiok':
        break
      a.append(s)
    options = {}
    for s in a:
      b = s.split()
      if len(b) >= 3 and b[0] == 'id' and b[1] == 'name':
        params.set_engine_name(b[2:], self._suffix_name)
      elif (len(b) >= 3) and (b[0] == 'option'):
        o = USIEngineOption(b)
        options[o.name] = o
    #p = options.get('USI_Hash')
    #if p is None:
    #  options['USI_Hash'] = USIEngineOption('USI_Hash type spin default 256 min 1 max 33554432'.split())
    for name, value in chain([('USI_Hash', params.hash_size), ('Threads', params.threads)], params.extra_options.items()):
      p = options.get(name)
      if p is None:
        if not name.startswith('USI_'):
          logging.warning("Skipping unknown USI option '%s'", name)
          continue
      elif not p.check_value(value):
        log.raise_value_error(f"Illegal value '{value}' for USI option '{name}'")
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
    self.ping(False)
  def analyse_position(self, start_position_sfen: Optional[str], usi_moves: Optional[list[str]]):
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
    self.ping(True)
    self.send(f'go wtime 0 btime 0 byoyomi {self.params.time_ms}')
    infos = []
    bestmove = None
    while True:
      s = self.recv()
      if s.startswith('info '):
        infos.append(s)
      elif s.startswith('bestmove '):
        a = s.split()
        assert a[0] == 'bestmove'
        bestmove = a[1]
        break
      else:
        log.raise_value_error(f'Unknown engine line: {s}')
    for s in reversed(infos):
      im = InfoMessage(s)
      if not im.exact_score():
        log.raise_value_error('Last info message has not exact score')
      return (im, bestmove)
    return (None, bestmove)

class _USIGame:
  def __init__(self, start_sfen: Optional[str]):
    self.start_sfen = start_sfen
    self.usi_moves = []
    self.pos = Position(start_sfen)
    self.parsed_moves = []
    self.game_result = None
  def do_usi_move(self, s: str):
    self.usi_moves.append(s)
    m = self.pos.parse_usi_move(s)
    assert m.usi_str() == s
    self.parsed_moves.append(m)
    self.pos.do_move(m)
  def set_result(self, jp: str):
    self.game_result = kifu.game_result_by_jp(jp)

def play_game(output_kifu_file: kifu.KifuOutputFile, sente_engine: USIEngine, gote_engine: USIEngine, start_sfen: Optional[str], usi_moves: Optional[str], test_pv: bool = True):
  if sente_engine.params.time_ms != gote_engine.params.time_ms:
    log.raise_value_error('Engines have different thinking move settings')
  s = sente_engine.params.time_ms // 1000
  h = {
    'sente': sente_engine.params.engine_name,
    'gote': gote_engine.params.engine_name,
    'start_date': datetime.today(),
    'time_control': kifu.TimeControl(0, s),
  }
  if not start_sfen is None:
    h['start_sfen'] = start_sfen
  output_kifu_file.write_headers(h)
  sente_engine.new_game()
  gote_engine.new_game()
  g = _USIGame(start_sfen)
  if not usi_moves is None:
    for s in usi_moves.split():
      g.do_usi_move(s)
  c = {}
  while True:
    sfen = g.pos.sfen(move_no = False)
    logging.debug('%s', sfen)
    i = c.get(sfen, 0)
    if i >= 3:
      g.set_result('千日手')
      break
    c[sfen] = i + 1
    e = sente_engine if g.pos.side_to_move > 0 else gote_engine
    info, best_move = e.analyse_position(g.start_sfen, g.usi_moves)
    if best_move == 'resign':
      g.set_result('投了')
      break
    if test_pv:
      q = Position(g.pos.sfen())
      for s in info.get('pv'):
        m = q.parse_usi_move(s)
        assert m.usi_str() == s
        q.do_move(m)
    g.do_usi_move(best_move)
  output_kifu_file.write_moves(g.parsed_moves)
  if not g.game_result is None:
    logging.info('%s', g.game_result.result)
    output_kifu_file.write_result(g.game_result)
