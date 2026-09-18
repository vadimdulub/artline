import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('origin',Path(__file__).with_name('overnight-commons-origin.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class OriginalProvenance(unittest.TestCase):
 def page(self,credit):return {'imageinfo':[{'extmetadata':{'Credit':{'value':credit}}}]}
 def test_own_photograph(self):self.assertEqual(m.verify({},self.page('Own work')),'independent_photographer')
 def test_exact_institution_subdomain(self):self.assertEqual(m.verify({'website_url':'https://museum.example'},self.page('<a href="https://collection.museum.example/object/7">Source</a>')),'holding_institution_source')
 def test_similar_domain_does_not_match(self):
  with self.assertRaises(ValueError):m.verify({'website_url':'https://museum.example'},self.page('<a href="https://museum.example.invalid/object/7">Source</a>'))
 def test_national_portal_is_provenance_only(self):self.assertEqual(m.verify({},self.page('<a href="https://artuk.org/discover/artworks/example-123">Record</a>')),'institutional_cultural_record')
 def test_commercial_library_overrides_an_own_work_string(self):
  with self.assertRaises(ValueError):m.verify({},self.page('Own work copied from https://www.alamy.com/example'))
 def test_blog_is_not_cleared_by_a_commons_licence(self):
  with self.assertRaises(ValueError):m.verify({},self.page('<a href="https://example.blogspot.com/picture">Source</a>'))
 def test_unidentified_book_scan_fails(self):
  with self.assertRaises(ValueError):m.verify({},self.page('Copied from an art book'))
 def test_unknown_source_fails(self):
  with self.assertRaises(ValueError):m.verify({},self.page('Unknown source'))
 def test_secondary_search_service_fails(self):
  with self.assertRaises(ValueError):m.verify({},self.page('Google Arts & Culture'))
 def test_pushkin_website_copy_is_not_cleared_by_commons(self):
  with self.assertRaises(ValueError):m.verify({'website_url':'https://pushkinmuseum.art'},self.page('<a href="https://collection.pushkinmuseum.art/entity/PERSON/340">Source</a>'))
 def test_pushkin_holding_does_not_block_independent_photo(self):
  self.assertEqual(m.verify({'website_url':'https://pushkinmuseum.art'},self.page('Own work; photograph by User:Example')),'independent_photographer')
 def test_book_copy_overrides_an_own_work_string(self):
  with self.assertRaises(ValueError):m.verify({},self.page('1. Copied from an art book; 2. Own work'))
 def test_transferring_user_is_not_a_photographer(self):
  with self.assertRaises(ValueError):m.verify({},self.page('Transferred from de.wikipedia to Commons by User:Example'))
 def test_mirror_credit_is_not_cleared_by_a_museum_link(self):
  with self.assertRaises(ValueError):m.verify({'website_url':'https://museum.example'},self.page('http://allart.biz/example copied from https://museum.example/object/7'))
 def test_empty_source_fails(self):
  with self.assertRaises(ValueError):m.verify({},self.page(''))
if __name__=='__main__':unittest.main()
