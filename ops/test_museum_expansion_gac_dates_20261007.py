"""Offline creation-date, missing-object and preservation checks; no DB fixtures."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-gac-dates-20261007.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


class GACDateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=v.records();cls.scope=v.m.load(v.SCOPE)
        cls.before=v.m.load(Path(cls.scope['backup_path']))

    def check(self,record,change=None):
        aid=record['facts']['artwork_id']
        art=copy.deepcopy(next(a for a in self.before['artworks'] if a['id']==aid))
        if change:art.update(change)
        artist=next(a for a in self.scope['artists'] if a['artwork_id']==aid)
        authority=next(a for a in self.scope['artist_authorities'] if a['entity_id']==artist['artist_id'])
        return v.facts(art,record['wikidata']['entity'],record['source'],artist,authority,record['decision'])

    def test_six_explicit_dates_five_holdings(self):
        self.assertEqual(6,len(self.records))
        self.assertEqual(5,sum(r['facts']['accept_holding'] for r in self.records))
        for r in self.records:self.assertEqual(r['facts'],self.check(r))

    def test_decade_preserves_range(self):
        self.assertEqual((1650,1659,'range'),v.creation('1650s'))
        self.assertEqual((1960,1969,'range'),v.creation('1960s'))

    def test_cutoff_and_uncertainty_require_review(self):
        for literal in ['', '1970s','c.1970','1969-1971','1950?','after 1950']:
            with self.subTest(literal=literal),self.assertRaises(AssertionError):v.creation(literal)

    def test_circa_ranges_and_slash_dates(self):
        self.assertEqual((1850,1870,'circa_range'),v.creation('c.1850-1870'))
        self.assertEqual((1957,1958,'range'),v.creation('1957/1958'))

    def test_only_initial_unknown_dates_may_change(self):
        for change in [{'creation_year_start':1950},{'creation_year_end':1950},{'date_precision':'exact'},{'date_display':'Unknown'}]:
            with self.subTest(change=change),self.assertRaises(AssertionError):self.check(self.records[0],change)

    def test_published_or_linked_records_rejected(self):
        for change in [{'status':'published'},{'published_at':'2026-10-07'},{'current_institution_id':v.IID}]:
            with self.subTest(change=change),self.assertRaises(AssertionError):self.check(self.records[0],change)

    def test_missing_object_date_does_not_authorize_holding(self):
        r=next(r for r in self.records if r['facts']['qid']==v.MISSING)
        self.assertFalse(r['facts']['accept_holding']);self.assertIsNone(r['holding_id'])
        changed=copy.deepcopy(r);changed['decision']['accept_holding']=True
        with self.assertRaises(AssertionError):self.check(changed)

    def test_source_creator_pair_requires_review(self):
        r=copy.deepcopy(self.records[0]);r['decision']['creator_pair'][1]='Another artist'
        with self.assertRaises(AssertionError):self.check(r)

    def delta_pair(self):
        before={k:copy.deepcopy(self.before[k]) for k in ['artworks','artists','media','identifiers','citations','assertions','museum']}
        after=copy.deepcopy(before);arts={a['id']:a for a in after['artworks']}
        for r in self.records:
            f=r['facts'];aid=f['artwork_id'];arts[aid].update(f['patch'],updated_by=v.m.ACTOR)
            after['citations'].append(dict(entity_id=aid,source_id=v.SID,source_record_id=f['inventory'],source_url=f['source_url'],field_name='museum_expansion_native_date_enrichment',evidence_note=v.note(r,'digest')))
            if f['accept_holding']:
                arts[aid]['current_institution_id']=v.IID
                next(a for a in after['assertions'] if a['artwork_id']==aid)['superseded_by']=r['holding_id']
                after['assertions'].append(dict(artwork_id=aid,id=r['holding_id'],source_id=v.SID,claim_type='holding',institution_id=v.IID,review_state='accepted',context='collection',superseded_by=None,source_url=f['source_url'],evidence_note=v.holding_note(r,'digest')))
        return before,after

    def test_exact_successor_delta(self):
        before,after=self.delta_pair();v.assert_delta(before,after,self.records,'digest')

    def test_unselected_metadata_changes_rejected(self):
        before,after=self.delta_pair();after['artworks'][0]['title']='Changed title'
        with self.assertRaises(AssertionError):v.assert_delta(before,after,self.records,'digest')

    def test_missing_object_holding_rejected(self):
        before,after=self.delta_pair();aid=next(r['facts']['artwork_id'] for r in self.records if not r['facts']['accept_holding'])
        next(a for a in after['artworks'] if a['id']==aid)['current_institution_id']=v.IID
        with self.assertRaises(AssertionError):v.assert_delta(before,after,self.records,'digest')

    def test_display_claim_rejected(self):
        before,after=self.delta_pair();after['assertions'][-1]['display_state']='on_view'
        with self.assertRaises(AssertionError):v.assert_delta(before,after,self.records,'digest')

    def test_existing_relations_preserved(self):
        for key in ['artists','media','identifiers','citations']:
            before,after=self.delta_pair();after[key].pop(0)
            with self.subTest(key=key),self.assertRaises(AssertionError):v.assert_delta(before,after,self.records,'digest')


if __name__=='__main__':unittest.main()
