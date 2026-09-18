#!/usr/bin/env python3
"""Selected Nationalmuseum paintings: current identity, scope and exact image rights."""
import argparse, collections, fcntl, importlib.util, json, re, time, uuid
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse
import psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('nga_util',ROOT/'ops/overnight-nga-commons.py')
util=importlib.util.module_from_spec(s); s.loader.exec_module(util)
# Use the base writer: Nationalmuseum has its own independent identity checks.
core=util.core; core.attach=util.original_attach
PROVIDER='followup-nationalmuseum'; SCHEME='nationalmuseum-object'
HOST='https://collection.nationalmuseum.se'; PDM='https://creativecommons.org/publicdomain/mark/1.0/'
CC0='https://creativecommons.org/publicdomain/zero/1.0/'
BYSA='https://creativecommons.org/licenses/by-sa/4.0/'
SOURCE='followup-nationalmuseum-current-20260916'
core.PROVIDERS[PROVIDER]='Nationalmuseum, Sweden'; core.HOSTS.add('collection.nationalmuseum.se')
core.VERSION='nationalmuseum-current-object-exact-media-v1'
norm=util.norm

def fact_check(lead,capture):
    i=capture['item']; oid=lead['native_id']
    if str(i.get('Id'))!=oid or capture['url']!=HOST+'/en/collection/item/'+oid+'/':raise ValueError('Official object identity differs')
    if i.get('ObjCollectionSearchTxt',{}).get('LabelTxt')!='Paintings':raise ValueError('Current museum classification is not paintings')
    if i.get('ObjCategoryTxt') not in ('','#painting#'):raise ValueError('Conflicting current object category')
    acc=i.get('ObjInventoryNumberTxt','')
    if not re.fullmatch(r'NM(?:B|Grh)?\s+[\d: A-Za-z./-]+',acc) or acc not in lead['accessions']:raise ValueError('Accession or institutional collection requires review')
    if acc.startswith('NMGrh') and not capture.get('holding_administration_evidence',{}).get('url')=='https://www.nationalmuseum.se/en/explore-art-and-design/the-collections':raise ValueError('Gripsholm collection responsibility evidence missing')
    if re.search(r'loan|deposit|private collection|deaccession|returned|restituted',i.get('ObjDonationTxt',''),re.I):raise ValueError('Institutional ownership requires review')
    makers=i.get('ObjPersonRef',{}).get('Items',[])
    # Retain earlier attributions as evidence, but require one unqualified current artist.
    active=[m for m in makers if m.get('RoleVoc',{}).get('LabelTxt') not in ('Previously attributed to','Former attribution')]
    if len(active)!=1 or active[0].get('RoleVoc',{}).get('LabelTxt')!='Artist':raise ValueError('Current creator attribution requires review')
    maker=active[0]; label=maker.get('LinkLabelTxt','')
    match=re.fullmatch(r'(.+?) \((\d{4}) - (\d{4})\)',label)
    if not match or not maker.get('ReferencedId'):raise ValueError('Current creator lacks verifiable name and life dates')
    artist=lead['artist']; names={norm(x) for x in [artist['display_name']]+[p['name'] for p in lead['people']]}
    if norm(match[1]) not in names or int(match[2])!=artist['birth_year'] or int(match[3])!=artist['death_year']:raise ValueError('Creator name or life dates conflict with existing authority')
    lo=i.get('ObjFromYearTxt','');hi=i.get('ObjToYearTxt',''); date=i.get('ObjDateMainTxt','')
    if not re.fullmatch(r'\d{4}',lo) or not re.fullmatch(r'\d{4}',hi):raise ValueError('Unknown creation bounds')
    lo,hi=int(lo),int(hi)
    if not 1000<=lo<=hi<=1970 or lo<artist['birth_year'] or hi>artist['death_year']:raise ValueError('Creation bounds outside scope or creator lifetime')
    if (lo,hi)==(artist['birth_year'],artist['death_year']):raise ValueError('Creator lifetime is not an artwork date')
    if not date or re.search(r'\bor\b|\?|before|after|published|acquired|\bcopy\b',date,re.I):raise ValueError('Creation date wording needs editorial review')
    stated=[int(x) for x in re.findall(r'\b(\d{4})(?:s\b|\b)',date)]
    if not stated or any(x<lo or x>hi for x in stated):raise ValueError('Original date wording conflicts with normalized bounds')
    circa=bool(re.search(r'\bc\.|circa|about|probably',date,re.I))
    precision=('circa' if lo==hi else 'circa_range') if circa else ('exact' if lo==hi else 'range')
    if re.search(r'\b\d{3}0s\b',date):precision='decade'
    title=i.get('ObjTitleMainTxt','').strip()
    if not title:raise ValueError('Current museum title is missing')
    qids=set(re.findall(r'\bQ[1-9]\d*\b',i.get('ObjExternalIDTxt','')))
    if len(qids)>1:raise ValueError('Multiple physical-object cross references')
    return {'title':title,'accession_number':acc,'creation_year_start':lo,'creation_year_end':hi,'date_precision':precision,
            'date_display':date,'work_type':'painting','medium':i.get('ObjMaterialTechniqueTxt') or None,
            'artist_slug':artist['slug'],'artist':artist['display_name'],'artist_qid':artist['qid'],
            'source_artist_id':maker['ReferencedId'],'qid':next(iter(qids),None),'popular':artist['popular']}

def exact_image(capture):
    i=capture['item']; default=i.get('DefaultImage','')
    if not re.fullmatch(r'multimedia/\d+/multimedia-\d+\.large\.jpg',default):raise ValueError('No eligible default full-frame museum image')
    if '/'+default not in capture['rendered_image_paths']:raise ValueError('Image is not linked by the official object page')
    hits=[]
    for item in i.get('ObjMultimediaRef',{}).get('Items',[]):
        for media in item.get('Multimedia',[]):
            if media.get('full')==default:hits.append((item,media))
    if len(hits)!=1:raise ValueError('Primary image media identity is ambiguous')
    item,media=hits[0]
    approved={'Public Domain, '+PDM:(PDM,'public_domain','Public Domain Mark 1.0'), 'CC BY SA, '+BYSA:(BYSA,'cc_by_sa','CC BY-SA 4.0')}
    license=approved.get(item.get('MulRightsTxt','').strip())
    if not license:raise ValueError('Exact primary image does not have an approved unambiguous licence')
    if item.get('InternetVoc',{}).get('LabelTxt')!='Public' or media.get('mime')!='image/jpeg':raise ValueError('Primary media is not a public JPEG resource')
    if item.get('MulPhotographicalCopyrightTxt','').strip():raise ValueError('Image has a separate photographic copyright claim')
    credit=item.get('MulPhotocreditTxt','').strip()
    if not credit:
        if license[0]!=PDM:raise ValueError('Required image photographer credit missing')
        credit='Image supplied by Nationalmuseum; photographer not credited in source'
    return HOST+'/'+default,credit,item['ReferencedId'],license

def verify_catalogue_facts(im, facts):
    """Permit explicit image-only handling of harmless legacy display formatting."""
    for k in ('title','accession_number','creation_year_start','creation_year_end','date_display','date_precision','work_type','artist','artist_slug'):
        if im.get('preserve_existing_catalogue_format') is True and k=='accession_number':
            if re.sub(r'\s+','',im[k])!=re.sub(r'\s+','',facts[k]):raise ValueError('Source accession differs')
            continue
        if im.get('preserve_existing_catalogue_format') is True and k=='date_display':
            # Bounds and precision still match exactly below. This exception
            # is only for exact dates, e.g. "Made 1869" versus "1869".
            years=set(re.findall(r'\b\d{4}\b',im[k] or ''))
            if facts['date_precision']!='exact' or facts['creation_year_start']!=facts['creation_year_end'] or years!={str(facts['creation_year_start'])}:
                raise ValueError('Legacy date wording needs editorial review')
            if re.search(r'\b(before|after|circa|about|probably|unknown|undated|or)\b|\?|\bc\.',im[k],re.I):
                raise ValueError('Legacy date uncertainty differs')
            year=str(facts['creation_year_start'])
            if not re.fullmatch(r'(?:Made |Signed )?'+year+r'(?:; museum description dates the painting to '+year+r')?',im[k]):
                raise ValueError('Unrecognized legacy date wording')
            continue
        if im[k]!=facts[k]:raise ValueError('Source fact differs: '+k)

def verify(im):
    facts=fact_check(im['raw']['lead'],im['raw']['official_capture'])
    verify_catalogue_facts(im, facts)
    url,credit,mid,license=exact_image(im['raw']['official_capture'])
    if url!=im['source_image_url'] or im['policy_url']!=license[0] or im['rights_status']!=license[1] or im['license_label']!=license[2]:raise ValueError('Exact media rights or URL differ')
    if im['policy_url']==BYSA and 'ShareAlike' not in im['attribution_text']:raise ValueError('ShareAlike requirement is missing')
    if credit not in im['creator_credit'] or im['external_id']!=im['raw']['lead']['native_id']:raise ValueError('Media attribution or object differs')
    if im['raw']['official_capture']['url']!=im['source_record_url'] or not im['rights_verified_at']:raise ValueError('Independent source evidence missing')

def plan(run,discovery,excluded_plans=()):
    path=run/'plan.json'
    if path.exists():return json.loads(path.read_text())
    leads=json.loads((discovery/'bounded-primary-leads.json').read_text()); records=[];held=[]
    if isinstance(leads,dict):leads=leads['records']
    excluded_ids={r['external_id'] for previous in excluded_plans for r in json.loads(previous.read_text())['records']}
    for lead in leads:
        if lead['native_id'] in excluded_ids:continue
        p=discovery/'current-records'/(lead['native_id']+'.json')
        if not p.exists():continue
        capture=json.loads(p.read_text())
        capture['holding_administration_evidence']=json.loads((discovery/'holding-administration-evidence.json').read_text())
        try:
            facts=fact_check(lead,capture)
            try:image_url,credit,mid,license=exact_image(capture); rights_error=None
            except ValueError as e:image_url=credit=mid=license=None;rights_error=str(e)
            records.append(dict(facts,external_id=lead['native_id'],page=capture['url'],image_url=image_url,photo_credit=credit,media_native_id=mid,image_license=license,rights_error=rights_error,
                         raw={'lead':lead,'official_capture':capture}))
        except ValueError as e:held.append({'source_object_id':lead['native_id'],'reason':str(e)})
    qids=[r['qid'] for r in records if r['qid']];native=[r['external_id'] for r in records];artist_slugs=list({r['artist_slug'] for r in records})
    targets={}
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        with util.ro(dsn) as db:
            inst=db.execute("SELECT i.id::text,p.country_code FROM institutions i JOIN places p ON p.id=i.place_id WHERE i.slug='nationalmuseum-stockholm' AND i.status<>'archived'").fetchall()
            assert len(inst)==1 and inst[0]['country_code']=='SE';iid=inst[0]['id']
            artists=db.execute("""SELECT p.id::text,p.slug,p.display_name,p.birth_year,p.death_year,array_agg(e.external_id) FILTER(WHERE e.external_id IS NOT NULL) qids
                FROM artists p LEFT JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=p.id AND e.scheme='wikidata'
                WHERE p.slug=ANY(%s) AND p.status<>'archived' GROUP BY p.id""",(artist_slugs,)).fetchall()
            artistmap={r['slug']:r for r in artists}
            hits=db.execute("""SELECT a.id::text,a.slug,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.date_display,a.date_precision,a.work_type,
                a.primary_media_id::text,a.current_institution_id::text,a.status,
                ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artist_ids,
                ARRAY(SELECT e.external_id FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata') qids,
                ARRAY(SELECT e.external_id FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme=%s) native_ids
                FROM artworks a WHERE a.current_institution_id=%s OR a.id IN
                (SELECT e.entity_id FROM external_identifiers e WHERE e.entity_type='artwork' AND ((e.scheme='wikidata' AND e.external_id=ANY(%s)) OR (e.scheme=%s AND e.external_id=ANY(%s))))
                OR a.id IN (SELECT aa.artwork_id FROM artwork_artists aa WHERE aa.artist_id=ANY(%s::uuid[]))""",
                (SCHEME,iid,qids,SCHEME,native,[a['id'] for a in artists])).fetchall()
            targets[target]=(iid,artistmap,hits)
    selected=[]; seen_qids=set(); seen_acc=set()
    blocked={x['artwork_id'] for x in json.loads((run.parent/'withdrawn-images.json').read_text())['records']}
    for r in records:
        try:
            if r['qid'] and r['qid'] in seen_qids or norm(r['accession_number']) in seen_acc:raise ValueError('Duplicate selected physical-object identifier')
            r['targets']={}; existing_media=False
            for target,(iid,artists,hits) in targets.items():
                a=artists.get(r['artist_slug']); la=r['raw']['lead']['artist']
                qid_consistent=a and ((r['artist_qid'] in (a['qids'] or [])) if r['artist_qid'] else not a['qids'])
                if not a or a['display_name']!=r['artist'] or a['birth_year']!=la['birth_year'] or a['death_year']!=la['death_year'] or not qid_consistent:raise ValueError(target+': existing creator authority differs')
                exact=[h for h in hits if (r['qid'] and r['qid'] in h['qids']) or r['external_id'] in h['native_ids'] or (h['current_institution_id']==iid and norm(h['accession_number'])==norm(r['accession_number']))]
                if len(exact)>1:raise ValueError(target+': multiple catalogue objects match source identity')
                if exact:
                    old=exact[0]
                    if old['status']!='review' or old['artist_ids']!=[a['id']] or old['current_institution_id']!=iid or any(old[k]!=r[k] for k in ('title','accession_number','creation_year_start','creation_year_end','date_display','date_precision','work_type')):raise ValueError(target+': existing artwork facts require reconciliation')
                    existing_media=existing_media or bool(old['primary_media_id'])
                    aid=old['id'];slug=old['slug'];mode='existing'
                else:
                    titles={norm(r['title']),norm(r['raw']['lead']['title'])}
                    if any(a['id'] in h['artist_ids'] and norm(h['title']) in titles for h in hits):raise ValueError(target+': same artist and title needs physical-object review')
                    aid=str(uuid.uuid5(uuid.NAMESPACE_URL,HOST+'/en/collection/item/'+r['external_id']+'/'));slug='nationalmuseum-'+r['external_id'];mode='new'
                r['targets'][target]={'artwork_id':aid,'artist_id':a['id'],'institution_id':iid,'mode':mode,'slug':slug}
                if aid in blocked:raise ValueError('Inherited image-identity hold requires separate review')
            if existing_media:raise ValueError('Existing catalogue image preserved')
            seen_qids.add(r['qid']);seen_acc.add(norm(r['accession_number']));selected.append(r)
        except ValueError as e:held.append({'source_object_id':r['external_id'],'reason':str(e)})
    data={'at':core.now(),'records':selected,'held':held,'metadata_basis':'CC0 institutional LIDO discovery, verified against current official object facts. No authored descriptions imported; institution country Sweden is distinct from artist nationality.'}
    core.save_new(path,data);core.save_new(run/'plan-manifest.json',{'sha256':core.sha(path.read_bytes()),'count':len(selected)})
    core.save_new(run/'selection-summary.json',{'selected':len(selected),'pictures':sum(bool(r['image_url']) for r in selected),'popular':sum(r['popular'] for r in selected),'modes':{t:dict(collections.Counter(r['targets'][t]['mode'] for r in selected)) for t in targets},'held':dict(collections.Counter(h['reason'] for h in held))})
    print((run/'selection-summary.json').read_text(),flush=True);return data

base_attach=core.attach
def attach(db,im,target):
    verify(im)
    with db.transaction():
        row=db.execute("""SELECT a.id::text,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.date_display,a.date_precision,a.work_type,a.status,
            a.current_institution_id::text,ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artist_ids
            FROM artworks a WHERE a.id=%s FOR UPDATE""",(im['target_ids'][target],)).fetchone()
        expected=im['targets'][target]
        if not row or row['status']!='review' or row['current_institution_id']!=expected['institution_id'] or row['artist_ids']!=[expected['artist_id']] or any(row[k]!=im[k] for k in ('title','accession_number','creation_year_start','creation_year_end','date_display','date_precision','work_type')):raise ValueError('Current target artwork facts differ')
        result=base_attach(db,im,target)
        if result=='attached':db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
        return result
core.attach=attach

def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','images']);p.add_argument('--run',type=Path,required=True);p.add_argument('--discovery',type=Path);p.add_argument('--exclude-plan',type=Path,action='append',default=[]);p.add_argument('--canary',action='store_true');p.add_argument('--limit',type=int,default=1000);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
    if a.phase=='plan':plan(a.run,a.discovery,a.exclude_plan);return
    if (a.run.parent/'nationalmuseum-direct-source-pause.json').exists():raise SystemExit('Direct museum image access is paused after HTTP 403 responses; use independently verified Commons donations instead.')
    lock=(a.run/'image-worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    data=json.loads((a.run/'plan.json').read_text());assert core.sha((a.run/'plan.json').read_bytes())==json.loads((a.run/'plan-manifest.json').read_text())['sha256']
    if a.canary:
        assert 0<a.limit<=5
        for target in ('local','cloud'):
            verified=json.loads((a.run/(target+'-metadata-verified-canary.json')).read_text())
            assert {r['targets'][target]['artwork_id'] for r in data['records'][:a.limit]} <= {r['artwork_id'] for r in verified['records']}
        data['records']=data['records'][:a.limit]
    else:assert (a.run/'local-metadata-verified.json').exists() and (a.run/'cloud-metadata-verified.json').exists()
    done={k for k,v in core.latest_events(a.run).items() if v['outcome'] in ('complete','prepared','failed')};ready=[]
    for r in data['records']:
        if not r['image_url']:continue
        aid=r['targets']['local']['artwork_id']
        if aid in done:continue
        credit=r['artist']+'; '+r['photo_credit']+'; Nationalmuseum, Sweden'
        uri,status,label=r['image_license'];share=' Derivative licensed under the same CC BY-SA 4.0 licence (ShareAlike).' if uri==BYSA else ''
        im=dict(r,provider=PROVIDER,scheme=SCHEME,artwork_id=aid,slug=r['targets']['local']['slug'],target_ids={t:x['artwork_id'] for t,x in r['targets'].items()},
                source_record_url=r['page'],source_name=core.PROVIDERS[PROVIDER],source_object_id=r['external_id'],source_image_url=r['image_url'],policy_url=uri,rights_status=status,license_label=label,
                creator_credit=credit,attribution_text=f"{r['artist']}. {r['title']}. {credit}. {r['page']}. {label} ({uri}). Full-frame proportional resize and JPEG compression."+share,
                checked_at=core.now(),rights_verified_at=r['raw']['official_capture']['retrieved_at'],creation_date=r['date_display'])
        selected_path=a.run/'selected'/PROVIDER/(aid+'.json')
        if selected_path.exists():im=json.loads(selected_path.read_text())
        verify(im);core.save_new(selected_path,im);ready.append(im)
    for n in range(0,min(len(ready),a.limit),20):
        if time.time()>=a.deadline:break
        core.worker(PROVIDER,ready[n:min(n+20,a.limit)],SimpleNamespace(run=a.run,prepare_only=True),None)
        print(core.now(),'Nationalmuseum selected images',dict(core.COUNTS),flush=True)

if __name__=='__main__':main()
