# -*- coding: UTF8 -*-
import tarfile
from PIL import ImageTk, Image

import shogi

def _load_images(filename):
  a = {}
  d = dict(map(lambda t: (t[1], t[0]), filter(lambda t: not t[1] is None, enumerate(shogi.piece.ASCII_LONG_NAMES))))
  d['king.sente'] = shogi.piece.KING
  d['king.gote'] = -shogi.piece.KING
  with tarfile.open(filename, 'r|xz') as tar_png:
    for m in tar_png:
      if not m.isreg():
        continue
      i = d.get(m.name.removesuffix('.png'))
      if i is None:
        continue
      with tar_png.extractfile(m) as g:
        image = Image.open(g)
        a[i] = ImageTk.PhotoImage(image)
        if abs(i) != shogi.piece.KING:
          a[-i] = ImageTk.PhotoImage(image.transpose(Image.Transpose.ROTATE_180))
  return a

class ShogiPiecesImages:
  def __init__(self, filename, cell_width):
    self._filename = filename
    self.cell_width = cell_width
    self._images = _load_images(filename)
  def get(self, piece: int):
    return self._images.get(piece)
