#!/usr/bin/env python3
"""Offline regression checks for consequential matching and sampling mistakes."""
import copy,gzip,hashlib,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
w=mod('wiki','reconcile-random-5000-wikiart-museums-20261006.py');v=mod('web','review-random-5000-web-discovery-20261006.py');p=mod('primary','refine-random-5000-primary-20261006.py');d=mod('delivery','apply-random-5000-museums-20261006.py')
n=mod('native','refine-random-5000-native-identities-20261006.py')
class MuseumResearchTests(unittest.TestCase):
    def test_year_is_not_an_inventory(self):
        self.assertFalse(v.inventory_match('1879','Painted in 1879; 56 x 45 cm.'))
        self.assertTrue(v.inventory_match('1879','Inventory number: 1879'))
    def test_accession_needs_token_boundary(self):
        self.assertFalse(v.inventory_match('SK-A-20','Object number SK-A-201'))
        self.assertTrue(v.inventory_match('SK-A-20','Object number SK-A-20'))
    def test_distinct_people_are_not_fuzzy_matched(self):
        self.assertFalse(w.creator_match('Pieter Bruegel the Younger',{w.norm('Pieter Bruegel the Elder')}))
        self.assertFalse(w.creator_match('Lucas Cranach the Younger',{w.norm('Lucas Cranach the Elder')}))
        self.assertTrue(w.creator_match('Martiros Sarian',{w.norm('Martiros Saryan')}))
    def test_encoding_preserves_version_suffix(self):
        self.assertEqual(w.urlkey('https://www.wikiart.org/en/a/sch%C3%B6ner'),w.urlkey('https://www.wikiart.org/en/a/schöner'))
        self.assertNotEqual(w.urlkey('https://www.wikiart.org/en/a/work'),w.urlkey('https://www.wikiart.org/en/a/work-1'))
    def test_city_distinguishes_generic_museums(self):
        self.assertNotEqual(w.ALIASES['National Gallery, London'],w.ALIASES['National Gallery, Oslo'])
        plan=w.r.load(w.RUN/'wikiart-holding-plan-v5.json.gz')
        for label,info in plan['institution_resolutions'].items():
            if label=='National Portrait Gallery, London, UK':self.assertNotEqual(info['institution']['id'],'609cb813-85e1-50d1-9c92-cfd932b90cfb')
    def test_sculpture_does_not_enter_painting_department(self):
        plan=w.r.load(w.RUN/'wikiart-holding-plan-v5.json.gz')
        self.assertNotIn('2834e858-5432-54e7-8e1c-00059cf10525',{c['artwork_id']for c in plan['claims']})
    def test_deposit_roles_keep_owner_and_recipient_distinct(self):
        o={'Nom_officiel_musee':'Musée des beaux-arts','Ville':'Bordeaux','Localisation':'Bordeaux ; Musée des beaux-arts','Statut_juridique':'propriété de la commune; Bordeaux; musée des beaux-arts','Lieu_de_depot':'dépôt;Bordeaux;Hôtel de ville'}
        self.assertEqual(p.deposit_role(o),'registered_museum_collection_with_separately_disclosed_deposit')
        o['Statut_juridique']='propriété de la commune; Rouen; musée des beaux-arts'
        self.assertIsNone(p.deposit_role(o))
        o['Lieu_de_depot']='dépôt;Bordeaux;Musée des beaux-arts'
        self.assertEqual(p.deposit_role(o),'documented_deposit_received_by_registered_museum')
        o['MANQUANT']='oui';self.assertIsNone(p.deposit_role(o))
    def test_frozen_sample_has_no_selection_bias_or_replacement(self):
        sample=w.r.load(w.RUN/'sample.json');frame=w.r.load(w.RUN/'sampling-frame.json.gz')
        expected=sorted(frame,key=lambda aid:(hashlib.sha256((sample['seed']+'/'+aid).encode()).digest(),aid))[:5000]
        self.assertEqual(sample['artwork_ids'],expected);self.assertEqual(len(set(expected)),5000)
    def test_local_catalogue_is_not_a_delivery_target(self):
        with self.assertRaises(AssertionError):d.production_connect('local',readonly=False)
    def test_modern_rijks_url_preserves_native_and_legacy_identity(self):
        c={'source_url':'https://www.rijksmuseum.nl/en/collection/object/A-new-path--abc','external_id':'url','scheme':'museum-catalogue-url','object_evidence':{'reviewed_indexed_object':{'excerpt':'Object number\nSK-A-2414\nPersistent URL\nhttps://id.rijksmuseum.nl/20026415','source_title':'A painting'}}}
        x=n.enrich(c);self.assertEqual((x['scheme'],x['external_id']),('rijks-object','20026415'))
        self.assertIn('https://www.rijksmuseum.nl/en/collection/SK-A-2414',x['duplicate_source_urls'])
        self.assertEqual(c['scheme'],'museum-catalogue-url')
    def test_ambiguous_permalink_is_not_promoted_to_native_id(self):
        c={'source_url':'https://www.rijksmuseum.nl/en/collection/object/Example','external_id':'url','scheme':'museum-catalogue-url','object_evidence':{'reviewed_indexed_object':{'excerpt':'https://id.rijksmuseum.nl/20000001 and https://id.rijksmuseum.nl/20000002','source_title':'Example'}}}
        self.assertEqual(n.enrich(c)['scheme'],'museum-catalogue-url')
    def test_legacy_capture_path_is_resolved_without_faking_http_status(self):
        plan=w.r.load(w.RUN/'primary-plans/wikiart-reviewed-native-reviewed.json.gz');c=next(x for x in plan['claims']if not x['source_receipt'].get('body_path'))
        rc=d.verified_receipt(c);self.assertEqual(rc['body_path'],c['object_evidence']['page']['capture']['body_path']);self.assertTrue(rc['http_status_not_observed']);self.assertNotIn('status',rc)
    def test_changed_evidence_is_rejected_before_delivery(self):
        c=copy.deepcopy(w.r.load(w.RUN/'primary-plans/wikiart-reviewed-native-reviewed.json.gz')['claims'][0]);c['source_receipt']=d.verified_receipt(c);c['source_receipt']['sha256']='0'*64
        with self.assertRaises(AssertionError):d.verified_receipt(c)
if __name__=='__main__':unittest.main()
