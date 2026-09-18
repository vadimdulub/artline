import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('descriptions', Path(__file__).with_name('research-event-descriptions.py'))
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class DescriptionsTest(unittest.TestCase):
    def test_two_sentences_and_whitespace(self):
        self.assertEqual(d.short_intro('First event.\n\nSecond event. Third event.'), 'First event. Second event.')

    def test_initials_and_abbreviations(self):
        self.assertEqual(d.short_intro('Dr. Smith met J. R. Jones. They signed a treaty. More happened.'), 'Dr. Smith met J. R. Jones. They signed a treaty.')

    def test_long_source_is_bounded_without_word_cut(self):
        result = d.short_intro('Historic ' * 300)
        self.assertLessEqual(len(result), 850)
        self.assertTrue(result.endswith('Historic…'))
        self.assertEqual(d.short_intro(''), '')

    def test_parenthetic_abbreviations_do_not_cut_a_sentence(self):
        text = 'A war (Thai: พ.ศ. 2376 – พ.ศ. 2377) occurred. Another sentence. Rest.'
        self.assertEqual(d.short_intro(text), 'A war (Thai: พ.ศ. 2376 – พ.ศ. 2377) occurred. Another sentence.')

    def test_existing_description_is_retained_as_metadata(self):
        self.assertEqual(d.metadata_description({'description': 'battle in 1700'}, {}), 'Battle in 1700.')

    def test_unknown_description_only_uses_source_class_and_dates(self):
        record = {'title': 'Example culture', 'description': '', 'kind': 'Period', 'years': 'c. 1000 BCE–500 BCE'}
        text = d.metadata_description(record, {'roots': ['Archaeological culture']})
        self.assertIn('an archaeological culture', text)
        self.assertIn(record['years'], text)
        self.assertNotIn('civilisation', text)


if __name__ == '__main__': unittest.main()
