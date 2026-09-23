#!/usr/bin/env python3
"""Fill exact existing museum-accession gaps lacking native museum identifiers."""
import argparse
import concurrent.futures
import importlib.util
import json
from pathlib import Path
import uuid
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('gaps',ROOT/'ops/open-access-image-gaps.py')
gaps=importlib.util.module_from_spec(spec);spec.loader.exec_module(gaps)
core=gaps.core
REVIEWED={
 '8264bb8f-a13f-505e-9b15-02bd3fd39071':('cleveland','115394','1936.18'),
 'a647a2cc-4a0b-521a-847a-ce4bb9113c5d':('cleveland','84732','2022.433'),
 '86678a0b-1d7d-5be3-b54f-d67d9f566302':('met','436059','45.110.4'),
}
SOURCE_SLUG='open-access-native-gap-crosswalk-20260919-'

def select(run):
    with gaps.campaign.read_only('postgres://localhost/artline') as db:
        rows=db.execute(gaps.QUERY+' AND a.id=ANY(%s::uuid[])',(['wikidata'],list(REVIEWED))).fetchall()
    held=[];selected=[];dsn=core.cloud_dsn()
    for c in rows:
        provider,native,accession=REVIEWED[c['artwork_id']]
        if c['accession_number']!=accession:raise ValueError('Reviewed accession changed')
        reference={'scheme':c['scheme'],'external_id':c['external_id'],'page':c['page'],'source_id':c['source_id']}
        c['reference_identifier']=reference
        with gaps.campaign.read_only(dsn) as db:
            matches=db.execute(gaps.QUERY+' AND e.external_id=%s',(['wikidata'],reference['external_id'])).fetchall()
        keys=('title','accession_number','creation_year_start','creation_year_end','date_precision','work_type','status','artist_slugs','roles')
        if len(matches)!=1 or any(matches[0][k]!=c[k] for k in keys):
            held.append({'artwork_id':c['artwork_id'],'reason':'Production source identity differs'});continue
        remote=matches[0]
        c['before']={'local':c.pop('before_record'),'cloud':remote['before_record']}
        c['target_ids']={'local':c['artwork_id'],'cloud':remote['artwork_id']}
        c.update(provider=provider,scheme=core.SCHEMES[provider],external_id=native,
            source_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/sources/'+SOURCE_SLUG+provider)))
        c['page']='https://www.metmuseum.org/art/collection/search/'+native if provider=='met' else 'https://clevelandart.org/art/'+accession
        try:
            image=core.image_record(c,core.Fetcher(run/'metadata'/provider),{}, {})
            if image is None:raise ValueError('No explicit current open image')
            if provider=='cleveland':
                raw=image['raw']
                if raw.get('legal_status')!='accessioned' or raw.get('on_loan') is not False:raise ValueError('Museum ownership not established')
                if raw.get('record_type')!='object' or raw.get('cover_accession_number'):raise ValueError('Multipart object needs review')
            for target,d in [('local','postgres://localhost/artline'),('cloud',dsn)]:
                with gaps.campaign.read_only(d) as db:
                    collision=db.execute('''SELECT entity_id::text FROM external_identifiers
                        WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=%s''',(gaps.SCHEMES[provider],native)).fetchall()
                    if collision:raise ValueError('Native museum object already represented')
                    iid=c['before'][target]['current_institution_id']
                    institution=db.execute('SELECT slug FROM institutions WHERE id=%s',(iid,)).fetchone()
                    if not institution or institution['slug']!={'met':'the-met','cleveland':'cleveland-museum-of-art'}[provider]:raise ValueError('Existing museum link differs')
            image['crosswalk_review']='Existing Wikidata-linked artwork; exact accepted museum, accession, title, unqualified creator name/alias and compatible pre-1971 source dates. Native museum identifier absent in both targets. No new artwork or catalogue date normalization.'
            if provider=='cleveland':
                image['date_review_note']='Museum date interval is broader than existing catalogue precision. Both are retained in evidence; catalogue dates remain unchanged and record remains in review.'
            selected.append(image)
        except Exception as error:
            held.append({'artwork_id':c['artwork_id'],'provider':provider,'native_id':native,'reason':str(error)[:500]})
    backups={}
    backup=Path('/Users/vadimdulub/Library/Application Support/Artline/backups')/run.parent.name/run.name
    for target,d in [('local','postgres://localhost/artline'),('cloud',dsn)]:
        with gaps.campaign.read_only(d) as db:
            ids=[c['target_ids'][target] for c in selected]
            identifiers=db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchall()
            citations=db.execute("SELECT to_jsonb(c) record FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchall()
            path=backup/(target+'-before.json')
            core.save_new(path,{'artworks':[c['before'][target] for c in selected],'identifiers':identifiers,'citations':citations})
            backups[target]={'path':str(path),'sha256':core.sha(path.read_bytes())}
    core.save_new(run/'backups.json',{'targets':backups})
    core.save_new(run/'candidates.json',{'candidates':selected})
    core.save_new(run/'held.json',held)
    for c in selected:core.save_new(run/'selected'/c['provider']/(c['artwork_id']+'.json'),c)
    print(json.dumps({'selected':len(selected),'held':held},indent=2),flush=True)

original_attach=core.attach
def attach(db,im,target):
    gaps.verify_identity(im)
    with db.transaction():
        db.execute('SELECT pg_advisory_xact_lock(559220260919)')
        aid=im['target_ids'][target]
        row=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s FOR UPDATE',(aid,)).fetchone()
        excluded={'primary_media_id','updated_at','updated_by','revision'}
        if not row or {k:v for k,v in row['record'].items() if k not in excluded}!={k:v for k,v in im['before'][target].items() if k not in excluded}:raise ValueError('Target catalogue facts changed')
        if row['record']['primary_media_id'] not in (None,im['media_id']):return 'existing_media_preserved'
        ref=im['reference_identifier']
        links=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(ref['scheme'],ref['external_id'])).fetchall()
        if len(links)!=1 or links[0]['entity_id']!=aid:raise ValueError('Original authority link differs')
        if im['provider']=='met':
            artist_qid=im['raw'].get('artistWikidata_URL','').rstrip('/').rsplit('/',1)[-1]
            authorities=db.execute("""SELECT e.external_id FROM artwork_artists aa JOIN external_identifiers e
                ON e.entity_type='artist' AND e.entity_id=aa.artist_id AND e.scheme='wikidata'
                WHERE aa.artwork_id=%s""",(aid,)).fetchall()
            if len(authorities)!=1 or authorities[0]['external_id']!=artist_qid:raise ValueError('Explicit museum artist authority differs')
        links=db.execute("SELECT entity_id::text,scheme,source_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=%s",(gaps.SCHEMES[im['provider']],im['external_id'])).fetchall()
        if links and (len(links)!=1 or links[0]!={'entity_id':aid,'scheme':im['scheme'],'source_id':im['source_id']}):raise ValueError('Native museum identity already represented or provenance changed')
        slug=SOURCE_SLUG+im['provider']
        base={'met':'https://collectionapi.metmuseum.org/','cleveland':'https://openaccess-api.clevelandart.org/'}[im['provider']]
        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,terms_url) VALUES(%s,%s,%s,'museum_api',%s,%s) ON CONFLICT(slug) DO NOTHING",(im['source_id'],slug,core.PROVIDERS[im['provider']]+': verified native object crosswalk',base,im['policy_url']))
        source=db.execute('SELECT id::text,base_url,terms_url FROM sources WHERE slug=%s',(slug,)).fetchone()
        if source!={'id':im['source_id'],'base_url':base,'terms_url':im['policy_url']}:raise ValueError('Source provenance identity differs')
        if not links:
            db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,im['scheme'],im['external_id'],im['page'],im['source_id'],im['checked_at']))
            db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at) VALUES('artwork',%s,%s,'official_object_identity',%s,%s,%s,%s)",(aid,im['source_id'],im['external_id'],im['page'],im['crosswalk_review']+' '+im.get('date_review_note',''),im['checked_at']))
        return original_attach(db,im,target)
core.attach=attach

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['select','prepare','apply']);p.add_argument('--run',type=Path,required=True);a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
    if a.phase=='select':select(a.run);return
    # Shared runner verifies recovery hashes and the checksum-pinned visual review.
    gaps.run_phase(SimpleNamespace(run=a.run,phase=a.phase))
if __name__=='__main__':main()
