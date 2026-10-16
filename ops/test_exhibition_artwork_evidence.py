"""Participation evidence must not turn a listing into a physical-display claim."""
import unittest
from exhibition_artworks_local import history_match


class ExhibitionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.event=dict(title='Winter Show',format='physical',state='held',startYear=2020,endYear=2021,venues=[dict(name='Espace Meyer Zafra')])

    def test_explicit_title_venue_and_year(self):
        self.assertIsNotNone(history_match('Winter Show, Espace Meyer Zafra, Paris, 2021',self.event))

    def test_unrelated_year_or_venue(self):
        for history in ['Winter Show, Espace Meyer Zafra, 1999','Winter Show, Different Gallery, 2021',
                        'Winter Show, Espace Meyer Zafra, 1999\nOther Show, 2021',
                        'Winter Show, Espace Meyer Zafra, 1999; Other Show, 2021']:
            with self.subTest(history=history):self.assertIsNone(history_match(history,self.event))

    def test_tentative_withdrawn_cancelled_and_online(self):
        for label in ['Proposed','Withdrawn','Cancelled','Not exhibited','Online']:
            with self.subTest(label=label):self.assertIsNone(history_match(f'{label}: Winter Show, Espace Meyer Zafra, 2021',self.event))
        self.event['format']='online'
        self.assertIsNone(history_match('Winter Show, Espace Meyer Zafra, 2021',self.event))

    def test_title_boundary_and_cross_line_guard(self):
        self.assertIsNone(history_match('Winter Showroom, Espace Meyer Zafra, 2021',self.event))
        self.assertIsNone(history_match('Winter Show\nEspace Meyer Zafra, 2021',self.event))


if __name__=='__main__':unittest.main()
