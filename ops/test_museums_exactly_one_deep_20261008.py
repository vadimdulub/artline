#!/usr/bin/env python3
import importlib.util,unittest,copy,json,io
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museums-exactly-one-artefact-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
s=importlib.util.spec_from_file_location('q',Path(__file__).with_name('museums-exactly-one-deep-qagoma-20261008.py'));q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
class Guards(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=a.d.load(a.RUN/'waves/artefact-corrected/source-verified.json.gz')['records'];cls.r=next(x for x in cls.records if x['facts']['title']=='Akatui');cls.raw=a.checked(cls.r['source_receipt'])
 def parse(self,raw=None,review=None):return a.parse(raw or self.raw,review or self.r['raw_source_record']['authority'],self.r['raw_source_record']['parsed']['index_candidate'])
 def test_pinned_native_fields(self):
  out,reason=self.parse();self.assertIsNone(reason);self.assertEqual(out['facts']['first'],1934);self.assertEqual(out['facts']['last'],1935)
 def test_wrong_museum_not_accepted(self):
  authority=copy.deepcopy(self.r['raw_source_record']['authority']);authority['names']=['Unrelated Museum'];self.assertEqual(self.parse(review=authority)[1],'collection_authority_requires_review')
 def test_wrong_canonical_not_accepted(self):self.assertEqual(self.parse(raw=self.raw.replace(b'/en/subject/akatuy',b'/en/subject/different-object'))[1],'native_canonical_conflict')
 def test_cutoff_on_creation_not_acquisition(self):self.assertEqual(a.dates('1971'),(1971,1971,'exact'));self.assertEqual(a.dates('1950-1980'),(1950,1980,'range'))
 def test_russian_decade_not_exact_year(self):self.assertEqual(a.dates('1920-е гг.')[:2],(1920,1929));self.assertNotEqual(a.dates('1920-е гг.')[2],'exact')
 def test_unknown_and_cross_century_not_invented(self):self.assertIsNone(a.dates('Дата неизвестна'));self.assertIsNone(a.dates('late 19th century–early 20th century'))
 def test_qualified_range_preserved(self):self.assertEqual(a.dates('around 1801–1802'),(1801,1802,'circa_range'))
 def test_no_swapped_range(self):self.assertIsNone(a.dates('1950-1900'))
 def test_explicit_anonymous_icon(self):
  r=next(x for x in self.records if x['facts']['title']=='The Galaktotrophousa');self.assertIsNone(r['facts']['creator_label']);self.assertEqual(r['facts']['object_form'],'icon')
 def test_russian_canonical_same_object_allowed(self):
  r=next(x for x in self.records if x['facts']['title']=='Одуванчики');self.assertTrue(r['facts']['source_url'].startswith('https://ar.culture.ru/ru/subject/oduvanchiki'))
 def test_qagoma_related_artists_are_excluded(self):
  r=next(x for x in a.d.load(a.RUN/'waves/qagoma-corrected/source-verified.json.gz')['records']if x['source_record_id']=='12117');p,reason=q.parse(a.checked(r['source_receipt']),'12117');self.assertIsNone(reason);self.assertEqual(p['creators'],['STREETON, Arthur']);self.assertEqual(p['facts']['first'],1900)
 def test_qagoma_wrong_object_number_rejected(self):
  r=a.d.load(a.RUN/'waves/qagoma-corrected/source-verified.json.gz')['records'][0]
  with self.assertRaises(AssertionError):q.parse(a.checked(r['source_receipt']),'999999')
if __name__=='__main__':
 stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Guards));print(stream.getvalue());assert result.wasSuccessful();a.d.save(a.RUN/'native-tests.json',dict(at=a.d.now(),tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),output=stream.getvalue()))
