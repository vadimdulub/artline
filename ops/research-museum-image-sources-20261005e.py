#!/usr/bin/env python3
"""Extract museum image-source links from checksum-verified catalogue captures.

No image binary is requested, downloaded, attached, relicensed or published.
Candidates are keyed by exact museum record URL, never by similar titles.
"""
import collections
import gzip
import importlib.util
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-artwork-locations-20261004.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
DEST=r.ROOT/'docs/research/museum-guides-20261005'


def canonical(url):
    if not isinstance(url,str) or not url.startswith(('https://','http://')):return None
    u=urlsplit(url);host=u.netloc.lower().removeprefix('www.');path=u.path.rstrip('/').replace('%3A',':').replace('%3a',':')
    if host=='collections.louvre.fr':path=path.removeprefix('/en').removesuffix('.json')
    if host=='open.smk.dk':path=path.replace('/artwork/image/','/artwork/')
    if host=='purl.thewalters.org':host='art.thewalters.org';path=path.replace('/art/','/object/')
    return urlunsplit(('https',host,path,u.query,''))


def add(index,page,rc,kind,image_url=None,credit=None,rights=None,source_details=None):
    key=canonical(page)
    if not key:return
    if image_url and not image_url.startswith('https://'):return
    item={'source_page_url':page,'image_url':image_url,'kind':kind,'credit':credit,'source_rights':rights,
        'source_receipt':rc,'source_details':source_details,
        'rights_review':'Source metadata only. A visible image or museum clearance flag is not permission for Artline to reuse it.',
        'no_image_downloaded':True}
    old=index.get(key)
    priority={'catalogue_reports_no_image':0,'catalogue_reports_image':1,'direct_catalogue_image':2}
    if old is None or (priority[kind],rc['retrieved_at'])>(priority[old['kind']],old['source_receipt']['retrieved_at']):index[key]=item


def capture_data(path):
    rc=r.load(path)
    if rc['status']!=200:return None,None
    raw=gzip.decompress((r.ROOT/rc['body_path']).read_bytes());assert r.sha(raw)==rc['sha256'],str(path)
    return raw,rc


def build(label):
    index={};counts=collections.Counter();errors=[]
    folders=['joconde','joconde-alias-20261005b','marseille-current-20261005b',
        'louvre-selected-json-20261005c','whitney-20261005','colombia-object-json-20261005b',
        'smk','smk-current-title-20261005b','smk-creator-refinement-20261005b',
        'met-selected-catalogue-20261005c','tate-current-api-20261005e',
        'rijks-discovery-20261005b','rijks-20261005','walters','saam']
    for folder in folders:
        n=0
        for path in sorted((r.RUN/folder).glob('*.receipt.json')):
            raw,rc=capture_data(path)
            if rc is None:continue
            try:
                if folder in ['joconde','joconde-alias-20261005b','marseille-current-20261005b']:
                    for o in json.loads(raw)['data']:
                        if o.get('Presence_image') in [True,False]:
                            add(index,'https://pop.culture.gouv.fr/notice/joconde/'+o['Reference'],rc,
                                'catalogue_reports_image' if o['Presence_image'] else 'catalogue_reports_no_image',
                                rights={'artist_under_rights':o.get('Artiste_sous_droits'),'public_domain_entry_date':o.get('Date_entree_dans_le_domaine_public')},
                                source_details={'record_id':o['Reference'],'title':o.get('Titre'),'image_present_flag':o['Presence_image'],'source_updated_at':o.get('Date_de_mise_a_jour')})
                elif folder.startswith('louvre'):
                    o=json.loads(raw);imgs=sorted(o.get('image',[]),key=lambda v:v.get('position',999))
                    if imgs:
                        img=imgs[0];add(index,o['url'],rc,'direct_catalogue_image',img['urlImage'],img.get('copyright'),
                            source_details={'record_id':o['arkId'],'title':o.get('title'),'view':img.get('type')})
                elif folder.startswith('whitney'):
                    o=json.loads(raw)['data']['attributes'];imgs=o.get('images')or[]
                    if imgs:add(index,'https://whitney.org/collection/works/'+str(o['id']),rc,'direct_catalogue_image',imgs[0]['url'],source_details={'record_id':o['id'],'title':o['title']})
                elif folder.startswith('colombia'):
                    o=json.loads(raw)['item'];imgs=[v for v in o.get('imagenes',[])if v.get('principal')]
                    if len(imgs)==1 and o.get('imagen_principal')==imgs[0].get('imagen'):
                        img=imgs[0];add(index,'https://colecciones.museonacional.gov.co/objeto/'+o['id_objeto'],rc,'direct_catalogue_image',
                            urljoin('https://colecciones.museonacional.gov.co/',img['imagen']),img.get('credito'),
                            {'museum_rights_flag':img.get('tiene_derechos'),'restriction':img.get('mensaje_restriccion')},
                            {'record_id':o['id_objeto'],'inventory':o['numero_registro'],'title':o['titulo']})
                elif folder.startswith('smk'):
                    for o in json.loads(raw).get('items',[]):
                        img=o.get('image_native') or o.get('image_thumbnail')
                        if o.get('has_image')and img:
                            add(index,o.get('frontend_url') or 'https://open.smk.dk/artwork/image/'+o['object_number'],rc,'direct_catalogue_image',img,
                                rights=o.get('rights'),source_details={'record_id':o['object_number'],'titles':o.get('titles')})
                elif folder.startswith('met'):
                    o=json.loads(raw)
                    if o.get('primaryImage'):add(index,o['objectURL'],rc,'direct_catalogue_image',o['primaryImage'],
                        rights={'public_domain':o.get('isPublicDomain'),'rights_and_reproduction':o.get('rightsAndReproduction')},
                        source_details={'record_id':o['objectID'],'inventory':o.get('accessionNumber'),'title':o['title']})
                elif folder.startswith('tate'):
                    for o in json.loads(raw).get('items',[]):
                        imgs=o.get('master_images')or[]
                        if imgs:
                            img=imgs[0];sizes=img.get('sizes')or[];url=sizes[-1][2] if sizes else img.get('default_url')
                            if url:add(index,o['url'],rc,'direct_catalogue_image',url,img.get('copyright'),
                                {'museum_status':o.get('masterImageStatus'),'museum_cc_label':o.get('masterImageCC'),'protected':img.get('protected')},
                                {'inventory':o['acno'],'title':o.get('title')})
                elif folder.startswith('rijks'):
                    if b'<rdf:RDF'not in raw[:1000]:continue
                    root=ET.fromstring(raw);ns={'ore':'http://www.openarchives.org/ore/terms/','edm':'http://www.europeana.eu/schemas/edm/'};rdf='{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'
                    for agg in root.findall('ore:Aggregation',ns):
                        page=agg.find('edm:isShownAt',ns);img=agg.find('edm:isShownBy',ns);rights=agg.find('edm:rights',ns)
                        if page is not None and img is not None:add(index,page.get(rdf+'resource'),rc,'direct_catalogue_image',img.get(rdf+'resource'),rights=rights.get(rdf+'resource')if rights is not None else None)
                elif folder in ['walters','saam']:
                    soup=BeautifulSoup(raw,'html.parser');page=soup.find('meta',property='og:url');img=soup.find('meta',property='og:image')
                    if page and img:
                        url=img.get('content','')
                        if (folder=='walters' and '/images/art/'in url) or (folder=='saam' and 'ids.si.edu/'in url):
                            add(index,page['content'],rc,'direct_catalogue_image',url,source_details={'image_identity_basis':'museum object page explicitly identifies this sharing image'})
                n+=1
            except (KeyError,TypeError,ValueError,ET.ParseError) as exc:
                errors.append({'receipt':str(path.relative_to(r.ROOT)),'error':str(exc)[:200]})
        counts[folder]=n
        print('Image source metadata',folder,n,'indexed pages',len(index),flush=True)
    r.save_gz(DEST/(label+'.json.gz'),{'at':r.now(),'by_object_url':index,'source_counts':dict(counts),'parser_holds':errors,
        'scope':'Only exact museum object URLs may join these image sources to catalogue artworks. Links are research evidence, not downloaded assets or reuse approvals.'})
    print('Image source index',len(index),collections.Counter(v['kind']for v in index.values()),'parser holds',len(errors),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('label');build(parser.parse_args().label)
