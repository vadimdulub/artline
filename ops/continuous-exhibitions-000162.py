"""Bounded exact-impression reconciliation. External supervisor owns continuation."""
import gzip, json, subprocess, sys
from pathlib import Path
import requests
from psycopg.types.json import Jsonb
import exhibitions_common as c

ROOT=c.ROOT
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000162'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000162'
B=Path.home()/'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000162'
OP='continuous-exhibitions-20261013-batch-000162'
ACTOR='local-european-research'
ARTIST='b67ddc7c-a73d-4b52-b065-8d317edeeb14'
INST='729385eb-92b0-4cc8-9229-1ac3a46aee1f'
SOURCE='d63cee47-716a-45ba-9e88-b552ff5b59c0'
WORK=c.uid('cleveland/artwork/106831')
API='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
serial=lambda x:json.loads(json.dumps(x,ensure_ascii=False,default=str))
save=lambda n,x:c.save(E/n,x)
uid=lambda key:c.uid(OP+'/'+key)

def target(db):
    cmd='/tmp/artline-cloud-sql-proxy --address 127.0.0.1 --port 55519 --gcloud-auth artline-508319:europe-west1:artline-postgres'
    assert cmd in [x.strip()for x in subprocess.check_output(['ps','-axo','command'],text=True).splitlines()]
    assert (db.info.host,db.info.port,db.info.dbname)==('127.0.0.1',55519,'artline')
    row=db.execute('select current_database() database,current_user role,pg_is_in_recovery() recovery').fetchone()
    assert row==dict(database='artline',role='artline_app',recovery=False)
    return dict(at=c.now(),instance='artline-508319:europe-west1:artline-postgres',host=db.info.host,port=db.info.port,**row)

def body(rc):
    raw=Path(rc['body_path']).read_bytes()
    if rc['body_path'].endswith('.gz'):raw=gzip.decompress(raw)
    assert c.sha(raw)==rc['sha256'] and len(raw)==rc['bytes'] and rc['status']==200
    return raw

def snapshot(db):
    live=c.load(E/'cleveland-live-reconciliation.json');eids=[x['exhibition_id']for x in live['entries']]
    out={}
    for t in ['exhibitions','exhibition_entries','exhibition_occurrences','exhibition_participants','exhibition_source_records','exhibition_publications']:
        col='id' if t=='exhibitions' else 'exhibition_id'
        out[t]=db.execute('select * from '+t+' where '+col+'=any(%s::uuid[]) order by id',(eids,)).fetchall()
    for t,col in [('artworks','id'),('artwork_artists','artwork_id'),('artwork_location_assertions','artwork_id')]:
        order='artwork_id,artist_id' if t=='artwork_artists' else 'id'
        out[t]=db.execute('select * from '+t+' where '+col+'=%s order by '+order,(WORK,)).fetchall()
    for t in ['citations','external_identifiers']:
        out[t]=db.execute('select * from '+t+" where entity_type='artwork' and entity_id=%s order by id",(WORK,)).fetchall()
    out['artists']=db.execute('select * from artists where id=%s',(ARTIST,)).fetchall()
    out['artist_aliases']=db.execute('select * from artist_aliases where artist_id=%s order by id',(ARTIST,)).fetchall()
    out['institutions']=db.execute('select * from institutions where id=%s',(INST,)).fetchall()
    out['sources']=db.execute('select * from sources where id=%s',(SOURCE,)).fetchall()
    return serial(out)

def duplicate_guard(db):
    assert not db.execute("select id from external_identifiers where entity_type='artwork' and ((scheme ilike '%%cleveland%%' and external_id='106831') or canonical_url like '%%clevelandart.org/art/1924.848.10%%')").fetchall()
    assert not db.execute("select id from artworks where accession_number in ('1924.848.10','1924.858')").fetchall()
    assert not db.execute("select id from artworks where slug='cleveland-1924-848-10-storm-at-sea'").fetchall()

def prepare():
    src=c.load(E/'cma-106831.json');d=json.loads(body(src['receipt']))['data'];assert d==src['data']
    assert d['id']==106831 and d['accession_number']=='1924.848.10' and d['record_type']=='component'
    assert d['type']=='Portfolio' and d['technique']=='etching' and d['state_of_the_work']=='iii/iii'
    assert d['creation_date_earliest']==d['creation_date_latest']==1701
    live=c.load(E/'cleveland-live-reconciliation.json');creator=c.load(E/'creator-and-event-reconciliation.json')
    assert any(a['normalized_alias']=='ludolf backhuysen'for a in creator['aliases'])
    assert creator['artist']['display_name']=='Ludolf Bakhuizen' and creator['artist']['death_year']==1708
    originals=[];entries=[]
    for s in live['source_records']:
        rc=c.load(c.RUN/'captures'/(c.sha(s['capture_url'].encode())+'.json'))
        raw=json.loads(body(rc));assert rc['sha256']==s['capture_sha256']
        event=next(x for x in raw['data']if x['id']==s['source_payload']['id']);assert event==s['source_payload']
        member=next(x for x in event['artworks']if x['id']==106831)
        assert member['accession_number']==d['accession_number'] and member['title']==d['title'] and member['url']==d['url']
        reciprocal=next(x for x in d['exhibitions']['current']if x['id']==event['id'])
        assert reciprocal['title']==event['title']
        entry=next(x for x in live['entries']if x['source_record_id']==s['id'])
        assert entry['artwork_id'] is None and entry['source_artwork_id']=='106831' and entry['title_label']==d['title']
        entries.append(dict(entry_id=entry['id'],exhibition_id=entry['exhibition_id'],source_record_id=s['id'],native_event_id=str(event['id']),new_source_id=uid('source/'+str(event['id'])),participant_id=uid('participant/'+str(event['id'])),event_title=event['title'],reciprocal=reciprocal))
        originals.append(dict(record=s,receipt=rc,member=member))
    with c.connect()as db:
        t=target(db);duplicate_guard(db);pre=snapshot(db)
        assert not db.execute('select id from audit_log where request_id=%s',(OP,)).fetchall()
    assert not pre['artworks'] and len(entries)==3
    assert all(e['status']=='review' and e['checklist_state']=='partial' and 1600<=e['start_year']<=e['end_year']<=1989 for e in pre['exhibitions'])
    assert not any(p['artist_id']==ARTIST or 'bakh' in p['name_label'].lower() or 'backh' in p['name_label'].lower()for p in pre['exhibition_participants'])
    assert pre['sources'][0]['slug']=='cleveland-museum-of-art'
    review=dict(at=c.now(),selected_existing_entries=10,selected_for_delivery=3,held_boston_entries=6,held_woodblock_entries=1,
        exact_identity='Cleveland native106831, accession1924.848.10, etching state iii/iii, sheet22x29.8cm, plate17.5x23.9cm. Individually accessioned portfolio component; parent1924.848 and other impressions are distinct.',
        duplicate_review='215 broad title/creator records examined by creator and provider identity. The same-composition Rijksmuseum print RP-P-BI-209/native200151641 is a distinct institutional impression, not this accession. Other Bakhuizen prints have separate accessions; no unaccessioned Bakhuizen record exists in the candidate set. MIA native106831 is a different artist/object; numerical cross-provider identity rejected.',
        creator='Existing Ludolf Bakhuizen alias exactly includes Ludolf Backhuysen. Source maker68582 is separately artist and publisher of the same sheet, not two creators. Museum birth1631 conflicts with catalogue1630; preserve both in evidence and do not rewrite the artist.',
        chronology='Museum dates work1701, corroborated by transcribed plate inscription. Independently present in1955 exhibition. No separate impression printing year invented.',
        participation='Three reciprocal native event memberships confirmed in checksum-verified original exhibition API captures and current object record. Preserve existing participation labels and occurrence associations. Posthumous representation, not personal attendance.',
        held='MFA robot verification prevents exact reconciliation of six Blake entries. Cleveland105741 is a Woodblock, not an identified paper impression; keep documentary and do not convert to a print or infer Rubens authorship.',
        images='No image downloaded, prepared, visually reviewed or uploaded. Museum CC0 field retained for106831;105741 Copyrighted label remains distinct.',
        complete_checklist=False,passed=True)
    p=dict(at=c.now(),operation=OP,target=t,work_id=WORK,artist_id=ARTIST,institution_id=INST,source_id=SOURCE,object_source=src,original_sources=originals,entries=entries,preimage=pre,review=review,
        duplicate_snapshot_sha256=c.sha((E/'cleveland-live-reconciliation.json').read_bytes()),creator_snapshot_sha256=c.sha((E/'creator-and-event-reconciliation.json').read_bytes()))
    B.mkdir(parents=True,exist_ok=True);B.chmod(0o700);save('immutable-plan.json',p);c.save(B/'immutable-plan.json',p)
    pin=c.sha((E/'immutable-plan.json').read_bytes());save('plan-pin.json',dict(operation=OP,sha256=pin))
    save('candidate-reconciliation-verification.json',review)
    save('source-capture-verification.json',dict(at=c.now(),object_receipt=src['receipt'],original_event_receipts=[o['receipt']for o in originals],all_raw_capture_checksums_verified=True,reciprocal_native_event_membership_verified=True,accession_and_component_identity_verified=True,images_viewed=0,passed=True))
    print('Prepared one review print, three existing-entry exact links and three artist connections.',flush=True)

def pinned():
    p=c.load(E/'immutable-plan.json');pin=c.load(E/'plan-pin.json')['sha256']
    assert p['operation']==OP and c.sha((E/'immutable-plan.json').read_bytes())==c.sha((B/'immutable-plan.json').read_bytes())==pin
    body(p['object_source']['receipt'])
    for o in p['original_sources']:body(o['receipt'])
    return p,pin

def audit(db,table,row,before,pin):
    db.execute('insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json)values(%s,%s,%s,%s,%s,%s,%s)',(ACTOR,'continuous_exhibition_exact_impression_reconciliation',table,row.get('id',row.get('artwork_id')),OP,Jsonb(before),Jsonb(dict(record=serial(row),plan_sha256=pin))))

def insert(db,table,row,pin):
    keys=list(row);vals=[Jsonb(v)if isinstance(v,(dict,list))else v for v in row.values()]
    out=db.execute('insert into '+table+'('+','.join(keys)+')values('+','.join(['%s']*len(keys))+') returning *',vals).fetchone()
    audit(db,table,out,None,pin);return out

def apply():
    p,pin=pinned();rc=p['object_source']['receipt'];d=p['object_source']['data']
    with c.connect(write=True)as db:
        target(db);db.execute("select set_config('artline.actor_user_id',%s,true)",(ACTOR,))
        db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('select pg_advisory_xact_lock(2026101201)')
        own=db.execute('select interpretation from exhibition_source_records where source_key=%s',(OP,)).fetchall()
        if own:
            assert len(own)==3 and all(x['interpretation']['plan_sha256']==pin for x in own) and (B/'transaction-preimage.json').exists()
            print('Own pinned transaction present; verification only.',flush=True);return
        db.execute('select id from exhibition_entries where id=any(%s::uuid[]) order by id for update',([x['entry_id']for x in p['entries']],))
        pre=snapshot(db);assert pre==p['preimage'];duplicate_guard(db)
        tx=db.execute('select txid_current()::text id').fetchone()['id'];t=target(db)
        backup=dict(at=c.now(),operation=OP,plan_sha256=pin,target=t,transaction_id=tx,rows=pre,locks=['artline-curated-ingestion',2026101201])
        c.save(B/'transaction-preimage.json',backup);save('transaction-preimage.json',backup)
        assert c.load(B/'transaction-preimage.json')==backup
        save('production-target-before-write.json',t|dict(plan_sha256=pin,passed=True))
        ev=dict(operation=OP,plan_sha256=pin,transaction_id=tx,source_capture=rc['body_path'],source_sha256=rc['sha256'],native_object='106831',accession='1924.848.10',former_accession='1924.858',parent_accession='1924.848',record_type='component',source_type='Portfolio',state='iii/iii',source_creator_roles=d['creators'],creator_birth_conflict='Museum1631; existing catalogue1630. Identity resolved by exact alias, same death1708 and established artist; birth unchanged.',source_creation='1701',independent_impression_date_unknown=True,checklist_complete=False,current_display_claim=False,rights_label=d['share_license_status'],images_added=0)
        insert(db,'artworks',dict(id=WORK,slug='cleveland-1924-848-10-storm-at-sea',title=d['title'],normalized_title=c.norm(d['title']),date_display='1701',creation_year_start=1701,creation_year_end=1701,date_precision='exact',work_type='print',medium_text='Etching on cream laid paper',dimensions_text=d['measurements'],accession_number=d['accession_number'],status='review',research_candidate=True,created_by=ACTOR,updated_by=ACTOR),pin)
        insert(db,'artwork_artists',dict(artwork_id=WORK,artist_id=ARTIST,attribution_role='primary',attribution_note='Official maker68582: Ludolf Backhuysen; unqualified artist, also separately credited as publisher. Cleveland accession1924.848.10, stateiii/iii. Existing alias reconciled;1631/1630 birth discrepancy retained in evidence.'),pin)
        insert(db,'external_identifiers',dict(id=uid('identifier'),entity_type='artwork',entity_id=WORK,scheme='cleveland-object',external_id='106831',canonical_url=d['url'],source_id=SOURCE,retrieved_at=rc['retrieved_at']),pin)
        insert(db,'citations',dict(id=uid('citation'),entity_type='artwork',entity_id=WORK,field_name='native_impression_identity_and_exhibition_connections',source_id=SOURCE,source_record_id='106831',source_url=rc['url'],page_or_locator='1924.848.10; Hollstein10; stateiii/iii; exhibitions300448/309956/310281',evidence_note=json.dumps(ev,ensure_ascii=False),retrieved_at=rc['retrieved_at'],created_by=ACTOR),pin)
        insert(db,'artwork_location_assertions',dict(id=uid('holding'),artwork_id=WORK,claim_type='holding',institution_id=INST,context='collection',source_id=SOURCE,source_url=rc['url'],evidence_note=json.dumps(ev|dict(holding_basis='Official museum accessioned object, Dudley P. Allen Fund; accession date1924-10-17. Holding does not derive from historical participation.'),ensure_ascii=False),checked_at=rc['retrieved_at'],review_state='accepted'),pin)
        for x in p['entries']:
            orig=next(o for o in p['original_sources']if o['record']['id']==x['source_record_id'])
            evidence=ev|dict(original_source_record=x['source_record_id'],original_event_capture_sha256=orig['receipt']['sha256'],native_event=x['native_event_id'],reciprocal_history=x['reciprocal'],historical_participation_only=True)
            insert(db,'exhibition_source_records',dict(id=x['new_source_id'],exhibition_id=x['exhibition_id'],source_key=OP,source_record_id='cleveland/106831/event/'+x['native_event_id'],source_url=rc['url'],retrieved_at=rc['retrieved_at'],capture_url=rc['body_path'],capture_sha256=rc['sha256'],source_payload=dict(object=d,original_exhibition_member=orig['member']),interpretation=evidence),pin)
            old=next(r for r in pre['exhibition_entries']if r['id']==x['entry_id'])
            updated=db.execute('update exhibition_entries set artwork_id=%s,evidence=%s,match_basis=%s where id=%s and artwork_id is null returning *',(WORK,Jsonb(old['evidence']|dict(canonicalObjectMatch=evidence,canonicalObjectMatchPending=False)),p['review']['exact_identity']+' Reciprocal exhibition native ID '+x['native_event_id']+' and original member accession agree.',x['entry_id'])).fetchone();assert updated
            audit(db,'exhibition_entries',updated,old,pin)
            insert(db,'exhibition_participants',dict(id=x['participant_id'],exhibition_id=x['exhibition_id'],source_record_id=x['new_source_id'],artist_id=ARTIST,name_label='Ludolf Backhuysen',role='artist',evidence=evidence|dict(participation_basis='Explicit exact etching membership; posthumous representation, not personal attendance. Source publisher role retained separately; no second participant inferred.')),pin)
        post=snapshot(db);c.save(B/'transaction-postimage.json',dict(at=c.now(),plan_sha256=pin,rows=post))
    save('applied.json',dict(at=c.now(),operation=OP,plan_sha256=pin,independent_verification_pending=True));print('Committed; independent verification pending.',flush=True)

def verify():
    p,pin=pinned();pre=c.load(B/'transaction-preimage.json');post=c.load(B/'transaction-postimage.json');old=pre['rows']
    assert pre['plan_sha256']==post['plan_sha256']==pin and old==p['preimage']
    with c.connect()as db:
        t=target(db);rows=snapshot(db);au=serial(db.execute('select * from audit_log where request_id=%s order by id',(OP,)).fetchall())
    assert rows==post['rows'] and len(au)==14 and all(a['after_json']['plan_sha256']==pin for a in au)
    for table in ['exhibitions','exhibition_occurrences','exhibition_publications','artists','artist_aliases','institutions','sources']:assert rows[table]==old[table]
    for table in ['exhibition_source_records','exhibition_participants']:
        oldids={x['id']for x in old[table]};assert [x for x in rows[table]if x['id']in oldids]==old[table]
        assert len(rows[table])-len(old[table])==3
    selected={x['entry_id']for x in p['entries']}
    assert [x for x in rows['exhibition_entries']if x['id']not in selected]==[x for x in old['exhibition_entries']if x['id']not in selected]
    for x in p['entries']:
        before=next(r for r in old['exhibition_entries']if r['id']==x['entry_id']);entry=next(r for r in rows['exhibition_entries']if r['id']==x['entry_id'])
        assert before['artwork_id'] is None and entry['artwork_id']==WORK and entry['evidence']['canonicalObjectMatch']['plan_sha256']==pin
        assert all(entry[k]==v for k,v in before.items()if k not in ['artwork_id','evidence','match_basis'])
        assert any(a['entity_id']==x['entry_id']and a['before_json']==before for a in au)
        assert any(s['id']==x['new_source_id']and s['interpretation']['plan_sha256']==pin for s in rows['exhibition_source_records'])
        assert any(s['id']==x['participant_id']and s['evidence']['plan_sha256']==pin and s['artist_id']==ARTIST for s in rows['exhibition_participants'])
    w=rows['artworks'][0];assert not old['artworks'] and w['status']=='review' and w['work_type']=='print' and w['accession_number']=='1924.848.10' and w['current_institution_id']==INST and w['primary_media_id']is None
    assert any(a['entity_id']==WORK and a['entity_type']=='artworks' and a['before_json']is None for a in au)
    assert json.loads(rows['citations'][0]['evidence_note'])['plan_sha256']==pin
    counts=dict(new_exhibitions=0,new_venue_stops=0,new_artists=0,new_catalogue_artworks=1,new_documentary_entries=0,new_artist_participation_links=3,new_exact_artwork_links=3,new_images=0,existing_records_enriched=3)
    save('independent-database-verification.json',dict(at=c.now(),operation=OP,target=t,plan_sha256=pin,rows=rows,audits=au,verified_counts=counts,attribution='Work absent and all three entries null in locked preimage. All14 audits plus persisted object citation, source records and participant evidence carry this plan checksum. Existing and concurrent campaign changes excluded.',passed=True))
    receipts=[]
    def get(key,url,params=None):
        res=requests.get(url,params=params,timeout=(15,45));res.raise_for_status();data=res.json();path=R/('public-'+key+'.json');c.save(path,data)
        receipts.append(dict(url=res.url,status=res.status_code,raw_sha256=c.sha(res.content),saved_sha256=c.sha(path.read_bytes()),path=str(path)));return data
    for x in p['entries']:
        eid=x['exhibition_id'];detail=get(eid+'-detail',API+'exhibitions/'+eid)
        assert any(a['artist_id']==ARTIST for a in detail['participants'])
        found=False;cursor=None
        for page in range(20):
            params=dict(limit=100)
            if cursor:params['cursor']=cursor
            data=get(eid+'-entries-'+str(page),API+'exhibitions/'+eid+'/entries',params)
            hits=[z for z in data['items']if z['id']==x['entry_id']]
            if hits:assert len(hits)==1 and hits[0]['artworkId']==WORK and not hits[0].get('image');found=True;break
            cursor=data.get('nextCursor')
            if not cursor:break
        assert found
    work=get('artwork',API+'artists/'+rows['artists'][0]['slug']+'/works/'+WORK)
    assert work['id']==WORK and work['status']=='review' and work['accession_number']=='1924.848.10' and work['holding']['id']==INST and work['display']is None
    assert work['dimensions_text']==w['dimensions_text'] and work['creation_year_start']==1701
    assert any(z['source_url']==p['object_source']['receipt']['url']for z in work['citations'])
    save('independent-public-verification.json',dict(at=c.now(),plan_sha256=pin,receipts=receipts,new_review_artworks=1,new_exact_links=3,new_artist_participation_links=3,partial_checklists_preserved=True,images_added=0,passed=True))
    save('backup-verification.json',dict(at=c.now(),plan_sha256=pin,kind='scoped affected-row transactional recovery backups; not a full database backup',files=[dict(path=str(B/n),sha256=c.sha((B/n).read_bytes()))for n in ['immutable-plan.json','transaction-preimage.json','transaction-postimage.json']],preimage_saved_and_decoded_before_write=True,postimage_matches_independent_read=True,backups_outside_Documents=True,passed=True))
    print(json.dumps(counts),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
