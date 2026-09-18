import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location('selection', pathlib.Path(__file__).with_name('select-book-covers.py'))
selection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selection)


class CoverRightsTests(unittest.TestCase):
    def candidate(self, categories, license_name='Public domain', restrictions=''):
        candidate = {'bookId': 'book', 'sourceId': 'Q1', 'file': 'A book cover.jpg', 'workEvidence': {'revision': 1}}
        fields = {'Categories': categories, 'LicenseShortName': license_name, 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0/',
                  'DateTimeOriginal': '1900', 'Artist': 'The cover designer', 'Credit': 'Own scan of the 1900 edition', 'Restrictions': restrictions}
        info = {'mime': 'image/jpeg', 'url': 'https://upload.wikimedia.org/wikipedia/commons/a/ab/Cover.jpg',
                'descriptionurl': 'https://commons.wikimedia.org/wiki/File:Cover.jpg', 'extmetadata': {k: {'value': v} for k, v in fields.items()}}
        return candidate, {'page': {'imageinfo': [info]}, 'evidenceFile': 'saved-response.gz', 'evidenceSha256': 'checksum'}

    def test_photographer_release_does_not_clear_underlying_cover(self):
        for license_name in ['Public domain', 'CC BY-SA 4.0']:
            result, reason = selection.classify(*self.candidate('Book covers|Self-published work|PD-self', license_name))
            self.assertIsNone(result)
            self.assertEqual(reason, 'underlying-design-rights-not-established')

    def test_pd_design_preserves_separate_photograph_attribution(self):
        result, _ = selection.classify(*self.candidate('Book covers|PD-old-100-expired', 'CC BY-SA 4.0'))
        cover, basis = result
        self.assertEqual(cover['license'], 'CC BY-SA 4.0')
        self.assertEqual(cover['credit'], 'The cover designer')
        self.assertEqual(basis['work']['revision'], 1)

    def test_disputed_and_restricted_images_are_held(self):
        for categories, restrictions in [('PD-old-100-expired|Items with disputed copyright information', ''), ('PD-old-100-expired', 'noncommercial')]:
            result, reason = selection.classify(*self.candidate(categories, restrictions=restrictions))
            self.assertIsNone(result)
            self.assertEqual(reason, 'rights-warning-or-restriction')

    def test_illustration_is_not_automatically_a_cover(self):
        candidate, result = self.candidate('PD-old-100-expired|Portraits')
        candidate['file'] = 'Portrait of the author.jpg'
        self.assertEqual(selection.classify(candidate, result)[1], 'image-not-identified-as-cover-or-title-page')

    def test_missing_source_and_unlicensed_metadata_are_held(self):
        candidate, result = self.candidate('PD-old-100-expired')
        self.assertEqual(selection.classify(candidate, {})[1], 'source-metadata-unavailable')
        result['page']['imageinfo'][0]['extmetadata']['LicenseShortName']['value'] = 'All rights reserved'
        self.assertEqual(selection.classify(candidate, result)[1], 'unsupported-reproduction-license')

    def test_public_domain_is_not_custodian_commercial_permission(self):
        for credit, reason in [('Source gallica.bnf.fr', 'bnf-commercial-reuse-needs-clearance'), ('Biblioteca Nazionale Braidense', 'italian-custodian-permission-needs-review'), ('', 'reproduction-origin-not-established')]:
            candidate, result = self.candidate('Book covers|PD-old-100-expired')
            result['page']['imageinfo'][0]['extmetadata']['Credit']['value'] = credit
            self.assertEqual(selection.classify(candidate, result)[1], reason)


if __name__ == '__main__':
    unittest.main()
