import copy,importlib.util,unittest
from pathlib import Path

def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=module('pages','research-wien-museum-pages.py');a=module('apply_austria','import-austrian-catalogue.py')
def claim(v,qualifiers=None):return {'rank':'normal','mainsnak':{'snaktype':'value','datavalue':{'value':v}},'qualifiers':qualifiers or {}}
def entity(q,properties):return {'id':q,'claims':{k:[claim(v)] for k,v in properties.items()}}
class AustrianResearch(unittest.TestCase):
 def record(self):
  return {'qid':'Q100','title':'Synthetic painting','creator_qid':'Q101','creator_label':'Synthetic painter','institution_qid':'Q505873','date':{'first':1900,'last':1900},'entity':entity('Q100',{'P31':{'id':'Q3305213'},'P170':{'id':'Q101'},'P195':{'id':'Q505873'}}),'creator_entity':entity('Q101',{'P31':{'id':'Q5'}})}
 def test_scope_valid(self):a.validate_record(self.record())
 def test_late_work_held(self):
  x=self.record();x['date']['last']=1971
  with self.assertRaises(AssertionError):a.validate_record(x)
 def test_qualified_creator_held(self):
  x=self.record();x['entity']['claims']['P170'][0]['qualifiers']={'P1480':[claim({'id':'Q18122778'})]}
  with self.assertRaises(AssertionError):a.validate_record(x)
 def test_historical_holding_held(self):
  x=self.record();x['entity']['claims']['P195'][0]['qualifiers']={'P582':[claim({'time':'+1930-00-00T00:00:00Z'})]}
  with self.assertRaises(AssertionError):a.validate_record(x)
 def test_non_painting_held(self):
  x=self.record();x['entity']['claims']['P31']=[claim({'id':'Q860861'})]
  with self.assertRaises(AssertionError):a.validate_record(x)
 def html(self,licence='https://creativecommons.org/licenses/by/4.0/deed.de',caption='CC BY 4.0, Foto: Example, Wien Museum',extra=''):
  return f'''<h1>Synthetic painting</h1><dl class="object-details"><div><div class="row"><dt>Inventarnummer</dt><dd>TEST 1</dd></div></div></dl><figure data-object-image data-copy-text="Synthetic painting. Example, Wien Museum"><img class="object-image" src="https://sammlung.wienmuseum.at/images/objects/1/2_default.webp" data-src="https://sammlung.wienmuseum.at/images/objects/1/2_full.jpg" data-width="1500" data-height="1000"><span data-caption>{caption}</span></figure><div><a href="{licence}">Licence</a>{extra}<a download href="https://sammlung.wienmuseum.at/images/objects/1/2_full.jpg">Download</a></div>'''
 def parse(self,html):return p.parse(html,{'url':'https://sammlung.wienmuseum.at/objekt/1/'})
 def test_exact_media_licence_and_credit(self):
  x=self.parse(self.html());self.assertEqual(x['images'][0]['license'][2],'cc_by');self.assertEqual(x['facts']['Inventarnummer'],'TEST 1')
 def test_nc_image_rejected(self):self.assertIsNone(self.parse(self.html('https://creativecommons.org/licenses/by-nc/4.0/'))['images'][0]['license'])
 def test_conflicting_licences_rejected(self):self.assertIsNone(self.parse(self.html(extra='<a href="https://creativecommons.org/licenses/by-nc/4.0/">NC</a>'))['images'][0]['license'])
 def test_credit_required(self):self.assertIsNone(self.parse(self.html(caption='CC BY 4.0'))['images'][0]['license'])
 def test_unrelated_licence_not_applied(self):
  html=self.html().replace('2_full.jpg">Download','3_full.jpg">Download');self.assertIsNone(self.parse(html)['images'][0]['license'])
 def test_internal_api_rejected(self):
  with self.assertRaises(ValueError):p.p.permitted('https://sammlung.wienmuseum.at/api/objects')
 def test_robots_path_rejected(self):
  with self.assertRaises(ValueError):p.p.permitted('https://sammlung.belvedere.at/assets/main.js')
class AlternateWithoutPrimaryImage(unittest.TestCase):
 def test_missing_primary_can_be_searched_but_creator_conflict_still_fails(self):
  e=entity('Q100',{'P31':{'id':'Q3305213'},'P170':{'id':'Q101'},'P195':{'id':'Q505873'}});e['labels']={'en':{'value':'Synthetic painting'}}
  c={'qid':'Q100','title':'Synthetic painting','institution_qid':'Q505873','accession_number':None,'creators':[{'qid':'Q101'}],'creation_year_start':1900,'creation_year_end':1900}
  with self.assertRaises(ValueError):a.m.entity_match(c,e)
  self.assertIsNone(a.m.entity_match(c,e,require_primary_image=False))
  c['creators']=[{'qid':'Q102'}]
  with self.assertRaises(ValueError):a.m.entity_match(c,e,require_primary_image=False)

class CountryAffiliations(unittest.TestCase):
 def test_explicit_affiliations_and_historical_exclusions(self):
  c=module('country','reconcile-austrian-research-countries.py')
  for text,expected in [('Austrian painter',['AT']),('Austrian-born American painter',['US']),('Austro-Hungarian painter',[]),('Flemish painter',[]),('painter from Austria',['AT']),('Austrian-Italian painter',['AT','IT'])]:
   with self.subTest(text=text):self.assertEqual(c.affiliations(text),expected)

class HighlightFacts(unittest.TestCase):
 def html(self,kind='Painting',date='1901',artist='Synthetic Painter (1850 Vienna – 1910 Vienna)'):
  fields={'Artist':artist,'Person depicted':'Synthetic Sitter (1890 Vienna – 1950 Vienna)','Object type':kind,'Date':date,'Inventory number':'TEST-1','Medium':'Oil on canvas'}
  return '<h1>Synthetic portrait</h1>'+''.join('<div class="detailField"><div class="detailFieldLabel">'+k+'</div><div class="detailFieldValue">'+v+'</div></div>' for k,v in fields.items())
 def parse(self,**kwargs):
  b=module('belvedere','import-belvedere-highlights.py');return b.facts({'selection':{'object_id':'1','selection_url':'https://sammlung.belvedere.at/highlights/images'},'capture':{'url':'https://sammlung.belvedere.at/objects/1/synthetic'},'title':'Synthetic portrait'},self.html(**kwargs))
 def test_sitter_not_used_as_artist(self):self.assertEqual(self.parse()['creator_name'],'Synthetic Painter')
 def test_drawings_excluded(self):
  with self.assertRaises(ValueError):self.parse(kind='Drawing')
 def test_crossing_cutoff_held(self):
  with self.assertRaises(ValueError):self.parse(date='1968/1972')
 def test_qualified_attribution_held(self):
  with self.assertRaises(ValueError):self.parse(artist='After Synthetic Painter (1850 – 1910)')
 def test_source_approximate_range_preserved(self):
  x=self.parse(date='c. 1901/1902');self.assertEqual((x['creation_year_start'],x['creation_year_end'],x['date_precision']),(1901,1902,'circa_range'))

if __name__=='__main__':unittest.main()
