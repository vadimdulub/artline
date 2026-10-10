#!/usr/bin/env python3
"""Check modern/legacy source permalinks and accepted holding URL ownership."""
import collections,copy,importlib.util,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('delivery',ROOT/'ops/apply-random-5000-museums-20261006.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);r=m.r;RUN=m.RUN;d=m.d
def enrich(c):
    c=copy.deepcopy(c);obj=c.get('object_evidence',{}).get('reviewed_indexed_object');urls=set(c.get('duplicate_source_urls',[]))
    if not obj:return c
    url=c['source_url'];text=obj['excerpt'];native=None;scheme=None;alternates=[]
    if 'rijksmuseum.nl/'in url:
        ids=set(re.findall(r'https://id\.rijksmuseum\.nl/(\d+)',text));accs=set(re.findall(r'Object(?: number|nummer)[\s*:\|]+(SK-[A-Z]-\d+(?:-[A-Z])?)',text,re.I))
        if len(ids)==1:
            native=next(iter(ids));scheme='rijks-object';urls.add('https://id.rijksmuseum.nl/'+native)
        if len(accs)==1:
            acc=next(iter(accs));alternates.append(acc)
            urls.update('https://www.rijksmuseum.nl/'+language+'/'+acc for language in ['en/collection','nl/collectie'])
    elif 'nationalgallery.org.uk/'in url:
        ids=set(re.findall(r'\|\s*(NG\d+)\s*\|',obj['source_title']))
        if not ids:ids=set(re.findall(r'Inventory number\s+(NG\d+)',text))
        if not ids and c['artwork_id']=='a37042e5-3bfd-4e56-9dff-99f17b69dfb8'and 'NG 722'in text:ids={'NG722'}
        if len(ids)==1:native=next(iter(ids));scheme='ng-object'
        urls.update(u+'.html'for u in set(re.findall(r'https://data\.ng\.ac\.uk/[A-Z0-9-]+',text)))
    elif 'americanart.si.edu/artwork/'in url:
        q=re.search(r'-(\d+)/?$',url)
        if q:native=q[1];scheme='saam-object'
    elif 'www.nga.gov/artworks/'in url:
        q=re.search(r'/artworks/(\d+)-',url)
        if q:
            native=q[1];scheme='nga-object';urls.add('https://www.nga.gov/collection/art-object-page.'+native+'.html')
    elif 'moma.org/collection/works/'in url:
        q=re.search(r'/collection/works/(\d+)',url)
        if q:native=q[1];scheme='moma-object'
    if native:
        c['scheme']=scheme;c['external_id']=native
        if alternates:c['duplicate_native_ids']=alternates
        c['object_evidence']['native_identity_review']={'scheme':scheme,'native_id':native,'alternate_source_identifiers':alternates,'source_url_aliases':sorted(urls),'basis':'Exact identifier/permalink printed on the preserved primary object record; used for duplicate checks, not inserted as new metadata.'}
    c['duplicate_source_urls']=sorted(urls);return c

def main():
    plans={name:r.load(RUN/'primary-plans'/(name+'.json.gz'))for name in m.PROVIDERS};claims=[enrich(c)|{'origin_provider':name}for name,data in plans.items()for c in data['claims']]
    urls=sorted(set().union(*(d.claim_urls(c)for c in claims)));institutions=sorted({c['institution']['id']for c in claims})
    with r.connect('production')as db:
        owners=db.execute("SELECT h.artwork_id::text,h.institution_id::text,h.source_url FROM artwork_location_assertions h JOIN artworks a ON a.id=h.artwork_id WHERE h.institution_id=ANY(%s::uuid[]) AND h.source_url=ANY(%s) AND h.claim_type='holding' AND h.review_state='accepted' AND h.superseded_by IS NULL AND a.status<>'archived'",(institutions,urls)).fetchall()
    held=[];ready=collections.defaultdict(list)
    for c in claims:
        collisions=[o for o in owners if o['source_url']in d.claim_urls(c)and o['artwork_id']!=c['artwork_id']]
        if collisions:held.append({'artwork_id':c['artwork_id'],'provider':c['origin_provider'],'reason':'source_object_already_has_accepted_holding_on_another_record','source_url':c['source_url'],'existing_records':collisions})
        else:ready[c['origin_provider']].append(c)
    final=[]
    for name,data in plans.items():
        final.append(name+'-native-reviewed');r.save_gz(RUN/'primary-plans'/(final[-1]+'.json.gz'),{'at':r.now(),'claims':ready[name],'holds':data.get('holds',[])+[h for h in held if h['provider']==name],'supersedes':name+'.json.gz; exact source native IDs and accepted-holding URL ownership checked before writes.'})
    r.save(RUN/'final-providers.json',final);r.save_gz(RUN/'native-identity-preflight.json.gz',{'at':r.now(),'claims_considered':len(claims),'native_identifier_enrichments':sum('native_identity_review'in c.get('object_evidence',{})for c in claims),'existing_accepted_source_owners':owners,'held':held,'remaining':sum(map(len,ready.values()))})
    print('Native/holding URL audit',len(claims),'candidates',len(held),'duplicate holds',sum(map(len,ready.values())),'remaining',flush=True)
if __name__=='__main__':main()
