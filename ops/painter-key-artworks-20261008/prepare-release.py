import pathlib,subprocess,json,base64,hashlib,tarfile,difflib,shutil
root=pathlib.Path.cwd();out=pathlib.Path.home()/'Library/Application Support/Artline/backups/key-artworks-20261008';work=pathlib.Path(__file__).parent
prior=out.parent/'public-cleanup-20261008'
changes={'web':['components/ArtistRecord.tsx','components/ArtistChronologyRecord.tsx','lib/types.ts','app/globals.css'],'api':['internal/catalog/repository.go','internal/catalog/types.go','internal/catalog/artist_key_artwork.go','db/migrations/0037_artist_key_artworks.sql']}
for service,buildid in [('web','b3386432-ea4a-4c5a-be30-9d193ed88d81'),('api','62cef1d1-67b3-49ee-8fe6-f000821883a2')]:
 if service=='web' and (out/'web-prepared-source.tgz').exists():continue
 def cloud(args):return subprocess.check_output(['gcloud',*args,'--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True)
 state=json.loads(cloud(['run','services','describe','artline-'+service,'--region=europe-west1']));(out/(service+'-deploy-preflight.json')).write_text(json.dumps(state))
 build=json.loads(cloud(['builds','describe',buildid]+(['--region=europe-west1'] if service=='api' else [])));(out/(service+'-baseline-build.json')).write_text(json.dumps(build))
 digest=build['results']['images'][0]['digest']; active=[t['revisionName'] for t in state['status']['traffic'] if t.get('percent')]; assert len(active)==1; serving=json.loads(cloud(['run','revisions','describe',active[0],'--region=europe-west1'])); assert serving['spec']['containers'][0]['image'].endswith('@'+digest),'New live release detected'; (out/(service+'-serving-revision.json')).write_text(json.dumps(serving))
 source=build['sourceProvenance']['resolvedStorageSource'];uri='gs://'+source['bucket']+'/'+source['object']+'#'+str(source['generation'])
 archive=out/(service+'-baseline-source.tgz')
 if archive.exists() and service=='api':archive.rename(out/(service+'-prior-baseline-source.tgz'))
 if not archive.exists():subprocess.run(['gcloud','storage','cp',uri,str(archive)],check=True,stdout=subprocess.DEVNULL)
 hashes=[h['value'] for e in build['sourceProvenance']['fileHashes'].values() for h in e['fileHash'] if h['type']=='SHA256'];assert base64.urlsafe_b64encode(hashlib.sha256(archive.read_bytes()).digest()).decode() in hashes
 dest=work/(service+'-source');dest.mkdir(exist_ok=True)
 with tarfile.open(archive) as tar:tar.extractall(dest,filter='data')
 repo=root/'apps'/('web' if service=='web' else 'server')
 manifest=lambda:{str(p.relative_to(dest)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dest.rglob('*')) if p.is_file() and 'node_modules' not in p.parts and '.next' not in p.parts}
 before=manifest();patches=[]
 for name in changes[service]:
  old=out/'workspace-before'/'apps'/('web' if service=='web' else 'server')/name
  current=(repo/name).read_text()
  if old.exists():
   patch=''.join(difflib.unified_diff(old.read_text().splitlines(True),current.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
   result=subprocess.run(['patch','--batch','--forward','-p1'],cwd=dest,input=patch,text=True,capture_output=True);assert result.returncode==0,result.stdout+result.stderr
   patches.append(patch)
  else:
   p=dest/name;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(current)
 after=manifest();changed=[k for k in after if after[k]!=before.get(k)];assert sorted(changed)==sorted(changes[service]),changed
 assert all(after[k]==v for k,v in before.items() if k.startswith('public/'))
 (out/(service+'-release.patch')).write_text(''.join(patches));(out/(service+'-manifest.json')).write_text(json.dumps(dict(before=before,after=after,changed=changed)))
 prepared=out/(service+'-prepared-source.tgz')
 with tarfile.open(prepared,'w:gz') as tar:
  for name in after:tar.add(dest/name,arcname=name,recursive=False)
 config=json.loads((prior/'web-cloudbuild.json').read_text().replace('public-cleanup-20261008','key-artworks-20261008').replace('/web:', '/'+service+':'))
 (work/(service+'-cloudbuild.json')).write_text(json.dumps(config));(out/(service+'-cloudbuild.json')).write_text(json.dumps(config))
 print(service,'baseline verified',digest,'changed',changed,flush=True)
for name in ['build.py','release.py']:
 text=(prior/name).read_text().replace('public-cleanup-20261008','key-artworks-20261008').replace('public-cleanup2-1008','key-artworks-1008')
 (work/name).write_text(text);(out/name).write_text(text)
