import pathlib,json,subprocess,sys
work=pathlib.Path(__file__).parent
backup=pathlib.Path.home()/'Library/Application Support/Artline/backups/key-artworks-20261008'
service=sys.argv[1]
assert service in ('api','web')
uri=f'gs://artline-508319-build-source/source/key-artworks-20261008-{service}.tgz'
subprocess.run(['gcloud','storage','cp',str(backup/(service+'-prepared-source.tgz')),uri,'--project=artline-508319','--account=vadim@alingva.com'],check=True)
p=subprocess.run(['gcloud','builds','submit',uri,'--async','--gcs-source-staging-dir=gs://artline-508319-build-source/source','--config='+str(work/(service+'-cloudbuild.json')),'--project=artline-508319','--account=vadim@alingva.com','--format=json'],capture_output=True,text=True)
if p.returncode:
    print(p.stderr);raise SystemExit(p.returncode)
data=json.loads(p.stdout)
(backup/(service+'-build.json')).write_text(p.stdout)
print(json.dumps({'service':service,'build':data['id'],'status':data['status']}))
