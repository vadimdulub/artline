"""Read-only checksum resolution for evidence moved by the concurrent storage cleanup.

No restoration, archive mutation or database access. Checked paths may be absent:
callers use this helper to validate logical pins, not to load missing file bytes.
"""
import hashlib,json,subprocess,tarfile
from pathlib import Path
BASE=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/project-cleanup-20261009')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
class Resolver:
 def __init__(self,root,pins):
  self.root=root;self.pins={};self.members={};self.manifests={};self.verified={};self.archives={}
  for v in pins:
   if v['path'] in self.pins:assert self.pins[v['path']]['sha256']==v['sha256']
   self.pins[v['path']]=v
  self.refresh()
 def refresh(self):
  for p in sorted(BASE.glob('*.manifest.json')):
   if str(p) in self.manifests:continue
   v=json.loads(p.read_text());selected={r['path']:r for r in v['files'] if r['path'] in self.pins}
   for name,r in selected.items():assert r['sha256']==self.pins[name]['sha256'],name;assert name not in self.members
   self.manifests[str(p)]=dict(path=str(p),sha256=sha(p),archive=v['archive'],archive_sha256=v['archive_sha256'],selected=selected)
   for name,r in selected.items():self.members[name]=(str(p),r)
 def verify_archive(self,manifest_path):
  info=self.manifests[manifest_path];archive=Path(info['archive']);selected=info['selected']
  if str(archive) in self.archives:return
  assert archive.is_file() and sha(archive)==info['archive_sha256'];proc=subprocess.Popen(['zstd','-q','-d','-c',str(archive)],stdout=subprocess.PIPE);found=set()
  try:
   with tarfile.open(fileobj=proc.stdout,mode='r|') as tar:
    for member in tar:
     if member.name not in selected:continue
     exp=selected[member.name];assert member.isfile() and member.name not in found and member.size==exp['bytes'];h=hashlib.sha256()
     with tar.extractfile(member) as fp:
      while chunk:=fp.read(1024*1024):h.update(chunk)
     assert h.hexdigest()==exp['sha256'];found.add(member.name);self.verified[member.name]=dict(path=member.name,sha256=exp['sha256'],bytes=exp['bytes'],archive_path=str(archive),archive_sha256=info['archive_sha256'],manifest_path=manifest_path,manifest_sha256=info['sha256'])
   while proc.stdout.read(1024*1024):pass
   assert proc.wait()==0 and found==selected.keys()
  except BaseException:proc.kill();proc.wait();raise
  self.archives[str(archive)]=dict(path=str(archive),sha256=info['archive_sha256']);print(json.dumps(dict(archive=archive.name,verified_campaign_members=len(found))),flush=True)
 def checked(self,dep):
  p=self.root/dep['path']
  if p.exists():assert sha(p)==dep['sha256'],dep['path'];return p
  self.refresh();assert dep['path'] in self.members,'Missing evidence is not in a verified archive: '+dep['path'];manifest,row=self.members[dep['path']];assert row['sha256']==dep['sha256'];self.verify_archive(manifest);assert self.verified[dep['path']]['sha256']==dep['sha256'];return p
 def verify_available_archives(self):
  self.refresh()
  for name,info in list(self.manifests.items()):
   if info['selected']:self.verify_archive(name)
 def result(self):
  return dict(archive_members=list(self.verified.values()),archive_references=list(self.archives.values()),manifest_references=[dict(path=k,sha256=v['sha256']) for k,v in self.manifests.items() if v['selected']],policy='External cleanup relocation,not deletion or catalogue mutation. Original logical evidence paths and hashes preserved; selected decompressed archive members independently SHA256-verified. No files restored and no archives changed.')
