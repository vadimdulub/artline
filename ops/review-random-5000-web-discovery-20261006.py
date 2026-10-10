#!/usr/bin/env python3
"""Conservative evidence extraction from preserved, indexed museum records."""
import argparse,collections,gzip,hashlib,importlib.util,json,re,unicodedata,uuid
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('task',ROOT/'ops/random-5000-museum-research-20261006.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);r=m.r;RUN=m.RUN
def norm(x):return ' '.join(re.findall(r'[^\W_]+',''.join(c for c in unicodedata.normalize('NFKD',x or '').casefold()if not unicodedata.combining(c))))
def host(x):return (urlsplit(x or '').hostname or '').removeprefix('www.')
def statements(e,p):
    values=[x for x in e.get('claims',{}).get(p,[])if x.get('rank')!='deprecated'and 'P582'not in x.get('qualifiers',{})];preferred=[x for x in values if x.get('rank')=='preferred'];return preferred or values
def value(s):
    x=s.get('mainsnak',{}).get('datavalue',{}).get('value');return x.get('id')if isinstance(x,dict)and'id'in x else x

def inventory_match(number,text):
    needle=norm(number);hay=norm(text)
    if not needle:return False
    if re.search(r'(?<!\w)'+re.escape(needle)+r'(?!\w)',hay)is None:return False
    if len(needle)>=5 and re.search('[a-z]',needle):return True
    # Short/numeric inventory values require an explicit field label, so dates
    # and dimensions cannot accidentally become accession correspondence.
    return bool(re.search(r'(?:accession|inventory|inventaire|inventario|catalogue number|object number|inv|identification number)\s+(?:no\s+|number\s+)?'+re.escape(needle)+r'(?!\w)',hay))

def run():
    rows=r.load(RUN/'baseline.json.gz');ii=r.load(RUN/'institutions.json.gz');original_ids={i['id']for i in ii};ii+=r.load(RUN/'wikiart-holding-plan-v3.json.gz')['new_institutions'];byid={i['id']:i for i in ii};byqid={i['wikidata_id']:i for i in ii if i.get('wikidata_id')};byhost=collections.defaultdict(list)
    for i in ii:
        if i.get('website_url')and host(i['website_url'])not in ['pop.culture.gouv.fr','wikidata.org','commons.wikimedia.org']:byhost[host(i['website_url'])].append(byid.get(i.get('canonical_institution_id'),i))
    wd=r.load(RUN/'wikidata-entities.json.gz');supplied={x['artwork_id']:x['raw_json']['csv']['cells']for x in r.load(RUN/'supplied-research-links.json.gz')};wiki=r.load(RUN/'cached-wikiart-results-supplement.json.gz');authorities=r.load(RUN/'cached-institution-authorities.json.gz')
    authority_resolutions={}
    for q,a in authorities.items():
        if q in byqid:continue
        e=a['entity'];types={value(x)for x in statements(e,'P31')};sites=[value(x)for x in statements(e,'P856')if isinstance(value(x),str)];label=e.get('labels',{}).get('en',{}).get('value');names={norm(v['value'])for v in e.get('labels',{}).values()}|{norm(v['value'])for group in e.get('aliases',{}).values()for v in group}
        if not label or not sites or not types.intersection({'Q33506','Q207694'}):continue
        if re.search(r'museums service|museum service|network|collections service',label,re.I):continue
        generic={'national gallery','national portrait gallery','national museum','museum of fine arts'}
        named=[i for i in ii if norm(i['name'])in names or(i['id']not in original_ids and norm(re.sub(r'\([^)]*\)','',i['name'].split(',')[0]).strip()) not in generic and norm(re.sub(r'\([^)]*\)','',i['name'].split(',')[0]).strip())in names)]
        samehost={i['id']:i for u in sites for i in byhost[host(u)]}
        if len(named)==1 and (named[0]['id']not in original_ids or named[0]['id']in samehost):i=named[0]
        elif named or samehost:continue
        else:
            i={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/random-5000-museums-20261006/institution/'+q)),'slug':'museum-research-'+q.lower(),'name':label,'normalized_name':norm(label),'website_url':sites[0],'wikidata_id':q,'kind':'museum','status':'review','description':'Museum identity from a preserved Wikidata museum/art-museum authority with an official website, corroborated by the selected primary catalogue record. No display claim.','canonical_institution_id':None}
            byid[i['id']]=i
        byqid[q]=i
        for site in sites:
            if host(site)not in ['artuk.org','wikidata.org','wikipedia.org']:byhost[host(site)].append(i)
        authority_resolutions[q]={'institution':i,'authority_path':a['path'],'authority_receipt':a['receipt']}
    candidates=collections.defaultdict(dict);related=collections.defaultdict(dict);searched=set();stats=collections.Counter()
    for path in sorted((RUN/'web-discovery').glob('*.json')):
        d=r.load(path);searched.update(q['artwork_id']for q in d['queries']);text=d['result'];stats['batches']+=1
        blocks=re.split(r'-{20,}',text)
        for block in blocks:
            match=re.match(r'\s*(.*?)\s*\((https?://[^\n]+)\)\n',block)
            if not match:continue
            url=match[2];sourcehost=host(url);plain=norm(block);source_title=match[1]
            # Native catalogue detail pages, not news, exhibitions or shops.
            detail=bool(re.search(r'/(?:artworks?|objects?|paintings?|works?|detail|notice/joconde|ark[:%]|collection/[^/]+/[^/]+|collections/search/portrait/)',url,re.I))and not re.search(r'/(?:search|artists|node|news|events|exhibitions|stories|shop)(?:/|\?)',url,re.I)and sourcehost!='salons.musee-orsay.fr'
            for q in d['queries']:
                aid=q['artwork_id'];a=rows[aid]['artwork'];title=norm(q['title']);creator=q['creator'];names=[norm(x['name'])for x in rows[aid]['creator_keys']]
                if not names and creator:names=[norm(creator)]
                stop={'by','possibly','attributed','to','after','workshop','of','school','and','the','unknown','circle','follower','copy','da','de','van','von'}
                names=[{x for x in n.split()if len(x)>1 and x not in stop and not x.isdigit()}for n in names];words=set(plain.split())
                creatorok=any(n and n<=words for n in names);titleok=bool(title and title in plain)
                if not titleok or not creatorok:continue
                possible=[]
                for hostname,items in byhost.items():
                    if sourcehost==hostname or sourcehost.endswith('.'+hostname):possible.extend(items)
                qids=[e['external_id']for e in rows[aid]['identifiers']if e['scheme']=='wikidata'];collections_=set();inventory=set();native_urls=set();physical_types=set()
                for qid in qids:
                    if qid not in wd:continue
                    e=wd[qid]['entity'];collections_.update(value(x)for x in statements(e,'P195'));inventory.update(str(value(x))for x in statements(e,'P217')if isinstance(value(x),str));physical_types.update(value(x)for x in statements(e,'P31'))
                    for st in statements(e,'P1679'):native_urls.add('https://artuk.org/discover/artworks/'+str(value(st)))
                    for st in statements(e,'P973'):
                        if isinstance(value(st),str):native_urls.add(value(st))
                    for st in statements(e,'P195'):
                        for ref in st.get('references',[]):
                            native_urls.update(snak.get('datavalue',{}).get('value')for snak in ref.get('snaks',{}).get('P854',[])if isinstance(snak.get('datavalue',{}).get('value'),str))
                exact_source_url=url.rstrip('/')in {u.rstrip('/')for u in native_urls}|{e.get('canonical_url','').rstrip('/')for e in rows[aid]['identifiers']}
                if sourcehost=='artuk.org'and len(collections_)==1 and next(iter(collections_))in byqid:
                    i=byqid[next(iter(collections_))]
                    if norm(i['name'])in plain:possible.append(i)
                possible={i['id']:i for i in possible}
                if len(possible)>1:
                    narrowed={k:i for k,i in possible.items()if (i.get('wikidata_id')in collections_)or norm(i['name'])in plain or (supplied.get(aid)and norm(i['name'])==norm(supplied[aid][3]))}
                    if len(narrowed)==1:possible=narrowed
                expected_collection=len(possible)==1 and any(byqid.get(q,{}).get('id')in possible for q in collections_)
                invok=inventory_match(a.get('accession_number'),block)or bool((exact_source_url or expected_collection)and any(inventory_match(n,block)for n in inventory))
                year=a.get('creation_year_start');yearok=year is not None and bool(re.search(r'(?<!\d)'+str(year)+r'(?!\d)',block))
                dimensions=a.get('dimensions_text')or '';dimnums=re.findall(r'\d+(?:[.,]\d+)?',dimensions);dimok=len(dimnums)>=2 and all(v.replace(',','.')in block.replace(',','.')for v in dimnums[:2])
                qualified=bool(re.search(r'\b(?:on loan|lent by|loan from|bruikleen|leihgabe|deaccessioned|restituted|destroyed|private collection|stolen|present whereabouts unknown)\b',block,re.I))
                edition=(a['work_type']=='print'or bool(re.search(r'\b(?:etching|engraving|woodcut|woodblock|lithograph|screenprint|linocut|aquatint)\b',block,re.I)))and not(exact_source_url or invok)
                supplied_museum=norm(supplied[aid][3])if supplied.get(aid)else ''
                museum_agrees=len(possible)==1 and re.sub(r'^the ','',supplied_museum)==re.sub(r'^the ','',norm(next(iter(possible.values()))['name']))
                header_matches=title in norm(source_title)
                generic_title=title in {'portrait of a man','portrait of a woman','still life with fruit','the judgment of paris','l adoration des bergers','portrait of a lady','portrait of a gentleman'}
                enough=exact_source_url or invok or (yearok and header_matches and (len(title.split())>=4 or dimok)and museum_agrees and (not generic_title or dimok))
                museum_scope=len(possible)==1 and not re.search(r'parliamentary|government|state art commission|hospital|county council|university of oxford(?!.*museum)',next(iter(possible.values()))['name'],re.I)
                reason='supported'if detail and museum_scope and enough and not qualified and not edition else 'primary_or_secondary_lead_requires_object_review'
                result={'artwork_id':aid,'title':a['title'],'source_url':url,'source_title':source_title,'institution':next(iter(possible.values()))if len(possible)==1 else None,'possible_institutions':[i['name']for i in possible.values()],'evidence_path':str(path.relative_to(ROOT)),'evidence_sha256':r.sha(path.read_bytes()),'captured_at':d['at'],'exact_source_url':exact_source_url,'inventory_correspondence':invok,'year_correspondence':yearok,'dimension_correspondence':dimok,'detail_page':detail,'qualified_holding_text':qualified,'print_impression_unresolved':edition,'outcome':reason,'excerpt':block[:16000]}
                related[aid][url]=result
                if reason=='supported':candidates[aid][url]=result
    output={'at':r.now(),'search_queries_completed':len(searched),'searched_ids':sorted(searched),'supported_candidates':{aid:list(v.values())for aid,v in candidates.items()},'related_source_leads':{aid:list(v.values())for aid,v in related.items()},'institution_authority_resolutions':authority_resolutions,'stats':dict(stats),'scope':'Index-derived candidates require final review and conflict reconciliation before any database write.'}
    stamp=r.now().replace(':','').replace('-','');r.save_gz(RUN/'web-review'/(stamp+'.json.gz'),output)
    (RUN/'latest-web-review.json').write_text(json.dumps({'path':'web-review/'+stamp+'.json.gz','at':output['at'],'search_queries_completed':len(searched),'supported_artworks':len(candidates),'related_artworks':len(related)},indent=2)+'\n')
    print(json.dumps({'searched':len(searched),'supported_artworks':len(candidates),'related_artworks':len(related),'top_hosts':collections.Counter(host(x['source_url'])for v in candidates.values()for x in v.values()).most_common(12)}),flush=True)

if __name__=='__main__':run()
