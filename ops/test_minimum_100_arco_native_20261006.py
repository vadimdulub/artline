import copy, gzip, importlib.util, re, unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('native',Path(__file__).with_name('minimum-100-arco-native-20261006.py'))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)


class PreservedSourceGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=gzip.decompress((n.RUN/'pages/6ceae9a634c6293f8b30d13995a7064414476d4e44079c1ac1652f225df351bd.html.gz').read_bytes())
        review=next(x for x in n.c.load(n.INDEX)['reviews']if any(y['work'].endswith('/0900067752')for y in x.get('candidate_source_ids',[])))
        cls.candidate=dict(scope=review,index_row=next(y for y in review['candidate_source_ids']if y['work'].endswith('/0900067752')))

    def test_preserves_disputed_creator_and_creation_range(self):
        value,reason=n.native(self.raw,self.candidate)
        self.assertIsNone(reason)
        self.assertEqual(value['facts']['creator_label'],'Ambito Romano')
        self.assertEqual((value['facts']['first'],value['facts']['last']),(1650,1674))
        self.assertIn('Trevisani',value['native_fields']['NOTIZIE STORICO CRITICHE'])
        self.assertIsNone(value['facts']['dimensions'])

    def test_different_museum_cannot_reuse_same_title(self):
        changed=copy.deepcopy(self.candidate)
        changed['scope']['authority']['source_institution_uri']='https://w3id.org/arco/resource/CulturalInstituteOrSite/other'
        self.assertEqual(n.native(self.raw,changed)[1],'native_museum_identity_conflict')

    def test_discovery_date_cannot_override_native_creation(self):
        changed=copy.deepcopy(self.candidate);changed['index_row']['date']='1960'
        self.assertEqual(n.native(self.raw,changed)[1],'index_native_creation_date_conflict')

    def test_native_id_cannot_be_substituted(self):
        changed=copy.deepcopy(self.candidate);changed['index_row']['work']=changed['index_row']['work'][:-1]+'3'
        self.assertEqual(n.native(self.raw,changed)[1],'native_id_conflict')

    def test_native_component_stays_out(self):
        raw=self.raw.replace(b'dipinto, opera isolata',b'dipinto, elemento di insieme')
        self.assertEqual(n.native(raw,self.candidate)[1],'native_ensemble_or_component_requires_review')

    def test_approximate_cutoff_requires_review(self):
        self.assertIsNone(n.a.numeric_date('ca 1970'))
        self.assertIsNone(n.a.numeric_date('1965-1975'))
        self.assertEqual(n.a.numeric_date('1970'),(1970,1970,'exact'))

    def test_missing_map_does_not_invent_a_category(self):
        raw=re.sub(rb'var addressPoints\s*=\s*\[.*?\];',b'var addressPoints = [];',self.raw,flags=re.S)
        value,reason=n.native(raw,self.candidate)
        self.assertIsNone(reason);self.assertIsNone(value['object_label'])
        self.assertEqual(value['facts']['creator_label'],'Ambito Romano')

    def test_public_custody_is_not_claimed_as_ownership(self):
        raw=self.raw.replace('proprietà Ente pubblico territoriale'.encode(),b'detenzione Stato')
        value,reason=n.native(raw,self.candidate)
        self.assertIsNone(reason)
        self.assertEqual(value['native_fields']['CONDIZIONE GIURIDICA'],'detenzione Stato')
        self.assertIn('no current display or independent legal ownership claim',value['facts']['holding_basis'])

    def test_explicit_comodato_loan_remains_held(self):
        raw=self.raw.replace(b'Come riferiva',b'Opera in comodato. Come riferiva')
        self.assertEqual(n.native(raw,self.candidate)[1],'qualified_or_historical_custody_requires_review')

    def test_publisher_inventory_correction_is_held(self):
        raw=self.raw.replace(b'Come riferiva',b'Il numero di inventario corrisponde a un altro dipinto. Come riferiva')
        self.assertEqual(n.native(raw,self.candidate)[1],'publisher_flags_incorrect_inventory_or_fields')


if __name__=='__main__':unittest.main()
