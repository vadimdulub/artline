#!/usr/bin/env python3
"""Production-only exhibition schema, reviewed plans and idempotent batch delivery."""
import argparse
import collections
import datetime as dt
import json
import re
import subprocess
from pathlib import Path

from psycopg.types.json import Jsonb

import exhibitions_common as c

MIGRATION='0047_exhibitions_catalogue.sql'
MUSEUMS={
    'moma':'038c9af4-f059-50ae-aae5-085fcabc8842',
    'aic':'9e75033c-8e6b-464b-974b-d94fcc91c6a3',
    'cleveland':'729385eb-92b0-4cc8-9229-1ac3a46aee1f',
}
ARTWORK_SCHEMES={
    'aic-object':['aic-object','european-chicago-art-institute-of-chicago-object'],
    'cleveland-object':['cleveland-object','continuous-cleveland-object','european-cleveland-cleveland-museum-of-art-object'],
    'artsy-artwork':['artsy-artwork'],
}


def baseline():
    dest=c.RUN/'baseline.json.gz'
    if dest.exists():
        print('Immutable baseline exists');return
    with c.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        tables=db.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'exhibition%'").fetchall()
        assert not tables,'Exhibition baseline is no longer empty'
        institutions=db.execute("SELECT i.id::text,i.name,i.normalized_name,i.website_url,i.status,i.canonical_institution_id::text,p.name city,p.country_code FROM institutions i LEFT JOIN places p ON p.id=i.place_id").fetchall()
        aliases=[dict(institution_id=x['canonical_institution_id'],alias=x['name']) for x in institutions if x['canonical_institution_id']]
        db_counts={t:db.execute('SELECT count(*) n FROM '+t).fetchone()['n'] for t in ['artists','artworks','institutions']}
        migrations=db.execute('SELECT filename FROM schema_migrations ORDER BY filename').fetchall()
        schemes=db.execute("SELECT scheme,count(*) n FROM external_identifiers WHERE scheme ILIKE '%cleveland%' GROUP BY scheme").fetchall()
    with c.connect(local=True) as db:
        local_counts={t:db.execute('SELECT count(*) n FROM '+t).fetchone()['n'] for t in ['artists','artworks','institutions']}
    value=dict(at=c.now(),target='production',exhibitions=0,institutions=institutions,institution_aliases=aliases,counts=db_counts,local_readonly_counts=local_counts,migrations=migrations,cleveland_schemes=schemes)
    c.save(dest,value);c.BACKUP.mkdir(parents=True,exist_ok=True);c.BACKUP.chmod(0o700);c.save(c.BACKUP/'baseline.json.gz',value)
    c.save(c.RUN/'authorization.json',dict(at=c.now(),instruction='ok, now we have sources, go ahead add 100k exebitions',target_distinct_exhibitions=100000,production_ingestion_authorized=True,local_read_only=True,source_guide='docs/exhibition-sources.md'))
    print(json.dumps(dict(institutions=len(institutions),counts=db_counts,local_readonly_counts=local_counts,cleveland_schemes=schemes)),flush=True)


def migrate():
    assert (c.RUN/'baseline.json.gz').exists()
    backups=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--limit=10','--format=json'],text=True))
    backup=next(r for r in backups if r['status']=='SUCCESSFUL')
    assert (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(backup['endTime'].replace('Z','+00:00'))).total_seconds()<86400
    if not (c.RUN/'cloud-backup.json').exists():
        c.save(c.RUN/'cloud-backup.json',backup);c.save(c.BACKUP/'cloud-backup.json',backup)
    body=(c.ROOT/'apps/server/db/migrations'/MIGRATION).read_text()
    with c.connect(write=True) as db:
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute('SELECT pg_advisory_xact_lock(20250907001)')
        applied=db.execute('SELECT filename FROM schema_migrations WHERE filename=%s',(MIGRATION,)).fetchone()
        if not applied:
            db.execute(body)
            db.execute('INSERT INTO schema_migrations(filename) VALUES(%s)',(MIGRATION,))
    receipt=c.RUN/'schema-delivery.json'
    if not receipt.exists():
        c.save(receipt,dict(at=c.now(),migration=MIGRATION,sha256=c.sha(body.encode()),backup_id=backup['id'],target='production',method='Additive empty tables and indexes in one transaction; existing catalogue rows unchanged'))
    print('Production exhibition schema installed',flush=True)


def museum_index():
    b=c.load(c.RUN/'baseline.json.gz');index=collections.defaultdict(set)
    institutions={x['id']:x for x in b['institutions']}
    for x in b['institutions']:
        if x['status']=='archived' or x.get('canonical_institution_id'):continue
        for label in [x['name'],x['normalized_name']]:index[c.norm(label).removeprefix('the ')].add(x['id'])
    for x in b['institution_aliases']:
        if institutions[x['institution_id']]['status']!='archived':index[c.norm(x['alias']).removeprefix('the ')].add(x['institution_id'])
    return index,institutions


def match_institution(venue,index,institutions):
    if venue.get('institution_source') in MUSEUMS:
        mid=MUSEUMS[venue['institution_source']]
        return institutions[mid].get('canonical_institution_id') or mid
    label=c.norm(venue.get('venue_label')).removeprefix('the ')
    # Generic names and multi-venue labels remain unresolved.
    if len(label)<12 or len(label.split())<2:
        return None
    ids=index.get(label,set())
    cc=venue.get('country_code')
    if cc:ids={i for i in ids if not institutions[i]['country_code'] or institutions[i]['country_code']==cc}
    return next(iter(ids)) if len(ids)==1 else None


def object_links(db,rows):
    requests=collections.defaultdict(set)
    for r in rows:
        for e in r['entries']:
            for scheme in ARTWORK_SCHEMES.get(e.get('source_scheme'),[]):requests[scheme].add(e['source_artwork_id'])
    matches=collections.defaultdict(set)
    for scheme,ids in requests.items():
        ids=sorted(ids)
        for start in range(0,len(ids),2000):
            for x in db.execute("SELECT e.scheme,e.external_id,e.entity_id::text FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme=%s AND e.external_id=ANY(%s) AND a.status<>'archived'",(scheme,ids[start:start+2000])):
                matches[(scheme,x['external_id'])].add(x['entity_id'])
    for r in rows:
        for e in r['entries']:
            ids=set().union(*(matches.get((s,e['source_artwork_id']),set()) for s in ARTWORK_SCHEMES.get(e.get('source_scheme'),[])))
            e['artwork_id']=next(iter(ids)) if len(ids)==1 else None
            e['match_basis']='Exact native source artwork identifier' if e['artwork_id'] else None
    people=collections.defaultdict(set)
    for r in rows:
        for p in r['participants']:
            if p.get('source_scheme') and p.get('source_person_id'):people[p['source_scheme']].add(p['source_person_id'])
    pm=collections.defaultdict(set)
    for scheme,ids in people.items():
        for x in db.execute("SELECT e.external_id,e.entity_id::text FROM external_identifiers e JOIN artists a ON a.id=e.entity_id WHERE e.entity_type='artist' AND e.scheme=%s AND e.external_id=ANY(%s) AND a.status<>'archived'",(scheme,sorted(ids))):pm[(scheme,x['external_id'])].add(x['entity_id'])
    for r in rows:
        for p in r['participants']:
            ids=pm.get((p.get('source_scheme'),p.get('source_person_id')),set())
            p['artist_id']=next(iter(ids)) if len(ids)==1 else None


def identity_keys(r):
    """Exact dated identity only; fuzzy/tour candidates get a separate audit."""
    if not r.get('start_date') or not r.get('end_date') or r.get('date_conflict'):
        return []
    titles={r['normalized_title'],*(c.norm(x) for x in r.get('alternate_titles',[]))}
    venues={v.get('institution_id') or '|'.join([c.norm(v.get('venue_label')).removeprefix('the '),c.norm(v.get('city_label')),v.get('country_code') or c.norm(v.get('country_label'))]) for v in r['occurrences'] if v.get('institution_id') or v.get('venue_label')}
    if not venues:
        venues={c.norm(p['name_label']) for p in r['participants'] if p['role'] in ['organizer','presenting_organization']}
    return [(t,v,r['start_date'],r['end_date']) for t in titles if t for v in venues if v]


def screen_record(r):
    """Conservative target eligibility; source data remains immutable evidence."""
    r['normalized_title']=r.get('normalized_title') or r['title'].casefold()
    if r['provider']!='artsy':return
    issues=list(r.get('research_issues') or [])
    # Provider "show" records also contain events and commerce listings. Keep
    # these available for research, without counting them as held exhibitions.
    if re.search(r'\b(auction|auctions|gala|fundraiser|fundraising|art\s*fair|art\s*basel|frieze|tefaf|artissima|artgen[eè]ve|artbrussels|art\s*miami|scope\s*(miami|basel|new york)|volta\s*(basel|new york)|armory\s*show|art\s*dubai|fiac|art\s*cologne|art\s*taipei|art\s*karlsruhe)\b',r['title'],re.I):
        issues.append('possible_fair_sale_or_other_event_requires_exhibition_confirmation')
    if re.search(r'\b(sale|sales|new\s+arrivals|new\s+inventory|inventory\s+highlights|new\s+acquisitions|works\s+available)\b',r['title'],re.I):
        issues.append('possible_inventory_or_sales_listing_requires_exhibition_confirmation')
    if issues:
        r['research_issues']=sorted(set(issues))
        if r['event_state']!='cancelled':r['event_state']='uncertain'
        r['state_basis']='Source fields require review: '+', '.join(r['research_issues'])
    if 'implausible_dates_for_this_modern_exhibition_platform' in issues:
        for v in r['occurrences']:
            v['evidence']=dict(v.get('evidence') or {},date_conflict=True,original_start=v.get('start_date'),original_end=v.get('end_date'))
            v['start_date']=v['end_date']=None


def plan(provider):
    with c.connect() as db:
        db.autocommit=True
        _plan(provider,db)


def _plan(provider,db):
    assert (c.RUN/'schema-delivery.json').exists()
    index,institutions=museum_index()
    existing_keys={}
    existing_native={}
    canonical_seen=set()
    # A subsequent enrichment must follow completed identity consolidations,
    # not the original ID stored in an immutable historical import plan.
    current_native={(x['source_key'],x['source_record_id']):x['exhibition_id'] for x in db.execute('SELECT source_key,source_record_id,exhibition_id::text FROM exhibition_source_records')}
    # Only the new exhibition catalogue, never a global artwork enrichment CTE.
    for path in sorted((c.RUN/'plans').glob('*/*.json.gz')):
        for r in c.load(path)['rows']:
            r['canonical_id']=current_native.get((r['provider'],r['native_id']),r['canonical_id'])
            existing_native[(r['provider'],r['native_id'])]=r['canonical_id']
            canonical_seen.add(r['canonical_id'])
            for k in identity_keys(r):existing_keys[k]=r['canonical_id']
    paths=sorted((c.DATA/'normalized'/provider).glob('*.json.gz'))
    for path in paths:
        dest=c.RUN/'plans'/provider/path.name
        if dest.exists():continue
        rows=c.load(path);duplicates=[]
        object_links(db,rows)
        for r in rows:
            screen_record(r)
            for v in r['occurrences']:
                v['institution_id']=match_institution(v,index,institutions)
                if v.get('start_date') and v.get('end_date') and v['start_date']>v['end_date']:
                    v['evidence']=dict(v.get('evidence') or {},date_conflict=True,original_start=v['start_date'],original_end=v['end_date'])
                    v['start_date']=v['end_date']=None
            match={existing_keys[k] for k in identity_keys(r) if k in existing_keys}
            native=existing_native.get((r['provider'],r['native_id']))
            if native:match={native}
            if r.get('canonical_source_id'):
                match={native or existing_native.get((r['provider'],r['canonical_source_id'])) or c.uid(r['provider']+'/tour/'+r['canonical_source_id'])}
            if len(match)>1:
                raise ValueError('Conflicting canonical exhibition identities: '+str(match))
            r['canonical_id']=next(iter(match)) if match else r['id']
            r['identity_basis']=r.get('identity_basis') or ('existing native ID or exact title, venue and date range' if match else 'distinct source exhibition identity')
            if r['canonical_id'] in canonical_seen:duplicates.append(dict(native_id=r['native_id'],canonical_id=r['canonical_id']))
            canonical_seen.add(r['canonical_id'])
            existing_native[(r['provider'],r['native_id'])]=r['canonical_id']
            for k in identity_keys(r):existing_keys[k]=r['canonical_id']
        value=dict(provider=provider,input_path=str(path),input_sha256=c.sha(path.read_bytes()),rows=rows,duplicates=duplicates)
        c.save(dest,value)
        print(json.dumps(dict(planned=provider,page=path.name,rows=len(rows),duplicates=len(duplicates),artwork_links=sum(bool(e.get('artwork_id')) for r in rows for e in r['entries']))),flush=True)


def apply(provider,max_pages=None):
    # Reuse transports, not transactions. Every source page commits atomically
    # and is checked through a separate connection forced read-only.
    with c.connect(write=True) as writer,c.connect() as verifier:
        writer.autocommit=True
        verifier.autocommit=True
        _apply(provider,max_pages,writer,verifier)


def _apply(provider,max_pages,writer,verifier):
    assert (c.RUN/'schema-delivery.json').exists() and (c.RUN/'cloud-backup.json').exists()
    applied=0
    for path in sorted((c.RUN/'plans'/provider).glob('*.json.gz')):
        receipt=c.RUN/'delivery'/provider/(path.name.removesuffix('.json.gz')+'.json')
        if receipt.exists():continue
        p=c.load(path);assert c.sha(Path(p['input_path']).read_bytes())==p['input_sha256']
        source_ids=[];events=[];sources=[];venues=[];people=[];entries=[];publications=[]
        for r in p['rows']:
            eid=r['canonical_id'];sid=c.uid('source/'+provider+'/'+r['native_id']);source_ids.append(sid)
            date_held=r.get('date_conflict') or 'implausible_dates_for_this_modern_exhibition_platform' in r.get('research_issues',[])
            start=None if date_held else r['start_date'];end=None if date_held else r['end_date']
            dates=r.get('date_display') or ' / '.join(str(x or '?') for x in [r.get('source_start'),r.get('source_end')])
            events.append((eid,r['title'],r['normalized_title'],Jsonb(r.get('alternate_titles',[])),start,end,int(start[:4]) if start else None,int(end[:4]) if end else None,dates,'day' if start and end else 'mixed' if start or end else 'unknown',r['event_state'],r['state_basis'],r.get('format','unknown'),r['checklist_state'],c.OP))
            rc=r['receipt']
            sources.append((sid,eid,provider,r['native_id'],r['source_url'],rc['retrieved_at'],rc['url'],rc['sha256'],Jsonb(r['source_payload']),Jsonb({k:r.get(k) for k in ['identity_basis','research_issues','public_artwork_list','date_conflict']})))
            for i,v in enumerate(r['occurrences']):
                venues.append((c.uid(f'occurrence/{provider}/{r["native_id"]}/{i}'),eid,sid,v.get('institution_id'),v.get('source_venue_id'),v.get('venue_label'),v.get('city_label'),v.get('country_label'),v.get('country_code'),v.get('start_date'),v.get('end_date'),v.get('date_display'),Jsonb(v.get('evidence') or {})))
            for i,x in enumerate(r['participants']):
                people.append((c.uid(f'participant/{provider}/{r["native_id"]}/{i}'),eid,sid,x.get('artist_id'),x['name_label'],x['role'],x.get('source_person_id'),Jsonb(x.get('evidence') or {})))
            for i,x in enumerate(r['entries']):
                entries.append((c.uid(f'entry/{provider}/{r["native_id"]}/{i}'),eid,sid,x.get('artwork_id'),x.get('source_artwork_id'),x.get('catalogue_number'),x.get('title_label'),x.get('creator_label'),x.get('date_label'),x.get('medium_label'),x.get('dimensions_label'),x.get('lender_label'),x['participation'],x.get('source_page'),Jsonb(x['evidence']),x.get('match_basis')))
            for i,x in enumerate(r['publications']):
                publications.append((c.uid(f'publication/{provider}/{r["native_id"]}/{i}'),eid,sid,x['publication_type'],x.get('title_label'),x.get('author_label'),x.get('publication_date_label'),x.get('url'),x.get('source_identifier'),x.get('page_label'),Jsonb(x['evidence'])))
        with writer.transaction():
            db=writer
            db.execute('SELECT pg_advisory_xact_lock(20261011047)')
            cur=db.cursor()
            cur.executemany('INSERT INTO exhibitions(id,title,normalized_title,alternate_titles,start_date,end_date,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,import_batch) VALUES('+','.join(['%s']*15)+') ON CONFLICT(id) DO NOTHING',events)
            cur.executemany('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES('+','.join(['%s']*10)+') ON CONFLICT(id) DO NOTHING',sources)
            for table,columns,values in [
                ('exhibition_occurrences','id,exhibition_id,source_record_id,institution_id,source_venue_id,venue_label,city_label,country_label,country_code,start_date,end_date,date_display,evidence',venues),
                ('exhibition_participants','id,exhibition_id,source_record_id,artist_id,name_label,role,source_person_id,evidence',people),
                ('exhibition_entries','id,exhibition_id,source_record_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,dimensions_label,lender_label,participation,source_page,evidence,match_basis',entries),
                ('exhibition_publications','id,exhibition_id,source_record_id,publication_type,title_label,author_label,publication_date_label,url,source_identifier,page_label,evidence',publications),
            ]:
                if values:cur.executemany(f'INSERT INTO {table}({columns}) VALUES('+','.join(['%s']*len(values[0]))+') ON CONFLICT(id) DO NOTHING',values)
            found=db.execute('SELECT count(*) n FROM exhibition_source_records WHERE id=ANY(%s::uuid[])',(source_ids,)).fetchone()['n']
            assert found==len(set(source_ids))
        check=verifier.execute('SELECT count(*) n FROM exhibition_source_records WHERE id=ANY(%s::uuid[])',(source_ids,)).fetchone()['n']
        assert check==found
        c.save(receipt,dict(at=c.now(),provider=provider,plan_sha256=c.sha(path.read_bytes()),source_records=found,canonical_exhibition_ids=sorted({x[0] for x in events}),entries=len(entries),artwork_links=sum(x[3] is not None for x in entries),participants=len(people),occurrences=len(venues),verified_after_commit=True))
        applied+=1
        print(json.dumps(dict(delivered=provider,page=path.name,source_records=found,entries=len(entries),participants=len(people))),flush=True)
        if max_pages and applied>=max_pages:break


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['baseline','migrate','plan','apply']);p.add_argument('--provider');p.add_argument('--max-pages',type=int)
    a=p.parse_args()
    if a.action=='apply':apply(a.provider,a.max_pages)
    elif a.action=='plan':plan(a.provider)
    else:globals()[a.action]()
