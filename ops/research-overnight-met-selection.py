#!/usr/bin/env python3
"""Fresh API verification for a bounded, preselected Met metadata batch; no DB writes."""
import argparse,collections,concurrent.futures,importlib.util,json,re,time,uuid
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('campaign',ROOT/'ops/overnight-image-campaign.py');campaign=importlib.util.module_from_spec(s);s.loader.exec_module(campaign);core=campaign.core
CC0='https://creativecommons.org/publicdomain/zero/1.0/'
def norm(v):return ' '.join(re.findall(r'\w+',str(v or '').casefold()))
def date_fields(o):
    lo,hi=o.get('objectBeginDate'),o.get('objectEndDate');text=o.get('objectDate','').strip()
    if not isinstance(lo,int) or not isinstance(hi,int) or not 1000<=lo<=hi<=1970:raise ValueError('Creation bounds outside scope or absent')
    if not text or re.search(r'\b(?:undated|unknown|n\.?d\.?|before|after|since|earlier|later|posthumous|restrike)\b',text,re.I):raise ValueError('Date wording requires individual review')
    text_years={int(y) for y in re.findall(r'(?<!\d)(\d{4})(?!\d)',text)}
    if any(y<1000 or y>1970 for y in text_years):raise ValueError('Source text includes a creation/edition date outside scope')
    if not (re.search(r'\d{4}',text) or re.search(r'\d{1,2}(?:st|nd|rd|th)[ -]+century',text,re.I)):raise ValueError('Source date text not independently interpretable')
    if lo!=hi and str(lo)==str(o.get('artistBeginDate','')).strip() and str(hi)==str(o.get('artistEndDate','')).strip():raise ValueError('Creation bounds repeat creator lifespan')
    approximate=bool(re.search(r'(?<!\w)(?:(?:c|ca)\.|(?:circa|about|probably|possibly|approximately|early|mid|late)\b)|[?\[\]]',text,re.I))
    if re.fullmatch(r'\d{4}',text):
        if (lo,hi)!=(int(text),int(text)):raise ValueError('Exact source text and index bounds differ')
        precision='exact'
    elif re.search(r'\d{1,2}(?:st|nd|rd|th)[ -]+century',text,re.I):precision='century' if not approximate else 'circa_range'
    elif re.fullmatch(r'\d{3}0s',text):precision='decade'
    elif not approximate and lo==hi and text_years=={lo}:precision='exact'
    else:precision=('circa' if lo==hi else 'circa_range') if approximate else ('range' if lo!=hi else 'circa')
    return {'creation_year_start':lo,'creation_year_end':hi,'date_precision':precision,'date_display':text}

def verify(lead,o):
    csv=lead['object'];oid=csv['Object ID'];artist=lead['artist']
    if str(o.get('objectID'))!=oid:raise ValueError('Fresh object ID differs')
    if o.get('isPublicDomain') is not True or o.get('rightsAndReproduction'):raise ValueError('No explicit fresh open-access image rights')
    image=o.get('primaryImageSmall','')
    if urlparse(image).scheme!='https' or urlparse(image).hostname!='images.metmuseum.org':raise ValueError('No approved primary source image')
    if not o.get('accessionNumber') or o['accessionNumber']!=csv['Object Number']:raise ValueError('Current accession differs')
    if o.get('artistPrefix','').strip() or o.get('artistSuffix','').strip():raise ValueError('Qualified attribution requires separate support')
    if o.get('artistWikidata_URL','').rstrip('/').rsplit('/',1)[-1]!=artist['qid']:raise ValueError('Current artist authority differs')
    makers=[c for c in o.get('constituents',[]) or [] if c.get('role') in ('Artist','Painter','Maker')]
    if len(makers)!=1 or makers[0].get('constituentWikidata_URL','').rstrip('/').rsplit('/',1)[-1]!=artist['qid']:raise ValueError('Unique primary maker authority not confirmed')
    if re.search(r'\b(?:loan|lent)\b',o.get('creditLine',''),re.I):raise ValueError('Loan holding requires fresh individual evidence')
    if 'Metropolitan Museum of Art' not in o.get('repository',''):raise ValueError('Museum repository not confirmed')
    page=o.get('objectURL','');parts=urlparse(page)
    if parts.scheme!='https' or parts.hostname!='www.metmuseum.org' or not parts.path.endswith('/'+oid):raise ValueError('Stable official object page differs')
    dates=date_fields(o);candidate=dict(dates,work_type=lead['work_type']);campaign.fresh_scope('met',o,candidate)
    qid=o.get('objectWikidata_URL','').rstrip('/').rsplit('/',1)[-1];qid=qid if re.fullmatch(r'Q\d+',qid or '') else None
    aid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/night-selected-met/'+oid))
    return {'artwork_id':aid,'slug':'night-met-'+oid,'title':o['title'],**dates,'work_type':lead['work_type'],'accession_number':o['accessionNumber'],'scheme':'met-object','external_id':oid,'provider':'met',
       'artist':artist['display_name'],'artist_id':artist['id'],'artist_slug':artist['slug'],'artist_qid':artist['qid'],'popular':artist['popular'],'qid':qid,'object':o,'source_image_url':image,'page':page,'metadata_license':CC0}

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=0);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();rows=json.loads((a.run/'source-candidates.json').read_text());rows=rows[:a.limit] if a.limit else rows
    pending=[c for c in rows if not (a.run/'verified'/(c['object']['Object ID']+'.json')).exists() and not (a.run/'review-held'/(c['object']['Object ID']+'.json')).exists()];counts=collections.Counter()
    def batch(stripe):
        fetcher=core.Fetcher(a.run/'fresh-api')
        for lead in stripe:
            if time.time()>=a.deadline:return
            oid=lead['object']['Object ID'];url='https://collectionapi.metmuseum.org/public/collection/v1/objects/'+oid
            try:
                o=fetcher.metadata(url);c=verify(lead,o);capture=json.loads((fetcher.cache/(core.sha(url.encode())+'.receipt.json')).read_text());c['metadata_capture']=capture
                core.save_new(a.run/'verified'/(oid+'.json'),c);outcome='verified'
            except ValueError as e:
                core.save_new(a.run/'review-held'/(oid+'.json'),{'at':core.now(),'object_id':oid,'reason':str(e)});outcome='needs_review'
            except Exception as e:
                with (a.run/'api-errors.jsonl').open('ab') as f:f.write(core.encode({'at':core.now(),'object_id':oid,'error':str(e)[:250]})+b'\n')
                outcome='api_error'
            with core.LOCK:
                counts[outcome]+=1
                if sum(counts.values())%100==0:print(core.now(),'Met fresh source review',sum(counts.values()),'of',len(pending),dict(counts),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for future in [pool.submit(batch,pending[n::4]) for n in range(4) if pending[n::4]]:future.result()
    print(core.now(),'Met source review pass finished',dict(counts),flush=True)
if __name__=='__main__':main()
