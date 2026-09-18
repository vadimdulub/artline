#!/usr/bin/env python3
"""Independent museum-scoped Wikidata research; no database mutation or images."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
spec=importlib.util.spec_from_file_location('commons',Path(__file__).with_name('overnight-commons-images.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
spec=importlib.util.spec_from_file_location('research',Path(__file__).with_name('research-wikimedia-catalogues.py'));r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

def entities(qids,run,fetch):
    result={};missing=[]
    for q in sorted(set(qids)):
        p=run/'entities'/(q+'.json')
        if p.exists():result[q]=json.loads(p.read_text())
        else:missing.append(q)
    for start in range(0,len(missing),10):
        part=missing[start:start+10];params={'action':'wbgetentities','ids':'|'.join(part),'props':'claims|labels|aliases|descriptions|info','languages':'en|mul|de|fr|it|nl|ru|el'}
        data=m.api(fetch,'www.wikidata.org',params)
        for q in part:
            capture={'entity':data['entities'][q],'source_url':'https://www.wikidata.org/wiki/'+q,'retrieved_at':m.core.now(),'evidence_sha256':m.core.sha(m.core.encode(data['entities'][q]))}
            m.core.save_new(run/'entities'/(q+'.json'),capture);result[q]=capture
        print(m.core.now(),'Authority records captured',min(start+10,len(missing)),'of',len(missing),flush=True)
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args();run=a.run;index=json.loads((run/'discovery-index.json').read_text());fetch=m.core.Fetcher(run/'captures');institutions={x['institution_qid']:x for x in index['institutions']};museum_entities=json.loads((run/'museum-entities.json').read_text());qids={q for i in institutions.values() for q in i['work_qids']};works=entities(qids,run,fetch)
    artist_ids={v for x in works.values() for v in m.ids(x['entity'],'P170')};artists=entities(artist_ids,run,fetch)
    properties={k for x in works.values() for k in x['entity'].get('claims',{})};props=entities(properties,run,fetch);m.core.save_new(run/'property-definitions.json',props)
    out=[];held=[]
    for q,capture in works.items():
        e=capture['entity'];cs=r.claims(e,'P170');hs=[c for c in r.claims(e,'P195') if 'P582' not in c.get('qualifiers',{})];date=r.date(e)
        if date['first'] is not None:date['eligible']=1000<=date['first']<=date['last']<=1970
        why=None
        if e.get('id')!=q:why='Redirected identity'
        elif len(hs)!=1 or r.value(hs[0]).get('id') not in institutions:why='Multiple, historical or different holding institutions'
        elif len(cs)!=1 or cs[0].get('qualifiers'):why='Multiple, qualified or missing creator attribution'
        elif date['first'] is not None and not date['eligible']:why='Known creation date outside selected 1000–1970 scope'
        if why:held.append({'qid':q,'reason':why});continue
        cq=r.value(cs[0]).get('id');artist=artists.get(cq,{}).get('entity',{});mq=r.value(hs[0])['id'];museum=museum_entities[mq]
        if artist.get('id')!=cq or not r.label(artist) or r.label(artist)==cq:held.append({'qid':q,'reason':'Creator identity unresolved'});continue
        if re.search(r'\b(?:anonymous|unknown|unidentified)\b',r.label(artist),re.I):held.append({'qid':q,'reason':'Anonymous attribution needs explicit object-level review'});continue
        if m.ids(museum,'P17')!={'Q40'}:held.append({'qid':q,'reason':'Austrian institution country not uniquely established'});continue
        accession=list(dict.fromkeys(x for x in r.values(e,'P217') if isinstance(x,str)))
        urls=[]
        for prop in e.get('claims',{}):
            pd=props.get(prop,{}).get('entity',{});formats=[x for x in m.values(pd,'P1630') if isinstance(x,str) and x.startswith(('https://','http://'))]
            if pd.get('datatype')=='external-id':
                for value in m.values(e,prop):
                    if isinstance(value,str):
                        for fmt in formats:urls.append({'property':prop,'source_id':value,'url':fmt.replace('$1',value),'property_name':r.label(pd)})
        urls.extend({'property':'P973','url':x} for x in m.values(e,'P973') if isinstance(x,str))
        out.append({'qid':q,'title':r.label(e),'titles':r.labels(e),'date':date,'work_type':'painting','accession':accession[0] if len(accession)==1 else None,'accessions':accession,'institution_qid':mq,'institution_country':'AT','institution_name':r.label(museum),'institution_websites':m.values(museum,'P856'),'creator_qid':cq,'creator_label':r.label(artist),'creator_names':r.labels(artist),'creator_birth':r.year(artist,'P569'),'creator_death':r.year(artist,'P570'),'creator_countries':sorted(m.ids(artist,'P27')),'creator_description':artist.get('descriptions',{}).get('en',{}).get('value',''),'image_names':m.values(e,'P18'),'object_urls':urls,'entity':e,'entity_capture':capture,'creator_entity':artist,'creator_capture':artists[cq],'holding_statement':hs[0]})
    report={'at':m.core.now(),'records':out,'held':held,'unique_discovery_works':len(works),'counts_by_museum':dict(collections.Counter(x['institution_name'] for x in out)),'known_eligible_dates':sum(x['date']['eligible'] for x in out),'unknown_dates_review_only':sum(x['date']['first'] is None for x in out),'has_image_discovery_lead':sum(bool(x['image_names']) for x in out),'policy':'Independent Wikidata statements retained; official museum links need separate validation. Images are discovery leads only and require exact rights and provenance checks. Museum country does not assign artist nationality.'}
    m.core.save_new(run/'researched-records.json',report);print(m.core.now(),'Research facts prepared',len(out),'held',len(held),report['counts_by_museum'],flush=True)
if __name__=='__main__':main()
