#!/usr/bin/env python3
"""Evidence-based 80% editorial assessment; no database writes in research phases."""
import argparse,collections,gzip,json,re,time,uuid
from urllib.parse import urlsplit
import requests
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
t=module('round2','ops/random-5000-museums-round2-20261006.py');r=t.r;RUN=t.RUN;OLD=t.OLD
w=module('wiki_match','ops/reconcile-random-5000-wikiart-museums-20261006.py');norm=w.norm
def value(s):
    v=s.get('mainsnak',{}).get('datavalue',{}).get('value');return v.get('id')if isinstance(v,dict)and'id'in v else v
def statements(e,p):
    ss=[s for s in e.get('claims',{}).get(p,[])if s.get('rank')!='deprecated'and'P582'not in s.get('qualifiers',{})];preferred=[s for s in ss if s.get('rank')=='preferred'];return preferred or ss
def vals(e,p):return[value(s)for s in statements(e,p)]
def names(e):return{norm(v['value'])for v in e.get('labels',{}).values()}|{norm(v['value'])for vv in e.get('aliases',{}).values()for v in vv}
def host(v):return(urlsplit(v or '').hostname or '').removeprefix('www.')
def authority():
    wd=r.load(RUN/'wikidata-entities.json.gz');au=r.load(RUN/'cached-institution-authorities.json.gz');wanted={v for x in wd.values()for v in vals(x['entity'],'P195')if isinstance(v,str)}
    base=ROOT/'docs/research/artwork-locations-20261004'
    for folder in ['institution-authority-responses-20261005','institution-authorities-20261005','major-museum-authorities-20261005d','museum-authorities']:
        for p in(base/folder).glob('*.receipt.json'):
            rc=r.load(p)
            if rc.get('status')!=200 or not rc.get('body_path'):continue
            try:
                raw=(ROOT/rc['body_path']).read_bytes();raw=gzip.decompress(raw)if rc['body_path'].endswith('.gz')else raw
                assert r.sha(raw)==rc['sha256'];data=json.loads(raw)
            except (ValueError,OSError):continue
            for q,e in data.get('entities',{}).items():
                if q in wanted and q not in au:au[q]={'entity':e,'receipt':rc,'path':str(p.relative_to(ROOT))}
    missing=sorted(wanted-au.keys())
    for start in range(0,len(missing),40):
        url=requests.Request('GET','https://www.wikidata.org/w/api.php',params={'action':'wbgetentities','ids':'|'.join(missing[start:start+40]),'props':'labels|aliases|claims','format':'json'}).prepare().url
        raw,rc=r.capture(url,tag='selected-institution-authorities')
        if rc['status']!=200:print('Authority API stopped',rc['status'],flush=True);break
        for q,e in json.loads(raw).get('entities',{}).items():au[q]={'entity':e,'receipt':rc,'path':rc['body_path']}
        print('Selected authorities',min(start+40,len(missing)),'/',len(missing),flush=True);time.sleep(1.2)
    r.save_gz(RUN/'institution-authorities-complete.json.gz',au);print('Missing authorities',len(wanted-au.keys()),flush=True)

def wiki():
    w.RUN=RUN;w.r.RUN=RUN;w.r.PORT=55483
    w.CREATOR_ALIASES += [('Lawrence Alma-Tadema','Sir Lawrence Alma-Tadema'),('James Abbott McNeill Whistler','James McNeill Whistler'),('Verhaecht Tobias','Tobias Verhaecht'),('Nikolai Dmitriyevich Kuznetsov','Nikolai Kuznetsov'),('Antonio da Correggio','Correggio')]
    save=w.r.save_gz
    def save_reviewed(path,data):
        if path.name=='wikiart-holding-plan-v5.json.gz':
            path=path.with_name('wikiart-holding-plan-v6.json.gz');held={}
            for c in data['claims']:
                label=c['object_evidence']['page']['fields']['Location']
                if label in ["Louvre, Paris, France, Musée d'Orsay, Paris, France",'Amsterdams Historisch Museum, Amsterdam, Netherlands, Rijksmuseum, Amsterdam, Netherlands']:held[c['artwork_id']]='multiple_museums_in_literal_source_label'
            data['claims']=[c for c in data['claims']if c['artwork_id']not in held]
            for o in data['outcomes']:
                if o['artwork_id']in held:o['outcome']=held[o['artwork_id']];o['issues'].append(held[o['artwork_id']])
            data['supersedes']='v5; reviewed named-creator variants; concatenated museum locations require object-specific resolution.'
        save(path,data)
    w.r.save_gz=save_reviewed
    w.main()

def creators():
    prior=r.load(RUN/'wikidata-assessment-v2.json.gz');rows=r.load(RUN/'baseline.json.gz');wd=r.load(RUN/'wikidata-entities.json.gz');wanted=set()
    for o in prior['outcomes']:
        if o['outcome']!='artwork_creator_requires_reconciliation':continue
        for x in rows[o['artwork_id']]['identifiers']:
            if x['scheme']=='wikidata'and x['external_id']in wd:wanted.update(v for v in vals(wd[x['external_id']]['entity'],'P170')if isinstance(v,str))
    out={};wanted=sorted(wanted)
    for start in range(0,len(wanted),40):
        url=requests.Request('GET','https://www.wikidata.org/w/api.php',params={'action':'wbgetentities','ids':'|'.join(wanted[start:start+40]),'props':'labels|aliases|claims','format':'json'}).prepare().url
        raw,rc=r.capture(url,tag='selected-creator-authorities')
        if rc['status']!=200:print('Creator API stopped',rc['status'],flush=True);break
        for q,e in json.loads(raw).get('entities',{}).items():out[q]={'entity':e,'receipt':rc}
        time.sleep(1.2)
    r.save_gz(RUN/'selected-creator-authorities.json.gz',out);print('Creator authorities captured',len(out),flush=True)

NON_MUSEUM=re.compile(r'private collection|national trust$|government art|arts council|hospital|(?:library|libraries)(?!.*museum)|county council|parliament|town hall|theatre|scouts heritage|university(?!.*(?:museum|gallery))|school(?!.*museum)|cathedral|church|monastery|archive(?!.*(?:gallery|museum))',re.I)
# Verified against preserved type authorities; a museum building alone does not
# establish that a municipality or performance venue is a museum collection.
MUSEUM_TYPES={'Q33506','Q207694','Q17431399','Q1970365','Q866133','Q2772772','Q2087181','Q1595639','Q2327632','Q1863818','Q113095515','Q88667167'}
COLLECTION_PARENT={'Q195436':'a1976c92-e516-4585-9c6e-c4e640f6a8e9','Q193375':'a1976c92-e516-4585-9c6e-c4e640f6a8e9'}
def institutions(au,ii):
    byid={i['id']:i for i in ii};byqid=collections.defaultdict(list)
    for i in ii:
        if i.get('wikidata_id'):byqid[i['wikidata_id']].append(byid.get(i.get('canonical_institution_id'),i))
    resolved={};held={}
    for q,a in au.items():
        e=a['entity'];label=e.get('labels',{}).get('en',e.get('labels',{}).get('mul',{})).get('value');ns=names(e);sites=[v for v in vals(e,'P856')if isinstance(v,str)];types=set(v for v in vals(e,'P31')if isinstance(v,str))
        direct={i['id']:i for i in byqid.get(q,[])}
        sameofficial={i['id']:i for i in ii if norm(i['name'])in ns and host(i.get('website_url'))and host(i.get('website_url'))in {host(s)for s in sites}}
        if q in COLLECTION_PARENT:direct={COLLECTION_PARENT[q]:byid[COLLECTION_PARENT[q]]}
        if not direct and len(sameofficial)==1:direct=sameofficial
        if not label and len(direct)==1:label=next(iter(direct.values()))['name']
        if not label:held[q]='missing_institution_label';continue
        if NON_MUSEUM.search(label):held[q]='documented_non_museum_collection';continue
        # An existing Q-ID is identity evidence; an institution kind alone is
        # insufficient for libraries, public agencies and private collections.
        museum=bool(types&MUSEUM_TYPES)or(bool(direct)and bool(re.search(r'museum|gallery|galleries|musee|musée|museo|pinakothek|kunst|hermitage|tate|louvre|academy|academie|center for british art',label,re.I)))
        if not museum:held[q]='museum_function_requires_evidence';continue
        if re.search(r'sevastopol|horlivka|roerich.*moscow|staechelin',label,re.I):held[q]='changed_custody_requires_current_evidence';continue
        if len(direct)==1:inst=next(iter(direct.values()));basis='Exact collection Q-ID, or exact authority name and official website, reconciled to the existing museum; Tate branches use the established Tate collection authority.'
        elif len(direct)>1:held[q]='duplicate_existing_institution_authorities';continue
        else:
            matched=[]
            for i in ii:
                exact=norm(i['name'])in ns
                samehost=host(i.get('website_url'))and host(i.get('website_url'))in {host(s)for s in sites}
                # Full city-qualified names from the preceding WikiArt pass.
                fullname=any(n and len(n.split())>=3 and norm(i['name']).startswith(n+' ')for n in ns)
                if (exact and samehost)or(fullname and not i.get('wikidata_id')):matched.append(byid.get(i.get('canonical_institution_id'),i))
            matched={i['id']:i for i in matched}
            if len(matched)==1:inst=next(iter(matched.values()));basis='Source authority name and official website, or full city-qualified museum name, match an existing institution.'
            elif matched:held[q]='multiple_name_authority_matches';continue
            else:
                if not sites:held[q]='new_museum_lacks_official_website_authority';continue
                inst={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/random-5000-museums-round2-20261006/institution/'+q)),'slug':'museum-authority-'+q.lower(),'name':label,'normalized_name':norm(label),'website_url':sites[0],'wikidata_id':q,'kind':'museum','status':'review','description':'Museum authority documented by the preserved Wikidata entity, museum type and official website. Collection connection is distinct from current display.','canonical_institution_id':None};basis='New review museum authority with source museum type, exact Q-ID and official website.'
        resolved[q]={'institution':inst,'basis':basis,'authority':a}
    return resolved,held

def title_names(e):
    return names(e)|{norm(v.get('text',''))for v in vals(e,'P1476')if isinstance(v,dict)}
def wd_assessment(row,entry,artistq,resolved,creator_authorities=None):
    a=row['artwork'];e=entry['entity'];collections_=statements(e,'P195');qs={value(s)for s in collections_ if isinstance(value(s),str)}
    if len(qs)!=1:return None,'no_single_current_collection'
    q=next(iter(qs))
    if q not in resolved:return None,'collection_authority_unresolved'
    if any(set(s.get('qualifiers',{}))-{'P580','P217'}for s in collections_):return None,'qualified_collection_statement'
    if any(vals(e,p)for p in ['P576']):return None,'source_reports_destruction'
    titleok=bool({norm(a['title']),norm(a.get('alternate_title'))}-{''}&title_names(e))
    creators={q for x in row['creators']for q in artistq[x['artist_id']]};sourcecreators={v for v in vals(e,'P170')if isinstance(v,str)}
    creatorok=bool(creators and creators&sourcecreators)
    label_match=[]
    if not row['creators'] and a.get('unlinked_creator_label'):
        for cq in sourcecreators:
            ce=(creator_authorities or {}).get(cq,{}).get('entity',{})
            if r.namekey(a['unlinked_creator_label'])in {r.namekey(n)for n in names(ce)}:label_match.append(cq)
        creatorok=bool(label_match)
    if not titleok:return None,'artwork_title_requires_reconciliation'
    if not creatorok:return None,'artwork_creator_requires_reconciliation'
    inventories=[v for v in vals(e,'P217')if isinstance(v,str)]
    native={p:[v for v in vals(e,p)if isinstance(v,str)]for p in ['P1679','P973','P350','P3634','P2014','P2268','P4525','P4610','P217']};native={k:v for k,v in native.items()if v}
    if not inventories and not native:return None,'version_identity_insufficient'
    existinginv=a.get('accession_number');invok=existinginv and norm(existinginv)in {norm(x)for x in inventories}
    if existinginv and inventories and not invok:return None,'existing_inventory_disagrees'
    if a['work_type']=='print'and not invok:return None,'specific_print_impression_requires_inventory'
    inst=resolved[q]['institution']
    if q=='Q95569'and a['work_type']not in ['painting','unknown']:return None,'museum_department_scope'
    confidence=.9 if inventories and native.get('P1679')else .86 if inventories else .82
    basis='Exact existing artwork Wikidata ID; matching title/alias and '+('preserved unlinked creator label matched to source creator authority'if label_match else 'creator Wikidata ID')+'; one active unqualified collection statement; '+('object inventory '+', '.join(inventories)if inventories else 'native catalogue reference')+'; documented museum authority. Editorial confidence '+str(round(confidence*100))+'%, not a calibrated probability.'
    rc=entry['receipt'];proof={'wikidata_artwork_id':e['id'],'title_verified':True,'creator_qids':sorted(creators),'source_creator_qids':sorted(sourcecreators),'collection_statement':collections_,'inventory':inventories,'native_catalogue_references':native,'institution_resolution':resolved[q]['basis'],'institution_authority_receipt':resolved[q]['authority']['receipt'],'editorial_confidence':confidence,'confidence_basis':basis,'calibrated_probability':False}
    if label_match:proof['preserved_unlinked_creator_check']={'label':a['unlinked_creator_label'],'matched_source_creators':label_match,'authority_receipts':{q:creator_authorities[q]['receipt']for q in label_match},'artist_relationship_changes':0}
    return {'artwork_id':a['id'],'title':a['title'],'scheme':'wikidata','external_id':e['id'],'institution':inst,'source_url':'https://www.wikidata.org/wiki/'+e['id'],'checked_at':rc['retrieved_at'],'location_text':inst['name'],'identity_basis':basis,'source_class':'exact_object_wikidata_collection_with_native_catalogue_identity','source_receipt':rc,'object_evidence':proof,'claim_type':'holding','review_state':'accepted','editorial_confidence':confidence,'limitation':'Source-documented museum collection connection, assessed at the user-approved 80% editorial threshold. Cached source retrieval time retained. No current-display, legal ownership or physical-whereabouts claim. Existing dates, creators, images and publication state preserved.'},'supported_wikidata_museum'

def assess():
    rows=r.load(RUN/'baseline.json.gz');wd=r.load(RUN/'wikidata-entities.json.gz');au=r.load(RUN/'institution-authorities-complete.json.gz');ii=r.load(RUN/'institutions.json.gz');artists=r.load(RUN/'artists.json.gz');resolved,held=institutions(au,ii);artistq=collections.defaultdict(set);ca=r.load(RUN/'selected-creator-authorities.json.gz')if(RUN/'selected-creator-authorities.json.gz').exists()else{}
    for x in artists['identifiers']:
        if x['scheme']=='wikidata':artistq[x['entity_id']].add(x['external_id'])
    # Existing museum Q IDs omitted from authority cache still require a capture;
    # they are never synthesized as Wikidata entities.
    claims=[];outcomes=[]
    for aid,row in rows.items():
        qids={e['external_id']for e in row['identifiers']if e['scheme']=='wikidata'};found=[];reasons=[]
        for q in qids:
            if q not in wd:reasons.append('uncaptured_artwork_identity');continue
            c,reason=wd_assessment(row,wd[q],artistq,resolved,ca);reasons.append(reason)
            if c:found.append(c)
        if len({c['institution']['id']for c in found})>1:found=[];reasons.append('conflicting_source_collections')
        if found:claims.append(found[0])
        outcomes.append({'artwork_id':aid,'outcome':'supported_wikidata_museum'if found else reasons[0]if reasons else 'no_existing_wikidata_artwork_identity','reasons':reasons,'collection_candidates':[{'qid':v,'resolution':resolved.get(v,{}).get('basis'),'hold':held.get(v),'label':au.get(v,{}).get('entity',{}).get('labels',{}).get('en',{}).get('value')}for q in qids if q in wd for v in vals(wd[q]['entity'],'P195')if isinstance(v,str)]})
    r.save_gz(RUN/('wikidata-assessment-v3.json.gz'if ca else 'wikidata-assessment-v2.json.gz'),{'at':r.now(),'claims':claims,'outcomes':outcomes,'institution_resolutions':resolved,'institution_holds':held,'supersedes':'Earlier assessment; verified museum subtype semantics, excluded municipality/theatre/heritage-service ambiguity and reconciled established museum website identities. Preserved unlinked labels checked against exact source creator authorities without creating artist relationships.'});print('Wikidata supported',len(claims),'outcomes',dict(collections.Counter(o['outcome']for o in outcomes)),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['authority','wiki','creators','assess']);args=ap.parse_args();globals()[args.phase]()
