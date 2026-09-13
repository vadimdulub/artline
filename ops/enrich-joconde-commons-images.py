#!/usr/bin/env python3
"""Two reviewed Monet reproductions with exact Joconde/accession identities."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import quote, urlparse
from bs4 import BeautifulSoup
import psycopg
from psycopg.rows import dict_row

spec=importlib.util.spec_from_file_location('research',Path(__file__).with_name('enrich-research-images.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
core=m.core
m.IDENTITY=m.IDENTITY.replace("'smk:'","'joconde:'").replace("r.source_kind='smk'","r.source_kind='joconde'")
m.PROVIDER='joconde-commons'
m.VERSION='verified-joconde-commons-images-v1'
core.VERSION=m.VERSION
core.PROVIDERS[m.PROVIDER]="Musée d'Orsay via Wikimedia Commons"
FILES={
 '000PE003970':{'file':'Carrieres-Saint-Denis-1872.jpg','title':'Carrières-Saint-Denis','year':1872,
   'accession':'RF 1674','sha1':'a65141acf5260e4192946b0c40e70397765149ce'},
 '000PE003943':{'file':"Claude Monet, 1879, Camille sur son lit de mort, oil on canvas, 90 x 68 cm, Musée d'Orsay, Paris.jpg",
   'title':'Camille Monet sur son lit de mort','year':1879,'accession':'RF 1963 3',
   'sha1':'12e89c02381df390b20a52be922d672f68900100'},
}


def normalize(s):
    return ''.join(c for c in unicodedata.normalize('NFD',s.casefold()) if c.isalnum())


def validate(candidate,raw):
    expected=FILES[candidate['external_id']]
    soup=BeautifulSoup(raw['html'],'html.parser')
    def field(key):
        label=soup.find(id=key)
        return label.find_next_sibling('td').get_text(' ',strip=True) if label else ''
    refs=soup.find(id='fileinfotpl_art_references')
    links=[a.get('href','') for a in refs.find_next_sibling('td').find_all('a')] if refs else []
    expected_path='/notice/joconde/'+candidate['external_id']
    if not any(urlparse(u).hostname=='www.pop.culture.gouv.fr' and urlparse(u).path==expected_path for u in links):
        raise ValueError('Commons lacks exact Joconde reference')
    if expected['accession'] not in field('fileinfotpl_art_id') or candidate['facts_json']['accession']!=expected['accession']:
        raise ValueError('Accession mismatch')
    if normalize(expected['title']) not in normalize(field('fileinfotpl_art_title')):
        raise ValueError('Commons title mismatch')
    if not field('fileinfotpl_aut').startswith('Claude Monet ') or 'Monet' not in candidate['artist']:
        raise ValueError('Creator mismatch')
    if not field('fileinfotpl_date').startswith(str(expected['year'])+' ') or not (candidate['creation_year_start']==candidate['creation_year_end']==expected['year']<=1970):
        raise ValueError('Creation date mismatch')
    if "Musée d'Orsay" not in field('fileinfotpl_art_gallery'):
        raise ValueError('Museum object context mismatch')
    rights=[t.get_text(strip=True) for t in soup.select('.licensetpl_short')]
    pdm=soup.find('a',href='https://creativecommons.org/publicdomain/mark/1.0/deed.en')
    if set(rights)!={'Public domain','PDM'} or not pdm or not pdm.find_parent('table',class_='layouttemplate'):
        raise ValueError('No explicit file-level Public Domain Mark')
    original=soup.select_one('.fullImageLink a')
    url=original['href'].split('?',1)[0] if original else ''
    if urlparse(url).hostname!='upload.wikimedia.org' or urlparse(url).scheme!='https':
        raise ValueError('Missing original reproduction URL')
    if expected['sha1'] not in soup.get_text(' ',strip=True):
        raise ValueError('Reviewed original file SHA-1 changed')
    if raw.get('source_image_url')!=url:
        raise ValueError('Original URL changed')


def make_image(c,fetcher,*unused):
    url='https://commons.wikimedia.org/wiki/File:'+quote(FILES[c['external_id']]['file'].replace(' ','_'),safe=",:'")
    path=fetcher.cache/(c['external_id']+'.json')
    if path.exists():raw=json.loads(path.read_text())
    else:
        data,headers=fetcher.get(url)
        soup=BeautifulSoup(data,'html.parser')
        link=soup.select_one('.fullImageLink a')
        if not link:raise ValueError('Commons original file unavailable')
        raw={'html':data.decode(),'url':url,'retrieved_at':core.now(),'html_sha256':core.sha(data),
             'source_image_url':link['href'].split('?',1)[0],'headers':headers}
        core.save_new(path,raw)
    validate(c,raw)
    return {**c,'source_image_url':raw['source_image_url'],'raw':raw,'rights_status':'public_domain',
      'license_label':'Public Domain Mark 1.0','policy_url':core.POLICIES['smk'],
      'checked_at':raw['retrieved_at'],'commons_file_page':url,'commons_original_sha1':FILES[c['external_id']]['sha1'],
      'identity_basis':'Exact Joconde reference and museum accession on current Commons file page; reviewed title variant, Monet attribution and creation year; explicit file-level Public Domain Mark. Research review status retained.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['select','apply','verify'])
    parser.add_argument('--run',type=Path,required=True)
    args=parser.parse_args();args.run.mkdir(parents=True,exist_ok=True)
    args.report='verification-final.json';args.prepare_only=False
    if args.phase=='select':
        with psycopg.connect('postgres://localhost/artline',row_factory=dict_row) as db:
            db.execute('SET TRANSACTION READ ONLY')
            rows=db.execute(m.IDENTITY+' AND r.source_object_id=ANY(%s) AND a.primary_media_id IS NULL', (list(FILES),)).fetchall()
        if len(rows)!=2:raise ValueError('Expected exactly two existing eligible records')
        for c in rows:c.update(provider=m.PROVIDER,scheme='research-artwork-link',artist='Claude Monet')
        core.save_new(args.run/'candidates.json',{'selected_at':core.now(),'candidates':rows})
        m.preflight(args,rows);return
    rows=json.loads((args.run/'candidates.json').read_text())['candidates']
    maps={t:json.loads((args.run/(t+'-identities.json')).read_text()) for t in ['local','cloud']}
    for c in rows:c['targets']={t:maps[t][c['artwork_id']] for t in maps}
    if args.phase=='verify':
        m.validate_current=validate
        m.validate_rights=lambda image:validate(image,image['raw'])
        return m.verify(args,rows)
    core.attach=m.attach;core.image_record=make_image
    core.worker(m.PROVIDER,rows,args,core.cloud_dsn())
    print(dict(core.COUNTS),flush=True)


if __name__=='__main__':main()
