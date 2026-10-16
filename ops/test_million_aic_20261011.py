"""Regression cases from actual AIC source semantics; no database fixtures."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('aic',Path(__file__).with_name('million-aic-20261011.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class SourceSemantics(unittest.TestCase):
 def test_working_span_is_not_artwork_creation(self):
  self.assertIsNone(a.creation(dict(date_display='n.d.',date_start=1865,date_end=1880,date_qualifier_title="Artist's working dates")))
 def test_explicit_noncreation_qualifier_is_held(self):
  self.assertIsNone(a.creation(dict(date_display='1900',date_qualifier_title="Artist's working dates")))
 def test_cutoff_approximation_and_crossing_ranges(self):
  for text in ['c. 1970','1968–1971','1971','printed 1980 after a 1900 negative']:
   self.assertIsNone(a.creation(dict(date_display=text,date_qualifier_title='Made')))
  self.assertEqual(a.creation(dict(date_display='1869',date_qualifier_title='Made')),(1869,1869,'exact'))
 def test_component_parent_and_deaccession(self):
  base=dict(main_reference_number='1880.1',title='Priest and Boy')
  self.assertIsNone(a.physical_reason(base,set()))
  self.assertEqual(a.physical_reason(base,{'1880.1'}),'parent_inventory_has_component_records')
  self.assertEqual(a.physical_reason(dict(base,main_reference_number='1880.1a'),set()),'complex_or_component_inventory')
  self.assertEqual(a.physical_reason(dict(base,fiscal_year_deaccession=2020),set()),'deaccessioned_object')
 def test_culture_is_not_a_named_painter(self):
  row=dict(artist_ids=[1],artist_id=1,artist_title='Chinese',artist_display='Chinese')
  people={1:dict(record_sha256='sample',data=dict(title='Chinese',agent_type_title='Culture'))}
  result,reason=a.creator(row,people);self.assertEqual(result,[]);self.assertIn('nonindividual',reason)
 def test_qualified_creator_does_not_become_unqualified(self):
  person=dict(title='Test Painter',agent_type_title='Individual',api_link='https://api.artic.edu/api/v1/agents/1',birth_date=1800,death_date=1900)
  people={1:dict(record_sha256='sample',data=person)};row=dict(artist_ids=[1],artist_id=1,artist_title='Test Painter',artist_display='After Test Painter\nFrench, 1800–1900')
  self.assertEqual(a.creator(row,people)[0],[])
  result,_=a.creator(dict(row,artist_display='Attributed to Test Painter\nFrench, 1800–1900'),people);self.assertEqual(result[0]['prefix'],'attributed to')
 def test_activity_does_not_become_life_from_numeric_fields(self):
  person=dict(title='Test Painter',agent_type_title='Individual',api_link='https://api.artic.edu/api/v1/agents/1',birth_date=1800,death_date=1900)
  row=dict(artist_ids=[1],artist_id=1,artist_title='Test Painter',artist_display='Test Painter\nFrench, active 1840–1850')
  result,_=a.creator(row,{1:dict(record_sha256='sample',data=person)})
  self.assertIsNone(a.n.life.literal_life(result[0]['displaydate']))
 def test_qualified_authority_is_held_even_if_display_omits_it(self):
  for name in ['Imitator of Vincent van Gogh','Circle of Jacopo Sansovino']:
   person=dict(title=name,agent_type_title='Individual',api_link='https://api.artic.edu/api/v1/agents/1')
   row=dict(artist_ids=[1],artist_id=1,artist_title=name,artist_display='Artist\nItalian, 1486–1570')
   self.assertEqual(a.creator(row,{1:dict(record_sha256='sample',data=person)})[0],[])
 def test_conventional_master_identity_remains_anonymous(self):
  person=dict(title='Master F.V.B.',agent_type_title='Individual',api_link='https://api.artic.edu/api/v1/agents/1')
  row=dict(artist_ids=[1],artist_id=1,artist_title=person['title'],artist_display='Master F.V.B.\nNetherlandish, active 1475–1500')
  result,_=a.creator(row,{1:dict(record_sha256='sample',data=person)})
  self.assertEqual(result[0]['entity_type_hint'],'anonymous_master');self.assertIsNone(a.n.life.literal_life(result[0]['displaydate']))
if __name__=='__main__':unittest.main()
