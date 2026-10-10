"""Offline source and mutation-boundary checks; no database access or fixtures."""
import copy
import importlib.util
import unittest
from pathlib import Path
from unittest import mock
s=importlib.util.spec_from_file_location('russell',Path(__file__).with_name('museum-expansion-russell-holdings-20261007.py'))
w=importlib.util.module_from_spec(s);s.loader.exec_module(w)


class RussellHoldingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=w.records();cls.arts={r['id']:r for r in w.baseline()['artworks']}
        cls.identities={r['artwork_id']:r for r in w.m.load(w.RUN/'identity-comparison-001.json.gz')['selected']}
        cls.record=next(r for r in cls.records if r['facts']['qid']=='Q119141497')

    def setUp(self):
        self.entity=copy.deepcopy(self.record['source']['entity'])
        self.art=copy.deepcopy(self.arts[self.record['facts']['artwork_id']])
        self.identity=copy.deepcopy(self.identities[self.art['id']])

    def check(self):return w.facts(self.entity,self.art,self.identity)

    def test_selected_sources_and_held_accounting(self):
        self.assertEqual(98,len(self.records));self.assertEqual(98,len({w.compact(r['facts']['inventory']) for r in self.records}))
        rows=w.m.load(w.REVIEW)['decisions'];self.assertEqual(115,len(rows));self.assertEqual(17,sum(r['decision']=='hold' for r in rows))
        self.assertEqual(self.record['facts'],self.check())

    def test_historical_owner_does_not_become_current_owner(self):
        self.assertEqual('Q6820727',w.val(self.entity,'P127')['id'])
        self.assertEqual(1921,w.year(w.qualifier_value(w.one(self.entity,'P127'),'P582')))
        del self.entity['claims']['P127'][0]['qualifiers']['P582']
        with self.assertRaises(AssertionError):self.check()

    def test_other_historical_owner_not_blanket_accepted(self):
        self.entity['claims']['P127'][0]['mainsnak']['datavalue']['value']['id']='Q1'
        with self.assertRaises(AssertionError):self.check()

    def test_foreign_or_ended_collection_rejected(self):
        for mutate in [lambda c:c['mainsnak']['datavalue']['value'].update(id='Q1'),lambda c:c.setdefault('qualifiers',{}).update(P582=[])]:
            self.setUp();mutate(self.entity['claims']['P195'][0])
            with self.assertRaises(AssertionError):self.check()

    def test_conflicting_preferred_collection_not_hidden(self):
        second=copy.deepcopy(self.entity['claims']['P195'][0]);second['rank']='preferred';self.entity['claims']['P195'].append(second)
        with self.assertRaises(AssertionError):self.check()

    def test_exact_artuk_reference_url_is_validated(self):
        r=next(r for r in self.records if r['facts']['qid']=='Q119870066');e=copy.deepcopy(r['source']['entity']);a=self.arts[r['facts']['artwork_id']];i=self.identities[a['id']]
        self.assertEqual(r['facts'],w.facts(e,a,i))
        e['claims']['P195'][0]['references'][0]['snaks']['P854'][0]['datavalue']['value']='https://artuk.org/discover/artworks/another-1'
        with self.assertRaises(AssertionError):w.facts(e,a,i)

    def test_inventory_namespace_and_duplicate_guards(self):
        self.identity['inventory_collisions']=[{'id':'other'}]
        with self.assertRaises(AssertionError):self.check()
        self.setUp();self.entity['claims']['P217'][0]['qualifiers']['P195'][0]['datavalue']['value']['id']='Q1'
        with self.assertRaises(AssertionError):self.check()

    def test_both_possible_faces_remain_unassigned(self):
        held={r['qid'] for r in w.m.load(w.REVIEW)['decisions'] if r['decision']=='hold'}
        self.assertTrue({'Q119146933','Q119147222'}<=held)

    def test_unknown_creator_and_qualified_attribution_held(self):
        self.identity['creator_match']=False
        with self.assertRaises(AssertionError):self.check()
        self.setUp();self.entity['claims']['P170'][0]['qualifiers']={'P1480':[]}
        with self.assertRaises(AssertionError):self.check()

    def test_copy_object_not_confused_with_original(self):
        r=next(r for r in self.records if r['facts']['qid']=='Q119710615')
        self.assertEqual('Henry Justice Ford',r['facts']['creator_label'])
        self.assertIn('copy of Anna Lea Merritt',r['decision']['version_review'])
        self.assertIn('Tate original',r['decision']['version_review'])
        self.assertEqual((1890,1910),(r['facts']['first'],r['facts']['last']))
        self.assertIn('1889',r['decision']['native_comparison']['exact_inventory_sources'][0]['parsed']['caption_lines'][0])

    def test_native_date_discrepancy_retained(self):
        r=next(r for r in self.records if r['facts']['qid']=='Q119140460')
        self.assertEqual(1885,r['facts']['first']);self.assertIn('1865',r['decision']['version_review'])
        self.assertIn('copy',r['decision']['version_review'])

    def test_preexisting_metadata_and_publication_must_match(self):
        for k,v in [('creation_year_start',1971),('date_precision','unknown'),('status','published'),('current_institution_id',w.IID)]:
            self.setUp();self.art[k]=v
            with self.assertRaises(AssertionError):self.check()

    def test_native_caption_tampering_is_detected(self):
        ref=w.m.load(w.RUN/'native-holding-comparison-001.json.gz')['capture_files'][0];x=copy.deepcopy(w.m.load(w.m.ROOT/ref['path']));x['parsed']['caption_lines']=['changed']
        with mock.patch.object(w.m,'load',return_value=x):
            with self.assertRaises(AssertionError):w.checked_native_page(ref)

    def test_disposal_proposal_is_not_reported_as_completed(self):
        r=w.m.load(w.RUN/'disposal-review-001.json');self.assertTrue(r['proposal_not_completed']);self.assertEqual('2026-10-26',r['proposed_committee_decision']);self.assertFalse(r['existing_scope_inventory_matches'])

    def delta_pair(self):
        f=self.record['facts'];aid=f['artwork_id'];old={'artwork_id':aid,'id':'old','source_id':'old-source','superseded_by':None}
        before=dict(artworks=[copy.deepcopy(self.art)],artists=[],media=[],identifiers=[],museum={},citations=[],assertions=[old]);after=copy.deepcopy(before);after['artworks'][0]['current_institution_id']=w.IID
        after['citations']=[dict(entity_id=aid,source_id=w.SID,source_record_id=f['qid'],source_url=f['source_url'],field_name='museum_expansion_holding_reconciliation',evidence_note=w.note(self.record,'digest'))]
        after['assertions'][0]['superseded_by']=self.record['holding_id']
        after['assertions'].append(dict(artwork_id=aid,id=self.record['holding_id'],source_id=w.SID,claim_type='holding',institution_id=w.IID,review_state='accepted',context='collection',superseded_by=None,source_url=f['source_url'],evidence_note=w.holding_note(self.record,'digest')))
        return before,after

    def test_only_expected_delta_accepted(self):
        before,after=self.delta_pair();w.assert_delta(before,after,[self.record],'digest')
        for k,v in [('date_display','wrong'),('status','published'),('unlinked_creator_label','invented'),('primary_media_id','new')]:
            before,after=self.delta_pair();after['artworks'][0][k]=v
            with self.assertRaises(AssertionError):w.assert_delta(before,after,[self.record],'digest')

    def test_multiple_old_claims_preserved_and_superseded(self):
        before,after=self.delta_pair();second=dict(before['assertions'][0],id='second')
        before['assertions'].append(second)
        after['assertions'].insert(1,dict(second,superseded_by=self.record['holding_id']))
        w.assert_delta(before,after,[self.record],'digest')
        after['assertions'][1]['superseded_by']=None
        with self.assertRaises(AssertionError):w.assert_delta(before,after,[self.record],'digest')

    def test_images_creators_citations_and_display_protected(self):
        for k in ['media','artists','identifiers']:
            before,after=self.delta_pair();after[k]=[{'unexpected':'mutation'}]
            with self.assertRaises(AssertionError):w.assert_delta(before,after,[self.record],'digest')
        before,after=self.delta_pair();after['assertions'][-1]['display_state']='on_view'
        with self.assertRaises(AssertionError):w.assert_delta(before,after,[self.record],'digest')


if __name__=='__main__':unittest.main()
