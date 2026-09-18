"""Offline-only checks; never connects to the real catalogue or inserts fixtures."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('denmark-switzerland-museums.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

class SelectedMuseumsTest(unittest.TestCase):
    def test_unknowns_and_ranges(self):
        for text in ('Undated','o. J.','1950er Jahre','1904/1906'):
            self.assertIsNone(c.parse_date(text)['first'])
        self.assertEqual(c.parse_date('1883–1886')['last'],1886)
        self.assertEqual(c.parse_date('between 1891 and 1893')['last'],1893)

    def test_file_license_not_footer(self):
        soup=c.b.BeautifulSoup('<table><tr><td>Date</td><td>1885</td></tr></table><table class="licensetpl"><tr><td>Public domain</td></tr></table><footer>Creative Commons Attribution-ShareAlike 4.0</footer>','html.parser')
        fields,licenses=c.commons_fields(soup)
        self.assertEqual(fields['Date'],'1885')
        self.assertEqual(licenses,['Public domain'])

    def test_reviewed_metadata_policy(self):
        plan=c.load(c.RUN/'metadata-plan.json');review=c.load(c.RUN/'metadata-review.json')
        self.assertEqual(c.core.sha((c.RUN/'metadata-plan.json').read_bytes()),review['plan_sha256'])
        self.assertEqual(len(review['selected_keys']),47)
        selected=[p for p in plan['targets']['local'] if p['record']['key'] in review['selected_keys']]
        self.assertEqual(sum(p['action']=='new' for p in selected),46)
        self.assertTrue(all(p['action']!='hold' for p in selected))
        self.assertNotIn('hirschsprung-eckersberg-trekroner',review['selected_keys'])
        unknown=[p for p in selected if p['record']['date']['first'] is None]
        self.assertGreater(len(unknown),0)

if __name__=='__main__': unittest.main()
