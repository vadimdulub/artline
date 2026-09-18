#!/usr/bin/env python3
"""Keep artwork public-domain and photographer CC licence evidence distinct.

Accept only an identified photographer's explicit self licence, present in both
the exact source revision and its rendered licence block. Never rewrite source
API captures or treat a photograph licence as clearance for protected artwork.
"""
import importlib.util
from pathlib import Path
import re
from urllib.parse import urlencode
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
c=module('campaign','italy-image-campaign.py')
w=module('commons','overnight-commons-images.py')
SELF=re.compile(r'\{\{\s*self\s*\|\s*cc-(by(?:-sa)?)-(1\.0|2\.0|2\.5|3\.0|4\.0)\s*\}\}',re.I)

def source_terms(record,page):
    meta=page.get('imageinfo',[{}])[0].get('extmetadata',{})
    field=lambda k:meta.get(k,{}).get('value','')
    text=page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
    if field('LicenseShortName')!='Public domain' or field('Copyrighted')!='False' or field('LicenseUrl') or field('Restrictions'):
        raise ValueError('This interpretation requires the exact mixed artwork/photo rights case')
    if not re.search(r'\{\{\s*(?:own|sf)\s*\}\}',text,re.I) or not re.search(r'\{\{\s*PD-Art(?:\||-)',text,re.I):
        raise ValueError('Own photograph and underlying public-domain artwork evidence required')
    licences={(a.lower(),b) for a,b in SELF.findall(text)}
    if len(licences)!=1 or not w.photographic_credits(record,page):
        raise ValueError('A unique explicit photographer self licence and credit are required')
    if not record['creators'] or any(a.get('role')!='primary' or not a.get('death') or a['death']+70>=2026 for a in record['creators']):
        raise ValueError('Photograph licence does not independently clear the artwork')
    code,version=next(iter(licences))
    return 'CC '+code.upper()+' '+version,'https://creativecommons.org/licenses/'+code+'/'+version+'/'

def validate(record,page,evidence):
    label,uri=source_terms(record,page)
    revision=page['revisions'][0]['revid']
    if evidence.get('kind')!='explicit_photographic_licence' or evidence.get('pageid')!=page['pageid'] or evidence.get('revid')!=revision:
        raise ValueError('Photographic licence proof refers to a different revision/object')
    if evidence.get('label')!=label or evidence.get('uri')!=uri:
        raise ValueError('Photographic licence label/URI differs from exact self declaration')
    path=(ROOT/evidence['rendered_capture_path']).resolve()
    if not path.is_relative_to(c.RUN.resolve()) or c.core.sha(path.read_bytes())!=evidence['capture']['sha256']:
        raise ValueError('Rendered photographic licence capture checksum/path differs')
    parsed=c.load(path)['parse']
    if parsed.get('pageid')!=page['pageid'] or parsed.get('revid')!=revision:
        raise ValueError('Rendered licence identity/revision differs')
    soup=BeautifulSoup(parsed.get('text',{}).get('*',''),'html.parser')
    uris={w.canonical_licence_uri(n.get_text(strip=True)) for n in soup.select('.licensetpl_link') if n.get_text(strip=True)}
    if uris!={w.PDM,uri}:
        raise ValueError('Exact photographic and underlying-artwork licence blocks not established')
    return label,uri

def resolve(fetcher,record,page):
    label,uri=source_terms(record,page)
    params={'action':'parse','oldid':page['revisions'][0]['revid'],'prop':'text|revid'}
    w.api(fetcher,'commons.wikimedia.org',params)
    url='https://commons.wikimedia.org/w/api.php?'+urlencode(dict(params,format='json',maxlag=5))
    key=c.core.sha(url.encode());path=fetcher.cache/(key+'.json')
    proof={'kind':'explicit_photographic_licence','pageid':page['pageid'],
        'revid':page['revisions'][0]['revid'],'label':label,'uri':uri,
        'rendered_capture_path':str(path.relative_to(ROOT)),
        'capture':c.load(fetcher.cache/(key+'.receipt.json')),
        'interpretation':'Source summary describes public-domain artwork; the identified photographer separately offers this explicit CC licence. Original source metadata preserved without modification.'}
    validate(record,page,proof)
    return proof
