#!/usr/bin/env python3
"""Scoped production collection research, with immutable source evidence."""
import argparse, base64, collections, concurrent.futures, datetime, difflib, gzip, hashlib, html, importlib.util, json, re, subprocess, threading, time, unicodedata, uuid
from pathlib import Path
from urllib.parse import urljoin,urlparse,quote
import psycopg, requests
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg import sql
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/havre-rouen-cyprus-20261006'
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/RUN.name
ACTOR='local-european-research'
def now():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def uid(value):return str(uuid.uuid5(uuid.NAMESPACE_URL,RUN.name+'/'+value))
def norm(v):return ' '.join(re.findall(r'[^\W_]+',''.join(c for c in unicodedata.normalize('NFKD',v or '').casefold()if not unicodedata.combining(c))))
def save(path,value):
    raw=json.dumps(value,ensure_ascii=False,indent=2,default=str).encode()
    if path.suffix=='.gz':raw=gzip.compress(raw,mtime=0)
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==raw,'Preserve evidence: '+str(path)
    else:path.write_bytes(raw)
def load(path):return json.loads(gzip.decompress(path.read_bytes())if path.suffix=='.gz'else path.read_bytes())
def connect(target='production',readonly=True):
    dsn='postgresql://localhost/artline'
    if target=='production':
        secret=subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319','--account=vadim@alingva.com'],text=True).strip()
        params=psycopg.conninfo.conninfo_to_dict(secret);params.update(host='127.0.0.1',port='55478',sslmode='disable',connect_timeout='20');dsn=psycopg.conninfo.make_conninfo(**params)
    return psycopg.connect(dsn,row_factory=dict_row,autocommit=True,options='-c timezone=UTC -c statement_timeout=180000 -c lock_timeout=10000'+(' -c default_transaction_read_only=on'if readonly else''))
LAST={};LOCKS=collections.defaultdict(threading.Lock);STOPPED=set()
def capture(url,method='GET',timeout=45):
    key=sha((url if method=='GET'else method+' '+url).encode());dest=RUN/'captures'/(key+'.json');body=dest.with_suffix('.body.gz');host=urlparse(url).netloc
    if dest.exists():
        receipt=load(dest);raw=gzip.decompress(body.read_bytes());assert sha(raw)==receipt['sha256'];return raw,receipt
    if host in STOPPED:raise ValueError('Host paused after source denial: '+host)
    with LOCKS[host]:
        delay=10.5 if 'muma-lehavre' in host or 'mbarouen' in host else 1.1
        time.sleep(max(0,LAST.get(host,0)+delay-time.monotonic()));LAST[host]=time.monotonic()
        with requests.request(method,url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected factual catalogue metadata)'},timeout=(15,timeout),stream=True)as response:
            raw=b''
            for chunk in response.iter_content(65536):
                raw+=chunk;assert len(raw)<8_000_000,'Metadata response exceeds bound'
            receipt=dict(url=url,method=method,final_url=response.url,status=response.status_code,sha256=sha(raw),bytes=len(raw),retrieved_at=now(),body_path=str(body.relative_to(ROOT)))
    body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(gzip.compress(raw,mtime=0));save(dest,receipt)
    if response.status_code in (403,429):STOPPED.add(host)
    return raw,receipt
def discover():
    indexes={'muma':'https://www.muma-lehavre.fr/fr/collections/oeuvres-commentees',
      'rouen':'https://mbarouen.fr/fr/collections',
      'leventis':'https://leventisgallery.org/collections/paris-collection/',
      'cvar':'https://cvar.severis.org/en/explore/collections-archives/paintings/'}
    def one(item):
        source,url=item;raw,rc=capture(url);soup=BeautifulSoup(raw,'html.parser')
        links=list({urljoin(url,a['href']):a.get_text(' ',strip=True)for a in soup.select('a[href]')}.items())
        data=dict(source=source,receipt=rc,links=[dict(url=u,title=t)for u,t in links],text=soup.get_text(' ',strip=True))
        save(RUN/'discovery'/(source+'.json'),data)
        print(source,rc['status'],'links',len(links),json.dumps(links[:12],ensure_ascii=False),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:list(pool.map(one,indexes.items()))
def objects():
    def french(source):
        d=load(RUN/'discovery'/(source+'.json'));urls=[];index_receipts=[]
        if source=='muma':urls=[x['url']for x in d['links']if re.search(r'/oeuvres-commentees/[^/]+/[^/]+$',x['url'])]
        else:
            themes=[x['url']for x in d['links']if '/fr/collections/'in x['url']]
            for url in themes:
                raw,rc=capture(url);index_receipts.append(rc)
                if rc['status']!=200:continue
                urls +=[urljoin(url,a['href'])for a in BeautifulSoup(raw,'html.parser').select('a[href]')if '/fr/oeuvres/'in a['href']]
        urls=list(dict.fromkeys(urls));assert len(urls)<=180
        save(RUN/'object-indexes'/(source+'.json'),dict(urls=urls,receipts=index_receipts,initial=d['receipt']))
        # The primary site's featured objects form a bounded metadata selection.
        for index,url in enumerate(urls):
            path=RUN/'objects'/source/(sha(url.encode())+'.json')
            if path.exists():continue
            raw,rc=capture(url);soup=BeautifulSoup(raw,'html.parser');data=dict(url=url,source=source,receipt=rc)
            if rc['status']==200:
                data['title']=soup.select_one('#page-title').get_text(' ',strip=True)if soup.select_one('#page-title')else None
                data['legends']=[n.get_text('|',strip=True)for n in soup.select('.legend_visuel')]
                data['creator']=[n.get_text(' ',strip=True)for n in soup.select('.artiste')]
                data['details']=[n.get_text('|',strip=True)for n in soup.select('.details')]
                data['shortlink']=[n.get('href')for n in soup.select('link[rel=shortlink]')]
            save(path,data)
            if (index+1)%10==0:print(source,index+1,'/',len(urls),'metadata pages',flush=True)
    def cvar():
        links={};receipts=[]
        base='https://cvar.severis.org/en/explore/collections-archives/paintings/'
        for page in range(1,5):
            url=base+('?page='+str(page)if page>1 else'');raw,rc=capture(url);receipts.append(rc)
            if rc['status']!=200:continue
            for a in BeautifulSoup(raw,'html.parser').select('a[href]'):
                if '/collections/item/'in a['href']:links[urljoin(url,a['href'])]=a.get_text(' ',strip=True)
        save(RUN/'object-indexes/cvar.json',dict(links=links,receipts=receipts))
        for url,label in links.items():
            path=RUN/'objects/cvar'/(sha(url.encode())+'.json')
            if path.exists():continue
            # Reject definitely post-cutoff index dates before object requests.
            end=re.search(r'(\d{4})(?:--\d\d--\d\d)?\s*$',label)
            if end and int(end[1])>1970:continue
            raw,rc=capture(url);soup=BeautifulSoup(raw,'html.parser')
            save(path,dict(url=url,source='cvar',receipt=rc,index_label=label,text=soup.get_text(' ',strip=True),headings=[n.get_text(' ',strip=True)for n in soup.select('h1,h2')]))
        print('cvar',len(list((RUN/'objects/cvar').glob('*.json'))),'metadata pages',flush=True)
    def leventis():
        base='https://cypriotartists.leventisgallery.org/api/en/'
        raw,rc=capture(base+'fetch-artists','POST');assert rc['status']==200;index=json.loads(raw)
        save(RUN/'object-indexes/leventis.json',dict(data=index,receipt=rc))
        for a in index['artists'][:6]:
            raw,rc=capture(base+'fetch-artist/'+a['slug'],'POST');assert rc['status']==200
            save(RUN/'objects/leventis'/(a['slug']+'.json'),dict(profile=json.loads(raw),receipt=rc))
        print('leventis',len(index['artists'][:6]),'museum artist catalogues',flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        jobs=[pool.submit(french,x)for x in ['muma','rouen']]+[pool.submit(cvar),pool.submit(leventis)]
        for j in concurrent.futures.as_completed(jobs):j.result()
def plain(value):return BeautifulSoup(value or'','html.parser').get_text(' ',strip=True)
def parse_date(value):
    literal=plain(value);text=re.sub(r'\s+',' ',literal).strip();text=text.replace('\u2013','-').replace('\u2014','-')
    result=dict(date_display=literal or'Creation date unknown',first=None,last=None,precision='unknown')
    m=re.fullmatch(r'(?:(ca?\.|circa|vers|Vers|environ)\s*)?(\d{4})(?:\s*-\s*(\d{4}))?',text)
    if m:
        first=int(m[2]);last=int(m[3]or m[2])
        if first<=last:return dict(date_display=literal,first=first,last=last,precision='circa_range'if m[3]and m[1]else'range'if m[3]else'circa'if m[1]else'exact')
    m=re.fullmatch(r'between (\d{4}) and (\d{4})',text)
    if m and int(m[1])<=int(m[2]):return dict(date_display=literal,first=int(m[1]),last=int(m[2]),precision='range')
    m=re.fullmatch(r'(?:before|avant|Avant) (\d{4})',text)
    if m:return dict(date_display=literal,first=None,last=int(m[1]),precision='before')
    m=re.fullmatch(r'\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) (\d{4})',text)
    if m:return dict(date_display=literal,first=int(m[1]),last=int(m[1]),precision='exact')
    m=re.fullmatch(r'(\d{4})--?(\d{2})--?(\d{2})',text)
    if m:
        try:day=datetime.date(*map(int,m.groups()))
        except ValueError:return result
        return dict(date_display=literal,first=day.year,last=day.year,precision='exact')
    m=re.fullmatch(r'(\d{1,2})(?:st|nd|rd|th) century',text)
    if m:return dict(date_display=literal,first=(int(m[1])-1)*100+1,last=int(m[1])*100,precision='century')
    m=re.fullmatch(r'\d{1,2} (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) (\d{4})',text,re.I)
    if m:return dict(date_display=literal,first=int(m[1]),last=int(m[1]),precision='exact')
    m=re.fullmatch(r'(\d{4})-(\d{2})',text)
    if m:
        first=int(m[1]);last=first//100*100+int(m[2])
        if first<=last:return dict(date_display=literal,first=first,last=last,precision='range')
    if text.startswith('~'):
        d=parse_date(text[1:])
        if d['precision']in ['exact','range']:return dict(d,date_display=literal,precision='circa'if d['precision']=='exact'else'circa_range')
    roman={'XIV':14,'XV':15,'XVI':16,'XVII':17,'XVIII':18,'XIX':19}
    m=re.fullmatch(r'(?:(2nde moitié du|Fin) )?(XIV|XV|XVI|XVII|XVIII|XIX)e(?: siècle)?',text,re.I)
    if m:
        century=roman[m[2].upper()];first=(century-1)*100+1;last=century*100
        if m[1]and m[1].lower()=='2nde moitié du':first+=50
        # "Late" is preserved literally while the numeric bounds remain the
        # full stated century, without inventing an arbitrary late-century year.
        return dict(date_display=literal,first=first,last=last,precision='range'if m[1]and m[1].lower()=='2nde moitié du'else'century')
    return result
def kind(medium):
    t=norm(medium)
    if re.search(r'photocop|photograph|photocopy|photo on|photograv|print on fabric',t):return None
    if any(x in t for x in ['watercol','aquarelle']):return 'watercolor'
    if any(x in t for x in ['huile','oil','tempera','gouache','acryli']):return 'painting'
    if any(x in t for x in ['lithograph','etching','engraving','woodcut','eau forte','estampe','gravure','screenprint']):return 'print'
    if any(x in t for x in ['pencil','crayon','charcoal','ink','encre','pastel','fusain','sanguine','graphite']):return 'drawing'
    if any(x in t for x in ['bronze','sculpture','platre','marbre']):return 'sculpture'
    return 'unknown'
def facts():
    records=[];held=[]
    for source in ['muma','rouen','cvar']:
        for path in sorted((RUN/'objects'/source).glob('*.json')):
            x=load(path);f=dict(source=source,source_url=x['url'],receipt=x['receipt'],accession=None,dimensions=None,creator_label=None,image_url=None)
            if x['receipt']['status']!=200:held.append(dict(url=x['url'],reason='source_unavailable'));continue
            if source=='muma':
                if len(x['legends'])!=1:held.append(dict(url=x['url'],reason='group_or_component_review'));continue
                raw=gzip.decompress((ROOT/x['receipt']['body_path']).read_bytes());soup=BeautifulSoup(raw,'html.parser');caption=soup.select_one('.legend_visuel')
                for br in caption.select('br'):br.replace_with('\n')
                lines=[' '.join(z.split())for z in caption.get_text().splitlines()if z.strip()]
                if len(lines)<4:held.append(dict(url=x['url'],reason='caption_layout_review'));continue
                f.update(title=lines[1],creator_label=re.sub(r'\s*\([^)]*\)\s*$','',lines[0]),creator_detail=lines[0],raw_fields=lines,museum_slug='muma-le-havre')
                dates=parse_date(lines[2]);date_literal=bool(re.search(r'\d{3,4}|siècle',lines[2]))and kind(lines[2])=='unknown'
                pos=3 if dates['precision']!='unknown'or date_literal else 2
                f.update(dates);f['medium']=lines[pos];f['dimensions']=lines[pos+1]if len(lines)>pos+1 and 'cm'in lines[pos+1]else None
                if dates['precision']=='unknown'and not date_literal:f['date_display']='Creation date unknown'
                f['work_type']=kind(f['medium']);f['source_id']=x['url'].rsplit('/',1)[-1];f['scheme']='muma-object-page'
                f['holding_note']='Official MuMa collection object page, captured on '+x['receipt']['retrieved_at']+'. Collection connection only; no current display claim.'
                if re.search(r'\bMNR\b|en attente de sa restitution|déposée|déposé|dépôt',x['legends'][0],re.I):held.append(dict(url=x['url'],reason='deposit_or_restitution_context_requires_review'));continue
            elif source=='rouen':
                if len(x['creator'])!=1 or len(x['details'])!=1:held.append(dict(url=x['url'],reason='object_layout_review'));continue
                raw=gzip.decompress((ROOT/x['receipt']['body_path']).read_bytes());soup=BeautifulSoup(raw,'html.parser')
                artist=soup.select_one('.artiste h2');detail=soup.select_one('.details');segments=list(detail.stripped_strings)
                creator=artist.get_text(' ',strip=True)if artist else None
                creator=re.sub(r'\s*\([^)]*\).*','',creator or'').strip()or None
                f.update(title=x['title'],creator_label=creator,creator_detail=x['creator'][0],raw_fields=segments,museum_slug='musee-beaux-arts-rouen')
                f['scheme']='rouen-object-page';f['source_id']=x['url'].rsplit('/',1)[-1]
                # Some newer pages place explicitly labelled facts in one line.
                details=detail.get_text(' ',strip=True)
                if 'Date :'in details or 'Technique :'in details:
                    date_text=details.split('Date :',1)[1].split('Technique :',1)[0].strip(' |')if'Date :'in details else None
                    medium_text=details.split('Technique :',1)[1].strip(' |')if'Technique :'in details else None
                    f.update(parse_date(date_text));f['medium']=re.split(r',\s*\d',medium_text)[0]if medium_text else None
                    f['dimensions']=medium_text[len(f['medium']):].strip(' ,')or None if medium_text else None
                else:
                    f.update(parse_date(segments[0]if segments else None));f['medium']=segments[1]if len(segments)>1 else None
                    f['dimensions']=next((z for z in segments[2:]if re.search(r'\d.*(?:cm|m\b)',z)),None)
                f['accession']=next((re.sub(r'^(?:N[°o] ?d[’\u0027]inventaire\s*:?|Inv(?:entaire)?\.?\s*:?)\s*','',z,flags=re.I)for z in segments if re.match(r'^(?:N[°o] ?d[’\u0027]inventaire|Inv(?:entaire)?\.?)\s',z,re.I)),None)
                inventory=re.search(r'\(inv\.\s*([^)]*)\)',x['creator'][0],re.I)
                if inventory:f['accession']=inventory[1]
                f['work_type']=kind(f['medium']);f['holding_note']='Official Rouen collection object page. No present-display claim.'
                if 'MNR'in x['creator'][0]or re.search(r'restitution|dépôt',details,re.I):held.append(dict(url=x['url'],reason='deposit_or_restitution_context_requires_review'));continue
            else:
                raw=gzip.decompress((ROOT/x['receipt']['body_path']).read_bytes());soup=BeautifulSoup(raw,'html.parser');fields={}
                for node in soup.select('.info-table-row'):
                    cells=node.find_all('p',recursive=False)
                    if len(cells)==2:fields[cells[0].get_text(' ',strip=True).rstrip(':').strip()]=cells[1].get_text(' ',strip=True)
                if not fields.get('Identifier')or not soup.h1:held.append(dict(url=x['url'],reason='cvar_object_layout_review'));continue
                f.update(title=soup.h1.get_text(' ',strip=True),creator_label=fields.get('Creator'),medium=fields.get('Medium'),dimensions=fields.get('Dimensions'),accession=fields['Identifier'],raw_fields=fields,museum_slug='cvar-nicosia',source_id=x['url'].rstrip('/').rsplit('/',1)[-1],scheme='cvar-object')
                f.update(parse_date(fields.get('Date')));f['work_type']=kind(fields.get('Medium')or fields.get('Object Type'))
                ims=[im for im in soup.select('img[src]')if fields['Identifier']in im.get('alt','')or fields['Identifier']in im['src']]
                if len(ims)==1:f['image_url']=urljoin(x['url'],ims[0]['src'])
                f['holding_note']='CVAR official object catalogue: '+fields.get('Collection','')+'; exact identifier '+fields['Identifier']+'. Not a current display assertion.'
                f['creator_credit']=fields.get('Rights Holder')or'Costas and Rita Severis Foundation';f['rights_label']=fields.get('Rights Statement')or'No reuse licence stated'
                if fields.get('Collection')!='Paintings Collection':held.append(dict(url=x['url'],reason='different_collection_requires_review'));continue
                if 'sketchbook'in f['title'].lower():held.append(dict(url=x['url'],reason='grouped_sketchbook_parent_components_kept_separate'));continue
            if f['last']and (f['last']>1970 if f['precision']!='before'else f['last']>1971):held.append(dict(url=x['url'],reason='after_artwork_creation_cutoff'));continue
            if f['work_type']is None:held.append(dict(url=x['url'],reason='photograph_or_surrogate_review'));continue
            records.append(f)
    for path in sorted((RUN/'objects/leventis').glob('*.json')):
        x=load(path);p=x['profile']
        for w in p['artworks']['all']:
            f=dict(source='leventis',source_url='https://cypriotartists.leventisgallery.org/en/'+p['slug']+'/works/'+w['slug'],
                source_id=str(w['id']),scheme='leventis-cypriot-artwork',title=html.unescape(w['title']),creator_label=p['title'],creator_detail=dict(birth=p.get('birthYear'),death=p.get('deathYear')),
                medium=plain(w['medium'])or None,dimensions=None,accession=w.get('number'),image_url=w.get('image'),receipt=x['receipt'],raw_fields=w,
                work_type=kind(w['medium']),museum_slug=None,creator_credit=p['title']+'; A. G. Leventis Gallery; '+plain(w.get('collection')),rights_label='Source reproduction; no independently obtained reuse licence')
            f.update(parse_date(w['date']));collection=plain(w.get('collection'))
            if w['category']=='Our Collections':f['museum_slug']='leventis-gallery'
            elif collection.startswith('State Gallery'):f['museum_slug']='state-gallery-cyprus'
            elif 'Bank of Cyprus Cultural Foundation'in collection:f['museum_slug']='boccf'
            f['holding_note']='Official Leventis object metadata: category '+w['category']+'; collection credit '+(collection or'not stated')+'. Exhibition-only connections do not establish holdings.'
            if f['last']and(f['last']>1970 if f['precision']!='before'else f['last']>1971):held.append(dict(url=f['source_url'],reason='after_artwork_creation_cutoff'));continue
            if re.search(r'photo of the original|destroyed|various studies',plain(w.get('body'))+' '+collection+' '+f['title'],re.I):held.append(dict(url=f['source_url'],reason='group_or_destroyed_original_review'));continue
            if not f['museum_slug']:held.append(dict(url=f['source_url'],reason='exhibition_or_private_collection_only'));continue
            records.append(f)
    supplement=RUN/'other-museum-local-leads.json.gz'
    if supplement.exists():
        spec=importlib.util.spec_from_file_location('joconde_fields',ROOT/'ops/museum-expansion-20261006.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        for lead in load(supplement):
            citations=[c for c in lead['row']['citations']if c['field_name']=='museum_expansion_primary_metadata']
            if len(citations)!=1:continue
            evidence=json.loads(citations[0]['evidence_note']);row=evidence['raw_source_record'];rc=dict(evidence['source_receipt'],body_path=evidence['body_path'])
            assert rc['retrieved_at'].startswith('2026-10-06')and sha(gzip.decompress((ROOT/rc['body_path']).read_bytes()))==rc['sha256']
            if re.search(r'copie|reproduction|original',str(row.get('Genese')or'')+' '+str(row.get('Periode_de_l_original_copie')or''),re.I):
                held.append(dict(url=citations[0]['source_url'],reason='copy_original_creation_date_needs_review'));continue
            parsed=[]
            parsers=[m.joconde_facts,m.joconde_period_facts,m.joconde_range_facts,m.joconde_circa_facts,m.joconde_before_facts]
            for fn in parsers:
                facts_,reason=fn(row)
                if facts_:parsed.append(facts_)
            if not parsed:held.append(dict(url=citations[0]['source_url'],reason='joconde_source_date_type_or_holding_review'));continue
            assert len(parsed)==1;v=parsed[0];w=lead['row']['artwork'];first=v.get('first',v.get('year'));last=v.get('last',v.get('year'));precision=v.get('date_precision','exact')
            assert(first,last,precision)==(w['creation_year_start'],w['creation_year_end'],w['date_precision'])
            records.append(dict(source='joconde',source_url=v['source_url'],receipt=rc,accession=v['accession'],dimensions=v['dimensions'],creator_label=v['creator_label'],creator_detail=v['creator_label'],image_url=None,title=v['title'],date_display=v['date_display'],first=first,last=last,precision=precision,medium=v['medium'],work_type=v['work_type'],source_id=row['Reference'],scheme='joconde-object',museum_slug=lead['museum_slug'],holding_note=v['holding_basis'],raw_fields=row))
    dest=RUN/'facts'/(sha(json.dumps(records,sort_keys=True,ensure_ascii=False).encode())+'.json');save(dest,dict(records=records,held=held));(RUN/'facts-pointer.txt').write_text(str(dest))
    print('FACTS',dict(collections.Counter(x['source']for x in records)),'held',dict(collections.Counter(x['reason']for x in held)),flush=True)
def creator_names(value):
    clean=re.sub(r'\s*\([^)]*\)','',value or'').strip();names={norm(clean)}
    if ','in clean:
        parts=clean.split(',',1);names.add(norm(parts[1]+' '+parts[0]))
    return names-{''}
def creator_key(value):return ' '.join(sorted(norm(re.sub(r'\([^)]*\)','',value or'')).split()))
def inventory_key(value):return re.sub(r'[^a-z0-9]','',norm(value or''))
def wikiart():
    rows=load(RUN/'production-artworks.json.gz');selected=[]
    for x in rows:
        w=x['artwork']
        urls=[c['source_url']for c in x['citations']if c.get('source_url')and('muma-lehavre.fr/fr/collections/'in c['source_url']or'mbarouen.fr/fr/oeuvres/'in c['source_url'])]
        if urls and not w['primary_media_id']and w['status']=='review'and w['creation_year_end']and w['creation_year_end']<=1970:selected.append(dict(record=x,museum_url=urls[0]))
    assert len(selected)<=140
    save(RUN/'wikiart-search-selection.json',selected)
    def one(item):
        w=item['record']['artwork'];path=RUN/'wikiart-searches'/(w['id']+'.json')
        if path.exists():return
        url='https://www.wikiart.org/fr/search/'+quote(w['title'],safe='')+'?json=2'
        try:raw,rc=capture(url,timeout=15)
        except requests.RequestException as e:
            save(RUN/'wikiart-search-errors'/(w['id']+'-'+str(time.time_ns())+'.json'),dict(artwork_id=w['id'],url=url,error=str(e)));return
        data=json.loads(raw)if rc['status']==200 else{};names={creator_key(a['display_name'])for a in item['record']['artists']}
        if w.get('unlinked_creator_label'):names.add(creator_key(w['unlinked_creator_label']))
        candidates=[p for p in data.get('Paintings')or[]if creator_key(html.unescape(p.get('artistName')or''))in names]
        save(path,dict(item=item,receipt=rc,candidates=candidates,all_results_count=len(data.get('Paintings')or[])))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:list(pool.map(one,selected))
    spec=importlib.util.spec_from_file_location('wikiart_page_parser',ROOT/'ops/research-production-wikiart-images-20261006.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
    ready=[];held=[]
    for path in sorted((RUN/'wikiart-searches').glob('*.json')):
        x=load(path);w=x['item']['record']['artwork'];matches=[]
        for c in x['candidates'][:12]:
            url=urljoin('https://www.wikiart.org',c['paintingUrl']).replace('/fr/','/en/',1)
            try:raw,rc=capture(url,timeout=20)
            except requests.RequestException:continue
            if rc['status']!=200:continue
            try:page=q.page_metadata(raw,rc)
            except ValueError:continue
            save(RUN/'wikiart-pages'/(sha(url.encode())+'.json'),page)
            loc=norm(page['fields'].get('Location'));source_muma='muma-lehavre'in x['item']['museum_url']
            museum_agrees=('havre'in loc and any(t in loc for t in ['malraux','modern','muma']))if source_muma else('rouen'in loc and any(t in loc for t in ['beaux','fine arts']))
            if not museum_agrees:continue
            d=page['date']
            if not d or w['creation_year_start']is None or max(d[0],w['creation_year_start'])>min(d[1],w['creation_year_end']):continue
            creator=html.unescape(page['metadata'].get('artistName')or'')
            if creator_key(creator)!=creator_key(html.unescape(c.get('artistName')or'')):continue
            matches.append(dict(candidate=c,page=page))
        if len(matches)==1:ready.append(dict(**x,match=matches[0]))
        else:held.append(dict(artwork_id=w['id'],title=w['title'],reason='no_unique_creator_date_museum_match',matches=len(matches),candidates=len(x['candidates'])))
    save(RUN/'wikiart-review.json',dict(ready=ready,held=held))
    print('WIKIART',len(selected),'selected existing museum objects;',len(ready),'corroborated page candidates;',len(held),'held',flush=True)
def plan(region):
    source_facts=load(Path((RUN/'facts-pointer.txt').read_text()));chosen=[f for f in source_facts['records']if(f['source']in ['cvar','leventis'])==(region=='cyprus')]
    names=set().union(*(creator_names(f['creator_label'])for f in chosen));names.discard('anonymous');names.discard('unknown')
    qualified=r'\b(?:attribue|attributed|atelier|workshop|ecole|school|entourage|after|apres|copy|copie|anonymous|anonyme|unknown|inconnu)\b'
    base=load(RUN/'production-artworks.json.gz');institutions={x['institution']['slug']:x['institution']for x in load(RUN/'production-audit.json')['institutions']}
    families={k:{institutions[s]['id']for s in v}for k,v in {'muma-le-havre':['muma-le-havre','joconde-m0720'],'musee-beaux-arts-rouen':['musee-beaux-arts-rouen','joconde-m0729']}.items()}
    ready=[];held=[];unchanged=[]
    with connect()as db:
        ar=db.execute("""SELECT to_jsonb(a) artist,
          coalesce((SELECT jsonb_agg(alias) FROM artist_aliases WHERE artist_id=a.id),'[]') aliases
          FROM artists a WHERE a.status<>'archived' AND (a.normalized_name=ANY(%s) OR a.id IN
          (SELECT artist_id FROM artist_aliases WHERE normalized_alias=ANY(%s)))""",(sorted(names),sorted(names))).fetchall()
        ars={x['artist']['id']:x for x in ar};artist_index=collections.defaultdict(set)
        for x in ar:
            for name in [x['artist']['display_name']]+x['aliases']:artist_index[creator_key(name)].add(x['artist']['id'])
        urls=set()
        for f in chosen:
            for u in [f['source_url'],f['source_url'].replace('https://','http://')]:urls.update([u.rstrip('/'),u.rstrip('/')+'/'])
        matches=db.execute("""SELECT entity_id::text id,source_url url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)
          UNION SELECT entity_id::text,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)""",(sorted(urls),sorted(urls))).fetchall()
        source_index=collections.defaultdict(set)
        for x in matches:source_index[x['url'].replace('http://','https://').rstrip('/')].add(x['id'])
        # Scope title checks by the selected titles and painter IDs, not full collection enrichment.
        title_keys=sorted({norm(f['title'])for f in chosen})
        painter_titles=db.execute("""SELECT a.id::text,a.title,a.alternate_title FROM artwork_artists aa
          JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived'""",(list(ars),)).fetchall()
        title_set=set(title_keys);alternate_ids={x['id']for x in painter_titles if norm(x.get('alternate_title'))in title_set}
        query="""SELECT a.id::text,a.title,a.alternate_title,a.unlinked_creator_label,a.current_institution_id::text,
          coalesce((SELECT array_agg(aa.artist_id::text) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'{}') creator_ids
          FROM artworks a WHERE a.status<>'archived' AND
          (a.normalized_title=ANY(%s) OR a.id=ANY(%s::uuid[]))"""
        params=(title_keys,sorted({x['id']for x in matches}|alternate_ids))
        explained=db.execute('EXPLAIN (FORMAT JSON) '+query,params).fetchone()
        save(RUN/'identity-scans'/(region+'-query-'+sha(json.dumps(explained,default=str).encode())+'.json'),explained)
        minimal=db.execute(query,params).fetchall();exact_ids={x['id']for x in matches};base_ids={x['artwork']['id']for x in base};ids=[]
        for x in minimal:
            if x['id']in exact_ids or x['id']in base_ids or x['id']in alternate_ids or set(x['creator_ids'])&set(ars)or creator_names(x['unlinked_creator_label'])&names:ids.append(x['id'])
        extra=[]
        for start in range(0,len(ids),250):
            extra+=db.execute("""SELECT to_jsonb(a) artwork,
              coalesce((SELECT jsonb_agg(to_jsonb(c)) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id),'[]') citations,
              coalesce((SELECT jsonb_agg(to_jsonb(l)) FROM artwork_location_assertions l WHERE l.artwork_id=a.id),'[]') locations,
              coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]') identifiers,
              coalesce((SELECT jsonb_agg(to_jsonb(ar)) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') artists
              FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY a.id""",(ids[start:start+250],)).fetchall()
        live={x['artwork']['id']:x for x in base+extra}
        snapshot=dict(artists=ar,artworks=extra)
        save(RUN/'identity-scans'/(region+'-'+sha(json.dumps(snapshot,default=str).encode())+'.json.gz'),snapshot)
        places=db.execute("SELECT to_jsonb(p) place FROM places p WHERE country_code='CY' AND name='Nicosia' ORDER BY id").fetchall()
        assert len(places)==1,'Nicosia place identity requires reconciliation'
        cvar=dict(id=uid('institution/cvar-nicosia'),slug='cvar-nicosia',name='Centre of Visual Arts and Research (CVAR)',kind='museum',place_id=places[0]['place']['id'],website_url='https://cvar.severis.org/en/',status='review',created_by=ACTOR,updated_by=ACTOR)
        exists=db.execute("SELECT to_jsonb(i) institution FROM institutions i WHERE id=%s OR slug=%s OR website_url ILIKE '%%severis.org%%'",(cvar['id'],cvar['slug'])).fetchall()
        assert len(exists)<=1
        if exists:cvar=exists[0]['institution']
        institutions['cvar-nicosia']=cvar
        for f in chosen:
            f=dict(f);pids=artist_index[creator_key(f['creator_label'])];pid=next(iter(pids))if len(pids)==1 and not re.search(qualified,norm(f['creator_label']))else None
            if pid:
                artist=ars[pid]['artist'];life=re.search(r'\((\d{4})\s*[-–]\s*(\d{4})\)',str(f.get('creator_detail')or f['creator_label']))
                if life and any(artist[k]and artist[k]!=int(life[i])for k,i in [('birth_year',1),('death_year',2)]):pid=None
            exact=set(source_index[f['source_url'].rstrip('/')]);museum=institutions[f['museum_slug']]
            candidate_by_inv=[]
            if f['accession']:
                for aid,x in live.items():
                    if inventory_key(x['artwork'].get('accession_number'))==inventory_key(f['accession']) and(x['artwork']['current_institution_id']==museum['id']or any(l['institution_id']==museum['id']for l in x['locations'])):candidate_by_inv.append(aid)
            if not exact and len(candidate_by_inv)==1:exact.update(candidate_by_inv)
            # Reconcile a unique physical object across the pre-existing museum
            # representations. Full creator, exact title, and a narrow date must
            # all agree; keep its existing institution ID and holding assertion.
            if not exact and f['source']in ['muma','rouen']and f['first']and f['last']-f['first']<=5 and not re.search(qualified,norm(f['creator_label'])):
                concordant=[]
                for aid,x in live.items():
                    w=x['artwork'];creators=[a['display_name']for a in x['artists']]+[w.get('unlinked_creator_label')or'']
                    if w['current_institution_id']not in families[f['museum_slug']]:continue
                    if norm(f['title'])not in {norm(w['title']),norm(w.get('alternate_title'))}:continue
                    if creator_key(f['creator_label'])not in {creator_key(name)for name in creators}:continue
                    if w['work_type']!='unknown'and f['work_type']!='unknown'and w['work_type']!=f['work_type']:continue
                    d=dict(first=w['creation_year_start'],last=w['creation_year_end'])
                    if d['first']is None or d['last']is None:d=parse_date(w['date_display'].removeprefix('Unverified date: '))
                    if d['first']is None or d['last']is None or d['last']-d['first']>5:continue
                    if max(d['first'],f['first'])>min(d['last'],f['last']):continue
                    concordant.append(aid)
                if len(concordant)==1:
                    exact.update(concordant);current_institution=live[concordant[0]]['artwork']['current_institution_id']
                    museum=next(i for i in institutions.values()if i['id']==current_institution)
                    f['museum_slug']=museum['slug'];f['cross_source_identity']='Unique full creator, exact title, narrow concordant creation date, and same documented MuMa/Rouen museum identity. Existing institution representation retained.'
            if len(exact)>1:held.append(dict(facts=f,reason='multiple_catalogue_records_for_source',ids=sorted(exact)));continue
            before=live[next(iter(exact))]if exact else None
            if before:
                w=before['artwork']
                if w['status']!='review' or w['published_at']:held.append(dict(facts=f,reason='existing_record_not_unpublished_review'));continue
                known={a['id']for a in before['artists']}
                if pid and known and pid not in known:held.append(dict(facts=f,reason='creator_link_conflict',artwork_id=w['id']));continue
                if w['current_institution_id']not in [None,museum['id']]:held.append(dict(facts=f,reason='existing_holding_conflict',artwork_id=w['id']));continue
                aid=w['id'];action='enrich'
            else:
                possible=[]
                for aid,x in live.items():
                    w=x['artwork'];titles={norm(w.get('title')),norm(w.get('alternate_title'))}
                    if norm(f['title'])not in titles:continue
                    known={a['id']for a in x['artists']}
                    creator_same=pid in known if pid else bool(creator_key(f['creator_label'])and creator_key(f['creator_label'])==creator_key(w.get('unlinked_creator_label')))
                    relevant_museums=families.get(f['museum_slug'],{museum['id']})
                    if creator_same or w['current_institution_id']in relevant_museums:possible.append(w['id'])
                if possible:held.append(dict(facts=f,reason='title_creator_or_museum_collision_requires_object_reconciliation',ids=possible));continue
                variants=[]
                if f['source']in ['muma','rouen']:
                    target_title=norm(f['title']);creator_tokens=set(creator_key(f['creator_label']).split())-{'de','di','van','von','le','la','d','da'}
                    for existing_id,x in live.items():
                        w=x['artwork']
                        if w['current_institution_id']not in families[f['museum_slug']]:continue
                        same_creator=bool(pid and pid in {a['id']for a in x['artists']})
                        for label in [w.get('unlinked_creator_label')or'']+[a['display_name']for a in x['artists']]:
                            tokens=set(creator_key(label).split())-{'de','di','van','von','le','la','d','da'}
                            if len(tokens&creator_tokens)>=2 and(min(len(tokens),len(creator_tokens))==len(tokens&creator_tokens)):same_creator=True
                        if not same_creator:continue
                        old_title=norm(w['title']);similar=difflib.SequenceMatcher(None,target_title,old_title).ratio()
                        contained=min(len(target_title),len(old_title))>9 and(target_title in old_title or old_title in target_title)
                        if similar>=.70 or contained:variants.append(dict(artwork_id=existing_id,title=w['title'],similarity=round(similar,4)))
                if variants:held.append(dict(facts=f,reason='same_museum_creator_title_variant_requires_reconciliation',candidates=variants));continue
                if f['work_type']=='unknown' or not f['title']:held.append(dict(facts=f,reason='object_type_or_title_review'));continue
                if re.search(qualified,norm(f['creator_label']))and f['precision']=='unknown':held.append(dict(facts=f,reason='unknown_creator_and_creation_date'));continue
                aid=uid('artwork/'+f['scheme']+'/'+f['source_id']);action='create'
            changes=[]
            if not before:changes=['new_artwork','documented_holding']+(['painter_link']if pid else[])
            else:
                if not before['artists']and pid:changes.append('painter_link')
                if not any(l['claim_type']=='holding'and l['institution_id']==museum['id']and l['review_state']=='accepted'and not l['superseded_by']for l in before['locations']):changes.append('documented_holding')
                if w['date_precision']=='unknown'and f['precision']!='unknown':changes.append('creation_date')
                if w['work_type']=='unknown'and f['work_type']!='unknown':changes.append('work_type')
                if not w['medium_text']and f['medium']:changes.append('medium')
                if not w['dimensions_text']and f['dimensions']:changes.append('dimensions')
                if not w['accession_number']and f['accession']:changes.append('accession')
            # Existing dates, images and attribution links are never overwritten.
            f['artwork_id']=aid;f['artist_id']=pid;f['museum']=museum;f['action']=action;f['before']=before;f['changes']=changes
            if changes:ready.append(f)
            else:unchanged.append(f)
        value=dict(at=now(),region=region,records=ready,held=held,unchanged=unchanged,artists=ar,new_cvar_institution=None if exists or not any(f['museum_slug']=='cvar-nicosia'for f in ready)else cvar,place_evidence=places)
    path=RUN/'plans'/(region+'-'+sha(json.dumps(value,sort_keys=True,default=str).encode())+'.json');save(path,value);(RUN/(region+'-plan-pointer.txt')).write_text(str(path))
    save(BACKUP/(path.stem+'-plan-and-preimages.json.gz'),value)
    print('PLAN',region,'create',sum(f['action']=='create'for f in ready),'enrich',sum(f['action']=='enrich'for f in ready),'unchanged',len(unchanged),'holds',dict(collections.Counter(x['reason']for x in held)),flush=True)
def pinned(region):
    path=Path((RUN/(region+'-plan-pointer.txt')).read_text());return load(path),sha(path.read_bytes())
def insert(db,table,row):
    db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,row)),sql.SQL(',').join(sql.Placeholder()for _ in row)),list(row.values()))
def audit_entry(db,entity_type,entity_id,before,after,action):
    insert(db,'audit_log',dict(actor_user_id=ACTOR,action=action,entity_type=entity_type,entity_id=entity_id,request_id=RUN.name,before_json=Jsonb(before)if before is not None else None,after_json=Jsonb(after)))
def backup_status():
    raw=subprocess.check_output(['gcloud','sql','backups','describe','1791309359006','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True)
    data=json.loads(raw);assert data['status']=='SUCCESSFUL','Backup still running'
    save(BACKUP/'cloud-backup.json',data);save(RUN/'cloud-backup.json',data)
    return data
def prepare(region):
    p,_=pinned(region);selected=[]
    if region=='cyprus':
        for f in p['records']+p['unchanged']:
            if f['image_url']and f['last']and f['last']<=1955 and not(f['before']and f['before']['artwork']['primary_media_id']):
                selected.append(dict(artwork_id=f['artwork_id'],title=f['title'],creator=f['creator_label'],image_url=f['image_url'],source_url=f['source_url'],source_id=f['source_id'],rights_status='restricted',rights_label=f['rights_label'],creator_credit=f['creator_credit'],receipt=f['receipt'],facts=f,policy='User-approved Cyprus museum/artist collection workflow (20 September 2026), works ending by 1955; actual rights retained, no independent licence asserted.'))
    else:
        for x in load(RUN/'wikiart-review.json')['ready']:
            w=x['item']['record']['artwork'];page=x['match']['page']
            selected.append(dict(artwork_id=w['id'],title=w['title'],creator=html.unescape(page['metadata']['artistName']),image_url=page['image_url'],source_url=page['url'],source_id=page['metadata']['_id'],rights_status='public_domain'if page['rights_status']=='public_domain'else'restricted',rights_label=page['rights_label']or'No reuse licence stated',creator_credit=html.unescape(page['metadata']['artistName'])+'; WikiArt',receipt=page['receipt'],facts=x,policy='User-approved WikiArt collection and public-display workflow, 6 October 2026; source rights label preserved.'))
    save(RUN/(region+'-image-selection.json'),selected)
    spec=importlib.util.spec_from_file_location('compression',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
    originals=Path.home()/'Library/Application Support/Artline/source-images'/RUN.name;originals.mkdir(parents=True,exist_ok=True)
    def one(x):
        path=RUN/'prepared'/region/(x['artwork_id']+'.json')
        if path.exists():return 'preserved'
        original=originals/(sha(x['image_url'].encode())+'.body');receipt=RUN/'image-downloads'/(sha(x['image_url'].encode())+'.json')
        try:
            if receipt.exists():rc=load(receipt);raw=original.read_bytes();assert sha(raw)==rc['sha256']
            else:
                host=urlparse(x['image_url']).netloc
                with LOCKS[host]:
                    time.sleep(max(0,LAST.get(host,0)+1.1-time.monotonic()));LAST[host]=time.monotonic()
                    with requests.get(x['image_url'],headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected catalogue image)'},timeout=(15,45),stream=True)as resp:
                        resp.raise_for_status();assert resp.headers.get('Content-Type','').startswith('image/');raw=b''
                        for chunk in resp.iter_content(65536):raw+=chunk;assert len(raw)<=20_000_000
                        rc=dict(url=x['image_url'],final_url=resp.url,status=resp.status_code,sha256=sha(raw),bytes=len(raw),retrieved_at=now(),path=str(original))
                original.write_bytes(raw);save(receipt,rc)
            content,width,height,quality=core.compress(raw);assert min(width,height)>=80
            digest=sha(content);image_path='/assets/artworks/imported/'+RUN.name+'/'+x['artwork_id']+'-'+digest[:16]+'.jpg';dest=ROOT/'apps/web/public'/image_path.lstrip('/')
            dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():assert dest.read_bytes()==content
            else:dest.write_bytes(content)
            im=dict(**x,media_id=uid('media/'+digest),path=image_path,sha256=digest,bytes=len(content),width=width,height=height,quality=quality,download=rc,visual_path=str(dest))
            save(path,im);return 'prepared'
        except Exception as e:
            save(RUN/'image-errors'/(x['artwork_id']+'-'+str(time.time_ns())+'.json'),dict(artwork_id=x['artwork_id'],source_url=x['image_url'],error=type(e).__name__+': '+str(e)));return 'held'
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:counts=collections.Counter(pool.map(one,selected))
    print('IMAGES',region,len(selected),dict(counts),flush=True)
    from PIL import Image,ImageOps,ImageDraw
    records=[load(p)for p in sorted((RUN/'prepared'/region).glob('*.json'))];index=[];folder=originals/'contact-sheets'/region;folder.mkdir(parents=True,exist_ok=True)
    for start in range(0,len(records),20):
        sheet=Image.new('RGB',(1500,1120),'#eee9df');draw=ImageDraw.Draw(sheet)
        for n,im in enumerate(records[start:start+20]):
            with Image.open(im['visual_path'])as src:thumb=ImageOps.contain(src.convert('RGB'),(294,215))
            left=n%5*300;top=n//5*280;sheet.paste(thumb,(left+(300-thumb.width)//2,top))
            draw.multiline_text((left+4,top+219),f"{start+n+1} {im['source_id']}\n{im['title'][:42]}\n{im['creator'][:40]}",fill='black',spacing=3)
            index.append(dict(number=start+n+1,sheet=start//20+1,artwork_id=im['artwork_id'],sha256=im['sha256'],title=im['title'],creator=im['creator']))
        sheet.save(folder/f'{start//20+1:03}.jpg',quality=90)
    save(RUN/(region+'-contact-index.json'),index);print('CONTACT SHEETS',folder,'images',len(records),flush=True)
def apply(region):
    p,digest=pinned(region);assert not(RUN/(region+'-applied.json')).exists(),'Already applied'
    backup_status();records=p['records'];ids=[f['artwork_id']for f in records];sid=uid('source')
    assert len(set(ids))==len(ids),'Duplicate target identity in plan'
    for f in records:
        raw=gzip.decompress((ROOT/f['receipt']['body_path']).read_bytes());assert sha(raw)==f['receipt']['sha256']
        assert f['precision']!='unknown' or f['first']is None and f['last']is None
    with connect(readonly=False)as db,db.transaction():
        assert db.execute('SELECT current_database() name').fetchone()['name']=='artline'
        db.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',(RUN.name,))
        before={x['record']['id']:x['record']for x in db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,))}
        for f in records:
            assert before.get(f['artwork_id'])==(f['before']['artwork']if f['before']else None),'Artwork drift: '+f['artwork_id']
        artists={x['artist']['id']:x['artist']for x in p['artists']};used=sorted({f['artist_id']for f in records if f['artist_id']})
        for x in db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(used,)):
            assert x['record']==artists[x['record']['id']],'Painter changed'
        # Exact source identity is rechecked under the import lock before writes.
        urls=[f['source_url']for f in records]
        concurrent=db.execute("SELECT entity_id::text id,source_url url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) UNION SELECT entity_id::text,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(urls,urls)).fetchall()
        expected={f['source_url']:f['artwork_id']for f in records};assert all(expected[x['url']]==x['id']for x in concurrent),'Concurrent source identity conflict'
        bp=BACKUP/(region+'-transaction-preimages.json.gz')
        if bp.exists():
            saved=load(bp);assert saved['plan_sha256']==digest and saved['artworks']==before and saved['plan']==p,'Existing backup differs'
        else:save(bp,dict(at=now(),plan_sha256=digest,artworks=before,plan=p))
        source=db.execute('SELECT to_jsonb(s) record FROM sources s WHERE id=%s OR slug=%s',(sid,RUN.name)).fetchall()
        if not source:insert(db,'sources',dict(id=sid,slug=RUN.name,name='Le Havre, Rouen and Cyprus: verified museum records, 6 October 2026',source_type='collection_page',base_url='https://cvar.severis.org/en/'))
        else:assert len(source)==1 and source[0]['record']['id']==sid
        if p['new_cvar_institution']:
            c=p['new_cvar_institution'];row={k:c[k]for k in ['id','slug','name','kind','place_id','website_url','status']};row['normalized_name']=norm(c['name'])
            insert(db,'institutions',row);audit_entry(db,'institution',c['id'],None,row,'insert')
            rc=load(RUN/'discovery/cvar.json')['receipt']
            insert(db,'citations',dict(entity_type='institution',entity_id=c['id'],field_name='museum_identity',source_id=sid,source_url='https://cvar.severis.org/en/explore/collections-archives/paintings/',evidence_note=json.dumps(dict(receipt=rc,identity='Official CVAR collection catalogue and Nicosia contact address; institution remains review.')),retrieved_at=rc['retrieved_at'],created_by=ACTOR))
        for f in records:
            aid=f['artwork_id'];change=f['changes'];pid=f['artist_id'];w=f['before']['artwork']if f['before']else None
            if f['action']=='create':
                row=dict(id=aid,slug=RUN.name+'-'+f['source']+'-'+f['source_id'],title=f['title'],normalized_title=norm(f['title']),date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['precision'],work_type=f['work_type'],medium_text=f['medium'],dimensions_text=f['dimensions'],accession_number=f['accession'],status='review',research_candidate=True,unlinked_creator_label=None if pid else f['creator_label'],created_by=ACTOR,updated_by=ACTOR)
                insert(db,'artworks',row)
            else:
                update={}
                if 'creation_date'in change:update.update(date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['precision'])
                for kind_,field in [('work_type','work_type'),('medium','medium_text'),('dimensions','dimensions_text'),('accession','accession_number')]:
                    if kind_ in change:update[field]=f[kind_]
                if 'painter_link'in change:update['unlinked_creator_label']=None
                update.update(revision=w['revision']+1,updated_by=ACTOR)
                db.execute(sql.SQL('UPDATE artworks SET {},updated_at=now() WHERE id=%s').format(sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k))for k in update)),list(update.values())+[aid])
            if 'painter_link'in change:
                link=dict(artwork_id=aid,artist_id=pid,attribution_role='primary',representative_order=1,attribution_note='Exact primary museum creator: '+f['creator_label']+'. Original source label and date preserved in citation. '+f['source_url'])
                assert not db.execute('SELECT 1 FROM artwork_artists WHERE artwork_id=%s',(aid,)).fetchone();insert(db,'artwork_artists',link);audit_entry(db,'artwork_creator_link',aid,None,link,'insert')
            external=db.execute("SELECT entity_id::text id FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(f['scheme'],f['source_id'])).fetchall()
            if external:assert len(external)==1 and external[0]['id']==aid
            else:
                row=dict(id=uid('identifier/'+f['scheme']+'/'+f['source_id']),entity_type='artwork',entity_id=aid,scheme=f['scheme'],external_id=f['source_id'],canonical_url=f['source_url'],source_id=sid,retrieved_at=f['receipt']['retrieved_at'])
                insert(db,'external_identifiers',row);audit_entry(db,'external_identifier',row['id'],None,row,'insert')
            evidence={k:v for k,v in f.items()if k not in ['before','museum']};evidence['plan_sha256']=digest;evidence['preservation']='Existing nonempty metadata, images and editorial state preserved. Holding is independently evidenced; current display is not asserted.'
            insert(db,'citations',dict(id=uid('citation/'+region+'/'+aid),entity_type='artwork',entity_id=aid,field_name='museum_data_reconciliation_20261006',source_id=sid,source_record_id=f['source_id'],source_url=f['source_url'],evidence_note=json.dumps(evidence,ensure_ascii=False),retrieved_at=f['receipt']['retrieved_at'],created_by=ACTOR))
            if 'documented_holding'in change:
                assert not db.execute("SELECT 1 FROM artwork_location_assertions WHERE artwork_id=%s AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL",(aid,)).fetchone()
                insert(db,'artwork_location_assertions',dict(id=uid('holding/'+region+'/'+aid),artwork_id=aid,claim_type='holding',institution_id=f['museum']['id'],context='collection',source_id=sid,source_url=f['source_url'],evidence_note=f['holding_note']+' Capture SHA-256 '+f['receipt']['sha256']+'.',checked_at=f['receipt']['retrieved_at'],review_state='accepted'))
        after=db.execute('SELECT to_jsonb(a) artwork,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,artline_has_selection_evidence(id) selected FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall()
        assert len(after)==len(records)
        target={f['artwork_id']:f for f in records}
        for x in after:
            w=x['artwork'];f=target[w['id']];assert w['status']=='review'and w['published_at']is None and w['current_institution_id']==f['museum']['id']and x['selected']
            if f['before']:assert w['primary_media_id']==f['before']['artwork']['primary_media_id']
            else:assert x['scope']=='eligible' or f['precision']=='unknown'
        save(BACKUP/(region+'-transaction-after.json.gz'),after)
    result=dict(at=now(),plan_sha256=digest,target='production',new_artworks=sum(f['action']=='create'for f in records),enriched=sum(f['action']=='enrich'for f in records),painter_links=sum('painter_link'in f['changes']for f in records),holdings=sum('documented_holding'in f['changes']for f in records),new_institutions=bool(p['new_cvar_institution']),artwork_ids=ids,after=after)
    save(RUN/(region+'-applied.json'),result);print('APPLIED',region,{k:v for k,v in result.items()if k not in ['artwork_ids','after']},flush=True)
def image_plan(region):
    review=load(RUN/(region+'-visual-review.json'));assert review['contact_index_sha256']==sha((RUN/(region+'-contact-index.json')).read_bytes())
    selected=[];held=[]
    for x in review['approved']:
        im=load(RUN/'prepared'/region/(x['artwork_id']+'.json'));raw=Path(im['visual_path']).read_bytes()
        assert im['sha256']==x['sha256']==sha(raw)and len(raw)==im['bytes']<=100000
        selected.append(im)
    with connect()as db:
        rows=db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE id=ANY(%s::uuid[])',([x['artwork_id']for x in selected],)).fetchall();before={x['artwork']['id']:x['artwork']for x in rows}
        duplicate_pixels={x['checksum_sha256']:x['id']for x in db.execute('SELECT id::text,checksum_sha256 FROM media_assets WHERE checksum_sha256=ANY(%s)',([im['sha256']for im in selected],))}
    ready=[];counts=collections.Counter(x['sha256']for x in selected)
    for im in selected:
        w=before.get(im['artwork_id']);reason=None
        if not w:reason='artwork_not_delivered'
        elif w['primary_media_id']:reason='existing_image_preserved'
        elif w['status']!='review' or w['published_at']:reason='not_unpublished_review'
        elif counts[im['sha256']]>1 or im['sha256']in duplicate_pixels:reason='duplicate_pixels_require_reconciliation'
        if reason:held.append(dict(artwork_id=im['artwork_id'],reason=reason));continue
        ready.append(dict(image=im,before=w))
    result=dict(at=now(),region=region,records=ready,held=held,visual_review=review)
    save(RUN/(region+'-image-plan.json.gz'),result);save(BACKUP/(region+'-image-preimages.json.gz'),result)
    print('IMAGE PLAN',region,len(ready),'ready',len(held),'held',flush=True)
def upload(region):
    p=load(RUN/(region+'-image-plan.json.gz'));token=subprocess.check_output(['gcloud','auth','print-access-token','--account=vadim@alingva.com'],text=True).strip();session=requests.Session();session.headers['Authorization']='Bearer '+token
    checks=[];bucket='artline-508319-images'
    for item in p['records']:
        im=item['image'];data=Path(im['visual_path']).read_bytes();assert sha(data)==im['sha256']and len(data)<=100000
        dest=RUN/'storage'/region/(im['artwork_id']+'.json')
        if dest.exists():checks.append(load(dest));continue
        name=im['path'].lstrip('/');url='https://storage.googleapis.com/storage/v1/b/'+bucket+'/o/'+quote(name,safe='')
        response=session.get(url,timeout=(15,30));created=False
        if response.status_code==404:
            response=session.post('https://storage.googleapis.com/upload/storage/v1/b/'+bucket+'/o',params=dict(uploadType='media',name=name,ifGenerationMatch=0),data=data,headers={'Content-Type':'image/jpeg'},timeout=(15,45));created=True
        response.raise_for_status();obj=response.json();assert int(obj['size'])==len(data)and obj['md5Hash']==base64.b64encode(hashlib.md5(data).digest()).decode()
        check=dict(artwork_id=im['artwork_id'],path=im['path'],sha256=im['sha256'],generation=obj['generation'],created=created);save(dest,check);checks.append(check)
    save(RUN/(region+'-storage.json'),dict(at=now(),checks=checks));print('UPLOADED',region,len(checks),'verified objects',flush=True)
def attach(region):
    p=load(RUN/(region+'-image-plan.json.gz'));digest=sha((RUN/(region+'-image-plan.json.gz')).read_bytes());storage=load(RUN/(region+'-storage.json'));assert len(storage['checks'])==len(p['records']);sid=uid('source')
    after=[]
    with connect(readonly=False)as db:
        for start in range(0,len(p['records']),20):
            path=RUN/'image-applied'/region/(str(start//20+1).zfill(3)+'.json')
            if path.exists():after+=load(path)['after'];continue
            batch=p['records'][start:start+20];current=[]
            with db.transaction():
                for item in batch:
                    im=item['image'];aid=im['artwork_id'];w=db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE id=%s FOR UPDATE',(aid,)).fetchone()['artwork'];assert w==item['before'],'Artwork changed before image attachment: '+aid
                    row=dict(id=im['media_id'],storage_kind='local',storage_path=im['path'],source_page_url=im['source_url'],provider_name='CVAR'if region=='cyprus'else'WikiArt',mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=im['title']+' — '+im['creator'],rights_status=im['rights_status'],license_label=im['rights_label'],license_url=im['source_url'],creator_credit=im['creator_credit'],attribution_text=im['creator_credit'],retrieved_at=im['download']['retrieved_at'],verified_at=None,verified_by=None)
                    insert(db,'media_assets',row);audit_entry(db,'media_asset',im['media_id'],None,row,'insert')
                    insert(db,'media_rights_evidence',dict(media_id=im['media_id'],source_id=sid,source_record_id=im['source_id'],source_checksum=im['receipt']['sha256'],source_image_url=im['image_url'],policy_url=im['source_url'],rights_basis=im['policy'],adapter_version=RUN.name,checked_at=im['receipt']['retrieved_at'],evidence_json=Jsonb(im)))
                    link=dict(artwork_id=aid,media_id=im['media_id'],sort_order=0,view_label='Full supplied composition; original source marks retained');insert(db,'artwork_media',link);audit_entry(db,'artwork_media',aid,None,link,'insert')
                    db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_by=%s,updated_at=now() WHERE id=%s AND primary_media_id IS NULL',(im['media_id'],ACTOR,aid))
                    insert(db,'citations',dict(id=uid('image-citation/'+aid),entity_type='artwork',entity_id=aid,field_name='verified_image_identity_20261006',source_id=sid,source_record_id=im['source_id'],source_url=im['source_url'],evidence_note=json.dumps(dict(plan_sha256=digest,source_receipt=im['receipt'],download=im['download'],visual_review=p['visual_review'],identity='Exact museum object source or reviewed WikiArt creator/date/museum correspondence.'),ensure_ascii=False),retrieved_at=im['receipt']['retrieved_at'],created_by=ACTOR))
                    result=db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE id=%s',(aid,)).fetchone()['artwork']
                    ignored={'primary_media_id','revision','updated_at','updated_by'};assert all(result[k]==w[k]for k in w if k not in ignored)
                    current.append(result)
            save(path,dict(at=now(),plan_sha256=digest,after=current));after+=current;print('ATTACHED',region,len(after),'/',len(p['records']),flush=True)
    save(RUN/(region+'-images-applied.json'),dict(at=now(),plan_sha256=digest,images=len(after),after=after))
def verify(region):
    p,digest=pinned(region);applied=load(RUN/(region+'-applied.json'));assert applied['plan_sha256']==digest
    expected={x['artwork']['id']:x['artwork']for x in applied['after']};images={};image_applied=RUN/(region+'-images-applied.json')
    if image_applied.exists():
        expected.update({x['id']:x for x in load(image_applied)['after']})
        images={x['image']['artwork_id']:x['image']for x in load(RUN/(region+'-image-plan.json.gz'))['records']}
    ids=list(expected);records={f['artwork_id']:f for f in p['records']+p['unchanged']};metadata_ids={f['artwork_id']for f in p['records']}
    with connect()as db:
        rows=db.execute("""SELECT to_jsonb(a) artwork,artline_has_selection_evidence(a.id) selected,
          coalesce((SELECT jsonb_agg(to_jsonb(l)) FROM artwork_location_assertions l WHERE l.artwork_id=a.id),'[]') locations,
          coalesce((SELECT jsonb_agg(to_jsonb(c)) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id),'[]') citations,
          coalesce((SELECT jsonb_agg(to_jsonb(aa)) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') creators
          FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id""",(ids,)).fetchall()
        assert len(rows)==len(ids)
        audits=db.execute("SELECT entity_id::text,after_json FROM audit_log WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND created_at>=%s",(ids,p['at'])).fetchall()
        for x in rows:
            w=x['artwork'];aid=w['id'];f=records[aid];assert w==expected[aid],('current_artwork_drift',aid)
            assert w['status']=='review'and w['published_at']is None and x['selected']and w['current_institution_id']==f['museum']['id']
            assert any(a['entity_id']==aid and a['after_json']==w for a in audits)
            if aid in metadata_ids:
                citation=next(c for c in x['citations']if c['id']==uid('citation/'+region+'/'+aid));assert json.loads(citation['evidence_note'])['plan_sha256']==digest
            if f['artist_id']:assert any(a['artist_id']==f['artist_id']and a['attribution_role']=='primary'for a in x['creators'])
            if f['before']:
                assert all(c in x['citations']for c in f['before']['citations'])
                assert all(l in x['locations']for l in f['before']['locations'])
            assert sum(l['claim_type']=='display'for l in x['locations'])==sum(l['claim_type']=='display'for l in(f['before']['locations']if f['before']else[]))
        if images:
            media=db.execute('SELECT to_jsonb(m) media,to_jsonb(e) evidence FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=ANY(%s::uuid[])',([im['media_id']for im in images.values()],)).fetchall()
            assert len(media)==len(images)
            byid={im['media_id']:im for im in images.values()}
            for row in media:
                im=byid[row['media']['id']];m=row['media'];assert m['checksum_sha256']==im['sha256']and m['byte_size']==im['bytes']<=100000 and m['rights_status']==im['rights_status']
                assert row['evidence']['evidence_json']==im and m['source_page_url']==im['source_url']
        museum_ids=sorted({f['museum']['id']for f in p['records']})
        totals=db.execute("SELECT i.id::text,i.slug,i.name,count(a.id) artworks,count(a.primary_media_id) illustrated,count(a.id)FILTER(WHERE a.status='review') in_review FROM institutions i LEFT JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived' WHERE i.id=ANY(%s::uuid[]) GROUP BY i.id ORDER BY i.name",(museum_ids,)).fetchall()
    # Live reads cover each museum plus selected beginning/middle/end objects.
    samples={}
    for f in p['records']:samples.setdefault(f['museum_slug'],f)
    sample_rows=list(samples.values())+[p['records'][n]for n in range(0,len(p['records']),max(1,len(p['records'])//6))]
    sample_rows=list({f['artwork_id']:f for f in sample_rows}.values());checks=[]
    def check(f):
        url='https://artlines.org/api/backend/v1/museums/'+f['museum_slug']+'/works/'+f['artwork_id']
        for attempt in range(3):
            response=requests.get(url,timeout=(15,45))
            if response.status_code in [500,502,503,504]and attempt<2:time.sleep(2);continue
            response.raise_for_status();break
        body=response.json();assert body['id']==f['artwork_id']and body['status']=='review'
        if f['artwork_id']in images:assert body['media_url']==images[f['artwork_id']]['path']
        return dict(url=url,status=response.status_code,artwork_id=f['artwork_id'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:checks=list(pool.map(check,sample_rows))
    image_checks=[]
    def check_image(im):
        response=requests.get('https://artlines.org'+im['path'],timeout=(15,45));response.raise_for_status();assert sha(response.content)==im['sha256']
        return dict(artwork_id=im['artwork_id'],path=im['path'],status=response.status_code,sha256=sha(response.content))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:image_checks=list(pool.map(check_image,images.values()))
    summary=dict(at=now(),target='production',region=region,new_artworks=applied['new_artworks'],enriched=applied['enriched'],painter_links=applied['painter_links'],holdings=applied['holdings'],images=len(images),artwork_audits_verified=len(rows),api_checks=checks,image_checks=image_checks,museum_totals=totals,all_in_review=True,no_new_current_display_claims=True,errors=[])
    save(RUN/(region+'-verification.json'),summary);print('VERIFIED',region,applied['new_artworks'],'new,',applied['enriched'],'enriched,',len(images),'images;',len(checks),'API checks',flush=True)
def institutions():
    assert not(RUN/'institution-geography-applied.json').exists()
    sources={'leventis-gallery':('https://leventisgallery.org/collections/paris-collection/','5 Anastasios G. Leventis Street, 1095 Nicosia, Cyprus'),
      'state-gallery-cyprus':('https://www.visitcyprus.com/discover-cyprus/culture/museums-galleries/state-gallery-of-contemporary-art/','Lefkosia (Nicosia)')}
    evidence={}
    for slug,(url,anchor)in sources.items():
        raw,rc=capture(url);text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True);assert rc['status']==200 and anchor in text;evidence[slug]=dict(url=url,receipt=rc,location_statement=anchor)
    with connect()as db:
        rows=db.execute('SELECT to_jsonb(i) institution FROM institutions i WHERE slug=ANY(%s) ORDER BY id',(list(sources),)).fetchall()
        place=db.execute("SELECT id::text FROM places WHERE country_code='CY' AND name='Nicosia'").fetchall();assert len(place)==1 and len(rows)==2
    plan=dict(at=now(),before=rows,evidence=evidence,place_id=place[0]['id']);save(RUN/'institution-geography-plan.json',plan);save(BACKUP/'institution-geography-preimages.json',plan)
    after=[]
    with connect(readonly=False)as db,db.transaction():
        for x in rows:
            old=x['institution'];current=db.execute('SELECT to_jsonb(i) institution FROM institutions i WHERE id=%s FOR UPDATE',(old['id'],)).fetchone()['institution'];assert current==old and old['place_id']is None
            db.execute('UPDATE institutions SET place_id=%s,updated_at=now() WHERE id=%s',(plan['place_id'],old['id']))
            new=db.execute('SELECT to_jsonb(i) institution FROM institutions i WHERE id=%s',(old['id'],)).fetchone()['institution'];audit_entry(db,'institution',old['id'],old,new,'update')
            ev=evidence[old['slug']]
            insert(db,'citations',dict(entity_type='institution',entity_id=old['id'],field_name='verified_museum_city',source_id=uid('source'),source_url=ev['url'],evidence_note=json.dumps(ev),retrieved_at=ev['receipt']['retrieved_at'],created_by=ACTOR));after.append(new)
    save(RUN/'institution-geography-applied.json',dict(at=now(),after=after));print('Verified and filled Nicosia geography for 2 existing museum records',flush=True)
def audit():
    for target in ['local','production']:
        if (RUN/(target+'-audit.json')).exists():continue
        with connect(target)as db:
            institutions=db.execute("""SELECT to_jsonb(i) institution,p.name city,p.country_code,
              (SELECT count(*) FROM artworks a WHERE a.current_institution_id=i.id AND a.status<>'archived') works,
              (SELECT count(*) FROM artworks a WHERE a.current_institution_id=i.id AND a.primary_media_id IS NOT NULL AND a.status<>'archived') images
              FROM institutions i LEFT JOIN places p ON p.id=i.place_id
              WHERE p.country_code='CY' OR p.name ILIKE '%%rouen%%' OR p.name ILIKE '%%havre%%'
              OR i.name ~* 'rouen|havre|cyprus|cypriot|leventis|kykkos|severis|makarios'
              ORDER BY i.name""").fetchall()
            ids=[x['institution']['id']for x in institutions];rows=[];last='00000000-0000-0000-0000-000000000000'
            query="""WITH ids AS MATERIALIZED(SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[])
              UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) AND superseded_by IS NULL),
              page AS MATERIALIZED(SELECT id FROM ids WHERE id>%s::uuid ORDER BY id LIMIT 250)
              SELECT to_jsonb(a) artwork,
              coalesce((SELECT jsonb_agg(to_jsonb(c)) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id),'[]') citations,
              coalesce((SELECT jsonb_agg(to_jsonb(l)) FROM artwork_location_assertions l WHERE l.artwork_id=a.id),'[]') locations,
              coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]') identifiers,
              coalesce((SELECT jsonb_agg(to_jsonb(ar)) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') artists
              FROM page JOIN artworks a USING(id) ORDER BY a.id"""
            save(RUN/(target+'-scope-plan.json'),db.execute('EXPLAIN (FORMAT JSON) '+query,(ids,ids,last)).fetchone())
            while True:
                batch=db.execute(query,(ids,ids,last)).fetchall()
                if not batch:break
                rows+=batch;last=batch[-1]['artwork']['id']
            save(RUN/(target+'-artworks.json.gz'),rows)
            save(RUN/(target+'-audit.json'),dict(at=now(),institutions=institutions,scoped_artworks=len(rows)))
            print(target,len(rows),'scoped artworks',json.dumps([dict(name=x['institution']['name'],slug=x['institution']['slug'],works=x['works'],images=x['images'],city=x['city'])for x in institutions],ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['audit','discover','objects','facts','plan','wikiart','apply','prepare','image_plan','upload','attach','verify','institutions']);p.add_argument('--region',choices=['cyprus','france'],default='cyprus');args=p.parse_args();globals()[args.phase](args.region)if args.phase in ['plan','apply','prepare','image_plan','upload','attach','verify']else globals()[args.phase]()
