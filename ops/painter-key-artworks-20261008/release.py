import copy,json,os,pathlib,subprocess,sys,urllib.request
os.umask(0o077)
OUT=pathlib.Path.home()/'Library/Application Support/Artline/backups/key-artworks-20261008'
ROOT='projects/artline-508319/locations/europe-west1'
TAG='key-artworks-20261008'
token=subprocess.check_output(['gcloud','auth','print-access-token','--account=vadim@alingva.com'],text=True).strip()
def request(path,body=None,method=None):
    req=urllib.request.Request('https://run.googleapis.com/v2/'+path,data=None if body is None else json.dumps(body).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},method=method)
    with urllib.request.urlopen(req,timeout=45) as response:return json.load(response)
def save(name,data):(OUT/name).write_text(json.dumps(data,indent=2)+'\n')
action,service=sys.argv[1:3]
assert service in ('api','web')
name=ROOT+'/services/artline-'+service
revision='artline-'+service+'-key-artworks-1008'
current=request(name)
if action=='stage':
    image=sys.argv[3]
    assert image.startswith('europe-west1-docker.pkg.dev/artline-508319/artline/'+service+'@sha256:')
    assert not current.get('reconciling')
    before=json.loads((OUT/(service+'-deploy-preflight.json')).read_text())
    assert current['template']['containers'][0]['image']==before['spec']['template']['spec']['containers'][0]['image'],'Serving image changed'
    expected={t['revisionName']:t['percent'] for t in before['status']['traffic'] if t.get('percent')}
    actual={t['revision']:t['percent'] for t in current['traffic'] if t.get('percent')}
    assert actual==expected,'Traffic changed'
    assert all(t.get('type')=='TRAFFIC_TARGET_ALLOCATION_TYPE_REVISION' for t in current['traffic'])
    save(service+'-before-v2.json',current)
    containers=copy.deepcopy(current['template']['containers']);assert len(containers)==1
    containers[0]['image']=image
    assert not any(t.get('tag')==TAG and t.get('percent',0)>0 for t in current['traffic'])
    traffic=[t for t in copy.deepcopy(current['traffic']) if t.get('tag')!=TAG]
    traffic.append({'type':'TRAFFIC_TARGET_ALLOCATION_TYPE_REVISION','revision':revision,'tag':TAG})
    body={'name':name,'etag':current['etag'],'template':{'revision':revision,'containers':containers},'traffic':traffic}
    save(service+'-candidate-patch.json',body)
    mask='template.revision,template.containers,traffic'
    request(name+'?updateMask='+mask+'&validateOnly=true',body,'PATCH')
    operation=request(name+'?updateMask='+mask,body,'PATCH');save(service+'-candidate-operation.json',operation)
    print(json.dumps({'operation':operation['name'],'revision':revision,'publicTraffic':0}))
elif action in ('check','final'):
    before=json.loads((OUT/(service+'-before-v2.json')).read_text());staged=json.loads((OUT/(service+'-candidate-patch.json')).read_text())
    expected=copy.deepcopy(before['template']);expected.update(staged['template'])
    assert current['template']==expected,'Runtime configuration differs from staged template'
    for key in ['ingress','invokerIamDisabled','defaultUriDisabled','scaling','binaryAuthorization','iapEnabled']:
        assert current.get(key)==before.get(key),'Runtime setting changed: '+key
    ready=not current.get('reconciling') and current.get('terminalCondition',{}).get('state')=='CONDITION_SUCCEEDED'
    save(service+'-'+action+'.json',current)
    traffic=[t for t in current.get('trafficStatuses',[]) if t.get('percent') or t.get('tag')==TAG]
    print(json.dumps({'ready':ready,'traffic':traffic,'runtimeConfigurationPreserved':True}))
    if action=='final':
        active=[t for t in current['trafficStatuses'] if t.get('percent',0)>0]
        assert ready and len(active)==1 and active[0]['revision']==revision and active[0]['percent']==100
elif action=='promote':
    verification=json.loads((OUT/(service+'-candidate-verification.json')).read_text());assert verification['passed'],'Candidate verification failed'
    staged=json.loads((OUT/(service+'-candidate-patch.json')).read_text())
    assert current['traffic']==staged['traffic'],'Traffic changed after staging'
    assert current['template']['containers']==staged['template']['containers'],'Candidate changed'
    assert not current.get('reconciling') and current['latestReadyRevision'].endswith('/'+revision)
    traffic=copy.deepcopy(current['traffic'])
    for target in traffic:
        target.pop('percent',None)
        if target['revision']==revision:target['percent']=100
    traffic=[t for t in traffic if t.get('tag') or t.get('percent')]
    assert sum(t.get('percent',0) for t in traffic)==100
    body={'name':name,'etag':current['etag'],'traffic':traffic};save(service+'-promotion-patch.json',body)
    operation=request(name+'?updateMask=traffic',body,'PATCH');save(service+'-promotion-operation.json',operation)
    print(json.dumps({'operation':operation['name'],'revision':revision,'publicTraffic':100}))
else:raise ValueError('Unknown release action')
