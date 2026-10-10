"""Offline evidence and qualification guards; no catalogue fixtures or writes."""
import copy,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-britain-two-review-20261008.py'));r=importlib.util.module_from_spec(z);z.loader.exec_module(r)
class Review(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows=r.m.load(r.RUN/'source-context-001.json.gz')['rows'];cls.initial=r.m.load(r.RUN/'initial-scope-001.json.gz');cls.decisions=r.build()
 def row(self,n=1):return copy.deepcopy(self.rows[n-1])
 def test_wrong_museum(self):
  v=self.row();v['entity']['claims']['P195'][0]['mainsnak']['datavalue']['value']['id']='Q1800739'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_ended_holding(self):
  v=self.row();v['entity']['claims']['P195'][0].setdefault('qualifiers',{})['P582']=[{}]
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_inventory_conflict(self):
  v=self.row();v['artwork']['accession_number']='NAM. 1964-02-43'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_inventory_museum_conflict(self):
  v=self.row();v['entity']['claims']['P217'][0]['qualifiers']['P195'][0]['datavalue']['value']['id']='Q1800739'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_changed_title(self):
  v=self.row();v['artwork']['title']='Other Recruit';self.assertIn('literal_title_mismatch',r.f.facts(v,self.initial)['issues'])
 def test_source_object_mismatch(self):
  v=self.row();v['source_id']='Q1'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_reference_url_form(self):
  v=self.row(5);self.assertEqual(r.f.facts(v,self.initial)['issues'],[])
 def test_bad_reference(self):
  v=self.row(5);v['entity']['claims']['P195'][0]['references'][0]['snaks']['P854'][0]['datavalue']['value']='https://artuk.org/discover/artworks/wrong-1'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_duplicate_same_collection(self):
  for n in [17,56]:self.assertEqual(r.f.facts(self.row(n),self.initial)['issues'],[])
 def test_acquisition_not_creation(self):
  d=self.decisions[55];self.assertEqual(d['facts']['first'],1912);self.assertEqual(r.f.w.year(r.f.qual(d['facts']['source_collection_statements'][0],'P580')),2001)
 def test_unknown_dates_preserved(self):
  ds=[v for v in self.decisions if v['state']=='approved_existing_holding' and v['facts']['date_precision']=='unknown'];self.assertEqual(len(ds),27);self.assertTrue(all(v['facts']['first'] is None and v['facts']['last'] is None and not v['derived_fields'] for v in ds))
 def test_unlinked_creators_preserved(self):
  qs=r.m.load(r.RUN/'unlinked-creator-authorities-001.json.gz')['rows'];self.assertEqual(len(qs),15);self.assertTrue(all(q['label_match'] and self.decisions[q['number']-1]['facts']['artist_links']==[] for q in qs))
 def test_copy_dates_preserved(self):
  self.assertEqual([(self.decisions[n-1]['facts']['first'],self.decisions[n-1]['state']) for n in [116,194,218]],[(1849,'approved_existing_holding'),(1904,'approved_existing_holding'),(1917,'approved_existing_holding')])
 def test_false_temporal_after(self):self.assertEqual(self.decisions[56]['state'],'approved_existing_holding')
 def test_native_attribution_and_duplicates_held(self):
  self.assertEqual({v['number'] for v in self.decisions if v['state']=='editorial_hold'},{23,33,71,104,121,176,178,185,207})
 def test_native_watercolour_identity(self):
  d=self.decisions[211];self.assertEqual(d['state'],'approved_existing_holding');self.assertEqual(d['facts']['inventory'],'NAM. 1975-05-7-1');self.assertEqual(d['facts']['first'],1815);self.assertEqual(d['derived_fields'],[])
if __name__=='__main__':unittest.main()
