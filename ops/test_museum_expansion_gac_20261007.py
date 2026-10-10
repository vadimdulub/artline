"""Offline GAC source/identity and preservation checks; no database fixtures."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('gac',Path(__file__).with_name('museum-expansion-gac-holdings-20261007.py'))
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)


class GACReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=w.records()
        cls.record=next(r for r in cls.records if r['facts']['qid']=='Q117793009')
        scope=w.m.load(w.RUN/'initial-scope-001.json.gz')
        cls.arts={r['id']:r for r in w.m.load(Path(scope['backup_path']))['artworks']}
        cls.identities={r['artwork_id']:r for r in w.m.load(w.RUN/'identity-comparison-001.json.gz')['selected']}

    def setUp(self):
        self.entity=copy.deepcopy(self.record['wikidata']['entity'])
        self.art=copy.deepcopy(self.arts[self.record['facts']['artwork_id']])
        self.identity=copy.deepcopy(self.identities[self.art['id']])
        self.native=copy.deepcopy(self.record['source'])

    def check(self):
        return w.facts(self.entity,self.art,self.identity,self.native)

    def test_unique_primary_records(self):
        self.assertEqual(118,len(self.records))
        self.assertEqual(118,len({r['facts']['inventory'] for r in self.records}))
        self.assertEqual(self.record['facts'],self.check())
        self.assertEqual(135,len(w.native_rows()))

    def test_native_inventory_cannot_change(self):
        self.native['parsed']['fields']['GAC number']='1'
        with self.assertRaises(AssertionError):self.check()

    def test_native_creator_qualification_not_dropped(self):
        for term in ['after','circle','attributed','workshop']:
            with self.subTest(term=term):
                self.native['parsed']['fields']['Artist']='John Henry Frederick Bacon ('+term+')'
                with self.assertRaises(AssertionError):self.check()

    def test_native_date_must_be_eligible(self):
        for date in ['', '1971', '1969-1971', 'c.1970', '1861?', '1950-unknown']:
            with self.subTest(date=date):
                self.native['parsed']['fields']['Date']=date
                with self.assertRaises(AssertionError):self.check()

    def test_date_precision_and_explicit_short_ranges(self):
        for value,expected in [('c.1805-1806',(1805,1806,'circa_range')),('1940-45',(1940,1945,'range')),('15 July 1825',(1825,1825,'exact')),('November 1954',(1954,1954,'exact')),('1953/1954',(1953,1954,'range')),('c1955',(1955,1955,'circa'))]:
            self.assertEqual(expected,w.native_dates(value))

    def test_native_title_change_requires_review(self):
        self.native['parsed']['fields']['Title']='Different diplomat'
        self.native['parsed']['headings']=['Different diplomat']
        with self.assertRaises(AssertionError):self.check()

    def test_native_creator_change_requires_review(self):
        self.native['parsed']['fields']['Artist']='Francis Bacon (1909 - 1992)'
        with self.assertRaises(AssertionError):self.check()

    def test_canonical_alias_cannot_redirect_to_other_object(self):
        self.native['parsed']['canonical']='https://artcollection.dcms.gov.uk/artwork/17381/'
        with self.assertRaises(AssertionError):self.check()

    def test_unknown_acquisition_needs_explicit_review(self):
        self.native['parsed']['fields']['Acquisition']='Origin uncertain'
        with self.assertRaises(AssertionError):self.check()
        selected=[r for r in self.records if r['facts']['acquisition']=='Origin uncertain']
        self.assertEqual(2,len(selected))
        self.assertTrue(all('explicitly uncertain' in r['decision']['limitation'] for r in selected))

    def test_incoming_loan_not_treated_as_collection(self):
        self.native['parsed']['fields']['Acquisition']='Loan from another museum'
        with self.assertRaises(AssertionError):self.check()

    def test_foreign_collection_rejected(self):
        self.entity['claims']['P195'][0]['mainsnak']['datavalue']['value']['id']='Q1'
        with self.assertRaises(AssertionError):self.check()

    def test_historical_collection_rejected(self):
        self.entity['claims']['P195'][0].setdefault('qualifiers',{})['P582']=[]
        with self.assertRaises(AssertionError):self.check()

    def test_preferred_claim_cannot_hide_second_identity(self):
        claim=copy.deepcopy(self.entity['claims']['P195'][0]);claim['rank']='preferred'
        self.entity['claims']['P195'].append(claim)
        with self.assertRaises(AssertionError):self.check()

    def test_inventory_qualifier_must_be_same_collection(self):
        self.entity['claims']['P217'][0]['qualifiers']['P195'][0]['datavalue']['value']['id']='Q1'
        with self.assertRaises(AssertionError):self.check()

    def test_filename_qualified_attribution_preserved(self):
        self.entity['claims']['P18'][0]['mainsnak']['datavalue']['value']='John Henry Frederick Bacon (after) - Portrait.jpg'
        with self.assertRaises(AssertionError):self.check()

    def test_native_catalogue_discrepancy_preserved(self):
        record=next(r for r in self.records if r['facts']['qid']=='Q119207913')
        art=copy.deepcopy(self.arts[record['facts']['artwork_id']]);before=copy.deepcopy(art)
        result=w.facts(record['wikidata']['entity'],art,self.identities[art['id']],record['source'])
        self.assertEqual('1926',result['date_display'])
        self.assertEqual('c.1958-1959',result['native_date_display'])
        self.assertEqual(before,art)

    def test_live_catalogue_change_requires_new_review(self):
        self.art['creation_year_start']=1906
        with self.assertRaises(AssertionError):self.check()

    def test_published_or_prelinked_record_rejected(self):
        for field,value in [('published_at','2026-10-07'),('status','published'),('current_institution_id',w.IID)]:
            with self.subTest(field=field):
                self.art=copy.deepcopy(self.arts[self.record['facts']['artwork_id']]);self.art[field]=value
                with self.assertRaises(AssertionError):self.check()

    def test_unlinked_names_stay_object_labels(self):
        selected=[r for r in self.records if not self.identities[r['facts']['artwork_id']]['creator_links']]
        self.assertTrue(selected)
        for record in selected:
            art=self.arts[record['facts']['artwork_id']]
            self.assertEqual(art['unlinked_creator_label'],record['facts']['creator_label'])

    def test_versions_require_distinct_physical_evidence(self):
        pair=[r for r in self.records if r['facts']['qid'] in ['Q119026134','Q119026136']]
        self.assertEqual(2,len(pair))
        self.assertEqual(2,len({r['facts']['dimensions'] for r in pair}))
        self.identity['same_creator_title_collisions']=[{'id':'unknown'}]
        with self.assertRaises(AssertionError):self.check()

    def test_unreviewed_inventory_collision_rejected(self):
        self.identity['inventory_collisions']=[{'id':'not-researched'}]
        with self.assertRaises((AssertionError,StopIteration)):self.check()

    def test_unresolved_records_retained(self):
        review=w.m.load(w.REVIEW)
        self.assertEqual(135,len(review['decisions']))
        self.assertEqual(17,sum(r['decision']=='hold' for r in review['decisions']))
        held={r['qid'] for r in review['decisions'] if r['decision']=='hold'}
        self.assertTrue({'Q118893285','Q119268156','Q119195236','Q119293854'}<=held)

    def delta_pair(self):
        f=self.record['facts'];aid=f['artwork_id'];old={'artwork_id':aid,'id':'old','source_id':'old-source','superseded_by':None}
        before=dict(artworks=[copy.deepcopy(self.art)],artists=[],media=[],identifiers=[],museum={},citations=[],assertions=[old])
        after=copy.deepcopy(before);after['artworks'][0]['current_institution_id']=w.IID
        after['citations']=[dict(entity_id=aid,source_id=w.SID,source_record_id=f['inventory'],source_url=f['source_url'],field_name='museum_expansion_holding_reconciliation',evidence_note=w.note(self.record,'digest'))]
        after['assertions'][0]['superseded_by']=self.record['holding_id']
        after['assertions'].append(dict(artwork_id=aid,id=self.record['holding_id'],source_id=w.SID,claim_type='holding',institution_id=w.IID,review_state='accepted',context='collection',superseded_by=None,source_url=f['source_url'],evidence_note=w.holding_note(self.record,'digest')))
        return before,after

    def test_delta_accepts_only_expected_holding_change(self):
        before,after=self.delta_pair();w.assert_delta(before,after,[self.record],'digest')
        after['artworks'][0]['date_display']='1906'
        with self.assertRaises(AssertionError):w.assert_delta(before,after,[self.record],'digest')

    def test_delta_rejects_new_display_claim(self):
        before,after=self.delta_pair();after['assertions'][-1]['display_state']='on_view'
        with self.assertRaises(AssertionError):w.assert_delta(before,after,[self.record],'digest')

    def test_delta_rejects_image_or_creator_changes(self):
        for key in ['media','artists']:
            before,after=self.delta_pair();after[key]=[{'unexpected':'mutation'}]
            with self.assertRaises(AssertionError):w.assert_delta(before,after,[self.record],'digest')


if __name__=='__main__':unittest.main()
