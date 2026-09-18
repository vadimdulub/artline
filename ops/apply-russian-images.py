#!/usr/bin/env python3
"""Prepare and attach the individually cleared Russian Museum reproductions."""
import argparse, importlib.util, json, time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/russian-painters-20260913'
spec=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
PROVIDER='russian-commons'
core.PROVIDERS[PROVIDER]='Wikimedia Commons'
core.VERSION='russian-museum-exact-commons-images-v1'
SCHEME='european-russian-session-museum-object'

class ProviderPaused(BaseException):pass

class ConservativeFetcher(core.Fetcher):
    def get(self,url,limit=20_000_000):
        if urlparse(url).scheme!='https' or urlparse(url).hostname not in core.HOSTS:raise ValueError('Unapproved source host')
        time.sleep(max(0,15-(time.monotonic()-self.last)));self.last=time.monotonic()
        with self.session.get(url,timeout=(15,45),stream=True,allow_redirects=False) as response:
            if response.status_code in (429,502,503,504):
                core.event(RUN/'images',{'provider':PROVIDER,'outcome':'provider_paused_http','status':response.status_code,'retry_after':response.headers.get('Retry-After'),'source_url':url})
                raise ProviderPaused('Source provider paused; recorded status and Retry-After, no automatic retry.')
            response.raise_for_status()
            if response.status_code!=200:raise ValueError('Unexpected source response')
            data=bytearray()
            for chunk in response.iter_content(65536):
                data.extend(chunk)
                if len(data)>limit:raise ValueError('Source exceeds selected byte budget')
            return bytes(data),{k:response.headers.get(k) for k in ('Content-Type','ETag','Last-Modified')}
core.Fetcher=ConservativeFetcher

original_attach=core.attach
def attach(db,image,target):
    # Preserve the photographer's required credit as well as the painted-work
    # creator; the reusable museum adapter otherwise credits only the painter.
    with db.transaction():
        result=original_attach(db,image,target)
        if result=='attached':
            db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',
              (image['creator_credit'],image['attribution_text'],image['media_id']))
        return result
core.attach=attach

def selection():
    candidates=[]
    with psycopg.connect('postgres://127.0.0.1/artline',row_factory=dict_row) as db:
        db.execute('SET TRANSACTION READ ONLY')
        for c in json.loads((RUN/'image-rights-cleared.json').read_bytes()):
            w=c['work']
            row=db.execute("""SELECT a.id::text artwork_id,a.slug,a.title FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id
             WHERE e.entity_type='artwork' AND e.scheme=%s AND e.external_id=%s AND a.status='review'
             AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
             AND EXISTS(SELECT 1 FROM artwork_artists aa JOIN external_identifiers x ON x.entity_type='artist' AND x.entity_id=aa.artist_id AND x.scheme='wikidata' WHERE aa.artwork_id=a.id AND x.external_id=%s)""",(SCHEME,w['source_object_id'],w['painter'])).fetchone()
            if not row:raise ValueError('Imported image target missing: '+w['url'])
            credit=BeautifulSoup(c['commons_creator_credit'],'html.parser').get_text(' ',strip=True)
            ext=c['commons_page']['imageinfo'][0].get('extmetadata',{})
            preferred=BeautifulSoup(ext.get('Attribution',{}).get('value',''),'html.parser').get_text(' ',strip=True)
            attribution=f"{c['artist']['name']}. {w['title']}. Image credit: {credit}. {preferred} {c['commons_page_url']}. {c['license_label']}. Full-frame proportional resize and JPEG compression."
            image={**row,'provider':PROVIDER,'scheme':SCHEME,'external_id':w['source_object_id'],'artist':c['artist']['name'],
              'page':c['commons_page_url'],'source_image_url':c['source_image_url'],'policy_url':c['license_url'],
              'rights_status':c['rights_status'],'license_label':c['license_label'],'checked_at':core.now(),
              'commons_original_sha1':c['commons_original_sha1'],'creator_credit':credit,'attribution_text':attribution,
              'raw':c,'identity_basis':'Exact museum accession, creator authority and object title checked against the detailed museum record; corresponding Wikidata P18 file with explicit Commons rights.'}
            path=RUN/'images/selected'/PROVIDER/(row['artwork_id']+'.json')
            if path.exists():image=json.loads(path.read_bytes())
            else:core.save_new(path,image)
            candidates.append({k:image[k] for k in ('artwork_id','provider','scheme','external_id','artist','title','slug')})
    core.save_new(RUN/'images/candidates.json',{'candidates':candidates})
    return candidates

def record_evidence():
    records=[]
    for c in json.loads((RUN/'image-rights-cleared.json').read_bytes()):
        records.append({'object_id':c['work']['source_object_id'],'url':c['commons_page_url'],
          'evidence':json.dumps({'state':'rights-reviewed image candidate; local reproduction may still be pending','license':c['license_label'],'license_url':c['license_url'],'wikidata_artwork':c['wikidata_artwork'],'museum_inventory':c['museum_inventory'],'source_image_url':c['source_image_url'],'commons_original_sha1':c['commons_original_sha1'],'file_revision':c['commons_page']['revisions'][0]['revid']},ensure_ascii=False)})
    results={}
    for target,connection in [('local','postgres://127.0.0.1/artline'),('production',core.cloud_dsn())]:
        with psycopg.connect(connection,row_factory=dict_row) as db:
            db.execute('SELECT pg_advisory_xact_lock(2026091314)')
            db.execute("SET LOCAL statement_timeout='30s'")
            db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES('russian-commons-image-research','Wikimedia Commons — Russian Museum image research','authority_data','https://commons.wikimedia.org','https://commons.wikimedia.org/wiki/Commons:Licensing') ON CONFLICT DO NOTHING")
            sid=db.execute("SELECT id FROM sources WHERE slug='russian-commons-image-research'").fetchone()['id']
            count=db.execute("""WITH input AS (SELECT * FROM jsonb_to_recordset(%s::jsonb) AS x(object_id text,url text,evidence text))
              SELECT count(*) n FROM input i JOIN external_identifiers e ON e.entity_type='artwork' AND e.scheme=%s AND e.external_id=i.object_id""",(Jsonb(records),SCHEME)).fetchone()['n']
            if count!=len(records):raise ValueError('Image research targets are missing')
            result=db.execute("""WITH input AS (SELECT * FROM jsonb_to_recordset(%s::jsonb) AS x(object_id text,url text,evidence text))
              INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
              SELECT 'artwork',e.entity_id,'image_candidate',%s,i.object_id,i.url,i.evidence,now(),%s FROM input i
              JOIN external_identifiers e ON e.entity_type='artwork' AND e.scheme=%s AND e.external_id=i.object_id
              WHERE NOT EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=e.entity_id AND c.field_name='image_candidate' AND c.source_id=%s AND c.source_url=i.url)""",(Jsonb(records),sid,core.ACTOR,SCHEME,sid))
            results[target]={'candidates':len(records),'inserted_citations':result.rowcount}
    core.save_new(RUN/'image-research-database-receipt.json',results);print(results,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','apply','record-evidence']);args=p.parse_args()
    if args.phase=='record-evidence':record_evidence();raise SystemExit(0)
    if args.phase=='prepare' and (RUN/'images/events.jsonl').exists():
        pauses=[json.loads(line) for line in (RUN/'images/events.jsonl').read_text().splitlines() if 'provider_paused_http' in line]
        if pauses:
            last=pauses[-1]
            retry=last.get('retry_after') or '600'
            retry=int(retry) if retry.isdigit() else 600
            remaining=datetime.fromisoformat(last['at'].replace('Z','+00:00')).timestamp()+retry-datetime.now(timezone.utc).timestamp()
            if remaining>0:raise SystemExit(f'Source Retry-After remains active for {int(remaining)+1} seconds; no request sent.')
    candidates=selection()
    if args.phase=='apply':
        candidates=[c for c in candidates if (RUN/'images/images'/PROVIDER/(c['artwork_id']+'.json')).exists()]
    try:
        core.worker(PROVIDER,candidates,SimpleNamespace(run=RUN/'images',prepare_only=args.phase=='prepare',upload_prepared_only=args.phase=='apply'),'' if args.phase=='prepare' else core.cloud_dsn())
    except ProviderPaused as error:print(str(error),flush=True)
