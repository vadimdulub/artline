"""Offline reproduction checks; no catalogue connections or fixtures."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('f',Path(__file__).with_name('denmark-switzerland-more-images.py'))
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

class MorePicturesTest(unittest.TestCase):
    def test_licence_scope(self):
        soup=f.b.BeautifulSoup('<table class="licensetpl"><tr><td>Public domain</td></tr></table><footer><a href="https://creativecommons.org/licenses/by-sa/4.0/">Site text licence</a></footer>','html.parser')
        e=f.file_evidence(soup)
        self.assertEqual(e['licenses'],[dict(text='Public domain',links=[])])

    def test_bounded_preview(self):
        e=dict(previews=[dict(url='https://upload.wikimedia.org/wikipedia/commons/huge.jpg',label=''),dict(url='https://thumb.wikimedia.org/wikipedia/commons/thumb/a.jpg/1280px-a.jpg',label='1,280 × 940 pixels')])
        self.assertIn('1280px',f.select_preview(e))
        with self.assertRaises(AssertionError):f.select_preview(dict(previews=e['previews'][:1]))

    def test_selected_existing_eligible_missing_only(self):
        audit=f.load(f.RUN/'audit.json')
        for target in ('local','cloud'):
            candidates={p['record']['key']:p for p in audit['targets'][target]}
            for key in f.CHOICES:
                before=candidates[key]['before']
                self.assertEqual(before['date_scope'],'eligible')
                self.assertIsNone(before['row']['primary_media_id'])
                self.assertEqual(before['row']['status'],'review')
        self.assertNotIn('basel-1569',f.CHOICES)
        self.assertNotIn('hirschsprung-wegmann-jeanna-bauck',f.CHOICES)

if __name__=='__main__':unittest.main()
