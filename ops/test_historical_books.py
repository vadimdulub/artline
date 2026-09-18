import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location('books_research', pathlib.Path(__file__).with_name('research-historical-books.py'))
books = importlib.util.module_from_spec(spec)
spec.loader.exec_module(books)


class HistoricalDates(unittest.TestCase):
    def test_precision_is_not_an_exact_year(self):
        self.assertEqual(books.date_span({'time': '+1850-00-00T00:00:00Z', 'precision': 7}), (1801, 1900, True))
        self.assertEqual(books.date_span({'time': '-0800-00-00T00:00:00Z', 'precision': 7}), (-800, -701, True))
        self.assertEqual(books.date_span({'time': '-1850-00-00T00:00:00Z', 'precision': 8}), (-1859, -1850, True))

    def test_qualifiers_and_unknown_values_survive(self):
        claim = {'mainsnak': {'datavalue': {'value': {'time': '+1905-00-00T00:00:00Z', 'precision': 9}}}, 'qualifiers': {'P1480': [{'datavalue': {'value': {'id': 'Q5727902'}}}]}}
        self.assertEqual(books.claim_span(claim), (1905, 1905, True))
        self.assertIsNone(books.date_span({'time': '+0000-00-00T00:00:00Z', 'precision': 9}))
        self.assertIsNone(books.claim_span({'mainsnak': {'snaktype': 'somevalue'}}))
        self.assertEqual(books.year_label(1905), '1905')
        self.assertEqual(books.year_label(-800), '800 BCE')


if __name__ == '__main__':
    unittest.main()
