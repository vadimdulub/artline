"""Offline adversarial evidence and preservation tests; no database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-royal-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);r=a.r;m=a.m
class RoyalReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.initial=m.load(a.RUN/'initial-scope-001.json.gz');cls.src={v['number']:v for v in m.load(a.RUN/'source-context-001.json.gz')['rows']};cls.dec={v['number']:v for v in m.load(a.REVIEW)['decisions']};cls.holds=a.records();cls.before=cls.initial['snapshot'];cls.after=copy.deepcopy(cls.before)
  for v in cls.holds:
   next(x for x in cls.after['artworks'] if x['id']==v['artwork_id'])['current_institution_id']=v['institution_id']
   for h in cls.after['assertions']:
    if h['id'] in v['decision']['supersede_assertion_ids']:h['superseded_by']=v['holding_id']
   cls.after['citations'].append(dict(entity_id=v['artwork_id'],source_id=a.SID,field_name='museum_expansion_holding_reconciliation',source_record_id=v['facts']['source_id'],source_url=v['facts']['source_url'],evidence_note=a.citation_note(v,'proof'),retrieved_at=v['retrieved_at']))
   cls.after['assertions'].append(dict(id=v['holding_id'],artwork_id=v['artwork_id'],source_id=a.SID,claim_type='holding',institution_id=v['institution_id'],context='collection',review_state='accepted',superseded_by=None,source_url=v['facts']['source_url'],evidence_note=a.holding_note(v,'proof'),checked_at=v['retrieved_at']))
 def reject_delta(self,mutate):
  after=copy.deepcopy(self.after);mutate(after)
  with self.assertRaises(AssertionError):a.assert_delta(self.before,after,self.holds,'proof')
 def test_valid_selective_delta(self):a.assert_delta(self.before,self.after,self.holds,'proof')
 def test_unresolved_assertion_cannot_be_superseded(self):
  hid=self.dec[52]['pending_assertion_id'];self.reject_delta(lambda s:next(v for v in s['assertions'] if v['id']==hid).update(superseded_by=self.holds[0]['holding_id']))
 def test_existing_holding_cannot_be_removed(self):
  aid=next(v['id'] for v in self.before['artworks'] if v['current_institution_id']);self.reject_delta(lambda s:next(v for v in s['artworks'] if v['id']==aid).update(current_institution_id=None))
 def test_legacy_date_cannot_be_rewritten(self):
  aid=self.dec[39]['existing_artwork_id'];self.reject_delta(lambda s:next(v for v in s['artworks'] if v['id']==aid).update(date_precision='range'))
 def test_status_cannot_be_published(self):
  aid=self.holds[0]['artwork_id'];self.reject_delta(lambda s:next(v for v in s['artworks'] if v['id']==aid).update(status='published'))
 def test_image_cannot_be_replaced(self):
  aid=self.holds[0]['artwork_id'];self.reject_delta(lambda s:next(v for v in s['artworks'] if v['id']==aid).update(primary_media_id='11111111-1111-1111-1111-111111111111'))
 def test_artist_cannot_be_reassigned(self):self.reject_delta(lambda s:s['artists'][0].update(artist_id='11111111-1111-1111-1111-111111111111'))
 def test_no_display_claim(self):self.reject_delta(lambda s:next(v for v in s['assertions'] if v['source_id']==a.SID).update(display_state='on_view'))
 def test_unknown_dates_remain_unknown(self):
  rows=[v for v in self.holds if v['facts']['date_precision']=='unknown'];self.assertEqual({v['decision']['number'] for v in rows},{15,69,72});self.assertTrue(all(v['facts']['first'] is None and v['facts']['last'] is None for v in rows))
 def test_rcin_normalization_does_not_merge_arbitrary_punctuation(self):
  self.assertEqual(r.f.rcin('RCIN 402411'),'402411');self.assertEqual(r.f.rcin('402411'),'402411');self.assertIsNone(r.f.rcin('402/411'));self.assertIsNone(r.f.rcin('402411a'))
 def test_wrong_inventory_rejected(self):
  row=copy.deepcopy(self.src[2]);row['entity']['claims']['P217'][0]['mainsnak']['datavalue']['value']='RCIN 999999'
  with self.assertRaises(AssertionError):r.f.facts(row,self.initial)
 def test_wrong_inventory_collection_rejected(self):
  row=copy.deepcopy(self.src[2]);row['entity']['claims']['P217'][0]['qualifiers']['P195'][0]['datavalue']['value']['id']='Q41661713'
  with self.assertRaises(AssertionError):r.f.facts(row,self.initial)
 def test_native_id_disagreement_requires_review(self):
  row=copy.deepcopy(self.src[2]);row['entity']['claims']['P11057'][0]['mainsnak']['datavalue']['value']='999999';self.assertIn('native_id_inventory_conflict',r.f.facts(row,self.initial)['issues'])
 def test_modern_namesake_creators_stay_held(self):
  for n in [10,25,52,66,89]:self.assertEqual(self.dec[n]['state'],'editorial_hold')
 def test_cleveley_father_son_conflict_stays_held(self):self.assertEqual(self.dec[59]['state'],'editorial_hold');self.assertIn('father/son',self.dec[59]['hold_reason'])
 def test_uncertain_physical_versions_stay_held(self):
  for n in [56,57,76]:self.assertEqual(self.dec[n]['state'],'editorial_hold')
 def test_walters_replica_explicitly_distinguished(self):
  self.assertEqual(self.dec[9]['state'],'approved_existing_holding');self.assertIn('replica',self.dec[9]['basis']);self.assertIn('telescope',self.dec[9]['basis']);self.assertIn('112.5x89.4',self.dec[9]['basis'])
 def test_pendants_are_separate_objects(self):
  rows=[self.dec[n] for n in [27,39]];self.assertEqual({v['facts']['rcin'] for v in rows},{'421665','421666'});self.assertTrue(all(v['state']=='approved_existing_holding' for v in rows));self.assertNotEqual(rows[0]['existing_artwork_id'],rows[1]['existing_artwork_id'])
 def test_derivatives_preserve_explicit_version_evidence(self):
  for n in [44,45]:self.assertEqual(self.dec[n]['state'],'approved_existing_holding');self.assertTrue(self.dec[n]['facts']['source_related_statements']);self.assertIn('derivative',self.dec[n]['basis'])
 def test_persimmon_same_title_different_recorded_artists(self):
  self.assertEqual(self.dec[80]['facts']['creator_label'],'Adrian Jones');self.assertEqual(self.dec[88]['facts']['creator_label'],'Edwin Douglas');self.assertNotEqual(self.dec[80]['facts']['rcin'],self.dec[88]['facts']['rcin'])
 def test_unlinked_creator_labels_not_new_artist_links(self):
  for n in [16,22,24,31,90]:self.assertEqual(self.dec[n]['facts']['artist_links'],[]);self.assertEqual(self.dec[n]['state'],'approved_existing_holding')
 def test_ineligible_creation_is_not_accepted_by_parser(self):
  row=copy.deepcopy(self.src[2]);v=row['entity']['claims']['P571'][0];v.pop('qualifiers',None);v['mainsnak']['datavalue']['value']['time']='+1971-00-00T00:00:00Z';self.assertIn('creation_qualifier_requires_review',r.f.facts(row,self.initial)['issues'])
 def test_source_age_and_secondary_evidence_remain_explicit(self):
  for v in self.holds:self.assertEqual(v['retrieved_at'],self.src[v['decision']['number']]['pending_assertion']['checked_at']);self.assertIn('correlated secondary evidence',v['decision']['limitation']);self.assertIn('no freshly fetched',v['decision']['limitation'])
if __name__=='__main__':unittest.main()
