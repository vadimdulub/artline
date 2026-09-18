#!/usr/bin/env python3
"""Guarded primary Greek museum metadata and identity enrichment, both DBs."""
import argparse,collections,importlib.util,json,re,uuid
from pathlib import Path

s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s=importlib.util.spec_from_file_location('primary',Path(__file__).with_name('research-greek-primary-catalogues.py'));primary=importlib.util.module_from_spec(s);s.loader.exec_module(primary)
RUN=m.x.BASE/'greek-primary-catalogues';SOURCE='overnight-greek-primary-20260913';ACTOR='local-european-research'

def key(value):return re.sub(r'\s+','',value or '').casefold()
def uid(value):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/greek-primary/'+value))
def medium(raw):
    # Museum strings use a comma before dimensions; decimal commas belong to
    # dimensions and must not split the medium a second time.
    match=re.search(r',\s*(?=\d)',raw);a,b=(raw[:match.start()],raw[match.end():]) if match else (raw,'')
    lower=a.casefold()
    kind='fresco' if 'fresco' in lower or 'wall painting' in lower else 'watercolor' if 'watercolour' in lower else 'painting' if any(t in lower for t in ('oil','tempera')) else 'drawing' if any(t in lower for t in ('pencil','charcoal','crayon','pastel','ink','chalk')) else 'unknown'
    return a.strip(),b.strip(),kind

def inventory(db,slugs):
    artists={r['slug']:r for r in m.artist_inventory(db) if r['slug'] in slugs}
    assert set(artists)==set(slugs)
    ids=[r['id'] for r in artists.values()]
    # Bounded by twenty painter foreign keys, not a global artwork enrichment CTE.
    works=db.execute("""WITH selected AS MATERIALIZED (SELECT DISTINCT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[]))
    SELECT to_jsonb(a) artwork,i.slug institution_slug,
    coalesce((SELECT jsonb_agg(aa.artist_id::text) FROM artwork_artists aa WHERE aa.artwork_id=a.id AND attribution_role='primary'),'[]') primary_creators,
    coalesce((SELECT jsonb_agg(jsonb_build_object('scheme',scheme,'id',external_id)) FROM external_identifiers WHERE entity_type='artwork' AND entity_id=a.id),'[]') authorities,
    coalesce((SELECT jsonb_agg(DISTINCT source_url) FROM citations WHERE entity_type='artwork' AND entity_id=a.id),'[]') source_urls
    FROM selected s JOIN artworks a ON a.id=s.artwork_id LEFT JOIN institutions i ON i.id=a.current_institution_id WHERE a.status<>'archived'""",(ids,)).fetchall()
    return artists,works

def plan():
    if (RUN/'application-plan.json').exists():return
    research=[json.loads((RUN/f'round-{n:02d}'/'research.json').read_text()) for n in range(1,21)]
    assert all(r['completed'] for r in research)
    records=[{**w,'date':primary.date(w['date']['display']),'date_interpretation_version':2} for r in research for w in r['records']];assert len({w['key'] for w in records})==len(records)
    slugs=[r['artist']['slug'] for r in research];targets={};identity={}
    for target in ('local','production'):
        states=[]
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'")
            artists,works=inventory(db,slugs);inst=db.execute("SELECT id::text,slug FROM institutions WHERE slug='national-gallery-greece' AND status<>'archived'").fetchone();assert inst
            for r in research:
                p=r['artist'];a=artists[p['slug']];assert a['status']=='review' and 'GR' in a['countries']
                known=any(e['scheme']=='nationalgallery-gr-artist' and e['id']==p['external_id'] for e in a['authorities'])
                if not known:
                    assert p.get('wikidata') and any(e['scheme']=='wikidata' and e['id']==p['wikidata'] for e in a['authorities'])
                    assert not any(e['scheme']=='nationalgallery-gr-artist' for e in a['authorities'])
                identity.setdefault(p['slug'],{})[target]=dict(artist_id=a['id'],museum_person_id=p['external_id'],already_identified=known,primary_artist=r['primary_artist'],wiki_identity=p.get('wikidata'),country='GR',uncertainty='Existing numeric/unknown biography dates preserved; museum uncertainty captured separately.')
            for w in records:
                a=artists[w['artist']['slug']];aid=a['id'];d=w['date'];reason=w['review_reason'];match=None
                creator_works=[r for r in works if aid in r['primary_creators']]
                exact=[r for r in creator_works if any(e['scheme']=='nationalgallery-gr-work' and e['id']==w['key'] for e in r['authorities']) or w['source_url'] in r['source_urls'] or (r['institution_slug']==inst['slug'] and key(r['artwork']['accession_number'])==key(w['accession']))]
                if len(exact)>1:reason='Multiple existing records share primary object identity; reconcile duplicates first'
                elif exact:match=exact[0]
                else:
                    titles=[r for r in creator_works if m.m.r.norm(w['title']) in {m.m.r.norm(r['artwork']['title']),m.m.r.norm(r['artwork']['alternate_title'] or '')}]
                    if titles:reason='Existing same-title creator records need exact source-object reconciliation'
                if d['first'] is not None and a['death_year'] is not None and d['first']>a['death_year']:reason='Work date outside existing painter lifespan'
                if d['last'] is not None and a['birth_year'] is not None and d['last']<a['birth_year']:reason='Work date before existing painter birth'
                if match:
                    if match['artwork']['status']!='review':reason='Existing publication decision requires separate editorial review'
                    oldscheme=[e['id'] for e in match['authorities'] if e['scheme']=='nationalgallery-gr-work']
                    if oldscheme and oldscheme!=[w['key']]:reason='Existing different primary museum object identifier'
                med,dimensions,kind=medium(w['medium_dimensions']);updates={};date_conflict=None
                if match and not reason:
                    old=match['artwork']
                    if not old['medium_text']:updates['medium_text']=med
                    if not old['dimensions_text']:updates['dimensions_text']=dimensions or None
                    if old['work_type']=='unknown' and kind!='unknown':updates['work_type']=kind
                    if not old['accession_number']:updates['accession_number']=w['accession']
                    if old['date_precision']=='unknown' and d['first'] is not None and d['eligible']:
                        updates.update(date_display=d['display'],creation_year_start=d['first'],creation_year_end=d['last'],date_precision=d['precision'])
                    elif d['first'] is not None and old['creation_year_start'] is not None and (old['creation_year_start'],old['creation_year_end'])!=(d['first'],d['last']):date_conflict=dict(existing=[old['creation_year_start'],old['creation_year_end'],old['date_precision']],primary=d,action='Primary citation added; known dating preserved pending individually reviewed correction')
                state=dict(key=w['key'],action='held' if reason else 'existing' if match else 'new',reason=reason,artist_id=aid,artist_slug=a['slug'],institution_id=inst['id'],artwork_id=match['artwork']['id'] if match else uid('artwork/'+w['key']),artwork_slug=match['artwork']['slug'] if match else 'greek-primary-'+w['key'],existing=match['artwork'] if match else None,updates=updates,date_conflict=date_conflict,work_type=kind,medium=med,dimensions=dimensions)
                states.append(state)
        targets[target]=states
    for a,b in zip(targets['local'],targets['production']):
        assert a['key']==b['key']
        if a['action']=='held' or b['action']=='held':
            reasons=sorted({s['reason'] for s in (a,b) if s['reason']})
            for s in (a,b):s.update(action='held',reason='; '.join(reasons))
        assert (a['action'],a['artist_slug'],a['artwork_slug'],a['updates'],a['date_conflict'])==(b['action'],b['artist_slug'],b['artwork_slug'],b['updates'],b['date_conflict'])
    plan=dict(at=m.m.core.now(),records=records,targets=targets,artist_identity=identity)
    m.m.core.save_new(RUN/'application-plan.json',plan)
    manifest=dict(at=m.m.core.now(),plan_sha256=m.m.core.sha((RUN/'application-plan.json').read_bytes()),rounds=20,inspected=len(records),decisions=dict(collections.Counter(s['action'] for s in targets['local'])),unknown_dates=sum(w['date']['precision']=='unknown' for w in records),known_date_conflicts=[dict(key=s['key'],conflict=s['date_conflict']) for s in targets['local'] if s['date_conflict']],policy='Exact primary museum object, accession and painter links. Country existing GR evidence preserved. New and enriched records remain review. No museum photograph downloaded; no current-display assertion added.')
    m.m.core.save_new(RUN/'application-manifest.json',manifest);print(json.dumps(manifest,indent=2),flush=True)

def apply():
    raw=(RUN/'application-plan.json').read_bytes();data=json.loads(raw);pin=json.loads((RUN/'application-manifest.json').read_text())['plan_sha256'];assert m.m.core.sha(raw)==pin
    assert json.loads((RUN/'application-quality-review.json').read_text())==dict(approved=True,plan_sha256=pin)
    records={w['key']:w for w in data['records']}
    for target in ('local','production'):
        path=m.BACKUPS/('greek-primary-'+target+'-preimages.json')
        if path.exists():continue
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');artists,works=inventory(db,list(data['artist_identity']));byid={r['artwork']['id']:r for r in works}
            for s in data['targets'][target]:
                if s['action']=='existing':assert byid[s['artwork_id']]['artwork']==s['existing']
        m.m.core.save_new(path,dict(at=m.m.core.now(),plan_sha256=pin,artists=artists,works=works))
    for target in ('local','production'):
        with m.m.r.base.connect(target=='production') as db:
            sid=m.m.source(db,SOURCE,'Greek National Gallery: primary painter/object catalogue research','collection_page','https://www.nationalgallery.gr/')
            for state in data['targets'][target]:
                if state['action']=='held':continue
                dest=RUN/'applied'/target/(state['key']+'.json')
                if dest.exists():continue
                w=records[state['key']];aid=state['artwork_id'];artist=state['artist_id'];identity=data['artist_identity'][state['artist_slug']][target]
                with db.transaction():
                    db.execute('SELECT pg_advisory_xact_lock(559220260914)');db.execute("SET LOCAL statement_timeout='45s'")
                    done=db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND field_name='official_object_identity' AND source_record_id=%s",(aid,sid,w['key'])).fetchone()
                    if not done:
                        if state['action']=='new':
                            d=w['date'];description=f"Museum-catalogued {state['medium'].lower()} by {w['artist']['display_name']}. "+(f"Collection credit: {w['collection_credit']}. " if w['collection_credit'] else '')+'Primary museum metadata; record remains in review. The catalogue connection does not assert current display.'
                            m.m.r.base.insert(db,'artworks',dict(id=aid,slug=state['artwork_slug'],title=w['title'],normalized_title=m.m.r.norm(w['title']),date_display=d['display'] or 'Date unknown in museum catalogue',creation_year_start=d['first'],creation_year_end=d['last'],date_precision=d['precision'],work_type=state['work_type'],medium_text=state['medium'],dimensions_text=state['dimensions'] or None,description_md=description,current_institution_id=state['institution_id'],current_location_text='National Gallery – Alexandros Soutsos Museum',location_checked_at=w['receipt']['retrieved_at'],accession_number=w['accession'],status='review',research_candidate=d['precision']=='unknown' or state['work_type']=='unknown',created_by=ACTOR,updated_by=ACTOR))
                            m.m.r.base.insert(db,'artwork_artists',dict(artwork_id=aid,artist_id=artist,attribution_role='primary',attribution_note='Exact maker link on the primary museum object page, also listed by the museum person catalogue.'))
                            m.m.r.base.insert(db,'artwork_location_assertions',dict(artwork_id=aid,claim_type='holding',institution_id=state['institution_id'],context='collection',source_id=sid,source_url=w['source_url'],evidence_note='Primary museum object record and inventory number document the catalogue connection. '+('Collection credit: '+w['collection_credit']+'. ' if w['collection_credit'] else '')+'No present-display or exclusive ownership claim.',checked_at=w['receipt']['retrieved_at'],review_state='accepted'))
                        else:
                            old=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s FOR UPDATE',(aid,)).fetchone()['row'];assert old==state['existing'],'Existing artwork changed after reviewed plan'
                            if state['updates']:
                                from psycopg import sql
                                fields=state['updates'];query=sql.SQL('UPDATE artworks SET {} ,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s').format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in fields));db.execute(query,(*fields.values(),ACTOR,aid))
                        db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'nationalgallery-gr-work',%s,%s,%s,%s) ON CONFLICT(scheme,external_id) DO NOTHING",(aid,w['key'],w['source_url'],sid,w['receipt']['retrieved_at']))
                        actual=db.execute("SELECT entity_id::text FROM external_identifiers WHERE scheme='nationalgallery-gr-work' AND external_id=%s",(w['key'],)).fetchone();assert actual['entity_id']==aid
                        m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name='official_object_identity',source_id=sid,source_record_id=w['key'],source_url=w['source_url'],retrieved_at=w['receipt']['retrieved_at'],created_by=ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,object_receipt=w['receipt'],artist_receipt=identity['primary_artist']['receipt'],accession=w['accession'],museum_maker_link=w['source_artist_links'],date=w['date'],date_conflict=state['date_conflict'],medium_dimensions=w['medium_dimensions'],collection_credit=w['collection_credit']),ensure_ascii=False)))
                        person=w['artist'];db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artist',%s,'nationalgallery-gr-artist',%s,%s,%s,%s) ON CONFLICT(scheme,external_id) DO NOTHING",(artist,person['external_id'],person['canonical_url'],sid,identity['primary_artist']['receipt']['retrieved_at']))
                        assert db.execute("SELECT entity_id::text FROM external_identifiers WHERE scheme='nationalgallery-gr-artist' AND external_id=%s",(person['external_id'],)).fetchone()['entity_id']==artist
                        if not db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s AND field_name='official_person_identity'",(artist,sid)).fetchone():m.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=artist,field_name='official_person_identity',source_id=sid,source_record_id=person['external_id'],source_url=person['canonical_url'],retrieved_at=identity['primary_artist']['receipt']['retrieved_at'],created_by=ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,identity=identity,review='Source name and life context corroborated; disputed/missing biography dates remain unchanged. Country GR retained from existing separately documented affiliation.'),ensure_ascii=False)))
                m.m.core.save_new(dest,dict(at=m.m.core.now(),plan_sha256=pin,target=target,key=w['key'],action=state['action'],artwork_id=aid,artwork_slug=state['artwork_slug'],updates=state['updates']));print(target,'Greek primary',w['key'],state['action'],flush=True)

def verify():
    data=json.loads((RUN/'application-plan.json').read_text());records={w['key']:w for w in data['records']};out={}
    for target in ('local','production'):
        counts=collections.Counter()
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY')
            for s in data['targets'][target]:
                if s['action']=='held':continue
                w=records[s['key']];a=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s',(s['artwork_id'],)).fetchone()['row'];assert a['status']=='review' and a['published_at'] is None
                assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND entity_id=%s AND scheme='nationalgallery-gr-work' AND external_id=%s",(a['id'],w['key'])).fetchone()
                assert db.execute("SELECT 1 FROM artwork_artists aa JOIN artist_countries ac ON ac.artist_id=aa.artist_id WHERE aa.artwork_id=%s AND aa.artist_id=%s AND aa.attribution_role='primary' AND ac.country_code='GR'",(a['id'],s['artist_id'])).fetchone()
                assert db.execute('SELECT artline_has_selection_evidence(%s) selected',(a['id'],)).fetchone()['selected']
                if s['action']=='new':
                    assert (a['title'],a['creation_year_start'],a['creation_year_end'],a['date_precision'],a['medium_text'],a['work_type'])==(w['title'],w['date']['first'],w['date']['last'],w['date']['precision'],s['medium'],s['work_type'])
                    assert db.execute("SELECT count(*) n FROM artwork_location_assertions WHERE artwork_id=%s AND claim_type='display'",(a['id'],)).fetchone()['n']==0
                else:
                    expected={**s['existing'],**s['updates']};ignored={'revision','updated_at','updated_by'};assert {k:v for k,v in a.items() if k not in ignored}=={k:v for k,v in expected.items() if k not in ignored}
                counts[s['action']]+=1
            backup=json.loads((m.BACKUPS/('greek-primary-'+target+'-preimages.json')).read_text())
            for old in backup['artists'].values():
                a=db.execute('SELECT display_name,birth_year,death_year,status FROM artists WHERE id=%s',(old['id'],)).fetchone();assert all(a[k]==old[k] for k in a)
        out[target]=dict(counts)
    assert out['local']==out['production'];m.m.core.save_new(RUN/'verification.json',dict(at=m.m.core.now(),rounds=20,targets=out));print('Greek primary verified both',out,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);a=p.parse_args();globals()[a.command]()
