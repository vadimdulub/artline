"""Offline rejection proofs for the selected production batch; no DB fixtures."""
import copy, importlib.util, unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('publication',Path(__file__).with_name('catalogue-expansion-publish-20261008.py'))
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class PublicationSafety(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.plan=p.m.load(p.PLAN)
 def rejected(self,change):
  plan=copy.deepcopy(self.plan);change(plan)
  with self.assertRaises(AssertionError):p.validate(plan)
 def test_complete_selected_evidence(self):
  self.assertEqual(p.validate(self.plan)['artworks'],2351)
 def test_post_cutoff_creation(self):self.rejected(lambda x:x['artworks'][0].update(last=1971))
 def test_missing_creation_date(self):self.rejected(lambda x:x['artworks'][0].update(first=None))
 def test_uncertain_cutoff(self):self.rejected(lambda x:x['artworks'][0].update(first=1970,last=1970,date_precision='circa'))
 def test_duplicate_inventory_identity(self):self.rejected(lambda x:x['artworks'].append(copy.deepcopy(x['artworks'][0])))
 def test_changed_source_capture(self):self.rejected(lambda x:x['artworks'][0]['receipt'].update(sha256='0'*64))
 def test_invented_inventory(self):self.rejected(lambda x:x['artworks'][0].update(accession='invented-inventory'))
 def test_invented_public_title(self):self.rejected(lambda x:x['artworks'][0].update(title='A different artwork'))
 def test_unsupported_current_display(self):self.rejected(lambda x:x['artworks'][0].update(display_state='on_view'))
 def test_qualified_creator_cannot_become_primary(self):
  def change(x):
   w=next(w for w in x['artworks'] if w['attribution_role']=='attributed_to' and w['artist_id']);w['attribution_role']='primary';x['artworks'].remove(w);x['artworks'].insert(0,w)
  self.rejected(change)
 def test_no_existing_entity_updates_in_payload(self):
  data=p.payloads(self.plan,p.m.sha(p.PLAN.read_bytes()))
  self.assertEqual({x['id'] for x in data['artworks']},{x['id'] for x in self.plan['artworks']})
  self.assertEqual({x['id'] for x in data['artists']},{x['id'] for x in self.plan['artists']})
  self.assertTrue(all(x['status']=='published' and not x['research_candidate'] for x in data['artworks']))
  self.assertTrue(all(x['claim_type']=='holding' and 'display_state' not in x for x in data['artwork_location_assertions']))
  self.assertFalse({x['id'] for x in data['artists']}&{x['id'] for x in self.plan['protected']['artists']})

if __name__=='__main__':unittest.main()
