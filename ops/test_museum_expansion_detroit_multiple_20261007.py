"""Original-source checks for multi-maker catalogue records."""
import importlib.util,unittest
from pathlib import Path
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
v=module('v','museum-expansion-detroit-followup-v2-20261007.py');old=module('old','museum-expansion-detroit-facts-20261007.py')
class Multiple(unittest.TestCase):
 def test_two_artists_are_one_physical_object(self):
  r=v.parse(v.f.RUN/'objects-001/object-060.json.gz');f=r['facts'];self.assertEqual(f['source_id'],'47961');self.assertEqual(f['inventory'],'38.31');self.assertEqual(f['creator_label'],'Adriaen van de Velde; Jan van der Heyden');self.assertEqual(len(f['source_makers']),2);self.assertIn('multiple_source_creators_review',r['review_flags'])
 def test_both_creators_are_searched_and_life_dates_are_not_creation(self):
  r=v.parse(v.f.RUN/'objects-001/object-060.json.gz');self.assertEqual(set(v.i.params_for([r])['patterns']),{'%velde%','%heyden%'});f=r['facts'];self.assertEqual((f['first'],f['last'],f['date_precision']),(1670,1670,'circa'));self.assertEqual(f['source_makers'][0]['biography'],'Dutch, 1636-1672')
 def test_single_and_unknown_source_facts_are_preserved(self):
  for n in [1,7,9]:
   p=v.f.RUN/('objects-001/object-%03d.json.gz'%n);a=old.parse(p)['facts'];b=v.f.parse(p)['facts'];self.assertEqual(b.pop('source_makers'),[]);self.assertEqual(a,b)
if __name__=='__main__':unittest.main()
