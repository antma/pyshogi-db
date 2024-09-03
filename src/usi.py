# -*- coding: UTF8 -*-

import logging
import subprocess

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
