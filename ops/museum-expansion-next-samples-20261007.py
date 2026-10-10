#!/usr/bin/env python3
"""Offline source validation and read-only identity checks for two complete samples."""
import argparse,copy,hashlib,importlib.util,json,re
from pathlib import Path
from bs4 import BeautifulSoup
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
a=module('ago','museum-expansion-ago-web-20261007.py');d=module('detroit','museum-expansion-detroit-native-20261007.py');i=module('identity','museum-expansion-yale-identity-20261007.py');n=module('creator','museum-expansion-nelson-facts-20261007.py');m=a.m;ref=a.ref
def ago():
 path=a.RUN/'web-objects-001/object-001.json';x=m.load(path);assert ref(m.ROOT/x['queue_reference']['path'])==x['queue_reference'];q=m.load(m.ROOT/x['queue_reference']['path'])['selected'][0]
 for r in q['index_references']:
  fp=m.ROOT/r['index_capture_reference']['path'];assert ref(fp)==r['index_capture_reference'];page=next(p for p in a.pages(m.load(fp)['result']) if p['web_ref']==r['index_web_ref']);assert {k:r[k] for k in a.index_rows(page)[0]} in a.index_rows(page)
 ps=a.pages(x['result']);assert len(ps)==1;p=ps[0];assert p['complete'] and p['source_call']==dict(method='click',args=x['request']) and x['request']==dict(ref_id=q['index_web_ref'],id=q['link_id'])
 url=a.cleanurl(p['url']);match=re.fullmatch(r'https://art\.ago\.ca/objects/(\d+)/[^/]+',url);assert match;lines=[t for no,t in p['lines'] if t];start=next(k for k,t in enumerate(lines) if t.startswith('# '));end=next(k for k,t in enumerate(lines) if t.startswith('We continue to research'))
 core=lines[start+1:end];fields={};rawfields={};key=None
 labels=['Creator','Date','Medium','Dimensions','Credit Line','Object number','Category','Copyright','Location']
 for t in core:
  label=next((v for v in labels if t==v or t.startswith(v+' ')),None)
  if label:assert label not in fields;key=label;fields[key]=[];rawfields[key]=[];t=t[len(label):].strip()
  assert key,(t,'Unmapped field');fields[key].append(a.plain(t));rawfields[key].append(t)
 fields={k:' '.join(t for t in vs if t) for k,vs in fields.items()};creator=n.creator(' '.join(rawfields['Creator']));title=lines[start][2:].strip()
 assert title==q['title'] and creator==q['creator_label'] and fields['Date']==q['date_display'] and fields['Category']=='* Paintings'
 facts=dict(source_id=match[1],native_object_id=match[1],source_url=url,native_page_urls=[url,'https://art.ago.ca/objects/'+match[1]],native_metadata_urls=[],wikidata_ids=[],title=title,titles=[title],creator_label=creator,detail_creator_label=creator,identity_creator_labels=[creator],date_display=fields['Date'],**a.creation(fields['Date']),inventory=fields['Object number'],medium=fields['Medium'],dimensions_text=fields['Dimensions'],work_type='painting',object_form=None,credit_line=fields['Credit Line'],source_fields=fields,source_rights=fields['Copyright'],source_metadata=p['source_metadata'],source_note='Complete official object-page web extraction, not original object HTTP bytes. Literal creator, date, credit, accession, category and photo copyright retained. Gallery text is source evidence only; no current-display claim.')
 return dict(provider='ago',institution_id=a.IID,source_id=match[1],facts=facts,source_reference=ref(path),source_references=[ref(path)]+[r['index_capture_reference'] for r in q['index_references']],retrieved_at=x['at'],state='source_candidate')
def detroit():
 path=d.RUN/'sample-object-001.json.gz';x=m.load(path);soup=BeautifulSoup(d.body(x['capture']),'html.parser');fields=[]
 for node in soup.select('.artwork_details > p'):
  label=node.select_one('label');assert label
  tooltip=label.select_one('.tooltip')
  if tooltip:tooltip.decompose()
  key=label.get_text(' ',strip=True);label.decompose();fields.append(dict(label=key,value=node.get_text(' ',strip=True)))
 ff={v['label']:v['value'] for v in fields};assert len(ff)==len(fields)
 p=d.RUN/'sample-metadata-001.json.gz';meta=m.load(p);raw=d.body(meta['capture']);assert raw.decode()==meta['text'];j=json.loads(raw)
 assert j['source']['museum']=='Detroit Institute of Arts' and str(j['core']['objectID'])=='109832';core=j['core'];creator='; '.join(v['displayName'] for v in j['creators']);assert all(v['role']=='Artist' for v in j['creators'])
 for h,k in [('Title','primaryTitle'),('Artwork Date','dated'),('Accession Number','objectNumber'),('Dimensions','dimensions'),('Classification','classification'),('Department','department'),('Medium','medium')]:assert m.norm(ff[h])==m.norm(core[k]),(h,k)
 assert ff['Artist']==creator and ff['Credit']==j['provenance']['creditLine'];assert soup.h1.get_text(' ',strip=True)==core['primaryTitle'];assert any(v.get_text(' ',strip=True)=='Metadata' and v['href']=='/download/metadata/109832' for v in soup.select('a[href]'))
 canonical=soup.select_one('link[rel=canonical]')['href'];assert canonical==x['url'];sections=[]
 for h in soup.select('h2.section-title'):
  node=copy.copy(h.parent)
  for tooltip in node.select('.tooltip'):tooltip.decompose()
  sections.append(dict(heading=h.get_text(' ',strip=True),classes=h.parent.get('class'),text=node.get_text(' ',strip=True)))
 facts=dict(source_id='109832',native_object_id='109832',source_url=canonical,native_page_urls=[canonical,'https://dia.org/collection/reading-fate-christ-child/109832',j['source']['objectURL']],native_metadata_urls=[meta['capture']['receipt']['url']],wikidata_ids=[],title=core['primaryTitle'],titles=[core['primaryTitle']],creator_label=creator,detail_creator_label=creator,identity_creator_labels=[creator,'Josefa de Ayala'],date_display=core['dated'],**d.creation(core['dated']),inventory=core['objectNumber'],medium=ff['Medium'],dimensions_text=core['dimensions'],work_type=core['objectName'],object_form=None,credit_line=j['provenance']['creditLine'],source_fields=fields,source_sections=sections,native_metadata=j,source_rights=j['rights'],source_note='Complete original official object HTML and linked JSON metadata agree on identity, date, materials, accession and credit. Literal metadata, artist biography, provenance, actual rights and unknown values retained as source evidence. Ayala is an identity search label from the cited source publication, not a catalogue creator rewrite. No images, legal-title or current-display claim.')
 return dict(provider='detroit',institution_id=d.IID,source_id='109832',facts=facts,source_reference=ref(path),source_references=[ref(path),ref(p)],retrieved_at=x['capture']['receipt']['retrieved_at'],state='source_candidate')
def facts():
 for fn,mod in [(ago,a),(detroit,d)]:
  row=fn();assert row['facts']['date_issue'] is None;m.save(mod.RUN/'complete-sample-candidate-001.json.gz',dict(at=m.now(),rows=[row],parser_reference=ref(Path(__file__).resolve()),policy='Source validation only. Fresh physical-object and duplicate identity review required before writes.'))
  print(json.dumps(dict(provider=row['provider'],facts={k:row['facts'][k] for k in ['title','creator_label','date_display','inventory','credit_line']})),flush=True)
def identity():
 for fn,mod in [(ago,a),(detroit,d)]:
  row=fn();i.RUN=mod.RUN;i.IID=mod.IID;p=i.params_for([row]);p['native_object_ids']=[]
  with m.connect() as db:
   state=i.queries(db,p);hits=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND external_id=%s AND (scheme ILIKE %s OR scheme ILIKE %s) ORDER BY entity_id,scheme,external_id",(row['source_id'],'%'+row['provider']+'%','%dia%' if row['provider']=='detroit' else '%ontario%')).fetchall()
   assert not hits,'Native IDs require additional scope';comps=i.comparisons([row],state)
  m.save(mod.RUN/'complete-sample-identity-001.json.gz',dict(at=m.now(),row=row,params=p,state=state,comparisons=comps,native_scheme_hits=hits,read_only=True))
  print(json.dumps(dict(provider=row['provider'],counts={k:len(v) for k,v in state.items()},comparisons=comps),ensure_ascii=False),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['facts','identity']);v=p.parse_args();globals()[v.command]()
