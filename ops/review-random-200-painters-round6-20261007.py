#!/usr/bin/env python3
"""Flag source qualifications for individual review; never approve images automatically."""
import argparse
import collections
import importlib.util
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('round_six',ROOT/'ops/run-random-200-round6-20261007.py')
x=importlib.util.module_from_spec(sp);sp.loader.exec_module(x)
r=x.r;RUN=x.RUN


def scan(final=False):
    plans=list(x.d.plans());issues=[];title_candidates=[];architectural=[]
    for data,pin in plans:
        artist=data['artist'];pre=r.load(x.BACKUP/'selection-preimages'/(artist['id']+'.json.gz'))['records']
        for row in data['rows']:
            if row['action'] not in ['create','existing']:continue
            aid=row['artwork_id'];date=x.s.source_date(row['page']);creators=pre.get(aid,{}).get('creators',[]);flags=[]
            if date and ((artist.get('birth_year') and date['creation_year_end']<artist['birth_year']) or (artist.get('death_year') and date['creation_year_start']>artist['death_year'])):flags.append('outside_creator_lifespan')
            elif date and artist.get('birth_year') and date['creation_year_end']<artist['birth_year']+12:flags.append('source_before_age_twelve_requires_identity_review')
            if any(re.search(r'\b(follower|circle|workshop|school of|attributed|copy|after|entourage|atelier|suiveur|attribu|kopie|nach)\b',c.get('attribution_note') or '',re.I) for c in creators):flags.append('qualified_existing_creator')
            base={'artist':artist['display_name'],'artist_id':artist['id'],'artwork_id':aid,'title':row['title'],'action':row['action'],'source_url':row['source_url'],'date':date,'source_fields':row['page']['fields']}
            if flags:issues.append({**base,'flags':flags,'lifespan':[artist.get('birth_year'),artist.get('death_year')],'creators':creators})
            if re.search(r'\b(after|copy|engraving|engraved|workshop|studio|reproduction|detail|fragment|attributed|circle|follower|school of|attribution|detale|detalle)\b',row['title'],re.I):title_candidates.append(base)
            if 'architecture' in str(row['page']['fields'].get('Genre','')).lower():architectural.append(base)
    result={'at':r.now(),'painters':len(plans),'lifespan_or_qualified_creator':issues,'title_review_candidates':title_candidates,'architectural_version_candidates':architectural,'policy':'Anomaly flags require source/version review; a creator’s lifetime is not the artwork eligibility cutoff. Preserve source values and qualified copies/studies. No automatic publication, date correction or creator reassignment.'}
    if final:
        assert len(plans)==len(x.m.cohort());r.save(RUN/'quality-final-candidates.json',result)
    else:x.m.status('quality-candidates',**{k:v for k,v in result.items() if k!='at'})
    print('Quality candidates:',len(plans),'painters;',len(issues),'lifespan/creator flags;',len(title_candidates),'title qualifications;',len(architectural),'architecture versions',flush=True)


def additional_image_audit():
    """Compare against scoped existing images and the verified Otto Dix delivery."""
    assert len(list((RUN/'image-audits').glob('*.json')))==len(x.m.cohort())
    bysha=collections.defaultdict(dict);existing={}
    for pair in x.m.cohort():
        for row in r.load(RUN/'catalogue-works'/(pair['artist']['id']+'.json.gz')):
            digest=row.get('existing_image_sha256')
            if digest:
                existing[row['id']]=row
                bysha[digest][row['id']]={'artwork_id':row['id'],'artist':pair['artist']['display_name'],'title':row['title'],'source_url':row.get('existing_image_source'),'reference':'Scoped production baseline image'}
    folder=ROOT/'docs/research/otto-dix-20261006';path=folder/'image-delivery-plan.json'
    assert r.sha(path.read_bytes())==r.load(folder/'image-delivery-plan-pin.json')['sha256']
    verification=r.load(folder/'image-verification.json');assert not verification['errors']
    old=r.load(path)['images'];assert len(old)==verification['database_images_verified']
    for im in old:
        for digest in {im['sha256'],im['download']['sha256']}:
            bysha[digest][im['artwork_id']]={'artwork_id':im['artwork_id'],'artist':'Otto Dix','title':im['title'],'source_url':im['source_page_url'],'reference':'Verified Otto Dix delivery'}
    images=[r.load(p) for p in (RUN/'prepared-images').glob('*.json')];ready=[im for im in images if im['outcome']=='prepared'];matches=[];held={}
    for im in ready:
        others={aid:value for digest in {im['sha256'],im['download']['sha256']} for aid,value in bysha[digest].items() if aid!=im['artwork_id']}
        if others:
            matches.append({'artwork_id':im['artwork_id'],'artist':im['artist'],'title':im['title'],'source_url':im['source_page_url'],'sha256':im['sha256'],'existing_references':list(others.values())})
            held[im['artwork_id']]='Exact image matches another artwork in the scoped production baseline or the Otto Dix delivery; reconcile object/version identity before attachment or import.'
    r.save(RUN/'additional-image-reference-audit.json',{'at':r.now(),'selected_prepared_images':len(ready),'existing_baseline_images_compared':len(existing),'otto_dix_images_compared':len(old),'otto_dix_plan_sha256':r.sha(path.read_bytes()),'matches':matches,'held_artwork_ids':held,'scope':'In-memory comparison of preserved source-scoped evidence. No global artwork/media scan and no independent claim that different impressions are the same object.'})
    print('Additional image references:',len(existing),'baseline images;',len(old),'Otto Dix images;',len(held),'holds',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--final',action='store_true');parser.add_argument('--additional-image-audit',action='store_true');args=parser.parse_args()
    if args.additional_image_audit:additional_image_audit()
    else:scan(args.final)
