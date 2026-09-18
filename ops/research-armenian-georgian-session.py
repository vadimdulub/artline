#!/usr/bin/env python3
"""Bounded Armenian/Georgian artwork and public artist-identity research."""
import argparse,collections,importlib.util,json,re,subprocess,time
from pathlib import Path
from urllib.parse import urlencode
import psycopg
from psycopg.rows import dict_row
spec=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('research-russian-deep-images.py'));prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
core=prior.core;ROOT=prior.ROOT;RUN=ROOT/'docs/research/armenian-georgian-women-20260913';BACKUP=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/armenian-georgian-women-20260913');prior.base.RUN=RUN;fetch=prior.base.fetch;save=core.save_new
def connect(target):return psycopg.connect('postgres://127.0.0.1/artline' if target=='local' else core.cloud_dsn(),row_factory=dict_row)
def audit():
 for target in ['local','production']:
  with connect(target) as db:
   db.execute('SET TRANSACTION READ ONLY')
   artists=db.execute("""SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,a.status,
    (SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'id',e.external_id)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id) identifiers,
    (SELECT jsonb_agg(jsonb_build_object('country',c.country_code,'relationship',c.relationship_type,'note',c.note)) FROM artist_countries c WHERE c.artist_id=a.id) countries
    FROM artists a WHERE a.status<>'archived' ORDER BY a.id""").fetchall()
   ids=[a['id'] for a in artists if any(c['country'] in ('AM','GE') for c in a['countries'] or [])]
   works=db.execute("""WITH selected AS MATERIALIZED(SELECT DISTINCT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])) SELECT a.id::text,a.slug,a.title,a.alternate_title,a.accession_number,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.status,a.primary_media_id::text,a.revision,i.slug institution,artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) date_scope,artline_has_selection_evidence(a.id) selected,
    (SELECT jsonb_agg(jsonb_build_object('id',aa.artist_id::text,'role',aa.attribution_role)) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creators,
    (SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'id',e.external_id,'url',e.canonical_url)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) identifiers
    FROM selected s JOIN artworks a ON a.id=s.artwork_id LEFT JOIN institutions i ON i.id=a.current_institution_id ORDER BY a.id""",(ids,)).fetchall()
   institutions=db.execute("SELECT id::text,slug,name,wikidata_id,website_url FROM institutions WHERE status<>'archived'").fetchall()
  save(RUN/(target+'-before.json'),{'at':core.now(),'artists':artists,'works':works,'institutions':institutions});print(target,'artists',len(artists),'AM/GE artists',len(ids),'works',len(works),'images',sum(bool(w['primary_media_id']) for w in works),flush=True)
def backup():
 BACKUP.mkdir(parents=True,exist_ok=True);dump=BACKUP/'local-before.dump'
 if not dump.exists():subprocess.run(['pg_dump','-Fc','--no-owner','--no-acl','-d','postgres://127.0.0.1/artline','-f',str(dump)],check=True)
 subprocess.run(['pg_restore','--list',str(dump)],check=True,stdout=subprocess.DEVNULL)
 description='Armenian Georgian research and women filter 20260913';request=BACKUP/'production-backup-request.json'
 if not request.exists():save(request,subprocess.check_output(['gcloud','sql','backups','create','--instance=artline-postgres','--project=artline-508319','--description='+description,'--format=json']))
 records=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--limit=30','--format=json']));b=next(x for x in records if x.get('description')==description);assert b['status']=='SUCCESSFUL';save(RUN/'backups.json',{'local':{'path':str(dump),'bytes':dump.stat().st_size,'sha256':core.sha(dump.read_bytes())},'production':b});print('Recovery backups verified',flush=True)
def genders():
 d=json.loads((RUN/'local-before.json').read_bytes());ids=sorted({e['id'] for a in d['artists'] for e in a['identifiers'] or [] if e['scheme']=='wikidata' and re.fullmatch(r'Q\d+',e['id'])});rows=[]
 for start in range(0,len(ids),200):
  part=ids[start:start+200];query='SELECT ?artist ?statement ?gender ?rank WHERE { VALUES ?artist { '+' '.join('wd:'+q for q in part)+' } ?artist p:P21 ?statement . ?statement ps:P21 ?gender; wikibase:rank ?rank. FILTER(?rank != wikibase:DeprecatedRank) }'
  data=fetch('https://query.wikidata.org/sparql?'+urlencode({'query':query,'format':'json'}));partrows=data['results']['bindings'];save(RUN/'gender-research'/(str(start).zfill(5)+'.json'),{'artist_qids':part,'rows':partrows,'query':query});rows+=partrows;print('Gender source research',min(start+200,len(ids)),'/',len(ids),flush=True)
 byid=collections.defaultdict(list)
 for row in rows:byid[row['artist']['value'].rsplit('/',1)[-1]].append(row)
 selected=[];conflicts=[]
 for q,statements in byid.items():
  preferred=[s for s in statements if s['rank']['value'].endswith('PreferredRank')];effective=preferred or statements;values={s['gender']['value'].rsplit('/',1)[-1] for s in effective}
  if values and values<={'Q6581072','Q1052281'}:selected.append({'qid':q,'is_woman':True,'statements':statements,'effective_statements':effective,'basis':'Explicit, non-deprecated Wikidata P21 identity statements, using preferred rank when present. No inference from name, image, occupation or nationality.','source_url':'https://www.wikidata.org/wiki/'+q,'checked_at':core.now()})
  elif values & {'Q6581072','Q1052281'}:conflicts.append({'qid':q,'values':sorted(values),'reason':'Conflicting or additional gender identities need individual review; no automatic binary classification.'})
 save(RUN/'women-source-selection.json',selected);save(RUN/'women-source-conflicts.json',conflicts);save(RUN/'gender-research-summary.json',{'existing_wikidata_artists':len(ids),'with_gender_statements':len(byid),'selected_women':len(selected),'conflicts':len(conflicts)});print('Women artists selected',len(selected),'conflicts',len(conflicts),flush=True)
def roster():
 query='SELECT DISTINCT ?artist ?country WHERE { VALUES ?country { wd:Q399 wd:Q230 wd:Q79797 wd:Q48441 } ?artist (wdt:P27|wdt:P172) ?country; wdt:P106/wdt:P279* wd:Q1028181 . } ORDER BY ?artist LIMIT 800'
 data=fetch('https://query.wikidata.org/sparql?'+urlencode({'query':query,'format':'json'}));rows=data['results']['bindings'];ids=sorted({x['artist']['value'].rsplit('/',1)[-1] for x in rows});save(RUN/'artist-roster-discovery-v2.json',{'query':query,'rows':rows,'bounded':True,'supersedes':'Initial query used an incorrect occupation identifier; its zero-result response is retained as query evidence, not an absence-of-artists finding.'});print('Discovered Armenian/Georgian painter authorities',len(ids),flush=True)
 for start in range(0,len(ids),30):
  part=ids[start:start+30];data=fetch('https://www.wikidata.org/w/api.php?'+urlencode({'action':'wbgetentities','ids':'|'.join(part),'props':'labels|descriptions|aliases|claims|sitelinks','languages':'en|hy|ka|ru|fr|mul','format':'json','maxlag':5}))
  for q,e in data['entities'].items():save(RUN/'artist-entities'/(q+'.json'),e)
  print('Artist authorities',min(start+30,len(ids)),'/',len(ids),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['audit','backup','genders','roster']);args=p.parse_args();globals()[args.phase]()
