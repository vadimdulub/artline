"""Pure validation tests; no catalogue connection or filesystem fixtures."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import uuid

spec = importlib.util.spec_from_file_location('round2', Path(__file__).with_name('low-count-200-painters-round2-20261009.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def claim(value, qualifiers=None, references=None):
    result = dict(rank='normal', mainsnak=dict(snaktype='value', datavalue=dict(value=value)))
    if qualifiers: result['qualifiers'] = qualifiers
    if references: result['references'] = references
    return result


def entity_id(qid):
    return {'entity-type': 'item', 'numeric-id': int(qid[1:]), 'id': qid}


def plan():
    artist = dict(id='test-artist', display_name='Test Painter', birth_year=1800, death_year=1870)
    person = dict(labels={'en': dict(value='Test Painter')}, claims={
        'P31': [claim(entity_id('Q5'))], 'P106': [claim(entity_id('Q1028181'))],
        'P569': [claim(dict(time='+1800-01-01T00:00:00Z', precision=9))],
        'P570': [claim(dict(time='+1870-01-01T00:00:00Z', precision=9))]})
    rows = []
    for number in range(20):
        qid = 'Q'+str(900000000+number)
        wid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://www.wikidata.org/entity/'+qid))
        title = 'Validation example '+str(number)
        rows.append(dict(artwork_id=wid, artist_id=artist['id'], artist_ids=[artist['id']], qid=qid, source_id=qid,
             title=title, painter_qid='Q123', institution_id='museum', institution_qid='Q456',
             source_scheme='wikidata', source_url='https://www.wikidata.org/wiki/'+qid,
             source_evidence=dict(id=qid, claims={'P571':[claim(dict(time='+1840-00-00T00:00:00Z',precision=9,calendarmodel='http://www.wikidata.org/entity/Q1985727',before=0,after=0))], 'P170': [claim(entity_id('Q123'))],
                 'P195': [claim(entity_id('Q456'), references=[dict(snaks={'P854': [dict(datavalue=dict(value='https://example.org/object'))]})])]}),
             source_collection_matches=[dict(source_qid='Q456', record=dict(id='museum'))], confidence=.85,
             receipt=dict(status=200), first=1840, last=1840, precision='exact', date_display='1840', uncertainty=[],
             work=dict(id=wid, title=title, creation_year_start=1840, creation_year_end=1840, date_precision='exact', date_display='1840')))
    return dict(pair=dict(artist=artist, aliases=[], count_at_selection=4), profile=dict(entity=person), rows=rows)


class ValidationTests(unittest.TestCase):
    def test_late_century_retains_broad_source_bounds(self):
        value = dict(time='+1801-01-01T00:00:00Z', precision=7, calendarmodel='http://www.wikidata.org/entity/Q1985727', before=0, after=0)
        c = claim(value, qualifiers={'P4241':[dict(snaktype='value',datavalue=dict(value=entity_id('Q40719766')))]})
        self.assertEqual(m.source_date(dict(claims={'P571':[c]})),dict(first=1801,last=1900,precision='century',date_display='late 19th century'))
        c['qualifiers']['P4241'][0]['datavalue']['value']=entity_id('Q123')
        with self.assertRaises(ValueError):m.source_date(dict(claims={'P571':[c]}))

    def test_collection_scoped_inventory_requires_matching_museum(self):
        row=dict(inventories=[],source_collection_matches=[dict(source_qid='Q456')],source_evidence=dict(claims={'P217':[
            claim('1984.35.2',qualifiers={'P195':[dict(snaktype='value',datavalue=dict(value=entity_id('Q456')))]}),
            claim('other museum',qualifiers={'P195':[dict(snaktype='value',datavalue=dict(value=entity_id('Q789')))]})]}))
        self.assertEqual(m.identity_inventories(row),['1984.35.2'])

    def test_reviewed_false_positive_does_not_hide_another_collision(self):
        row=dict(artwork_id='new',source_scheme='wikidata',external_id='Q123',source_url='https://www.wikidata.org/wiki/Q123',
            source_evidence={'claims':{}},native_urls=[],inventories=['1984.35.2'],institution_id='museum',
            title_aliases=['Study'],artist_ids=['painter'],creator_label='Painter')
        false=dict(id='false',title='Different object',alternate_title=None,accession_number='1984.3.52',current_institution_id='museum',unlinked_creator_label=None)
        real=dict(id='real',title='Study',alternate_title=None,accession_number='1984.35.2',current_institution_id='museum',unlinked_creator_label=None)
        candidates=dict(artworks=[false,real],external=[],citations=[],creators=[])
        waiver={('new','false'):dict(expected_existing=dict(title='Different object',accession_number='1984.3.52',current_institution_id='museum',artist_ids=[]))}
        with patch.object(m,'identity_waivers',return_value=waiver):
            self.assertEqual(m.collision_reason(row,candidates),('Existing institution inventory',['real']))
            false['title']='Unreviewed change'
            self.assertEqual(m.collision_reason(row,candidates),('Existing institution inventory',['false','real']))

    def test_valid_museum_objects(self):
        m.validate_plan(plan())

    def test_unknown_dates_need_explicit_uncertainty(self):
        p = plan(); row = p['rows'][0]
        row.update(first=None, last=None)
        row.update(precision='unknown',date_display='Creation date unknown')
        row['source_evidence']['claims'].pop('P571')
        row['work'].update(creation_year_start=None, creation_year_end=None, date_precision='unknown', date_display='Creation date unknown')
        with self.assertRaises(AssertionError): m.validate_plan(p)
        row['uncertainty'] = ['Creation date unknown; retained in review without inferred years.']
        m.validate_plan(p)

    def test_post_cutoff_date_is_rejected(self):
        p = plan(); row = p['rows'][0]
        row.update(first=1971, last=1971)
        row['work'].update(creation_year_start=1971, creation_year_end=1971)
        with self.assertRaises(AssertionError): m.validate_plan(p)

    def test_qualified_creator_is_not_silently_primary(self):
        p = plan(); p['rows'][0]['source_evidence']['claims']['P170'][0]['qualifiers'] = {'P1480': [dict()]}
        with self.assertRaises(AssertionError): m.validate_plan(p)

    def test_historical_holding_needs_review(self):
        p = plan(); p['rows'][0]['source_evidence']['claims']['P195'][0]['qualifiers'] = {'P582': [dict()]}
        with self.assertRaises(AssertionError): m.validate_plan(p)

    def test_holding_without_reference_is_rejected(self):
        p = plan(); p['rows'][0]['source_evidence']['claims']['P195'][0].pop('references')
        with self.assertRaises(AssertionError): m.validate_plan(p)

    def test_unknown_reference_value_is_not_evidence(self):
        p = plan()
        p['rows'][0]['source_evidence']['claims']['P195'][0]['references'] = [dict(snaks={'P248':[dict(snaktype='somevalue')]})]
        with self.assertRaises(AssertionError): m.validate_plan(p)

    def test_explicit_wikiart_identity_catches_translated_title(self):
        url = 'https://www.wikiart.org/en/example-painter/example-work'
        row = dict(source_scheme='wikidata', source_url='https://www.wikidata.org/wiki/Q123', source_evidence={'claims':{}}, native_urls=[url])
        existing = dict(external=[dict(entity_id='existing-artwork', scheme='wikiart-artwork', external_id='12345', canonical_url=url)], citations=[], artworks=[], creators=[])
        self.assertEqual(m.collision_reason(row, existing), ('Existing exact source identity', ['existing-artwork']))

    def test_department_and_parent_must_resolve_to_same_museum(self):
        p = plan(); row = p['rows'][0]
        row['source_evidence']['claims']['P195'].append(claim(entity_id('Q789')))
        row['source_collection_matches'].append(dict(source_qid='Q789', record=dict(id='museum')))
        m.validate_plan(p)
        row['source_collection_matches'][1]['record']['id'] = 'different-museum'
        with self.assertRaises(AssertionError): m.validate_plan(p)

    def test_painter_lifespan_conflict_is_rejected(self):
        p = plan(); p['pair']['artist']['birth_year'] = 1810
        with self.assertRaises(AssertionError): m.validate_plan(p)

    def test_identical_name_without_painter_occupation_is_not_enough(self):
        p = plan(); p['profile']['entity']['claims']['P106'] = [claim(entity_id('Q49757'))]
        with self.assertRaises(AssertionError): m.validate_plan(p)

    def test_duplicate_source_object_is_rejected(self):
        p = plan(); p['rows'][-1] = copy.deepcopy(p['rows'][0])
        with self.assertRaises(AssertionError): m.validate_plan(p)

    def test_minimum_is_twenty_new_objects(self):
        p = plan(); p['rows'].pop()
        with self.assertRaises(AssertionError): m.validate_plan(p)

    def test_high_count_painter_is_rejected(self):
        p = plan(); p['pair']['count_at_selection'] = 11
        with self.assertRaises(AssertionError): m.validate_plan(p)

    def test_source_century_is_not_an_exact_year(self):
        value = dict(time='+1800-00-00T00:00:00Z', precision=7, calendarmodel='http://www.wikidata.org/entity/Q1985727', before=0, after=0)
        date = m.source_date(dict(claims={'P571':[claim(value)]}))
        self.assertEqual(date, dict(first=1701,last=1800,precision='century',date_display='18th century'))
        value['time'] = '+1801-00-00T00:00:00Z'
        self.assertEqual(m.source_date(dict(claims={'P571':[claim(value)]}))['first'], 1801)

    def test_decade_crossing_cutoff_is_not_silently_eligible(self):
        value = dict(time='+1970-00-00T00:00:00Z', precision=8, calendarmodel='http://www.wikidata.org/entity/Q1985727', before=0, after=0)
        with self.assertRaises(ValueError): m.source_date(dict(claims={'P571':[claim(value)]}))

    def test_explicit_creation_range_is_preserved(self):
        value = dict(time='+1850-00-00T00:00:00Z', precision=9, calendarmodel='http://www.wikidata.org/entity/Q1985727', before=0, after=0)
        low = copy.deepcopy(value); low['time'] = '+1845-00-00T00:00:00Z'
        high = copy.deepcopy(value); high['time'] = '+1855-00-00T00:00:00Z'
        c = claim(value, qualifiers={'P1319':[dict(snaktype='value',datavalue=dict(value=low))], 'P1326':[dict(snaktype='value',datavalue=dict(value=high))]})
        self.assertEqual(m.source_date(dict(claims={'P571':[c]})), dict(first=1845,last=1855,precision='range',date_display='1845–1855'))

    def test_unreviewed_single_date_bound_is_held(self):
        c = claim(None, qualifiers={'P1326':[dict(snaktype='value',datavalue=dict(value={}))]})
        with self.assertRaises(ValueError): m.source_date(dict(claims={'P571':[c]}))

    def test_documented_drawing_subtype_is_supported(self):
        types = {'Q987':dict(entity=dict(claims={'P279':[claim(entity_id('Q93184'))]}))}
        e = dict(claims={'P31':[claim(entity_id('Q93184')),claim(entity_id('Q987'))]})
        self.assertEqual(m.source_kind(e, types), 'drawing')
        self.assertIsNone(m.source_kind(e, {}))


if __name__ == '__main__': unittest.main()
