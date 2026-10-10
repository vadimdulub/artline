"""Offline source and preservation guards; no database or inserted fixtures."""
import copy,importlib.util,json,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-dulwich-target-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class DulwichTarget(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rs,cls.hs=a.records();cls.byinv={r['facts']['inventory']:r for r in cls.rs};cls.ds=a.decisions()
 def test_selected_physical_objects_are_unique_and_disjoint_from_first_batch(self):
  old=a.prior.records();self.assertEqual(len(self.rs),70);self.assertTrue({r['facts']['inventory'] for r in old}.isdisjoint(self.byinv));self.assertEqual(set(r['facts']['inventory'] for r in self.hs),{'DPG258','DPG632'})
 def test_unresolved_close_physical_counterparts_remain_held(self):
  for inv in ['DPG093','DPG295','DPG329','DPG247','DPG485','DPG471','DPG210','DPG184']:
   self.assertEqual(self.ds[inv]['state'],'editorial_hold');self.assertNotIn(inv,self.byinv)
 def test_releases_preserve_earlier_decisions_and_counterpart_evidence(self):
  releases=a.m.load(a.RUN/'target-reconsidered-001.json.gz')['decisions'];self.assertEqual(len(releases),7)
  for d in releases:
   earlier=a.m.load(a.checked_reference(d['previous_decision_reference']));old=next(x for x in earlier['decisions'] if x['inventory']==d['inventory']);self.assertEqual(old['state'],'editorial_hold');self.assertGreater(len(d['followup_evidence']),10)
 def test_paper_on_canvas_does_not_invent_painting_technique(self):
  v=a.expected_art(self.byinv['DPG380']);self.assertEqual(v['work_type'],'unknown');self.assertEqual(v['medium_text'],'Paper on canvas');self.assertIn('Girolamo Bedoli',v['unlinked_creator_label'])
 def test_artist_header_typo_is_explicit_detail_override(self):
  r=self.byinv['DPG643'];self.assertEqual(r['facts']['creator_label'],'Friedrich Drck');self.assertEqual(a.expected_art(r)['unlinked_creator_label'],'Friedrich Dürck');note=json.loads(a.citation_note(r,'offline'));self.assertIn('source_heading',note['source_record']['creator_override'])
 def test_copy_date_and_studio_attributions_are_preserved(self):
  self.assertEqual(self.byinv['DPG630']['facts']['date_display'],'19th Century');self.assertIn('Workshop',self.byinv['DPG212']['facts']['creator_label']);self.assertIn('Studio',self.byinv['DPG081']['facts']['creator_label'])
 def test_before_date_keeps_unknown_lower_bound(self):
  r=self.byinv['DPG641'];self.assertIsNone(r['facts']['first']);self.assertEqual(r['facts']['last'],1934);self.assertEqual(r['facts']['date_precision'],'before')
 def expected_delta(self):
  before=copy.deepcopy(a.m.load(a.RUN/'existing-identity-followup-001.json.gz')['snapshot']);after=copy.deepcopy(before)
  for art in after['artworks']:art['current_institution_id']=a.IID;art['updated_at']='offline-verification'
  for r in self.hs:
   v=r['facts'];after['citations'].append(dict(entity_id=r['artwork_id'],source_id=a.SID,source_record_id=v['source_id'],source_url=v['source_url'],field_name='museum_expansion_holding_reconciliation',evidence_note=a.citation_note(r,'offline')))
   for h in after['assertions']:
    if h['artwork_id']==r['artwork_id']:h['superseded_by']=r['holding_id']
   after['assertions'].append(dict(id=r['holding_id'],artwork_id=r['artwork_id'],source_id=a.SID,claim_type='holding',institution_id=a.IID,context='collection',review_state='accepted',superseded_by=None,source_url=v['source_url'],evidence_note=a.holding_note(r,'offline')))
  return before,after
 def test_existing_holding_delta_accepts_only_intended_link_changes(self):
  before,after=self.expected_delta();a.assert_delta(before,after,self.hs,'offline')
 def test_existing_exact_piero_date_cannot_be_rewritten_to_circa(self):
  before,after=self.expected_delta();p=next(r for r in after['artworks'] if r['id']==a.HOLDINGS['DPG258']);self.assertEqual(p['date_precision'],'exact');p['date_precision']='circa'
  with self.assertRaises(AssertionError):a.assert_delta(before,after,self.hs,'offline')
 def test_old_image_and_painter_links_cannot_be_changed(self):
  for field in ['artists','media','identifiers','citations']:
   before,after=self.expected_delta();self.assertTrue(after[field]);after[field].pop(0)
   with self.subTest(field=field),self.assertRaises(AssertionError):a.assert_delta(before,after,self.hs,'offline')
 def test_accepted_holding_must_not_acquire_display_state(self):
  before,after=self.expected_delta();next(x for x in after['assertions'] if x['source_id']==a.SID)['display_state']='on_view'
  with self.assertRaises(AssertionError):a.assert_delta(before,after,self.hs,'offline')
 def test_pending_brodie_is_superseded_without_changing_old_claim(self):
  before,after=self.expected_delta();old=next(x for x in after['assertions'] if x['source_id']!=a.SID);self.assertEqual(old['review_state'],'review');old['review_state']='accepted'
  with self.assertRaises(AssertionError):a.assert_delta(before,after,self.hs,'offline')

if __name__=='__main__':unittest.main()
