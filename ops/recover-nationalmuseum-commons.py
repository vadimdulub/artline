#!/usr/bin/env python3
"""Revisit bounded museum image gaps using exact museum object evidence."""
import argparse,collections,copy,fcntl,importlib.util,json,time
from pathlib import Path
from types import SimpleNamespace

s=importlib.util.spec_from_file_location('nmc',Path(__file__).with_name('followup-nationalmuseum-commons.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m);core=m.core

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--candidates',type=Path,required=True);p.add_argument('--limit',type=int,default=100);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
    lock=(a.run/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert (a.run.parent/'backups.json').exists()
    rows=json.loads(a.candidates.read_text())['records'];done={k for k,v in core.latest_events(a.run).items() if v['outcome'] in ('prepared','complete','failed','manual_review')}
    rows=[c for c in rows if c['targets']['local']['artwork_id'] not in done][:a.limit]
    fetch=m.common.core.Fetcher(a.run/'commons-evidence');render=m.common.core.Fetcher(a.run/'rendered-licences')
    for n,r in enumerate(rows,1):
        if time.time()>=a.deadline:break
        aid=r['targets']['local']['artwork_id'];c=copy.deepcopy(r);c['artwork_id']=aid;held=[];accepted=[]
        try:
            link=c['raw']['official_capture']['item'].get('ObjWikimediaLinkTxt')
            if link:titles=[m.file_title(link)]
            else:
                query='"Nationalmuseum" "'+c['external_id']+'"'
                params={'action':'query','list':'search','srsearch':query,'srnamespace':6,'srlimit':10,'srprop':''}
                discovery=m.common.api(fetch,'commons.wikimedia.org',params)
                c['raw']['commons_discovery']={'source_object_id':c['external_id'],'query':query,'response':discovery,'retrieved_at':core.now(),'source_url':'https://commons.wikimedia.org/w/api.php?'+m.common.urlencode(dict(params,format='json',maxlag=5))}
                titles=[p['title'] for p in discovery.get('query',{}).get('search',[])]
            if not titles:raise ValueError('No Commons file found for the exact museum object lead')
            data=m.common.api(fetch,'commons.wikimedia.org',{'action':'query','titles':'|'.join(titles),'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main'})
            for page in data.get('query',{}).get('pages',{}).values():
                if not page.get('imageinfo'):continue
                try:
                    local=copy.deepcopy(c);rendered=m.common.rendered_rights_uri(render,page)
                    local['rendered_identity_evidence']=m.rendered_identity(render,page);local['creator_alias_evidence']=m.creator_alias(fetch,local,page)
                    sid='M'+str(page['pageid']);sdc=m.common.api(fetch,'commons.wikimedia.org',{'action':'wbgetentities','ids':sid,'props':'claims'})['entities'][sid]
                    url,credit,pageurl=m.verify_file(local,page,rendered,sdc)
                    raw={'lead':r['raw']['lead'],'official_capture':m.project_capture(r['raw']['official_capture']),'commons_file':m.project_file(page),'structured_data':sdc}
                    if c['raw'].get('commons_discovery'):raw['commons_discovery']=c['raw']['commons_discovery']
                    im=dict(r,raw=raw,provider=m.PROVIDER,scheme=r.get('scheme',m.nm.SCHEME),artwork_id=aid,slug=r['targets']['local']['slug'],target_ids={t:v['artwork_id'] for t,v in r['targets'].items()},source_record_url=r['page'],source_name=core.PROVIDERS[m.PROVIDER],source_object_id=r['external_id'],page=pageurl,source_image_url=url,policy_url=m.nm.PDM,rights_status='public_domain',license_label='Public Domain Mark 1.0',creator_credit=credit,attribution_text=f"{r['artist']}. {r['title']}. {credit}. {pageurl}. Public Domain Mark ({m.nm.PDM}). Full-frame proportional resize and JPEG compression.",rendered_licence_evidence=rendered,rendered_identity_evidence=local['rendered_identity_evidence'],creator_alias_evidence=local['creator_alias_evidence'],checked_at=core.now(),rights_verified_at=core.now(),creation_date=r['date_display'])
                    im.update(image_url=url,image_license='Public Domain Mark 1.0',image_license_url=m.nm.PDM,rights_statement='Public Domain Mark 1.0')
                    for key in ('photo_credit','media_native_id','rights_error','prior_hold_reason'):im.pop(key,None)
                    m.verify(im);accepted.append(im)
                except ValueError as exc:held.append({'pageid':page.get('pageid'),'reason':str(exc)})
            core.save_new(a.run/'research'/(aid+'.json'),{'at':core.now(),'artwork_id':aid,'source_object_id':c['external_id'],'candidate_files':len(titles),'verified_files':len(accepted),'held':held})
            if len(accepted)!=1:raise ValueError('No unique verified full artwork file; manual selection required')
            im=accepted[0];core.save_new(a.run/'selected'/m.PROVIDER/(aid+'.json'),im)
            core.worker(m.PROVIDER,[im],SimpleNamespace(run=a.run,prepare_only=True),None)
        except ValueError as exc:
            core.event(a.run,{'provider':m.PROVIDER,'artwork_id':aid,'external_id':r['external_id'],'outcome':'manual_review','reason':str(exc)})
        print(core.now(),'Recovery',n,'of',len(rows),dict(core.COUNTS),flush=True)

if __name__=='__main__':main()
