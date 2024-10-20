# -*- coding: UTF8 -*-

from datetime import datetime
from enum import IntEnum
from itertools import chain
import json
import logging
import os
from queue import Queue, Empty
import subprocess
from threading import Thread
import time
from typing import Mapping, Optional, Tuple

import log
from shogi import evaluation, kifu
from shogi.game import Game
from shogi.position import Position
from shogi.result import GameResult, description

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
    self.s = None
    if isinstance(param, str):
      self.s = param
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
  def win_rate(self) -> float:
    p = self._d.get('score.cp')
    if not p is None:
      return evaluation.win_rate(p)
    p = self._d['score.mate']
    if p > 0:
      return 1.0
    return 0.0
  def get(self, key: str):
    return self._d.get(key)
  def score_to_short_str(self, side_to_move: int) -> str:
    p = self._d.get('score.cp')
    if not p is None:
      return str(p * side_to_move)
    p = self._d['score.mate']
    return 'm' + str(p * side_to_move)
  def kifu_str(self) -> str:
    if self.s is None:
      log.raise_value_error('InfoMessage.s original engine output is not set')
    return '%[' + self.s + ']'

def enqueue_output(engine):
  engine.enqueue_output()

class USIEngine:
  def __init__(self, params: USIEngineSearchParameters, suffix_name: Optional[str] = None, logfile: bool = False):
    self.params = params
    self._p = None
    self._logfile = logfile
    self._suffix_name = suffix_name
    self._thread = None
    self._queue = None
  def enqueue_output(self):
    try:
      for line in self._p.stdout:
        self._queue.put((line.decode('ascii').rstrip('\n'), time.time()))
      self._queue.put((0, time.time()))
    except IOError as e:
      self._queue.put(e.errno)
  def send(self, cmd):
    logging.debug('SEND[%s] %s', self.params.engine_short_name, cmd)
    self._p.stdin.write((cmd + '\n').encode('ascii'))
    self._p.stdin.flush()
  def recv(self) -> tuple[str, float]:
    s, t = self._queue.get()
    if isinstance(s, int):
      s = os.strerror(s)
    logging.debug('RECV[%s] %s', self.params.engine_short_name, s)
    return (s, t)
  def recv_nowait(self) -> Optional[tuple[str, float]]:
    try:
      s, t = self._queue.get_nowait()
      if isinstance(s, int):
        s = os.strerror(s)
      logging.debug('RECV_NW[%s] %s', self.params.engine_short_name, s)
      return (s, t)
    except Empty:
      return None
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
      return []
    t = time.time()
    self.send('isready')
    a = []
    while True:
      s, _ = self.recv()
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
      stderr = open(params._args[0] + '.log', 'w', encoding = 'UTF8')
    self._queue = Queue()
    self._p = subprocess.Popen(params._args, stdin = subprocess.PIPE, stdout = subprocess.PIPE, cwd = cwd, stderr = stderr)
    self._thread = Thread(target = enqueue_output, args = (self, ))
    self._thread.daemon = True
    self._thread.start()
    self.send('usi')
    a = []
    while True:
      s, _ = self.recv()
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
      self._thread.join()
      self._thread = None
      self._p = None
  def new_game(self):
    self.send('usinewgame')
    self.ping(False)
  def send_go_with_byoyomi(self):
    self.send(f'go wtime 0 btime 0 byoyomi {self.params.time_ms}')
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
    self.send_go_with_byoyomi()
    infos = []
    bestmove = None
    while True:
      s, _ = self.recv()
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
  def analyse_game(self, game: Game):
    self.new_game()
    usi_moves = []
    pos = Position(game.start_pos)
    for m in game.moves:
      pos.do_move(m)
      usi_moves.append(m.usi_str())
      im, _ = self.analyse_position(game.start_pos, usi_moves)
      game.append_comment_before_move(pos.move_no, im.kifu_str())

class USIGame:
  '''for running game between two engine with tkinter (single threaded)'''
  STATE = IntEnum('STATE', ['IDLE', 'ENGINE_THINKING', 'COMPLETE'])
  def __init__(self, sente_engine: USIEngine, gote_engine: USIEngine, start_sfen: Optional[str], usi_moves: Optional[str], output_kifu_filename: Optional[str], resign_score: Optional[int]):
    assert (resign_score is None) or (resign_score > 1000)
    if sente_engine.params.time_ms != gote_engine.params.time_ms:
      log.raise_value_error('Engines have different thinking move settings')
    self._sente_engine = sente_engine
    self._gote_engine = gote_engine
    self._output_kifu_filename = output_kifu_filename
    game = Game(start_sfen)
    self.game = game
    if isinstance(usi_moves, str):
      for s in usi_moves.split():
        game.do_usi_move(s)
    self._thinking_seconds = sente_engine.params.time_ms // 1000
    game.set_tag('sente', sente_engine.params.engine_name)
    game.set_tag('gote', gote_engine.params.engine_name)
    game.set_tag('start_date', datetime.today())
    game.set_tag('time_control', kifu.TimeControl(0, self._thinking_seconds))
    if not start_sfen is None:
      game.set_tag('start_sfen', start_sfen)
    sente_engine.new_game()
    gote_engine.new_game()
    self.state = self.STATE.IDLE
    self._resign_score = -resign_score
    self._start_thinking_time = None
    self._last_info = None
  def is_idle(self):
    return self.state == self.STATE.IDLE
  def is_complete(self):
    return self.state == self.STATE.COMPLETE
  def _on_complete(self):
    self.state = self.STATE.COMPLETE
    if self._output_kifu_filename is None:
      return
    self.game.set_tag('end_date', datetime.today())
    with open(self._output_kifu_filename, 'w', encoding = 'UTF8') as f:
      kifu.game_write_to_file(self.game, f)
  def _time_off(self):
    self.game.set_result(GameResult.TIME)
    self._on_complete()
  def step(self):
    if self.is_complete():
      return
    e = self._sente_engine if self.game.pos.side_to_move > 0 else self._gote_engine
    if self.state == self.STATE.IDLE:
      e.send(self.game.usi_position_command())
      #e.send(f'go btime {s} wtime {s} byoyomi {s}')
      e.send_go_with_byoyomi()
      self._start_thinking_time = time.time()
      self.state = self.STATE.ENGINE_THINKING
      self._last_info = None
      return
    assert self.state == self.STATE.ENGINE_THINKING
    if time.time() - self._start_thinking_time > self._thinking_seconds + 1.0:
      self._time_off()
      return
    best_move = None
    while True:
      p = e.recv_nowait()
      if p is None:
        break
      line, t = p
      if t - self._start_thinking_time > self._thinking_seconds + 0.1:
        self._time_off()
        return
      if line.startswith('info '):
        self._last_info = line
      elif line.startswith('bestmove '):
        a = line.split()
        assert a[0] == 'bestmove'
        best_move = a[1]
        break
      else:
        log.raise_value_error(f'Unknown engine line: {line}')
    if best_move is None:
      return
    im = None
    if isinstance(self._last_info, str) and (not self._resign_score is None):
      im = InfoMessage(self._last_info)
      score = im.score_i16()
      if score < self._resign_score:
        logging.info('RESIGN[%s]: engine score %d is below resign score %d', e.params.engine_short_name, score, self._resign_score)
        best_move = 'resign'
    if im:
      self.game.append_comment_before_move(self.game.pos.move_no, im.kifu_str())
    self.game.do_usi_move(best_move)
    if self.game.has_result():
      logging.debug('Result: %s', description(self.game.game_result))
      self._on_complete()
    else:
      self.state = self.STATE.IDLE
  def run(self, sleep_ms: int):
    '''run game in console'''
    s = 0.001 * sleep_ms
    while self.state != self.STATE.COMPLETE:
      time.sleep(s)
      self.step()

def game_win_rates(game: Game) -> Mapping[int, Tuple[float, str]]:
  p = game.positions()
  d = {}
  for move_no, l in game.comments.items():
    for s in l:
      if s.startswith('%[info ') and s.endswith(']'):
        im = InfoMessage(s[2:-1])
        if im.has_score():
          wr = im.win_rate()
          if game.move_no_to_side_to_move(move_no) < 0:
            wr = 1.0 - wr
          best_move = None
          pv = im.get('pv')
          if pv:
            sfen = p.get(move_no)
            if sfen:
              pos = Position(sfen)
              logging.debug('%s: %s', pos.sfen(), pv[0])
              m = pos.parse_usi_move(pv[0])
              best_move = pos.western_move_str(m)
          d[move_no] = (wr, best_move)
          break
  return d
