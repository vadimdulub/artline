#!/usr/bin/env python3
"""Second bounded production pass for museums currently holding one artwork."""
import argparse, collections, contextlib, csv, gzip, hashlib, importlib.util, io, json, os, re, time
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/museums-exactly-one-round2-20261008'
OP='museums-exactly-one-round2-20261008'
os.environ.setdefault('ARTLINE_MUSEUM_PROXY_PORT','55493')
def module(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file)
    x=importlib.util.module_from_spec(s);s.loader.exec_module(x);return x
p=module('round_one','museums-exactly-one-20261008.py')
p.RUN=RUN;d=p.d

def baseline():
    with contextlib.redirect_stdout(io.StringIO()) as output:p.baseline()
    print(output.getvalue().splitlines()[0],flush=True)

def local_candidates():p.local_candidates()

def qualified_links():
    c=p.campaign();c.OP=OP
    w=module('round_two_links','minimum-100-wikidata-links-20261006.py')
    with d.connect() as db:
        allinst=[x['v'] for x in db.execute("SELECT to_jsonb(i) v FROM institutions i WHERE status<>'archived' AND canonical_institution_id IS NULL")]
    byq=collections.Counter(x.get('wikidata_id') for x in allinst)
    w.c.BASE={iid:x for iid,x in c.BASE.items() if x['institution'].get('wikidata_id') and byq[x['institution']['wikidata_id']]==1}
    w.main(qualified=True,target_count=100,output_root=RUN/'links/qualified')

def history():
    n=module('round_two_wd','minimum-100-wikidata-catalogue-20261006.py')
    histories=n.index_history();b=d.load(RUN/'baseline.json.gz')
    rows=[]
    for x in b['selected']:
        i=x['institution'];h=histories.get(i['id'],[])
        if not i.get('wikidata_id'):continue
        cursor,reason=n.next_cursor(h)
        rows.append(dict(museum=i,pages=len(h),cursor=cursor,reason=reason,last_objects=len(h[-1]['selected_ids']) if h else None))
    d.save(RUN/'wikidata-history.json',rows)
    print('History',dict(collections.Counter(r['reason'] for r in rows)),flush=True)
    for r in rows:
        if not r['reason']:print(r['museum']['name'],r['museum']['wikidata_id'],'pages',r['pages'],flush=True)

def wd_module():
    n=module('round2_native','minimum-100-wikidata-catalogue-20261006.py')
    n.ROOT=RUN/'wikidata-catalogue';n.c.RUN=RUN;n.c.OP=OP
    n.c.BASE={x['institution']['id']:x for x in d.load(RUN/'baseline.json.gz')['selected']}
    return n

def wikidata_research():
    n=wd_module();wave='new-museums'
    rows=d.load(RUN/'wikidata-history.json')
    with d.connect() as db:
        institutions=[x['v'] for x in db.execute("SELECT to_jsonb(i) v FROM institutions i WHERE status<>'archived' AND canonical_institution_id IS NULL")]
    byq=collections.Counter(x.get('wikidata_id') for x in institutions)
    selected=[dict(museum=x['museum'],projected_count=1,cursor='',page_number=1) for x in rows if not x['reason'] and byq[x['museum']['wikidata_id']]==1]
    d.save(n.ROOT/wave/'selected-museums.json',selected)
    n.research(wave,len(selected),target_count=25)

def capture(url):
    assert url.startswith('https://www.crockerart.org/art/')
    path=RUN/'crocker/captures'/(d.sha(url.encode())+'.json')
    if path.exists():
        rc=d.load(path);raw=gzip.decompress((ROOT/rc['body_path']).read_bytes())
        assert d.sha(raw)==rc['sha256'] and rc['status']==200
        return raw,rc
    response=d.requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected catalogue metadata; no images)'},timeout=(15,50))
    raw=response.content;assert len(raw)<5_000_000
    body=path.with_suffix('.body.gz');body.parent.mkdir(parents=True,exist_ok=True)
    assert not body.exists();body.write_bytes(gzip.compress(raw,mtime=0))
    rc=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=d.now(),sha256=d.sha(raw),bytes=len(raw),body_path=str(body.relative_to(ROOT)))
    d.save(path,rc);response.raise_for_status();time.sleep(.5)
    return raw,rc

def crocker_props(raw):
    soup=BeautifulSoup(raw,'html.parser');node=soup.select_one('#__NEXT_DATA__');assert node
    return json.loads(node.text)['props']['pageProps'],soup

def crocker_facts(raw):
    prop,soup=crocker_props(raw);art=prop['art']
    node=next(x for x in soup.find_all('h3') if x.get_text(' ',strip=True)=='Details')
    fields={}
    for li in node.parent.parent.parent.select('ul li'):
        cells=li.select('div.grid > div');assert len(cells)==2
        key=cells[0].get_text(' ',strip=True);assert key not in fields
        fields[key]=cells[1].get_text(' ',strip=True)
    assert fields['title']==art['title']
    if prop.get('name'):assert prop['name']==art['title']
    assert fields['accession no.']==art['accessionNumber'] and fields['date']==art['madeDate']['date']
    assert fields['medium']==art['mediumDetail'] and fields['credit line']==art['creditLine']
    assert re.fullmatch(r'\d{4}',fields['date']) and 100<=int(fields['date'])<=1970
    assert art['medium'] in ['Painting','Drawing'] and re.match(r'^Crocker Art Museum(?:,| Purchase\b)',fields['credit line'])
    assert not re.search(r'\b(?:loan|lent|deposit|deaccession)\b',fields['credit line'],re.I)
    assert art['artists'] and all(x.get('fullNameAggregate') for x in art['artists'])
    creator=fields.get('artist/culture') or fields.get('artists/culture');assert creator
    title=fields['title'];assert not re.search(r'\b(?:detail|fragment|copy|after|verso|recto)\b',title,re.I)
    f=dict(title=title,creator_label=creator,first=int(fields['date']),last=int(fields['date']),date_precision='exact',date_display=fields['date'],work_type={'Painting':'painting','Drawing':'drawing'}[art['medium']],medium=fields['medium'],dimensions=fields.get('dimensions'),accession=fields['accession no.'],source_url='https://www.crockerart.org/art/detail/'+art['slug'],holding_basis='Official Crocker individual collection object: exact native object ID, inventory, title, creator, creation date and Crocker collection credit; HTML and embedded museum metadata agree. Source on-view label retained only in raw evidence, not imported as a current-display assertion.')
    return f,art,fields

def crocker_research():
    museum=next(x['institution'] for x in d.load(RUN/'baseline.json.gz')['selected'] if x['institution']['name']=='Crocker Art Museum')
    candidates=[];held=[];indexes=[]
    for collection in ['american-art-1800-to-1945','european-art']:
        raw,rc=capture('https://www.crockerart.org/art/collections/'+collection)
        props,_=crocker_props(raw);rows=props['artwork'];assert len(rows)<=750
        indexes.append(dict(receipt=rc,rows=len(rows)))
        for art in rows:
            date=art.get('madeDate',{}).get('date','')
            if art['medium'] not in ['Painting','Drawing'] or not re.fullmatch(r'\d{4}',date) or not 100<=int(date)<=1970:continue
            if not art.get('accessionNumber') or not art.get('artists') or any(not x.get('fullNameAggregate') for x in art['artists']):continue
            if re.search(r'\b(?:detail|fragment|copy|after|verso|recto|untitled)\b',art['title'],re.I):continue
            candidates.append(dict(art=art,index_receipt=rc))
    grouped=collections.defaultdict(list)
    for x in candidates:grouped[';'.join(a['fullNameAggregate'] for a in x['art']['artists'])].append(x)
    chosen=[]
    while grouped and len(chosen)<36:
        for name in sorted(list(grouped)):
            if len(chosen)>=36:break
            chosen.append(grouped[name].pop(0))
            if not grouped[name]:del grouped[name]
    d.save(RUN/'crocker/selected.json',dict(indexes=indexes,selected=chosen,eligible_metadata_candidates=len(candidates),policy='Bounded 36-object sample of exact-year paintings/drawings, spread across named source creators; no image downloads.'))
    ready=[]
    for i,x in enumerate(chosen,1):
        art=x['art'];raw,rc=capture('https://www.crockerart.org/art/detail/'+art['slug'])
        try:
            facts,native,fields=crocker_facts(raw)
            for key in ['id','accessionNumber','title','slug','madeDate','medium','mediumDetail','creditLine']:
                assert native[key]==art[key],key
            assert [a['id'] for a in native['artists']]==[a['id'] for a in art['artists']]
            ready.append(dict(artwork_id=d.uid(OP+'/crocker/'+native['id']),slug=OP+'-crocker-'+native['id'],source_record_id=native['id'],museum=museum,facts=facts,provider='crocker-native',origin='fresh_official_object_page',source_receipt=rc,body_path=rc['body_path'],raw_source_record=dict(native=native,fields=fields,index=x)))
            print('Crocker',i,'/',len(chosen),facts['date_display'],facts['title'],flush=True)
        except (AssertionError,KeyError,StopIteration) as exc:
            held.append(dict(source_record_id=art['id'],title=art['title'],reason=type(exc).__name__+': '+str(exc),source_receipt=rc))
    c=p.campaign();c.OP=OP;c.prepare_wave('crocker',ready,held)

def crocker_review():
    selected=d.load(RUN/'crocker/selected.json')['selected']
    museum=next(x['institution'] for x in d.load(RUN/'baseline.json.gz')['selected'] if x['institution']['name']=='Crocker Art Museum')
    ready=[];held=[]
    for x in selected:
        a=x['art'];raw,rc=capture('https://www.crockerart.org/art/detail/'+a['slug'])
        try:
            facts,native,fields=crocker_facts(raw)
            for key in ['id','accessionNumber','title','slug','madeDate','medium','mediumDetail','creditLine']:assert native[key]==a[key],key
            assert [v['id'] for v in native['artists']]==[v['id'] for v in a['artists']]
            ready.append(dict(artwork_id=d.uid(OP+'/crocker/'+native['id']),slug=OP+'-crocker-'+native['id'],source_record_id=native['id'],museum=museum,facts=facts,provider='crocker-native',origin='fresh_official_object_page',source_receipt=rc,body_path=rc['body_path'],raw_source_record=dict(native=native,fields=fields,index=x)))
        except (AssertionError,KeyError,StopIteration) as exc:held.append(dict(source_record_id=a['id'],title=a['title'],reason=type(exc).__name__+': '+str(exc),source_receipt=rc))
    c=p.campaign();c.OP=OP;c.prepare_wave('crocker-reviewed',ready,held)
    for row in ready:print(row['facts']['title'],row['facts']['date_display'],row['facts']['accession'],flush=True)

def configure(wave):
    n=wd_module();n.c.configure(wave);out=n.c.d
    out.TARGET_COUNT=25;out.TARGET_FIELD='linked'
    out.SOURCE_NAME='Exactly-one museum expansion round two: '+('referenced Wikidata catalogue metadata' if wave=='new-museums' else 'Crocker official catalogue metadata')
    out.SOURCE_BASE_URL='https://www.wikidata.org/' if wave=='new-museums' else 'https://www.crockerart.org/'
    out.DEFAULT_CONFIDENCE=.85 if wave=='new-museums' else .95
    out.CONFIDENCE_BASIS=('Exact full Wikidata painting/icon entity, unique live museum authority, one referenced collection statement, original creator labels and explicit eligible creation date. Referenced documents not independently opened; editorial assessment, not calibrated probability.' if wave=='new-museums' else 'Exact official museum page and embedded catalogue object agree on object ID, inventory, title, creator, date and Crocker collection credit. Editorial assessment, not calibrated probability.')
    out.scheme=lambda row:'wikidata' if row['provider']=='wikidata-catalogue' else 'crocker-object'
    def check(row,cache):
        if row['provider']=='wikidata-catalogue':n.check_body(row,cache);return
        assert row['provider']=='crocker-native'
        rc=row['source_receipt'];raw=gzip.decompress((ROOT/row['body_path']).read_bytes())
        assert rc['status']==200 and d.sha(raw)==rc['sha256']
        facts,art,fields=crocker_facts(raw)
        assert facts==row['facts'] and art==row['raw_source_record']['native'] and fields==row['raw_source_record']['fields']
        assert art['id']==row['source_record_id']
    out.check_body=check
    connect=out.connect
    def patient_connect(readonly=True):
        db=connect(readonly)
        if not readonly:db.execute("SET lock_timeout='180s'")
        return db
    out.connect=patient_connect
    return out

def delivery(phase,wave):
    assert wave in ['new-museums','crocker-reviewed','crocker-final']
    out=configure(wave)
    if phase=='plan':out.plan()
    else:
        assert d.load(RUN/'backups.json')['production']['status']=='SUCCESSFUL'
        out.apply()

def backup():
    import subprocess
    raw=subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--limit=5','--format=json'],text=True)
    item=next(x for x in json.loads(raw) if x['status']=='SUCCESSFUL' and x['startTime'].startswith('2026-10-08'))
    d.save(RUN/'backups.json',dict(at=d.now(),production=item,policy='Completed production recovery backup, supplemented by locked per-record transaction preimages under Application Support/Artline/backups. No local writes.'))
    print('Recovery backup',item['id'],item['startTime'],flush=True)

def status():
    with d.connect() as db:
        locks=db.execute("SELECT a.pid,a.application_name,a.state,now()-a.xact_start transaction_age,a.wait_event_type,a.wait_event,left(a.query,160) query_kind FROM pg_locks l JOIN pg_stat_activity a ON a.pid=l.pid WHERE l.locktype='advisory' AND l.granted ORDER BY a.xact_start").fetchall()
    print(json.dumps(locks,default=str),flush=True)

def crocker_collision():
    loc=module('collision_snapshots','apply-artwork-locations-20261004.py')
    with d.connect() as db:
        ids=[x['id'] for x in db.execute("SELECT id::text FROM artworks WHERE normalized_title=%s",(d.norm('A Rocky Hillside'),))]
        snapshots=loc.snapshots(db,ids)
    d.save(RUN/'crocker/rocky-hillside-existing.json.gz',snapshots)
    for aid,x in snapshots.items():
        a=x['artwork'];print(json.dumps(dict(id=aid,artwork={k:a[k] for k in ['title','date_display','creation_year_start','creation_year_end','work_type','medium_text','dimensions_text','accession_number','current_institution_id','status']},creators=x['creator_keys'],identifiers=x['identifiers']),ensure_ascii=False),flush=True)

def crocker_final():
    selected=d.load(RUN/'crocker/selected.json')['selected'];c=p.campaign();c.OP=OP
    museum=next(x['institution'] for x in d.load(RUN/'baseline.json.gz')['selected'] if x['institution']['name']=='Crocker Art Museum')
    ready=[]
    for x in selected:
        a=x['art'];raw,rc=capture('https://www.crockerart.org/art/detail/'+a['slug'])
        facts,native,fields=crocker_facts(raw)
        for key in ['id','accessionNumber','title','slug','madeDate','medium','mediumDetail','creditLine']:assert native[key]==a[key],key
        assert [v['id'] for v in native['artists']]==[v['id'] for v in a['artists']]
        ready.append(dict(artwork_id=d.uid(OP+'/crocker/'+native['id']),slug=OP+'-crocker-'+native['id'],source_record_id=native['id'],museum=museum,facts=facts,provider='crocker-native',origin='fresh_official_object_page',source_receipt=rc,body_path=rc['body_path'],raw_source_record=dict(native=native,fields=fields,index=x)))
    if not (RUN/'waves/crocker-final-base/source-verified.json.gz').exists():c.prepare_wave('crocker-final-base',ready,[])
    out=configure('crocker-final-base')
    if not (out.RUN/'plan.json.gz').exists():out.plan()
    basepath=out.RUN/'plan.json.gz';plan=d.load(basepath)
    assert len(plan['held'])==1 and plan['held'][0]['reason']=='catalogue_title_collision_requires_version_review'
    held=plan['held'][0];row=next(x for x in ready if x['artwork_id']==held['artwork_id'])
    assert row['facts']['title']=='A Rocky Hillside' and row['facts']['first']==row['facts']['last']==1907 and d.norm(row['facts']['creator_label'])=='percy gray'
    comparison=d.load(RUN/'crocker/rocky-hillside-existing.json.gz');assert set(comparison)=={'bb59df27-caec-4c64-8998-90d8756a8586'}
    other=comparison['bb59df27-caec-4c64-8998-90d8756a8586']
    assert other['artwork']['accession_number']=='1989.192' and other['artwork']['creation_year_start']==1635 and other['creator_keys'][0]['name']=='Claude Lorrain'
    assert {x['id'] for x in plan['baseline_title_matches'] if x['normalized_title']==d.norm('A Rocky Hillside')}==set(comparison)
    note='Distinct physical objects share A Rocky Hillside: Crocker Percy Gray, 1907, inventory 2015.68.1 versus Art Institute of Chicago Claude Lorrain, 1635/1636, inventory 1989.192 (native 74186). Different named creators, dates, inventories and media; preserve the Chicago record. Source and full comparison snapshot retained. Editorial confidence 0.95, not calibrated probability.'
    row=dict(row,before=None,action='create',museum=plan['institutions'][museum['id']],editorial_confidence=.95,confidence_basis=note,remaining_uncertainty='Official documented collection holding only; no current display or legal-title assertion.',raw_source_record=dict(row['raw_source_record'],individual_identity_review=dict(basis=note,comparison_path=str((RUN/'crocker/rocky-hillside-existing.json.gz').relative_to(ROOT)),comparison_sha256=d.sha((RUN/'crocker/rocky-hillside-existing.json.gz').read_bytes()))))
    plan['records'].append(row);plan['held']=[];plan['editorial_title_review']=note
    plan['parent_plan']=dict(path=str(basepath.relative_to(ROOT)),sha256=d.sha(basepath.read_bytes()))
    for summary in plan['museums']:
        summary['new_artworks']+=1;summary['projected_eligible']+=1;summary['projected_linked']+=1;summary['available_after_identity_review']+=1
    assert not out.batch_identity_conflicts(plan['records']) and len(plan['records'])==8
    dest=RUN/'waves/crocker-final'
    for file in ['sample.json','source-verified.json.gz','identity-query-plan.json']:d.save(dest/file,d.load(out.RUN/file))
    plan['sample_sha256']=d.sha((dest/'sample.json').read_bytes());d.save(dest/'plan.json.gz',plan)
    d.save(Path.home()/'Library/Application Support/Artline/backups'/OP/'crocker-final/plan-and-preimages.json.gz',plan)
    print('Final Crocker selection: eight native works; exact-title collision independently resolved.',flush=True)

def qualified_phase(phase):
    c=p.campaign();c.OP=OP
    if phase=='link_plan':
        source=d.load(RUN/'links/qualified/claims.json.gz');claims=source['claims']
        before=d.load(RUN/'links/qualified/baseline.json.gz')
        with d.connect() as db:
            scopes={x['id']:x['scope'] for x in db.execute('SELECT id::text,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope FROM artworks WHERE id=ANY(%s::uuid[])',([x['artwork_id'] for x in claims],))}
        ready=[];held=list(source['held'])
        for row in claims:
            art=before[row['artwork_id']]['artwork'];qid=row['external_id']
            if qid=='Q119069371':
                assert art['accession_number']=='P.1986.2045' and art['date_precision']=='unknown'
                qs=row['object_evidence']['collection_statement']['qualifiers']
                assert qs['P580'][0]['datavalue']['value']['time']=='+1950-01-01T00:00:00Z'
                note='Individually reviewed existing painting P.1986.2045: referenced collection-start statement is 1950, not a creation date. Preserve unknown creation fields and review status; accept documented holding only.'
            elif qid in {'Q26270507','Q26270515','Q26270529'}:
                inventory={'Q26270507':'2011.35.4','Q26270515':'2011.35.1','Q26270529':'2011.35.3'}[qid]
                assert art['accession_number']==inventory and scopes[row['artwork_id']]=='eligible'
                qs=row['object_evidence']['collection_statement']['qualifiers']
                assert qs['P217'][0]['datavalue']['value']==inventory
                note='Individually reviewed generic source title Unknown: exact distinct artwork authority, creator authority and matching museum inventory '+inventory+' establish this physical object. Preserve Unknown and the supplied 1920 date without inventing a title. Retain actual Wikidata evidence; direct PastPerfect reference was unavailable.'
            else:
                held.append(dict(artwork_id=row['artwork_id'],reason='No individual qualified-claim review'));continue
            row=dict(row,identity_basis=row['identity_basis']+' '+note,object_evidence=dict(row['object_evidence'],individual_review=note))
            ready.append(row)
        d.save(RUN/'links/qualified-reviewed/claims.json.gz',dict(source,claims=ready,held=held))
        d.save(RUN/'links/qualified-reviewed/baseline.json.gz',d.load(RUN/'links/qualified/baseline.json.gz'))
        d.save(RUN/'links/qualified-reviewed/backups.json',d.load(RUN/'backups.json'))
        print('Reviewed qualified links',len(ready),flush=True)
    c.link_delivery(phase,'qualified-reviewed')

def verify():
    baseline=d.load(RUN/'baseline.json.gz');base={x['institution']['id']:x for x in baseline['selected']}
    records={};receipts=[]
    for wave in ['new-museums','crocker-final']:
        folder=RUN/'waves'/wave;plan=d.load(folder/'plan.json.gz');receipt=d.load(folder/'applied.json')
        assert receipt['plan_sha256']==d.sha((folder/'plan.json.gz').read_bytes())
        receipts.append(dict(wave=wave,**receipt))
        for row in plan['records']:
            assert row['museum']['id'] in base and row['artwork_id'] not in records and row['action']=='create'
            records[row['artwork_id']]=dict(row,plan_sha256=receipt['plan_sha256'])
    linkfolder=RUN/'links/qualified-reviewed/delivery/verified'
    linkplan=d.load(linkfolder/'plan.json.gz');linkproof=d.load(linkfolder/'verification.json')
    assert not linkproof['errors'] and linkproof['plan_sha256']==d.sha((linkfolder/'plan.json.gz').read_bytes())
    links=linkplan['claims'];assert linkproof['targets']=={'production':len(links)}
    assert all(x['target_institutions']['production']['id'] in base for x in links)
    with d.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        rows=db.execute('SELECT to_jsonb(a) artwork,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,artline_has_selection_evidence(id) selected FROM artworks a WHERE id=ANY(%s::uuid[])',(list(records),)).fetchall()
        assert len(rows)==len(records)
        for r in rows:
            a=r['artwork'];row=records[a['id']];f=row['facts']
            assert a['current_institution_id']==row['museum']['id'] and a['status']=='review' and a['published_at'] is None and a['primary_media_id'] is None
            assert r['scope']=='eligible' and r['selected']
            for col,key in [('title','title'),('unlinked_creator_label','creator_label'),('date_display','date_display'),('creation_year_start','first'),('creation_year_end','last'),('date_precision','date_precision'),('accession_number','accession'),('medium_text','medium'),('dimensions_text','dimensions'),('work_type','work_type'),('object_form','object_form')]:assert a[col]==f.get(key),(a['id'],col)
        cites=db.execute("SELECT entity_id::text,source_record_id,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='museum_source_metadata_and_holding'",(list(records),)).fetchall()
        assert len(cites)==len(records)
        for cit in cites:
            row=records[cit['entity_id']];ev=json.loads(cit['evidence_note'])
            assert cit['source_url']==row['facts']['source_url'] and cit['source_record_id']==row['source_record_id'] and ev['plan_sha256']==row['plan_sha256'] and ev['raw_source_record']==row['raw_source_record']
        holdings=db.execute('SELECT artwork_id::text,institution_id::text,claim_type,review_state,superseded_by,display_state FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[])',(list(records),)).fetchall()
        assert len(holdings)==len(records)
        for h in holdings:assert h['institution_id']==records[h['artwork_id']]['museum']['id'] and h['claim_type']=='holding' and h['review_state']=='accepted' and h['superseded_by'] is None and h['display_state'] is None
        external=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(list(records),)).fetchall()
        assert len(external)==len(records)
        for x in external:
            r=records[x['entity_id']];assert x['external_id']==r['source_record_id'] and x['canonical_url']==r['facts']['source_url'] and x['scheme']==('wikidata' if r['provider']=='wikidata-catalogue' else 'crocker-object')
        counts={}
        for part in d.chunks(list(base),100):
            counts.update({x['id']:x for x in db.execute("SELECT i.id::text,i.status,i.canonical_institution_id::text,count(a.id) linked,count(a.id) FILTER(WHERE artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible') eligible,count(a.primary_media_id) images FROM institutions i LEFT JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived' WHERE i.id=ANY(%s::uuid[]) GROUP BY i.id",(part,))})
    added=collections.Counter(x['museum']['id'] for x in records.values());linked=collections.Counter(x['target_institutions']['production']['id'] for x in links)
    museums=[]
    for iid,b in base.items():
        a=counts[iid];changed=added[iid]+linked[iid]
        if changed:assert a['linked']>=1+changed
        museums.append(dict(id=iid,name=b['institution']['name'],slug=b['institution']['slug'],before=1,added=added[iid],linked_existing=linked[iid],after=a['linked'],eligible=a['eligible'],images=a['images'],outside_this_pass_delta=a['linked']-1-changed,outcome='expanded' if changed else 'no_approved_change_in_this_round'))
    summary=dict(at=d.now(),target='production',baseline_museums=len(base),museums_expanded=sum(bool(x['added']+x['linked_existing']) for x in museums),new_artworks=len(records),existing_artworks_linked=len(links),verified_artworks=len(records)+len(links),museums_still_exactly_one=sum(x['after']==1 for x in museums),new_publications=0,new_images=0,new_display_claims=0,local_database_writes=0,museums=museums,receipts=receipts)
    d.save(RUN/'verification.json',summary)
    with (RUN/'museum-results.csv').open('x',newline='') as fp:w=csv.DictWriter(fp,fieldnames=list(museums[0]));w.writeheader();w.writerows(museums)
    arts=[dict(artwork_id=aid,museum=r['museum']['name'],slug=r['museum']['slug'],title=r['facts']['title'],action='create',date_display=r['facts']['date_display'],source_url=r['facts']['source_url'],confidence=r['editorial_confidence']) for aid,r in records.items()]
    arts += [dict(artwork_id=r['target_ids']['production'],museum=r['target_institutions']['production']['name'],slug=r['target_institutions']['production']['slug'],title=r['title'],action='link',date_display='Preserved existing catalogue date',source_url=r['source_url'],confidence=r['object_evidence']['editorial_confidence']) for r in links]
    with (RUN/'artwork-results.csv').open('x',newline='') as fp:w=csv.DictWriter(fp,fieldnames=list(arts[0]));w.writeheader();w.writerows(arts)
    md=f"# Exactly-one-artwork museums: round two\n\nFresh production selection {baseline['at']}: **{len(base)} museums** had exactly one non-archived linked artwork, including review records. Verified {summary['at']}: **{len(records)} new artworks and {len(links)} existing-artwork links across {summary['museums_expanded']} museums**. All new artworks remain review.\n\n"
    md+='[Museum before/after counts](museum-results.csv) · [Every artwork and source](artwork-results.csv) · [Database verification](verification.json) · [19 passed source-validation tests](tests.json).\n\n'
    md+='The collection research covered 22 previously unqueried museum authorities, with bounded index pages and 555 new object entities inspected. Full creator, creation, object-type, collection-statement and reference checks produced 98 source candidates. Production native-ID, inventory, title and version checks admitted 83 new works; conflicting holdings and unresolved title collisions remain held. The actual source is referenced Wikidata metadata, with full original statements retained; underlying referenced documents were not independently opened. Confidence is 0.85 editorial assessment, not calibrated probability.\n\n'
    md+='Eight additional works use fresh official Crocker catalogue pages, with agreement between visible fields and embedded native metadata. The sample covered two 12-object collection pages and selected eight exact-year paintings/drawings. Official purchase and collection credit lines support holdings, not current display. Source labels, inventoried physical objects, creator names, medium, dimensions and creation dates are retained. A Percy Gray drawing dated 1907 and a Claude Lorrain drawing dated 1635/1636 share A Rocky Hillside but have different inventories and institutions; the retained production comparison resolves the collision without altering the Chicago work. Crocker confidence is 0.95 editorial assessment.\n\n'
    md+='Four existing-artwork links use exact artwork/creator authorities and referenced collection statements qualified only by past collection start or inventory. The Carisbrooke painting retains unknown creation dates: 1950 is collection-start evidence and was not copied into creation fields. Three separately inventoried Tucson paintings retain their literal title Unknown and 1920 dates; distinct native object IDs and inventories establish their identity without invented titles. Direct PastPerfect access was unavailable; actual source attribution remains Wikidata. Existing titles, dates, creators, images and publication states were independently verified preserved.\n\n'
    md+=f"At verification **{summary['museums_still_exactly_one']} museums** in this snapshot still had exactly one artwork. Source gaps and holds remain research work; they are not evidence that eligible holdings do not exist. Concurrent catalogue changes, if any, are separate CSV deltas and excluded from this round's totals. No image downloads, display assertions, local database writes, publication, commits or deployment.\n\n"
    md+='Recovery uses completed Cloud SQL backup '+str(d.load(RUN/'backups.json')['production']['id'])+' and exact locked transaction preimages under `~/Library/Application Support/Artline/backups/'+OP+'/`. Shared ingestion locking was respected while another production import completed.\n\n| Museum | Before | Added | Linked | After |\n|---|---:|---:|---:|---:|\n'
    for x in sorted(museums,key=lambda v:(-(v['added']+v['linked_existing']),v['name'])):
        if x['added']+x['linked_existing']:md+=f"| {x['name'].replace('|','/')} | 1 | {x['added']} | {x['linked_existing']} | {x['after']} |\n"
    (RUN/'README.md').write_text(md)
    print(json.dumps({k:v for k,v in summary.items() if k not in ['museums','receipts']}),flush=True)

def api_verify():
    with (RUN/'artwork-results.csv').open() as fp:rows=list(csv.DictReader(fp))
    sample={}
    for row in rows:sample.setdefault(row['slug'],row)
    checks=[]
    for row in sample.values():
        url='https://artlines.org/api/backend/v1/museums/'+row['slug']+'/works/'+row['artwork_id']
        response=d.requests.get(url,timeout=(15,45));body=response.json() if response.status_code==200 else {}
        checks.append(dict(museum=row['museum'],artwork_id=row['artwork_id'],url=url,status=response.status_code,verified=response.status_code==200 and body.get('title')==row['title']))
        print('API',row['museum'],response.status_code,checks[-1]['verified'],flush=True)
    d.save(RUN/'api-verification.json',dict(at=d.now(),checks=checks,passed=sum(x['verified'] for x in checks),failed=sum(not x['verified'] for x in checks)))
    assert all(x['verified'] for x in checks)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['baseline','local_candidates','qualified_links','history','wikidata_research','crocker_research','crocker_review','crocker_collision','crocker_final','status','backup','plan','apply','link_plan','link_apply','link_verify','verify','api_verify']);ap.add_argument('--wave')
    args=ap.parse_args()
    if args.phase in ['plan','apply']:delivery(args.phase,args.wave)
    elif args.phase.startswith('link_'):qualified_phase(args.phase)
    else:globals()[args.phase]()
