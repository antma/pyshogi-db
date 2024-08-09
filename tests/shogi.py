# -*- coding: UTF8 -*-
import inspect
import logging
import os
import unittest

import shogi

MODULE_DIR = os.path.dirname(inspect.getfile(inspect.currentframe()))

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

GAME2 = ['７六歩(77)', '８四歩(83)', '５六歩(57)', '３四歩(33)', '５五歩(56)', '４二玉(51)', '５八飛(28)',
'６二銀(71)', '７七角(88)', '７四歩(73)', '６八銀(79)', '７三銀(62)', '５七銀(68)', '６四銀(73)',
'６六銀(57)', '３二銀(31)', '５四歩(55)', '同\u3000歩(53)', '同\u3000飛(58)', '３三銀(32)',
'５八飛(54)', '４四銀(33)', '４八玉(59)', '３二玉(42)', '３八玉(48)', '５二金(61)', '２八玉(38)',
'７三桂(81)', '３八銀(39)', '８五歩(84)', '１六歩(17)', '９四歩(93)', '９六歩(97)', '６五桂(73)',
'６八角(77)', '８六歩(85)', '同\u3000角(68)', '５五銀(44)', '同\u3000銀(66)',
'同\u3000銀(64)', '５四歩打', '５六歩打', '５三歩成(54)', '５七歩成(56)', '９八飛(58)', '８五銀打',
'９七角(86)', '９六銀(85)', '５二と(53)', '同\u3000金(41)', '５四歩打', '９七銀成(96)',
'同\u3000飛(98)', '６四角打', '５三銀打', '同\u3000金(52)', '同\u3000歩成(54)',
'同\u3000角(64)', '５四銀打', '９七角成(53)', '同\u3000桂(89)', '４七と(57)', '同\u3000銀(38)',
'５七桂(65)', '５九金(69)', '４九桂成(57)', '同\u3000金(59)', '８八飛打', '５八歩打', '８九飛成(88)',
'３九金打', '９九龍(89)', '７一角打', '８七飛成(82)', '５三角成(71)', '４二金打', '４五桂打', '４一香打',
'４二馬(53)', '同\u3000香(41)', '５二金打', '４四銀(55)', '５三銀成(54)', '４五銀(44)', '４二金(52)',
'３三玉(32)', '４三成銀(53)', '２四玉(33)', '２六香打']

SENTE_WINS = [(102, 'l5+R1k/6gLp/r1n1p2p+L/p4sN2/1p2sb1P1/2P2p1N1/PP5G1/4PG1K1/L8 w GNPb2s6p 194')]
GOTE_WINS = [(10, 'lr6p/4g1k1l/3sN2pl/ppp1P1N2/4ppb2/PLPp2N2/NP3PP2/3G1S3/+p3K2Pr b GSPbgsp 111')]

class TestShogiPiece(unittest.TestCase):
  def test_to_string(self):
    self.assertEqual(shogi.piece.to_string(shogi.piece.DRAGON), '+R')
    self.assertEqual(shogi.piece.to_string(-shogi.piece.DRAGON), '+r')
    self.assertEqual(shogi.piece.to_string(shogi.piece.HORSE), '+B')
    self.assertEqual(shogi.piece.to_string(-shogi.piece.HORSE), '+b')

class TestShogiPosition(unittest.TestCase):
  def test_init_default(self):
    p = shogi.Position()
    self.assertEqual(p.sfen(), shogi.SFEN_INITIAL)
  def _test_fen(self, fen):
    p = shogi.Position(fen)
    self.assertEqual(p.sfen(), fen)
  def test_init(self):
    self.assertRaises(ValueError, shogi.Position, '9 - - 1')
    self._test_fen('+B2g1ksn+L/6g2/9/9/4+r4/9/4+b4/7R1/LNSGKGSN1 w SN2L18P 84')
    self._test_fen('+B2g1ksn+L/6g2/9/9/4+r4/9/9/5K1R1/L+b1G1GSN1 b SN2L18Psn 87')
  def test_one_move(self):
    p = shogi.Position()
    mv = shogi.kifu.move_parse(GAME1[0], p.side_to_move, None)
    self.assertIsNotNone(mv)
    u = p.do_move(mv)
    self.assertEqual(p.sfen(), 'lnsgkgsnl/1r5b1/ppppppppp/9/9/7P1/PPPPPPP1P/1B5R1/LNSGKGSNL w - 2')
  def _check_game(self, game, fens):
    p = shogi.Position()
    prev_move = None
    d = dict(map(lambda t: (int(list(t[0].split(' '))[3]) - 2, t[0]), fens))
    for i, m in enumerate(game):
      logging.debug('Move: %s', m)
      mv = shogi.kifu.move_parse(m, p.side_to_move, prev_move)
      self.assertIsNotNone(mv)
      logging.debug('Parsed move: %s', mv)
      p.do_move(mv)
      prev_move = mv
      q = d.get(i)
      if not q is None:
        self.assertEqual(p.sfen(), q)
  def test_games(self):
    fens1 = [('ln1g4l/1ks2r3/1ppppgn2/p5ppp/5p3/P1P1P2RP/1PBP1P3/2K1GS3/LN1G3N+b b SPslp 47', 'after promotion bishop to a horse'),
      ('ln1g3+Rl/1ks2r3/1ppppgn2/p5p1p/9/P1P1P+b2P/1PBP5/2K1GS3/LN1G3N1 w S3Psl2p 52', 'after promotion rook to a dragon'),
      ('ln1g4l/1ks2r3/1ppppgn2/p5pRp/9/P1P1P+b2P/1PBP5/2K1GS3/LN1G3N1 b S3Psl2p 51', 'after horse recaptures a pawn'),
      ('ln1g4l/1ks2r3/1ppppgn2/p5pRp/9/P1P1PP2P/1PBP5/2K1GS3/LN1G3N+b w S3Pslp 50', 'before horse recaptures a pawn'),
      ('ln1g5/1ks3r2/1ppppsn2/pl3pp1p/9/P1+R5P/1PBPP1N2/1LK1GS1p1/LN1G5 w BGSP3p 72', 'final position')
    ]
    logging.debug('First game')
    self._check_game(GAME1, fens1)
    fens2 = [('l6nl/5G1b1/3p1+S1pp/p1p3pk1/5s3/2P4LP/N+r1P1SPP1/4P2K1/+r4GGNL w GPbsn5p 90', 'final position')]
    logging.debug('Second game')
    self._check_game(GAME2, fens2)
  def _check_kifu(self, t):
    kifu_id, sfen = t
    with open(os.path.join(MODULE_DIR, '81dojo', f'{kifu_id:04d}.kif'), 'r', encoding = 'UTF8') as f:
      g = shogi.kifu.Game.parse(f.read())
    self.assertIsNotNone(g)
    p = shogi.Position()
    for m in g.moves:
      p.do_move(m)
    self.assertEqual(p.sfen(), sfen)
    return g
  def test_kifu(self):
    for t in SENTE_WINS:
      g = self._check_kifu(t)
      self.assertEqual(g.sente_points(), 1)
    for t in GOTE_WINS:
      g = self._check_kifu(t)
      self.assertEqual(g.sente_points(), -1)

if __name__ == '__main__':
  unittest.main()
