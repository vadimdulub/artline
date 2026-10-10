#!/usr/bin/env python3
"""Offline evidence/date/identity regression checks; never connect to a database."""
import copy,importlib.util,tempfile,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-budapest-gac-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
w=a.w;m=a.m
class Dates(unittest.TestCase):
 def test_explicit_range(self):self.assertEqual(w.creation('between 1808 and 1812'),dict(first=1808,last=1812,date_precision='range',date_issue=None))
 def test_circa_range(self):self.assertEqual(w.creation('ca. 1495–1496'),dict(first=1495,last=1496,date_precision='circa_range',date_issue=None))
 def test_full_decade_retained(self):self.assertEqual(w.creation('early 1620s')['last'],1629)
 def test_uncertain_cutoff_held(self):self.assertIsNotNone(w.creation('ca. 1970')['date_issue'])
 def test_post_cutoff_held(self):self.assertIsNotNone(w.creation('1989')['date_issue'])
 def test_multi_phase_not_conflated(self):self.assertIsNotNone(w.creation('model: 1884; marble carving: 1901')['date_issue'])
 def test_alternative_years_not_range(self):self.assertIsNotNone(w.creation('1510 or 1520')['date_issue'])
 def test_open_end_held(self):self.assertIsNotNone(w.creation('ca. 1507 or later')['date_issue'])
 def test_no_date_invented(self):self.assertEqual(w.creation(None)['date_precision'],'unknown')
 def test_uncertain_century_whole_bounds(self):self.assertEqual((w.creation('first half of the 16th century')['first'],w.creation('first half of the 16th century')['last']),(1500,1599))
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=a.records();cls.byid={r['facts']['source_id']:r for r in cls.records}
 def test_all_sources_revalidated(self):self.assertEqual(len(self.records),103)
 def test_unique_physical_inventories(self):self.assertEqual(len({r['facts']['inventory'] for r in self.records}),103)
 def test_no_source_scope_leaks(self):self.assertTrue(all(r['facts']['publisher']=='Museum of Fine Arts Budapest' for r in self.records))
 def test_qualified_creator_survives_entity_heading(self):self.assertEqual(self.byid['ggFVBm9bDkQ6eg']['facts']['creator_label'],'Leonardo da Vinci (ascribed to)')
 def test_after_attribution_retained(self):self.assertEqual(self.byid['XAGiXIp9spXPJA']['facts']['creator_label'],'Lorenzo Ghiberti (after)')
 def test_anonymous_school_label_preserved(self):self.assertEqual(self.byid['yQGC-yopeFV21Q']['facts']['creator_label'],'Bohemian Artist')
 def test_unknown_type_retained(self):
  f=self.byid['lAH12XeDTwiXcQ']['facts'];self.assertEqual((f['work_type'],f['source_type']),('unknown','relief'))
 def test_known_duplicates_held(self):self.assertTrue({'5wFvaxMutFadYw','FAFbvvEOZ39B2A','-gGLrO1BwvNcmQ','WQEo76LiC6nvnA'}.isdisjoint(self.byid))
 def test_internal_date_conflicts_held(self):self.assertTrue({'pwGg-8hGffZlbg','fwG76CONgysT8Q','sAGc0AZndjyPsw','6wEsUyPTnT-FkQ'}.isdisjoint(self.byid))
 def test_review_status_and_unknown_location(self):
  for r in self.records:
   art=a.expected_art(r);self.assertEqual(art['status'],'review');self.assertTrue(art['research_candidate']);self.assertNotIn('current_location_text',art)
 def test_case_sensitive_source_ids_survive_slug(self):
  r=self.byid['DgFHSEIgpmjUBA'];self.assertEqual(r['facts']['source_id'],'DgFHSEIgpmjUBA');self.assertRegex(r['slug'],r'^[a-z0-9-]+$')
 def test_hashed_evidence_rejects_mutation(self):
  with tempfile.TemporaryDirectory(prefix='artline-budapest-test-') as temp:
   p=Path(temp)/'evidence';p.write_bytes(b'changed')
   with self.assertRaises(AssertionError):a.checked_reference(dict(path=str(p),sha256='0'*64))
 def test_duplicate_identity_fields_rejected(self):
  r=self.records[0];x=m.load(m.ROOT/r['decision']['source_reference']['path']);p=copy.deepcopy(x['parsed']);p['fields'].append(copy.deepcopy(p['fields'][0]))
  with self.assertRaises(AssertionError):w.facts(x,p)
 def test_index_detail_title_conflict_rejected(self):
  r=self.records[0];x=m.load(m.ROOT/r['decision']['source_reference']['path']);x['index']['title']='A different physical object'
  with self.assertRaises(AssertionError):w.facts(x,x['parsed'])
 def test_every_capture_accounted_for(self):
  queue=m.load(a.RUN/'gac-followup-queue-001.json.gz')['rows'];captured=m.load(a.RUN/'gac-selected-capture-001.json.gz')['records'];self.assertEqual(len(self.records)+len(queue),len(captured));self.assertEqual(len(captured),134)
if __name__=='__main__':unittest.main()
