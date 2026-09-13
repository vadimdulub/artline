#!/usr/bin/env python3
"""Offline, source-pinned second-round artwork/creator research plan."""
import collections,csv,hashlib,importlib.util,json,re,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/research/expanded-round2-20260913'
SRC=ROOT/'content/imports/expanded-round2-20260913'
spec=importlib.util.spec_from_file_location('previous',ROOT/'ops/reconcile-artwork-creators.py')
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)

def norm(s):
 return ' '.join(''.join(c for c in unicodedata.normalize('NFD',s or '').casefold() if not unicodedata.combining(c)).replace('’',"'").split())
def namekey(s):
 return ' '.join(sorted(re.findall(r'[^\W_]+',norm(s))))
def datestr(s):
 return re.sub(r'\s+','',norm(s).replace('–','-').replace('—','-'))
def verify(path):
 receipt=json.loads(path.with_name(path.name+'.snapshot.json').read_text())
 assert hashlib.file_digest(path.open('rb'),'sha256').hexdigest()==receipt['sha256']
 return receipt

def date_literal(text):
 m=re.fullmatch(r'(?:(c\.?|ca\.?|circa|about)\s*)?(\d{4})(?:\s*[-–/]\s*(\d{4}))?',text.strip(),re.I)
 if not m:
  short=re.fullmatch(r'(?:(c\.?|ca\.?|circa)\s*)?(\d{4})\s*[-–]\s*(\d{2})',text.strip(),re.I)
  if short:
   a=int(short[2]);b=a//100*100+int(short[3]);b+=100 if b<a else 0
   return {'first':a,'last':b,'precision':'circa_range' if short[1] else 'range','display':text}
  years=re.findall(r'\b\d{4}\b',text)
  # A museum's month/place wording with one explicit year is still dated.
  # Do not collapse open dates, disputed dates, or partially written ranges.
  rest=re.sub(r'\b\d{4}\b','',text)
  if len(years)==1 and not re.search(r'\d|\?|\b(after|before|or|unknown|undated|repaint|original)\b',rest,re.I):
   y=int(years[0]);return {'first':y,'last':y,'precision':'circa' if re.search(r'\b(circa|about)\b|\bc\.',text,re.I) else 'exact','display':text}
  return {'first':None,'last':None,'precision':'unknown','display':text or 'Date unknown'}
 a=int(m[2]);b=int(m[3] or a)
 if a>b:return {'first':None,'last':None,'precision':'unknown','display':text}
 return {'first':a,'last':b,'precision':('circa_range' if m[1] else 'range') if a!=b else ('circa' if m[1] else 'exact'),'display':text}

def main(evidence_only=False, directory=None, matches_path=None, round_slug="round2"):
 global OUT
 if directory is not None:OUT=Path(directory)
 if not evidence_only:assert not (OUT/'plan.json').exists(),'Preserve the reviewed plan; choose a fresh directory for a new round'
 pending=json.loads((OUT/'unlinked.json').read_text());artists=json.loads((OUT/'artists.json').read_text())
 identifiers={};names=collections.defaultdict(set);by_slug={a['slug']:a for a in artists}
 for a in artists:
  for x in a['identifiers']:identifiers[(x['scheme'],x['id'])]=a['slug']
  for n in [a['display_name'],a['sort_name'],*a['aliases']]:names[namekey(n)].add(a['slug'])
 nga=verify(SRC/'nga-constituents-altnames.csv');nga_alias_evidence={}
 with (SRC/'nga-constituents-altnames.csv').open(encoding='utf-8-sig') as file:
  for r in csv.DictReader(file):
   slug=identifiers.get(('nga-constituent',r['constituentid']))
   if slug and r['nametype'] not in ('Spouse',):
    for n in [r['displayname'],r['forwarddisplayname']]:
     if n and not previous.QUALIFIED.search(n):
      names[namekey(n)].add(slug);nga_alias_evidence[(namekey(n),slug)]=r
 decisions=collections.Counter(); new_artists={}; output=[]; holds=[]; painter_cache={}

 def painter_match(p,source):
  if previous.QUALIFIED.search(p['name']):return None,'qualified_creator'
  if re.search(r'\bu[0-9a-f]{4}\b',p['name'],re.I):return None,'escaped_unicode_name_review'
  birth,death=p.get('birth'),p.get('death')
  if birth is not None and death is not None and not 0<=death-birth<=125:return None,'biography_conflict'
  direct=set()
  for scheme,id in [(source+'-person',p.get('source_id')),('wikidata',p.get('wikidata'))]:
   if id and (scheme,id) in identifiers:direct.add(identifiers[(scheme,id)])
  candidates=set().union(*(names.get(namekey(n),set()) for n in [p['name'],p.get('sort_name','')]))
  def compatible(a):
   return a['status']!='archived' and a['entity_type']=='person' and not any(p.get(k) is not None and a[k+'_year'] is not None and p[k]!=a[k+'_year'] for k in ['birth','death'])
  if direct:
   if len(direct)!=1:return None,'authority_conflict'
   slug=next(iter(direct));a=by_slug[slug]
   if not compatible(a):return None,'authority_biography_conflict'
   basis='museum_authority_or_wikidata_id'
  else:
   matches=[s for s in candidates if compatible(by_slug[s]) and any(p.get(k) is not None and p[k]==by_slug[s][k+'_year'] for k in ['birth','death'])]
   if len(matches)==1:slug=matches[0];a=by_slug[slug];basis='documented_name_variant_and_biography'
   elif candidates:return None,'name_or_biography_ambiguous'
   else:
    # Do not create a second painter when a shortened-name match is plausible.
    tokens=set(namekey(p['name']).split())
    for existing in artists:
     if any(p.get(k) is not None and p[k]==existing[k+'_year'] for k in ['birth','death']):
      if any(tokens.intersection(namekey(n).split()) for n in [existing['display_name'],existing['sort_name']]):return None,'possible_shortened_name'
    if birth is None or death is None:return None,'new_creator_biography_incomplete'
    key=namekey(p['name'])+f':{birth}:{death}'
    slug=re.sub('[^a-z0-9]+','-',norm(p['name'])).strip('-')+'-'+round_slug+'-'+hashlib.sha256(key.encode()).hexdigest()[:12]
    a={'slug':slug,'display_name':p['name'],'sort_name':p.get('sort_name') or p['name'],'birth_year':birth,'death_year':death,'status':'review','entity_type':'person','new':True}
    a=new_artists.setdefault(key,a);basis='museum_named_creator_closed_biography'
  result={k:a[k] for k in ['slug','display_name','sort_name','birth_year','death_year','status','entity_type']};result['new']=a.get('new',False);result['basis']=basis
  alias=next((nga_alias_evidence[(namekey(n),slug)] for n in [p['name'],p.get('sort_name','')] if (namekey(n),slug) in nga_alias_evidence),None)
  if alias:result['additional_alias_evidence']={'record':alias,'snapshot':nga}
  return result,None

 if matches_path is not None:
  matches=json.loads(Path(matches_path).read_text())
 else:
  # Source-backed exact object matching for previously supplied-only candidates.
  wanted=collections.defaultdict(list)
  for r in pending:
   if r['source'] is None:wanted[(namekey(r['cells'][0]),norm(r['cells'][1]),norm(r['cells'][3]))].append(r)
  matches=collections.defaultdict(dict)
  moma_artist_receipt=verify(SRC/'moma-Artists.csv');moma_work_receipt=verify(SRC/'moma-Artworks.csv')
  with (SRC/'moma-Artists.csv').open(encoding='utf-8-sig') as file:ma={r['ConstituentID']:r for r in csv.DictReader(file)}
  with (SRC/'moma-Artworks.csv').open(encoding='utf-8-sig') as file:
   for obj in csv.DictReader(file):
    ids=wanted.get((namekey(obj['Artist']),norm(obj['Title']),norm('Museum of Modern Art (MoMA)')),[])
    if not ids:continue
    author=ma.get(obj['ConstituentID'])
    if not author or obj['Cataloged']!='Y':continue
    for r in ids:
     if datestr(obj['Date'])!=datestr(r['cells'][2]):continue
     worktype={'Painting':'painting','Drawing':'drawing','Print':'print','Illustrated Book':'print'}.get(obj['Classification'])
     if not worktype:continue
     p={'name':author['DisplayName'],'sort_name':author['DisplayName'],'birth':int(author['BeginDate'] or 0) or None,'death':int(author['EndDate'] or 0) or None,'source_id':author['ConstituentID'],'wikidata':author['Wiki QID'],'role':'artist'}
     f={'source':'moma','object_id':obj['ObjectID'],'object_url':obj['URL'] or 'https://www.moma.org/collection/works/'+obj['ObjectID'],'painter':p,'date':date_literal(obj['Date']),'type':worktype,'medium':obj['Medium'],'dimensions':obj['Dimensions'],'accession':obj['AccessionNumber'],'evidence':[moma_artist_receipt,moma_work_receipt],'object_record':{k:v for k,v in obj.items() if k not in ['ImageURL','OnView']},'artist_record':author}
     matches[r['rid']]['moma:'+obj['ObjectID']]=f
  print('MoMA exact object matches:',len(matches),flush=True)
  fng_receipt=verify(SRC/'fng-objects.json')
  orgs={'Kansallisgalleria / Ateneumin taidemuseo':'Finnish National Gallery — Ateneum Art Museum','Kansallisgalleria / Sinebrychoffin taidemuseo':'Finnish National Gallery — Sinebrychoff Art Museum','Kansallisgalleria / Nykytaiteen museo Kiasma':'Finnish National Gallery — Museum of Contemporary Art Kiasma'}
  for obj in json.loads((SRC/'fng-objects.json').read_text()):
   museum=orgs.get(obj.get('responsibleOrganisation'))
   if not museum or obj['category'].get('categoryId')!='artwork':continue
   authors=[a for a in obj['people'] if ((a.get('role') or {}).get('en') or '').lower()=='artist']
   if len(authors)!=1 or authors[0].get('attribution'):continue
   a=authors[0];name=' '.join(filter(None,[a.get('firstName'),a.get('familyName')]))
   titles=set((obj.get('title') or {}).values())-{None,''}
   candidates={r['rid']:r for title in titles for r in wanted.get((namekey(name),norm(title),norm(museum)),[])}
   if not candidates:continue
   classes={c.get('en') for c in obj['classifications']};worktype=next((typ for label,typ in [('painting','painting'),('drawing','drawing'),('graphic arts','print')] if label in classes),None)
   if not worktype or obj.get('children') or obj.get('parents') or obj['category'].get('en')=='part of a work':continue
   y=obj.get('yearFrom');end=obj.get('yearTo') or y
   text='' if y is None else str(y) if y==end else f'{y}–{end}'
   prefix=(obj.get('datePrefix') or {}).get('en','')
   if prefix:text=prefix+' '+text
   for r in candidates.values():
    if datestr(text)!=datestr(r['cells'][2]):continue
    dims=[]
    for d in obj['dimensions']:
     if d.get('measurements') and d.get('unit'):dims.append(' × '.join(str(x) for x in d['measurements'])+' '+d['unit'])
    p={'name':name,'sort_name':name,'birth':a.get('birthYear'),'death':a.get('deathYear'),'source_id':str(a['id']),'role':'artist'}
    date=date_literal(text)
    if y==p['birth'] and end==p['death'] and y is not None and end-y>20:
     date={'first':None,'last':None,'precision':'unknown','display':'Date unknown; museum range matches the artist lifespan'}
    f={'source':'fng','object_id':str(obj['objectId']),'object_url':'https://kokoelma.kansallisgalleria.fi/en/object/'+str(obj['objectId']),'painter':p,'date':date,'type':worktype,'medium':'; '.join(c.get('en') or c.get('fi') or '' for c in obj['materials']),'dimensions':'; '.join(dims),'accession':obj['inventoryNumber'],'evidence':[fng_receipt],'object_record':{k:v for k,v in obj.items() if k not in ['multimedia','exhibitions','keywords']}}
    matches[r['rid']]['fng:'+f['object_id']]=f
  print('New-source exact object matches:',len(matches),flush=True)
 previous.save(OUT/'new-source-matches.json',matches)
 if evidence_only:return

 for r in pending:
  reason=None
  if r['source']:
   f=r['facts'];p=f['painter'];source=r['source']
   check={'painter':p,'context':f.get('object_context',{}),'state':r['state'],'review':r['review'],'note':r['note'],'first':r['first'],'last':r['last'],'precision':r['precision'],'type':r['type']}
   reason=previous.blocked(check)
   evidence={'source':source,'object_id':f['object_id'],'object_url':f['object_url'],'painter':p,'evidence':f['evidence'],'original_facts_sha':r['source_sha'],'original_state':r['state'],'original_note':r['note'],'original_review':r['review']}
   patch=None
  else:
   possible=matches.get(r['rid'],{})
   if len(possible)!=1:
    decisions['no_unique_official_object']+=1;continue
   evidence=next(iter(possible.values()));source=evidence['source'];p=evidence['painter']
   patch={k:evidence[k] for k in ['date','type','medium','dimensions','accession']}
   d=patch['date']
   if d['first'] is not None and d['first']>1970:reason='post_cutoff'
  if not reason:
   cache_key=json.dumps([source]+[p.get(k) for k in ['name','sort_name','source_id','wikidata','birth','death']],sort_keys=True)
   if cache_key not in painter_cache:painter_cache[cache_key]=painter_match(p,source)
   a,reason=painter_cache[cache_key]
  if not reason:
   d=patch['date'] if patch else {'first':r['first'],'last':r['last'],'precision':r['precision']}
   typ=patch['type'] if patch else r['type']
   if d['precision']!='unknown' and ((a['birth_year'] is not None and d['last'] is not None and d['last']<a['birth_year']) or (typ=='painting' and a['death_year'] is not None and d['first'] is not None and d['first']>a['death_year'])):reason='creator_date_conflict'
  if reason:
   decisions[reason]+=1;holds.append({'rid':r['rid'],'reason':reason,'source':source});continue
  item={'rid':r['rid'],'slug':r['slug'],'entry_sha':r['entry_sha'],'label':r['label'],'cells':r['cells'],'source':source,'painter':p,'artist':a,'evidence':evidence,'patch':patch,'before':{k:r[k] for k in ['title','type','first','last','precision']}}
  output.append(item);decisions['link_'+source]+=1
 # Hold possible aliases between newly proposed painters instead of duplicating
 # an identity simply because neither name was in the pre-round catalogue.
 bios=collections.defaultdict(dict)
 for row in output:
  a=row['artist']
  if a['new']:bios[(a['birth_year'],a['death_year'])][a['slug']]=a
 alias_holds=set()
 for group in bios.values():
  values=list(group.values())
  for i,a in enumerate(values):
   for b in values[i+1:]:
    if set(namekey(a['display_name']).split()).intersection(namekey(b['display_name']).split()):
     alias_holds.update([a['slug'],b['slug']])
 filtered=[]
 for row in output:
  if row['artist']['new'] and row['artist']['slug'] in alias_holds:
   decisions['new_artist_alias_collision']+=1;decisions['link_'+row['source']]-=1
   holds.append({'rid':row['rid'],'reason':'new_artist_alias_collision'})
  else:filtered.append(row)
 output=filtered
 # One pinned source object must not enrich two separately staged physical objects.
 counts=collections.Counter((r['source'],r['evidence']['object_id']) for r in output)
 accepted=[]
 for r in output:
  if counts[(r['source'],r['evidence']['object_id'])]>1:
   decisions['duplicate_source_object']+=1;decisions['link_'+r['source']]-=1;holds.append({'rid':r['rid'],'reason':'duplicate_source_object'});continue
  accepted.append(r)
 previous.save(OUT/'plan.json',accepted);previous.save(OUT/'holds.json',holds)
 manifest={'version':2,'sha256':hashlib.sha256((OUT/'plan.json').read_bytes()).hexdigest(),'audited':len(pending),'links':len(accepted),'new_artist_count':len({r['artist']['slug'] for r in accepted if r['artist']['new']}),'existing_artist_count':len({r['artist']['slug'] for r in accepted if not r['artist']['new']}),'metadata_enrichments':sum(r['patch'] is not None for r in accepted),'decisions':dict(decisions)}
 previous.save(OUT/'manifest.json',manifest);print(json.dumps(manifest,indent=2),flush=True)
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--matches-only',action='store_true')
 main(parser.parse_args().matches_only)
