#!/usr/bin/env python3
"""Offline adversarial checks; no database or catalogue fixtures."""
import collections,copy,importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,ROOT/p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
a=mod('assessment','ops/assess-random-5000-round3-20261007.py');d=mod('delivery','ops/apply-random-5000-round3-20261007.py')
def statement(v,**more):return {'mainsnak':{'datavalue':{'value':{'id':v}if v.startswith('Q')else v}},'rank':'normal',**more}
class EvidenceTests(unittest.TestCase):
 def setUp(self):
  self.row={'artwork':{'id':'object','title':'River at Sunset','alternate_title':None,'accession_number':None,'work_type':'painting','unlinked_creator_label':None},'creators':[{'artist_id':'artist'}]}
  self.e={'entity':{'id':'Q100','labels':{'en':{'value':'River at Sunset'}},'claims':{'P170':[statement('Q10')],'P195':[statement('Q20')],'P217':[statement('INV-42')]}},'receipt':{'retrieved_at':'2026-10-06T00:00:00Z'}}
  self.resolved={'Q20':{'institution':{'id':'museum','name':'Test Museum'},'basis':'documented','authority':{'receipt':{}}}};self.artists=collections.defaultdict(set,{'artist':{'Q10'}})
 def assess(self):return a.wd_assessment(self.row,self.e,self.artists,self.resolved)
 def test_exact_object_creator_collection_inventory(self):self.assertIsNotNone(self.assess()[0])
 def test_different_creator_is_not_a_title_match(self):self.e['entity']['claims']['P170']=[statement('Q11')];self.assertIsNone(self.assess()[0])
 def test_different_title_is_not_a_creator_match(self):self.row['artwork']['title']='Sunset Study';self.assertIsNone(self.assess()[0])
 def test_multiple_current_collections_are_held(self):self.e['entity']['claims']['P195'].append(statement('Q21'));self.assertIsNone(self.assess()[0])
 def test_ended_collection_is_not_current(self):self.e['entity']['claims']['P195'].append(statement('Q21',qualifiers={'P582':[{}]}));self.assertIsNotNone(self.assess()[0])
 def test_part_qualifier_is_not_whole_object_collection(self):self.e['entity']['claims']['P195'][0]['qualifiers']={'P518':[{}]};self.assertIsNone(self.assess()[0])
 def test_historical_point_in_time_is_not_current(self):self.e['entity']['claims']['P195'][0]['qualifiers']={'P585':[{}]};self.assertIsNone(self.assess()[0])
 def test_inventory_disagreement_is_held(self):self.row['artwork']['accession_number']='INV-43';self.assertIsNone(self.assess()[0])
 def test_unidentified_print_impression_is_held(self):self.row['artwork']['work_type']='print';self.assertIsNone(self.assess()[0])
 def test_print_with_exact_existing_inventory_can_match(self):self.row['artwork'].update(work_type='print',accession_number='INV-42');self.assertIsNotNone(self.assess()[0])
 def test_unknown_version_without_inventory_or_native_reference(self):self.e['entity']['claims'].pop('P217');self.assertIsNone(self.assess()[0])
 def test_unlinked_label_does_not_create_artist_relationship(self):
  self.row['creators']=[];self.row['artwork']['unlinked_creator_label']='Example, Alice';before=copy.deepcopy(self.row);ca={'Q10':{'entity':{'labels':{'en':{'value':'Alice Example'}}},'receipt':{}}}
  self.assertIsNotNone(a.wd_assessment(self.row,self.e,self.artists,self.resolved,ca)[0]);self.assertEqual(before,self.row)
 def test_municipality_is_not_museum_because_of_building_type(self):
  au={'Q20':{'entity':{'labels':{'en':{'value':'Oxford Town Hall'}},'claims':{'P31':[statement('Q24699794')],'P856':[statement('https://example.org')]}},'receipt':{}}};resolved,held=a.institutions(au,[]);self.assertFalse(resolved);self.assertIn('Q20',held)
 def test_indexed_generic_title_requires_version_evidence(self):
  c={'artwork_id':'object','institution':{'name':'Museum of Art'},'detail_page':True,'source_url':'https://example.org/objects/42','qualified_holding_text':False,'exact_source_url':False,'inventory_correspondence':False,'excerpt':'Portrait of a Man, Alice Example, 1882','print_impression_unresolved':False,'title':'Portrait of a Man','source_title':'Portrait of a Man | Museum','year_correspondence':True};self.assertIsNotNone(d.indexed_reason(c))
 def test_indexed_derivative_cannot_match_original_by_creator_mention(self):
  c={'artwork_id':'object','institution':{'name':'Museum of Art'},'detail_page':True,'source_url':'https://example.org/objects/42','qualified_holding_text':False,'exact_source_url':False,'inventory_correspondence':False,'excerpt':'Artist After Jean Fragonard, 1785','print_impression_unresolved':False,'title':'The Fountain of Love','source_title':'The Fountain of Love | Museum','year_correspondence':True};self.assertIsNotNone(d.indexed_reason(c))
 def test_indexed_study_is_not_the_completed_work(self):
  c={'artwork_id':'object','institution':{'name':'Museum of Art'},'detail_page':True,'source_url':'https://example.org/objects/42','qualified_holding_text':False,'exact_source_url':False,'inventory_correspondence':False,'excerpt':'Compositional Study for The Apotheosis of Napoleon I, Ingres, 1853','print_impression_unresolved':False,'title':'The Apotheosis of Napoleon I','source_title':'Compositional Study for The Apotheosis of Napoleon I','year_correspondence':True};self.assertIsNotNone(d.indexed_reason(c))
class WikiArtRegressionTests(unittest.TestCase):
 def test_multi_museum_literal_is_never_accepted_automatically(self):
  data=a.r.load(a.RUN/'wikiart-holding-plan-v9.json.gz')
  self.assertFalse([c for c in data['claims']if c['object_evidence']['page']['fields']['Location'].count(',')>=4])
 def test_christchurch_is_not_treated_as_a_church(self):
  data=a.r.load(a.RUN/'wikiart-holding-plan-v9.json.gz')
  self.assertIn('Christchurch Art Gallery Te Puna o Waiwhetū, Christchurch, New Zealand',data['institution_resolutions'])
 def test_known_replica_dates_do_not_establish_original_holdings(self):
  data=a.r.load(a.RUN/'wikiart-holding-plan-v9.json.gz');ids={c['artwork_id']for c in data['claims']}
  self.assertFalse(ids&{'2c89d7b8-94e1-5424-a753-9d62790d8173','432c03e8-6ca6-5a47-8710-2b372098d1f9','5e6930b3-9bb4-582e-b7af-ad1e76c07808','2d8f7898-05ec-5fe3-837c-e0d81d1dbebb'})
 def test_private_foundation_is_not_assigned_as_museum(self):
  data=a.r.load(a.RUN/'wikiart-holding-plan-v9.json.gz');self.assertNotIn('ea2832b9-bac8-531f-82ec-7b98bb73bb46',{c['artwork_id']for c in data['claims']})
 def test_future_collection_start_not_in_current_claims(self):
  data=a.r.load(a.RUN/'wikidata-assessment-v4.json.gz')
  for c in data['claims']:
   for st in c['object_evidence']['collection_statement']:
    for v in st.get('qualifiers',{}).get('P580',[]):
     value=v.get('datavalue',{}).get('value',{}).get('time','')
     self.assertTrue(not value or value.lstrip('+')[:10]<='2026-10-07')
if __name__=='__main__':unittest.main()
