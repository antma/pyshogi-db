# -*- coding: UTF8 -*-
import unittest

from elo_rating import rating_to_dan_81dojo

class TestRatingToDan(unittest.TestCase):
  def test_81dojo(self):
    self.assertEqual(rating_to_dan_81dojo(1015), -9)
    self.assertEqual(rating_to_dan_81dojo(1029), -9)
    self.assertEqual(rating_to_dan_81dojo(1050), -8)
    self.assertEqual(rating_to_dan_81dojo(1099), -8)
    self.assertEqual(rating_to_dan_81dojo(1111), -7)
    self.assertEqual(rating_to_dan_81dojo(1149), -7)
    self.assertEqual(rating_to_dan_81dojo(1500), 1)
    self.assertEqual(rating_to_dan_81dojo(1499), -1)
    self.assertEqual(rating_to_dan_81dojo(2326), 7)
    self.assertEqual(rating_to_dan_81dojo(2299), 6)
    self.assertEqual(rating_to_dan_81dojo(999), -10)
    self.assertEqual(rating_to_dan_81dojo(899), -11)
    self.assertEqual(rating_to_dan_81dojo(786), -12)
    self.assertEqual(rating_to_dan_81dojo(746), -12)
    self.assertEqual(rating_to_dan_81dojo(728), -12)
    """
    self.assertEqual(rating_to_dan_81dojo(275), -15)
    """

