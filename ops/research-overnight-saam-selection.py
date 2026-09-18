import importlib.util,json,collections,re,uuid
from pathlib import Path
from urllib.parse import urlparse,parse_qs
s=importlib.util.spec_from_file_location('saam',Path('ops/overnight-saam-images.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);r=Path('docs/research/overnight-images-20260915/saam');out=r.parent/'saam-new';out.mkdir(exist_ok=True)
with m.ro('postgres://localhost/artline') as db:
 people=db.execute("""SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,
 (SELECT e.external_id FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata') qid,
 ARRAY(SELECT al.alias FROM artist_aliases al WHERE al.artist_id=a.id) aliases,
 EXISTS(SELECT 1 FROM artist_discovery_selection d WHERE d.artist_id=a.id AND d.is_popular) popular
 FROM artists a WHERE a.status<>'archived'""").fetchall()
 existing={x['external_id'] for x in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='saam-object'").fetchall()}
index=collections.defaultdict(dict)
for a in people:
 for name in [a['display_name']]+a['aliases']:index[m.norm(name)][a['id']]=a
rows=[];held=collections.Counter()
for u in (r/'index.txt').read_text().splitlines():
 p=r/'metadata'/u.rsplit('/',1)[-1];receipt=json.loads(p.with_suffix('.receipt.json').read_text());raw=p.read_bytes();assert m.core.sha(raw)==receipt['sha256']
 for line in raw.splitlines():
  o=json.loads(line);dn=o.get('content',{}).get('descriptiveNonRepeating',{});ft=o.get('content',{}).get('freetext',{});oid=parse_qs(urlparse(dn.get('record_link','')).query).get('id',[None])[0]
  if not oid or oid in existing:continue
  typ=m.fields(ft,'objectType','Type');mapping={('Painting',):'painting',('Painting-Miniature',):'painting',('Drawing',):'drawing',('Graphic Arts-Print',):'print'};work_type=mapping.get(tuple(typ))
  if not work_type:held['unselected_type']+=1;continue
  names=m.fields(ft,'name','Artist');dates=m.fields(ft,'date','Date');acc=m.fields(ft,'identifier','Object number')
  if len(names)!=1:held['creator_qualification_or_absence']+=1;continue
  name=re.split(r', (?:born|died|active|ca\.)',names[0],maxsplit=1)[0];matches=list(index[m.norm(name)].values())
  if len(matches)!=1 or not matches[0]['qid']:held['creator_authority_not_unique']+=1;continue
  artist=matches[0]
  if len(dates)!=1:held['no_unique_creation_date']+=1;continue
  match=re.fullmatch(r'\s*(?P<approx>(?:ca\.|c\.|circa|about)\s*)?(?P<lo>\d{4})(?:\s*[-–—/]\s*(?P<hi>\d{4}|\d{2}))?\s*',dates[0],re.I)
  if not match:held['creation_date_needs_review']+=1;continue
  lo=int(match['lo']);end=match['hi'] or match['lo'];hi=int(str(lo)[:2]+end) if len(end)==2 else int(end)
  if not 1000<=lo<=hi<=1970:held['outside_creation_scope']+=1;continue
  precision=('circa' if lo==hi else 'circa_range') if match['approx'] else ('exact' if lo==hi else 'range')
  if (artist['birth_year'],artist['death_year'])==(lo,hi) and lo!=hi:held['creator_lifespan_not_creation']+=1;continue
  if len(acc)!=1 or not dn.get('title',{}).get('content'):held['identity_incomplete']+=1;continue
  media=dn.get('online_media',{}).get('media',[])
  if len(media)!=1 or media[0].get('usage',{}).get('access')!='CC0' or m.fields(ft,'objectRights','Restrictions & Rights')!=['CC0']:held['exact_image_rights_or_view_missing']+=1;continue
  if dn.get('metadata_usage',{}).get('access')!='CC0':held['metadata_rights_missing']+=1;continue
  # Do not resolve a namesake across contradictory museum biographical dates.
  years=re.findall(r'\b(1[0-9]{3})\b',names[0]);birth=int(years[0]) if 'born ' in names[0] and years else None;death=int(years[-1]) if 'died ' in names[0] and years else None
  if (birth and artist['birth_year'] and birth!=artist['birth_year']) or (death and artist['death_year'] and death!=artist['death_year']):held['creator_lifespan_disagrees']+=1;continue
  rows.append({'source_object_id':oid,'title':dn['title']['content'],'artist':artist,'work_type':work_type,'date_display':dates[0],'creation_year_start':lo,'creation_year_end':hi,'date_precision':precision,'accession_number':acc[0],'object':o,'metadata_capture':receipt})
rows.sort(key=lambda c:(not c['artist']['popular'],c['work_type']!='painting',c['artist']['display_name'],int(c['source_object_id'])))
m.core.save_new(out/'source-leads.json',rows);m.core.save_new(out/'source-lead-report.json',{'at':m.core.now(),'count':len(rows),'popular':sum(c['artist']['popular'] for c in rows),'by_type':dict(collections.Counter(c['work_type'] for c in rows)),'held':dict(held),'status':'Metadata leads only; duplicate and final source-adapter validation precede import or image download.'});print('SAAM new leads',len(rows),'popular',sum(c['artist']['popular'] for c in rows),'types',collections.Counter(c['work_type'] for c in rows),'held',held)
