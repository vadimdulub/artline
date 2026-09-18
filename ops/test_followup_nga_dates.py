import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('dates',Path(__file__).with_name('research-followup-nga-original-dates.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class OriginalDateEvidence(unittest.TestCase):
 def test_explicit_year_is_not_lifespan(self):self.assertEqual(m.explicit_date({'displaydate':'1840','beginyear':'1800','endyear':'1870'},{'beginyear':'1800','endyear':'1870'}),(1840,1840,'exact'))
 def test_circa_retained(self):self.assertEqual(m.explicit_date({'displaydate':'c. 1840','beginyear':'1800','endyear':'1870'},{'beginyear':'1800','endyear':'1870'}),(1840,1840,'circa'))
 def test_unknown_or_open_dates_not_invented(self):
  for text in ('','unknown','after 1840','published 1840','1840?'):
   with self.subTest(text=text),self.assertRaises(ValueError):m.explicit_date({'displaydate':text,'beginyear':'1800','endyear':'1870'},{'beginyear':'1800','endyear':'1870'})
 def test_birth_year_does_not_supply_creation(self):
  with self.assertRaises(ValueError):m.explicit_date({'displaydate':'1800','beginyear':'1800','endyear':'1870'},{'beginyear':'1800','endyear':'1870'})
 def test_conflicting_creator_or_numeric_bounds_held(self):
  with self.assertRaises(ValueError):m.explicit_date({'displaydate':'1840','beginyear':'1839','endyear':'1841'},{'beginyear':'1800','endyear':'1870'})
if __name__=='__main__':unittest.main()
