"""Coordinate this collection run under Wikimedia's published robot limits.

https://wikitech.wikimedia.org/wiki/Robot_policy
Media: at most two simultaneous requests, under 25 Mbps globally. This adapter
uses two cross-process slots and at most 1,000,000 bytes/second per connection
(16 Mbps combined), with starts at least 1.2 seconds apart globally.
Action API requests use one shared slot and pause five
seconds after slow responses. Existing server cooldowns are never shortened.
"""
import fcntl,hashlib,json,time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

LOCKS=Path.home()/'Library/Application Support/Artline/research-rate-limits'
MEDIA_HOSTS={'upload.wikimedia.org','thumb.wikimedia.org'}
API_HOSTS={'commons.wikimedia.org','www.wikidata.org'}

@contextmanager
def slot(name,count):
    LOCKS.mkdir(parents=True,exist_ok=True)
    held=None
    while held is None:
        for index in range(count):
            stream=(LOCKS/(name+'-'+str(index)+'.lock')).open('a')
            try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:stream.close();continue
            held=stream;break
        if held is None:time.sleep(.1)
    try:yield
    finally:fcntl.flock(held,fcntl.LOCK_UN);held.close()

def wait_cooldown(core,hosts):
    while True:
        delay=max(core.provider_cooldown_seconds(host) for host in hosts)
        if delay<=0:return
        time.sleep(min(delay,60))

def media_start():
    path=LOCKS/'wikimedia-media-start.lock'
    while True:
        with path.open('a+') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX);stream.seek(0)
            next_at=float(stream.read() or '0');now=time.time();delay=next_at-now
            if delay<=0:
                stream.seek(0);stream.truncate();stream.write(str(now+1.2));stream.flush();return
        time.sleep(min(delay,60))

def install(research):
    core=research.core;original_get=research.SESSION.get
    def api_get(url,**kwargs):
        parsed=urlparse(url)
        if parsed.hostname not in API_HOSTS or parsed.path!='/w/api.php':return original_get(url,**kwargs)
        with slot('wikimedia-action-global',1):
            wait_cooldown(core,API_HOSTS);started=time.monotonic()
            try:
                response=original_get(url,**kwargs)
                if response.status_code in (429,503):
                    pause=core.retry_delay(response.headers.get('Retry-After'),default=5)
                    for host in API_HOSTS:core.provider_rate_slot(host,cooldown=pause)
                return response
            finally:
                if time.monotonic()-started>1:time.sleep(5)
    research.SESSION.get=api_get
    base_fetcher=core.Fetcher
    class SelectedMediaFetcher(base_fetcher):
        def get(self,url,limit=8_000_000):
            parsed=urlparse(url)
            if parsed.hostname not in MEDIA_HOSTS:return super().get(url,limit)
            if parsed.scheme!='https':raise ValueError('Unapproved source protocol')
            for attempt in range(3):
                try:
                    with slot('wikimedia-media-global',2):
                        wait_cooldown(core,MEDIA_HOSTS)
                        media_start()
                        # Another connection can receive Retry-After while this
                        # request waits for its globally spaced start.
                        wait_cooldown(core,MEDIA_HOSTS)
                        started=time.monotonic()
                        response=self.session.get(url,timeout=(15,45),stream=True,allow_redirects=False)
                        with response:
                            if response.status_code in (429,502,503,504):
                                pause=max(core.retry_delay(response.headers.get('Retry-After'),default=5),15*(2**attempt))
                                evidence=getattr(research,'RUN',None)
                                if evidence:
                                    body=bytearray()
                                    for chunk in response.iter_content(4096):
                                        body.extend(chunk)
                                        if len(body)>=4096:break
                                    folder=Path(evidence)/'source-backoffs';folder.mkdir(parents=True,exist_ok=True)
                                    record={'url':url,'at':time.time(),'status':response.status_code,'wait_seconds':pause,'headers':{key:response.headers.get(key) for key in ('Retry-After','Content-Type','Server','X-Cache')},'body_prefix':bytes(body[:4096]).decode('utf-8','replace')}
                                    (folder/(hashlib.sha256(url.encode()).hexdigest()+'-'+str(time.time_ns())+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
                                print('Wikimedia media backoff',response.status_code,pause,'seconds',flush=True)
                                for host in MEDIA_HOSTS:core.provider_rate_slot(host,cooldown=pause)
                                continue
                            response.raise_for_status()
                            if response.status_code!=200:raise ValueError('Unexpected image response '+str(response.status_code))
                            data=bytearray()
                            for chunk in response.iter_content(65536):
                                data.extend(chunk)
                                if len(data)>limit:raise ValueError('Source response exceeds byte budget')
                                delay=len(data)/1_000_000-(time.monotonic()-started)
                                if delay>0:time.sleep(delay)
                            headers={key:response.headers.get(key) for key in ('Content-Type','ETag','Last-Modified')}
                            return bytes(data),headers
                except (core.requests.RequestException,ValueError):
                    if attempt==2:raise
                    time.sleep(2**attempt)
            raise RuntimeError('Source remains unavailable after bounded retries')
    core.Fetcher=SelectedMediaFetcher
