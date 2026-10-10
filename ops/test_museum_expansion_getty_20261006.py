"""Offline Getty evidence checks; no catalogue connection or inserted fixtures."""
import copy
import gzip
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('getty',Path(__file__).with_name('museum-expansion-getty-20261006.py'))
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)


class GettyPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def raw(url):
            return gzip.decompress((g.m.RUN/'getty-probes'/(hashlib.sha256(url.encode()).hexdigest()+'.body.gz')).read_bytes())
        cls.obj=json.loads(raw(g.API+'object/ff75c037-5ee4-4afa-b4a0-6264b7a58b6a'))
        cls.html=g.html_fields(raw(g.SITE+'/object/103RE7'))
        cls.index=json.loads(raw(g.SITE+'/api/search?from=0&size=5&department=Paintings'))['data'][0]

    def test_current_circle_attribution_kept_despite_bare_native_creator(self):
        facts,reason=g.facts(self.obj,self.index,self.html)
        self.assertIsNone(reason)
        self.assertEqual(facts['creator_label'],'Circle of Antonis Mor van Dashorst (Flemish, 1516 - 1576)')
        self.assertEqual((facts['first'],facts['last'],facts['date_precision']),(1558,1558,'exact'))

    def test_old_attribution_event_dates_do_not_become_creation(self):
        obj=copy.deepcopy(self.obj)
        obj['produced_by']['assigned_by'][0]['timespan']['begin_of_the_begin']='1999-01-01T00:00:00'
        facts,reason=g.facts(obj,self.index,self.html)
        self.assertIsNone(reason);self.assertEqual(facts['first'],1558)

    def test_unverified_current_owner_not_replaced_with_exhibition_membership(self):
        obj=copy.deepcopy(self.obj);obj['current_owner']=[]
        self.assertEqual(g.facts(obj,self.index,self.html)[1],'current_getty_ownership_not_confirmed')

    def test_missing_keeper_and_deaccessioned_objects_held(self):
        obj=copy.deepcopy(self.obj);obj['current_keeper']=[]
        self.assertEqual(g.facts(obj,self.index,self.html)[1],'current_paintings_department_not_confirmed')
        obj=copy.deepcopy(self.obj);obj['classified_as'].append({'id':g.LOCAL+'deaccessioned','_label':'Deaccessioned'})
        self.assertEqual(g.facts(obj,self.index,self.html)[1],'deaccession_requires_review')

    def test_native_identity_and_inventory_conflicts_held(self):
        html=copy.deepcopy(self.html);html['identity']['indexedId']='object/different'
        self.assertEqual(g.facts(self.obj,self.index,html)[1],'native_api_identity_conflict')
        html=copy.deepcopy(self.html);html['object']['identifier']=['other inventory']
        self.assertEqual(g.facts(self.obj,self.index,html)[1],'source_inventory_conflict')

    def test_components_and_separate_production_phases_held(self):
        obj=copy.deepcopy(self.obj);obj['part_of']=[{'id':'another object'}]
        self.assertEqual(g.facts(obj,self.index,self.html)[1],'component_or_ensemble_requires_review')
        obj=copy.deepcopy(self.obj);obj['produced_by']['part']=[{'timespan':{'begin_of_the_begin':'1960-01-01T00:00:00'}}]
        self.assertEqual(g.facts(obj,self.index,self.html)[1],'multiple_production_phases_require_review')

    def test_missing_creation_cannot_use_acquisition_or_lifespan(self):
        obj=copy.deepcopy(self.obj);obj['produced_by'].pop('timespan')
        self.assertEqual(g.facts(obj,self.index,self.html)[1],'production_date_requires_review')

    def test_circa_uses_only_source_explicit_outer_bounds(self):
        production={'timespan':{'identified_by':[{'content':'about 1650','classified_as':[{'id':g.AAT+'300458798'}]}],
          'begin_of_the_begin':'1645-01-01T00:00:00','end_of_the_end':'1655-12-31T23:59:59'}}
        self.assertEqual(g.source_dates(production,'about 1650'),(1645,1655,'circa_range'))
        production['timespan']['end_of_the_end']='1971-12-31T23:59:59'
        self.assertIsNone(g.source_dates(production,'about 1650'))

    def test_unknown_conflicting_and_ambiguous_dates_held(self):
        for literal in ['','unknown','1558 or 1560','after 1558','1960–1980','about 1970','1700–1600']:
            with self.subTest(literal=literal):self.assertIsNone(g.display_date(literal))
        obj=copy.deepcopy(self.obj);obj['produced_by']['timespan']['end_of_the_end']='1559-12-31T23:59:59'
        self.assertEqual(g.facts(obj,self.index,self.html)[1],'production_date_requires_review')

    def test_qualified_period_keeps_api_bounds_not_a_guessed_subperiod(self):
        production={'timespan':{'identified_by':[{'content':'late 1420s','classified_as':[{'id':g.AAT+'300458798'}]}],
          'begin_of_the_begin':'1427-01-01T00:00:00','end_of_the_end':'1429-12-31T23:59:59'}}
        self.assertEqual(g.source_dates(production,'late 1420s'),(1427,1429,'range'))
        production['timespan']['begin_of_the_begin']='1410-01-01T00:00:00'
        self.assertIsNone(g.source_dates(production,'late 1420s'))
        for value in ['1980s','late 20th century','after 1600','1647 ?', 'late 1420s or early 1430s']:
            with self.subTest(value=value):self.assertIsNone(g.display_date(value))


if __name__=='__main__':unittest.main()
