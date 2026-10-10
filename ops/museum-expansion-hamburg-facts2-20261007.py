#!/usr/bin/env python3
"""Retain supported unknowns and source calendars in the expanded Hamburg candidate review."""
import collections,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-hamburg-facts-20261007.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f);m=f.m;RUN=f.RUN;d=f.d;w=f.w;claims=f.claims;val=f.val;ref=f.ref

def label(e,langs=('de','en','mul','fr','it','nl')):return next((e.get('labels',{}).get(k,{}).get('value') for k in langs if e.get('labels',{}).get(k,{}).get('value')),None)
def year(v):
 assert v['calendarmodel'] in ['http://www.wikidata.org/entity/Q1985727','http://www.wikidata.org/entity/Q1985786'],'Unsupported source calendar'
 assert v['precision']>=9 and v['before']==v['after']==0,'Sub-year-resolution or bounded-uncertainty date requires review'
 assert re.fullmatch(r'\+\d{4}-\d\d-\d\dT00:00:00Z',v['time']),'Unsupported source time format'
 return int(v['time'][1:5])
def creation(r):
 qs=set(r.get('qualifiers',{}));assert not qs-{'P1319','P1326','P1480'},'Unreviewed creation qualifier'
 circa='P1480' in qs
 if circa:assert w.qualifier_value(r,'P1480')['id']=='Q5727902','Non-circa creation qualification'
 if qs&{'P1319','P1326'}:
  assert {'P1319','P1326'}<=qs,'Incomplete explicit creation range'
  first,last=year(w.qualifier_value(r,'P1319')),year(w.qualifier_value(r,'P1326'));precision='circa_range' if circa else 'range'
 else:first=last=year(val(r));precision='circa' if circa else 'exact'
 assert 100<=first<=last<=1970,'Creation outside supported pre1971scope'
 assert not(circa and last==1970),'Circa1970cutoff review required'
 return first,last,precision
def physical(e,labels):
 dimensions=[];materials=[]
 for p,name in [('P2048','Height'),('P2049','Width'),('P2610','Thickness')]:
  for r in claims(e,p):
   v=val(r)
   if not isinstance(v,dict):continue
   unit=v.get('unit','').rsplit('/',1)[-1];unit_label=label(labels.get(unit,{}).get('entity',{}),('en','mul','de'))
   dimensions.append(dict(property=p,label=name,value=v,unit_label=unit_label,qualifiers=r.get('qualifiers',{})))
 for r in claims(e,'P186'):
  v=val(r)
  if not isinstance(v,dict):continue
  materials.append(dict(value=v,label=label(labels.get(v.get('id'),{}).get('entity',{}),('en','mul','de')),qualifiers=r.get('qualifiers',{})))
 return dict(material_claims=materials,dimension_claims=dimensions)
def facts(e,labels):
 typ=w.one(e,'P31');assert val(typ)['id']=='Q3305213' and not typ.get('qualifiers'),'Qualified/non-painting type'
 col=w.one(e,'P195');assert val(col)['id']==f.QID,'Different collection'
 assert not set(col.get('qualifiers',{}))-{'P580'},'Historical/qualified collection'
 if col.get('qualifiers'):assert 100<=year(w.qualifier_value(col,'P580'))<=2026
 for prop in ['P276','P127']:
  if claims(e,prop):
   r=w.one(e,prop);assert val(r)['id']==f.QID and not r.get('qualifiers'),'Conflicting/qualified location or owner'
 cr=w.one(e,'P170');assert not cr.get('qualifiers'),'Qualified creator requires explicit review'
 cq=val(cr)['id'];maker=label(labels[cq]['entity']);assert maker,'Missing creator label'
 invs=claims(e,'P217');inventory=None
 if invs:
  inv=w.one(e,'P217');assert set(inv.get('qualifiers',{}))=={'P195'} and w.qualifier_value(inv,'P195')['id']==f.QID,'Inventory scope mismatch'
  inventory=val(inv);assert re.fullmatch(r'(?:HK-)?\d+(?:[a-zA-Z])?',inventory),'Compound/unfamiliar inventory'
 assert not any(claims(e,p) for p in ['P518','P361','P1877','P527']),'Component/copy/aggregate requires review'
 first,last,precision=creation(w.one(e,'P571'))
 title=label(e);assert title and not re.search(r'\b(triptych|diptych|predella|left wing|right wing)\b',title,re.I),'Component title requires review'
 urls=[val(r) for r in claims(e,'P973') if isinstance(val(r),str)];native=[u for u in urls if 'hamburger-kunsthalle.de/' in u]
 text=str(first) if first==last else str(first)+'–'+str(last);date_display=('circa ' if precision.startswith('circa') else '')+text
 titles=list(dict.fromkeys([v['value'] for v in e.get('labels',{}).values()]+[v['value'] for vs in e.get('aliases',{}).values() for v in vs]))
 return dict(source_id=e['id'],source_url='https://www.wikidata.org/wiki/'+e['id'],title=title,titles=titles,creator_label=maker,creator_qid=cq,identity_creator_labels=list(dict.fromkeys([v['value'] for v in labels[cq]['entity'].get('labels',{}).values()]+[v['value'] for vs in labels[cq]['entity'].get('aliases',{}).values() for v in vs])),date_display=date_display,first=first,last=last,date_precision=precision,inventory=inventory,native_page_urls=native,source_reference_urls=urls,work_type='painting',medium=None,dimensions_text=None,object_form=None,creation_statement=w.one(e,'P571'),collection_statement=col,**physical(e,labels),source_note='Current Wikidata statements with all original ranks, qualifiers and references retained. Inventory and native reference may be unknown; those absences are explicitly retained, not invented. Gregorian/Julian source calendar remains in evidence without calendar conversion. No museum-native verification, legal ownership or current-display claim.')
def main():
 objects={**f.sources('wikidata-selected-capture-001.json.gz'),**f.sources('wikidata-selected-capture-002.json.gz')};labels={**f.sources('wikidata-creator-capture-001.json.gz'),**f.sources('wikidata-extra-label-capture-002.json.gz')};assert len(objects)==260;rows=[]
 for qid,src in objects.items():
  e=src['entity']
  try:values=facts(e,labels)
  except (AssertionError,KeyError,TypeError) as ex:rows.append(dict(source_id=qid,title=label(e),source_reference=src['source_reference'],state='source_hold',reason=str(ex)))
  else:rows.append(dict(source_id=qid,facts=values,source_reference=src['source_reference'],state='candidate'))
 m.save(RUN/'wikidata-candidates-002.json.gz',dict(at=m.now(),rows=rows,counts=dict(collections.Counter(r['state'] for r in rows)),parser_reference=ref(Path(__file__).resolve()),policy='Expanded source triage only. Missing inventories/native references do not alone exclude named works, but each candidate still needs object-level identity and holding review. Source calendars and original claims remain explicit. Multiple current/historical collections are held, not silently selected by preferred rank.'))
 print(json.dumps(dict(counts=dict(collections.Counter(r['state'] for r in rows)),holds=dict(collections.Counter(r.get('reason') for r in rows if r['state']=='source_hold'))),ensure_ascii=False))
 for r in rows:
  if r['state']=='candidate':print(r['source_id'],r['facts']['creator_label'],r['facts']['title'],r['facts']['date_display'],r['facts']['inventory'])
if __name__=='__main__':main()
