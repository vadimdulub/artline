#!/usr/bin/env python3
"""Selected official Chinese museum and mural-site records; research only."""
import argparse, concurrent.futures, hashlib, importlib.util, re
from urllib.parse import urljoin
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('research',__file__.replace('research-chinese-museums-','research-chinese-art-'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

def npm():
    s=r.Source(); leads={}; errors=[]
    periods=['618~907~唐','907~960~五代','960~1279~宋','1271~1368~元','1368~1644~明','1644~1911~清']
    for period in periods:
        payload=dict(RegisterType='繪畫',IndexYear=None,WestBeginYear=0,WestEndYear=0,YearDisplay=period,
                     SearchContent=None,RegisterTypeEng=None,PageInfo=dict(PageIndex=1,PageSize=30,PageCount=1))
        text,rc=s.search_post('https://digitalarchive.npm.gov.tw/opendata/Pub/Search',payload)
        soup=BeautifulSoup(text,'html.parser')
        for card in soup.select('a.card[onclick]'):
            match=re.search(r"Detail\('(\d+)', '([A-Z])'\)",card['onclick'])
            if not match:continue
            oid,dep=match.groups();key=dep+'/'+oid
            leads[key]=dict(source_id=oid,dep=dep,title=card.select_one('.card-title').get_text(' ',strip=True),
                           index_evidence=rc,index_period=period,source_url=f'https://digitalarchive.npm.gov.tw/opendata/Pub/Detail?dep={dep}&id={oid}&mode=full')
        print('NPM',period,len(leads),'selected index records',flush=True)
    # Individually verified masterpiece reference, which need not occur on first index pages.
    leads['P/1195']=dict(source_id='1195',dep='P',title='宋范寬谿山行旅圖　軸',index_period=None,
                        source_url='https://digitalarchive.npm.gov.tw/opendata/Pub/Detail?dep=P&id=1195&mode=full')
    r.save('npm-index.json',list(leads.values()));out=[]
    for n,lead in enumerate(leads.values(),1):
        try:
            text,rc=s.get(lead['source_url'],as_json=False);soup=BeautifulSoup(text,'html.parser')
            tables=[]
            for tr in soup.select('tr'):
                cells=[x.get_text(' ',strip=True) for x in tr.select('th,td')]
                if cells:tables.append(cells)
            facts={}
            for row in tables:
                if len(row)==2 and row[0] in ['文物統一編號','作品號','品名','分類','作者','數量','創作時間']:facts[row[0]]=row[1]
            images=[urljoin(lead['source_url'],img['src']) for img in soup.select('img[src]') if '/Image/GetImage?' in img['src']]
            manifests=[urljoin(lead['source_url'],a['href']) for a in soup.select('a[href]') if 'manifest=' in a['href']]
            record=r.candidate('npm',dict(basic_fields=facts,tables=tables,index=lead,manifest_links=manifests),rc,
                source_id=lead['dep']+'/'+lead['source_id'],title=facts.get('品名') or lead['title'],museum='National Palace Museum, Taipei',
                accession_number=facts.get('文物統一編號') or facts.get('作品號'),source_url=lead['source_url'],creator_label=facts.get('作者'),
                date_display=facts.get('創作時間'),year_start=None,year_end=None,source_type=facts.get('分類'),culture='Chinese collection; individual attribution retained',
                medium=None,image_url=images[0] if images else None,image_rights_label='Museum offers CC0 low-resolution and CC BY 4.0 medium-resolution images; resource tier not yet selected',
                image_license_url=None,credit='National Palace Museum, Taipei',identity_note='Museum catalogue labels retained verbatim. Dynasty search is discovery evidence, not an exact creation date or proof of attribution. Views and album leaves need reconciliation.')
            record['open_image_tiers']=[dict(label='CC0',maximum_pixels=1000000,license_url=r.CC0),dict(label='CC BY 4.0',maximum_pixels=6000000,license_url='https://creativecommons.org/licenses/by/4.0/')]
            record['image_decision']='open_image_available_choose_exact_view_and_resolution';record['image_views']=images
            out.append(record)
        except Exception as e:
            errors.append(dict(lead=lead,error=str(e)))
            if s.blocked:break
        if n%30==0:r.save('npm.json.gz',dict(records=out,errors=errors,bounded=True));print('NPM object pages',n,flush=True)
    r.save('npm.json.gz',dict(records=out,errors=errors,bounded=True))

def namoc():
    s=r.Source();out={};pages=[]
    # Bounded 84-page Chinese-painting catalogue: metadata only, not image downloads.
    for page in range(1,85):
        url='https://www.namoc.cn/namoc/zgh/dc_list'+('' if page==1 else '_'+str(page))+'.shtml'
        text,rc=s.get(url,as_json=False);soup=BeautifulSoup(text,'html.parser');pages.append(rc)
        for block in soup.select('p.image'):
            card=block.parent;link=block.select_one('a[href]');image=block.select_one('img[src]')
            if not link:continue
            t=card.get_text(' ',strip=True)
            match=re.search(r'^(.*?)\s*作者[：:]\s*(.*?)\s*创作年代[：:]\s*(.*?)\s*规格[：:]\s*(.*)$',t)
            if not match:continue
            title,creator,date,dim=match.groups();first=last=int(date) if re.fullmatch(r'\d{4}',date) else None
            src=urljoin(url,link['href'])
            out[src]=r.candidate('namoc',dict(source_card_text=t,dimensions=dim),rc,source_id=src.split('/')[-1].split('.')[0],title=title,
                museum='National Art Museum of China',accession_number=None,source_url=src,creator_label=creator,
                date_display=date,year_start=first,year_end=last,medium=None,source_type='中国画',culture='Chinese painting',
                image_url=urljoin(url,image['src']) if image else None,image_license_url=None,image_rights_label='No open reuse permission established',credit='National Art Museum of China',
                identity_note='Collection index facts; exact object detail and reproduction rights need review. Contemporary copies of historical murals retain their actual creation date.')
        print('NAMOC index page',page,'records',len(out),flush=True)
        r.save('namoc.json.gz',dict(records=list(out.values()),index_pages=pages,bounded=True))

def dunhuang():
    s=r.Source();out=[];errors=[]
    # Individually selected caves across major phases; no full-site enumeration.
    for cave in [45,57,61,85,98,112,158,172,220,254,257,275,285,321,322,329,331,420]:
        url=f'https://www.e-dunhuang.com/cave/10.0001/0001.0001.{cave:04}'
        try:
            text,rc=s.get(url,as_json=False);soup=BeautifulSoup(text,'html.parser')
            sections=[]
            for modal in soup.select('.modal'):
                heading=modal.select_one('.modal-title')
                if not heading:continue
                title=heading.get_text(' ',strip=True)
                if not any(x in title for x in ['壁','披','藻井','顶部']):continue
                body=' '.join(p.get_text(' ',strip=True) for p in modal.select('p'))
                if not body or '登录' in body and len(body)<70:continue
                sections.append(dict(title=title,description=body,source_anchor=modal.get('id')))
            out.append(dict(provider='dunhuang',source_id='mogao-'+str(cave),title=f'Mogao Cave {cave}: documented painted surfaces',
                museum='Dunhuang Academy / Mogao Caves',source_url=url,evidence=rc,record_kind='cave_research_container',
                source_sections=sections,source_title=soup.title.get_text(' ',strip=True) if soup.title else None,
                raw_text=soup.get_text(' ',strip=True),image_decision='No open reuse permission established; metadata and official viewing link only',
                decision='Scene and layer identities require individual catalogue records; this container is not counted as an artwork',current_display=None))
            print('Dunhuang cave',cave,'documented surfaces',len(sections),flush=True)
        except Exception as e:
            errors.append(dict(cave=cave,error=str(e)))
            if s.blocked:break
    r.save('dunhuang.json.gz',dict(records=out,errors=errors,bounded=True))

def simple_years(text):
    if re.fullmatch(r'\d{3,4}',text):return int(text),int(text)
    m=re.fullmatch(r'(\d{3,4})\s*[-–]\s*(\d{3,4})',text)
    return tuple(map(int,m.groups())) if m else (None,None)

def hongkong():
    s=r.Source();out={};errors=[]
    base='https://hk.art.museum/en/web/ma/collections.html'
    text,rc=s.get(base,as_json=False);soup=BeautifulSoup(text,'html.parser')
    urls={urljoin(base,a['href']) for a in soup.select('a[href]') if any(k in a['href'] for k in ['chinese-painting','xubaizhai','chih-lo-lou','china-trade'])}
    urls.add('https://hk.art.museum/en/web/ma/collections/chinese-painting-and-calligraphy.html')
    for url in sorted(urls):
        try:
            text,rc=s.get(url,as_json=False);soup=BeautifulSoup(text,'html.parser')
            for card in soup.select('li.collection-item'):
                title=card.select_one('.data-title');attrs=[x.get_text(' ',strip=True) for x in card.select('.data-attribute > li')]
                if not title or len(attrs)<3:continue
                title=title.get_text(' ',strip=True);creator,date,medium=attrs[:3];lo,hi=simple_years(date)
                idx=card.get('data-index');img=soup.select_one(f'.collection-popup-toggle[data-index="{idx}"] img')
                key=hashlib.sha256((title+'|'+str(attrs)).encode()).hexdigest()[:20]
                out[key]=r.candidate('hkmoa',dict(attributes=attrs,collection_page=url,source_index=idx),rc,
                    source_id=key,title=title,museum='Hong Kong Museum of Art',accession_number=None,source_url=url,
                    creator_label=creator,date_display=date,year_start=lo,year_end=hi,medium=medium,source_type='Chinese painting/calligraphy collection',culture='Chinese',
                    image_url=urljoin(url,img['src']) if img else None,image_license_url=None,image_rights_label='No open reuse permission established',credit='Hong Kong Museum of Art',
                    identity_note='Exact collection-page caption; original artist lifespan stays in creator label and is not used as creation date. No accession supplied.')
            print('Hong Kong',url,len(out),flush=True)
        except Exception as e:
            errors.append(dict(url=url,error=str(e)))
            if s.blocked:break
    r.save('hkmoa.json.gz',dict(records=list(out.values()),errors=errors,bounded=True))

def ashmolean():
    s=r.Source();out={};errors=[]
    # Nine pages of the museum's selected Chinese-painting catalogue, not its entire collection.
    for offset in range(0,225,25):
        url=f'https://jameelcentre.ashmolean.org/collection/7/10232/10271/all/per_page/25/offset/{offset}/sort_by/date/sort_order/desc/morph/hide'
        try:
            text,rc=s.get(url,as_json=False);soup=BeautifulSoup(text,'html.parser')
            for card in soup.select('li.blockCont'):
                a=card.select_one('h3 a[href]')
                if not a:continue
                fields={}
                for item in card.select('.infoList li'):
                    k=item.select_one('strong');v=item.select_one('span')
                    if k and v:fields[k.get_text(' ',strip=True)]=v.get_text(' ',strip=True)
                oid=a['href'].rsplit('/',1)[-1];date=fields.get('Date','');lo,hi=simple_years(date);img=card.select_one('img[src]')
                out[oid]=r.candidate('ashmolean',fields,rc,source_id=oid,title=a.get_text(' ',strip=True),museum='Ashmolean Museum',
                    accession_number=fields.get('Accession no.'),source_url=a['href'],creator_label=None,date_display=date or None,year_start=lo,year_end=hi,
                    medium=None,source_type='Chinese-painting catalogue',culture='Chinese collection; exact origin verification pending',
                    image_url=img['src'] if img else None,image_license_url=None,image_rights_label='No open reuse permission established',credit='Ashmolean Museum, University of Oxford',
                    identity_note='Catalogue index facts; individual object page required for creator and image permission. Museum display markers are not imported.')
            print('Ashmolean',offset,len(out),flush=True)
        except Exception as e:
            errors.append(dict(url=url,error=str(e)))
            if s.blocked:break
    r.save('ashmolean.json.gz',dict(records=list(out.values()),errors=errors,bounded=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['npm','namoc','dunhuang','hongkong','ashmolean','all']);a=p.parse_args()
    if a.action=='all':
        with concurrent.futures.ThreadPoolExecutor(3) as pool:
            jobs={pool.submit(fn):fn.__name__ for fn in [npm,namoc,dunhuang]}
            for job in concurrent.futures.as_completed(jobs):
                try:job.result()
                except Exception as e:r.save(jobs[job]+'-error.json',dict(error=str(e)));print(jobs[job],str(e),flush=True)
    else:globals()[a.action]()
