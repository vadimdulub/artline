"""Offline checks of request coordination; never opens a database or network."""
import importlib.util,tempfile,threading,time,types,unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

s=importlib.util.spec_from_file_location('downloads',Path(__file__).with_name('uk-source-downloads-20260920.py'))
d=importlib.util.module_from_spec(s);s.loader.exec_module(d)

class FakeTime:
    def __init__(self):self.value=10.0;self.sleeps=[]
    def monotonic(self):return self.value
    def time(self):return self.value
    def sleep(self,delay):self.sleeps.append(delay);self.value+=delay

class Response:
    def __init__(self,status=200,data=b'',retry=None):
        self.status_code=status;self.data=data;self.headers={'Content-Type':'image/jpeg'}
        if retry:self.headers['Retry-After']=retry
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def raise_for_status(self):
        if self.status_code>=400:raise RuntimeError('HTTP '+str(self.status_code))
    def iter_content(self,size):
        for start in range(0,len(self.data),size):yield self.data[start:start+size]

def research(clock,responses):
    deadlines={};calls=[]
    class Session:
        def get(self,url,**kwargs):calls.append((url,clock.monotonic()));return responses.pop(0)
    class Fetcher:
        def __init__(self,cache):self.session=Session()
        def get(self,url,limit=8_000_000):return b'delegated',{}
    def cooldown(host,cooldown):deadlines[host]=max(deadlines.get(host,0),clock.monotonic()+cooldown)
    core=types.SimpleNamespace(Fetcher=Fetcher,requests=types.SimpleNamespace(RequestException=RuntimeError),provider_cooldown_seconds=lambda host:max(0,deadlines.get(host,0)-clock.monotonic()),provider_rate_slot=cooldown,retry_delay=lambda value,default=60:float(value) if value else default)
    return types.SimpleNamespace(core=core,SESSION=Session()),calls,deadlines

class DownloadCoordinationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='artline-uk-download-test-');self.folder=patch.object(d,'LOCKS',Path(self.temp.name));self.folder.start()
    def tearDown(self):self.folder.stop();self.temp.cleanup()

    def test_shared_slots_bound_concurrent_operations(self):
        guard=threading.Lock();active=0;peak=0
        def worker(_):
            nonlocal active,peak
            with d.slot('media',2):
                with guard:active+=1;peak=max(peak,active)
                time.sleep(.04)
                with guard:active-=1
        with ThreadPoolExecutor(max_workers=7) as pool:list(pool.map(worker,range(7)))
        self.assertEqual(peak,2);self.assertEqual(active,0)

    def test_media_transfer_is_bandwidth_bounded(self):
        clock=FakeTime();r,calls,_=research(clock,[Response(data=b'x'*1_000_000)])
        with patch.object(d,'time',clock):
            d.install(r);raw,_=r.core.Fetcher(self.temp.name).get('https://upload.wikimedia.org/example.jpg',2_000_000)
        self.assertEqual(len(raw),1_000_000);self.assertGreaterEqual(clock.value-10,1);self.assertEqual(len(calls),1)

    def test_retry_after_is_shared_across_media_hosts(self):
        clock=FakeTime();r,calls,deadlines=research(clock,[Response(429,retry='90'),Response(data=b'image')])
        with patch.object(d,'time',clock):
            d.install(r);raw,_=r.core.Fetcher(self.temp.name).get('https://thumb.wikimedia.org/example.jpg')
        self.assertEqual(raw,b'image');self.assertGreaterEqual(calls[1][1]-calls[0][1],90)
        self.assertEqual(set(deadlines),d.MEDIA_HOSTS)

    def test_existing_cooldown_is_not_shortened(self):
        clock=FakeTime();r,calls,deadlines=research(clock,[Response(data=b'image')]);deadlines['upload.wikimedia.org']=310
        with patch.object(d,'time',clock):
            d.install(r);r.core.Fetcher(self.temp.name).get('https://thumb.wikimedia.org/example.jpg')
        self.assertGreaterEqual(calls[0][1],310)

    def test_other_providers_keep_existing_fetcher(self):
        clock=FakeTime();r,calls,_=research(clock,[]);d.install(r)
        self.assertEqual(r.core.Fetcher(self.temp.name).get('https://example.org/image.jpg')[0],b'delegated');self.assertEqual(calls,[])

    def test_action_api_uses_one_global_connection(self):
        clock=types.SimpleNamespace(monotonic=time.monotonic);r,_,_=research(clock,[]);guard=threading.Lock();active=0;peak=0
        def get(url,**kwargs):
            nonlocal active,peak
            with guard:active+=1;peak=max(peak,active)
            time.sleep(.025)
            with guard:active-=1
            return Response()
        r.SESSION.get=get;d.install(r)
        urls=['https://commons.wikimedia.org/w/api.php','https://www.wikidata.org/w/api.php']*2
        with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(r.SESSION.get,urls))
        self.assertEqual(peak,1)

if __name__=='__main__':unittest.main()
