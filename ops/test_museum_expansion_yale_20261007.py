#!/usr/bin/env python3
"""Offline checks for real retained source evidence; no database fixtures."""
import copy,importlib.util,unittest,tempfile
from pathlib import Path
s=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-yale-facts-20261007.py'));w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
class Dates(unittest.TestCase):
 def test_question_year_retains_uncertainty(self):self.assertEqual(w.creation('1472(?)')['date_precision'],'circa')
 def test_question_cutoff_held(self):self.assertIsNotNone(w.creation('1970(?)')['date_issue'])
 def test_short_range(self):self.assertEqual(w.creation('ca. 1718–25')['last'],1725)
 def test_undated_not_inferred(self):self.assertIsNotNone(w.creation('n.d.')['date_issue'])
 def test_missing_not_inferred(self):self.assertIsNotNone(w.creation(None)['date_issue'])
 def test_biography_not_creation(self):self.assertIsNotNone(w.creation('(French, 1763–1843)')['date_issue'])
 def test_qualified_century_envelope(self):
  x=w.creation('early to mid-17th century');self.assertEqual((x['first'],x['last'],x['date_precision']),(1601,1700,'century'))
 def test_crossing_century_held(self):self.assertIsNotNone(w.creation('19th–20th century')['date_issue'])
 def test_post_cutoff_held(self):self.assertIsNotNone(w.creation('1994–96')['date_issue'])
 def test_before_unknown_lower_bound(self):self.assertIsNone(w.creation('before 1900')['first'])
class Source(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows={}
  for path in (w.RUN/'objects-001').glob('*.json.gz'):
   x,p=w.checked_record(path);f=w.facts(x,p);cls.rows[f['native_object_id']]=(x,p,f)
 def test_original_bytes_and_index_chains(self):self.assertGreaterEqual(len(self.rows),150)
 def test_native_and_inventory_differ(self):
  f=self.rows['48268'][2];self.assertEqual(f['inventory'],'1947.184');self.assertEqual(f['native_object_id'],'48268')
 def test_follower_qualification_retained(self):
  f=self.rows['48268'][2];self.assertEqual(f['creator_label'],'Artist, follower of: Pieter Huys');self.assertTrue(f['creator_fields'][0]['influenced_by'])
 def test_follower_candidate_supported(self):
  _,p,f=self.rows['48268'];self.assertEqual(w.source_holds(f,p),[])
 def test_multiple_contributors_kept(self):
  f=self.rows['44789'][2];self.assertEqual(f['creator_label'],'Antonio Francesco Peruzzini; Artist, follower of: Alessandro Magnasco')
 def test_unknown_creator_stays_unknown(self):self.assertIsNone(self.rows['54470'][2]['creator_label'])
 def test_unknown_creator_not_excluded(self):
  _,p,f=self.rows['54470'];self.assertEqual(w.source_holds(f,p),[])
 def test_former_attribution_not_current(self):
  f=self.rows['15568'][2];self.assertEqual(f['creator_label'],'Andrea di Cione (called Orcagna)');self.assertIn('Artist, formerly attributed to: Bernardo Daddi',f['identity_creator_labels'])
 def test_former_only_creator_unknown(self):self.assertIsNone(self.rows['39372'][2]['creator_label'])
 def test_machine_only_date_not_projected(self):
  f=self.rows['63604'][2];self.assertIsNone(f['date_display']);self.assertIsNone(f['first']);self.assertIn('1774',f['production_timespan']['begin_of_the_begin'])
 def test_loan_credit_overrides_owner_field(self):
  _,p,f=self.rows['63604'];self.assertEqual(f['source_owner'][0]['id'],w.GALLERY);self.assertTrue(any('loan/ownership' in t for t in w.source_holds(f,p)))
 def test_historical_accessions_not_silently_selected(self):
  f=self.rows['64423'][2];self.assertIsNone(f['inventory']);self.assertEqual(set(f['source_inventories']),{'2020.37.24','ILE1981.22'})
 def test_historical_accessions_held(self):
  _,p,f=self.rows['64263'];self.assertTrue(any('accession' in t for t in w.source_holds(f,p)))
 def test_foreign_owner_rejected(self):
  _,p,f=self.rows['48268'];f=copy.deepcopy(f);f['source_owner'][0]['id']='https://example.org/other';self.assertTrue(any('owner' in t for t in w.source_holds(f,p)))
 def test_wrong_yale_department_rejected(self):
  _,p,f=self.rows['48268'];f=copy.deepcopy(f);f['source_collection'][0]['_label']='Yale Center for British Art';self.assertTrue(any('scope' in t for t in w.source_holds(f,p)))
 def test_creation_machine_conflict_held(self):
  x,p,_=self.rows['48268'];p=copy.deepcopy(p);p['produced_by']['timespan']['end_of_the_end']='1980-12-31T00:00:00Z';self.assertIsNotNone(w.facts(x,p)['date_issue'])
 def test_missing_credit_held(self):
  _,p,f=self.rows['48268'];f=copy.deepcopy(f);f['credit_line']=None;self.assertIn('No collection credit',w.source_holds(f,p))
 def test_wrong_object_class_held(self):
  _,p,f=self.rows['48268'];p=copy.deepcopy(p);p['type']='VisualItem';self.assertIn('Outside selected physical paintings',w.source_holds(f,p))
 def test_date_labels_literal(self):self.assertEqual(self.rows['15568'][2]['date_display'],'1342(?)')
 def test_lifetime_parentheses_preserve_call_name(self):self.assertEqual(w.creator_label('Artist: Andrea di Cione (called Orcagna) (Florence, active by 1343–died 1368)'),'Andrea di Cione (called Orcagna)')
class Selection(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-yale-apply-20261007.py'));cls.a=importlib.util.module_from_spec(s);s.loader.exec_module(cls.a)
  cls.records=cls.a.records();cls.byid={r['facts']['native_object_id']:r for r in cls.records};cls.queue=w.m.load(w.RUN/'native-followup-queue-001.json.gz')
 def test99_validated_chains(self):self.assertEqual(len(self.records),99)
 def test240_objects_accounted(self):self.assertEqual(len(self.records)+len(self.queue['rows']),240)
 def test117_source24_editorial_holds(self):self.assertEqual(self.queue['counts'],dict(source_hold=117,editorial_hold=24))
 def test_native_ids_and_accessions_unique(self):self.assertEqual(len(self.byid),99);self.assertEqual(len({r['facts']['inventory'] for r in self.records}),99)
 def test_three_priority_traditions_supported(self):self.assertTrue({'49021','51376','254'}.issubset(self.byid))
 def test_greek_creator_remains_qualified_unknown(self):self.assertEqual(self.byid['51376']['facts']['creator_label'],'Unknown, Greek, 18th century')
 def test_russian_multipart_icon_counts_once(self):self.assertEqual(self.byid['49021']['facts']['inventory'],'1951.19.3')
 def test_unknown_maker_not_invented(self):self.assertIsNone(self.a.expected_art(self.byid['165655'])['unlinked_creator_label'])
 def test_copy_is_not_original_caravaggio(self):self.assertIn('copy after',self.byid['103786']['facts']['creator_label'])
 def test_ycba_credit_excluded(self):self.assertNotIn('200752',self.byid)
 def test_known_record_and_source_date_discrepancies_excluded(self):self.assertTrue({'160','196','195','2460'}.isdisjoint(self.byid))
 def test_source_lifetimes_are_not_date_projection(self):self.assertNotIn('2460',self.byid)
 def test_restitution_then_gift_preserved(self):self.assertIn('restituted',self.byid['110696']['facts']['provenance_text']);self.assertIn('2007',self.byid['110696']['facts']['provenance_text'])
 def test_no_publication_image_display_or_artist_projection(self):
  for r in self.records:
   a=self.a.expected_art(r);self.assertEqual(a['status'],'review');self.assertNotIn('primary_media_id',a);self.assertNotIn('current_location_text',a);self.assertNotIn('artist_id',a)
 def test_hash_tamper_rejected(self):
  with tempfile.TemporaryDirectory(prefix='artline-yale-proof-') as tmp:
   p=Path(tmp)/'evidence';p.write_bytes(b'changed')
   with self.assertRaises(AssertionError):self.a.checked_reference(dict(path=str(p),sha256='0'*64))
if __name__=='__main__':unittest.main()
