"""Meaningful evidence/date/identity boundaries; no database fixtures."""
import copy
import unittest

import exhibitions_common as c
from exhibitions_artsy import normalize
from exhibitions_deliver import identity_keys, match_institution, screen_record
from exhibitions_apj import parse_period


class ExhibitionEvidenceTests(unittest.TestCase):
    def source(self, **changes):
        value=dict(internalID='source-1',slug='sample-gallery-catalogue',name='Paintings from the River',
                   startAt='1969-10-01T12:00:00+00:00',endAt='1969-11-05T12:00:00+00:00',
                   status='closed',isFairBooth=False,isOnlineExclusive=False,isReference=True,isStubShow=False,
                   partner={'name':'Example Gallery','internalID':'gallery-1'},location={'city':'Paris','country':'FR'},
                   artists=[],artworksConnection={'totalCount':10,'pageInfo':{'hasNextPage':True},'edges':[{'node':{
                       'internalID':'object-1','slug':'artist-river','title':'River','artistNames':'An Artist','date':'1960'}}]})
        value.update(changes)
        return value

    def test_no_manufactured_month_or_year_dates(self):
        self.assertIsNone(c.exact_date('1958'))
        self.assertIsNone(c.exact_date('1958-04'))
        self.assertIsNone(c.exact_date('1958-02-30'))
        self.assertEqual(c.exact_date('1958-04-15T12:00:00Z'),'1958-04-15')

    def test_artwork_list_is_partial_and_not_physical_display_proof(self):
        r=normalize(self.source(),{})
        self.assertEqual(r['entries'][0]['participation'],'catalogued')
        self.assertEqual(r['entries'][0]['date_label'],'1960')
        self.assertEqual(r['checklist_state'],'partial')
        self.assertEqual(r['public_artwork_list']['retrieved'],1)
        self.assertEqual(r['public_artwork_list']['total'],10)
        self.assertNotIn('artwork_id',r['entries'][0])

    def test_online_presenter_does_not_become_physical_venue(self):
        r=normalize(self.source(isOnlineExclusive=True,location=None),{})
        self.assertEqual(r['format'],'online')
        self.assertEqual(r['occurrences'],[])
        self.assertEqual(r['participants'][0]['role'],'presenting_organization')

    def test_cancelled_or_implausible_events_do_not_count(self):
        self.assertEqual(normalize(self.source(name='Cancelled: Paintings from the River'),{})['event_state'],'cancelled')
        for changes in [dict(startAt='0002-05-04T00:00:00Z'),dict(startAt='1970-01-01',endAt='1969-01-01'),dict(isFairBooth=True),dict(isStubShow=True),dict(endAt=None)]:
            self.assertNotEqual(normalize(self.source(**changes),{})['event_state'],'held')

    def test_different_venues_or_editions_do_not_merge_on_title(self):
        r=normalize(self.source(),{})
        other=copy.deepcopy(r);other['occurrences'][0]['venue_label']='Another Gallery'
        self.assertFalse(set(identity_keys(r))&set(identity_keys(other)))
        other=copy.deepcopy(r);other['start_date']='1970-10-01';other['end_date']='1970-11-05'
        self.assertFalse(set(identity_keys(r))&set(identity_keys(other)))
        other=copy.deepcopy(r);other['provider']='other-authority';other['native_id']='different-id'
        self.assertTrue(set(identity_keys(r))&set(identity_keys(other)))

    def test_country_conflict_cannot_assign_a_museum(self):
        venue={'venue_label':'Example National Gallery','country_code':'FR'}
        institutions={'a':{'country_code':'GB'}}
        self.assertIsNone(match_institution(venue,{'example national gallery':{'a'}},institutions))

    def test_japanese_archive_explicit_date_formats(self):
        self.assertEqual(parse_period('1976.04.18-1976.04.29'),('1976-04-18','1976-04-29'))
        self.assertEqual(parse_period('1958-04-15/1958-05-04［20日間］'),('1958-04-15','1958-05-04'))
        self.assertEqual(parse_period('2001-03/2001-04'),(None,None))
        self.assertEqual(parse_period('2001.03.04-4.01'),(None,None))
        self.assertEqual(parse_period('2001.02.30-2001.03.12'),(None,'2001-03-12'))
        self.assertEqual(parse_period('2001.03.04'),('2001-03-04',None))

    def test_commerce_events_and_impossible_venue_dates_are_held(self):
        r=normalize(self.source(name='Art Basel 2014'),{});screen_record(r)
        self.assertEqual(r['event_state'],'uncertain')
        r=normalize(self.source(startAt='0002-05-04T00:00:00Z'),{});screen_record(r)
        self.assertIsNone(r['occurrences'][0]['start_date'])
        self.assertEqual(r['occurrences'][0]['evidence']['original_start'],'0002-05-04')


if __name__=='__main__':unittest.main()
