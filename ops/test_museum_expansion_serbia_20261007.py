"""Offline checks of retained real museum metadata. No database fixtures."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-serbia-vr-20261007.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
s=v.s
spec=importlib.util.spec_from_file_location('report',Path(__file__).with_name('museum-expansion-serbia-report-20261007.py'))
report=importlib.util.module_from_spec(spec);spec.loader.exec_module(report)
spec=importlib.util.spec_from_file_location('apply_serbia',Path(__file__).with_name('museum-expansion-serbia-apply-20261007.py'))
apply_serbia=importlib.util.module_from_spec(spec);spec.loader.exec_module(apply_serbia)


class SerbiaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gallery=s.m.load(s.RUN/'serbia-caption-001-research.json.gz')
        cls.vr=s.m.load(s.RUN/'serbia-vr-001-research.json.gz')

    def test_gallery_capture_roundtrip(self):
        self.assertEqual(len(self.gallery['records']),83)
        self.assertEqual(len(self.gallery['held']),24)
        for r in self.gallery['records']:
            raw=s.captured_body(dict(receipt=r['source_receipt'],body_path=r['body_path']))
            self.assertEqual(s.validate_record(r,raw),r['facts'])

    def test_virtual_object_and_museum_link_roundtrip(self):
        self.assertEqual(len(self.vr['records']),30)
        self.assertEqual(len(self.vr['held']),16)
        for r in self.vr['records']:
            raw=s.captured_body(dict(receipt=r['source_receipt'],body_path=r['body_path']))
            self.assertEqual(v.validate_record(r,raw),r['facts'])

    def test_prototypes_do_not_date_modern_fresco_copies(self):
        held={h['number']:h for h in self.gallery['held']}
        for num in range(94,108):self.assertEqual(held[num]['reason'],'modern_copy_creation_date_missing')
        original=next(r for r in self.gallery['records'] if r['raw_source_record']['queue_number']==91)
        self.assertEqual(original['facts']['work_type'],'fresco')
        self.assertEqual((original['facts']['first'],original['facts']['last']),(1301,1400))

    def test_unbounded_dates_and_cutoff_are_not_guessed(self):
        for value in ['After 1910','Posle 1890.','20. век','1971','1968-1972','око 1970','']:
            self.assertIsNone(v.dates(value),value)
        self.assertEqual(v.dates('Oko 1897.'),(1897,1897,'circa'))
        self.assertEqual(s.creation_date('1882–83'),(1882,1883,'range'))
        self.assertEqual(s.creation_date('средина 14. века'),(1301,1400,'century'))
        self.assertEqual(s.creation_date('прва четвртина 15. века'),(1401,1425,'range'))

    def test_repeated_views_components_and_contaminated_narrative_are_held(self):
        self.assertTrue({79,80,81}<={h['number'] for h in self.gallery['held']})
        ids={h['source_record_id'] for h in self.vr['held']}
        self.assertTrue(set(v.HOLDS)<=ids)

    def test_study_and_full_portrait_have_distinct_physical_formats(self):
        records={r['source_record_id']:r for r in self.vr['records']}
        study=records['vr-5PHEKGrvXYFQQfvbu'];full=records['vr-LvFtYJitunPAhuk4T']
        self.assertEqual(study['facts']['dimensions'],'height 82 × width 66 cm')
        self.assertEqual(full['facts']['dimensions'],'height 214 × width 131 cm')
        self.assertIn('pripremnu studiju',study['raw_source_record']['native_object']['shrFullDescription'])

    def test_explicit_approximation_survives_schema_year(self):
        r=next(r for r in self.vr['records'] if r['source_record_id']=='vr-8M3EpxiR3LMgSe899')
        self.assertEqual(r['facts']['date_display'],'Oko 1900')
        self.assertEqual(r['facts']['date_precision'],'circa')
        self.assertEqual(r['raw_source_record']['native_object']['creationDate']['year'],'1900')

    def test_replica_retains_its_own_creation_date(self):
        r=next(r for r in self.vr['records'] if r['source_record_id']=='vr-i2LBMg4pfNchNAbFG')
        self.assertEqual(r['facts']['first'],1925)
        self.assertIn('1884',r['raw_source_record']['native_object']['shrFullDescription'])

    def test_exhibition_alone_does_not_assign_paja_holdings(self):
        h=next(h for h in self.vr['held'] if h['source_record_id']=='2pWAjaaewHEH4aW7c')
        self.assertEqual(h['reason'],'individual_collection_holding_requires_review')

    def test_image_keys_and_report_comparisons_are_not_accessions(self):
        self.assertTrue(all(r['facts']['accession'] is None for r in self.gallery['records']+self.vr['records']))
        self.assertTrue(any('annual_report_comparison' in r['raw_source_record'] for r in self.vr['records']))

    def test_changed_object_or_gallery_caption_rejected(self):
        for original,validator in [(self.gallery['records'][0],s.validate_record),(self.vr['records'][0],v.validate_record)]:
            r=copy.deepcopy(original);raw=s.captured_body(dict(receipt=r['source_receipt'],body_path=r['body_path']))
            if 'gallery_entry' in r['raw_source_record']:r['raw_source_record']['gallery_entry']['caption']='changed'
            else:r['raw_source_record']['native_object']['shrTitle']='changed'
            with self.assertRaises(AssertionError):validator(r,raw)

    def test_report_preserves_inventories_and_unknown_types(self):
        research=s.m.load(s.RUN/'serbia-report-001-research.json.gz')
        self.assertEqual(len(research['records']),21)
        self.assertEqual(len(research['held']),3)
        raw=report.PDF.read_bytes()
        for r in research['records']:
            self.assertEqual(report.validate_record(r,raw),r['facts'])
            self.assertEqual(r['facts']['work_type'],'unknown')
            self.assertIsNone(r['facts']['medium'])
            self.assertIn('2015',r['facts']['holding_basis'])
        qualified=next(r for r in research['records'] if r['facts']['accession']=='НМ 1093')
        self.assertEqual(qualified['facts']['creator_label'],'Урош Кнежевић (?)')

    def test_report_does_not_create_overlap_records_or_date_from_exhibition(self):
        research=s.m.load(s.RUN/'serbia-report-001-research.json.gz')
        held={h['source_record_id']:h['reason'] for h in research['held']}
        self.assertEqual(held['report-2015-p55-pupin-3'],'creation_date_requires_review')
        for n in [6,7]:self.assertEqual(held['report-2015-p55-pupin-'+str(n)],'gallery_or_virtual_identity_overlap')
        self.assertTrue(all(r['facts']['last']<1910 for r in research['records']))

    def test_diacritic_variants_find_existing_paja_pool(self):
        comparisons=s.m.load(s.RUN/'creator-title-comparison-leads-002.json.gz')['records']
        row=next(r for r in comparisons if r['source_record_id']=='vr-i2LBMg4pfNchNAbFG')
        self.assertGreaterEqual(row['pool_size'],2)
        self.assertIn('paja jovanovic',row['search_names'])

    def test_pinned_plan_contains_only_the_individually_reviewed_subset(self):
        plan,digest=apply_serbia.validate_plan()
        self.assertEqual(len(plan['records']),115)
        self.assertEqual(len(plan['held']),62)
        self.assertEqual(len(digest),64)
        ids={r['source_record_id'] for r in plan['records']}
        for held in s.m.load(s.RUN/'editorial-triage-001.json')['decisions']:
            self.assertEqual(held['source_record_id'] in ids,held['decision']=='reviewed_candidate_pending_import_plan')

    def test_held_or_duplicated_record_cannot_be_sneaked_into_plan(self):
        plan=s.m.load(apply_serbia.PLAN);plan['records'][0]=copy.deepcopy(plan['records'][1])
        with self.assertRaises(AssertionError):apply_serbia.validate(plan)

    def test_final_date_cannot_disagree_with_source_or_review(self):
        plan=s.m.load(apply_serbia.PLAN);plan['records'][0]['facts']['first']=1971
        with self.assertRaises(AssertionError):apply_serbia.validate(plan)

    def test_new_or_changed_catalogue_identity_requires_fresh_review(self):
        expected=s.m.load(apply_serbia.IDENTITY)
        actual={k:copy.deepcopy(expected[k]) for k in ['artists','aliases','linked','unlinked','collisions']}
        apply_serbia.check_identity_snapshot(actual,expected)
        actual['linked'][0]['title']='Changed title'
        with self.assertRaisesRegex(AssertionError,'New or changed linked'):
            apply_serbia.check_identity_snapshot(actual,expected)

    def test_inventory_prefix_does_not_hide_duplicate_object(self):
        self.assertEqual(apply_serbia.inventory_keys('НМ 889'),apply_serbia.inventory_keys('889'))
        self.assertEqual(apply_serbia.inventory_keys('NM 889'),apply_serbia.inventory_keys('НМ 889'))
        self.assertNotEqual(apply_serbia.inventory_keys('НМ ЈВ 190'),apply_serbia.inventory_keys('190'))


if __name__=='__main__':unittest.main()
