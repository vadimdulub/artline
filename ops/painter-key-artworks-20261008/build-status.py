import base64,hashlib,json,pathlib,subprocess
out=pathlib.Path.home()/'Library/Application Support/Artline/backups/key-artworks-20261008'
for service in ['api','web']:
    p=out/(service+'-build.json')
    if not p.exists():continue
    build=json.loads(p.read_text())
    data=json.loads(subprocess.check_output(['gcloud','builds','describe',build['id'],'--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True))
    (out/(service+'-build-status.json')).write_text(json.dumps(data,indent=2))
    report={'service':service,'build':data['id'],'status':data['status']}
    if data['status']=='SUCCESS':
        digest=data['results']['images'][0]['digest']
        hashes=[h['value'] for entry in data['sourceProvenance']['fileHashes'].values() for h in entry['fileHash'] if h['type']=='SHA256']
        actual=base64.urlsafe_b64encode(hashlib.sha256((out/(service+'-prepared-source.tgz')).read_bytes()).digest()).decode()
        assert actual in hashes,'Build source provenance mismatch'
        image=f'europe-west1-docker.pkg.dev/artline-508319/artline/{service}@{digest}'
        (out/(service+'-release-image.txt')).write_text(image+'\n');report.update(image=image,sourceProvenanceVerified=True)
    print(json.dumps(report))
