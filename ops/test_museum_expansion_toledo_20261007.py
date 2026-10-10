#!/usr/bin/env python3
"""Offline source, date, attribution and identity checks. No database fixtures or writes."""
import copy,importlib.util,tempfile,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-toledo-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);w=a.w;m=a.m
class Dates(unittest.TestCase):
 def test_circa_marker(self):self.assertEqual(w.creation('about 1905'),dict(first=1905,last=1905,date_precision='circa',date_issue=None))
 def test_short_range(self):self.assertEqual((w.creation('1842-3')['first'],w.creation('1842-3')['last']),(1842,1843))
 def test_circa_range(self):self.assertEqual(w.creation('about 1620 - 29')['date_precision'],'circa_range')
 def test_qualified_century(self):self.assertEqual(w.creation('Probably mid-17th century'),dict(first=1601,last=1700,date_precision='circa_range',date_issue=None))
 def test_no_narrow_mid_late_bounds(self):self.assertEqual((w.creation('mid-late 17th Century')['first'],w.creation('mid-late 17th Century')['last']),(1601,1700))
 def test_explicit_era_bounds(self):self.assertEqual((w.creation('Meiji Era (1868-1912)')['first'],w.creation('Meiji Era (1868-1912)')['last']),(1868,1912))
 def test_unresolved_dynasty_conflict(self):self.assertIsNotNone(w.creation('Northern Song Dynasty (960-1279), 952')['date_issue'])
 def test_after_open_end(self):self.assertIsNotNone(w.creation('1545 or after')['date_issue'])
 def test_no_artist_lifespan_inference(self):self.assertIsNotNone(w.creation(None)['date_issue'])
 def test_twentieth_century_cutoff(self):self.assertIsNotNone(w.creation('early 20th Century')['date_issue'])
 def test_circa_cutoff(self):self.assertIsNotNone(w.creation('about 1970')['date_issue'])
 def test_post_cutoff(self):self.assertIsNotNone(w.creation('1971')['date_issue'])
class Sources(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=a.records();cls.byid={r['facts']['source_id']:r for r in cls.records}
 def page(self,sid='55352'):
  r=self.byid[sid];return w.pages(m.load(m.ROOT/r['decision']['source_reference']['path'])['result'])[0]
 def test_source_chain_revalidation(self):self.assertEqual(len(self.records),105)
 def test_unique_inventories(self):self.assertEqual(len({r['facts']['inventory'] for r in self.records}),105)
 def test_dormition_school_label(self):self.assertEqual(self.byid['57075']['facts']['creator_label'],'School of Andrey Rublyov')
 def test_velazquez_qualification(self):self.assertEqual(self.byid['55370']['facts']['creator_label'],'Attributed to Diego Velázquez')
 def test_copy_qualification(self):self.assertEqual(self.byid['57056']['facts']['creator_label'],'After Jean-François Millet')
 def test_unknown_creator_not_invented(self):self.assertIsNone(self.byid['56983']['facts']['creator_label'])
 def test_unknown_medium_not_invented(self):self.assertIsNone(self.byid['76788']['facts']['medium'])
 def test_metal_cover_evidence_preserved(self):self.assertEqual(self.byid['57076']['facts']['medium'],'metal and stones')
 def test_lifespan_not_catalogue_date(self):self.assertEqual(self.byid['54744']['facts']['creator_label'],'Piero di Cosimo');self.assertEqual(self.byid['54744']['facts']['date_display'],'about 1495-1500')
 def test_known_duplicate_excluded(self):self.assertNotIn('55283',self.byid)
 def test_unresolved_group_excluded(self):self.assertNotIn('55257',self.byid)
 def test_fragment_is_one_accession(self):self.assertEqual(self.byid['55216']['facts']['inventory'],'1951.341');self.assertIn('fragment',self.byid['55216']['decision']['basis'])
 def test_outward_loan_not_display(self):
  r=self.byid['57079'];self.assertIn('On Loan',r['decision']['basis']);self.assertNotIn('current_location_text',a.expected_art(r))
 def test_foreign_host_rejected(self):
  p=copy.deepcopy(self.page());p['url']=p['url'].replace('emuseum.toledomuseum.org','example.com')
  with self.assertRaises(AssertionError):w.object_facts(p)
 def test_partial_extract_rejected(self):
  p=copy.deepcopy(self.page());p['complete']=False
  with self.assertRaises(AssertionError):w.object_facts(p)
 def test_duplicate_date_field_rejected(self):
  p=copy.deepcopy(self.page());pos=next(i for i,(n,t) in enumerate(p['lines']) if t.startswith('Date '));p['lines'].insert(pos,(999,'Date 2000'))
  with self.assertRaises(AssertionError):w.object_facts(p)
 def test_hashed_evidence_mutation_rejected(self):
  with tempfile.TemporaryDirectory(prefix='artline-toledo-test-') as temp:
   p=Path(temp)/'evidence';p.write_text('changed')
   with self.assertRaises(AssertionError):a.checked_reference(dict(path=str(p),sha256='0'*64))
 def test_all_leads_accounted_for(self):
  follow=m.load(a.RUN/'native-followup-queue-001.json.gz');q=m.load(a.RUN/'web-object-queue-002.json');self.assertEqual(len(self.records)+len(follow['rows'])+len(follow['capture_errors']),len(q['rows']))
 def test_review_only(self):self.assertTrue(all(a.expected_art(r)['status']=='review' for r in self.records))
 def test_session_free_source_urls(self):self.assertTrue(all(';' not in r['facts']['source_url'] and '?' not in r['facts']['source_url'] for r in self.records))
if __name__=='__main__':unittest.main()
