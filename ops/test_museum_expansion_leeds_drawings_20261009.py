"""Offline physical-object/date/attribution and transactional preservation checks."""
import copy,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-leeds-drawings-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);r=a.r;m=a.m
class LeedsDrawings(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ds={v['number']:v for v in r.build()};cls.raw={v['number']:v for v in r.source_rows()};cls.identity=m.load(a.RUN/'identity-002.json.gz')
 def test_uncertain_whole_object_dates_held(self):
  self.assertEqual({n for n,d in self.ds.items() if d['state']=='editorial_hold'},{16,62})
  for n in [16,62]:self.assertEqual(self.ds[n]['physical_object_count'],0);self.assertIsNotNone(self.ds[n]['hold_reason'])
 def test_inscription_not_made_exact(self):
  f=self.ds[19]['facts'];self.assertEqual(f['date_precision'],'circa');self.assertIn('unverified',f['date_display']);self.assertEqual(f['original_date_fields']['date_precision'],'exact');self.assertEqual(f['source_fields']['Date'],'1823')
 def test_model_and_print_dates_not_creation(self):
  for n,y in [(9,1828),(21,1815),(50,1833),(97,1808),(103,1820)]:self.assertEqual(self.ds[n]['facts']['first'],y)
 def test_watermark_not_creation(self):
  for n,y in [(24,1831),(85,1831)]:self.assertEqual(self.ds[n]['facts']['first'],y)
 def test_broad_source_range_retained(self):
  f=self.ds[26]['facts'];self.assertEqual((f['first'],f['last'],f['date_precision']),(1800,1842,'range'))
 def test_separate_mounted_papers_count_separately(self):
  ds=[self.ds[n] for n in range(75,81)];self.assertEqual(len({d['facts']['inventory'] for d in ds}),6);self.assertTrue(all(d['physical_object_count']==1 for d in ds));self.assertEqual([b['numbers'] for b in self.identity['within_batch'] if b['kind']=='mounted_group_inventory'],[list(range(75,81))])
 def test_multiple_sketches_one_sheet(self):
  for n in [22,35,38,49,58,69,71,77,82,104]:self.assertEqual(self.ds[n]['physical_object_count'],1)
 def test_former_shared_titles_not_duplicates(self):
  for x,y in [(7,43),(11,66),(75,80),(19,41)]:self.assertNotEqual(self.ds[x]['facts']['inventory'],self.ds[y]['facts']['inventory']);self.assertNotEqual(self.ds[x]['facts']['title'],self.ds[y]['facts']['title'])
 def test_ambiguous_two_makers_not_joint_authorship(self):
  self.assertIn(' or ',self.ds[78]['facts']['creator_label']);self.assertIn('uncertain',self.ds[78]['facts']['creator_label']);self.assertIn('Possibly',self.ds[102]['facts']['creator_label'])
 def test_family_association_not_joint_authorship(self):
  for n in [27,29,82,85]:self.assertTrue(any(t in self.ds[n]['facts']['creator_label'] for t in ['school','associated']))
 def test_doubtful_and_studio_attribution_retained(self):
  self.assertIn('doubtful',self.ds[91]['facts']['creator_label']);self.assertIn('Studio',self.ds[99]['facts']['creator_label']);self.assertIn('Possibly',self.ds[96]['facts']['creator_label']);self.assertNotIn('Rubens',self.ds[91]['facts']['creator_label'])
 def test_possible_after_not_definite(self):
  for n in [8,19,41,71,86]:self.assertIn('possibly after',self.ds[n]['facts']['creator_label'])
 def test_explicit_after_relationship_retained(self):
  for n in [26,33,51,97]:self.assertIn(', after ',self.ds[n]['facts']['creator_label'])
 def test_artist_lifespan_not_cutoff(self):
  f=self.ds[37]['facts'];self.assertEqual(f['first'],1870);self.assertIn('John Joseph',f['creator_label']);self.assertEqual(self.ds[37]['state'],'approved_review_only_addition')
 def test_unverified_reverse_not_claimed_visual_confirmation(self):
  for n in [12,53]:self.assertIn('historically',self.ds[n]['version_note']);self.assertIn('not',self.ds[n]['version_note'])
 def test_blank_credit_needs_explicit_gallery_provenance(self):
  for n in [2,3]:self.assertFalse(self.ds[n]['facts']['source_fields']['Credit Line']);self.assertIn('Leeds',self.ds[n]['facts']['provenance'])
 def test_unknown_dimensions_not_invented(self):self.assertIsNone(self.ds[1]['facts']['dimensions_text'])
 def test_supported_schema_classification(self):
  for d in self.ds.values():self.assertIn(d['facts']['work_type'],['watercolor','drawing']);self.assertIsNone(d['facts']['object_form'])
 def test_bad_raw_hash_rejected(self):
  cap=copy.deepcopy(self.raw[1]['capture']);cap['receipt']['sha256']='0'*64
  with self.assertRaises(AssertionError):r.verified_raw(cap)
 def test_invalid_inventory_and_cutoff_rejected(self):
  for edit in ['inventory','date']:
   rows=copy.deepcopy(list(self.raw.values()))
   if edit=='inventory':rows[0]['parsed']['fields']['Reference']='OTHER.1'
   else:rows[0]['date'][1]=1971
   with self.assertRaises(AssertionError):r.validate_sources(rows)
 def test_numeric_source_namespace_collision_not_match(self):
  self.assertTrue(any(c['other_source_numeric_id_collisions'] for c in self.identity['comparisons']));self.assertFalse(any(c['source_hits'] for c in self.identity['comparisons']));state=copy.deepcopy(self.identity['state']);row=self.identity['rows'][0];state['native_id_hits'].append(dict(entity_id='example',scheme='cotmania-object',external_id=row['source_id'],canonical_url=row['facts']['source_url']));self.assertTrue(r.i.comparisons([row],state)[0]['source_hits'])
 def test_parent_inventory_candidate_detected(self):
  state=copy.deepcopy(self.identity['state']);row=self.identity['rows'][74];art=copy.deepcopy(state['artworks'][0]);art.update(id='parent-example',accession_number='LEEAG.1949.0009.0203',title='Unrelated words',alternate_title=None);state['artworks'].append(art);hits=r.i.comparisons([row],state)[0]['hits'];self.assertIn('parent_or_sibling_inventory',next(h for h in hits if h['id']=='parent-example')['hit_types'])
 def test_existing_metadata_and_evidence_cannot_change(self):
  before=dict(artworks=[dict(id='one',title='Keep',status='review',current_institution_id=a.IID,primary_media_id='image',date_precision='unknown')],artists=[],media=[],media_assets=[],identifiers=[],museums=[],citations=[dict(source_id='legacy',evidence_note='keep')],assertions=[]);a.assert_delta(before,copy.deepcopy(before),[],'test')
  for field in ['title','status','current_institution_id','primary_media_id','date_precision']:
   after=copy.deepcopy(before);after['artworks'][0][field]='changed'
   with self.assertRaises(AssertionError):a.assert_delta(before,after,[],'test')
  after=copy.deepcopy(before);after['citations']=[]
  with self.assertRaises(AssertionError):a.assert_delta(before,after,[],'test')
 def test_review_status_and_selected_scope(self):
  news,holds=a.records();self.assertEqual((len(news),len(holds)),(102,0));self.assertFalse({self.ds[n]['source_id'] for n in [16,62]}&{v['facts']['source_id'] for v in news})
  for v in news:
   art=a.expected_art(v);self.assertEqual(art['status'],'review');self.assertNotIn('published_at',art);self.assertNotIn('primary_media_id',art);self.assertTrue(100<=art['creation_year_start']<=art['creation_year_end']<=1970)
if __name__=='__main__':unittest.main()
