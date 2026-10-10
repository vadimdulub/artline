"""Use the observed composite-key media rights schema in read-only snapshots."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('base',Path(__file__).with_name('museum-expansion-larissa-common-20261010.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
module,s,prod,m,IID,IIDS,RUN,RESEARCH,CP,CP_SHA,RESEARCH_CP,RESEARCH_SHA,ref,checked,counts,research_verify=(getattr(base,k) for k in ['module','s','prod','m','IID','IIDS','RUN','RESEARCH','CP','CP_SHA','RESEARCH_CP','RESEARCH_SHA','ref','checked','counts','research_verify'])

def snapshot(db,ids):
    out=s.snapshot(db,ids);mids=[v['id'] for v in out['media_assets']]
    out['media_rights_evidence']=[v['row'] for v in db.execute('SELECT to_jsonb(x) row FROM media_rights_evidence x WHERE media_id=ANY(%s::uuid[]) ORDER BY media_id,source_id,source_record_id',(mids,))]
    return out
