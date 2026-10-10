"""Preservation suite plus the actual album external-identifier regression."""
import importlib.util
import json
import unittest
from pathlib import Path

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

b=module('b','museum-expansion-larissa-reconciled-v2-20261010.py')
original=module('original','test_museum_expansion_larissa_20261010.py');original.a=b.a

class Larissa(original.Larissa):
    def test_physical_album_obeys_observed_source_scheme_unique_constraint(self):
        keys=[('artwork',v['artwork_id'],'searchculture-edm') for v in self.news for sid,url in b.a.identifier_values(v)]
        self.assertEqual(len(keys),184);self.assertEqual(len(set(keys)),184)
        self.assertEqual(b.a.identifier_values(self.by[176]),[(self.by[176]['facts']['source_ids'][0],self.by[176]['facts']['source_urls'][0])])
    def test_all_album_plate_sources_preserved_in_citation_and_images(self):
        album=self.by[176];evidence=json.loads(b.a.evidence(album,'offline'))['source_record']['facts']
        self.assertEqual(evidence['source_ids'],album['facts']['source_ids']);self.assertEqual(len(evidence['source_ids']),12)
        self.assertEqual({x['source_id'] for x in self.images if x['primary_number']==176},set(evidence['source_ids']))

if __name__=='__main__':unittest.main(verbosity=2)
