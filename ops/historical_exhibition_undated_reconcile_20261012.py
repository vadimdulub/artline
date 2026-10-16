"""Review the frozen 154-record undated remainder using original source fields.

Year extraction is for scope decisions, not automatic day repair. Artist lives,
work dates, titles, source publication years and retrieval times are excluded.
"""
from pathlib import Path
from collections import Counter, defaultdict
import gzip
import json
import re
import sys

from psycopg.types.json import Jsonb
import exhibitions_common as c

OUT=Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/undated-legacy'
BACKUP=Path.home()/'Library/Application Support/Artline/backups/historical-exhibitions-release-20261012/undated-legacy'
BATCH='historical-exhibition-undated-reconciliation-20261012'
PLAN=OUT/'reviewed-plan.json'
TABLES=['exhibition_object_entries','exhibition_research_people','exhibition_research',
        'exhibition_entries','exhibition_publications','exhibition_participants',
        'exhibition_occurrences','exhibition_source_records']
MEDIUM={
 '417a6777-082a-501e-acfc-7c6d87d50851':'Chinese Imperial Porcelain: source title explicitly identifies excluded porcelain; no pictorial entries.',
 '470209fc-e75c-516e-ab47-0f45d0a43be1':'Source title explicitly says 写真展 (photography exhibition); no pictorial entries.',
 'e5da5785-0a86-595b-abc7-3f9ecb037624':'Roger Parry: Vintage Photographs; both source objects are gelatin silver photographs.',
 'eafa0469-9d4b-536e-b118-9d0554105439':'Venetian Glass; all three source objects are glass vessels, with no painting/drawing/print/icon evidence.'}
NON_EVENT={
 '23adfc6c-d5c1-536f-b7b4-1f3ba4ffef37':'Source explicitly labels Duplicate (36th May Show - no objects). No venues, dates or objects.',
 'a49d33f8-9834-5720-91a5-3f9aabe1f385':'Source explicitly labels Duplicate (37th May Show - no objects). No venues, dates or objects.',
 'b6c7297f-7ce2-5650-a31d-dd820768a646':'Empty source record titled sample exhibition, without dates, venues, organizer or objects. Not a documented event.',
 'ea691c72-ae7f-5af1-8176-c501d6993295':'Empty source record titled x, without dates, venues, organizer or objects. Not a documented event.'}
# Editorially selected single-event year recoveries. A second explicit year is
# retained only where the range is not reversed. Never supply missing days.
RECOVER={
 '01e3d67f-7d31-5e4a-84d8-7458fea60b9e':(1968,None,'1968; exact dates need review'),
 '0693edc1-9c06-595d-bb35-0afd4be2b281':(1965,None,'1965; exact dates need review'),
 '12bd650b-6c9e-5a66-856e-279292d522da':(1974,None,'1974; exact dates need review'),
 '17f69235-ee11-5e64-b5d4-36fe56de7159':(1987,None,'1987; exact dates need review'),
 '4a48521d-33bc-5be6-8dfe-ad0393a01b24':(1984,1984,'1984; opening and closing days unknown'),
 '616ced17-dd24-52b9-8332-b1aa6a3b0a46':(1985,None,'August 1985; exact dates unknown'),
 '6825f7cc-a3fd-5a95-b609-3d1125865965':(1981,None,'1981; source contains an invalid closing day'),
 '6be86d69-1729-5dc9-97d7-124359f52d64':(1975,1975,'1975; opening and closing days unknown'),
 'a83cdbf0-4ea7-526d-95a6-982af85ab1ad':(1982,None,'1982; source date range conflicts and closing year remains unresolved'),
 'b89903c9-6f93-550e-b48b-60261ef7bad0':(1982,1982,'1982; exact dates need review'),
 'c2aabeae-7f14-53e4-83a4-60d16b00a07a':(1989,1989,'1989; opening and closing days unknown'),
 'ce122f4c-364a-506b-8130-08b3e326bd19':(1984,1984,'1984; opening and closing days unknown'),
 'f56d983e-a4d4-52b3-a6e1-41d442144d2b':(1985,1985,'August–September 1985; exact dates unknown'),
 'fdbec17e-03b8-5ade-ad68-3bf8f6adce14':(1955,1955,'1–21 October and 4–27 November 1955; two separate display periods'),
 'ff7489f9-00c2-51b3-aaf0-0cd6eeb0e17a':(1985,1985,'October–November 1985; exact dates unknown')}
HOLD_REASONS={
 '56124e6d':'Installation: physical pictorial medium remains unresolved.',
 '6e5575f7':'Hamada exhibition: potter identity alone cannot exclude possible drawings; checklist needed.',
 'e33400e7':'Hirakushi exhibition: sculptor identity alone is not proof of an exclusively sculpture checklist.',
 'c039ff18':'Exhibition title names sculptors, not the physical media of every work; possible drawings remain unresolved.',
 '82cc44ff':'Tour has one dated November 1958 stop and four undated stops; do not invent the full tour span.',
 'bf38bac3':'Two sections grouped by publisher tour ID; bracketed 1962 dates and section/event identity need review.',
}


def normal(v):
    return json.loads(json.dumps(v,default=str))


def date_evidence(s):
    v=s['source_payload'];key=s['source_key'];fields={};years=[]
    if key=='apj_full':
        fields=v.get('period') or {}
        for value in fields.values():
            years.extend(int(x) for x in re.findall(r'(?<!\d)(?:19\d{2}|20\d{2})(?!\d)',value or ''))
    elif key=='artsy':
        fields={k:v.get(k) for k in ('startAt','endAt')}
        years=[int(x[:4]) for x in fields.values() if x and re.match(r'^\d{4}-',x)]
    elif key=='cleveland':
        fields={k:v.get(k) for k in ('opening_date','closing_date')}
        fields['venues']=[{k:o.get(k) for k in ('name','start_date','end_date')} for o in v.get('venues') or []]
        dates=[fields['opening_date'],fields['closing_date']]+[o.get(k) for o in fields['venues'] for k in ('start_date','end_date')]
        years=[int(x[:4]) for x in dates if x and re.match(r'^\d{4}-',x)]
    elif key=='moma':
        fields={k:v['exhibition'].get(k) for k in ('ExhibitionBeginDate','ExhibitionEndDate')}
        years=[int(x.split('/')[-1]) for x in fields.values() if x]
    else:
        raise AssertionError(key)
    return dict(sourceID=s['id'],sourceKey=key,sourceURL=s['source_url'],fields=fields,years=sorted(set(years)))


def verify_original_captures(sources):
    checked={}
    for s in sources:
        key=c.sha(s['capture_url'].encode())
        if key not in checked:
            path=c.DATA/'captures'/(key+'.body.gz')
            checked[key]=c.sha(gzip.decompress(path.read_bytes()))
        assert checked[key]==s['capture_sha256']
    return len(checked)


def plan():
    a=c.load(OUT/'source-audit.json');assert len(a['events'])==154 and len(a['sources'])==164
    capture_count=verify_original_captures(a['sources']);by=defaultdict(list)
    for s in a['sources']:by[s['exhibition_id']].append(s)
    decisions=[]
    for event in a['events']:
        id=event['id']; sources=by[id];evidence=[date_evidence(s) for s in sources]
        years=sorted(set(y for r in evidence for y in r['years']))
        action='hold';reason=HOLD_REASONS.get(id[:8],'Dates absent or conflicting. Preserve for source and checklist research.');recovery=None
        if any(y>=1990 for y in years):
            action='remove_date';reason='Source event-period fields explicitly include 1990 or later. Malformed days or reversed ranges do not make these modern years historical. Work dates and artist lifetimes are not used.'
        elif id in MEDIUM:action='remove_medium';reason=MEDIUM[id]
        elif id in NON_EVENT:
            action='remove_non_event';reason=NON_EVENT[id]
            assert all(not s['source_payload'].get('venues') and not s['source_payload'].get('artworks') and not s['source_payload'].get('organizer') for s in sources)
        elif id in RECOVER:
            action='recover_year';sy,ey,display=RECOVER[id]
            assert len(sources)==1 and sources[0]['source_key']=='apj_full'
            assert years==[sy] and (ey is None or ey==sy)
            assert all(1600<=y<=1989 for y in years)
            assert event['start_date'] is None and event['end_date'] is None
            recovery=dict(startYear=sy,endYear=ey,dateDisplay=display,datePrecision='year',sourceID=sources[0]['id'])
            reason='Recover the explicitly written event year only. Preserve unknown days, original date labels, status, participation and uncertain event state.'
        decisions.append(dict(id=id,title=event['title'],action=action,reason=reason,evidence=evidence,recovery=recovery))
    counts=dict(Counter(r['action'] for r in decisions))
    assert counts==dict(remove_date=97,remove_medium=4,remove_non_event=4,recover_year=15,hold=34),counts
    ids=[r['id'] for r in decisions if r['action'].startswith('remove_')]
    with c.connect() as db:
        current=db.execute('SELECT * FROM exhibitions WHERE id=ANY(%s::uuid[]) ORDER BY id',([r['id'] for r in a['events']],)).fetchall()
        assert normal(current)==a['events']
        sources=db.execute('SELECT * FROM exhibition_source_records WHERE exhibition_id=ANY(%s::uuid[]) ORDER BY exhibition_id,id',([r['id'] for r in a['events']],)).fetchall()
        assert normal(sources)==a['sources']
        assert not db.execute('SELECT id FROM exhibitions WHERE parent_exhibition_id=ANY(%s::uuid[]) AND NOT(id=ANY(%s::uuid[]))',(ids,ids)).fetchall()
        assert not db.execute('SELECT id FROM exhibitions WHERE id=ANY(%s::uuid[]) AND parent_exhibition_id IS NOT NULL',(ids,)).fetchall()
        backup=dict(at=c.now(),exhibitions=[e for e in a['events'] if e['id'] in set(ids)])
        for table in TABLES:
            backup[table]=db.execute(f'SELECT * FROM {table} WHERE exhibition_id=ANY(%s::uuid[]) ORDER BY exhibition_id',(ids,)).fetchall()
        # These legacy rows have no expanded research projections to mutate.
        assert all(not backup[t] for t in TABLES[:3])
        retained=[r['id'] for r in decisions if not r['action'].startswith('remove_')]
        backup['retained_entries']=db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=ANY(%s::uuid[]) ORDER BY id',(retained,)).fetchall()
        before=db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
    c.save(BACKUP/'preimage.json.gz',backup)
    c.save(PLAN,dict(at=c.now(),batch=BATCH,decisions=decisions,counts=counts,beforeActive=before,
                    auditSHA256=c.sha((OUT/'source-audit.json').read_bytes()),originalCapturesVerified=capture_count,
                    backupPath=str(BACKUP/'preimage.json.gz'),backupSHA256=c.sha((BACKUP/'preimage.json.gz').read_bytes()),
                    dependentCounts={t:len(backup[t]) for t in TABLES},removedEvents=len(ids),mainCatalogueWrites=False,realLocalDatabaseWrites=False))
    print('Prepared',counts,'dependents', {t:len(backup[t]) for t in TABLES})


def apply():
    p=c.load(PLAN);a=c.load(OUT/'source-audit.json');backup=c.load(Path(p['backupPath']))
    assert c.sha((OUT/'source-audit.json').read_bytes())==p['auditSHA256']
    assert c.sha(Path(p['backupPath']).read_bytes())==p['backupSHA256']
    assert verify_original_captures(a['sources'])==p['originalCapturesVerified']
    allids=[e['id'] for e in a['events']];remove=[d['id'] for d in p['decisions'] if d['action'].startswith('remove_')]
    counts={}
    with c.connect(write=True) as db:
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        current=db.execute('SELECT * FROM exhibitions WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(allids,)).fetchall()
        assert normal(current)==a['events'],'Frozen event rows changed'
        sources=db.execute('SELECT * FROM exhibition_source_records WHERE exhibition_id=ANY(%s::uuid[]) ORDER BY exhibition_id,id FOR UPDATE',(allids,)).fetchall()
        assert normal(sources)==a['sources'],'Frozen sources changed'
        assert not db.execute('SELECT id FROM exhibitions WHERE parent_exhibition_id=ANY(%s::uuid[])',(remove,)).fetchall()
        for table in TABLES:
            current=db.execute(f'SELECT * FROM {table} WHERE exhibition_id=ANY(%s::uuid[]) ORDER BY exhibition_id FOR UPDATE',(remove,)).fetchall()
            # Compare by complete row value; tie order within an event is not semantic.
            assert sorted(json.dumps(x,sort_keys=True,default=str) for x in normal(current))==sorted(json.dumps(x,sort_keys=True) for x in backup[table]),table
            counts[table]=db.execute(f'DELETE FROM {table} WHERE exhibition_id=ANY(%s::uuid[])',(remove,)).rowcount
            assert counts[table]==p['dependentCounts'][table]
        counts['exhibitions']=db.execute('DELETE FROM exhibitions WHERE id=ANY(%s::uuid[])',(remove,)).rowcount
        assert counts['exhibitions']==105
        before_by={e['id']:e for e in a['events']}
        for d in p['decisions']:
            if d['action']!='recover_year':continue
            r=d['recovery'];before=before_by[d['id']]
            note=dict(operation=BATCH,basis=d['reason'],previousEvent=before,explicitEventYears=d['evidence'][0]['years'],
                      originalPeriod=d['evidence'][0]['fields'],dateConflictPreserved=d['id'].startswith('a83cdbf0'))
            db.execute('UPDATE exhibitions SET start_year=%s,end_year=%s,date_display=%s,date_precision=%s,state_basis=%s,updated_at=now() WHERE id=%s',
                       (r['startYear'],r['endYear'],r['dateDisplay'],r['datePrecision'],before['state_basis']+' Explicit event year recovered from original period; exact date ambiguities remain in source evidence.',d['id']))
            db.execute('UPDATE exhibition_source_records SET interpretation=interpretation||%s WHERE id=%s',
                       (Jsonb(dict(historical_year_reconciliation=note)),r['sourceID']))
        counts['yearRecoveries']=15
    c.save(OUT/'delivered.json',dict(at=c.now(),batch=BATCH,counts=counts,decisionCounts=p['counts'],planSHA256=c.sha(PLAN.read_bytes()),mainCatalogueWrites=False,realLocalDatabaseWrites=False,localBackupsPreserved=True))
    print('Committed',counts)


def verify():
    p=c.load(PLAN);a=c.load(OUT/'source-audit.json');backup=c.load(Path(p['backupPath']))
    by={e['id']:e for e in a['events']};remove=[d['id'] for d in p['decisions'] if d['action'].startswith('remove_')]
    retained=[d['id'] for d in p['decisions'] if not d['action'].startswith('remove_')]
    with c.connect() as db:
        for t in ['exhibitions']+TABLES:
            field='id' if t=='exhibitions' else 'exhibition_id'
            assert db.execute(f'SELECT count(*) n FROM {t} WHERE {field}=ANY(%s::uuid[])',(remove,)).fetchone()['n']==0,t
        now={str(e['id']):normal(e) for e in db.execute('SELECT * FROM exhibitions WHERE id=ANY(%s::uuid[])',(retained,)).fetchall()}
        assert len(now)==49
        for d in p['decisions']:
            if d['action'].startswith('remove_'):continue
            r=now[d['id']];old=by[d['id']]
            if d['action']=='hold':assert r==old;continue
            plan=d['recovery'];assert r['start_year']==plan['startYear'] and r['end_year']==plan['endYear']
            assert r['start_date'] is None and r['end_date'] is None
            assert r['date_display']==plan['dateDisplay'] and r['date_precision']=='year'
            changed={'start_year','end_year','date_display','date_precision','state_basis','updated_at'}
            assert {k:v for k,v in r.items() if k not in changed}=={k:v for k,v in old.items() if k not in changed}
        sources=db.execute('SELECT * FROM exhibition_source_records WHERE exhibition_id=ANY(%s::uuid[]) ORDER BY exhibition_id,id',(retained,)).fetchall()
        original={s['id']:s for s in a['sources']}
        for s in normal(sources):
            old=original[s['id']];assert {k:v for k,v in s.items() if k!='interpretation'}=={k:v for k,v in old.items() if k!='interpretation'}
        entries=db.execute('SELECT * FROM exhibition_entries WHERE exhibition_id=ANY(%s::uuid[]) ORDER BY id',(retained,)).fetchall()
        assert normal(entries)==backup['retained_entries']
        active=db.execute("SELECT count(*) active,count(*) FILTER(WHERE start_year BETWEEN 1600 AND 1989) dated_start_within_scope,count(*) FILTER(WHERE start_year IS NULL) undated_legacy,count(*) FILTER(WHERE start_year<1600 OR start_year>1989 OR end_year>1989) outside_by_date_fields,min(start_year) earliest_dated FROM exhibitions WHERE status<>'archived'").fetchone()
        assert active['undated_legacy']==34 and active['outside_by_date_fields']==0
    c.save(OUT/'verified.json',dict(at=c.now(),removedEvents=105,removalReasons={k:v for k,v in p['counts'].items() if k.startswith('remove_')},yearRecoveries=15,remainingUndated=34,
        activeExhibitions=active,allRetainedEntriesUnchanged=True,allOriginalSourcePayloadsUnchanged=True,all34HeldEventRowsUnchanged=True,mainCatalogueWrites=False,realLocalDatabaseWrites=False))
    print('Verified',active)


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ('plan','apply','verify'):
        raise SystemExit('Use plan, apply or verify')
    globals()[sys.argv[1]]()
