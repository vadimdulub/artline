#!/usr/bin/env python3
"""Prepare licensed images for the pinned Spanish selection; never uploads."""
import argparse, importlib.util, json, re, uuid
from pathlib import Path
from types import SimpleNamespace
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('research',ROOT/'ops/research-spain-deep.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
m=r.m;core=m.core;RUN=r.RUN/'images'

def final_origin_hold(im):
    page=im['raw']['commons'];meta=page['imageinfo'][0]['extmetadata']
    credit=' '.join(meta.get(k,{}).get('value','') for k in ('Credit','Attribution'))
    markup=page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
    if re.search(r'artsdot\.com',credit,re.I):return 'Mixed institutional and unverified commercial mirror provenance'
    # A museum domain is provenance, never evidence of a Wikimedia donation.
    donated=re.search(r'(?:provided|donated|cedid[ao]s?).{0,250}(?:Wikimedia|Commons)',credit+' '+markup,re.I)
    if re.search(r'museodelprado|cdnprado',credit,re.I) and not donated:
        return 'Prado website reproduction requires separate permission; no explicit donation evidence'
    return None

def candidates():
    rows=[];held=[];cache={}
    for x in r.load('selected-metadata-final-v2.json')['records']:
        q=x['qid'];d=x['date']
        if x.get('existing') and x['existing']['primary_media_id']:reason='Existing image preserved'
        elif not d['eligible'] or d['first'] is None:reason='Creation date requires review'
        elif not x['image_names']:reason='No source primary-image lead'
        elif x['death'] is None or x['death']>1945:reason='Underlying artwork rights require individual permission; no automatic Spanish life-plus-80 clearance'
        else:reason=None
        if reason:held.append({'qid':q,'reason':reason});continue
        ident=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/spain-deep/'+q))
        row={'qid':q,'external_id':q,'artwork_id':ident,'slug':'spain-research-'+q.lower(),'title':x['title'],'alternate_title':None,'creation_year_start':d['first'],'creation_year_end':d['last'],'date_precision':d['precision'],'date_display':d['display'],'work_type':'painting','accession_number':x['accession'],'institution_qid':x['institution_qid'],'institution_slug':'spain-source-'+x['institution_qid'].lower(),'website_url':next(iter(x['institution_websites']),None),'creators':[{'qid':x['creator_qid'],'name':x['creator_name'],'death':x['death']}],'artist':x['creator_name'],'provider':'night-commons','scheme':'wikidata'}
        rows.append(row);entity_path=r.RUN/'enriched-title-entities'/(q+'.json') if x.get('title_enriched') else r.w.RUN/'entities'/(q+'.json');cache[q]=[str(entity_path.relative_to(ROOT))]
    core.save_new(RUN/'candidates.json',{'candidates':rows});core.save_new(RUN/'selection-held.json',held);core.save_new(RUN/'existing-authority-cache-index.json',cache)
    return rows

def prepare():
    rows=json.loads((RUN/'candidates.json').read_text())['candidates'] if (RUN/'candidates.json').exists() else candidates()
    fetch=core.Fetcher(RUN/'metadata/commons-evidence');latest=core.latest_events(RUN)
    rows=[x for x in rows if latest.get(x['artwork_id'],{}).get('outcome') not in ('prepared','manual_review')]
    for start in range(0,len(rows),10):
        group=rows[start:start+10]
        try:
            ready=[x for x in group if (RUN/'selected/night-commons'/(x['artwork_id']+'.json')).exists()]
            fresh=[x for x in group if x not in ready]
            if fresh:ready+=m.research_chunk(fresh,RUN,fetch)
        except Exception as exc:
            r.log('Source group deferred',type(exc).__name__,str(exc)[:200]);continue
        allowed=[]
        for x in ready:
            p=RUN/'selected/night-commons'/(x['artwork_id']+'.json');im=json.loads(p.read_text());page=im['raw']['commons'];meta=page['imageinfo'][0]['extmetadata']
            credit=' '.join(meta.get(k,{}).get('value','') for k in ('Credit','Attribution'))
            markup=page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
            # Prado website reproduction terms are distinct from its expressly
            # donated Commons files and independent visitor photographs.
            hold=final_origin_hold(im)
            if hold:
                core.event(RUN,{'artwork_id':x['artwork_id'],'external_id':x['qid'],'outcome':'manual_review','reason':hold});continue
            allowed.append(x)
        if allowed:core.worker('night-commons',allowed,SimpleNamespace(run=RUN,prepare_only=True),None)
        r.log('Image candidates checked',min(start+10,len(rows)),'/',len(rows),'licensed',len(allowed))
    manifest=[json.loads(p.read_text()) for p in sorted((RUN/'images/night-commons').glob('*.json'))]
    core.save_new(RUN/'prepared-manifest.json',manifest);r.log('Prepared images',len(manifest))

def gallery():
    manifest=json.loads((RUN/'prepared-manifest.json').read_text());folder=Path('/tmp/artline-spain-image-qa');folder.mkdir(exist_ok=True)
    for start in range(0,len(manifest),24):
        sheet=Image.new('RGB',(1440,1200),'#eee9df');draw=ImageDraw.Draw(sheet)
        for n,x in enumerate(manifest[start:start+24]):
            im=Image.open(ROOT/'apps/web/public'/x['path'].lstrip('/'));im.thumbnail((230,235));cx=(n%6)*240;cy=(n//6)*300
            sheet.paste(im,(cx+(240-im.width)//2,cy));label=f"{start+n+1} {x['qid']}\n{x['artist'][:31]}\n{x['title'][:34]}"
            draw.multiline_text((cx+4,cy+240),label,fill='black',spacing=3)
        sheet.save(folder/f'sheet-{start//24+1:02d}.jpg')
    core.save_new(RUN/'gallery-index.json',[{'n':i+1,'qid':x['qid'],'path':x['path'],'artist':x['artist'],'title':x['title']} for i,x in enumerate(manifest)])
    r.log('QA sheets',str(folder))

def quality():
    """Record completed visual review and enforce final provenance exclusions."""
    import hashlib
    manifest=json.loads((RUN/'prepared-manifest.json').read_text())
    held={x['qid']:why for x in manifest if (why:=final_origin_hold(x))}
    assert len(manifest)==302 and len(held)==210
    # The domain alone must never pass the donation exception.
    assert 'Q59782438' in held and 'Q19162929' not in held
    index=json.loads((RUN/'gallery-index.json').read_text());assert len(index)==len(manifest)
    for x in manifest:
        path=ROOT/'apps/web/public'/x['path'].lstrip('/');raw=path.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==x['sha256'] and len(raw)<=100000
        assert x['policy_url'] and x['creator_credit'] and x['creation_year_end']<=1970
        assert all(c['death'] is not None and c['death']<=1945 for c in x['creators'])
        with Image.open(path) as im:assert im.size==(x['width'],x['height']) and im.format=='JPEG'
    path=r.RUN/'delivery-plan.json';plan=json.loads(path.read_text());old=r.RUN/'delivery-plan-before-visual-review.json'
    if not old.exists():
        path.rename(old)
        for t in plan['targets'].values():
            st=next(x for x in t['states'] if x['qid']=='Q59782438');assert st['new']
            t['states']=[x for x in t['states'] if x['qid']!='Q59782438']
            t['held'].append({'qid':'Q59782438','reason':'Duplicate physical painting of selected Q19162929: Prado ownership and Víctor Balaguer deposit are separate relationships, not separate objects. Matched composition, artist and documented deposit; no authority merge performed.'})
        plan['visual_identity_review']={'excluded_duplicate':'Q59782438','retained_source_record':'Q19162929','sources':['https://www.museodelprado.es/coleccion/obra-de-arte/san-benito-destruyendo-los-idolos/9df62082-273c-45fb-b107-e0f5025f086f','https://www.vilanova.cat/noticies/detall?id=99995249'],'inference':'Identical composition and creator, Prado deposit declaration, and municipal museum report describing this painting among Prado deposits. Historical display evidence does not assert current display.'}
        r.save('delivery-plan.json',plan)
    a,b=[plan['targets'][t]['states'] for t in ('local','production')]
    assert [(x['qid'],x['new']) for x in a]==[(x['qid'],x['new']) for x in b]
    sheets=[str(p) for p in sorted(Path('/tmp/artline-spain-image-qa').glob('sheet-*.jpg'))];assert len(sheets)==13
    r.save('quality-review.json',{'at':core.now(),'approved':True,'plan_sha256':core.sha(path.read_bytes()),'images_sha256':core.sha((RUN/'prepared-manifest.json').read_bytes()),'visually_inspected_images':302,'contact_sheets':sheets,'held_images':held,'visual_notes':'All 13 sheets inspected: paintings correctly oriented and legible, no error pages or blank placeholders. Frames and one museum colour reference retained without crop. One duplicated composition across Prado and deposit museum checked and excluded from new-record delivery.','provenance_correction':'Original Prado donation exception incorrectly matched the museum domain itself. Corrected before catalogue writes or uploads; 209 Prado files and one commercial mirror withheld. Original preparation events preserved as research history, not final approval.','identity_review':plan['visual_identity_review'],'checks':['All served-file candidates JPEG, checksum and dimensions verified, at most 100000 bytes','Explicit per-file licence URI and credit present','Underlying creator chronology checked separately','Matching local/production object actions; independent existing IDs preserved']})
    r.log('Quality approved;',len(manifest)-len(held),'image files eligible,',len(a),'metadata records')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','gallery','quality']);a=p.parse_args();globals()[a.phase]()
