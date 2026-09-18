#!/usr/bin/env python3
"""Prepare only selected, licensed images; preserve metadata when images fail."""
import hashlib, importlib.util, json, re
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('research',Path(__file__).with_name('research-wikimedia-catalogues.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

def plain(text):return BeautifulSoup(text,'html.parser').get_text(' ',strip=True)

def rendered_object_qid(qid,html):
    # Restrict to the object-title field. A creator/depictee link elsewhere on
    # the page is not proof of the physical artwork identity.
    return bool(BeautifulSoup(html or '', 'html.parser').find('a',href=re.compile(r'^https?://www\.wikidata\.org/(?:wiki|entity)/'+re.escape(qid)+r'(?:$|[#/])')))

def image_credit(meta):
    """Preserve photograph/source attribution alongside the depicted artist."""
    field=lambda k:meta.get(k,{}).get('value','')
    artist=plain(field('Artist'));assert artist,'Missing creator/photographer credit'
    parts=[artist]
    for key,label in [('Credit','Source credit'),('Attribution','Required attribution')]:
        html=field(key);value=plain(html)
        if value and value.casefold() not in ('own work','self-made') and value not in artist:
            assert len(value)<=2000,'Source credit requires individual review'
            parts.append(label+': '+value)
    return '; '.join(parts)

def check_rights_chronology(record,licence,wikitext):
    """Hold concrete contradictions in generic life-based Commons tags.

    This is not a universal copyright determination. Country-specific grounds
    and explicit permission evidence require their own preserved source review.
    """
    death=r.year(record['creator_entity'],'P570')
    if death is None:return
    year=datetime.now(timezone.utc).year
    if licence!='Public domain':
        if death+70>=year and re.search(r'\{\{\s*Art Photo\b|\bphoto license\s*=',wikitext,re.I) and not re.search(r'\b(?:artwork|art) license\s*=\s*\{\{|PermissionTicket|PermissionOTRS',wikitext,re.I):
            raise ValueError('Photograph licence does not establish underlying artwork permission; documented artist death requires individual rights evidence')
        return
    if re.search(r'PD-old-100(?:-|\b)',wikitext,re.I) and death+100>=year:
        raise ValueError('Commons life-plus100 tag contradicts documented creator death; retain metadata, defer image rights')
    if death+70>=year and re.search(r'\{\{\s*PD-(?:Art|old)',wikitext,re.I) and not re.search(r'PD-RusEmpire|PermissionTicket|PermissionOTRS',wikitext,re.I):
        raise ValueError('Generic life-based public-domain tag needs individual rights review against documented creator death')

def main():
    records={};conflicts={}
    for path in sorted((r.RUN/'selected').glob('*.json')):
        for record in json.loads(path.read_text())['selected']:
            if record['qid'] in records:
                old=records[record['qid']]
                if old['collection']['qid']!=record['collection']['qid']:
                    conflicts.setdefault(record['qid'],set()).update([old['collection']['institution']['slug'],record['collection']['institution']['slug']])
                    # Existing catalogue provenance is preserved for image-only
                    # enrichment. Otherwise leave conflicting discoveries out.
                    if old.get('existing_local') and not record.get('existing_local'):continue
                    if not old.get('existing_local') and record.get('existing_local'):records[record['qid']]=record;continue
                    continue
            records[record['qid']]=record
    conflict_report={q:sorted(v) for q,v in conflicts.items()}
    if conflict_report:
        path=r.RUN/('collection-conflicts-'+r.core.sha(r.core.encode(conflict_report))[:12]+'.json')
        r.core.save_new(path,conflict_report)
    fetcher=r.core.Fetcher(r.RUN/'captures')
    fetcher.session.headers['User-Agent']=r.SESSION.headers['User-Agent']
    r.core.HOSTS.add('thumb.wikimedia.org')
    outcomes={}
    for qid,record in records.items():
        output=r.RUN/'ready'/(qid+'.json')
        if output.exists():continue
        if qid in conflicts and not record.get('existing_local'):
            print(qid,'conflicting_collection_deferred',flush=True);continue
        record['date']=r.date(record['entity'])
        cached=r.RUN/'prepared'/(qid+'.json')
        if cached.exists():
            previous=json.loads(cached.read_text())
            if previous['image'] or previous['image_outcome']!='date_requires_review' or not record['date']['eligible']:
                previous['record']=record;r.core.save_new(output,previous);continue
        result={'record':record,'image':None,'image_outcome':'date_requires_review'}
        if record['date']['eligible']:
            try:
                filename=record['images'][0]
                if re.search(r'\b(detail|detailled|collage|montage)\b',filename,re.I):raise ValueError('Detail or composite image requires manual review')
                data,receipt=r.fetch('https://commons.wikimedia.org/w/api.php?'+urlencode({'action':'query','format':'json','titles':'File:'+filename,'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':1280,'rvprop':'ids|content','rvslots':'main','maxlag':5}))
                pages=list(data['query']['pages'].values());assert len(pages)==1 and 'imageinfo' in pages[0]
                page=pages[0];info=page['imageinfo'][0];meta=info['extmetadata'];field=lambda k:meta.get(k,{}).get('value','')
                licence=field('LicenseShortName');licences={'Public domain':'public_domain','CC0':'cc0','CC BY 3.0':'cc_by','CC BY 4.0':'cc_by','CC BY-SA 3.0':'cc_by_sa','CC BY-SA 4.0':'cc_by_sa','CC BY 2.0':'cc_by','CC BY-SA 2.0':'cc_by_sa','CC BY-SA 2.5':'cc_by_sa'}
                assert licence in licences and not field('Restrictions'),'Unresolved per-file rights'
                if licence=='Public domain':assert field('Copyrighted')=='False'
                policy='https://creativecommons.org/publicdomain/mark/1.0/' if licence=='Public domain' else field('LicenseUrl')
                assert policy.startswith('https://creativecommons.org/')
                credit=image_credit(meta)
                wikitext=page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
                check_rights_chronology(record,licence,wikitext)
                # P18 is the primary exact entity-to-file link. Independent file
                # page identity confirmation avoids blindly trusting that link.
                identity_qid=bool(re.search(r'\b'+re.escape(qid)+r'\b',wikitext)) or rendered_object_qid(qid,field('ObjectName'))
                object_name=plain(field('ObjectName'))
                title_match=r.norm(object_name) in {r.norm(t) for t in record['titles']}
                accession_match=bool(record['accession'] and record['accession'] in wikitext)
                assert identity_qid or title_match or accession_match,'File identity needs manual review'
                original=info['size']<=20_000_000 and info['width']*info['height']<=40_000_000
                url=info['url'] if original else info.get('thumburl')
                assert url and urlparse(url).hostname in {'upload.wikimedia.org','thumb.wikimedia.org'}
                rawpath=r.BACKUPS/'selected-originals'/(qid+('.original' if original else '.commons-thumbnail'))
                download_path=r.RUN/'image-receipts'/(qid+'.json')
                if rawpath.exists():
                    raw=rawpath.read_bytes();download=json.loads(download_path.read_text());assert r.core.sha(raw)==download['sha256']
                else:
                    raw,headers=fetcher.get(url,20_000_000)
                    if original:assert hashlib.sha1(raw).hexdigest()==info['sha1'] and len(raw)==info['size']
                    download={'url':url,'sha256':r.core.sha(raw),'bytes':len(raw),'retrieved_at':r.core.now(),'kind':'commons_original' if original else 'commons_thumbnail','original_sha1':info['sha1'],'headers':headers}
                    r.core.save_new(rawpath,raw);r.core.save_new(download_path,download)
                data,width,height,quality=r.core.compress(raw)
                checksum=r.core.sha(data);path=f'/assets/artworks/imported/wikimedia-catalogue/{qid.lower()}-{checksum[:16]}.jpg'
                r.core.save_new(r.ROOT/'apps/web/public'/path.lstrip('/'),data)
                attribution=f"{record['creator_label']}. {record['title']}. Image credit: {credit}. Wikimedia Commons. {licence} ({policy}). Resized and JPEG-compressed; selected source frame preserved."
                result['image']={'path':path,'sha256':checksum,'bytes':len(data),'width':width,'height':height,'quality':quality,'rights_status':licences[licence],'license_label':licence,'license_url':policy,'creator_credit':credit,'attribution_text':attribution,'source_page_url':info['descriptionurl'],'source_image_url':url,'commons_page':page,'commons_receipt':receipt,'download':download,'checked_at':r.core.now(),'identity_basis':{'wikidata_P18':filename,'commons_work_qid':identity_qid,'commons_title':title_match,'commons_accession':accession_match}}
                result['image_outcome']='prepared'
            except (AssertionError,ValueError,RuntimeError,r.requests.RequestException) as error:
                result['image_outcome']='metadata_retained_image_deferred'
                result['image_reason']=str(error)[:400]
        r.core.save_new(output,result)
        outcomes[result['image_outcome']]=outcomes.get(result['image_outcome'],0)+1
        print(qid,result['image_outcome'],record['title'][:65],flush=True)
    print('New preparation outcomes',outcomes,flush=True)

if __name__=='__main__':main()
