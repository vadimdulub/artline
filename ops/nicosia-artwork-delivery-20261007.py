#!/usr/bin/env python3
"""Production-only Nicosia catalogue delivery with pinned identities/preimages."""
import argparse,collections,difflib,functools,gzip,importlib.util,json,re
from pathlib import Path
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('nicosia',Path(__file__).with_name('nicosia-museums-20261007.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
h,d,R,B=n.h,n.d,n.ROOT,n.BACKUP
loc=n.module('nicosia_location_snapshots','apply-artwork-locations-20261004.py')
QUALIFIED=re.compile(r'\b(?:attributed|attribue|workshop|atelier|school|ecole|after|manner|copy|copies|unknown|anonymous|unidentified)\b')

def key(f):return f['scheme']+'/'+f['source_id']
@functools.lru_cache(maxsize=50000)
def title_keys(value):return {n.norm(t)for t in [value,*value.split(' / ')]if t}
def creator_names(value):
    # Parentheses can contain given names, e.g. Bordone (Benedetto).
    # Remove explicit life dates only, never all parenthesized text.
    clean=re.sub(r'\(\s*\d{4}\s*[-–]\s*\d{4}\s*\)','',value or'').strip(' []')
    names={n.norm(clean)}
    if ','in clean:
        surname,given=clean.split(',',1);names.add(n.norm(given+' '+surname))
    return names-{''}
@functools.lru_cache(maxsize=50000)
def creator_key(value):return ' '.join(sorted(next(iter(creator_names(value)),'').split()))
@functools.lru_cache(maxsize=50000)
def qualified(value):return bool(QUALIFIED.search(n.norm(value)))
def urls(value):
    if not value:return set()
    return {prefix+value.split('://',1)[-1].rstrip('/')+suffix for prefix in ['http://','https://']for suffix in ['','/']}
def source_records(f):return [f,*f.get('alternate_sources',[])]
@functools.lru_cache(maxsize=50000)
def inventory(value):return re.sub(r'[^\w]','',n.norm(value or'')).replace('β','b')
def creator_keys(snap):
    return {creator_key(x)for x in [snap['artwork'].get('unlinked_creator_label')or'',*[x['name']for x in snap['creator_keys']]]if x}
def creator_same(f,snap,artist_id=None):
    if artist_id and artist_id in {x['artist_id']for x in snap['creators']}:return True
    label=creator_key(f['creator_label'])
    return bool(len(label.split())>=2 and not qualified(f['creator_label'])and label in creator_keys(snap))
def overlap(f,w):
    vals=[f['first'],f['last'],w['creation_year_start'],w['creation_year_end']]
    return all(x is not None for x in vals)and max(vals[0],vals[2])<=min(vals[1],vals[3])
def dimension_key(value):return re.sub(r'[^a-z0-9.]','',(value or'').lower().replace(',','.').replace('×','x'))

def inputs():
    p=n.load(R/'artwork-candidates.json.gz');assert len(p['records'])==620
    for f in p['records']:
        for src in source_records(f):
            rc=src['receipt'];assert rc['status']==200
            assert h.sha(gzip.decompress((n.REPO/rc['body_path']).read_bytes()))==rc['sha256']
        assert f['precision']=='unknown'and f['first']is None and f['last']is None or f['last']is not None and f['last']<=1970
    return p['records']

def artists(db,facts):
    names=sorted(set().union(*(creator_names(f['creator_label'])for f in facts)))
    rows=db.execute("""SELECT to_jsonb(a)artist,
      coalesce((SELECT jsonb_agg(alias ORDER BY alias)FROM artist_aliases WHERE artist_id=a.id),'[]')aliases
      FROM artists a WHERE a.status<>'archived' AND(a.normalized_name=ANY(%s)OR a.id IN
      (SELECT artist_id FROM artist_aliases WHERE normalized_alias=ANY(%s)))ORDER BY a.id""",(names,names)).fetchall()
    index=collections.defaultdict(set)
    for row in rows:
        for label in [row['artist']['display_name'],*row['aliases']]:index[creator_key(label)].add(row['artist']['id'])
    assignments={};conflicts=[]
    byid={x['artist']['id']:x['artist']for x in rows}
    for f in facts:
        ids=index[creator_key(f['creator_label'])];pid=None
        if len(ids)==1 and len(creator_key(f['creator_label']).split())>=2 and not qualified(f['creator_label']):
            pid=next(iter(ids));life=re.search(r'\((\d{4})\s*[-–]\s*(\d{4})\)',f['creator_label']or'')
            if life and any(byid[pid][field]and byid[pid][field]!=int(life[i])for field,i in [('birth_year',1),('death_year',2)]):pid=None
            if pid and ((f['first']is not None and byid[pid]['death_year']is not None and f['first']>byid[pid]['death_year'])or(f['last']is not None and byid[pid]['birth_year']is not None and f['last']<byid[pid]['birth_year'])):pid=None
        if ids and pid is None:conflicts.append(dict(source=key(f),creator=f['creator_label'],artist_ids=sorted(ids),reason='Qualified, incomplete, ambiguous or chronologically incompatible creator label; object label retained.'))
        if len(ids)>1:conflicts.append(dict(source=key(f),creator=f['creator_label'],artist_ids=sorted(ids)))
        assignments[key(f)]=pid
    return rows,assignments,conflicts

def identity_state(db,facts,artist_ids,museum_ids,explain=False):
    title_values=sorted(set().union(*(title_keys(f['title'])for f in facts)))
    queries={
      'titles':('SELECT id::text FROM artworks WHERE normalized_title=ANY(%s)ORDER BY id',(title_values,)),
      'museums':('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[])',(museum_ids,museum_ids)),
      'painters':('SELECT DISTINCT artwork_id::text id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])ORDER BY artwork_id::text LIMIT 20001',(artist_ids,))}
    groups={};plans={}
    for label,(query,params)in queries.items():
        if explain:plans[label]=db.execute('EXPLAIN(FORMAT JSON) '+query,params).fetchone()
        groups[label]=sorted(x['id']for x in db.execute(query,params))
    assert len(groups['painters'])<=20000,'Painter-scoped identity page requires narrower selection'
    native=collections.defaultdict(set);object_urls=collections.defaultdict(set);shared_urls=collections.defaultdict(set)
    for f in facts:
        for src in source_records(f):
            native[(src['scheme'],src['source_id'])].add(key(f))
            for url in urls(src['source_url']):
                if src.get('shared_source_url'):shared_urls[(url,src['source_id'])].add(key(f))
                else:object_urls[url].add(key(f))
    schemes=sorted({scheme for scheme,_ in native});external_ids=sorted({identifier for _,identifier in native})
    matches=[]
    for row in db.execute("SELECT entity_id::text id,scheme,external_id FROM external_identifiers WHERE entity_type='artwork'AND scheme=ANY(%s)AND external_id=ANY(%s)",(schemes,external_ids)):
        for k in native.get((row['scheme'],row['external_id']),[]):matches.append(dict(candidate=k,id=row['id'],basis='native_scheme_and_identifier'))
    all_urls=sorted(set(object_urls)|{u for u,_ in shared_urls})
    query="""SELECT entity_id::text id,source_url url,source_record_id native_id,'citation'origin FROM citations WHERE entity_type='artwork'AND source_url=ANY(%s)
      UNION SELECT entity_id::text,canonical_url,external_id,'identifier' FROM external_identifiers WHERE entity_type='artwork'AND canonical_url=ANY(%s)"""
    for row in db.execute(query,(all_urls,all_urls)):
        selected=object_urls.get(row['url'],set())|shared_urls.get((row['url'],row['native_id']),set())
        for k in selected:matches.append(dict(candidate=k,id=row['id'],basis='object_source_url_or_shared_url_with_object_identifier'))
    matches=sorted({json.dumps(x,sort_keys=True):x for x in matches}.values(),key=lambda x:(x['candidate'],x['id'],x['basis']))
    ids=sorted(set().union(*(set(x)for x in groups.values()),{x['id']for x in matches}))
    return dict(groups=groups,matches=matches,ids=ids),plans

def make_plan():
    facts=inputs();assert not(R/'artwork-plan.json.gz').exists()
    with d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        institutions={x['v']['slug']:x['v']for x in db.execute('SELECT to_jsonb(i)v FROM institutions i WHERE slug=ANY(%s)ORDER BY id',([x[0]for x in n.REGISTRY],))};assert len(institutions)==55
        ars,assignments,creator_conflicts=artists(db,facts);aids=sorted(x['artist']['id']for x in ars);mids=sorted(i['id']for i in institutions.values())
        state,plans=identity_state(db,facts,aids,mids,True);snaps={}
        for part in d.chunks(state['ids'],250):snaps.update(loc.snapshots(db,part))
    n.save(R/'artwork-identity-query-plans.json',plans)
    bysource=collections.defaultdict(set)
    for x in state['matches']:bysource[x['candidate']].add(x['id'])
    ready=[];held=[];editorial=n.load(R/'editorial-identity-resolutions.json')
    for f in facts:
        museum=institutions[f['museum_slug']];pid=assignments[key(f)];exact=set(bysource[key(f)]);basis='Exact native object evidence'
        if f['accession']:
            for aid,snap in snaps.items():
                w=snap['artwork'];related={w['current_institution_id'],*[x['institution_id']for x in snap['assertions']]}
                if museum['id']in related and inventory(w['accession_number'])==inventory(f['accession']):exact.add(aid);basis='Exact museum inventory and source object metadata'
        if len(exact)>1:held.append(dict(facts=f,reason='multiple_existing_native_or_inventory_identities',ids=sorted(exact)));continue
        if not exact:
            potential=[];strong=[]
            for aid,snap in snaps.items():
                w=snap['artwork'];old_titles=title_keys(w['title'])|title_keys(w['alternate_title']or'');same_title=bool(title_keys(f['title'])&old_titles)
                same_creator=creator_same(f,snap,pid);same_museum=w['current_institution_id']==museum['id']
                same_dims=bool(f['dimensions']and w['dimensions_text']and dimension_key(f['dimensions'])==dimension_key(w['dimensions_text']))
                if same_title and(same_creator or same_museum or same_dims):
                    different_inventory=f['accession']and w['accession_number']and inventory(f['accession'])!=inventory(w['accession_number'])
                    if different_inventory and same_museum:continue
                    potential.append(aid)
                    narrow=overlap(f,w)and f['last']-f['first']<=5 and w['creation_year_end']-w['creation_year_start']<=5
                    type_ok=f['work_type']=='unknown'or w['work_type']=='unknown'or f['work_type']==w['work_type']
                    if same_creator and type_ok and not different_inventory and(same_dims or narrow):strong.append(aid)
                elif same_creator and any(difflib.SequenceMatcher(None,t,old).ratio()>=.88 for t in title_keys(f['title'])for old in old_titles if min(len(t),len(old))>=10):potential.append(aid)
            if len(set(strong))==1 and set(potential)==set(strong):exact.update(strong);basis='Unique full creator and exact title/translation, with matching physical dimensions or narrow creation dates'
            elif potential:
                resolution=editorial.get(key(f))
                if resolution and resolution['decision']=='distinct_object'and sorted(set(potential))==sorted(resolution['compared_artwork_ids']):
                    basis=resolution['basis']
                else:held.append(dict(facts=f,reason='possible_existing_object_requires_reconciliation',ids=sorted(set(potential))));continue
        before=snaps[next(iter(exact))]if exact else None
        if before:
            w=before['artwork'];holdings=[x for x in before['assertions']if x['claim_type']=='holding'and x['review_state']=='accepted'and not x['superseded_by']]
            if w['status']=='archived':held.append(dict(facts=f,reason='existing_archived_record',ids=[w['id']]));continue
            if w['current_institution_id']not in [None,museum['id']]or any(x['institution_id']!=museum['id']for x in holdings):held.append(dict(facts=f,reason='conflicting_existing_holding',ids=[w['id']]));continue
            if pid and before['creators']and not creator_same(f,before,pid):held.append(dict(facts=f,reason='existing_creator_conflict',ids=[w['id']]));continue
            aid=w['id'];action='evidence'if holdings else'link';pid=None # preserve all existing creator metadata
        else:aid=n.uid('artwork/'+key(f));action='create'
        holding_url=f['source_url'];holding_anchor=None
        if not holding_url.startswith('https://'):
            # The location table accepts HTTPS reference anchors only.
            # Preserve actual HTTP object URL in its citation and evidence;
            # use the independently captured HTTPS institution identity page
            # as the holding assertion's reference anchor, without rewriting
            # or claiming an HTTPS fetch of the native object page.
            holding_anchor=next(x['source']for x in n.load(R/'institution-plan.json.gz')['records']if x['institution']['id']==museum['id'])
            holding_url=holding_anchor['url'];assert holding_url.startswith('https://')
        row=dict(facts=f,artwork_id=aid,action=action,artist_id=pid,before=before,museum=museum,
            slug=R.name+'-'+h.sha(key(f).encode())[:24],identity_basis=basis,editorial_confidence=min(.96 if not before or bysource[key(f)]else .9,editorial.get(key(f),{}).get('editorial_confidence',.96)),
            holding_source_url=holding_url,holding_reference_anchor=holding_anchor)
        ready.append(row)
    collisions=collections.defaultdict(list)
    for row in ready:collisions[row['artwork_id']].append(row)
    kept=[]
    for rows in collisions.values():
        if len(rows)>1:
            for row in rows:held.append(dict(facts=row['facts'],reason='multiple_candidates_resolve_to_same_existing_object',ids=[row['artwork_id']]))
        else:kept.extend(rows)
    plan=dict(at=n.now(),target='production',records=kept,held=held,artists=ars,creator_conflicts=creator_conflicts,institutions=institutions,identity_state=state,identity_snapshots=snaps,
        candidate_sha256=h.sha((R/'artwork-candidates.json.gz').read_bytes()),editorial_resolutions_sha256=h.sha((R/'editorial-identity-resolutions.json').read_bytes()),policy='Source-backed holdings; new records in review; unknown dates stay unknown; existing metadata, images, creator links and publication states preserved; no display claim.')
    n.save(R/'artwork-plan.json.gz',plan);n.save(B/'artwork-plan-preimages.json.gz',plan)
    print('PLAN',dict(collections.Counter(x['action']for x in kept)),'HELD',dict(collections.Counter(x['reason']for x in held)),flush=True)

def apply():
    p=n.load(R/'artwork-plan.json.gz');digest=h.sha((R/'artwork-plan.json.gz').read_bytes());assert not(R/'artworks-applied.json').exists()
    backup=n.load(R/'production-backup.json')['production'];assert backup['status']=='SUCCESSFUL'and backup['instance']=='artline-postgres'
    facts=inputs();assert h.sha((R/'artwork-candidates.json.gz').read_bytes())==p['candidate_sha256']
    assert h.sha((R/'editorial-identity-resolutions.json').read_bytes())==p['editorial_resolutions_sha256']
    records=p['records'];ids=[x['artwork_id']for x in records];sid=n.uid('artwork-source');existing_ids=[x['artwork_id']for x in records if x['before']]
    with d.connect(readonly=False)as db,db.transaction():
        assert db.execute('SELECT current_database()name').fetchone()['name']=='artline'
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',(R.name,))
        mids=sorted(x['id']for x in p['institutions'].values());aids=sorted(x['artist']['id']for x in p['artists'])
        actual={x['v']['slug']:x['v']for x in db.execute('SELECT to_jsonb(i)v FROM institutions i WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',(mids,))};assert actual==p['institutions'],'Museum versions changed'
        ars,_,_=artists(db,facts);assert ars==p['artists'],'Painter identities changed'
        state,_=identity_state(db,facts,aids,mids);assert state==p['identity_state'],'Object identity candidates changed'
        locked=db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',(p['identity_state']['ids'],)).fetchall();assert len(locked)==len(p['identity_state']['ids'])
        current={}
        for part in d.chunks(p['identity_state']['ids'],250):current.update(loc.snapshots(db,part))
        assert current==p['identity_snapshots'],'Object versions, source identities, creators, media or locations changed'
        newids=[x['artwork_id']for x in records if not x['before']]
        assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[])OR slug=ANY(%s)',(newids,[x['slug']for x in records if not x['before']])).fetchone()
        n.save(B/'artwork-transaction-preimages.json.gz',dict(at=n.now(),plan_sha256=digest,existing_artworks={i:current[i]for i in existing_ids},absent_ids=newids))
        h.insert(db,'sources',dict(id=sid,slug=R.name+'-artworks',name='Nicosia museums: selected primary object records and documentary catalogue evidence',source_type='authority_data'))
        for row in records:
            f=row['facts'];aid=row['artwork_id'];pid=row['artist_id']
            if row['action']=='create':
                h.insert(db,'artworks',dict(id=aid,slug=row['slug'],title=f['title'],normalized_title=n.norm(f['title']),date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['precision'],
                    work_type=f['work_type'],medium_text=f['medium'],dimensions_text=f['dimensions'],accession_number=f['accession'],status='review',research_candidate=True,unlinked_creator_label=None if pid else f['creator_label'],created_by=h.ACTOR,updated_by=h.ACTOR))
                if pid:h.insert(db,'artwork_artists',dict(artwork_id=aid,artist_id=pid,attribution_role='primary',representative_order=1,attribution_note='Verified exact museum creator label/alias: '+f['creator_label']+'. Original label retained in source citation.'))
            for index,src in enumerate(source_records(f)):
                # A source can publish duplicate pages for the same object;
                # retain the primary external ID and all secondary native IDs
                # as citations (one external ID per entity/scheme DB invariant).
                if index==0:
                    prior=db.execute("SELECT entity_id::text id FROM external_identifiers WHERE entity_type='artwork'AND scheme=%s AND external_id=%s",(src['scheme'],src['source_id'])).fetchall()
                    if prior:assert len(prior)==1 and prior[0]['id']==aid
                    else:
                        existing_scheme=db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork'AND entity_id=%s AND scheme=%s",(aid,src['scheme'])).fetchall()
                        if not existing_scheme:h.insert(db,'external_identifiers',dict(id=n.uid('identifier/'+key(src)),entity_type='artwork',entity_id=aid,scheme=src['scheme'],external_id=src['source_id'],canonical_url=src['source_url'],source_id=sid,retrieved_at=src['receipt']['retrieved_at']))
                evidence=dict(facts=src,plan_sha256=digest,identity_basis=row['identity_basis'],editorial_confidence=row['editorial_confidence'],holding_reference_anchor=row['holding_reference_anchor'],policy=p['policy'])
                h.insert(db,'citations',dict(id=n.uid('object-citation/'+key(src)),entity_type='artwork',entity_id=aid,field_name='nicosia_primary_object_metadata_and_holding',source_id=sid,source_record_id=src['source_id'],source_url=src['source_url'],page_or_locator='Catalogue '+str(src['raw_fields'].get('catalogue_number'))+', page '+str(src['raw_fields'].get('pdf_page'))if src['raw_fields'].get('pdf_page')else src.get('accession'),evidence_note=json.dumps(evidence,ensure_ascii=False),retrieved_at=src['receipt']['retrieved_at'],created_by=h.ACTOR))
            if row['action']in ['create','link']:
                assert not db.execute("SELECT 1 FROM artwork_location_assertions WHERE artwork_id=%s AND claim_type='holding'AND review_state='accepted'AND superseded_by IS NULL",(aid,)).fetchone()
                note=f['holding_note']+' Actual object source: '+f['source_url']+'. Source SHA-256 '+f['receipt']['sha256']+'. Editorial confidence '+str(row['editorial_confidence'])+' (assessment, not calibrated probability). '+f['remaining_uncertainty']
                if row['holding_reference_anchor']:note+=' HTTPS reference anchor identifies the institution; the separately cited HTTP native object record establishes this object holding. No HTTPS fetch of the object URL is claimed.'
                h.insert(db,'artwork_location_assertions',dict(id=n.uid('artwork-holding/'+aid),artwork_id=aid,claim_type='holding',institution_id=row['museum']['id'],context='collection',source_id=sid,source_url=row['holding_source_url'],evidence_note=note,checked_at=f['receipt']['retrieved_at'],review_state='accepted'))
        after=loc.snapshots(db,ids);verify_rows(p,after)
        for row in records:h.audit_entry(db,'artwork',row['artwork_id'],row['before']['artwork']if row['before']else None,after[row['artwork_id']]['artwork'],'insert'if row['action']=='create'else'update')
        n.save(B/'artwork-transaction-after.json.gz',dict(at=n.now(),plan_sha256=digest,artworks=after))
    receipt=dict(at=n.now(),target='production',plan_sha256=digest,new_artworks=sum(x['action']=='create'for x in records),new_links=sum(x['action']=='link'for x in records),existing_artworks_documented=sum(x['action']=='evidence'for x in records),painter_links=sum(bool(x['artist_id'])for x in records),artwork_ids=ids,held=len(p['held']),new_publications=0,new_display_claims=0,image_changes=0,local_database_writes=0)
    n.save(R/'artworks-applied.json',receipt);print('COMMITTED',{k:v for k,v in receipt.items()if k!='artwork_ids'},flush=True)

def verify_rows(p,after):
    assert len(after)==len(p['records'])
    for row in p['records']:
        snap=after[row['artwork_id']];w=snap['artwork'];f=row['facts'];assert w['current_institution_id']==row['museum']['id']
        if row['before']:
            old=row['before'];assert all(w[k]==v for k,v in old['artwork'].items()if k not in ['current_institution_id','updated_at','revision'])
            assert snap['creators']==old['creators']and snap['media']==old['media']and snap['creator_keys']==old['creator_keys']
            assert all(x in snap['identifiers']for x in old['identifiers'])and all(x in snap['assertions']for x in old['assertions'])
        else:
            assert w['status']=='review'and w['published_at']is None and w['primary_media_id']is None
            for field,source in [('title','title'),('date_display','date_display'),('creation_year_start','first'),('creation_year_end','last'),('date_precision','precision'),('medium_text','medium'),('dimensions_text','dimensions'),('accession_number','accession')]:assert w[field]==f[source],(field,w[field],f[source])
        own=[x for x in snap['assertions']if x['source_id']==n.uid('artwork-source')];assert all(x['claim_type']=='holding'for x in own)

def verify():
    p=n.load(R/'artwork-plan.json.gz');receipt=n.load(R/'artworks-applied.json');assert receipt['plan_sha256']==h.sha((R/'artwork-plan.json.gz').read_bytes())
    with d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        after=loc.snapshots(db,receipt['artwork_ids']);verify_rows(p,after)
        ids=[i['id']for i in p['institutions'].values()]
        counts=db.execute("""SELECT i.id::text,i.name,i.slug,i.status,count(a.id)artworks,
          count(a.id)FILTER(WHERE artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible')eligible,
          count(a.id)FILTER(WHERE a.status='published')published,count(a.id)FILTER(WHERE a.primary_media_id IS NOT NULL)with_images
          FROM institutions i LEFT JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived'
          WHERE i.id=ANY(%s::uuid[])GROUP BY i.id ORDER BY i.name""",(ids,)).fetchall();assert len(counts)==55
        citations=db.execute("SELECT entity_id::text,source_record_id,source_url FROM citations WHERE source_id=%s ORDER BY entity_id,source_record_id",(n.uid('artwork-source'),)).fetchall()
        assert len(citations)==sum(len(source_records(x['facts']))for x in p['records'])
        checked=db.execute("SELECT id::text,artline_creation_scope(creation_year_start,creation_year_end,date_precision)scope,artline_has_selection_evidence(id)selected FROM artworks WHERE id=ANY(%s::uuid[])",(receipt['artwork_ids'],)).fetchall()
        selected={x['id']:x for x in checked}
        for row in p['records']:
            assert selected[row['artwork_id']]['selected']
            if row['action']=='create':assert selected[row['artwork_id']]['scope']=='eligible'or row['facts']['precision']=='unknown'
    n.save(R/'production-verification.json',dict(at=n.now(),verified=True,receipt=receipt,counts=counts,citations=len(citations),creation_scopes=dict(collections.Counter(x['scope']for x in checked))))
    print('VERIFIED',len(after),'artworks;',len(counts),'institutions;',len(citations),'source citations',flush=True)
    for row in counts:
        if row['artworks']:print(row['name'],row['artworks'],'artworks;',row['eligible'],'dated eligible',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['plan','apply','verify']);args=parser.parse_args()
    make_plan()if args.phase=='plan'else globals()[args.phase]()
