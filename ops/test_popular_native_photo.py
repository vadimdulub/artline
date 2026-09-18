import copy
import datetime
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('native_photo',Path(__file__).with_name('popular-native-photo-images.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def claim(value):
    return {'mainsnak':{'snaktype':'value','datavalue':{'value':value}}}


class NativeInventory(unittest.TestCase):
    def setUp(self):
        self.c={'qid':'Q1','institution_qid':'Q2','institution_slug':'tate','website_url':'https://www.tate.org.uk',
                'source_record_url':'https://www.tate.org.uk/art/artworks/example-t123',
                'title':'Example','accession_number':'T123','creation_year_start':1850,'creation_year_end':1850,
                'creators':[{'qid':'Q3','name':'Synthetic Artist'}]}
        self.e={'id':'Q1','labels':{'en':{'value':'Example'}},'claims':{
            'P31':[claim({'id':'Q3305213'})],'P170':[claim({'id':'Q3'})],
            'P195':[claim({'id':'Q2'})],'P217':[claim('T123')],
            'P571':[claim({'time':'+1850-00-00T00:00:00Z','precision':9})]}}
        self.i={'id':'Q2','claims':{'P856':[claim('https://www.tate.org.uk/')]}}

    def test_exact_inventory_without_primary_image(self):
        m.verify_inventory(self.c,self.e,self.i)

    def test_semicolon_inventory_alias_preserves_stored_value(self):
        self.c['accession_number']='T123 ; OLD456'
        before=copy.deepcopy(self.c)
        m.common.entity_match(self.c,self.e,require_primary_image=False)
        self.assertEqual(self.c,before)

    def test_inventory_alias_is_not_a_prefix_or_substring_match(self):
        self.c['accession_number']='T1230 ; OLD456'
        with self.assertRaisesRegex(ValueError,'Accession conflict'):
            m.common.entity_match(self.c,self.e,require_primary_image=False)

    def test_similar_title_different_inventory(self):
        self.e['claims']['P217']=[claim('T124')]
        with self.assertRaises(ValueError):m.verify_inventory(self.c,self.e,self.i)

    def test_missing_inventory_cannot_match_by_title(self):
        self.e['claims'].pop('P217')
        with self.assertRaises(ValueError):m.verify_inventory(self.c,self.e,self.i)

    def test_uncertain_creation_cannot_be_invented(self):
        self.e['claims'].pop('P571')
        with self.assertRaises(ValueError):m.verify_inventory(self.c,self.e,self.i)

    def test_nearby_date_is_not_exact_inventory_confirmation(self):
        self.e['claims']['P571']=[claim({'time':'+1851-00-00T00:00:00Z','precision':9})]
        with self.assertRaises(ValueError):m.verify_inventory(self.c,self.e,self.i)

    def test_holding_museum_cannot_be_substituted(self):
        self.e['claims']['P195'].append(claim({'id':'Q4'}))
        with self.assertRaises(ValueError):m.verify_inventory(self.c,self.e,self.i)

    def test_historical_holding_is_not_current_evidence(self):
        self.e['claims']['P195'][0]['qualifiers']={'P582':[]}
        with self.assertRaises(ValueError):m.verify_inventory(self.c,self.e,self.i)

    def test_museum_authority_must_match_official_website(self):
        self.i['claims']['P856']=[claim('https://different.example')]
        with self.assertRaises(ValueError):m.verify_inventory(self.c,self.e,self.i)

    def test_unapproved_native_identifier_is_held(self):
        self.c['source_record_url']='https://unverified.example/object/123'
        with self.assertRaises(ValueError):m.verify_inventory(self.c,self.e,self.i)

    def test_attribution_conflict_is_held(self):
        self.e['claims']['P170']=[claim({'id':'Q5'})]
        with self.assertRaises(ValueError):m.verify_inventory(self.c,self.e,self.i)

    def test_discovery_queries_preserve_native_inventory_and_title(self):
        c=dict(self.c,accession_number='Ж-123')
        entity={'labels':{'ru':{'value':'Синтетическая картина'}}}
        self.assertEqual(m.photo.accession_queries(c,entity),['"Ж-123"','"Синтетическая картина"'])

    def test_search_control_characters_are_removed(self):
        c=dict(self.c,accession_number='T"123\n')
        self.assertEqual(m.photo.accession_queries(c,{}),['"T 123"'])


class CachedAuthority(unittest.TestCase):
    def test_only_intact_recent_requested_public_entity_is_reused(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);cache=root/'metadata';cache.mkdir()
            url='https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q1'
            key=hashlib.sha256(url.encode()).hexdigest()
            entity={'id':'Q1','claims':{}}
            content=json.dumps({'entities':{'Q1':entity}}).encode()
            receipt={'url':url,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),
                     'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
            (cache/(key+'.json')).write_bytes(content)
            path=cache/(key+'.receipt.json');path.write_text(json.dumps(receipt))
            self.assertEqual(m.verified_cached_entities(root,{'Q1'})['Q1'][0],entity)
            self.assertEqual(m.verified_cached_entities(root,{'Q2'}),{})
            receipt['retrieved_at']=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=49)).isoformat()
            path.write_text(json.dumps(receipt))
            self.assertEqual(m.verified_cached_entities(root,{'Q1'}),{})

    def test_modified_public_capture_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);cache=root/'metadata';cache.mkdir()
            url='https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q1'
            key=hashlib.sha256(url.encode()).hexdigest()
            (cache/(key+'.json')).write_text('{}')
            (cache/(key+'.receipt.json')).write_text(json.dumps({'url':url,'bytes':2,'sha256':'0'*64,
              'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}))
            with self.assertRaisesRegex(ValueError,'checksum'):m.verified_cached_entities(root,{'Q1'})


if __name__=='__main__':unittest.main()
