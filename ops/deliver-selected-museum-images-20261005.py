#!/usr/bin/env python3
"""Deliver only already prepared, licensed <=100KB museum images, with backups."""
import argparse,collections,importlib.util,json
from pathlib import Path
from types import SimpleNamespace
from psycopg.conninfo import make_conninfo
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('audit-museum-gaps-20261005.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);r=a.r
s=importlib.util.spec_from_file_location('core',Path(__file__).with_name('enrich-artwork-images.py'));core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
RUN=r.RUN/'open-images-01';BACKUP=Path.home()/'Library/Application Support/Artline/backups/selected-museum-images-20261005'

def main():
 images=[json.loads(p.read_text())for p in sorted((RUN/'images').glob('*/*.json'))];assert images
 groups=collections.defaultdict(list)
 for im in images:
  body=(r.ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert len(body)<=100000 and core.sha(body)==im['sha256'];core.validate_source_image_identity(im);groups[im['provider']].append(im)
 for target in ['local','production']:
  with r.connect(target)as db:
   rows=[]
   for im in images:
    found=db.execute('''SELECT to_jsonb(a) artwork,to_jsonb(e) identifier FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id
    WHERE e.entity_type='artwork' AND e.scheme=%s AND e.external_id=%s AND a.status<>'archived' ''',(im['scheme'],im['external_id'])).fetchall()
    assert len(found)==1;record=found[0]['artwork'];assert record['title']==im['title'] and record['date_display']==im['date_display'];assert record['primary_media_id']in (None,im['media_id']);rows.extend(found)
   r.save_gz(BACKUP/(target+'-before.json.gz'),rows)
 with r.connect('production')as db:dsn=make_conninfo(host='127.0.0.1',port='55445',dbname=db.info.dbname,user=db.info.user,password=db.info.password,sslmode='disable')
 for provider,items in groups.items():
  core.worker(provider,items,SimpleNamespace(run=RUN,prepare_only=False,upload_prepared_only=True),dsn)
 print(dict(core.COUNTS))

if __name__=='__main__':main()
