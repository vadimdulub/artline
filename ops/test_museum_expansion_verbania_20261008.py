"""Offline evidence guard tests; no database fixtures or writes."""
import copy,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-verbania-review-20261008.py'));r=importlib.util.module_from_spec(z);z.loader.exec_module(r)
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows=r.m.load(r.RUN/'source-context-001.json.gz')['rows'];cls.ds=r.build()
 def row(self,n=1):return copy.deepcopy(self.rows[n-1])
 def reject_triple(self,p,old,new):
  v=self.row();found=False
  for t in v['triples']:
   if t['p']==p and t['o']==old:t['o']=new;found=True
  self.assertTrue(found)
  with self.assertRaises(AssertionError):r.facts(v)
 def test_city(self):self.reject_triple(r.s.DC+'coverage','Verbania (VB)','Pavia (PV)')
 def test_museum(self):self.reject_triple(r.s.LOC+'hasCulturalInstituteOrSite',r.s.MURI,'wrong-museum')
 def test_historical_location(self):self.reject_triple(r.s.LOC+'hasLocationType',r.s.LOC+'CurrentPhysicalLocation',r.s.LOC+'HistoricalLocation')
 def test_private_label_retained(self):self.assertTrue(all('proprietà privata' in t for t in r.facts(self.row())['legal_labels']))
 def test_owner_not_inferred(self):self.assertEqual(r.facts(self.row())['legal_owner_uris'],['https://w3id.org/arco/resource/Agent/da9a5d411f26432c372928081ddf6f5c'])
 def test_changed_title(self):
  v=self.row();v['artwork']['title']='Other Flora'
  with self.assertRaises(AssertionError):r.facts(v)
 def test_changed_creator(self):
  v=self.row();v['artwork']['unlinked_creator_label']='Unknown Browne'
  with self.assertRaises(AssertionError):r.facts(v)
 def test_changed_date(self):
  v=self.row();v['artwork']['date_display']='1901'
  with self.assertRaises(AssertionError):r.facts(v)
 def test_duplicate_source(self):
  v=self.row();v['identity_hits'][0]['entity_id']='different-artwork'
  with self.assertRaises(AssertionError):r.facts(v)
 def test_malformed_dates_held(self):self.assertTrue(all(self.ds[n-1]['state']=='editorial_hold' for n in [117,133]))
 def test_ambiguous_versions_held(self):self.assertTrue(all(self.ds[n-1]['state']=='editorial_hold' for n in [18,75,106,145]))
 def test_cutoff_inclusive(self):self.assertEqual((self.ds[45]['state'],self.ds[45]['facts']['existing_creation_year_end']),('approved_existing_holding',1970))
 def test_unknowns_not_enriched(self):
  approved=[d for d in self.ds if d['state']=='approved_existing_holding'];self.assertEqual(sum(d['facts']['existing_date_precision']=='unknown' for d in approved),15);self.assertTrue(all(d['derived_fields']==[] for d in approved))
 def test_physical_units_and_metadata(self):
  self.assertEqual(len({d['facts']['inventory'] for d in self.ds}),161);self.assertEqual(len({d['existing_artwork_id'] for d in self.ds}),161);self.assertEqual(self.ds[18]['facts']['title'],'Tre volti femminili');self.assertEqual(self.ds[27]['facts']['title'],'Bagnanti, Banganti')
if __name__=='__main__':unittest.main()
