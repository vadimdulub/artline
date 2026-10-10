"""Offline source and identity safeguards; never writes database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-france-third-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Evidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.ds={v['number']:v for v in r.build()}
    def test_tournus_alias_preserves_actual_location(self):
        f=self.ds[70]['facts'];self.assertTrue(f['holding_context_reference']);self.assertEqual(f['source_fields']['Localisation'],'Tournus ; musée Greuze');self.assertEqual(f['credit_line'],f['source_fields']['Statut_juridique'])
    def test_alias_rejects_wrong_city(self):
        d=copy.deepcopy(self.ds[70]['facts']['source_fields']);d['Ville']='Autun';self.assertIsNone(r.f.t.screen(d)[0])
    def test_alias_rejects_deposit_and_missing(self):
        for key,value in [('Lieu_de_depot','Autre musée'),('MANQUANT','oui')]:
            d=copy.deepcopy(self.ds[70]['facts']['source_fields']);d[key]=value;self.assertIsNone(r.f.t.screen(d)[0])
    def test_public_owner_is_not_rewritten(self):
        f=self.ds[119]['facts'];self.assertTrue(f['holding_context_reference']);self.assertEqual(f['credit_line'],f['source_fields']['Statut_juridique']);self.assertTrue(f['credit_line'].startswith("propriété de la communauté d'agglomération"))
    def test_public_owner_exception_requires_exact_museum(self):
        for key,value in [('Localisation','Montargis ; autre musée'),('Ville','Paris'),('Nom_officiel_musee','autre musée')]:
            d=copy.deepcopy(self.ds[119]['facts']['source_fields']);d[key]=value;self.assertIsNone(r.f.t.screen(d)[0])
    def test_duplicate_source_references_do_not_become_two_works(self):
        a=self.ds[46];b=self.ds[55];self.assertNotEqual(a['source_id'],b['source_id']);self.assertEqual(a['facts']['inventory'],b['facts']['inventory']);self.assertEqual(a['facts']['dimensions_text'],b['facts']['dimensions_text']);self.assertEqual(a['state'],b['state']);self.assertEqual(a['state'],'editorial_hold')
    def test_cutoff_includes_1970(self):
        d=self.ds[18];self.assertEqual((d['facts']['first'],d['facts']['last']),(1970,1970));self.assertEqual(d['state'],'approved_review_only_addition')
    def test_bound_book_is_held(self):
        d=self.ds[75];self.assertEqual(d['state'],'editorial_hold');self.assertIn('Livre',d['facts']['title'])
    def test_current_nevelson_name_and_former_alias_are_scoped(self):
        d=self.ds[70];self.assertIn('Nevelson',d['facts']['creator_label']);self.assertIn('nevelson',d['comparison']['creator_terms']);self.assertIn('berliawsky',d['comparison']['creator_terms']);self.assertGreater(len(d['comparison']['creator_pool_ids']),0)
    def test_current_maury_date_conflict_is_held(self):
        d=self.ds[91];self.assertIn('Maury Rose',d['facts']['creator_label']);self.assertLessEqual(d['facts']['last'],1800);self.assertEqual(d['state'],'editorial_hold')
    def test_posthumous_inscription_conflicts_with_source_century(self):
        d=self.ds[94];self.assertIn('1805',d['facts']['source_fields']['Precisions_inscriptions']);self.assertLessEqual(d['facts']['last'],1800);self.assertEqual(d['state'],'editorial_hold')
    def test_cross_museum_inventory_does_not_force_link(self):
        d=self.ds[77];hit=next(v for v in d['comparison']['inventory_hits'] if v['id']=='bac0fa09-b739-4131-a349-642145a697af');self.assertTrue(hit['relevant']);self.assertNotEqual(hit['current_institution_id'],d['institution_id']);self.assertEqual(d['state'],'editorial_hold')
    def test_ancient_anonymous_record_does_not_invent_maker(self):
        f=self.ds[16]['facts'];self.assertEqual((f['first'],f['last']),(201,300));self.assertEqual(f['creator_label'],f['source_fields']['Auteur']);self.assertIn(f['creator_label'],[None,'anonyme']);self.assertEqual(f['work_type'],'sculpture')
    def test_event_and_sitter_years_do_not_replace_creation(self):
        f=self.ds[4]['facts'];self.assertGreaterEqual(f['first'],1801);self.assertIn('1798',str(f['source_fields']))
        f=self.ds[9]['facts'];self.assertIn('1768-1793',f['title']);self.assertEqual(f['first'],1877);self.assertIsNone(f['dimensions_text'])
    def test_recto_verso_is_one_physical_unit(self):
        d=self.ds[119];self.assertIn('recto',d['facts']['title']);self.assertIn('verso',d['facts']['title']);self.assertEqual(d['state'],'approved_review_only_addition');self.assertEqual(sum(v['source_id']==d['source_id'] for v in self.ds.values()),1)
    def test_prints_and_model_drawings_remain_distinct(self):
        a=self.ds[89]['facts'];b=self.ds[115]['facts'];self.assertEqual((a['work_type'],b['work_type']),('print','drawing'));self.assertNotEqual(a['inventory'],b['inventory']);self.assertNotEqual(a['dimensions_text'],b['dimensions_text'])
    def test_before_date_retains_unknown_lower_bound(self):
        f=self.ds[7]['facts'];self.assertIsNone(f['first']);self.assertEqual((f['last'],f['date_precision']),(1819,'before'))
    def test_qualified_creator_is_not_promoted(self):
        f=self.ds[20]['facts'];self.assertIn('manière de',f['creator_label']);self.assertEqual(f['creator_label'],f['source_fields']['Auteur'])
    def test_print_date_difference_remains_evidence(self):
        f=self.ds[90]['facts'];self.assertEqual(f['first'],1776);self.assertIn('1775',f['source_fields']['Precisions_inscriptions'])
    def test_hash_and_http_failures_are_rejected(self):
        x=r.m.load(r.checked(self.ds[70]['source_reference']));bad=copy.deepcopy(x);bad['receipt']['status']=429
        with self.assertRaises(AssertionError):r.f.body(bad)
        bad=copy.deepcopy(x);bad['receipt']['sha256']='0'*64
        with self.assertRaises(AssertionError):r.f.body(bad)
    def test_alias_expansion_includes_former_attribution(self):
        self.assertIn('dietrich',self.ds[3]['comparison']['creator_terms']);self.assertIn('schedoni',self.ds[111]['comparison']['creator_terms']);self.assertIn('hondecooter',self.ds[96]['comparison']['creator_terms'])
    def test_indexed_comparator_matches_independent_scan(self):
        x=r.m.load(r.IDENTITY);s=x['state']
        for n in [3,16,70,77,96,109,111,119]:
            d=self.ds[n];f=d['facts'];c=d['comparison'];ts=set(r.identity.terms(f));aids={a['id'] for a in s['artists'] if r.identity.i.tokens(a['display_name'])&ts}|{a['artist_id'] for a in s['aliases'] if r.identity.i.tokens(a['alias'])&ts}
            pool={a['id'] for a in s['artworks'] if r.identity.i.tokens(a['unlinked_creator_label'])&ts}|{v['artwork_id'] for v in s['links'] if v['artist_id'] in aids}
            exact={a['id'] for a in s['artworks'] if r.m.norm(a['title']) in {r.m.norm(t) for t in f['titles']}}
            self.assertEqual(pool,set(c['creator_pool_ids']));self.assertEqual(exact,{a['id'] for a in c['exact_title_hits']})
if __name__=='__main__':unittest.main()
