import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('split', Path(__file__).with_name('commons-photograph-licence.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class SeparatePhotographLicence(unittest.TestCase):
    def setUp(self):
        self.record = {'roles': ['primary'], 'creators': [{'name': 'Synthetic Painter', 'death': 1800}]}
        self.page = {'pageid': 10, 'revisions': [{'revid': 20, 'slots': {'main': {'*':
            '{{own}} {{PD-Art|PD-old-100-expired}} {{self|cc-by-sa-4.0}}'}}}],
            'imageinfo': [{'extmetadata': {'LicenseShortName': {'value': 'Public domain'},
                                          'Copyrighted': {'value': 'False'}}}]}

    def set_text(self, text):
        self.page['revisions'][0]['slots']['main']['*'] = text

    def test_explicit_photo_licence_is_more_restrictive_than_artwork_pdm(self):
        self.assertEqual(m.source_terms(self.record, self.page),
                         ('CC BY-SA 4.0', 'https://creativecommons.org/licenses/by-sa/4.0/'))

    def test_named_painting_and_framed_photo_sections(self):
        self.set_text('{{self-photographed}} Painting: {{pd-old-100}} Photo including frame: {{self|cc-by-3.0}}')
        self.assertEqual(m.source_terms(self.record, self.page)[0], 'CC BY 3.0')

    def art_photo(self, photo='{{cc-by-sa-4.0}}', source='{{own}}', artwork='{{PD-old-100}}'):
        return '{{Art Photo\n |source = ' + source + '\n |artwork license = ' + artwork + '\n |photo license = ' + photo + '\n}}'

    def test_art_photo_separate_explicit_fields(self):
        self.set_text(self.art_photo())
        self.assertEqual(m.source_terms(self.record, self.page), ('CC BY-SA 4.0', 'https://creativecommons.org/licenses/by-sa/4.0/'))

    def test_existing_explicit_licence_sections_keep_working_with_empty_wrapper(self):
        self.set_text('{{Art Photo\n |source = {{own}}\n |photo license =\n}}\n{{PD-Art|PD-old-100}}\n{{self|cc-by-sa-4.0}}')
        self.assertEqual(m.source_terms(self.record,self.page)[0],'CC BY-SA 4.0')

    def test_art_photo_extra_permission_terms_stay_held(self):
        for terms in ('{{NoImageNotes|Not permitted on Facebook}} {{cc-by-sa-4.0}}',
                      '{{cc-by-sa-4.0}} Noncommercial only', '{{cc-by-nc-4.0}}',
                      '{{cc-by-sa-4.0}}{{cc-by-4.0}}'):
            self.set_text(self.art_photo(photo=terms))
            with self.subTest(terms=terms), self.assertRaises(ValueError):
                m.source_terms(self.record, self.page)

    def test_art_photo_source_or_artwork_rights_cannot_be_inferred(self):
        for source, artwork in [('Museum website {{own}}', '{{PD-old-100}}'), ('{{own}}', 'Old painting')]:
            self.set_text(self.art_photo(source=source, artwork=artwork))
            with self.subTest(source=source), self.assertRaises(ValueError):
                m.source_terms(self.record, self.page)

    def test_art_photo_duplicate_or_external_fields_stay_held(self):
        for text in (self.art_photo().replace('\n}}', '\n |photo license = {{cc-by-4.0}}\n}}'),
                     self.art_photo().replace(' |photo license = {{cc-by-sa-4.0}}\n', '') + '\n |photo license = {{cc-by-sa-4.0}}\n}}'):
            self.set_text(text)
            with self.subTest(text=text), self.assertRaises(ValueError):
                m.source_terms(self.record, self.page)

    def test_licensed_pd_art_explicit_photo_parameter(self):
        self.set_text('{{own photograph}} {{Licensed-PD-art|PD-old-100-expired|cc-by-sa-4.0}}')
        self.assertEqual(m.source_terms(self.record, self.page)[0], 'CC BY-SA 4.0')

    def test_spaced_self_photographed_and_named_attribution(self):
        self.set_text('{{self photographed}} {{PD-art|PD-old}} {{self|cc-by-sa-3.0|attribution=[[User:Synthetic|Synthetic]]}}')
        self.assertEqual(m.source_terms(self.record,self.page),('CC BY-SA 3.0','https://creativecommons.org/licenses/by-sa/3.0/'))

    def test_attribution_cannot_conceal_another_licence(self):
        self.set_text('{{self photographed}} {{PD-art|PD-old}} {{self|cc-by-sa-3.0|attribution=Synthetic|cc-by-nc-4.0}}')
        with self.assertRaises(ValueError):m.source_terms(self.record,self.page)

    def test_unrecognized_photograph_source_stays_held(self):
        self.set_text('{{self photographed elsewhere}} {{PD-art|PD-old}} {{self|cc-by-sa-3.0}}')
        with self.assertRaises(ValueError):m.source_terms(self.record,self.page)

    def test_noncommercial_or_multiple_licences_are_held(self):
        for licence in ('cc-by-nc-4.0', 'cc-by-nd-4.0', 'cc-by-4.0|cc-by-sa-4.0'):
            self.set_text('{{own}} {{PD-Art|PD-old-100-expired}} {{self|' + licence + '}}')
            with self.subTest(licence=licence), self.assertRaises(ValueError):
                m.source_terms(self.record, self.page)

    def test_photo_licence_does_not_clear_a_recent_or_unknown_creator(self):
        for death in (None, 2000):
            self.record['creators'][0]['death'] = death
            with self.subTest(death=death), self.assertRaises(ValueError):
                m.source_terms(self.record, self.page)

    def test_uploader_claim_without_own_photograph_is_held(self):
        self.set_text('Uploaded by a user. {{PD-Art|PD-old-100-expired}} {{self|cc-by-4.0}}')
        with self.assertRaises(ValueError):
            m.source_terms(self.record, self.page)

    def test_missing_underlying_artwork_statement_is_held(self):
        self.set_text('{{own}} {{self|cc-by-4.0}}')
        with self.assertRaises(ValueError):
            m.source_terms(self.record, self.page)

    def test_structured_licence_must_agree_with_original_photo_terms(self):
        uri = 'https://creativecommons.org/licenses/by/4.0/'
        structured = {'claims': {'P275': [{'mainsnak': {'snaktype': 'value', 'datavalue': {'value': {'id': 'Q1'}}}}]}}
        entity = {'id': 'Q1', 'claims': {'P856': [{'mainsnak': {'snaktype': 'value', 'datavalue': {'value': uri}}}]}}
        proof = {'uri': uri, 'structured_licence_entities': {'Q1': entity}}
        m.validate_structured(proof, structured)
        proof['uri'] = 'https://creativecommons.org/licenses/by-sa/4.0/'
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            m.validate_structured(proof, structured)
        with self.assertRaisesRegex(ValueError, 'differs'):
            m.validate_structured({'uri': uri}, structured)

    def test_exact_revision_and_both_rendered_licences_required(self):
        label, uri = m.source_terms(self.record, self.page)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / 'docs/research/synthetic/capture.json'
            path.parent.mkdir(parents=True)
            parsed = {'parse': {'pageid': 10, 'revid': 20, 'text': {'*':
                f'<span class="licensetpl_link">{m.PDM}</span><span class="licensetpl_link">{uri}</span>'}}}
            path.write_text(json.dumps(parsed))
            proof = {'kind': m.KIND, 'pageid': 10, 'revid': 20, 'label': label, 'uri': uri,
                     'rendered_capture_path': str(path.relative_to(root)),
                     'capture': {'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}}
            self.assertEqual(m.validate(self.record, self.page, proof, root), (label, uri))
            changed = copy.deepcopy(proof)
            changed['revid'] = 21
            with self.assertRaises(ValueError):
                m.validate(self.record, self.page, changed, root)
            path.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                m.validate(self.record, self.page, proof, root)
            parsed['parse']['text']['*'] += '<span class="licensetpl_link">https://example.org/restricted</span>'
            path.write_text(json.dumps(parsed))
            proof['capture']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, 'conflicting'):
                m.validate(self.record, self.page, proof, root)


if __name__ == '__main__':
    unittest.main()
