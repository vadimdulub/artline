"""Pure-data regression checks; never connects to or creates a database."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-detroit-final-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class ProtectedDelta(unittest.TestCase):
 def setUp(self):
  self.before=copy.deepcopy(a.m.load(a.RUN/'initial-scope-001.json.gz')['snapshot']);self.before['media_assets']=[dict(id='protected-image',storage_key='existing-real-asset',rights='source-rights')]
  ds=a.m.load(a.REVIEW)['decisions'];self.holds=[]
  for d in ds:
   if d['state']=='approved_existing_holding':
    aid=a.HOLDINGS[d['number']];self.holds.append(dict(artwork_id=aid,holding_id=a.m.uid(a.KEY+'/holding/'+aid),facts=d['facts'],decision=d))
  self.after=copy.deepcopy(self.before)
  for v in self.holds:
   aid=v['artwork_id'];fv=v['facts']
   next(x for x in self.after['artworks'] if x['id']==aid).update(current_institution_id=a.IID,updated_at='changed')
   next(x for x in self.after['assertions'] if x['artwork_id']==aid)['superseded_by']=v['holding_id']
   self.after['citations'].append(dict(entity_id=aid,source_id=a.SID,field_name='museum_expansion_holding_reconciliation',source_record_id=fv['source_id'],source_url=fv['source_url'],evidence_note=a.citation_note(v,'test')))
   self.after['assertions'].append(dict(id=v['holding_id'],artwork_id=aid,source_id=a.SID,claim_type='holding',institution_id=a.IID,context='collection',review_state='accepted',superseded_by=None,source_url=fv['source_url'],evidence_note=a.holding_note(v,'test')))
 def verify(self):a.assert_delta(self.before,self.after,self.holds,'test')
 def test_only_documented_holding_delta_allowed(self):self.verify()
 def test_exact_date_cannot_be_silently_changed_to_native_circa(self):
  next(x for x in self.after['artworks'] if x['id']==self.holds[0]['artwork_id'])['date_precision']='circa'
  with self.assertRaises(AssertionError):self.verify()
 def test_existing_asset_rights_cannot_change(self):
  self.after['media_assets'][0]['rights']='invented-public-domain'
  with self.assertRaises(AssertionError):self.verify()
 def test_publication_cannot_change(self):
  self.after['artworks'][0]['status']='published'
  with self.assertRaises(AssertionError):self.verify()
 def test_old_assertion_evidence_cannot_be_rewritten(self):
  self.after['assertions'][0]['evidence_note']='replacement'
  with self.assertRaises(AssertionError):self.verify()
 def test_display_claim_cannot_be_added(self):
  self.after['assertions'][-1]['display_state']='on_view'
  with self.assertRaises(AssertionError):self.verify()
 def test_old_creator_link_cannot_be_removed(self):
  self.after['artists'].pop()
  with self.assertRaises(AssertionError):self.verify()
 def test_unresolved_reverse_and_lifespan_entries_are_held(self):
  ds={x['number']:x for x in a.m.load(a.REVIEW)['decisions']}
  for n in [2,21,31,33,36,37,117]:self.assertEqual(ds[n]['state'],'editorial_hold')
  self.assertNotIn(5,ds)
if __name__=='__main__':unittest.main()
