#!/usr/bin/env python3
"""Preserve native titles and explicitly record primary-source date conflicts."""
import importlib.util,json,re,sys
from pathlib import Path
from urllib.parse import urlencode
spec=importlib.util.spec_from_file_location('b',Path(__file__).with_name('research-armenian-georgian-artworks.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
s=b.s;r=b.r

def capture():
 records=json.loads((s.RUN/'selected/catalogue.json').read_bytes())['selected'];ids=[x['qid'] for x in records if re.fullmatch(r'Q\d+',x['title'])]
 for start in range(0,len(ids),30):
  data,receipt=b.fetch('https://www.wikidata.org/w/api.php?'+urlencode({'action':'wbgetentities','ids':'|'.join(ids[start:start+30]),'props':'labels|aliases|claims|sitelinks','languages':'en|hy|ka|ru|mul','format':'json','maxlag':5}))
  for q,e in data['entities'].items():s.save(s.RUN/'native-title-entities'/(q+'.json'),{'entity':e,'receipt':receipt})
  print('Native title evidence',min(start+30,len(ids)),'/',len(ids),flush=True)
def refine():
 changes=[];records=json.loads((s.RUN/'selected/catalogue.json').read_bytes())['selected']
 for rec in records:
  q=rec['qid'];path=s.RUN/'ready'/(q+'.json');item=json.loads(path.read_bytes());record=item['record'];native=s.RUN/'native-title-entities'/(q+'.json')
  if native.exists():
   data=json.loads(native.read_bytes());e=data['entity'];title=next((e['labels'][lang]['value'] for lang in ['en','hy','ka','ru','mul'] if lang in e.get('labels',{})),None);assert title and not re.fullmatch(r'Q\d+',title),'Native title remains unresolved'
   record['title']=title;record['titles']=list(dict.fromkeys(record['titles']+r.labels(e)));record['entity']=e;record['entity_receipt']=data['receipt'];changes.append({'qid':q,'field':'title','value':title,'basis':'Source-native title; no invented translation'})
  if q=='Q138349988':
   record['date']={'first':None,'last':None,'precision':'unknown','display':'Date conflict: 1906 / 1909; under review','eligible':False};record['date_review']={'source_url':'https://www.fondationbeyeler.ch/fileadmin/user_upload/Ausstellungen/Ausstellungen_2023/web2_Saalheft_PIROSMANI_EN.pdf','page':18,'basis':'Beyeler identifies Five Princes Carousing as dated 1906; Wikidata currently states 1909. Work/date identity needs reconciliation. Original statements retained.'};item['image']=None;item['image_reason']='Primary exhibition catalogue and authority date conflict';changes.append({'qid':q,'field':'date','value':record['date'],'basis':record['date_review']})
  assert record['date']['precision']!='unknown' or not item['image']
  s.save(s.RUN/'final-ready'/(q+'.json'),item)
 s.save(s.RUN/'editorial-refinements.json',{'changes':changes,'at':s.core.now()});print('Final records',len(records),'refinements',len(changes),flush=True)
if __name__=='__main__':capture() if sys.argv[1]=='capture' else refine()
