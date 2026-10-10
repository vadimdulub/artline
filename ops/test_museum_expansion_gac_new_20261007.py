"""Offline native-source, duplicate and metadata guards; no database fixtures."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-gac-new-20261007.py'))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)


class GACNewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.records=n.records()

    def setUp(self):self.record=copy.deepcopy(self.records[0])

    def check(self):
        r=self.record
        return n.facts(r['native'],r['wikidata']['entity'],r['creator_entity'],r['decision'])

    def test_58_distinct_native_objects(self):
        self.assertEqual(58,len(self.records));self.assertEqual(58,len({r['facts']['inventory'] for r in self.records}))
        self.assertEqual(56,len({r['facts']['creator_label'] for r in self.records}))
        self.assertEqual(self.record['facts'],self.check())

    def test_held_and_deferred_records_remain_evidence(self):
        decisions=n.m.load(n.REVIEW)['decisions'];self.assertEqual(100,len(decisions))
        held={r['qid']:r['state'] for r in decisions if r['state']!='approved_review_only_addition'}
        self.assertEqual(42,len(held));self.assertEqual('held_version_comparison',held['Q119308420'])
        self.assertEqual('held_missing_object',held['Q119303129'])
        self.assertEqual('held_unknown_native_date',held['Q119305052'])

    def test_foreign_holding_and_inventory_rejected(self):
        for prop in ['P195','P217']:
            self.setUp();e=self.record['wikidata']['entity']
            if prop=='P195':e['claims'][prop][0]['mainsnak']['datavalue']['value']['id']='Q1'
            else:e['claims'][prop][0]['mainsnak']['datavalue']['value']='9999'
            with self.subTest(prop=prop),self.assertRaises(AssertionError):self.check()

    def test_historical_collection_rejected(self):
        self.record['wikidata']['entity']['claims']['P195'][0].setdefault('qualifiers',{})['P582']=[]
        with self.assertRaises(AssertionError):self.check()

    def test_multiple_creator_statements_not_hidden(self):
        claims=self.record['wikidata']['entity']['claims']['P170'];claims.append(copy.deepcopy(claims[0]));claims[-1]['rank']='preferred'
        with self.assertRaises(AssertionError):self.check()

    def test_qualified_creator_cannot_become_primary(self):
        self.record['wikidata']['entity']['claims']['P170'][0]['qualifiers']={'P5102':[]}
        with self.assertRaises(AssertionError):self.check()

    def test_unreviewed_duplicate_lead_rejected(self):
        for key in ['same','invhits']:
            self.setUp();self.record['decision']['comparison'][key]=[{'id':'unreviewed'}]
            with self.subTest(key=key),self.assertRaises(AssertionError):self.check()

    def test_source_canonical_change_rejected(self):
        self.record['native']['parsed']['canonical']='https://artcollection.dcms.gov.uk/artwork/1/'
        with self.assertRaises(AssertionError):self.check()

    def test_explicit_native_date_over_secondary_index(self):
        r=next(r for r in self.records if r['facts']['qid']=='Q119839808')
        self.assertEqual('1970',r['facts']['date_display']);self.assertEqual(1970,r['facts']['first'])
        self.assertEqual(1960,n.w.year(n.w.val(r['wikidata']['entity'],'P571')))

    def test_circa_range_and_structural_form_preserved(self):
        r=next(r for r in self.records if r['facts']['qid']=='Q119656075')
        self.assertEqual(('c.1954-1956',1954,1956,'circa_range'),tuple(r['facts'][k] for k in ['date_display','first','last','date_precision']))
        panel=next(r for r in self.records if r['facts']['qid']=='Q119328396')
        self.assertEqual('Oil on four wood panels mounted on board',panel['facts']['medium'])
        self.assertEqual(1,sum(r['facts']['inventory']=='9276' for r in self.records))

    def test_literal_creator_name_preserved_without_biography(self):
        self.assertEqual('Sir Kyffin Williams',n.creator_label('Sir Kyffin Williams (1918 - 2006)'))
        self.assertEqual('Pietro (after) Annigoni',n.creator_label('Pietro (after) Annigoni (1910 - 1988)'))
        self.assertEqual('Diana Cumming',n.creator_label('Diana Cumming (1929 - 11/2024)'))

    def expected_artwork(self):
        r=self.record;f=r['facts']
        art=dict(id=r['artwork_id'],slug=r['slug'],title=f['title'],normalized_title=n.m.norm(f['title']),date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],medium_text=f['medium'],dimensions_text=f['dimensions'],accession_number=f['inventory'],status='review',research_candidate=True,unlinked_creator_label=f['creator_label'],current_institution_id=n.IID,created_by=n.m.ACTOR,updated_by=n.m.ACTOR)
        for k in ['alternate_title','description_md','primary_media_id','published_at','object_form','cultural_context','creation_place_display','creation_place_unknown_reason','current_location_text','current_location_unknown_reason','location_checked_at']:art[k]=None
        return art

    def test_publication_image_or_metadata_mutation_rejected(self):
        art=self.expected_artwork();n.assert_new(art,self.record)
        for key,value in [('status','published'),('primary_media_id','invented'),('creation_year_start',1971),('unlinked_creator_label','Another person')]:
            changed=dict(art);changed[key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):n.assert_new(changed,self.record)

    def test_creation_unknowns_not_invented(self):
        for key in ['object_form','cultural_context','creation_place_display','creation_place_unknown_reason']:
            art=self.expected_artwork();art[key]='invented'
            with self.subTest(key=key),self.assertRaises(AssertionError):n.assert_new(art,self.record)


if __name__=='__main__':unittest.main()
