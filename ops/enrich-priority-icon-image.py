#!/usr/bin/env python3
"""One exact Athens icon, using an independently licensed Commons photograph."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup
import psycopg
from psycopg.rows import dict_row

spec=importlib.util.spec_from_file_location('rounds',Path(__file__).with_name('run-selected-image-rounds.py'))
rounds=importlib.util.module_from_spec(spec);spec.loader.exec_module(rounds)
core=rounds.core
PROVIDER='athens-commons'
PAGE='https://commons.wikimedia.org/wiki/File:Icon_of_Saint_Michael_in_the_Byzantine_and_Christian_Museum_(Athens).jpg'
CATEGORY='https://commons.wikimedia.org/wiki/Category:Icon_of_Saint_Michael_in_the_Byzantine_and_Christian_Museum_(Athens)'
LICENSE='https://creativecommons.org/licenses/by-sa/4.0/'
ORIGINAL_SHA1='49179ecf55f36a259094262b58437e19e56e456e'
core.VERSION='verified-priority-icon-commons-v1'
core.PROVIDERS[PROVIDER]='Byzantine and Christian Museum, Athens; photograph by Yair-haklai via Wikimedia Commons'


def validate(candidate,raw):
    page=BeautifulSoup(raw['file_html'],'html.parser')
    category=BeautifulSoup(raw['category_html'],'html.parser')
    text=page.get_text(' ',strip=True)
    category_text=category.get_text(' ',strip=True)
    if candidate['external_id']!='63' or candidate['accession_number']!='ΒΧΜ 01353':
        raise ValueError('Wrong museum object')
    if 'ΒΧΜ 01353' not in category_text or 'first half of the 14th century' not in category_text:
        raise ValueError('Exact accession/creation context absent')
    links=[a.get('href','') for a in category.find_all('a')]
    if not any(urlparse(u).hostname=='www.ebyzantinemuseum.gr' and parse_qs(urlparse(u).query).get('id')==['63'] for u in links):
        raise ValueError('Category lacks exact official museum reference')
    if not any(unquote(urlparse(u).path)==urlparse(PAGE).path for u in links):
        raise ValueError('File not in exact museum-object category')
    back=[unquote(urlparse(a.get('href','')).path) for a in page.select('#mw-normal-catlinks a')]
    if urlparse(CATEGORY).path not in back:
        raise ValueError('File lacks exact object category')
    label=page.find(id='fileinfotpl_aut')
    author=label.find_next_sibling('td').get_text(' ',strip=True) if label else ''
    if author!='Yair-haklai' or 'Own work' not in text:
        raise ValueError('Independent photographer identity/source changed')
    licenses={n.get_text(strip=True) for n in page.select('.licensetpl_short')}
    if licenses!={'CC BY-SA 4.0'} or not any(a.get('href','').rstrip('/')==LICENSE.rstrip('/') for a in page.find_all('a')):
        raise ValueError('Current file-level license changed')
    if ORIGINAL_SHA1 not in text:
        raise ValueError('Reviewed original file checksum changed')
    original=page.select_one('.fullImageLink a')
    url=original['href'].split('?',1)[0] if original else ''
    if urlparse(url).hostname!='upload.wikimedia.org' or urlparse(url).scheme!='https':
        raise ValueError('Unexpected original image URL')
    return url


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    args=parser.parse_args();args.run.mkdir(parents=True,exist_ok=True)
    candidates_file=args.run/'candidates.json'
    if not candidates_file.exists():
        with psycopg.connect('postgres://localhost/artline',row_factory=dict_row) as db:
            db.execute('SET TRANSACTION READ ONLY')
            candidates=db.execute('''SELECT a.id::text AS artwork_id,a.title,a.date_display,a.work_type,
              a.creation_year_start,a.creation_year_end,a.accession_number,a.cultural_context,
              a.unlinked_creator_label,e.scheme,e.external_id,e.canonical_url AS page,e.source_id::text
              FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id
              WHERE e.entity_type='artwork' AND e.scheme='european-icons-athens-object' AND e.external_id='63'
              AND a.primary_media_id IS NULL AND a.status='review' AND a.object_form='icon'
              AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
              AND artline_has_selection_evidence(a.id)''').fetchall()
        if len(candidates)!=1:raise ValueError('Expected one existing eligible missing-image icon')
        for c in candidates:
            c.update(provider=PROVIDER,artist=c['unlinked_creator_label']+'; photograph by Yair-haklai')
        core.save_new(candidates_file,{'selected_at':core.now(),'candidates':candidates})
    candidates=json.loads(candidates_file.read_text())['candidates'];c=candidates[0]
    dsn=core.cloud_dsn();targets=[('local','postgres://localhost/artline'),('cloud',dsn)]
    for target,target_dsn in targets:
        path=args.run/(target+'-before.json')
        if not path.exists():core.save_new(path,rounds.snapshot(target_dsn,candidates))
    metadata=args.run/'metadata.json'
    if not metadata.exists():
        fetcher=core.Fetcher(args.run/'metadata')
        file_bytes,file_headers=fetcher.get(PAGE)
        cat_bytes,cat_headers=fetcher.get(CATEGORY)
        core.save_new(metadata,{'file_html':file_bytes.decode(),'category_html':cat_bytes.decode(),
          'file_page':PAGE,'category_page':CATEGORY,'file_sha256':core.sha(file_bytes),'category_sha256':core.sha(cat_bytes),
          'retrieved_at':core.now(),'file_headers':file_headers,'category_headers':cat_headers})
    raw=json.loads(metadata.read_text());url=validate(c,raw)
    selected={**c,'page':PAGE,'source_image_url':url,'raw':raw,'rights_status':'cc_by_sa',
      'license_label':'CC BY-SA 4.0','policy_url':LICENSE,'checked_at':raw['retrieved_at'],
      'commons_original_sha1':ORIGINAL_SHA1,'photographer':'Yair-haklai',
      'photographer_url':'https://commons.wikimedia.org/wiki/User:Yair-haklai',
      'derivative_license':LICENSE,'original_workshop_label':c['unlinked_creator_label'],
      'identity_basis':'Exact Athens object 63 and accession ΒΧΜ 01353 in museum-linked Commons category, reciprocal exact file/category membership, independent own-work photograph by Yair-haklai, explicit CC BY-SA 4.0 and pinned original SHA-1. Original workshop attribution retained; photo date is not artwork creation date.'}
    core.save_new(args.run/'selected'/PROVIDER/(c['artwork_id']+'.json'),selected)
    events=rounds.latest(args.run)
    if events.get(c['artwork_id'],{}).get('outcome')!='complete':
        core.worker(PROVIDER,candidates,SimpleNamespace(run=args.run),dsn)
    event=rounds.latest(args.run).get(c['artwork_id'],{})
    if event.get('outcome')!='complete' or event.get('local')!='attached' or event.get('cloud')!='attached':
        raise ValueError('Priority image attachment incomplete')
    report=args.run/'verification-final.json'
    if not report.exists():
        subprocess.run([sys.executable,str(core.ROOT/'ops/verify-enriched-images.py'),'--run',str(args.run),'--report',str(report)],check=True)
    for target,target_dsn in targets:
        after=rounds.snapshot(target_dsn,candidates)
        if after!=json.loads((args.run/(target+'-before.json')).read_text()):raise ValueError('Icon metadata or attribution changed')
        core.save_new(args.run/(target+'-after.json'),after)
    core.save_new(args.run/'complete.json',{'images':1,'metadata_and_creators_unchanged':True,
      'photographer_credit_preserved':True,'same_derivative_license':LICENSE,'finished_at':core.now()})
    print('Priority icon image verified in both databases',flush=True)


if __name__=='__main__':main()
