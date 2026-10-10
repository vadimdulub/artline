#!/usr/bin/env python3
"""Continue the authorized production campaign with pinned, verified source waves.

No fixtures, publication, image downloads, local-catalogue writes or code deploys.
Stops on changed scripts, failed preflight, source denial or verification failure.
"""
import datetime,fcntl,gzip,hashlib,json,os,re,socket,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/all-museums-minimum-100-20261006'
JOB=RUN/'jobs/continuation-20261007'
RUNTIME=Path.home()/'Library/Application Support/Artline/jobs/museum-minimum-100-20261007'
PORT=55486
PYTHON=sys.executable
SCRIPTS=['all-museums-minimum-100-20261006.py','museum-minimum-100-delivery-20261006.py',
    'minimum-100-arco-native-20261006.py','minimum-100-wikidata-catalogue-20261006.py',
    'minimum-100-wikidata-links-20261006.py','museum-expansion-arco-20261006.py','museum-expansion-20261006.py',
    'research-havre-rouen-cyprus-20261006.py','apply-artwork-locations-20261004.py','research-artwork-locations-20261004.py']


def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(path):
    raw=path.read_bytes();return json.loads(gzip.decompress(raw)if path.suffix=='.gz'else raw)
def state(**values):
    record=dict(at=now(),pid=os.getpid(),**values);temp=JOB/'status.tmp';temp.write_text(json.dumps(record,indent=2));temp.replace(JOB/'status.json')
    print(json.dumps(record),flush=True)


def main():
    JOB.mkdir(parents=True,exist_ok=True);RUNTIME.mkdir(parents=True,exist_ok=True)
    lock=(RUNTIME/'worker.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    hashes={name:hashlib.sha256((ROOT/'ops'/name).read_bytes()).hexdigest()for name in SCRIPTS}
    pin=JOB/'script-hashes.json'
    if pin.exists():assert read(pin)==hashes,'Campaign scripts changed since this job was pinned'
    else:pin.write_text(json.dumps(hashes,indent=2))
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',ARTLINE_MUSEUM_PROXY_PORT=str(PORT),CLOUDSDK_CORE_ACCOUNT='vadim@alingva.com')
    proxy_log=(JOB/'proxy.log').open('a')
    proxy=subprocess.Popen(['/tmp/artline-release-20261001-evening/cloud-sql-proxy','--gcloud-auth','--address=127.0.0.1','--port='+str(PORT),'artline-508319:europe-west1:artline-postgres'],env=env,stdout=proxy_log,stderr=subprocess.STDOUT)
    try:
        for _ in range(60):
            if proxy.poll()is not None:raise RuntimeError('Dedicated production proxy exited')
            try:
                with socket.create_connection(('127.0.0.1',PORT),timeout=1):break
            except OSError:time.sleep(1)
        else:raise RuntimeError('Dedicated production proxy did not become ready')

        def execute(script,*args):
            for name,digest in hashes.items():assert hashlib.sha256((ROOT/'ops'/name).read_bytes()).hexdigest()==digest,'Pinned campaign script changed: '+name
            state(status='running',script=script,arguments=list(args),objective='Research every remaining museum in the available scoped source indexes; add or link supported records toward 100; preserve unresolved gaps.')
            subprocess.run([PYTHON,str(ROOT/'ops'/script),*args],cwd=ROOT,env=env,check=True)

        families={
            'wikidata':dict(script='minimum-100-wikidata-catalogue-20261006.py',prefix='wikidata-catalogue-auto-',kwargs=['--museums','40']),
            'arco':dict(script='minimum-100-arco-native-20261006.py',prefix='arco-native-auto-',kwargs=['--museums','80','--pages','1800'])}
        paused={};delivered=[]
        for iteration in range(1,101):
            if not families:break
            for family,config in list(families.items()):
                wave=config['prefix']+f'{iteration:03d}';folder=RUN/'waves'/wave
                if not(folder/'source-verified.json.gz').exists():
                    try:execute(config['script'],'research','--wave',wave,*config['kwargs'])
                    except subprocess.CalledProcessError:
                        paused[family]=dict(wave=wave,reason='Source research stopped; retained evidence and logs require review. No unplanned writes.');del families[family];continue
                source=read(folder/'source-verified.json.gz')
                if any(x['reason']=='source_paused_after_access_response'or re.search(r'HTTP (403|429)',x.get('error',''))for x in source['held']):
                    paused[family]=dict(wave=wave,reason='Official source denied/rate-limited requests; no automatic further source requests.');del families[family];continue
                if family=='arco':
                    selection=read(RUN/'arco'/wave/'selection.json.gz');exhausted=not selection['candidates']
                else:exhausted=not read(RUN/'wikidata-catalogue'/wave/'selected-museums.json')
                if exhausted:
                    paused[family]=dict(wave=wave,reason='All available scoped targets/candidates in this source pass have been reviewed; unresolved gaps are preserved.');del families[family];continue
                if not source['records']:continue
                if not(folder/'plan.json.gz').exists():execute(config['script'],'plan','--wave',wave)
                plan=read(folder/'plan.json.gz')
                if plan['records']and not(folder/'applied.json').exists():execute(config['script'],'apply','--wave',wave)
                if(folder/'applied.json').exists():
                    execute('all-museums-minimum-100-20261006.py','audit');delivered.append(wave)
        progress=read(RUN/'progress.json')
        state(status='source_passes_finished_with_remaining_gaps'if progress['museums_still_below_100']else'target_met',
            new_artworks=progress['new_artworks'],existing_artworks_linked=progress['existing_artworks_linked'],museums_still_below_100=progress['museums_still_below_100'],source_outcomes=paused,delivered_waves=delivered)
    except Exception as exc:
        state(status='needs_attention',error=type(exc).__name__+': '+str(exc),note='Stopped on a source, version, script or database verification error. Existing committed receipts and recovery preimages are retained.')
        raise
    finally:
        proxy.terminate()
        try:proxy.wait(timeout=10)
        except subprocess.TimeoutExpired:proxy.kill();proxy.wait()
        proxy_log.close();lock.close()


if __name__=='__main__':main()
