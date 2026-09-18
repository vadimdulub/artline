"""Synthetic identity, geography and uncertain person chronology safeguards."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('research-overnight-smk-new-artists.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class TestNewArtistEvidence(unittest.TestCase):
 def setUp(self):
  self.p={'name':'Example, Ada','forename':'Ada','surname':'Example','birth_date_start':['1800-01-01'],'birth_date_end':['1805-12-31'],'birth_date_prec':['1800-1805'],'death_date_start':['1880-01-01'],'death_date_end':['1880-12-31'],'death_date_prec':['1880']}
 def test_birth_range_is_not_an_exact_birth_year(self):
  d=m.life_interval(self.p,'birth');self.assertIsNone(d['year']);self.assertEqual((d['lo'],d['hi'],d['display'],d['precision']),(1800,1805,'1800-1805','range'))
 def test_missing_life_evidence_is_held(self):
  self.p['birth_date_start']=[]
  with self.assertRaises(ValueError):m.life_interval(self.p,'birth')
 def test_exact_name_collision_is_held_even_without_dates(self):
  xs=[{'id':'synthetic-existing','display_name':'Ada Example','aliases':[],'birth_year':None,'death_year':None}];self.assertEqual(len(m.identity_conflicts(self.p,xs)),1)
 def test_alternative_spelling_with_overlapping_life_is_held(self):
  xs=[{'id':'synthetic-existing','display_name':'Ada Exampel','aliases':[],'birth_year':1802,'death_year':1880}];self.assertEqual(len(m.identity_conflicts(self.p,xs)),1)
 def test_distinct_person_is_not_a_duplicate(self):
  xs=[{'id':'synthetic-other','display_name':'Grace Different','aliases':[],'birth_year':1810,'death_year':1890}];self.assertEqual(m.identity_conflicts(self.p,xs),[])
 def test_flemish_is_not_silently_mapped_to_modern_belgian_citizenship(self):self.assertNotIn('Flamsk',m.COUNTRIES)
if __name__=='__main__':unittest.main()
