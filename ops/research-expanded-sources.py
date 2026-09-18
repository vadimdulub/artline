#!/usr/bin/env python3
"""Exact, source-pinned metadata research for retained named-creator artworks."""
import argparse,collections,csv,hashlib,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
s=importlib.util.spec_from_file_location('planner',ROOT/'ops/plan-expanded-round2.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)

def closed_bio(text):
 m=re.fullmatch(r'[^\d]*(\d{4})\s*[-–—/]\s*(\d{4})\s*\)?\s*',text or '')
 if re.search(r'active|circa|ca\.|\bc\.|\?|born|died|after|before|about',text or '',re.I):m=None
 return (int(m[1]),int(m[2])) if m else (None,None)

def strict_date(text):
 # Parse only explicitly bounded years; keep every other literal date in review.
 if re.fullmatch(r'\s*(?:(?:c\.?|ca\.?|circa|about)\s*)?\d{4}(?:\s*[-–—/]\s*(?:\d{4}|\d{2}))?\s*',text or '',re.I):return p.date_literal(text)
 return {'first':None,'last':None,'precision':'unknown','display':text or 'Date unknown'}

def index(rows,museum):
 wanted=collections.defaultdict(list)
 for row in rows:
  if row['source'] is None and row['cells'][3]==museum:wanted[(p.namekey(row['cells'][0]),p.norm(row['cells'][1]),p.datestr(row['cells'][2]))].append(row)
 return wanted

def walters(rows,src):
 wanted=index(rows,'The Walters Art Museum');matches=collections.defaultdict(dict);counts=collections.Counter()
 ar=p.verify(src/'art.csv');cr=p.verify(src/'creators.csv');rel=p.verify(src/'relationships.csv')
 artists={a['id']:a for a in csv.DictReader((src/'creators.csv').open(encoding='utf-8-sig'))}
 for obj in csv.DictReader((src/'art.csv').open(encoding='utf-8-sig')):
  counts['objects_scanned']+=1;a=artists.get(obj['Creators'])
  if not a:continue
  keys=wanted.get((p.namekey(a['name']),p.norm(obj['Title']),p.datestr(obj['DateText'])),[])
  if not keys:continue
  if p.previous.QUALIFIED.search(a['name']) or re.search(r'\battributed\b|\bworkshop\b|\bcopy of\b|\bfollower of\b|\bschool of\b|\bpossibly\b',obj['Description'] or '',re.I):counts['attribution_review']+=len(keys);continue
  if 'painting' in obj['ObjectName'].lower():typ='watercolor' if 'watercolor' in obj['ObjectName'].lower() else 'painting'
  elif 'drawing' in obj['ObjectName'].lower():typ='drawing'
  elif 'illuminat' in obj['ObjectName'].lower():typ='manuscript_illumination'
  else:counts['unsupported_type']+=len(keys);continue
  birth,death=closed_bio(a['date']);person={'name':a['name'],'sort_name':a['sort_name'],'birth':birth,'death':death,'source_id':a['id'],'role':'artist','date_display':a['date'] or ''}
  d=strict_date(obj['DateText'])
  if re.fullmatch(r'\d{4}',obj['DateBeginYear'] or '') and int(obj['DateBeginYear'])>1970:counts['post_cutoff']+=len(keys);continue
  f={'source':'walters','object_id':obj['ObjectID'],'object_url':obj['ResourceURL'],'painter':person,'date':d,'type':typ,'medium':obj['Medium'],'dimensions':obj['Dimensions'],'accession':obj['AccessionNumber'],'evidence':[ar,cr,rel],'object_record':{k:v for k,v in obj.items() if k not in ['Images','MuseumLocation','Exhibitions']},'artist_record':a}
  for row in keys:matches[row['rid']]['walters:'+obj['ObjectID']]=f
 return matches,counts

def saam_person(text):
 m=re.fullmatch(r'(.*?),\s*born\s+[^\d]*(\d{4})\s*[-–—]\s*died\s+[^\d]*(\d{4})',text or '')
 if m and not re.search(r'ca\.|circa|about|\?',text,re.I):return {'name':m[1],'sort_name':m[1],'birth':int(m[2]),'death':int(m[3]),'source_id':'','role':'artist','date_display':text}
 m=re.fullmatch(r'(.*?),\s*born\s+[^\d]*(\d{4})',text or '')
 if m:return {'name':m[1],'sort_name':m[1],'birth':int(m[2]),'death':None,'source_id':'','role':'artist','date_display':text}
 name=re.split(r', (?:born|died|active|ca\.)',text or '',maxsplit=1)[0]
 return {'name':name,'sort_name':name,'birth':None,'death':None,'source_id':'','role':'artist','date_display':text}

def saam(rows,src):
 import urllib.parse
 wanted=index(rows,'Smithsonian American Art Museum');matches=collections.defaultdict(dict);counts=collections.Counter()
 files=sorted(src.glob('??.txt'));assert len(files)==256
 for path in files:
  receipt=p.verify(path)
  for line in path.read_text().splitlines():
   obj=json.loads(line);counts['objects_scanned']+=1;c=obj.get('content',{});ft=c.get('freetext',{});dnr=c.get('descriptiveNonRepeating',{})
   if obj.get('unitCode')!='SAAM' or dnr.get('metadata_usage',{}).get('access')!='CC0':continue
   authors=[a for a in ft.get('name',[]) if a.get('label')=='Artist']
   if len(authors)!=1:continue
   person=saam_person(authors[0]['content']);dates=[d['content'] for d in ft.get('date',[]) if d.get('label')=='Date']
   if len(dates)!=1:continue
   date=dates[0];keys={r['rid']:r for name in [authors[0]['content'],person['name']] for r in wanted.get((p.namekey(name),p.norm(dnr.get('title',{}).get('content')),p.datestr(date)),[])};keys=list(keys.values())
   if not keys:continue
   if p.previous.QUALIFIED.search(person['name']) or re.search(r'\b(after|possibly|probably|studio)\b',person['name'],re.I):counts['attribution_review']+=len(keys);continue
   types={r.get('content') for r in ft.get('objectType',[]) if r.get('label')=='Type'}
   if len(types)!=1:counts['type_review']+=len(keys);continue
   typ={'Painting':'painting','Drawing':'drawing','Print':'print','Watercolor':'watercolor'}.get(next(iter(types)))
   if not typ:counts['unsupported_type']+=len(keys);continue
   url=dnr.get('record_link') or '';oid=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query).get('id',[None])[0]
   if not oid or not url.startswith('https://americanart.si.edu/'):counts['url_review']+=len(keys);continue
   physical=ft.get('physicalDescription',[])
   text=lambda label:'; '.join(x['content'] for x in physical if x.get('label')==label)
   accession='; '.join(x['content'] for x in ft.get('identifier',[]) if x.get('label')=='Object number')
   d=strict_date(date)
   if d['first']==person['birth'] and d['last']==person['death'] and d['first'] is not None and d['last']-d['first']>20:d={'first':None,'last':None,'precision':'unknown','display':'Date unknown; source range matches the artist lifespan'}
   facts={'source':'saam','object_id':oid,'object_url':url,'painter':person,'date':d,'type':typ,'medium':text('Medium'),'dimensions':text('Dimensions'),'accession':accession,'evidence':[receipt],'object_record':{'id':obj['id'],'record_ID':dnr.get('record_ID'),'freetext':ft,'descriptiveNonRepeating':{k:v for k,v in dnr.items() if k!='online_media'}}}
   for row in keys:matches[row['rid']]['saam:'+oid]=facts
 return matches,counts

def notation(obj):
 values=obj.get('notation',[])
 if isinstance(values,dict):values=[values]
 return next((v['@value'] for v in values if v.get('@language')=='en'),next((v['@value'] for v in values if v.get('@language')=='nl'),''))

def single_timespan(value):
 if isinstance(value,list):return value[0] if len(value)==1 and isinstance(value[0],dict) else None
 return value if isinstance(value,dict) else None

def event_year(event):
 t=single_timespan((event or {}).get('timespan',{}))
 if t is None:return None
 names={x.get('content') for x in t.get('identified_by',[]) if x.get('type')=='Name'}
 if not names or any(not re.fullmatch(r'\d{4}(?:-\d{2}(?:-\d{2})?)?',n or '') for n in names):return None
 years={int(n[:4]) for n in names}
 return next(iter(years)) if len(years)==1 else None

def rijks(rows,src):
 wanted=collections.defaultdict(list)
 for r in rows:
  if r['source'] is None and r['cells'][3]=='Rijksmuseum':wanted[(p.namekey(r['cells'][0]),p.norm(r['cells'][1]),p.datestr(r['cells'][2]))].append(r)
 people={};receipts={};matches=collections.defaultdict(dict);counts=collections.Counter()
 for path in src.glob('person-*.json'):
  if path.name.endswith('.snapshot.json'):continue
  rec=p.verify(path);a=json.loads(path.read_text());people[a['id']]=a;receipts[a['id']]=rec
 for path in src.glob('object-*.json'):
  if path.name.endswith('.snapshot.json'):continue
  receipt=p.verify(path);obj=json.loads(path.read_text());counts['objects_scanned']+=1
  if 'painting' not in {notation(c) for c in obj.get('classified_as',[])}:continue
  production=obj.get('produced_by',{});parts=production.get('part',[])
  if len(parts)!=1:counts['production_parts_review']+=1;continue
  part=parts[0];authors=part.get('carried_out_by',[])
  if len(authors)!=1 or authors[0].get('type')!='Person':continue
  source_person=authors[0];a=people.get(source_person['id'])
  if not a:continue
  if re.search(r'\b(attributed|attribution|copy|copies|after|workshop|school|follower|circle|possibly|probably|anonymous|toegeschreven|kopie|naar|atelier|school|anoniem)\b',json.dumps(production,ensure_ascii=False),re.I):counts['attribution_review']+=1;continue
  name=notation(source_person);names={name}|{n.get('content') for n in a.get('identified_by',[]) if n.get('type')=='Name'}
  titles={n.get('content') for n in obj.get('identified_by',[]) if n.get('type')=='Name'}
  timespan=single_timespan(production.get('timespan',{}))
  if timespan is None:counts['multiple_creation_periods_review']+=1;continue
  dates={n.get('content') for n in timespan.get('identified_by',[]) if n.get('type')=='Name'}
  keys={r['rid']:r for n in names if n for t in titles if t for d in dates if d for r in wanted.get((p.namekey(n),p.norm(t),p.datestr(d)),[])}
  if not keys:continue
  person={'name':name,'sort_name':name,'birth':event_year(a.get('born')),'death':event_year(a.get('died')),'source_id':a['id'].rsplit('/',1)[1],'role':'artist','wikidata':next((e['id'].rsplit('/',1)[1] for e in a.get('equivalent',[]) if 'wikidata.org/entity/Q' in e['id']),'')}
  accession=next((n['content'] for n in obj.get('identified_by',[]) if n.get('type')=='Identifier' and any(c.get('id')=='http://vocab.getty.edu/aat/300312355' for c in n.get('classified_as',[]))),'')
  medium='; '.join(filter(None,[notation(x) for x in obj.get('made_of',[])]));dims=[]
  for d in obj.get('dimension',[]):
   unit={'http://vocab.getty.edu/aat/300379098':'cm','http://vocab.getty.edu/aat/300379097':'mm'}.get(d.get('unit',{}).get('id'))
   label=next((notation(x) for x in d.get('classified_as',[]) if notation(x)),'')
   if unit and label in ['height','width','depth','diameter'] and d.get('value'):dims.append(label+': '+str(d['value'])+' '+unit)
  for r in keys.values():
   date=strict_date(r['cells'][2]);oid=obj['id'].rsplit('/',1)[1]
   f={'source':'rijks','object_id':oid,'object_url':obj['id'],'painter':person,'date':date,'type':'painting','medium':medium,'dimensions':'; '.join(dims),'accession':accession,'evidence':[receipt,receipts[a['id']]],'object_record':{k:obj.get(k) for k in ['id','type','produced_by','identified_by','classified_as','made_of','dimension']},'artist_record':a}
   matches[r['rid']]['rijks:'+oid]=f
 return matches,counts

def fng_extra(rows,src):
 path=ROOT/'content/imports/expanded-round2-20260913/fng-objects.json';receipt=p.verify(path)
 orgs={'Valtion taideteostoimikunta':'State Art Commission, Finland','Kansallisgalleria / Nykytaiteen museo Kiasma, Helsinki':'Finnish National Gallery — Museum of Contemporary Art Kiasma'}
 wanted=collections.defaultdict(list)
 for r in rows:
  if r['source'] is None:wanted[(p.namekey(r['cells'][0]),p.norm(r['cells'][1]),p.norm(r['cells'][3]),p.datestr(r['cells'][2]))].append(r)
 matches=collections.defaultdict(dict);counts=collections.Counter()
 for o in json.loads(path.read_text()):
  museum=orgs.get(o.get('responsibleOrganisation'))
  if not museum:continue
  counts['scoped_objects_scanned']+=1
  if o.get('category',{}).get('categoryId')!='artwork':continue
  authors=[a for a in o.get('people',[]) if ((a.get('role') or {}).get('en') or '').lower()=='artist']
  if len(authors)!=1 or authors[0].get('attribution'):continue
  a=authors[0];name=' '.join(filter(None,[a.get('firstName'),a.get('familyName')]))
  y=o.get('yearFrom');end=o.get('yearTo') or y;text='' if y is None else str(y) if y==end else f'{y}–{end}'
  prefix=(o.get('datePrefix') or {}).get('en','');text=(prefix+' '+text).strip() if prefix else text
  candidates={r['rid']:r for title in set((o.get('title') or {}).values()) if title for r in wanted.get((p.namekey(name),p.norm(title),p.norm(museum),p.datestr(text)),[])}
  if not candidates:continue
  if o.get('children') or o.get('parents') or o['category'].get('en')=='part of a work':counts['multipart_review']+=len(candidates);continue
  classes={c.get('en') for c in o.get('classifications',[])};typ=next((typ for label,typ in [('painting','painting'),('drawing','drawing'),('graphic arts','print')] if label in classes),None)
  if not typ:counts['unsupported_type']+=len(candidates);continue
  person={'name':name,'sort_name':name,'birth':a.get('birthYear'),'death':a.get('deathYear'),'source_id':str(a['id']),'role':'artist'}
  date=strict_date(text)
  if y==person['birth'] and end==person['death'] and y is not None and end-y>20:date={'first':None,'last':None,'precision':'unknown','display':'Date unknown; museum range matches the artist lifespan'}
  dims=[]
  for d in o.get('dimensions',[]):
   if d.get('measurements') and d.get('unit'):dims.append(' × '.join(str(x) for x in d['measurements'])+' '+d['unit'])
  oid=str(o['objectId']);f={'source':'fng','object_id':oid,'object_url':'https://kokoelma.kansallisgalleria.fi/en/object/'+oid,'painter':person,'date':date,'type':typ,'medium':'; '.join(c.get('en') or c.get('fi') or '' for c in o.get('materials',[])),'dimensions':'; '.join(dims),'accession':o.get('inventoryNumber') or '', 'evidence':[receipt],'object_record':{k:v for k,v in o.items() if k not in ['multimedia','exhibitions','keywords']}}
  for r in candidates.values():matches[r['rid']]['fng:'+oid]=f
 return matches,counts

def main(number,source):
 out=ROOT/f'docs/research/expanded-round{number}-20260913';src=ROOT/f'content/imports/expanded-round{number}-20260913';rows=json.loads((out/'unlinked.json').read_text())
 matches,counts=globals()[source](rows,src)
 p.previous.save(out/'source-matches.json',matches);p.previous.save(out/'source-audit.json',{'source':source,'counts':dict(counts),'matched_candidates':len(matches)})
 p.previous.save(out/'source-paths.json',(['content/imports/expanded-round2-20260913/fng-objects.json','content/imports/expanded-round2-20260913/fng-objects.json.snapshot.json'] if source=='fng_extra' else [str(src.relative_to(ROOT))]));print(dict(counts),'matched',len(matches),flush=True)
 p.main(directory=out,matches_path=out/'source-matches.json',round_slug=f'round{number}')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--round',type=int,required=True);a.add_argument('--source',required=True);args=a.parse_args();main(args.round,args.source)
