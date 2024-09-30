# -*- coding: UTF8 -*-

class Opening:
  def __init__(self, usi_moves: str, jp_name: str, en_name: str, url: str):
    self.usi_moves = usi_moves
    self.jp_name = jp_name
    self.en_name = en_name
    self.url = url

OPENINGS = [
  Opening('7g7f 3c3d 8h2b+ 3a2b B*4e',
    '筋違角', 'Wrong Diagonal Bishop', 'https://en.wikipedia.org/wiki/Wrong_Diagonal_Bishop'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b8h+ 7i8h 8f7f',
   '相横歩取り','Double Side Pawn Capture', 'https://en.wikipedia.org/wiki/Double_Side_Pawn_Capture'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b8h+ 7i8h P*2h 3i2h B*4e',
   '横歩取り☖４五角', 'Side Pawn Capture, Bishop*45', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop*45'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b8h+ 7i8h P*3h',
    '', '3rd File Pawn Drop Option', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d',
    '横歩取り', 'Side Pawn Picker', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2a3c',
    '横歩取り3三桂', 'Side Pawn Capture Knight-33', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b3c',
    '横歩取り3三角', 'Side Pawn Capture Bishop-33', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop-33'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b3c 3d3f 8f8e',
    '', "Chūza's Rook", 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop-33'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b3c 5i5h',
    '青野流', 'Aono Side Pawn', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop-33'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b3c 5i6h',
    '勇気流', 'Yūki Side Pawn', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop-33'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b3c 3d3c+',
    '', 'Takebe Rx33+ variation', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop-33'),
]
