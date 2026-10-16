"""Offline source identity and date boundaries; never connects to a database."""
import importlib.util,unittest
from pathlib import Path
def module(name):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name('million-'+name+'-20261010.py'))
    value=importlib.util.module_from_spec(s);s.loader.exec_module(value);return value
met=module('met');rijks=module('rijks');bulk=module('bulk-import')
class SourceEvidence(unittest.TestCase):
    def test_matched_person_dates_protect_against_a_wrong_source_authority(self):
        row=dict(first=1854,last=1854,work_type='print',links=[dict(artist_id='later-namesake',attribution_role='primary')])
        artists={'later-namesake':dict(birth_year=1881,death_year=1955)}
        self.assertTrue(bulk.matched_chronology_conflicts(row,artists))
        row.update(first=1960,last=1960)
        self.assertFalse(bulk.matched_chronology_conflicts(row,artists),'A posthumous print remains possible')
        row['work_type']='drawing'
        self.assertTrue(bulk.matched_chronology_conflicts(row,artists))
        row['links'][0]['attribution_role']='attributed_to'
        self.assertFalse(bulk.matched_chronology_conflicts(row,artists),'Qualified attributions need separate review')
    def row(self,**overrides):
        row={k:'' for k in ['Constituent ID','Artist Role','Artist Prefix','Artist Display Name','Artist Display Bio','Artist Suffix','Artist Alpha Sort','Artist Wikidata URL']}
        row.update({'Constituent ID':'1206','Artist Role':'Artist','Artist Display Name':'Ding Yunpeng','Artist Display Bio':'Chinese, 1547–1628'})
        row.update(overrides);return row
    def test_reused_met_constituent_is_not_a_person_key(self):
        first=met.creators(self.row())[0]
        second=met.creators(self.row(**{'Artist Display Name':'Li Liufang','Artist Display Bio':'Chinese, 1575–1629'}))[0]
        self.assertNotEqual(first['constituentid'],second['constituentid'])
        self.assertEqual(first['native_constituent_field'],second['native_constituent_field'])
    def test_incompatible_creator_lists_remain_unresolved(self):
        self.assertEqual(met.creators(self.row(**{'Artist Display Name':'A|B','Artist Role':'Artist'})),[])
    def test_qualified_attribution_is_retained(self):
        person=met.creators(self.row(**{'Artist Prefix':'After','Artist Wikidata URL':'https://www.wikidata.org/wiki/Q123'}))[0]
        self.assertEqual(person['prefix'],'After');self.assertEqual(person['constituentid'],'qid-Q123')
    def test_met_search_bounds_do_not_supply_creation_dates(self):
        self.assertIsNone(met.dates({'Object Date':'','Classification':'Paintings','Object Begin Date':'1500','Object End Date':'1600'}))
        self.assertIsNone(met.dates({'Object Date':'1900, printed 1980','Classification':'Photographs'}))
    def test_rijks_life_approximations_survive(self):
        self.assertEqual(rijks.lifeyear('ca. 1599'),'c. 1599')
        self.assertEqual(rijks.lifeyear('1660-11-23'),'1660')
        self.assertIsNone(rijks.lifeyear('active 1600-1640'))
    def test_sheet_back_views_do_not_inflate_new_objects(self):
        for accession in ['RP-T-1955-102(V)','RP-T-00-487(verso) ']:
            self.assertTrue(bulk.is_physical_view('rijks',accession))
        for accession in ['RP-T-1955-102(R)','SK-A-4751-A','SK-A-3979','RP-P-OB-67.305']:
            self.assertFalse(bulk.is_physical_view('rijks',accession))
        self.assertFalse(bulk.is_physical_view('met','something(V)'))
    def test_rijks_date_cutoff_and_qualifiers(self):
        self.assertEqual(rijks.date('1650 - c. 1655'),(1650,1655,'circa_range'))
        self.assertEqual(rijks.date('1898-10-23'),(1898,1898,'exact'))
        self.assertIsNone(rijks.date('1969 - 1972'))
        self.assertIsNone(rijks.date('after 1900'))
    def test_chronology_holds_originals_but_preserves_posthumous_prints(self):
        person=dict(displaydate='German, 1700 - 1750',prefix='',suffix='')
        row=dict(first=1760,last=1760,work_type='drawing',creators=[person])
        self.assertTrue(bulk.source_chronology_conflicts(row))
        self.assertFalse(bulk.source_chronology_conflicts(dict(row,work_type='print')))
        self.assertTrue(bulk.source_chronology_conflicts(dict(row,first=1650,last=1650,work_type='print')))
        self.assertFalse(bulk.source_chronology_conflicts(dict(row,creators=[dict(person,prefix='After')])))
    def test_rijks_selected_records_exclude_physical_parent_components(self):
        data=rijks.m.load(rijks.RUN/rijks.SELECTION)
        self.assertGreater(len(data['selected']),30000)
        import re
        for row in data['selected']:
            self.assertFalse(any(re.fullmatch(r'https://id\.rijksmuseum\.nl/20\d+',u) for u in row['raw']['parent_references']))
            self.assertEqual((row['first'],row['last'],row['precision']),rijks.date(row['date_display']))
            self.assertTrue(row['source_url']);self.assertLessEqual(row['last'],1970)
            self.assertTrue(all(c['source_uri'].startswith('https://id.rijksmuseum.nl/21') for c in row['creators']))
    def test_pinned_met_plan_and_execution_holds(self):
        folder=met.RUN/'002';p=met.m.load(folder/'plan.json.gz');pin=met.m.load(folder/'pin.json')['sha256']
        self.assertEqual(met.m.sha((folder/'plan.json.gz').read_bytes()),pin)
        exclusions=met.m.load(folder/'execution-exclusions-v2.json');self.assertEqual(exclusions['plan_sha256'],pin)
        held={r['artwork_id'] for r in exclusions['rows']};rows=[r for r in p['new_artworks'] if r['artwork_id'] not in held]
        self.assertEqual(len(rows),len({r['native_id'] for r in rows}))
        self.assertEqual(len(rows),len({met.m.norm(r['accession_number']) for r in rows}))
        for r in rows:
            self.assertLessEqual(len(r['creator_label']),500)
            self.assertLessEqual(r['last'],1970)
            self.assertEqual((r['first'],r['last'],r['precision']),met.dates(r['raw']))
            self.assertTrue(all(c['constituentid'].startswith(('qid-','evidence-')) for c in r['creators']))
if __name__=='__main__':unittest.main()
