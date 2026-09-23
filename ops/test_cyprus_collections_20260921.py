"""Evidence/parser checks only. Never creates a database or inserts fixtures."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('cyprus_apply',Path(__file__).with_name('cyprus-collections-20260921-apply.py'))
apply=importlib.util.module_from_spec(spec);spec.loader.exec_module(apply)
review=apply.review


class CyprusEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan,_=apply.load()
        cls.works={w['key']:w for w in cls.plan['works']}

    def test_date_cases(self):
        cases=[('',None,None,'unknown'),('1544 μ.Χ',1544,1544,'exact'),('Circa 1183 Γύρω στο 1183',1183,1183,'circa'),
          ('1814 1814',1814,1814,'exact'),('13th century',1201,1300,'century'),('16ος αι. μ.Χ.',1501,1600,'century'),
          ('18th century 18ος αιώνας',1701,1800,'century'),('Αρχές 16ου αιώνα',1501,1600,'century'),
          ('17-18ος αιώνας',1601,1800,'range'),('18th-19th century',1701,1900,'range'),
          ('First quarter of the 12th century',1101,1200,'century'),('1183 and 1503',None,None,'unknown')]
        for value,first,last,precision in cases:
            with self.subTest(value=value):
                d=review.dated(value);self.assertEqual((d['first'],d['last'],d['precision']),(first,last,precision))

    def test_photographic_dates_are_not_creation_dates(self):
        for w in self.plan['works']:
            if w['key'].startswith('apsida-45'):
                with self.subTest(key=w['key']):self.assertNotEqual(w['date']['first'],2006)

    def test_archive_creators_are_not_artists(self):
        names=[a['name'] for a in self.plan['artists']]
        self.assertNotIn('Ioannides, Marinos',names)
        self.assertNotIn('Holy Monastery of Saint Neophytos',names)

    def test_restoration_does_not_become_creation(self):
        for ident in (12196,12197,13555,13562):
            with self.subTest(id=ident):self.assertEqual(self.works[f'apsida-{ident}']['date']['precision'],'unknown')

    def test_conflicting_dates_remain_unknown(self):
        for ident in (15180,45338):
            with self.subTest(id=ident):self.assertIsNone(self.works[f'apsida-{ident}']['date']['first'])

    def test_aliases_do_not_create_duplicate_works(self):
        for alias,target in review.ALIASES.items():
            with self.subTest(alias=alias):
                self.assertNotIn(f'apsida-{alias}',self.works)
                self.assertIn(alias,[x['id'] for x in self.works[f'apsida-{target}']['additional_sources']])

    def test_named_iconographer_and_anonymous_paintings(self):
        self.assertEqual(self.works['apsida-15162']['creator'],'Joseph Chourri')
        self.assertEqual(self.works['apsida-45226']['creator'],'Asinou Master')
        self.assertEqual(self.works['apsida-21944']['creator_label'],'Unidentified painter')
        self.assertIsNone(self.works['apsida-21944']['artist_id'])

    def test_style_of_is_not_primary_attribution(self):
        w=self.works['apsida-20096'];self.assertEqual(w['creator_label'],'In the style of Panaretos');self.assertIsNone(w['artist_id'])

    def test_mural_and_icon_classification(self):
        self.assertEqual(self.works['apsida-15548']['work_type'],'fresco')
        self.assertIsNone(self.works['apsida-15548']['object_form'])
        self.assertEqual(self.works['apsida-21942']['object_form'],'icon')

    def test_holding_does_not_imply_production(self):
        self.assertIsNone(self.works['apsida-21942']['creation_country'])
        self.assertEqual(self.works['apsida-45226']['creation_country'],'CY')

    def test_multi_scene_object_remains_one_record(self):
        self.assertIn('Betrayal',self.works['apsida-45288']['title'])
        self.assertIn('Crucifixion',self.works['apsida-45288']['title'])

    def test_xeni_exhibition_and_permanent_membership_are_distinct(self):
        works=[w for w in self.plan['works'] if w['institution']=='xeniartspace']
        self.assertEqual(len(works),5)
        self.assertTrue(all('exhibition' in w['connection'] for w in works))
        self.assertFalse(any(w['creator']=='Anish Kapoor' for w in works))
        self.assertFalse(any(w['creator']=='Tracey Emin' for w in works))

    def test_source_birth_conflicts_remain_unknown(self):
        for a in self.plan['artists']:
            if a['name'] in ('Andreas Charalambides','George Kotsonis'):
                self.assertIsNone(a['birth']);self.assertIsNone(a['death']);self.assertEqual(a['basis'],'activity')

    def test_international_exhibitor_is_not_cypriot(self):
        a=next(a for a in self.plan['artists'] if a['name']=='Lydia Masterkova');self.assertIsNone(a['relationship'])

    def test_country_relationships_preserve_activity(self):
        for name in ('Glyn Hughes','Susan Kerr','Anastasia Krivenko','Nata Chebarkova'):
            with self.subTest(name=name):self.assertEqual(next(a['relationship'] for a in self.plan['artists'] if a['name']==name),'active')

    def test_capture_checksums_and_plan_invariants(self):
        apply.validate_plan(self.plan)

    def test_reject_later_artwork(self):
        p=copy.deepcopy(self.plan);p['works'][0]['date']=dict(first=1987,last=1987,display='1987',precision='exact')
        with self.assertRaises(AssertionError):apply.validate_plan(p)

    def test_reject_duplicate_ids(self):
        p=copy.deepcopy(self.plan);p['works'].append(p['works'][0])
        with self.assertRaises(AssertionError):apply.validate_plan(p)

    def test_reject_missing_evidence(self):
        p=copy.deepcopy(self.plan);p['works'][0]['receipt']['sha256']='invalid'
        with self.assertRaises(AssertionError):apply.validate_plan(p)

    def test_reject_unresolved_identity_conflicts(self):
        p=copy.deepcopy(self.plan);p['decisions'].append({'decision':'identity_check'})
        with self.assertRaises(AssertionError):apply.validate_plan(p)

    def test_reject_publication_or_remote_target(self):
        for field,value in [('status','published'),('local_only',False)]:
            with self.subTest(field=field):
                p=copy.deepcopy(self.plan);p[field]=value
                with self.assertRaises(AssertionError):apply.validate_plan(p)


if __name__=='__main__':unittest.main(verbosity=2)
