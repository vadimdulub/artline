import unittest
from exhibition_catalogue_links_20261013 import Identities,year

def artist(id='one',name='George Example',birth=1900,death=1970):
 return dict(id=id,display_name=name,birth_year=birth,death_year=death)
def index(artists,identifiers=None):return Identities(dict(artists=artists,aliases=[],identifiers=identifiers or []))
class IdentityTests(unittest.TestCase):
 def test_name_alone_does_not_link_or_duplicate(self):
  i=index([artist()]);self.assertIsNone(i.resolve('museum','1',['George Example'],None,None,'https://example.test/1',{}));self.assertFalse(i.new)
 def test_given_family_order_requires_matching_life_evidence(self):
  i=index([artist()]);r=i.resolve('museum','1',['EXAMPLE George'],1900,1970,'https://example.test/1',{});self.assertEqual(r['id'],'one');self.assertFalse(r['new'])
 def test_authority_does_not_override_conflicting_life_dates(self):
  i=index([artist()], [dict(entity_id='one',scheme='wikidata',external_id='Q1')]);self.assertIsNone(i.resolve('museum','1',['Different spelling'],1901,1970,'https://example.test/1',{'authority':{'wikiID':'Q1'}}))
 def test_duplicate_authority_stays_unresolved(self):
  i=index([artist(),artist('two')],[dict(entity_id=id,scheme='wikidata',external_id='Q1')for id in ['one','two']]);self.assertIsNone(i.resolve('museum','1',['George Example'],1900,1970,'https://example.test/1',{'authority':{'wikiID':'Q1'}}))
 def test_source_aliases_reuse_new_identity(self):
  i=index([]);a=i.resolve('a','1',['George Example','Example George'],1900,1970,'https://example.test/1',{});b=i.resolve('b','2',['EXAMPLE George'],1900,1970,'https://example.test/2',{});self.assertEqual(a['id'],b['id']);self.assertEqual(len(i.new),1)
 def test_qualified_or_unknown_years_are_not_invented(self):
  for value in ['c. 1900','1900?','1900–1910','active 1900','',None]:self.assertIsNone(year(value))
  self.assertEqual(year('1900-02-03'),1900)
if __name__=='__main__':unittest.main()
