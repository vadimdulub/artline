"""Offline adversarial evidence and preservation tests; no database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-leeds-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);r=a.r;m=a.m
class LeedsReviewTests(unittest.TestCase):
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
  hid=self.dec[51]['pending_assertion_id'];self.reject_delta(lambda s:next(v for v in s['assertions'] if v['id']==hid).update(superseded_by=self.holds[0]['holding_id']))
 def test_existing_holding_cannot_be_removed(self):
  aid=next(v['id'] for v in self.before['artworks'] if v['current_institution_id']);self.reject_delta(lambda s:next(v for v in s['artworks'] if v['id']==aid).update(current_institution_id=None))
 def test_legacy_date_cannot_be_rewritten(self):
  aid=self.dec[77]['existing_artwork_id'];self.reject_delta(lambda s:next(v for v in s['artworks'] if v['id']==aid).update(date_precision='exact'))
 def test_status_cannot_be_published(self):
  aid=self.holds[0]['artwork_id'];self.reject_delta(lambda s:next(v for v in s['artworks'] if v['id']==aid).update(status='published'))
 def test_image_cannot_be_replaced(self):
  aid=self.holds[0]['artwork_id'];self.reject_delta(lambda s:next(v for v in s['artworks'] if v['id']==aid).update(primary_media_id='11111111-1111-1111-1111-111111111111'))
 def test_artist_cannot_be_reassigned(self):self.reject_delta(lambda s:s['artists'][0].update(artist_id='11111111-1111-1111-1111-111111111111'))
 def test_no_display_claim(self):self.reject_delta(lambda s:next(v for v in s['assertions'] if v['source_id']==a.SID).update(display_state='on_view'))
 def test_unknown_dates_remain_unknown(self):
  rows=[v for v in self.holds if v['facts']['date_precision']=='unknown'];self.assertEqual(len(rows),22);self.assertTrue(all(v['facts']['first'] is None and v['facts']['last'] is None for v in rows))
 def test_inventory_namespace_preserved(self):
  self.assertEqual(r.f.inventory('LEEAG.PA.0009.LACF'),'LEEAG.PA.0009.LACF');self.assertIsNone(r.f.inventory('LEEDM.E.1932.0301.0001'));self.assertNotEqual(r.f.inventory('LEEAG.PA.0009.LACF'),r.f.inventory('LEEAG.PA.10010.LACF'))
 def test_wrong_inventory_rejected(self):
  row=copy.deepcopy(self.src[2]);row['entity']['claims']['P217'][0]['mainsnak']['datavalue']['value']='LEEAG.PA.999999'
  with self.assertRaises(AssertionError):r.f.facts(row,self.initial)
 def test_wrong_inventory_collection_rejected(self):
  row=copy.deepcopy(self.src[2]);row['entity']['claims']['P217'][0]['qualifiers']['P195'][0]['datavalue']['value']['id']='Q69789812'
  with self.assertRaises(AssertionError):r.f.facts(row,self.initial)
 def test_wrong_collection_rejected(self):
  row=copy.deepcopy(self.src[2]);row['entity']['claims']['P195'][0]['mainsnak']['datavalue']['value']['id']='Q2748017'
  with self.assertRaises(AssertionError):r.f.facts(row,self.initial)
 def test_duplicate_collection_statement_counts_once(self):
  self.assertEqual(len(self.dec[25]['facts']['source_collection_statements']),2);self.assertEqual(sum(v['decision']['number']==25 for v in self.holds),1)
 def test_unresolved_compositions_stay_held(self):self.assertEqual({v['number'] for v in self.dec.values() if v['state']=='editorial_hold'},{46,51,57,59})
 def test_study_and_maker_remain_explicit(self):
  self.assertIn('Study',self.dec[19]['facts']['title']);self.assertEqual(self.dec[19]['facts']['creator_label'],'Norman Adams')
 def test_verified_object_labels_stay_unlinked(self):
  for n in [4,41]:self.assertEqual(self.dec[n]['facts']['artist_links'],[]);self.assertEqual(self.dec[n]['state'],'approved_existing_holding')
 def test_ineligible_creation_requires_review(self):
  row=copy.deepcopy(self.src[2]);v=row['entity']['claims']['P571'][0];v.pop('qualifiers',None);v['mainsnak']['datavalue']['value']['time']='+1971-00-00T00:00:00Z';self.assertIn('creation_qualifier_requires_review',r.f.facts(row,self.initial)['issues'])
 def test_ended_collection_qualifier_requires_review(self):
  row=copy.deepcopy(self.src[2]);v=row['entity']['claims']['P195'][0];v.setdefault('qualifiers',{})['P582']=[{'snaktype':'value','datavalue':{'value':{'time':'+2000-00-00T00:00:00Z'}}}];self.assertIn('collection_qualification_requires_review',r.f.facts(row,self.initial)['issues'])
 def test_source_age_not_relabelled_fresh(self):
  for v in self.holds:self.assertEqual(v['retrieved_at'],self.src[v['decision']['number']]['pending_assertion']['checked_at']);self.assertIn('correlated secondary evidence',v['decision']['limitation'])
if __name__=='__main__':unittest.main()
