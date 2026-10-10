#!/usr/bin/env python3
"""Continue the authorized 1–100 museum expansion with verified production batches."""
import datetime,fcntl,gzip,hashlib,json,os,socket,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CAMPAIGN=ROOT/'docs/research/all-museums-minimum-100-20261006'
TASK=CAMPAIGN/'expansion-1-100-20261007';JOB=TASK/'worker'
RUNTIME=Path.home()/'Library/Application Support/Artline/jobs/museum-1-100-expansion-20261007'
PORT=55490
SCRIPTS=['continue-museum-1-100-expansion-20261007.py','museum-1-100-expansion-20261007.py',
    'museum-1-10-priority-20261007.py','minimum-100-wikidata-catalogue-20261006.py',
    'minimum-100-wikidata-links-20261006.py','minimum-100-arco-native-20261006.py','museum-1-10-arco-review-20261007.py',
    'all-museums-minimum-100-20261006.py','museum-minimum-100-delivery-20261006.py','museum-expansion-20261006.py',
    'research-havre-rouen-cyprus-20261006.py','apply-artwork-locations-20261004.py','research-artwork-locations-20261004.py']


def read(path):return json.loads(gzip.decompress(path.read_bytes())if path.suffix=='.gz'else path.read_bytes())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def state(**values):
    data=dict(at=now(),pid=os.getpid(),**values);temp=JOB/'status.tmp';temp.write_text(json.dumps(data,indent=2));temp.replace(JOB/'status.json');print(json.dumps(data),flush=True)


def main():
    JOB.mkdir(parents=True,exist_ok=True);RUNTIME.mkdir(parents=True,exist_ok=True)
    lock=(RUNTIME/'worker.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    hashes={name:hashlib.sha256((ROOT/'ops'/name).read_bytes()).hexdigest()for name in SCRIPTS}
    pin=JOB/'script-hashes.json'
    if pin.exists():assert read(pin)==hashes,'Pinned research/delivery scripts changed; review required'
    else:pin.write_text(json.dumps(hashes,indent=2))
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',ARTLINE_MUSEUM_PROXY_PORT=str(PORT),CLOUDSDK_CORE_ACCOUNT='vadim@alingva.com')
    with socket.socket()as probe:probe.bind(('127.0.0.1',PORT))
    log=(JOB/'proxy.log').open('a')
    proxy=subprocess.Popen(['/tmp/artline-release-20261001-evening/cloud-sql-proxy','--gcloud-auth','--address=127.0.0.1','--port='+str(PORT),'artline-508319:europe-west1:artline-postgres'],env=env,stdout=log,stderr=subprocess.STDOUT)
    delivered=[]
    try:
        for _ in range(60):
            if proxy.poll()is not None:raise RuntimeError('Dedicated production proxy exited')
            try:
                with socket.create_connection(('127.0.0.1',PORT),timeout=1):break
            except OSError:time.sleep(1)
        else:raise RuntimeError('Dedicated proxy failed to start')

        def execute(script,*args):
            for name,digest in hashes.items():assert hashlib.sha256((ROOT/'ops'/name).read_bytes()).hexdigest()==digest,'Pinned script changed: '+name
            state(status='running',script=script,arguments=list(args),delivered_waves=delivered,
                objective='Expand every museum in the frozen 1–100 production cohort toward 200, then continue remaining original under-100 sources; verified source records only.')
            subprocess.run([sys.executable,str(ROOT/'ops'/script),*args],cwd=ROOT,env=env,check=True)

        handoff=JOB/'research-handoff.json'
        if handoff.exists():
            item=read(handoff)
            assert item['wave']=='expand-1-100-wikidata-001'
            while True:
                observed=subprocess.run(['ps','-p',str(item['pid']),'-o','command='],capture_output=True,text=True)
                if observed.returncode or observed.stdout.strip()!=item['command']:break
                state(status='running',phase='waiting_for_active_source_research',research_pid=item['pid'],
                    wave=item['wave'],delivered_waves=delivered,note='Adopting the already-running read-only source capture; no duplicate requests or concurrent delivery.')
                time.sleep(30)
            assert(CAMPAIGN/'waves'/item['wave']/'source-verified.json.gz').exists(),'Handed-over source research ended without a verified batch'

        for script,prefix in [
            ('museum-1-100-expansion-20261007.py','expand-1-100-wikidata-'),
            ('minimum-100-wikidata-catalogue-20261006.py','minimum-100-resume-')]:
            iteration=1
            while True:
                wave=prefix+f'{iteration:03d}';iteration+=1;folder=CAMPAIGN/'waves'/wave
                if not(folder/'source-verified.json.gz').exists():execute(script,'research','--wave',wave,'--museums','20')
                selected=read(CAMPAIGN/'wikidata-catalogue'/wave/'selected-museums.json')
                if not selected:break
                source=read(folder/'source-verified.json.gz')
                if not source['records']:continue
                if not(folder/'plan.json.gz').exists():execute(script,'plan','--wave',wave)
                plan=read(folder/'plan.json.gz')
                if plan['records']and not(folder/'applied.json').exists():execute(script,'apply','--wave',wave)
                if(folder/'applied.json').exists():
                    execute('museum-1-100-expansion-20261007.py','audit')
                    execute('all-museums-minimum-100-20261006.py','audit')
                    delivered.append(wave)
        execute('museum-1-100-expansion-20261007.py','audit')
        execute('all-museums-minimum-100-20261006.py','audit')
        progress=read(TASK/'progress.json')
        state(status='available_source_passes_finished_with_remaining_gaps'if progress['status']!='target_met'else'target_met',
            new_artworks=progress['new_artworks'],existing_artworks_linked=progress['existing_artworks_linked'],
            museums_still_1_to_100=progress['museums_still_1_to_100'],delivered_waves=delivered,
            note='Source exhaustion, missing authorities and withheld objects remain explicit research gaps; no quota-based invented records.')
    except Exception as exc:
        state(status='needs_attention',error=type(exc).__name__+': '+str(exc),delivered_waves=delivered,
            note='Stopped on source access, transport, version, script or database verification failure. Committed receipts and preimages retained.')
        raise
    finally:
        proxy.terminate()
        try:proxy.wait(timeout=10)
        except subprocess.TimeoutExpired:proxy.kill();proxy.wait()
        log.close();lock.close()


if __name__=='__main__':main()
