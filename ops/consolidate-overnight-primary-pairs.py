#!/usr/bin/env python3
"""Four primary-museum duplicate pairs with missing holding/type enrichment."""
import argparse,importlib.util,json
from pathlib import Path
from psycopg import sql
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('consolidate-overnight-artworks.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
m=a.m;CORE=a.CORE;RUN=m.x.BASE/'duplicates/primary-pair-consolidation';SOURCE='overnight-primary-pair-review-20260913'

def plan():
    facts=json.loads((m.x.BASE/'duplicates/primary-pair-reviewed-facts.json').read_text())['approved_physical_identities']
    leads=json.loads((m.BACKUPS/'four-primary-pairs-local-snapshot.json').read_text());entries=[]
    for e in facts:
        lead=next(g for g in leads if g['lead'].get('url')==e['url'] or (e['key']=='joconde-maes-de1048' and g['lead'].get('institution')=='joconde-m5052'))
        pair=sorted(lead['snapshot']['artworks'],key=lambda w:(w['created_at'],w['slug']));keep,old=pair
        entries.append(dict(key=e['key'],canonical_slug=keep['slug'],old_slug=old['slug'],evidence=e,targets={}))
    for target in ('local','production'):
        snapshots={}
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');a.ensure_schema(db)
            for e in entries:
                rows={r['slug']:r for r in db.execute('SELECT id::text,slug FROM artworks WHERE slug=ANY(%s)',([e['canonical_slug'],e['old_slug']],)).fetchall()};assert len(rows)==2
                old=rows[e['old_slug']]['id'];keep=rows[e['canonical_slug']]['id'];snap=a.snapshot(db,[old,keep]);works={r['id']:r for r in snap['artworks']};w=works[keep];other=works[old];ev=e['evidence']
                assert w['status']==other['status']=='review' and w['published_at'] is None and other['published_at'] is None
                assert w['title']==other['title'] and [w['creation_year_start'],w['creation_year_end']]==[other['creation_year_start'],other['creation_year_end']]==ev['years']
                artistkeys=lambda aid:{(r['artist_id'],r['attribution_role']) for r in snap['artwork_artists'] if r['artwork_id']==aid}
                assert artistkeys(old)==artistkeys(keep) and artistkeys(keep)
                assert not snap['artwork_places'] and not snap['curated_collection_items']
                institution=db.execute('SELECT id::text,slug,name FROM institutions WHERE slug=%s',(ev['institution_slug'],)).fetchone();assert institution
                assert w['current_institution_id'] in (None,institution['id']) and other['current_institution_id'] in (None,institution['id'])
                common={r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==old}&{r['scheme'] for r in snap['external_identifiers'] if r['entity_id']==keep}
                assert not common or (e['key']=='joconde-maes-de1048' and common=={'european-joconde-m5052-object'})
                expected={};new_holding=not any(r['artwork_id']==keep and r['claim_type']=='holding' and r['review_state']=='accepted' and r['superseded_by'] is None for r in snap['artwork_location_assertions'])
                if not w['accession_number']:expected['accession_number']=ev['accession']
                else:assert m.m.accession_key(w['accession_number'])==m.m.accession_key(ev['accession'])
                if w['work_type']=='unknown':expected['work_type']=ev['work_type']
                else:assert w['work_type']==ev['work_type']
                if w['date_display'].startswith('Unverified date:'):expected['date_display']=ev['date_display']
                for field in ('medium_text','dimensions_text'):
                    if not w[field] and ev.get(field):expected[field]=ev[field]
                if not w['primary_media_id'] and other['primary_media_id']:
                    media=next(r for r in snap['media_assets'] if r['id']==other['primary_media_id']);assert media['verified_at'] and media['byte_size']<=100000 and any(r['media_id']==media['id'] for r in snap['media_rights_evidence']);expected['primary_media_id']=media['id']
                scheme='rijks-object' if e['key'].startswith('rijks-') else ('moma-object' if e['key'].startswith('moma-') else None)
                ident=e['key'].split('-',1)[1] if scheme else None
                if scheme:
                    found=db.execute('SELECT entity_id::text FROM external_identifiers WHERE scheme=%s AND external_id=%s',(scheme,ident)).fetchall();assert not found or len(found)==1 and found[0]['entity_id'] in (old,keep)
                snapshots[e['key']]=snap;e['targets'][target]=dict(old_id=old,canonical_id=keep,updates=expected,institution=institution,new_holding=new_holding,preserve_archived_schemes=sorted(common),source_scheme=scheme,source_identifier=ident)
        CORE.save_new(m.BACKUPS/('primary-pairs-'+target+'-preimages.json'),snapshots)
    for e in entries:
        comparable=lambda target:{k:v for k,v in e['targets'][target].items() if k not in ('old_id','canonical_id','institution','updates')}
        assert comparable('local')==comparable('production')
        assert {k:v for k,v in e['targets']['local']['updates'].items() if k!='primary_media_id'}=={k:v for k,v in e['targets']['production']['updates'].items() if k!='primary_media_id'}
    path=RUN/'plan.json';CORE.save_new(path,entries);CORE.save_new(RUN/'manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha(path.read_bytes()),pairs=len(entries)));print('Four primary pair plans prepared',flush=True)

def read_plan():
    raw=(RUN/'plan.json').read_bytes();pin=json.loads((RUN/'manifest.json').read_text())['plan_sha256'];assert CORE.sha(raw)==pin;return json.loads(raw),pin

def apply():
    entries,pin=read_plan();qa=json.loads((RUN/'quality-review.json').read_text());assert qa['approved'] and qa['plan_sha256']==pin
    for target in ('local','production'):
        backup=json.loads((m.BACKUPS/('primary-pairs-'+target+'-preimages.json')).read_text())
        with m.m.r.base.connect(target=='production') as db:
            for e in entries:
                dest=RUN/'applied'/target/(e['key']+'.json')
                if dest.exists():continue
                t=e['targets'][target];old=t['old_id'];keep=t['canonical_id'];before=backup[e['key']];ev=e['evidence']
                with db.transaction():
                    db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(559220260914)');a.ensure_schema(db);db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',([old,keep],)).fetchall()
                    sid=m.m.source(db,SOURCE,'Individually reviewed primary museum object identities','collection_page','https://www.rijksmuseum.nl/')
                    done=db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND field_name='duplicate_identity' AND source_record_id=%s AND evidence_note LIKE %s",(keep,sid,e['old_slug'],'%'+pin+'%')).fetchone()
                    if not done:
                        assert a.snapshot(db,[old,keep])==before,'Relationships changed after review'
                        for table in a.MOVE:db.execute(sql.SQL('UPDATE {} SET artwork_id=%s WHERE artwork_id=%s').format(sql.Identifier(table)),(keep,old))
                        db.execute('UPDATE research_artwork_links SET possible_artwork_ids=array_replace(possible_artwork_ids,%s::uuid,%s::uuid) WHERE %s::uuid=ANY(possible_artwork_ids)',(old,keep,old))
                        for table in ('citations','slug_redirects'):db.execute(sql.SQL("UPDATE {} SET entity_id=%s WHERE entity_type='artwork' AND entity_id=%s").format(sql.Identifier(table)),(keep,old))
                        db.execute("UPDATE external_identifiers SET entity_id=%s WHERE entity_type='artwork' AND entity_id=%s AND NOT(scheme=ANY(%s))",(keep,old,t['preserve_archived_schemes']))
                        if t['source_scheme'] and not db.execute("SELECT 1 FROM external_identifiers WHERE scheme=%s AND external_id=%s",(t['source_scheme'],t['source_identifier'])).fetchone():m.m.r.base.insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=keep,scheme=t['source_scheme'],external_id=t['source_identifier'],canonical_url=ev['url'],source_id=sid,retrieved_at=CORE.now()))
                        if t['new_holding']:
                            m.m.r.base.insert(db,'artwork_location_assertions',dict(artwork_id=keep,claim_type='holding',institution_id=t['institution']['id'],context='collection',source_id=sid,source_url=ev['url'],evidence_note='Primary museum object identity and collection connection reviewed. This does not assert current display, visitor access, or legal ownership.',checked_at=CORE.now(),review_state='accepted'))
                        db.execute('INSERT INTO source_institutions(source_id,institution_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',(sid,t['institution']['id']))
                        if t['updates'].get('primary_media_id'):
                            im=t['updates']['primary_media_id'];rel=next(r for r in before['artwork_media'] if r['artwork_id']==old and r['media_id']==im);m.m.r.base.insert(db,'artwork_media',{**rel,'artwork_id':keep})
                        updates=t['updates'];sets=[sql.SQL('{}=%s').format(sql.Identifier(k)) for k in updates];sets+=[sql.SQL('revision=revision+1'),sql.SQL('updated_at=now()'),sql.SQL('updated_by=%s')]
                        db.execute(sql.SQL('UPDATE artworks SET {} WHERE id=%s').format(sql.SQL(',').join(sets)),[*updates.values(),m.m.ACTOR,keep])
                        db.execute("UPDATE artworks SET status='archived',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(m.m.ACTOR,old));db.execute("INSERT INTO slug_redirects(entity_type,entity_id,old_slug) VALUES('artwork',%s,%s)",(keep,e['old_slug']))
                        evidence=dict(plan_sha256=pin,primary=ev,archived_id=old,canonical_id=keep,updates=updates,archived_authorities=[r for r in before['external_identifiers'] if r['entity_id']==old and r['scheme'] in t['preserve_archived_schemes']],archived_attributions=[r for r in before['artwork_artists'] if r['artwork_id']==old],archived_location_assertions=[r for r in before['artwork_location_assertions'] if r['artwork_id']==old],preservation='Original physical rows, source assertions, media and rights preserved. Redundant record archived with canonical slug redirect. Alternate same-scheme Joconde notice stays on archived row and is recorded here; future ingestion must follow its redirect.')
                        m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=keep,field_name='duplicate_identity',source_id=sid,source_record_id=e['old_slug'],source_url=ev['url'],retrieved_at=CORE.now(),created_by=m.m.ACTOR,evidence_note=json.dumps(evidence,ensure_ascii=False)))
                CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,key=e['key'],target=target,canonical_slug=e['canonical_slug'],archived_slug=e['old_slug']));print(target,'primary pair consolidated',e['key'],flush=True)

def verify():
    entries,pin=read_plan();out={}
    for target in ('local','production'):
        before=json.loads((m.BACKUPS/('primary-pairs-'+target+'-preimages.json')).read_text());checked=[]
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY')
            for e in entries:
                t=e['targets'][target];old=t['old_id'];keep=t['canonical_id'];snap=a.snapshot(db,[old,keep]);b=before[e['key']];original={w['id']:w for w in b['artworks']};works={w['id']:w for w in snap['artworks']}
                assert works[old]['status']=='archived' and works[keep]['status']=='review' and works[keep]['published_at'] is None and works[keep]['current_institution_id']==t['institution']['id']
                for aid,allowed in [(old,{'status','revision','updated_at','updated_by'}),(keep,{'revision','updated_at','updated_by','current_institution_id',*t['updates']})]:assert {k:v for k,v in works[aid].items() if k not in allowed}=={k:v for k,v in original[aid].items() if k not in allowed}
                for field,value in t['updates'].items():assert works[keep][field]==value
                for table in ('media_assets','media_rights_evidence','artwork_artists','artwork_places','curated_collection_items'):assert snap[table]==b[table],table
                for row in b['artwork_location_assertions']:assert row in snap['artwork_location_assertions']
                for table in ('citations','external_identifiers','slug_redirects'):
                    now={r['id']:r for r in snap[table]}
                    for row in b[table]:
                        move=row['entity_id']==old and not(table=='external_identifiers' and row['scheme'] in t['preserve_archived_schemes']);expected={**row,'entity_id':keep if move else row['entity_id']};assert now[row['id']]==expected
                for table in a.MOVE:assert not any(r['artwork_id']==old for r in snap[table]) and len(snap[table])==len(b[table])
                assert any(r['old_slug']==e['old_slug'] and r['entity_id']==keep for r in snap['slug_redirects'])
                assert db.execute('SELECT artline_has_selection_evidence(%s) yes',(keep,)).fetchone()['yes']
                checked.append(dict(key=e['key'],canonical_slug=e['canonical_slug'],archived_slug=e['old_slug'],institution=t['institution']['slug'],status='review'))
        out[target]=checked
    assert out['local']==out['production'];CORE.save_new(RUN/'verification.json',dict(at=CORE.now(),plan_sha256=pin,verified_pairs=len(entries),targets=out));print('Four primary pairs verified both databases',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);x=p.parse_args();globals()[x.command]()
