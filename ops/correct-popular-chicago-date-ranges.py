#!/usr/bin/env python3
"""Preserve explicit abbreviated year ranges omitted by native numeric fields.

Restricted to newly imported records in this pinned plan. Original evidence and
plans remain preserved; corrections carry an independent museum citation.
"""
import argparse,importlib.util,json,copy
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-popular-chicago-catalogue.py'))
r=importlib.util.module_from_spec(s);s.loader.exec_module(r);core=r.core
def main(run):
    if (run/'date-normalization-verified.json').exists():return
    plan=json.loads((run/'plan.json').read_text());changes=[]
    assert core.sha((run/'plan.json').read_bytes())==json.loads((run/'plan-manifest.json').read_text())['sha256']
    for c in plan['records']:
        facts=r.check.metadata(c['source_object'],c['artist_evidence'],c['source_artist'])
        diff={k:v for k,v in facts.items() if c[k]!=v}
        if not diff:continue
        assert set(diff)<={'creation_year_start','creation_year_end','date_precision'} and not c['existing']
        changes.append({'artwork_id':c['artwork_id'],'before':{k:c[k] for k in diff},'after':diff,'source_object_id':c['external_id'],'source_url':c['page'],'source_date_text':c['date_display']})
    backup=r.backup_root(run)/'local-before-date-normalization.json'
    with psycopg.connect('postgres://localhost/artline',row_factory=dict_row,autocommit=True) as db:
        old=db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE id=ANY(%s::uuid[])',([c['artwork_id'] for c in changes],)).fetchall()
        if not backup.exists():core.save_new(backup,old)
        with db.transaction():
            db.execute('SELECT pg_advisory_xact_lock(559220260915)')
            for change in changes:
                c=next(v for v in plan['records'] if v['artwork_id']==change['artwork_id'])
                row=db.execute('SELECT * FROM artworks WHERE id=%s FOR UPDATE',(c['artwork_id'],)).fetchone()
                assert row['status']=='review' and row['published_at'] is None and row['title']==c['title'] and row['date_display']==c['date_display']
                assert all(row[k] in (change['before'][k],v) for k,v in change['after'].items())
                c.update(change['after'])
                db.execute('UPDATE artworks SET creation_year_start=%s,creation_year_end=%s,date_precision=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(c['creation_year_start'],c['creation_year_end'],c['date_precision'],core.ACTOR,c['artwork_id']))
                sid=db.execute("SELECT source_id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=%s AND scheme=%s AND external_id=%s",(c['artwork_id'],r.check.SCHEME,c['external_id'])).fetchone()['source_id']
                db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'creation_year_end',%s,%s,%s,%s,%s)",(c['artwork_id'],sid,c['external_id'],c['page'],json.dumps({'normalization':change,'basis':'Expand the abbreviated end year explicitly written in the museum date_display; retain the native numeric interval uncertainty. No year inferred from artist biography.'}),c['metadata_capture']['retrieved_at'],core.ACTOR))
    draft=run/'review-drafts/before-date-normalization';draft.mkdir(parents=True,exist_ok=True)
    for name in ('plan.json','plan-manifest.json','candidates.json'):
        if not (draft/name).exists():(run/name).rename(draft/name)
    plan['date_normalization']='Explicit abbreviated endpoints in museum date text are retained even when its numeric date_end omits them.'
    core.save_new(run/'plan.json',plan);core.save_new(run/'plan-manifest.json',{'sha256':core.sha((run/'plan.json').read_bytes()),'count':len(plan['records'])})
    candidates=json.loads((draft/'candidates.json').read_text());index={v['artwork_id']:v for v in changes}
    for c in candidates['candidates']:
        change=index.get(c['artwork_id'])
        if not change:continue
        c.update(change['after']);c['date_normalization']=change
        original=run/'selected/chicago'/(c['artwork_id']+'.json');dest=draft/'selected'/original.name;dest.parent.mkdir(exist_ok=True)
        if not dest.exists():original.rename(dest)
        core.save_new(original,c)
    core.save_new(run/'candidates.json',candidates)
    core.save_new(run/'date-normalization-verified.json',{'at':core.now(),'target':'local','corrected':len(changes),'records':changes,'backup':str(backup)})
    print('Source-text date ranges corrected',len(changes))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args();main(a.run)
