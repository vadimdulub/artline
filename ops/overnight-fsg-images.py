#!/usr/bin/env python3
"""Selected National Museum of Asian Art objects with exact CC0 media evidence."""
import argparse, concurrent.futures, fcntl, importlib.util, json, re, time, uuid
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse, parse_qs
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('fsg_saam_helpers',ROOT/'ops/overnight-saam-images.py');helpers=importlib.util.module_from_spec(s);s.loader.exec_module(helpers)
core=helpers.core;core.VERSION='overnight-fsg-explicit-cc0-v1';core.PROVIDERS['night-fsg']='Smithsonian National Museum of Asian Art'
core.HOSTS.add('asia.si.edu')
CC0=helpers.CC0;norm=helpers.norm;fields=helpers.fields;ro=helpers.ro
NAME='National Museum of Asian Art';SLUG='smithsonian-national-museum-of-asian-art';INSTITUTION_ID=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://asia.si.edu/'))
QUERY=helpers.QUERY.replace("e.scheme='saam-object'","e.scheme='fsg-object'")
POLICY='https://asia.si.edu/research/research-resources/image-services-and-permissions/'

def creator_variants(value):
    if re.search(r'\b(attributed|after|workshop|school|follower|circle|possibly|probably|anonymous|signature|possibly by)\b',value,re.I):
        raise ValueError('Qualified source creator requires separate attribution review')
    name=value.split(' (',1)[0].strip();variants={name}
    latin=re.split(r'[\u3400-\u9fff\uf900-\ufaff]',name,maxsplit=1)[0].strip()
    if latin:variants.add(latin)
    return variants

def date_parts(value):
    # Only explicitly bounded creation dates; no before/after or activity dates.
    m=re.fullmatch(r'\s*(?P<approx>(?:ca\.|c\.|circa|about)\s*)?(?P<lo>\d{4})(?:\s*[-–—/]\s*(?P<hi>\d{4}|\d{2}))?\s*',value,re.I)
    if m:
        lo=int(m['lo']);end=m['hi'] or m['lo'];hi=int(str(lo)[:2]+end) if len(end)==2 else int(end)
        precision=('circa' if lo==hi else 'circa_range') if m['approx'] else ('exact' if lo==hi else 'range')
    else:
        m=re.fullmatch(r'(\d{1,2})(?:st|nd|rd|th) century',value.strip(),re.I)
        if not m:raise ValueError('Source creation-date wording requires review')
        century=int(m[1]);lo=(century-1)*100;hi=century*100-1;precision='century'
    if not 1000<=lo<=hi<=1970:raise ValueError('Creation interval outside selected scope')
    return lo,hi,precision

def source_match(c,o):
    d=o.get('content',{});dn=d.get('descriptiveNonRepeating',{});ft=d.get('freetext',{});url=dn.get('record_link','')
    if o.get('unitCode')!='FSG' or dn.get('data_source')!=NAME:raise ValueError('Holding institution differs')
    if dn.get('record_ID')!='fsg_'+c['external_id'] or url!='https://asia.si.edu/object/'+c['external_id']+'/':raise ValueError('Official object identifier differs')
    if dn.get('metadata_usage',{}).get('access')!='CC0':raise ValueError('Metadata rights not CC0')
    if fields(ft,'objectType','Type')!={'painting':['Painting'],'drawing':['Drawing'],'print':['Print']}.get(c['work_type']):raise ValueError('Object type differs')
    if norm(dn.get('title',{}).get('content'))!=norm(c['title']):raise ValueError('Source title differs')
    if fields(ft,'identifier','Accession Number')!=[c['accession_number']] or c['accession_number']!=c['external_id']:raise ValueError('Source accession differs')
    names=fields(ft,'name','Artist')
    if len(names)!=1 or c['roles']!=['primary']:raise ValueError('Unique source artist absent')
    if not {norm(v) for v in creator_variants(names[0])}&{norm(v) for v in [c['artist']]+c['aliases']}:raise ValueError('Existing artist identity differs')
    dates=fields(ft,'date','Date')
    if len(dates)!=1:raise ValueError('Unique creation date absent')
    lo,hi,precision=date_parts(dates[0])
    if (lo,hi,precision)!=(c['creation_year_start'],c['creation_year_end'],c['date_precision']) or c['date_display']!=dates[0]:raise ValueError('Creation normalization differs')
    life=re.search(r'\((\d{4})[-–—](\d{4})\)',names[0])
    if life and (int(life[1]),int(life[2]))==(lo,hi) and lo!=hi:raise ValueError('Creator lifespan is not an artwork creation interval')
    if fields(ft,'objectRights','Restrictions & Rights')!=['CC0']:raise ValueError('Object rights not explicitly CC0')
    collections=fields(ft,'notes','Collection')
    if len(collections)!=1 or collections[0] not in ('Freer Gallery of Art Collection','Arthur M. Sackler Gallery Collection','National Museum of Asian Art Collection','Freer Study Collection','Freer Gallery of Art Study Collection'):raise ValueError('Collection membership needs review')
    origins=fields(ft,'place','Origin')
    if not origins or c.get('creation_place_display')!='; '.join(origins):raise ValueError('Source origin differs')
    media=dn.get('online_media',{}).get('media',[])
    if len(media)!=1:raise ValueError('Multiple or absent source images require view selection')
    im=media[0];image=im.get('content','');parts=urlparse(image)
    if im.get('type')!='Images' or im.get('usage',{}).get('access')!='CC0':raise ValueError('Exact media rights not CC0')
    if parts.scheme!='https' or parts.hostname!='ids.si.edu' or parts.path!='/ids/deliveryService' or parse_qs(parts.query).get('id')!=[im.get('idsId')] or not im.get('idsId','').startswith('FS-'):raise ValueError('Image delivery identity differs')
    return im,image,{'source_year_start':lo,'source_year_end':hi,'source_date_text':dates[0],'source_creator':names[0],'source_collection':collections[0],'source_origin':origins}

# Bypass the SAAM-specific wrapper but keep the shared media integrity writer.
original_attach=helpers.original_attach
def attach(db,im,target):
    source_match(im,im['raw']['object'])
    with db.transaction():
        rows=db.execute(QUERY+' AND e.external_id=%s FOR UPDATE OF a',(im['external_id'],)).fetchall()
        if len(rows)!=1 or rows[0]['artwork_id']!=im['target_ids'][target]:raise ValueError('FSG target identity changed')
        row=rows[0]
        if any(row[k]!=im[k] for k in ('title','creation_year_start','creation_year_end','date_precision','date_display','artist_slugs','roles','work_type')):raise ValueError('FSG target facts changed')
        if row['current_institution_id']!=im['institution_ids'][target]:raise ValueError('Holding institution differs')
        origin=db.execute('SELECT creation_place_display FROM artworks WHERE id=%s',(row['artwork_id'],)).fetchone()
        if origin['creation_place_display']!=im['creation_place_display']:raise ValueError('Source origin changed')
        if row['primary_media_id'] and row['primary_media_id']!=im['media_id']:return 'existing_media_preserved'
        result=original_attach(db,im,target)
        if result=='attached':db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
        return result
core.attach=attach

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=20);p.add_argument('--deadline',type=float,required=True);p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    lock=(a.run/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if not (a.run.parent/'backups.json').exists() or not (a.run/'institution.receipt.json').exists():raise SystemExit('Backups and institution evidence required')
    rows=json.loads((a.run/'candidates.json').read_text())['candidates'];done={k for k,v in core.latest_events(a.run).items() if v['outcome'] in ('complete','prepared','failed')}
    rows=[c for c in rows if c['artwork_id'] not in done][:a.limit]
    for c in rows:source_match(c,c['raw']['object'])
    dsn=None if a.prepare_only else core.cloud_dsn()
    for start in range(0,len(rows),50):
        if time.time()>=a.deadline:break
        group=rows[start:start+50]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            jobs=[pool.submit(core.worker,'night-fsg',group[n::3],SimpleNamespace(run=a.run,prepare_only=a.prepare_only),dsn) for n in range(3) if group[n::3]]
            for job in jobs:job.result()
        print(core.now(),'FSG',dict(core.COUNTS),flush=True)
if __name__=='__main__':main()
