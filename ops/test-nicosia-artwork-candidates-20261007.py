#!/usr/bin/env python3
"""Offline source/identity regression checks. No database or network access."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('candidates',Path(__file__).with_name('nicosia-artwork-candidates-20261007.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
s=importlib.util.spec_from_file_location('delivery',Path(__file__).with_name('nicosia-artwork-delivery-20261007.py'));delivery=importlib.util.module_from_spec(s);s.loader.exec_module(delivery)

class NicosiaEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=c.h.load(c.R/'artwork-candidates.json.gz');cls.rows=cls.p['records']
    def record(self,scheme,identifier):
        return next(f for f in self.rows if f['scheme']==scheme and f['source_id']==identifier)
    def test_cvar_calendar_month_not_abbreviated_year_range(self):
        for literal in ['1965-03','1880-10','1967 - 08']:
            actual=c.cvar_dates(literal);self.assertEqual(actual['first'],int(literal[:4]));self.assertEqual(actual['last'],int(literal[:4]));self.assertEqual(actual['date_display'],literal)
    def test_cvar_short_year_range_distinct_from_calendar(self):
        self.assertEqual((c.cvar_dates('1924-5')['first'],c.cvar_dates('1924-5')['last']),(1924,1925))
    def test_unknown_and_crossing_cutoff_not_invented(self):
        self.assertIsNone(c.dates('[s.d.]')['first']);self.assertIsNone(c.dates('')['last']);self.assertEqual(c.dates('20th century')['last'],2000)
    def test_makarios_fields_do_not_use_website_author_or_provenance_date(self):
        f=self.record('makarios-foundation-object','bmen001');self.assertEqual(f['creator_label'],'Unknown');self.assertEqual((f['first'],f['last']),(1201,1300));self.assertEqual(f['raw_fields']['Provenance'],'Church of Virgin Phaneromeni, Nicosia');self.assertIsNone(f['accession'])
    def test_horned_god_creation_is_not_catalogue_publication_or_accession_year(self):
        f=self.record('cyprus-museum-cultures-in-dialogue-2012','247');self.assertEqual((f['first'],f['last']),(-1300,-1101));self.assertEqual(f['accession'],'1949/V-20/6');self.assertEqual(f['raw_fields']['pdf_page'],246)
    def test_aphrodite_copy_dated_to_copy_not_hellenistic_original(self):
        f=self.record('cyprus-museum-cultures-in-dialogue-2012','291');self.assertEqual((f['first'],f['last']),(101,200))
    def test_leventis_unknown_year_remains_review_required(self):
        f=self.record('leventis-gallery-object','4758');self.assertIsNone(f['first']);self.assertIsNone(f['last']);self.assertIn('Not eligible',f['review_reason'])
    def test_confirmed_duplicate_keeps_both_native_records(self):
        f=self.record('leventis-gallery-object','4758');self.assertEqual(f['alternate_sources'][0]['source_id'],'6598');self.assertEqual(len(self.p['merged_source_duplicates']),3)
    def test_conflicting_inventory_excludes_both_objects(self):
        self.assertFalse(any(f.get('accession')=='AGLG 557'for f in self.rows));held=[x for x in self.p['held']if x['reason']=='conflicting_source_inventory_requires_object_review'];self.assertEqual({x['facts']['source_id']for x in held},{'6609','6610'})
    def test_no_source_images_downloaded_or_publication_requested(self):
        self.assertTrue(all(f['image_url']is None and 'status'not in f for f in self.rows));self.assertFalse(any(f['last']and f['last']>1970 for f in self.rows))
    def test_all_receipts_still_hash_to_original_sources(self):
        import gzip
        receipts={f['receipt']['body_path']:f['receipt']for f in self.rows}
        for path,rc in receipts.items():self.assertEqual(c.h.sha(gzip.decompress((c.n.REPO/path).read_bytes())),rc['sha256'])
    def test_no_planned_museum_missing_from_registry(self):
        slugs={x[0]for x in c.n.REGISTRY};self.assertTrue(all(f['museum_slug']in slugs for f in self.rows))
    def test_parenthesized_given_name_is_not_discarded(self):
        self.assertEqual(delivery.creator_key('[Bordone (Benedetto)]'),'benedetto bordone')
        self.assertNotEqual(delivery.creator_key('[Bordone (Benedetto)]'),delivery.creator_key('Paris Bordone'))
    def test_life_dates_do_not_break_full_name_identity(self):
        self.assertEqual(delivery.creator_key('Boudin, Eugène (1824–1898)'),delivery.creator_key('Eugène Boudin'))
    def test_incomplete_and_chronologically_impossible_creators_remain_labels(self):
        class Rows:
            def execute(self,*args):return self
            def fetchall(self):return [dict(artist=dict(id='marc',display_name='Franz Marc',birth_year=1880,death_year=1916),aliases=['Marc'])]
        facts=[dict(scheme='test',source_id=str(i),creator_label=label,first=1967,last=1967)for i,label in enumerate(['Marc','Franz Marc','Attributed to Franz Marc'])]
        _,assigned,_=delivery.artists(Rows(),facts)
        self.assertTrue(all(x is None for x in assigned.values()))

if __name__=='__main__':unittest.main()
