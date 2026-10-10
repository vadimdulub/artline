"""Offline ingestion safety tests. Never creates or connects to a database."""
import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('publication',Path(__file__).with_name('south-africa-publish-20261008.py'))
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class SouthAfricaPublicationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.plan=p.m.load(p.PLAN)
 def test_every_selected_object_revalidates_against_pinned_primary_source(self):
  self.assertEqual(p.validate(self.plan)['artworks'],342)
 def test_dates_do_not_infer_unknowns_or_use_acquisition_or_title_dates(self):
  for s in [None,'','Unknown','n.d.','1971','1960/1980','c.1970','1948, Date created: 1993','Acquired 1965','1880 (cast 1980)']:
   self.assertIsNone(p.m.dates(s),s)
  self.assertEqual(p.m.dates('1220/1250')['last'],1250)
  self.assertEqual(p.m.dates('c.1940')['date_precision'],'circa')
 def test_corrupted_receipt_fails_before_mutation(self):
  rc=copy.deepcopy(self.plan['artworks'][0]['receipt']);rc['sha256']='0'*64
  with self.assertRaises(AssertionError):p.raw(rc)
 def test_duplicate_native_identity_is_rejected(self):
  q=copy.deepcopy(self.plan);q['artworks'].append(copy.deepcopy(q['artworks'][0]))
  with self.assertRaises(AssertionError):p.validate(q)
 def test_post_cutoff_or_display_claim_is_rejected(self):
  for change in [dict(last=1971),dict(display_state='on_view'),dict(venue_id='invented')]:
   q=copy.deepcopy(self.plan);q['artworks'][0].update(change)
   with self.assertRaises(AssertionError):p.validate(q)
 def test_private_loans_default_dates_and_duplicate_views_are_excluded(self):
  ids={w['source_id'] for w in self.plan['artworks']}
  for sid in ['EAHVuU4VJkikfg','iQG7RkChvYw3_w','2AEmKiL_fWZ7QQ','dgHw3amlhaoXIg','fQGTV_nXMcXQow','cwGFtnpJiV0jrQ','vgH92U9xmqzCUg']:
   self.assertNotIn(sid,ids)
 def test_publisher_and_anonymous_maker_not_invented_persons(self):
  publisher=next(w for w in self.plan['artworks'] if w['key']=='mandela/10468')
  self.assertIsNone(publisher['artist_id']);self.assertEqual(publisher['accession'],'P283/83 08')
  gold=[w for w in self.plan['artworks'] if w['cultural_context']=='Mapungubwe']
  self.assertEqual(len(gold),6);self.assertTrue(all(w['artist_id'] is None and w['creator_label'] is None for w in gold))
 def test_activity_is_not_an_invented_lifespan(self):
  for a in self.plan['artists']:
   self.assertIsNone(a['birth_year']);self.assertIsNone(a['death_year']);self.assertEqual(a['timeline_basis'],'activity')
   ws=[w for w in self.plan['artworks'] if w['artist_id']==a['id']]
   self.assertEqual(a['timeline_start_year'],min(w['first'] for w in ws));self.assertEqual(a['timeline_end_year'],max(w['last'] for w in ws))
 def test_actual_collection_owner_and_no_current_display(self):
  for w in self.plan['artworks']:
   if w['source_kind']=='rupert':self.assertEqual(w['collection_owner'],w['institution_name'])
  data=p.payloads(self.plan,'offline-proof')
  self.assertTrue(all(r['claim_type']=='holding' and 'display_state' not in r for r in data['artwork_location_assertions']))
  self.assertTrue(all(r['status']=='published' and not r['research_candidate'] for r in data['artworks']))

if __name__=='__main__':unittest.main()
