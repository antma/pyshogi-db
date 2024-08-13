# -*- coding: UTF8 -*-
from PIL import ImageTk, Image
import tarfile

import shogi.piece

def _load_images(filename):
  a = {}
  d = dict(map(lambda t: (t[1], t[0]), filter(lambda t: not t[1] is None, enumerate(shogi.piece.ASCII_LONG_NAMES))))
  with tarfile.open(filename, 'r|xz') as tar_png:
    for m in tar_png:
      if not m.isreg():
        continue
      i = d.get(m.name.removesuffix('.png'), -1)
      if i < 0:
        continue
      with tar_png.extractfile(m) as g:
        image = Image.open(g)
        a[i] = ImageTk.PhotoImage(image)
        #a[-i] = ImageTk.PhotoImage(image.rotate(180))
        a[-i] = ImageTk.PhotoImage(image.transpose(Image.Transpose.ROTATE_180))
  return a

class ShogiPiecesImages:
  def __init__(self, filename):
    self._filename = filename
    self.images = _load_images(filename)
