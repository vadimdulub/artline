"""Offline source/date/credit tests on selected real evidence; no database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('proof',Path(__file__).with_name('museum-expansion-thyssen-proof-20261007.py'));proof=importlib.util.module_from_spec(s);s.loader.exec_module(proof);f=proof.f;m=f.m
class ThyssenSources(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows={}
  for suffix in ['001','002']:
   for ref in m.load(f.RUN/('selected-capture-'+suffix+'.json.gz'))['records']:
    x,p=proof.checked_record(ref['path'],ref['sha256']);v=f.facts(x,p);cls.rows[v['source_id']]=(x,p,v)
 def test_initial_selected_chain_is_bounded_and_distinct(self):self.assertEqual(len(self.rows),136)
 def test_creation_not_accession_year(self):
  v=self.rows['1971.7'][2];self.assertEqual((v['first'],v['last']),(1310,1311));self.assertEqual(v['inventory'],'133 ( 1971.7 )')
 def test_1971_masterpiece_excluded_before_capture(self):
  rows=m.load(f.RUN/'masterpiece-leads-001.json.gz')['rows'];out=[r for r in rows if r['state']=='outside_1970_scope'];self.assertEqual(len(out),1);self.assertEqual(out[0]['date_display'],'1971')
  self.assertNotIn(out[0]['source_url'],{v[2]['source_url'] for v in self.rows.values()})
 def test_source_names_bound_by_native_creator_url(self):
  x,p,v=self.rows['1934.38'];self.assertEqual(v['creator_label'],'Albrecht Dürer');self.assertEqual(v['detail_creator_label'],'Dürer, Albrecht');self.assertFalse(f.source_holds(v,x,p))
 def test_different_creator_url_is_held(self):
  x,p,v=copy.deepcopy(self.rows['1934.38']);v['creator_fields'][0]['url']+='-different-person';self.assertIn('Creator labels or role structure require review',f.source_holds(v,x,p))
 def test_index_date_disagreement_is_held(self):
  x,p,v=copy.deepcopy(self.rows['1971.7']);v['index_date']='1320';self.assertIn('Related/masterpiece card and object dates disagree',f.source_holds(v,x,p))
 def test_source_qualifications_are_not_dropped(self):
  vs=[v for x,p,v in self.rows.values() if 'attributed' in (v['creator_label'] or '').casefold() or 'workshop' in (v['creator_label'] or '').casefold()];self.assertGreaterEqual(len(vs),2)
  self.assertTrue(all(v['creator_fields'] for v in vs))
 def test_barcelona_deposit_not_madrid_holding(self):
  vs=[(x,p,v) for x,p,v in self.rows.values() if 'MNAC' in v['credit_line']];self.assertGreaterEqual(len(vs),5)
  for x,p,v in vs:self.assertIn('Qualified collection/deposit/holding credit requires explicit review',f.source_holds(v,x,p))
 def test_bare_carmen_credit_is_held(self):
  vs=[(x,p,v) for x,p,v in self.rows.values() if v['credit_line']=='Carmen Thyssen Collection'];self.assertGreaterEqual(len(vs),10)
  for x,p,v in vs:self.assertIn('Qualified collection/deposit/holding credit requires explicit review',f.source_holds(v,x,p))
 def test_empty_credit_not_inferred_from_gallery_map(self):
  x,p,v=self.rows['1973.66.a'];self.assertEqual(v['credit_line'],'');self.assertEqual(v['source_location_label'],'Room 36');self.assertIn('Qualified collection/deposit/holding credit requires explicit review',f.source_holds(v,x,p))
 def test_work_on_paper_not_invented_as_painting(self):
  for sid in ['1971.2','1982.22']:
   v=self.rows[sid][2];self.assertEqual(v['source_artform'],'Work on paper');self.assertEqual(v['work_type'],'unknown');self.assertEqual(v['object_form'],'Work on paper')
 def test_relief_retains_source_form(self):
  v=self.rows['1980.56'][2];self.assertEqual(v['work_type'],'unknown');self.assertEqual(v['object_form'],'Relief');self.assertEqual(v['dimensions_text'],'18 x 25 x 2.2 cm')
 def test_spanish_and_english_native_urls_retained(self):
  v=self.rows['1934.8'][2];self.assertEqual(len(v['native_page_urls']),2);self.assertTrue(any('/coleccion/artistas/' in u for u in v['native_page_urls']))
 def test_unknown_and_cross_cutoff_dates_stay_held(self):
  for raw in ['s.f','', '1969 - 1972','1971','ca. 1970','after 1960']:self.assertIsNotNone(f.n.creation(raw)['date_issue'])
 def test_source_numeric_dates_preserve_precision(self):
  v=f.n.creation('ca.  1598-99');self.assertEqual((v['first'],v['last'],v['date_precision']),(1598,1599,'circa_range'))
  v=f.n.creation('1969 - 1970');self.assertEqual((v['first'],v['last'],v['date_precision']),(1969,1970,'range'))
 def test_corrupted_source_reference_is_rejected(self):
  with self.assertRaises(AssertionError):proof.checked_reference(dict(path='AGENTS.md',sha256='0'*64))
if __name__=='__main__':unittest.main()
