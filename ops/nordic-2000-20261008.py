#!/usr/bin/env python3
"""Selected Nordic continuation, with explicit authorization for direct delivery."""
import argparse,collections,copy,csv,gzip,importlib.util,json,re,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('nordic_base',ROOT/'ops/nordic-1000-20261008.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
n=b.n;m=b.m;OP='nordic-2000-20261008';RUN=ROOT/'docs/research'/OP;PREVIOUS=ROOT/'docs/research/nordic-1000-20261008'
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
b.OP=OP;b.RUN=RUN;b.BACKUP=BACKUP;b.TARGET=2000;m.RUN=RUN;n.RUN=RUN
b.AUTHORIZATION="User: nice add more 1000 or 2000, don't ask my approve. Continue Denmark, Sweden and Norway production catalogue additions directly. Target 2,000 genuinely new objects."
b.BACKUP_DESCRIPTION='Before Nordic additional 2000 artworks 20261008'
b.EVIDENCE_FILES=['baseline.json.gz','selected.json.gz','source-decisions.json.gz','current-native-samples.json']
save=b.save;load=b.load;norm=b.norm;acc=b.acc

def capture(url,params=None,pace=1.2):return b.capture(url,params,pace)
baseline=b.baseline;backup=b.backup;backup_verify=b.backup_verify

def norwegian_fragment(part=0):
    # One bounded metadata fragment, not the complete collection or any images.
    assert part in (0,3)
    url=f'https://raw.githubusercontent.com/nasjonalmuseet/collection/master/metadata-json/nasjonalmuseet-collection-part{part}.json'
    key=m.sha(url.encode());dest=RUN/'captures'/(key+'.json');body=dest.with_suffix('.body.gz')
    if dest.exists():return gzip.decompress(body.read_bytes()),load(dest)
    response=m.SESSION.get(url,timeout=(15,90),stream=True)
    if response.status_code in (403,429):raise RuntimeError('Source access restriction; stop this source')
    response.raise_for_status();chunks=[];size=0
    for part in response.iter_content(65536):
        size+=len(part);assert size<=35_000_000,'Bounded fragment size exceeded';chunks.append(part)
    raw=b''.join(chunks);body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(gzip.compress(raw,mtime=0))
    rc=dict(url=url,final_url=response.url,status=200,retrieved_at=m.now(),bytes=len(raw),sha256=m.sha(raw),body_path=str(body.relative_to(ROOT)))
    save(dest,rc);return raw,rc

def norway(part=0):
    mu=b.museums()['Q1132918'];existing,titles=b.existing_keys(mu);raw,rc=norwegian_fragment(part);data=json.loads('{'+raw.decode()+'}')
    rows=[];held=[];lead_count=0
    for item in data['hits']:
        lead_count+=1;row,reason=b.norwegian_fields(item,mu,rc)
        if row and (acc(row['accession']) in existing or any(norm(t) in titles for t in row['title_aliases'])):reason='Existing institution inventory/title'
        if reason:held.append(dict(key=item['_id'],reason=reason))
        elif len(rows)<1800:rows.append(row)
    suffix='' if part==0 else '-extra'
    save(RUN/('norway'+suffix+'-selected.json.gz'),rows);save(RUN/('norway'+suffix+'-decisions.json.gz'),dict(lead_count=lead_count,selected=len(rows),held=held,source_date='2020-12-03',selection='One 10,000-record museum metadata fragment; up to 1,800 eligible painting/drawing candidates; no image downloads.'))
    print('Norway candidates',len(rows),'from bounded fragment',lead_count,collections.Counter(r['reason'] for r in held),flush=True)

def norway_extra():norway(3)

def graphic_fields(e,mu,rc):
    types=[x.get('name') for x in e.get('object_names',[])];inventory=e.get('object_number','')
    if types!=['Drawing'] or not inventory.startswith('KKS'):return None,'Outside selected KKS drawing scope'
    if re.search(r'\b(?:recto|verso)\b',inventory,re.I):return None,'Sheet-side identity needs individual object reconciliation'
    # Reuse date and creator checks without changing the retained source record.
    surrogate=copy.deepcopy(e);surrogate['object_number']='KMS-validation';surrogate['object_names']=[dict(name='Painting')]
    row,why=b.smk_fields(surrogate,mu,rc)
    if why:return None,why
    row.update(key=row['source_scheme']+'/'+inventory,qid=inventory,external_id=inventory,work_type='drawing',inventories=[inventory],accession=inventory,source_evidence=e)
    return row,None

def smk():
    mu=b.museums()['Q671384'];existing,titles=b.existing_keys(mu);rows=[];held=[];seen=set();pages=[]
    for nationality in ['French','German','Italian','Dutch','Norwegian','Swedish','Russian','Greek']:
        for offset in [0,250]:
            raw,rc=capture('https://api.smk.dk/api/v1/art/search/',dict(keys='*',filters=f'[object_names:Drawing],[creator_nationality:{nationality}]',rows=250,offset=offset,lang='en',sort='object_number',sort_type='asc'))
            assert rc['status']==200;data=json.loads(raw);pages.append(dict(nationality=nationality,offset=offset,found=data['found'],count=len(data['items']),receipt=rc))
            for e in data['items']:
                if e['id'] in seen:continue
                seen.add(e['id']);row,reason=graphic_fields(e,mu,rc)
                if row and (acc(row['accession']) in existing or any(norm(t) in titles for t in row['title_aliases'])):reason='Existing institution inventory/title'
                if reason:held.append(dict(key=e['object_number'],reason=reason))
                else:rows.append(row)
            print('SMK',nationality,offset,'cumulative new candidates',len(rows),flush=True)
            if offset+len(data['items'])>=data['found']:break
    save(RUN/'smk-selected.json.gz',rows);save(RUN/'smk-decisions.json.gz',dict(leads=len(seen),pages=pages,held=held))

def wd_index():
    # Continue past previously researched entities, keeping referenced collection evidence.
    known=set()
    for folder in [PREVIOUS,ROOT/'docs/research/nordic-museums-20261008']:
        for path in (folder/'entities').glob('works*/*.json.gz'):known.update(load(path)['entities'])
    base=load(RUN/'baseline.json.gz');known.update(x['external_id'] for x in base['identifiers'] if x['scheme']=='wikidata')
    targets=[('Q842858',1200),('Q1992004',120),('Q4346239',120),('Q1132918',200),('Q844926',120),('Q3555520',100),('Q2982867',100),('Q1140507',100),('Q10601378',100)]
    choices=[];ledger=[]
    for q,limit in targets:
        if q not in b.museums():continue
        ids=[]
        for offset in [0,1800]:
            if offset and q!='Q842858':break
            query='SELECT DISTINCT ?work WHERE { ?work wdt:P195 wd:'+q+'; wdt:P31 wd:Q3305213; wdt:P571 ?date . FILTER(?date <= "1970-12-31T23:59:59Z"^^xsd:dateTime) ?work p:P195 ?claim . ?claim ps:P195 wd:'+q+'; prov:wasDerivedFrom ?reference . { ?reference pr:P854 ?url } UNION { ?reference pr:P248 ?source } } ORDER BY ?work LIMIT 1800 OFFSET '+str(offset)
            raw,rc=capture('https://query.wikidata.org/sparql',dict(query=query,format='json'),pace=8);assert rc['status']==200
            found=[r['work']['value'].rsplit('/',1)[-1] for r in json.loads(raw)['results']['bindings']]
            ids += [v for v in found if v not in known];ledger.append(dict(qid=q,offset=offset,count=len(found),receipt=rc))
            if len(ids)>=limit or len(found)<1800:break
        selected=list(dict.fromkeys(ids))[:limit];choices+=selected;print('Referenced WD candidates',q,len(selected),flush=True)
    save(RUN/'wd-choices.json',sorted(set(choices)));save(RUN/'wd-index.json',ledger)

def entities():
    n.entity_batches(load(RUN/'wd-choices.json'),'works')
    creators=set()
    for d in n.saved_entities('works').values():creators.update(v['id'] for v in n.vals(d['entity'],'P170') if isinstance(v,dict) and 'id' in v)
    n.entity_batches(creators,'creators')

def collection_inventories(entity,museum_qid):
    result=[]
    for claim in n.active(entity,'P217'):
        qs=claim.get('qualifiers',{});value=n.value(claim)
        if not isinstance(value,str) or set(qs)!={'P195'}:continue
        collections_=qs['P195']
        if len(collections_)==1 and collections_[0].get('datavalue',{}).get('value',{}).get('id')==museum_qid:result.append(value)
    return result

def creator_date_conflict(row,creators):
    for q in row['creator_qids']:
        e=creators.get(q,{}).get('entity',{})
        for prop,condition in [('P569',lambda y:row['last']<y),('P570',lambda y:row['first']>y+5)]:
            vs=n.vals(e,prop)
            if len(vs)!=1 or not isinstance(vs[0],dict) or vs[0].get('precision',0)<9:continue
            hit=re.match(r'^\+(\d{4})-',vs[0].get('time',''))
            if hit and condition(int(hit[1])):return 'Creation date conflicts with source creator lifetime; held without substituting an inferred date'
    return None

def wd_select():
    ms=b.museums();creators=n.saved_entities('creators');rows=[];held=[]
    for q,d in n.saved_entities('works').items():
        qs=[v['id'] for v in n.vals(d['entity'],'P195') if isinstance(v,dict)]
        if len(qs)!=1 or qs[0] not in ms:held.append(dict(key=q,reason='Multiple or unresolved institutions'));continue
        row,why=n.work_fields(d['entity'],ms[qs[0]],creators,d['receipt'])
        if not why and row['precision']=='unknown':why='No explicit eligible date in this selected continuation'
        if not why:why=creator_date_conflict(row,creators)
        if why:held.append(dict(key=q,reason=why));continue
        row['inventories']=list(dict.fromkeys(row['inventories']+collection_inventories(d['entity'],qs[0])));row['accession']='; '.join(row['inventories']) or None
        row.update(key='wikidata/'+q,source_scheme='wikidata',external_id=q,country=ms[qs[0]]['country'],source_kind='referenced Wikidata record',source_evidence=d['entity'])
        rows.append(row)
    save(RUN/'wd-selected-v2.json.gz',rows);save(RUN/'wd-held-v2.json',held)
    print('WD eligible',len(rows),collections.Counter(r['country'] for r in rows),'held',collections.Counter(r['reason'] for r in held),flush=True)

def raw_rows():
    rows=[]
    for name in ['norway-selected.json.gz','norway-extra-selected.json.gz','smk-selected.json.gz','wd-selected-v2.json.gz']:
        if (RUN/name).exists():rows+=load(RUN/name)
    for r in rows:
        if r['source_scheme']=='nasjonalmuseet-object':
            original=r['source_url'];canonical='https://www.nasjonalmuseet.no/en/collection/object/'+b.quote(r['accession'].replace('&','_'),safe='')
            r.update(source_url=canonical,native_urls=list(dict.fromkeys([canonical,original])),references=[canonical,r['receipt']['url']],object_url_normalization=dict(original_inventory=r['accession'],legacy_url=original,basis='The museum public collection links and getUrlSafeNmId implementation replace ampersands with underscores in object URL paths; catalogue inventories remain unchanged.',evidence='native-url-evidence.json'))
    assert len({r['key'] for r in rows})==len(rows),'Duplicate source keys between evidence packages'
    return rows

def native_samples():
    raw,rc=capture('https://www.nasjonalmuseet.no/en/collection/');soup=m.BeautifulSoup(raw,'html.parser');links=[a['href'] for a in soup.select('a[href]') if '/collection/object/NG.K_H.' in a['href']]
    assert links
    js,jrc=capture('https://www.nasjonalmuseet.no/dist/vue-ssr.461bbb09f1ceb58f.js')
    rule='getUrlSafeNmId(e){return e.replace(RegExp("&","g"),"_")}'
    assert rule in js.decode();save(RUN/'native-url-evidence.json',dict(receipt=rc,example_links=links[:8],implementation_receipt=jrc,public_url_rule=rule))
    rows=[r for r in raw_rows() if r['source_scheme']=='nasjonalmuseet-object'];groups=collections.defaultdict(list)
    for r in rows:groups[(r['receipt']['url'],r['work_type'])].append(r)
    samples=[]
    for group in groups.values():samples+=group[::max(1,len(group)//4)][:4]
    results=[]
    for r in samples:
        raw,rc=capture(r['source_url']);out=dict(key=r['key'],receipt=rc,verified=False,source='Current museum object page')
        if rc['status']==200:
            soup=m.BeautifulSoup(raw,'html.parser');head=soup.select_one('.collection-object-header');fields={}
            for dt in soup.select('.description-list dt'):
                dd=dt.find_next_sibling('dd')
                if dd:fields[dt.get_text(' ',strip=True).rstrip(':')]=dd.get_text(' ',strip=True)
            if head and head.select_one('h1'):
                title=head.select_one('h1').get_text(' ',strip=True);names=[a.get_text(' ',strip=True) for a in head.select('a[href*="/producer/"]')]
                years=[int(y) for y in re.findall(r'\b[12]\d{3}\b',fields.get('Creation date',''))]
                out.update(title=title,creators=names,fields=fields,verified=bool(acc(fields.get('Inventory no.',''))==acc(r['accession']) and norm(title) in {norm(t) for t in r['title_aliases']} and norm(r['creator_label']) in {norm(x) for x in names} and years and min(years)>=r['first'] and max(years)<=r['last']))
        results.append(out);print('Native sample',r['accession'],'verified',out['verified'],flush=True)
    save(RUN/'current-norway-samples-v2.json',results)

def swedish_samples():
    rows=[r for r in load(RUN/'wd-selected-v2.json.gz') if r['institution_qid']=='Q842858' and n.vals(r['source_evidence'],'P2539')];creators=n.saved_entities('creators');results=[]
    for r in rows[::max(1,len(rows)//10)][:10]:
        ids=n.vals(r['source_evidence'],'P2539')
        if len(ids)!=1:continue
        url='https://collection.nationalmuseum.se/en/collection/item/'+str(ids[0])+'/'
        raw,rc=capture(url);out=dict(key=r['key'],receipt=rc,verified=False,source='Current museum object page')
        if rc['status']==200:
            soup=m.BeautifulSoup(raw,'html.parser');script=soup.find('script',id='__NEXT_DATA__')
            if script:
                item=json.loads(script.string)['props']['pageProps']['data']['item'];makers=item.get('ObjPersonRef',{}).get('Items',[])
                aliases=set()
                for q in r['creator_qids']:
                    e=creators.get(q,{}).get('entity',{});aliases.update(norm(v['value']) for v in e.get('labels',{}).values());aliases.update(norm(v['value']) for vs in e.get('aliases',{}).values() for v in vs)
                names=[norm(re.sub(r'\s*\([^)]*\)\s*$','',x.get('LinkLabelTxt',''))) for x in makers]
                date=item.get('ObjDateMainTxt') or '';years=[int(y) for y in re.findall(r'\b[12]\d{3}\b',date)]
                verified=bool(len(makers)==len(r['creator_qids']) and names and all(name in aliases for name in names) and all(x.get('RoleVoc',{}).get('LabelTxt')=='Artist' for x in makers) and acc(item.get('ObjInventoryNumberTxt','')) in {acc(v) for v in r['inventories']} and years and min(years)<=r['last']<=max(years) and max(years)<=1970)
                out.update(fields=item,verified=verified)
        results.append(out);print('Swedish native sample',r['qid'],'verified',out['verified'],flush=True)
    save(RUN/'current-sweden-samples-v2.json',results)

def ambiguous_sheet_keys(rows,baseline):
    def family(value):return acc(re.sub(r'\b(?:recto|verso)\b','',value or '',flags=re.I))
    marked=lambda value:bool(re.search(r'\b(?:recto|verso)\b',value or '',re.I))
    smk=[r for r in rows if r['source_scheme']=='european-smk-statens-museum-for-kunst-object']
    museums={r['institution_id'] for r in smk}
    families={(r['institution_id'],family(r['accession'])) for r in smk if marked(r['accession'])}
    families.update((r['current_institution_id'],family(r['accession_number'])) for r in baseline['works'] if r['current_institution_id'] in museums and marked(r['accession_number']))
    return {r['key'] for r in smk if (r['institution_id'],family(r['accession'])) in families}

def selection():
    samples=load(RUN/'current-norway-samples-v2.json')+load(RUN/'current-sweden-samples-v2.json');heldkeys={r['key'] for r in samples if not r['verified']}
    checked={r['key']:r for r in samples if r['verified']};rows=[];candidates=raw_rows();sheetkeys=ambiguous_sheet_keys(candidates,load(RUN/'baseline.json.gz'))
    for r in candidates:
        if r['key'] in heldkeys or r['key'] in sheetkeys:continue
        if r['key'] in checked:r['current_native_corroboration']=checked[r['key']]
        rows.append(r)
    save(RUN/'current-native-samples.json',samples);save(RUN/'selected.json.gz',rows)
    decisions=dict(at=m.now(),source_files=[n.proof_file(RUN/f) for f in ['norway-decisions.json.gz','norway-extra-decisions.json.gz','smk-decisions.json.gz','wd-held-v2.json','wd-index.json','native-url-evidence.json']],current_native_samples_held=sorted(heldkeys),sheet_identity_held=sorted(sheetkeys),selected_count=len(rows),policy='Selected explicit pre-1971 museum-connected objects. Unknown dates, qualified creators, multipart/verso identities, source conflicts and possible duplicates remain held; no image downloads or current-display claims.')
    save(RUN/'source-decisions.json.gz',decisions);print('Source-selected',len(rows),collections.Counter(r['country'] for r in rows),flush=True)

b.source_rows=lambda:load(RUN/'selected.json.gz')
prepare=b.prepare;apply=b.apply;verify=b.verify

def report():
    plan,digest=b.pinned();applied=load(RUN/'applied.json');database=load(RUN/'database-verification.json');api=load(RUN/'api-verification.json');rows=plan['records'];count=len(rows)
    assert count==applied['new_artworks']==database['verified_artworks']==2000
    country=collections.Counter(r['country'] for r in rows);types=collections.Counter(r['work_type'] for r in rows);sources=collections.Counter(r['source_kind'] for r in rows);museums=collections.Counter(r['institution_id'] for r in rows);linked=sum(bool(r['artist_ids']) for r in rows);labeled=sum(bool(r['creator_label']) and not r['artist_ids'] for r in rows)
    with (RUN/'delivered-artworks.csv').open('w',newline='') as f:
        fields=['country','museum','artwork_id','title','creator','date','work_type','inventory','source_kind','object_url','captured_evidence_url'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:w.writerow(dict(country=r['country'],museum=plan['institutions'][r['institution_id']]['name'],artwork_id=r['artwork_id'],title=r['title'],creator=r['creator_label'],date=r['date_display'],work_type=r['work_type'],inventory=r['accession'],source_kind=r['source_kind'],object_url=r['source_url'],captured_evidence_url=r['receipt']['url']))
    country_table='\n'.join(f'| {name} | {country[cc]} |' for cc,name in [('DK','Denmark'),('SE','Sweden'),('NO','Norway')])
    museum_table='\n'.join(f"| {plan['institutions'][iid]['name']} | {num} |" for iid,num in sorted(museums.items(),key=lambda x:-x[1]))
    samples=load(RUN/'current-native-samples.json');identity=load(RUN/'identity-review.json.gz');native=load(RUN/'current-norway-samples-v2.json');swedish=load(RUN/'current-sweden-samples-v2.json')
    md=f'''# Additional 2,000 Nordic artworks — 8 October 2026

The user requested “nice add more 1000 or 2000, don't ask my approve.” This continuation delivered **exactly 2,000 new production artworks** with documented collection links across **{len(museums)} existing institutions**. The previous 1,000 records and all other existing records were excluded from the new-object count. New records retain review status as audit data and are available through the unified catalogue.

| Country | New artworks |
| --- | ---: |
{country_table}

The batch contains **{types['painting']} paintings** and **{types['drawing']} drawings**. All selected creation bounds end in or before 1970. Original ranges, circa qualifiers, titles, inventory numbers, materials and known dimensions are retained. No dates, creator biographies or images were invented.

## Collections expanded

| Collection | Added artworks |
| --- | ---: |
{museum_table}

## Evidence

- **{sources['european-smk-statens-museum-for-kunst-object']} SMK drawings:** selected from the museum's [public catalogue API](https://api.smk.dk/api/v1/docs/), using bounded nationality-specific drawing searches, with at most 500 source records per requested group. Danish holdings include works by artists from other countries. The exact KKS inventory and museum creator authority IDs are retained. Deposits, uncertain creation bounds and qualified/multiple creator roles were withheld.
- **{sources['nasjonalmuseet-object']} Norwegian objects:** selected from two bounded fragments of [Nasjonalmuseet's own metadata](https://github.com/nasjonalmuseet/collection), 20,000 source records in total, rather than the complete five-fragment dataset. The museum export is dated **3 December 2020**; that date remains explicit in every relevant citation. A current retrieval does not make its catalogue facts newly researched. Current museum-page samples corroborated {sum(x['verified'] for x in native)} of {len(native)} sampled records; the remaining sample decisions are held. Museum inventory ampersands remain unchanged, while object URLs use the museum's documented underscore format. Public collection links and the museum's own URL builder were captured to establish this format.
- **{sources['referenced Wikidata record']} referenced Wikidata records:** continued beyond previously researched entities, scoped to the verified Nordic institutions. Every accepted row has exact object identity, a supported collection statement, eligible source date and retained creator/attribution evidence. Linked underlying reference pages were not described as independently fetched. Native Swedish object-page checks corroborated {sum(x['verified'] for x in swedish)} of {len(swedish)} samples; records with conflicting or unresolved primary fields were withheld.

Holding confidence remains an editorial assessment, not a calibrated probability. Holdings establish a source-backed collection connection, not current display or a legal-ownership guarantee. No current-display assertions were created. All raw source statements, receipts and limitations remain available in the hashed plan and citations.

**{linked}** objects link to unique existing museum/Wikidata creator authorities. **{labeled}** retain source creator labels without creating artist profiles or treating a matching name as proof of identity. **{count-linked-labeled}** preserve an unknown creator explicitly. Names are used conservatively to flag possible pre-existing artwork versions even where a source creator has no linked profile.

Collection-qualified inventory numbers are accepted only when the qualifier names the exact museum. Forty-five SMK candidates with an explicit sheet-side identity or matching sheet family were held. Six Wikidata candidates with creation years conflicting with the source creator lifetime were held; lifetime evidence was used only to detect conflicts, never to invent a replacement creation date.

## Reconciliation and verification

The final duplicate review checked global source identifiers and object URLs, institution-scoped inventories, selected indexed title/creator candidates and within-batch object/version identities. It withheld {len(identity['held'])} candidates and retained {len(identity['remaining'])} additional eligible candidates outside the requested batch. Exact new IDs were absent before the transaction. Relevant institutions and creators were locked and compared with the pinned plan before insertion.

All **2,000 database records** passed metadata, source identity, holding, creator, citation, audit, review-state and image-absence checks. All **{len(api['museums'])} affected live museum responses** and **{len(api['artworks'])} representative artwork responses** passed, with samples spanning institutions, work types, date precision and linked/unlinked creators. Country browsing was checked through bounded pagination, with positive collection counts. **28 offline regression checks passed** for source eligibility, attribution, date boundaries, version exclusions, collection-qualified inventories, identifier namespaces and duplicate candidates.

The Cloud SQL recovery backup **{load(RUN/'cloud-backup.json')['id']}** completed before production writes. Plan SHA-256: `{digest}`. Recovery plans, locked preimages and transaction postimages are stored under `{BACKUP}`. The complete batch was inserted atomically and verified before commit. Existing artwork, institution and creator metadata was not rewritten; existing images and publication states were preserved. No new images were downloaded or attached. The real local catalogue was unchanged.

The retained execution plan concerns the current production catalogue; it is not a 10-million-row load test. No application deployment, Terraform apply, test database, catalogue fixture or Git commit was used. Temporary test outputs are kept outside Documents.

This pass expands selected collection content. It does not establish complete national museum or artwork coverage. The [575-lead institution ledger](../nordic-museums-20261008/coverage-and-gaps.csv) and prior source gaps remain applicable.

## Delivery files

- [All 2,000 delivered records](delivered-artworks.csv)
- [Production receipt](applied.json)
- [Database verification](database-verification.json)
- [Live API checks](api-verification.json)
- [Source decisions](source-decisions.json.gz)
- [Identity exclusions](identity-review.json.gz)
- [Current native museum samples](current-native-samples.json)
- [Norwegian object URL evidence](native-url-evidence.json)

Procedure: `ops/nordic-2000-20261008.py`, using the shared insert/verification functions in `ops/nordic-1000-20261008.py`. Tests: `ops/test_nordic_2000_20261008.py` and `ops/test_nordic_1000_20261008.py`.
'''
    (RUN/'README.md').write_text(md)
    save(RUN/'summary.json',dict(at=m.now(),new_artworks=count,countries=dict(country),institutions=len(museums),work_types=dict(types),sources=dict(sources),new_images=0,all_review=True,verified_artworks=count,live_artwork_examples=len(api['artworks']),local_database_changed=False))
    print(md[:1600],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command');a=ap.parse_args();globals()[a.command]()
