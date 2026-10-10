#!/usr/bin/env python3
"""Snapshot accepted museum holdings with bounded, indexed museum pages."""
import argparse
import collections
import gzip
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-artwork-locations-20261004.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
ROOT=r.ROOT/'docs/research/museum-guides-20261005'
PAGE_SQL="""SELECT a.id::text,a.slug,a.title,a.alternate_title,a.date_display,
    a.creation_year_start,a.creation_year_end,a.status,a.accession_number,a.unlinked_creator_label,
    a.research_candidate,a.primary_media_id::text,a.current_institution_id::text,
    h.id::text holding_id,h.source_url,h.checked_at,h.source_updated_at,h.review_state,h.context,
    to_jsonb(m) media,
    CASE WHEN me.media_id IS NOT NULL THEN jsonb_build_object('source_image_url',me.source_image_url,
        'source_record_id',me.source_record_id,'policy_url',me.policy_url,'rights_basis',me.rights_basis,
        'checked_at',me.checked_at,'source_checksum',me.source_checksum) END image_rights_evidence,
    COALESCE((SELECT jsonb_agg(jsonb_build_object('name',ar.display_name,'slug',ar.slug,'role',aa.attribution_role)
        ORDER BY ar.slug) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') artists
    FROM artworks a
    JOIN artwork_location_assertions h ON h.artwork_id=a.id AND h.institution_id=a.current_institution_id
        AND h.claim_type='holding' AND h.review_state='accepted' AND h.superseded_by IS NULL
    LEFT JOIN media_assets m ON m.id=a.primary_media_id
    LEFT JOIN media_rights_evidence me ON me.media_id=m.id
    WHERE a.current_institution_id=%s::uuid AND a.status<>'archived'
        AND (%s::uuid IS NULL OR a.id>%s::uuid) ORDER BY a.id LIMIT 500"""


def snapshot(label):
    folder=ROOT/'snapshots'/label
    assert not (folder/'manifest.json').exists(),'Preserve completed snapshot; choose another label'
    counts=collections.Counter();museums=[];plans=[]
    with r.connect() as db:
        # A consistent read-only snapshot, with no changes to the real catalogue.
        with db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            rows=db.execute("""SELECT to_jsonb(i) institution,count(*) works,count(a.primary_media_id) images
                FROM institutions i JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived'
                JOIN artwork_location_assertions h ON h.artwork_id=a.id AND h.institution_id=i.id
                  AND h.claim_type='holding' AND h.review_state='accepted' AND h.superseded_by IS NULL
                GROUP BY i.id ORDER BY count(*) DESC,i.id""").fetchall()
            captured_at=r.now()
            for n,entry in enumerate(rows,1):
                institution=entry['institution'];iid=institution['id'];cursor=None;works=[]
                if n in [1,12,100]:
                    plan=db.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+PAGE_SQL,(iid,None,None)).fetchone()
                    plans.append({'institution_id':iid,'actual_institution_rows':entry['works'],'plan':plan})
                while True:
                    batch=db.execute(PAGE_SQL,(iid,cursor,cursor)).fetchall()
                    if not batch:break
                    ids=[v['id']for v in batch]
                    externals=collections.defaultdict(list)
                    for ext in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,scheme,external_id",(ids,)):
                        externals[ext.pop('entity_id')].append(ext)
                    for work in batch:work['identifiers']=externals[work['id']]
                    works.extend(batch);cursor=batch[-1]['id']
                assert len(works)==entry['works'],institution['name']
                assert len({v['id']for v in works})==len(works)
                dest=folder/'museums'/(institution['slug']+'.json.gz')
                r.save_gz(dest,{'captured_at':captured_at,'institution':institution,'artworks':works})
                museums.append({**entry,'path':str(dest.relative_to(ROOT)),'sha256':r.sha(dest.read_bytes())})
                counts['artworks']+=len(works);counts['with_media']+=sum(v['media'] is not None for v in works)
                if n%100==0:print('Museum snapshot',label,n,'/',len(rows),'artworks',counts['artworks'],flush=True)
    r.save(folder/'query-plans.json',{'plans':plans,'scope':'Real existing institutions; indexed 500-record keyset pages. No fixture writes. These plans do not establish 10-million-row load performance.'})
    r.save(folder/'manifest.json',{'captured_at':captured_at,'label':label,'read_only':True,'page_size':500,
        'museum_count':len(museums),'counts':dict(counts),'museums':museums})
    print(json.dumps({'label':label,'museums':len(museums),**counts}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('label');snapshot(parser.parse_args().label)
