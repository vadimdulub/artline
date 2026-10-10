"""Offline adversarial checks; no database or network fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-glasgow-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);r=a.r;m=a.m
class GlasgowReviewTests(unittest.TestCase):
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
 def test_branch_assertion_cannot_be_silently_superseded(self):
  hid=self.dec[2]['pending_assertion_id'];self.reject_delta(lambda s:next(v for v in s['assertions'] if v['id']==hid).update(superseded_by=self.holds[0]['holding_id']))
 def test_existing_network_cannot_be_moved(self):
  aid=self.dec[3]['existing_artwork_id'];self.reject_delta(lambda s:next(v for v in s['artworks'] if v['id']==aid).update(current_institution_id=a.IIDS[0]))
 def test_legacy_date_cannot_be_rewritten(self):
  aid=self.dec[204]['existing_artwork_id'];self.reject_delta(lambda s:next(v for v in s['artworks'] if v['id']==aid).update(creation_year_start=1940))
 def test_status_cannot_be_published(self):
  aid=self.holds[0]['artwork_id'];self.reject_delta(lambda s:next(v for v in s['artworks'] if v['id']==aid).update(status='published'))
 def test_image_cannot_be_replaced(self):
  aid=self.holds[0]['artwork_id'];self.reject_delta(lambda s:next(v for v in s['artworks'] if v['id']==aid).update(primary_media_id='11111111-1111-1111-1111-111111111111'))
 def test_no_display_claim(self):self.reject_delta(lambda s:next(v for v in s['assertions'] if v['source_id']==a.SID).update(display_state='on_view'))
 def test_unknown_dates_remain_unknown(self):
  rows=[v for v in self.holds if v['facts']['date_precision']=='unknown'];self.assertEqual(len(rows),12);self.assertTrue(all(v['facts']['first'] is None and v['facts']['last'] is None for v in rows))
 def test_resource_centre_location_does_not_choose_branch(self):
  for v in self.holds:
   if v['decision']['source_institution_id']==a.IIDS[0]:self.assertEqual(v['institution_id'],a.s.NETWORK);self.assertNotIn(v['decision']['pending_assertion_id'],v['decision']['supersede_assertion_ids'])
 def test_loan_does_not_invent_destination(self):
  d=self.dec[112];self.assertEqual(d['native_evidence'][0]['parsed']['fields']['Location'],'Out on Loan');self.assertEqual(d['institution_id'],a.s.NETWORK);self.assertEqual(len(d['supersede_assertion_ids']),1)
 def test_real_qualified_creators_held(self):
  for n in [11,57,227,248]:self.assertEqual(self.dec[n]['state'],'editorial_hold')
 def test_title_words_not_qualified_authorship(self):
  for n in [125,213]:self.assertEqual(self.dec[n]['state'],'preserved_existing_network_holding')
 def test_unresolved_versions_not_double_counted(self):
  for n in [38,71,117,208]:self.assertEqual(self.dec[n]['state'],'editorial_hold')
 def test_distinct_cadell_physical_dimensions_recorded(self):self.assertIn('116.8x101.6',self.dec[9]['basis']);self.assertIn('61x50.8',self.dec[9]['basis'])
 def test_unlinked_creator_labels_not_new_artist_links(self):
  for n in [124,238]:self.assertEqual(self.dec[n]['facts']['artist_links'],[]);self.assertEqual(self.dec[n]['state'],'approved_existing_holding')
 def test_wrong_inventory_rejected(self):
  row=copy.deepcopy(self.src[1]);row['entity']['claims']['P217'][0]['mainsnak']['datavalue']['value']='other-version'
  with self.assertRaises(AssertionError):r.f.facts(row,self.initial)
 def test_wrong_inventory_collection_rejected(self):
  row=copy.deepcopy(self.src[1]);row['entity']['claims']['P217'][0]['qualifiers']['P195'][0]['datavalue']['value']['id']='Q41661713'
  with self.assertRaises(AssertionError):r.f.facts(row,self.initial)
 def test_reference_qualifiers_do_not_change_creation(self):
  row=copy.deepcopy(self.src[217]);original=r.f.facts(row,self.initial);self.assertEqual((original['first'],original['last']),(1895,1895));row['entity']['claims']['P1679'][0]['qualifiers']['P407'][0]['datavalue']['value']['id']='Q150'
  with self.assertRaises(AssertionError):r.f.facts(row,self.initial)
if __name__=='__main__':unittest.main()
