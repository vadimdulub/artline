import importlib.util,sys,re
s=importlib.util.spec_from_file_location('d','ops/deliver-max-liebermann-20261011.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
BASE=m.RUN;OLD_BACKUP=m.BACKUP;m.RUN=BASE/'smk-supplement';m.BACKUP=OLD_BACKUP/'smk-supplement';m.OP+='-smk-supplement'
def prepare():
 base=m.r.load(BASE/'reviewed-plan.json.gz');rows=[]
 for x in base['held']:
  if x['reason']!='object_type_requires_review' or x['source']!='SMK – National Gallery of Denmark':continue
  y,reason=m.normalize(x['record']['raw']);assert reason is None
  cfg=base['configuration'][y['source']];y.update(institution_id=cfg[1],source_scheme=cfg[2],provider=cfg[0],id=m.uid('artwork/'+cfg[0]+'/'+y['source_id']),slug='liebermann-smk-'+y['source_id'].lower())
  if y['date_display']=='1847-1935':y.update(creation_year_start=None,creation_year_end=None,date_precision='unknown',physical_unit_note='Museum gives the artist lifespan as its broad date range; numeric creation date left unknown. Original literal range retained.')
  rows.append(y)
 assert len(rows)==8
 with m.r.connect('production')as db:
  ids=[x['id']for x in db.execute("SELECT a.id::text FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=%s AND a.status<>'archived'",(m.AID,)).fetchall()];assert len(ids)==788
  current=m.b.s.snapshots(db,ids);artist=db.execute('SELECT to_jsonb(a) a FROM artists a WHERE id=%s',(m.AID,)).fetchone()['a']
 m.r.save_gz(m.RUN/'existing.json.gz',dict(rows=[dict(artwork=x['artwork'])for x in current.values()]))
 p=dict(at=m.d.now(),artist=artist,rows=rows,link_existing=[],configuration={'SMK – National Gallery of Denmark':base['configuration']['SMK – National Gallery of Denmark']},baseline_count=788,policy='Danish native object names Tegning and Litografi, creator authority 31761_person. Three artist-lifespan date ranges remain numeric unknowns. No images or display claims.')
 m.validate(p);m.r.save_gz(m.RUN/'reviewed-plan.json.gz',p);m.r.save(m.BACKUP/'cloud-backup.json',m.r.load(OLD_BACKUP/'cloud-backup.json'));print('Prepared 8 source-verified SMK records',flush=True)
if sys.argv[1]=='prepare':prepare()
else:getattr(m,sys.argv[1])()
