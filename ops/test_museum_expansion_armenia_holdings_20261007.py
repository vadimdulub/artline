"""Offline rejection tests for existing-object holding reconciliation."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('h',Path(__file__).with_name('museum-expansion-armenia-holdings-20261007.py'))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h);m=h.m

class HoldingIdentity(unittest.TestCase):
    def setUp(self):
        r=m.load(h.RUN/'existing-holding-screen-001.json.gz')['candidate_records'][0]
        self.entity=copy.deepcopy(r['entity']);self.record=copy.deepcopy(r['record'])
        self.creator=next(x for x in m.load(h.RUN/'existing-holding-creator-identities-001.json')['rows'] if x['artwork_id']==self.record['id'])

    def runfacts(self):return h.facts(self.entity,self.record,self.creator)
    def test_exact_identity(self):self.assertEqual(self.runfacts()['inventory'],'310')
    def test_wrong_museum_rejected(self):
        self.entity['claims']['P195'][0]['mainsnak']['datavalue']['value']['id']='Q182955'
        with self.assertRaises(AssertionError):self.runfacts()
    def test_historic_collection_qualifier_rejected(self):
        self.entity['claims']['P195'][0]['qualifiers']={'P582':[{}]}
        with self.assertRaises(AssertionError):self.runfacts()
    def test_unknown_creator_rejected(self):
        self.entity['claims']['P170'][0]['mainsnak']['snaktype']='somevalue';self.entity['claims']['P170'][0]['mainsnak'].pop('datavalue')
        with self.assertRaises(AssertionError):self.runfacts()
    def test_qualified_creator_rejected(self):
        self.entity['claims']['P170'][0]['qualifiers']={'P1480':[{}]}
        with self.assertRaises(AssertionError):self.runfacts()
    def test_another_artist_rejected(self):
        self.creator=copy.deepcopy(self.creator);self.creator['wikidata_ids']=['Q5582']
        with self.assertRaises(AssertionError):self.runfacts()
    def test_conflicting_inventory_rejected(self):
        self.record['accession_number']='311'
        with self.assertRaises(AssertionError):self.runfacts()
    def test_inventory_belongs_to_other_museum_rejected(self):
        self.entity['claims']['P217'][0]['qualifiers']['P195'][0]['datavalue']['value']['id']='Q182955'
        with self.assertRaises(AssertionError):self.runfacts()
    def test_title_mismatch_rejected(self):
        self.record['title']='Another physical work'
        with self.assertRaises(AssertionError):self.runfacts()
    def test_date_conflict_rejected(self):
        self.record['creation_year_end']=1926
        with self.assertRaises(AssertionError):self.runfacts()
    def test_cutoff_rejected(self):
        self.entity['claims']['P571'][0]['mainsnak']['datavalue']['value']['time']='+1971-00-00T00:00:00Z'
        self.record['creation_year_start']=self.record['creation_year_end']=1971
        with self.assertRaises(AssertionError):self.runfacts()
    def test_multiple_collections_rejected(self):
        other=copy.deepcopy(self.entity['claims']['P195'][0]);other['mainsnak']['datavalue']['value']['id']='Q182955';self.entity['claims']['P195'].append(other)
        with self.assertRaises(AssertionError):self.runfacts()
    def test_component_requires_review(self):
        self.entity['claims']['P361']=copy.deepcopy(self.entity['claims']['P195'])
        with self.assertRaises(AssertionError):self.runfacts()
    def test_pinned_plan_has_exact_selected_scope(self):
        plan,digest=h.validate_plan();self.assertEqual(len(plan['records']),136)
        self.assertFalse({r['facts']['qid'] for r in plan['records']}&set(h.EXCLUDED))
        self.assertEqual(len({r['facts']['inventory'] for r in plan['records']}),136)
    def test_all_source_captures_hash_verified(self):self.assertEqual(len(h.source_rows()),153)

if __name__=='__main__':unittest.main()
