#!/usr/bin/env python3
"""Public museum datasets and exact indexed Walters object pages; no DB writes."""
import importlib.util,json,csv,hashlib,re,requests,io
from pathlib import Path
from collections import Counter
from urllib.parse import urlsplit,parse_qs,unquote,urljoin
from concurrent.futures import ThreadPoolExecutor,as_completed
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('native',Path(__file__).with_name('source-index-native-20261010.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n);m=n.m;RUN=n.RUN


def dataset(repo,filename):
    api='https://api.github.com/repos/'+repo+'/commits?per_page=1'
    data,rc=n.f.get(api,True);commit=data[0]['sha'];assert re.fullmatch('[a-f0-9]{40}',commit)
    directory=n.CACHE/repo.split('/')[0];directory.mkdir(parents=True,exist_ok=True);path=directory/(commit+'-'+filename);receipt=RUN/'datasets'/(repo.split('/')[0]+'-'+filename+'.json')
    if receipt.exists():
        rr=m.load(receipt);assert m.m.sha(path)==rr['sha256'];return path,rr
    url='https://raw.githubusercontent.com/'+repo+'/'+commit+'/'+filename
    # MoMA stores its public CSV with Git LFS; use the repository's published media URL.
    if repo.startswith('MuseumofModernArt/'):url='https://media.githubusercontent.com/media/'+repo+'/'+commit+'/'+filename
    with requests.get(url,headers={'User-Agent':n.f.UA},timeout=(15,90),stream=True) as response:
        response.raise_for_status();h=hashlib.sha256();count=0;temp=path.with_suffix('.part')
        with temp.open('wb') as f:
            for block in response.iter_content(262144):
                count+=len(block);assert count<500_000_000;h.update(block);f.write(block)
        temp.replace(path)
        rr=dict(url=url,commit=commit,commit_capture=rc,retrieved_at=m.now(),path=str(path),bytes=count,sha256=h.hexdigest(),http_status=response.status_code);m.save(receipt,rr)
    return path,rr


def moma():
    targets,_=n.refs();targets=targets['moma'];path,receipt=dataset('MuseumofModernArt/collection','Artworks.csv');found=0
    with path.open(newline='',encoding='utf-8-sig') as f:
        for o in csv.DictReader(f):
            key=o['ObjectID']
            if key not in targets:continue
            lo,hi,precision=n.date_parse(o.get('Date'));ids=re.findall(r'\d+',o.get('ConstituentID') or '')
            v=dict(native_id=key,scheme='moma-object',accession=o.get('AccessionNumber'),titles=[o['Title']],dates=dict(display=o.get('Date'),start=lo,end=hi),date_precision=precision,medium=o.get('Medium'),dimensions=o.get('Dimensions'),page=o.get('URL') or 'https://www.moma.org/collection/works/'+key,creator_labels=[o.get('Artist')],creator_authorities=[dict(scheme='moma-person',external_id=i,label=o.get('Artist')) for i in ids],raw_creator_data=dict(artist=o.get('Artist'),native_ids=ids,birth=o.get('BeginDate'),death=o.get('EndDate')),qualified_creators=[o.get('Artist')] if re.search(r'\b(attributed|after|workshop|school|follower|circle|possibly|probably)\b',o.get('Artist') or '',re.I) else [],image=o.get('ImageURL'),image_open=False,image_rights='No per-image reuse grant established by the open metadata dataset',license_url=None,credit=o.get('CreditLine'),institution_id=n.IIDS['moma'],classification=o.get('Classification'),work_type=n.type_for([o.get('Classification','')],o.get('Medium','')),holding_qualified=o.get('Cataloged')!='Y' or bool(re.search(r'\b(loan|lent by|private collection|deaccession)\b',o.get('CreditLine') or '',re.I)))
            m.save(RUN/'native/moma'/(hashlib.sha256(key.encode()).hexdigest()+'.json.gz'),dict(provider='moma',key=key,state='captured',facts=v,raw=o,receipt=receipt,source_index_ids=[x['id'] for x in targets[key]],index_bindings=[b for x in targets[key] for b in x['artline_bindings']]))
            found+=1
    print('MoMA metadata',found,'/',len(targets),flush=True)


def walters():
    targets,_=n.refs();targets=targets['walters'];path,rc=dataset('WaltersArtMuseum/api-thewalters-org','art.csv');creator_path,creator_rc=dataset('WaltersArtMuseum/api-thewalters-org','creators.csv')
    with creator_path.open(newline='',encoding='utf-8-sig') as stream:creators={x['id']:x for x in csv.DictReader(stream) if re.fullmatch(r'\d+',x.get('id') or '')}
    with path.open(newline='',encoding='utf-8-sig') as stream:objects={x['AccessionNumber']:x for x in csv.DictReader(stream) if x.get('AccessionNumber') in targets}
    for i,(key,resources) in enumerate(sorted(targets.items()),1):
        dest=RUN/'native/walters'/(hashlib.sha256(key.encode()).hexdigest()+'.json.gz');held=RUN/'native-holds/walters'/(hashlib.sha256(key.encode()).hexdigest()+'.json')
        if dest.exists() or held.exists():continue
        try:
            o=objects.get(key);url='https://art.thewalters.org/object/'+key+'/'
            raw,receipt=n.f.get(url);soup=BeautifulSoup(raw,'html.parser')
            def text(selector):
                xs=soup.select(selector);assert len(xs)==1,selector;return ' '.join(xs[0].get_text(' ',strip=True).split())
            title=text('h1.artwork--title');date=text('.section__date');acc=text('.stat--accession-number .stat > p');author=text('.section__author');assert acc==key
            if o:assert n.old.norm(o['Title'])==n.old.norm(title), 'Dataset and live object title conflict'
            lo,hi,precision=n.date_parse(date);images=soup.select('a.item__image');image=None;grant=False;image_note=None
            if images:
                selected=images[0];item=selected.find_parent(class_='item');im=selected.find('img',src=True)
                grants=item.select('.item__actions .tooltip__inner a[href]') if item else [];downloads=item.select('a.btn--download__image[href]') if item else []
                if im and len(grants)==1 and grants[0]['href']==n.CC0 and len(downloads)==1:
                    filenames=parse_qs(urlsplit(downloads[0]['href']).query).get('download',[])
                    if filenames==[unquote(Path(urlsplit(im['src']).path).name)] and re.search(r'(?:^|_)'+re.escape(key)+r'(?:_|\.)',filenames[0]):
                        image=im['src'];grant=True;image_note='Museum primary photograph; exact accession appears in filename.'
                        if re.search(r'_BW(?:_|\.)',filenames[0]):image_note+=' Archival monochrome reproduction; original colours are not represented.'
            labels=[a.get_text(' ',strip=True).split(' (')[0] for a in soup.select('.section__author a')]
            if not labels:labels=[author]
            qualified=[author] if re.search(r'\?|\b(attributed|after|workshop|school|follower|circle|possibly|probably)\b',author,re.I) else []
            ids=re.findall(r'\d+',o.get('Creators') or '') if o else []
            authorities=[dict(scheme='walters-person',external_id=x,label=creators.get(x,{}).get('name')) for x in ids if x in creators]
            medium=None;dimensions=None;credit=None;classification=o.get('Classification') or o.get('ObjectName') if o else None
            for heading in soup.select('.stat h3'):
                label=heading.get_text(' ',strip=True);value=heading.find_next_sibling('p');value=' '.join(value.get_text(' ',strip=True).split()) if value else None
                if label in ('Medium','Medium/Technique'):medium=value
                elif label=='Dimensions':dimensions=value
                elif label=='Credit Line':credit=value
            v=dict(native_id=o['ObjectID'] if o else key,scheme='walters-object' if o else 'walters-accession',accession=key,titles=[title],dates=dict(display=date,start=lo,end=hi),date_precision=precision,medium=medium or (o.get('Medium') if o else None),dimensions=dimensions or (o.get('Dimensions') if o else None),page=url,creator_labels=labels,creator_authorities=authorities,raw_creator_data=dict(label=author,authorities=[creators[x] for x in ids if x in creators]),qualified_creators=qualified,image=image,image_open=grant,image_rights='CC0 1.0 — exact photograph' if grant else None,license_url=n.CC0,credit=credit,institution_id=n.IIDS['walters'],classification=classification,work_type=n.type_for([classification or ''],medium or ''),holding_qualified=bool(re.search(r'\b(loan|lent by|private collection|deaccession)\b',credit or '',re.I)),image_view_note=image_note)
            # The museum excludes underlying artist rights. Preserve a separate hold for recent deaths.
            deaths=[int(x) for x in re.findall(r'\b\d{4}\s*[-–]\s*(\d{4})\b',author)]
            if deaths and max(deaths)>1955:v['image_open']=False;v['image_rights']='Photograph CC0; underlying artist rights require further evidence'
            m.save(dest,dict(provider='walters',key=key,state='captured',facts=v,raw=o,receipt=receipt,dataset_receipt=rc,creator_receipt=creator_rc,source_index_ids=[x['id'] for x in resources],index_bindings=[b for x in resources for b in x['artline_bindings']]))
        except Exception as e:m.save(held,dict(key=key,error=repr(e),source_index_ids=[x['id'] for x in resources]))
        if i%50==0:print('Walters native objects',i,'/',len(targets),flush=True)


if __name__=='__main__':
    n.configure()
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs={pool.submit(fn):name for name,fn in [('moma',moma),('walters',walters)]}
        for job in as_completed(jobs):
            try:job.result();print('Completed',jobs[job],flush=True)
            except Exception as e:m.save(RUN/'native-holds'/(jobs[job]+'-run.json'),dict(error=repr(e),at=m.now()));print('Error',jobs[job],repr(e),flush=True)
