"""Offline regressions for source identity/date boundaries; no database writes."""
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('prado',Path(__file__).with_name('expand-prado-catalogue-20261006.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class PradoSelection(unittest.TestCase):
    def test_single_year_cutoff(self):
        self.assertFalse(m.date('1970')['review'])
        self.assertTrue(m.date('1971')['review'])
        self.assertTrue(m.date('Hacia 1970')['review'])

    def test_crossing_range_requires_review(self):
        d=m.date('1968–1972');self.assertEqual((d['first'],d['last']),(1968,1972));self.assertTrue(d['review'])

    def test_creation_cannot_come_from_prose(self):
        for text in ['', 'Restaurado en 1880', '1630, repintado en 1880', '1660 (?)', '1900-1800']:
            with self.subTest(text=text):
                d=m.date(text);self.assertIsNone(d['first']);self.assertIsNone(d['last']);self.assertTrue(d['review'])

    def test_open_intervals_keep_unknown_bound(self):
        self.assertIsNone(m.date('Antes de 1600')['first'])
        self.assertIsNone(m.date('Después de 1600')['last'])
        self.assertTrue(m.date('Después de 1600')['review'])

    def test_century_is_enclosing_not_invented_exact_year(self):
        d=m.date('Segunda mitad del siglo XVII');self.assertEqual((d['first'],d['last'],d['precision']),(1601,1700,'century'))
        self.assertEqual(d['display'],'Segunda mitad del siglo XVII')
        self.assertTrue(m.date('Siglo XX')['review'])

    def test_components_remain_distinct(self):
        self.assertNotEqual(m.inventory('P001554/004-01'),m.inventory('P001554/004-02'))
        self.assertNotEqual(m.inventory('P001554/004'),m.inventory('P001554'))
        self.assertEqual(m.inventory('P008071'),m.inventory('P 8071'))

    def test_languages_share_native_identity(self):
        self.assertEqual(m.native('https://www.museodelprado.es/en/the-collection/art-work/name/abc'),m.native('https://www.museodelprado.es/coleccion/obra-de-arte/nombre/abc'))

    def test_whole_source_coverage_and_exclusions(self):
        data=m.r.load(m.RUN/'painting-reconciled.json.gz')['records']
        self.assertEqual(len(data),7141)
        self.assertEqual(len({x['source_id']for x in data}),7141)
        self.assertFalse(any(x['outcome']=='identity_conflict'for x in data))
        for x in data:
            if x['outcome']=='excluded_post_1970':self.assertGreater(x['date']['first'],1970)
            if x['qualified_creator']:self.assertIsNone(x['artist_id'])

    def test_final_plan_does_not_invent_blank_creators_or_duplicate_qids(self):
        rows=m.r.load(m.RUN/'production-plan.json.gz')['records']
        imported=[]
        for x in rows:
            if not x['creator_label']:self.assertIsNone(x['artist_id'])
            if x['add_wikidata_identifier']:imported.extend(x['wikidata_ids'])
        self.assertEqual(len(imported),len(set(imported)))
        wisdom=[x for x in rows if x['accession']in ('P007728','P008170')]
        self.assertEqual(len({x['artwork_id']for x in wisdom}),2)
        self.assertTrue(all(not x['add_wikidata_identifier']and not x['image_leads']for x in wisdom))

if __name__=='__main__':unittest.main()
