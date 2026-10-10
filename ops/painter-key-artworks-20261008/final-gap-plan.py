import importlib.util,collections,re,uuid
from pathlib import Path
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
images=m.base.load(m.RUN/'gap-image-preparation-retry.json.gz');entities={k:v for p in (m.RUN/'entities').glob('*.json') for k,v in m.base.load(p).get('entities',{}).items()}
bytarget={}
for target in ['local','production']:
 rows=m.base.load(m.BACKUP/(target+'-gap-artwork-identities.json.gz')); byartist=collections.defaultdict(list)
 for r in rows:byartist[r['artist_id']].append(r)
 bytarget[target]=byartist
norm=lambda x:re.sub(r'\W','',x.casefold())
lives={k:v for p in (m.RUN/'artist-entities').glob('*.json') for k,v in m.base.load(p).get('entities',{}).items()}
manual={'Q25439957':'Museum record 339.1991 identifies dates 1968 and 1991, plus Matthew Dillon; the photographed large version is not securely pre-1970 (https://www.artgallery.nsw.gov.au/collection/works/339.1991/)','Q3525935':'Schematic recreation of Three Flags, not a photograph of the painting','Q23020485':'Museum case view does not show a usable reproduction of the panorama','Q20441745':"Photograph of Sofala the place, not Drysdale's painting",'Q101474848':'Only part of the triptych is shown','Q117048947':'Image shows the reverse of the portrait','Q1757822':'Edition/can number identity needs reconciliation'}
ready=[];held=[]
for row in images:
 if not row.get('prepared'):held.append(row);continue
 if row['license_label']=='No restrictions':held.append(dict(work_qid=row['work_qid'],reason='ambiguous_rights_label'));continue

 if row['work_qid'] in manual:held.append(dict(work_qid=row['work_qid'],reason=manual[row['work_qid']]));continue
 life=lives.get(row['artist_qid'])
 if not life:held.append(dict(work_qid=row['work_qid'],reason='creator_life_evidence_missing'));continue
 bounds={}
 for prop in ['P569','P570']:
  bounds[prop]=[int(c['mainsnak']['datavalue']['value']['time'][1:5]) for c in life.get('claims',{}).get(prop,[]) if c.get('rank')!='deprecated' and c.get('mainsnak',{}).get('datavalue',{}).get('value',{}).get('precision',0)>=9 and c['mainsnak']['datavalue']['value']['time'].startswith('+')]
 if (bounds['P569'] and row['year']<min(bounds['P569'])+8) or (bounds['P570'] and row['year']>max(bounds['P570'])):
  held.append(dict(work_qid=row['work_qid'],reason='creation_date_conflicts_with_creator_life_or_requires_childhood_review',year=row['year'],life_bounds=bounds));continue
 row['creator_life_evidence']=bounds
 row['targets']={};reason=None
 labels={norm(v['value']) for v in entities[row['work_qid']].get('labels',{}).values()}
 for target,artists in bytarget.items():
  works=artists[row['artist_id']];matches={w['id']:w for w in works if w['wikidata']==row['work_qid']}
  inventory={norm(v) for v in row['inventory'] if isinstance(v,str)}
  if not matches:
   matches={w['id']:w for w in works if w['institution_wikidata'] in row['collections'] and w['accession_number'] and norm(w['accession_number']) in inventory}
  if len(matches)>1:reason='multiple_object_matches';break
  existing=next(iter(matches.values()),None)
  if existing:
   if existing['attribution_role']!='primary' or (existing['wikidata'] and existing['wikidata']!=row['work_qid']):reason='object_or_attribution_conflict';break
   if existing['creation_year_start']!=row['year'] or existing['creation_year_end'] not in [None,row['year']] or existing['date_precision'] not in ['exact','circa']:reason='existing_date_difference';break
   row['targets'][target]=dict(artwork_id=existing['id'],slug=existing['slug'],new=False,primary_media_id=existing['primary_media_id'],status=existing['status'])
  else:
   if any(norm(w['title']) in labels for w in works):reason='possible_existing_translated_title';break
   row['targets'][target]=dict(artwork_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://www.wikidata.org/wiki/'+row['work_qid']+'#artline-key-artwork')),slug='key-artwork-'+row['work_qid'].lower(),new=True,primary_media_id=None,status='review')
 if reason:held.append(dict(work_qid=row['work_qid'],reason=reason));continue
 ready.append(row)
m.save('gap-final-plan-v2.json.gz',ready);m.save('gap-final-held-v2.json.gz',held);print('Final gap plan',len(ready),'new local',sum(r['targets']['local']['new'] for r in ready),'new production',sum(r['targets']['production']['new'] for r in ready),'held',len(held))
