import copy,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('writer',Path(__file__).with_name('apply-expanded-activity.py'));w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
class ActivityEvidenceTests(unittest.TestCase):
 def plan(self):
  return {'rid':'a'*64,'painter':{'name':'Example Artist','source_id':'museum-person-7'},'artist':{'new':True,'entity_type':'person','display_name':'Example Artist','birth_year':None,'death_year':None,'timeline_basis':'activity','active_start_year':1900,'active_end_year':1900},'patch':{'type':'painting','date':{'first':1900,'last':1900,'precision':'exact'}}}
 def check(self,r):
  with tempfile.TemporaryDirectory(prefix='artline-activity-policy-') as d:
   p=Path(d);raw=json.dumps([r]).encode();(p/'plan.json').write_bytes(raw);(p/'manifest.json').write_text(json.dumps({'sha256':hashlib.sha256(raw).hexdigest(),'links':1}));return w.load(p)
 def test_documented_work_does_not_invent_birth_or_death(self):
  _,rows=self.check(self.plan());self.assertIsNone(rows[0]['artist']['birth_year']);self.assertIsNone(rows[0]['artist']['death_year'])
 def test_unknown_work_date_cannot_establish_activity(self):
  r=self.plan();r['patch']['date']['precision']='unknown'
  with self.assertRaises(ValueError):self.check(r)
 def test_activity_requires_stable_museum_creator(self):
  r=self.plan();r['painter']['source_id']=''
  with self.assertRaises(ValueError):self.check(r)
 def test_cannot_expand_activity_beyond_documented_work(self):
  r=self.plan();r['artist']['active_start_year']=1800
  with self.assertRaises(ValueError):self.check(r)
 def test_anonymous_master_is_not_a_named_painter(self):
  r=self.plan();r['painter']['name']='Goodhart Ducciesque Master'
  with self.assertRaises(ValueError):self.check(r)
 def test_post_cutoff_work_cannot_anchor_a_new_painter(self):
  r=self.plan();r['artist']['active_start_year']=r['artist']['active_end_year']=1971;r['patch']['date'].update(first=1971,last=1971)
  with self.assertRaises(ValueError):self.check(r)
if __name__=='__main__':unittest.main()
