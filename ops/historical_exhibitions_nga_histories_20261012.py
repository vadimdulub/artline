#!/usr/bin/env python3
"""Reviewed NGA object-history exhibition links; production only, native IDs only.

The published CSV is metadata, not an image licence or a complete checklist.
Group numbers refer to the immutable discovery evidence for this phase.
"""
import collections
import json
import re
import sys
from pathlib import Path

from psycopg.types.json import Jsonb
import exhibitions_common as c

OUT = Path.home() / 'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/nga-object-histories'
BACKUP = Path.home() / 'Library/Application Support/Artline/backups/historical-exhibitions-release-20261012/nga-object-histories'
OP = 'historical-exhibitions-nga-histories-20261012'
MID = '4a7cf367-a105-f2bf-dc1c-a2210974752e'
URL = 'https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/main/data/objects_text_entries.csv'
TABLES = ['exhibitions', 'exhibition_occurrences', 'exhibition_entries', 'exhibition_participants', 'exhibition_source_records', 'exhibition_publications']
ALIASES = {
    49:29, 76:17, 135:17, 136:17, 179:17, 197:17, 77:4, 143:4, 210:4, 211:4,
    75:38, 178:38, 79:71, 80:26, 97:78, 98:41, 109:41, 103:90, 104:74, 215:74,
    111:70, 153:70, 165:1, 115:18, 138:18, 198:18, 118:3, 120:46, 122:69,
    123:124, 126:95, 127:11, 133:106, 139:31, 140:100, 145:43, 146:66, 147:93,
    148:161, 152:34, 184:156, 162:50, 173:50, 170:28, 174:96, 180:116,
    189:62, 192:62, 203:55, 213:20, 216:13, 177:8, 60:58, 119:63, 190:63,
    205:48,
}
HOLD = {
    19:'Two active catalogue identities already represent Durer in America 1971; resolve their sources and entries before enrichment.',
    25:'Same-title source period 1952–1959 may be an extended collection display. No one-year event inferred.',
    50:'Possible continuation of the source-dated 1953–1954 Masterpieces of Graphic Art display; no second event inferred from the 1954 citation.',
    59:'Recent Accessions versus Recent Acquisitions in 1950 requires original catalogue reconciliation; no second event inferred.',
    114:'Techniques section supplementary to the Callot installation; reconcile section-level participation before linking.',
    176:'Explicit supplementary techniques gallery, not the main Callot checklist; held with the section cohort.',
    137:'Complementary installation to the Dutch Drawings tour; participation not assigned to the main exhibition.',
    157:'Sculpture-only exhibition outside requested scope.',
    159:'Postcard prints reference may be distribution or reproduction rather than a held exhibition.',
    172:'Source title says 1980s for a 1977 exhibition. Resolve against original record before linking.',
    183:'Twentieth-Century French Paintings from the Dale Collection has extended-display identity ambiguity.',
    199:'Explicit permanent-collection loan, not a distinct exhibition.',
    204:'Explicit permanent-collection loan alongside an exhibition, not evidence of participation in it.',
    206:'Explicit permanent-collection loan, not a distinct exhibition.',
    212:'Explicit permanent-collection loan, not a distinct exhibition.',
}
RANGE_END = {2:1974,15:1982,71:1963,81:1981,83:1977,101:1985,112:1983,121:1966,
             129:1948,130:1951,151:1960,154:1966,155:1968,156:1969,158:1954,
             171:1970,175:1970,181:1987}
TOURS = {
    2:[('California Palace of the Legion of Honor','San Francisco','United States','US')],
    15:[('University of Iowa Museum of Art','Iowa City','United States','US')],
    83:[('Dallas Museum of Fine Arts','Dallas','United States','US'),('Detroit Institute of Fine Arts','Detroit','United States','US')],
    101:[('Galeries nationales du Grand Palais','Paris','France','FR'),('Schloss Charlottenburg','Berlin','West Germany','DE')],
}
QUALIFIED = re.compile(r'\b(workshop|follower|circle|after|attributed|school|anonymous|unknown|manner|style|copy|imitator|assistant)\b',re.I)
NEGATIVE = re.compile(r'\b(possibl[ey]|probably|may have|not exhibited|not shown|not lent|withdrawn|cancelled|canceled|discussed only|illustrated only|permanent collection|complementary|supplement)\b',re.I)
EXISTING = {
    10:'ce8cf895-328e-5ac4-80f9-be51c24d50cd', 13:'96b66559-78e0-5b32-b38c-c4f91a3c7906',
    34:'147daa50-6b62-5d49-b14e-90a2c60a1414', 42:'e160b525-24ff-5b25-a610-8aa771bdb0a1',
    47:'7aa1c135-9ab7-5525-a7af-c6d0fe6e0a84', 108:'a0b7158d-d761-5c66-9b81-e0ae6aa9a40c',
    110:'ee3384f4-5b3d-5e37-9d96-0cb61f2c1273', 150:'2ab4e735-8769-5f2e-aaab-11b95e96623a',
    168:'4c0cb124-7205-5e02-a121-d8ac50e15205', 195:'05b53117-0c6e-57a5-91e0-1b448519d65c',
    200:'27479a39-0dc8-5eec-824f-46586d323af8', 202:'c2580bc2-3c68-5154-9a10-a0262ec82899',
    214:'97bf0f07-c98a-5c3b-84e0-deb68cd23c26',
}


def normal(value):
    return json.loads(json.dumps(value, default=str))


def review():
    groups = c.load(OUT/'nga-venue-groups.json')['groups']
    histories = c.load(OUT/'histories.json.gz')['records']
    leads = collections.defaultdict(list)
    variants = collections.defaultdict(list)
    first = collections.defaultdict(list)
    for group in groups:
        if group['index'] in HOLD:
            continue
        key = c.norm(group['title'])
        first[key.split()[0]].append((group, key))
    for index, row in enumerate(histories):
        text = row['text']; n = c.norm(text)
        if not n or not re.search(r'National Gallery of Art|\bNGA\b', text, re.I):
            continue
        for group, key in first.get(n.split()[0], []):
            if row['year'] != str(group['year']) or not n.startswith(key+' '):
                continue
            root = ALIASES.get(group['index'], group['index'])
            m = re.search(r',\s*'+str(group['year'])+r'\b', text)
            if not m:
                continue
            tail = text[m.end():]
            item = dict(index=index, objectID=row['objectid'], text=text, tail=tail)
            variants[root].append(item)
            if re.match(r'\s*[-–/]\s*\d', tail) or re.search(r'\b(?:only|not shown|not exhibited|permanent|withdrawn|possibly|probably|cancelled|supplement|complementary)\b', text, re.I):
                leads[root].append(item)
    c.save(OUT/'expanded-title-review.json.gz', dict(at=c.now(),leads=dict(leads),variants=dict(variants),aliases=ALIASES,holds=HOLD))
    for root, rows in leads.items():
        tails = collections.Counter(r['tail'] for r in rows)
        print(root, groups[root]['title'], 'ROWS', len(rows), 'TAILS', list(tails)[:8])


def pins():
    names=['histories.json.gz','prefix-discovery.json.gz','nga-venue-groups.json','artwork-audit.json.gz',
           'event-institution-audit.json','existing-event-duplicate-candidates.json','expanded-title-review.json.gz']
    result={name:c.sha((OUT/name).read_bytes())for name in names}
    receipt=c.load(OUT/'source-receipt.json')
    import gzip
    assert c.sha(gzip.decompress(Path(receipt['body_path']).read_bytes()))==receipt['sha256']
    result['historyCSV']=receipt['sha256']
    obj=Path.home()/'Library/Application Support/Artline/source-metadata/million-catalogue-20261010/nga/objects.csv'
    result['objectCSV']=c.sha(obj.read_bytes())
    assert result['objectCSV']=='172191ec434b678859d577bad495b8076488078049cfe6881d20559075d5cd59'
    return result


def plan():
    pin=pins();groups=c.load(OUT/'nga-venue-groups.json')['groups']
    discovery={r['index']:r for r in c.load(OUT/'prefix-discovery.json.gz')['records']}
    audit=c.load(OUT/'artwork-audit.json.gz');old=c.load(OUT/'event-institution-audit.json')
    expanded=c.load(OUT/'expanded-title-review.json.gz')
    works={r['id']:r for r in audit['artworks']};native=collections.defaultdict(set);artists=collections.defaultdict(list)
    for r in audit['external']:native[r['external_id']].add(r['entity_id'])
    for r in audit['artists']:artists[r['artwork_id']].append(r)
    merged=collections.defaultdict(list);decisions=[];held=[]
    for g in groups:
        root=ALIASES.get(g['index'],g['index'])
        if g['index']in HOLD or root in HOLD:
            decisions.append(dict(group=g['index'],root=root,action='held',reason=HOLD.get(g['index'])or HOLD[root]));continue
        assert groups[root]['year']==g['year']
        merged[root].append(g)
        decisions.append(dict(group=g['index'],root=root,action='alias'if root!=g['index']else'reviewed',
            reason='Reviewed title spelling/subtitle variant, same museum and year; original wording retained.'if root!=g['index']else'Native museum exhibition-history evidence; compared titles, period and venue against the full existing event audit.'))
    existing_ids=list(EXISTING.values())
    with c.connect()as db:
        before={t:normal(db.execute('SELECT * FROM '+t+' WHERE '+('id'if t=='exhibitions'else'exhibition_id')+'=ANY(%s::uuid[]) ORDER BY id',(existing_ids,)).fetchall())for t in TABLES}
        assert not db.execute('SELECT 1 FROM exhibition_research WHERE exhibition_id=ANY(%s::uuid[])',(existing_ids,)).fetchone()
        assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
        before_active=db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
    current={r['id']:r for r in before['exhibitions']};pairs={(r['exhibition_id'],r['artwork_id'])for r in before['exhibition_entries']if r['artwork_id']}
    records=[];entries=[];already=[]
    for root,gs in merged.items():
        g=groups[root];eid=EXISTING.get(root)or c.uid(OP+'/event/'+str(root));new=root not in EXISTING
        occurrences=[r for r in before['exhibition_occurrences']if r['exhibition_id']==eid and r['institution_id']==MID]
        if not new:assert occurrences
        oid=c.uid(OP+'/occurrence/'+str(root))if new else sorted(occurrences,key=lambda r:r['id'])[0]['id']
        proof=[r for r in expanded['leads'].get(str(root),[])if re.match(r'\s*[-–/]\s*\d',r['tail'])]
        if root in RANGE_END:
            assert proof,(root,'range proof missing')
            for r in proof:
                short=re.match(r'\s*[-–/]\s*(\d{1,4})\b',r['tail']).group(1)
                end=int(str(g['year'])[:-len(short)]+short)if len(short)<4 else int(short)
                assert end==RANGE_END[root],(root,end)
        r=dict(root=root,id=eid,new=new,title=g['title'],year=g['year'],endYear=RANGE_END.get(root),
               dateDisplay=str(g['year'])+('–'+str(RANGE_END[root])if root in RANGE_END else''),
               occurrenceID=oid,sourceID=c.uid(OP+'/event-source/'+str(root)),
               aliases=[s['title']for s in gs if s['index']!=root],groups=[s['index']for s in gs],
               dateEvidence=proof,extraOccurrences=[],before=current.get(eid),entries=[])
        for venue,city,country,code in TOURS.get(root,[]):
            # A tour-level source does not provide separate stop dates or prove every object at every stop.
            r['extraOccurrences'].append(dict(id=c.uid(OP+'/tour/'+str(root)+'/'+c.norm(venue)),venue=venue,city=city,country=country,code=code))
        candidates=collections.defaultdict(list)
        for sourcegroup in gs:
            for ix in sourcegroup['recordIndexes']:
                row=discovery[ix];o=row['object'];reason=None
                if NEGATIVE.search(row['text']):reason='Qualified, negative or supplementary participation requires individual review.'
                elif 'recto only'in row['tail'].lower()and'[recto]'not in o['title'].lower():reason='Only recto was shown; this record is a different view.'
                elif 'verso only'in row['tail'].lower()and'[verso]'not in o['title'].lower():reason='Only verso was shown; this record is a different view.'
                elif len(native[row['objectID']])!=1:reason='No unique existing native museum-object identity; no new main artwork inferred.'
                if not reason:
                    aid=next(iter(native[row['objectID']]));w=works[aid]
                    if w['current_institution_id']!=MID or w['accession_number']!=o['accessionnum']:reason='Accession or institution cross-check conflicts.'
                    elif w['status']=='archived'or w['work_type']not in ['painting','drawing','print','icon']:reason='Existing work is archived or has an out-of-scope type.'
                    elif (w['creation_year_start']and w['creation_year_start']>g['year'])or(w['creation_year_end']and w['creation_year_end']>1970):reason='Existing creation interval conflicts with exhibition or catalogue cutoff.'
                    elif o['isvirtual']=='1':reason='Virtual parent/aggregate requires object-level review.'
                if reason:
                    held.append(dict(root=root,group=sourcegroup['index'],objectID=row['objectID'],history=row['text'],reason=reason));continue
                if(eid,aid)in pairs:
                    already.append(dict(root=root,artworkID=aid,objectID=row['objectID'],history=row['text']));continue
                candidates[aid].append(row)
        for aid,rows in candidates.items():
            native_ids={row['objectID']for row in rows};assert len(native_ids)==1
            obj=rows[0]['object'];nid=rows[0]['objectID'];nums=set()
            for row in rows:
                if re.search(r'not (?:included )?in (?:the )?cat|no cat|unnumbered|of (?:Voltri|checklist)|of checklist',row['tail'],re.I):continue
                nums.update(re.findall(r'\bno\.\s*(\d+(?:[a-z]|[-./]\d+[a-z]?)*)\b',row['tail'],re.I))
            entry=dict(id=c.uid(OP+'/entry/'+str(root)+'/'+nid),root=root,exhibitionID=eid,occurrenceID=oid,
                       artworkID=aid,objectID=nid,sourceID=c.uid(OP+'/object-source/'+str(root)+'/'+nid),
                       object={k:obj[k]for k in ['objectid','accessionnum','title','displaydate','beginyear','endyear','medium','dimensions','attribution','classification','parentid','isvirtual','creditline']},
                       histories=[dict(index=row['index'],text=row['text'],year=row['year'])for row in rows],
                       catalogueNumber=next(iter(nums))if len(nums)==1 else None,
                       numberReview='Multiple conflicting numbers retained only in original source text.'if len(nums)>1 else None,
                       partialDuration=any(re.search(r'only.*(?:part|weeks)|only on view',row['tail'],re.I)for row in rows),
                       before=works[aid],artistLinks=artists[aid])
            entries.append(entry);r['entries'].append(entry['id'])
        if r['entries']:
            records.append(r)
        else:
            decisions.append(dict(root=root,action='held_empty',reason='No eligible exact existing artwork links in this reviewed delivery.'))
    selected_ids={r['id']for r in records};assert all(e['exhibitionID']in selected_ids for e in entries)
    # Keep only preimages actually touched by this phase.
    before={t:[r for r in rows if(r['id']if t=='exhibitions'else r['exhibition_id'])in selected_ids]for t,rows in before.items()}
    existing_people={(r['exhibition_id'],r['artist_id'])for r in before['exhibition_participants']if r['artist_id']}
    participants={};person_holds=[]
    for e in entries:
        if QUALIFIED.search(e['object']['attribution']):continue
        for link in e['artistLinks']:
            key=(e['exhibitionID'],link['artist_id'])
            if key in existing_people or link['attribution_role']!='primary'or link['artist_status']=='archived':continue
            labels=[r for r in before['exhibition_participants']if r['exhibition_id']==e['exhibitionID']and not r['artist_id']and r['role']=='artist'and c.norm(r['name_label'])==c.norm(link['display_name'])]
            if labels:person_holds.append(dict(exhibitionID=e['exhibitionID'],artistID=link['artist_id'],reason='Existing unlinked same-name artist; reconcile instead of adding a duplicate.'));continue
            if key not in participants:participants[key]=dict(id=c.uid(OP+'/participant/'+key[0]+'/'+key[1]),exhibitionID=key[0],artistID=key[1],name=link['display_name'],sourceID=e['sourceID'],artworkIDs=[])
            participants[key]['artworkIDs'].append(e['artworkID'])
    p=dict(at=c.now(),operation=OP,sourcePins=pin,sourceReceipt=c.load(OUT/'source-receipt.json'),records=records,entries=entries,participants=list(participants.values()),
           beforeExisting=before,beforeActive=before_active,decisions=decisions,heldEntries=held,alreadyLinked=already,participantHolds=person_holds,
           scope='Selected NGA historical exhibition histories, exact current catalogue objects classified painting/drawing/print, explicit event years 1943–1988 and reviewed full ranges through 1989. Partial object-history reconstruction, not complete original checklists.',
           mainCatalogueWrites=False,newImages=0,realLocalDatabaseWrites=False)
    p['counts']=dict(newEvents=sum(r['new']for r in records),enrichedEvents=sum(not r['new']for r in records),newEntries=len(entries),
                     linkedWorks=len({e['artworkID']for e in entries}),illustratedConnections=sum(bool(e['before']['primary_media_id'])for e in entries),
                     newOccurrences=sum((1+len(r['extraOccurrences']))if r['new']else 0 for r in records),participants=len(participants),
                     sources=len(records)+len(entries),heldEntries=len(held),alreadyLinked=len(already),eventsWithEntries=len(records))
    c.save(OUT/'delivery-plan.json.gz',p);c.save(BACKUP/'preimage.json.gz',p)
    print(json.dumps(p['counts']),flush=True)


def apply():
    p=c.load(OUT/'delivery-plan.json.gz');assert p['sourcePins']==pins()
    assert c.load(BACKUP/'preimage.json.gz')==p
    plan_sha=c.sha((OUT/'delivery-plan.json.gz').read_bytes());receipt=p['sourceReceipt']
    expected={e['artworkID']:e['before']for e in p['entries']}
    existing=[r['id']for r in p['records']if not r['new']]
    base=dict(operation=OP,planSHA256=plan_sha,historyCSV_SHA256=receipt['sha256'],objectCSV_SHA256=p['sourcePins']['objectCSV'],
              catalogueMetadataPreserved=True,checklistComplete=False,holdingClaim=False,currentDisplayClaim=False,
              scope=p['scope'],metadataLicence='NGA published open metadata; no image licence inferred or new images downloaded.')
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        assert not db.execute('SELECT 1 FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()
        assert not db.execute('SELECT 1 FROM exhibitions WHERE import_batch=%s',(OP,)).fetchone()
        assert not db.execute('SELECT 1 FROM exhibition_research WHERE exhibition_id=ANY(%s::uuid[])',(existing,)).fetchone()
        for table in TABLES:
            now=normal(db.execute('SELECT * FROM '+table+' WHERE '+('id'if table=='exhibitions'else'exhibition_id')+'=ANY(%s::uuid[]) ORDER BY id'+(' FOR UPDATE'if table=='exhibitions'else''),(existing,)).fetchall())
            assert now==p['beforeExisting'][table],table
        now=normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[]) FOR SHARE',(list(expected),)).fetchall())
        assert {r['id']:r for r in now}==expected,'Main catalogue changed after identity audit; prepare a new reviewed plan.'
        pairs={(r['start_year'],c.norm(r['title']))for r in db.execute('SELECT start_year,title FROM exhibitions WHERE start_year BETWEEN 1943 AND 1988').fetchall()}
        assert not [r['root']for r in p['records']if r['new']and(r['year'],c.norm(r['title']))in pairs]
        assert db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']==p['beforeActive']
        with db.pipeline():
            for r in p['records']:
                if r['new']:
                    db.execute("INSERT INTO exhibitions(id,title,normalized_title,alternate_titles,start_year,end_year,date_display,date_precision,event_state,state_basis,format,checklist_state,status,import_batch) VALUES(%s,%s,%s,%s,%s,%s,%s,'year','held',%s,'physical','partial','review',%s)",
                               (r['id'],r['title'],c.norm(r['title']),Jsonb(r['aliases']),r['year'],r['endYear'],r['dateDisplay'],
                                'Official NGA object exhibition histories identify the historical exhibition and eligible exhibited works. Explicit source years retained; unknown exact dates and unestablished closing years remain unknown.',OP))
                else:
                    db.execute("UPDATE exhibitions SET checklist_state='partial',updated_at=now() WHERE id=%s AND checklist_state<>'complete'",(r['id'],))
                evidence=base|dict(group=r['root'],mergedSourceGroups=r['groups'],sourceTitleVariants=r['aliases'],
                                   dateReview='Explicit source year only; no January/December boundaries inferred. Full reviewed tour ranges retained; pre-existing dates preserved.',
                                   duplicateReview='Full existing event/title/venue audit plus reviewed source aliases; 13 existing identities reused, unresolved candidates held.',
                                   sourceDateRangeProof=r['dateEvidence'])
                example=next(e for e in p['entries']if e['exhibitionID']==r['id'])
                db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                           (r['sourceID'],r['id'],OP,'event/'+str(r['root']),URL,receipt['retrieved_at'],receipt['body_path'],receipt['sha256'],
                            Jsonb(dict(title=r['title'],year=r['year'],exampleHistories=example['histories'],rangeProof=r['dateEvidence'])),Jsonb(evidence)))
                if r['new']:
                    display=str(r['year'])if r['extraOccurrences']else r['dateDisplay']
                    db.execute('INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,institution_id,venue_label,city_label,country_label,country_code,date_display,evidence) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                               (r['occurrenceID'],r['id'],r['sourceID'],MID,'National Gallery of Art','Washington, D.C.','United States','US',display,Jsonb(evidence)))
                    for o in r['extraOccurrences']:
                        db.execute('INSERT INTO exhibition_occurrences(id,exhibition_id,source_record_id,venue_label,city_label,country_label,country_code,date_display,evidence) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                   (o['id'],r['id'],r['sourceID'],o['venue'],o['city'],o['country'],o['code'],r['dateDisplay']+' (tour; stop dates unknown)',
                                    Jsonb(evidence|dict(stopDatesUnknown=True,allObjectsAtEveryStopNotInferred=True,historicalVenueNamePreserved=True))))
            for e in p['entries']:
                o=e['object'];evidence=base|dict(nativeObjectID=e['objectID'],sourceHistoryRows=e['histories'],numberReview=e['numberReview'],
                    sourceNativeIDAndAccessionMatched=True,viewIdentityReviewed=True,limitedDisplayDuration=e['partialDuration'],
                    participationBasis='Native museum exhibition_history explicitly names only the NGA venue for this participation claim. No participation inferred at other stops.')
                db.execute('INSERT INTO exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                           (e['sourceID'],e['exhibitionID'],OP,'object/'+str(e['root'])+'/'+e['objectID'],URL,receipt['retrieved_at'],receipt['body_path'],receipt['sha256'],Jsonb(dict(object=o,histories=e['histories'])),Jsonb(evidence)))
                db.execute("INSERT INTO exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,catalogue_number,title_label,creator_label,date_label,medium_label,dimensions_label,participation,evidence,match_basis) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s)",
                           (e['id'],e['exhibitionID'],e['sourceID'],e['occurrenceID'],e['artworkID'],e['objectID'],e['catalogueNumber'],o['title'],o['attribution'],o['displaydate'],o['medium'],o['dimensions'],Jsonb(evidence),
                            'Exact NGA native object ID, accession and current institution agree with the existing catalogue. Original museum object exhibition history identifies the reviewed event and NGA venue; versions and explicit recto-only claims checked.'))
            for person in p['participants']:
                db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,%s,'artist',%s)",
                           (person['id'],person['exhibitionID'],person['sourceID'],person['artistID'],person['name'],Jsonb(base|dict(basis='Existing unqualified primary creators of exact exhibited works; historical attribution wording preserved in entry sources.',artworkIDs=person['artworkIDs']))))
            db.execute("INSERT INTO exhibition_source_coverage(id,institution_id,source_key,source_url,inspected_start_year,inspected_end_year,research_state,details) VALUES(%s,%s,%s,%s,1600,1989,'partial',%s)",
                       (c.uid(OP+'/coverage'),MID,OP,URL,Jsonb(base|dict(sourceHistoryRows=67656,reviewedSingleNGATitleGroups=217,counts=p['counts'],
                        remaining='Other venue histories, ranges and touring identities, 511 selected histories without unique existing objects, title/section/duplicate holds, original checklists, dates and missing images.'))))
    c.save(OUT/'delivered.json',dict(at=c.now(),counts=p['counts'],planSHA256=plan_sha,newArtworks=0,newArtists=0,newImages=0,realLocalDatabaseWrites=False))
    print('Committed',json.dumps(p['counts']),flush=True)


def verify():
    import requests
    from concurrent.futures import ThreadPoolExecutor
    p=c.load(OUT/'delivery-plan.json.gz');expected={e['artworkID']:e['before']for e in p['entries']}
    with c.connect()as db:
        rows=normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(list(expected),)).fetchall())
        assert {r['id']:r for r in rows}==expected
        entries=normal(db.execute('SELECT * FROM exhibition_entries WHERE id=ANY(%s::uuid[])',([e['id']for e in p['entries']],)).fetchall())
        assert {(e['id'],e['artwork_id'],e['occurrence_id'],e['participation'])for e in entries}=={(e['id'],e['artworkID'],e['occurrenceID'],'exhibited')for e in p['entries']}
        events=normal(db.execute('SELECT * FROM exhibitions WHERE id=ANY(%s::uuid[])',([r['id']for r in p['records']],)).fetchall());byid={r['id']:r for r in events}
        for r in p['records']:
            now=byid[r['id']];assert now['event_state']=='held'
            if r['new']:
                assert now['start_year']==r['year']and now['end_year']==r['endYear']and now['start_date']is None and now['end_date']is None and now['status']=='review'
            else:
                assert all(now[k]==v for k,v in r['before'].items()if k not in ['updated_at','checklist_state'])
        for table in TABLES[1:]:
            old=p['beforeExisting'][table]
            if old:
                now=normal(db.execute('SELECT * FROM '+table+' WHERE id=ANY(%s::uuid[]) ORDER BY id',([r['id']for r in old],)).fetchall())
                assert now==old,table
        people=normal(db.execute('SELECT * FROM exhibition_participants WHERE id=ANY(%s::uuid[])',([r['id']for r in p['participants']],)).fetchall())
        assert {(r['exhibition_id'],r['artist_id'])for r in people}=={(r['exhibitionID'],r['artistID'])for r in p['participants']}
        assert len(people)==p['counts']['participants']
        assert db.execute('SELECT count(*) n FROM exhibition_source_records WHERE source_key=%s',(OP,)).fetchone()['n']==p['counts']['sources']
        assert db.execute('SELECT count(*) n FROM exhibitions WHERE import_batch=%s',(OP,)).fetchone()['n']==p['counts']['newEvents']
        active=db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n'];assert active==p['beforeActive']+p['counts']['newEvents']
        totals=normal(db.execute("SELECT count(*) active,count(*) FILTER(WHERE event_state='held') held,count(*) FILTER(WHERE start_year IS NULL) undated,count(*) FILTER(WHERE start_year<1600 OR end_year>1989 OR start_date<'1600-01-01' OR end_date>='1990-01-01') outside FROM exhibitions WHERE status<>'archived'").fetchone())
        sample=max(p['records'],key=lambda r:len(r['entries']))
        query_plan=normal(db.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT * FROM exhibition_entries WHERE exhibition_id=%s ORDER BY id LIMIT 101',(sample['id'],)).fetchone())
    api='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions'
    wanted=collections.defaultdict(list)
    for e in p['entries']:wanted[e['exhibitionID']].append(e)
    def check(event):
        items=[];after='';pages=0
        while True:
            response=requests.get(api+'/'+event['id']+'/entries',params=dict(limit=100,after=after),timeout=40);response.raise_for_status();data=response.json()
            items+=data['items'];pages+=1;after=data.get('nextCursor')or''
            if not after:break
            assert pages<20
        by={r['id']:r for r in items};assert len(by)==len(items),'Duplicate keyset entry'
        for e in wanted[event['id']]:
            row=by[e['id']];assert row['artworkId']==e['artworkID']and row['participation']=='exhibited'
            assert bool(row.get('image'))==bool(e['before']['primary_media_id'])
        return dict(id=event['id'],root=event['root'],entries=len(wanted[event['id']]),illustrated=sum(bool(by[e['id']].get('image'))for e in wanted[event['id']]),pages=pages)
    with ThreadPoolExecutor(max_workers=3)as pool:
        checked=list(pool.map(check,p['records']))
    for entry in [p['entries'][0],p['entries'][-1]]:
        response=requests.get(api,params=dict(artwork=entry['artworkID'],limit=100),timeout=40);response.raise_for_status()
        assert entry['exhibitionID']in {r['id']for r in response.json()['items']}
    response=requests.get(api,params=dict(limit=1),timeout=40);response.raise_for_status();directory=response.json()
    assert directory['total']==active and directory['heldTotal']==totals['held']
    c.save(OUT/'verified.json',dict(at=c.now(),counts=p['counts'],totals=totals,queryPlan=query_plan,apiChecks=checked,allNewLinksAndImagePresenceVerified=True,
           reverseLinkSamples=2,mainArtworkRecordsPreserved=True,existingEventDatesAndChildrenPreserved=True,newArtworks=0,newArtists=0,newImages=0,
           imageGapConnections=p['counts']['newEntries']-p['counts']['illustratedConnections'],realLocalDatabaseWrites=False))
    print('Verified',json.dumps(totals),sum(r['entries']for r in checked),'links',sum(r['illustrated']for r in checked),'illustrated',flush=True)


def venue_links():
    """Resolve two historical venue names after the event delivery is verified."""
    import gzip
    from bs4 import BeautifulSoup
    specs=[(83,'Dallas Museum of Fine Arts','bb1d958a-8192-559f-ac6a-d05d783155db','https://publications.dma.org/node/100',
            'renamed the Dallas Museum of Art', 'Official museum publication documents the 1984 change from Dallas Museum of Fine Arts to Dallas Museum of Art.'),
           (15,'University of Iowa Museum of Art','09dede1f-3cf7-5e7b-870d-e2295a4bdb6c','https://stanleymuseum.uiowa.edu/about/history',
            '1969','Official university museum history identifies the same Iowa City institution established in 1969 and renamed Stanley in 2018.')]
    receipts={r['url']:r['receipt']for r in c.load(OUT/'venue-history-receipts-v2.json')['sources']if 'receipt'in r}
    links=[]
    with c.connect()as db:
        for root,venue,mid,url,expected_text,basis in specs:
            rc=receipts[url];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert c.sha(raw)==rc['sha256']
            text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True);assert expected_text in text
            oid=c.uid(OP+'/tour/'+str(root)+'/'+c.norm(venue))
            before=normal(db.execute('SELECT * FROM exhibition_occurrences WHERE id=%s',(oid,)).fetchone())
            institution=normal(db.execute('SELECT id,name FROM institutions WHERE id=%s',(mid,)).fetchone())
            assert before and before['institution_id']is None and before['venue_label']==venue and institution
            links.append(dict(id=oid,institutionID=mid,institution=institution,before=before,receipt=rc,basis=basis,confidence=0.98))
    p=dict(at=c.now(),links=links,note='Editorial identity confidence, not a calibrated probability. Original venue labels, dates and source participation retained.')
    c.save(OUT/'tour-museum-link-plan.json',p);c.save(BACKUP/'tour-museum-links-preimage.json',p)
    with c.connect(write=True)as db:
        db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(2026101201)')
        for link in links:
            before=normal(db.execute('SELECT * FROM exhibition_occurrences WHERE id=%s FOR UPDATE',(link['id'],)).fetchone());assert before==link['before']
            ev=before['evidence']|dict(institutionIdentityReview=dict(basis=link['basis'],editorialConfidence=link['confidence'],source=link['receipt'],historicalVenueLabelPreserved=True))
            db.execute('UPDATE exhibition_occurrences SET institution_id=%s,evidence=%s WHERE id=%s',(link['institutionID'],Jsonb(ev),link['id']))
    with c.connect()as db:
        for link in links:
            now=normal(db.execute('SELECT * FROM exhibition_occurrences WHERE id=%s',(link['id'],)).fetchone())
            assert now['institution_id']==link['institutionID']
            assert all(now[k]==v for k,v in link['before'].items()if k not in ['institution_id','evidence'])
            assert all(now['evidence'][k]==v for k,v in link['before']['evidence'].items())
    c.save(OUT/'tour-museum-links-verified.json',dict(at=c.now(),links=2,occurrenceIDs=[r['id']for r in links],sourceReceipts=[r['receipt']for r in links],mainCatalogueWrites=False,newParticipationClaims=0))
    print('Verified two historical venue links; labels and dates preserved.')


if __name__ == '__main__':
    if len(sys.argv)!=2 or sys.argv[1]not in ['review','plan','apply','verify','venue_links']:
        raise SystemExit('Use review, plan, apply, verify or venue_links')
    globals()[sys.argv[1]]()
