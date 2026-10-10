"""Offline source and physical-object checks; no database fixtures."""
import importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-brest-review-20261009.py'));r=importlib.util.module_from_spec(z);z.loader.exec_module(r);f=r.i.f
class EvidenceBoundaries(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds={d['number']:d for d in r.build()};cls.rows,cls.held,cls.known=f.rows()
 def test_period_not_replaced_with_artist_lifespan(self):self.assertEqual(f.dates({'Periode_de_creation':'4e quart 19e siècle;1ère moitié 20e siècle','Auteur':'Schuffenecker Émile (1851-1934)'})[:3],(1876,1950,'range'))
 def test_notice_and_acquisition_dates_not_creation(self):self.assertEqual(f.dates({'Date_creation':'2014-04-07','Date_d_acquisition':'1984'})[:3],(None,None,'unknown'))
 def test_circa_suffix_retained(self):self.assertEqual(f.dates({'Millesime_de_creation':'1930 vers'})[:3],(1930,1930,'circa'))
 def test_post_1970_period_not_truncated(self):self.assertEqual(f.dates({'Periode_de_creation':'20e siècle'})[:3],(1901,2000,'century'))
 def test_poster_missing_dimensions_not_invented(self):self.assertIsNone(self.ds[7]['facts']['dimensions_text'])
 def test_sculpture_not_confused_with_photograph(self):
  self.assertEqual(self.ds[32]['facts']['work_type'],'sculpture');self.assertIn(66,{v['number'] for v in self.held})
 def test_shared_support_and_two_print_group_held(self):self.assertTrue({39,103}<={v['number'] for v in self.held})
 def test_recto_verso_count_once(self):
  for n in [19,34]:self.assertEqual(sum(d['facts']['inventory']==self.ds[n]['facts']['inventory'] for d in self.ds.values()),1);self.assertIn('reverse',self.ds[n]['facts']['description_md'])
 def test_close_alternate_title_not_auto_approved(self):self.assertEqual(self.ds[70]['state'],'held_editorial_review')
 def test_inventory_collision_does_not_merge_other_museum(self):
  for n in [92,99]:self.assertEqual(self.ds[n]['state'],'approved_review_only_addition');self.assertTrue(any('inventory' in h['hit_types'] and not h['same_museum'] for h in self.ds[n]['comparison']['hits']))
 def test_design_is_drawing_and_poster_is_print(self):self.assertEqual((self.ds[92]['facts']['work_type'],self.ds[7]['facts']['work_type']),('drawing','print'))
 def test_every_source_notice_has_one_decision(self):
  rows=self.rows+self.held+self.known;self.assertEqual(len(rows),103);self.assertEqual(len({v['source_id'] for v in rows}),103)
if __name__=='__main__':unittest.main()
