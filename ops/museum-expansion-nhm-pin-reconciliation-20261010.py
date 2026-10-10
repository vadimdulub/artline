"""Preserve two byte-exact historical helper variants without editing live helpers."""
import ast,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-nhm-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN

def main():
    dest=RUN/'historical-pin-reconciliation-001.json';assert not dest.exists()
    old={x['path']:x for x in m.load(c.CP)['artifacts']};plan=m.load(RUN/'nhm-production-001-plan-001.json.gz')
    conflicts=[x for x in plan['evidence'] if x['path'] in old and old[x['path']]!=x]
    assert {x['path'] for x in conflicts}=={'ops/museum-expansion-larissa-common-20261010.py','ops/museum-expansion-larissa-common-v2-20261010.py'}
    folder=c.PROOF/'historical-helper-variants';folder.mkdir(parents=True,exist_ok=True);rows=[]
    for now in conflicts:
        p=m.ROOT/now['path'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==now['sha256']
        previous=raw+b'\n';before=old[now['path']];assert hashlib.sha256(previous).hexdigest()==before['sha256']
        assert ast.dump(ast.parse(raw))==ast.dump(ast.parse(previous))
        refs={}
        for label,data in [('inherited',previous),('nhm-used',raw)]:
            target=folder/(p.stem+'-'+label+'.py');assert not target.exists();target.write_bytes(data);refs[label]=dict(path=str(target),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
        rows.append(dict(logical_path=now['path'],inherited_pin=before,nhm_plan_pin=now,inherited_byte_copy=refs['inherited'],nhm_used_byte_copy=refs['nhm-used'],observed_mtime=datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat(),difference='Exactly one final LF byte removed; no source-code or AST change.',ast_equal=True))
    value=dict(at=m.now(),rows=rows,previous_checkpoint_reference=c.ref(c.CP),nhm_plan_reference=c.ref(RUN/'nhm-production-001-plan-001.json.gz'),script_reference=c.ref(Path(__file__).resolve()),current_files_edited=False,prior_checkpoints_edited=False,plan_edited=False,database_writes=False,actor_or_cause='Not established. Both file mtimes are17:21UTC, after NHM17:08baseline and before its pinned production plan. Do not attribute the change to a user or process without evidence.',resolution='Descendant checkpoint may retain the NHM plan pins for the current logical paths and record both inherited pins and byte-exact historical copies as explicit artifact revisions. Prior checkpoint and plan pins remain untouched. Historical copies reproduce the exact inherited SHA256 values; both versions have identical ASTs. This is provenance reconciliation, not a new catalogue change.')
    m.save(dest,value);print(json.dumps(dict(reconciled=len(rows),difference='one trailing LF per file',historical_hashes_reproduced=True,current_files_edited=False)),flush=True)

if __name__=='__main__':main()
