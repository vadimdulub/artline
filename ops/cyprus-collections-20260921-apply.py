#!/usr/bin/env python3
"""Apply a pinned, validated metadata selection to the real local catalogue only."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

spec=importlib.util.spec_from_file_location('cyprus_review',Path(__file__).with_name('cyprus-collections-20260921-review.py'))
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
core=review.core
ACTOR='local-european-research'
SOURCE='cyprus-collections-20260921'
INSTITUTIONS={
 'xeniartspace':dict(name='XeniArtSpace',kind='foundation',place='Limassol',url='https://xeniartspace.com/collection',website='https://xeniartspace.com/',
    description='XeniArtSpace Foundation collection and exhibition spaces in Limassol. Object-level permanent membership must be distinguished from exhibition participation.'),
 'boccf':dict(name='Bank of Cyprus Cultural Foundation',kind='foundation',place='Nicosia',
    url='https://www.boccf.org/en-gb/homepage/museums-collections2/sulloge-sugkhrones-kupriakes-tekhnes/sulloge/',website='https://www.boccf.org/',
    description='Cultural foundation with a contemporary Cypriot art collection; individual source-documented works selected for owner research.'),
 'saint-neophytos-monastery':dict(name='Monastery of Saint Neophytos',kind='historic_site',place='Paphos',
    url='https://apsida.cut.ac.cy/items/show/21943',website=None,
    description='Enkleistra, monastery church and museum represented in Cyprus University of Technology archival documentation.'),
 'kykkos-monastery-museum':dict(name='Museum of Kykkos Monastery',kind='museum',place=None,
    url='https://apsida.cut.ac.cy/items/show/15548',website=None,
    description='Monastery museum documented as a contributor to the Cyprus University of Technology digital archive.'),
}


def insert(db,table,fields):
    columns=list(fields)
    db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),
       sql.SQL(',').join(map(sql.Identifier,columns)),sql.SQL(',').join(sql.Placeholder() for _ in columns)),[fields[k] for k in columns])


def load():
    raw=(core.RUN/'application-plan.json').read_bytes()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()


def validate_plan(plan):
    assert plan['local_only'] and plan['cutoff']==1970 and plan['status']=='review'
    assert not any(d['decision']=='identity_check' for d in plan['decisions'])
    for kind in ('artists','works'):
        assert len({x['id'] for x in plan[kind]})==len(plan[kind]),'Duplicate IDs'
        assert len({x['slug'] for x in plan[kind]})==len(plan[kind]),'Duplicate slugs'
    for a in plan['artists']:
        assert a['first']<=a['last'] and a['last']<=2026
        assert not a['death'] or a['birth']<=a['death']
        assert a['entity_type'] in ('person','anonymous_master')
    for w in plan['works']:
        d=w['date'];assert w['title'] and w['url'].startswith('https://')
        assert d['first'] is None or (d['first']<=d['last']<=1970)
        assert (d['first'] is None)==(d['precision']=='unknown')
        assert w['object_form']!='icon' or w['work_type']=='painting'
        if w['scheme']=='apsida-item' and int(w['source_id'])>=45216:assert d['first']!=2006
        assert bool(w['artist_id']) or bool(w['creator_label'])
    for x in [*plan['artists'],*plan['works']]:
        c=x['receipt'];p=core.ROOT/c['path']
        assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==c['sha256'],'Evidence checksum mismatch'
    return {'artists':len(plan['artists']),'new_artists':sum(not a['existing'] for a in plan['artists']),
       'works':len(plan['works']),'new_works':sum(not w['existing'] for w in plan['works']),
       'unknown_dates':sum(w['date']['precision']=='unknown' for w in plan['works']),
       'frescoes':sum(w['work_type']=='fresco' for w in plan['works']),
       'icons':sum(w['object_form']=='icon' for w in plan['works'])}


def backup():
    plan,pin=load();validate_plan(plan)
    core.BACKUP.mkdir(parents=True,exist_ok=True)
    path=core.BACKUP/'local-before.dump'
    assert not path.exists(),'Preserve existing backup; reconcile before another application'
    with path.open('xb') as output:
        subprocess.run(['pg_dump','--dbname',core.DSN,'--format=custom','--no-owner','--no-privileges'],stdout=output,check=True)
    result=subprocess.run(['pg_restore','--list',str(path)],capture_output=True,check=True)
    assert b'TABLE DATA public artworks' in result.stdout and b'TABLE DATA public artists' in result.stdout
    receipt=dict(at=core.now(),path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size,plan_sha256=pin)
    core.save(core.RUN/'local-backup.json',receipt)
    print(json.dumps(receipt))


def citation(db,sid,kind,ident,field,url,data,checked=None):
    insert(db,'citations',dict(entity_type=kind,entity_id=ident,field_name=field,source_id=sid,source_url=url,
        source_record_id=str(data.get('source_id') or data.get('key') or data.get('name') or ident),
        evidence_note=json.dumps(data,ensure_ascii=False,default=str),retrieved_at=checked or core.now(),created_by=ACTOR))


def apply(expected):
    plan,pin=load();assert pin==expected,'Plan changed';summary=validate_plan(plan)
    assert not (core.RUN/'applied.json').exists(),'Already applied; verification is read-only'
    receipt=json.loads((core.RUN/'local-backup.json').read_text())
    assert receipt['plan_sha256']==pin
    assert hashlib.sha256(Path(receipt['path']).read_bytes()).hexdigest()==receipt['sha256']
    with psycopg.connect(core.DSN,row_factory=dict_row) as db:
        db.execute("SET LOCAL lock_timeout='10s'");db.execute("SET LOCAL statement_timeout='30s'")
        db.execute('SELECT pg_advisory_xact_lock(559220260915)')
        assert db.execute("SELECT current_database() db,inet_server_addr() addr,inet_server_port() port").fetchone()['db']=='artline'
        owner=db.execute("SELECT * FROM curated_collections WHERE id=%s FOR UPDATE",(plan['owner_collection_id'],)).fetchone()
        assert owner['curator_kind']=='owner' and owner['institution_id'] is None and owner['status']=='review'
        artist_ids=[a['id'] for a in plan['artists'] if a['existing']]
        before_artists=db.execute('SELECT * FROM artists WHERE id=ANY(%s::uuid[])',(artist_ids,)).fetchall()
        assert len(before_artists)==len(artist_ids)
        before_relations=db.execute('SELECT * FROM artist_countries WHERE artist_id=ANY(%s::uuid[])',(artist_ids,)).fetchall()
        # Reconcile again under the ingestion lock; never swallow identity conflicts.
        for a in plan['artists']:
            if a['existing']:continue
            names=[review.norm(n) for n in [a['name'],*a['aliases']]]
            assert not db.execute("SELECT id FROM artists WHERE id=%s OR slug=%s OR normalized_name=ANY(%s)",(a['id'],a['slug'],names)).fetchone(),a['name']
            assert not db.execute('SELECT id FROM artist_aliases WHERE normalized_alias=ANY(%s)',(names,)).fetchone(),a['name']
        for w in plan['works']:
            if w['existing']:
                assert db.execute('SELECT id FROM artworks WHERE id=%s',(w['id'],)).fetchone();continue
            assert not db.execute('SELECT id FROM artworks WHERE id=%s OR slug=%s',(w['id'],w['slug'])).fetchone(),w['key']
            assert not db.execute("SELECT id FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(w['scheme'],w['source_id'])).fetchone(),w['key']
        core.save(core.BACKUP/('transaction-preimages-'+core.datetime.now(core.timezone.utc).strftime('%H%M%S%f')+'.json'),dict(at=core.now(),plan_sha256=pin,owner=owner,
           existing_artists=before_artists,existing_artist_countries=before_relations,
           new_artist_ids=[a['id'] for a in plan['artists'] if not a['existing']],new_artwork_ids=[w['id'] for w in plan['works'] if not w['existing']]))
        db.execute("INSERT INTO sources(slug,name,source_type,base_url) VALUES(%s,%s,'collection_page','https://apsida.cut.ac.cy/') ON CONFLICT(slug) DO NOTHING",
                   (SOURCE,'Cyprus and XeniArtSpace: owner-requested, source-documented metadata review'))
        sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
        institutions={}
        for key,i in INSTITUTIONS.items():
            found=db.execute('SELECT * FROM institutions WHERE slug=%s OR normalized_name=%s',(key,review.norm(i['name']))).fetchall()
            assert len(found)<=1
            if found:institutions[key]=str(found[0]['id']);continue
            pid=None
            if i['place']:
                places=db.execute('SELECT id FROM places WHERE normalized_name=%s AND country_code=%s',(review.norm(i['place']),'CY')).fetchall()
                assert len(places)<=1
                pid=str(places[0]['id']) if places else review.uid('place:'+i['place'])
                if not places:insert(db,'places',dict(id=pid,name=i['place'],normalized_name=review.norm(i['place']),country_code='CY'))
            iid=review.uid('institution:'+key);institutions[key]=iid
            insert(db,'institutions',dict(id=iid,slug=key,name=i['name'],normalized_name=review.norm(i['name']),place_id=pid,
                 website_url=i['website'],kind=i['kind'],status='review',description=i['description']))
            citation(db,sid,'institution',iid,'institution_identity',i['url'],i)
        for a in plan['artists']:
            if not a['existing']:
                biography=('Cyprus-associated artist. ' if a['relationship'] else '')+a['note']+'\n\n[Research source]('+a['url']+').'
                insert(db,'artists',dict(id=a['id'],slug=a['slug'],display_name=a['name'],sort_name=a['name'],normalized_name=review.norm(a['name']),
                   entity_type=a['entity_type'],birth_year=a['birth'],death_year=a['death'],timeline_start_year=a['first'],timeline_end_year=a['last'],
                   timeline_basis=a['basis'],timeline_display=a['display'],active_start_year=a['first'] if a['basis']=='activity' else None,
                   active_end_year=a['last'] if a['basis']=='activity' else None,activity_display=a['display'] if a['basis']=='activity' else None,
                   biography_md=biography,status='review',created_by=ACTOR,updated_by=ACTOR))
                seen_aliases=set()
                for name in [a['name'],*a['aliases']]:
                    if review.norm(name) in seen_aliases:continue
                    seen_aliases.add(review.norm(name))
                    insert(db,'artist_aliases',dict(artist_id=a['id'],alias=name,normalized_alias=review.norm(name),alias_type='alternate'))
            if a['relationship'] and not db.execute("SELECT 1 FROM artist_countries WHERE artist_id=%s AND country_code='CY' AND relationship_type=%s",(a['id'],a['relationship'])).fetchone():
                insert(db,'artist_countries',dict(artist_id=a['id'],country_code='CY',relationship_type=a['relationship'],is_primary=False,
                    note='Explicit source evidence: '+a['url']+'. '+a['note']))
            citation(db,sid,'artist',a['id'],'cyprus_collection_research',a['url'],a,a['receipt']['retrieved_at'])
        cyplace=review.uid('place:Cyprus (unspecified locality)')
        found=db.execute("SELECT id FROM places WHERE normalized_name='cyprus' AND country_code='CY'").fetchall()
        assert len(found)<=1
        if found:cyplace=str(found[0]['id'])
        else:insert(db,'places',dict(id=cyplace,name='Cyprus',normalized_name='cyprus',country_code='CY'))
        for w in plan['works']:
            if w['existing']:continue
            d=w['date'];description=w['connection']+'.'
            if w['notes']:description+='\n\n'+' '.join(w['notes'])
            description+='\n\n[Source record]('+w['url']+').'
            insert(db,'artworks',dict(id=w['id'],slug=w['slug'],title=w['title'],alternate_title=w.get('alternate_title'),normalized_title=review.norm(w['title']),
                 date_display=d['display'],creation_year_start=d['first'],creation_year_end=d['last'],date_precision=d['precision'],
                 work_type=w['work_type'],object_form=w['object_form'],medium_text=w['medium'],dimensions_text=w['dimensions'],
                 unlinked_creator_label=w['creator_label'] if not w['artist_id'] else None,cultural_context=w['cultural_context'],
                 description_md=description,creation_place_display='Cyprus' if w['creation_country'] else None,
                 current_institution_id=None,status='review',research_candidate=True,created_by=ACTOR,updated_by=ACTOR))
            if w['artist_id']:insert(db,'artwork_artists',dict(artwork_id=w['id'],artist_id=w['artist_id'],attribution_role='primary',
                            attribution_note='Object-specific source attribution; no inference from archive photographer or digital record creator.'))
            if w['creation_country']:insert(db,'artwork_places',dict(artwork_id=w['id'],place_id=cyplace,relationship_type='created',
                 note='In-situ wall painting documented at a Cyprus church; exact source placement retained in the citation.'))
            insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=w['id'],scheme=w['scheme'],external_id=w['source_id'],
                   canonical_url=w['url'],source_id=sid,retrieved_at=w['receipt']['retrieved_at']))
            citation(db,sid,'artwork',w['id'],'cyprus_object_identity',w['url'],w,w['receipt']['retrieved_at'])
            # No accepted holding or display claims are created by this research import.
        selections={w['id']:w for w in [*plan['existing_selection'],*plan['works']]}
        position=db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s',(owner['id'],)).fetchone()['n']
        added=[]
        for wid,w in selections.items():
            if db.execute('SELECT id FROM curated_collection_items WHERE collection_id=%s AND artwork_id=%s',(owner['id'],wid)).fetchone():continue
            position+=1
            insert(db,'curated_collection_items',dict(collection_id=owner['id'],artwork_id=wid,position=position,
                reason='Owner requested Cyprus painters, frescoes and icons, plus XeniArtSpace review. Personal research selection; not ownership, publication or museum masterpiece designation.',
                source_id=sid,source_url=w['url'],checked_at=core.now()))
            added.append(wid)
        # An owner research selection associated with the institution, explicitly not its permanent inventory.
        xeni_collection=review.uid('collection:xeniartspace-owner-research')
        insert(db,'curated_collections',dict(id=xeni_collection,institution_id=institutions['xeniartspace'],curator_kind='owner',
                 title='XeniArtSpace — personal research selection',status='review'))
        xeniworks=[w for w in plan['works'] if w['institution']=='xeniartspace']
        for n,w in enumerate(xeniworks,1):
            insert(db,'curated_collection_items',dict(collection_id=xeni_collection,artwork_id=w['id'],position=n,
                reason=w['connection']+'. Permanent collection membership and current display not established for this work.',source_id=sid,source_url=w['url'],checked_at=core.now()))
        citation(db,sid,'institution',institutions['xeniartspace'],'permanent_collection_review','https://xeniartspace.com/collection',
             {'verified_permanent_acquisitions_outside_cutoff':[{'creator':'Anish Kapoor','title':'Untitled','year':2007},
              {'creator':'Anish Kapoor','title':'Spanish and Pagan Gold to Cobalt Blue','year':2019}],
              'acquisition_source':'https://cyprus-mail.com/2025/02/26/xeniartspace-gallery-exhibits-two-works-by-famed-sculptor-anish-kapoor',
              'decision':'Retained as research evidence; not inserted as artwork records under the existing 1970 cutoff.',
              'inventory_limit':'Official collection pages and audio guide do not expose a complete object-level inventory.'})
        db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(owner['id'],))
        # Preserve existing artist metadata exactly, including any previous editorial status.
        after=db.execute('SELECT * FROM artists WHERE id=ANY(%s::uuid[])',(artist_ids,)).fetchall()
        assert sorted(after,key=lambda a:str(a['id']))==sorted(before_artists,key=lambda a:str(a['id']))
        newids=[w['id'] for w in plan['works'] if not w['existing']]
        check=db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND status='review' AND research_candidate AND published_at IS NULL AND primary_media_id IS NULL",(newids,)).fetchone()
        assert check['n']==len(newids)
        assert not db.execute('SELECT id FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[])',(newids,)).fetchone()
        result=dict(at=core.now(),plan_sha256=pin,summary=summary,new_personal_selections=len(added),added_selection_ids=added,
            institution_ids=institutions,xeni_collection_id=xeni_collection,xeni_work_ids=[w['id'] for w in xeniworks],local_only=True,
            new_artwork_ids=newids,new_artist_ids=[a['id'] for a in plan['artists'] if not a['existing']])
    core.save(core.RUN/'applied.json',result)
    print(json.dumps({k:v for k,v in result.items() if not isinstance(v,list)},default=str))


def verify():
    plan,pin=load();receipt=json.loads((core.RUN/'applied.json').read_text());assert pin==receipt['plan_sha256']
    with psycopg.connect(core.DSN,options='-c default_transaction_read_only=on -c statement_timeout=15000',row_factory=dict_row) as db:
        rows=db.execute("""SELECT a.id::text,a.title,a.status,a.published_at,a.primary_media_id,a.date_precision,a.work_type,a.object_form,
          artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) creation_scope,
          EXISTS(SELECT 1 FROM curated_collection_items ci WHERE ci.collection_id=%s AND ci.artwork_id=a.id) selected,
          EXISTS(SELECT 1 FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id AND c.created_by=%s) cited
          FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id""",(plan['owner_collection_id'],ACTOR,receipt['new_artwork_ids'])).fetchall()
        assert len(rows)==len(receipt['new_artwork_ids'])
        assert all(w['status']=='review' and not w['published_at'] and not w['primary_media_id'] and w['selected'] and w['cited'] for w in rows)
        assert db.execute("SELECT count(*) n FROM artists WHERE id=ANY(%s::uuid[]) AND status='review'",(receipt['new_artist_ids'],)).fetchone()['n']==len(receipt['new_artist_ids'])
        allids=list({w['id'] for w in [*plan['works'],*plan['existing_selection']]})
        assert db.execute('SELECT count(*) n FROM curated_collection_items WHERE collection_id=%s AND artwork_id=ANY(%s::uuid[])',(plan['owner_collection_id'],allids)).fetchone()['n']==len(allids)
        assert db.execute('SELECT count(*) n FROM curated_collection_items WHERE collection_id=%s',(receipt['xeni_collection_id'],)).fetchone()['n']==5
        totals=db.execute("""SELECT (SELECT count(DISTINCT artist_id) FROM artist_countries WHERE country_code='CY') artists,
          (SELECT count(*) FROM artworks WHERE id=ANY(%s::uuid[])) reviewed_selection""",(allids,)).fetchone()
    path=core.RUN/'verification.json'
    if not path.exists():core.save(path,dict(at=core.now(),plan_sha256=pin,checks_passed=True,totals=totals,new_works=rows))
    else:assert json.loads(path.read_text())['plan_sha256']==pin, 'Preserved verification belongs to a different selection'
    print(json.dumps({'verified':len(rows),'totals':totals}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['validate','backup','apply','verify']);parser.add_argument('--plan-sha256')
    args=parser.parse_args()
    if args.stage=='validate':
        plan,pin=load();print(json.dumps({'plan_sha256':pin,**validate_plan(plan)}))
    elif args.stage=='backup':backup()
    elif args.stage=='apply':apply(args.plan_sha256)
    else:verify()
