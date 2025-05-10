# -*- coding: UTF8 -*-
import csv
import glob
import gzip
import inspect
import io
import itertools
import logging
import math
import os
import unittest

import shogi
from shogi.castles import Castle
from shogi.history import PositionWithHistory
from shogi.openings import Opening
from shogi.move import (IllegalMove, Move)
from shogi.position import Position

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

NORMAL_GAMES = [
  (102, 'l5+R1k/6gLp/r1n1p2p+L/p4sN2/1p2sb1P1/2P2p1N1/PP5G1/4PG1K1/L8 w GNPb2s6p 194', 1),
  (10, 'lr6p/4g1k1l/3sN2pl/ppp1P1N2/4ppb2/PLPp2N2/NP3PP2/3G1S3/+p3K2Pr b GSPbgsp 111', -1),  #time loss
]

ILLEGAL_MOVE_GAMES = [
  (11, 'l5gkl/5sgs1/2+Pp2np1/p4pp1p/1NBP2l2/2p5P/P4PNP1/4PGPK1/1+r4N1L b RBGP2s2p 105', -1),  #nifu
  (36, 'lnS+R4+P/2sSb4/nkppp4/p4pg1p/1K7/P1PBP3P/1P1P1P3/3+r5/LN1+s4L b GLP2gn3p 81', -1), #check
  (44, '4k2nl/4g1gs1/p1+B1sp+rp1/1r6p/1p3B1P1/2P1L1P1P/PPSPPPN2/2G1K1S2/LN3G2L w N4P 54', 1),
  (49, '7nl/1p4gk1/2n2gspp/1Ppn1sp2/+R1bpPp3/3s5/3KLP1PP/6RB1/1+l1G3NL b GS6P 109', -1),
  (53, 'l5+R1l/3s+B4/pG1p1+N3/2p2p1N1/R2Gp1S1p/2gk1P3/PP1g+sS2P/9/LNK3B1L w 3Pn5p 118', 1),
  (105, 'lnsgk3l/6g2/1pppp1n1p/p3s1pp1/7P1/P1P6/1P1PPB+b1P/1S5R1/LN1GKG2L b RPsn2p 41', -1),
  (124, 'l2G3nl/3+Rskg2/pp2ppspp/2ps2p2/4+bb3/2P2N3/PP2PPP1P/4G1K2/Lr2NG1Ns w 2Plp 60', 1),
]

USI_GAMES = [
('7g7f 3c3d 6g6f 8c8d 7i7h 7a6b 8h7g 5a4b 7h6g 6a5b 2h5h 4b3b 5i4h 3a4b 4h3h '
 '7c7d 3h2h 6b7c 3i3h 8d8e 5g5f 5c5d 6i7h 4b5c 1g1f 1c1d 5h5i 5c4d 4g4f 7c6d '
 '7g6h 9c9d 3h4g 5b4b 3g3f 7d7e 6f6e 6d6e 7f7e 5d5e 4f4e 4d4e 5f5e P*5f 6h7g '
 '8b5b P*4f 2b5e 7g5e 5b5e B*8h B*6d 4f4e 5f5g+ 4g4f 5e4e 8h1a+ 6d4f S*3g '
 '4f3g+ 2i3g 4e4g+ B*3h S*2b 3h4g 5g4g R*1b 4a3a 4i3h P*5h 6g5h 4g3h 2h3h B*5f '
 '5h4g 5f4g+ 3h4g S*5f 4g3h G*4g 3h2h S*4h 5i7i 4h3g 2h1h 4g3h L*2i 3h2i 7i2i '
 'N*2e 2g2f 3g3h 2f2e 3h2i 1h2i R*5i N*3i 5i5h+ G*6h L*2f S*2g 2f2g 3i2g S*2h '
 '2i1h 5h3h 1a2b 3a2b 1b2b+ 3b2b B*5e B*4d',
 'ln5n1/5g1k1/3p1p1p1/p4bp1p/1pPsB2P1/4s1P1P/PP5N1/2GG2+rsK/LN6L b GSL3Pr2p 113'),
('5g5f 5c5d 7i6h 8b5b 6h5g 3c3d 5g6f 5a6b 2g2f 6b7b 2f2e 2b3c 3i4h 3a4b 4h5g '
 '4b5c 5g4f 5c4d 7g7f 7b8b 5i6h 7a7b 6h7h 9c9d 9g9f 6c6d 7f7e 7b6c 4i5i 5b7b '
 '8g8f 7c7d 7e7d 6c7d 7h8g 6d6e 6f7g 4a5b 6i7h 5b6c 8h7i 8c8d P*7f 7b2b 3g3f '
 '6a7b 1g1f 3c5a 7i5g 2a3c 7f7e 7d8c 7g7f 3c4e 5g4h 8a7c 8i7g 6c6d 5i6h 1c1d '
 '2i3g 4e3g+ 4h3g 5a4b 3f3e 6d7e 7f7e 4b7e 4f5g N*4e 3g7c+ 7b7c 7g6e 7c7d 5g6f '
 '7e6d P*7e 7d6e 6f6e 6d2h+ N*7d 8b9c G*8h R*5i 9i9h P*7c G*8b 7c7d 8b8c 9c8c '
 '6e7d 8c7b N*4f 7b6b S*6c 6b5a 7d6e 4e5g+ 6h5g 5i5g+ 4f3d 2b9b N*6d S*6a 5f5e '
 'B*6i 6e7f G*6e 7f6e 5g6g G*7g 6g6e P*6b 6e6d 6b6a+ 5a6a 6c5d+ 6d6h P*6b 6a7a '
 'S*8c N*6e 8g9g 6e7g+ 7h6h G*8g',
 'l1k5l/r2P5/1S3p1p1/pp2+SsN1p/2P1P1PP1/PP6P/Kg+n2P3/LG1G3+b1/3b4L b RPgs2n3p 127'),
]

POSITIONS_IN_KIFU = [
  ('ln5n1/5g1k1/3p1p1p1/p4bp1p/1pPsB2P1/4s1P1P/PP5N1/2GG2+rsK/LN6L b GSL3Pr2p 113',
'''後手の持駒：飛 歩二
  ９ ８ ７ ６ ５ ４ ３ ２ １
+---------------------------+
|v香v桂 ・ ・ ・ ・ ・v桂 ・|一
| ・ ・ ・ ・ ・v金 ・v玉 ・|二
| ・ ・ ・v歩 ・v歩 ・v歩 ・|三
|v歩 ・ ・ ・ ・v角v歩 ・v歩|四
| ・v歩 歩v銀 角 ・ ・ 歩 ・|五
| ・ ・ ・ ・v銀 ・ 歩 ・ 歩|六
| 歩 歩 ・ ・ ・ ・ ・ 桂 ・|七
| ・ ・ 金 金 ・ ・v龍v銀 玉|八
| 香 桂 ・ ・ ・ ・ ・ ・ 香|九
+---------------------------+
先手の持駒：金 銀 香 歩三
'''),
  ('1n7/R3l4/kpp2s3/1N3p3/6p2/l1PP+BP2p/pPS1PSP2/1K7/LN1G2GN1 w 2G5Prbslp 98',
'''後手の持駒：飛 角 銀 香 歩
  ９ ８ ７ ６ ５ ４ ３ ２ １
+---------------------------+
| ・v桂 ・ ・ ・ ・ ・ ・ ・|一
| 飛 ・ ・ ・v香 ・ ・ ・ ・|二
|v玉v歩v歩 ・ ・v銀 ・ ・ ・|三
| ・ 桂 ・ ・ ・v歩 ・ ・ ・|四
| ・ ・ ・ ・ ・ ・v歩 ・ ・|五
|v香 ・ 歩 歩 馬 歩 ・ ・v歩|六
|v歩 歩 銀 ・ 歩 銀 歩 ・ ・|七
| ・ 玉 ・ ・ ・ ・ ・ ・ ・|八
| 香 桂 ・ 金 ・ ・ 金 桂 ・|九
+---------------------------+
先手の持駒：金二 歩五
後手番
''')
]

WESTERN_MOVE_TESTS = [
  ('l6nl/1r1gk1gs1/4pp1p1/p1pps1P1p/1p1n5/P1PP3RP/1P2PPN2/2GSK1S2/LN3G2L w B2Pb 38', 'B*4d', 'B*4d'),
  ('l7l/5kgs1/3gpp1p1/p1pN2P1p/3pP1n2/P1P1N1B1P/1+r4+s2/7R1/2G2GK1L b BSPsnl5p 101', '3f6c+', 'Bx6c+'),
  ('l7l/5kgs1/3+Bpp1p1/p1pN2Plp/3pP1n2/P1P1N3P/1+r7/9/2G2GK1L w BG2SPrsn5p 106', '8g3g', '+R-3g'),
  ('lr6l/3gk1gs1/4pp1p1/p1p3P1p/3p1n3/P1P1PS2P/1P+s2P+pR1/4K1S2/+b1G2G2L b B2N2Pnlp 73', '3h3g', 'S3hx3g'),
  ('ln1g1g1nl/1ks2r3/1pp1p1spp/p2p1pp2/9/2PS1SPP1/PP1PPPN1P/2GK1G1R1/LN6L w Bb 26', '4a5b', 'G4a-5b'),
  ('5+RB1l/2g6/1s1k1pnp1/2pp2p1p/4B4/LpP3PPP/1P1P1PN2/K1G6/2G5L b RGNL2P3sn2p 87', '3a6d+', 'B3ax6d+'),
  ('ln3g2l/2r1g1k2/3pppnpp/p5S2/1p3P3/2sPn1P1P/PPp3NP1/4R1SK1/L+b1G1G2L w B2Psp 64', '7f6g', 'S-6g='),
  ('lnsgkg1+R1/5s1+R+P/p1pppp2p/6p2/9/2P6/P2PPPP1P/9/2+pGKGSNL b BNLPbsnlp 23', '2b1a', '+R2b-1a'),
  ('ln1g1g1+B+B/1rks1s3/pppppp1pp/6p2/9/2P6/PP1PPPPPP/7R1/LNSGKGSNL b NL 11', '2a2b', '+B2a-2b'),
  ('ln2kgsnl/2s1g2b1/p1ppppppp/9/1P5P1/P8/2PPPPP1P/1B1R3R1/LNSGKGSNL b P 13', '2h4h', 'R2h-4h'),
  ('lnsgknsnl/1r3g3/pppppp1pp/6p2/9/2P6/PPBPPPPPP/2S1K2R1/L2G1GSNL w B 10', '4a3c', 'N4a-3c'),
  ('l2gg1bnl/1rsk1s3/p1nppppGp/1pp6/9/P5P1P/1PPPPP1P1/1B5R1/LNSGK1SNL b P 19', '2c3b', 'G-3b'),
  ('lnsgkgsnl/1r5b1/ppppppppp/9/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL w - 2', '8c8d', 'P-8d'),
]

class TestShogiPiece(unittest.TestCase):
  def test_to_string(self):
    self.assertEqual(shogi.piece.to_string(shogi.piece.DRAGON), '+R')
    self.assertEqual(shogi.piece.to_string(-shogi.piece.DRAGON), '+r')
    self.assertEqual(shogi.piece.to_string(shogi.piece.HORSE), '+B')
    self.assertEqual(shogi.piece.to_string(-shogi.piece.HORSE), '+b')

class TestShogiPosition(unittest.TestCase):
  def test_init_default(self):
    p = Position()
    self.assertEqual(p.sfen(), shogi.position.SFEN_STARTPOS)
  def _test_fen(self, fen):
    p = Position(fen)
    self.assertEqual(p.sfen(), fen)
  def test_init(self):
    self.assertRaises(ValueError, Position, '9 - - 1')
    self._test_fen('+B2g1ksn+L/6g2/9/9/4+r4/9/4+b4/7R1/LNSGKGSN1 w SN2L18P 84')
    self._test_fen('+B2g1ksn+L/6g2/9/9/4+r4/9/9/5K1R1/L+b1G1GSN1 b SN2L18Psn 87')
  def _check_game(self, game, fens):
    p = Position()
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
    kifu_id, sfen, sente_points = t
    with open(os.path.join(MODULE_DIR, '81dojo', f'{kifu_id:04d}.kif'), 'r', encoding = 'UTF8') as f:
      g = shogi.kifu.game_parse(f.read())
    self.assertIsNotNone(g)
    self.assertEqual(g.pos.sfen(), sfen)
    self.assertEqual(g.sente_points(), sente_points)
    #testing Position.undo_move
    pos = Position()
    pos_sfen = pos.sfen()
    prev_move = None
    for m in g.moves:
      #testing Move.kifu_str
      #self.assertEqual(km.kifu, m.kifu_str(prev_move))
      #testing move packing
      packed_move = m.pack_to_int()
      self.assertEqual(m, Move.unpack_from_int(packed_move, pos.side_to_move))
      try:
        u = pos.do_move(m)
      except IllegalMove:
        break
      pos.undo_move(m, u)
      self.assertEqual(pos_sfen, pos.sfen())
      pos.do_move(m)
      pos_sfen = pos.sfen()
      prev_move = m
    return g
  def test_normal_kifu(self):
    for t in NORMAL_GAMES:
      self._check_kifu(t)
  def test_illegal_move_kifu(self):
    for t in ILLEGAL_MOVE_GAMES:
      self._check_kifu(t)
  def test_is_legal(self):
    p = Position('l4+N+R1l/2ksg4/p2p1s3/2p1pp1N1/6S1p/2r2P3/PP1P1g2P/1G1S2+b2/LN1K4L b BGN3P4p 85')
    self.assertTrue(p.is_legal())
    for sfen in ['lnsg1gsnl/1r5b1/ppppkpppp/4p4/5N3/6P2/PPPPPP1PP/1B5R1/LNSGKGS1L b - 1',
                 'lnsg1gsnl/1r5b1/pppp1ppkp/4p2p1/8N/6P2/PPPPPP1PP/1B5R1/LNSGKGS1L b - 1']:
      with self.assertRaises(ValueError):
        p = Position(sfen)
  def test_is_check(self):
    p = Position('ln4gkl/3s2+Ss1/2pp2np1/p5p1p/9/3P1PP1P/P1+r1PGNP1/3R2SK1/L4G2L w BG3Pbn2p 50')
    self.assertTrue(p.is_check())
  def test_usi_games(self):
    for usi_moves, final_sfen in USI_GAMES:
      pos = Position()
      for s in usi_moves.split():
        m = pos.parse_usi_move(s)
        self.assertEqual(s, m.usi_str())
        pos.do_move(m)
      self.assertEqual(final_sfen, pos.sfen())
  '''
  def test_openings(self):
    for o in OPENINGS:
      pos = Position()
      for s in o.usi_moves.split():
        m = pos.parse_usi_move(s)
        self.assertEqual(s, m.usi_str())
        pos.do_move(m)
  '''
  def test_western_move_str(self):
    for (fen, usi_move, expected) in WESTERN_MOVE_TESTS:
      pos = Position(fen)
      m = pos.parse_usi_move(usi_move)
      self.assertEqual(pos.western_move_str(m), expected)

class TestKifu(unittest.TestCase):
  def test_time_control(self):
    s = "15分+60秒"
    tc = shogi.kifu.parse_time_control('15+60')
    self.assertEqual(str(tc), s)
    tc = shogi.kifu.parse_time_control(s)
    self.assertEqual(str(tc), s)
  def test_position_kifu_str(self):
    for sfen, kifu in POSITIONS_IN_KIFU:
      pos = Position(sfen)
      self.assertEqual(pos.kifu_str(), kifu)

class TestEvaluation(unittest.TestCase):
  def test_winning_percentage(self):
    with gzip.open(os.path.join(MODULE_DIR, 'eval.csv.gz'), 'rt', encoding = 'UTF8') as f:
      r = csv.reader(f, delimiter='\t')
      for i, t in enumerate(r):
        score = float(t[1])
        win_rate = shogi.evaluation.win_rate(score) * 100.0
        if win_rate > 50.0:
          e = math.floor(win_rate)
        else:
          e = math.ceil(win_rate)
        e = round(shogi.evaluation.winning_percentage(score))
        self.assertEqual(e, int(t[0]), msg = f'test #{i+1}: win_rate({score}) = {win_rate}')

class TestPuzzles(unittest.TestCase):
  def test_puzzles(self):
    for puzzle_id in range(1, 2):
      with open(os.path.join(MODULE_DIR, 'puzzles', f'{puzzle_id:04d}.kif'), 'r', encoding = 'UTF8') as f:
        s = f.read()
      g = shogi.kifu.game_parse(s)
      self.assertIsNotNone(g)
      f = io.StringIO()
      shogi.kifu.game_write_to_file(g, f)
      t = f.getvalue()
      '''
      with open(os.path.join(MODULE_DIR, 'puzzles', f'{puzzle_id:04d}.out'), 'w', encoding = 'UTF8') as g:
        g.write(t)
      '''
      self.assertEqual(s, t)

class TestCheckmates(unittest.TestCase):
  def test_checkmates(self):
    with open(os.path.join(MODULE_DIR, 'sfen', 'checkmates.sfen'), 'r', encoding = 'UTF8') as f:
      for s in f:
        pos = Position(s)
        self.assertTrue(pos.is_check())
        self.assertFalse(pos.has_legal_move())

_TEST_CASTLE_BY_POSITIONS = [
  ('ln1g3rl/1ks2bg2/2pp1snp1/pp2ppp1p/7P1/PPP1PPP1P/1SBP2N2/1KG1GS1R1/LN6L w - 38', 1, Castle.SILVER_CROWN),
  ('ln1g3nl/1ks3gr1/1ppppsbp1/p4pp1p/7P1/P1P2PP1P/1P1PPSN2/1BK1G2R1/LNSG4L b - 27', -1, Castle.HALF_MINO_CASTLE),
  ('kn1gr3l/ls1b1sg2/pppp1pnpp/4p4/P4P3/2P3R2/1PBPP1P1P/1K2GS3/LNSG3NL b 2P 35', -1, Castle.SWINGING_ROOK_ANAGUMA),
  ('ln3gsnl/1r3k1b1/p2ppg1pp/2ps1pp2/1p2P4/2PS5/PPBP1PPPP/4R1SK1/LN1G1G1NL w - 24', 1, Castle.HALF_MINO_CASTLE),
  ('ln1g1gsnl/1ks1r2b1/1ppp1p1pp/p5p2/4p4/P1P2P1P1/1P1PP1P1P/1BKSGS1R1/LN1G3NL b - 19', -1, Castle.HALF_MINO_CASTLE),
  ('ln1g3nl/1ks1grsb1/1pp1p2p1/p2p1pp1p/9/P1PBP2P1/1PNP1PP1P/1S2GS1R1/LKG4NL w - 26', -1, Castle.MILLENIUM_CASTLE),
  ('ln1g1k1nl/1r1s2gb1/p1pp1pspp/1p2p1p2/9/2PP3P1/PP1SPPP1P/1BG1GS1R1/LN1K3NL w - 18', 1, Castle.SNOW_ROOF_CASTLE),
]

_TEST_DATA_CASTLES = [
  (4, [], []),
  (5, [Castle.BOAT_CASTLE], []),
  (6, [Castle.BOAT_CASTLE, Castle.CASTLE_TOWER_MINO], [Castle.HALF_MINO_CASTLE, Castle.TOPKNOT_MINO, Castle.SILVER_CROWN]),
  (7, [Castle.MINO_CASTLE], []),
  (8, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE], [Castle.PEERLESS_GOLDS]),
  (9, [Castle.MINO_CASTLE], [Castle.BOAT_CASTLE]),
  (10, [Castle.BOAT_CASTLE], [Castle.SWINGING_ROOK_ANAGUMA]),
  (11, [Castle.MINO_CASTLE], []),
  (12, [Castle.BOAT_CASTLE, Castle.LEFT_HAND_MINO], [Castle.SWINGING_ROOK_ANAGUMA]),
  (13, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE, Castle.HIGH_MINO_CASTLE], [Castle.STATIC_ROOK_ANAGUMA]),
  (14, [Castle.BOAT_CASTLE], [Castle.HALF_MINO_CASTLE]),
  (15, [Castle.HALF_MINO_CASTLE], []),
  (16, [], [Castle.HALF_MINO_CASTLE]),
  (17, [], []),
  (18, [], []),
  (19, [Castle.KIMURA_MINO, Castle.HALF_MINO_CASTLE], []),
  (20, [Castle.CASTLE_TOWER_MINO], [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE]),
  (21, [Castle.KIMURA_MINO, Castle.HALF_MINO_CASTLE], []),
  (22, [], [Castle.STRAWBERRY_CASTLE]),
  (23, [], []),
  (24, [], []),
  (25, [Castle.HALF_MINO_CASTLE], [Castle.LEFT_HAND_MINO]),
  (26, [],[]),
  (27, [],[]),
  (28, [],[]),
  (29, [],[]),
  (30, [],[]),
  (31, [Castle.LEFT_HAND_MINO, Castle.STATIC_ROOK_ANAGUMA], [Castle.MINO_CASTLE, Castle.HIGH_MINO_CASTLE, Castle.SILVER_CROWN]),
  (32, [], [Castle.KIMURA_MINO, Castle.HALF_MINO_CASTLE]),
  (33, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE], [Castle.BOAT_CASTLE, Castle.STATIC_ROOK_ANAGUMA]),
  (34, [], []),
  (35, [Castle.MINO_CASTLE, Castle.HALF_MINO_CASTLE], [Castle.MINO_CASTLE]),
  (36, [Castle.MINO_CASTLE, Castle.HALF_MINO_CASTLE, Castle.HIGH_MINO_CASTLE], [Castle.STATIC_ROOK_ANAGUMA]),
  (37, [], []),
  (38, [], []),
  (39, [Castle.SWINGING_ROOK_ANAGUMA], [Castle.STATIC_ROOK_ANAGUMA]),
  (40, [], []),
  (41, [], []),
  (42, [], []),
  (43, [], []),
  (44, [Castle.SWINGING_ROOK_ANAGUMA], [Castle.BOAT_CASTLE, Castle.STATIC_ROOK_ANAGUMA]),
  (45, [Castle.BOAT_CASTLE, Castle.LEFT_HAND_MINO, Castle.SILVER_CROWN], [Castle.TOPKNOT_MINO, Castle.HALF_MINO_CASTLE, Castle.SILVER_CROWN]),
  (46, [], [Castle.HALF_MINO_CASTLE]),
  (47, [], []),
  (48, [Castle.BOAT_CASTLE, Castle.STATIC_ROOK_ANAGUMA], [Castle.HALF_MINO_CASTLE]),
  (49, [], [Castle.SNOW_ROOF_CASTLE]),
  (50, [Castle.HALF_MINO_CASTLE, Castle.KIMURA_MINO], []),
  (51, [], []),
  (52, [], []),
  (53, [Castle.STATIC_ROOK_ANAGUMA], [Castle.SWINGING_ROOK_ANAGUMA]),
  (54, [Castle.ELMO_CASTLE], [Castle.MINO_CASTLE]),
  (55, [], [Castle.HALF_MINO_CASTLE]),
  (56, [Castle.SNOW_ROOF_CASTLE], [Castle.TOPKNOT_MINO, Castle.HALF_MINO_CASTLE, Castle.SILVER_MINO, Castle.SILVER_CROWN]),
  (57, [Castle.HALF_MINO_CASTLE], []),
  (58, [Castle.STATIC_ROOK_ANAGUMA], [Castle.TOPKNOT_MINO, Castle.HALF_MINO_CASTLE]),
  (59, [Castle.MINO_CASTLE], [Castle.BOAT_CASTLE]),
  (60, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE], [Castle.SILVER_CROWN_ANAGUMA, Castle.SILVER_CROWN, Castle.LEFT_HAND_MINO]),
  (61, [Castle.ELMO_CASTLE, Castle.BOAT_CASTLE], [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE]),
  (62, [Castle.HALF_MINO_CASTLE], [Castle.LEFT_HAND_MINO, Castle.BOAT_CASTLE]),
  (63, [Castle.GIRL_IN_THE_HOUSE, Castle.STATIC_ROOK_ANAGUMA], [Castle.SWINGING_ROOK_ANAGUMA]),
  (64, [Castle.HALF_MINO_CASTLE], []),
  (65, [], [Castle.PEERLESS_GOLDS]),
  (66, [], []),
  (67, [Castle.HALF_MINO_CASTLE], [Castle.ELMO_CASTLE]),
  (68, [], []),
  (69, [], []),
  (70, [Castle.CRAB_CASTLE, Castle.YAGURA_CASTLE], []),
  (71, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE], []),
  (72, [Castle.MINO_CASTLE, Castle.HIGH_MINO_CASTLE], [Castle.HALF_MINO_CASTLE]),
  (73, [], []),
  (74, [], []),
  (75, [], [Castle.SWINGING_ROOK_ANAGUMA]),
  (76, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE, Castle.HIGH_MINO_CASTLE], [Castle.CASTLE_TOWER_MINO, Castle.EDGE_KING_SILVER_CROWN]),
  (77, [Castle.SWINGING_ROOK_ANAGUMA], [Castle.GIRL_IN_THE_HOUSE, Castle.KUSHIKATSU_CASTLE]),
  (78, [Castle.DOI_YAGURA], [Castle.SNOW_ROOF_CASTLE]),
  (79, [], []),
  (80, [Castle.HALF_MINO_CASTLE], []),
  (81, [Castle.HALF_MINO_CASTLE], [Castle.BONANZA_CASTLE]),
  (82, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE], [Castle.BOAT_CASTLE]),
  (83, [], []),
  (84, [], []),
  (85, [Castle.HALF_MINO_CASTLE], []),
  (86, [Castle.GIRL_IN_THE_HOUSE, Castle.STATIC_ROOK_ANAGUMA], [Castle.SWINGING_ROOK_ANAGUMA]),
  (87, [Castle.HALF_MINO_CASTLE], []),
  (88, [Castle.STRAWBERRY_CASTLE],[]),
  (89, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE, Castle.HIGH_MINO_CASTLE], [Castle.BOAT_CASTLE, Castle.STATIC_ROOK_ANAGUMA]),
  (90, [Castle.BOAT_CASTLE, Castle.STATIC_ROOK_ANAGUMA], [Castle.HALF_MINO_CASTLE]),
  (91, [], [Castle.HALF_MINO_CASTLE]),
  (92, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE, Castle.HIGH_MINO_CASTLE], []),
  (93, [Castle.HALF_MINO_CASTLE] , [Castle.BOAT_CASTLE, Castle.BONANZA_CASTLE]),
  (94, [Castle.LEFT_HAND_MINO], [Castle.TOPKNOT_MINO, Castle.HALF_MINO_CASTLE]),
  (95, [], [Castle.BOAT_CASTLE]),
  (96, [Castle.MINO_CASTLE], []),
  (97, [], []),
  (98, [], []),
  (99, [], []),
  (100, [Castle.BOAT_CASTLE], []),
  (101, [], [Castle.CRAB_CASTLE]),
  (102, [Castle.STATIC_ROOK_ANAGUMA], [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE, Castle.HIGH_MINO_CASTLE]),
  (103, [Castle.BOAT_CASTLE], [Castle.HALF_MINO_CASTLE]),
  (104, [], []),
  (105, [Castle.ELMO_CASTLE], [Castle.HALF_MINO_CASTLE]),
  (106, [], [Castle.CRAB_CASTLE]),
  (107, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE, Castle.HIGH_MINO_CASTLE], [Castle.STATIC_ROOK_ANAGUMA]),
  (108, [], [Castle.HALF_MINO_CASTLE]),
  (109, [Castle.HALF_MINO_CASTLE, Castle.SILVER_CROWN], [Castle.CASTLE_TOWER_MINO]),
  (110, [], []),
  (111, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE], [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE]),
  (112, [], []),
  (113, [Castle.ELMO_CASTLE], [Castle.HALF_MINO_CASTLE]),
  (114, [Castle.RAPID_CASTLE, Castle.HALF_YAGURA], [Castle.SWINGING_ROOK_ANAGUMA]),
  (115, [], []),
  (116, [], []),
  (117, [], []),
  (118, [], []),
  (119, [Castle.HALF_MINO_CASTLE], []),
  (120, [Castle.BOAT_CASTLE, Castle.STATIC_ROOK_ANAGUMA], [Castle.SWINGING_ROOK_ANAGUMA]),
  (121, [Castle.MINO_CASTLE], [Castle.ELMO_CASTLE]),
  (122, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE], [Castle.LEFT_HAND_MINO]),
  (123, [], []),
  (124, [Castle.PEERLESS_GOLDS], [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE]),
  (125, [], [Castle.CRAB_CASTLE]),
  (126, [Castle.BOAT_CASTLE, Castle.KUSHIKATSU_CASTLE], [Castle.HALF_MINO_CASTLE]),
  (127, [Castle.INVINCIBLE_CASTLE], [Castle.MINO_CASTLE]),
  (128, [], []),
  (129, [Castle.MINO_CASTLE], [Castle.ELMO_CASTLE]),
  (130, [], [Castle.CENTRAL_HOUSE]),
  (131, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE, Castle.HIGH_MINO_CASTLE], [Castle.BOAT_CASTLE, Castle.STATIC_ROOK_ANAGUMA]),
  (132, [Castle.STATIC_ROOK_ANAGUMA, Castle.SILVER_CROWN_ANAGUMA], []),
  (133, [Castle.CENTRAL_HOUSE], []),
  (134, [], [Castle.GOLD_MINO, Castle.KIMURA_MINO]),
  (135, [Castle.BOAT_CASTLE], [Castle.TOPKNOT_MINO, Castle.HALF_MINO_CASTLE]),
  (136, [Castle.GOLD_MINO], [Castle.LEFT_HAND_MINO]),
  (137, [], []),
  (138, [], [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE]),
  (139, [Castle.CASTLE_TOWER_MINO], []),
  (140, [], []),
  (141, [], [Castle.RAPID_CASTLE, Castle.COMPLETE_YAGURA, Castle.YAGURA_ANAGUMA, Castle.YAGURA_CASTLE, Castle.STATIC_ROOK_ANAGUMA]),
  (142, [Castle.MINO_CASTLE], [Castle.BOAT_CASTLE, Castle.STATIC_ROOK_ANAGUMA]),
  (143, [], [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE]),
  (144, [], []),
  (145, [], []),
  (146, [Castle.BOAT_CASTLE], []),
  (147, [], []),
  (148, [], []),
  (149, [Castle.TOPKNOT_MINO, Castle.HALF_MINO_CASTLE], [Castle.BOAT_CASTLE]),
  (150, [Castle.MINO_CASTLE], [Castle.BOAT_CASTLE, Castle.MILLENIUM_CASTLE]),
  (151, [], []),
  (152, [], []),
  (153, [Castle.FOUR_PIECE_MINO, Castle.CASTLE_TOWER_MINO, Castle.BOAT_CASTLE], []),
  (154, [], []),
  (155, [Castle.MINO_CASTLE, Castle.HIGH_MINO_CASTLE], [Castle.BOAT_CASTLE, Castle.STATIC_ROOK_ANAGUMA]),
  (156, [Castle.CASTLE_TOWER_MINO, Castle.EDGE_KING_SILVER_CROWN], [Castle.MINO_CASTLE]),
  (157, [], []),
  (158, [], [Castle.SILVER_CROWN_ANAGUMA, Castle.STATIC_ROOK_ANAGUMA]),
  (159, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE], [Castle.PEERLESS_GOLDS]),
  (160, [], []),
  (161, [], []),
  (162, [], []),
  (163, [], []),
  (164, [], []),
  (165, [], []),
  (166, [Castle.MILLENIUM_CASTLE, Castle.BOAT_CASTLE], [Castle.MINO_CASTLE]),
  (167, [], []),
  (168, [], []),
  (169, [], []),
  (170, [Castle.HALF_MINO_CASTLE], [Castle.BONANZA_CASTLE]),
  (171, [Castle.BOAT_CASTLE], []),
  (172, [], []),
  (173, [], []),
  (174, [], [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE]),
  (175, [Castle.DIAMOND_MINO, Castle.MINO_CASTLE, Castle.HIGH_MINO_CASTLE], [Castle.BOAT_CASTLE, Castle.MILLENIUM_CASTLE]),
  (176, [Castle.HALF_MINO_CASTLE, Castle.KIMURA_MINO], [Castle.BOAT_CASTLE, Castle.LEFT_HAND_MINO]),
  (177, [], []),
  (178, [Castle.BOAT_CASTLE], [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE]),
  (179, [], []),
  (180, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE, Castle.DIAMOND_MINO], [Castle.STATIC_ROOK_ANAGUMA, Castle.SILVER_CROWN_ANAGUMA]),
  (181, [Castle.SNOW_ROOF_CASTLE], []),
  (182, [], []),
  (183, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE, Castle.HIGH_MINO_CASTLE], [Castle.BOAT_CASTLE, Castle.STATIC_ROOK_ANAGUMA]),
  (184, [Castle.HALF_MINO_CASTLE], []),
  (185, [Castle.HALF_MINO_CASTLE, Castle.KIMURA_MINO], [Castle.STATIC_ROOK_ANAGUMA, Castle.SILVER_CROWN_ANAGUMA]),
  (186, [], []),
  (187, [], [Castle.PEERLESS_GOLDS]),
  (188, [], []),
  (189, [Castle.HALF_MINO_CASTLE, Castle.MINO_CASTLE], []),
]

class TestCastles(unittest.TestCase):
  def test_positions(self):
    for sfen, side, ct in _TEST_CASTLE_BY_POSITIONS:
      self.assertEqual(ct, shogi.castles.sfen_find_castle(sfen))

_TEST_OPENINGS_BY_POSITIONS = [
  ('ln1gkgbnl/1r1s2s2/p1pp1pppp/4p4/1p7/2PP5/PPB1PPPPP/2SR1K3/LN1G1GSNL b - 13', -1, Opening.IJIMAS_BACK_BISHOP_STRATEGY),
  ('lnsgk1snl/7r1/2ppppgpp/pp4p2/7P1/P1P5P/1P1PPPP2/1S5R1/LN1GKGSNL b Bb 15', -1, Opening.SAKATA_OPPOSING_ROOK),
  #('lnsgk1snl/1r4g2/p1pppp1pp/6p2/1p5P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL w Bb 12', -1, Opening.BISHOP_EXCHANGE),
  #('lnsgk2nl/1r4g2/p1ppppspp/1p4p2/7P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL b Bb 13', -1, Opening.BISHOP_EXCHANGE),
]

_TEST_OPENINGS_BY_POSITIONS_AND_MOVE = [
  ('l2gk2nl/1r1s2g2/2n1ppspp/p1pp2p2/1p7/2P2PPPP/PPSPPS3/2GKG2R1/LN5NL b Bb 29', '4g5f', Opening.BISHOP_EXCHANGE_RECLINING_SILVER),
]

_TEST_DATA_OPENINGS = [
  (4, [Opening.BISHOP_EXCHANGE, Opening.BISHOP_EXCHANGE_RECLINING_SILVER], [Opening.BISHOP_EXCHANGE]),
  (5, [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE], [Opening.FORTH_FILE_ROOK, Opening.FUJII_SYSTEM]),
  (6, [], [Opening.OPPOSING_ROOK]),
  (7, [Opening.QUICK_ISHIDA], [Opening.RIGHT_HAND_FORTH_FILE_ROOK]),
  (8, [Opening.QUICK_ISHIDA], [Opening.DOUBLE_SWINGING_ROOK]),
  (9, [Opening.THIRD_FILE_ROOK], []),
  (10, [], [Opening.FORTH_FILE_ROOK]),
  (11, [Opening.QUICK_ISHIDA, Opening.DOUBLE_SWINGING_ROOK], [Opening.FORTH_FILE_ROOK]),
  (12, [], []),
  (13, [Opening.GOKIGEN_CENTRAL_ROOK], [Opening.SILVER37_SUPER_RAPID]),
  (14, [], [Opening.GOKIGEN_CENTRAL_ROOK]),
  (15, [Opening.GOKIGEN_CENTRAL_ROOK], []),
  (16, [Opening.MARUYAMA_VACCINE], [Opening.GOKIGEN_CENTRAL_ROOK]),
  (17, [Opening.BISHOP_EXCHANGE, Opening.RIGHT_HAND_KING], [Opening.BISHOP_EXCHANGE]),
  (18, [Opening.URESINO_STYLE], []),
  (19, [Opening.URESINO_STYLE], [Opening.DOUBLE_SWINGING_ROOK]),
  (20, [Opening.RIGHT_HAND_FORTH_FILE_ROOK], [Opening.FORTH_FILE_ROOK]),
  (21, [Opening.GOKIGEN_CENTRAL_ROOK], [Opening.PRIMITIVE_CLIMBING_SILVER]),
  (22, [Opening.RECLINING_SILVER], [Opening.RECLINING_SILVER]),
  (23, [Opening.DOUBLE_WING_ATTACK], [Opening.DOUBLE_WING_ATTACK]),
  (24, [Opening.SIDE_PAWN_PICKER, Opening.AONO_STYLE], [Opening.BISHOP33_STRATEGY]),
  (25, [Opening.GOKIGEN_CENTRAL_ROOK], [Opening.IJIMAS_BACK_BISHOP_STRATEGY]),
  (26, [], [Opening.SAKATA_OPPOSING_ROOK]),
  (27, [], [Opening.BISHOP_EXCHANGE_CLIMBING_SILVER]),
  (28, [], [Opening.RIGHT_HAND_FORTH_FILE_ROOK]),
  (29, [], [Opening.BISHOP_EXCHANGE]),
  (30, [Opening.BISHOP_EXCHANGE, Opening.RIGHT_HAND_KING], [Opening.BISHOP_EXCHANGE]),
  (31, [], [Opening.OPPOSING_ROOK]),
  (32, [], [Opening.GOKIGEN_CENTRAL_ROOK]),
  (33, [Opening.THIRD_FILE_ROOK], [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE]),
  (34, [Opening.PRIMITIVE_CLIMBING_SILVER, Opening.FORTH_FILE_ROOK], [Opening.URESINO_STYLE, Opening.RIGHT_HAND_FORTH_FILE_ROOK]),
  (35, [Opening.QUICK_ISHIDA, Opening.DOUBLE_SWINGING_ROOK], [Opening.FORTH_FILE_ROOK]),
  (36, [Opening.GOKIGEN_CENTRAL_ROOK], []),
  (37, [Opening.URESINO_STYLE], []),
  (38, [], []),
  (39, [Opening.AMAHIKO_OPPOSING_ROOK], []),
  (40, [Opening.DOUBLE_WING_ATTACK], [Opening.DOUBLE_WING_ATTACK]),
  (41, [], []),
  (42, [Opening.OPPOSING_ROOK], []),
  (43, [Opening.BISHOP_EXCHANGE, Opening.BISHOP_EXCHANGE_RECLINING_SILVER], []),
  (44, [Opening.THIRD_FILE_ROOK], [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE]),
  (45, [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE], [Opening.OPPOSING_ROOK]),
  (46, [], [Opening.GOKIGEN_CENTRAL_ROOK]),
  (47, [], []),
  (48, [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE], [Opening.THIRD_FILE_ROOK]),
  (49, [], []),
  (50, [Opening.GOKIGEN_CENTRAL_ROOK], [Opening.SPEARING_THE_BIRD]),
  (51, [Opening.QUICK_ISHIDA], []),
  (52, [Opening.AMAHIKO_OPPOSING_ROOK], []),
  (53, [], [Opening.GOKIGEN_CENTRAL_ROOK]),
  (54, [Opening.RIGHT_HAND_FORTH_FILE_ROOK], [Opening.THIRD_FILE_ROOK]),
  (55, [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE], [Opening.OPPOSING_ROOK]),
  (56, [Opening.SILVER_HORNED_SNOW_ROOF], []),
  (57, [Opening.GOKIGEN_CENTRAL_ROOK], []),
  (58, [], [Opening.QUICK_ISHIDA, Opening.MASUDAS_ISHIDA_STYLE]),
  (59, [Opening.FORTH_FILE_ROOK, Opening.FUJII_SYSTEM], []),
  (60, [], []),
  (61, [], [Opening.GOKIGEN_CENTRAL_ROOK]),
  (62, [Opening.GOKIGEN_CENTRAL_ROOK], []),
  (63, [Opening.SLEEVE_ROOK], [Opening.THIRD_FILE_ROOK]),
  (64, [Opening.GOKIGEN_CENTRAL_ROOK], []),
  (65, [Opening.GOKIGEN_CENTRAL_ROOK], [Opening.DOUBLE_SWINGING_ROOK]),
  (66, [Opening.SIDE_PAWN_PICKER], [Opening.BISHOP45_STRATEGY]),
  (67, [Opening.QUICK_ISHIDA, Opening.ISHIDA_STYLE], []),
  (68, [], []),
  (69, [], []),
  (70, [], []),
  (71, [Opening.FORTH_FILE_ROOK], [Opening.CLIMBING_GOLD]),
  (72, [Opening.FORTH_FILE_ROOK], [Opening.GOKIGEN_CENTRAL_ROOK]),
  (73, [Opening.DOUBLE_WING_ATTACK], [Opening.DOUBLE_WING_ATTACK]),
  (74, [], [Opening.SAKATA_OPPOSING_ROOK, Opening.ONE_TURN_LOSS_BISHOP_EXCHANGE]),
  (75, [Opening.BISHOP_EXCHANGE], [Opening.LEGHORN_SPECIAL]),
  (76, [Opening.FORTH_FILE_ROOK], [Opening.RIGHT_HAND_FORTH_FILE_ROOK]),
  (77, [], []),
  (78, [], [Opening.SILVER_HORNED_SNOW_ROOF]),
  (79, [Opening.DOUBLE_WING_ATTACK, Opening.PRIMITIVE_CLIMBING_SILVER], []),
  (80, [Opening.GOKIGEN_CENTRAL_ROOK], []),
  (81, [], []),
  (82, [Opening.THIRD_FILE_ROOK], [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE]),
  (83, [Opening.GOKIGEN_CENTRAL_ROOK], []),
  (84, [Opening.BISHOP33_STRATEGY], [Opening.SIDE_PAWN_PICKER]),
  (85, [Opening.FORTH_FILE_ROOK], [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE]),
  (86, [], []),
  (87, [Opening.GOKIGEN_CENTRAL_ROOK], [Opening.SILVER37_SUPER_RAPID]),
  (88, [Opening.DOUBLE_WING_ATTACK, Opening.DOUBLE_WING_ATTACK_CLIMBING_SILVER, Opening.UFO_SILVER], []),
  (89, [Opening.THIRD_FILE_ROOK], [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE]),
  (90, [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE], [Opening.THIRD_FILE_ROOK]),
  (91, [], [Opening.OPPOSING_ROOK]),
  (92, [Opening.GOKIGEN_CENTRAL_ROOK], []),
  (93, [Opening.GOKIGEN_CENTRAL_ROOK], []),
  (94, [Opening.MARUYAMA_VACCINE], [Opening.GOKIGEN_CENTRAL_ROOK]),
  (95, [Opening.GOKIGEN_CENTRAL_ROOK], []),
  (96, [Opening.FORTH_FILE_ROOK], []),
  (97, [Opening.URESINO_STYLE], [Opening.THIRD_FILE_ROOK]),
  (98, [Opening.URESINO_STYLE], []),
  (99, [Opening.URESINO_STYLE], []),
  (100, [], [Opening.GOKIGEN_CENTRAL_ROOK]),
  (101, [Opening.URESINO_STYLE, Opening.RIGHT_HAND_KING], []),
  (102, [], [Opening.FORTH_FILE_ROOK, Opening.FORTH_THIRD_FILE_ROOK_STRATEGY]),
  (103, [], [Opening.GOKIGEN_CENTRAL_ROOK]),
  (104, [Opening.PRIMITIVE_CLIMBING_SILVER], []),
  (105, [Opening.RIGHT_HAND_FORTH_FILE_ROOK], [Opening.FORTH_FILE_ROOK]),
  (106, [Opening.URESINO_STYLE], []),
  (107, [Opening.FORTH_FILE_ROOK], [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE]),
  (108, [Opening.DOUBLE_SWINGING_ROOK], []),
  (109, [Opening.URESINO_STYLE], []),
  (110, [], [Opening.FORTH_FILE_ROOK, Opening.FUJII_SYSTEM]),
  (111, [Opening.QUICK_ISHIDA], [Opening.DOUBLE_SWINGING_ROOK]),
  (112, [], []),
  (113, [Opening.RIGHT_HAND_FORTH_FILE_ROOK], [Opening.FORTH_FILE_ROOK]),
  (114, [], [Opening.DIRECT_OPPOSING_ROOK]),
  (115, [Opening.FORTH_FILE_ROOK], [Opening.IJIMAS_BACK_BISHOP_STRATEGY]),
  (116, [], [Opening.MURATA_SYSTEM]),
  (117, [], [Opening.FORTH_FILE_ROOK]),
  (118, [Opening.FORTH_FILE_ROOK], []),
  (119, [Opening.FORTH_FILE_ROOK], [Opening.SPEARING_THE_BIRD]),
  (120, [], [Opening.HIDE_CHAN_STYLE_CENTRAL_ROOK]),
  (121, [Opening.FORTH_FILE_ROOK], [Opening.RIGHT_HAND_FORTH_FILE_ROOK]),
  (122, [Opening.FORTH_FILE_ROOK], [Opening.IJIMAS_BACK_BISHOP_STRATEGY]),
  (123, [Opening.URESINO_STYLE, Opening.MURATA_SYSTEM], []),
  (124, [Opening.DOUBLE_SWINGING_ROOK], [Opening.ROOK32_STRATEGY]),
  (125, [], []),
  (126, [], [Opening.GOKIGEN_CENTRAL_ROOK]),
  (127, [Opening.URESINO_STYLE, Opening.HIDE_CHAN_STYLE_CENTRAL_ROOK], [Opening.DOUBLE_SWINGING_ROOK]),
  (128, [Opening.CRAB_SILVERS], []),
  (129, [Opening.QUICK_ISHIDA], [Opening.RIGHT_HAND_FORTH_FILE_ROOK]),
  (130, [Opening.DOUBLE_WING_ATTACK], [Opening.DOUBLE_WING_ATTACK]),
  (131, [Opening.FORTH_FILE_ROOK], [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE]),
  (132, [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE], [Opening.FORTH_FILE_ROOK, Opening.SWINGING_ROOK_MILLENIUM]),
  (133, [Opening.SIDE_PAWN_PICKER], []),
  (134, [], [Opening.PRIMITIVE_CENTRAL_ROOK]),
  (135, [], [Opening.GOKIGEN_CENTRAL_ROOK]),
  (136, [Opening.OPPOSING_ROOK], []),
  (137, [Opening.SIDE_PAWN_PICKER], [Opening.BISHOP45_STRATEGY]),
  (138, [Opening.SAGINOMIYA_JOSEKI], [Opening.FORTH_FILE_ROOK]),
  (139, [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE], [Opening.FORTH_FILE_ROOK]),
  (140, [], []),
  (141, [Opening.WRONG_DIAGONAL_BISHOP], []),
  (142, [Opening.FORTH_FILE_ROOK, Opening.FUJII_SYSTEM], [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE]),
  (143, [], [Opening.THIRD_FILE_ROOK]),
  (144, [Opening.DOUBLE_WING_ATTACK, Opening.PRIMITIVE_CLIMBING_SILVER], [Opening.DOUBLE_WING_ATTACK]),
  (145, [], []),
  (146, [], [Opening.GOKIGEN_CENTRAL_ROOK]),
  (147, [], []),
  (148, [Opening.DOUBLE_WING_ATTACK], [Opening.DOUBLE_WING_ATTACK]),
  (149, [Opening.FORTH_FILE_ROOK], []),
  (150, [Opening.FORTH_FILE_ROOK], []),
  (151, [], [Opening.FORTH_FILE_ROOK]),
  (152, [Opening.MURATA_SYSTEM], []),
  (153, [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE], [Opening.FORTH_FILE_ROOK]),
  (154, [], [Opening.DOUBLE_WING_ATTACK]),
  (155, [Opening.FORTH_FILE_ROOK], [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE]),
  (156, [], [Opening.FORTH_FILE_ROOK]),
  (157, [Opening.MURATA_SYSTEM], []),
  (158, [Opening.FORTH_FILE_ROOK], []),
  (159, [Opening.ROOK78_STRATEGY], []),
  (160, [], [Opening.MURATA_SYSTEM]),
  (161, [Opening.URESINO_STYLE], []),
  (162, [Opening.URESINO_STYLE], [Opening.GOKIGEN_CENTRAL_ROOK]),
  (163, [], [Opening.URESINO_STYLE]),
  (164, [], []),
  (165, [Opening.THIRD_FILE_ROOK], []),
  (166, [], [Opening.THIRD_FILE_ROOK, Opening.ISHIDA_STYLE]),
  (167, [Opening.MURATA_SYSTEM], []),
  (168, [Opening.DOUBLE_WING_ATTACK], [Opening.DOUBLE_WING_ATTACK]),
  (169, [], [Opening.URESINO_STYLE, Opening.MURATA_SYSTEM]),
  (170, [Opening.GOKIGEN_CENTRAL_ROOK], [Opening.SILVER37_SUPER_RAPID]),
  (171, [], [Opening.PACMAN]),
  (172, [Opening.QUICK_ISHIDA], [Opening.ONE_TURN_LOSS_BISHOP_EXCHANGE]),
  (173, [Opening.SILVER37_STRATEGY], [Opening.SILVER37_STRATEGY]),
  (174, [Opening.CLIMBING_SILVER], [Opening.FORTH_FILE_ROOK]),
  (175, [Opening.FORTH_FILE_ROOK], []),
  (176, [Opening.GOKIGEN_CENTRAL_ROOK], []),
  (177, [Opening.SILVER37_STRATEGY], []),
  (178, [Opening.RIGHT_HAND_FORTH_FILE_ROOK], [Opening.FORTH_FILE_ROOK]),
  (179, [Opening.MURATA_SYSTEM], [Opening.DOUBLE_WING_ATTACK_CLIMBING_SILVER]),
  (180, [Opening.THIRD_FILE_ROOK], [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE]),
  (181, [], [Opening.RIGHT_HAND_FORTH_FILE_ROOK]),
  (182, [Opening.URESINO_STYLE], [Opening.PRIMITIVE_CLIMBING_SILVER]),
  (183, [Opening.FORTH_FILE_ROOK], [Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE]),
  (184, [Opening.FORTH_FILE_ROOK], [Opening.URESINO_STYLE, Opening.SPEARING_THE_BIRD]),
  (185, [Opening.HIDE_CHAN_STYLE_CENTRAL_ROOK], []),
  (186, [], []),
  (187, [Opening.OPPOSING_ROOK], [Opening.THIRD_FILE_ROOK]),
  (188, [], [Opening.PAWN23_STRATEGY]),
  (189, [Opening.QUICK_ISHIDA], []),
]

class TestClassifier(unittest.TestCase):
  def _check_gamelist_issorted(self, l):
    for u, v in zip(l, l[1:]):
      self.assertLess(u[0], v[0])
  def _kifu_game_load(self, filename):
    with open(filename, 'r', encoding = 'UTF8') as f:
      data = f.read()
    g = shogi.kifu.game_parse(data, True)
    self.assertIsNotNone(g, filename)
    return g
  def _check_game(self, game_id, castles, openings):
    msg = f'game #{game_id:04d}'
    g = self._kifu_game_load(os.path.join(MODULE_DIR, 'wars', f'{game_id:04d}.kif'))
    if not castles is None:
      sente_castles, gote_castles = castles
      rr = shogi.castles.game_find_castles(g)
      self.assertEqual(set(sente_castles), rr.get_set(1).as_set(), msg)
      self.assertEqual(set(gote_castles), rr.get_set(-1).as_set(), msg)
    else:
      logging.warning("%s: castles aren't set", msg);
    if not openings is None:
      sente_openings, gote_openings = openings
      rr = shogi.openings.game_find_openings(g)
      self.assertEqual(set(sente_openings), rr.get_set(1).as_set(), msg)
      self.assertEqual(set(gote_openings), rr.get_set(-1).as_set(), msg)
    else:
      logging.warning("%s: openings aren't set", msg);
  def test_partial_castles(self):
    for fn in glob.glob(os.path.join(MODULE_DIR, 'castles', '*.kif')):
      g = self._kifu_game_load(fn)
      s = os.path.basename(fn)
      i = s.index('-')
      c = Castle[s[:i]]
      rr = shogi.castles.game_find_castles(g)
      side = -g.pos.side_to_move
      s = rr.get_set(side)
      self.assertIn(c, s.as_set(), fn)
      self.assertEqual(g.pos.move_no - 1, s.get_move_no(c))
  def test_partial_openings(self):
    for fn in glob.glob(os.path.join(MODULE_DIR, 'openings', '*.kif')):
      g = self._kifu_game_load(fn)
      s = os.path.basename(fn)
      i = s.index('-')
      o = Opening[s[:i]]
      rr = shogi.openings.game_find_openings(g)
      side = -g.pos.side_to_move
      s = rr.get_set(side)
      self.assertIn(o, s.as_set(), fn)
      self.assertEqual(g.pos.move_no - 1, s.get_move_no(o))
  def test_castles_and_openings(self):
    self._check_gamelist_issorted(_TEST_DATA_CASTLES)
    self._check_gamelist_issorted(_TEST_DATA_OPENINGS)
    it = iter(_TEST_DATA_CASTLES)
    jt = iter(_TEST_DATA_OPENINGS)
    while True:
      i = next(it, None)
      if i is None:
        for j in jt:
          self._check_game(j[0], None, (j[1], j[2]))
        break
      j = next(jt, None)
      if j is None:
        for i in itertools.chain([i], it):
          self._check_game(i[0], (i[1], i[2]), None)
        break
      if i[0] == j[0]:
        self._check_game(i[0], (i[1], i[2]), (j[1], j[2]))
      elif i[0] < j[0]:
        self._check_game(i[0], (i[1], i[2]), None)
        jt = itertools.chain([j], jt)
      else:
        self._check_game(j[0], None, (j[1], j[2]))
        it = itertools.chain([i], it)
    shogi.castles.piece_patterns_stats()

if __name__ == '__main__':
  unittest.main()
