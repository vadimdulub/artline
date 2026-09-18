#!/usr/bin/env python3
"""Preserve primary French object evidence and four individually reviewed corrections."""
import argparse,importlib.util,json
from pathlib import Path
from psycopg import sql
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;RUN=m.x.SESSION_BASE/'france/primary-objects';SOURCE='overnight-french-primary-review-20260913'
CORRECTIONS={
 'Q112080411':dict(role='attributed_to',note='POP/Joconde06070000369 explicitly qualifies Charles de La Fosse as attributed. Preserve uncertain maker attribution.',updates=dict(description_md='Susanna and the Elders, attributed to Charles de La Fosse in the primary museum catalogue. Creation date remains under review.')),
 'Q139792106':dict(updates=dict(work_type='drawing',medium_text='Pastel on paper',dimensions_text='34 × 49 cm'),note='POP/Joconde06070001948 classifies the exact MI.899.5.26 object as dessin and pastel,papier. Distinct from companion MI.899.5.25.'),
 'Q115754179':dict(updates=dict(date_display='c. 1890',date_precision='circa'),note='POP/Joconde03110005517 explicitly dates the exact907.19.60 object 1890vers. Preserve approximate dating rather than exact1890.'),
 'Q131754458':dict(role='attributed_to',updates=dict(unlinked_creator_label='Alternatively attributed to Jean-Baptiste Tonnesse',description_md='Marcus Curius Dentatus refusing the gifts of the Samnites, 1776. The museum attributes the painting to either Anne-Nicolas Dubois or Jean-Baptiste Tonnesse; its curatorial history explicitly says the attribution cannot yet be resolved. These are alternative makers, not collaborators.'),note='POP/Joconde01370031391 historical commentary explicitly says either Dubois or Tonnesse, unresolved. One attributed_to link and a source-named alternative preserve this uncertainty without inventing a second artist identity.')}
def plan():
    dest=RUN/'review-plan.json'
    if dest.exists():return
    records=[e for p in sorted(RUN.glob('round-*/research.json')) for e in json.loads(p.read_text())['records']];targets={};entries=[];holds=[]
    for target in ('local','production'):
        rows={}
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY')
            for e in records:
                q=e['qid'];found=db.execute("SELECT to_jsonb(w) work FROM artworks w JOIN external_identifiers ei ON ei.entity_id=w.id AND ei.entity_type='artwork' WHERE ei.scheme='wikidata' AND ei.external_id=%s",(q,)).fetchall()
                if len(found)!=1:continue
                w=found[0]['work'];assert w['status']=='review' and w['published_at'] is None
                links=db.execute('SELECT to_jsonb(aa) row FROM artwork_artists aa WHERE artwork_id=%s ORDER BY artist_id,attribution_role',(w['id'],)).fetchall()
                rows[q]=dict(work=w,links=[r['row'] for r in links])
        targets[target]=rows;CORE.save_new(m.BACKUPS/f'french-primary-review-{target}-preimages.json',rows)
    for e in records:
        q=e['qid']
        if q not in targets['local'] or q not in targets['production']:holds.append(dict(qid=q,reason='Candidate not applied in both databases'));continue
        a=targets['local'][q]['work'];b=targets['production'][q]['work'];assert all(a[k]==b[k] for k in ('slug','title','creation_year_start','creation_year_end','date_precision','accession_number','status','work_type'))
        correction=CORRECTIONS.get(q,dict(updates={},note='Primary source fields retained with their uncertainty. Conflicting accession, maker and chronology are evidence for further review, not silently replaced.'))
        if q in CORRECTIONS:
            assert m.m.accession_key(a['accession_number'])==m.m.accession_key(e['primary']['fields']["Numéro d'inventaire"])
            if correction.get('role'):
                for t in targets:assert len(targets[t][q]['links'])==1 and targets[t][q]['links'][0]['attribution_role']=='primary'
            if q=='Q115754179':assert a['creation_year_start']==a['creation_year_end']==1890
            if q=='Q131754458':assert 'soit' in e['primary']['fields']['Historique'] and 'Tonnesse' in e['primary']['fields']['Historique']
        entries.append(dict(qid=q,evidence=e,correction=correction))
    assert set(CORRECTIONS)<=set(e['qid'] for e in entries)
    CORE.save_new(dest,dict(at=CORE.now(),entries=entries,targets=targets,holds=holds));CORE.save_new(RUN/'review-manifest.json',dict(at=CORE.now(),plan_sha256=CORE.sha(dest.read_bytes()),objects=len(entries),individual_corrections=len(CORRECTIONS),review='All captured primary author, chronology, medium and object-context fields individually inspected. Alternative versus collaborative attribution explicitly checked in historical commentary. Images/assets and publication status preserved.'));print('French primary reviewplan',len(entries),'corrections4',flush=True)
def apply():
    raw=(RUN/'review-plan.json').read_bytes();data=json.loads(raw);pin=CORE.sha(raw);assert pin==json.loads((RUN/'review-manifest.json').read_text())['plan_sha256']
    for target in ('local','production'):
        done=RUN/f'review-{target}-verified.json'
        if done.exists():continue
        with m.m.r.base.connect(target=='production') as db:
            with db.transaction():
                db.execute('SELECT pg_advisory_xact_lock(559220260914)');sid=m.m.source(db,SOURCE,'French primary museum object review: catalogue context and qualified attribution','collection_page','https://pop.culture.gouv.fr/')
                for e in data['entries']:
                    q=e['qid'];old=data['targets'][target][q];aid=old['work']['id'];ev=e['evidence'];cor=e['correction']
                    if db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND source_record_id=%s AND evidence_note LIKE %s",(aid,sid,ev['pop_id'],'%'+pin+'%')).fetchone():continue
                    assert db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE id=%s FOR UPDATE',(aid,)).fetchone()['row']==old['work']
                    fields=cor.get('updates',{})
                    if fields:
                        query=sql.SQL('UPDATE artworks SET {},revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s').format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in fields));db.execute(query,(*fields.values(),m.m.ACTOR,aid))
                    if cor.get('role'):
                        link=old['links'][0];assert db.execute('UPDATE artwork_artists SET attribution_role=%s,attribution_note=%s WHERE artwork_id=%s AND artist_id=%s AND attribution_role=%s',(cor['role'],cor['note'],aid,link['artist_id'],link['attribution_role'])).rowcount==1
                    receipt=ev['primary']['receipt'];m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,source_id=sid,field_name='primary_object_review',source_record_id=ev['pop_id'],source_url=receipt['url'],retrieved_at=receipt['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps(dict(plan_sha256=pin,evidence=ev,individual_review=cor,publication_status='review',country_policy='Object school field retained as catalogue context; not automatic maker nationality.'),ensure_ascii=False)))
            with db.transaction():
                db.execute('SET TRANSACTION READ ONLY')
                for e in data['entries']:
                    old=data['targets'][target][e['qid']];cor=e['correction'];now=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE id=%s',(old['work']['id'],)).fetchone()['row'];expected={**old['work'],**cor.get('updates',{})};ignore={'revision','updated_at','updated_by'}
                    assert {k:v for k,v in now.items() if k not in ignore}=={k:v for k,v in expected.items() if k not in ignore}
                    if cor.get('role'):assert db.execute('SELECT attribution_role,attribution_note FROM artwork_artists WHERE artwork_id=%s',(now['id'],)).fetchone()==dict(attribution_role=cor['role'],attribution_note=cor['note'])
        CORE.save_new(done,dict(at=CORE.now(),plan_sha256=pin,objects_cited=len(data['entries']),individual_corrections=4,images_and_review_preserved=True));print(target,'French primary objects verified',len(data['entries']),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);a=p.parse_args();globals()[a.command]()
