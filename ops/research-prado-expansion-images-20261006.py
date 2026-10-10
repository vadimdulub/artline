#!/usr/bin/env python3
"""Bounded metadata research for the explicitly selected Prado paintings."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('expansion','ops/expand-prado-catalogue-20261006.py')
cm=module('commons','ops/overnight-commons-images.py');r=m.r
RUN=m.RUN/'images'

def metadata():
    plan=r.load(m.RUN/'production-plan.json.gz');selected=[]
    qcount=collections.Counter(q for x in plan['records']for q in x['wikidata_ids'])
    for x in plan['records']:
        old=plan['preimages'].get(x['artwork_id'])
        if old and old['artwork']['primary_media_id']:continue
        if x['date']['review']or x['date']['last']is None or x['date']['last']>1955:continue
        if any(qcount[q]>1 for q in x['wikidata_ids']):continue
        for link in x['image_leads']:
            filename=unquote(link.split('Special:FilePath/',1)[1])
            selected.append({'artwork_id':x['artwork_id'],'accession':x['accession'],'source_id':x['source_id'],'qid':x['wikidata_ids'],'title':x['object']['Título'],'creator':x['creator_label'],'filename':filename})
    r.save(RUN/'selected-image-leads.json',selected)
    names=list(dict.fromkeys(x['filename']for x in selected));fetch=cm.core.Fetcher(RUN/'commons-captures');fetch.defer_long_cooldowns=True
    for start in range(0,len(names),20):
        chunk=names[start:start+20];dest=RUN/'commons-batches'/f'{start:05}.json'
        if dest.exists():continue
        try:
            data=cm.api(fetch,'commons.wikimedia.org',{'action':'query','titles':'|'.join('File:'+n for n in chunk),'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main','redirects':1})
            r.save(dest,{'at':r.now(),'filenames':chunk,'response':data})
        except Exception as e:
            r.save(RUN/'metadata-interruption.json',{'at':r.now(),'offset':start,'error':type(e).__name__+': '+str(e)[:300]});raise
        if start%200==0:print('Image metadata',min(start+20,len(names)),'/',len(names),flush=True)
    print('Image metadata complete',len(names),flush=True)

def review():
    candidates=r.load(RUN/'commons-origin-selected.json.gz');plan=r.load(m.RUN/'production-plan.json.gz');by={x['artwork_id']:x for x in plan['records']}
    artists={a['id']:a for a in r.load(m.RUN/'production-baseline.json.gz')['artists']}
    artist_qids={e['entity_id']:e['external_id']for e in r.load(m.RUN/'production-artist-wikidata.json.gz')}
    fetch=cm.core.Fetcher(RUN/'commons-rights-captures');fetch.defer_long_cooldowns=True
    sdc={}
    for start in range(0,len(candidates),40):
        chunk=candidates[start:start+40];data=cm.api(fetch,'commons.wikimedia.org',{'action':'wbgetentities','ids':'|'.join('M'+str(x['page']['pageid'])for x in chunk),'props':'claims'});sdc.update(data['entities'])
    approved=[];held=[]
    for n,item in enumerate(candidates,1):
        lead=item['lead'];p=item['page'];x=by[lead['artwork_id']];dest=RUN/'rights-decisions'/(x['artwork_id']+'.json')
        if dest.exists():
            d=r.load(dest)
            if d['outcome']=='selected':approved.append(d)
            else:held.append(d)
            continue
        try:
            assert len(lead['qid'])==1,'Multiple object authorities need manual review'
            a=artists.get(x['artist_id'],{});death=a.get('death_year')
            meta=p['imageinfo'][0].get('extmetadata',{});text=p.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
            # An old work does not by itself establish a modern painter's death.
            if x['date']['last']>1830 and (death is None or death>1945):
                matches=re.findall(r'\b(?:deathyear|death year)\s*=\s*(\d{4})\b',text,re.I)
                if not matches or any(int(y)>1945 for y in matches):raise ValueError('Underlying artwork needs individual term/permission evidence')
            c={'qid':lead['qid'][0],'accession_number':x['accession'],'artist':x['creator_label']or'',
              'creators':[{'name':a['display_name'],'death':death,'qid':artist_qids.get(a['id'],'unresolved-authority')}]if a else[],
              'institution_slug':'museo-del-prado','website_url':'https://www.museodelprado.es/',
              'native_identifiers':[{'url':x['object']['url']}]}
            entity={'labels':{'es':{'value':x['object']['Título']}}}
            structured=sdc['M'+str(p['pageid'])];rendered=cm.rendered_rights_uri(fetch,p)
            info,credit,label,uri,status,image,original=cm.rights_and_identity(c,entity,p,structured,rendered)
            result={'outcome':'selected','at':r.now(),'lead':lead,'page':p,'structured_data':structured,'rendered_licence_evidence':rendered,
              'source_image_url':image,'source_page_url':info['descriptionurl'],'creator_credit':credit,'license_label':label,'policy_url':uri,'rights_status':status,
              'origin':item['origin'],'identity_basis':'Exact Commons physical-object link or exact corroborated museum inventory, linked through Prado-native ID; file rights and independent origin checked separately.',
              'underlying_work_basis':{'source_creation':x['date'],'reconciled_creator_death_year':death,'commons_deathyear':matches if x['date']['last']>1830 and(death is None or death>1945)else[]}}
            r.save(dest,result);approved.append(result)
        except Exception as exc:
            result={'outcome':'held','at':r.now(),'lead':lead,'reason':type(exc).__name__+': '+str(exc)[:350]};r.save(dest,result);held.append(result)
        if n%10==0:print('Image rights reviewed',n,'/',len(candidates),'selected',len(approved),flush=True)
    r.save_gz(RUN/'commons-reviewed-selection.json.gz',{'approved':approved,'held':held});print('Image rights complete',len(approved),'selected',len(held),'held',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['metadata','review']);globals()[p.parse_args().command]()
