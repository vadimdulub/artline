#!/usr/bin/env python3
"""Source-pinned Prado catalogue expansion; production only, records in review.

Read-only discovery precedes a guarded, backed-up import. Original source dates,
qualified/unknown creators and per-object museum links remain explicit.
"""
import argparse, collections, csv, gzip, hashlib, importlib.util, io, json, os, re, subprocess, unicodedata, uuid
from pathlib import Path
from psycopg import sql
from psycopg.types.json import Jsonb

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/prado-expansion-20261006'
OP='prado-catalogue-expansion-20261006'
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
ACTOR='local-european-research'
spec=importlib.util.spec_from_file_location('research',ROOT/'ops/research-artwork-locations-20261004.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
r.PORT=55481
os.environ['CLOUDSDK_CORE_ACCOUNT']='vadim@alingva.com'
MUSEUM='008d3646-ed41-4691-9a37-25a9fff40e51'
RECEIPT=ROOT/'docs/research/artwork-locations-20261004/prado-dataset-receipt-20261005d.json'

def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artlines.org/prado-catalogue/'+key))
def norm(text):
    return ' '.join(re.findall(r'[^\W_]+',''.join(c for c in unicodedata.normalize('NFKD',text or '').casefold()if not unicodedata.combining(c))))
def native(url):return (url or '').split('?')[0].rstrip('/').rsplit('/',1)[-1]
def inventory(text):
    x=re.sub('[^A-Z0-9]','',(text or '').upper())
    return re.sub(r'\d+',lambda m:str(int(m[0])),x)
def insert(db,table,row):
    return db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,row)),sql.SQL(',').join(sql.Placeholder()for _ in row)),tuple(row.values()))
def roman(text):
    values={'I':1,'V':5,'X':10,'L':50,'C':100};n=0;last=0
    for c in reversed(text):v=values[c];n+=v if v>=last else -v;last=max(v,last)
    return n

def date(text):
    """Exact literals only; century subdivisions retain conservative full bounds."""
    original=text;value=norm(text);out={'display':original,'first':None,'last':None,'precision':'unknown','review':True}
    # Normalize typography without extracting years from arbitrary prose.
    value=' '.join(unicodedata.normalize('NFKD',text.replace('–','-').replace('—','-')).encode('ascii','ignore').decode().lower().split())
    approx=bool(re.search(r'hacia|\(ca\.\)|\(circa\)',value))
    cleaned=re.sub(r'^hacia\s+|\s*\((?:hacia|ca\.|circa)\)$','',value)
    m=re.fullmatch(r'(\d{3,4})(?:\s*[-–]\s*(\d{3,4}))?',cleaned)
    if m:
        first=int(m[1]);last=int(m[2]or m[1])
        if first<=last:out.update(first=first,last=last,precision=('circa'if approx else 'exact')if first==last else('circa_range'if approx else'range'),review=last>1970 or approx and last==1970)
        return out
    m=re.fullmatch(r'(antes|despues) de\s+(\d{3,4})',value)
    if m:
        year=int(m[2]);out.update(first=year if m[1]=='despues'else None,last=year if m[1]=='antes'else None,precision='after'if m[1]=='despues'else'before',review=m[1]=='despues'or year>1971)
        return out
    # Century boundaries are an enclosing interval, not invented subdivision dates.
    if re.fullmatch(r'(?:(?:primera|segunda) mitad del |(?:primer|segundo|tercer|ultimo) (?:cuarto|tercio) del |(?:principio|principios|mediados|finales) del )?siglos? [ivxlc]+(?:\s*-\s*(?:(?:(?:primera|segunda) mitad del |(?:primer|segundo|tercer|ultimo) (?:cuarto|tercio) del |(?:principio|principios|mediados|finales) del )?siglo )?[ivxlc]+)?',value):
        centuries=[roman(x.upper())for x in re.findall(r'\b[ivxlc]+\b',value)]
        if centuries and 0<min(centuries)<=max(centuries)<25:
            out.update(first=(min(centuries)-1)*100+1,last=max(centuries)*100,precision='century',review=max(centuries)*100>1970,interval_basis='Enclosing whole-century bounds; original finer wording retained verbatim.')
    return out

def objects():
    receipt=r.load(RECEIPT);raw=gzip.decompress((ROOT/receipt['body_path']).read_bytes());assert r.sha(raw)==receipt['sha256']
    return list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))),receipt

def discover():
    baseline=r.load(RUN/'production-baseline.json.gz');identities=r.load(RUN/'production-source-identities.json.gz')
    rows,receipt=objects();paintings=[x for x in rows if re.fullmatch(r'P\d+(?:/\d+(?:-\d+)?)?',x['Número de catálogo'])]
    allrecords={x['artwork']['id']:x for x in baseline['records']+identities['records']}
    bynative=collections.defaultdict(set);byinventory=collections.defaultdict(set)
    for x in allrecords.values():
        a=x['artwork']
        if a['current_institution_id']==MUSEUM:byinventory[inventory(a['accession_number'])].add(a['id'])
        for e in x['identifiers']:
            if 'prado' in e['scheme'] or 'museodelprado.es' in(e['canonical_url']or''):
                bynative[native(e['canonical_url'])].add(a['id']);bynative[e['external_id']].add(a['id'])
    for x in identities['citations']:bynative[native(x['source_url'])].add(x['entity_id'])
    names=collections.defaultdict(set)
    for a in baseline['artists']:
        if a['status']=='archived':continue
        for name in [a['display_name']]+a['aliases']:names[norm(name)].add(a['id'])
    byacc={inventory(x['Número de catálogo']):x for x in paintings}
    # Existing exact object identities also reconcile the catalogue's Spanish names.
    for x in baseline['records']:
        obj=byacc.get(inventory(x['artwork']['accession_number']))
        primary=[c for c in x['creators']if c['attribution_role']=='primary']
        if obj and len(primary)==1 and not obj['Autores'] and not re.search(r'atribu|taller|copia|anonimo|seguidor|escuela|circulo',norm(obj['Autor'])):
            names[norm(obj['Autor'])].add(primary[0]['artist_id'])
    selection=[]
    for obj in paintings:
        oid=native(obj['url']);assert re.fullmatch(r'[0-9a-f-]{36}',oid)
        matches=bynative[oid]|byinventory[inventory(obj['Número de catálogo'])]
        qualified=bool(obj['Autores']or re.search(r'atribu|taller|copia|anonimo|seguidor|escuela|circulo|posible|colabora',norm(obj['Autor'])))
        creators=names[norm(obj['Autor'])]if not qualified else set()
        d=date(obj['Fecha']);state='existing'if len(matches)==1 else'identity_conflict'if matches else'candidate'
        if d['first'] is not None and (d['first']>1970 or d['precision']=='after'and d['first']>=1970):state='excluded_post_1970'
        selection.append({'source_id':oid,'accession':obj['Número de catálogo'],'object':obj,'date':d,
            'artwork_id':next(iter(matches))if len(matches)==1 else uid('object/'+oid),
            'existing_ids':sorted(matches),'artist_id':next(iter(creators))if len(creators)==1 else None,
            'creator_label':obj['Autores']or obj['Autor']or None,'qualified_creator':qualified,'outcome':state})
    assert len({x['source_id']for x in selection})==len(selection)==7141
    r.save_gz(RUN/'painting-discovery.json.gz',{'at':r.now(),'source_receipt':receipt,'records':selection,'counts':dict(collections.Counter(x['outcome']for x in selection))})
    summary={'records':len(selection),'outcomes':dict(collections.Counter(x['outcome']for x in selection)),
        'creator_reconciled':sum(bool(x['artist_id'])for x in selection),'creator_label_retained':sum(not x['artist_id']for x in selection),
        'date_review':sum(x['date']['review']for x in selection),'date_precisions':dict(collections.Counter(x['date']['precision']for x in selection))}
    r.save(RUN/'painting-discovery-summary.json',summary);print(json.dumps(summary),flush=True)

def backup():
    description='Before complete Prado catalogue expansion 20261006'
    def gc(*args):return json.loads(subprocess.check_output(['gcloud',*args,'--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True))
    matches=[x for x in gc('sql','backups','list','--instance=artline-postgres','--limit=100')if x.get('description')==description]
    if not matches:
        op=gc('sql','backups','create','--instance=artline-postgres','--description='+description,'--async');r.save(BACKUP/'cloud-backup-operation.json',op);print('Recovery backup requested');return
    current=max(matches,key=lambda x:int(x['id']))
    if current['status']!='SUCCESSFUL':print('Recovery backup',current['status']);return
    r.save(BACKUP/'cloud-backup.json',current);r.save(RUN/'cloud-backup.json',{'id':current['id'],'status':current['status']});print('Recovery backup verified',current['id'])

def reconcile():
    discovery=r.load(RUN/'painting-discovery.json.gz')
    wd=r.load(RUN/'production-wikidata-identities.json.gz')
    baseline=r.load(RUN/'production-baseline.json.gz')
    qexisting=collections.defaultdict(set)
    for e in wd['identifiers']:qexisting[e['external_id']].add(e['entity_id'])
    wrows=r.load(RUN/'prado-wikidata-discovery.body.gz')['results']['bindings']
    bynative=collections.defaultdict(list);byinventory=collections.defaultdict(list)
    for w in wrows:
        if 'prado'in w:bynative[w['prado']['value']].append(w)
        if 'inventory'in w:byinventory[inventory(w['inventory']['value'])].append(w)
    extras={x['accession']:x for x in r.load(ROOT/'docs/research/prado-wikiart-20261006/resolution-20261006/additional-artworks.json')['artworks']}
    anames=collections.defaultdict(set)
    for a in baseline['artists']:
        if a['status']!='archived':
            for name in [a['display_name']]+a['aliases']:anames[norm(name)].add(a['id'])
    aq={x['external_id']:x['entity_id'] for x in r.load(RUN/'production-artist-wikidata.json.gz')}
    creators=collections.defaultdict(set)
    for w in r.load(RUN/'prado-wikidata-creators.body.gz')['results']['bindings']:
        creators[native(w['item']['value'])].add(native(w['creator']['value']))
    for x in discovery['records']:
        matches=set(x['existing_ids']);ws=bynative[x['source_id']]
        if not ws:
            # Inventory-only links must not carry a contradictory native museum ID.
            ws=[w for w in byinventory[inventory(x['accession'])] if 'prado'not in w or w['prado']['value']==x['source_id']]
        qs=sorted({native(w['item']['value'])for w in ws})
        for q in qs:matches.update(qexisting[q])
        extra=extras.get(x['accession'])
        if extra and extra.get('existing_record'):
            matches.add(extra['existing_record']['id'])
        x['wikidata_ids']=qs
        x['image_leads']=sorted({w['image']['value'] for w in ws if 'image'in w})
        x['existing_ids']=sorted(matches)
        if len(matches)==1:x['artwork_id']=next(iter(matches))
        if x['outcome']!='excluded_post_1970':x['outcome']='existing'if len(matches)==1 else'identity_conflict'if matches else'candidate'
        if x['creator_label'] and not x['qualified_creator']:
            candidates=set().union(*(creators[q] for q in qs))
            ids={aq[q] for q in candidates if q in aq}
            if len(candidates)==len(ids)==1:
                anames[norm(x['object']['Autor'])].update(ids)
                x['creator_identity_evidence']={'wikidata_creator':next(iter(candidates)),'museum_creator':x['object']['Autor']}
    # Propagate only unambiguous, exact museum creator labels across this source.
    for x in discovery['records']:
        ids=anames[norm(x['object']['Autor'])]
        if x['creator_label'] and not x['qualified_creator'] and len(ids)==1:x['artist_id']=next(iter(ids))
        if not x['creator_label']:x['artist_id']=None
    reused=collections.defaultdict(list)
    for x in discovery['records']:
        if x['outcome']=='existing':reused[x['artwork_id']].append(x)
    collisions=[]
    for aid,rows in reused.items():
        if len(rows)>1:
            collisions.append({'artwork_id':aid,'accessions':[x['accession']for x in rows]})
            for x in rows:x['outcome']='identity_conflict'
    summary={'at':r.now(),'source_rows':len(discovery['records']),
        'outcomes':dict(collections.Counter(x['outcome']for x in discovery['records'])),
        'creators_reconciled':sum(bool(x['artist_id'])for x in discovery['records']),
        'with_image_lead':sum(bool(x['image_leads'])for x in discovery['records']), 'cross_object_collisions':collisions}
    r.save_gz(RUN/'painting-reconciled.json.gz',{'records':discovery['records'],'summary':summary,'source_receipt':discovery['source_receipt']})
    r.save(RUN/'painting-reconciled-summary.json',summary);print(json.dumps(summary),flush=True)

def plan():
    data=r.load(RUN/'painting-reconciled.json.gz');records=data['records']
    manual={
      'P007945':('a1d47b63-9654-5746-b653-2607001f1485','Exact Leonardo Alenza title and 1844 date; preserved WikiArt page explicitly names Prado; museum inventory corroborates the former secondary location lead.'),
      'P004604':('8492cf8a-2780-5132-8686-41360d7922fc','Exact Manuel Rodriguez de Guzman title and 1855 date; existing WikiArt reproduction aspect agrees with 194 by 124 cm museum object.'),
      'P004494':('465041a6-b915-53e3-8a3c-1b8eb4dd19c7','Exact original Spanish title, Martin Rico, 1865, 85 by 160 cm and Prado location in preserved WikiArt metadata.'),
      'P005624':('57009f96-e6ce-5617-a9e6-63ed0cc8cfc5','Two Wikidata entities describe the same title, Ventura Alvarez Sala, 1897, 230 by 280 cm Prado work. Preserve the existing record and its identifier; add the museum-native identifier. See title-collision-wikidata.json.')}
    for x in records:
        if not x['creator_label']:
            x['artist_id']=None
            x.pop('creator_identity_evidence',None)
        if x['accession']in manual:
            aid,reason=manual[x['accession']];assert x['outcome']=='candidate'
            x.update(artwork_id=aid,existing_ids=[aid],outcome='existing',identity_resolution=reason)
        if x['accession']=='P008071':x['identity_resolution']='Distinct from P008072 despite identical artist, title and 1912 date: native IDs and heights 120 versus 114.5 cm differ. Retain separate records.'
    selected=[x for x in records if x['outcome']in ('existing','candidate')]
    qcounts=collections.Counter(q for x in selected for q in x['wikidata_ids'])
    for x in selected:
        x['add_wikidata_identifier']=x['outcome']=='candidate' and len(x['wikidata_ids'])==1 and qcounts[x['wikidata_ids'][0]]==1
        if any(qcounts[q]>1 for q in x['wikidata_ids']):
            x['identity_resolution']='Shared Wikidata entity conflates two museum objects. Keep distinct native museum IDs and dimensions; do not import the shared Wikidata identifier or use its image lead.'
            x['image_leads']=[]
    assert len({x['artwork_id']for x in selected})==len(selected)
    ids=[x['artwork_id']for x in selected]
    with r.connect('production')as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        current={x['artwork']['id']:x for x in db.execute("SELECT to_jsonb(a) artwork,COALESCE((SELECT jsonb_agg(to_jsonb(e) ORDER BY e.id) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]') identifiers,COALESCE((SELECT jsonb_agg(to_jsonb(l) ORDER BY l.id) FROM artwork_location_assertions l WHERE l.artwork_id=a.id),'[]') assertions FROM artworks a WHERE a.id=ANY(%s::uuid[])",(ids,)).fetchall()}
        museum=db.execute('SELECT to_jsonb(i) data FROM institutions i WHERE id=%s',(MUSEUM,)).fetchone()['data']
        before=db.execute('SELECT count(*) works,count(primary_media_id) images FROM artworks WHERE current_institution_id=%s',(MUSEUM,)).fetchone()
        assert db.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s',(ACTOR,)).fetchone()
    for x in selected:
        a=current.get(x['artwork_id']);assert bool(a)==(x['outcome']=='existing')
        if a:
            institution=a['artwork']['current_institution_id']
            assert institution in (None,MUSEUM),'Conflicting existing museum requires individual resolution'
            accepted=[z for z in a['assertions']if z['claim_type']=='holding'and z['review_state']=='accepted'and not z['superseded_by']]
            assert not accepted or len(accepted)==1 and accepted[0]['institution_id']==MUSEUM
            x['add_holding']=not bool(accepted)
        else:x['add_holding']=True
        assert len(x['creator_label']or'')<=500
    plan={'operation':OP,'at':r.now(),'records':selected,'excluded':[x for x in records if x['outcome']not in ('existing','candidate')],
      'source_receipt':data['source_receipt'],'source_dataset':'https://zenodo.org/records/19261880','source_publication_date':'2026-03-27',
      'source_id':uid('source/'+OP),'preimages':current,'museum':museum,'before':before,
      'policy':'Paintings first; add review records with exact Prado-native source IDs and preserved literal dates and creator labels. Source is an independent archived scrape of museum catalogue pages, not a fresh official export. Museum collection connection is separate from physical location and current display. No publication, personal masterpiece designation, or existing metadata/image replacement.'}
    r.save_gz(RUN/'production-plan.json.gz',plan);digest=r.sha((RUN/'production-plan.json.gz').read_bytes())
    r.save(RUN/'production-plan-pin.json',{'sha256':digest,'new':sum(x['outcome']=='candidate'for x in selected),'existing':len(current),'add_holdings':sum(x['add_holding']for x in selected),'date_review':sum(x['date']['review']for x in selected),'before':before})
    r.save_gz(BACKUP/'production-plan.json.gz',plan)
    print(json.dumps(r.load(RUN/'production-plan-pin.json')),flush=True)

def apply():
    raw=(RUN/'production-plan.json.gz').read_bytes();digest=r.sha(raw);pin=r.load(RUN/'production-plan-pin.json');assert digest==pin['sha256']
    plan=json.loads(gzip.decompress(raw));assert r.load(BACKUP/'cloud-backup.json')['status']=='SUCCESSFUL'
    rows=plan['records'];ids=[x['artwork_id']for x in rows];new=[x for x in rows if x['outcome']=='candidate'];sid=plan['source_id']
    with r.connect('production',readonly=False)as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='10s'")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        if db.execute('SELECT 1 FROM sources WHERE id=%s',(sid,)).fetchone():
            assert db.execute('SELECT count(*) n FROM external_identifiers WHERE source_id=%s AND scheme=%s',(sid,'prado-native-object')).fetchone()['n']==len(rows)
            print('Already applied; zero writes',flush=True);return
        actual={x['data']['id']:x['data']for x in db.execute('SELECT to_jsonb(a) data FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()}
        assert set(actual)==set(plan['preimages']),'Object existence changed after plan'
        for aid,a in actual.items():assert a==plan['preimages'][aid]['artwork'],'Existing artwork changed after plan: '+aid
        urls=[x['object']['url']for x in new]
        assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) LIMIT 1",(urls,)).fetchone(),'Concurrent source identity'
        newqs=sorted({q for x in new for q in x['wikidata_ids']})
        assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s) LIMIT 1",(newqs,)).fetchone(),'Concurrent Wikidata identity'
        assert not db.execute("SELECT 1 FROM external_identifiers WHERE scheme='prado-native-object' AND external_id=ANY(%s) LIMIT 1",([x['source_id']for x in rows],)).fetchone()
        current_inventories={inventory(x['accession_number'])for x in db.execute('SELECT accession_number FROM artworks WHERE current_institution_id=%s',(MUSEUM,))if x['accession_number']}
        assert not current_inventories&{inventory(x['accession'])for x in new},'Concurrent museum accession'
        r.save_gz(BACKUP/'locked-production-preimages.json.gz',{'at':r.now(),'plan_sha256':digest,'artworks':actual})
        insert(db,'sources',{'id':sid,'slug':OP,'name':'Prado catalogue — independent March 2026 source snapshot, reconciled 6 October 2026','source_type':'collection_page','base_url':'https://www.museodelprado.es/coleccion/','api_docs_url':plan['source_dataset']})
        now=r.now()
        with db.pipeline():
            for n,x in enumerate(rows,1):
                aid=x['artwork_id'];o=x['object'];d=x['date']
                if x['outcome']=='candidate':
                    insert(db,'artworks',{'id':aid,'slug':'prado-'+x['accession'].lower().replace('/','-')+'-'+x['source_id'][:8],
                      'title':o['Título'],'normalized_title':norm(o['Título']),'date_display':o['Fecha']or'Unknown',
                      'creation_year_start':d['first'],'creation_year_end':d['last'],'date_precision':d['precision'],'work_type':'painting',
                      'medium_text':'; '.join(z for z in (o['Técnica'],o['Soporte'])if z)or None,'dimensions_text':o['Dimensión']or None,
                      'accession_number':x['accession'],'status':'review','research_candidate':True,'unlinked_creator_label':x['creator_label'],
                      'created_by':ACTOR,'updated_by':ACTOR})
                    if x['artist_id']:
                        assert x['creator_label'],'Missing source creator must remain unlinked'
                        insert(db,'artwork_artists',{'artwork_id':aid,'artist_id':x['artist_id'],'attribution_role':'primary','attribution_note':'Exact museum creator label reconciled to existing authority; source wording: '+x['creator_label']})
                    if x['add_wikidata_identifier']:
                        q=x['wikidata_ids'][0];insert(db,'external_identifiers',{'entity_type':'artwork','entity_id':aid,'scheme':'wikidata','external_id':q,'canonical_url':'https://www.wikidata.org/wiki/'+q,'source_id':sid,'retrieved_at':now})
                insert(db,'external_identifiers',{'entity_type':'artwork','entity_id':aid,'scheme':'prado-native-object','external_id':x['source_id'],'canonical_url':o['url'],'source_id':sid,'retrieved_at':now})
                evidence={'operation':OP,'plan_sha256':digest,'museum_accession':x['accession'],'source_dataset':plan['source_dataset'],
                  'source_snapshot_sha256':plan['source_receipt']['sha256'],'source_publication_date':plan['source_publication_date'],
                  'raw_source_record_sha256':r.sha(json.dumps(o,ensure_ascii=False,sort_keys=True).encode()),
                  'creator_label':x['creator_label'],'date':d,'wikidata_ids':x['wikidata_ids'],
                  'identity_resolution':x.get('identity_resolution'),'policy':plan['policy']}
                insert(db,'citations',{'entity_type':'artwork','entity_id':aid,'field_name':'prado_catalogue_source_metadata','source_id':sid,'source_record_id':x['source_id'],'source_url':o['url'],'evidence_note':json.dumps(evidence,ensure_ascii=False),'retrieved_at':now,'created_by':ACTOR})
                if x['add_holding']:
                    insert(db,'artwork_location_assertions',{'artwork_id':aid,'claim_type':'holding','institution_id':MUSEUM,'context':'collection','source_id':sid,'source_url':o['url'],
                      'evidence_note':'Prado catalogue connection: '+x['accession']+', '+o['Título']+'. Exact native object ID in independently archived museum catalogue metadata published 2026-03-27; dataset '+plan['source_dataset']+'; SHA-256 '+plan['source_receipt']['sha256']+'. '+('Corroborating Wikidata collection/native ID: '+', '.join(x['wikidata_ids'])+'. 'if x['wikidata_ids']else'')+'No physical whereabouts or on-view claim.',
                      'checked_at':now,'source_updated_at':'2026-03-27T00:00:00Z','review_state':'accepted'})
                if n%500==0:print('Queued',n,'/',len(rows),flush=True)
        after=db.execute('SELECT count(*) works,count(primary_media_id) images FROM artworks WHERE current_institution_id=%s',(MUSEUM,)).fetchone()
        assert db.execute('SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND current_institution_id=%s',(ids,MUSEUM)).fetchone()['n']==len(ids)
        assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND status='review' AND research_candidate AND published_at IS NULL",([x['artwork_id']for x in new],)).fetchone()['n']==len(new)
        assert db.execute("SELECT count(*) n FROM artwork_location_assertions WHERE source_id=%s AND claim_type='display'",(sid,)).fetchone()['n']==0
    r.save(RUN/'production-applied.json',{'at':r.now(),'plan_sha256':digest,'created':len(new),'existing_reconciled':len(rows)-len(new),'holdings_added':sum(x['add_holding']for x in rows),'before':plan['before'],'after':after,'published':0,'local_database_writes':0})
    print(json.dumps(r.load(RUN/'production-applied.json')),flush=True)

def verify():
    plan=r.load(RUN/'production-plan.json.gz');pin=r.load(RUN/'production-plan-pin.json');rows=plan['records'];ids=[x['artwork_id']for x in rows]
    assert pin['sha256']==r.sha((RUN/'production-plan.json.gz').read_bytes())
    with r.connect('production')as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        after={x['data']['id']:x['data']for x in db.execute('SELECT to_jsonb(a) data FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()}
        identifiers=db.execute('SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE source_id=%s',(plan['source_id'],)).fetchall()
        citations=db.execute('SELECT entity_id::text,source_record_id,source_url,evidence_note FROM citations WHERE source_id=%s',(plan['source_id'],)).fetchall()
        locations=db.execute('SELECT artwork_id::text,claim_type,review_state,institution_id::text FROM artwork_location_assertions WHERE source_id=%s',(plan['source_id'],)).fetchall()
        counts=db.execute('SELECT count(*) works,count(primary_media_id) images,count(*) FILTER(WHERE status=%s) review FROM artworks WHERE current_institution_id=%s',('review',MUSEUM)).fetchone()
        scopes=db.execute('SELECT artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) GROUP BY 1',(ids,)).fetchall()
        creators=db.execute('SELECT artwork_id::text,artist_id::text,attribution_role FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',([x['artwork_id']for x in rows if x['outcome']=='candidate'],)).fetchall()
    assert len(after)==len(ids)==len(citations)
    native_ids={x['entity_id']:x for x in identifiers if x['scheme']=='prado-native-object'};assert len(native_ids)==len(ids)
    creator_map=collections.defaultdict(list)
    for c in creators:creator_map[c['artwork_id']].append(c)
    for x in rows:
        a=after[x['artwork_id']];o=x['object'];assert a['current_institution_id']==MUSEUM
        assert native_ids[a['id']]['external_id']==x['source_id']and native_ids[a['id']]['canonical_url']==o['url']
        if x['outcome']=='candidate':
            assert a['status']=='review'and a['research_candidate']and a['published_at']is None
            assert a['title']==o['Título']and a['date_display']==(o['Fecha']or'Unknown')and a['unlinked_creator_label']==x['creator_label']
            assert (a['creation_year_start'],a['creation_year_end'],a['date_precision'])==(x['date']['first'],x['date']['last'],x['date']['precision'])
            assert a['accession_number']==x['accession']and a['work_type']=='painting'
            cs=creator_map[a['id']];assert (len(cs)==1 and cs[0]['artist_id']==x['artist_id']and cs[0]['attribution_role']=='primary')if x['artist_id']else not cs
        else:
            before=plan['preimages'][a['id']]['artwork'];allowed={'current_institution_id','updated_at'}
            assert {k:v for k,v in a.items()if k not in allowed}=={k:v for k,v in before.items()if k not in allowed},'Existing metadata or image changed: '+a['id']
    assert all(x['claim_type']=='holding'and x['review_state']=='accepted'and x['institution_id']==MUSEUM for x in locations)
    assert all(json.loads(c['evidence_note'])['plan_sha256']==pin['sha256']for c in citations)
    result={'at':r.now(),'read_only':True,'plan_sha256':pin['sha256'],'verified_records':len(ids),'new_review_records':sum(x['outcome']=='candidate'for x in rows),
      'existing_records_preserved':len(plan['preimages']),'native_identity_citations':len(citations),'holding_assertions':len(locations),'display_claims_added':0,
      'production':counts,'creation_scope_counts':scopes,'all_checks_passed':True}
    r.save_gz(RUN/'production-after-metadata.json.gz',{'at':r.now(),'records':after});r.save(RUN/'metadata-verification.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['discover','backup','reconcile','plan','apply','verify']);args=parser.parse_args();globals()[args.command]()
