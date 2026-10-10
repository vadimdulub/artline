"""Repeat the baseline after a read-only schema mismatch, preserving the failed writer."""
import importlib.util
from pathlib import Path
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
b=module('b','museum-expansion-larissa-baseline-20261010.py')
b.c=module('c','museum-expansion-larissa-common-v2-20261010.py')
if __name__=='__main__':
    assert not list(b.RUN.glob('*scope*'))
    b.m.save(b.RUN/'baseline-schema-observation-001.json',dict(at=b.m.now(),first_attempt='Read-only local snapshot rejected ORDER BY id: media_rights_evidence has a composite key and no id column. Transaction rolled back; no artifacts or database writes.',
        correction='Observed actual column names. V2 orders rights evidence by media_id,source_id,source_record_id; all other baseline guards unchanged.',script_reference=b.c.ref(Path(__file__).resolve())))
    b.main()
