"""Preserve source profiles and the untouched next-museum baseline; no additions."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-france-fourteenth-discovery-20261008.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
m=d.m;RUN=d.RUN;ref=d.prior.reference

def main():
    dest=RUN/'preparation-checkpoint-001.json';initial=RUN/'initial-scope-001.json.gz';profile=RUN/'discovery-field-profile-001.json';assert not any(p.exists() for p in [dest,initial,profile]);x=m.load(d.DISCOVERY);iids=sorted(v['id'] for v in x['targets']);base=d.prior.r.identity.prior.prior.base
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
        ids=[v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) UNION SELECT artwork_id::text FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) ORDER BY id',(iids,iids))]
        state=base.snapshot(db,ids,iids[0]);state.pop('museum');state['museums']=[v['row'] for v in db.execute('SELECT to_jsonb(x) row FROM institutions x WHERE id=ANY(%s::uuid[]) ORDER BY id',(iids,))]
        mids=sorted({v['media_id'] for v in state['media']}|{v['primary_media_id'] for v in state['artworks'] if v['primary_media_id']});state['media_assets']=[v['row'] for v in db.execute('SELECT to_jsonb(x) row FROM media_assets x WHERE id=ANY(%s::uuid[]) ORDER BY id',(mids,))];counts={iid:base.counts(db,iid) for iid in iids}
    m.save(initial,dict(at=m.now(),scoped_ids=ids,snapshot=state,counts=counts,read_only=True))
    profiles={}
    for target in x['targets']:
        rs=[v['raw_source_record'] for v in x['rows'] if v['museum']['id']==target['id'] and not v['already_known']]
        profiles[target['slug']]=dict(institution_id=target['id'],name=target['name'],unrepresented_source_rows=len(rs),fields={key:dict(collections.Counter(v.get(key) or '' for v in rs)) for key in ['Nom_officiel_musee','Ville','Localisation','Statut_juridique','Domaine','Denomination','Periode_de_creation']})
    m.save(profile,dict(at=m.now(),discovery_reference=ref(d.DISCOVERY),profiles=profiles,policy='Descriptive source-field frequencies, not approval or enrichment. Literal unknowns remain unknown.'))
    captures=[]
    for p in sorted(RUN.glob('museum-context-*/*.receipt.json')):
        receipt=m.load(p);raw=gzip.decompress(p.with_name(p.name.replace('.receipt.json','.html.gz')).read_bytes());assert receipt['status']==200 and hashlib.sha256(raw).hexdigest()==receipt['sha256'];captures.append(receipt)
    assert len(captures)==7
    dependencies={p for p in RUN.rglob('*') if p.is_file()}|{Path(__file__).resolve(),Path(d.__file__).resolve(),m.ROOT/'AGENTS.md'}
    m.save(dest,dict(at=m.now(),read_only=True,database_writes=0,reviewed_objects=0,approved_additions=0,source_rows=len(x['rows']),new_source_rows=sum(not v['already_known'] for v in x['rows']),target_ids=iids,protected_initial_records=len(ids),counts=counts,museum_context_captures=len(captures),dependencies=[ref(p) for p in sorted(dependencies)],prior_delivered_checkpoint=ref(d.prior.RUN/'delivery-checkpoint-001.json'),pending_work=['Reconcile Paris catalogue acquisition-only/blank legal labels without inventing ownership; verify exact source code, named collection and operator evidence.','Reconcile the joint Maison de Victor Hugo / Hauteville House catalogue at collection level, without asserting an object is currently in Paris or on view.','Select eligible independent artworks with literal date/type/custody evidence; bound current object API captures before downloading any reproductions.','Support arts-graphiques records using explicit drawing denomination and physical medium; separate printing matrices, bound illustrations, garments, photographs, paper originals and related published versions.','Reconcile all source IDs, inventories, creator identities and existing objects before any addition. Preserve earlier unresolved holds and unknown metadata.'],policy='Initial research checkpoint only. No selected-object queue, current-object capture, approved import plan or database additions yet. Wave 68 is delivered and immutable. Baltimore and Orsay Coubertin-page access holds remain; no retry or alternate route.'))
    print(json.dumps(dict(source_rows=len(x['rows']),new_source_rows=sum(not v['already_known'] for v in x['rows']),protected_initial_records=len(ids),captures=len(captures),database_writes=0,checkpoint=ref(dest))),flush=True)
if __name__=='__main__':main()
