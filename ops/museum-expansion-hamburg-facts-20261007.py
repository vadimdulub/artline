#!/usr/bin/env python3
"""Conservative source-level candidate extraction; selection still requires editorial identity review."""
import collections,gzip,hashlib,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-hamburg-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;RUN=d.RUN
s=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-walker-holdings-20261007.py'));w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
QID='Q169542'
def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def sources(name):
 out={}
 for rr in m.load(RUN/name)['batches']:
  path=m.ROOT/rr['path'];assert ref(path)==rr
  v=m.load(path);raw=gzip.decompress((m.ROOT/v['capture']['body_path']).read_bytes());rc=v['capture']['receipt']
  assert hashlib.sha256(raw).hexdigest()==rc['sha256'] and rc['status']==200 and rc['url']==rc['final_url']
  assert json.loads(raw)['entities']==v['entities'] and set(v['entities'])==set(v['ids'])
  for key,e in v['entities'].items():assert key not in out;out[key]=dict(entity=e,source_reference=rr,capture=v['capture'])
 return out
def label(e):return next((e.get('labels',{}).get(k,{}).get('value') for k in ['de','en','fr','it','nl'] if e.get('labels',{}).get(k,{}).get('value')),None)
def claims(e,p):return [r for r in e.get('claims',{}).get(p,[]) if r['rank']!='deprecated']
def val(r):return r.get('mainsnak',{}).get('datavalue',{}).get('value')
def facts(e,creators):
 typ=w.one(e,'P31');assert val(typ)['id']=='Q3305213' and not typ.get('qualifiers'),'Qualified/non-painting type'
 col=w.one(e,'P195');assert val(col)['id']==QID,'Different collection'
 assert not set(col.get('qualifiers',{}))-{'P580'},'Historical/qualified collection'
 if col.get('qualifiers'):assert 100<=w.year(w.qualifier_value(col,'P580'))<=2026
 for prop in ['P276','P127']:
  if claims(e,prop):
   r=w.one(e,prop);assert val(r)['id']==QID and not r.get('qualifiers'),'Conflicting/qualified location or owner'
 cr=w.one(e,'P170');assert not cr.get('qualifiers'),'Qualified creator requires explicit review'
 cq=val(cr)['id'];maker=label(creators[cq]['entity']);assert maker,'Missing creator label'
 inv=w.one(e,'P217');assert set(inv.get('qualifiers',{}))=={'P195'} and w.qualifier_value(inv,'P195')['id']==QID,'Inventory scope mismatch'
 inventory=val(inv);assert re.fullmatch(r'(?:HK-)?\d+(?:[a-zA-Z])?',inventory),'Compound/unfamiliar inventory'
 assert not any(claims(e,p) for p in ['P518','P361','P1877','P527']),'Component/copy/aggregate requires review'
 first,last,precision=w.creation(w.one(e,'P571'))
 title=label(e);assert title and not re.search(r'\b(triptych|diptych|predella|left wing|right wing)\b',title,re.I),'Component title requires review'
 native=[val(r) for r in claims(e,'P973') if isinstance(val(r),str) and 'hamburger-kunsthalle.de/' in val(r)]
 assert native,'No native museum object reference'
 year_text=str(first) if first==last else str(first)+'–'+str(last);date_display=('circa ' if precision.startswith('circa') else '')+year_text
 titles=list(dict.fromkeys([v['value'] for v in e.get('labels',{}).values()]+[v['value'] for vs in e.get('aliases',{}).values() for v in vs]))
 return dict(source_id=e['id'],source_url='https://www.wikidata.org/wiki/'+e['id'],title=title,titles=titles,creator_label=maker,creator_qid=cq,identity_creator_labels=list(dict.fromkeys([v['value'] for v in creators[cq]['entity'].get('labels',{}).values()]+[v['value'] for vs in creators[cq]['entity'].get('aliases',{}).values() for v in vs])),date_display=date_display,first=first,last=last,date_precision=precision,inventory=inventory,native_page_urls=native,work_type='painting',medium=None,dimensions_text=None,object_form=None,creation_statement=w.one(e,'P571'),collection_statement=col,source_note='Wikidata structured claims and references, retained with raw HTTP evidence. Native object links are unfetched references because native search denies access. Secondary evidence does not establish current display or legal ownership. Physical details remain in raw claims pending explicit unit/material parsing.')
def main():
 objects=sources('wikidata-selected-capture-001.json.gz');creators=sources('wikidata-creator-capture-001.json.gz');rows=[]
 for qid,source in objects.items():
  e=source['entity']
  try:f=facts(e,creators)
  except (AssertionError,KeyError,TypeError) as ex:rows.append(dict(source_id=qid,title=label(e),source_reference=source['source_reference'],state='source_hold',reason=str(ex)))
  else:rows.append(dict(source_id=qid,facts=f,source_reference=source['source_reference'],state='candidate'))
 m.save(RUN/'wikidata-candidates-001.json.gz',dict(at=m.now(),rows=rows,counts=dict(collections.Counter(r['state'] for r in rows)),policy='Source candidates, not approved additions. All non-deprecated claims considered; preferred rank never hides conflicting historical/other holders. Original claims/qualifiers and references remain evidence.'))
 print(json.dumps(dict(counts=dict(collections.Counter(r['state'] for r in rows)),holds=dict(collections.Counter(r.get('reason') for r in rows if r['state']=='source_hold'))),ensure_ascii=False))
 for r in rows:
  if r['state']=='candidate':print(r['source_id'],r['facts']['creator_label'],r['facts']['title'],r['facts']['date_display'],r['facts']['inventory'])
if __name__=='__main__':main()
