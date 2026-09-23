"""Reviewed overrides shared by the import preparation and local reconciliation.

Unknown or genuinely broad dates are not shortened automatically. A review
contains a source, an explicit dating basis and the original values.
"""
import json
from pathlib import Path

MANIFEST = Path(__file__).with_name('curated-book-reviews-20260921.json')


def manifest():
    return json.loads(MANIFEST.read_text())


def apply_reviewed_date(book):
    review = next((r for r in manifest()['dates'] if r['bookId'] == book['id']), None)
    if review:
        assert book['title'] == review['title'], 'Reconcile the changed book identity before applying a date review'
        book.update(review['fields'])
    return book
