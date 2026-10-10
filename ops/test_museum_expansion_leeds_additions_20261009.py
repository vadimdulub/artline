"""Offline evidence and preservation checks; never creates a test database or fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-leeds-additions-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);r=a.r;m=a.m
class LeedsAdditions(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ds={v['number']:v for v in r.build()};cls.raw={v['number']:v for v in r.source_rows()};cls.identity=m.load(a.RUN/'identity-003.json.gz')
 def test_missing_object_cannot_be_accepted(self):self.assertEqual(self.ds[18]['state'],'editorial_hold');self.assertEqual(self.ds[18]['physical_object_count'],0);self.assertIn('missing',self.ds[18]['facts']['source_fields']['Credit Line'])
 def test_dutch_source_print_year_not_creation(self):
  for n in [8,19,22,27]:self.assertIn('1607',self.ds[n]['facts']['title']);self.assertEqual((self.ds[n]['facts']['first'],self.ds[n]['facts']['date_precision']),(1825,'circa'))
 def test_recto_verso_counts_once(self):
  for n in [9,19,22,27,33]:self.assertEqual(self.ds[n]['physical_object_count'],1);self.assertIn('Verso',self.ds[n]['facts']['title'])
 def test_musketeers_shared_alias_not_duplicate(self):
  self.assertNotEqual(self.ds[19]['facts']['inventory'],self.ds[27]['facts']['inventory']);self.assertIn('C Watson',self.ds[19]['facts']['title']);self.assertIn('castle',self.ds[27]['facts']['title']);self.assertTrue(self.identity['within_batch'])
 def test_pupil_reverse_not_definite_cotman(self):
  for n in [19,22,27]:self.assertIn('probably an unidentified pupil (verso)',self.ds[n]['facts']['creator_label']);self.assertEqual(self.ds[n]['facts']['original_creator_label'],'John Sell Cotman')
 def test_cooke_replaces_composite_with_qualification(self):
  v=self.ds[10]['facts'];self.assertIn('Almost certainly Edward William Cooke',v['creator_label']);self.assertIn('Composite',v['original_creator_label']);self.assertEqual(v['first'],1864)
 def test_thirtle_scope_uncertain(self):self.assertIn('authorship of recto and verso unresolved',self.ds[33]['facts']['creator_label']);self.assertIn('Possibly',self.ds[33]['facts']['creator_label'])
 def test_unqualified_table_not_copied_when_essay_rejects(self):
  for n in [36,37,39]:self.assertEqual(self.ds[n]['facts']['source_fields']['Artist'],'John Sell Cotman, British, 1782 - 1842');self.assertNotEqual(self.ds[n]['facts']['creator_label'],'John Sell Cotman')
 def test_norwich_model_date_not_watercolour_date(self):self.assertEqual(self.ds[37]['facts']['first'],1803);self.assertIn('after John Sell Cotman',self.ds[37]['facts']['creator_label'])
 def test_possible_copy_not_definite(self):self.assertNotIn('after John',self.ds[39]['facts']['creator_label']);self.assertIn('possible copy',self.ds[39]['facts']['creator_editorial_basis'])
 def test_artist_lifespan_not_artwork_cutoff(self):self.assertEqual((self.ds[35]['facts']['creator_label'],self.ds[35]['facts']['first']),('John Joseph Cotman',1873));self.assertEqual(self.ds[35]['state'],'approved_review_only_addition')
 def test_associated_person_not_creator(self):
  v=self.ds[44]['facts'];self.assertNotIn('Artist',v['source_fields']);self.assertEqual(v['source_artist_fields'],[]);self.assertTrue(v['creator_label'].startswith('Unidentified pupil'))
 def test_studio_and_after_preserved(self):self.assertTrue(self.ds[41]['facts']['creator_label'].startswith('Studio of'));self.assertIn('After David Cox',self.ds[49]['facts']['creator_label'])
 def test_unknown_dimensions_not_invented(self):self.assertIsNone(self.ds[20]['facts']['dimensions_text']);self.assertIn('114 mm x 267 mm',self.ds[22]['facts']['dimensions_text'])
 def test_bad_raw_hash_rejected(self):
  cap=copy.deepcopy(self.raw[1]['capture']);cap['receipt']['sha256']='0'*64
  with self.assertRaises(AssertionError):r.verified_raw(cap)
 def test_invalid_inventory_and_cutoff_rejected(self):
  for edit in ['inventory','date']:
   rows=copy.deepcopy(list(self.raw.values()))
   if edit=='inventory':rows[0]['parsed']['fields']['Reference']='OTHER.1'
   else:rows[0]['date'][1]=1971
   with self.assertRaises(AssertionError):r.validate_sources(rows)
 def test_other_source_numeric_id_not_exact_match(self):
  comps=r.i.comparisons(self.identity['rows'],self.identity['state']);self.assertTrue(any(c['other_source_numeric_id_collisions'] for c in comps));self.assertFalse(any(c['source_hits'] for c in comps))
  state=copy.deepcopy(self.identity['state']);row=self.identity['rows'][0];state['native_id_hits'].append(dict(entity_id='example',scheme='cotmania-object',external_id=row['source_id'],canonical_url=row['facts']['source_url']));self.assertTrue(r.i.comparisons([row],state)[0]['source_hits'])
 def test_no_existing_metadata_delta_allowed(self):
  before=dict(artworks=[dict(id='one',title='Keep',status='review',current_institution_id=a.IID,primary_media_id='image',date_precision='unknown')],artists=[],media=[],media_assets=[],identifiers=[],museums=[],citations=[],assertions=[])
  a.assert_delta(before,copy.deepcopy(before),[],'test')
  for field in ['title','status','current_institution_id','primary_media_id','date_precision']:
   after=copy.deepcopy(before);after['artworks'][0][field]='changed'
   with self.assertRaises(AssertionError):a.assert_delta(before,after,[],'test')
 def test_old_evidence_not_deleted(self):
  before=dict(artworks=[],artists=[],media=[],media_assets=[],identifiers=[],museums=[],citations=[dict(source_id='legacy',evidence_note='keep')],assertions=[]);after=copy.deepcopy(before);after['citations']=[]
  with self.assertRaises(AssertionError):a.assert_delta(before,after,[],'test')
 def test_review_record_fields_and_disjoint_selection(self):
  news,holds=a.records();self.assertEqual((len(news),len(holds)),(49,0));self.assertNotIn(self.ds[18]['source_id'],{v['facts']['source_id'] for v in news})
  for v in news:
   art=a.expected_art(v);self.assertEqual(art['status'],'review');self.assertNotIn('published_at',art);self.assertNotIn('primary_media_id',art);self.assertTrue(100<=art['creation_year_start']<=art['creation_year_end']<=1970)
if __name__=='__main__':unittest.main()
