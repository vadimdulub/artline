"""Offline regression checks for physical-object identity and museum scope."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-thyssen-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class ThyssenSelection(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records={r['facts']['source_id']:r for r in a.records()};cls.held={r['source_id']:r for r in a.m.load(a.REVIEW)['holds']}
 def test_all_selected_pages_accounted_once(self):
  self.assertEqual(len(self.records),172);self.assertEqual(len(self.held),95);self.assertFalse(set(self.records)&set(self.held))
 def test_dali_date_conflict_does_not_make_new_object(self):
  self.assertNotIn('1974.46',self.records);h=self.held['1974.46'];self.assertEqual(h['facts']['date_display'],'1947');self.assertIn('1944',h['review_note'])
 def test_workshop_and_joint_creators_remain_qualified(self):
  self.assertEqual(self.records['1977.99']['facts']['creator_label'],'Orazio Gentileschi (workshop of)')
  self.assertEqual(self.records['1930.29']['facts']['creator_label'],'El Greco and Jorge Manuel Theotokópoulos')
  self.assertEqual(self.records['1930.35']['facts']['creator_label'],'Jacob Jordaens and Workshop')
 def test_byzantine_anonymous_triptych_is_one_supported_record(self):
  r=self.records['1934.30.1-3'];self.assertEqual(r['facts']['creator_label'],'Anonymous Venetian artist');self.assertIn('Byzantine',r['facts']['source_description']);self.assertIn('One complete triptych',r['decision']['basis'])
 def test_recto_verso_counted_as_one_sheet(self):
  r=self.records['1973.65.a/b'];self.assertIn('one record for the sheet',r['decision']['basis']);self.assertIn('verso',r['facts']['title'])
  self.assertNotIn('1973.66.a',self.records);self.assertNotIn('1973.66.b',self.records)
 def test_diptych_not_two_additions(self):
  r=self.records['1933.11.2'];self.assertIn('Left wing',r['facts']['dimensions_text']);self.assertIn('Right wing',r['facts']['dimensions_text']);self.assertIn('one catalogue record',r['decision']['basis'].lower())
 def test_barcelona_deposits_and_bare_carmen_credits_held(self):
  for sid in ['1962.1','1930.120','1928.14.4','1928.14.2','1930.71','1936.3']:self.assertNotIn(sid,self.records);self.assertEqual(self.held[sid]['state'],'source_hold')
  for r in self.records.values():self.assertEqual(r['facts']['credit_line'],'Museo Nacional Thyssen-Bornemisza, Madrid')
 def test_unknown_type_not_fabricated_from_work_on_paper(self):
  for sid,label in [('1982.22','Work on paper'),('1980.56','Relief')]:
   r=self.records[sid];self.assertEqual(r['facts']['work_type'],'unknown');self.assertIsNone(r['facts']['object_form']);self.assertEqual(r['source_facts']['object_form'],label)
 def test_catalogue_object_form_contract_and_source_preservation(self):
  reviewed={r['source_id']:r['facts'] for r in a.m.load(a.REVIEW)['decisions']}
  for sid,r in self.records.items():
   self.assertEqual(r['source_facts'],reviewed[sid]);self.assertIn(r['facts']['object_form'],(None,'icon'))
   self.assertEqual({k:v for k,v in r['facts'].items() if k!='object_form'},{k:v for k,v in reviewed[sid].items() if k!='object_form'})
  receipt=a.m.load(a.RUN/'failed-plan-002-rollback-verification.json')
  constraint=next(c['definition'] for c in receipt['artwork_constraints'] if c['conname']=='artwork_object_form')
  self.assertEqual(constraint,"CHECK (((object_form IS NULL) OR (object_form = 'icon'::text)))")
 def test_late_creation_and_acquisition_year_are_separate(self):
  r=self.records['1974.53'];self.assertEqual((r['facts']['first'],r['facts']['last']),(1970,1970));self.assertEqual(r['facts']['date_precision'],'exact')
  r=self.records['1971.7'];self.assertEqual((r['facts']['first'],r['facts']['last']),(1310,1311))
 def test_reworking_range_retained(self):
  v=self.records['1973.63']['facts'];self.assertEqual((v['first'],v['last']),(1914,1925))
 def test_close_pastel_and_candle_versions_remain_held(self):
  for sid in ['1978.10','1930.21','1972.13','1979.62']:self.assertNotIn(sid,self.records);self.assertEqual(self.held[sid]['state'],'version_hold')
 def test_pendants_and_editions_have_explicit_identity_evidence(self):
  self.assertIn('separate pendant',self.records['1935.14']['decision']['basis']);self.assertIn('first edition',self.records['1973.32']['decision']['basis']);self.assertIn('two large versions',self.records['1980.55']['decision']['basis'])
 def test_current_museum_count_does_not_imply_publication(self):
  for r in self.records.values():
   v=a.expected_art(r);self.assertEqual(v['status'],'review');self.assertTrue(v['research_candidate']);self.assertEqual(v['current_institution_id'],a.IID)
   self.assertLessEqual(v['creation_year_end'],1970);self.assertNotIn('published_at',v);self.assertNotIn('primary_media_id',v)
 def test_qualified_sitter_and_source_rights_preserved(self):
  r=self.records['1982.16'];self.assertIn('(?)',r['facts']['title']);self.assertIsNone(r['facts']['source_rights'])
if __name__=='__main__':unittest.main()
