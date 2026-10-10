"""Offline checks of creation dates and physical-object counting; no database use."""
import importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-beziers-more-review-20261009.py'));r=importlib.util.module_from_spec(z);z.loader.exec_module(r);f=r.i.f
class EvidenceBoundaries(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds={d['number']:d for d in r.build()};cls.rows,cls.held,cls.known=f.rows()
 def test_after_has_no_inferred_upper_year(self):self.assertEqual(f.dates({'Millesime_de_creation':'après 1922','Periode_de_creation':'1er quart 20e siècle','Auteur':'Moulin Jean (1899-1943)'})[:3],(1922,None,'after'))
 def test_questioned_lower_endpoint_remains_approximate(self):self.assertEqual(f.dates({'Millesime_de_creation':'1925 (?)-1939'})[:3],(1925,1939,'circa_range'))
 def test_inscription_preserves_circa(self):self.assertEqual((self.ds[5]['facts']['date_precision'],self.ds[5]['facts']['date_display']),('circa','vers 1931'))
 def test_acquisition_does_not_supply_creation(self):self.assertEqual(f.dates({'Date_d_acquisition':'1975-09-05','Auteur':'Moulin Jean (1899-1943)'})[:3],(None,None,'unknown'))
 def test_depicted_costume_date_does_not_replace_creation(self):self.assertEqual((self.ds[93]['facts']['first'],self.ds[93]['facts']['last']),(1932,1932))
 def test_recto_verso_and_heads_are_single_objects(self):
  for n in [20,65,66,69,72,73,75,99]:self.assertEqual(sum(d['source_id']==self.ds[n]['source_id'] for d in self.ds.values()),1)
 def test_joined_fragments_and_group_leaves_held(self):self.assertTrue({22,94,95}<={v['number'] for v in self.held})
 def test_identical_crowd_notices_held(self):
  for n in [76,77]:self.assertEqual(self.ds[n]['state'],'held_editorial_review')
 def test_folded_document_not_counted_as_sketchbook(self):
  d=self.ds[72];self.assertEqual(d['state'],'approved_review_only_addition');self.assertIn('one folded',d['facts']['description_md'])
 def test_all_new_source_records_accounted_for(self):
  allrows=self.rows+self.held+self.known;self.assertEqual(len(allrows),100);self.assertEqual(len({v['source_id'] for v in allrows}),100)
 def test_new_page_does_not_repeat_prior_sources(self):
  prior=r.m.load(r.m.RUN/'native/beziers-20261009/joconde-selected-001.json.gz')['rows'];new=r.m.load(r.RUN/'joconde-selected-001.json.gz')['rows'];self.assertFalse({v['Reference'] for v in prior}&{v['Reference'] for v in new})
 def test_no_exact_year_for_unrecognized_expression(self):
  with self.assertRaises(ValueError):f.dates({'Millesime_de_creation':'1930 ou 1934'})
if __name__=='__main__':unittest.main()
