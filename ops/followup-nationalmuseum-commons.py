#!/usr/bin/env python3
"""Independently verify museum-linked Commons donations; never request denied museum images."""
import argparse,copy,fcntl,importlib.util,json,re,time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import unquote,urlparse

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('nm',ROOT/'ops/followup-nationalmuseum-images.py');nm=importlib.util.module_from_spec(s);s.loader.exec_module(nm);core=nm.core
s=importlib.util.spec_from_file_location('common',ROOT/'ops/overnight-commons-images.py');common=importlib.util.module_from_spec(s);s.loader.exec_module(common)
PROVIDER='followup-nationalmuseum-commons';core.PROVIDERS[PROVIDER]='Nationalmuseum, Sweden via Wikimedia Commons';core.VERSION='nationalmuseum-object-commons-v2'

def file_title(url):
    # Normalize legacy museum metadata links; network requests still use HTTPS.
    if (url or '').startswith('http://commons.wikimedia.org/wiki/'):
        url='https://'+url[len('http://'):]
    prefix='https://commons.wikimedia.org/wiki/'
    if not (url or '').startswith(prefix):raise ValueError('Official record lacks a canonical Commons file link')
    # Some museum links leave a literal question mark in the filename. Treat
    # the bounded File: label as a title, never as a URL to fetch or a query.
    title=unquote(url[len(prefix):]).replace('_',' ')
    if '#' in title or not re.fullmatch(r'File:.+\.(?:tif|tiff|jpg|jpeg|png)',title,re.I):raise ValueError('Official Commons filename requires review')
    return title

def rendered_identity(fetch,page):
    params={'action':'parse','pageid':page['pageid'],'prop':'text|revid'};d=common.api(fetch,'commons.wikimedia.org',params);parsed=d.get('parse',{})
    if parsed.get('pageid')!=page['pageid'] or parsed.get('revid')!=page['revisions'][0]['revid']:raise ValueError('Rendered object identity revision changed')
    soup=common.BeautifulSoup(parsed.get('text',{}).get('*',''),'html.parser');cell=soup.find(id='fileinfotpl_art_id');numbers=[]
    if cell:
        for node in cell.parent.select('.identifier'):
            for extra in node.select('small,.noprint,[typeof]'):extra.decompose()
            text=node.get_text(' ',strip=True)
            if text:numbers.append(text)
    url='https://commons.wikimedia.org/w/api.php?'+common.urlencode(dict(params,format='json',maxlag=5))
    receipt=json.loads((fetch.cache/(common.core.sha(url.encode())+'.receipt.json')).read_text())
    return {'pageid':page['pageid'],'revid':page['revisions'][0]['revid'],'accessions':numbers,'source_url':url,'capture':receipt,'retrieved_at':core.now()}

def creator_alias(fetch,c,page):
    wt=page['revisions'][0]['slots']['main']['*'];line=re.search(r'^\s*\|artist\s*=\s*(.*)$',wt,re.M)
    names=re.findall(r'\{\{Creator:([^}|]+)',line[1] if line else '')
    if len(names)!=1 or not c.get('artist_qid'):return None
    title='Creator:'+names[0];d=common.api(fetch,'commons.wikimedia.org',{'action':'query','titles':title,'redirects':1,'prop':'revisions','rvprop':'ids|content','rvslots':'main'});pages=list(d.get('query',{}).get('pages',{}).values())
    if len(pages)!=1 or not pages[0].get('revisions'):return None
    redirects=d.get('query',{}).get('redirects',[])
    if any(not x.get('from','').startswith('Creator:') or not x.get('to','').startswith('Creator:') for x in redirects):return None
    p=pages[0];text=p['revisions'][0]['slots']['main']['*'];qids=re.findall(r'^\s*\|\s*Wikidata\s*=\s*(Q\d+)\s*$',text,re.I|re.M)
    if qids!=[c['artist_qid']]:return None
    return {'creator_template':title,'resolved_creator_template':p['title'],'redirects':redirects,'wikidata_id':qids[0],'source_url':'https://commons.wikimedia.org/wiki/'+p['title'].replace(' ','_'),'pageid':p['pageid'],'revid':p['revisions'][0]['revid'],'identity_line':next(l for l in text.splitlines() if re.search(r'\|\s*Wikidata\s*=',l,re.I))}

def verify_file_reference(c,page):
    item=c['raw']['official_capture']['item'];link=item.get('ObjWikimediaLinkTxt')
    if link:
        if page.get('title','').replace('_',' ')!=file_title(link):raise ValueError('Commons file is not the museum-linked resource')
        return
    # Discovery is only a lead. The native museum ID, accession, artist, title,
    # physical-object cross reference and exact donation licence below remain
    # mandatory even when the current museum page has no outward Commons link.
    evidence=c['raw'].get('commons_discovery',{})
    query='"Nationalmuseum" "'+c['external_id']+'"'
    hits=evidence.get('response',{}).get('query',{}).get('search',[])
    if evidence.get('source_object_id')!=c['external_id'] or evidence.get('query')!=query or not evidence.get('retrieved_at'):
        raise ValueError('Independent Commons discovery evidence is absent')
    if not any(x.get('pageid')==page.get('pageid') and x.get('title')==page.get('title') for x in hits):
        raise ValueError('Commons file differs from captured discovery lead')
    if re.search(r'\b(detail|détail|verso|reverse|collage|montage|cropped)\b',page.get('title',''),re.I):
        raise ValueError('Discovered partial or composite reproduction requires review')

def verify_accession(c,page,wt):
    # Horizontal whitespace matters: \\s* consumed the following template line
    # when an accession field was empty, misreading it as a conflicting number.
    stated=re.search(r'^[ \t]*\|accession number[ \t]*=[ \t]*([^\r\n]*)',wt,re.M)
    value=stated[1].strip() if stated else ''
    expected=c['raw']['official_capture']['item']['ObjInventoryNumberTxt'] if c.get('preserve_existing_catalogue_format') else c['accession_number']
    if value==expected:return
    linked=re.fullmatch(r'\{\{Nationalmuseum Stockholm link\|([^|{}]+)\|([^|{}]+)\}\}',value)
    if linked and linked[1]==c['external_id'] and linked[2].strip()==expected:return
    if value:raise ValueError('File accession conflicts with current museum object')
    evidence=c.get('rendered_identity_evidence',{})
    if evidence.get('pageid')!=page['pageid'] or evidence.get('revid')!=page['revisions'][0]['revid'] or evidence.get('accessions')!=[expected]:
        raise ValueError('File accession conflicts with current museum object')

def multilingual_title(wt):
    """Explicit title-template languages; never translate or infer a title."""
    match=re.search(r'^\s*\|title\s*=\s*(\{\{title\|[^{}]*\}\})',wt,re.M)
    if not match:return '',set()
    names=re.findall(r'\|(?:en|sv|fr|de|it|ca)\s*=\s*([^|{}]+)',match[1])
    return match[1],{nm.norm(name.strip()) for name in names}

def verify_file(c,page,rendered,sdc):
    capture=c['raw']['official_capture'];item=capture['item'];wt=page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
    verify_file_reference(c,page)
    info=page.get('imageinfo',[{}])[0];meta=info.get('extmetadata',{});field=lambda k:meta.get(k,{}).get('value','')
    if re.search(r'\{\{\s*(?:copyvio|delete|no permission|no source|wrong license|disputed)',wt,re.I) or field('Restrictions'):raise ValueError('Commons file has rights concerns')
    if not re.search(r'\{\{Nationalmuseum Stockholm link\|'+re.escape(c['external_id'])+r'\|',wt):raise ValueError('Exact museum object provenance is absent')
    verify_accession(c,page,wt)
    if '{{Nationalmuseum Stockholm cooperation project}}' not in wt or not re.search(r'\{\{Licensed-PD-Art\|[^\n}]*\b2=PD-Nationalmuseum_Stockholm',wt):raise ValueError('Explicit museum photographic donation rights are missing')
    source_titles={nm.norm(t) for t in (c['title'],item.get('ObjTitleMainTxt_sv'),c['raw']['lead'].get('title')) if t}
    file_titles=nm.util.visible_title_variants(field('ObjectName'))
    title_line=re.search(r'^\s*\|title\s*=\s*(.*)$',wt,re.M)
    file_titles.update(nm.norm(t) for t in re.findall(r'\{\{(?:en|sv|fr|de|it)\|([^{}]+)\}\}',title_line[1] if title_line else ''))
    file_titles.update(multilingual_title(wt)[1])
    if not source_titles & file_titles:raise ValueError('Commons title differs from current or historical museum titles')
    artist_names={nm.norm(c['artist'])}|{nm.norm(p['name']) for p in c['raw']['lead']['people']}
    if nm.norm(common.plain(field('Artist'))) not in artist_names:
        alias=c.get('creator_alias_evidence') or {};line=re.search(r'^\s*\|artist\s*=\s*(.*)$',wt,re.M);names=re.findall(r'\{\{Creator:([^}|]+)',line[1] if line else '')
        if len(names)!=1 or alias.get('creator_template')!='Creator:'+names[0] or not c.get('artist_qid') or alias.get('wikidata_id')!=c['artist_qid'] or not re.search(r'\|\s*Wikidata\s*=\s*'+re.escape(c['artist_qid'])+r'\s*$',alias.get('identity_line',''),re.I):raise ValueError('Commons creator differs from the verified museum artist')
    qids=re.findall(r'^\s*\|wikidata\s*=\s*(Q\d+)\s*$',wt,re.M)
    if len(qids)!=1 or c.get('qid') and qids!=[c['qid']]:raise ValueError('Commons physical-object cross reference differs')
    common.verify_structured_object({'qid':qids[0]},sdc)
    uri=common.canonical_licence_uri(field('LicenseUrl'))
    if not uri and rendered and rendered.get('pageid')==page.get('pageid') and rendered.get('revid')==page.get('revisions',[{}])[0].get('revid'):uri=rendered['uri']
    if field('LicenseShortName')!='Public domain' or field('Copyrighted')!='False' or uri!=nm.PDM:raise ValueError('Exact donated image lacks an explicit unambiguous Public Domain Mark')
    url=info.get('thumburl','')
    if urlparse(url).scheme!='https' or urlparse(url).hostname not in ('upload.wikimedia.org','thumb.wikimedia.org'):raise ValueError('Unapproved Commons rendition host')
    credit=common.plain(field('Artist'))+'; Nationalmuseum, Sweden (museum-contributed reproduction)'
    for k in ('Credit','Attribution'):
        value=common.plain(field(k))
        if value and value not in credit:credit+='; '+value
    return url,credit,info['descriptionurl']

def verify(im):
    facts=nm.fact_check(im['raw']['lead'],im['raw']['official_capture'])
    nm.verify_catalogue_facts(im,facts)
    url,credit,page=verify_file(im,im['raw']['commons_file'],im.get('rendered_licence_evidence'),im['raw']['structured_data'])
    if (url,credit,page)!=(im['source_image_url'],im['creator_credit'],im['page']) or im['policy_url']!=nm.PDM or im['rights_status']!='public_domain':raise ValueError('Image provenance or exact rights differ')

def project_capture(capture):
    fields={'Id','ObjCollectionSearchTxt','ObjCategoryTxt','ObjInventoryNumberTxt','ObjDonationTxt','ObjPersonRef','ObjFromYearTxt','ObjToYearTxt','ObjDateMainTxt','ObjTitleMainTxt','ObjTitleMainTxt_sv','ObjMaterialTechniqueTxt','ObjExternalIDTxt','ObjWikimediaLinkTxt'}
    out=copy.deepcopy(capture);out['item']={k:v for k,v in out['item'].items() if k in fields};out.pop('rendered_image_paths',None);return out

def project_file(page):
    out=copy.deepcopy(page)
    for info in out.get('imageinfo',[]):
        for key in ('ImageDescription','Permission'):info.get('extmetadata',{}).pop(key,None)
    wt=out['revisions'][0]['slots']['main']['*']
    kept=[line for line in wt.splitlines() if re.match(r'^\s*\|(?:artist|title|wikidata|object_type|date|institution|accession number|source|permission)\s*=',line) or line.startswith('{{Licensed-PD-Art|') or line.strip()=='{{Nationalmuseum Stockholm cooperation project}}']
    title,_=multilingual_title(wt)
    if title:
        kept=[line for line in kept if not re.match(r'^\s*\|title\s*=',line)]
        kept.append(' |title = '+title)
    out['revisions'][0]['slots']['main']['*']='\n'.join(kept)
    out['projection_note']='Authored descriptions excluded. Original public response and file revision remain captured in research evidence.'
    return out

# Reuse the target writer and its transaction/identity guards, substituting
# independent Commons evidence for the unavailable museum-hosted image.
nm.verify=verify
attach=nm.attach;core.attach=attach

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--plan',type=Path,action='append',required=True);p.add_argument('--canary',action='store_true');p.add_argument('--limit',type=int,default=1000);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
    lock=(a.run/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    records=[]
    for p in a.plan:
        assert core.sha(p.read_bytes())==json.loads((p.parent/'plan-manifest.json').read_text())['sha256']
        plan=json.loads(p.read_text())['records']
        if a.canary:assert 0<a.limit<=5;plan=plan[:a.limit]
        for target in ('local','cloud'):
            verified=json.loads((p.parent/(target+'-metadata-verified'+('-canary' if a.canary else '')+'.json')).read_text())
            assert {r['targets'][target]['artwork_id'] for r in plan}<={r['artwork_id'] for r in verified['records']}
        records+=plan
    done={k for k,v in core.latest_events(a.run).items() if v['outcome'] in ('prepared','complete','manual_review','failed')}
    rows=[r for r in records if r['targets']['local']['artwork_id'] not in done][:a.limit]
    fetch=common.core.Fetcher(a.run/'commons-evidence');render=common.core.Fetcher(a.run/'rendered-licences')
    for n,r in enumerate(rows,1):
        if time.time()>=a.deadline:break
        aid=r['targets']['local']['artwork_id'];c=dict(r,artwork_id=aid)
        try:
            title=file_title(r['raw']['official_capture']['item'].get('ObjWikimediaLinkTxt'))
            d=common.api(fetch,'commons.wikimedia.org',{'action':'query','titles':title,'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main'})
            pages=list(d.get('query',{}).get('pages',{}).values())
            if len(pages)!=1 or not pages[0].get('imageinfo'):raise ValueError('Museum-linked Commons file unavailable')
            page=pages[0];rendered=common.rendered_rights_uri(render,page)
            c['rendered_identity_evidence']=rendered_identity(render,page)
            c['creator_alias_evidence']=creator_alias(fetch,c,page)
            sid='M'+str(page['pageid']);sdc=common.api(fetch,'commons.wikimedia.org',{'action':'wbgetentities','ids':sid,'props':'claims'})['entities'][sid]
            url,credit,pageurl=verify_file(c,page,rendered,sdc)
            projected=project_file(page);raw={'lead':r['raw']['lead'],'official_capture':project_capture(r['raw']['official_capture']),'commons_file':projected,'structured_data':sdc}
            im=dict(r,raw=raw,provider=PROVIDER,scheme=nm.SCHEME,artwork_id=aid,slug=r['targets']['local']['slug'],target_ids={t:v['artwork_id'] for t,v in r['targets'].items()},
                source_record_url=r['page'],source_name=core.PROVIDERS[PROVIDER],source_object_id=r['external_id'],page=pageurl,source_image_url=url,policy_url=nm.PDM,rights_status='public_domain',license_label='Public Domain Mark 1.0',
                creator_credit=credit,attribution_text=f"{r['artist']}. {r['title']}. {credit}. {pageurl}. Public Domain Mark ({nm.PDM}). Full-frame proportional resize and JPEG compression.",
                rendered_licence_evidence=rendered,rendered_identity_evidence=c['rendered_identity_evidence'],creator_alias_evidence=c['creator_alias_evidence'],checked_at=core.now(),rights_verified_at=core.now(),creation_date=r['date_display'])
            im.update(image_url=url,image_license='Public Domain Mark 1.0',image_license_url=nm.PDM,rights_statement='Public Domain Mark 1.0')
            for key in ('photo_credit','media_native_id','rights_error'):im.pop(key,None)
            selected=a.run/'selected'/PROVIDER/(aid+'.json')
            if selected.exists():im=json.loads(selected.read_text())
            verify(im);core.save_new(selected,im);core.worker(PROVIDER,[im],SimpleNamespace(run=a.run,prepare_only=True),None)
        except ValueError as e:core.event(a.run,{'provider':PROVIDER,'artwork_id':aid,'external_id':r['external_id'],'outcome':'manual_review','reason':str(e)})
        if n%10==0:print(core.now(),'Nationalmuseum Commons',n,'of',len(rows),dict(core.COUNTS),flush=True)

if __name__=='__main__':main()
