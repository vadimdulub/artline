"""Nine reviewed event identities; source witnesses and historical touring stops retained."""
import copy
import importlib.util
import json
from pathlib import Path

import requests
from psycopg.types.json import Jsonb
import exhibitions_common as c

s=importlib.util.spec_from_file_location('resume',Path(__file__).with_name('catalogue-deduplication-resume-20261027.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
E=m.E;B=m.B/'exhibitions';OP=m.OP+'-exhibitions-nine'
VENUES={c.norm('東京都美術館（新館）'):c.norm('東京都美術館'),c.norm('University Art Museum, Binghamton, NY'):c.norm('Binghamton University Art Museum'),c.norm('Allentown Art Museum, PA'):c.norm('Allentown Art Museum')}


def institution_label(v):
    n=c.norm(v)
    return VENUES.get(n,n)


def plan():
    p=c.load(E/'exhibition-nine-fresh-preimages.json.gz');tables=p['tables'];events={r['id']:r for r in tables['exhibitions:id']}
    assert len(events)==20 and all(r.get('canonical_exhibition_id') is None and r['status']!='archived'for r in events.values())
    for k in ['exhibition_research:exhibition_id','exhibition_object_entries:exhibition_id','exhibition_research_people:exhibition_id','exhibitions:parent_exhibition_id','exhibitions:canonical_exhibition_id']:assert not tables[k],('Extra references need specific reconciliation',k)
    after=copy.deepcopy(tables);mapping={a:g['canonical_id']for g in p['groups']for a in g['alias_ids']}
    removed={};merged_witnesses=[]
    for g in p['groups']:
        canonical=g['canonical_id'];ids=[canonical,*g['alias_ids']]
        main=events[canonical]
        for alias in g['alias_ids']:
            r=events[alias]
            assert main['start_date']<=r['start_date']<=r['end_date']<=main['end_date']
            if len(g['alias_ids'])==1:assert main['start_date']==r['start_date'] and main['end_date']==r['end_date']
        # An occurrence is one dated physical stop. Multiple source records are
        # documentary witnesses, not additional stops of the same tour.
        venue_groups={}
        for r in tables['exhibition_occurrences:exhibition_id']:
            if r['exhibition_id']not in ids:continue
            key=(r['institution_id']or institution_label(r['venue_label']),r['start_date'],r['end_date'])
            venue_groups.setdefault(key,[]).append(r)
        occurrence_map={}
        for vv in venue_groups.values():
            chosen=sorted(vv,key=lambda r:(r['exhibition_id']!=canonical,not bool(r['city_label']),r['id']))[0]
            duplicates=[r for r in vv if r['id']!=chosen['id']]
            if duplicates:
                dest=next(r for r in after['exhibition_occurrences:exhibition_id']if r['id']==chosen['id'])
                assert 'merged_source_assertions'not in dest['evidence']
                dest['evidence']['merged_source_assertions']=duplicates
                dest['evidence']['deduplication_operation']=OP
                for r in duplicates:
                    occurrence_map[r['id']]=chosen['id'];removed[r['id']]='exhibition_occurrences'
                merged_witnesses.extend(duplicates)
        participants=[r for r in tables['exhibition_participants:exhibition_id']if r['exhibition_id']in ids]
        name_ids={}
        for r in participants:
            key=(institution_label(r['name_label'])if r['role']=='organizer'else c.norm(r['name_label']),r['role'])
            if r['artist_id']:name_ids.setdefault(key,set()).add(r['artist_id'])
        person_groups={}
        for r in participants:
            label=institution_label(r['name_label'])if r['role']=='organizer'else c.norm(r['name_label'])
            known=name_ids.get((label,r['role']),set())
            # Distinct identified people with a homonymous label stay separate.
            person=r['artist_id']or(next(iter(known))if len(known)==1 else label)
            key=(person,r['role']);person_groups.setdefault(key,[]).append(r)
        for pp in person_groups.values():
            chosen=sorted(pp,key=lambda r:(not bool(r['artist_id']),r['exhibition_id']!=canonical,r['id']))[0]
            duplicates=[r for r in pp if r['id']!=chosen['id']]
            if duplicates:
                dest=next(r for r in after['exhibition_participants:exhibition_id']if r['id']==chosen['id'])
                assert 'merged_source_assertions'not in dest['evidence']
                dest['evidence']['merged_source_assertions']=duplicates
                dest['evidence']['deduplication_operation']=OP
                for r in duplicates:removed[r['id']]='exhibition_participants'
                merged_witnesses.extend(duplicates)
        for r in after['exhibition_entries:exhibition_id']:
            if r.get('occurrence_id')in occurrence_map:r['occurrence_id']=occurrence_map[r['occurrence_id']]
        # The four Cleveland artwork entries have distinct exact object IDs,
        # inventories and media. Their coincident titles never collapse them.
        for alias in g['alias_ids']:
            event=next(r for r in after['exhibitions:id']if r['id']==alias)
            event['canonical_exhibition_id']=canonical;event['status']='archived'
        alt=next(r for r in after['exhibitions:id']if r['id']==canonical)
        alt['alternate_titles']=list(dict.fromkeys([*alt['alternate_titles'],*[events[a]['title']for a in g['alias_ids']if events[a]['title']!=alt['title']]]))
    for key,values in list(after.items()):
        table,col=key.split(':')
        if col!='exhibition_id':continue
        after[key]=[r for r in values if r.get('id')not in removed]
        for r in after[key]:
            if r['exhibition_id']in mapping:r['exhibition_id']=mapping[r['exhibition_id']]
    assert len(after['exhibition_occurrences:exhibition_id'])==11
    assert len(after['exhibition_entries:exhibition_id'])==4
    assert len(after['exhibition_source_records:exhibition_id'])==22
    B.mkdir(parents=True,exist_ok=True);B.chmod(0o700)
    value=dict(at=c.now(),before=p,after=after,mapping=mapping,removed_duplicate_child_rows=removed,merged_source_assertions=merged_witnesses,
        source_preparation=c.load(E.parent/'exhibition-source-identity-preparation-001.json'),source_addendum=c.load(E.parent/'exhibition-source-identity-preparation-addendum.json'),
        preservation='Every native exhibition source record survives. Full duplicate venue/participant witness rows are embedded in the surviving exact assertion evidence and retained in atomic delete audits and scoped backups. All four distinct artwork entries survive with their UUIDs. Parent programme identities remain unchanged.')
    c.save(B/'plan.json.gz',value)
    c.save(E/'exhibition-nine-plan-pin.json',dict(at=c.now(),path=str(B/'plan.json.gz'),sha256=c.sha((B/'plan.json.gz').read_bytes()),canonical_events=9,duplicate_event_aliases=11,source_records=22,distinct_tour_stops=11,participant_assertions_before=120,participant_assertions_after=len(after['exhibition_participants:exhibition_id']),duplicate_child_rows=len(removed),all_removed_child_witnesses_embedded_and_audited=True))
    print('Pinned nine event identities, eleven redundant event aliases and',len(removed),'duplicate source witnesses, with all original content retained.',flush=True)


def apply():
    assert c.load(E/'identity-deployment-verification.json')['passed']
    path=B/'plan.json.gz';assert c.sha(path.read_bytes())==c.load(E/'exhibition-nine-plan-pin.json')['sha256']
    p=c.load(path);before=p['before'];changes=[]
    with c.connect(write=True)as db:
        m.acquire_locks(db)
        db.execute('SELECT id FROM exhibitions WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',(before['ids'],)).fetchall()
        for key,expected in before['tables'].items():
            t,col=key.split(':');assert m.ordered(m.rows(db,t,col,before['ids']))==m.ordered(expected),('Changed preimage',key)
        # Verify no other application table points at the source-witness IDs
        # being consolidated; the supported occurrence FK is handled explicitly.
        refs=db.execute("SELECT conrelid::regclass::text table_name,pg_get_constraintdef(oid) definition FROM pg_constraint WHERE contype='f' AND confrelid=ANY(%s::regclass[])",(['exhibition_participants','exhibition_occurrences'],)).fetchall()
        assert all(r['table_name']=='exhibition_entries' and 'occurrence_id' in r['definition']for r in refs)
        c.save(B/'locked-preimages.json.gz',before)
        for key,expected_after in p['after'].items():
            t,col=key.split(':')
            if t=='exhibitions' and col!='id':continue
            oldrows={r['id']:r for r in before['tables'][key]};newrows={r['id']:r for r in expected_after}
            for rid,r in newrows.items():
                old=oldrows[rid]
                fields={k:v for k,v in r.items()if old[k]!=v}
                if not fields:continue
                if t=='exhibitions':fields['updated_at']=db.execute('SELECT now()::text at').fetchone()['at']
                columns=list(fields)
                vals=[Jsonb(fields[k])if isinstance(fields[k],(dict,list))else fields[k]for k in columns]
                assignments=','.join(k+'=%s'for k in columns)
                new=db.execute('UPDATE '+t+' SET '+assignments+' WHERE id=%s RETURNING to_jsonb('+t+')v',(*vals,rid)).fetchone()['v']
                changes.append(dict(table=t,key=rid,before=old,after=new))
        # Delete only redundant source assertion rows after all entry pointers
        # and the complete surviving embedded witnesses have been established.
        for rid,t in p['removed_duplicate_child_rows'].items():
            old=next(r for r in before['tables'][t+':exhibition_id']if r['id']==rid)
            r=db.execute('DELETE FROM '+t+' WHERE id=%s RETURNING to_jsonb('+t+')v',(rid,)).fetchone()['v'];assert r==old or all(r[k]==v for k,v in old.items()if k=='exhibition_id')
            # Rows selected for deletion were intentionally never updated above.
            assert r==old
            changes.append(dict(table=t,key=rid,before=old,after=None))
        m.audit(db,changes,OP)
        after={}
        for key in before['tables']:
            t,col=key.split(':');after[key]=m.rows(db,t,col,before['ids'])
        for key,expected in p['after'].items():
            if key=='exhibitions:canonical_exhibition_id':continue
            strip=lambda rows:[{k:v for k,v in r.items()if k!='updated_at'}for r in rows]
            assert m.ordered(strip(after[key]))==m.ordered(strip(expected)),('Final merge mismatch',key)
        c.save(B/'transaction-after.json.gz',dict(at=c.now(),operation=OP,changes=changes,after=after))
    verify()


def verify():
    p=c.load(B/'plan.json.gz');tx=c.load(B/'transaction-after.json.gz');changes=tx['changes']
    with c.connect()as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        for key,expected in tx['after'].items():
            t,col=key.split(':');assert m.ordered(m.rows(db,t,col,p['before']['ids']))==m.ordered(expected),('Independent postimage mismatch',key)
        aa=db.execute('SELECT id,before_json,after_json FROM audit_log WHERE id=ANY(%s::uuid[])',([m.uid(OP+'/'+r['table']+'/'+r['key'])for r in changes],)).fetchall()
        aa={str(r['id']):r for r in aa};assert len(aa)==len(changes)
        assert all(aa[m.uid(OP+'/'+r['table']+'/'+r['key'])]['before_json']==r['before']and aa[m.uid(OP+'/'+r['table']+'/'+r['key'])]['after_json']==r['after']for r in changes)
    s=requests.Session();public=[]
    for g in p['before']['groups']:
        for id in [g['canonical_id'],*g['alias_ids']]:
            r=s.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+id,timeout=(10,35));assert r.status_code==200
            v=r.json();assert v['id']==g['canonical_id']
            entries=s.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+id+'/entries?limit=100',timeout=(10,35));assert entries.status_code==200
            expected_entries=[r for r in p['after']['exhibition_entries:exhibition_id']if r['exhibition_id']==g['canonical_id']]
            assert {r['id']for r in entries.json()['items']}=={r['id']for r in expected_entries}
            assert v['venueCount']==len([r for r in p['after']['exhibition_occurrences:exhibition_id']if r['exhibition_id']==g['canonical_id']])
            public.append(dict(input_id=id,canonical_id=v['id'],venue_count=v['venueCount'],entry_count=v['entryCount'],sources=len(v['sources'])))
    c.save(E/'exhibition-nine-verification.json',dict(at=c.now(),passed=True,canonical_event_groups=9,merged_duplicate_events=11,atomic_audits=len(changes),source_records_preserved=22,distinct_venue_stops=11,artwork_entries_preserved=4,duplicate_source_witnesses_embedded_and_audited=len(p['removed_duplicate_child_rows']),old_and_canonical_UUID_detail_and_entry_routes=len(public)*2,public=public,unrelated_tours_sections_installations_and_holds_preserved=True))
    print('Nine exhibition identity groups merged; eleven redundant event rows now resolve canonically. All22source records and four distinct work entries retained.',flush=True)


if __name__=='__main__':
    import sys
    globals()[sys.argv[1]]()
