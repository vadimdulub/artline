#!/usr/bin/env python3
"""Second bounded, source-first Byzantine/Russian collection pass."""
import argparse
import importlib.util
import json
import re
import io
import os
import subprocess
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('icons_base',Path(__file__).with_name('byzantine-russian-expansion.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.RUN=m.ROOT/'docs/research/byzantine-russian-more-20260920'
m.BACKUP=Path.home()/'Library/Application Support/Artline/backups/byzantine-russian-more-20260920'
m.SOURCE='byzantine-russian-more-20260920'
m.IMAGE_CAMPAIGN='byzantine-russian-more-20260920'
m.IMAGE_ASSET_FOLDER='byzantine-russian-more-20260920'
m.IMAGE_CONTACT_SHEET='/tmp/artline-byzantine-russian-more-contact.jpg'
m.HOSTS.update({'www.iconmuseum.org','www.rublev-museum.ru','api.vam.ac.uk','collections.vam.ac.uk','www.benaki.org','sp-mz.ru'})
m.PROVIDERS.update({'rublev-museum':('Andrei Rublev Museum','https://www.rublev-museum.ru/'),
                    'icon-museum':('The Icon Museum and Study Center','https://www.iconmuseum.org/'),
                    'vam':('Victoria and Albert Museum','https://www.vam.ac.uk/')})
m.INSTITUTION_DEFINITIONS.update({
    'andrei-rublev-museum':{'name':'Andrei Rublev Museum of Ancient Russian Culture and Art','url':'https://www.rublev-museum.ru/','description':'Official museum collection of icons and original monumental wall-painting fragments. Source attributions and creation dates retained for review.'},
    'icon-museum-and-study-center':{'name':'The Icon Museum and Study Center','url':'https://www.iconmuseum.org/','description':'Museum collection of Eastern Christian icons. Collection ownership and explicitly identified loans are kept separate.'}})


def read_capture(record):
    raw=(m.ROOT/record['capture']['path']).read_bytes();assert m.sha(raw)==record['capture']['sha256'];return raw


def russian_date(literal):
    if re.search(r'оклад\s*[-–—:]|копи',literal,re.I):return None,None,'unknown'
    return m.russian_date(literal.replace('Χ','X').replace('Ι','I'))


def english_date(literal):
    if re.search(r'probably|possibly|renovat|repaint|restor|\?|copy| or ',literal,re.I):return None,None,'unknown'
    return m.english_date(literal)


def rublev_candidates():
    rows,held,seen=[],[],set()
    for path in sorted((m.RUN/'rublev-pages').glob('*.json')):
        record=json.loads(path.read_text());soup=BeautifulSoup(read_capture(record),'html.parser')
        for card in soup.select('.permanent-exhibition-floors-item[data-id]'):
            key=card['data-id']
            if key in seen:continue
            seen.add(key)
            fields={}
            for node in card.select('.properties > div'):
                label=next((c for c in node.get('class',[]) if c.isupper()),None)
                if label:fields[label]=node.get_text(' ',strip=True)
            title=card.h3.get_text(' ',strip=True);date=fields.get('DATE_TXT','');medium=fields.get('MATERIALS','')
            why=None
            if not fields.get('NUMBER'):why='No exact accession in museum card'
            elif re.search(r'копи|прорись|кальк',title+' '+date,re.I):why='Copy or tracing, not the original icon or wall painting'
            elif record['category']=='icons' and not re.search('темпер|масло|живопис|энкауст',medium,re.I):why='Icon medium requires separate classification review'
            elif record['category']!='icons' and not re.search('штукатур|известков|фреск',medium,re.I):why='Wall-painting category contains a copy or unsupported original wall medium'
            if why:
                held.append({'provider':'rublev-museum','source_id':key,'title':title,'reason':why,'fields':fields,'capture':record['capture']});continue
            w=m.base_work('rublev-museum',key,record['url'],title,fields['NUMBER'],'andrei-rublev-museum',record['capture'])
            w.update(date_display=date or 'Date not stated',medium_text=medium or None,dimensions_text=fields.get('SIZES') or None,
                     creator_label=fields.get('AUTHOR') or 'Unidentified artist (not separately named in the museum record)',
                     cultural_context='Russian icon and monumental painting collection; '+fields.get('LOCATION',''))
            w['creation_year_start'],w['creation_year_end'],w['date_precision']=russian_date(date)
            if w['creation_year_start'] and w['creation_year_start']>1970:
                held.append({'provider':'rublev-museum','source_id':key,'title':title,'reason':'Creation after 1970'});continue
            if record['category']!='icons':w.update(work_type='fresco',object_form=None)
            if re.search(r'^Оклад',w['creator_label'],re.I):
                w['creator_label']='Icon painter not recorded; metal-cover attribution: '+w['creator_label']
            w['source_fields']={'catalogue_id':key,'shared_source_page':True,'category':record['category'],'fields':fields,'card_title':title}
            w['notes']=['Museum catalogue card identifies one accessioned object. Page URL is shared by several cards; the source record ID and exact accession determine identity. No current-display claim.',
                        'Original date wording, cover attribution and restoration/provenance comments are retained separately. Museum image reuse permission remains unreviewed.']
            rows.append(w)
    return rows,held


def icon_museum_fields(raw):
    soup=BeautifulSoup(raw,'html.parser');fields={}
    labels={'Inventory Number','Artist','Title','Object Date','Country of Origin','Credit Line','Provenance','Keywords','Metric Dims','Medium'}
    for p in soup.select('p.stk-block-text__text'):
        if p.get_text(' ',strip=True) not in labels:continue
        label=p.get_text(' ',strip=True);wrapper=p.parent;value=wrapper.find_next_sibling('div')
        if value:
            text=value.find('p');fields[label]=text.get_text(' ',strip=True) if text else ''
    return fields


def imsc_candidates():
    rows,held=[],[]
    for path in sorted((m.RUN/'imsc-objects').glob('*.json')):
        record=json.loads(path.read_text());fields=icon_museum_fields(read_capture(record))
        assert fields.get('Title') and fields.get('Inventory Number'),record['url']
        title=fields['Title'];date=fields.get('Object Date','');medium=fields.get('Medium','');country=fields.get('Country of Origin','')
        why=None
        if not re.search(r'Russia|Greece|Crete',country,re.I):why='Origin outside the requested Byzantine/Greek and Russian scope'
        elif not re.search(r'tempera|oil|paint|encaustic',medium,re.I):why='Medium needs separate icon-form review'
        if why:
            held.append({'provider':'icon-museum','url':record['url'],'title':title,'reason':why,'fields':fields});continue
        w=m.base_work('icon-museum',urlparse(record['url']).path,record['url'],title,fields['Inventory Number'],'icon-museum-and-study-center',record['capture'])
        w.update(date_display=date or 'Date not stated',medium_text=medium or None,dimensions_text=fields.get('Metric Dims') or None,
                 creator_label=fields.get('Artist') or 'Unidentified artist (not named in the museum record)',
                 cultural_context='Eastern Christian icon painting; source origin: '+country)
        w['creation_year_start'],w['creation_year_end'],w['date_precision']=english_date(date)
        if (w['creation_year_end'] and w['creation_year_end']<330) or re.search(r'mummy portrait|\bBCE?\b',title+' '+date,re.I):
            held.append({'provider':'icon-museum','url':record['url'],'title':title,'reason':'Pre-Byzantine precursor rather than a Byzantine or Russian icon'});continue
        if w['creation_year_start'] and w['creation_year_start']>1970:
            held.append({'provider':'icon-museum','url':record['url'],'title':title,'reason':'Creation after 1970'});continue
        w['holding_verified']=not bool(re.search(r'\bloan\b',fields.get('Credit Line',''),re.I))
        w['source_fields']={'fields':fields,'country_listing':record['country_index']}
        w['notes']=['Original title, date, origin, attribution, credit line and provenance retained. No current-display claim. Commercial image permission requires further review.']
        if not w['holding_verified']:w['notes'].append('Museum explicitly identifies a loan; its custody is not converted into museum ownership or a current-display assertion.')
        rows.append(w)
    return rows,held


def vam_candidates():
    rows,held=[],[]
    for path in sorted((m.RUN/'vam-objects').glob('*.json')):
        capture=json.loads(path.read_text());data=json.loads(read_capture(capture));r=data['record'];key=r['systemNumber']
        places=[v['place']['text'] for v in r['placesOfOrigin']];medium=r.get('materialsAndTechniques','')
        titles=[t['title'] for t in r['titles'] if t['title']];title=titles[0] if titles else r.get('briefDescription')
        if not title or not re.search('Russia|Greece|Crete|Balkan|Byzant',str(places),re.I) or not re.search('temper|oil|paint',medium,re.I):
            held.append({'provider':'vam','source_id':key,'reason':'Needs title, cultural-origin or painted-icon medium review','source_fields':r});continue
        url=data['meta']['_links']['collection_page']['href'];date='; '.join(v['date']['text'] for v in r['productionDates'])
        w=m.base_work('vam',key,url,title,r['accessionNumber'],'wikimedia-museum-q213322',capture['capture'])
        creator=[]
        for a in r['artistMakerPerson']:
            creator.append(' — '.join(filter(None,[a['name']['text'],a['association']['text'],a.get('note')])) )
        w.update(date_display=date or 'Date not stated',medium_text=medium,creator_label='; '.join(creator) or 'Unidentified artist (not named in the source record)',
                 dimensions_text='; '.join(' '.join(filter(None,[d['dimension'],d['value'],d['unit'],d.get('part'),d.get('qualifier')])) for d in r['dimensions']) or None,
                 cultural_context='Eastern Christian icon; source origin: '+', '.join(places))
        w['creation_year_start'],w['creation_year_end'],w['date_precision']=english_date(date)
        if len(r['productionDates'])!=1:w.update(creation_year_start=None,creation_year_end=None,date_precision='unknown')
        # Keep the museum's supplied structured bounds where one unambiguous
        # creation statement exists; do not infer dates from acquisition years.
        if len(r['productionDates'])==1 and w['date_precision']!='unknown':
            dt=r['productionDates'][0]['date'];a,b=dt.get('earliest'),dt.get('latest')
            if a and b and re.match(r'^\d{4}-',a) and re.match(r'^\d{4}-',b):
                w['creation_year_start'],w['creation_year_end']=int(a[:4]),int(b[:4])
        if w['creation_year_start'] and w['creation_year_start']>1970:
            held.append({'provider':'vam','source_id':key,'reason':'Creation after 1970'});continue
        w['source_fields']={'record':r,'image_metadata':data['meta'].get('images'),'api_url':capture['url']}
        w['notes']=['Source object record, exact accession and museum production fields retained. Repainting, tentative dating and multiple production phases remain in review. V&A image copyright retained; no image downloaded. No current-display claim.']
        rows.append(w)
    return rows,held


def open_access_candidates():
    """Previously captured official records: extend explicitly to other icon media."""
    previous=m.ROOT/'docs/research/byzantine-russian-icons-frescoes-20260920'
    met_ids={466046,468541,466163,463984,468547,467736,464531,465946,464013,468704,474336,464014,466068,465941,468607,464520,466272,464428}
    rows=[]
    for path in sorted((previous/'met-objects').glob('*.json')):
        record=json.loads(path.read_text());o=record.get('object',{})
        if o.get('objectID') not in met_ids:continue
        w=m.base_work('met',o['objectID'],o['objectURL'],o['title'],o['accessionNumber'],'the-met',record['capture'])
        w.update(work_type='unknown',date_display=o['objectDate'],medium_text=o['medium'],dimensions_text=o.get('dimensions'),cultural_context=o['culture'])
        if not re.search(r' or |later|\?',o['objectDate'],re.I):
            lo,hi=o['objectBeginDate'],o['objectEndDate'];assert lo<=hi<=1970
            w.update(creation_year_start=lo,creation_year_end=hi,date_precision=('circa' if lo==hi else 'circa_range') if re.search(r'ca\.|circa',o['objectDate'],re.I) else ('exact' if lo==hi else 'range'))
        assert o['isPublicDomain'] is True and not o.get('rightsAndReproduction') and o['primaryImage']
        w['image_candidate']={'url':o['primaryImage'],'rights_status':'cc0','license_label':'CC0 1.0','license_url':'https://creativecommons.org/publicdomain/zero/1.0/','credit':'The Metropolitan Museum of Art; '+o.get('creditLine','')}
        w['source_fields']={'object':o,'reused_capture_from':str(previous.relative_to(m.ROOT))}
        w['notes']=['An icon in the museum’s literal material and classification ('+o['classification']+'); broad work type remains unknown pending editorial classification. It is not labelled as a panel painting. No current-display claim. Icon frames, detached frame ornaments and covers are not separate selections.']
        rows.append(w)
    url='https://openaccess-api.clevelandart.org/api/artworks/?q=icon&limit=100';key=m.sha(url.encode())
    receipt=json.loads((previous/'captures'/(key+'.json')).read_text());raw=(m.ROOT/receipt['path']).read_bytes();assert m.sha(raw)==receipt['sha256']
    for o in json.loads(raw)['data']:
        if o['id'] not in {375054,128824,137347,131821,150516}:continue
        assert o['legal_status']=='accessioned' and not o['on_loan'] and o['share_license_status']=='CC0' and not o.get('copyright')
        w=m.base_work('cleveland',o['id'],o['url'],o['title'],o['accession_number'],'cleveland-museum-of-art',receipt)
        w.update(work_type='unknown',date_display=o['creation_date'],medium_text=o['technique'],dimensions_text=o.get('measurements'),cultural_context='; '.join(o['culture']))
        if o['id']!=128824:
            lo,hi=o['creation_date_earliest'],o['creation_date_latest'];assert lo<=hi<=1970
            w.update(creation_year_start=lo,creation_year_end=hi,date_precision='exact' if lo==hi else 'range')
        if o['creators']:w['creator_label']='; '.join(((a.get('qualifier')+' ') if a.get('qualifier') else '')+a['description'] for a in o['creators'])[:500]
        assert not o.get('rights_and_reproductions') and o['images']['web']['url']
        w['image_candidate']={'url':o['images']['web']['url'],'rights_status':'cc0','license_label':'CC0 1.0','license_url':'https://creativecommons.org/publicdomain/zero/1.0/','credit':'The Cleveland Museum of Art; '+o.get('creditline','')}
        w['source_fields']={'object':o,'reused_capture_from':str(previous.relative_to(m.ROOT))}
        w['notes']=['One accessioned icon or icon fragment; literal stone, metal or enamel medium retained. Broad type remains in review, not inferred to be painting. No current-display claim.']
        if o['id']==128824:w['notes'].append('The pendant and its later frame are one composite museum object. Their different dates are preserved in the source wording without a fabricated single creation range. Component records are not separately imported.')
        rows.append(w)
    assert len(rows)==23
    return rows,[]


def assemble():
    rows,held=[],[]
    for fn in (rublev_candidates,imsc_candidates,vam_candidates,open_access_candidates):
        selected,deferred=fn();rows.extend(selected);held.extend(deferred)
    identities={}
    for w in rows:identities.setdefault((w['institution_slug'],m.accession_key(w['accession_number'])),[]).append(w)
    merged=set()
    reviewed_accessions={'кп3871','кп-549','кп942','кп1935'}
    for (_,accession),group in identities.items():
        if len(group)<2 or accession not in reviewed_accessions:continue
        assert len(group)==2 and all(w['provider']=='rublev-museum' for w in group)
        fields=('title','date_display','medium_text','work_type','creator_label')
        assert all(all(w[k]==group[0][k] for k in fields) for w in group)
        assert len({tuple(re.findall(r'\d+(?:[.,]\d+)?',w['dimensions_text'])) for w in group})==1
        primary=sorted(group,key=lambda w:(-len(json.dumps(w['source_fields'])),int(w['source_object_id'])))[0]
        aliases=[w for w in group if w is not primary]
        primary['source_fields']['additional_source_records']=[{'source_object_id':w['source_object_id'],'source_url':w['source_url'],'source_capture':w['source_capture'],'source_fields':w['source_fields']} for w in aliases]
        primary['notes'].append('Two museum cards identify the same accession, subject, creation date, dimensions and medium. One physical object is retained; alternate card identity and both source captures are preserved. For a double-sided icon, both faces remain one artwork.')
        merged.update(w['id'] for w in aliases)
    rows=[w for w in rows if w['id'] not in merged]
    conflicts={w['id'] for group in identities.values() if len(group)>1 and not any(w['id'] in merged for w in group) for w in group}
    for w in rows:
        if w['id'] in conflicts:held.append({'provider':w['provider'],'title':w['title'],'reason':'Selected object identity requires accession reconciliation','source_fields':w['source_fields']})
    rows=[w for w in rows if w['id'] not in conflicts]
    value={'at':m.now(),'records':rows,'held':held,'merged_source_cards':len(merged),'scope':'Second local Byzantine/post-Byzantine and Russian icon/fresco expansion'}
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode();digest=m.sha(raw);path=m.RUN/'selections'/(digest+'.json');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    (m.RUN/'latest-selection.json').write_text(json.dumps({'path':str(path.relative_to(m.ROOT)),'sha256':digest},indent=2)+'\n')
    print(json.dumps({'selected':len(rows),'held':len(held),'providers':dict(Counter(w['provider'] for w in rows)),'types':dict(Counter(w['work_type'] for w in rows)),'dates':dict(Counter(w['date_precision'] for w in rows))}),flush=True)


def fetch(urls):
    c=m.Capture()
    for url in urls:
        try:
            raw,receipt=c.get(url)
            soup=BeautifulSoup(raw,'html.parser')
            links=[{'url':urljoin(url,a['href']),'text':a.get_text(' ',strip=True)} for a in soup.select('a[href]')]
            for n in soup.select('script,style,nav,header,footer'):n.decompose()
            path=m.RUN/'probes'/(m.sha(url.encode())+'.json')
            if not path.exists():m.save(path,{'capture':receipt,'text':soup.get_text(' ',strip=True),'links':links})
            print(json.dumps({'url':url,'bytes':len(raw),'links':len(links),'probe':str(path.relative_to(m.ROOT))}),flush=True)
        except Exception as exc:
            print(json.dumps({'url':url,'error':str(exc)}),flush=True)


def capture_object(c,url,folder,extra=None):
    path=m.RUN/folder/(m.sha(url.encode())+'.json')
    if path.exists():return json.loads(path.read_text())
    raw,receipt=c.get(url)
    value={'url':url,'capture':receipt,**(extra or {})};m.save(path,value)
    return value


def collect_rublev():
    c=m.Capture();seen=set()
    for category,cap in [('icons',70),('frescoes-monumental-painting',20)]:
        url='https://www.rublev-museum.ru/collection/'+category+'/'
        for page in range(1,cap+1):
            record=capture_object(c,url,'rublev-pages',{'category':category,'page':page})
            soup=BeautifulSoup((m.ROOT/record['capture']['path']).read_bytes(),'html.parser')
            cards=soup.select('.permanent-exhibition-floors-item[data-id]')
            assert cards,'No collection cards: '+url
            ids={n['data-id'] for n in cards}
            if ids<=seen:break
            seen.update(ids)
            links=[urljoin(url,a['href']) for a in soup.select('a[href]') if 'PAGEN_1=' in a['href']]
            if page%5==0:print('Rublev',category,'page',page,'distinct records',len(seen),flush=True)
            if not links:break
            assert len(set(links))==1
            url=links[0]
    print('Rublev capture complete',len(seen),flush=True)


def collect_imsc():
    c=m.Capture();leads={}
    for country,cap in [('russia',16),('greece',5)]:
        for page in range(1,cap+1):
            url='https://www.iconmuseum.org/country/'+country+'/'+('page/'+str(page)+'/' if page>1 else '')
            record=capture_object(c,url,'imsc-index',{'country':country,'page':page})
            soup=BeautifulSoup((m.ROOT/record['capture']['path']).read_bytes(),'html.parser')
            links={urljoin(url,a['href']) for a in soup.select('a[href]') if re.search(r'/collection/[^/]+/$',a['href'])}
            assert links,'No object links: '+url
            for link in sorted(links):leads[link]={'country_index':country,'index_capture':record['capture']}
            if not any('/page/'+str(page+1)+'/' in a['href'] for a in soup.select('a[href]')):break
    for i,(url,extra) in enumerate(leads.items()):
        capture_object(c,url,'imsc-objects',extra)
        if (i+1)%20==0:print('Icon Museum captured',i+1,'/',len(leads),flush=True)
    print('Icon Museum capture complete',len(leads),flush=True)


def collect_vam():
    c=m.Capture()
    url='https://api.vam.ac.uk/v2/objects/search?q_object_type=icon&page_size=100'
    raw,receipt=c.get(url);data=json.loads(raw)
    assert data['info']['pages']==1 and len(data['records'])<100
    for r in data['records']:
        if r['_primaryPlace'] in ('India','Rome','Kyiv'):continue
        url='https://api.vam.ac.uk/v2/museumobject/'+r['systemNumber']
        capture_object(c,url,'vam-objects',{'listing':r,'index_capture':receipt})
    print('V&A icon metadata capture complete',flush=True)


def collect():
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(fn) for fn in (collect_rublev,collect_imsc,collect_vam)]
        for future in futures:future.result()


def verify():
    from PIL import Image
    plan,pin=m.selection();works={w['id']:w for w in plan['records']};ids=sorted(works)
    receipts=[];receipt_ids=[];record_pins={}
    for path in sorted((m.RUN/'applied').glob('*.json')):
        if path.name.startswith('selection-'):continue
        r=json.loads(path.read_text());receipts.append(str(path.relative_to(m.ROOT)))
        for row in r['new_records']:
            receipt_ids.append(row['id']);record_pins[row['id']]=r['selection']['sha256']
    assert len(receipt_ids)==len(set(receipt_ids))==len(ids) and set(receipt_ids)==set(ids)
    with m.psycopg.connect(m.DSN,options='-c default_transaction_read_only=on',row_factory=m.dict_row) as db:
        rows=db.execute("""SELECT to_jsonb(a) artwork,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,
          artline_has_selection_evidence(id) selected FROM artworks a WHERE id=ANY(%s::uuid[])""",(ids,)).fetchall()
        holdings=db.execute('SELECT to_jsonb(h) record FROM artwork_location_assertions h WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchall()
        citations=db.execute("SELECT entity_id::text artwork_id,source_url,source_record_id,field_name,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchall()
        media=db.execute('SELECT a.id::text artwork_id,to_jsonb(m) record FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,)).fetchall()
        existing=m.reconcile(db,plan)
        baseline=json.loads((m.RUN/'baseline.json').read_text());baseline_ids=[r['artwork']['id'] for r in baseline['records']]
        assert not set(ids)&set(baseline_ids)
        scoped_plan=db.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT id,title FROM artworks WHERE id=ANY(%s::uuid[])',(ids[:20],)).fetchone()['QUERY PLAN']
    assert len(rows)==len(ids) and not existing['new'] and not existing['conflicts']
    byid={r['artwork']['id']:r for r in rows};holdings_by_id={}
    for h in holdings:holdings_by_id.setdefault(h['record']['artwork_id'],[]).append(h['record'])
    for key,r in byid.items():
        w=works[key];a=r['artwork']
        for field in ('title','date_display','creation_year_start','creation_year_end','date_precision','work_type','object_form','medium_text','dimensions_text','cultural_context','accession_number'):
            assert a[field]==w[field],(key,field)
        assert a['unlinked_creator_label']==w['creator_label'] and a['status']=='review' and a['published_at'] is None and a['research_candidate'] and r['selected']
        assert any(c['artwork_id']==key and c['field_name']=='official_object_identity' and c['source_url']==w['source_url'] and record_pins[key] in c['evidence_note'] for c in citations)
        for alias in w['source_fields'].get('additional_source_records',[]):
            assert m.sha((m.ROOT/alias['source_capture']['path']).read_bytes())==alias['source_capture']['sha256']
            assert any(c['artwork_id']==key and c['field_name']=='alternate_object_identity' and c['source_record_id']==alias['source_object_id'] for c in citations)
        hh=holdings_by_id.get(key,[])
        if w.get('holding_verified',True):
            assert len(hh)==1 and hh[0]['claim_type']=='holding' and hh[0]['review_state']=='accepted' and hh[0]['institution_id']==a['current_institution_id'] and hh[0]['source_url']==w['source_url']
        else:assert not hh and a['current_institution_id'] is None
    attached=json.loads((m.RUN/'images-attached.json').read_text())['records']
    assert {r['artwork_id'] for r in attached}=={r['artwork_id'] for r in media}
    image_checks=[]
    for row in media:
        im=row['record'];raw=(m.ROOT/'apps/web/public'/im['storage_path'].lstrip('/')).read_bytes()
        assert m.sha(raw)==im['checksum_sha256'].strip() and len(raw)==im['byte_size']<=100000 and im['rights_status']=='cc0'
        with Image.open(io.BytesIO(raw)) as decoded:decoded.load();assert decoded.size==(im['width'],im['height'])
        image_checks.append({'artwork_id':row['artwork_id'],'path':im['storage_path'],'sha256':m.sha(raw),'bytes':len(raw)})
    report={'at':m.now(),'selection':pin,'new_records':len(ids),'icons':sum(w['object_form']=='icon' for w in works.values()),'frescoes':sum(w['work_type']=='fresco' for w in works.values()),
            'providers':dict(Counter(w['provider'] for w in works.values())),'date_precision':dict(Counter(w['date_precision'] for w in works.values())),
            'creation_scope':dict(Counter(r['scope'] for r in rows)),'holding_assertions':len(holdings),'loan_records_without_holding':sum(not w.get('holding_verified',True) for w in works.values()),
            'display_assertions':0,'held_records':len(plan['held']),'merged_source_cards':plan['merged_source_cards'],'batch_receipts':receipts,
            'images':image_checks,'id_query_plan':scoped_plan,'checks':[],'limitations':'Local verification only; no fixture database, production delivery or large-scale benchmark. Unknown/open-ended dates stay out of the dated atlas.'}
    token=re.search(r'^ARTLINE_EDITOR_TOKEN=(.*)$',(m.ROOT/'apps/server/.env').read_text(),re.M)[1].strip().strip('\"\'')
    session=requests.Session();session.headers['Authorization']='Bearer '+token
    def get(path,status=200):
        start=time.monotonic();r=session.get('http://localhost:8081/api/v1/'+path,timeout=20)
        report['checks'].append({'path':path,'status':r.status_code,'ms':round((time.monotonic()-start)*1000)})
        assert r.status_code==status,(path,r.status_code,r.text[:250]);return r.json()
    samples={}
    for field in ('provider','work_type','date_precision'):
        for w in works.values():samples.setdefault((field,w[field]),w)
    sample_ids={w['id'] for w in samples.values()}|{im['artwork_id'] for im in media}
    sample_ids.update(w['id'] for w in sorted(works.values(),key=lambda w:w['creation_year_start'] or 9999)[:5])
    sample_ids.update(w['id'] for w in works.values() if w['source_fields'].get('additional_source_records'))
    sample_ids.update(w['id'] for w in [w for w in works.values() if not w.get('holding_verified',True)][:3])
    sample_ids.update(w['id'] for w in [w for w in works.values() if w['work_type']=='fresco'][::20])
    for key in sorted(sample_ids):
        w=works[key];eligible=byid[key]['scope']=='eligible'
        d=get('atlas/artworks/'+key+'?preview=1',200 if eligible else 404)
        if eligible:
            for field in ('id','title','date_precision','creation_year_start','creation_year_end','work_type','object_form'):assert d[field]==w[field],(key,field)
            assert d['status']=='review' and d['media_url']==next((im['record']['storage_path'] for im in media if im['artwork_id']==key),None)
        if w.get('holding_verified',True):
            d=get('museums/'+w['institution_slug']+'/works/'+key+'?preview=1')
            assert d['title']==w['title'] and d['display'] is None and d['holding']['slug']==w['institution_slug']
            assert any(c['source_url']==w['source_url'] for c in d['citations'])
    for slug in m.INSTITUTION_DEFINITIONS:
        expected=sum(w['institution_slug']==slug and w.get('holding_verified',True) for w in works.values())
        page=get('museums/'+slug+'/works?preview=1&limit=5')
        assert page['total']==expected and len(page['items'])==5 and page['next_cursor']
        page2=get('museums/'+slug+'/works?preview=1&limit=5&cursor='+requests.utils.quote(page['next_cursor'],safe=''))
        assert not {w['id'] for w in page['items']} & {w['id'] for w in page2['items']}
        assert get('museums/'+slug+'/works?preview=1&display=on_view')['total']==0
    preview=Path('/tmp/artline-all-zoom-web');assert (preview/'public').resolve()==m.ROOT/'apps/web/public'
    with Path('/tmp/artline-byzantine-more-web-verify.log').open('w') as log:
        proc=subprocess.Popen(['node',str(m.ROOT/'apps/web/node_modules/next/dist/bin/next'),'start','--port','3111','--hostname','127.0.0.1'],cwd=preview,stdout=log,stderr=subprocess.STDOUT)
        try:
            for attempt in range(30):
                assert proc.poll() is None
                try:
                    if requests.get('http://127.0.0.1:3111'+image_checks[0]['path'],timeout=2).status_code==200:break
                except requests.ConnectionError:pass
                time.sleep(.5)
            for item in image_checks:
                r=requests.get('http://127.0.0.1:3111'+item['path'],timeout=15)
                assert r.status_code==200 and m.sha(r.content)==item['sha256']
                item['local_http_verified']=True
        finally:
            proc.terminate()
            try:proc.wait(timeout=10)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
    report['passed']=True
    m.save(m.RUN/'verification.json',report)
    m.save(m.RUN/'delivery-manifest.json',{'at':m.now(),'selection':pin,'batch_receipts':receipts,'new_artwork_ids':ids,'new_records':len(ids),'images':attached,'local_only':True})
    print(json.dumps({k:report[k] for k in ('new_records','icons','frescoes','providers','creation_scope','holding_assertions','loan_records_without_holding','passed')}),flush=True)
    print('API checks',len(report['checks']),'HTTP image checks',len(image_checks),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['fetch','audit','collect','assemble','preflight','backup','apply','prepare_images','attach_images','verify']);p.add_argument('urls',nargs='*');args=p.parse_args()
    if args.stage=='fetch':fetch(args.urls)
    elif args.stage in ('audit','preflight','backup','apply','prepare_images','attach_images'):getattr(m,args.stage)()
    else:globals()[args.stage]()
