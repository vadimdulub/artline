#!/usr/bin/env python3
"""Select exact Russian Museum / Wikidata / Commons image chains before download."""
import argparse, hashlib, importlib.util, json, re
from pathlib import Path
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('research',ROOT/'ops/research-russian-session.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
RUN=r.RUN

def inventory_key(value):
    return re.sub(r'[^a-z0-9]','',value.casefold().translate(str.maketrans({'ж':'zh','б':'b','р':'r','г':'g','и':'i','к':'k'})))

def candidates():
    raw=json.loads(Path('/tmp/artline-russian-image-candidates.json').read_bytes())
    r.save(RUN/'wikidata-image-candidates.json',raw)
    works={w['url']:w for f in sorted((RUN/'batch').glob('chunk-*.json')) for w in json.loads(f.read_bytes())['works']}
    artists=json.loads((RUN/'selected-authors.json').read_bytes())
    selected={}; ambiguous=[]
    for row in raw['results']['bindings']:
        q=row['creator']['value'].rsplit('/',1)[1]
        if q not in artists or not artists[q]['death'] or artists[q]['death']>1955:continue
        inv=row.get('inventory',{}).get('value','')
        key=inventory_key(inv)
        url=row.get('url',{}).get('value','').replace('http://','https://').split('?')[0]
        if url.endswith('/'):url+='index.php'
        match=[]
        for u,w in works.items():
            if w['painter']!=q or w['work_type']!='painting' or w['creation_date']['precision']=='unknown':continue
            pathkey=inventory_key(u.split('/')[-2])
            if u==url or key and len(key)>3 and (pathkey==key or pathkey.endswith(key)):
                match.append(w)
        if len(match)!=1:continue
        w=match[0];artq=row['w']['value'].rsplit('/',1)[1]
        image=unquote(row['image']['value'].split('Special:FilePath/',1)[1])
        entry={'work':w,'artist':artists[q],'wikidata_artwork':artq,'inventory':inv,'commons_title':'File:'+image,'identity_basis':'Exact creator QID, museum collection and accession candidate; detailed museum accession is checked next.'}
        selected.setdefault(w['url'],{})[image]=entry
    out=[next(iter(v.values())) for v in selected.values() if len(v)==1]
    out.sort(key=lambda x:x['work']['url'])
    r.save(RUN/'image-candidates.json',out[:300])
    print('image candidates',len(out),'bounded selection',min(300,len(out)),flush=True)

def verify():
    good=[];bad=[]
    for n,c in enumerate(json.loads((RUN/'image-candidates.json').read_bytes())):
        w=c['work'];key=hashlib.sha256(w['url'].encode()).hexdigest()
        output=RUN/'image-object-checks'/(key+'.json')
        if output.exists():
            result=json.loads(output.read_bytes())
        else:
            try:
                soup,capture=r.fetch(w['url'])
                inv=r.txt(soup.select_one('[title="Инвентарный номер"]'))
                authors=[a.get('href') for a in soup.select('.work__author a')]
                expected=c['artist']['url'].removeprefix(r.BASE)
                title=r.txt(soup.select_one('.work__title'))
                period=r.txt(soup.select_one('.period'))
                safe=bool(inv and inventory_key(inv)==inventory_key(c['inventory']) and expected in authors and len(authors)==1 and r.norm(title)==r.norm(w['title']))
                result={**c,'verified':safe,'museum_inventory':inv,'museum_title':title,'museum_date':period,'museum_author_links':authors,'museum_capture':capture}
            except Exception as e:result={**c,'verified':False,'error':str(e)[:300]}
            r.save(output,result)
        (good if result['verified'] else bad).append(result)
        if (n+1)%20==0:print('object image identity',n+1,'verified',len(good),'deferred',len(bad),flush=True)
    r.save(RUN/'image-identity-verified.json',good);r.save(RUN/'image-identity-deferred.json',bad)
    print('verified image identities',len(good),flush=True)

def rights():
    candidates=json.loads((RUN/'image-identity-verified.json').read_bytes())
    pages={}
    for start in range(0,len(candidates),15):
        titles='|'.join(c['commons_title'] for c in candidates[start:start+15])
        data=r.jsonfetch('https://commons.wikimedia.org/w/api.php',{'action':'query','format':'json','titles':titles,'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size','rvprop':'ids|content','rvslots':'main'})
        for page in data.get('query',{}).get('pages',{}).values():pages[page['title'].replace('_',' ')]=page
        print('Commons file metadata',min(start+15,len(candidates)),'/',len(candidates),flush=True)
    cleared=[];deferred=[]
    for c in candidates:
        p=pages.get(c['commons_title'].replace('_',' '),{})
        info=(p.get('imageinfo') or [{}])[0];ext=info.get('extmetadata',{})
        field=lambda k:ext.get(k,{}).get('value','')
        label=field('LicenseShortName');license=field('LicenseUrl')
        source=field('Credit');wikitext=(p.get('revisions') or [{}])[0].get('slots',{}).get('main',{}).get('*','')
        reason=''
        if not info.get('url'):reason='no_source_image'
        elif label not in ('Public domain','CC0','CC BY-SA 4.0','CC BY-SA 3.0','CC BY 4.0','CC BY 3.0'):reason='licence_not_allowlisted'
        elif re.search(r'\b(?:rusmuseumvrm\.ru|(?:en\.)?rusmuseum\.ru)\b',source,re.I):reason='museum_source_requires_separate_permission'
        elif info.get('size',0)>20_000_000:reason='source_image_over_20mb_budget'
        elif label=='Public domain' and field('Copyrighted')!='False':reason='public_domain_status_conflict'
        elif label!='Public domain' and not license.startswith(('https://creativecommons.org/','http://creativecommons.org/')):reason='missing_explicit_licence_url'
        if reason:deferred.append({**c,'reason':reason,'license_label':label,'credit':source});continue
        status='public_domain' if label=='Public domain' else 'cc0' if label=='CC0' else 'cc_by_sa' if 'BY-SA' in label else 'cc_by'
        cleared.append({**c,'commons_page':p,'source_image_url':info['url'],'commons_original_sha1':info['sha1'],'license_label':label,'license_url':license.replace('http://','https://') if license else 'https://creativecommons.org/publicdomain/mark/1.0/','rights_status':status,'credit':source,'commons_creator_credit':field('Artist'),'commons_page_url':info['descriptionurl']})
    r.save(RUN/'image-rights-cleared.json',cleared);r.save(RUN/'image-rights-deferred.json',deferred)
    print('rights cleared',len(cleared),'deferred',len(deferred),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['candidates','verify','rights']);a=p.parse_args();globals()[a.phase]()
