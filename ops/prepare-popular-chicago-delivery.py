#!/usr/bin/env python3
"""Check the production metadata and back up target rows before image delivery.

Run after import-popular-chicago-catalogue.py --target cloud. Read-only database
queries; the manifest and external preimage backup are the only writes.
"""
import argparse,importlib.util,json
from pathlib import Path
from psycopg.types.json import Jsonb
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-popular-chicago-catalogue.py'))
r=importlib.util.module_from_spec(s);s.loader.exec_module(r);core=r.core
def main(run):
    reviewed={c['artwork_id']:c['image_sha256'] for c in json.loads((run/'reviewed-images.json').read_text())['records']}
    paths=list(run.glob('images/*/*.json'))+list(run.glob('*/images/*/*.json'))
    images=[json.loads(p.read_text()) for p in paths if p.stem in reviewed]
    commons=r.module('chicago_commons_delivery','popular-chicago-commons.py')
    for im in images:
        assert reviewed[im['artwork_id']]==im['sha256']
        if im['provider']=='chicago':assert r.check.image(im['source_object'],im['raw']['verified_image_resource'])==im['source_image_url']
        elif im['provider']==commons.PROVIDER:commons.verify(im)
        else:raise ValueError('Unreviewed delivery adapter')
    requests=[{k:im[k] for k in ('artwork_id','scheme','external_id')} for im in images]
    with r.campaign.read_only(core.cloud_dsn()) as db:
        rows=db.execute("""WITH requested AS (SELECT * FROM jsonb_to_recordset(%s) AS x(artwork_id text,scheme text,external_id text))
          SELECT q.artwork_id local_id,to_jsonb(a) artwork,
          ARRAY(SELECT to_jsonb(aa) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creators,
          ARRAY(SELECT to_jsonb(e2) FROM external_identifiers e2 WHERE e2.entity_type='artwork' AND e2.entity_id=a.id) identifiers,
          ARRAY(SELECT ar.slug FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id) artist_slugs,
          i.slug institution_slug
          FROM requested q JOIN external_identifiers e ON e.entity_type='artwork' AND e.scheme=q.scheme AND e.external_id=q.external_id
          JOIN artworks a ON a.id=e.entity_id JOIN institutions i ON i.id=a.current_institution_id""",(Jsonb(requests),)).fetchall()
    assert len(rows)==len(images)==len({v['local_id'] for v in rows}),'Production source identity missing or ambiguous'
    idx={v['local_id']:v for v in rows}
    for im in images:
        row=idx[im['artwork_id']];a=row['artwork']
        assert all(a[k]==im[k] for k in ('slug','title','accession_number','creation_year_start','creation_year_end','date_precision','date_display','work_type'))
        assert a['status']=='review' and a['published_at'] is None and a['primary_media_id'] in (None,im['media_id'])
        assert row['artist_slugs']==im['artist_slugs'] and row['institution_slug']==r.check.SLUG
    backup=r.backup_root(run)/('cloud-selected-before-images-'+core.sha(core.encode(rows))[:16]+'.json')
    core.save_new(backup,rows)
    manifest=json.loads((run/'backups.json').read_text())
    prior=r.backup_root(run)/('backups-manifest-'+core.sha(core.encode(manifest))[:16]+'.json');core.save_new(prior,manifest)
    manifest.setdefault('targets',{})['cloud']={'path':str(backup),'sha256':core.sha(backup.read_bytes())}
    manifest.pop('cloud',None)
    temporary=run/'backups.next.json';temporary.write_bytes(core.encode(manifest));temporary.replace(run/'backups.json')
    print('Production image targets and external preimage backup verified',len(images))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args();main(a.run)
