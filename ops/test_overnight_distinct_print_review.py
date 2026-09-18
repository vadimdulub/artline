import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('review',Path(__file__).with_name('overnight-distinct-print-review.py'));review=importlib.util.module_from_spec(s);s.loader.exec_module(review)
s=importlib.util.spec_from_file_location('guard',Path(__file__).with_name('import-overnight-met-selection.py'));guard=importlib.util.module_from_spec(s);s.loader.exec_module(guard)
class PhysicalPrintReview(unittest.TestCase):
 def setUp(self):
  self.old={'id':'old','slug':'old','title':'Shared print title','work_type':'print','accession_number':'A.1','current_institution_id':'other-museum','artist_ids':['artist'],'status':'review'}
  self.c={'artwork_id':'new','slug':'new','title':'Shared print title','work_type':'print','accession_number':'B.1','external_id':'200','page':'https://collections.artsmia.org/art/200','artist_qid':'Q1','artist_slug':'artist','provider':'night-mia','scheme':'mia-object','physical_object_review':{'decision':'distinct_accessioned_prints','candidate_key':'mia:200','candidate_accession':'B.1','objects':[{'key':'met:100','object_type':'print','title':'Shared print title','accession_number':'A.1','source_url':'https://www.metmuseum.org/art/collection/search/100','source_capture_sha256':'0'*64}]}}
  self.state={'institution_id':'mia','works':[self.old],'artists':{'Q1':[{'id':'artist','slug':'artist','status':'review'}]},'identifiers':[],'redirects':[],'schemes':['mia-object'],'review_native_keys':{'old':['met:100']}}
 def test_default_still_holds_same_title(self):
  accepted,held=guard.conflicts([self.c],self.state);self.assertEqual(len(held),1);self.assertEqual(accepted,[])
 def test_explicit_review_distinguishes_impressions(self):
  accepted,held=guard.conflicts([self.c],self.state,review.allow);self.assertEqual(len(accepted),1);self.assertEqual(held,[])
 def test_missing_native_evidence_fails(self):
  self.state['review_native_keys']={};self.assertFalse(review.allow(self.c,[self.old],[],self.state))
 def test_changed_accession_fails(self):
  self.old['accession_number']='changed';self.assertFalse(review.allow(self.c,[self.old],[],self.state))
 def test_changed_title_fails(self):
  self.old['title']='Other work';self.assertFalse(review.allow(self.c,[self.old],[],self.state))
 def test_ambiguous_source_identity_fails(self):
  self.state['review_native_keys']['old'].append('met:101');self.assertFalse(review.allow(self.c,[self.old],[],self.state))
 def test_painting_exception_is_not_allowed(self):
  self.c['work_type']='painting';self.assertFalse(review.allow(self.c,[self.old],[],self.state))
 def test_smk_requires_matching_native_provider(self):
  self.c.update(provider='night-smk',scheme='european-smk-statens-museum-for-kunst-object');self.c['physical_object_review']['candidate_key']='smk:200'
  self.assertTrue(review.allow(self.c,[self.old],[],self.state))
  self.c['provider']='night-mia';self.assertFalse(review.allow(self.c,[self.old],[],self.state))
 def test_smk_preserves_real_wikidata_after_native_guard(self):
  spec=importlib.util.spec_from_file_location('smk_import',Path(__file__).with_name('import-overnight-smk-selection.py'));smk=importlib.util.module_from_spec(spec);spec.loader.exec_module(smk)
  self.c.update(provider='night-smk',scheme='european-smk-statens-museum-for-kunst-object',artist_authority='123_person',artist_qid='Q999')
  self.c['physical_object_review']['candidate_key']='smk:200';self.state['artists']={'123_person':self.state['artists']['Q1']}
  accepted,held=smk.conflicts([self.c],self.state);self.assertEqual(held,[]);self.assertEqual(accepted[0]['artist_qid'],'Q999')
 def test_no_evidence_never_bypasses_title_guard(self):
  self.c.pop('physical_object_review');accepted,held=guard.conflicts([self.c],self.state,review.allow);self.assertEqual(len(held),1);self.assertEqual(accepted,[])
 def test_native_duplicate_stays_held(self):
  self.state['identifiers']=[{'entity_id':'old','scheme':'mia-object','external_id':'200','canonical_url':self.c['page']}]
  accepted,held=guard.conflicts([self.c],self.state,review.allow);self.assertEqual(accepted,[]);self.assertIn('source identifier',held[0]['reason'])
 def test_accession_duplicate_stays_held(self):
  self.old.update(current_institution_id='mia',accession_number='B.1');accepted,held=guard.conflicts([self.c],self.state,review.allow);self.assertEqual(accepted,[]);self.assertIn('accession',held[0]['reason'])
 def test_unreviewed_second_impression_stays_held(self):
  second=copy.deepcopy(self.c);second.update(artwork_id='second',slug='second',external_id='201',page='https://collections.artsmia.org/art/201',accession_number='B.2');second['physical_object_review'].update(candidate_key='mia:201',candidate_accession='B.2')
  accepted,held=guard.conflicts([self.c,second],self.state,review.allow);self.assertEqual(len(accepted),1);self.assertEqual(len(held),1)
if __name__=='__main__':unittest.main()
