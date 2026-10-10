#!/usr/bin/env python3
"""Offline source, chronology and physical identity checks; no test DB or fixtures."""
import copy,importlib.util,tempfile,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-ngaustralia-gac-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);w=a.w;m=a.m
class Dates(unittest.TestCase):
 def test_exact_creation(self):self.assertEqual(w.creation('1889'),dict(first=1889,last=1889,date_precision='exact',date_issue=None))
 def test_circa_without_space(self):self.assertEqual(w.creation('c1895')['date_precision'],'circa')
 def test_short_range(self):self.assertEqual(w.creation('1946-47')['last'],1947)
 def test_decade_full_bounds(self):self.assertEqual((w.creation('c.1890s')['first'],w.creation('c.1890s')['last']),(1890,1899))
 def test_ambiguous_leading_minus_held(self):self.assertIsNotNone(w.creation('-1931')['date_issue'])
 def test_slash_dates_held(self):self.assertIsNotNone(w.creation('1962/1964')['date_issue'])
 def test_uncertain_cast_held(self):self.assertIsNotNone(w.creation('c.1850-1852, cast1862-1878?')['date_issue'])
 def test_post1970_held(self):self.assertIsNotNone(w.creation('1979')['date_issue'])
 def test_circa1970_held(self):self.assertIsNotNone(w.creation('c.1970')['date_issue'])
 def test_unknown_not_filled_from_biography(self):self.assertEqual(w.creation(None)['date_precision'],'unknown')
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=a.records();cls.byid={r['facts']['source_id']:r for r in cls.records}
 def test_all_source_chains(self):self.assertEqual(len(self.records),103)
 def test_unique_native_ids(self):self.assertEqual(len({r['facts']['native_object_id'] for r in self.records}),103)
 def test_native_irn_not_accession(self):self.assertTrue(all(r['facts']['inventory'] is None for r in self.records))
 def test_uncertain_units_left_unknown(self):
  f=self.byid['5gFJ9OW2MC90rQ']['facts'];self.assertEqual(f['source_dimensions_text'],'w1526 x h813 cm');self.assertIsNone(f['dimensions_text']);self.assertTrue(f['dimension_issue'])
 def test_missing_credit_survives(self):self.assertIsNone(self.byid['ngE6JGArQerbwg']['facts']['acquisition_text'])
 def test_anonymous_cultural_label_retained(self):self.assertEqual(self.byid['XQGpybmaUmr4cA']['facts']['creator_label'],'Unknown MAKER  | Bardi people')
 def test_people_qualifier_retained(self):self.assertEqual(self.byid['iwGd7XfOtg9nlw']['facts']['creator_label'],'William BARAK - Wurundjeri people')
 def test_creator_search_includes_barak(self):self.assertIn('barak',a.i.search_terms(self.byid['iwGd7XfOtg9nlw']['facts']))
 def test_creator_search_includes_mickey(self):self.assertIn('ulladulla',a.i.search_terms(self.byid['zAFhXRk3rYICrA']['facts']))
 def test_unmapped_type_remains_unknown(self):self.assertEqual(self.byid['XQGpybmaUmr4cA']['facts']['work_type'],'unknown')
 def test_buddha_date_is_inscription_year(self):self.assertEqual(self.byid['6QF_yOceObMRag']['facts']['first'],1807)
 def test_screen_one_object(self):self.assertEqual(sum(r['facts']['native_object_id']=='115741' for r in self.records),1)
 def test_later_bronze_not_substituted(self):self.assertEqual(self.byid['VQF2ju2o6lZDnw']['facts']['medium'],'painted plaster')
 def test_seurat_study_distinguished(self):self.assertIn('Tate N06067',self.byid['awGdV5KaneoocQ']['decision']['basis'])
 def test_bridge_variant_distinguished(self):self.assertIn('Bridge in-curve',self.byid['ywE-_izp3iBJoQ']['decision']['basis'])
 def test_known_duplicates_and_joint_holdings_held(self):self.assertTrue({'mwFCyYb483WWlQ','cQHo-H9AASYwOg','rAH3wSjx2kymbw','aQG3GaDaMaLVVA','3QEEe4iqSDAetQ','nQGkS__SGYPWyA','2gG0dr7EIeS9aw'}.isdisjoint(self.byid))
 def test_print_and_provenance_holds(self):self.assertTrue({'VAE3AsfK8q8M6A','UwEazE_oCEFJQA'}.isdisjoint(self.byid))
 def test_no_empty_inventory_matching(self):
  comps=m.load(a.COMPARISONS)['records'];self.assertTrue(all(not c['inventory_hits'] for c in comps))
 def test_all137_captures_accounted(self):
  held=m.load(a.RUN/'gac-followup-queue-002.json.gz')['rows'];self.assertEqual(len(self.records)+len(held),137);self.assertEqual(len({x['source_id'] for x in held}),34)
 def test_only_review_records(self):
  for r in self.records:self.assertEqual(a.expected_art(r)['status'],'review');self.assertNotIn('current_location_text',a.expected_art(r))
 def test_hash_mutation_rejected(self):
  with tempfile.TemporaryDirectory(prefix='artline-ngaustralia-test-') as d:
   p=Path(d)/'test';p.write_bytes(b'changed')
   with self.assertRaises(AssertionError):a.checked_reference(dict(path=str(p),sha256='0'*64))
 def test_duplicate_fields_rejected(self):
  x=m.load(m.ROOT/self.records[0]['decision']['source_reference']['path']);p=copy.deepcopy(x['parsed']);p['fields'].append(p['fields'][0])
  with self.assertRaises(AssertionError):w.facts(x,p)
 def test_index_title_conflict_rejected(self):
  x=m.load(m.ROOT/self.records[0]['decision']['source_reference']['path']);x['index']['title']='Different work'
  with self.assertRaises(AssertionError):w.facts(x,x['parsed'])
if __name__=='__main__':unittest.main()
