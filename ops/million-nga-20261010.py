#!/usr/bin/env python3
"""Pinned NGA physical-object selection and resumable production-only ingestion."""
import argparse,collections,csv,importlib.util,json,re,subprocess,time
from pathlib import Path
from psycopg import sql
s=importlib.util.spec_from_file_location('million',Path(__file__).with_name('million-catalogue-20261010.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s=importlib.util.spec_from_file_location('life',Path(__file__).with_name('lifetimes-plan-20261010.py'));life=importlib.util.module_from_spec(s);s.loader.exec_module(life)
RUN=m.RUN/'nga';MID='4a7cf367-a105-f2bf-dc1c-a2210974752e';SID=m.uid('source/nga');SCHEME='european-nga-object'
PLAN='plan-v2.json.gz';PIN='plan-v2-pin.json'
def read(name):
    p=m.DATA/'nga'/name;rc=m.load(m.RUN/'sources/nga'/(name+'.receipt.json'));assert m.sha(p.read_bytes())==rc['sha256']
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def dates(label):
    """Parse literal creation dates, never artist lifespan-derived search bounds."""
    t=label.strip().replace('–','-').replace('—','-')
    match=re.fullmatch(r'(?:(c\.?|ca\.?|circa|about)\s*)?(\d{3,4})(?:\s*[-/]\s*(\d{2,4}))?',t,re.I)
    if match:
        a=int(match[2]);b=int(match[3] or match[2])
        if match[3] and len(match[3])==2:b=a//100*100+b
        if 100<=a<=b<=1970:return (a,b,('circa' if a==b else 'circa_range') if match[1] else ('exact' if a==b else 'range'))
    match=re.fullmatch(r'(\d{3})0s',t)
    if match:
        a=int(match[1])*10
        if a+9<=1970:return a,a+9,'decade'
    match=re.fullmatch(r'(\d{1,2})(?:st|nd|rd|th) century',t)
    if match:
        a=(int(match[1])-1)*100+1;b=int(match[1])*100
        if 1<=a<=b<=1970:return a,b,'century'
    return None
def selection():
    if (RUN/'selection.json.gz').exists():return
    objects=read('objects.csv');people={r['constituentid']:r for r in read('constituents.csv')}
    inseparable={r['childobjectid'] for r in read('object_associations.csv') if r['relationship']=='inseparable'}
    creators=collections.defaultdict(list)
    for r in read('objects_constituents.csv'):
        if r['roletype']=='artist':creators[r['objectid']].append(r)
    images=collections.defaultdict(list)
    for r in read('published_images.csv'):
        if r['viewtype']=='primary' and r['openaccess']=='1':images[r['depictstmsobjectid']].append(r)
    types={'Painting':'painting','Drawing':'drawing','Print':'print','Photograph':'photograph','Sculpture':'sculpture','Index of American Design':'drawing'}
    selected=[];held=[]
    for r in objects:
        reason=None;d=dates(r['displaydate'])
        if r['accessioned']!='1':reason='not_accessioned'
        elif r['isvirtual']!='0':reason='virtual_cover_record'
        elif r['objectid'] in inseparable:reason='inseparable_child_view'
        elif r['classification'] not in types:reason='type_needs_separate_review'
        elif not d:reason='literal_date_requires_review_or_after_1970'
        elif not r['title'].strip() or not r['accessionnum'].strip():reason='identity_incomplete'
        if reason:held.append(dict(id=r['objectid'],reason=reason,date=r['displaydate']));continue
        cr=sorted(creators[r['objectid']],key=lambda x:int(x['displayorder']))
        row=dict(native_id=r['objectid'],title=r['title'],normalized_title=m.norm(r['title']),accession_number=r['accessionnum'],date_display=r['displaydate'],first=d[0],last=d[1],precision=d[2],work_type=types[r['classification']],medium=r['medium'],dimensions=r['dimensions'],creator_label=r['attribution'],creators=cr,source_url='https://www.nga.gov/collection/art-object-page.'+r['objectid']+'.html',wikidata_id=r['wikidataid'],images=images[r['objectid']],raw={k:v for k,v in r.items() if k not in ['provenancetext','inscription','markings']})
        selected.append(row)
    used={c['constituentid'] for r in selected for c in r['creators']}
    receipts={p.name:m.load(p) for p in (m.RUN/'sources/nga').glob('*.receipt.json')}
    result=dict(at=m.now(),selected=selected,people={k:people[k] for k in used},held=held,receipts=receipts,policy='Only accessioned nonvirtual physical fine-art objects; inseparable child views excluded. Literal dates wholly through 1970. Unparsed dates held separately. Native accession and source IDs retained. Metadata only; image URLs are candidates, not attachments.')
    m.save(RUN/'selection.json.gz',result)
    print(json.dumps(dict(selected=len(selected),held=collections.Counter(r['reason'] for r in held),types=collections.Counter(r['work_type'] for r in selected),creator_authorities=len(used))),flush=True)
def workkey(r):return 'nga/'+r['native_id']
def artkeys(r):return [(SCHEME,r['native_id']),('nga-object',r['native_id'])]+([('wikidata',r['wikidata_id'])] if r['wikidata_id'] else [])
def artist_plan(person,works,artists,byexternal,bynames,provider='nga',native_scheme='nga-constituent'):
    native=person['constituentid'];name=person['forwarddisplayname'].strip();lf=life.literal_life(person['displaydate']) or {}
    found=set(byexternal.get((native_scheme,native),set()));qid=person['wikidataid']
    qmatch=byexternal.get(('wikidata',qid),set()) if qid else set()
    if found and qmatch and found!=qmatch:return None,'conflicting_authority_ids',None
    if not found and qmatch:
        for aid in qmatch:
            ar=artists[aid]
            if m.norm(name) in ar['names'] and all(ar[k+'_year'] is None or ar[k+'_year']==v['year'] for k,v in lf.items()):found.add(aid)
        if not found:return None,'qid_name_or_lifetime_conflict',None
    names=bynames.get(m.norm(name),set())
    if not found and names:
        candidates={aid for aid in names if len(lf)==2 and all(artists[aid][k+'_year']==v['year'] for k,v in lf.items())}
        if len(candidates)==1:found=candidates
        else:return None,'existing_name_ambiguous',None
    if len(found)>1:return None,'multiple_artist_matches',None
    if found:
        aid=next(iter(found))
        if artists[aid]['status']=='archived':return None,'archived_artist',None
        return aid,'native_identity' if (native_scheme,native) in byexternal else 'authority_or_name_and_life',None
    if person['constituenttype']!='individual' or not name or re.search(r'unknown|anonymous|unidentified|school|workshop|^estate|^mrs\.|^mr\.',name,re.I):return None,'not_a_resolved_individual',None
    b=lf.get('birth');d=lf.get('death')
    death_match=re.search(r'(?:^|;)\s*died\s+((?:c\.\s*)?\d{3,4})$',person['displaydate'])
    if not d and death_match:d=life.date_token(death_match[1])
    if b and d and (d['year']<b['year'] or d['year']-b['year']>120):return None,'life_conflict',None
    if b and d and d['year']-b['year']<15:return None,'short_source_range_may_be_activity_requires_review',None
    # A source-backed artwork span is explicitly a plotting estimate, never a biography.
    first=min(r['first'] for r in works);last=max(r['last'] for r in works)
    if b and any(r['last']<b['year'] for r in works):return None,'work_precedes_birth',None
    if b and d:lo=b['year'];hi=d['year'];basis='life';label=b['display']+'–'+d['display']
    else:lo=min(first,b['year']) if b else first;hi=max(last,d['year']) if d else last;basis='estimated';label='Documented works '+str(first)+'–'+str(last)+'; lifespan incomplete'
    active=re.search(r'\bactive\s+(?:c\.\s*)?(\d{3,4})\s*[-/]\s*(?:c\.\s*)?(\d{3,4})$',person['displaydate'])
    if active and int(active[1])<=int(active[2]):lo=int(active[1]);hi=int(active[2]);basis='activity';label=person['displaydate']
    a=dict(id=m.uid('artist/'+provider+'/'+native),slug=provider+'-'+native+'-'+re.sub(r'[^a-z0-9]+','-',m.norm(name)).strip('-')[:130],display_name=name,sort_name=person['preferreddisplayname'] or name,normalized_name=m.norm(name),entity_type='anonymous_master' if name.startswith('Master of ') else 'person',birth_year=b['year'] if b else None,death_year=d['year'] if d else None,birth_display=b['display'] if b else None,death_display=d['display'] if d else None,birth_precision=b['precision'] if b else None,death_precision=d['precision'] if d else None,active_start_year=lo if basis=='activity' else None,active_end_year=hi if basis=='activity' else None,activity_display=label if basis=='activity' else None,timeline_start_year=lo,timeline_end_year=hi,timeline_display=label,timeline_basis=basis,status='review',created_by=m.ACTOR,updated_by=m.ACTOR)
    return a['id'],'new_native_authority',a
def plan():
    dest=RUN/PLAN
    if dest.exists():print('Existing immutable plan');return
    data=m.load(RUN/'selection.json.gz');rows=data['selected'];native_ids=[r['native_id'] for r in rows];qids=[r['wikidata_id'] for r in rows if r['wikidata_id']]
    with m.m.connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        artists={r['id']:r for r in db.execute('SELECT id::text,display_name,normalized_name,birth_year,death_year,status FROM artists')}
        byexternal=collections.defaultdict(set);bynames=collections.defaultdict(set)
        for aid,a in artists.items():a['names']={m.norm(a['display_name']),m.norm(a['normalized_name'])}
        for a in db.execute('SELECT artist_id::text,alias FROM artist_aliases'):artists[a['artist_id']]['names'].add(m.norm(a['alias']))
        for aid,a in artists.items():
            for n in a['names']:bynames[n].add(aid)
        for e in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artist'"):byexternal[(e['scheme'],e['external_id'])].add(e['entity_id'])
        existing=db.execute('SELECT id::text,title,normalized_title,accession_number,status FROM artworks WHERE current_institution_id=%s',(MID,)).fetchall()
        ext=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (scheme=ANY(%s) OR canonical_url LIKE 'https://www.nga.gov/%%' OR canonical_url LIKE 'http://www.nga.gov/%%')",([SCHEME,'nga-object'],)).fetchall()
        for ids in m.chunks(qids,3000):ext+=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s)",(ids,)).fetchall()
        qp=db.execute('EXPLAIN (FORMAT JSON) SELECT id FROM artworks WHERE current_institution_id=%s',(MID,)).fetchone()
    exkeys=collections.defaultdict(set);exacc=collections.defaultdict(set);extitles=collections.defaultdict(list)
    for e in ext:
        exkeys[(e['scheme'],e['external_id'])].add(e['entity_id'])
        match=re.search(r'art-object-page\.(\d+)\.html',e['canonical_url'] or '')
        if match:exkeys[(SCHEME,match[1])].add(e['entity_id'])
    for r in existing:
        if r['accession_number']:exacc[m.norm(r['accession_number'])].add(r['id'])
        extitles[m.norm(r['title'])].append(r)
    new=[];skips=[];seen=set();qid_counts=collections.Counter(r['wikidata_id'] for r in rows if r['wikidata_id'])
    for r in rows:
        if r['wikidata_id'] and qid_counts[r['wikidata_id']]>1:skips.append(dict(native_id=r['native_id'],reason='export_qid_covers_multiple_native_objects'));continue
        if r['last']==1970 and 'circa' in r['precision']:skips.append(dict(native_id=r['native_id'],reason='circa_cutoff_needs_review'));continue
        matches=set().union(*(exkeys.get(k,set()) for k in artkeys(r)),exacc.get(m.norm(r['accession_number']),set()))
        if matches:skips.append(dict(native_id=r['native_id'],reason='existing_identity' if len(matches)==1 else 'existing_identity_conflict',ids=sorted(matches)));continue
        # Unknown-inventory same-title museum entries need version review, not another row.
        if any(not e['accession_number'] for e in extitles.get(r['normalized_title'],[])):skips.append(dict(native_id=r['native_id'],reason='same_title_unknown_inventory'));continue
        acc=m.norm(r['accession_number'])
        if acc in seen:skips.append(dict(native_id=r['native_id'],reason='same_export_inventory'));continue
        seen.add(acc);r.update(artwork_id=m.uid('artwork/'+workkey(r)),links=[]);new.append(r)
    usable_roles={'artist','painter','sculptor','engraver','etcher','photographer','designer','medalist','ceramist'}
    candidates=collections.defaultdict(list)
    for r in new:
        for c in r['creators']:
            if c['role'] in usable_roles and c['prefix'] in ('','and',',','Attributed to') and not c['suffix']:candidates[c['constituentid']].append(r)
    amap={};newartists=[];artistdecisions=[]
    for native,works in candidates.items():
        person=data['people'][native];aid,reason,a=artist_plan(person,works,artists,byexternal,bynames);amap[native]=aid;artistdecisions.append(dict(native_id=native,artist_id=aid,reason=reason,authority=person))
        if a:
            newartists.append(a);artists[aid]=dict(a,names={m.norm(person['forwarddisplayname'])});bynames[a['normalized_name']].add(aid);byexternal[('nga-constituent',native)].add(aid)
            if person['wikidataid']:byexternal[('wikidata',person['wikidataid'])].add(aid)
    for r in new:
        for c in r['creators']:
            aid=amap.get(c['constituentid'])
            if aid and c['role'] in usable_roles and c['prefix'] in ('','and',',','Attributed to') and not c['suffix']:
                role='attributed_to' if c['prefix']=='Attributed to' else 'primary'
                if not any(x['artist_id']==aid and x['attribution_role']==role for x in r['links']):r['links'].append(dict(artwork_id=r['artwork_id'],artist_id=aid,attribution_role=role,representative_order=min(10,len(r['links'])+1),attribution_note='NGA native creator '+c['constituentid']+'; source role: '+c['role']+'; '+c['prefix']+' '+data['people'][c['constituentid']]['forwarddisplayname']))
    for a in artists.values():a.pop('names',None)
    p=dict(at=m.now(),selection_sha256=m.sha((RUN/'selection.json.gz').read_bytes()),new_artworks=new,new_artists=newartists,artist_decisions=artistdecisions,skipped=skips,query_plan=qp,source_receipts=data['receipts'],existing_artist_preconditions={aid:artists[aid] for aid in {l['artist_id'] for r in new for l in r['links']} if aid not in {a['id'] for a in newartists}})
    m.save(dest,p);m.save(RUN/PIN,dict(sha256=m.sha(dest.read_bytes())));m.save(m.BACKUP/'nga'/PLAN,p)
    print(json.dumps(dict(new_artworks=len(new),new_artists=len(newartists),creator_links=sum(len(r['links']) for r in new),images_available=sum(bool(r['images']) for r in new),skipped=collections.Counter(r['reason'] for r in skips),artist_decisions=collections.Counter(r['reason'] for r in artistdecisions))),flush=True)
def copy_rows(db,table,rows):
    if not rows:return
    keys=list(rows[0]);assert all(list(r)==keys for r in rows)
    query=sql.SQL('COPY {} ({}) FROM STDIN').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,keys)))
    with db.cursor().copy(query) as out:
        for r in rows:out.write_row([r[k] for k in keys])
def backup():
    rows=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--limit=30','--format=json'],text=True))
    r=next(r for r in rows if r.get('description')=='Before million catalogue source expansion 20261010');assert r['status']=='SUCCESSFUL',r['status']
    m.save(m.RUN/'cloud-sql-backup.json',r);m.save(m.BACKUP/'cloud-sql-backup.json',r);print('Verified backup',r['id'],flush=True)
def apply(limit=None):
    path=RUN/PLAN;digest=m.load(RUN/PIN)['sha256'];assert digest==m.sha(path.read_bytes());p=m.load(path)
    assert m.load(m.RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL';rc=p['source_receipts']['objects.csv.receipt.json'];artists={r['id']:r for r in p['new_artists']};decisions={r['artist_id']:r for r in p['artist_decisions'] if r['reason']=='new_native_authority'}
    for number,rows in enumerate(m.chunks(p['new_artworks'],1000)):
        if limit is not None and number>=limit:break
        receiptpath=RUN/'batches'/(str(number).zfill(4)+'.json')
        if receiptpath.exists():continue
        ids=[r['artwork_id'] for r in rows];artistids=sorted({l['artist_id'] for r in rows for l in r['links']});tables=collections.defaultdict(list)
        with m.m.connect(write=True) as db:
            db.execute("SET LOCAL lock_timeout='120s'")
            db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
            done=db.execute('SELECT id::text FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
            if done:
                assert len(done)==len(ids),'Partial batch identity collision'
                assert db.execute("SELECT count(*) n FROM citations WHERE entity_id=ANY(%s::uuid[]) AND field_name='million_catalogue_nga' AND evidence_note::jsonb->>'plan_sha256'=%s",(ids,digest)).fetchone()['n']==len(ids)
                m.save(receiptpath,dict(at=m.now(),recovered_committed_batch=True,number=number,artworks=len(ids),plan_sha256=digest,artwork_ids=ids));continue
            assert db.execute('SELECT count(*) n FROM institutions WHERE id=%s AND status<>%s AND canonical_institution_id IS NULL',(MID,'archived')).fetchone()['n']==1
            actualartists={a['id']:a for a in db.execute('SELECT id::text,display_name,normalized_name,birth_year,death_year,status FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',(artistids,))}
            for aid,a in actualartists.items():
                if aid in p['existing_artist_preconditions']:assert a==p['existing_artist_preconditions'][aid],'Artist changed since plan'
            # Concurrent source identity and accession recheck within the serialized import.
            native=[r['native_id'] for r in rows];qids=[r['wikidata_id'] for r in rows if r['wikidata_id']]
            conflicts=db.execute("SELECT scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND ((scheme=ANY(%s) AND external_id=ANY(%s)) OR (scheme='wikidata' AND external_id=ANY(%s)))",([SCHEME,'nga-object'],native,qids)).fetchall();assert not conflicts,conflicts[:3]
            conflictacc=db.execute('SELECT id FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s)',(MID,[r['accession_number'] for r in rows])).fetchall();assert not conflictacc,'Concurrent accession duplicate'
            newa=[artists[aid] for aid in artistids if aid in artists and aid not in actualartists]
            m.save(m.BACKUP/'nga'/('batch-'+str(number).zfill(4)+'-before.json.gz'),dict(plan_sha256=digest,artwork_ids_absent=ids,artist_preconditions=actualartists,new_artist_ids=[a['id'] for a in newa]))
            db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,api_docs_url,terms_url,adapter_key) VALUES(%s,%s,%s,'museum_api',%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",(SID,m.OP+'-nga','National Gallery of Art official open data','https://www.nga.gov/','https://github.com/NationalGalleryOfArt/opendata','https://github.com/NationalGalleryOfArt/opendata/blob/main/LICENSE',m.OP))
            copy_rows(db,'artists',newa)
            for a in newa:
                d=decisions[a['id']];person=d['authority'];nid=person['constituentid'];url='https://www.nga.gov/artists/'+nid
                tables['external_identifiers'].append(dict(id=m.uid('identifier/nga-artist/'+nid),entity_type='artist',entity_id=a['id'],scheme='nga-constituent',external_id=nid,canonical_url=url,source_id=SID,retrieved_at=rc['retrieved_at']))
                if person['wikidataid']:tables['external_identifiers'].append(dict(id=m.uid('identifier/nga-artist-qid/'+nid),entity_type='artist',entity_id=a['id'],scheme='wikidata',external_id=person['wikidataid'],canonical_url='https://www.wikidata.org/wiki/'+person['wikidataid'],source_id=SID,retrieved_at=rc['retrieved_at']))
                tables['citations'].append(dict(id=m.uid('citation/nga-artist/'+nid),entity_type='artist',entity_id=a['id'],field_name='million_catalogue_nga_artist',source_id=SID,source_record_id=nid,source_url='https://github.com/NationalGalleryOfArt/opendata/blob/main/data/constituents.csv',evidence_note=json.dumps(dict(authority=person,plan_sha256=digest,life_policy='Literal displaydate only; numeric search bounds never promoted to life. Incomplete lives use explicitly estimated artwork span.'),ensure_ascii=False),retrieved_at=rc['retrieved_at'],created_by=m.ACTOR))
            for r in rows:
                aid=r['artwork_id'];key=workkey(r)
                tables['artworks'].append(dict(id=aid,slug='nga-object-'+r['native_id'],title=r['title'],normalized_title=r['normalized_title'],date_display=r['date_display'],creation_year_start=r['first'],creation_year_end=r['last'],date_precision=r['precision'],work_type=r['work_type'],medium_text=r['medium'] or None,dimensions_text=r['dimensions'] or None,accession_number=r['accession_number'],current_institution_id=MID,status='review',research_candidate=True,unlinked_creator_label=r['creator_label'] or None,created_by=m.ACTOR,updated_by=m.ACTOR))
                tables['artwork_artists']+=r['links']
                tables['external_identifiers'].append(dict(id=m.uid('identifier/'+key),entity_type='artwork',entity_id=aid,scheme=SCHEME,external_id=r['native_id'],canonical_url=r['source_url'],source_id=SID,retrieved_at=rc['retrieved_at']))
                if r['wikidata_id']:tables['external_identifiers'].append(dict(id=m.uid('identifier/qid/'+key),entity_type='artwork',entity_id=aid,scheme='wikidata',external_id=r['wikidata_id'],canonical_url='https://www.wikidata.org/wiki/'+r['wikidata_id'],source_id=SID,retrieved_at=rc['retrieved_at']))
                note=dict(plan_sha256=digest,source_sha256=rc['sha256'],native_object=r['raw'],native_creators=r['creators'],identity='Native object ID + accession; source physical object, not virtual cover or inseparable view',date_basis='Literal creation date parsed; no artist-life fallback',scope='Museum collection holding, no current display claim',metadata_license='CC0; image rights assessed separately')
                tables['citations'].append(dict(id=m.uid('citation/'+key),entity_type='artwork',entity_id=aid,field_name='million_catalogue_nga',source_id=SID,source_record_id=r['native_id'],source_url=r['source_url'],evidence_note=json.dumps(note,ensure_ascii=False),retrieved_at=rc['retrieved_at'],created_by=m.ACTOR))
                tables['artwork_location_assertions'].append(dict(id=m.uid('holding/'+key),artwork_id=aid,claim_type='holding',institution_id=MID,context='collection',source_id=SID,source_url=r['source_url'],evidence_note='Official NGA accessioned collection object '+r['native_id']+', inventory '+r['accession_number']+'. Source SHA256 '+rc['sha256']+'. Editorial confidence: high (direct native object evidence); no current display claim.',checked_at=rc['retrieved_at'],review_state='accepted'))
            for table in ['artworks','artwork_artists','external_identifiers','citations','artwork_location_assertions']:copy_rows(db,table,tables[table])
            check=db.execute("SELECT count(*) n,count(*) FILTER(WHERE status='review' AND published_at IS NULL AND primary_media_id IS NULL AND current_institution_id=%s AND creation_year_end<=1970) valid FROM artworks WHERE id=ANY(%s::uuid[])",(MID,ids)).fetchone();assert check['n']==check['valid']==len(ids)
            db.commit()
        receipt=dict(at=m.now(),number=number,artworks=len(rows),artists=len(newa),creator_links=len(tables['artwork_artists']),plan_sha256=digest,artwork_ids=ids,local_database_changes=0)
        m.save(receiptpath,receipt);print(json.dumps({k:v for k,v in receipt.items() if k!='artwork_ids'}),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['selection','plan','backup','apply']);ap.add_argument('--limit',type=int);a=ap.parse_args()
    apply(a.limit) if a.action=='apply' else globals()[a.action]()
