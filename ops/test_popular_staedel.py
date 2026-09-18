"""Synthetic rights/identity boundaries; no live catalogue or network access."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('staedel', Path(__file__).with_name('popular-staedel-images.py'))
s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
PAGE = s.HOST + '/en/work/synthetic-painting'
DOWNLOAD = [{'action': 'layer', 'content': f'''<form action="{PAGE}/download">
<input name="_token" value="synthetic-session-token">
<p>Reproductions may be used <a href="{s.PDM}">public-domain</a> without restrictions.</p>
<p>{s.CREDIT}</p><input name="files[]" value="1234abcd"></form>'''}]


class DownloadRights(unittest.TestCase):
    def test_exact_image_statement_retains_no_session_token(self):
        result = s.parse_download(DOWNLOAD, PAGE)
        self.assertEqual(result['licence_uri'], s.PDM)
        self.assertNotIn('synthetic-session-token', str(result))

    def test_another_object_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'another object'):
            s.parse_download(DOWNLOAD, PAGE + '-other')

    def test_noncommercial_statement_is_rejected(self):
        d = copy.deepcopy(DOWNLOAD); d[0]['content'] = d[0]['content'].replace('without restrictions.', 'without restrictions. Non-commercial only.')
        with self.assertRaisesRegex(ValueError, 'restriction'):
            s.parse_download(d, PAGE)

    def test_metadata_cc0_is_not_image_pdm(self):
        d = copy.deepcopy(DOWNLOAD); d[0]['content'] = d[0]['content'].replace(s.PDM, 'https://creativecommons.org/publicdomain/zero/1.0/')
        with self.assertRaises(ValueError): s.parse_download(d, PAGE)

    def test_multiple_images_require_review(self):
        d = copy.deepcopy(DOWNLOAD); d[0]['content'] = d[0]['content'].replace('</form>', '<input name="files[]" value="5678abcd"></form>')
        with self.assertRaisesRegex(ValueError, 'Ambiguous'): s.parse_download(d, PAGE)


class SourceObject(unittest.TestCase):
    def setUp(self):
        self.image = 'https://cdn.staedelmuseum.de/images/ab/cd/1234/thumb-xl.jpg'
        fields = {'Title': 'Synthetic painting', 'Painter': 'Synthetic painter', 'Inventory Number': '1234',
                  'Object Type': 'painting (artwork)', 'Institution': 'Städel Museum', 'Creditline': s.CREDIT, 'Picture Copyright': 'Public Domain'}
        self.html = f'''<meta property="og:url" content="{PAGE}"><meta property="og:image" content="{self.image}">
<h1><span class="dsArtwork__titleCaption">Synthetic painting</span><span class="dsArtwork__titleYear">, 1800 – 1801</span></h1>
<img src="{self.image}" alt="Synthetic painting, Synthetic painter"><button data-action="download" data-target="{PAGE}/download"></button>'''
        self.html += ''.join(f'<dl class="dsProperty"><dt>{k}</dt><dd>{v}</dd></dl>' for k, v in fields.items())

    def test_published_full_frame_primary(self):
        self.assertEqual(s.parse_object(self.html, PAGE)['year_end'], 1801)

    def test_unrelated_hero_image_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'accession'):
            s.parse_object(self.html.replace('/1234/', '/5678/'), PAGE)

    def test_unknown_date_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'date'):
            s.parse_object(self.html.replace('1800 – 1801', 'unknown'), PAGE)

    def test_square_crop_is_rejected(self):
        with self.assertRaises(ValueError):
            s.parse_object(self.html.replace('thumb-xl.jpg', 'square-lg.jpg'), PAGE)

    def test_conflicting_acc_numbers_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            s.parse_object(self.html + '<dl class="dsProperty"><dt>Inventory Number</dt><dd>9876</dd></dl>', PAGE)


if __name__ == '__main__': unittest.main()
