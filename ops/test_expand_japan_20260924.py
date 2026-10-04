"""Offline regression checks: never connect to a catalogue or create fixtures there."""
import copy
import importlib.util
import io
from pathlib import Path
import unittest

from PIL import Image

spec = importlib.util.spec_from_file_location('japan', Path(__file__).with_name('expand-japan-20260924.py'))
japan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(japan)


class SourceSafety(unittest.TestCase):
    def setUp(self):
        self.record = {
            'id': 1, 'title': 'Museum test object', 'department': 'Japanese Art',
            'culture': ['Japan, Edo period'], 'legal_status': 'accessioned', 'on_loan': False,
            'record_type': 'object', 'type': 'Painting', 'creation_date': '1832',
            'creation_date_earliest': 1832, 'creation_date_latest': 1832,
            'creators': [{'id': 2, 'role': 'artist', 'description': 'Named Artist (Japanese, 1790–1840)',
                'birth_year': '1790', 'death_year': '1840'}],
            'share_license_status': 'CC0', 'accession_number': '2000.1',
            'url': 'https://clevelandart.org/art/2000.1',
            'images': {'web': {'url': 'https://openaccess-cdn.clevelandart.org/2000.1/2000.1_web.jpg'}}}

    def rejected(self, change):
        record = copy.deepcopy(self.record)
        change(record)
        with self.assertRaises(ValueError):
            japan.source_facts(record)

    def test_cutoff_depends_on_artwork_date(self):
        self.rejected(lambda r: r.update(creation_date='1965–1975', creation_date_earliest=1965, creation_date_latest=1975))
        self.rejected(lambda r: r.update(creation_date_latest=None))

    def test_unknown_and_open_dates_stay_held(self):
        for text in ['undated', 'before 1840', 'after 1810', '1832?']:
            self.rejected(lambda r: r.update(creation_date=text))

    def test_conflicting_display_and_numeric_date_stay_held(self):
        self.rejected(lambda r: r.update(creation_date='late 1800s-early 1900s', creation_date_earliest=1765, creation_date_latest=1820))

    def test_posthumous_painting_needs_review(self):
        self.rejected(lambda r: r.update(creation_date='1850', creation_date_earliest=1850, creation_date_latest=1850))

    def test_attribution_and_multiple_creators_stay_held(self):
        self.rejected(lambda r: r['creators'][0].update(qualifier='attributed to'))
        self.rejected(lambda r: r['creators'].append(dict(r['creators'][0])))
        self.rejected(lambda r: r.update(creators=[]))

    def test_loan_and_multipart_are_not_accepted_holdings(self):
        self.rejected(lambda r: r.update(on_loan=True))
        self.rejected(lambda r: r.update(legal_status='loan'))
        self.rejected(lambda r: r.update(record_type='component'))

    def test_metadata_cc0_does_not_imply_image_cc0(self):
        self.rejected(lambda r: r.update(share_license_status='Copyrighted'))
        self.rejected(lambda r: r.update(copyright='Artist estate'))

    def test_wrong_object_or_external_image_is_rejected(self):
        self.rejected(lambda r: r['images']['web'].update(url='https://openaccess-cdn.clevelandart.org/2000.2/2000.2_web.jpg'))
        self.rejected(lambda r: r['images']['web'].update(url='https://example.com/2000.1/2000.1_web.jpg'))

    def test_unknown_artist_life_uses_documented_work_activity(self):
        a = {'id': 'unused', 'slug': 'unused', 'name': 'Named Artist',
             'source_maker': {'description': 'Named Artist (Japanese, active mid-1700s)'},
             'first_work': 1740, 'last_work': 1770}
        result = japan.artist_values(a)
        self.assertIsNone(result['birth_year'])
        self.assertIsNone(result['death_year'])
        self.assertEqual(result['timeline_basis'], 'activity')
        self.assertEqual((result['timeline_start_year'], result['timeline_end_year']), (1740, 1770))

    def test_uncertain_life_dates_are_not_made_exact(self):
        a = {'id': 'unused', 'slug': 'unused', 'name': 'Named Artist',
             'source_maker': {'description': 'Named Artist (Japanese, c. 1800-after 1857)', 'birth_year': '1800', 'death_year': '1857'},
             'first_work': 1840, 'last_work': 1849}
        result = japan.artist_values(a)
        self.assertEqual(result['birth_precision'], 'circa')
        self.assertIsNone(result['death_year'])
        self.assertEqual(result['timeline_basis'], 'activity')

    def test_compression_keeps_whole_frame_and_byte_budget(self):
        source = Image.effect_noise((900, 450), 80).convert('RGB')
        raw = io.BytesIO()
        source.save(raw, 'PNG')
        out, width, height = japan.compress(raw.getvalue())
        self.assertLessEqual(len(out), 100000)
        self.assertAlmostEqual(width / height, 2, places=2)
        with Image.open(io.BytesIO(out)) as result:
            self.assertEqual(result.format, 'JPEG')


if __name__ == '__main__':
    unittest.main()
