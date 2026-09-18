#!/usr/bin/env python3
"""Image evidence for selected current SMK objects with exact painter authorities."""
import argparse,collections,concurrent.futures,fcntl,importlib.util,json,re,time,uuid
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import quote
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('smk_helpers',ROOT/'ops/overnight-saam-images.py');helpers=importlib.util.module_from_spec(s);s.loader.exec_module(helpers);core=helpers.core
core.VERSION='overnight-smk-selected-primary-pdm-v1';core.PROVIDERS['night-smk']='Statens Museum for Kunst'
METADATA_TERMS='https://www.smk.dk/article/smk-api/'
PDM='https://creativecommons.org/publicdomain/mark/1.0/';NAME='Statens Museum for Kunst (SMK)';SLUG='statens-museum-for-kunst';SCHEME='european-smk-statens-museum-for-kunst-object';norm=helpers.norm;ro=helpers.ro
QUERY=helpers.QUERY.replace("e.scheme='saam-object'","e.scheme='"+SCHEME+"'")

def work_type(o):
    names={x.get('name','').casefold() for x in o.get('object_names',[])}
    if names=={'maleri'}:return 'painting'
    if 'tegning' in names and names<={'tegning','akvarel','gouache','pastel','kul','blyant'}:return 'drawing'
    if 'grafik' in names and names<={'grafik','radering','kobberstik','træsnit','xylografi','litografi','dybtryk','mezzotinte','højtryk','clairobscurtræsnit','linoleumssnit','akvatinte','koldnål','stik','ætsning'}:return 'print'
    raise ValueError('Mixed or unsupported source artwork classification')

def primary_maker(o):
    makers=o.get('production',[]);primary=[m for m in makers if m.get('creator_role') in (None,'','Kunstner')]
    if len(primary)!=1:raise ValueError('Source primary maker is absent, qualified, or multiple')
    # After-artists are explicitly secondary design references, never merged
    # into the physical printmaker. Qualified current makers remain held.
    allowed={None,'','Kunstner','Efter','Efter forlæg af','Udgiver','Trykker','Forfatter','Tidligere tilskrevet'}
    if any(m.get('creator_role') not in allowed for m in makers):raise ValueError('Current attribution uncertainty needs editorial review')
    maker=primary[0]
    if not re.fullmatch(r'\d+_person',maker.get('creator_lref','')):raise ValueError('Exact museum maker authority is unavailable')
    return maker

def date_parts(o,allow_activity_default=False):
    spans=o.get('production_date',[]);notes=o.get('production_dates_notes') or []
    if len(spans)!=1:raise ValueError('Multiple or absent source date intervals')
    if any(re.search(r'udateret|virkeår|virketid|levetid|kunstnerens liv|livstid|lifetime|undated|active years',note,re.I) for note in notes):raise ValueError('Undated work or creator-life/activity-derived date needs review')
    span=spans[0];period=span.get('period','');m=re.fullmatch(r'(?P<ca>(?:ca\.|c\.|circa)\s*)?(?P<lo>\d{4})(?:\s*[-–—/]\s*(?P<hi>\d{4}))?',period)
    if not m or not all(re.match(r'^\d{4}-',span.get(k,'')) for k in ('start','end')):raise ValueError('Open or unsupported source date wording')
    lo=int(span['start'][:4]);hi=int(span['end'][:4]);text_lo=int(m['lo']);text_hi=int(m['hi'] or m['lo'])
    if not 1000<=lo<=hi<=1970:raise ValueError('Artwork creation interval outside scope')
    ca=bool(m['ca']);display=period
    for note in notes:
        if re.fullmatch(r'(?:ca\.|c\.|circa)\s*\d{4}',note,re.I):
            ca=True;display=note
        match=re.match(r'^Værkdatering:\s*(.*)$',note,re.I)
        if not match:continue
        original=match[1].strip()
        if re.match(r'^(?:ca\.|c\.|circa)\s*',original,re.I):ca=True
        if re.search(r'\b(før|efter|først|sidst|ukendt|eller|muligvis)\b|\?|\d{4}\s*[-–—]\s*$',original,re.I):raise ValueError('Original source date wording requires review')
        # Preserve exact source uncertainty text while the supplied interval
        # remains the authority for boundaries.
        display=original
    if (text_lo,text_hi)!=(lo,hi) and not (ca and lo<=text_lo<=text_hi<=hi):raise ValueError('Structured and textual source date bounds conflict')
    maker=primary_maker(o) if o.get('production') else {}
    birth=maker.get('creator_date_of_birth','');death=maker.get('creator_date_of_death','')
    if re.match(r'^\d{4}-',birth) and re.match(r'^\d{4}-',death) and (lo,hi)==(int(birth[:4])+15,int(death[:4])) and not allow_activity_default:
        raise ValueError('Museum interval matches default artist activity span; artwork date unresolved')
    precision=('circa' if lo==hi else 'circa_range') if ca else ('exact' if lo==hi else 'range')
    return lo,hi,precision,display

def source_match(c,o):
    if o.get('object_number')!=c['external_id'] or c['accession_number']!=c['external_id'] or o.get('id')!=c['source_api_id']:raise ValueError('Native museum object identity differs')
    if not o.get('responsible_department') or not o.get('acquisition_date'):raise ValueError('Museum collection membership needs independent review')
    if o.get('frontend_url')!='https://open.smk.dk/artwork/image/'+c['external_id']:raise ValueError('Stable collection page differs')
    titles={norm(x.get('title')) for x in o.get('titles',[])}
    if norm(c['title']) not in titles or c['work_type']!=work_type(o):raise ValueError('Source title or object type differs')
    maker=primary_maker(o)
    if maker['creator_lref']!=c['artist_authority'] or c['roles']!=['primary']:raise ValueError('Exact source maker authority differs')
    metadata_only=c.get('image_eligibility')=='date_unresolved'
    dates=date_parts(o,allow_activity_default=metadata_only)
    if metadata_only:
        try:date_parts(o)
        except ValueError as e:
            if 'default artist activity span' not in str(e):raise
        else:raise ValueError('Unresolved-date exception lacks evidence')
        if (c['creation_year_start'],c['creation_year_end'],c['date_precision'],c['date_display'])!=(None,None,'unknown','Date unresolved'):raise ValueError('Unresolved artwork date must remain unknown')
    elif dates!=(c['creation_year_start'],c['creation_year_end'],c['date_precision'],c['date_display']):raise ValueError('Source creation facts differ')
    life=[]
    for key in ('creator_date_of_birth','creator_date_of_death'):
        value=maker.get(key,'');life.append(int(value[:4]) if re.match(r'^\d{4}-',value) else None)
    if dates[0]!=dates[1] and tuple(life)==dates[:2]:raise ValueError('Artwork date repeats maker lifespan')
    if o.get('public_domain') is not True or o.get('rights')!=PDM or o.get('has_image') is not True or o.get('copyright_notice'):raise ValueError('Exact image PDM rights are missing or conflicting')
    base=o.get('image_iiif_id','')
    if re.fullmatch(r'https://iip\.smk\.dk/iiif/jp2/[A-Za-z0-9_.-]+',base):image=base+'/full/!1000,1000/0/default.jpg'
    else:
        image=o.get('image_native') or o.get('image_thumbnail') or ''
        if not re.fullmatch(r'https://api\.smk\.dk/api/v1/thumbnail/[A-Za-z0-9_-]{1,100}\.(?:jpg|JPG)',image):raise ValueError('Exact public image resource is unavailable')
    return None if metadata_only else image,{'source_creator':maker['creator'],'source_maker_authority':maker['creator_lref'],'source_year_start':dates[0],'source_year_end':dates[1],'source_date_text':dates[3],'source_date_notes':o.get('production_dates_notes',[]),'date_review':'Unresolved activity-derived range; metadata only' if metadata_only else 'Source artwork interval verified'}

original_attach=helpers.original_attach

def attach(db,im,target):
    image,_=source_match(im,im['raw']['object']);assert image==im['source_image_url']
    with db.transaction():
        rows=db.execute(QUERY+' AND e.external_id=%s FOR UPDATE OF a',(im['external_id'],)).fetchall()
        if len(rows)!=1 or rows[0]['artwork_id']!=im['target_ids'][target]:raise ValueError('SMK target identity differs')
        row=rows[0]
        if any(row[k]!=im[k] for k in ('title','accession_number','creation_year_start','creation_year_end','date_precision','date_display','work_type','artist_slugs','roles')):raise ValueError('SMK target source facts changed')
        maker=db.execute("SELECT e.external_id FROM artwork_artists aa JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=aa.artist_id WHERE aa.artwork_id=%s AND e.scheme='smk-person'",(row['artwork_id'],)).fetchall()
        if len(maker)!=1 or maker[0]['external_id']!=im['artist_authority']:raise ValueError('Existing target maker authority changed')
        if row['primary_media_id'] and row['primary_media_id']!=im['media_id']:return 'existing_media_preserved'
        iid=im['institution_ids'][target]
        if row['current_institution_id']!=iid:raise ValueError('Target holding institution differs')
        result=original_attach(db,im,target)
        if result=='attached':db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
        return result
core.attach=attach

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=10000);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();assert (a.run.parent/'backups.json').exists()
    lock=(a.run/'image-worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    rows=json.loads((a.run/'candidates.json').read_text())['candidates'];done={k for k,v in core.latest_events(a.run).items() if v['outcome'] in ('prepared','complete','failed')};todo=[c for c in rows if c.get('image_eligibility')!='date_unresolved' and c['artwork_id'] not in done][:a.limit]
    for start in range(0,len(todo),50):
        if time.time()>=a.deadline:break
        group=todo[start:start+50]
        for c in group:source_match(c,c['raw']['object'])
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            for job in [pool.submit(core.worker,'night-smk',group[n::3],SimpleNamespace(run=a.run,prepare_only=True),None) for n in range(3)]:job.result()
        print(core.now(),'SMK selected images',dict(core.COUNTS),flush=True)
if __name__=='__main__':main()
