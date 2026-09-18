#!/usr/bin/env python3
"""Withdraw one visually disproved source image; preserve artwork and assets."""
import importlib.util,json
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/overnight-images-20260915'
s=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(s);s.loader.exec_module(core)

def withdraw(im,note,report_stem,receipt=None):
    provider=im['provider']
    review={'at':core.now(),'artwork_id':im['artwork_id'],'media_id':im['media_id'],'provider':provider,'source_object_id':im['external_id'],'status':'withdrawn','reason':note,'source_url':im['page'],'source_image_url':im['source_image_url'],'sha256':im['sha256']}
    registry=RUN/'withdrawn-images.json'
    existing=json.loads(registry.read_text()) if registry.exists() else {'records':[]}
    if not any(r['artwork_id']==im['artwork_id'] and r['media_id']==im['media_id'] for r in existing['records']):
        existing['records'].append(review);temp=registry.with_suffix('.new.json');temp.write_text(json.dumps(existing,ensure_ascii=False,indent=2));temp.replace(registry)
    report=[];backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915/source-image-conflicts'
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
            with db.transaction():
                row=db.execute("""SELECT a.id::text,a.title,a.primary_media_id::text,to_jsonb(a) artwork FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id
                  WHERE e.scheme=%s AND e.external_id=%s FOR UPDATE OF a""",(im['scheme'],im['external_id'])).fetchall()
                assert len(row)==1 and row[0]['id']==im['target_ids'][target] and row[0]['title']==im['title']
                before=backup/(target+'-'+provider+'-'+core.sha(im['external_id'].encode())[:16]+'-before.json')
                evidence=db.execute('SELECT to_jsonb(m) media,to_jsonb(r) rights FROM media_assets m LEFT JOIN media_rights_evidence r ON r.media_id=m.id WHERE m.id=%s',(im['media_id'],)).fetchone()
                if not before.exists():core.save_new(before,{'artwork':row[0],'media_and_rights':evidence})
                current=row[0]['primary_media_id']
                if current not in (None,im['media_id']):raise ValueError('A different primary image is already attached; preserve it')
                if current:
                    db.execute('UPDATE artworks SET primary_media_id=NULL,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id=%s',(core.ACTOR,row[0]['id'],im['media_id']))
                if evidence:
                    db.execute("UPDATE media_rights_evidence SET evidence_json=evidence_json || %s WHERE media_id=%s",(Jsonb({'image_identity_review':review}),im['media_id']))
                sid=db.execute("SELECT source_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(im['scheme'],im['external_id'])).fetchone()['source_id']
                if not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND field_name='image_identity_review' AND source_record_id=%s",(row[0]['id'],im['external_id'])).fetchone():
                    db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'image_identity_review',%s,%s,%s,%s,%s)",(row[0]['id'],sid,im['external_id'],im['page'],note,core.now(),core.ACTOR))
                check=db.execute('SELECT primary_media_id,status FROM artworks WHERE id=%s',(row[0]['id'],)).fetchone();assert check['primary_media_id'] is None and check['status']=='review'
                report.append({'target':target,'artwork_id':row[0]['id'],'outcome':'attachment_withdrawn' if current else 'already_without_image','artwork_retained':True,'asset_retained':True})
        print(target,report[-1]['outcome'],flush=True)
    if receipt is None:receipt=next(json.loads(line)['receipt'] for line in (RUN/'local-attachments.jsonl').read_text().splitlines() if json.loads(line).get('media_id')==im['media_id'])
    journal={'at':core.now(),'provider':provider,'artwork_id':im['artwork_id'],'media_id':im['media_id'],'receipt':receipt,'outcome':'withdrawn','reason':note}
    with (RUN/'local-attachments.jsonl').open('a') as f:f.write(json.dumps(journal)+'\n')
    core.event(Path(receipt).parents[2],{'provider':provider,'artwork_id':im['artwork_id'],'external_id':im['external_id'],'outcome':'metadata_needs_review','reason':note})
    path=RUN/(report_stem+'.json')
    if not path.exists():core.save_new(path,{'at':core.now(),'records':report,'visual_evidence':report_stem,'review':review})

def main():
    images=json.loads((RUN/'identical-images-selected-review.json').read_text());im=next(x for x in images if x['provider']=='met' and x['external_id']=='409630')
    assert im['source_image_url']=='https://images.metmuseum.org/CRDImages/dp/web-large/DP260583.jpg'
    note='Artline visual audit: the reproduction is inscribed Veduta di Campo Vaccino and depicts the Roman Forum. The same source resource is assigned to the separately accessioned Forum print, Met 366647. It does not depict the Colosseum print Met 409630. Withdraw only this primary-image attachment; retain the physical artwork record, source evidence and licensed asset. A corrected independent reproduction is still needed.'
    withdraw(im,note,'source-image-conflict-withdrawal')

if __name__=='__main__':main()
