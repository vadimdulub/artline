#!/usr/bin/env python3
"""Deliver the explicitly authorized, selected Prado WikiArt images to production.

Uses the existing image-only transaction and storage verification. No artwork
creation, publication, metadata reconciliation or local database mutation.
"""
import argparse,collections,copy,gzip,hashlib,importlib.util,json,re,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('delivery',ROOT/'ops/deliver-production-wikiart-images-20261006.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
r=d.r;q=d.q
RESEARCH=ROOT/'docs/research/prado-wikiart-20261006'
RUN=RESEARCH/'delivery';OP='prado-wikiart-images-20261006'
MUSEUM='008d3646-ed41-4691-9a37-25a9fff40e51'
d.RUN=r.RUN=q.RUN=RUN;r.PORT=55447;d.OP=OP
d.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
d.ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/OP

def review():
    p=RUN/'selection.json';raw=p.read_bytes()
    return json.loads(raw),{'path':str(p.relative_to(ROOT)),'sha256':r.sha(raw)}
d.review=review

def prepared_for(aid):
    replacement=RUN/'prepared-replacements'/(aid+'.json')
    return r.load(replacement if replacement.exists() else RUN/'prepared'/(aid+'.json'))

def prepare_replacements():
    data,pointer=review();by={x['work']['id']:x for x in data['ready']}
    for aid,override in r.load(RUN/'source-replacements.json').items():
        page=override['page'];raw=gzip.decompress((ROOT/page['receipt']['body_path']).read_bytes())
        assert r.sha(raw)==page['receipt']['sha256']
        assert page['public_domain_label'] and page['rights_label'] in ['Public domain','Dominio público']
        assert page['metadata']['artistName']==by[aid]['page']['metadata']['artistName']
        original,receipt=d.download(page['image_url']);raw,width,height,quality=d.core.compress(original)
        digest=r.sha(raw);path='/assets/artworks/imported/'+OP+'/'+aid+'-'+digest[:16]+'.jpg'
        r.save(ROOT/'apps/web/public'/path.lstrip('/'),raw)
        im={'artwork_id':aid,'page':page,'review_outcome':by[aid]['review_outcome']+'; '+override['reason'],'review_pin':pointer,
            'title':by[aid]['work']['title'],'artist':page['metadata']['artistName'],'outcome':'prepared','reuse':False,
            'path':path,'media_id':d.uid('media/'+digest),'sha256':digest,'bytes':len(raw),'width':width,'height':height,
            'jpeg_quality':quality,'download':receipt,'visual_path':str(ROOT/'apps/web/public'/path.lstrip('/')),
            'supersedes_preparation_sha256':r.sha((RUN/'prepared'/(aid+'.json')).read_bytes()),'replacement_reason':override['reason']}
        with d.Image.open(im['visual_path']) as image:image.verify()
        r.save(RUN/'prepared-replacements'/(aid+'.json'),im)
        print(json.dumps({'artwork_id':aid,'visual_path':im['visual_path'],'width':width,'height':height,'bytes':len(raw)}),flush=True)

def source_page(link):
    rc=link['page_receipt'];key=r.sha(rc['url'].encode())
    p=next(folder/'captures'/(key+'.html.gz') for folder in (RESEARCH/'round-2',RESEARCH) if (folder/'captures'/(key+'.html.gz')).exists())
    raw=gzip.decompress(p.read_bytes());assert r.sha(raw)==rc['sha256']
    metadata=dict(_id=link['wikiart_id'],title=link['source_title'],artistName=link['source_artist'],year=link['source_date'],width=link['width'],height=link['height'],image=link['image_url'])
    return {'url':link['wikiart_page_url'],'metadata':metadata,'image_url':link['image_url'],'rights_label':link['source_rights_label'],
        'receipt':{**rc,'body_path':str(p.relative_to(ROOT))},'fields':{'Location':link['source_location'],'Dimensions':link['source_dimensions']},
        'date':q.parse_date(link['source_date']),'public_domain_label':link['wikiart_public_domain_label']}

def select():
    data=r.load(RESEARCH/'round-2/image-matches.json');baseline={w['artwork']['id']:w for w in r.load(RESEARCH/'production-catalog.json')['works']}
    ids=[w['artwork_id'] for w in data['works']]
    with r.connect('production') as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        current=d.snapshots(db,ids)
        institution=db.execute('SELECT to_jsonb(i) data FROM institutions i WHERE id=%s',(MUSEUM,)).fetchone()['data']
        eligibility={x['id']:x['scope'] for x in db.execute('SELECT id::text,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()}
        counts=db.execute('SELECT count(*) works,count(primary_media_id) images FROM artworks WHERE current_institution_id=%s',(MUSEUM,)).fetchone()
        assert db.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s',(d.ACTOR,)).fetchone()
    r.save_gz(RUN/'fresh-production-snapshot.json.gz',{'at':r.now(),'read_only':True,'records':current,'counts':counts,'institution':institution})
    ready=[];held=[]
    for match in data['works']:
        aid=match['artwork_id'];a=current[aid]['artwork'];b=baseline[aid]
        reason=None
        if a['primary_media_id']:reason='existing_primary_image_preserved'
        elif a['current_institution_id']!=MUSEUM:reason='museum_changed_since_research'
        elif eligibility[aid]!='eligible' or a['creation_year_end'] is None or a['creation_year_end']>1955:reason='unresolved_or_ineligible_creation_date'
        elif not match['image_links']:reason=match['outcome']
        elif len(match['image_links'])!=1:reason='unresolved_source_versions'
        elif any(a[k]!=b['artwork'][k] for k in ['title','alternate_title','creation_year_start','creation_year_end','date_precision','accession_number','unlinked_creator_label']):reason='identity_changed_since_research'
        elif sorted((c['artist_id'],c['attribution_role']) for c in current[aid]['creators'])!=sorted((c['id'],c['role']) for c in b['artists']):reason='creator_changed_since_research'
        if reason:held.append({'artwork_id':aid,'title':a['title'],'reason':reason});continue
        link=match['image_links'][0]
        if not link['wikiart_public_domain_label'] or link['source_rights_label'] not in ['Public domain','Dominio público']:
            held.append({'artwork_id':aid,'title':a['title'],'reason':'source_rights_label_needs_separate_handling'});continue
        work={**a,'institution_id':MUSEUM,'creators':[{'artist_id':c['artist_id'],'role':c['attribution_role']} for c in current[aid]['creators']]}
        ready.append({'work':work,'institution':institution,'page':source_page(link),'research':match,
            'review_outcome':match['outcome']+'; '+match['note'],'pending_visual_review':True})
    selection={'at':r.now(),'authorization':'User requested WikiArt source documentation and adding as many Prado images as possible on 6 October 2026; docs/ARTLINE_IMAGE_USE.md',
        'scope':'Existing production Prado records only; fill absent primary images, retain metadata/status and source labels.','ready':ready,'held':held,'before_counts':counts}
    r.save(RUN/'selection.json',selection)
    print(json.dumps({'selected_for_visual_review':len(ready),'held':dict(collections.Counter(x['reason'] for x in held)),'production':counts}),flush=True)

def visual():
    """Record only the decisions already made from the actual contact sheets."""
    decisions=r.load(RUN/'visual-decisions.json');index=r.load(RUN/'contact-sheet-index.json');by={x['artwork_id']:x for x in index}
    assert set(decisions['approved_ids'])|set(decisions['held'])==set(by)
    assert not set(decisions['approved_ids'])&set(decisions['held'])
    approved=[{**by[x],'media_sha256':prepared_for(x)['sha256']} for x in decisions['approved_ids']];held=[{**by[aid],**note} for aid,note in decisions['held'].items()]
    result={'at':r.now(),'contact_index_sha256':r.sha((RUN/'contact-sheet-index.json').read_bytes()),'reviewer':'assistant visual inspection',
        'criteria':decisions['criteria'],'approved':approved,'held':held,'object_resolutions':decisions.get('object_resolutions',{}),
        'replacement_preparations':{x:r.sha((RUN/'prepared-replacements'/(x+'.json')).read_bytes()) for x in decisions['approved_ids'] if (RUN/'prepared-replacements'/(x+'.json')).exists()}}
    r.save(RUN/'visual-review.json',result)
    for x in held:
        im=r.load(RUN/'prepared'/(x['artwork_id']+'.json'))
        if not im['reuse']:
            src=Path(im['visual_path']);dest=d.ORIGINALS/'held-derivatives'/src.name;dest.parent.mkdir(parents=True,exist_ok=True)
            if src.exists():assert r.sha(src.read_bytes())==im['sha256'];assert not dest.exists();src.rename(dest)
    for aid in result['replacement_preparations']:
        old=r.load(RUN/'prepared'/(aid+'.json'))
        if not old['reuse']:
            src=Path(old['visual_path']);dest=d.ORIGINALS/'superseded-derivatives'/src.name;dest.parent.mkdir(parents=True,exist_ok=True)
            if src.exists():assert r.sha(src.read_bytes())==old['sha256'];assert not dest.exists();src.rename(dest)
    print('Visual review:',len(approved),'approved,',len(held),'held',flush=True)

def plan():
    data,pointer=review();visual=r.load(RUN/'visual-review.json')
    assert visual['contact_index_sha256']==r.sha((RUN/'contact-sheet-index.json').read_bytes())
    approved={x['artwork_id']:x['media_sha256'] for x in visual['approved']};prepared={};ready=[];held=[]
    for item in data['ready']:
        aid=item['work']['id'];im=prepared_for(aid)
        if aid not in approved or im['outcome']!='prepared':held.append({'artwork_id':aid,'reason':'not_visually_approved'});continue
        assert approved[aid]==im['sha256']
        raw=Path(im['visual_path']).read_bytes();assert r.sha(raw)==im['sha256'] and len(raw)==im['bytes']<=100000
        assert im['review_pin']==pointer
        if aid in visual['replacement_preparations']:
            assert r.sha((RUN/'prepared-replacements'/(aid+'.json')).read_bytes())==visual['replacement_preparations'][aid]
            assert im['page']==r.load(RUN/'source-replacements.json')[aid]['page']
        else:assert im['page']==item['page']
        x=copy.deepcopy(item);x['review_outcome']+='; full supplied image visually reviewed'
        x['page']=im['page']
        if aid in visual['object_resolutions']:x['review_outcome']+='; '+visual['object_resolutions'][aid]
        ready.append(x);prepared[aid]=im
    assert len({x['page']['metadata']['_id'] for x in ready})==len(ready),'Duplicate source object'
    assert len({im['sha256'] for im in prepared.values()})==len(ready),'Duplicate image pixels'
    with r.connect('production') as db:
        current=d.snapshots(db,[x['work']['id'] for x in ready])
        for x in ready:
            aid=x['work']['id'];a=current[aid]['artwork'];im=prepared[aid]
            assert a['current_institution_id']==MUSEUM and a['primary_media_id'] is None
            expected={k:x['work'][k] for k in a};assert a==expected,'Production changed after selection'
            assert sorted((c['artist_id'],c['attribution_role']) for c in current[aid]['creators'])==sorted((c['artist_id'],c['role']) for c in x['work']['creators'])
            if im['reuse']:
                row=db.execute('SELECT to_jsonb(m) media,to_jsonb(e) rights FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=%s',(im['media_id'],)).fetchone();assert row==im['media']
            im['attachment_was_present']=any(y['media_id']==im['media_id'] for y in current[aid]['attachments'])
    assert ready
    result={'operation':OP,'at':r.now(),'review_pin':pointer,'claims':ready,'prepared':prepared,'preimages':current,'held':held,
        'source_id':d.uid('source'),'visual_review_sha256':r.sha((RUN/'visual-review.json').read_bytes()),'policy':data['scope']}
    r.save_gz(RUN/'production-plan.json.gz',result);digest=r.sha((RUN/'production-plan.json.gz').read_bytes())
    r.save(RUN/'production-plan-pin.json',{'sha256':digest,'claims':len(ready)})
    r.save_gz(d.BACKUP/'production-preimages.json.gz',{'plan_sha256':digest,'preimages':current})
    r.save_gz(d.BACKUP/'production-plan.json.gz',result)
    print(json.dumps({'ready':len(ready),'reuse':sum(x['reuse'] for x in prepared.values()),'new_media':sum(not x['reuse'] for x in prepared.values()),'plan_sha256':digest}),flush=True)

def backup():
    description='Before Prado WikiArt selected image attachments 20261006'
    def gc(*args):return json.loads(subprocess.check_output(['gcloud',*args,'--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True))
    rows=gc('sql','backups','list','--instance=artline-postgres','--limit=50');matching=[x for x in rows if x.get('description')==description]
    if not matching:
        op=gc('sql','backups','create','--instance=artline-postgres','--description='+description,'--async');r.save(d.BACKUP/'cloud-sql-backup-operation.json',op);print('Recovery backup requested',flush=True);return
    current=max(matching,key=lambda x:int(x['id']))
    if current['status']!='SUCCESSFUL':print('Recovery backup',current['status'],flush=True);return
    r.save(d.BACKUP/'cloud-sql-backup.json',current)
    r.save(RUN/'cloud-sql-backup.json',{'id':current['id'],'status':current['status'],'at':r.now()});print('Recovery backup verified',current['id'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['select','prepare','prepare_replacements','sheets','visual','plan','backup','upload','apply','verify'])
    command=p.parse_args().command
    {'select':select,'prepare':d.prepare,'prepare_replacements':prepare_replacements,'sheets':d.contact_sheets,'visual':visual,'plan':plan,'backup':backup,'upload':d.upload,'apply':d.apply,'verify':d.verify}[command]()
