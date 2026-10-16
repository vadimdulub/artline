"""Offline cutoff and physical-print-date safeguards; no database fixtures."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('american-printmaking-delivery-20261011.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)

class DateSelection(unittest.TestCase):
 def test_scope_boundaries(self):
  for label in ['1800','1901','1970']:
   self.assertEqual(d.m.dates(label)['creation_year_end'],int(label))
  for label in ['1799','1971','1970s','20th century','1969–1972']:
   self.assertIsNone(d.m.dates(label))
 def test_approximate_cutoff_requires_review(self):
  for label in ['ca. 1970','circa 1968–1970','about 1970']:
   self.assertIsNone(d.m.dates(label))
  self.assertEqual(d.m.dates('ca. 1969')['date_precision'],'circa')
 def test_literal_qualifiers_are_preserved(self):
  label='published March 10, 1865';self.assertEqual(d.m.dates(label)['date_display'],label)
  for label in ['mid 19th century','late 19th century']:
   value=d.m.dates(label);self.assertEqual((value['creation_year_start'],value['creation_year_end']),(1801,1900));self.assertEqual(value['date_display'],label)
 def test_unknown_or_subject_dates_are_not_invented(self):
  for label in ['n.d.','1865?','before 1865','after 1840','French, 1804–1866','Henri IV (1553–1610), published 1830','1830, printed 1905']:
   self.assertIsNone(d.m.dates(label))
 def test_explicit_ranges(self):
  value=d.m.dates('ca. 1833–34');self.assertEqual((value['creation_year_start'],value['creation_year_end'],value['date_precision']),(1833,1834,'circa_range'))
  self.assertIsNone(d.m.dates('1890–89'))
 def test_postdeath_date_needs_printing_evidence(self):
  row={'artist_identity':{'death_year':1866},'date':d.m.dates('ca. 1935')}
  self.assertIsNotNone(d.physical_date_hold(row))
  row['date']=d.m.dates('printed 1935');self.assertIsNone(d.physical_date_hold(row))
  row['date']=d.m.dates('1865');self.assertIsNone(d.physical_date_hold(row))
 def test_unknown_death_is_not_invented(self):
  self.assertIsNone(d.physical_date_hold({'artist_identity':{'death_year':None},'date':d.m.dates('1935')}))
 def test_corporate_publisher_is_not_assumed_to_be_a_person(self):
  self.assertTrue(d.corporate_creator_hold('Strobridge & Co.'))
  self.assertTrue(d.corporate_creator_hold('Smith and Knight'))
  self.assertFalse(d.corporate_creator_hold('Nathaniel Currier'))
 def test_physical_matrix_is_not_imported_as_print(self):
  for medium in ['Woodblock','Lithographic crayon (transfer drawing)']:
   self.assertIsNotNone(d.physical_object_hold({'title':'Test','medium':medium}))
  self.assertIsNone(d.physical_object_hold({'title':'Test','medium':'Woodcut from five blocks'}))
 def test_explicit_birth_blocks_impossible_object_date(self):
  row={'artist_identity':{},'source_creator_label':'Artist: Brian D. Cohen (American, born 1959)','date':d.m.dates('1955')}
  self.assertIsNotNone(d.source_life_hold(row,{}))
 def test_conflicting_authority_life_dates_remain_held(self):
  row={'artist_identity':{'death_year':1841},'source_creator_label':'Artist: Example (American, 1795–1841)','date':d.m.dates('1830')}
  self.assertIsNotNone(d.source_life_hold(row,{'died':{'timespan':{'begin_of_the_begin':'1851-01-01','end_of_the_end':'1851-12-31'}}}))

if __name__=='__main__':unittest.main()
