#!/usr/bin/env python3
"""Read-only country ranking and bounded Met metadata selection for existing painters."""
import argparse
import collections
import csv
from datetime import datetime,timezone,timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import uuid
import requests

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('met',ROOT/'ops/import-overnight-met-selection.py')
met=importlib.util.module_from_spec(spec);spec.loader.exec_module(met)
core=met.core;research=met.research;campaign=research.campaign
INDEX=ROOT/'docs/research/overnight-images-20260915/met-new/MetObjects.csv'


def recheck(a):
    """Recheck captured current sources with explicit creator-role support."""
    if not a.recheck_run:raise ValueError('Specify source review runs')
    dest=a.run/'fresh-selection';leads={};captures=[]
    for reference in a.recheck_run:
        source=reference/'fresh-selection'
        for lead in json.loads((source/'source-candidates.json').read_text()):
            oid=lead['source_object_id'];url='https://collectionapi.metmuseum.org/public/collection/v1/objects/'+oid;key=core.sha(url.encode())
            path=source/'fresh-api'/(key+'.json');receipt_path=source/'fresh-api'/(key+'.receipt.json')
            if not path.exists() or not receipt_path.exists():continue
            raw=path.read_bytes();receipt=json.loads(receipt_path.read_text())
            if core.sha(raw)!=receipt['sha256'] or receipt['url']!=url:raise ValueError('Captured source checksum or URL differs')
            if datetime.now(timezone.utc)-datetime.fromisoformat(receipt['retrieved_at'].replace('Z','+00:00'))>timedelta(hours=24):raise ValueError('Refresh old metadata before role recheck')
            if oid in leads:continue
            leads[oid]=lead;captures.append({'object_id':oid,'reference':str(reference),'sha256':receipt['sha256']})
            core.save_new(dest/'fresh-api'/(key+'.json'),raw)
            core.save_new(dest/'fresh-api'/(key+'.receipt.json'),receipt_path.read_bytes())
    core.save_new(dest/'source-candidates.json',list(leads.values()))
    core.save_new(a.run/'role-recheck-provenance.json',{'at':core.now(),'captures':captures,
        'rule':'Accept an exact matching single Draftsman/Draughtsman for drawings or Etcher/Artist and publisher for prints; publisher-only, conflicting makers and qualified attribution remain held. Museum life years must not contradict existing known creator dates.'})
    fresh(a)


def continuation(a):
    """Resume metadata discovery without re-requesting previously selected objects."""
    if not a.reference:raise ValueError('Continuation requires a prior run')
    if a.run.resolve()==a.reference.resolve():raise ValueError('Use a new continuation directory')
    leads=json.loads((a.reference/'all-source-leads.json').read_text())
    done={r['source_object_id'] for r in json.loads((a.reference/'fresh-selection/source-candidates.json').read_text())}
    remaining=[r for r in leads if r['source_object_id'] not in done]
    core.save_new(a.run/'inventory.json',(a.reference/'inventory.json').read_bytes())
    core.save_new(a.run/'all-source-leads.json',remaining)
    core.save_new(a.run/'continuation.json',{'at':core.now(),'reference':str(a.reference),
        'previously_selected_objects_excluded':len(done),'remaining_metadata_leads':len(remaining),
        'note':'Original country ranking and discovery evidence retained; both catalogues and selected object sources are checked again.'})
    preflight(a)


def ledger(a):
    run=a.run/'fresh-selection';people={}
    delivery=a.delivery;events=core.latest_events(delivery) if delivery else {}
    prior={c['external_id']:c['artwork_id'] for folder in a.previous_delivery
        for c in json.loads((folder/'plan.json').read_text())['records']
        if core.latest_events(folder).get(c['artwork_id'],{}).get('outcome')=='complete'}
    conflicts={r['source_object_id']:r['reason'] for r in json.loads((delivery/'plan.json').read_text())['held']} if delivery else {}
    for lead in json.loads((run/'source-candidates.json').read_text()):
        oid=lead['source_object_id'];person=lead['artist'];entry=people.setdefault(person['slug'],
            {'painter':person['display_name'],'artist_slug':person['slug'],'artist_qid':person['qid'],
             'catalogue_birth_year':person.get('birth_year'),'catalogue_death_year':person.get('death_year'),
             'country_codes':sorted(set(person['country_codes'])),'works':[]})
        row={'object_id':oid,'discovery_title':lead['object']['Title'],'source_url':'https://www.metmuseum.org/art/collection/search/'+oid}
        url='https://collectionapi.metmuseum.org/public/collection/v1/objects/'+oid
        source_path=run/'fresh-api'/(core.sha(url.encode())+'.json')
        if source_path.exists():
            obj=json.loads(source_path.read_text())
            row.update(source_title=obj.get('title'),source_artist_authority=obj.get('artistWikidata_URL'),
                source_birth_year=obj.get('artistBeginDate'),source_death_year=obj.get('artistEndDate'),
                source_creator_roles=obj.get('constituents'),source_date=obj.get('objectDate'),
                source_is_public_domain=obj.get('isPublicDomain'))
        if oid in prior:row.update(previously_delivered=True,artwork_id=prior[oid])
        verified=run/'verified'/(oid+'.json');held=run/'review-held'/(oid+'.json')
        if verified.exists():
            c=json.loads(verified.read_text());row.update(title=c['title'],date_display=c['date_display'],outcome='source_verified')
            if oid in conflicts:row.update(outcome='duplicate_review',reason=conflicts[oid])
            elif events.get(c['artwork_id'],{}).get('outcome')=='complete':row.update(outcome='delivered',artwork_id=c['artwork_id'])
            elif oid in prior:row['outcome']='already_delivered'
        elif held.exists():row.update(outcome='held',reason=json.loads(held.read_text())['reason'])
        else:row['outcome']='not_yet_verified'
        entry['works'].append(row)
    report={'at':core.now(),'painters':list(people.values()),'outcomes':dict(collections.Counter(w['outcome'] for p in people.values() for w in p['works']))}
    core.save_new(a.run/'painter-by-painter-review.json',report)
    print(json.dumps({'painters':len(people),'outcomes':report['outcomes']}),flush=True)


def fresh(a):
    run=a.run/'fresh-selection'
    rows=json.loads((run/'source-candidates.json').read_text())[:a.limit]
    rows.sort(key=lambda r:(r['artist']['display_name'],r['source_object_id']))
    fetch=core.Fetcher(run/'fresh-api');fetch.defer_long_cooldowns=True
    counts=collections.Counter()
    for lead in rows:
        oid=lead['source_object_id']
        if any((run/folder/(oid+'.json')).exists() for folder in ('verified','review-held')):continue
        url='https://collectionapi.metmuseum.org/public/collection/v1/objects/'+oid
        try:
            obj=fetch.metadata(url);record=research.verify(lead,obj)
            record['metadata_capture']=json.loads((fetch.cache/(core.sha(url.encode())+'.receipt.json')).read_text())
            record['country_codes']=sorted(set(lead['artist']['country_codes']))
            core.save_new(run/'verified'/(oid+'.json'),record);counts['verified']+=1
        except ValueError as error:
            core.save_new(run/'review-held'/(oid+'.json'),{'at':core.now(),'object_id':oid,'reason':str(error)})
            counts['held']+=1
        except (requests.RequestException,core.SourceCooldown,RuntimeError) as error:
            if isinstance(error,requests.HTTPError) and error.response is not None and error.response.status_code==404:
                core.save_new(run/'review-held'/(oid+'.json'),{'at':core.now(),'object_id':oid,'reason':'Exact current Met object endpoint returned HTTP 404'})
                counts['held']+=1
                continue
            # Stop this source on access/rate/network errors; do not evade them.
            path=run/('source-pause-'+oid+'.json')
            if not path.exists():core.save_new(path,{'at':core.now(),'object_id':oid,'error':str(error)[:500]})
            print('Met metadata paused:',oid,str(error)[:250],flush=True);break
        if sum(counts.values())%10==0:print(core.now(),'Fresh Met review',dict(counts),flush=True)
    print(core.now(),'Fresh Met review finished',dict(counts),flush=True)


def preflight(a):
    parent=a.run
    run=parent/'fresh-selection';run.mkdir(parents=True,exist_ok=True)
    leads=json.loads((parent/'all-source-leads.json').read_text())
    ranking=json.loads((parent/'inventory.json').read_text())['top_ten'];codes=[r['code'] for r in ranking]
    records=[]
    for lead in leads:
        o=lead['object'];person=lead['artist'];oid=lead['source_object_id']
        dates=research.date_fields({'objectBeginDate':int(o['Object Begin Date']),'objectEndDate':int(o['Object End Date']),
            'objectDate':o['Object Date'],'artistBeginDate':o['Artist Begin Date'],'artistEndDate':o['Artist End Date']})
        qid=o.get('Object Wikidata URL','').rstrip('/').rsplit('/',1)[-1]
        records.append({'artwork_id':str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/night-selected-met/'+oid)),
            'slug':'night-met-'+oid,'external_id':oid,'title':o['Title'],'accession_number':o['Object Number'],**dates,
            'work_type':lead['work_type'],'artist_qid':person['qid'],'artist_slug':person['slug'],
            'qid':qid if re.fullmatch(r'Q\d+',qid or '') else None,'page':'https://www.metmuseum.org/art/collection/search/'+oid})
    holds=[];snapshots={}
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        with campaign.read_only(dsn) as db:
            state=met.snapshot(db,records);accepted,held=met.conflicts(records,state)
        holds.extend(dict(h,target=target) for h in held)
        records=[{k:v for k,v in r.items() if k not in ('already_present','target_artist_id')} for r in accepted if not r['already_present']]
        snapshots[target]={'accepted':len(records),'held':len(held)}
    allowed={c['external_id'] for c in records};by_country=collections.defaultdict(list)
    for lead in leads:
        if lead['source_object_id'] not in allowed:continue
        country=min(lead['artist']['country_codes'],key=codes.index);by_country[country].append(lead)
    for rows in by_country.values():rows.sort(key=lambda r:(not r['artist']['popular'],r['artist']['display_name'],r['work_type']!='painting',r['source_object_id']))
    chosen=[]
    for n in range(max(map(len,by_country.values()),default=0)):
        for country in codes:
            if n<len(by_country[country]):chosen.append(by_country[country][n])
        if len(chosen)>=a.limit:break
    chosen=chosen[:a.limit]
    core.save_new(run/'source-candidates.json',chosen)
    core.save_new(run/'preflight.json',{'at':core.now(),'source_leads':len(leads),'targets':snapshots,
        'selected':len(chosen),'country_memberships':dict(collections.Counter(code for c in chosen for code in set(c['artist']['country_codes']))),
        'held':holds,'note':'Metadata-only duplicate preflight, not import approval. Exact current source and final identity guards still required.'})
    print(json.dumps({'targets':snapshots,'selected':len(chosen),'countries':dict(collections.Counter(code for c in chosen for code in set(c['artist']['country_codes'])))},indent=2),flush=True)


def inventory(a):
    with campaign.read_only('postgres://localhost/artline') as db:
        ranking=db.execute("""SELECT co.code,co.name,count(DISTINCT p.id) painters,
            count(DISTINCT a.id) eligible_artworks,
            count(DISTINCT a.id) FILTER(WHERE a.primary_media_id IS NULL) image_gaps
            FROM countries co JOIN artist_countries pc ON pc.country_code=co.code
            JOIN artists p ON p.id=pc.artist_id AND p.status<>'archived'
            JOIN artwork_artists aa ON aa.artist_id=p.id
            JOIN artworks a ON a.id=aa.artwork_id AND a.status<>'archived'
            WHERE co.region_code LIKE '%%europe' AND a.work_type IN ('painting','drawing','print','watercolor','fresco')
            AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
            GROUP BY co.code,co.name ORDER BY eligible_artworks DESC,co.code""").fetchall()
        top=ranking[:10];codes=[r['code'] for r in top]
        people=db.execute("""SELECT p.id::text,p.slug,p.display_name,p.birth_year,p.death_year,e.external_id qid,
            array(SELECT ac.country_code::text FROM artist_countries ac WHERE ac.artist_id=p.id AND ac.country_code=ANY(%s) ORDER BY ac.country_code) country_codes,
            EXISTS(SELECT 1 FROM artist_discovery_selection d WHERE d.artist_id=p.id AND d.is_popular) popular
            FROM artists p JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=p.id AND e.scheme='wikidata'
            WHERE p.status<>'archived' AND EXISTS(SELECT 1 FROM artist_countries ac WHERE ac.artist_id=p.id AND ac.country_code=ANY(%s))""",(codes,codes)).fetchall()
        native=db.execute("""SELECT e.entity_id::text,e.external_id FROM external_identifiers e
            WHERE e.entity_type='artwork' AND e.scheme=ANY(%s)""",(met.SCHEMES,)).fetchall()
        gaps=db.execute("""SELECT a.id::text artwork_id,a.title,a.accession_number,e.external_id,
            p.slug artist_slug,p.display_name,ac.country_code::text country
            FROM artist_countries ac JOIN artists p ON p.id=ac.artist_id AND p.status<>'archived'
            JOIN artwork_artists aa ON aa.artist_id=p.id JOIN artworks a ON a.id=aa.artwork_id
            JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme=ANY(%s)
            WHERE ac.country_code=ANY(%s) AND a.status<>'archived' AND a.primary_media_id IS NULL
            AND a.work_type IN ('painting','drawing','print','watercolor','fresco')
            AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
            ORDER BY ac.country_code,p.display_name,a.id""",(met.SCHEMES,codes)).fetchall()
    people_by_qid=collections.defaultdict(list)
    for person in people:people_by_qid[person['qid']].append(person)
    existing={r['external_id'] for r in native};gap_ids={r['external_id'] for r in gaps}
    receipt=json.loads(INDEX.with_name('MetObjects.receipt.json').read_text())
    with INDEX.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!=receipt['sha256']:raise ValueError('Met index checksum differs')
    leads=[];held=collections.Counter();open_gaps=[]
    with INDEX.open(encoding='utf-8-sig') as stream:
        for obj in csv.DictReader(stream):
            if obj['Is Public Domain']!='True':continue
            if obj['Object ID'] in gap_ids:open_gaps.append(obj)
            if obj['Object ID'] in existing:continue
            qid=obj.get('Artist Wikidata URL','').rstrip('/').rsplit('/',1)[-1]
            matches=people_by_qid.get(qid,[])
            if len(matches)!=1:continue
            kind={'Paintings':'painting','Drawings':'drawing','Prints':'print'}.get(obj['Classification'])
            if not kind:held['unselected_type']+=1;continue
            if obj.get('Artist Prefix','').strip() or obj.get('Artist Suffix','').strip():held['qualified_attribution']+=1;continue
            try:
                source={'objectBeginDate':int(obj['Object Begin Date']),'objectEndDate':int(obj['Object End Date']),
                    'objectDate':obj['Object Date'],'artistBeginDate':obj['Artist Begin Date'],'artistEndDate':obj['Artist End Date']}
                research.date_fields(source)
            except (ValueError,KeyError):held['source_date_review']+=1;continue
            leads.append({'source_object_id':obj['Object ID'],'object':obj,'artist':matches[0],'work_type':kind})
    # Preserve the complete metadata lead inventory, but request only a balanced batch.
    groups=collections.defaultdict(list)
    for lead in leads:
        code=min(lead['artist']['country_codes'],key=codes.index)
        groups[(code,lead['artist']['slug'])].append(lead)
    for values in groups.values():values.sort(key=lambda r:(r['work_type']!='painting',r['object']['Object ID']))
    chosen=[]
    for rank in range(max(map(len,groups.values()),default=0)):
        for country in codes:
            subset=sorted([(key,items) for key,items in groups.items() if key[0]==country],key=lambda x:(not x[1][0]['artist']['popular'],x[1][0]['artist']['display_name']))
            for key,items in subset:
                if rank<len(items):chosen.append(items[rank])
        if len(chosen)>=a.limit:break
    chosen=chosen[:a.limit]
    core.save_new(a.run/'inventory.json',{'at':core.now(),'ranking_basis':'Ten European countries ranked by distinct eligible catalogue artworks, using existing artist-country relationships; a multi-country artist may count for more than one country. Not a ranking of artistic merit.',
        'top_ten':top,'country_ranking':ranking,'painters_with_authority':len(people),'existing_met_gap_records':gaps,
        'open_index_gap_objects':open_gaps,'new_met_leads':len(leads),'lead_holds':held,'source_index':receipt})
    core.save_new(a.run/'all-source-leads.json',leads)
    core.save_new(a.run/'source-candidates.json',chosen)
    print(json.dumps({'top_ten':top,'painters_with_authority':len(people),'existing_met_gap_objects':len(gap_ids),
        'open_index_gap_objects':len(open_gaps),'new_metadata_leads':len(leads),'selected_for_fresh_review':len(chosen),'held':held},indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=100);p.add_argument('--phase',choices=['inventory','preflight','fresh','continuation','ledger','recheck'],default='inventory');p.add_argument('--reference',type=Path);p.add_argument('--delivery',type=Path);p.add_argument('--recheck-run',type=Path,action='append',default=[]);p.add_argument('--previous-delivery',type=Path,action='append',default=[])
    a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True);globals()[a.phase](a)
