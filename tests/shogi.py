# -*- coding: UTF8 -*-
import logging
import unittest

import shogi

GAME1 =  ['２六歩(27)', '３四歩(33)', '７六歩(77)', '４四歩(43)', '４八銀(39)', '４二飛(82)', '５八金(49)',
'６二玉(51)', '５六歩(57)', '７二玉(62)', '６八玉(59)', '８二玉(72)', '７八玉(68)', '７二銀(71)',
'２五歩(26)', '３三角(22)', '３六歩(37)', '３二銀(31)', '９六歩(97)', '９四歩(93)', '６八銀(79)',
'５二金(41)', '５七銀(68)', '４三銀(32)', '１六歩(17)', '１四歩(13)', '３五歩(36)',
'同\u3000歩(34)', '４六銀(57)', '３四銀(43)', '３八飛(28)', '４五歩(44)', '３三角成(88)',
'同\u3000桂(21)', '７七角打', '４三金(52)', '３五銀(46)', '同\u3000銀(34)', '同\u3000飛(38)',
'３四歩打', '３六飛(35)', '２八角打', '２四歩(25)', '同\u3000歩(23)', '２六飛(36)', '１九角成(28)',
'２四飛(26)', '４六歩(45)', '同\u3000歩(47)', '同\u3000馬(19)', '２一飛成(24)', '５六馬(46)',
'５七歩打', '６五馬(56)', '１一龍(21)', '７六馬(65)', '４四歩打', '同\u3000金(43)', '３一龍(11)',
'３二飛(42)', '４一龍(31)', '８四香打', '８八香打', '２八歩打', '３七桂(29)', '５二銀打', '４四龍(41)',
'４三銀(52)', '４六龍(44)', '４四歩打', '７六龍(46)']

class TestShogiPosition(unittest.TestCase):
  def test_init_default(self):
    p = shogi.Position()
    self.assertEqual(p.sfen(), shogi.SFEN_INITIAL)
  def test_init(self):
    self.assertRaises(ValueError, shogi.Position, '9 - - 1')
  def test_one_move(self):
    p = shogi.Position()
    mv = shogi.kifu.move_parse(GAME1[0], p.side_to_move, None)
    self.assertIsNotNone(mv)
    u = p.do_move(mv)
    self.assertEqual(p.sfen(), 'lnsgkgsnl/1r5b1/ppppppppp/9/9/7P1/PPPPPPP1P/1B5R1/LNSGKGSNL w - 2')
  def test_game(self):
    p = shogi.Position()
    prev_move = None
    for m in GAME1:
      logging.debug('Move: %s', m)
      mv = shogi.kifu.move_parse(m, p.side_to_move, prev_move)
      self.assertIsNotNone(mv)
      p.do_move(mv)
      prev_move = mv
    self.assertEqual(p.sfen(), 'ln1g5/1ks3r2/1ppppsn2/pl3pp1p/9/P1+R5P/1PBPP1N2/1LK1GS1p1/LN1G5 w BGSP3p 72')
if __name__ == '__main__':
  unittest.main()
