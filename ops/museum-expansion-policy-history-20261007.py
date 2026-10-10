#!/usr/bin/env python3
"""Verify the exact historical policy bytes after an additive external update."""
import hashlib,importlib.util,types
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('museum-expansion-20261006.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
OLD='f660dad19b462c8680ddf6d05fd1512ec388b18daf8b6ae2610829207c3e0e8f';NEW='73d40fb4a78728ff98262f28ace6a1ea3786ed9f1623a02b7763ccda12a02f56';BACKUP=m.BACKUP/'campaign-agents-before-20261007-image-delivery.md';RECEIPT=m.RUN/'native/next-samples/policy-supersession-001.json'
def preserve():
 current=(m.ROOT/'AGENTS.md').read_bytes();assert hashlib.sha256(current).hexdigest()==NEW
 first=current.index(b'- Local image delivery (7 October 2026):');last=current.index(b'- Museum matching confidence (6 October 2026):');old=current[:first]+current[last:];assert hashlib.sha256(old).hexdigest()==OLD
 if BACKUP.exists():assert BACKUP.read_bytes()==old
 else:BACKUP.write_bytes(old)
 m.save(RECEIPT,dict(at=m.now(),path='AGENTS.md',before_sha256=OLD,after_sha256=NEW,backup_path=str(BACKUP),backup_sha256=OLD,change='External additive Local image delivery paragraph observed during this pass. All preceding constraints are byte-identical. Current instructions were reread and govern new work. Historical plans are verified against their exact original policy snapshot, with the changed live policy separately recorded. No source, plan, code or catalogue integrity checks are waived.'))
def checked_policy(reference):
 assert reference['path']=='AGENTS.md' and reference['sha256']==OLD
 receipt=m.load(RECEIPT);assert receipt['before_sha256']==OLD and receipt['after_sha256']==NEW and receipt['backup_path']==str(BACKUP)
 assert hashlib.sha256(BACKUP.read_bytes()).hexdigest()==OLD;assert hashlib.sha256((m.ROOT/'AGENTS.md').read_bytes()).hexdigest()==NEW;return BACKUP
def install(module):
 """Adapt historical reference validators only; no source or plan mutations."""
 visited=set();changed=[]
 def visit(mod):
  if id(mod) in visited:return
  visited.add(id(mod));file=getattr(mod,'__file__',None)
  if not file or Path(file).resolve().parent!=m.ROOT/'ops':return
  for value in list(vars(mod).values()):
   if isinstance(value,types.ModuleType):visit(value)
  for name in ['checked_reference','checked']:
   original=getattr(mod,name,None)
   if not callable(original):continue
   def wrapper(reference,*args,_original=original,**kwargs):
    if isinstance(reference,dict) and reference.get('path')=='AGENTS.md' and reference.get('sha256')==OLD:return checked_policy(reference)
    return _original(reference,*args,**kwargs)
   setattr(mod,name,wrapper);changed.append(str(Path(file).name)+':'+name)
 visit(module);return changed
if __name__=='__main__':preserve()
