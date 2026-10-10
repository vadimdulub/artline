"""Real preserved primary-source pages; in-memory mutations, no database fixtures."""
import copy,gzip,importlib.util,re,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('review',Path(__file__).with_name('museum-1-10-arco-review-20261007.py'))
n=importlib.util.module_from_spec(s);s.loader.exec_module(n)


class ObjectMapEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        keys={'1600003003','0300045200'};cls.rows={}
        for path in n.old.RUN.glob('*/selection.json.gz'):
            for row in n.c.load(path)['candidates']:
                key=row['index_row']['work'].rsplit('/',1)[-1]
                if key in keys:cls.rows[key]=row
        cls.terlizzi=gzip.decompress((n.old.RUN/'pages/c0f3d381968885990e6aff462f90a1fc68100e3e378cbb98e103ece36f326273.html.gz').read_bytes())
        cls.sondrio=gzip.decompress((n.old.RUN/'pages/fcec6d8ae488326190101cfb5dc7bf2fe0a70e5d3f91364d556a70a3835dbfb1.html.gz').read_bytes())

    def test_exact_object_map_city_supports_missing_visible_address(self):
        value,reason=n.native(self.terlizzi,self.rows['1600003003']);self.assertIsNone(reason)
        self.assertEqual(value['city_evidence'],'explicit_same_object_map_municipality')
        self.assertNotIn('INDIRIZZO',value['native_fields'])
        self.assertEqual(value['facts']['creator_label'],'De Napoli Michele (attribuito)')

    def test_different_map_city_is_not_inferred_from_museum_name(self):
        raw=self.terlizzi.replace(b'"site_comune":["Terlizzi"]',b'"site_comune":["Roma"]')
        self.assertEqual(n.native(raw,self.rows['1600003003'])[1],'native_museum_city_conflict')

    def test_map_must_identify_this_exact_object(self):
        raw=self.terlizzi.replace(b'"typeOfRes":"/HistoricOrArtisticProperty/1600003003"',b'"typeOfRes":"/HistoricOrArtisticProperty/0000000000"')
        self.assertEqual(n.native(raw,self.rows['1600003003'])[1],'native_object_label_identity_requires_review')

    def test_plain_alternative_titles_do_not_erase_catalogue_label(self):
        value,reason=n.native(self.sondrio,self.rows['0300045200']);self.assertIsNone(reason)
        self.assertEqual(len(value['all_object_labels']),2)
        self.assertIn('(disegno, opera isolata)',value['object_label'])
        self.assertEqual((value['facts']['first'],value['facts']['last']),(1716,1767))

    def test_conflicting_object_category_labels_still_require_review(self):
        raw=self.sondrio.replace(b'ancona per l',b'altare (dipinto) ancona per l')
        self.assertEqual(n.native(raw,self.rows['0300045200'])[1],'native_object_label_ambiguity')

    def test_explicit_loan_is_not_overridden_by_map_evidence(self):
        raw=self.terlizzi.replace('proprietà Ente pubblico territoriale'.encode(),'proprietà Ente pubblico territoriale; in prestito'.encode())
        self.assertEqual(n.native(raw,self.rows['1600003003'])[1],'native_custody_requires_review')


if __name__=='__main__':unittest.main()
