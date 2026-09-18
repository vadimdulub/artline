#!/usr/bin/env python3
"""Replace this run's QID placeholders with captured, source-language titles."""
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('catalogue', Path(__file__).with_name('apply-wikimedia-catalogues.py'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
r = m.r


def main():
    capture = json.loads((r.RUN/'missing-title-authorities.json').read_text())
    amendments = []
    for qid, entity in capture['data']['entities'].items():
        label = next(iter(entity['labels'].values()))
        assert label['value'] and label['value'] != qid
        amendments.append({'qid':qid, 'title':label['value'], 'language':label['language'], 'artwork_id':m.uid('artwork/'+qid)})
    r.core.save_new(r.RUN/'title-refinements.json', {'amendments':amendments, 'source_receipt':capture['receipt']})
    for target in ('local','production'):
        result = r.RUN/('title-refinements-'+target+'.json')
        if result.exists():continue
        before=[]
        with r.base.connect(target=='production') as db, db.transaction():
            db.execute('SET TRANSACTION READ ONLY')
            for entry in amendments:
                receiptpath=r.RUN/'applied'/target/(entry['qid']+'.json')
                assert receiptpath.exists(), 'Finish batches before refining titles'
                applied=json.loads(receiptpath.read_text())
                assert applied['action']=='new' and applied['artwork_id']==entry['artwork_id']
                row=db.execute('SELECT to_jsonb(a) AS artwork FROM artworks a WHERE id=%s',(entry['artwork_id'],)).fetchone()['artwork']
                assert row['status']=='review' and row['title']==entry['qid']
                media=db.execute('SELECT to_jsonb(ma) AS media FROM media_assets ma WHERE id=%s',(row['primary_media_id'],)).fetchone() if row['primary_media_id'] else None
                before.append({'artwork':row,'media':media['media'] if media else None})
        r.core.save_new(r.BACKUPS/('title-refinements-'+target+'-preimages.json'),before)
        with r.base.connect(target=='production') as db, db.transaction():
            db.execute("SET LOCAL statement_timeout='45s'")
            sid=db.execute("SELECT id FROM sources WHERE slug='wikimedia-catalogue-scan-20260913'").fetchone()['id']
            for entry, old in zip(amendments,before):
                qid=entry['qid'];title=entry['title'];aid=entry['artwork_id'];work=old['artwork']
                updated=db.execute('''UPDATE artworks SET title=%s,normalized_title=%s,description_md=%s,
                    revision=revision+1,updated_at=now(),updated_by=%s
                    WHERE id=%s AND title=%s AND revision=%s RETURNING id''',
                    (title,r.norm(title),work['description_md'].replace(qid,title),m.ACTOR,aid,qid,work['revision'])).fetchone()
                assert updated,'Concurrent title change'
                if old['media']:
                    media=old['media']
                    db.execute('UPDATE media_assets SET alt_text=%s,attribution_text=%s WHERE id=%s',
                        (media['alt_text'].replace(qid,title),media['attribution_text'].replace(qid,title),media['id']))
                r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name='source_language_title',source_id=sid,source_record_id=qid,source_url='https://www.wikidata.org/wiki/'+qid,evidence_note='Source-language title ('+entry['language']+') recovered by fetching all Wikidata label languages. Replaces this import’s QID placeholder; no translation invented. Capture SHA-256: '+capture['receipt']['sha256'],retrieved_at=capture['receipt']['retrieved_at'],created_by=m.ACTOR))
        r.core.save_new(result,{'at':r.core.now(),'updated':amendments})
        print(target,'source-language titles restored',len(amendments),flush=True)


if __name__=='__main__':main()
