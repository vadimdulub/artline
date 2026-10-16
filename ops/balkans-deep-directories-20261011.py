"""Country directory ledgers; directory entries do not establish artworks."""
import concurrent.futures,importlib.util,json,re,sys
from urllib.parse import urlparse
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('b','ops/balkans-deep-20261011.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
MK='https://aspi.mk/иматели-на-информации/јавни-претпријатија-и-установи-во-реп/јавни-установи-во-република-северна-м/музеи/'
def build():
    register=m.h.load(m.RUN/'bulgaria-official-register.json');rows=[]
    for sheet in register['sheets']:
        for raw in sheet['rows']:
            r={re.sub(r'\d','',k):v for k,v in raw.items()}
            if not r.get('B')or not r.get('C')or r['B']=='Наименование на музея'or r['B'].isdigit():continue
            sites=[]
            for token in re.split(r'[\s;]+',r.get('G','')):
                token=token.strip('.,"()')
                if '@'not in token and re.match(r'^(?:https?://|www\.)[^\s]+\.[a-zA-Z]{2,}',token):sites.append(token if '://'in token else'https://'+token)
            rows.append(dict(country='BG',name=r['B'].strip(),city=r['C'].strip(),directory_number=r.get('A'),websites=sites,source=register['receipt']['url'],status='Directory entry indexed; individual object research remains open.'))
    # Carry forward the fully documented Ministry audit, with its actual check date.
    prior=m.h.load(m.ROOT/'docs/research/greek-museums-20261008/ministry-directory-audit.json')
    for x in prior['entries']:
        rows.append(dict(country='GR',name=x['name'],city=x.get('region'),directory_number=x['key'],websites=[l['url']for l in x.get('outgoing_links',[])],source=x['source_url'],prior_checked_at=prior['at'],status='Prior Ministry directory research carried forward; separate current catalogue/source checks recorded.'))
    p=m.page(MK)
    for x in p['links']:
        if any(t in x['text']for t in ['Музеј','музеј','галерија']) and x['url']!=MK and 'aspi.mk' in x['url']:
            rows.append(dict(country='MK',name=x['text'],city=None,directory_number=None,websites=[],source=x['url'],status='Government museum directory indexed; individual object research remains open.'))
    rows=list({(x['country'],x['name'],x.get('city')):x for x in rows}.values())
    m.h.save(m.RUN/'country-directory-ledger-reviewed.json',dict(at=m.h.now(),records=rows,review_note='Removed the numeric spreadsheet column header and retained identically named branches in different cities. Earlier draft is preserved. Directory entries do not establish object-level collection coverage.'))
    print({cc:sum(x['country']==cc for x in rows)for cc in ['GR','BG','MK']},flush=True)
def audit_bg():
    rows=m.h.load(m.RUN/'country-directory-ledger.json')['records'];urls=sorted({u for x in rows if x['country']=='BG'for u in x['websites']})
    def one(url):
        try:
            p=m.page(url);return dict(url=url,status=p['receipt']['status'],title=p['title'],receipt=p['receipt'])
        except Exception as e:return dict(url=url,error=type(e).__name__+': '+str(e)[:200])
    result=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5)as pool:
        for x in pool.map(one,urls):
            result.append(x)
            if len(result)%20==0:print('BULGARIA DIRECTORY',len(result),'/',len(urls),flush=True)
    m.h.save(m.RUN/'bulgaria-directory-audit.json',dict(at=m.h.now(),sources=result))
if __name__=='__main__':globals()[sys.argv[1]]()
