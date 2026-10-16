"""Offline date-scope safeguards; no catalogue connections or fixtures."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('french',Path(__file__).with_name('french-printmaking-20261011.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class LiteralDates(unittest.TestCase):
 def test_exact_scope_boundaries(self):
  self.assertEqual(m.dates('1800')['creation_year_start'],1800)
  self.assertEqual(m.dates('1900')['creation_year_end'],1900)
  for value in ['1799','1901','1970']:self.assertIsNone(m.dates(value))
 def test_ranges_keep_precision(self):
  x=m.dates('ca. 1833–34');self.assertEqual((x['creation_year_start'],x['creation_year_end'],x['date_precision']),(1833,1834,'circa_range'))
  self.assertEqual(m.dates('1850s')['creation_year_end'],1859)
  self.assertEqual(m.dates('19th century')['date_precision'],'century')
 def test_date_wording_preserved(self):
  label='published March 10, 1865';x=m.dates(label);self.assertEqual(x['date_display'],label);self.assertEqual(x['creation_year_start'],1865)
 def test_modern_extension_keeps_1970_cutoff(self):
  self.assertEqual(m.dates('1970',1970)['creation_year_end'],1970)
  self.assertEqual(m.dates('1960s',1970)['creation_year_end'],1969)
  for value in ['1971','1970s','1969–1972','20th century','ca. 1970','circa 1968–1970']:self.assertIsNone(m.dates(value,1970))
 def test_unknown_and_uncertain_are_not_invented(self):
  for value in [None,'','n.d.','undated','1865?','before 1865','after 1840']:
   with self.subTest(value=value):self.assertIsNone(m.dates(value))
 def test_qualified_centuries_preserve_conservative_envelope(self):
  for label in ['mid 19th century','early 19th–mid 19th century','late 19th century']:
   x=m.dates(label);self.assertEqual((x['creation_year_start'],x['creation_year_end'],x['date_precision']),(1801,1900,'century'));self.assertEqual(x['date_display'],label)
  self.assertEqual(m.dates('late 1830s')['creation_year_end'],1839)
  self.assertIsNone(m.dates('mid 19th–early 20th century',1970))
 def test_subject_lifespans_and_restrikes_are_not_creation(self):
  for value in ['Henri IV (1553–1610), published 1830','French, 1804–1866','1830, printed 1905','1890–1910','1890–89','20th century']:
   with self.subTest(value=value):self.assertIsNone(m.dates(value))

if __name__=='__main__':unittest.main()
