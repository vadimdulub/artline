"""Offline source hazards and identity regressions; no database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-france-second-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Evidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.ds={v['number']:v for v in r.build()}
    def test_multi_prefix_surname_is_in_identity_scope(self):
        c=self.ds[111]['comparison'];self.assertIn('tour',c['creator_terms']);self.assertTrue(c['creator_pool_ids']);self.assertEqual(self.ds[111]['state'],'editorial_hold')
        self.assertTrue(any('Pompadour' in a['title'] for a in c['leads']))
    def test_association_keeps_actual_private_source_label(self):
        f=self.ds[139]['facts'];self.assertTrue(f['holding_context_reference']);self.assertEqual(f['credit_line'],f['source_fields']['Statut_juridique']);self.assertTrue(f['credit_line'].startswith('propriété privée personne morale'))
    def test_association_exception_rejects_other_museum(self):
        d=copy.deepcopy(self.ds[139]['facts']['source_fields']);d['Code_Museofile']='M0381'
        self.assertIsNone(r.f.t.screen(d)[0])
    def test_association_requires_exact_location(self):
        d=copy.deepcopy(self.ds[139]['facts']['source_fields']);d['Localisation']='Toulouse ; autre musée'
        self.assertIsNone(r.f.t.screen(d)[0])
    def test_association_rejects_deposit_and_missing_flags(self):
        for key,value in [('Lieu_de_depot','Autre collection'),('MANQUANT','oui'),('Statut_juridique','propriété privée personne morale;dépôt;Toulouse;musée du vieux Toulouse')]:
            d=copy.deepcopy(self.ds[139]['facts']['source_fields']);d[key]=value;self.assertIsNone(r.f.t.screen(d)[0])
    def test_unknown_maker_and_medium_not_invented(self):
        f=self.ds[1]['facts'];self.assertIsNone(f['creator_label']);self.assertIsNone(f['medium']);self.assertEqual(self.ds[1]['state'],'approved_review_only_addition')
    def test_depicted_year_does_not_replace_object_date(self):
        f=self.ds[147]['facts'];self.assertIn('1900',f['title']);self.assertEqual((f['first'],f['last']),(1959,1959))
        f=self.ds[141]['facts'];self.assertEqual(f['first'],1833);self.assertIn('1775',f['source_fields']['Precisions_inscriptions']);self.assertEqual(f['work_type'],'drawing')
    def test_before_keeps_unknown_start_and_exclusive_end(self):
        f=self.ds[161]['facts'];self.assertIsNone(f['first']);self.assertEqual((f['last'],f['date_precision']),(1762,'before'))
    def test_composite_services_and_vases_not_inflated(self):
        for n in [64,159,162,168]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
        self.assertIn('Paire',self.ds[159]['facts']['title'])
    def test_conflicting_drawing_print_is_held(self):
        d=self.ds[117];self.assertEqual(d['state'],'editorial_hold');self.assertEqual(d['facts']['work_type'],'drawing');self.assertIn('roulette',str(d['facts']['source_fields']).lower())
    def test_conflicting_josephine_date_not_rewritten(self):
        d=self.ds[127];self.assertEqual(d['state'],'editorial_hold');self.assertEqual((d['facts']['first'],d['facts']['last']),(1701,1750))
    def test_copies_keep_their_makers_sizes_and_dates(self):
        a=self.ds[140]['facts'];b=self.ds[170]['facts'];self.assertIn('ANDRIEU',a['creator_label']);self.assertIn('Planet',b['creator_label']);self.assertNotEqual(a['inventory'],b['inventory']);self.assertNotEqual(a['dimensions_text'],b['dimensions_text']);self.assertIn("d'après",a['creator_label'])
    def test_close_jouas_formats_have_distinct_signed_dates(self):
        a=self.ds[86]['facts'];b=self.ds[94]['facts'];self.assertNotEqual(a['inventory'],b['inventory']);self.assertNotEqual(a['source_fields']['Precisions_inscriptions'],b['source_fields']['Precisions_inscriptions'])
        self.assertEqual(self.ds[98]['facts']['first'],1883)
    def test_same_format_market_sheets_keep_distinct_medium(self):
        a=self.ds[142]['facts'];b=self.ds[176]['facts'];self.assertEqual(a['dimensions_text'],b['dimensions_text']);self.assertNotEqual(a['medium'],b['medium']);self.assertEqual((a['inventory'],b['inventory']),('88.1.1','88.1.2'))
    def test_qualified_creator_labels_are_verbatim(self):
        for n in [108,124,126,132,153,155]:
            f=self.ds[n]['facts'];self.assertEqual(f['creator_label'],f['source_fields']['Auteur']);self.assertIn('attribu',f['creator_label'])
    def test_capture_status_and_body_hash_are_enforced(self):
        x=r.m.load(r.checked(self.ds[139]['source_reference']));bad=copy.deepcopy(x);bad['receipt']['status']=429
        with self.assertRaises(AssertionError):r.f.body(bad)
        bad=copy.deepcopy(x);bad['receipt']['sha256']='0'*64
        with self.assertRaises(AssertionError):r.f.body(bad)
    def test_indexed_identity_matches_independent_linear_scan(self):
        ix=r.m.load(r.IDENTITY);s=ix['state'];links=s['links']
        for n in [1,32,56,107,111,139,174]:
            d=self.ds[n];v=d['facts'];c=d['comparison'];ts=set(r.identity.terms(v));aids={a['id'] for a in s['artists'] if r.identity.i.tokens(a['display_name'])&ts}|{a['artist_id'] for a in s['aliases'] if r.identity.i.tokens(a['alias'])&ts}
            pool={a['id'] for a in s['artworks'] if r.identity.i.tokens(a['unlinked_creator_label'])&ts}|{l['artwork_id'] for l in links if l['artist_id'] in aids}
            exact={a['id'] for a in s['artworks'] if r.m.norm(a['title']) in {r.m.norm(t) for t in v['titles']}}
            inv={a['id'] for a in s['artworks'] if set(r.m.acc(a['accession_number']))&set(r.m.acc(v['inventory']))}
            self.assertEqual(pool,set(c['creator_pool_ids']));self.assertEqual(exact,{a['id'] for a in c['exact_title_hits']});self.assertEqual(inv,{a['id'] for a in c['inventory_hits']})
if __name__=='__main__':unittest.main()
