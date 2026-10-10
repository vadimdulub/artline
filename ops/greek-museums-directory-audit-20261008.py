#!/usr/bin/env python3
"""Audit every public Ministry directory entry without treating room photos as artworks."""
import collections, concurrent.futures, importlib.util
from pathlib import Path
from urllib.parse import urlparse, urljoin
spec=importlib.util.spec_from_file_location('g',Path(__file__).with_name('greek-museums-20261008.py'))
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)


def main():
    soup,rc=g.page(g.PORTAL+'/en');mapped={x['key']:x for x in g.load(g.RUN/'ministry-directory.json')}
    names=g.load(g.RUN/'ministry-greek-names.json')['names'];entries=[]
    for group in soup.select('optgroup'):
        for option in group.select('option[value]'):
            key=option['value']
            entries.append(dict(mapped.get(key)or dict(key=key,name=g.clean(option),region=group['label'],source_url=g.PORTAL+'/en/museum/'+key,directory_receipt=rc),greek_name=names.get(key)))
    assert len({x['key']for x in entries})==len(entries)==214
    def one(entry):
        dest=g.RUN/'ministry-audit'/(entry['key']+'.json')
        if dest.exists():return g.load(dest)
        try:
            s,receipt=g.page(entry['source_url']);links=[]
            for a in s.select('a[href]'):
                u=urljoin(entry['source_url'],a['href']);host=urlparse(u).hostname
                if host and host!=urlparse(g.PORTAL).hostname and not any(x in host for x in ['facebook','twitter','instagram','youtube','google','linkedin']):links.append(dict(title=g.clean(a),url=u))
            out=dict(**entry,receipt=receipt,source_text=g.clean(s),outgoing_links=list({x['url']:x for x in links}.values()),
                catalogue_status='directory_page_audited; artwork identity requires separate object catalogue; no room or building photo imported')
        except Exception as e:out=dict(**entry,error=type(e).__name__+': '+str(e),catalogue_status='directory_page_unavailable')
        g.save(dest,out);return out
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        for n,row in enumerate(pool.map(one,entries),1):
            rows.append(row)
            if n%25==0:print('Directory',n,'/',len(entries),flush=True)
    g.save(g.RUN/'ministry-directory-audit.json',dict(at=g.now(),entries=rows))
    print('Directory audit',len(rows),'entries',sum('error'in r for r in rows),'unavailable',flush=True)


if __name__=='__main__':main()
