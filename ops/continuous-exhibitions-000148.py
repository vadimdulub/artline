#!/usr/bin/env python3
"""One bounded, checksum-pinned Greek drawing-exhibition production batch."""
import fcntl
import gzip
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import requests
from psycopg.types.json import Jsonb

import exhibitions_common as c

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'docs/research/continuous-exhibitions-20261013/batches/000148'
R = Path.home() / 'Library/Application Support/Artline/continuous-exhibition-research/batches/000148'
B = Path.home() / 'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000148'
Q = E.parents[1] / 'source-queue.json'
OP = 'continuous-exhibitions-20261013-batch-000148'
ACTOR = 'local-european-research'
MID = '052007aa-11f7-4d57-90e6-d3b62bb0bf4b'
SID = 'cc9c1590-deee-45c1-8aea-e0557558fb65'
INSTANCE = 'artline-508319:europe-west1:artline-postgres'
API = 'https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
SPECS = [
    dict(key='sikeliotis1983', en='giorgos-sikeliotis-2', el='giorgos-sikeliotis',
         artist_slug='sikeliotis-giorgos', name='Giorgos Sikeliotis',
         native_name='Γιώργος Σικελιώτης', birth=1917, death=1984,
         start='1983-11-08', end='1983-12-08', type_label='drawings exhibition',
         medium_basis='Drawings (1935-1950)',
         excluded_previous_event='41939a75-0b0c-5952-9cba-6ed46f26d7f0'),
    dict(key='dimitriadis1983', en='fokion-dimitriadis-1940-1972', el='phokion-dimitriadis-1940-1972',
         artist_slug='dimitriadis-fokion', name='Fokion Dimitriadis',
         native_name='Φωκίων Δημητριάδης', birth=1894, death=1977,
         start='1983-04-18', end='1983-05-22', type_label='cartoons and drawings exhibition',
         medium_basis='Cartoons and drawings', excluded_previous_event=None),
]


def serial(x):
    return json.loads(json.dumps(x, ensure_ascii=False, default=str))


def save(path, data):
    c.save(path, data)


def target(db):
    processes = subprocess.check_output(['ps', '-axo', 'command'], text=True).splitlines()
    command = '/tmp/artline-cloud-sql-proxy --address 127.0.0.1 --port 55519 --gcloud-auth ' + INSTANCE
    assert command in [s.strip() for s in processes]
    assert (db.info.host, db.info.port, db.info.dbname) == ('127.0.0.1', 55519, 'artline')
    check = db.execute('select current_database() database,current_user role').fetchone()
    assert check['database'] == 'artline' and check['role'] == 'artline_app'
    return dict(instance=INSTANCE, host=db.info.host, port=db.info.port,
                database=check['database'], role=check['role'], checked_at=c.now())


def artist_collisions(db, a):
    names = [c.norm(x) for x in [a['name'], a['native_name'], a['source']['title']]]
    # Broad variant/lifespan and all native-provider identities were reviewed separately.
    return serial(db.execute("""select distinct a.id,a.display_name,a.birth_year,a.death_year,a.status
      from artists a where a.id=%s or a.slug=%s or a.normalized_name=any(%s)
      or exists(select 1 from artist_aliases n where n.artist_id=a.id and n.normalized_alias=any(%s))
      or exists(select 1 from external_identifiers x where x.entity_type='artist' and x.entity_id=a.id
        and ((x.scheme='nationalgallery-gr-artist' and x.external_id=%s) or x.canonical_url=%s))""",
      (a['id'], a['slug'], names, names, a['artist_slug'], a['source']['receipt']['url'])).fetchall())


def event_collisions(db, e):
    urls = [x['receipt']['url'] for x in e['sources']]
    titles = [x['title'] for x in e['sources']]
    return serial(db.execute("""select distinct e.id,e.title,e.start_year,e.end_year,e.import_batch
      from exhibitions e left join exhibition_source_records s on s.exhibition_id=e.id
      where e.id=%s or s.source_url=any(%s)
        or ((e.normalized_title=any(%s) or e.alternate_titles ?| %s)
            and (e.start_year is null or e.start_year=1983))""",
      (e['id'], urls, [c.norm(t) for t in titles], titles)).fetchall())


def snapshot(db, plan):
    eids = [x['id'] for x in plan['events']]
    aids = [x['id'] for x in plan['artists']]
    out = {}
    for table in ['exhibitions', 'exhibition_source_records', 'exhibition_occurrences',
                  'exhibition_participants', 'exhibition_entries']:
        col = 'id' if table == 'exhibitions' else 'exhibition_id'
        out[table] = serial(db.execute('select * from '+table+' where '+col+'=any(%s::uuid[]) order by id', (eids,)).fetchall())
    out['artists'] = serial(db.execute('select * from artists where id=any(%s::uuid[]) order by id', (aids,)).fetchall())
    out['artist_aliases'] = serial(db.execute('select * from artist_aliases where artist_id=any(%s::uuid[]) order by id', (aids,)).fetchall())
    for table in ['citations', 'external_identifiers']:
        out[table] = serial(db.execute("select * from "+table+" where entity_type='artist' and entity_id=any(%s::uuid[]) order by id", (aids,)).fetchall())
    out['audits'] = serial(db.execute('select * from audit_log where request_id=%s order by id', (OP,)).fetchall())
    return out


def unchanged_entities(db):
    return serial(dict(institution=db.execute('select * from institutions where id=%s', (MID,)).fetchone(),
                       source=db.execute('select * from sources where id=%s', (SID,)).fetchone(),
                       earlier_sikeliotis_event=db.execute('select * from exhibitions where id=%s', (SPECS[0]['excluded_previous_event'],)).fetchone()))


def prepare():
    captures = c.load(E/'candidate-captures.json')
    creator_captures = c.load(E/'artist-source-captures.json')
    events, artists = [], []
    with c.connect() as db:
        t = target(db)
        preserved = unchanged_entities(db)
        assert preserved['institution']['slug'] == 'national-gallery-greece'
        assert preserved['source']['slug'] == 'national-gallery-greece'
        assert preserved['earlier_sikeliotis_event']['start_year'] == 1975
        assert not db.execute('select 1 from exhibitions where import_batch=%s', (OP,)).fetchone()
        for spec in SPECS:
            enurl = 'https://www.nationalgallery.gr/en/exhibitions/'+spec['en']+'/'
            elurl = 'https://www.nationalgallery.gr/ektheseis/'+spec['el']+'/'
            sources = [dict(next(x for x in captures if x['receipt']['url'] == u)) for u in [enurl, elurl]]
            for x in sources:
                x.pop('links', None)
                raw = gzip.decompress(Path(x['receipt']['body_path']).read_bytes())
                assert c.sha(raw) == x['receipt']['sha256']
                x['native_id'] = re.search(rb'postid-(\d+)', raw).group(1).decode()
                x['id'] = c.uid(OP+'/source/'+x['native_id'])
                for date in [spec['start'], spec['end']]:
                    assert '.'.join(reversed(date.split('-'))) in x['text']
            assert spec['medium_basis'] in sources[0]['text']
            assert 'National Gallery - Central Building' in sources[0]['text']
            a = dict(spec)
            a['source'] = next(x for x in creator_captures if x['slug'] == spec['artist_slug'])
            a['id'] = c.uid('artist/nationalgallery-gr/'+spec['artist_slug'])
            a['slug'] = c.norm(a['name']).replace(' ', '-')
            assert str(a['birth']) in a['source']['text'] and str(a['death']) in a['source']['text']
            a['collision_rows'] = artist_collisions(db, a)
            assert not a['collision_rows'], a['collision_rows']
            e = dict(spec, id=c.uid(OP+'/exhibition/'+spec['key']),
                     oid=c.uid(OP+'/occurrence/'+spec['key']), pid=c.uid(OP+'/participant/'+spec['key']),
                     title=sources[1]['title'], alt=sources[0]['title'], sources=sources, artist_id=a['id'])
            e['collision_rows'] = event_collisions(db, e)
            assert not e['collision_rows'], e['collision_rows']
            events.append(e)
            artists.append(a)
    plan = dict(at=c.now(), operation=OP, target=t, events=events, artists=artists,
                preserved_entities=preserved, checklist_state='unknown', status='review',
                scope='Exhibitions 1600–1989; paintings/drawings/prints/icons. Main artworks through 1970; none created in this batch.',
                basis='Official bilingual historical exhibition records explicitly name the exhibiting artist, drawing/cartoon media, dated venue and past occurrence. Official artist pages establish the same creator identity and lifespan. Artist biography is not used to infer individual exhibited objects.',
                holds=['No original checklists or exact exhibited objects reviewed; no artwork participation or image inferred.',
                       'Three further 1982–1983 retrospectives captured as leads pending event-level pictorial-medium/catalogue confirmation: Sakellaridis, Plakotaris, Vassiliou.',
                       'Vassiliou exhibition title includes 1902, while the artist biography gives birth year 1903; no creator/date resolution forced.',
                       'National Museum of Western Art provider returned HTTP403; no retry or bypass.',
                       'Existing Arthive HTTP429, Greek catalogue PDF host and prior source holds remain unchanged.'])
    save(E/'plan.json', plan)
    B.mkdir(parents=True, exist_ok=True)
    B.chmod(0o700)
    save(B/'plan.json', plan)
    pin = c.sha((E/'plan.json').read_bytes())
    save(E/'plan-pin.json', dict(sha256=pin, backup=str(B/'plan.json')))
    receipts = [x['receipt'] for e in events for x in e['sources']] + [x['source']['receipt'] for x in artists]
    for rc in receipts:
        assert c.sha(gzip.decompress(Path(rc['body_path']).read_bytes())) == rc['sha256']
    save(E/'source-capture-verification.json', dict(at=c.now(), plan_sha256=pin, receipts=receipts,
         count=6, exact_urls_native_ids_and_original_wording_preserved=True, passed=True))
    save(E/'candidate-review-verification.json', dict(at=c.now(), plan_sha256=pin,
         distinct_event_candidates=5, prepared_events=2, deferred_events=3, prior_events_recounted=0,
         selected=[dict(title=e['title'], start=e['start'], end=e['end'], medium=e['medium_basis'], artist=e['name']) for e in events],
         creator_reconciliation='Name/alias variants, lifetime candidates, exact official identifiers and source citations checked; seven returned candidates are different people.',
         creator_reconciliation_receipt=str(E/'final-artist-reconciliation.json'),
         checklists_complete=0, exact_object_links_prepared=0, images_prepared=0, visual_review_claimed=False,
         holds=plan['holds'], passed=True))
    print('Prepared two historical exhibitions, two creators and two artist links; plan', pin)


def evidence(plan, pin):
    return dict(operation=OP, plan_sha256=pin, checked_at=plan['at'], basis=plan['basis'],
                checklist_complete=False, individual_objects_unknown=True, organizer_unknown=True,
                ownership_inferred=False, current_display_inferred=False)


def audit(db, table, entity_type, ident, pin):
    record = serial(db.execute('select * from '+table+' where id=%s', (ident,)).fetchone())
    db.execute("""insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json)
        values(%s,'continuous_exhibition_insert',%s,%s,%s,%s,%s)""",
        (ACTOR, entity_type, ident, OP, Jsonb(None), Jsonb(dict(record=record, plan_sha256=pin))))


def apply():
    plan = c.load(E/'plan.json')
    pin = c.load(E/'plan-pin.json')['sha256']
    assert plan['operation'] == OP and c.sha((E/'plan.json').read_bytes()) == pin
    assert c.sha((B/'plan.json').read_bytes()) == pin
    with c.connect(write=True) as db:
        t = target(db)
        db.execute("select set_config('artline.actor_user_id',%s,true)", (ACTOR,))
        db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('select pg_advisory_xact_lock(2026101201)')
        before = snapshot(db, plan)
        if before['exhibitions']:
            # A previous commit must be verified independently; never count a retry as an addition.
            assert len(before['exhibitions']) == 2
            assert all(x['import_batch'] == OP for x in before['exhibitions'])
            assert (B/'transaction-preimage.json').exists()
            for x in before['exhibition_source_records']:
                assert x['interpretation']['plan_sha256'] == pin
            print('Existing own plan detected; no replay. Run verify.')
            return
        assert not any(before.values())
        assert unchanged_entities(db) == plan['preserved_entities']
        for a in plan['artists']:
            assert not artist_collisions(db, a), 'Creator inserted by another job; replan without duplicate.'
        for e in plan['events']:
            assert not event_collisions(db, e), 'Event inserted by another job; replan without duplicate.'
        pre = dict(at=c.now(), target=t, operation=OP, plan_sha256=pin, rows=before,
                   preserved_entities=unchanged_entities(db), locks=['artline-curated-ingestion', 2026101201])
        save(B/'transaction-preimage.json', pre)
        save(E/'transaction-preimage.json', pre)
        save(E/'production-target-before-write.json', dict(**t, plan_sha256=pin, passed=True))
        ev = evidence(plan, pin)
        for a in plan['artists']:
            db.execute("""insert into artists(id,slug,display_name,sort_name,normalized_name,birth_year,death_year,
                birth_display,death_display,birth_precision,death_precision,timeline_start_year,timeline_end_year,
                timeline_display,timeline_basis,status,created_by,updated_by)
                values(%s,%s,%s,%s,%s,%s,%s,%s,%s,'exact','exact',%s,%s,%s,'life','review',%s,%s)""",
                (a['id'],a['slug'],a['name'],a['source']['title'],c.norm(a['name']),a['birth'],a['death'],
                 str(a['birth']),str(a['death']),a['birth'],a['death'],f"{a['birth']}–{a['death']}",ACTOR,ACTOR))
            for name,lang,kind in [(a['native_name'],'el','native_name'),(a['source']['title'],'en','alternate')]:
                db.execute('insert into artist_aliases(id,artist_id,alias,normalized_alias,language_code,alias_type) values(%s,%s,%s,%s,%s,%s)',
                           (c.uid(OP+'/alias/'+name),a['id'],name,c.norm(name),lang,kind))
            rc=a['source']['receipt']
            db.execute("""insert into external_identifiers(id,entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)
                values(%s,'artist',%s,'nationalgallery-gr-artist',%s,%s,%s,%s)""",
                (c.uid(OP+'/identifier/'+a['artist_slug']),a['id'],a['artist_slug'],rc['url'],SID,rc['retrieved_at']))
            note=dict(**ev, native_id=a['source']['native_id'], source_receipt=rc,
                      source_identity=a['source']['title'], birth_year=a['birth'], death_year=a['death'])
            db.execute("""insert into citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,
                evidence_note,retrieved_at,created_by) values(%s,'artist',%s,'continuous_exhibition_creator_identity',%s,%s,%s,%s,%s,%s)""",
                (c.uid(OP+'/citation/'+a['artist_slug']),a['id'],SID,a['source']['native_id'],rc['url'],
                 json.dumps(note,ensure_ascii=False),rc['retrieved_at'],ACTOR))
            audit(db,'artists','artist',a['id'],pin)
        for e in plan['events']:
            display=e['start']+' – '+e['end']
            ee=dict(**ev,type_label=e['type_label'],medium_basis=e['medium_basis'],
                    source_date_period_in_title_is_not_exhibition_date=True)
            db.execute("""insert into exhibitions(id,title,normalized_title,alternate_titles,start_date,end_date,start_year,end_year,
                date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch)
                values(%s,%s,%s,%s,%s,%s,1983,1983,%s,'day','held',%s,'physical','unknown','review',%s)""",
                (e['id'],e['title'],c.norm(e['title']),Jsonb([e['alt']]),e['start'],e['end'],display,
                 plan['basis']+' Assessed '+plan['at'],OP))
            for x in e['sources']:
                rc=x['receipt']
                db.execute("""insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,
                    capture_url,capture_sha256,source_payload,interpretation) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (x['id'],e['id'],'national-gallery-greece-official',x['native_id'],rc['url'],rc['retrieved_at'],
                     rc['body_path'],rc['sha256'],Jsonb(x),Jsonb(ee)))
                audit(db,'exhibition_source_records','exhibition_source_record',x['id'],pin)
            db.execute("""insert into exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,
                country_label,country_code,start_date,end_date,date_display,evidence) values(%s,%s,%s,%s,%s,'Athens','Greece','GR',%s,%s,%s,%s)""",
                (e['oid'],e['id'],e['sources'][1]['id'],MID,'National Gallery - Central Building',e['start'],e['end'],display,Jsonb(ee)))
            a=next(a for a in plan['artists'] if a['id']==e['artist_id'])
            pe=dict(**ee,participation_basis='Artist named as the subject/maker of the exhibition of drawings/cartoon drawings in the event-specific source.',
                    creator_identity_source=a['source']['receipt'],posthumous=a['death']<1983)
            db.execute("""insert into exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,source_person_id,evidence)
                values(%s,%s,%s,%s,%s,'artist',%s,%s)""",
                (e['pid'],e['id'],e['sources'][1]['id'],e['artist_id'],e['native_name'],a['artist_slug'],Jsonb(pe)))
            for table,kind,ident in [('exhibitions','exhibition',e['id']),('exhibition_occurrences','exhibition_occurrence',e['oid']),
                                     ('exhibition_participants','exhibition_participant',e['pid'])]:
                audit(db,table,kind,ident,pin)
        assert unchanged_entities(db)==plan['preserved_entities']
        save(B/'transaction-postimage.json',dict(at=c.now(),plan_sha256=pin,rows=snapshot(db,plan)))
    save(E/'applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin))
    print('Transaction completed. Independent verification still required.')


def verify():
    plan=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];pre=c.load(B/'transaction-preimage.json')
    assert c.sha((E/'plan.json').read_bytes())==pin and pre['plan_sha256']==pin and not any(pre['rows'].values())
    with c.connect() as db:
        db.execute('set transaction isolation level repeatable read, read only')
        t=target(db);rows=snapshot(db,plan)
        assert unchanged_entities(db)==plan['preserved_entities']
        expected={'exhibitions':2,'exhibition_source_records':4,'exhibition_occurrences':2,'exhibition_participants':2,
                  'exhibition_entries':0,'artists':2,'artist_aliases':4,'citations':2,'external_identifiers':2}
        for table,n in expected.items():assert len(rows[table])==n,(table,len(rows[table]))
        own_audits=[x for x in rows['audits'] if x['action']=='continuous_exhibition_insert']
        assert len(own_audits)==12
        assert all(x['before_json'] is None and x['after_json']['plan_sha256']==pin for x in own_audits)
        for e in plan['events']:
            ev=next(x for x in rows['exhibitions'] if x['id']==e['id'])
            assert (ev['title'],ev['start_date'],ev['end_date'],ev['status'],ev['event_state'],ev['checklist_state'],ev['import_batch'])==(
                    e['title'],e['start'],e['end'],'review','held','unknown',OP)
            occ=next(x for x in rows['exhibition_occurrences'] if x['id']==e['oid'])
            assert (occ['exhibition_id'],occ['institution_id'],occ['start_date'],occ['end_date'])==(e['id'],MID,e['start'],e['end'])
            part=next(x for x in rows['exhibition_participants'] if x['id']==e['pid'])
            assert (part['exhibition_id'],part['artist_id'],part['role'],part['name_label'])==(e['id'],e['artist_id'],'artist',e['native_name'])
            for v in [occ,part]:assert v['evidence']['plan_sha256']==pin and v['evidence']['operation']==OP
            for x in e['sources']:
                src=next(y for y in rows['exhibition_source_records'] if y['id']==x['id'])
                assert (src['exhibition_id'],src['source_url'],src['capture_sha256'],src['source_record_id'])==(
                    e['id'],x['receipt']['url'],x['receipt']['sha256'],x['native_id'])
                assert src['interpretation']['plan_sha256']==pin and src['interpretation']['operation']==OP
        for a in plan['artists']:
            row=next(x for x in rows['artists'] if x['id']==a['id'])
            assert (row['display_name'],row['birth_year'],row['death_year'],row['status'])==(a['name'],a['birth'],a['death'],'review')
            citation=next(x for x in rows['citations'] if x['entity_id']==a['id'])
            note=json.loads(citation['evidence_note'])
            assert note['plan_sha256']==pin and note['source_receipt']['sha256']==a['source']['receipt']['sha256']
            ident=next(x for x in rows['external_identifiers'] if x['entity_id']==a['id'])
            assert (ident['scheme'],ident['external_id'],ident['canonical_url'])==('nationalgallery-gr-artist',a['artist_slug'],a['source']['receipt']['url'])
    counts=dict(new_exhibitions=2,new_venue_stops=2,new_artists=2,new_catalogue_artworks=0,new_documentary_entries=0,
                new_artist_participation_links=2,new_exact_artwork_links=0,new_images=0,existing_records_enriched=0)
    save(E/'independent-database-verification.json',dict(at=c.now(),target=t,plan_sha256=pin,rows=rows,verified_counts=counts,
        attribution='All counted IDs absent in shared-lock transaction preimage, persisted source/citation plan checksums match this operation, and rows verified on a new read-only production connection. No prior or concurrent job increments included.',
        existing_institution_source_and_1975_event_unchanged=True,passed=True))
    pubs=[]
    for e in plan['events']:
        url=API+'exhibitions/'+e['id'];response=requests.get(url,timeout=(15,45));response.raise_for_status();j=response.json()
        assert j['id']==e['id'] and j['title']==e['title'] and j['startYear']==1983 and j['endYear']==1983
        assert j['entryCount']==0 and len(j['venues'])==1 and len(j['participants'])==1
        assert j['participants'][0]['artist_id']==e['artist_id']
        save(R/('public-'+e['id']+'.json'),j)
        pubs.append(dict(url=url,status=response.status_code,sha256=c.sha(response.content),exhibition_id=e['id'],
                         artist_id=e['artist_id'],venues=j['venues'],participants=j['participants'],entry_count=0,passed=True))
    save(E/'independent-public-verification.json',dict(at=c.now(),plan_sha256=pin,receipts=pubs,passed=True))
    print(json.dumps(counts))


def finalize():
    plan=c.load(E/'plan.json');pin=c.load(E/'plan-pin.json')['sha256'];v=c.load(E/'independent-database-verification.json')
    assert v['passed'] and c.load(E/'independent-public-verification.json')['passed']
    assert c.load(E/'independent-public-relationship-verification.json')['passed']
    assert c.load(E/'backup-verification.json')['passed']
    assert c.load(E/'prior-programme-recovery-verification.json')['passed']
    startup=c.load(E/'startup-verification.json');cp=c.load(E.parents[1]/'CHECKPOINT.json');assert cp['inflight']['batch']==148
    for k in ['worker_pid','supervisor_pid']:
        assert cp[k]==startup[k];os.kill(cp[k],0)
    for f in startup['supervisor_files']:assert c.sha(Path(f['path']).read_bytes())==f['sha256']
    ps=subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()
    workers=[x for x in ps if '/opt/homebrew/bin/codex exec ' in x and '--output-schema /Users/vadimdulub/Library/Application Support/Artline/continuous-exhibition-research/schema.json' in x]
    assert len(workers)==1 and int(workers[0].split()[0])==cp['worker_pid'] and int(workers[0].split()[1])==cp['supervisor_pid']
    lockpath=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/supervisor.lock'
    holders=subprocess.check_output(['lsof','-a','-p',str(cp['supervisor_pid'])+','+str(cp['worker_pid']),str(lockpath)],text=True)
    assert all(str(cp[k]) in holders for k in ['supervisor_pid','worker_pid'])
    save(E/'continuation-process-verification.json',dict(at=c.now(),supervisor_pid=cp['supervisor_pid'],worker_pid=cp['worker_pid'],
        supervisor_and_worker_running=True,single_exhibition_worker=True,inherited_singleton_lock_open=True,
        supervisor_and_protected_artwork_programme_files_unchanged=True,new_supervisor_started=False,passed=True))
    nxt='Continue Moralis 1988 from printed page 258 (PDF 259), or inspect original catalogues for the newly documented Sikeliotis and Dimitriadis 1983 drawing shows. Retain the three retrospective-medium leads and NMWA/Arthive access holds; do not replay these two event IDs.'
    rel=lambda name:str((E/name).relative_to(ROOT))
    evidence_names=['startup-verification.json','source-capture-verification.json','candidate-review-verification.json',
                    'provider-access-verification.json','independent-database-verification.json','independent-public-verification.json',
                    'independent-public-relationship-verification.json','backup-verification.json','prior-programme-recovery-verification.json',
                    'continuation-process-verification.json','queue-update-verification.json','CHECKPOINT.json','final-verification.json']
    with Q.with_suffix('.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        before=c.load(Q);q=serial(before);before_sha=c.sha(Q.read_bytes())
        g=next(x for x in q['sources'] if x['source_id']=='national_gallery_athens')
        g['last_checked_at']=c.now();g['research_status']='batch148_two_1983_drawing_events_two_creators_verified'
        g.setdefault('cursor',{})['batch148']=dict(completed_urls=[x['receipt']['url'] for e in plan['events'] for x in e['sources']],
            completed_native_ids=[x['native_id'] for e in plan['events'] for x in e['sources']],
            production_exhibition_ids=[e['id'] for e in plan['events']],new_creator_ids=[a['id'] for a in plan['artists']],
            source_evidence=rel('source-capture-verification.json'),next=nxt)
        g['cursor'].setdefault('completed',[])
        for e in plan['events']:
            if e['sources'][0]['receipt']['url'] not in g['cursor']['completed']:g['cursor']['completed'].append(e['sources'][0]['receipt']['url'])
        g.setdefault('holds',[]).append(dict(key='batch148-three-retrospective-medium-leads',at=c.now(),
            candidates=['Dimitris Sakellaridis 1982','Spyros Vassiliou 1983','Kostas Plakotaris 1983'],
            reason='Exact dates and venue captured; original exhibition catalogue/pictorial-medium confirmation remains pending. No forced artist or object links. Vassiliou title1902 versus biography1903 retained.',
            evidence=rel('candidate-review-verification.json')))
        g.setdefault('evidence',[]).extend([rel('independent-database-verification.json'),rel('independent-public-verification.json'),rel('candidate-review-verification.json')])
        n=next(x for x in q['sources'] if x['source_id']=='nmwa_japan');n['last_checked_at']=c.now();n['research_status']='access_held_http403_batch148'
        n['cursor']=dict(batch=148,url='https://www.nmwa.go.jp/en/exhibitions/',historical_archive_coverage='unassessed_due_to_access_hold',
                         next='Await documented provider access-state change. Do not retry unchanged requests.')
        n.setdefault('holds',[]).append(dict(at=c.now(),type='provider_access_http403',url=n['cursor']['url'],evidence=rel('provider-access-verification.json')))
        n.setdefault('evidence',[]).append(rel('provider-access-verification.json'))
        assert before['supplemental_sources']==q['supplemental_sources']
        excluded={'national_gallery_athens','nmwa_japan'}
        assert [x for x in before['sources'] if x['source_id'] not in excluded]==[x for x in q['sources'] if x['source_id'] not in excluded]
        save(B/'source-queue-before.json',before)
        tmp=Q.with_suffix('.batch148.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q)
        assert c.load(Q)==q
    save(E/'queue-update-verification.json',dict(at=c.now(),before_sha256=before_sha,after_sha256=c.sha(Q.read_bytes()),
        updated_sources=['national_gallery_athens','nmwa_japan'],all_unrelated_entries_and_supplemental_sources_preserved=True,
        moralis_cursor_preserved=True,registry_unmodified=True,next_task=nxt,passed=True))
    checkpoint=dict(at=c.now(),batch=148,stage='verified_complete',plan_sha256=pin,verified_counts=v['verified_counts'],
                    production_ids=[e['id'] for e in plan['events']],next_task=nxt,holds=plan['holds'],external_supervisor_unchanged=True)
    save(E/'CHECKPOINT.json',checkpoint);save(R/'CHECKPOINT.json',checkpoint)
    result=dict(outcome='progress',summary='Added and independently verified two Athens drawing exhibitions from 1983, two venue stops, two review-state artists and two explicit artist participation links. Checklists remain unknown; no objects or images were inferred. Source queue and checkpoint saved; existing supervisor and worker verified running.',
                next_task=nxt,blocker='',verified_counts=v['verified_counts'],evidence_paths=[rel(x) for x in evidence_names])
    save(E/'final-verification.json',dict(**result,at=c.now(),plan_sha256=pin,passed=True))
    save(E/'worker-result.json',result)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['prepare','apply','verify','finalize']
    globals()[sys.argv[1]]()
