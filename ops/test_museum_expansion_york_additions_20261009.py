"""Offline adversarial checks; never create database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-york-additions-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);r=a.r;m=a.m
class YorkAdditions(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ds={d['number']:d for d in r.build()};cls.raw={d['number']:d for d in m.load(a.RUN/'selected-objects-001.json.gz')['rows']};cls.identity=m.load(a.RUN/'identity-001.json.gz')
 def test_conflicting_native_date_is_held(self):
  self.assertEqual(self.ds[162]['state'],'source_fact_hold');self.assertEqual(self.raw[162]['parsed']['fields']['Production date start'],['1903','1913'])
  with self.assertRaises(AssertionError):r.f.facts(self.raw[162])
 def test_likely_existing_wikiart_records_not_duplicated(self):
  for n in [50,190]:self.assertEqual(self.ds[n]['state'],'editorial_hold');self.assertIn('Likely existing WikiArt',self.ds[n]['hold_reason'])
 def test_version_and_cross_attribution_holds(self):
  self.assertEqual({n for n,d in self.ds.items() if d['state']=='editorial_hold'},set(r.HELD)-{162})
  for n in r.HELD:self.assertEqual(self.ds[n]['physical_object_count'],0)
 def test_valid_month_dates(self):
  for n,y in [(180,1943),(181,1933)]:
   f=self.ds[n]['facts'];self.assertEqual((f['first'],f['last']),(y,y));self.assertEqual(f['date_display'],str(y)+'-08')
 def test_invalid_month_dates_rejected(self):
  for v in ['1943-13','1933-00','1933-02-30','1933/08','about 1933']:
   with self.assertRaises(ValueError):r.f.date_value(v)
 def test_subject_year_not_creation(self):
  self.assertEqual(self.ds[141]['facts']['first'],1863);self.assertIn('1739',self.ds[141]['facts']['title']);self.assertEqual(self.ds[140]['facts']['first'],1866)
 def test_broad_native_range_retained(self):
  f=self.ds[28]['facts'];self.assertEqual((f['first'],f['last'],f['date_precision']),(1504,1540,'range'))
 def test_multiple_makers_not_asserted_joint(self):
  for n in [13,16,17,19,29,58,63,72,88,161]:self.assertTrue(self.ds[n]['facts']['creator_label'].startswith('Source attribution unresolved:'))
 def test_follower_and_studio_qualifications(self):
  self.assertIn('follower of',self.ds[24]['facts']['creator_label']);self.assertIn('studio of',self.ds[36]['facts']['creator_label']);self.assertIn('follower of',self.ds[161]['facts']['creator_label'])
 def test_empty_role_cleanup_preserves_original(self):
  f=self.ds[50]['facts'];self.assertIn('()',f['original_creator_label']);self.assertNotIn('()',f['creator_label']);self.assertIn('Thoedore',f['creator_label'])
 def test_sitter_conflicts_explicit(self):
  for n in [112,113]:
   f=self.ds[n]['facts'];self.assertIn('sitter uncertain',f['title']);self.assertIn(f['original_title'],f['titles']);self.assertIn('after Thomas Lawrence',f['title']);self.assertEqual(f['creator_label'],'William Etty')
 def test_after_reynolds_not_original(self):self.assertIn('after Sir Joshua Reynolds',self.ds[114]['facts']['title']);self.assertEqual(self.ds[114]['facts']['creator_label'],'William Etty')
 def test_anonymous_source_records_supported(self):
  for n in [22,23,26,31,33,37,38,43,44,45,46,59,79,85,86,93]:self.assertEqual(self.ds[n]['facts']['creator_label'],'Unidentified artist');self.assertEqual(self.ds[n]['state'],'approved_review_only_addition')
 def test_multiple_panels_one_object(self):
  for n in [23,31,38]:self.assertEqual(self.ds[n]['physical_object_count'],1);self.assertEqual(self.ds[n]['facts']['physical_object_count'],'1')
 def test_separate_roundels_not_whole_altarpiece(self):
  self.assertNotEqual(self.ds[17]['facts']['inventory'],self.ds[18]['facts']['inventory']);self.assertEqual([b['numbers'] for b in self.identity['within_batch'] if b['kind']=='mounted_group_inventory'],[[17,18]])
 def test_recto_verso_count_once(self):
  for n in [128,129,136]:self.assertEqual(self.ds[n]['physical_object_count'],1)
 def test_existing_known_index_records_not_readded(self):
  self.assertTrue(set(self.ds).isdisjoint([9,14,97,126,142,143,147,150,160,163,169,184,186]));self.assertEqual(len(self.ds),177)
 def test_same_titles_distinct_makers_and_objects(self):
  for x,y in [(6,125),(125,128),(100,176),(60,61)]:self.assertNotEqual(self.ds[x]['facts']['creator_label'],self.ds[y]['facts']['creator_label']);self.assertNotEqual(self.ds[x]['facts']['inventory'],self.ds[y]['facts']['inventory'])
 def test_dimensions_labels_not_invented(self):self.assertEqual(self.ds[22]['facts']['dimensions_text'].count('Canvas width'),2);self.assertNotIn('Canvas height',self.ds[22]['facts']['dimensions_text'])
 def test_materials_and_frame_dimensions_preserved(self):
  f=self.ds[57]['facts'];self.assertIn('Canvas height 99.0 cm',f['dimensions_text']);self.assertIn('Frame height',f['dimensions_text']);self.assertIsNone(f['object_form'])
 def test_bad_raw_hash_rejected(self):
  cap=copy.deepcopy(self.raw[1]['capture']);cap['receipt']['sha256']='0'*64
  with self.assertRaises(AssertionError):r.verified_raw(cap)
 def test_bad_source_status_rejected(self):
  cap=copy.deepcopy(self.raw[1]['capture']);cap['receipt']['status']=403
  with self.assertRaises(AssertionError):r.verified_raw(cap)
 def test_tampered_parsed_source_rejected(self):
  row=copy.deepcopy(self.raw[1]);row['parsed']['fields']['Object number']=['OTHER:1']
  with self.assertRaises(AssertionError):r.f.facts(row)
 def test_source_namespace_collision_not_match(self):
  self.assertFalse(any(c['source_hits'] for c in self.identity['comparisons']));state=copy.deepcopy(self.identity['state']);row=self.identity['rows'][0];state['native_id_hits'].append(dict(entity_id='example',scheme='york-museums-object',external_id=row['source_id'],canonical_url=row['facts']['source_url']));self.assertTrue(r.i.comparisons([row],state)[0]['source_hits'])
 def test_unrelated_numeric_namespace_not_match(self):
  state=copy.deepcopy(self.identity['state']);row=self.identity['rows'][0];state['native_id_hits'].append(dict(entity_id='example',scheme='other-museum',external_id=row['facts']['native_id'],canonical_url='https://example.org/object/1'));c=r.i.comparisons([row],state)[0];self.assertFalse(c['source_hits']);self.assertTrue(any(h['entity_id']=='example' for h in c['other_source_numeric_id_collisions']))
 def test_parent_inventory_candidate_detected(self):
  state=copy.deepcopy(self.identity['state']);row=next(r for r in self.identity['rows'] if r['number']==17);art=copy.deepcopy(state['artworks'][0]);art.update(id='parent-example',accession_number='YORAG : 779',title='Unrelated words',alternate_title=None);state['artworks'].append(art);hits=r.i.comparisons([row],state)[0]['hits'];self.assertIn('parent_or_sibling_inventory',next(h for h in hits if h['id']=='parent-example')['hit_types'])
 def test_existing_metadata_and_publication_preserved(self):
  before=dict(artworks=[dict(id='one',title='Keep',status='published',current_institution_id=a.IID,primary_media_id='image',date_precision='unknown')],artists=[],media=[],media_assets=[],identifiers=[],museums=[],citations=[dict(source_id='legacy',evidence_note='keep')],assertions=[]);a.assert_delta(before,copy.deepcopy(before),[],'test')
  for field in ['title','status','current_institution_id','primary_media_id','date_precision']:
   after=copy.deepcopy(before);after['artworks'][0][field]='changed'
   with self.assertRaises(AssertionError):a.assert_delta(before,after,[],'test')
 def test_legacy_evidence_cannot_be_removed(self):
  before=dict(artworks=[],artists=[],media=[],media_assets=[],identifiers=[],museums=[],citations=[dict(source_id='legacy',evidence_note='keep')],assertions=[]);after=copy.deepcopy(before);after['citations']=[]
  with self.assertRaises(AssertionError):a.assert_delta(before,after,[],'test')
 def test_new_nga_access_hold_not_bypassed(self):
  v=m.load(a.RUN/'comparison-native-extra-attempt-001.json');self.assertEqual((v['status'],v['state']),(403,'access_hold'));self.assertEqual(self.ds[25]['state'],'editorial_hold')
 def test_selected_scope_review_and_slug(self):
  news,holds=a.records();self.assertEqual((len(news),len(holds)),(160,0));self.assertFalse({self.ds[n]['source_id'] for n in r.HELD}&{v['facts']['source_id'] for v in news})
  for v in news:
   art=a.expected_art(v);self.assertEqual(art['status'],'review');self.assertNotIn('published_at',art);self.assertNotIn('primary_media_id',art);self.assertNotIn('/',art['slug']);self.assertTrue(100<=art['creation_year_start']<=art['creation_year_end']<=1970)
if __name__=='__main__':unittest.main()
