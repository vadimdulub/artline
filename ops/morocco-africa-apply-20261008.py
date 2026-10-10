#!/usr/bin/env python3
"""Source-pinned, idempotent local Morocco/Africa catalogue expansion."""
import argparse, collections, copy, gzip, hashlib, importlib.util, json
from pathlib import Path
from urllib.parse import urlsplit

spec=importlib.util.spec_from_file_location('b',Path(__file__).with_name('morocco-africa-build-20261008.py'))
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
m=b.m; PLAN=m.RUN/'application-plan.json.gz'
SCHEME='morocco-africa-object-20261008'; FIELD='morocco_africa_research_20261008'
CALDECOTT='05a8efd8-5531-50a9-953b-0e9d1c7c9bb3'
COUNTRIES={'KE':('Kenya','eastern-africa'),'RW':('Rwanda','eastern-africa'),'ZW':('Zimbabwe','eastern-africa'),'BJ':('Benin','western-africa'),'TN':('Tunisia','northern-africa'),'TZ':('United Republic of Tanzania','eastern-africa')}
FIELDS={'title':'title','date_display':'date_display','creation_year_start':'first','creation_year_end':'last','date_precision':'date_precision','work_type':'work_type','medium_text':'medium','dimensions_text':'dimensions','accession_number':'accession','unlinked_creator_label':'creator'}

def json_safe(value):return json.loads(json.dumps(value,default=str))
def source_key(r):return urlsplit(r['receipt']['url']).netloc.lower().removeprefix('www.')
def source_id(r):return m.uid('source/'+source_key(r))
def check_receipt(r):
    assert r['status']==200 and not r.get('error')
    raw=gzip.decompress((m.ROOT/r['body_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==r['sha256']
def rows(db,table,ids,column='id'):
    return db.execute(f'SELECT to_jsonb(t) row FROM {table} t WHERE {column}=ANY(%s::uuid[]) ORDER BY to_jsonb(t)::text',(ids,)).fetchall()

def prepare():
    assert not PLAN.exists(),'Preserve existing reviewed plan'
    directory=m.load(m.RUN/'proposed-directory.json');works=m.load(m.RUN/'proposed-artworks.json')
    # Resolve source heading/address discrepancies without rewriting source names.
    corrections={'ng-kanta':'Argungu','ng-oko-surulere':'Oko','ng-benin':'Benin City','ng-birni-kudu':'Birnin Kudu','ng-yenegoa':'Yenagoa'}
    for r in directory:
        if r['key'] in corrections:
            r['city']=corrections[r['key']];r['note']+=' City follows the postal address in the same official directory, rather than its abbreviated heading.'
    url='https://if-maroc.org/wp-content/uploads/2023/06/Brochure-2eme-edition-de-la-NMEC-2023.pdf'
    rc,_=m.capture(url);texts=Path('/tmp/artline-nmec2023.txt').read_text().split('\f')
    for key,name,city,n,anchor in [
      ('slaoui','Musée de la Fondation Abderrahman Slaoui','Casablanca',5,'MUSÉE DE LA FONDATION ABDERRAHMAN SLAOUI'),
      ('macma','Musée d’Art et de Culture de Marrakech (MACMA)','Marrakech',14,'MUSÉE D’ART ET DE CULTURE – MACMA'),
      ('femme','Musée de la Femme de Marrakech','Marrakech',15,'MUSÉE DE LA FEMME'),
      ('parfum','Musée du Parfum','Marrakech',16,'MUSÉE DU PARFUM'),
      ('telecom','Musée de Maroc Telecom','Rabat',21,'MUSÉE DE MAROC TELECOM'),
      ('barid','Musée Barid Al-Maghrib','Rabat',24,'MUSÉE BARID AL-MAGHRIB')]:
        d=dict(receipt=rc,text=texts[n-1]);note='Institution identity and address documented by the 2023 museum-night organiser; no current opening, exhibition or display claim.'
        if key=='femme':note+=' Later closure reports require operational-status follow-up; retain historical institution identity only.'
        r=b.institution(key,name,city,'MA',d,anchor,note=note);r['source_url']+='#page='+str(n);r['existing']=None;r['confidence']=.96
        r['confidence_basis']='Named museum and precise address in its cultural-event organiser’s brochure; historical existence is secure, current operation is not asserted.'
        directory.append(r)
    for key,name,city,pk,anchor in [('marrakech','Musée de Marrakech','Marrakech','marrakech-seven','Musée de Marrakech'),('belghazi-fes','Musée Dar Belghazi — Fès','Fès','morocco-tourism','Dar Belghazi Museum')]:
        r=b.institution(key,name,city,'MA',b.page(pk),anchor,note='Official tourism authority confirms museum and city; no individual object holding or current display inferred.');r['existing']=None;directory.append(r)
    # Consolidate national-collection venues without assigning objects to a branch.
    venues=[]
    for city,n,anchor in [('Casablanca',4,'VILLA DES ARTS DE CASABLANCA'),('Rabat',23,'VILLA DES ARTS DE RABAT')]:
        assert anchor in texts[n-1]
        venues.append(dict(id=m.uid('venue/villa-'+city.lower()),institution_key='almada',name='Villa des Arts de '+city,slug='villa-des-arts-'+city.lower(),city=city,country='MA',source_url=url+'#page='+str(n),visit_url='https://www.villadesarts.ma/',receipt=rc,anchor=anchor))
    identity=m.load(m.RUN/'identity-audit.json.gz');supp=m.load(m.RUN/'identity-audit-supplement.json.gz')
    artist_rows={x['row']['id']:x['row'] for x in identity['artists']+supp['artists']}
    # Only unique exact full-name token matches; no surname-only artist assignment.
    for r in works:
        candidates=[a for a in artist_rows.values() if sorted(m.norm(a['display_name']).split())==sorted(m.norm(r['creator']).split())]
        if r['creator']=='Mahmoud Said':candidates=[artist_rows['a464236f-3175-546d-ad0c-840ec6c56950']]
        assert len(candidates)<=1
        r['artist_id']=candidates[0]['id'] if candidates else None
        r['artist_basis']='Unique full-name match to existing artist directory; original museum creator label retained.' if candidates else 'Unreconciled creator retained as source label; no artist biography created.'
        if r['creator']=='Mahmoud Said':r['artist_basis']='Mahmoud Said / Mahmoud Saiid spelling reconciled with existing WikiArt-backed artist profile (1897–1964) and Ministry catalogue biography; original label retained.'
        r['existing_id']=None
        if r['key']=='gac/dgFzQFpfp8VpYg':
            r['existing_id']=CALDECOTT;r['confidence']=.98
            r['identity_basis']='Existing Q56230417: same distinctive title Cricket Match (Malay Quarter), Harry Stratford Caldecott, 1924, and original Q1419469 collection statement; independently confirmed by museum-supplied GAC record. Add holding and evidence only; preserve all catalogue metadata.'
        elif r['key']=='said-2024/portrait-of-listas':
            r['identity_basis']='Compared the existing Painter Leysans reproduction with rendered catalogue PDF page 17. They depict different people and compositions despite identical published dimensions (79 x 62.9 cm). Separate objects; no merge and no borrowed 1940 date.'
        elif r['key']=='legation/storyteller':
            r['identity_basis']='Existing NGA and Met impressions have separate institutional provenance and dimensions. Add only the Legation’s separately catalogued physical print; no edition or inventory inferred.'
        else:r['identity_basis']='Scoped existing creator-linked and creator-labelled catalogue searched; no same-object title/date/inventory/measurement collision. Distinct inventories preserve generic-title works.'
        if r['key']=='legation/zohra':r['date_display']='May 1952'
    with m.connect() as db:
        initial=m.load(m.RUN/'initial-directory.json.gz')
        current=db.execute('SELECT to_jsonb(i) row FROM institutions i ORDER BY id').fetchall()
        assert [x['row'] for x in current]==initial['institutions'],'Institution directory changed'
        for r in directory:
            matches=[x['row'] for x in current if m.norm(x['row']['name'])==m.norm(r['name']) or x['row']['slug']==r['slug']]
            assert not matches or r['existing'] and len(matches)==1 and matches[0]['id']==r['id'],r['name']
        places=db.execute('SELECT to_jsonb(p) row FROM places p ORDER BY id').fetchall();newplaces={}
        for r in directory+venues:
            key=(r['country'],m.norm(r['city']));matches=[x['row'] for x in places if x['row']['country_code']==r['country'] and m.norm(x['row']['name'])==key[1]]
            assert len(matches)<=1
            if matches:r['place_id']=matches[0]['id']
            else:
                newplaces[key]=dict(id=m.uid('place/'+key[0]+'/'+key[1]),name=r['city'],normalized_name=key[1],country_code=key[0]);r['place_id']=newplaces[key]['id']
        protected={x['row']['id']:x['row'] for x in identity['artworks']+supp['artworks']}
        ids=sorted(protected)
        assert {x['row']['id']:x['row'] for x in rows(db,'artworks',ids)}==protected,'Artwork identity snapshot changed'
        baseline={name:rows(db,name,ids,col) for name,col in [('artworks','id'),('artwork_artists','artwork_id'),('artwork_media','artwork_id'),('artwork_location_assertions','artwork_id')]}
        baseline['citations']=db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(ids,)).fetchall()
        baseline['institutions']=[r['existing'] for r in directory if r['existing']]
        baseline['artists']=rows(db,'artists',[r['artist_id'] for r in works if r['artist_id']])
        assert not [r for r in baseline['artwork_location_assertions'] if r['row']['artwork_id']==CALDECOTT and r['row']['review_state']=='accepted' and r['row']['superseded_by'] is None]
        baseline['countries']=db.execute('SELECT * FROM countries WHERE code=ANY(%s) ORDER BY code',([r['country'] for r in directory],)).fetchall()
        newcountries=[dict(code=k,name=v[0],region_code=v[1]) for k,v in COUNTRIES.items() if k not in {r['code'] for r in baseline['countries']}]
    m.save(m.RUN/'application-baseline.json.gz',baseline)
    source_names={'fnm.ma':'Fondation Nationale des Musées — Morocco','fondationalmada.ma':'Fondation Al Mada','villadesarts.ma':'Villas des Arts — Fondation Al Mada collection catalogue','artsandculture.google.com':'Google Arts & Culture — museum-supplied object catalogues','fineart.gov.eg':'Egypt Ministry of Culture — Fine Arts Sector','if-maroc.org':'Institut français du Maroc — museum-night organiser'}
    sources={source_key(r):dict(id=source_id(r),slug='africa-research-20261008-'+source_key(r).replace('.','-'),name=source_names.get(source_key(r),'Institutional museum source — '+source_key(r)),source_type='collection_page',base_url='https://'+urlsplit(r['receipt']['url']).netloc+'/') for r in directory+works}
    evidence=[b.ref(m.RUN/name) for name in ['proposed-directory.json','proposed-artworks.json','identity-audit.json.gz','identity-audit-supplement.json.gz','application-baseline.json.gz','source-holds.json.gz']]
    plan=dict(at=m.now(),institutions=directory,artworks=works,venues=venues,places=list(newplaces.values()),countries=newcountries,sources=list(sources.values()),evidence=evidence,policy='Requested selected LOCAL catalogue additions only. New artworks and institutions remain review. Unknown dates retain research candidates and are not automatically eligible. No current display, publication, image or artist-biography changes. Existing holdings enrichment preserves prior metadata. Holdings confidence is editorial, not probability.')
    validate(plan)
    m.save(PLAN,plan)
    print('Prepared',len(directory),'institutions,',len(works),'object decisions; new artworks',sum(not r['existing_id'] for r in works),'SHA256',hashlib.sha256(PLAN.read_bytes()).hexdigest())

def validate(plan):
    for ref in plan['evidence']:assert hashlib.sha256((m.ROOT/ref['path']).read_bytes()).hexdigest()==ref['sha256'],ref['path']
    receipts={r['receipt']['sha256']:r['receipt'] for r in plan['institutions']+plan['artworks']+plan['venues']}
    for r in receipts.values():check_receipt(r)
    assert len({r['id'] for r in plan['institutions']})==len(plan['institutions'])
    assert len({r['key'] for r in plan['artworks']})==len(plan['artworks'])
    for r in plan['artworks']:
        assert r['creator'] and r['confidence']>=.8 and r['institution_key'] in {x['key'] for x in plan['institutions']}
        assert r['source_url'].startswith('https://')
        if r['date_precision']=='unknown':assert r['first'] is None and r['last'] is None
        else:assert r['first'] is not None and r['last'] is not None and r['first']<=r['last']<=1970

def unchanged(db,plan,after=False):
    baseline=m.load(m.RUN/'application-baseline.json.gz');ids=[x['row']['id'] for x in baseline['artworks']]
    inst={r['key']:r for r in plan['institutions']}
    expected=copy.deepcopy(baseline['artworks'])
    if after:
        for x in expected:
            if x['row']['id']==CALDECOTT:x['row']['current_institution_id']=inst['iziko']['id']
    actual=rows(db,'artworks',ids)
    assert {x['row']['id']:x['row'] for x in actual}=={x['row']['id']:x['row'] for x in expected},'Existing artwork metadata changed'
    for table in ['artwork_artists','artwork_media']:
        assert rows(db,table,ids,'artwork_id')==baseline[table],table
    before_c=baseline['citations'];current=db.execute("SELECT to_jsonb(c) row FROM citations c WHERE id=ANY(%s::uuid[]) ORDER BY id",([x['row']['id'] for x in before_c],)).fetchall()
    assert current==before_c,'Existing citations changed'
    old_locations=baseline['artwork_location_assertions'];assert rows(db,'artwork_location_assertions',[x['row']['id'] for x in old_locations])==old_locations,'Existing location assertion changed'
    for prior in baseline['institutions']:
        expected=copy.deepcopy(prior)
        if after:expected['place_id']=inst['iziko']['place_id']
        actual=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s',(prior['id'],)).fetchone()['row']
        assert actual==expected,'Existing institution fields changed'
    assert rows(db,'artists',[x['row']['id'] for x in baseline['artists']])==baseline['artists'],'Existing artist changed'
    return len(ids)

def citation(db,r,entity,digest):
    aid=r.get('existing_id') or r['id'];note=dict(plan_sha256=digest,decision=r,policy='Review catalogue research; holdings are not current display.')
    db.execute('''INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',(m.uid('citation/'+entity+'/'+r['key']),entity,aid,FIELD,source_id(r),r['key'],r['source_url'],json.dumps(note,ensure_ascii=False),r['receipt']['retrieved_at'],m.ACTOR))

def verify(db,plan,digest):
    protected=unchanged(db,plan,True);inst={r['key']:r for r in plan['institutions']};works=plan['artworks'];ids=[r.get('existing_id') or r['id'] for r in works]
    actual={x['row']['id']:x['row'] for x in rows(db,'artworks',ids)}
    for r in plan['institutions']:
        i=db.execute('SELECT * FROM institutions WHERE id=%s',(r['id'],)).fetchone()
        assert str(i['place_id'])==r['place_id']
        if not r['existing']:assert i['name']==r['name'] and i['kind']==r['kind'] and i['status']=='review' and i['slug']==r['slug']
    cites=db.execute('SELECT entity_type,entity_id::text,evidence_note,source_url,source_id::text FROM citations WHERE field_name=%s',(FIELD,)).fetchall()
    byc={(r['entity_type'],r['entity_id']):r for r in cites};assert len(byc)==len(cites)==len(works)+len(inst)
    for r in plan['institutions']+works:
        typ='artwork' if 'creator' in r else 'institution';aid=r.get('existing_id') or r['id'];c=byc[(typ,aid)]
        assert c['source_id']==source_id(r) and c['source_url']==r['source_url']
        assert json.loads(c['evidence_note'])['decision']==r and json.loads(c['evidence_note'])['plan_sha256']==digest
    for r in works:
        aid=r['existing_id'] or r['id'];a=actual[aid]
        assert a['current_institution_id']==inst[r['institution_key']]['id']
        if not r['existing_id']:
            for col,key in FIELDS.items():assert a[col]==r[key],(r['key'],col)
            assert a['normalized_title']==m.norm(r['title']) and a['slug']==r['slug']
            assert a['status']=='review' and a['research_candidate'] and a['published_at'] is None and a['primary_media_id'] is None and a['location_checked_at'] is None
        loc=db.execute('SELECT * FROM artwork_location_assertions WHERE id=%s',(m.uid('holding/'+r['key']),)).fetchone()
        assert str(loc['artwork_id'])==aid and str(loc['institution_id'])==inst[r['institution_key']]['id'] and loc['claim_type']=='holding' and loc['review_state']=='accepted' and loc['superseded_by'] is None and loc['display_state'] is None and loc['venue_id'] is None
        assert loc['source_url']==r['source_url'] and str(loc['source_id'])==source_id(r)
        ex=db.execute('SELECT * FROM external_identifiers WHERE scheme=%s AND external_id=%s',(SCHEME,r['key'])).fetchone()
        assert str(ex['entity_id'])==aid and ex['canonical_url']==r['source_url']
    new=[r for r in works if not r['existing_id']];newids=[r['id'] for r in new]
    links=db.execute('SELECT artwork_id::text,artist_id::text FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(newids,)).fetchall()
    assert {(r['artwork_id'],r['artist_id']) for r in links}=={(r['id'],r['artist_id']) for r in new if r['artist_id']}
    assert not db.execute('SELECT 1 FROM artwork_media WHERE artwork_id=ANY(%s::uuid[]) LIMIT 1',(newids,)).fetchone()
    scopes=db.execute('SELECT artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,count(*) n,bool_and(artline_has_selection_evidence(id)) selected FROM artworks WHERE id=ANY(%s::uuid[]) GROUP BY 1',(newids,)).fetchall()
    assert sum(r['n'] for r in scopes)==len(new) and all(r['selected'] for r in scopes)
    eligible=next(r['n'] for r in scopes if r['scope']=='eligible');assert eligible==sum(r['first'] is not None for r in new)
    for v in plan['venues']:
        a=db.execute('SELECT * FROM institution_venues WHERE id=%s',(v['id'],)).fetchone()
        assert a['name']==v['name'] and a['status']=='review' and str(a['place_id'])==v['place_id'] and str(a['institution_id'])==inst[v['institution_key']]['id']
    return dict(new_institutions=sum(not r['existing'] for r in plan['institutions']),new_artworks=len(new),existing_artworks_linked=sum(bool(r['existing_id']) for r in works),artist_links=len(links),new_venues=len(plan['venues']),countries=len({r['country'] for r in plan['institutions']}),protected_existing_artworks=protected,new_artwork_scope=scopes,artworks_by_country=dict(collections.Counter(inst[r['institution_key']]['country'] for r in new)),institutions_by_country=dict(collections.Counter(r['country'] for r in plan['institutions'])),new_images=0,published=0,display_claims=0)

def apply(expected):
    plan=m.load(PLAN);digest=hashlib.sha256(PLAN.read_bytes()).hexdigest();assert expected==digest;validate(plan)
    with m.connect(True) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1']
        exists=db.execute('SELECT 1 FROM citations WHERE field_name=%s LIMIT 1',(FIELD,)).fetchone()
        if exists:
            result=verify(db,plan,digest);print('Verified unchanged replay; zero writes',json.dumps(result));return
        unchanged(db,plan)
        new=[r for r in plan['artworks'] if not r['existing_id']]
        assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[]) OR slug=ANY(%s) LIMIT 1',([r['id'] for r in new],[r['slug'] for r in new])).fetchone()
        assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR scheme=%s) LIMIT 1",([r['source_url'] for r in plan['artworks']],SCHEME)).fetchone()
        assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) LIMIT 1",([r['source_url'] for r in plan['artworks']],)).fetchone()
        m.save(m.BACKUP/'preimages.json.gz',m.load(m.RUN/'application-baseline.json.gz'));m.save(m.BACKUP/'reviewed-plan.json.gz',plan)
        for r in plan['countries']:db.execute('INSERT INTO countries(code,name,region_code) VALUES(%s,%s,%s)',(r['code'],r['name'],r['region_code']))
        for r in plan['places']:db.execute('INSERT INTO places(id,name,normalized_name,country_code) VALUES(%s,%s,%s,%s)',(r['id'],r['name'],r['normalized_name'],r['country_code']))
        for r in plan['sources']:db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(r['id'],r['slug'],r['name'],r['source_type'],r['base_url']))
        inst={r['key']:r for r in plan['institutions']}
        for r in plan['institutions']:
            if r['existing']:db.execute('UPDATE institutions SET place_id=%s WHERE id=%s AND place_id IS NULL',(r['place_id'],r['id']))
            else:db.execute("INSERT INTO institutions(id,slug,name,normalized_name,place_id,website_url,kind,status,description) VALUES(%s,%s,%s,%s,%s,%s,%s,'review',%s)",(r['id'],r['slug'],r['name'],m.norm(r['name']),r['place_id'],r['source_url'],r['kind'],r['note']))
            citation(db,r,'institution',digest)
        for v in plan['venues']:db.execute("INSERT INTO institution_venues(id,institution_id,slug,name,place_id,visit_url,source_url,checked_at,status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'review')",(v['id'],inst[v['institution_key']]['id'],v['slug'],v['name'],v['place_id'],v['visit_url'],v['source_url'],v['receipt']['retrieved_at']))
        for r in plan['artworks']:
            aid=r['existing_id'] or r['id']
            if not r['existing_id']:
                db.execute('''INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,created_by,updated_by)
                  VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s)''',(aid,r['slug'],r['title'],m.norm(r['title']),r['date_display'],r['first'],r['last'],r['date_precision'],r['work_type'],r['medium'],r['dimensions'],r['accession'],r['creator'],m.ACTOR,m.ACTOR))
                if r['artist_id']:db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",(aid,r['artist_id'],r['artist_basis']+' Source label: '+r['creator']))
            citation(db,r,'artwork',digest)
            db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,SCHEME,r['key'],r['source_url'],source_id(r),r['receipt']['retrieved_at']))
            note=r['review_note']+' '+r['identity_basis']+' Confidence '+str(r['confidence'])+' (editorial, not probability). SHA256 '+r['receipt']['sha256']
            db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(m.uid('holding/'+r['key']),aid,inst[r['institution_key']]['id'],source_id(r),r['source_url'],note,r['receipt']['retrieved_at']))
        result=verify(db,plan,digest)
    m.save(m.RUN/'applied.json',dict(at=m.now(),plan_sha256=digest,local_only=True,backup_path=str(m.BACKUP),verification=result));print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');a=p.parse_args()
    if a.command=='prepare':prepare()
    elif a.command=='apply':apply(a.plan_sha)
    else:
        plan=m.load(PLAN);validate(plan)
        with m.connect() as db:print(json.dumps(verify(db,plan,hashlib.sha256(PLAN.read_bytes()).hexdigest()),indent=2))
