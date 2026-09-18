#!/usr/bin/env python3
"""Apply independently corroborated creator authorities, retaining artwork review.

Plans use captured museum/CSV names + both lifespan years + Wikidata authority.
New painters require no existing ID or documented-name collision. Writes lock
and re-check each target, preserve full selected preimages, and cite evidence.
"""
import argparse, collections, importlib.util, json, uuid
from pathlib import Path
spec=importlib.util.spec_from_file_location('research',Path(__file__).with_name('research-unresolved-creator-authorities.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);m=a.m;r=a.r
BASE=m.RUN
m.RUN=a.RUN
m.BACKUPS=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/creator-authorities-20260913')
m.FIELD='creator_authority_reconciled_20260913'
m.SOURCE_SLUG='creator-authorities-20260913'
m.SOURCE_NAME='Museum and supplied creator biographies corroborated with Wikidata'
ID_PROPERTIES={'P2252':'nga-constituent','P2174':'moma-person','P2741':'tate-person'}

def read_base(name):return json.loads((BASE/name).read_text())
def all_artists(db):
    return db.execute("""SELECT id::text,slug,display_name,normalized_name,birth_year,death_year,status,entity_type,
    coalesce((SELECT jsonb_agg(alias ORDER BY alias) FROM artist_aliases WHERE artist_id=a.id),'[]') aliases,
    coalesce((SELECT jsonb_agg(jsonb_build_object('scheme',scheme,'id',external_id) ORDER BY scheme,external_id) FROM external_identifiers WHERE entity_type='artist' AND entity_id=a.id),'[]') authorities FROM artists a ORDER BY slug""").fetchall()

def authority_ids(e):
    ids=[{'scheme':'wikidata','id':e['id']}]
    for prop,scheme in ID_PROPERTIES.items():
        ids.extend({'scheme':scheme,'id':str(x)} for x in r.values(e,prop) if isinstance(x,(str,int)))
        if scheme=='tate-person':
            ids.extend({'scheme':scheme,'id':str(x).rsplit('-',1)[-1]} for x in r.values(e,prop) if isinstance(x,str) and '-' in x and x.rsplit('-',1)[-1].isdigit())
    return ids

def no_new_collision(artist,matcher):
    for ident in artist['identity_ids']:
        assert not matcher.ids.get((ident['scheme'],ident['id'])),('Existing authority collision',artist['slug'],ident)
    for name in artist['identity_names']:
        assert not matcher.names.get(m.names.namekey(name)),('Existing painter-name collision',artist['slug'],name)

def plan():
    assert not (m.RUN/'plan.json').exists()
    assert len(list((m.RUN/'decisions-v2').glob('*.json')))==len(m.read('selected-groups.json')),'Wait for the selected research round to finish'
    works={w['id']:w for w in read_base('unlinked-artworks.json')}
    originals={w['id']:w for w in read_base('unlinked-original-identities.json')}
    facts={w['id']:w for w in read_base('museum-creator-facts.json')}
    matcher=m.Matcher(read_base('artists.json'));entries={};holds=[]
    for path in sorted((m.RUN/'decisions-v2').glob('*.json')):
        decision=json.loads(path.read_text());g=decision['group']
        if len(decision['candidates'])!=1:continue
        candidate=decision['candidates'][0];p={**g['painter'],'wikidata':candidate['qid']}
        entity_path=m.RUN/'entities'/(p['wikidata']+'.json');captured=json.loads(entity_path.read_text());e=captured['entity']
        assert r.year(e,'P569')==p['birth'] and r.year(e,'P570')==p['death']
        assert m.names.namekey(p['name']) in {m.names.namekey(x) for x in r.labels(e)}
        match,reason=matcher.match(p,'wikidata',r.labels(e))
        if match:
            artist={**match['artist'],'new':False};basis='documented_creator_name_and_both_lifespan_years_corroborated_by_wikidata_existing_identity'
        else:
            if reason!='no_identity_with_corroborating_closed_lifespan':
                holds.append({'name':p['name'],'reason':reason,'works':len(g['works'])});continue
            name=r.label(e);qid=p['wikidata']
            artist={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.app/creator-authority/'+qid)),'slug':'wikimedia-painter-'+qid.lower(),'display_name':name,'normalized_name':r.norm(name),'birth_year':p['birth'],'death_year':p['death'],'status':'review','entity_type':'person','aliases':[],'authorities':[{'scheme':'wikidata','id':qid}],'new':True,'identity_names':list(dict.fromkeys([p['name'],*r.labels(e)])),'identity_ids':authority_ids(e),'entity_path':str(entity_path.relative_to(m.ROOT)),'entity_sha256':r.core.sha(entity_path.read_bytes()),'receipt':captured['receipt']}
            for wid in g['works']:
                fact=facts.get(wid)
                if fact and fact['painter'].get('source_id'):
                    artist['identity_ids'].append({'scheme':fact['source_kind']+'-person','id':str(fact['painter']['source_id'])})
            try:no_new_collision(artist,matcher)
            except AssertionError as ex:
                holds.append({'name':p['name'],'reason':str(ex),'works':len(g['works'])});continue
            basis='museum_or_supplied_closed_biography_and_unique_wikidata_authority_new_painter'
        for wid in g['works']:
            w=works[wid];original=originals.get(wid);fact=facts.get(wid)
            if not original:continue
            if fact and fact['painter'].get('source_id'):
                anchored=matcher.ids.get((fact['source_kind']+'-person',str(fact['painter']['source_id'])),set())
                if anchored and anchored!={artist['id']}:
                    holds.append({'slug':w['slug'],'reason':'museum_creator_identifier_points_to_another_painter'});continue
            if (w['creation_year_end'] is not None and w['creation_year_end']<p['birth']) or (w['creation_year_start'] is not None and w['creation_year_start']>p['death']):
                holds.append({'slug':w['slug'],'reason':'artwork_outside_creator_lifetime'});continue
            assert wid not in entries
            entries[wid]={'before':w,'artist':artist,'basis':basis,'painter':p,'source':(fact or {}).get('source_kind','supplied-authority'),'source_guard':fact,'original':original,'evidence':{'object_url':(fact or {}).get('object_url') or 'https://www.wikidata.org/wiki/'+p['wikidata'],'research_record_id':original['research_record_id'],'authority_url':'https://www.wikidata.org/wiki/'+p['wikidata'],'creator_receipt':captured['receipt'],'entity_path':str(entity_path.relative_to(m.ROOT)),'entity_sha256':r.core.sha(entity_path.read_bytes()),'decision_path':str(path.relative_to(m.ROOT)),'decision_sha256':r.core.sha(path.read_bytes()),'original_kind':g['kind']}}
    entries=sorted(entries.values(),key=lambda x:x['before']['slug'])
    m.save('plan.json',entries);m.save('holds.json',holds)
    artists={e['artist']['slug']:e['artist'] for e in entries}
    manifest={'at':r.core.now(),'sha256':r.core.sha((m.RUN/'plan.json').read_bytes()),'links':len(entries),'existing_painters':sum(not p['new'] for p in artists.values()),'new_painters':sum(p['new'] for p in artists.values()),'sources':dict(collections.Counter(e['source'] for e in entries)),'review_status_preserved':True}
    m.save('manifest.json',manifest);print(json.dumps(manifest,indent=2),flush=True)

def check_new_evidence(entries):
    for e in entries:
        evidence=e['evidence'];raw=(m.ROOT/evidence['entity_path']).read_bytes()
        assert r.core.sha(raw)==evidence['entity_sha256']
        assert r.core.sha((m.ROOT/evidence['decision_path']).read_bytes())==evidence['decision_sha256']

def existing_rows(db,entries):
    old=[e for e in entries if not e['artist']['new']]
    return m.artist_rows(db,old) if old else {}

def validate(db,entries,works,artists):
    # Generic guards compare all preserved artwork/source/CSV fields. A new
    # painter's planned values stand in only before its atomic insert.
    for entry in entries:
        p=entry['artist']
        if p['new'] and p['slug'] not in artists:
            artists[p['slug']]={'row':p,'aliases':p['aliases'],'authorities':p['authorities']}
    m.guards(db,entries,works,artists)

def preflight(target):
    manifest,entries=m.load_plan();check_new_evidence(entries);works={};artists={}
    with r.base.connect(target=='production') as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');db.execute("SET LOCAL statement_timeout='120s'")
        matcher=m.Matcher(all_artists(db))
        for p in {e['artist']['slug']:e['artist'] for e in entries if e['artist']['new']}.values():no_new_collision(p,matcher)
        for offset in range(0,len(entries),100):
            batch=entries[offset:offset+100];w=m.selected_rows(db,batch);p=existing_rows(db,batch);artists.update(p);validate(db,batch,w,p);works.update(w)
        assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name=%s LIMIT 1",([w['id'] for w in works.values()],m.FIELD)).fetchone()
        counts=db.execute("SELECT (SELECT count(*) FROM artworks) artworks,(SELECT count(*) FROM artists) artists,(SELECT count(*) FROM artworks w WHERE unlinked_creator_label IS NOT NULL AND status='review' AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=w.id)) unlinked").fetchone()
    m.BACKUPS.mkdir(parents=True,exist_ok=True)
    m.r.core.save_new(m.BACKUPS/(target+'-preimages.json'),{'at':r.core.now(),'plan_sha256':manifest['sha256'],'works':works,'artists':artists,'counts':counts})
    m.save(target+'-preflight.json',{'at':r.core.now(),'plan_sha256':manifest['sha256'],'counts':counts,'works':len(works),'preimages_sha256':r.core.sha((m.BACKUPS/(target+'-preimages.json')).read_bytes())})
    print(target,'preflight passed',len(works),flush=True)

def insert_artist(db,p,sid):
    captured=json.loads((m.ROOT/p['entity_path']).read_text());entity=captured['entity'];qid=entity['id']
    fields={k:p[k] for k in ('id','slug','display_name','normalized_name','birth_year','death_year','status','entity_type')}
    fields.update(sort_name=p['display_name'],birth_display=str(p['birth_year']),death_display=str(p['death_year']),timeline_start_year=p['birth_year'],timeline_end_year=p['death_year'],timeline_basis='life',timeline_display=f"{p['birth_year']}–{p['death_year']}",created_by=m.ACTOR,updated_by=m.ACTOR)
    r.base.insert(db,'artists',fields)
    r.base.insert(db,'external_identifiers',dict(entity_type='artist',entity_id=p['id'],scheme='wikidata',external_id=qid,canonical_url='https://www.wikidata.org/wiki/'+qid,source_id=sid,retrieved_at=p['receipt']['retrieved_at']))
    for lang,label in entity.get('labels',{}).items():
        db.execute("INSERT INTO artist_aliases(artist_id,alias,normalized_alias,language_code,alias_type) VALUES(%s,%s,%s,%s,'alternate') ON CONFLICT DO NOTHING",(p['id'],label['value'],r.norm(label['value']),lang))
    r.base.insert(db,'citations',dict(entity_type='artist',entity_id=p['id'],field_name='authority_identity_and_dates',source_id=sid,source_record_id=qid,source_url='https://www.wikidata.org/wiki/'+qid,evidence_note=json.dumps({'entity_sha256':p['entity_sha256'],'receipt':p['receipt'],'basis':'Source creator name and both lifespan boundaries corroborated with Wikidata; review retained.'}),retrieved_at=p['receipt']['retrieved_at'],created_by=m.ACTOR))

def apply(target):
    manifest,entries=m.load_plan();check_new_evidence(entries)
    parent=m.BACKUPS.parent/'creator-lifespans-20260913'
    assert json.loads((parent/'production-backup-receipt.json').read_text())['status']=='SUCCESSFUL'
    assert (parent/'local-backup-receipt.json').exists()
    for t in ('local','production'):assert m.read(t+'-preflight.json')['plan_sha256']==manifest['sha256']
    for offset in range(0,len(entries),100):
        receipt=m.RUN/'applied'/target/f'batch-{offset//100+1:03d}.json'
        if receipt.exists():continue
        batch=entries[offset:offset+100];outcomes=[];created=[]
        with r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE');db.execute("SET LOCAL statement_timeout='120s'");db.execute("SET LOCAL lock_timeout='10s'")
            db.execute('SELECT pg_advisory_xact_lock(2026090959)');db.execute('SELECT pg_advisory_xact_lock(559220260914)')
            db.execute("INSERT INTO sources(slug,name,source_type,base_url) VALUES(%s,%s,'authority_data','https://www.wikidata.org/') ON CONFLICT(slug) DO NOTHING",(m.SOURCE_SLUG,m.SOURCE_NAME))
            sid=db.execute('SELECT id FROM sources WHERE slug=%s',(m.SOURCE_SLUG,)).fetchone()['id']
            works=m.selected_rows(db,batch,True);artists=existing_rows(db,batch);validate(db,batch,works,dict(artists))
            fresh=m.Matcher(all_artists(db))
            for p in {e['artist']['slug']:e['artist'] for e in batch if e['artist']['new']}.values():
                existing=fresh.artists.get(p['id'])
                if existing:
                    assert all(existing[k]==p[k] for k in ('slug','display_name','birth_year','death_year','status','entity_type'))
                    assert existing['authorities']==p['authorities']
                    # Only a previous committed batch in this plan can have
                    # created the painter; an unrelated UUID collision fails.
                    assert db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND field_name=%s AND evidence_note::jsonb->>'plan_sha256'=%s AND evidence_note::jsonb->>'artist_slug'=%s LIMIT 1",(m.FIELD,manifest['sha256'],p['slug'])).fetchone()
                else:
                    no_new_collision(p,fresh);insert_artist(db,p,sid);created.append(p['slug'])
                    fresh=m.Matcher([*fresh.artists.values(),{**p,'aliases':p['identity_names']}])
            artists=m.artist_rows(db,batch);m.guards(db,batch,works,artists)
            updates=[]
            with db.pipeline():
                for e in batch:
                    w=works[e['before']['slug']];p=artists[e['artist']['slug']]['row']
                    r.base.insert(db,'artwork_artists',dict(artwork_id=w['id'],artist_id=p['id'],attribution_role='primary',attribution_note='Creator identity: '+e['basis']+'. Original creator label: '+e['before']['unlinked_creator_label']+'. Review retained.'))
                    updates.append(db.execute('UPDATE artworks SET unlinked_creator_label=NULL,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND unlinked_creator_label=%s',(m.ACTOR,w['id'],e['before']['unlinked_creator_label'])))
                    evidence={'identity_basis':e['basis'],'original_creator_label':e['before']['unlinked_creator_label'],'source_painter':e['painter'],'source_evidence':e['evidence'],'plan_sha256':manifest['sha256'],'artist_slug':p['slug']}
                    r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=w['id'],field_name=m.FIELD,source_id=sid,source_record_id=e['original']['research_record_id'],source_url=e['evidence']['object_url'],evidence_note=json.dumps(evidence,ensure_ascii=False,sort_keys=True),retrieved_at=r.core.now(),created_by=m.ACTOR))
                    outcomes.append({'slug':w['slug'],'artwork_id':w['id'],'artist_id':p['id'],'artist_slug':p['slug'],'source':e['source']})
            assert all(x.rowcount==1 for x in updates)
        r.core.save_new(receipt,{'at':r.core.now(),'plan_sha256':manifest['sha256'],'outcomes':outcomes,'created_painters':created})
        print(target,'linked batch',offset//100+1,len(outcomes),'new painters',len(created),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','preflight','apply']);p.add_argument('--target',choices=['local','production']);arg=p.parse_args()
    if arg.command=='plan':plan()
    elif arg.command=='preflight':preflight(arg.target)
    else:apply(arg.target)
