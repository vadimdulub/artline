"""Offline identity-policy cases; never connect to a database."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('followup',Path(__file__).with_name('reconcile-creators-followup.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def artist(key='a',birth=1800,death=1870,authorities=None):
    return {'id':key,'display_name':'Jean Example','aliases':['Example, Jean'],'birth_year':birth,'death_year':death,'status':'review','entity_type':'person','authorities':authorities or []}


class IdentityPolicy(unittest.TestCase):
    def test_name_alone_is_insufficient(self):
        match,reason=m.Matcher([artist()]).match({'name':'Jean Example'},'joconde')
        self.assertIsNone(match)

    def test_both_lifespan_boundaries_and_documented_variant(self):
        match,reason=m.Matcher([artist()]).match({'name':'Example, Jean','birth':1800,'death':1870},'joconde')
        self.assertIsNone(reason);self.assertEqual(match['artist']['id'],'a')

    def test_namesakes_are_not_merged(self):
        match,reason=m.Matcher([artist(),artist('b')]).match({'name':'Jean Example','birth':1800,'death':1870},'joconde')
        self.assertIsNone(match);self.assertEqual(reason,'ambiguous_identity')

    def test_identifier_conflicting_with_biography_is_held(self):
        match,reason=m.Matcher([artist(authorities=[{'scheme':'tate-person','id':'7'}])]).match({'name':'Jean Example','source_id':'7','birth':1801},'tate')
        self.assertIsNone(match);self.assertEqual(reason,'authority_biography_conflict')

    def test_verified_redirect_matches_original_identity(self):
        match,reason=m.Matcher([artist(authorities=[{'scheme':'wikidata','id':'Q110476382'}])],{'Q110476382':'Q334262'}).match({'name':'Jean Example','wikidata':'Q334262'},'wikidata')
        self.assertIsNone(reason);self.assertEqual(match['artist']['id'],'a')

    def test_different_existing_wikidata_identity_blocks_name_match(self):
        match,reason=m.Matcher([artist(authorities=[{'scheme':'wikidata','id':'Q999'}])]).match({'name':'Jean Example','wikidata':'Q123','birth':1800,'death':1870},'wikidata')
        self.assertIsNone(match);self.assertEqual(reason,'existing_wikidata_conflict')

    def test_workshop_label_is_not_a_person(self):
        match,reason=m.Matcher([artist()]).match({'name':'Workshop of Jean Example','birth':1800,'death':1870},'joconde')
        self.assertIsNone(match)


if __name__=='__main__':unittest.main()
