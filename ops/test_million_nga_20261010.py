"""Offline boundary proofs for the production museum import; no database fixtures."""
import collections,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('nga',Path(__file__).with_name('million-nga-20261010.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
class SourceBoundaries(unittest.TestCase):
    def test_creation_dates_do_not_borrow_lifetimes(self):
        for literal in ['', 'n.d.', 'active 1500 - 1570','probably 1626/1641','1920, printed 1980','1960s-1970s','1971','1969/1971']:
            self.assertIsNone(n.dates(literal),literal)
    def test_literal_ranges_and_approximation_survive(self):
        self.assertEqual(n.dates('c. 1423/1424'),(1423,1424,'circa_range'))
        self.assertEqual(n.dates('1935/1942'),(1935,1942,'range'))
        self.assertEqual(n.dates('1850/55'),(1850,1855,'range'))
        self.assertEqual(n.dates('16th century'),(1501,1600,'century'))
        self.assertEqual(n.dates('1960s'),(1960,1969,'decade'))
    def test_activity_is_not_a_lifespan(self):
        person=dict(constituentid='test',forwarddisplayname='Puccio di Simone',preferreddisplayname='Puccio di Simone',displaydate='Florentine, active c. 1330 - 1360',wikidataid='',constituenttype='individual')
        aid,reason,a=n.artist_plan(person,[dict(first=1354,last=1354)],{},collections.defaultdict(set),collections.defaultdict(set))
        self.assertIsNone(a['birth_year']);self.assertIsNone(a['death_year']);self.assertEqual(a['timeline_basis'],'activity');self.assertEqual((a['timeline_start_year'],a['timeline_end_year']),(1330,1360))
    def test_same_name_without_authority_or_life_is_held(self):
        person=dict(constituentid='test',forwarddisplayname='John Smith',preferreddisplayname='Smith, John',displaydate='',wikidataid='',constituenttype='individual')
        existing={'a':dict(birth_year=None,death_year=None,status='review',names={'john smith'})}
        aid,reason,a=n.artist_plan(person,[dict(first=1850,last=1850)],existing,{}, {'john smith':{'a'}})
        self.assertIsNone(aid);self.assertEqual(reason,'existing_name_ambiguous')
    def test_unqualified_short_date_range_is_not_promoted_to_life(self):
        person=dict(constituentid='test',forwarddisplayname='Johann Otmar',preferreddisplayname='Otmar, Johann',displaydate='German, Augsburg, 1502–1514',wikidataid='',constituenttype='individual')
        aid,reason,a=n.artist_plan(person,[dict(first=1504,last=1504)],{},collections.defaultdict(set),collections.defaultdict(set))
        self.assertIsNone(aid);self.assertIsNone(a);self.assertEqual(reason,'short_source_range_may_be_activity_requires_review')
        person['displaydate']='German, active 1502 - 1514'
        aid,reason,a=n.artist_plan(person,[dict(first=1504,last=1504)],{},collections.defaultdict(set),collections.defaultdict(set))
        self.assertEqual(a['timeline_basis'],'activity');self.assertIsNone(a['birth_year']);self.assertIsNone(a['death_year'])
    def test_pinned_plan_physical_identity_and_scope(self):
        p=n.m.load(n.RUN/n.PLAN);rows=p['new_artworks'];self.assertGreater(len(rows),40000)
        self.assertEqual(n.m.sha((n.RUN/n.PLAN).read_bytes()),n.m.load(n.RUN/n.PIN)['sha256'])
        inseparable={r['childobjectid'] for r in n.read('object_associations.csv') if r['relationship']=='inseparable'}
        self.assertFalse(inseparable & {r['native_id'] for r in rows})
        self.assertEqual(len(rows),len({r['native_id'] for r in rows}));self.assertEqual(len(rows),len({n.m.norm(r['accession_number']) for r in rows}))
        qids=[r['wikidata_id'] for r in rows if r['wikidata_id']];self.assertEqual(len(qids),len(set(qids)))
        for r in rows:
            self.assertEqual(r['raw']['isvirtual'],'0');self.assertEqual(r['raw']['accessioned'],'1')
            self.assertEqual((r['first'],r['last'],r['precision']),n.dates(r['date_display']))
            self.assertLessEqual(r['last'],1970);self.assertFalse(r['last']==1970 and 'circa' in r['precision'])
        for a in p['new_artists']:
            if a['timeline_basis']=='life':self.assertIsNotNone(a['birth_year']);self.assertIsNotNone(a['death_year'])
            self.assertEqual(a['status'],'review')
if __name__=='__main__':unittest.main()
