#!/usr/bin/env python3
"""Reconcile selected public museum facts before planning database writes."""
import argparse,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('import-austrian-catalogue.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

def date(text):
    text=re.sub(r'\s+',' ',text or '').strip()
    hit=re.fullmatch(r'(um )?(\d{4})(?:\s*[–-]\s*(\d{4}))?',text)
    if not hit:raise ValueError('Official creation date needs editorial review')
    lo,hi=int(hit[2]),int(hit[3] or hit[2]);assert 1000<=lo<=hi<=1970
    return {'first':lo,'last':hi,'display':text,'precision':('circa' if lo==hi else 'circa_range') if hit[1] else ('exact' if lo==hi else 'range'),'eligible':True}

def verify(w,n):
    makers=n['makers']
    if len(makers)!=1 or makers[0]['role'] not in ('Künstler','Maler'):raise ValueError('Current official creator attribution requires review')
    match=re.fullmatch(r'(.+?) \((\d{4})—(\d{4})\)',makers[0]['name'])
    if not match or a.r.norm(match[1]) not in {a.r.norm(s) for s in w['creator_names']}:raise ValueError('Same title leads to another artist or unresolved creator identity')
    if w['creator_birth'] is not None and int(match[2])!=w['creator_birth'] or w['creator_death'] is not None and int(match[3])!=w['creator_death']:raise ValueError('Official and authority creator dates conflict')
    if 'Gemälde' not in n['facts'].get('Objektart',''):raise ValueError('Official object is not a painting')
    d=date(n['facts'].get('Datierung'));acc=n['facts'].get('Inventarnummer')
    if w['accession'] and re.sub(r'[^a-z0-9]','',w['accession'].lower())!=re.sub(r'[^a-z0-9]','',acc.lower()):raise ValueError('Different institutional accession')
    if not acc:raise ValueError('Official inventory number missing')
    if d['first']<int(match[2]) or d['last']>int(match[3]):raise ValueError('Creation date contradicts official artist lifetime')
    return d,acc

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);args=p.parse_args();run=args.run;data=json.loads((run/'wikimedia/researched-records.json').read_text());rows={x['qid']:x for x in data['records']};holds=[];verified=[];excluded=set()
    for f in (run/'wien/objects').glob('*.json'):
        n=json.loads(f.read_text());w=rows.get(n['lead']['qid'])
        if not w:continue
        try:
            d,acc=verify(w,n);w['secondary_date']=w['date'];w['date']=d;w['accession']=acc;w['primary_wien']=n;verified.append(w['qid'])
        except (AssertionError,ValueError) as exc:
            # A title-only discovery mismatch does not contradict the authority.
            # An exact native link with a source type correction does.
            direct=any(re.search(r'/objekt/'+n['object_id']+r'(?:/|-|$)',v['url']) for v in w['object_urls'])
            if direct and 'not a painting' in str(exc):excluded.add(w['qid'])
            holds.append({'qid':w['qid'],'official_url':n['url'],'reason':str(exc),'exclude_metadata':w['qid'] in excluded})
    out={'at':a.core.now(),'records':[x for q,x in rows.items() if q not in excluded],'official_wien_verified':verified,'official_review_holds':holds,'policy':'Official primary facts supersede secondary discovery fields only for new imports. Existing catalogue metadata remains unchanged.'}
    a.core.save_new(run/'metadata-input.json',out);print('Metadata candidates',len(out['records']),'primary Wien verified',len(verified),'held links',len(holds),'non-painting exclusions',len(excluded))
if __name__=='__main__':main()
