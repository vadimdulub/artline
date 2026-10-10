"""Capture concurrent comparison-set image additions without changing the delivery."""
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-larissa-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
c,m,RUN=a.c,a.m,a.RUN

def main():
    old=m.load(RUN/'production-identity-001.json.gz');state=old['state'];ids=state['artwork_ids']
    oldc=m.load(RUN/'production-identity-citations-001.json.gz')['citations']
    protected=set(m.load(RUN/'focused-comparators-001.json.gz')['ids'])|set(m.load(RUN/'production-initial-scope-001.json.gz')['scoped_ids'])|set(m.load(RUN/'baseline-verification-001.json')['prior_production_ids'])
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        current=db.execute('SELECT '+a.identity.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(ids,)).fetchall()
        links=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id,aa.attribution_role',(ids,)).fetchall()
        cites=[v['row'] for v in db.execute("SELECT to_jsonb(x) row FROM citations x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(ids,))]
        assert links==state['creator_links']
        assert len(current)==len(state['artworks']);changes=[]
        for before,after in zip(state['artworks'],current):
            assert before['id']==after['id']
            if before!=after:
                fields=sorted(k for k in before if before[k]!=after[k])
                assert fields==['primary_media_id'] and before['primary_media_id'] is None and after['primary_media_id']
                assert before['id'] not in protected
                changes.append(dict(id=before['id'],before=before,after=after,fields=fields))
        oldby={x['id']:x for x in oldc};nowby={x['id']:x for x in cites}
        assert all(nowby.get(k)==v for k,v in oldby.items())
        added=[x for x in cites if x['id'] not in oldby]
        assert all(x['entity_id'] not in protected for x in added)
        changed_ids=[x['id'] for x in changes]
        changed_snapshot=c.snapshot(db,changed_ids)
    m.save(RUN/'production-identity-refresh-001.json.gz',dict(at=m.now(),read_only=True,artwork_ids=ids,artworks=current,creator_links=links,citations=cites,changes=changes,added_citations=added,changed_snapshot=changed_snapshot,old_references=[c.ref(RUN/'production-identity-001.json.gz'),c.ref(RUN/'production-identity-citations-001.json.gz')],script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(changed=len(changes),added_citations=added,changed_ids=changed_ids),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
