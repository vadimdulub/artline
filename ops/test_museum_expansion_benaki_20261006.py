"""Offline checks against preserved native Benaki object descriptions."""
import importlib.util
import copy
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('benaki',Path(__file__).with_name('museum-expansion-benaki-20261006.py'))
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)


class BenakiPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records={r['source_record_id']:r for r in b.m.load(b.RUN/'byzantine-reviewed-statements-001.json')['records']}
        cls.captures={r['item']['source_id']:r for r in b.m.load(b.RUN/'byzantine-objects-001.json.gz')['records']}
        cls.next_records={r['source_record_id']:r for r in b.m.load(b.RUN/'byzantine-reviewed-statements-002.json')['records']}

    def test_creation_is_separate_from_lifespan(self):
        r=self.records['108387'];f=b.facts(r['native_fields'],r['review'],r['source']['receipt']['url'])
        self.assertEqual((f['first'],f['last']),(1817,1817))
        self.assertIn('πιθανώς',f['creator_label']);self.assertIn('1779-1844',f['creator_label'])
        self.assertIsNone(b.reviewed_date(r['native_fields']['description']))

    def test_style_attribution_is_not_changed_to_named_authorship(self):
        r=self.records['107487'];f=r['facts']
        self.assertEqual((f['first'],f['last']),(1751,1800))
        self.assertIn('σύμφωνα με το ύφος',f['creator_label'])
        self.assertIn('1620-1692',f['creator_label'])

    def test_commissioner_and_donor_are_not_assigned_as_creator(self):
        self.assertIsNone(self.records['108339']['facts']['creator_label'])
        self.assertIn('ιατρού Φιοροβάντε Κρασσά',self.records['108339']['native_fields']['description'])
        self.assertIsNone(self.records['108423']['facts']['creator_label'])

    def test_literal_dimension_typo_is_not_silently_corrected(self):
        self.assertEqual(self.records['108495']['facts']['dimensions'],'0,39x30,2 μ.')

    def test_native_language_identity_and_inventory_prefix(self):
        self.assertEqual(self.records['108387']['native_fields']['language_variant_ids'],['108388'])
        self.assertEqual(b.inventory_keys('ΓΕ_11198'),b.inventory_keys('GE 11198'))
        self.assertEqual(b.inventory_keys('11198'),b.inventory_keys('ΓΕ 11198'))
        self.assertNotEqual(b.inventory_keys('ΓΕ 34585α'),b.inventory_keys('ΓΕ 34585'))

    def test_icon_filter_does_not_make_a_silver_cover_a_painting(self):
        r=self.captures['108477'];p=b.fields(b.read_capture(r['source']))
        review=dict(creation_statement='1800',creator_statement=None,dimensions_statement='Ύψ. 0,77 μ.',medium_statement=None,accession='ΓΕ 34585α',work_type='painting',object_form='icon')
        with self.assertRaises(AssertionError):b.facts(p,review,r['source']['receipt']['url'])

    def test_unreviewed_qualifiers_and_cutoff_held(self):
        for value in ['1971','20ος αι.','Αρχές 20ου αι.','1960-1980','17ος (;) αι.','Γύρω στο 1970']:
            with self.subTest(value=value):self.assertIsNone(b.reviewed_date(value))

    def test_early_century_does_not_invent_early_cutoff(self):
        r=self.next_records['108399'];f=r['facts']
        self.assertEqual((f['first'],f['last'],f['date_precision']),(1801,1900,'century'))
        self.assertEqual(f['date_display'],'Αρχές 19ου αι.')
        r=self.next_records['108723'];self.assertEqual(r['facts']['date_display'],'Αρχές 18ου αιώνα.')
        self.assertEqual(b.reviewed_date(r['review']['creation_statement']),(1701,1800,'century'))

    def test_circa_keeps_central_year_and_precision(self):
        r=self.next_records['107535'];f=r['facts']
        self.assertEqual((f['first'],f['last'],f['date_precision']),(1600,1600,'circa'))
        self.assertEqual(f['date_display'],'Γύρω στo 1600')

    def test_depicted_event_does_not_supply_creation_year(self):
        r=self.next_records['108276'];self.assertIn('843',r['native_fields']['description'])
        self.assertEqual((r['facts']['first'],r['facts']['last']),(1501,1600))

    def test_prototype_date_is_separate_from_icon_creation(self):
        r=self.next_records['108633'];self.assertIn('16ου αι.',r['native_fields']['description'])
        self.assertEqual((r['facts']['first'],r['facts']['last']),(1701,1800))

    def test_false_signature_and_date_do_not_become_authorship_or_creation(self):
        r=self.next_records['107607'];f=r['facts']
        self.assertIn('1637',r['native_fields']['description']);self.assertIn('20ού αι.',r['native_fields']['description'])
        self.assertEqual((f['first'],f['last']),(1401,1500))
        self.assertIn('Aγγέλου (;)',f['creator_label']);self.assertNotIn('Tζάνε',f['creator_label'])

    def test_single_panel_requires_recorded_scope_review(self):
        r=self.next_records['108714'];review=copy.deepcopy(r['review']);review.pop('object_scope_review')
        with self.assertRaises(AssertionError):b.facts(r['native_fields'],review,r['source']['receipt']['url'])
        self.assertEqual(b.facts(r['native_fields'],r['review'],r['source']['receipt']['url']),r['facts'])

    def test_reused_chest_support_does_not_mean_fragmentary_painting(self):
        r=self.next_records['107583'];self.assertEqual((r['facts']['first'],r['facts']['last']),(1565,1567))
        review=copy.deepcopy(r['review']);review.pop('support_scope_review')
        with self.assertRaises(AssertionError):b.facts(r['native_fields'],review,r['source']['receipt']['url'])

    def test_double_encoded_header_agrees_with_native_literal_title(self):
        r=self.next_records['108279'];self.assertIn('&quot;',r['native_fields']['page_title'])
        self.assertIn('"Madre della Consolazione"',r['facts']['title'])
        self.assertEqual(b.facts(r['native_fields'],r['review'],r['source']['receipt']['url']),r['facts'])


if __name__=='__main__':unittest.main()
