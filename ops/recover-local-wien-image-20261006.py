#!/usr/bin/env python3
"""Recover the selected Wien Museum photograph with its native CC BY credit."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import uuid

from bs4 import BeautifulSoup

s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('recover-local-commons-images-20261005.py'))
base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
core=base.core
RUN=core.ROOT/'docs/research/local-wien-native-image-20261006';base.RUN=RUN
PROVIDER='wien-museum-native';core.PROVIDERS[PROVIDER]='Wien Museum'
core.HOSTS.add('sammlung.wienmuseum.at')
core.VERSION='local-wien-exact-native-photograph-v1'
AID='4ba9c01a-2f59-584e-857d-64c08b904da0'
PAGE='https://sammlung.wienmuseum.at/en/object/467916-bertha-mueller-die-schwester-des-kuenstlers/'
IMAGE='https://sammlung.wienmuseum.at/images/objects/467916/2206588_full.jpg'
LICENCE='https://creativecommons.org/licenses/by/4.0/'
CREDIT='Birgit und Peter Kainz, Wien Museum'
SLUG='wien-native-image-recovery-20261006'
SID=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/sources/'+SLUG))


def native_check(im):
    base.original_entity_match(im,im['raw']['wikidata'],require_primary_image=False)
    capture=im['raw']['native_capture'];path=core.ROOT/capture['path']
    if not path.resolve().is_relative_to(RUN.resolve()) or core.sha(path.read_bytes())!=capture['sha256'] or capture['url']!=PAGE:
        raise ValueError('Pinned source page changed')
    soup=BeautifulSoup(path.read_bytes(),'html.parser')
    headings=soup.find_all('h1');inventory=soup.select('[data-inventory-number]')
    if len(headings)!=1 or base.m.norm(headings[0].get_text(' ',strip=True))!=base.m.norm(im['title']):
        raise ValueError('Native title differs')
    if len(inventory)!=1 or inventory[0].get_text(strip=True)!='51369' or not re.fullmatch(r'(?:Inv\. No\. )?51369',im['accession_number']):
        raise ValueError('Native inventory differs')
    labels={d.get_text(' ',strip=True):d.find_next_sibling('dd') for d in soup.find_all('dt')}
    rows=labels['Artists/Producer'].select('tbody tr')
    if len(rows)!=1 or len(im['creators'])!=1 or im['roles']!=['primary']:
        raise ValueError('Native creator is not unique')
    cells=rows[0].find_all('td');name=cells[0].get_text(' ',strip=True)
    if (len(cells)!=2 or cells[1].get_text(strip=True)!='Artist'
            or name!='Leopold Carl Müller (1834—1892)'
            or base.m.norm(im['artist'])!=base.m.norm('Leopold Carl Müller')
            or im['creators'][0]['qid']!='Q640342' or im['creators'][0]['death']!=1892):
        raise ValueError('Native artist authority differs')
    date=labels['Date'].get_text(' ',strip=True)
    if not re.fullmatch(r'around\s+1870\s+–\s+1880',date) or (im['creation_year_start'],im['creation_year_end'],im['date_precision'])!=(1870,1880,'circa_range'):
        raise ValueError('Exact source creation interval differs')
    if 'paintings' not in labels['Classification'].get_text(' ',strip=True) or im['work_type']!='painting':
        raise ValueError('Native object classification differs')
    photos=soup.select('img.object-image')
    if not photos or photos[0].get('data-src')!=IMAGE:
        raise ValueError('Selected source primary photograph differs')
    figure=photos[0].find_parent('figure')
    captions=figure.select('[data-caption]') if figure else []
    if len(captions)!=1 or captions[0].get_text(' ',strip=True)!='CC BY 4.0, Foto: '+CREDIT:
        raise ValueError('Exact photograph licence or credit missing')
    if not soup.find('a',href=LICENCE+'deed.en') or not soup.find('a',href=IMAGE,attrs={'download':True}):
        raise ValueError('Published licence/download mapping missing')
    if (im['artwork_id'],im['page'],im['source_image_url'],im['policy_url'],im['rights_status'],im['license_label'],im['creator_credit'])!=(AID,PAGE,IMAGE,LICENCE,'cc_by','CC BY 4.0',CREDIT):
        raise ValueError('Selected image rights or identity changed')
    if CREDIT not in im['attribution_text'] or LICENCE not in im['attribution_text']:
        raise ValueError('Photograph attribution missing')


def research():
    source=RUN.parent/'local-commons-priority-followup-20261006/selected/night-commons'/(AID+'.json')
    lead=json.loads(source.read_bytes())
    c=next(c for c in json.loads((source.parents[2]/'candidates.json').read_bytes())['candidates'] if c['artwork_id']==AID)
    with base.connect() as db:
        current=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(AID,)).fetchone()['record']
        if current!=c['before_record'] or current['primary_media_id']:raise ValueError('Candidate changed or already has an image')
        baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
    manifest=RUN/'candidates.json'
    if manifest.exists():
        if json.loads(manifest.read_bytes())['candidates']!=[c]:raise ValueError('Pinned selection changed')
    else:core.save_new(manifest,dict(at=core.now(),baseline=baseline,candidates=[c],source_lead=str(source.relative_to(core.ROOT))))
    original=RUN.parent/'local-source-policy-review-20261006/metadata'/(core.sha(PAGE.encode())+'.html')
    capture=json.loads(original.with_suffix('.receipt.json').read_bytes())
    if core.sha(original.read_bytes())!=capture['sha256']:raise ValueError('Source capture checksum differs')
    copied=RUN/'metadata'/original.name;core.save_new(copied,original.read_bytes())
    capture.update(path=str(copied.relative_to(core.ROOT)),copied_from_receipt=str(original.with_suffix('.receipt.json').relative_to(core.ROOT)))
    core.save_new(copied.with_suffix('.receipt.json'),capture)
    im=dict(c,provider=PROVIDER,page=PAGE,source_image_url=IMAGE,policy_url=LICENCE,rights_status='cc_by',license_label='CC BY 4.0',checked_at=core.now(),creator_credit=CREDIT,
        raw=dict(wikidata=lead['raw']['wikidata'],native_capture=capture,discovery_commons_file=lead['page'],licence_decision='Native photograph-specific CC BY 4.0 and photographer credit retained separately from the public-domain underlying artwork.'),
        attribution_text=f"{c['artist']}. {c['title']}, around 1870–1880. Wien Museum, inventory 51369. Photo: {CREDIT}. CC BY 4.0 ({LICENCE}). {PAGE}. Full-frame proportional resize and JPEG compression.")
    native_check(im);core.save_new(RUN/'selected'/PROVIDER/(AID+'.json'),im)
    core.event(RUN,dict(provider=PROVIDER,artwork_id=AID,outcome='rights_selected'))
    print('Verified native Wien Museum photograph and credit',flush=True)


def attach(db,im,target):
    if target!='local':raise ValueError('Only local attachment is authorized')
    native_check(im)
    result=base.m.original_attach(db,im,target)
    if result=='attached':
        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,terms_url) VALUES(%s,%s,'Wien Museum — per-image CC BY 4.0','collection_page','https://sammlung.wienmuseum.at/',%s) ON CONFLICT(slug) DO NOTHING",(SID,SLUG,LICENCE))
        if db.execute('SELECT id::text FROM sources WHERE slug=%s',(SLUG,)).fetchone()['id']!=SID:raise ValueError('Native source identity changed')
        db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
        db.execute('UPDATE media_rights_evidence SET source_id=%s,source_record_id=%s,rights_basis=%s WHERE media_id=%s',
            (SID,'467916/2206588','Exact museum object, inventory, title, artist and creation interval; source primary photograph explicitly CC BY 4.0 with named photographers. Catalogue fields retained.',im['media_id']))
    return result


base.m.attach=attach
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','prepare','apply','verify']);args=p.parse_args()
    if args.phase=='research':research()
    elif args.phase=='prepare':
        for path in (RUN/'selected'/PROVIDER).glob('*.json'):native_check(json.loads(path.read_bytes()))
        base.prepare(PROVIDER)
    elif args.phase=='apply':base.apply()
    else:
        for im in base.prepared():native_check(im)
        base.verify()
