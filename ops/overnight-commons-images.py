#!/usr/bin/env python3
"""Exact Wikidata/Commons image matching for existing museum-held painting gaps."""
import argparse,collections,concurrent.futures,hashlib,importlib.util,json,re,time,unicodedata,fcntl
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode,urlparse,urlsplit,parse_qsl
import psycopg
from psycopg.rows import dict_row
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('commons_core',ROOT/'ops/enrich-artwork-images.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
core.VERSION='overnight-exact-commons-images-v1'
core.PROVIDERS['night-commons']='Wikimedia Commons'
core.HOSTS.update({'www.wikidata.org','thumb.wikimedia.org'})
PDM='https://creativecommons.org/publicdomain/mark/1.0/'
CC0='https://creativecommons.org/publicdomain/zero/1.0/'
PAINTED={'Q3305213','Q134194','Q132137','Q22669139'}
_origin_spec=importlib.util.spec_from_file_location('commons_origin',Path(__file__).with_name('overnight-commons-origin.py'));origin=importlib.util.module_from_spec(_origin_spec);_origin_spec.loader.exec_module(origin)

def plain(s):return BeautifulSoup(s or '','html.parser').get_text(' ',strip=True)
def norm(s):return ' '.join(re.findall(r'[^\W_]+',unicodedata.normalize('NFKD',str(s).casefold())))
def accession_keys(value):
    # Joconde retains historical inventory numbers separated by semicolons.
    # Preserve the stored value; match whole alternatives, never numeric prefixes.
    return {norm(part) for part in re.split(r'\s*;\s*',value or '') if part.strip()}
def source_key(url):
    parts=urlsplit(url or '');host=(parts.hostname or '').removeprefix('www.')
    if parts.scheme not in ('https','http'):return None
    query=[(k,v) for k,v in parse_qsl(parts.query) if not k.startswith('utm_') and not (host=='marmottan.fr' and k=='is')]
    return host,parts.path.rstrip('/'),tuple(sorted(query))
def exact_native_file(c,page,text):
    """Exact linked museum object, labelled accession, and artwork creator.

    Own photographs may put object facts in ImageDescription and the photographer
    in Artist. The official object link remains mandatory, never a museum home.
    """
    accession=c.get('accession_number');museum=source_key(c.get('website_url'))
    if not accession or not museum:return False
    meta=page.get('imageinfo',[{}])[0].get('extmetadata',{})
    description=meta.get('ImageDescription',{}).get('value','')
    labelled=text+' '+plain(description)
    if not re.search(r'(?:accession(?: number)?|inv(?:entory|entaire)?\.?)\s*(?:=|:)?\s*'+re.escape(accession)+r'(?![\w])',labelled,re.I):return False
    native={key for x in c.get('native_identifiers') or [] if (key:=source_key(x.get('url')))
            and key[1] not in ('','/') and (key[0]==museum[0] or key[0].endswith('.'+museum[0]))}
    source=' '.join(meta.get(k,{}).get('value','') for k in ('Credit','Attribution','ImageDescription'))
    urls={source_key(a.get('href')) for a in BeautifulSoup(source,'html.parser').find_all('a')}
    artist=norm(c.get('artist',''));credited=norm(plain(meta.get('Artist',{}).get('value','')))
    described=' '+norm(plain(description))+' '
    creator=bool(artist) and (artist==credited or ' '+artist+' ' in described)
    return bool(native&urls) and creator
def canonical_licence_uri(uri):
    uri=(uri or '').replace('http://','https://')
    match=re.fullmatch(r'(https://creativecommons\.org/(?:publicdomain/(?:mark|zero)/1\.0|licenses/(?:by|by-sa)/(?:1\.0|2\.0|2\.5|3\.0|4\.0)))(?:/(?:deed|legalcode)(?:\.[A-Za-z-]+)?)?/?',uri)
    return match[1]+'/' if match else uri
def claims(e,p):
    statements=e.get('claims',e.get('statements',{}))
    # MediaWiki serializes an empty structured-data map as [] on some files.
    if statements==[]:return []
    if not isinstance(statements,dict):raise ValueError('Unsupported structured-data shape requires review')
    cs=[c for c in statements.get(p,[]) if c.get('rank')!='deprecated' and c.get('mainsnak',{}).get('snaktype')=='value']
    return [c for c in cs if c.get('rank')=='preferred'] or cs
def values(e,p):return [c['mainsnak']['datavalue']['value'] for c in claims(e,p)]
def ids(e,p):return {v.get('id') for v in values(e,p) if isinstance(v,dict)}
def verify_structured_object(c,sdc):
    targets=ids(sdc,'P6243')
    if targets and targets!={c['qid']}:
        raise ValueError('Commons structured physical-object identity conflicts; independent review required')
def photographic_credits(c,page):
    meta=page.get('imageinfo',[{}])[0].get('extmetadata',{});field=lambda k:meta.get(k,{}).get('value','')
    painters=[norm(c.get('artist',''))]+[norm(x.get('name','')) for x in c.get('creators',[]) or []]
    def is_painter(name):
        value=norm(name);return bool(value) and any(p and (value in p or p in value) for p in painters)
    names=[];artist=plain(field('Artist'))
    if artist and not is_painter(artist):names.append(artist)
    text=page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
    for value in re.findall(r'^\s*\|\s*(?:photographer|photo author|author)\s*=[ \t]*(.*?)(?=^\s*\||^\s*\}\}|\Z)',text,re.I|re.M|re.S):
        for user,label in re.findall(r'\[\[User:([^]|]+)(?:\|([^]]+))?\]\]',value,re.I):names.append(label or user)
        for name in re.findall(r'\{\{(?:Creator|Institution):([^}|]+)',value,re.I):
            if not is_painter(name):names.append(name)
        # A named photographer may be supplied as plain text or an external
        # profile link, rather than a Commons Creator template.
        clean=re.sub(r'\[https?://\S+\s+([^]]+)\]',r'\1',value).strip()
        if clean and not any(x in clean for x in ('{{','[[','<','|')) and not is_painter(clean):names.append(clean)
    source=field('Credit')+' '+field('Attribution')
    for node in BeautifulSoup(source,'html.parser').find_all('a'):
        if re.search(r'(?:/wiki/|title=)User(?::|%3A)',node.get('href',''),re.I):
            name=node.get_text(' ',strip=True)
            if name and name.lower() not in ('talk','contribs'):names.append(name)
    for name in re.findall(r'photo(?:graph)? by\s+([^;,]+)',plain(source),re.I):names.append(name.strip())
    # An original photograph may credit its maker in a file-level author
    # category. Require the explicit self-photography statement as well;
    # generic categories or the uploading account are not photographic credit.
    if re.search(r'\{\{\s*(?:own(?: photograph)?|self-photographed)\s*\}\}',text,re.I):
        names.extend(re.findall(r'\[\[Category:(?:Images|Photographs) by ([^\]|]+)(?:\|[^\]]*)?\]\]',text,re.I))
    return list(dict.fromkeys(name for name in names if name and not is_painter(name)))
def api(fetcher,host,params):
    url='https://'+host+'/w/api.php?'+urlencode(dict(params,format='json',maxlag=5))
    for attempt in range(3):
        d=fetcher.metadata(url)
        if 'error' not in d:return d
        # Preserve error evidence while allowing a later successful capture.
        key=core.sha(url.encode());suffix='.'+str(time.time_ns())+'.error'
        for ext in ('.json','.receipt.json'):
            path=fetcher.cache/(key+ext)
            if path.exists():path.rename(fetcher.cache/(key+suffix+ext))
        if d['error'].get('code')!='maxlag':raise RuntimeError('Wikimedia API error: '+d['error'].get('code','unknown'))
        core.provider_rate_slot(host,cooldown=60)
        print(core.now(),host,'replication lag; backing off 60 seconds',flush=True)
        time.sleep(60)
    raise RuntimeError('Wikimedia replication lag persists; resume later')

def entity_match(c,e,require_primary_image=True):
    if e.get('id')!=c['qid']:raise ValueError('Redirected or missing artwork authority')
    if not ids(e,'P31') & PAINTED:raise ValueError('Source painting classification needs review')
    if not c['institution_qid'] or c['institution_qid'] not in ids(e,'P195'):raise ValueError('Holding institution not corroborated')
    holdings=[x for x in claims(e,'P195') if x['mainsnak']['datavalue']['value'].get('id')==c['institution_qid']]
    if any('P582' in x.get('qualifiers',{}) for x in holdings):raise ValueError('Historical holding needs review')
    creators={x['qid'] for x in c['creators'] or []}
    if creators and ids(e,'P170')!=creators:raise ValueError('Creator authority conflict')
    if any(set(x.get('qualifiers',{}))-{'P7452'} for x in claims(e,'P170')):raise ValueError('Qualified attribution needs review')
    names={norm(v['value']) for v in e.get('labels',{}).values()}
    names.update(norm(v['value']) for xs in e.get('aliases',{}).values() for v in xs)
    accession={norm(v) for v in values(e,'P217') if isinstance(v,str)}
    stored_accessions=accession_keys(c['accession_number'])
    if stored_accessions and accession and not stored_accessions & accession:raise ValueError('Accession conflict')
    title_match=bool({norm(c['title']),norm(c.get('alternate_title') or '')}&names)
    inv_match=bool(stored_accessions & accession)
    if not title_match and not inv_match:raise ValueError('Title and inventory require manual match')
    for d in values(e,'P571'):
        m=re.match(r'^\+(\d+)-',d.get('time','')) if isinstance(d,dict) else None
        if m and d.get('precision',0)>=9:
            y=int(m[1])
            if not 1000<=y<=1970 or not c['creation_year_start']-5<=y<=c['creation_year_end']+5:raise ValueError('Current date contradiction')
    images=values(e,'P18')
    if not require_primary_image:
        return images[0] if len(images)==1 and isinstance(images[0],str) else None
    if len(images)!=1 or not isinstance(images[0],str):raise ValueError('Missing or multiple primary images')
    if re.search(r'\b(detail|collage|montage|verso|reverse)\b',images[0],re.I):raise ValueError('Detail or reverse needs manual review')
    return images[0]

def rendered_rights_uri(fetcher,page):
    """Recover an explicit file-level licence URI when imageinfo omits it."""
    info=page.get('imageinfo',[{}])[0];meta=info.get('extmetadata',{})
    uri=meta.get('LicenseUrl',{}).get('value','');label=meta.get('LicenseShortName',{}).get('value','')
    if uri or label not in ('Public domain','CC0'):return None
    params={'action':'parse','pageid':page['pageid'],'prop':'text|revid'}
    data=api(fetcher,'commons.wikimedia.org',params);parsed=data.get('parse',{})
    if parsed.get('pageid')!=page['pageid']:raise ValueError('Rendered licence page identity differs')
    revision=page.get('revisions',[{}])[0].get('revid')
    if not revision or parsed.get('revid')!=revision:raise ValueError('File revision changed during licence verification')
    html=parsed.get('text',{}).get('*','');soup=BeautifulSoup(html,'html.parser')
    uris={canonical_licence_uri(n.get_text(strip=True)) for n in soup.select('.licensetpl_link') if n.get_text(strip=True)}
    expected=PDM if label=='Public domain' else CC0
    if uris!={expected}:raise ValueError('Explicit rendered image licence absent or conflicting')
    url='https://commons.wikimedia.org/w/api.php?'+urlencode(dict(params,format='json',maxlag=5))
    receipt=json.loads((fetcher.cache/(core.sha(url.encode())+'.receipt.json')).read_text())
    return {'pageid':page['pageid'],'revid':revision,'uri':expected,'selector':'.licensetpl_link','source_url':url,'capture':receipt}

def rights_and_identity(c,e,page,sdc,rendered=None,allow_exact_depicts=False):
    info=page.get('imageinfo',[{}])[0];meta=info.get('extmetadata',{});field=lambda k:meta.get(k,{}).get('value','')
    label=field('LicenseShortName');uri=canonical_licence_uri(field('LicenseUrl'))
    if rendered and rendered.get('kind')=='explicit_photo_and_artwork_licences':
        split_spec=importlib.util.spec_from_file_location('photo_licence',Path(__file__).with_name('commons-photograph-licence.py'))
        split=importlib.util.module_from_spec(split_spec);split_spec.loader.exec_module(split)
        label,uri=split.validate(c,page,rendered)
        split.validate_structured(rendered,sdc)
    elif not uri and rendered and rendered.get('pageid')==page.get('pageid'):
        uri=rendered.get('uri','')
    if label=='Public domain':
        if field('Copyrighted')!='False':raise ValueError('Conflicting public-domain state')
        if uri.rstrip('/')!=PDM.rstrip('/'):raise ValueError('Missing or conflicting public-domain URI')
        uri=PDM;status='public_domain'
    elif label=='CC0':
        if uri.rstrip('/')!=CC0.rstrip('/'):raise ValueError('Missing or conflicting CC0 URI')
        uri=CC0;status='cc0'
    elif re.fullmatch(r'CC BY(?:-SA)? (?:1\.0|2\.0|2\.5|3\.0|4\.0)',label):
        code='by-sa' if 'BY-SA' in label else 'by';version=label.rsplit(' ',1)[-1]
        if uri.rstrip('/')!=f'https://creativecommons.org/licenses/{code}/{version}':raise ValueError('Licence URI/version mismatch')
        uri=uri.rstrip('/')+'/';status='cc_by_sa' if code=='by-sa' else 'cc_by'
    else:raise ValueError('Licence not approved')
    if field('Restrictions'):raise ValueError('Image restriction needs review')
    wikitext=page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
    if re.search(r'\{\{\s*(?:copyvio|no permission|no source|delete|disputed|wrong license|Not-PD-US)',wikitext,re.I):raise ValueError('Commons rights dispute')
    credit=plain(field('Artist'))
    if not credit:raise ValueError('Missing image creator credit')
    source=field('Credit')+' '+field('Attribution')
    origin.verify(c,page)
    if re.search(r'art500k|wikiart|wikipaintings|pinterest|wallpaper|fineartamerica|wga\.hu|web gallery of art',source,re.I):raise ValueError('Unapproved original image provenance')
    # Concrete source-specific conflicts remain in manual review; no blanket
    # restriction is inferred merely from a work's age or country.
    if re.search(r'(?:rusmuseumvrm\.ru|(?:en\.)?rusmuseum\.ru|nationalgallery\.org\.uk)',source,re.I):raise ValueError('Original source reproduction terms conflict')
    if c['institution_slug'] in ('uffizi','european-uffizi','galleria-degli-uffizi'):raise ValueError('Institutional publication review outstanding')
    if label=='Public domain' and ids(sdc,'P275')-{'Q98592850','Q19652','Q7257361'}:raise ValueError('Conflicting structured image licence')
    if label=='Public domain' and 'Q50423863' in ids(sdc,'P6216'):raise ValueError('Structured image copyright conflict')
    for artist in c['creators'] or []:
        death=artist.get('death')
        if death and int(death)+70>=2026 and label=='Public domain' and re.search(r'PD-(?:Art|old)',wikitext,re.I) and not re.search(r'PD-RusEmpire|PermissionTicket|PermissionOTRS',wikitext,re.I):
            raise ValueError('Generic life-based licence contradicts creator date')
        if death and int(death)+70>=2026 and label!='Public domain' and re.search(r'\{\{\s*Art Photo\b|\bphoto license\s*=',wikitext,re.I) and not re.search(r'\b(?:artwork|art) license\s*=\s*\{\{|PermissionTicket|PermissionOTRS',wikitext,re.I):
            raise ValueError('Photo licence alone does not clear depicted artwork')
    title_html=BeautifulSoup(field('ObjectName') or '','html.parser')
    title_variants={norm(title_html.get_text(' ',strip=True))}
    title_variants.update(norm(node.get_text(' ',strip=True)) for node in title_html.select('[lang], i, .fn'))
    names={norm(v['value']) for v in e.get('labels',{}).values()}
    verify_structured_object(c,sdc)
    q_match=bool(re.search(r'\b'+re.escape(c['qid'])+r'\b',wikitext+' '+field('ObjectName'))) or c['qid'] in ids(sdc,'P6243')
    # Opt-in callers must independently corroborate the exact artwork category,
    # creator and holding context. A depicts claim alone can include copies.
    if allow_exact_depicts and ids(sdc,'P180')=={c['qid']}:q_match=True
    inv_match=bool(c['accession_number'] and c['accession_number'] in wikitext)
    site=(urlparse(c.get('website_url') or '').hostname or '').removeprefix('www.')
    credited_sites={(urlparse(a.get('href','')).hostname or '').removeprefix('www.') for a in BeautifulSoup(source,'html.parser').find_all('a')}
    institution_match=bool(site and site in credited_sites)
    creator_text=norm(plain(field('Artist')))
    creator_match=bool(c['creators']) and all(norm(a['name']) in creator_text or a['qid'] in field('Artist') for a in c['creators'])
    if not q_match and not exact_native_file(c,page,wikitext) and not (inv_match and (bool(title_variants&names) or institution_match and creator_match)):
        raise ValueError('Commons physical-object identity needs review')
    for key in ('Credit','Attribution'):
        v=plain(field(key))
        if v and v not in credit:credit+='; '+v
    photographers=photographic_credits(c,page)
    if status in ('cc_by','cc_by_sa') and not photographers:raise ValueError('Required photographic author attribution is not independently established')
    for name in photographers:
        if norm(name) not in norm(credit):credit+='; Photographic credit: '+name
    if len(credit)>4000:raise ValueError('Unbounded attribution needs review')
    # Use the API-provided standard study rendition for the app's <=100 KB
    # display asset. Request originals only when the API supplies no thumbnail.
    original=not info.get('thumburl') and info.get('size',100_000_000)<=8_000_000 and info.get('width',10000)*info.get('height',10000)<=40_000_000
    url=info.get('url') if original else info.get('thumburl')
    if not url or urlparse(url).hostname not in ('upload.wikimedia.org','thumb.wikimedia.org'):raise ValueError('Unapproved Commons delivery')
    return info,credit,label,uri,status,url,original

original_attach=core.attach
def attach(db,im,target):
    # P18 is a discovery lead, not the identity of the selected photograph.
    # The exact file/object and rights checks below remain mandatory.
    entity_match(im,im['raw']['wikidata'],require_primary_image=False)
    rights_and_identity(im,im['raw']['wikidata'],im['raw']['commons'],im['raw']['structured_data'],im.get('rendered_licence_evidence'))
    with db.transaction():
        matches=db.execute('''SELECT a.id::text,a.slug,a.title,a.creation_year_start,a.creation_year_end,a.work_type
          FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id
          AND e.scheme='wikidata' WHERE e.external_id=%s''',(im['external_id'],)).fetchall()
        if len(matches)!=1 or any(matches[0][k]!=im[k] for k in ('slug','title','creation_year_start','creation_year_end','work_type')):
            raise ValueError('Catalogue object changed or ambiguous')
        if matches[0]['id']!=im['target_ids'][target]:raise ValueError('Target identity changed')
        result=original_attach(db,im,target)
        if result=='attached':
            db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
            db.execute("UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s",('Existing artwork authority, creator and holding institution verified against Wikidata; exact Commons object link or corroborated accession/title/institution/creator, with explicit per-file approved rights and source credit.',im['media_id']))
        return result
core.attach=attach

def prepare_targets(run,dsn):
    path=run/'candidates.json'
    if path.exists():return json.loads(path.read_text())['candidates']
    rows=json.loads((run/'candidates-local.json').read_text());accepted=[];held=[]
    with psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
        remote=db.execute('''SELECT a.id::text,a.slug,a.title,a.creation_year_start,a.creation_year_end,a.work_type,a.primary_media_id::text,e.external_id
          FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata'
          WHERE e.external_id=ANY(%s) AND a.status<>'archived' AND artline_has_selection_evidence(a.id)''',([c['qid'] for c in rows],)).fetchall()
        index=collections.defaultdict(list)
        for r in remote:index[r['external_id']].append(r)
        for c in rows:
            matches=index[c['qid']]
            if not c['institution_qid'] or len(matches)!=1 or any(matches[0][k]!=c[k] for k in ('slug','title','creation_year_start','creation_year_end','work_type')):
                held.append(dict(c,reason='Cross-database or museum identity needs review'));continue
            if matches[0]['primary_media_id']:continue
            accepted.append(dict(c,external_id=c['qid'],provider='night-commons',scheme='wikidata',
              artist='; '.join(x['name'] for x in c['creators'] or []) or 'Attributed creator',
              target_ids={'local':c['artwork_id'],'cloud':matches[0]['id']}))
    core.save_new(path,{'selected_at':core.now(),'candidates':accepted});core.save_new(run/'target-held.json',held)
    return accepted

def research_chunk(rows,run,fetcher):
    es={};entity_receipts={};missing=[]
    index_path=run/'existing-authority-cache-index.json'
    index=json.loads(index_path.read_text()) if index_path.exists() else {}
    for c in rows:
        paths=index.get(c['qid'],[])
        if paths:
            capture=json.loads((ROOT/paths[0]).read_text())
            if capture.get('entity',{}).get('id')==c['qid'] and capture.get('receipt',{}).get('url','').startswith('https://www.wikidata.org/'):
                es[c['qid']]=capture['entity'];entity_receipts[c['qid']]=capture['receipt'];continue
        missing.append(c['qid'])
    if missing:es.update(api(fetcher,'www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(missing),'props':'claims|labels|aliases','languages':'en|mul|fr|it|nl|de|ru|el|sv|da|fi|es|pt|nb|pl'})['entities'])
    prepared=[];verified=[]
    for c in rows:
        try:verified.append((c,es.get(c['qid'],{}),entity_match(c,es.get(c['qid'],{}))))
        except (ValueError,KeyError) as error:core.event(run,{'provider':'night-commons','artwork_id':c['artwork_id'],'external_id':c['qid'],'outcome':'manual_review','reason':str(error)[:250]})
    if not verified:return prepared
    # MediaWiki recommends serial, grouped reads. A single bounded request
    # preserves per-file revisions/licensing and avoids one round trip per file.
    titles=list(dict.fromkeys('File:'+filename for _,_,filename in verified))
    d=api(fetcher,'commons.wikimedia.org',{'action':'query','titles':'|'.join(titles),'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main'})
    pages_by_id={};page_errors={}
    for c,e,filename in verified:
        try:pages_by_id[c['qid']]=page_for_filename(d,filename)
        except ValueError as error:page_errors[c['qid']]=str(error)
    media_ids=list(dict.fromkeys('M'+str(page['pageid']) for page in pages_by_id.values()))
    structured=api(fetcher,'commons.wikimedia.org',{'action':'wbgetentities','ids':'|'.join(media_ids),'props':'claims'})['entities'] if media_ids else {}
    for c,e,filename in verified:
        try:
            if c['qid'] in page_errors:raise ValueError(page_errors[c['qid']])
            page=pages_by_id[c['qid']];mid='M'+str(page['pageid']);sdc=structured.get(mid,{})
            rendered=rendered_rights_uri(fetcher,page)
            info,credit,label,uri,status,url,original=rights_and_identity(c,e,page,sdc,rendered)
            im=dict(c,page=info['descriptionurl'],source_image_url=url,policy_url=uri,rights_status=status,license_label=label,checked_at=core.now(),
              raw={'wikidata':e,'wikidata_capture':entity_receipts.get(c['qid']),'commons':page,'structured_data':sdc},creator_credit=credit,
              source_name='Wikimedia Commons',source_record_url=info['descriptionurl'],image_url=url,image_license=label,
              image_license_url=uri,rights_statement=label,creator=c['artist'],creation_date=c['date_display'],source_object_id=c['qid'],rights_verified_at=core.now())
            if rendered:im['rendered_licence_evidence']=rendered
            im['attribution_text']=f"{c['artist']}. {c['title']}. Image credit: {credit}. {info['descriptionurl']}. {label} ({uri}). Full-frame resize and JPEG compression; applicable ShareAlike terms retained."
            if original:im['commons_original_sha1']=info['sha1']
            core.save_new(run/'selected/night-commons'/(c['artwork_id']+'.json'),im);prepared.append(c)
        except (ValueError,KeyError) as error:
            core.event(run,{'provider':'night-commons','artwork_id':c['artwork_id'],'external_id':c['qid'],'outcome':'manual_review','reason':str(error)[:250]})
    return prepared

def page_for_filename(response,filename):
    query=response.get('query',{});title='File:'+filename
    normalized={x['from']:x['to'] for x in query.get('normalized',[])}
    title=normalized.get(title,title)
    if any(x.get('from')==title for x in query.get('redirects',[])):raise ValueError('Redirected Commons file needs identity review')
    matches=[page for page in query.get('pages',{}).values() if page.get('title')==title]
    if len(matches)!=1 or matches[0].get('ns')!=6 or not matches[0].get('imageinfo') or not isinstance(matches[0].get('pageid'),int) or matches[0]['pageid']<=0:raise ValueError('Exact Commons file missing or ambiguous in batch')
    return matches[0]

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=50);p.add_argument('--deadline',type=float,required=True);p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    lock=(a.run/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if not (a.run.parent/'backups.json').exists():raise SystemExit('Verified recovery backups required')
    dsn=None if a.prepare_only else core.cloud_dsn();rows=prepare_targets(a.run,dsn);latest={}
    if (a.run/'events.jsonl').exists():
        for line in (a.run/'events.jsonl').read_text().splitlines():
            try:r=json.loads(line)
            except ValueError:continue
            if r.get('artwork_id'):latest[r['artwork_id']]=r
    done={k for k,r in latest.items() if r['outcome'] in (('complete','manual_review','failed','prepared') if a.prepare_only else ('complete','manual_review','failed'))}
    rows=[c for c in rows if c['artwork_id'] not in done][:a.limit]
    fetcher=core.Fetcher(a.run/'metadata/commons-evidence')
    for start in range(0,len(rows),10):
        if time.time()>=a.deadline:break
        group=rows[start:start+10];ready=[];fresh=[]
        for c in group:
            if (a.run/'selected/night-commons'/(c['artwork_id']+'.json')).exists():ready.append(c)
            else:fresh.append(c)
        if fresh:ready+=research_chunk(fresh,a.run,fetcher)
        if ready:
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
                jobs=[pool.submit(core.worker,'night-commons',ready[n::3],SimpleNamespace(run=a.run,prepare_only=a.prepare_only),dsn) for n in range(3) if ready[n::3]]
                for job in jobs:job.result()
        print(core.now(),'Commons selected checked',min(start+10,len(rows)),'of',len(rows),'ready',len(ready),'outcomes',dict(core.COUNTS),flush=True)

if __name__=='__main__':main()
