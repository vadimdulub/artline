"""Creation-year boundaries must never be replaced by biography or title years."""
import importlib.util, unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('soviet',Path(__file__).with_name('soviet-realism-20261011.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Dates(unittest.TestCase):
 def test_exact(self):
  for label,y in [('холст, масло 1966 год',1966),('масло 1970г.',1970),('масло 1971',1971)]:
   d=m.date_tail(label);self.assertEqual((d['creation_year_start'],d['creation_year_end'],d['date_precision']),(y,y,'exact'))
 def test_decades(self):
  for label,y in [('1960-е г.',1960),('1970е',1970),('1950 е.',1950),('1930-е годы',1930)]:
   d=m.date_tail(label);self.assertEqual((d['creation_year_start'],d['creation_year_end']),(y,y+9))
 def test_ranges(self):
  for label,lo,hi in [('1960-65 гг.',1960,1965),('1960–1971',1960,1971)]:
   d=m.date_tail(label);self.assertEqual((d['creation_year_start'],d['creation_year_end']),(lo,hi))
 def test_ambiguity_held(self):
  for label in ['около 1970','масло 1960?','масло 1960/1970','1930-40-е','1990-1960','масло','1970-е?']:
   self.assertIsNone(m.date_tail(label),label)
 def test_creation_is_after_dimensions(self):
  title='Митинг 1917 года 120-160 см. холст масло 1965 год'
  self.assertEqual(m.date_tail(title[m.DIM.search(title).end():])['creation_year_start'],1965)
if __name__=='__main__':unittest.main()
