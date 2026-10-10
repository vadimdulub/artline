"""Offline regressions for real source hazards; no databases or catalogue fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-five-museums-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Evidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.ds={v['number']:v for v in r.build()}
    def test_before_keeps_unknown_start_and_exclusive_endpoint(self):
        v=self.ds[157]['facts'];self.assertIsNone(v['first']);self.assertEqual((v['last'],v['date_precision']),(1867,'before'))
    def test_circa_uses_literal_period_not_invented_tolerance(self):
        v=self.ds[161]['facts'];self.assertEqual((v['first'],v['last'],v['date_precision']),(1801,1900,'circa_range'));self.assertIn('1830',v['date_display'])
    def test_1970_drawing_remains_eligible(self):
        v=self.ds[70];self.assertEqual(v['facts']['last'],1970);self.assertEqual(v['state'],'approved_review_only_addition')
    def test_twentieth_century_proof_not_seventeenth_century_plate(self):
        v=self.ds[85]['facts'];self.assertEqual((v['first'],v['last']),(1901,1950));self.assertIn('1630',v['source_fields']['Historique'])
    def test_blank_denomination_does_not_erase_explicit_domain(self):
        v=self.ds[130]['facts'];self.assertFalse(v['source_fields']['Denomination']);self.assertEqual(v['work_type'],'drawing');self.assertTrue(v['type_derivations'])
    def test_ceramic_vessel_not_image_subject(self):
        self.assertEqual(self.ds[101]['facts']['work_type'],'ceramic');self.assertEqual(self.ds[36]['facts']['work_type'],'print')
    def test_domain_and_technique_conflict_is_held(self):
        v=self.ds[108];self.assertEqual(v['state'],'editorial_hold');self.assertIn('eau-forte',v['facts']['source_fields']['Description'])
    def test_double_sided_board_counts_one(self):
        v=self.ds[154];self.assertEqual(v['state'],'approved_review_only_addition');self.assertIn(';',v['facts']['title']);self.assertIn('ONE',v['basis'])
    def test_shared_purchase_catalogue_not_duplicate_sheets(self):
        rows=[self.ds[n]['facts'] for n in [159,165,168,171,173,175,176]];self.assertEqual(len({v['inventory'].split(';')[0] for v in rows}),7);self.assertTrue(all('139' in v['inventory'] for v in rows))
    def test_album_and_conflicting_old_inventory_are_held(self):
        for n in [46,56,140]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
        self.assertTrue(any(v['relevant'] for v in self.ds[56]['comparison']['inventory_hits']))
    def test_maker_roles_and_attributed_labels_remain_literal(self):
        for n in [52,85,100,120]:self.assertEqual(self.ds[n]['facts']['creator_label'],self.ds[n]['facts']['source_fields']['Auteur'])
        self.assertIn('attribu',self.ds[52]['facts']['creator_label']);self.assertIn('anonyme',self.ds[85]['facts']['creator_label'])
    def test_bad_capture_status_or_hash_is_rejected(self):
        x=r.m.load(r.checked(self.ds[4]['source_reference']));bad=copy.deepcopy(x);bad['receipt']['status']=429
        with self.assertRaises(AssertionError):r.f.body(bad)
        bad=copy.deepcopy(x);bad['receipt']['sha256']='0'*64
        with self.assertRaises(AssertionError):r.f.body(bad)
    def test_indexed_comparator_agrees_with_simple_physical_identity_scan(self):
        # Independent linear reference for creator/title/inventory candidate sets.
        ix=r.m.load(r.IDENTITY);state=ix['state'];by={a['id']:a for a in state['artworks']};links=state['links']
        for n in [4,46,56,85,110,131]:
            row=self.ds[n];v=row['facts'];cmp=row['comparison'];ts=set(r.identity.terms(v));artist_ids={a['id'] for a in state['artists'] if r.identity.i.tokens(a['display_name'])&ts}|{a['artist_id'] for a in state['aliases'] if r.identity.i.tokens(a['alias'])&ts}
            pool={a['id'] for a in state['artworks'] if r.identity.i.tokens(a['unlinked_creator_label'])&ts}|{l['artwork_id'] for l in links if l['artist_id'] in artist_ids}
            exact={a['id'] for a in state['artworks'] if r.m.norm(a['title']) in {r.m.norm(t) for t in v['titles']}}
            inv={a['id'] for a in state['artworks'] if set(r.m.acc(a['accession_number']))&set(r.m.acc(v['inventory']))}
            self.assertEqual(pool,set(cmp['creator_pool_ids']));self.assertEqual(exact,{a['id'] for a in cmp['exact_title_hits']});self.assertEqual(inv,{a['id'] for a in cmp['inventory_hits']})
if __name__=='__main__':unittest.main()
