import unittest

import shogi

class TestShogiPosition(unittest.TestCase):
  def test_init_default(self):
    p = shogi.Position()
    p.sfen()
  def test_init(self):
    self.assertRaises(ValueError, shogi.Position, '9 - - 1')

if __name__ == '__main__':
  unittest.main()
