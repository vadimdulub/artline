#!/usr/bin/env python3
"""One bounded metadata fetch per selected primary page; stop a host on access failure."""
import collections,concurrent.futures,importlib.util,json
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('task',ROOT/'ops/random-5000-museum-research-20261006.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);r=m.r;r.RUN=m.RUN
def main():
    pin=r.load(r.RUN/'latest-web-review.json');review=r.load(r.RUN/pin['path']);groups=collections.defaultdict(set)
    for cc in review['supported_candidates'].values():
        for c in cc:groups[urlsplit(c['source_url']).hostname].add(c['source_url'])
    def capture_group(item):
        host,urls=item;stopped=None;out=[]
        for url in sorted(urls):
            if stopped:out.append({'url':url,'outcome':'not_attempted_after_host_access_failure','reason':stopped});continue
            try:
                raw,rc=r.capture(url,tag='primary-page-validation',timeout=30)
                out.append({'url':url,'outcome':'captured','receipt':rc})
                if rc['status']in [401,403,429]or rc['status']>=500:stopped='HTTP '+str(rc['status'])
            except Exception as e:
                stopped=type(e).__name__;out.append({'url':url,'outcome':'request_failed','reason':stopped})
        print('Primary host checked',host,len(out),stopped or 'complete',flush=True);return out
    result=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        for out in pool.map(capture_group,groups.items()):result.extend(out)
    r.save_gz(r.RUN/'primary-page-validation.json.gz',{'at':r.now(),'review_pin':pin,'results':result,'policy':'One public metadata-page request per selected URL; no image fetching, retries, alternate endpoint or access-control bypass. Indexed primary captures are retained separately.'})
    print('Primary-page outcomes',dict(collections.Counter((x['outcome'],str(x.get('receipt',{}).get('status')))for x in result)),flush=True)
if __name__=='__main__':main()
