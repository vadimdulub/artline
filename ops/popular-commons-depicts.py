#!/usr/bin/env python3
"""Selected original photographs with corroborated Commons depicts identities.

P180 alone is insufficient: require the exact source artwork category, creator,
holding context, an identified photographer, explicit rights, and visual review
before delivery. Copies, details, room views and book scans remain on hold.
"""
import argparse, collections, fcntl, importlib.util, json, re, time
from pathlib import Path
from types import SimpleNamespace
s=importlib.util.spec_from_file_location('photo',Path(__file__).with_name('research-popular-painting-photos.py'))
photo=importlib.util.module_from_spec(s);s.loader.exec_module(photo)
m=photo.m;core=m.core;PROVIDER='popular-commons-depicts'
core.PROVIDERS[PROVIDER]='Wikimedia Commons'

def identity(c,e,page,sdc,institution):
    m.entity_match(c,e,require_primary_image=False)
    m.verify_structured_object(c,sdc)
    if m.ids(sdc,'P180')!={c['qid']}:raise ValueError('Depicts is not exactly this single artwork')
    if institution.get('id')!=c['institution_qid']:raise ValueError('Holding authority differs')
    text=page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
    info=page.get('imageinfo',[{}])[0];meta=info.get('extmetadata',{})
    if page.get('ns')!=6 or min(info.get('width',0),info.get('height',0))<300:raise ValueError('Not a sufficiently large file')
    categories={m.norm(v.strip()) for v in re.findall(r'\[\[Category:([^]|]+)',text,re.I)}
    expected={m.norm(v) for v in m.values(e,'P373') if isinstance(v,str)}
    if not expected & categories:raise ValueError('Exact artwork category not independently corroborated')
    labels=' '.join(categories)+' '+page['title']
    if re.search(r'\b(detail|details|works after|copies|replicas|posters|souvenirs|verso|reverse|collage|montage)\b',labels,re.I):raise ValueError('Partial, copied or composite image')
    if re.search(r'\b(annotated|diagram|schema prospettico|perspective analysis|analysis overlay)\b',labels+' '+text,re.I):raise ValueError('Annotated or diagrammatic image')
    plain=m.plain(text+' '+meta.get('ImageDescription',{}).get('value',''))
    if m.norm(c['artist']) not in m.norm(plain):raise ValueError('Artwork creator not corroborated in this file')
    names=[v['value'] for v in institution.get('labels',{}).values()]
    names += [v['value'] for vs in institution.get('aliases',{}).values() for v in vs]
    if not any(len(m.norm(n))>8 and m.norm(n) in m.norm(plain) for n in names):raise ValueError('Original museum context not independently corroborated')
    source=m.plain(' '.join(meta.get(k,{}).get('value','') for k in ('Credit','Attribution')))
    if re.search(r'scann?ed|scan from|original uploader|book|DVD|digital processing|digitally desaturated',source,re.I):raise ValueError('A scan or uploader credit does not establish an original photograph')
    if m.origin.verify(c,page)!='independent_photographer':raise ValueError('Independent original photographer absent')
    if not m.photographic_credits(c,page):raise ValueError('Photographer credit absent')
    photo.verify_original_photograph(c,page)

def verify(im):
    raw=im['raw'];identity(im,raw['wikidata'],raw['commons'],raw['structured_data'],raw['institution'])
    core.validate_source_image_identity(dict(im,provider='night-commons'))
    m.rights_and_identity(im,raw['wikidata'],raw['commons'],raw['structured_data'],im.get('rendered_licence_evidence'),allow_exact_depicts=True)

def attach(db,im,target):
    verify(im)
    with db.transaction():
        rows=db.execute("SELECT a.id::text,a.slug,a.title,a.creation_year_start,a.creation_year_end,a.work_type FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata' WHERE e.external_id=%s",(im['qid'],)).fetchall()
        if len(rows)!=1 or rows[0]['id']!=im['target_ids'][target] or any(rows[0][k]!=im[k] for k in ('slug','title','creation_year_start','creation_year_end','work_type')):raise ValueError('Current target artwork differs')
        outcome=m.original_attach(db,im,target)
        if outcome=='attached':db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
        return outcome
core.attach=attach

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=50);p.add_argument('--deadline',type=float,required=True);args=p.parse_args()
    lock=(args.run/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert (args.run.parent/'backups.json').exists()
    done=core.latest_events(args.run);rows=[c for c in json.loads((args.run/'candidates.json').read_text())['candidates'] if c['artwork_id'] not in done][:args.limit]
    fetch=core.Fetcher(args.run/'metadata');institutions={};entities={}
    for start in range(0,len(rows),25):
        if time.time()>=args.deadline:break
        group=rows[start:start+25];qs=list({c['qid'] for c in group}|{c['institution_qid'] for c in group})
        entities.update(m.api(fetch,'www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(qs),'props':'claims|labels|aliases','languages':'en|mul|fr|it|nl|de|ru|el|es'})['entities'])
        for c in group:
            if time.time()>=args.deadline:break
            c=dict(c,provider=PROVIDER);held=[];chosen=None
            try:
                e=entities[c['qid']];institution=entities[c['institution_qid']];m.entity_match(c,e,require_primary_image=False)
                search=m.api(fetch,'commons.wikimedia.org',{'action':'query','list':'search','srsearch':'haswbstatement:P180='+c['qid'],'srnamespace':6,'srlimit':25,'srprop':''})
                titles=[x['title'] for x in search.get('query',{}).get('search',[])]
                for offset in range(0,len(titles),10):
                    part=titles[offset:offset+10]
                    data=m.api(fetch,'commons.wikimedia.org',{'action':'query','titles':'|'.join(part),'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main'})
                    pages=[v for v in data.get('query',{}).get('pages',{}).values() if v.get('imageinfo')]
                    mids=['M'+str(v['pageid']) for v in pages]
                    sd=m.api(fetch,'commons.wikimedia.org',{'action':'wbgetentities','ids':'|'.join(mids),'props':'claims'})['entities'] if mids else {}
                    for page in pages:
                        try:
                            sdc=sd.get('M'+str(page['pageid']),{});identity(c,e,page,sdc,institution)
                            rendered=photo.rendered_photo_rights(fetch,c,page,sdc)
                            info,credit,label,uri,status,url,original=m.rights_and_identity(c,e,page,sdc,rendered,allow_exact_depicts=True)
                            chosen=dict(c,page=info['descriptionurl'],source_image_url=url,policy_url=uri,rights_status=status,license_label=label,checked_at=core.now(),
                              raw={'wikidata':e,'commons':page,'structured_data':sdc,'institution':institution,'depicts_discovery':search},creator_credit=credit,
                              source_name='Wikimedia Commons',source_record_url=info['descriptionurl'],image_url=url,image_license=label,image_license_url=uri,
                              rights_statement=label,creator=c['artist'],creation_date=c['date_display'],source_object_id=c['qid'],rights_verified_at=core.now())
                            if rendered:chosen['rendered_licence_evidence']=rendered
                            if original:chosen['commons_original_sha1']=info['sha1']
                            chosen['attribution_text']=f"{c['artist']}. {c['title']}. Image credit: {credit}. {info['descriptionurl']}. {label} ({uri}). Full-frame proportional resize and JPEG compression; applicable ShareAlike terms retained."
                            verify(chosen);break
                        except (ValueError,KeyError) as exc:held.append({'title':page['title'],'reason':str(exc)})
                    if chosen:break
                core.save_new(args.run/'discovery'/(c['artwork_id']+'.json'),{'at':core.now(),'held':held,'selected':chosen['page'] if chosen else None})
                if not chosen:raise ValueError('No corroborated original full painting photograph with approved rights')
                core.save_new(args.run/'selected'/PROVIDER/(c['artwork_id']+'.json'),chosen)
                core.worker(PROVIDER,[c],SimpleNamespace(run=args.run,prepare_only=True),None)
            except (ValueError,KeyError) as exc:core.event(args.run,{'provider':PROVIDER,'artwork_id':c['artwork_id'],'outcome':'manual_review','reason':str(exc)})
            print(core.now(),'Corroborated depicts photographs',dict(collections.Counter(x['outcome'] for x in core.latest_events(args.run).values())),flush=True)

if __name__=='__main__':main()
