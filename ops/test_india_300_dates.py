"""Creation-date boundaries for the Indian museum ingestion; no database use."""
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('india_facts',Path(__file__).with_name('india-300-facts-20261011.py'))
facts=importlib.util.module_from_spec(spec);spec.loader.exec_module(facts)

class CreationDates(unittest.TestCase):
 def test_creation_bounds(self):
  cases={
   '1970':(1970,1970,'eligible'),
   '1971':(1971,1971,'after_cutoff'),
   '1968-1972':(None,None,'date_review'),
   '20th Century CE':(None,None,'date_review'),
   '21st century':(2001,2100,'after_cutoff'),
   'C. Late 19th Century CE':(1801,1900,'eligible'),
   '17th - 18th century CE':(1601,1800,'eligible'),
   '3rd/4th century CE':(201,400,'eligible'),
   '2nd century BCE':(-200,-101,'eligible'),
   '3-2 century BC':(-300,-101,'eligible'),
   '200-100 BCE':(-200,-100,'eligible'),
   'Kushana period, c. 2nd century CE':(101,200,'eligible'),
   'Late 19th Century (1892)':(1892,1892,'eligible'),
   '19th Century (1952)':(None,None,'date_review'),
   'Modern':(None,None,'date_review'),
   'Not Known':(None,None,'date_review'),
  }
  for label,expected in cases.items():
   with self.subTest(label=label):self.assertEqual(facts.dates(label)[:3],expected)

if __name__=='__main__':unittest.main()
