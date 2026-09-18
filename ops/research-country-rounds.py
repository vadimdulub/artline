#!/usr/bin/env python3
"""Twenty bounded painter/collection research rounds per selected country.

Discovery and metadata selection only. Database writes and licensed image
preparation are separate reviewed stages. Every round records its distinct
creator scope, new object research, evidence, exclusions and remaining cursor.
"""
import argparse,collections,importlib.util,json,re,math,uuid,os
from pathlib import Path
from urllib.parse import urlencode,urlparse
spec=importlib.util.spec_from_file_location('wiki',Path(__file__).with_name('research-wikimedia-catalogues.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
ROOT=r.ROOT;SESSION_NAME=os.environ.get('ARTLINE_RESEARCH_SESSION','overnight-countries-20260913')
assert re.fullmatch(r'[a-z0-9][a-z0-9-]{5,79}',SESSION_NAME)
SESSION_BASE=ROOT/'docs/research'/SESSION_NAME
CAMPAIGN=os.environ.get('ARTLINE_RESEARCH_CAMPAIGN','');assert not CAMPAIGN or re.fullmatch(r'[a-z0-9][a-z0-9-]{1,59}',CAMPAIGN)
BASE=SESSION_BASE/CAMPAIGN if CAMPAIGN else SESSION_BASE;r.RUN=SESSION_BASE/'wikimedia'
COUNTRIES={'NL':{'name':'Netherlands','qid':'Q55','adjective':'Dutch'},'GR':{'name':'Greece','qid':'Q41','adjective':'Greek'},'RU':{'name':'Russia','qid':'Q159','adjective':'Russian'},'FR':{'name':'France','qid':'Q142','adjective':'French'},'IT':{'name':'Italy','qid':'Q38','adjective':'Italian'}}
COUNTRIES['ES']={'name':'Spain','qid':'Q29','adjective':'Spanish'}
COUNTRIES['DE']={'name':'Germany','qid':'Q183','adjective':'German'}
COUNTRIES['AT']={'name':'Austria','qid':'Q40','adjective':'Austrian'}
COUNTRIES['BE']={'name':'Belgium','qid':'Q31','adjective':'Belgian'}
COUNTRIES['FI']={'name':'Finland','qid':'Q33','adjective':'Finnish'}
COUNTRIES['PT']={'name':'Portugal','qid':'Q45','adjective':'Portuguese'}
for code,name,qid,adjective in [('SE','Sweden','Q34','Swedish'),('DK','Denmark','Q35','Danish'),('NO','Norway','Q20','Norwegian'),('GB','United Kingdom','Q145','British'),('PL','Poland','Q36','Polish'),('CZ','Czechia','Q213','Czech'),('HU','Hungary','Q28','Hungarian'),('RO','Romania','Q218','Romanian'),('UA','Ukraine','Q212','Ukrainian')]:COUNTRIES[code]={'name':name,'qid':qid,'adjective':adjective}
HISTORICAL_CONTEXT={'NL':[], 'GR':['Q12544','Q12560','Q4948'], 'RU':['Q34266','Q15180'], 'FR':['Q70972','Q71084'], 'IT':['Q172579','Q148540','Q4948']}
HISTORICAL_CONTEXT['BE']=[]
HISTORICAL_CONTEXT['FI']=[]
HISTORICAL_CONTEXT['PT']=[]
HISTORICAL_CONTEXT['ES']=[]
HISTORICAL_CONTEXT['DE']=['Q43287','Q38872']
HISTORICAL_CONTEXT['AT']=['Q131964','Q28513']
for code in ('SE','DK','NO','GB','PL','CZ','HU','RO','UA'):HISTORICAL_CONTEXT[code]=[]
COUNTRIES['CH']={'name':'Switzerland','qid':'Q39','adjective':'Swiss'}
HISTORICAL_CONTEXT['CH']=[]
COUNTRIES['US']={'name':'United States','qid':'Q30','adjective':'American'}
HISTORICAL_CONTEXT['US']=[]
# Discovery context only. Explicit Czech cultural biography is required by the
# historical-country review; imperial citizenship never assigns Czech identity.
HISTORICAL_CONTEXT['CZ']=['Q33946','Q28513','Q131964']
HISTORICAL_CONTEXT['RO']=['Q203493','Q131964','Q28513']
HISTORICAL_CONTEXT['UA']=['Q133356','Q15180','Q34266','Q28513']

def save(path,value):r.core.save_new(path,value)
def unnamed_creator_context(entity):
    pattern=r'\b(?:anonymous|unknown|unidentified|anonym(?:e|ous)?|anonim[oa])\b|\b(?:master of|workshop of|meister (?:des|der|von)|mestre (?:de|do|dos|da|das)|maestro (?:de|del|della)|ma[iî]tre (?:de|du|des)|meester van)\b'
    return any(re.search(pattern,label,re.I) for label in r.labels(entity))
def artist_country(entity,code):
    target=COUNTRIES[code]['qid']
    matches=[c for c in r.claims(entity,'P27') if r.value(c).get('id')==target]
    historical=[c for c in r.claims(entity,'P27') if r.value(c).get('id') in HISTORICAL_CONTEXT[code]]
    desc=entity.get('descriptions',{}).get('en',{}).get('value','')
    adjective=COUNTRIES[code]['adjective']
    explicit=bool(re.search(r'\b'+adjective+r'(?![- ]born)\b(?:[- /](?:Dutch|Greek|Russian|American|French|German|Danish|British|Swedish|Norwegian|Finnish|Portuguese|Polish|Czech|Hungarian|Romanian|Ukrainian|Austrian|Swiss))?(?: [\w-]+){0,4} (?:painter|artist|iconographer|printmaker|engraver|illustrator|draughtsman|sculptor)\b',desc,re.I))
    if code=='NL':
        explicit=explicit or bool(re.search(r'\bpainter from (?:the )?(?:Northern )?Netherlands\b',desc,re.I))
        if re.search(r'\bFlemish\b|Southern Netherlands|Early Netherlandish',desc,re.I) and not re.search(r'\bDutch\b',desc,re.I):explicit=False
    if not explicit or not (matches or historical):return None
    return {'country_code':code,'country_qid':target,'statements':matches,'historical_polity_statements':historical,'requires_biographical_affiliation_corroboration':not bool(matches),'source_description':desc,'basis':'Explicit painter cultural-affiliation wording corroborated by source country/biography evidence. Historical polity membership is discovery context only and never mapped automatically to a modern country. Not museum location, birthplace or exclusive citizenship.'}

def roster(code):
    path=BASE/code/'roster.json'
    if path.exists():return json.loads(path.read_text())
    country=COUNTRIES[code]
    polities=' '.join('wd:'+q for q in [country['qid'],*HISTORICAL_CONTEXT[code]])
    types='wd:Q3305213 wd:Q22669139 wd:Q132137' if code in ('GR','RU') else 'wd:Q3305213'
    cap=int(os.environ.get('ARTLINE_RESEARCH_ROSTER_LIMIT','200' if code in ('FR','IT','ES','DE','AT','BE','FI','PT') else '600'))
    offset=int(os.environ.get('ARTLINE_RESEARCH_ROSTER_OFFSET','0'));assert 20<=cap<=1000 and 0<=offset<=10000
    query=f"SELECT DISTINCT ?artist WHERE {{ VALUES ?polity {{ {polities} }} VALUES ?kind {{ {types} }} ?work wdt:P170 ?artist; wdt:P195 ?museum; wdt:P31 ?kind; wdt:P18 ?image. ?artist wdt:P27 ?polity . }} ORDER BY ?artist LIMIT {cap} OFFSET {offset}"
    data,receipt=r.fetch('https://query.wikidata.org/sparql?'+urlencode({'query':query,'format':'json'}))
    ids=[x['artist']['value'].rsplit('/',1)[-1] for x in data['results']['bindings']]
    es,receipts=r.entities(ids)
    artists=[];holds=[]
    baseline=json.loads((SESSION_BASE/'local-artists-baseline.json').read_text());known={e['id']:a['row']['slug'] for a in baseline for e in a['authorities'] if e['scheme']=='wikidata'}
    for q in ids:
        e=es[q];evidence=artist_country(e,code);birth=r.year(e,'P569')
        if e.get('id')!=q or not evidence or not any(v.get('id')=='Q5' for v in r.values(e,'P31') if isinstance(v,dict)):
            holds.append({'qid':q,'reason':'creator_or_country_identity_requires_review'});continue
        if birth is not None and birth>1970:
            holds.append({'qid':q,'reason':'born_after_artwork_creation_cutoff'});continue
        artists.append({'qid':q,'name':r.label(e),'birth':birth,'death':r.year(e,'P570'),'existing_slug':known.get(q),'country_evidence':evidence,'receipt':receipts[q]})
    # Put missing painters first, then distribute distinct artist scopes across
    # 20 rounds. This is not 20 calls on the same records or 20 write batches.
    artists.sort(key=lambda a:(bool(a['existing_slug']),a['birth'] is None,a['birth'] or 0,a['name']))
    rounds=[{'round':i+1,'artists':artists[i::20],'country_code':code,'question':'Find additional museum-connected paintings through 1970 and licensed reproductions for this distinct creator group; verify creator/country and object identity.'} for i in range(20)]
    result={'at':r.core.now(),'country':country,'code':code,'query_receipt':receipt,'artists':artists,'rounds':rounds,'holds':holds,'discovery_cap':cap,'discovery_offset':offset,'session':SESSION_NAME}
    save(path,result);print(code,'roster',len(artists),'painters;',sum(not a['existing_slug'] for a in artists),'missing Wikidata identities; 20 distinct rounds',flush=True);return result

def collection(qid,entity,receipt,db):
    # Reuse explicit catalogue Wikidata IDs or the earlier reviewed website /
    # Muséofile crosswalk. New institutions need an official website identity.
    mapping=dict(r.MAPPING)
    previous=ROOT/'docs/research/wikimedia-catalogue-scan-20260913/discovery-index.json'
    if previous.exists():
        for item in json.loads(previous.read_text())['collections']:mapping[item['institution']['slug']]=item['qid']
    slugs=[s for s,q in mapping.items() if q==qid]
    rows=db.execute("SELECT id::text,slug,name,website_url,wikidata_id,status FROM institutions WHERE wikidata_id=%s OR slug=ANY(%s) ORDER BY slug",(qid,slugs)).fetchall()
    if rows:
        active=[x for x in rows if x['status']!='archived']
        if not active:return None,'archived_institution'
        primary=next((x for x in active if x['wikidata_id']==qid),active[0])
        return {'qid':qid,'institution':primary,'related_institution_ids':[x['id'] for x in active],'related_institution_slugs':[x['slug'] for x in active]},None
    websites=[v for v in r.values(entity,'P856') if isinstance(v,str) and v.startswith('https://')]
    if entity.get('id')!=qid or not websites:return None,'new_collection_official_identity_needs_review'
    # A holding can be a private collection, institution umbrella or building.
    # Require museum/gallery/collection identity evidence, not a person entity.
    kinds={v.get('id') for v in r.values(entity,'P31') if isinstance(v,dict)}
    descriptions=' '.join(x['value'] for x in entity.get('descriptions',{}).values()).lower()
    if 'Q5' in kinds or not re.search(r'museum|musée|музей|μουσείο|art gallery|collection|galerie|pinacoteca|gallery',descriptions):return None,'new_collection_kind_requires_review'
    name=r.label(entity)
    existing=db.execute('SELECT slug FROM institutions WHERE lower(name)=%s OR website_url=ANY(%s)',(name.lower(),websites)).fetchall()
    if existing:return None,'new_collection_name_or_website_collision'
    inst={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikimedia-catalogue/institution/'+qid)),'slug':'wikimedia-museum-'+qid.lower(),'name':name,'website_url':websites[0],'wikidata_id':qid,'new_institution':True,'authority_receipt':receipt}
    return {'qid':qid,'institution':inst,'related_institution_ids':[inst['id']],'related_institution_slugs':[inst['slug']]},None

def research(code,number):
    country=roster(code);scope=country['rounds'][number-1];run=BASE/code/f'round-{number:02d}'
    if (run/'metadata-summary.json').exists():print(code,number,'metadata already captured',flush=True);return
    save(run/'scope.json',scope)
    artist_ids=[a['qid'] for a in scope['artists']]
    if not artist_ids:
        save(run/'metadata-summary.json',{'country':code,'round':number,'completed':False,'reason':'No distinct eligible creators discovered; expand the country roster before counting this round.'});return
    creators,creator_receipts=r.entities(artist_ids)
    discovered=[];holds=[];pages=[]
    for artist in scope['artists']:
        q=artist['qid'];path=run/'discovery'/(q+'.json')
        if path.exists():discovery=json.loads(path.read_text())
        else:
            types='wd:Q3305213 wd:Q22669139 wd:Q132137' if code in ('GR','RU') else 'wd:Q3305213'
            query=f'SELECT DISTINCT ?work WHERE {{ VALUES ?kind {{ {types} }} ?work wdt:P170 wd:{q}; wdt:P195 ?collection; wdt:P31 ?kind; wdt:P18 ?image. }} ORDER BY ?work LIMIT 80'
            data,receipt=r.fetch('https://query.wikidata.org/sparql?'+urlencode({'query':query,'format':'json'}))
            discovery={'artist_qid':q,'artist':artist['name'],'works':[x['work']['value'].rsplit('/',1)[-1] for x in data['results']['bindings']],'receipt':receipt,'bounded_cap':80}
            save(path,discovery)
        discovered.append(discovery);pages.append(discovery['receipt'])
    with r.base.connect(False) as db,db.transaction():
        db.execute('SET TRANSACTION READ ONLY')
        allids=list({q for group in discovered for q in group['works']})
        existing={x['external_id'] for x in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s)",(allids,)).fetchall()}
    previous=set()
    for path in BASE.glob('*/round-*/metadata-summary.json'):
        previous.update(json.loads(path.read_text()).get('selected_qids',[]))
    byartist={g['artist_qid']:[q for q in g['works'] if q not in existing and q not in previous] for g in discovered}
    for q in existing:holds.append({'qid':q,'reason':'already_has_catalogue_wikidata_identity_preserved_for_separate_image_gap_review'})
    # Inspect up to 24 new object records per artist and 360 per round.
    selected_ids=[]
    for pos in range(24):
        for q in artist_ids:
            group=byartist[q]
            if pos<len(group) and group[pos] not in selected_ids:selected_ids.append(group[pos])
            if len(selected_ids)>=360:break
        if len(selected_ids)>=360:break
    entities,receipts=r.entities(selected_ids)
    museum_ids=sorted({r.value(c)['id'] for e in entities.values() for c in r.claims(e,'P195') if isinstance(r.value(c),dict) and 'P582' not in c.get('qualifiers',{})})
    museums,museum_receipts=r.entities(museum_ids) if museum_ids else ({},{})
    selected=[];collection_cache={};counts=collections.Counter()
    with r.base.connect(False) as db,db.transaction():
        db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'")
        for qid in selected_ids:
            e=entities[qid];reason=None;d=r.date(e);cs=r.claims(e,'P170')
            cq=r.value(cs[0]).get('id') if len(cs)==1 else None
            if e.get('id')!=qid:reason='redirected_object_identity'
            elif len(cs)!=1 or cs[0].get('qualifiers') or cq not in creators:reason='qualified_multiple_or_different_creator'
            elif unnamed_creator_context(creators[cq]):reason='unidentified_creator_retained_for_object_level_attribution_review'
            elif not artist_country(creators[cq],code):reason='country_affiliation_requires_biographical_context'
            elif d['first'] is not None and not d['eligible']:reason='known_date_outside_creation_scope'
            hs=[c for c in r.claims(e,'P195') if 'P582' not in c.get('qualifiers',{})]
            if len(hs)!=1:reason=reason or 'multiple_or_historical_collections_need_object_research'
            collection_info=None
            if not reason:
                mq=r.value(hs[0])['id']
                if mq not in collection_cache:collection_cache[mq]=collection(mq,museums[mq],museum_receipts[mq],db)
                collection_info,reason=collection_cache[mq]
            if not reason and counts[cq]>=8:reason='outside_selected_eight_works_per_painter_this_round'
            if reason:holds.append({'qid':qid,'creator_qid':cq,'reason':reason});continue
            ce=creators[cq];images=r.values(e,'P18')
            if not images:holds.append({'qid':qid,'reason':'source_image_statement_missing'});continue
            accession=list(dict.fromkeys(v for v in r.values(e,'P217') if isinstance(v,str)))
            record={'qid':qid,'title':r.label(e),'titles':r.labels(e),'date':d,'entity':e,'entity_receipt':receipts[qid],'creator_qid':cq,'creator_label':r.label(ce),'creator_entity':ce,'creator_receipt':creator_receipts[cq],'collection':collection_info,'holding_statement':hs[0],'accession':accession[0] if len(accession)==1 else None,'images':images,'existing_local':None,'country_evidence':artist_country(ce,code),'round':number,'country_code':code}
            kinds={v.get('id') for v in r.values(e,'P31') if isinstance(v,dict)}
            record['work_type']='fresco' if 'Q22669139' in kinds else ('painting' if 'Q3305213' in kinds else 'unknown')
            record['source_form']='icon' if 'Q132137' in kinds else None
            selected.append(record);counts[cq]+=1
    grouped=collections_module(selected)
    for slug,records in grouped.items():save(run/'selected'/(slug+'.json'),{'selected':records,'deferred':[]})
    save(run/'holds.json',holds)
    summary={'at':r.core.now(),'country':code,'round':number,'completed':True,'research_question':scope['question'],'painters_researched':len(artist_ids),'discovered_objects':len({q for g in discovered for q in g['works']}),'new_metadata_inspected':len(selected_ids),'selected_records':len(selected),'selected_qids':[x['qid'] for x in selected],'selected_painters':len(counts),'new_collection_identities':sum(bool(c[0] and c[0]['institution'].get('new_institution')) for c in collection_cache.values()),'hold_counts':dict(collections.Counter(x['reason'] for x in holds)),'discovery_receipts':pages,'stage':'Metadata only; image rights, duplicate guards, both-target preflight, application and verification still required.'}
    save(run/'metadata-summary.json',summary);print(code,'round',number,'metadata',len(selected_ids),'selected',len(selected),'painters',len(counts),flush=True)

def collections_module(selected):
    result={}
    for record in selected:result.setdefault(record['collection']['institution']['slug'],[]).append(record)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['roster','research']);p.add_argument('--country',choices=COUNTRIES,required=True);p.add_argument('--round',type=int);args=p.parse_args()
    if args.command=='roster':roster(args.country)
    else:
        assert args.round and 1<=args.round<=20;research(args.country,args.round)
