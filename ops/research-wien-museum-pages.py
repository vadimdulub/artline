#!/usr/bin/env python3
"""Selected Wien Museum public HTML records, never the prohibited internal API."""
import argparse,importlib.util,json,re,unicodedata
from pathlib import Path
from urllib.parse import unquote
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('public',Path(__file__).with_name('research-austrian-museums.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)

def key(text):
    return re.sub(r'[^a-z0-9]+','',unicodedata.normalize('NFKD',text.lower().replace('ß','ss')).encode('ascii','ignore').decode())

def parse(raw,receipt):
    soup=BeautifulSoup(raw,'html.parser');facts={}
    for row in soup.select('dl.object-details .row'):
        dt,dd=row.find('dt'),row.find('dd')
        if dt and dd:facts[dt.get_text(' ',strip=True)]=dd.get_text(' ',strip=True)
    images=[]
    for fig in soup.select('figure[data-object-image]'):
        im=fig.select_one('img.object-image');cap=fig.select_one('[data-caption]')
        if not im or not cap:continue
        url=im.get('data-src');caption=cap.get_text(' ',strip=True);links=[]
        for a in soup.select('a[download][href]'):
            if a['href']!=url:continue
            links.extend(x['href'] for x in a.parent.select('a[href*="creativecommons.org"]'))
        approved={'https://creativecommons.org/licenses/by/4.0/deed.de':('https://creativecommons.org/licenses/by/4.0/','CC BY 4.0','cc_by'), 'https://creativecommons.org/publicdomain/zero/1.0/deed.de':('https://creativecommons.org/publicdomain/zero/1.0/','CC0','cc0'), 'https://creativecommons.org/publicdomain/zero/1.0/':('https://creativecommons.org/publicdomain/zero/1.0/','CC0','cc0')}
        licence=approved.get(links[0]) if len(set(links))==1 else None
        credit=fig.get('data-copy-text','');eligible=bool(licence and caption.startswith(licence[1]) and credit and 'Wien Museum' in credit and (licence[2]=='cc0' or 'Foto:' in caption))
        images.append({'source_image_url':url,'preview_url':im.get('src'),'width':int(im.get('data-width',0)),'height':int(im.get('data-height',0)),'caption':caption,'credit':credit,'license_links':links,'license':licence if eligible else None})
    makers=[]
    for row in soup.select('dl.object-details .row'):
        dt=row.find('dt')
        if dt and dt.get_text(' ',strip=True)=='Künstler:in/Hersteller:in':
            for tr in row.select('tbody tr'):
                td=tr.find_all('td');
                if len(td)==2:makers.append({'name':td[0].get_text(' ',strip=True),'role':td[1].get_text(' ',strip=True)})
    return {'url':receipt['url'],'capture':receipt,'title':soup.h1.get_text(' ',strip=True) if soup.h1 else None,'facts':facts,'makers':makers,'images':images,'authority_links':[a['href'] for a in soup.select('a[href*="d-nb.info/gnd/"]')]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);a=ap.parse_args();root=a.run;run=root/'wien';records=json.loads((root/'wikimedia/researched-records.json').read_text())['records'];records=[r for r in records if r['institution_qid']=='Q505873']
    xml=(root/'source-preflight/wien-sitemap-de.xml').read_text();urls=set(re.findall(r'<loc>(https://sammlung.wienmuseum.at/objekt/[^<]+)</loc>',xml));by_id={re.search(r'/objekt/(\d+)',u)[1]:u for u in urls};by_name={key(unquote(re.sub(r'^.*/objekt/\d+-','',u)).strip('/')):u for u in urls};selection={};held=[]
    for r in records:
        ids={re.search(r'/objekt/(\d+)',x['url'])[1] for x in r['object_urls'] if x['url'].startswith('https://sammlung.wienmuseum.at/objekt/') and re.search(r'/objekt/(\d+)',x['url'])}
        matches={by_id[i] for i in ids if i in by_id}
        if not matches:matches={by_name[key(t)] for t in r['titles'] if len(key(t))>=8 and key(t) in by_name}
        if len(matches)==1:
            u=matches.pop();selection[u]={'qid':r['qid'],'method':'Exact published object identifier or full title from the public sitemap; facts independently checked next'}
        else:held.append({'qid':r['qid'],'reason':'Public page identity needs further research'})
    for oid in ('102692','200675'):
        if oid in by_id:selection.setdefault(by_id[oid],{'qid':None,'method':'Individually inspected official painting record'})
    p.core.save_new(run/'selection.json',{'records':[dict(url=u,**lead) for u,lead in selection.items()],'held':held})
    pages=p.PublicPages(run)
    for u,lead in selection.items():
        oid=re.search(r'/objekt/(\d+)',u)[1];out=run/'objects'/(oid+'.json')
        if out.exists():continue
        try:
            raw,receipt=pages.get(u);data=parse(raw,receipt);data.update(lead=lead,object_id=oid);p.core.save_new(out,data)
            print(p.core.now(),'Wien Museum selected public record',oid,'images with explicit licence',sum(bool(x['license']) for x in data['images']),flush=True)
        except Exception as exc:print(p.core.now(),'Wien record held',oid,type(exc).__name__,str(exc)[:150],flush=True)
if __name__=='__main__':main()
