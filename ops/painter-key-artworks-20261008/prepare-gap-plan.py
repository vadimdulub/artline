import importlib.util,collections,re,urllib.parse,json,hashlib
from pathlib import Path
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
entities={k:v for p in (m.RUN/'entities').glob('*.json') for k,v in m.base.load(p).get('entities',{}).items()};pages={p['title'].replace('_',' '):p for path in (m.RUN/'commons').glob('*.json') for p in m.base.load(path).get('query',{}).get('pages',{}).values()};artists=m.base.load(m.RUN/'local-artists.json.gz');artist_byqid={q:a for a in artists for q in a['wikidata']};works=m.base.load(m.RUN/'local-works.json.gz');work_byqid={q:w for w in works for q in w['wikidata']};work_byartist=collections.defaultdict(list)
for w in works:work_byartist[w['artist_id']].append(w)
links={r['artist']['value'].split('/')[-1]:r['selected']['value'].split('/')[-1] for p in (m.RUN/'gap-candidates').glob('*.json') for r in m.base.load(p)['results']['bindings']}
def values(e,p):return [c['mainsnak']['datavalue']['value'] for c in e.get('claims',{}).get(p,[]) if c.get('rank')!='deprecated' and 'datavalue' in c.get('mainsnak',{})]
def norm(s):return re.sub(r'\W','',s.casefold())
ready=[];held=[]
for artistq,workq in links.items():
 e=entities.get(workq);a=artist_byqid.get(artistq)
 if not e or not a:held.append(dict(artist=artistq,work=workq,reason='missing_entity_evidence'));continue
 claims=[c for c in e.get('claims',{}).get('P170',[]) if c.get('rank')!='deprecated'];creators=values(e,'P170')
 if len(creators)!=1 or creators[0].get('id')!=artistq or any(c.get('qualifiers') for c in claims):held.append(dict(artist=artistq,work=workq,reason='qualified_or_multiple_creators'));continue
 dates=values(e,'P571');years=sorted({int(d['time'][1:5]) for d in dates if d.get('precision',0)>=9 and d['time'].startswith('+')})
 if any(c.get('qualifiers') for c in e.get('claims',{}).get('P571',[]) if c.get('rank')!='deprecated') or not years or len(years)!=1 or any(d.get('precision',0)<9 for d in dates) or years[0]>1970:held.append(dict(artist=artistq,work=workq,reason='date_requires_review'));continue
 images=values(e,'P18')
 if len(images)!=1:held.append(dict(artist=artistq,work=workq,reason='multiple_or_missing_reproductions'));continue
 info=pages.get('File:'+images[0].replace('_',' '),{}).get('imageinfo',[{}])[0];ext=info.get('extmetadata',{});license=ext.get('LicenseShortName',{}).get('value','')
 rights='public_domain' if license in ['Public domain','No restrictions'] else 'cc0' if license=='CC0' else 'cc_by_sa' if license.startswith('CC BY-SA') else 'cc_by' if license.startswith('CC BY ') else None
 if not rights or not info.get('url'):held.append(dict(artist=artistq,work=workq,reason='image_evidence_pending',file=images[0]));continue
 label=next((e['labels'][l]['value'] for l in ['en','fr','de','es','it','el','ru'] if l in e.get('labels',{})),None)
 if not label:held.append(dict(artist=artistq,work=workq,reason='missing_title'));continue
 existing=work_byqid.get(workq)
 if not existing:
  near=[w for w in work_byartist[a['id']] if norm(w['title'])==norm(label)]
  if near:held.append(dict(artist=artistq,work=workq,reason='existing_title_needs_identity_reconciliation',existing_ids=[w['id'] for w in near]));continue
 elif existing['artist_id']!=a['id'] or existing['creation_scope']!='eligible' or existing['primary_media_id']:
  held.append(dict(artist=artistq,work=workq,reason='existing_work_not_an_empty_eligible_target'));continue
 ready.append(dict(artist_id=a['id'],artist_slug=a['slug'],artist_name=a['display_name'],artist_qid=artistq,work_qid=workq,title=label,year=years[0],existing_artwork_id=existing['id'] if existing else None,existing_slug=existing['slug'] if existing else None,commons_file=images[0],image_info=info,rights_status=rights,license_label=license,source_url='https://www.wikidata.org/wiki/'+workq,collections=[v['id'] for v in values(e,'P195')],inventory=values(e,'P217'),types=[v['id'] for v in values(e,'P31')],entity_revision=e.get('lastrevid')))
m.save('gap-reviewed-plan.json.gz',ready);m.save('gap-held.json.gz',held);print('ready',len(ready),'existing',sum(bool(r['existing_artwork_id']) for r in ready),'held',dict(collections.Counter(r['reason'] for r in held)))
