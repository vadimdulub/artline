import unittest
from expanded_object_identity import find_conflicts


class MuseumObjectIdentityTests(unittest.TestCase):
    def check_pair(self, url, other_url, identifier='1', other_id='2'):
        plan = [{'rid': 'record', 'slug': 'candidate', 'evidence': {'object_url': url, 'object_id': identifier}}]
        existing = [{'slug': 'existing', 'scheme': 'museum-object', 'id': other_id, 'url': other_url}]
        return find_conflicts(plan, existing, ['americanart.si.edu', 'rijksmuseum.nl'])

    def test_distinct_query_string_object_ids_are_distinct_objects(self):
        self.assertFalse(self.check_pair('https://americanart.si.edu/artwork/?id=1', 'https://americanart.si.edu/artwork/?id=2'))

    def test_same_query_identity_survives_scheme_and_www_variants(self):
        self.assertTrue(self.check_pair('https://www.americanart.si.edu/artwork/?id=1', 'http://americanart.si.edu/artwork?id=1'))

    def test_same_source_id_survives_different_url_shapes(self):
        self.assertTrue(self.check_pair('https://americanart.si.edu/artwork/?id=1', 'https://americanart.si.edu/artwork/a-title-1', other_id='1'))

    def test_numeric_identifiers_are_scoped_to_museum(self):
        self.assertFalse(self.check_pair('https://americanart.si.edu/artwork/?id=1', 'https://id.rijksmuseum.nl/1', other_id='1'))

    def test_domain_text_in_path_is_not_source_identity(self):
        self.assertFalse(self.check_pair('https://americanart.si.edu/artwork/?id=1', 'https://example.org/americanart.si.edu/1', other_id='1'))


if __name__ == '__main__':
    unittest.main()
