"""Bounded follow-up on mosaic subjects and translated icon titles; read only."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-mbp-more-identity-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);m=i.m;RUN=i.RUN
with i.prod.connect()as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
 arts=db.execute('SELECT '+i.q.ARTCOLS+" FROM artworks a WHERE normalized_title LIKE ANY(%s) ORDER BY id LIMIT 1001",(['%peacock%','%demetr%','%acheirop%','%potiphar%','%palaiolog%'],)).fetchall();assert len(arts)<=1000
 ids=[a['id']for a in arts];snap=i.s.snapshot(db,ids)
m.save(RUN/'subject-comparators-001.json.gz',dict(at=m.now(),artworks=arts,snapshot=snap,read_only=True,script_reference=i.s.ref(Path(__file__).resolve())))
for a in arts:print(json.dumps({k:a[k]for k in ['id','title','accession_number','date_display','dimensions_text','current_institution_id']},ensure_ascii=False))
