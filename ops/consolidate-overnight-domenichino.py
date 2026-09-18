#!/usr/bin/env python3
"""Merge Domenichino/Le Dominiquin with an atomic obsolete-authority repair."""
import argparse,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
from psycopg import sql
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('consolidate-overnight-painters.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
m=c.m;CORE=m.m.core;c.RUN=m.x.BASE/'duplicates/domenichino-consolidation';m.BACKUPS=m.BACKUPS/'domenichino-consolidation';SOURCE='overnight-domenichino-primary-20260913'
OLD='domenichino-q109294631';KEEP='le-dominiquin-round2-033f8b250c97';OLDQ='Q109294631';Q='Q320118'

def plan():
    if (c.RUN/'plan.json').exists():return
    path=m.x.BASE/'duplicates/redirect-person-primary/domenichino.html';raw=path.read_bytes();receipt=json.loads(path.with_suffix('.receipt.json').read_text());assert CORE.sha(raw)==receipt['sha256'];text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
    assert all(x in text for x in ('1581-1641','Domenichino','Le Dominiquin','ZAMPIERI Domenico'))
    wiki=json.loads((m.x.r.RUN/'entities'/(OLDQ+'.json')).read_text());assert wiki['entity']['id']==Q and all(n in m.m.r.labels(wiki['entity']) for n in ('Domenichino','Le Dominiquin'))
    e=dict(qid=Q,old_slug=OLD,canonical_slug=KEEP,evidence=dict(primary_url=receipt['url'],primary_receipt=receipt,authority_receipt=wiki['receipt'],decision='Louvre creator2769 explicitly lists Domenichino and Le Dominiquin as synonyms of Domenico Zampieri1581–1641. Wikidata oldQ109294631 redirects toQ320118 already owned by LeDominiquin. Preserve old identifier row under wikidata-redirect and consolidate all relationships atomically; retain original numeric dates, biographies, images and review.'),targets={})
    for target in ('local','production'):
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');deps=c.dependencies(db);rows={r['row']['slug']:r['row'] for r in db.execute('SELECT to_jsonb(a) row FROM artists a WHERE slug=ANY(%s)',([OLD,KEEP],))};assert len(rows)==2
            old=rows[OLD];keep=rows[KEEP];assert all(a['status']=='review' and a['published_at'] is None and a['entity_type']=='person' and [a['birth_year'],a['death_year']]==[1581,1641] for a in rows.values());assert not old['biography_md'] and not old['portrait_media_id']
            snap=c.snapshot(db,old['id'],keep['id'],deps);overlaps=c.overlaps(db,old['id'],keep['id'],deps);assert overlaps==['external_identifier_scheme_overlap']
            oldident=next(i for i in snap['external_identifiers'] if i['entity_id']==old['id'] and i['scheme']=='wikidata');assert oldident['external_id']==OLDQ
            assert any(i['entity_id']==keep['id'] and i['scheme']=='wikidata' and i['external_id']==Q for i in snap['external_identifiers']);assert not any(i['scheme']=='wikidata-redirect' for i in snap['external_identifiers'])
            e['targets'][target]=dict(old_id=old['id'],canonical_id=keep['id'],old_authority_id=oldident['id'],old_signature=c.signature(old),canonical_signature=c.signature(keep),dependencies=deps)
            CORE.save_new(m.BACKUPS/f'painter-consolidation-{target}-preimages.json',dict(at=CORE.now(),pairs={Q:snap}))
    assert e['targets']['local']['old_signature']==e['targets']['production']['old_signature'] and e['targets']['local']['canonical_signature']==e['targets']['production']['canonical_signature']
    CORE.save_new(c.RUN/'plan.json',[e]);CORE.save_new(c.RUN/'manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha((c.RUN/'plan.json').read_bytes()),confirmed_pairs=1));print('Domenichino atomic authority/identity plan prepared',flush=True)

def apply():
    raw=(c.RUN/'plan.json').read_bytes();pin=CORE.sha(raw);assert pin==json.loads((c.RUN/'manifest.json').read_text())['plan_sha256'];qa=json.loads((c.RUN/'quality-review.json').read_text());assert qa['approved'] and qa['plan_sha256']==pin;e=json.loads(raw)[0]
    for target in ('local','production'):
        dest=c.RUN/'applied'/target/(Q+'.json')
        if dest.exists():continue
        before=json.loads((m.BACKUPS/f'painter-consolidation-{target}-preimages.json').read_text())['pairs'][Q];t=e['targets'][target];old=t['old_id'];keep=t['canonical_id']
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SELECT pg_advisory_xact_lock(559220260914)');db.execute('SELECT id FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',([old,keep],)).fetchall();sid=m.m.source(db,SOURCE,'Louvre Domenichino/Le Dominiquin identity and Wikidata redirect review','authority_data',e['evidence']['primary_url'])
            done=db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s AND field_name='duplicate_identity' AND evidence_note LIKE %s",(keep,sid,'%'+pin+'%')).fetchone()
            if not done:
                deps=c.dependencies(db);assert c.snapshot(db,old,keep,deps)==before;assert c.overlaps(db,old,keep,deps)==['external_identifier_scheme_overlap']
                assert db.execute("UPDATE external_identifiers SET scheme='wikidata-redirect' WHERE id=%s AND scheme='wikidata' AND external_id=%s",(t['old_authority_id'],OLDQ)).rowcount==1
                assert not c.overlaps(db,old,keep,deps)
                workids=[r['artwork_id'] for r in db.execute('SELECT artwork_id FROM artwork_artists WHERE artist_id=%s',(old,))]
                for table,column in deps:db.execute(sql.SQL('UPDATE {} SET {}=%s WHERE {}=%s').format(sql.Identifier(table),sql.Identifier(column),sql.Identifier(column)),(keep,old))
                for table in ('citations','external_identifiers','slug_redirects'):db.execute(sql.SQL("UPDATE {} SET entity_id=%s WHERE entity_type='artist' AND entity_id=%s").format(sql.Identifier(table)),(keep,old))
                db.execute("INSERT INTO artist_aliases(artist_id,alias,normalized_alias,alias_type) VALUES(%s,'Domenichino','domenichino','historical') ON CONFLICT DO NOTHING",(keep,));db.execute("INSERT INTO slug_redirects(entity_type,entity_id,old_slug) VALUES('artist',%s,%s)",(keep,OLD))
                db.execute("UPDATE artists SET status='archived',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(m.m.ACTOR,old));db.execute('UPDATE artists SET revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(m.m.ACTOR,keep))
                if workids:db.execute('UPDATE artworks SET revision=revision+1,updated_at=now(),updated_by=%s WHERE id=ANY(%s::uuid[])',(m.m.ACTOR,workids))
                m.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=keep,source_id=sid,field_name='duplicate_identity',source_record_id=OLD,source_url=e['evidence']['primary_url'],retrieved_at=e['evidence']['primary_receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,primary=e['evidence'],obsolete_authority=dict(id=t['old_authority_id'],old_scheme='wikidata',new_scheme='wikidata-redirect',old_qid=OLDQ,canonical_qid=Q),original_profile_id=old,canonical_profile_id=keep),ensure_ascii=False)))
        CORE.save_new(dest,dict(at=CORE.now(),plan_sha256=pin,old_slug=OLD,canonical_slug=KEEP));print(target,'Domenichino consolidated',flush=True)

def verify():
    c.verify()
    for target in ('local','production'):
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY');e=json.loads((c.RUN/'plan.json').read_text())[0];t=e['targets'][target];before=json.loads((m.BACKUPS/f'painter-consolidation-{target}-preimages.json').read_text())['pairs'][Q]
            current={r['row']['id']:r['row'] for r in db.execute("SELECT to_jsonb(e) row FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s",(t['canonical_id'],))}
            for row in before['external_identifiers']:assert current[row['id']]=={**row,'entity_id':t['canonical_id'],'scheme':'wikidata-redirect' if row['id']==t['old_authority_id'] else row['scheme']}
    CORE.save_new(c.RUN/'authority-preservation-verified.json',dict(at=CORE.now(),old_qid=OLDQ,canonical_qid=Q,verified_both=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);args=p.parse_args();globals()[args.command]()
