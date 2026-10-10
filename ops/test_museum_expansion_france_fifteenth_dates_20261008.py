"""Source-preserving parsing of explicit French creation-date forms; no DB fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-france-fifteenth-native-20261008.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
class Dates(unittest.TestCase):
 def date(self,raw,period='18e siècle',creator='anonyme'):
  source=dict(Millesime_de_creation=raw,Periode_de_creation=period,Auteur=creator);before=copy.deepcopy(source);result=n.date_facts(source);self.assertEqual(source,before);return result
 def test_en_exact_retains_literal_display(self):
  d,e=self.date('En 1750');self.assertIsNone(e);self.assertEqual((d['first'],d['last'],d['date_precision'],d['date_display']),(1750,1750,'exact','En 1750'))
 def test_entre_retains_full_source_range(self):
  d,e=self.date('Entre 1740 et 1755');self.assertIsNone(e);self.assertEqual((d['first'],d['last'],d['date_precision'],d['date_display']),(1740,1755,'range','Entre 1740 et 1755'))
 def test_cutoff_year_inclusive(self):
  d,e=self.date('En 1970','20e siècle');self.assertIsNone(e);self.assertEqual(d['last'],1970)
 def test_postcutoff_exact_rejected(self):self.assertIsNone(self.date('En 1971','20e siècle')[0])
 def test_crossing_range_rejected(self):self.assertIsNone(self.date('Entre 1960 et 1980','20e siècle')[0])
 def test_reversed_range_rejected(self):self.assertIsNone(self.date('Entre 1755 et 1740')[0])
 def test_period_contradiction_rejected(self):self.assertIsNone(self.date('En 1750','19e siècle')[0])
 def test_lifespan_contradiction_rejected(self):self.assertIsNone(self.date('En 1750','18e siècle','Peintre (1800-1880)')[0])
 def test_qualified_en_not_forced_exact(self):
  for raw in ['En 1750 ?','En 1750 (supposé)','En 1750 ou 1755','Environ 1750']:self.assertIsNone(self.date(raw)[0])
 def test_before_keeps_unknown_lower_bound(self):
  d,e=self.date('Avant 1971','20e siècle');self.assertIsNone(e);self.assertIsNone(d['first']);self.assertEqual((d['last'],d['date_precision']),(1971,'before'))
if __name__=='__main__':unittest.main()
