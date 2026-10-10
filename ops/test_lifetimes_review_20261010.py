import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('plan',Path(__file__).with_name('lifetimes-plan-20261010.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
class ChronologyTests(unittest.TestCase):
    def test_search_bounds_and_activity_are_not_life_dates(self):
        for label in ['active 1743–1749','American, active c. 1813','Italian, 1497/1498 - 1543','French, 1840 - after 1875','Italian, probably 1392 - 1450','German, 19th century']:
            self.assertIsNone(p.literal_life(label),label)
    def test_circa_and_open_life_preserve_precision(self):
        self.assertEqual(p.literal_life('Italian, c. 1589 - 1654')['birth'],dict(year=1589,precision='circa',display='c. 1589'))
        self.assertEqual(set(p.literal_life('American, born 1911')),{'birth'})
        self.assertEqual(set(p.literal_life('German, died 1866')),{'death'})
    def test_padded_native_columns_do_not_enter_literal_parser(self):
        source=dict(displaydate='American, born 1911',beginyear=1911,endyear=2011)
        self.assertNotIn('death',p.literal_life(source['displaydate']))
    def test_uccello_correction_resolves_artwork_without_redating(self):
        artist=dict(status='review',entity_type='person',birth_year=1475,death_year=1475)
        work=dict(status='review',creation_year_start=1436,creation_year_end=1436,attribution_role='primary',work_type='painting',medium_text='fresco')
        self.assertIn('entirely_before_recorded_birth',p.r.artwork_flags(work,artist))
        self.assertEqual(p.r.artwork_flags(work,{**artist,'birth_year':1397}),[])
        self.assertEqual(work['creation_year_start'],1436)
    def test_posthumous_and_qualified_attribution_not_automatic_error(self):
        artist=dict(status='review',entity_type='person',birth_year=1800,death_year=1880)
        work=dict(status='review',creation_year_start=1900,creation_year_end=1900,attribution_role='after',work_type='print',medium_text='etching')
        flags=p.r.artwork_flags(work,artist)
        self.assertIn('posthumous_physical_production_possible',flags)
        self.assertIn('qualified_attribution_preserve_distinction',flags)
    def test_unknown_and_collective_dates_are_not_person_life(self):
        artist=dict(status='review',entity_type='collective',birth_year=None,death_year=None)
        work=dict(status='review',creation_year_start=1400,creation_year_end=1500,attribution_role='primary',work_type='sculpture',medium_text='stone')
        self.assertEqual(p.r.artwork_flags(work,artist),['nonperson_use_activity_not_lifespan'])
        self.assertEqual(p.r.artwork_flags({**work,'creation_year_start':None},artist),['creation_date_unassessable'])
if __name__=='__main__':unittest.main()
