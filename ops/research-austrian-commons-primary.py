#!/usr/bin/env python3
"""Batch-check primary Commons file evidence for already selected painting gaps."""
import argparse,collections,importlib.util,json
from pathlib import Path
from types import SimpleNamespace
s=importlib.util.spec_from_file_location('images',Path(__file__).with_name('austrian-collection-images.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
m=a.m;core=a.core

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=1000);args=p.parse_args();run=args.run/'images-research';rows=json.loads((run/'candidates.json').read_text())['candidates'];done=core.latest_events(run);rows=[c for c in rows if c['provider']=='austria-commons' and done.get(c['artwork_id'],{}).get('outcome') not in ('prepared','complete')];rows.sort(key=lambda c:(not c['popular'],c['museum'],c['artist'],c['title']));fetch=core.Fetcher(run/'metadata');rows=rows[:args.limit]
    for start in range(0,len(rows),10):
        batch=rows[start:start+10];selected=[]
        for c in batch:
            try:
                e=json.loads((args.run/'wikimedia/entities'/(c['qid']+'.json')).read_text())['entity'];title='File:'+m.entity_match(c,e);selected.append((c,e,title))
            except (ValueError,KeyError,AssertionError) as exc:core.event(run,{'provider':c['provider'],'artwork_id':c['artwork_id'],'qid':c['qid'],'outcome':'manual_review','reason':str(exc),'strategy':'primary_file'})
        if not selected:continue
        try:
            response=m.api(fetch,'commons.wikimedia.org',{'action':'query','titles':'|'.join(t for c,e,t in selected),'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main'})
            pages=[p for p in response.get('query',{}).get('pages',{}).values() if p.get('imageinfo')];mids=['M'+str(p['pageid']) for p in pages];structured=m.api(fetch,'commons.wikimedia.org',{'action':'wbgetentities','ids':'|'.join(mids),'props':'claims'})['entities'] if mids else {};bytitle={p['title'].replace('_',' '):p for p in pages}
            normalized={v['from'].replace('_',' '):v['to'].replace('_',' ') for v in response.get('query',{}).get('normalized',[])}
        except Exception as exc:
            print(core.now(),'Commons batch paused',type(exc).__name__,str(exc)[:180],flush=True);break
        for c,e,title in selected:
            try:
                page=bytitle.get(normalized.get(title.replace('_',' '),title.replace('_',' ')))
                if not page:raise ValueError('Primary Commons file unavailable')
                sdc=structured.get('M'+str(page['pageid']),{});a.photo.exact_photo(c,page,sdc)
                if m.origin.verify(c,page)!='independent_photographer':raise ValueError('Native Austrian image origin requires exact museum media rights review')
                rendered=m.rendered_rights_uri(fetch,page);im=a.photo.candidate_image(c,e,page,sdc,rendered,{'method':'Exact Wikidata P18 file, independently verified Commons physical-object statement and per-image rights','retrieved_at':core.now()});im['provider']='austria-commons';a.verify(im)
                core.save_new(run/'selected'/im['provider']/(im['artwork_id']+'.json'),im);core.worker(im['provider'],[c],SimpleNamespace(run=run,prepare_only=True),None)
            except (ValueError,KeyError,AssertionError) as exc:core.event(run,{'provider':c['provider'],'artwork_id':c['artwork_id'],'qid':c['qid'],'outcome':'manual_review','reason':str(exc),'strategy':'primary_file'})
            except Exception as exc:
                core.event(run,{'provider':c['provider'],'artwork_id':c['artwork_id'],'qid':c['qid'],'outcome':'temporary_error','reason':str(exc)[:200],'strategy':'primary_file'});print(core.now(),'Source paused',type(exc).__name__,flush=True);return
        print(core.now(),'Primary Commons batch',min(start+10,len(rows)),'of',len(rows),dict(collections.Counter(v['outcome'] for v in core.latest_events(run).values())),flush=True)
if __name__=='__main__':main()
