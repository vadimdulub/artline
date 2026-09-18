"""Offline checks only: never connect to any database or create test fixtures."""
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('dutch-german-museum-campaign.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


class SourceParsingTests(unittest.TestCase):
    def test_exact_and_approximate_dates(self):
        self.assertEqual(c.parse_date('1500')['precision'],'exact')
        self.assertEqual(c.parse_date('um 1475')['precision'],'circa')
        d=c.parse_date('c. 1670-1675')
        self.assertEqual((d['first'],d['last'],d['precision']),(1670,1675,'circa_range'))

    def test_uncertain_or_multiphase_dates_remain_unknown(self):
        for raw in ['1918/30','c. 1460-1464?','c. 1651-1654 and c. 1655-1658','Not stated','(1483-1520)']:
            with self.subTest(raw=raw):
                d=c.parse_date(raw)
                self.assertIsNone(d['first']);self.assertIsNone(d['last'])
                self.assertEqual(d['precision'],'unknown')

    def test_cutoff_is_not_silently_rewritten(self):
        self.assertEqual(c.parse_date('1968-1973')['last'],1973)

    def test_invalid_reverse_range_rejected(self):
        with self.assertRaises(AssertionError):c.parse_date('1675-1670')

    def test_source_collection_not_temporary_display(self):
        rows={r['native_id']:r for r in c.load(c.RUN/'parsed-objects-v2.json')}
        self.assertTrue(rows['Y0GR9B7LRX']['display_text_not_asserted'].startswith('AP '))
        self.assertEqual(rows['Y0GR9B7LRX']['institution_slug'],'neue-pinakothek')
        self.assertEqual(rows['9pL3KbKLeb']['institution_slug'],'neue-pinakothek')

    def test_qualified_creator_not_erased(self):
        rows={r['native_id']:r for r in c.load(c.RUN/'parsed-objects-v2.json')}
        self.assertIn('(and studio)',rows['264']['creator_label'])
        self.assertIn('Kopie nach',rows['5RGQ1vpGz3']['creator_label'])
        self.assertEqual(rows['5RGQ1vpGz3']['date']['display'],'Not stated')

    def test_rights_conflict_is_held(self):
        rows=[r for r in c.load(c.RUN/'parsed-objects-v2.json') if r['museum']=='mauritshuis']
        self.assertTrue(all(r['image_hold'] and r['image_url'] is None for r in rows))

    def test_geography_does_not_invent_composite_venues(self):
        plan=c.load(c.RUN/'geography-plan.json')
        self.assertEqual(len(plan['facts']),21)
        self.assertEqual(sum(r['create_venue'] for r in plan['facts']),19)
        for q in ['Q162610','Q11722011']:
            self.assertFalse(next(r for r in plan['facts'] if r['qid']==q)['create_venue'])


if __name__=='__main__':unittest.main()
