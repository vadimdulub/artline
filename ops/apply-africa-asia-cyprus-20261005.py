#!/usr/bin/env python3
"""Pinned, backed-up local review import for the selected regional research."""
import collections
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import uuid
import concurrent.futures
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('regional_research',ROOT/'ops/research-africa-asia-cyprus-20261005.py')
r=importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
RUN=r.RUN
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/RUN.name
ACTOR='local-european-research'
SOURCE=RUN.name
DSN='postgres://localhost/artline'


def read(path):return json.loads(path.read_text())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/'+SOURCE+'/'+key))
def slug(value):return re.sub(r'[^a-z0-9]+','-',r.norm(value)).strip('-')


def canonical_name(value):
    value=re.sub(r'\s*\([^)]*\)\s*','',value).strip()
    if ',' in value:
        surname,given=value.split(',',1)
        value=given.strip()+' '+surname.strip()
    return value


def plan():
    assert not (RUN/'application-plan.json').exists(),'Plan already pinned'
    sel=read(RUN/'selection.json');cy=read(RUN/'cyprus-selection.json')
    works=[read(RUN/'objects'/(x['source_id']+'.json')) for x in sel['works']]+cy['works']
    profiles={a['profile']['name']:a['profile'] for a in sel['artists']}
    profiles.update({a['name']:dict(name=a['name'],slug=a['source_slug'],source_url=a['profile_url'],
                                  birth=a['birth'],death=a['death'],receipt=a['receipt']) for a in cy['artists']})
    # Explicit cross-source name reconciliation. Museum and catalogue lifespans
    # are retained independently when they disagree (Loukia: 1993 vs 1994).
    aliases={'Nikolaidou, Loukia (1909-1993)':'Loukia Nicolaides-Vassiliou',
             'Georgiou, George Pol (1901-1972)':'George Pol. Georghiou',
             'Georghiou, George Pol (1901-1972)':'George Pol. Georghiou'}
    artists={};held=[];ready=[];identity_audit=[]
    resolutions=read(RUN/'identity-resolutions.json') if (RUN/'identity-resolutions.json').exists() else {}
    rejected_images=read(RUN/'rejected-images.json') if (RUN/'rejected-images.json').exists() else {}
    repeated=collections.Counter((w['artist_name'],r.norm(w['title'])) for w in works)
    with r.readonly() as db:
        # Bounded artist-name inventory for alias/token reconciliation; artwork
        # enrichment below remains scoped by the resolved creator IDs.
        catalogue=db.execute("""SELECT id::text,display_name,slug,birth_year,death_year,status,
          coalesce((SELECT jsonb_agg(alias) FROM artist_aliases al WHERE al.artist_id=a.id),'[]') aliases FROM artists a""").fetchall()
        names=collections.defaultdict(dict)
        for a in catalogue:
            for name in [a['display_name'],*a['aliases']]:
                names[' '.join(sorted(r.norm(name).split()))][a['id']]=a
        current_owner=db.execute("SELECT * FROM curated_collections WHERE curator_kind='owner' AND institution_id IS NULL").fetchall()
        assert len(current_owner)==1
        image_sources={x.stem:read(x) for x in (RUN/'images').glob('*.json')}
        for name in dict.fromkeys(w['artist_name'] for w in works):
            display=aliases.get(name,canonical_name(name))
            matches=list(names[' '.join(sorted(r.norm(display).split()))].values())
            p=profiles.get(name)
            if p:
                exact=db.execute("""SELECT entity_id::text FROM external_identifiers WHERE entity_type='artist'
                    AND (canonical_url=%s OR (scheme='wikiart-artist' AND external_id=%s))""",(p['source_url'],p['slug'])).fetchall()
                if exact:
                    exact_ids={x['entity_id'] for x in exact}
                    matches=[x for x in catalogue if x['id'] in exact_ids]
            if len(matches)>1:
                identity_audit.append(dict(name=name,outcome='ambiguous',matches=matches));continue
            if matches:
                a=dict(id=matches[0]['id'],display_name=matches[0]['display_name'],existing=True,profile=p,
                       baseline=matches[0],source_name=name)
            elif p:
                # Close surnames are candidates for manual reconciliation, not
                # automatic new authorities or automatic merges.
                last=r.norm(display).split()[-1]
                near=[x for x in catalogue if last in r.norm(x['display_name']).split()]
                resolved=resolutions.get(name)
                if near and not (resolved and set(resolved['distinct_from'])=={x['id'] for x in near}):
                    identity_audit.append(dict(name=name,outcome='possible_existing',matches=near));continue
                cohort=[w for w in works if w['artist_name']==name]
                def year(value):
                    m=re.search(r'(?<!\d)(\d{3,4})$',str(value or ''))
                    return int(m[1]) if m else None
                birth,death=year(p.get('birth')),year(p.get('death'))
                start=min(w['date']['creation_year_start'] for w in cohort)
                end=max(w['date']['creation_year_end'] for w in cohort)
                assert birth is None or birth<=start,(name,birth,start)
                a=dict(id=uid('artist/'+p['source_url']),slug='regional-'+slug(display)+'-'+uid(p['source_url'])[:8],
                       display_name=display,existing=False,profile=p,source_name=name,birth_year=birth,death_year=death,
                       timeline_start_year=birth if birth is not None and death is not None else start,
                       timeline_end_year=death if birth is not None and death is not None else end,
                       timeline_basis='life' if birth is not None and death is not None else 'activity')
            else:
                # Keep incomplete museum creator labels at object level.
                a=dict(id=None,display_name=display,existing=False,object_level=True,profile=None,source_name=name)
            artists[name]=a
            identity_audit.append(dict(name=name,outcome='object_label' if a.get('object_level') else ('existing' if a['existing'] else 'new'),id=a['id']))
        for w in works:
            reason=None
            if w.get('page_outcome') not in (None,'verified'):reason='unverified_object'
            elif '(detail)' in w['title'].casefold():reason='detail_view_not_additional_artwork'
            elif repeated[(w['artist_name'],r.norm(w['title']))]>1:reason='same_artist_title_needs_composition_review'
            elif w['artist_name'] not in artists:reason='artist_identity_needs_review'
            a=artists.get(w['artist_name'])
            existing=[]
            if not reason and a and a['id'] and a['existing']:
                rows=db.execute("""SELECT a.id::text,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end FROM artwork_artists aa
                  JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s""",(a['id'],)).fetchall()
                existing=[x for x in rows if r.norm(w['title']) in {r.norm(x['title']),r.norm(x['alternate_title'])}]
                if existing:reason='existing_artist_title_after_alias_reconciliation'
            if reason:
                held.append(dict(work=w,reason=reason,existing=existing));continue
            w=dict(w,id=uid('artwork/'+w['source_id']),slug='regional-'+slug(w['title'])[:80]+'-'+uid(w['source_id'])[:10],
                   creator=a,image=None if w['source_id'] in rejected_images else image_sources.get(w['source_id']))
            if w['source_id'].startswith('leventis-'):
                w['work_type']={'Oil on canvas':'painting','Oil on wood':'painting','Watercolour':'watercolor'}.get(w['source_metadata'].get('medium'),'unknown')
                w['medium_text']=w['source_metadata'].get('medium')
            elif w['source_id'].startswith('cvar-'):
                fields=w['source_metadata']
                w['work_type']={'Oil Painting':'painting','Watercolour':'watercolor','Lithograph':'print','Poster':'print'}.get(fields.get('Object Type'),'unknown')
                w['medium_text']=fields.get('Medium')
            else:
                w['work_type']='unknown';w['medium_text']=None
            ready.append(w)
        used_names={w['artist_name'] for w in ready}
        assert len({w['source_id'] for w in ready})==len(ready)
        assert len({w['id'] for w in ready})==len(ready)
        assert len({w['source_url'] for w in ready})==len(ready)
        used=[a for name,a in artists.items() if name in used_names]
        geography=[]
        for a in used:
            if not a['id']:continue
            p=a['profile']
            countries=sorted({r.NATIONS[n] for n in (p or {}).get('nationalities',[]) if n in r.NATIONS})
            for country in countries:
                code=country[0]
                before=db.execute('SELECT * FROM artist_countries WHERE artist_id=%s AND country_code=%s',(a['id'],code)).fetchall()
                if not before:geography.append(dict(artist_id=a['id'],country=country,profile=p))
        result=dict(at=r.now(),works=ready,artists=used,held=held,identity_audit=identity_audit,geography=geography,
                    owner_collection_id=str(current_owner[0]['id']),sources=[dict(path=str(RUN/'selection.json'),sha256=digest(RUN/'selection.json')),
                    dict(path=str(RUN/'cyprus-selection.json'),sha256=digest(RUN/'cyprus-selection.json'))],
                    policy='Local review only. No publication, accepted holdings, display assertions, production writes, or guessed work types. All artwork dates <=1970.')
    r.save(RUN/'application-plan.json',result)
    print(json.dumps(dict(works=len(ready),artists=len(used),new_artists=sum(not a['existing'] and not a.get('object_level') for a in used),
                          object_labels=sum(bool(a.get('object_level')) for a in used),images=sum(bool(w['image']) for w in ready),
                          geography=len(geography),holds=dict(collections.Counter(x['reason'] for x in held)),
                          identity_holds=[x for x in identity_audit if x['outcome'] in ('possible_existing','ambiguous')])),flush=True)


def backup():
    assert (RUN/'application-plan.json').exists()
    BACKUP.mkdir(parents=True,exist_ok=True)
    path=BACKUP/'local-before.dump'
    if not (BACKUP/'backup.json').exists():
        assert not path.exists(),'Unvalidated partial backup needs inspection'
        subprocess.run(['pg_dump','--format=custom','--file='+str(path),DSN],check=True)
        result=subprocess.run(['pg_restore','--list',str(path)],check=True,capture_output=True)
        assert b'TABLE DATA public artworks' in result.stdout
        r.save(BACKUP/'archive-list.txt',result.stdout)
        r.save(BACKUP/'application-plan.json',(RUN/'application-plan.json').read_bytes())
        r.save(BACKUP/'backup.json',dict(at=r.now(),path=str(path),sha256=digest(path),bytes=path.stat().st_size,
                                      plan_sha256=digest(RUN/'application-plan.json')))
    print(read(BACKUP/'backup.json'),flush=True)


def insert(db,table,data):
    from psycopg import sql
    db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),
               sql.SQL(',').join(map(sql.Identifier,data)),sql.SQL(',').join(sql.Placeholder() for _ in data)),tuple(data.values()))


def citation(db,sid,entity,eid,field,url,evidence):
    insert(db,'citations',dict(entity_type=entity,entity_id=eid,field_name=field,source_id=sid,source_url=url,
                              retrieved_at=r.now(),created_by=ACTOR,evidence_note=json.dumps(evidence,ensure_ascii=False,default=str)))


def apply():
    assert not (RUN/'applied.json').exists(),'Already applied; run verification'
    plan_path=RUN/'application-plan.json';p=read(plan_path);backup=read(BACKUP/'backup.json')
    assert backup['plan_sha256']==digest(plan_path)
    assert digest(Path(backup['path']))==backup['sha256']
    approved=read(RUN/'visual-review.json')
    assert set(approved['approved_source_ids'])=={w['source_id'] for w in p['works'] if w['image']}
    # Prepare all served assets before touching the database, preserving originals.
    for w in p['works']:
        im=w['image']
        if not im:continue
        assert digest(ROOT/im['path'])==im['sha256'] and im['bytes']<=100000
        served='/assets/artworks/imported/'+SOURCE+'/'+w['source_id']+'.jpg'
        r.save(ROOT/'apps/web/public'/served.lstrip('/'),(ROOT/im['path']).read_bytes())
        im['storage_path']=served
    with psycopg.connect(DSN,row_factory=dict_row) as db:
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        assert db.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s',(ACTOR,)).fetchone()
        assert not db.execute('SELECT 1 FROM sources WHERE slug=%s',(SOURCE,)).fetchone()
        image_urls=[w['image']['source_image_url'] for w in p['works'] if w['image']]
        overlaps=db.execute('SELECT media_id::text,source_image_url FROM media_rights_evidence WHERE source_image_url=ANY(%s)',(image_urls,)).fetchall()
        if overlaps:
            r.save(RUN/'existing-image-overlaps.json',overlaps)
            raise ValueError('Selected reproduction already attached; reconcile before import')
        owner=db.execute('SELECT * FROM curated_collections WHERE id=%s FOR UPDATE',(p['owner_collection_id'],)).fetchone()
        assert owner and owner['curator_kind']=='owner' and owner['institution_id'] is None and owner['status']!='archived'
        before_artists=db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[]) FOR SHARE',
                                 ([a['id'] for a in p['artists'] if a['existing']],)).fetchall()
        before_countries=db.execute('SELECT * FROM artist_countries WHERE artist_id=ANY(%s::uuid[])',
                                   ([a['id'] for a in p['artists'] if a['id']],)).fetchall()
        for w in p['works']:
            assert not db.execute('SELECT id FROM artworks WHERE id=%s OR slug=%s',(w['id'],w['slug'])).fetchone()
            assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=%s",(w['source_url'],)).fetchone()
            assert not db.execute("SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=%s",(w['source_url'],)).fetchone()
            if w['creator']['existing']:
                titles=db.execute("""SELECT a.title,a.alternate_title FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
                                     WHERE aa.artist_id=%s""",(w['creator']['id'],)).fetchall()
                assert not any(r.norm(w['title']) in {r.norm(x['title']),r.norm(x['alternate_title'])} for x in titles),'Creator/title changed after selection'
        r.save(BACKUP/('preimages-'+r.now().replace(':','-')+'.json'),dict(at=r.now(),plan_sha256=digest(plan_path),
            owner_collection=owner,artists=before_artists,artist_countries=before_countries,new_artwork_ids=[w['id'] for w in p['works']],
            new_artist_ids=[a['id'] for a in p['artists'] if not a['existing'] and a['id']]))
        sid=uid('source')
        insert(db,'sources',dict(id=sid,slug=SOURCE,name='Africa, Asia and Cyprus: selected WikiArt and museum research, 5 October 2026',
                                source_type='collection_page',base_url='https://www.wikiart.org/'))
        for a in p['artists']:
            if a['existing'] or a.get('object_level'):continue
            assert not db.execute('SELECT id FROM artists WHERE normalized_name=%s OR slug=%s',(r.norm(a['display_name']),a['slug'])).fetchone()
            insert(db,'artists',dict(id=a['id'],slug=a['slug'],display_name=a['display_name'],sort_name=a['display_name'],
                normalized_name=r.norm(a['display_name']),entity_type='person',birth_year=a['birth_year'],death_year=a['death_year'],
                birth_display=str(a['birth_year']) if a['birth_year'] else None,death_display=str(a['death_year']) if a['death_year'] else None,
                birth_precision=('circa' if str(a['profile'].get('birth','')).startswith('c.') else 'exact') if a['birth_year'] else None,
                death_precision=('circa' if str(a['profile'].get('death','')).startswith('c.') else 'exact') if a['death_year'] else None,
                timeline_start_year=a['timeline_start_year'],timeline_end_year=a['timeline_end_year'],timeline_basis=a['timeline_basis'],
                timeline_display=('Life dates: ' if a['timeline_basis']=='life' else 'Documented selected works: ')+str(a['timeline_start_year'])+'–'+str(a['timeline_end_year']),
                status='review',created_by=ACTOR,updated_by=ACTOR))
            profile=a['profile']
            insert(db,'external_identifiers',dict(entity_type='artist',entity_id=a['id'],scheme='wikiart-artist',
                    external_id=profile['slug'],canonical_url=profile['source_url'],source_id=sid,retrieved_at=profile['receipt']['retrieved_at']))
            citation(db,sid,'artist',a['id'],'source_identity',profile['source_url'],profile)
        for g in p['geography']:
            code,name,region=g['country']
            if not db.execute('SELECT 1 FROM countries WHERE code=%s',(code,)).fetchone():
                insert(db,'countries',dict(code=code,name=name,region_code=region))
            exists=db.execute('SELECT 1 FROM artist_countries WHERE artist_id=%s AND country_code=%s',(g['artist_id'],code)).fetchone()
            if not exists:
                insert(db,'artist_countries',dict(artist_id=g['artist_id'],country_code=code,relationship_type='cultural_affiliation',
                    is_primary=False,note='WikiArt Nationality field retained as cultural affiliation for regional discovery; citizenship and birth country not inferred.'))
                citation(db,sid,'artist',g['artist_id'],'cultural_affiliation',g['profile']['source_url'],
                         dict(country_code=code,nationalities=g['profile']['nationalities'],receipt=g['profile']['receipt']))
        position=db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s',(p['owner_collection_id'],)).fetchone()['n']
        assert position+len(p['works'])<=100000
        for w in p['works']:
            a=w['creator'];im=w['image'];mid=uid('media/'+w['source_id']) if im else None
            if im:
                insert(db,'media_assets',dict(id=mid,storage_kind='local',storage_path=im['storage_path'],source_page_url=w['source_url'],
                    provider_name='WikiArt',mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],
                    checksum_sha256=im['sha256'],alt_text=w['title']+' — '+a['display_name'],rights_status='public_domain',
                    license_label='Public domain (WikiArt per-object label)',license_url='https://www.wikiart.org/en/terms-of-use',
                    creator_credit=a['display_name']+'; reproduction via WikiArt',attribution_text=im['rights_label'],retrieved_at=im['retrieved_at'],
                    verified_at=r.now(),verified_by=ACTOR))
                insert(db,'media_rights_evidence',dict(media_id=mid,source_id=sid,source_record_id=w['source_id'],
                    source_checksum=im['page_receipt']['sha256'],source_image_url=im['source_image_url'],policy_url='https://www.wikiart.org/en/terms-of-use',
                    rights_basis='Explicit WikiArt per-object public-domain label; no age-based clearance or independent legal determination.',
                    adapter_version=SOURCE,checked_at=im['page_receipt']['retrieved_at'],evidence_json=Jsonb(im)))
            insert(db,'artworks',dict(id=w['id'],slug=w['slug'],title=w['title'],normalized_title=r.norm(w['title']),**w['date'],
                work_type=w['work_type'],medium_text=w['medium_text'],primary_media_id=mid,status='review',research_candidate=True,
                unlinked_creator_label=a['source_name'] if a.get('object_level') else None,
                created_by=ACTOR,updated_by=ACTOR))
            if a['id']:
                insert(db,'artwork_artists',dict(artwork_id=w['id'],artist_id=a['id'],attribution_role='primary',
                    attribution_note='Named creator from captured source; identity and artwork remain in editorial review.'))
            if im:insert(db,'artwork_media',dict(artwork_id=w['id'],media_id=mid,view_label='Selected source reproduction'))
            scheme='wikiart-artwork' if not w['source_id'].startswith(('leventis-','cvar-')) else SOURCE+'-object'
            insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=w['id'],scheme=scheme,external_id=w['source_id'],
                canonical_url=w['source_url'],source_id=sid,retrieved_at=r.now()))
            citation(db,sid,'artwork',w['id'],'regional_source_metadata',w['source_url'],
                     dict(source=w,accepted_holding=None,current_display=None,editorial_state='review'))
            position+=1
            insert(db,'curated_collection_items',dict(collection_id=p['owner_collection_id'],artwork_id=w['id'],position=position,
                reason=w['selection_basis'],source_id=sid,source_url=w['source_url'],checked_at=r.now()))
        db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(p['owner_collection_id'],))
    r.save(RUN/'applied.json',dict(at=r.now(),plan_sha256=digest(plan_path),source_id=sid,artworks=len(p['works']),
        artists=sum(not a['existing'] and not a.get('object_level') for a in p['artists']),images=sum(bool(w['image']) for w in p['works']),
        artwork_ids=[w['id'] for w in p['works']],local_only=True,status='review'))
    print(read(RUN/'applied.json'),flush=True)


def verify():
    p=read(RUN/'application-plan.json');receipt=read(RUN/'applied.json');errors=[]
    assert receipt['plan_sha256']==digest(RUN/'application-plan.json')
    ids=receipt['artwork_ids']
    with r.readonly() as db:
        rows=db.execute("""SELECT a.*,m.storage_path,m.byte_size,m.checksum_sha256 FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id
                            WHERE a.id=ANY(%s::uuid[])""",(ids,)).fetchall()
        actual={str(a['id']):a for a in rows}
        for w in p['works']:
            a=actual.get(w['id']);assert a is not None,w['id']
            assert a['status']=='review' and a['published_at'] is None and a['research_candidate']
            assert a['current_institution_id'] is None and a['location_checked_at'] is None
            assert all(a[k]==w['date'][k] for k in w['date']) and a['creation_year_end']<=1970
            assert a['title']==w['title'] and a['work_type']==w['work_type']
            assert db.execute('SELECT 1 FROM curated_collection_items WHERE artwork_id=%s AND collection_id=%s',(w['id'],p['owner_collection_id'])).fetchone()
            assert not db.execute('SELECT 1 FROM artwork_location_assertions WHERE artwork_id=%s',(w['id'],)).fetchone()
            if w['image']:
                im=w['image'];path=ROOT/'apps/web/public'/a['storage_path'].lstrip('/')
                assert digest(path)==im['sha256']==a['checksum_sha256'] and a['byte_size']==im['bytes']<=100000
                assert db.execute('SELECT 1 FROM media_rights_evidence WHERE media_id=%s',(a['primary_media_id'],)).fetchone()
            else:assert a['primary_media_id'] is None
        for a in p['artists']:
            if a.get('object_level'):continue
            record=db.execute('SELECT * FROM artists WHERE id=%s',(a['id'],)).fetchone();assert record
            if not a['existing']:assert record['status']=='review' and record['published_at'] is None and record['biography_md'] is None
        for g in p['geography']:
            assert db.execute('SELECT 1 FROM artist_countries WHERE artist_id=%s AND country_code=%s',(g['artist_id'],g['country'][0])).fetchone()
    result=dict(at=r.now(),artworks=len(rows),images=sum(bool(w['image']) for w in p['works']),
                new_artists=receipt['artists'],errors=errors,all_review=True,all_dates_within_cutoff=True,
                no_accepted_holdings_or_display=True,local_only=True,plan_sha256=digest(RUN/'application-plan.json'))
    r.save(RUN/'verification.json',result);print(result,flush=True)


def api_verify():
    import requests
    p=read(RUN/'application-plan.json')
    def check(w):
        url='http://127.0.0.1:8098/api/v1/atlas/artworks/'+w['id']
        response=requests.get(url,timeout=(5,20))
        response.raise_for_status();data=response.json()
        assert data['id']==w['id'] and data['title']==w['title'] and data['status']=='review'
        assert data['creation_year_end']==w['date']['creation_year_end']
        if w['image']:
            im=requests.get('http://127.0.0.1:3000'+data['media_url'],timeout=(5,20))
            im.raise_for_status();assert hashlib.sha256(im.content).hexdigest()==w['image']['sha256']
        return dict(artwork_id=w['id'],http_status=response.status_code,image_verified=bool(w['image']))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(check,p['works']))
    r.save(RUN/'api-verification.json',dict(at=r.now(),records=len(results),images=sum(x['image_verified'] for x in results),
        results=results,access='Existing loopback local-debug API; no login, credentials or subscription used',errors=[]))
    print('Local API verified:',len(results),'review records,',sum(x['image_verified'] for x in results),'served image hashes',flush=True)


def run(phase):
    if phase not in {'plan','backup','apply','verify','api_verify'}:raise ValueError('Explicit delivery phase required')
    globals()[phase]()
