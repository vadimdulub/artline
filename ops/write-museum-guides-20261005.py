#!/usr/bin/env python3
"""Write source-linked Markdown guides from a verified read-only snapshot."""
import argparse
import collections
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import quote

spec=importlib.util.spec_from_file_location('im',Path(__file__).with_name('research-museum-image-sources-20261005e.py'))
im=importlib.util.module_from_spec(spec);spec.loader.exec_module(im);r=im.r;ROOT=im.DEST
UNAVAILABLE_MEDIA=set()


def escape(value):
    return re.sub(r'([\\`*\[\]<>|])',r'\\\1',' '.join(str(value or '').split()))


def link(label,url):
    assert isinstance(url,str)and url.startswith(('https://','http://'))
    return '['+escape(label)+']('+quote(url,safe='/:#?=&%+-._~')+')'


def image_match(work,sources,commons):
    media=work.get('media')or{}
    if media.get('id')in UNAVAILABLE_MEDIA:media={}
    path=media.get('storage_path')
    if media.get('storage_kind')=='local' and isinstance(path,str)and path.startswith('/assets/')and '..'not in Path(path).parts:
        return 'existing_image',{'url':'https://artlines.org'+path,'media':media}
    if media.get('storage_kind')=='remote'and (media.get('delivery_url')or'').startswith('https://'):
        return 'existing_image',{'url':media['delivery_url'],'media':media}
    urls=[work['source_url']]+[v.get('canonical_url')for v in work.get('identifiers',[])]
    matches=[sources[im.canonical(url)]for url in urls if im.canonical(url)in sources]
    direct=[v for v in matches if v['kind']=='direct_catalogue_image']
    if direct:return 'direct_catalogue_image',direct[0]
    if work['id']in commons:return 'secondary_depiction_candidate',commons[work['id']]
    available=[v for v in matches if v['kind']=='catalogue_reports_image']
    if available:return 'catalogue_reports_image',available[0]
    if matches:return 'catalogue_reports_no_image',matches[0]
    return 'image_research_pending',None


def picture(work,kind,obj):
    if kind=='existing_image':
        m=obj['media'];value=link('Artline picture',obj['url'])+' · '+escape(m.get('rights_status','unknown'))
        credit=m.get('source_page_url')or m.get('license_url')
        if credit and credit.startswith(('https://','http://')):value+=' · '+link('source / credit',credit)
        return value
    if kind=='direct_catalogue_image':
        value=link('Museum picture',obj['image_url'])+' · '+link('source',obj['source_page_url'])
        if obj.get('credit'):value+=' · '+escape(obj['credit'])
        return value+' · reuse review'
    if kind=='secondary_depiction_candidate':
        return link('Image candidate',obj['image_url'])+' · '+link('Commons credit / licence',obj['source_page_url'])+' · identity review'
    if kind=='catalogue_reports_image':return link('Catalogue image page',obj['source_page_url'])+' · catalogue reports image'
    if kind=='catalogue_reports_no_image':return 'Catalogue reports no image · '+link('record',work['source_url'])
    return 'Image research pending · '+link('record',work['source_url'])


def table(works,matches):
    lines=['| Artwork | Creator / attribution | Date as recorded | Picture link | Museum holding evidence | Editorial state |',
        '| --- | --- | --- | --- | --- | --- |']
    for w in works:
        artists='; '.join(v['name']+(' ('+v['role']+')'if v.get('role')not in [None,'artist','primary'] else '')for v in w['artists'])or w.get('unlinked_creator_label')or'Unknown'
        kind,obj=matches[w['id']]
        title='<a id="artwork-'+w['id']+'"></a>'+escape(w['title'])
        source=link('Holding source',w['source_url'])+' · checked '+str(w['checked_at'])[:10]
        lines.append('| '+' | '.join([title,escape(artists),escape(w.get('date_display')or'Unknown'),picture(w,kind,obj),source,escape(w['status'])])+' |')
    return '\n'.join(lines)+'\n'


def write(snapshot,image_sources,rebuild=False):
    global UNAVAILABLE_MEDIA
    check=ROOT/'missing-local-assets-live-check.json'
    UNAVAILABLE_MEDIA={v['media_id']for v in r.load(check)['assets']if v.get('status')==404}if check.exists()else set()
    manifest=r.load(ROOT/'snapshots'/snapshot/'manifest.json')
    sources=r.load(ROOT/(image_sources+'.json.gz'))['by_object_url']
    commons_path=ROOT/'commons-image-candidates.json.gz'
    commons=r.load(commons_path)['by_artwork_id']if commons_path.exists()else{}
    totals=collections.Counter();museums=[];files=[];associations=[]
    def derivative(relative,raw):
        path=ROOT/relative
        if path.exists()and path.read_bytes()!=raw:
            assert rebuild,'Pass --rebuild to revise generated guides; primary captures remain immutable'
            r.save(ROOT/'revisions/before-broken-image-link-fix'/relative,path.read_bytes())
            temporary=path.with_name(path.name+'.partial');temporary.write_bytes(raw);temporary.replace(path)
        else:r.save(path,raw)
    def save(relative,body):
        path=ROOT/relative;derivative(relative,body.encode());files.append({'path':relative,'sha256':r.sha(path.read_bytes()),'bytes':path.stat().st_size})
    for entry in manifest['museums']:
        source=ROOT/entry['path'];assert r.sha(source.read_bytes())==entry['sha256']
        data=r.load(source);inst=data['institution'];slug=inst['slug'];works=data['artworks']
        assert re.fullmatch(r'[a-z0-9-]+',slug),slug
        works=sorted(works,key=lambda w:(r.norm(w['title']),w['id']))
        matches={w['id']:image_match(w,sources,commons)for w in works};counts=collections.Counter(kind for kind,obj in matches.values());totals.update(counts)
        for w in works:
            kind,obj=matches[w['id']]
            if kind in ['direct_catalogue_image','secondary_depiction_candidate','catalogue_reports_image']:
                associations.append({'artwork_id':w['id'],'slug':w['slug'],'title':w['title'],'museum_id':inst['id'],'museum_name':inst['name'],
                    'holding_source_url':w['source_url'],'image_kind':kind,'image_evidence':obj})
        header=['# '+escape(inst['name']),'','[All museums and collections](../README.md)','',
            f"{len(works):,} accepted holding links · {counts['existing_image']:,} existing Artline pictures · {counts['direct_catalogue_image']:,} direct museum picture links · {counts['secondary_depiction_candidate']:,} Commons candidates · {counts['catalogue_reports_image']:,} catalogue image pages.",'',
            'Institution type: '+escape(inst['kind'])+'. Institution editorial state: '+escape(inst['status'])+'.',
            '','Snapshot: '+data['captured_at']+'. Holding evidence does not establish current display or physical presence. Artwork dates, creator attributions and editorial review states are preserved.',
            '', 'External pictures are research links. Their availability does not establish permission to download, reuse or publish them. Commons candidates also require image-identity review. Full source receipts, image credits and recorded rights are preserved in the linked research manifest.','']
        if inst.get('website_url'):header.extend([link('Museum / collection website',inst['website_url']),''])
        if slug=='museo-del-prado':header.extend(['Source freshness: some accepted Prado links were corroborated using a March 2026 catalogue dataset in the preceding research round. The checked date is a research date, not confirmation of present physical location.',''])
        if slug=='state-russian-museum':header.extend(['Image-source freshness: many external picture links come from preserved official collection listings captured in September 2026. Museum reproduction restrictions remain in force.',''])
        if len(works)<=500:
            body='\n'.join(header)+table(works,matches)
        else:
            header.extend(['## Artworks and pictures',''])
            for offset in range(0,len(works),500):
                page=offset//500+1;relative=f'museums/{slug}/artworks-{page:03d}.md';part=works[offset:offset+500]
                page_body='# '+escape(inst['name'])+f' — artworks {offset+1:,}–{offset+len(part):,}\n\n[Back to museum](../'+slug+'.md) · [All museums](../../README.md)\n\n'
                page_body+='Holding links do not confirm current display. External images require reuse review; Commons images also require identity review.\n\n'+table(part,matches)
                save(relative,page_body)
                header.append(f'- [Artworks {offset+1:,}–{offset+len(part):,}]({slug}/artworks-{page:03d}.md) — '+escape(part[0]['title'])+' → '+escape(part[-1]['title']))
            body='\n'.join(header)+'\n'
        save('museums/'+slug+'.md',body)
        museums.append({'id':inst['id'],'slug':slug,'name':inst['name'],'kind':inst['kind'],'artworks':len(works),'pictures':dict(counts),'path':'museums/'+slug+'.md'})
    missing=totals['catalogue_reports_no_image']+totals['image_research_pending']
    intro=['# Museums, artworks and picture links','',
        f"{len(museums):,} museums and other holding institutions · {sum(v['artworks']for v in museums):,} accepted artwork–institution links.",'',
        f"{totals['existing_image']:,} existing Artline picture links; {totals['direct_catalogue_image']:,} direct museum picture links; {totals['secondary_depiction_candidate']:,} Commons image candidates; {totals['catalogue_reports_image']:,} catalogue pages that report an image. {missing:,} artworks still have no located picture link in this export.",'',
        'This is a research index of the real local catalogue. An accepted museum holding does not confirm current display. Review artworks remain in review, and unknown dates or attributions remain unknown. Larger collections have linked pages of 500 artworks.','',
        '“Artline picture” links an existing image asset. “Museum picture” links an image identified by the museum’s catalogue; reuse remains to be reviewed. “Image candidate” follows the artwork’s existing Wikidata identifier to a Commons file and needs visual identity and rights review. “Catalogue image page” means the source catalogue explicitly reports an image, without a verified direct image URL. No images were downloaded or attached by this research round.','',
        '## Major collections','']
    for wanted in ['musee-du-louvre','museo-del-prado','tate','rijksmuseum','musee-dorsay','the-met','national-gallery-of-art','state-russian-museum']:
        museum=next((m for m in museums if m['slug']==wanted),None)
        if museum:intro.append('- ['+escape(museum['name'])+']('+museum['path']+')')
    intro.extend(['','## All museums and holding institutions','',
        '| Museum / holding institution | Artworks | Artline pictures | Direct museum pictures | Commons candidates | Catalogue image pages |',
        '| --- | ---: | ---: | ---: | ---: | ---: |'])
    for m in sorted(museums,key=lambda v:r.norm(v['name'])):
        c=m['pictures'];intro.append('| ['+escape(m['name'])+']('+m['path']+') | '+' | '.join(f'{v:,}'for v in [m['artworks'],c.get('existing_image',0),c.get('direct_catalogue_image',0),c.get('secondary_depiction_candidate',0),c.get('catalogue_reports_image',0)])+' |')
    intro.extend(['','## Evidence and delivery','',
        '- [Snapshot manifest](snapshots/'+snapshot+'/manifest.json)',
        '- [Guide and source manifest](guide-manifest.json)',
        '- [Research and database delivery](RESEARCH-ROUND.md)',''])
    save('README.md','\n'.join(intro))
    import gzip
    derivative('artwork-image-source-associations.json.gz',gzip.compress(json.dumps({'at':r.now(),'associations':associations,'no_asset_changes':True},ensure_ascii=False,default=str).encode(),mtime=0))
    derivative('guide-manifest.json',json.dumps({'at':r.now(),'snapshot':snapshot,'image_sources':image_sources,'source_snapshot_sha256':r.sha((ROOT/'snapshots'/snapshot/'manifest.json').read_bytes()),
        'museum_count':len(museums),'artworks':sum(v['artworks']for v in museums),'pictures':dict(totals),'museums':museums,'markdown_files':files,
        'known_broken_asset_references_excluded':sorted(UNAVAILABLE_MEDIA),'no_images_downloaded_or_attached':True},ensure_ascii=False,sort_keys=True,indent=2).encode())
    print(json.dumps({'museums':len(museums),'artworks':sum(v['artworks']for v in museums),'markdown_files':len(files),'pictures':dict(totals),'new_image_source_associations':len(associations)}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('snapshot');parser.add_argument('image_sources');parser.add_argument('--rebuild',action='store_true');args=parser.parse_args();write(args.snapshot,args.image_sources,args.rebuild)
