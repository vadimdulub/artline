"""Offline evidence and preservation guards; no database fixtures or writes."""
import copy,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-milan-review-20261009.py'));r=importlib.util.module_from_spec(z);z.loader.exec_module(r)
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows=r.m.load(r.RUN/'source-context-001.json.gz')['rows'];cls.native=r.m.load(r.RUN/'identity-003.json.gz')['rows'];cls.ds=r.build()
 def pair(self,n=1):return copy.deepcopy(self.rows[n-1]),copy.deepcopy(self.native[n-1]['native_matches'][0])
 def reject_triple(self,p,old,new):
  a,n=self.pair();found=False
  for t in a['triples']:
   if t['p']==p and t['o']==old:t['o']=new;found=True
  self.assertTrue(found)
  with self.assertRaises(AssertionError):r.facts(a,n)
 def test_city(self):self.reject_triple(r.s.DC+'coverage','Milano (MI)','Verbania (VB)')
 def test_museum(self):self.reject_triple(r.s.LOC+'hasCulturalInstituteOrSite',r.s.MURI,'wrong-museum')
 def test_historical_location(self):self.reject_triple(r.s.LOC+'hasLocationType',r.s.LOC+'CurrentPhysicalLocation',r.s.LOC+'HistoricalLocation')
 def test_private_label_retained(self):self.assertTrue(all('proprietà privata' in t for t in r.facts(*self.pair())['legal_labels']))
 def test_changed_title(self):
  a,n=self.pair();a['artwork']['title']='Different view'
  with self.assertRaises(AssertionError):r.facts(a,n)
 def test_changed_creator(self):
  a,n=self.pair();a['artwork']['unlinked_creator_label']='Other Mariani'
  with self.assertRaises(AssertionError):r.facts(a,n)
 def test_changed_date(self):
  a,n=self.pair();a['artwork']['date_display']='1901'
  with self.assertRaises(AssertionError):r.facts(a,n)
 def test_duplicate_source(self):
  a,n=self.pair();a['identity_hits'][0]['entity_id']='other-artwork'
  with self.assertRaises(AssertionError):r.facts(a,n)
 def test_native_coauthor(self):
  a,n=self.pair();n['parsed']['fields']['autori'].append('Second author (esecutore)')
  with self.assertRaises(AssertionError):r.facts(a,n)
 def test_native_creator(self):
  a,n=self.pair();n['parsed']['fields']['autori']=['Other artist (esecutore)']
  with self.assertRaises(AssertionError):r.facts(a,n)
 def test_post_cutoff_native(self):
  a,n=self.pair();n['parsed']['date']='1971'
  with self.assertRaises(AssertionError):r.facts(a,n)
 def test_native_date_disagreement(self):
  a,n=self.pair();n['parsed']['date']='1884'
  with self.assertRaises(AssertionError):r.facts(a,n)
 def test_duplicates_excluded(self):self.assertEqual({d['number'] for d in self.ds if d['state']=='duplicate_candidate_hold'},r.DUPLICATES)
 def test_ambiguities_excluded(self):self.assertEqual({d['number'] for d in self.ds if d['state']=='editorial_hold'},set(r.HOLDS))
 def test_unknowns_preserved(self):
  chosen=[d for d in self.ds if d['state']=='approved_existing_holding'];self.assertEqual(len(chosen),122);self.assertEqual(sum(d['facts']['existing_date_precision']=='unknown' for d in chosen),60);self.assertTrue(all(d['derived_fields']==[] for d in chosen))
 def test_inganni_conflict_explicit(self):
  d=self.ds[55];self.assertEqual(d['facts']['date_display'],'ca. 1850-ca. 1850');self.assertEqual(d['facts']['native_fields']['date'],'1856 - 1859');self.assertIn('black to blue',d['basis']);self.assertEqual(d['facts']['existing_date_precision'],'unknown')
 def test_birth_year_not_creation(self):
  f=r.facts(*self.pair(14));self.assertEqual(f['date_display'],'1879-1879');self.assertIn('1810',f['creator_label'])
 def test_components_no_parent(self):
  invs={d['facts']['inventory'] for d in self.ds};self.assertEqual(len(invs),151);self.assertNotIn('IGB-1759',invs);self.assertTrue({f'IGB-1759-{n}' for n in range(1,8)}<=invs);self.assertTrue({'IGB-1389-1','IGB-1389-2','IGB-1389-3'}<=invs)
if __name__=='__main__':unittest.main()
