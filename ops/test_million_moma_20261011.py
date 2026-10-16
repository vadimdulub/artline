"""Offline MoMA selection boundaries; no database or production fixtures."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('moma',Path(__file__).with_name('million-moma-20261011.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class MomaSelection(unittest.TestCase):
 def test_creation_dates_do_not_hide_later_printing(self):
  self.assertEqual(a.dates('(1948)'),(1948,1948,'exact'))
  self.assertEqual(a.dates('1969–1970'),(1969,1970,'range'))
  self.assertIsNone(a.dates('1969–1971'))
  self.assertIsNone(a.dates('1930, printed 1980'))
 def test_parent_and_child_inventories_are_held(self):
  row=dict(AccessionNumber='22.1973.1',Title='Composition',Medium='Etching')
  self.assertIsNotNone(a.physical_reason(row,set()))
  self.assertIsNotNone(a.physical_reason(dict(row,AccessionNumber='22.1973'),{'22.1973'}))
  self.assertIsNone(a.physical_reason(dict(row,AccessionNumber='23.1973'),{'22.1973'}))
 def test_book_parts_do_not_count_as_standalone_objects(self):
  row=dict(AccessionNumber='10.1960',Title='Wrapper front',Medium='Engraving')
  self.assertIsNotNone(a.physical_reason(row,set()))
 def test_artist_identity_uses_native_authority_and_literal_biography(self):
  person=dict(ConstituentID='1',DisplayName='Person A',ArtistBio='American, born 1900',BeginDate='1900',EndDate='2100',**{'Wiki QID':''})
  people,reason=a.creators(dict(ConstituentID='1',Artist='Person A'),{'1':person})
  self.assertIsNone(reason);self.assertEqual(people[0]['displaydate'],'American, born 1900')
  self.assertEqual(a.creators(dict(ConstituentID='1',Artist='Person B'),{'1':person})[0],[])
  self.assertEqual(a.creators(dict(ConstituentID='1, 2',Artist='Person A, Person B'),{'1':person})[0],[])
 def test_selected_metadata_is_bounded_and_contains_no_downloaded_images(self):
  data=a.m.load(a.RUN/a.SELECTION);self.assertGreater(len(data['selected']),20000)
  ids=[r['native_id'] for r in data['selected']];self.assertEqual(len(ids),len(set(ids)))
  for r in data['selected']:
   self.assertEqual((r['first'],r['last'],r['precision']),a.dates(r['date_display']))
   self.assertLessEqual(r['last'],1970);self.assertEqual(r['images'],[])
   self.assertIsNone(a.physical_reason(r['raw'],set()))
 def test_after_title_preserves_qualified_source_creator(self):
  people={key:dict(ConstituentID=key,DisplayName=name,ArtistBio=bio,**{'Wiki QID':''}) for key,name,bio in [('1','Jacques Villon','1875–1963'),('2','Paul Cézanne','1839–1906')]}
  row=dict(ConstituentID='1, 2',Artist='Jacques Villon, Paul Cézanne',Title='Card Players, after Cézanne')
  actual,reason=a.creators(row,people)
  self.assertIsNone(reason);self.assertEqual([p['prefix'] for p in actual],['','after'])
  self.assertEqual(a.creators(dict(row,Title='Card Players, after an unknown artist'),people)[0],[])
if __name__=='__main__':unittest.main()
