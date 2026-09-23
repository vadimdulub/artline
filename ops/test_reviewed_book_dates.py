import importlib.util
import json
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('reviews',Path(__file__).with_name('reviewed_book_dates.py'))
reviews=importlib.util.module_from_spec(spec);spec.loader.exec_module(reviews)

class ReviewedBookDates(unittest.TestCase):
    def test_norna_keeps_approximation_and_a_real_source(self):
        value=reviews.apply_reviewed_date({'id':'wd-q119224','title':'Norna-Gests þáttr','startYear':1301,'endYear':2000})
        self.assertEqual((value['startYear'],value['endYear'],value['years']),(1300,1300,'c. 1300'))
        self.assertTrue(value['approximate'])
        self.assertIn('arlima.net',value['dateSources'][0]['url'])

    def test_unknown_and_genuinely_long_compositions_are_not_clamped(self):
        for book in [{'id':'unreviewed','startYear':None,'endYear':None}, {'id':'bible','startYear':-1000,'endYear':200}]:
            self.assertEqual(reviews.apply_reviewed_date(book.copy()),book)

    def test_identity_conflict_requires_review(self):
        with self.assertRaises(AssertionError):
            reviews.apply_reviewed_date({'id':'wd-q119224','title':'Different book'})

    def test_all_reviews_have_sources_and_ordered_dates(self):
        data=reviews.manifest()
        self.assertEqual(len(data['dates']),17)
        self.assertEqual(len({x['bookId'] for x in data['highlights']}),54)
        for r in data['dates']:
            self.assertLessEqual(r['fields']['startYear'],r['fields']['endYear'])
            self.assertTrue(r['fields']['dateSources'])
            self.assertTrue(r['fields']['dateBasis'])
            self.assertEqual(len(r['expectedChecksum']),64)

if __name__=='__main__':unittest.main()
