"""Offline tests of object identity, source conflicts and branch boundaries."""
import copy,importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
z=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-britain-six-review-20261009.py'));r=importlib.util.module_from_spec(z);z.loader.exec_module(r)
class Review(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=r.m.load(r.RUN/'source-context-001.json.gz')['rows'];cls.initial=r.m.load(r.RUN/'initial-scope-001.json.gz');cls.decisions=r.build();cls.by={v['number']:v for v in cls.decisions}
 def row(self,n=1):return copy.deepcopy(self.rows[n-1])
 def test_wrong_museum(self):
  v=self.row();v['entity']['claims']['P195'][0]['mainsnak']['datavalue']['value']['id']='Q4968867'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_ended_holding(self):
  v=self.row();v['entity']['claims']['P195'][0].setdefault('qualifiers',{})['P582']=[{}]
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_wrong_inventory(self):
  v=self.row();v['artwork']['accession_number']='WRONG'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_inventory_scope(self):
  v=self.row();v['entity']['claims']['P217'][0]['qualifiers']['P195'][0]['datavalue']['value']['id']='Q4968867'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_wrong_object(self):
  v=self.row();v['source_id']='Q1'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_wrong_primary_reference(self):
  v=self.row();v['entity']['claims']['P195'][0]['references'][0]['snaks']['P1679'][0]['datavalue']['value']='wrong-object-1'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_changed_title(self):
  v=self.row();v['artwork']['title']='Different castle';self.assertIn('literal_title_mismatch',r.f.facts(v,self.initial)['issues'])
 def test_archived_exclusion(self):
  v=self.row();v['artwork']['status']='archived';self.assertIn('archived_record_excluded',r.f.facts(v,self.initial)['issues'])
 def test_post1970_flag(self):
  v=self.row();v['artwork']['creation_year_end']=1971;self.assertIn('post1970_catalogue_date',r.f.facts(v,self.initial)['issues'])
 def test_native_new_modern_date_fails(self):
  rows=copy.deepcopy(r.native_rows());rows[2]['parsed']['fields']['Date/Period:']=['1971']
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
 def test_native_new_attribution_fails(self):
  rows=copy.deepcopy(r.native_rows());rows[2]['parsed']['fields']['Artist / Maker:'][0]+=' (attributed to)'
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
 def test_native_prose_attribution_fails(self):
  rows=copy.deepcopy(r.native_rows());rows[2]['parsed']['fields']['Brief Description:']=['Attributed to Walter Langley']
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
 def test_native_inventory_conflict_fails(self):
  rows=copy.deepcopy(r.native_rows());rows[2]['parsed']['fields']['Accession No:']=['KINCM:9999.1']
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
 def test_native_wrong_object_type_fails(self):
  rows=copy.deepcopy(r.native_rows());rows[2]['parsed']['fields']['Object Name:']=['frame']
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
 def test_native_search_new_flag(self):
  from urllib.parse import parse_qs,urlsplit
  q=parse_qs(urlsplit(r.w.search_url('KINCM:2005.5077a')).query);self.assertEqual(q['newsearch'],['new']);self.assertEqual(q['museum2'],['Ferens Art Gallery']);self.assertEqual(q['location'],['any']);self.assertEqual(q['accessionnumber'],['KINCM:2005.5077a'])
 def test_inventory_prefix_only_normalization(self):
  self.assertEqual(r.w.invkey('2005.5027'),r.w.invkey('KINCM:2005.5027'));self.assertNotEqual(r.w.invkey('KINCM:2005.5077a'),r.w.invkey('KINCM:2005.5077b'));self.assertNotEqual(r.w.invkey('KINCM:2005.5067.1'),r.w.invkey('KINCM:2005.5067.2'))
 def test_overview_is_not_detailed_object(self):
  with self.assertRaises(AssertionError):r.w.parsed(b'<dl><dt>Title:</dt><dd>Painting</dd><dt>Museum link:</dt><dd>Ferens Art Gallery</dd></dl>')
 def test_parser_preserves_repeated_values_and_dimensions(self):
  raw=b'<dl><dt>Accession No:</dt><dd>KINCM:2005.1</dd><dt>Artist / Maker:</dt><dd>A</dd><dt>Artist / Maker:</dt><dd>B</dd></dl><table class="displayDimensions"><tr><th>Type</th><th>Height</th></tr><tr><td>Frame</td><td>100[mm]</td></tr></table>';d=r.w.parsed(raw);self.assertEqual(d['fields']['Artist / Maker:'],['A','B']);self.assertEqual(d['dimensions'],[['Type','Height'],['Frame','100[mm]']])
 def test_modern_native_date_held(self):self.assertEqual(self.by[153]['state'],'editorial_hold')
 def test_attributed_creators_held(self):
  for n in [11,74]:self.assertEqual(self.by[n]['state'],'editorial_hold')
 def test_creator_chronology_conflicts_held(self):
  for n in [6,50,75,96,99,105]:self.assertEqual(self.by[n]['state'],'editorial_hold')
 def test_front_back_not_double_counted(self):
  for n in [30,232,102,189]:self.assertEqual(self.by[n]['state'],'editorial_hold')
 def test_diptych_triptych_scope_held(self):
  for n in [29,238,61,148,231]:self.assertEqual(self.by[n]['state'],'editorial_hold')
 def test_separate_series_panels_supported(self):
  for n in [31,72,245]:self.assertEqual(self.by[n]['state'],'approved_existing_holding');self.assertIn('separate',self.by[n]['basis'])
 def test_version_uncertainty_held(self):
  for n in [23,46,116]:self.assertEqual(self.by[n]['state'],'editorial_hold')
 def test_context_biography_not_primary_object_confirmation(self):
  ds=[d for d in self.decisions if d['institution_id']==r.s.IIDS[0] and d['state']=='approved_existing_holding'];self.assertTrue(ds);self.assertTrue(all(d['selected_native_object_url'] is None and d['confidence']==.8 and 'do not independently confirm' in d['basis'] for d in ds))
 def test_native_creation_evidence_does_not_rewrite_unknown_date(self):
  self.assertEqual(self.by[15]['facts']['date_precision'],'unknown');self.assertIsNone(self.by[15]['facts']['last']);self.assertEqual(r.native_rows()[15]['parsed']['fields']['Date/Period:'],['c.1935'])
 def test_title_keywords_not_attribution(self):
  for n in [126,235]:self.assertEqual(self.by[n]['state'],'approved_existing_holding');self.assertIn('filename_or_title_qualification',self.by[n]['resolved_issues'])
 def test_preserve_review_and_no_derived_metadata(self):self.assertTrue(all(v['existing_status']=='review' and not v['derived_fields'] and v['previous_institution_id'] is None for v in self.decisions))
if __name__=='__main__':unittest.main()
