import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location('events', pathlib.Path(__file__).with_name('research-historical-events.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def claim(year, precision=9):
    return {'rank': 'normal', 'mainsnak': {'datavalue': {'value': {'time': f'{year:+05d}-00-00T00:00:00Z', 'precision': precision}}}}


class ChronologyTests(unittest.TestCase):
    def test_bce_precision_is_retained(self):
        self.assertEqual(r.span_for_claim(claim(-9000, 6)), (-9000, -8001, True))
        self.assertEqual(r.span_for_claim(claim(-450, 7)), (-500, -401, True))
        self.assertEqual(r.span_for_claim(claim(1850, 8)), (1850, 1859, True))
        self.assertIsNone(r.span_for_claim(claim(0)))

    def test_treaty_occurrence_is_not_replaced_by_entry_into_force(self):
        e = {'claims': {'P585': [claim(1919)], 'P580': [claim(1920)]}}
        self.assertEqual(r.chronology(e, 'Event')[:2], (1919, 1919))

    def test_duration_alternatives_and_qualifiers(self):
        first = claim(1789)
        first['qualifiers'] = {'P1480': [{'datavalue': {'value': {'id': 'Q5727902'}}}]}
        e = {'claims': {'P580': [first, claim(1788)], 'P582': [claim(1799)], 'P585': [claim(1800)]}}
        start, end, uncertain, _ = r.chronology(e, 'Event')
        self.assertEqual((start, end, uncertain), (1788, 1799, True))

    def test_unknown_and_single_endpoint_do_not_invent_duration(self):
        self.assertEqual(r.chronology({}, 'Period')[:2], (None, None))
        result = r.chronology({'claims': {'P580': [claim(1500)]}}, 'Movement')
        self.assertEqual(result[:2], (1500, 1500))
        self.assertIn('does not imply', result[3])
        conflict = r.chronology({'claims': {'P580': [claim(1900)], 'P582': [claim(1800)]}}, 'Event')
        self.assertEqual(conflict[:2], (None, None))

    def test_deprecated_claims_do_not_expand_the_span(self):
        bad = claim(2026); bad['rank'] = 'deprecated'
        self.assertEqual(r.chronology({'claims': {'P585': [claim(1900), bad]}}, 'Event')[:2], (1900, 1900))

    def test_time_of_day_does_not_make_the_year_approximate(self):
        c = claim(1986, 11)
        c['qualifiers'] = {'P4241': [{'datavalue': {'value': {'id': 'Q1311'}}}]}
        self.assertEqual(r.span_for_claim(c), (1986, 1986, False))
        c['mainsnak']['datavalue']['value']['before'] = 2
        self.assertIsNone(r.span_for_claim(c))

    def test_multiple_occurrences_in_a_known_year_keep_that_year(self):
        result = r.chronology({'claims': {'P585': [claim(1945, 11), claim(1945, 11)]}}, 'Event')
        self.assertEqual(result[:3], (1945, 1945, False))


if __name__ == '__main__': unittest.main()
