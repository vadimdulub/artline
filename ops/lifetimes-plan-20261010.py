#!/usr/bin/env python3
"""Conservative, source-literal lifetime reconciliation and full review register."""
import collections,copy,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('sources',Path(__file__).with_name('lifetimes-sources-20261010.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
r=p.r;RUN=r.RUN
def date_token(text):
    v=re.fullmatch(r'(c\.\s*)?(\d{3,4})',text.strip())
    if not v:return None
    y=int(v[2]);return dict(year=y,precision='circa' if v[1] else 'exact',display=('c. ' if v[1] else '')+str(y))
def literal_life(label):
    """Never interpret search bounds, activity dates, or unparsed qualifiers as life."""
    text=label.strip()
    if re.search(r'active|flour|documented|century|probably|possibly|before|after|\?|/|\bor\b',text,re.I):return None
    token=r'(?:c\.\s*)?\d{3,4}'
    match=re.search(r'(?:^|,\s*|\bborn\s+(?:[A-Za-z ()]+\s)?)(?P<b>'+token+r')\s*[-–]\s*(?P<d>'+token+r')$',text)
    if match:return dict(birth=date_token(match['b']),death=date_token(match['d']))
    match=re.search(r'\bborn\s+(?P<b>'+token+r')$',text)
    if match:return dict(birth=date_token(match['b']))
    match=re.search(r'\bdied\s+(?P<d>'+token+r')$',text)
    if match:return dict(death=date_token(match['d']))
    return None
def fresh_index():
    out=collections.defaultdict(lambda:dict(claims={},receipts=[]))
    for path in sorted((RUN/'fresh-date-statements').glob('*.json.gz')):
        data=r.load(path)
        for q in data['qids']:out[q]['receipts'].append(dict(path=str(path.relative_to(r.ROOT)),at=data['at'],sha256=data['sha256']))
        for row in data['data']['results']['bindings']:
            def get(k):return row.get(k,{}).get('value')
            q=get('artist').rsplit('/',1)[-1];cid=get('claim');claims=out[q]['claims']
            if cid not in claims:claims[cid]=dict(property=get('property').rsplit('/',1)[-1],rank=get('rank').rsplit('#',1)[-1],value=get('value'),precision=int(get('precision')) if get('precision') else None,calendar=get('calendar'),qualifiers=[],references=[])
            c=claims[cid]
            qual=(get('qualifierProperty'),get('qualifierValue'))
            if qual[0] and qual not in c['qualifiers']:c['qualifiers'].append(qual)
            if get('reference') and get('reference') not in c['references']:c['references'].append(get('reference'))
    r.save(RUN/'fresh-date-index.json.gz',dict(out));print('Fresh authority identities',len(out),flush=True)
def source_years(qids,field,fresh,cached):
    prop={'birth':'P569','death':'P570'}[field];values=set()
    for q in qids:
        if q in fresh:
            for c in fresh[q]['claims'].values():
                if c['property']==prop and c['rank']!='DeprecatedRank' and c['precision'] is not None and c['precision']>=9 and c['value']:values.add(r.year(c['value']))
        elif q in cached:values.update(r.year(x) for x in cached[q][field])
    return values-{None}
def life_update(record,fields):
    out={}
    for key,d in fields.items():
        for tail,value in [('year',d['year']),('display',d['display']),('precision',d['precision'])]:out[key+'_'+tail]=value
    merged={**record,**out};b,d=merged['birth_year'],merged['death_year']
    if b is not None and d is not None:
        assert 15<=d-b<=125
        out.update(timeline_start_year=b,timeline_end_year=d,timeline_basis='life',timeline_display=(merged['birth_display'] or str(b))+'–'+(merged['death_display'] or str(d)))
    elif merged['timeline_basis']=='life':
        # Keep the existing plotting extent but stop calling its unknown endpoint a death/birth.
        out.update(timeline_basis='estimated',timeline_display=('born '+(merged['birth_display'] or str(b))+'; death unknown') if b is not None else ('died '+(merged['death_display'] or str(d))+'; birth unknown'))
    return {k:v for k,v in out.items() if record[k]!=v}
def plan():
    base=r.load(RUN/'production-snapshot.json.gz');artists={a['record']['id']:a for a in base['artists']};bindings=r.load(RUN/'research-identity-bindings.json.gz');fresh=r.load(RUN/'fresh-date-index.json.gz');cached=r.load(RUN/'cached-authority-index.json.gz')
    datasets={};indexes={};coverage=collections.defaultdict(list);rows={};decisions=[]
    specs=[('nga','nga-constituent','constituentid','displaydate'),('tate','tate-person','id','dates'),('moma','moma-person','ConstituentID','ArtistBio')]
    for provider,scheme,key,labelkey in specs:
        data=r.load(RUN/(provider+'-artist-authority.json.gz'));datasets[provider]=data;indexes[provider]={str(x[key]):x for x in data['records']}
    def add(a,updates,source_url,receipt,basis,evidence):
        ar=a['record'];updates={k:v for k,v in updates.items() if ar[k]!=v}
        if not updates:return
        assert ar['id'] not in rows,'Multiple correction plans for '+ar['display_name']
        rows[ar['id']]=dict(artist_id=ar['id'],name=ar['display_name'],before=ar,updates=updates,source_url=source_url,receipt=receipt,basis=basis,evidence=evidence)
    for a in artists.values():
        ar=a['record']
        if ar['status']=='archived':continue
        for provider,scheme,key,labelkey in specs:
            for ext in a['identifiers']:
                if ext['scheme']!=scheme:continue
                source=indexes[provider].get(ext['external_id'])
                if not source:continue
                label=source[labelkey] or '';receipt=datasets[provider]['receipt'];coverage[ar['id']].append(dict(provider=provider,native_id=ext['external_id'],literal=label,record=source,receipt=receipt))
                evidence=dict(native_identifier=ext,literal=label,source_record=source)
                if provider=='tate' and label.startswith('active'):
                    # Restore the source's semantics only when these are demonstrably the imported bounds.
                    nums=[int(x) for x in re.findall(r'\d{4}',label)]
                    if len(nums)==2 and (ar['birth_year'],ar['death_year'])==tuple(nums) and ar['timeline_basis']=='life':
                        died='died' in label
                        update=dict(birth_year=None,birth_display=None,birth_precision=None,death_year=nums[1] if died else None,death_display=str(nums[1]) if died else None,death_precision='exact' if died else None,active_start_year=nums[0],active_end_year=nums[1],activity_display=label,timeline_start_year=nums[0],timeline_end_year=nums[1],timeline_display=label,timeline_basis='mixed' if died else 'activity')
                        add(a,update,ext['canonical_url'],receipt,'Restore literal museum activity period; numeric export columns are not birth/death evidence.',evidence)
                    continue
                fields=literal_life(label)
                if not fields or ar['entity_type']!='person' or (provider=='nga' and source['constituenttype']!='individual'):continue
                conflicts=[];updates={};qs=r.effective_qids(a,bindings)
                for field,value in fields.items():
                    old=ar[field+'_year'];years=source_years(qs,field,fresh,cached)
                    if old is not None and old!=value['year']:conflicts.append(field+': existing source disagreement')
                    if years and value['year'] not in years:conflicts.append(field+': authority disagreement')
                    if old is None or (old==value['year'] and value['precision']=='circa' and ar[field+'_precision'] in [None,'exact']):updates[field]=value
                if len(qs)>1:conflicts.append('multiple identity authorities')
                merged={**ar,**{k+'_year':v['year'] for k,v in updates.items()}}
                if merged['birth_year'] is not None and merged['death_year'] is not None and not 15<=merged['death_year']-merged['birth_year']<=125:conflicts.append('implausible lifespan')
                if conflicts:decisions.append(dict(artist_id=ar['id'],name=ar['display_name'],state='conflicting_evidence_preserved',reasons=conflicts,evidence=evidence));continue
                if updates and ar['id'] not in rows:add(a,life_update(ar,updates),ext['canonical_url'] or receipt['url'],receipt,'Exact existing museum creator identifier; explicit literal life dates. Fill missing fields or restore stated circa precision; no inferred death from export bounds.',evidence)
    # Individually reviewed corrections, with captured primary evidence.
    def page(name):return r.load(RUN/'primary-pages'/(name+'.json.gz'))
    a=artists['c90a7468-e048-4a36-b497-bfe638973be0'];src=page('uccello');assert 'about 1397 - 1475' in src['text'];rows.pop(a['record']['id'],None)
    update=life_update(a['record'],dict(birth=dict(year=1397,precision='circa',display='c. 1397'),death=dict(year=1475,precision='exact',display='1475')))
    update['biography_md']='Paolo Uccello (c. 1397–1475) was an Italian painter. He trained with Lorenzo Ghiberti and is known for his investigations of linear perspective.\n\nSource: [National Gallery, London](https://www.nationalgallery.org.uk/artists/paolo-uccello). The birth year is approximate.'
    add(a,update,src['receipt']['url'],src['receipt'],'Primary museum chronology overrides erroneous Pantheon birthyear 1475; birth remains approximate.',dict(literal='about 1397 - 1475',original_import_capture='uccello-original-import-records.json.gz'))
    for aid,name,needle in [('04674ef6-db0e-5f58-a126-b9457cd9e0ec','henner','Laura (1872-1936)'),('6c57a4ef-03a3-5a1c-ba48-2895778ee589','roll','ROLL Alfred (1846-1919)')]:
        a=artists[aid];ar=a['record'];src=page(name);assert needle in src['text'];rows.pop(aid,None)
        add(a,dict(timeline_start_year=ar['birth_year'],timeline_end_year=ar['death_year'],timeline_display=str(ar['birth_year'])+'–'+str(ar['death_year'])),src['receipt']['url'],src['receipt'],'Synchronize timeline with the previously reviewed primary museum life dates; preserve primary evidence over conflicting Wikidata.',dict(literal=needle))
    a=artists['16a29412-3bd2-4965-a65c-f144c7941eab'];src=page('rondinelli');assert 'documented 1495-1502' in src['text'];rows.pop(a['record']['id'],None)
    add(a,dict(birth_year=None,death_year=None,birth_display=None,death_display=None,birth_precision=None,death_precision=None,active_start_year=1495,active_end_year=1502,activity_display='documented 1495–1502',timeline_start_year=1495,timeline_end_year=1502,timeline_display='documented 1495–1502',timeline_basis='activity'),src['receipt']['url'],src['receipt'],'Museum explicitly labels these years as documented activity, not a lifespan.',dict(literal='Niccolò Rondinelli (Italian, documented 1495-1502)'))
    a=artists['76d36b55-ccd4-5357-89a3-e8650912b323'];src=page('locke-gallery');assert 'Lives and works in London' in src['text'] and '1959' in src['text'];rows.pop(a['record']['id'],None)
    add(a,dict(death_year=None,death_display=None,death_precision=None,timeline_start_year=1959,timeline_end_year=2026,timeline_display='born 1959 (living in October 2026 source)',timeline_basis='estimated'),src['receipt']['url'],src['receipt'],'Current representing gallery and artist website contradict erroneous same-day birth/death authority claim. The 2026 plotting endpoint is the dated observation, not a death year.',dict(literal='b. 1959; Lives and works in London, UK',artist_website=page('locke')['receipt']))
    for aid,name,label in [('56768587-ee3a-5f4a-a6d5-b27a497c07a3','aztec','Cultural tradition: c. 1300–1521'),('592e4e11-34d3-50e0-b0c2-8a1d6eda20bd','viking','Cultural tradition: c. 780–c. 1100'),('97ff3704-63c8-5004-bd80-5baa57ca29e3','marseille','Collective project: 1940–1941')]:
        src=page(name)
        if src['receipt']['status']!=200:continue
        a=artists[aid];ar=a['record'];rows.pop(aid,None)
        add(a,dict(entity_type='collective',birth_year=None,death_year=None,birth_display=None,death_display=None,birth_precision=None,death_precision=None,active_start_year=ar['timeline_start_year'],active_end_year=ar['timeline_end_year'],activity_display=label,timeline_display=label,timeline_basis='activity'),src['receipt']['url'],src['receipt'],'Source describes a cultural tradition or collective project, not an individual person. Retain source period as activity and all catalogue links.',dict(literal_period=label))
    r.save(RUN/'primary-artist-comparison.json.gz',dict(coverage=coverage,conflicts=decisions))
    result=dict(at=r.now(),target='production',rows=list(rows.values()),publication_changes=0,local_changes=0)
    r.save(RUN/'correction-plan.json.gz',result)
    counts=collections.Counter(field for row in rows.values() for field in row['updates']);print('Planned artists',len(rows),'fields',dict(counts),'primary covered',len(coverage),'conflicts',len(decisions),flush=True)
def final_plan():
    data=r.load(RUN/'correction-plan.json.gz');rows={x['artist_id']:x for x in data['rows']};artists={x['record']['id']:x for x in r.load(RUN/'production-snapshot.json.gz')['artists']}
    def add(a,updates,src,basis,evidence):
        ar=a['record'];assert ar['id'] not in rows
        rows[ar['id']]=dict(artist_id=ar['id'],name=ar['display_name'],before=ar,updates={k:v for k,v in updates.items() if ar[k]!=v},source_url=src['receipt']['url'],receipt=src['receipt'],basis=basis,evidence=evidence)
    def activity(a,start,end,label,src,basis,evidence,estimated=False):
        add(a,dict(birth_year=None,death_year=None,birth_display=None,death_display=None,birth_precision=None,death_precision=None,active_start_year=None if estimated else start,active_end_year=None if estimated else end,activity_display=None if estimated else label,timeline_start_year=start,timeline_end_year=end,timeline_display=label,timeline_basis='estimated' if estimated else 'activity'),src,basis,evidence)
    # Museum histories explicitly explain why their numeric birth/death columns are placeholders.
    for number,lref,start,end,label,estimated in [
      ('KMS4507','3222_person',1753,1754,'documented commissions 1753–1754',False),
      ('KMS986','584_person',1703,1711,'active in Copenhagen 1703–1711',False),
      ('KMSst128','2909_person',1669,1669,'documented work 1669; lifetime unknown',False),
      ('KMSsp535','3120_person',1711,1810,'Work dated 1711–1810; lifetime unknown',True),
      ('KMS676','37695_person',1725,1824,'Work dated 1725–1824; lifetime unknown',True),
      ('KMSst479','37677_person',1728,1827,'Work dated 1728–1827; lifetime unknown',True),
    ]:
        a=next(x for x in artists.values() if any(e['scheme']=='smk-person' and e['external_id']==lref for e in x['identifiers']));src=r.load(RUN/'smk-sources'/(number+'.json.gz'));obj=src['data']['items'][0];creator=next(c for c in obj['production'] if c['creator_lref']==lref)
        activity(a,start,end,label,src,'Exact museum creator ID. Native creator history explicitly bases numeric dates on activity, object dating or acquisition; remove unsupported life dates. Broad object dates remain estimated placement, not an asserted career.',dict(creator=creator,production_date=obj['production_date']),estimated)
    src=r.load(RUN/'primary-pages'/'bezzi.json.gz');assert 'documenté en 1558 ; mort en 1571' in src['text'];a=artists['0af21a33-1348-43ac-8bd4-f42b5b44540a']
    add(a,dict(birth_year=None,birth_display=None,birth_precision=None,death_display='1571',death_precision='exact',active_start_year=1558,active_end_year=1558,activity_display='documented 1558',timeline_display='documented 1558; died 1571',timeline_basis='mixed'),src,'Native museum author clarification distinguishes first documentation from death; no Nosadella identity merge inferred.',dict(literal='documenté en 1558 ; mort en 1571'))
    src=r.load(RUN/'primary-pages'/'norma-gallery.json.gz');assert 'born in 1933' in src['text'] and '1951-55' in src['text'];a=artists['61c772ae-faa6-502a-be43-2d3eeb7c4ba8']
    add(a,dict(death_year=None,death_display=None,death_precision=None,timeline_end_year=1933,timeline_basis='estimated',timeline_display='born 1933; death unknown'),src,'Gallery biography documents art education and a career after the erroneous 1941 death. Remove contradicted death without asserting current living status or inventing a lifespan.',dict(birth=1933,documented_art_education='Bath Academy of Art 1951–1955; Liverpool University 1955–1956'))
    for aid,name,start,end,needle in [('b0f6fbd0-9d03-5ce2-829f-97eb70f5fd51','maud',1893,1905,'fl.1893'),('e78ffec7-a6fc-5b21-a2e5-c70a1b350ffe','curtius',1889,1930,'active 1889-1930')]:
        src=r.load(RUN/'primary-pages'/(name+'.json.gz'))
        if src['receipt']['status']!=200 or needle not in src['text']:continue
        activity(artists[aid],start,end,'active '+str(start)+'–'+str(end)+'; lifetime unknown',src,'Primary collection/authority explicitly labels activity dates; do not turn them into life endpoints.',dict(literal=needle,source_alternative_preserved=True))
    # Inspect introduced chronology flags before approval of the executable manifest.
    works=collections.defaultdict(list)
    for w in r.load(RUN/'production-snapshot.json.gz')['artwork_links']:works[w['artist_id']].append(w)
    for x in rows.values():
        ar={**x['before'],**x['updates']};assert ar['status']==x['before']['status'] and ar['published_at']==x['before']['published_at'];assert ar['timeline_start_year']<=ar['timeline_end_year']
        x['artwork_review_before']=dict(collections.Counter(f for w in works[x['artist_id']] for f in r.artwork_flags(w,x['before'])))
        x['artwork_review_after']=dict(collections.Counter(f for w in works[x['artist_id']] for f in r.artwork_flags(w,ar)))
    result=dict(at=r.now(),target='production',rows=list(rows.values()),publication_changes=0,local_changes=0,artwork_changes=0)
    r.save(RUN/'final-correction-plan.json.gz',result);print('Final correction plan',len(rows),flush=True)
if __name__=='__main__':
    import sys
    globals()[sys.argv[1]]()
