"""Offline adversarial review and mutation checks; no database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-britain-nine-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);r=a.r;m=a.m
class BritainNineReviewTests(unittest.TestCase):
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
 def art(self,s,n):return next(v for v in s['artworks'] if v['id']==self.dec[n]['existing_artwork_id'])
 def test_valid_selected_holding_delta(self):a.assert_delta(self.before,self.after,self.holds,'proof')
 def test_unresolved_assertion_cannot_be_superseded(self):
  hid=self.dec[122]['pending_assertion_id'];self.reject_delta(lambda s:next(v for v in s['assertions'] if v['id']==hid).update(superseded_by=self.holds[0]['holding_id']))
 def test_existing_holding_cannot_be_removed(self):
  aid=next(v['id'] for v in self.before['artworks'] if v['current_institution_id']);self.reject_delta(lambda s:next(v for v in s['artworks'] if v['id']==aid).update(current_institution_id=None))
 def test_unknown_date_cannot_be_filled(self):self.reject_delta(lambda s:self.art(s,27).update(creation_year_start=1920,date_precision='exact'))
 def test_legacy_bad_date_not_silently_fixed(self):self.assertEqual(self.dec[44]['facts']['first'],1808);self.reject_delta(lambda s:self.art(s,44).update(creation_year_start=1908,creation_year_end=1908))
 def test_cannot_newly_publish(self):self.reject_delta(lambda s:self.art(s,19).update(status='published'))
 def test_existing_publication_preserved(self):
  self.assertEqual(self.art(self.before,48)['status'],'published');self.assertIsNotNone(self.art(self.before,48)['published_at']);self.reject_delta(lambda s:self.art(s,48).update(status='review',published_at=None))
 def test_image_cannot_be_replaced(self):self.reject_delta(lambda s:self.art(s,19).update(primary_media_id='11111111-1111-1111-1111-111111111111'))
 def test_artist_cannot_be_reassigned(self):self.reject_delta(lambda s:s['artists'][0].update(artist_id='11111111-1111-1111-1111-111111111111'))
 def test_no_display_claim(self):self.reject_delta(lambda s:next(v for v in s['assertions'] if v['source_id']==a.SID).update(display_state='on_view'))
 def test_wrong_target_museum_rejected(self):self.reject_delta(lambda s:self.art(s,19).update(current_institution_id=a.IIDS[0]))
 def test_source_evidence_cannot_be_replaced(self):self.reject_delta(lambda s:next(v for v in s['citations'] if v['source_id']==a.SID).update(source_url='https://example.invalid'))
 def test_unknowns_not_counted_eligible(self):
  rows=[v for v in self.holds if v['facts']['date_precision']=='unknown'];self.assertEqual(len(rows),75);self.assertTrue(all(v['facts']['first'] is None and v['facts']['last'] is None for v in rows));self.assertEqual(sum(v['facts']['date_precision']!='unknown' for v in self.holds),154)
 def test_inventory_namespace(self):
  self.assertEqual(r.f.inventory('2005.2.4',a.IIDS[0]),'2005.2.4');self.assertEqual(r.f.inventory('PCF58 P2',a.IIDS[0]),'PCF58 P2');self.assertIsNone(r.f.inventory('YORAG : 382',a.IIDS[2]));self.assertIsNone(r.f.inventory('PRSMG : P1878.1',a.IIDS[1]))
 def test_wrong_inventory_rejected(self):
  row=copy.deepcopy(self.src[19]);row['entity']['claims']['P217'][0]['mainsnak']['datavalue']['value']='YORAG : 999999'
  with self.assertRaises(AssertionError):r.f.facts(row,self.initial)
 def test_wrong_inventory_collection_rejected(self):
  row=copy.deepcopy(self.src[19]);row['entity']['claims']['P217'][0]['qualifiers']['P195'][0]['datavalue']['value']['id']='Q7205781'
  with self.assertRaises(AssertionError):r.f.facts(row,self.initial)
 def test_wrong_collection_rejected(self):
  row=copy.deepcopy(self.src[19]);row['entity']['claims']['P195'][0]['mainsnak']['datavalue']['value']['id']='Q7205781'
  with self.assertRaises(AssertionError):r.f.facts(row,self.initial)
 def test_known_post1970_dates_stay_held(self):
  for n,year in [(20,'1991'),(67,'1986'),(199,'1998')]:self.assertEqual(self.dec[n]['state'],'editorial_hold');self.assertIn(year,self.dec[n]['hold_reason']);self.assertEqual(self.dec[n]['facts']['date_precision'],'unknown')
 def test_duplicate_objects_stay_held(self):
  for n in [51,122,132,241]:self.assertEqual(self.dec[n]['state'],'editorial_hold');self.assertEqual(self.dec[n]['supersede_assertion_ids'],[])
 def test_qualified_maker_conflicts_stay_held(self):
  for n in [125,192,233]:self.assertEqual(self.dec[n]['state'],'editorial_hold')
 def test_pendant_not_duplicate(self):
  self.assertEqual(self.dec[19]['state'],'approved_existing_holding');self.assertIn('Queen Charlotte',self.dec[19]['metadata_review_note'])
 def test_study_not_finished_canvas(self):
  self.assertIn('Study',self.dec[48]['facts']['title']);self.assertIn('103.8x82.5',self.dec[48]['metadata_review_note']);self.assertEqual(self.dec[48]['state'],'approved_existing_holding')
 def test_different_supports_and_native_title_conflict(self):
  self.assertEqual(self.dec[218]['state'],'approved_existing_holding');self.assertEqual(self.dec[193]['state'],'editorial_hold');self.assertIn('Acaster Malbis',self.dec[193]['hold_reason'])
 def test_creator_authorities_do_not_create_links(self):
  for n in [73,92,142,171,236]:self.assertEqual(self.dec[n]['facts']['artist_links'],[]);self.assertEqual(self.dec[n]['state'],'approved_existing_holding')
 def test_primary_object_support_does_not_resolve_collins_biography(self):
  self.assertIsNotNone(self.dec[236]['native_object_evidence']);self.assertIn('1867',self.dec[236]['metadata_review_note']);self.assertIn('1851',self.dec[236]['metadata_review_note'])
 def test_accession_year_not_creation(self):
  self.assertEqual(self.dec[209]['state'],'approved_existing_holding');self.assertEqual(self.dec[209]['facts']['date_precision'],'unknown');self.assertIn('2021',self.dec[209]['facts']['inventory'])
 def test_after_storm_is_subject(self):self.assertEqual(self.dec[174]['state'],'approved_existing_holding');self.assertIn('weather',self.dec[174]['metadata_review_note'])
 def test_ineligible_creation_requires_review(self):
  row=copy.deepcopy(self.src[19]);v=row['entity']['claims']['P571'][0];v.pop('qualifiers',None);v['mainsnak']['datavalue']['value']['time']='+1971-00-00T00:00:00Z';self.assertIn('creation_qualifier_requires_review',r.f.facts(row,self.initial)['issues'])
 def test_ended_collection_requires_review(self):
  row=copy.deepcopy(self.src[19]);v=row['entity']['claims']['P195'][0];v.setdefault('qualifiers',{})['P582']=[{'snaktype':'value','datavalue':{'value':{'time':'+2000-00-00T00:00:00Z'}}}];self.assertIn('collection_qualification_requires_review',r.f.facts(row,self.initial)['issues'])
 def test_historical_sources_not_relabelled_fresh(self):
  for v in self.holds:self.assertEqual(v['retrieved_at'],self.src[v['decision']['number']]['pending_assertion']['checked_at']);self.assertIn('correlated secondary evidence',v['decision']['limitation'])
if __name__=='__main__':unittest.main()
