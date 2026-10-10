"""Verify rollback after the old localproxy exited; no database mutation."""
import importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-spathario-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

def main():
    dest=a.RUN/'rolled-back-apply-001.json';assert not dest.exists();p,d=a.validate_plan();r={}
    with a.c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        r['new_records']=db.execute('SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[])',([v['artwork_id'] for v in p['records']],)).fetchone()['n']
        r['new_sources']=db.execute('SELECT count(*) n FROM sources WHERE id=%s',(a.SID,)).fetchone()['n']
        r['new_audits']=db.execute('SELECT count(*) n FROM audit_log WHERE request_id=%s',(a.KEY,)).fetchone()['n']
        r['new_media']=db.execute('SELECT count(*) n FROM media_assets WHERE id=ANY(%s::uuid[])',([v['media_id'] for v in p['images']],)).fetchone()['n']
        a.preflight(db,p);r['preflight_unchanged']=True
    assert r['new_records']==r['new_sources']==r['new_audits']==r['new_media']==0
    a.m.save(dest,dict(at=a.m.now(),**r,error='OperationalError: serverclosedconnection during transaction beforecommit, at current_art after artworkinsert. Firstverification also failed because no listener remained on55519.',connection_evidence='PID5785absent and port55519no listener; CloudSQLinstanceRUNNABLE. Sameverifiedproxybinary restarted asPID19001on127.0.0.1:55519 with--gcloud-auth. No service/database reset.',proxy_pid=19001,proxy_port=55519,proxy_binary_sha256='47c56cc88acd3250ac90b7ad063532cc22a8cca9dd0896012a2a60d1eab4c159',plan_sha256=d,writer_reference=a.c.ref(Path(__file__).with_name('museum-expansion-spathario-apply-20261010.py')),script_reference=a.c.ref(Path(__file__).resolve()),uploaded_images=64,uploaded_images_attached=0,read_only=True))
    print(json.dumps(r),flush=True)

if __name__=='__main__':main()
