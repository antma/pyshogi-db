import unittest

import shogi

class TestShogiPosition(unittest.TestCase):
  def test_init_default(self):
    p = shogi.Position()

if __name__ == '__main__':
  unittest.main()
