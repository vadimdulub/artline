#!/usr/bin/env python3
"""Production museum coverage campaign; local catalogue access is read-only."""
import argparse, collections, csv, gzip, hashlib, importlib.util, json, re, time
from contextlib import contextmanager
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

ROOT=Path(__file__).resolve().parents[1]
OP='all-museums-minimum-100-20261006'
RUN=ROOT/'docs/research'/OP
def module(name, filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'ops'/filename)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
d=module('minimum_delivery','museum-minimum-100-delivery-20261006.py')
h=module('minimum_capture','research-havre-rouen-cyprus-20261006.py')
m=d.m
save,load,norm,acc=d.save,d.load,d.norm,d.acc
BASE={x['institution']['id']:x for x in load(RUN/'baseline.json.gz')['below_100']}


def configure(wave):
    d.OP=OP+'-'+wave;d.RUN=RUN/'waves'/wave
    d.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP/wave
    d.EXPECTED_MUSEUMS=len(load(d.RUN/'sample.json')['selected']) if (d.RUN/'sample.json').exists() else None


def prepare_wave(wave, records, held=None):
    configure(wave)
    mids=sorted({x['museum']['id']for x in records})
    selected=[dict(id=iid,slug=BASE[iid]['institution']['slug'],name=BASE[iid]['institution']['name'])for iid in mids]
    save(d.RUN/'sample.json',dict(at=d.now(),selected=selected,selection='All baseline under-100 museums with verified records in this source wave; not a random subset.',target=100))
    save(d.RUN/'source-verified.json.gz',dict(at=d.now(),records=records,held=held or []))
    print('Prepared',wave,len(records),'records in',len(mids),'museums',flush=True)


def prior():
    records=[]
    for path in sorted(d.OLD.glob('*-applied.json')):
        source=path.name.removesuffix('-applied.json');receipt=load(path)
        if not receipt.get('created'):continue
        p,digest=m.validate_plan(source);assert digest==receipt['plan_sha256']
        for row in p['records']:
            if row['museum']['id'] in BASE:
                records.append(dict(row,provider=source,origin='prior_verified_primary_plan',prior_plan_sha256=digest))
    with d.connect() as db:
        ids=[x['artwork_id']for x in records]
        existing={x['id']for x in db.execute('SELECT id::text FROM artworks WHERE id=ANY(%s::uuid[])',(ids,))}
        institutions={x['v']['id']:x['v']for x in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[])',(list(BASE),))}
    records=[dict(x,museum=institutions[x['museum']['id']])for x in records if x['artwork_id']not in existing]
    prepare_wave('prior-primary-001',records)


def joconde():
    targets={x['institution']['slug'].removeprefix('joconde-').upper():x for x in BASE.values()if x['institution']['slug'].startswith('joconde-')}
    with d.connect()as db:
        known={x['external_id']for x in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme ILIKE '%joconde%'")}
        known.update(x['source_url'].rstrip('/').rsplit('/',1)[-1]for x in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE '%/joconde/%'"))
        mids=[x['institution']['id']for x in targets.values()];existing=d.scoped_rows(db,mids)
        counts={x['id']:x['eligible']for x in db.execute("SELECT current_institution_id::text id,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible')eligible FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' GROUP BY 1",(mids,))}
    inventories=collections.defaultdict(set);titles=collections.defaultdict(set)
    for x in existing:inventories[x['institution_id']].update(acc(x['accession_number']));titles[x['institution_id']].update(norm(x[k])for k in ['title','alternate_title']if x[k])
    records=collections.defaultdict(list);source_inventory=collections.Counter();stats=collections.defaultdict(collections.Counter)
    with m.SNAPSHOT.open('rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()==m.SNAPSHOT_SHA
    csv.field_size_limit(8_000_000)
    with m.SNAPSHOT.open(encoding='utf-8-sig',newline='')as f:
        for row in csv.DictReader(f,delimiter='|'):
            code=row.get('Code_Museofile')
            if code not in targets:continue
            iid=targets[code]['institution']['id'];stats[iid]['source_rows']+=1
            for key in acc(row.get('Numero_inventaire')):source_inventory[(iid,key)]+=1
            if counts.get(iid,0)>=100:continue
            if row['Reference']in known:stats[iid]['already_catalogued_native_id']+=1;continue
            if len(records[iid])>=125-counts.get(iid,0):continue
            facts,parser,reason=d.parse_joconde(row)
            if reason:
                facts,reason=m.joconde_sculpture_facts(row);parser='joconde-sculpture-reviewed'
            if reason:stats[iid][reason]+=1;continue
            if 'year'in facts:facts.update(first=facts['year'],last=facts['year'],date_precision='exact')
            inst=targets[code]['institution']
            if norm(row['Nom_officiel_musee']+' '+row['Ville'])!=norm(inst['name']):stats[iid]['museum_label_requires_review']+=1;continue
            if acc(facts['accession'])&inventories[iid]or norm(facts['title'])in titles[iid]:stats[iid]['existing_inventory_or_title_requires_review']+=1;continue
            records[iid].append(dict(artwork_id=d.uid('joconde/'+row['Reference']),slug=OP+'-joconde-'+row['Reference'].lower(),
                source_record_id=row['Reference'],museum=inst,facts=facts,provider=parser,origin='pinned_joconde_discovery_snapshot',raw_source_record=row))
    selected=[]
    for iid,group in records.items():
        seen_acc=set();seen_title=set()
        for row in group:
            f=row['facts'];keys=acc(f['accession']);title=norm(f['title'])
            if any(source_inventory[(iid,k)]>1 for k in keys)or keys&seen_acc or title in seen_title:stats[iid]['shared_or_duplicate_source_identity']+=1;continue
            seen_acc.update(keys);seen_title.add(title);selected.append(row)
    configure('joconde-001');save(d.RUN/'selected-candidates.json.gz',selected)
    save(d.RUN/'source-discovery-summary.json',dict(at=d.now(),museums=len(targets),candidates=len(selected),per_museum=stats,
        limitation='Complete preserved Joconde discovery snapshot reviewed within target museum codes; selected eligible records will be rechecked against the current official API. Source gaps do not prove museums have no other eligible holdings.'))
    print('Fresh Joconde selection',len(selected),'candidate works across',len({x['museum']['id']for x in selected}),'museums',flush=True)
    d.capture()
    ready=load(d.RUN/'source-verified.json.gz');mids=sorted({x['museum']['id']for x in ready['records']})
    save(d.RUN/'sample.json',dict(at=d.now(),selected=[dict(id=iid,slug=BASE[iid]['institution']['slug'],name=BASE[iid]['institution']['name'])for iid in mids],selection='Every under-100 Joconde museum with supported new object candidates.',target=100))


def wikiart_links(wave='wikiart-001',expanded=False):
    """Recheck exact, already captured WikiArt objects against live production."""
    w=module('minimum_wikiart','reconcile-random-5000-wikiart-museums-20261006.py')
    loc=module('minimum_locations','apply-artwork-locations-20261004.py')
    old=ROOT/'docs/research/artwork-locations-20261004/wikiart-leads'
    leads=[load(p)for p in old.glob('*.json')]
    authorities={}
    if expanded:
        latest={x['artwork_id']:x for x in leads}
        for path in old.parent.joinpath('wikiart-leads-retry-20261005').glob('*.json'):
            x=load(path);latest[x['artwork_id']]=x
        leads=list(latest.values())
        authorities=load(ROOT/'docs/research/random-5000-museums-20261006/cached-institution-authorities.json.gz')
    with d.connect()as db:
        institutions=[x['v']for x in db.execute("SELECT to_jsonb(i) v FROM institutions i WHERE status<>'archived'")]
        artist_urls=collections.defaultdict(set)
        for x in db.execute("SELECT entity_id::text,canonical_url FROM external_identifiers WHERE entity_type='artist' AND canonical_url LIKE 'https://www.wikiart.org/%%'"):
            artist_urls[x['entity_id']].add(x['canonical_url'].rstrip('/'))
        aliases=collections.defaultdict(set)
        for x in db.execute('SELECT artist_id::text,alias FROM artist_aliases'):aliases[x['artist_id']].add(w.norm(x['alias']))
    byid={x['id']:x for x in institutions};names=collections.defaultdict(set)
    for x in institutions:
        names[w.key(x['name'])].add(x.get('canonical_institution_id')or x['id'])
    for label,iid in w.ALIASES.items():
        if iid in byid:names[w.key(label)].add(byid[iid].get('canonical_institution_id')or iid)
    authority_evidence={}
    if expanded:
        for inst in institutions:
            authority=authorities.get(inst.get('wikidata_id'))
            if not authority:continue
            entity=authority['entity'];iid=inst.get('canonical_institution_id')or inst['id']
            for label in [v['value']for v in entity.get('labels',{}).values()]+[v['value']for values in entity.get('aliases',{}).values()for v in values]:
                names[w.key(label)].add(iid);authority_evidence[(w.key(label),iid)]=authority
    resolutions={};held=[]
    for lead in leads:
        label=lead.get('fields',{}).get('Location')
        if not label or label in resolutions:continue
        clean=re.sub(r'\([^)]*\)','',label);prefix=clean.split(',')[0].strip();keys={w.key(clean),w.key(prefix)}
        if expanded and w.key(prefix)in {'national gallery','national art gallery','national portrait gallery','national museum','museum of fine arts','museum of modern art','musee des beaux arts'}:keys={w.key(clean),w.key(label)}
        matches=set().union(*(names.get(k,set())for k in keys))
        if len(matches)==1 and next(iter(matches)) in BASE:
            # Exclude known changing/historical institutions and custody qualifiers.
            if re.search(r'private|unknown|destroyed|loan|formerly|horlivka|sevastopol|roerich museum, moscow|staechelin',label,re.I):continue
            resolutions[label]=byid[next(iter(matches))]
    relevant=[x for x in leads if x.get('fields',{}).get('Location')in resolutions]
    baseline={}
    with d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        for group in d.chunks([x['artwork_id']for x in relevant],500):baseline.update(loc.snapshots(db,group))
    claims=[]
    for lead in relevant:
        aid=lead['artwork_id'];snap=baseline.get(aid)
        if not snap:continue
        a=snap['artwork']
        if a['status']=='archived' or a['current_institution_id'] or any(x['claim_type']=='holding'and x['review_state']=='accepted'and not x['superseded_by']for x in snap['assertions']):continue
        reason=None;rc=lead['source_receipt'];raw=gzip.decompress((ROOT/rc['body_path']).read_bytes())
        assert d.sha(raw)==rc['sha256'] and rc['status']==200
        soup=BeautifulSoup(raw,'html.parser');info=soup.select_one('.wiki-layout-artwork-info');canonical=soup.find('link',rel='canonical')
        title=info.select_one('h1').get_text(' ',strip=True)if info and info.select_one('h1')else None
        creator=info.select_one('h2').get_text(' ',strip=True)if info and info.select_one('h2')else None
        native=set(re.findall(r"trackPageView\('painting',\s*'([a-f0-9]{24})'",raw.decode('utf8','replace')))
        exact={x['external_id']for x in snap['identifiers']if x['scheme']=='wikiart-artwork'and w.urlkey(x.get('canonical_url'))==w.urlkey(lead['source_url'])}
        creator_names={w.norm(x['name'])for x in snap['creator_keys']}|{w.norm(a.get('unlinked_creator_label'))}
        for link in snap['creators']:creator_names.update(aliases[link['artist_id']])
        creator_ok=w.creator_match(creator,creator_names)or any(lead['source_url'].rsplit('/',1)[0]in artist_urls[x['artist_id']]for x in snap['creators'])
        if expanded and not snap['creators']and a.get('unlinked_creator_label')=='Creator not recorded'and creator in {'Fayum portrait','Orthodox Icons'}:creator_ok=True
        if exact!={lead['external_id']} or native!=exact or not canonical or w.urlkey(canonical['href'])!=w.urlkey(lead['source_url']):reason='exact_native_identity_requires_review'
        elif w.norm(title)not in {w.norm(a['title']),w.norm(a.get('alternate_title'))}:reason='source_title_requires_review'
        elif not creator_ok:reason='creator_requires_review'
        elif a['work_type']=='print' or re.search(r'etching|engraving|lithograph|woodcut|woodblock|screenprint|linocut|aquatint',lead['fields'].get('Media',''),re.I):reason='print_impression_requires_inventory'
        loc_field=None
        if info:
            for li in info.select('article > ul > li'):
                label=li.find('s')
                if label and label.get_text(' ',strip=True).rstrip(':')=='Location':label.extract();loc_field=li.get_text(' ',strip=True)
        if loc_field!=lead['fields']['Location']:reason='source_location_extraction_conflict'
        if reason:held.append(dict(artwork_id=aid,reason=reason,source_url=lead['source_url']));continue
        inst=resolutions[loc_field]
        claims.append(dict(artwork_id=aid,title=a['title'],scheme='wikiart-artwork',external_id=lead['external_id'],institution=inst,
            source_url=lead['source_url'],checked_at=rc['retrieved_at'],location_text=loc_field,source_class='user_approved_wikiart_catalogue',
            source_receipt=rc,claim_type='holding',review_state='accepted',
            identity_basis='Exact existing WikiArt object ID, canonical URL, title, creator and literal Location reconciled to one existing museum authority.',
            object_evidence=dict(lead=lead,native_id_verified=True,editorial_confidence=0.95,confidence_basis='Exact object crosswalk and unambiguous museum name. Editorial assessment, not calibrated probability.'),
            limitation='Dated WikiArt collection statement only; no current display, physical whereabouts or independent legal ownership claim. Existing metadata, images and publication state remain unchanged.'))
    root=RUN/'links'/wave;save(root/'claims.json.gz',dict(at=d.now(),claims=claims,held=held))
    if expanded:
        save(root/'museum-authority-evidence.json.gz',dict(authorities=authorities,resolutions=resolutions,method='Exact source museum name or multilingual authority alias; ambiguous matches and generic name-only identities held.'))
    save(root/'baseline.json.gz',baseline)
    print('WikiArt under-100 museum links:',len(claims),'across',len({x['institution']['id']for x in claims}),'museums; held',dict(collections.Counter(x['reason']for x in held)),flush=True)


def link_delivery(phase,wave='wikiart-001'):
    loc=module('minimum_link_delivery','apply-artwork-locations-20261004.py');root=RUN/'links'/wave;loc.r.RUN=root
    loc.r.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP/wave;loc.ACTOR=OP+'-'+wave
    @contextmanager
    def connection(target='production',readonly=True):
        assert target=='production','Production only'
        with d.connect(readonly=readonly)as db:
            if phase=='link_apply':
                # Explicit per-batch transactions still control atomicity;
                # pipelining only removes repeated network round trips.
                with db.pipeline():yield db
            else:yield db
    loc.r.connect=connection
    if phase=='link_plan':
        source=load(root/'claims.json.gz');baseline=load(root/'baseline.json.gz')
        provider=source.get('provider','wikiart')
        input_path=root/'missing-locations.json.gz'
        if input_path.exists() and any('artists'not in x for x in load(input_path)):
            input_path.rename(root/'missing-locations-original-snapshot-schema.json.gz')
        loc.r.save_gz(input_path,[dict(x,artists=x['creator_keys'])for x in baseline.values()])
        loc.r.save_gz(root/'primary-plans'/(provider+'.json.gz'),source)
        loc.plan('verified', [provider], targets=['production'])
    elif phase=='link_apply':loc.apply('verified','production')
    else:loc.verify('verified',targets=['production'])


def audit():
    expected={};waves=[]
    for path in sorted((RUN/'waves').glob('*/applied.json')):
        receipt=load(path);planpath=path.parent/'plan.json.gz';assert d.sha(planpath.read_bytes())==receipt['plan_sha256']
        plan=load(planpath)
        for row in plan['records']:
            assert row['artwork_id']not in expected;expected[row['artwork_id']]=row
        waves.append(dict(wave=path.parent.name,new_artworks=receipt['new_artworks'],linked=receipt['linked_artworks'],museums_changed=len({x['museum']['id']for x in plan['records']})))
    links=[]
    for linkroot in (RUN/'links').iterdir():
        linkpin=linkroot/'delivery/verified/plan.json.gz'
        if not linkpin.exists():continue
        for path in (linkroot/'delivery/verified/production').glob('*.json'):
            links.extend(load(path)['artwork_ids'])
    with d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        rows=[]
        for group in d.chunks(list(expected),500):
            rows.extend(db.execute("SELECT to_jsonb(a) artwork,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,artline_has_selection_evidence(a.id) evidence FROM artworks a WHERE id=ANY(%s::uuid[])",(group,)).fetchall())
        for x in rows:
            a=x['artwork'];p=expected[a['id']];f=p['facts']
            assert a['current_institution_id']==p['museum']['id']and x['evidence']
            if p['action']=='create':
                assert a['status']=='review'and a['published_at']is None and a['primary_media_id']is None and x['scope']=='eligible'
                for key,skey in [('title','title'),('unlinked_creator_label','creator_label'),('date_display','date_display'),('creation_year_start','first'),('creation_year_end','last'),('date_precision','date_precision'),('accession_number','accession'),('medium_text','medium'),('dimensions_text','dimensions')]:assert a[key]==f[skey],(a['id'],key)
        assert len(rows)==len(expected)
        counts=db.execute("WITH counts AS MATERIALIZED (SELECT current_institution_id id,count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible')eligible,count(primary_media_id) images FROM artworks WHERE status<>'archived' AND current_institution_id=ANY(%s::uuid[]) GROUP BY 1) SELECT i.id::text,i.slug,i.name,coalesce(c.linked,0) linked,coalesce(c.eligible,0)eligible,coalesce(c.images,0)images FROM institutions i LEFT JOIN counts c ON c.id=i.id WHERE i.id=ANY(%s::uuid[]) ORDER BY i.name",(list(BASE),list(BASE))).fetchall()
        source_ids=[str(__import__('uuid').uuid5(__import__('uuid').NAMESPACE_URL,OP+'-'+x['wave']+'/source'))for x in waves]
        evidence=db.execute("SELECT count(*) citations FROM citations WHERE source_id=ANY(%s::uuid[])",(source_ids,)).fetchone()
        assertions=db.execute("SELECT claim_type,review_state,count(*) n FROM artwork_location_assertions WHERE source_id=ANY(%s::uuid[]) GROUP BY 1,2",(source_ids,)).fetchall()
    assert evidence['citations']==len(expected)
    assert assertions==[{'claim_type':'holding','review_state':'accepted','n':len(expected)}]
    for x in counts:
        b=BASE[x['id']];x.update(before_linked=b['linked'],before_eligible=b['eligible'],gap=max(0,100-x['linked']),eligible_gap=max(0,100-x['eligible']))
        x['state']='at_least_100_linked'if not x['gap']else 'expanded_still_below_100'if x['linked']>x['before_linked']else 'source_research_required'
    created=sum(x['action']=='create'for x in expected.values())
    linked=len(set(links)|{x['artwork_id']for x in expected.values()if x['action']=='link'})
    result=dict(at=d.now(),target='production',initial_museums_below_100=len(BASE),new_artworks=created,existing_artworks_linked=linked,
        museums_now_at_least_100=sum(x['linked']>=100 for x in counts),museums_still_below_100=sum(x['linked']<100 for x in counts),
        remaining_gap=sum(x['gap']for x in counts),waves=waves,museums=counts,local_database_writes=0,new_publications=0,new_images=0,new_display_claims=0,
        completion='incomplete; continue source research and verified production batches')
    save(RUN/'audits'/(d.now().replace(':','')+'.json.gz'),result)
    (RUN/'progress.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    with (RUN/'all-museums-progress.csv').open('w',newline='')as f:
        writer=csv.DictWriter(f,fieldnames=list(counts[0]));writer.writeheader();writer.writerows(counts)
    aargau=next(x for x in counts if x['id']=='b5c2baba-848a-5b03-a368-f858b02f9738')
    md=f"# All museums: minimum 100 artwork campaign\n\n**In progress.** Latest production verification: {result['at']}. The initial audit found **{len(BASE):,} canonical museum records below 100 artworks**, with a shortfall of 113,077. This is catalogue coverage, not a claim that every museum has 100 eligible physical objects. Unreconciled museum identities remain research gaps.\n\n"
    md+=f"Verified production additions: **{created:,} new artworks** and **{linked:,} existing-artwork museum links**. **{result['museums_now_at_least_100']}** initial targets now have at least 100 linked records; **{result['museums_still_below_100']:,}** remain below 100, with **{result['remaining_gap']:,}** further links/additions needed. Source research remains incomplete.\n\n"
    md+=f"Aargauer Kunsthaus now has **{aargau['linked']} linked artworks**, **{aargau['eligible']}** with eligible dates, and **{aargau['images']}** with existing images. Its initial count was one. Official native object pages and catalogue index agree on selected titles, creators, dates and museum credits; incoming loans and unresolved entries were held. The Anker *Kinderbegräbnis* was reconciled to the existing *Child funeral* record using WikiArt's original-title field, creator/date and museum, rather than duplicated.\n\n"
    md+="[Complete initial museum gap list](all-museums-below-100.csv) · [Live campaign register](all-museums-progress.csv) · [Latest database audit](progress.json). Each source wave retains selected source bodies, hashes, original retrieval dates, duplicate holds and pinned plans. Transaction preimages are under `~/Library/Application Support/Artline/backups/all-museums-minimum-100-20261006/`.\n\n"
    md+="New artwork records remain in review. Existing dates, images, creator links and publication states are preserved. Holdings do not assert current display. This operation has not imported new images or written to the local catalogue. The previous 1,813-work, 50-museum batch is separate and remains in production.\n"
    if(RUN/'jobs/continuation-20261007/status.json').exists():
        md+="\nContinuation: [worker status](jobs/continuation-20261007/status.json), [execution log](jobs/continuation-20261007/worker.log). The worker processes bounded museum-specific Wikidata and official Italian catalogue batches, checks pinned script hashes and object versions, commits reviewed plans and repeats this production audit after every wave. A source-pass finish with remaining gaps is not campaign completion. Source denials, changed scripts, conflicting versions and failed verification stop the affected work and preserve evidence.\n"
    (RUN/'README.md').write_text(md)
    print(json.dumps({k:v for k,v in result.items()if k not in ['museums','waves']},ensure_ascii=False),flush=True)
    print('Aargauer:',aargau,flush=True)


def aargauer_date(value):
    match=re.fullmatch(r'(?:(um|Um|ca\.)\s*)?(\d{4})(?:\s*[-–]\s*(\d{4}))?',value)
    if not match:return None
    first,last=int(match[2]),int(match[3]or match[2])
    if not 100<=first<=last<=1970 or (match[1] and last>=1970):return None
    return first,last,('circa' if first==last else 'circa_range')if match[1]else('exact'if first==last else'range')


def caption(element):
    title=element.find('i');assert title
    strings=list(element.children);pos=strings.index(title)
    creator=' '.join(' '.join(str(x)for x in strings[:pos]).split()).rstrip(',').strip()
    date=' '.join(' '.join(str(x)for x in strings[pos+1:]if not getattr(x,'name',None)).split()).lstrip(',').strip()
    return dict(title=title.get_text(' ',strip=True),creator_label=creator,date_display=date)


def aargauer_native(raw,index):
    soup=BeautifulSoup(raw,'html.parser');legend=soup.select_one('.sammlung_legend')
    if not legend:return None,'missing_native_legend'
    fields=caption(legend);dates=aargauer_date(fields['date_display'])
    if not dates:return None,'native_creation_date_requires_review'
    if fields!=index['caption']:return None,'native_index_title_creator_date_conflict'
    canonical=soup.find('link',rel='canonical')
    if not canonical or canonical['href']!=index['url']:return None,'canonical_object_conflict'
    post=next((x.removeprefix('postid-')for x in soup.body.get('class',[])if x.startswith('postid-')),None)
    if not post or not post.isdigit():return None,'missing_native_object_id'
    details=legend.select_one('.small_type')
    if not details:return None,'missing_native_details'
    direct=[x.get_text(' ',strip=True)for x in details.find_all('div',recursive=False)]
    credits=[x for x in direct if x.startswith('Aargauer Kunsthaus')]
    if len(credits)!=1:return None,'collection_credit_missing_or_ambiguous'
    credit=credits[0]
    if re.search(r'leihgabe|depot|deposit|privatsammlung|restitution',credit,re.I):return None,'qualified_collection_custody_requires_review'
    material=' '.join(str(x).strip()for x in details.children if type(x) is NavigableString).strip()
    material=' '.join(material.split())
    split=re.fullmatch(r'(.+?),\s*((?:\d+[.,]?\d*\s*[x×]\s*)+\d+[.,]?\d*\s*cm)',material)
    if not split:return None,'material_dimension_field_requires_review'
    medium,dimensions=split.groups()
    if not re.search(r'öl|acryl|tempera|gouache|oil',medium,re.I):return None,'painting_medium_requires_review'
    if re.search(r'collage|montage|relief|assemblage|fotograf|photograph',medium,re.I):return None,'mixed_media_requires_review'
    categories=[x.get_text(' ',strip=True)for x in soup.select('.current_categories a')]
    if 'Malerei'not in categories:return None,'native_type_conflict'
    provenance=legend.select_one('.provenienz_column_right')
    native=dict(caption=fields,post_id=post,credit=credit,material=material,medium=medium,dimensions=dimensions,
        provenance=provenance.get_text(' ',strip=True)if provenance else None,
        rights_credits=[x for x in direct if 'credit' in x.lower() or 'copyright'in x.lower()],categories=categories)
    facts=dict(**fields,first=dates[0],last=dates[1],date_precision=dates[2],work_type='painting',medium=medium,dimensions=dimensions,
        accession=index['inventory'],source_url=index['url'],holding_basis='Official Aargauer Kunsthaus native object page and catalogue index agree on object identity, title, creator, date and Malerei classification. Explicit Aargauer Kunsthaus collection credit retained; no current-display or independent legal-ownership claim.')
    return dict(facts=facts,native=native),None


def aargauer():
    h.RUN=RUN/'aargauer'
    url='https://aargauerkunsthaus.ch/de/ausstellungen/katalog-online/'
    raw,rc=h.capture(url);assert rc['status']==200
    soup=BeautifulSoup(raw,'html.parser');candidates=[];held=[]
    for card in soup.select('.sammlung_list .filter_listing'):
        if 'gattung_malerei'not in card.get('class',[]):continue
        a=card.select_one('a[href]');legend=card.select_one('.column_left')
        if not a or not legend:continue
        fields=caption(legend)
        if not aargauer_date(fields['date_display']):continue
        if re.search(r'ohne titel|recto|verso|mehrteil|dipty|tripty|teil[ie]g|fragment',fields['title'],re.I):continue
        keywords=card.select_one('.search_keywords').get_text(' ',strip=True)
        inv=re.search(r'\s([A-Z]?\d+(?:[./]\d+)?)\s+Aargauer Kunsthaus\s*/',keywords)
        if not inv:continue
        candidates.append(dict(url=a['href'],caption=fields,inventory=inv[1],index_keywords=keywords,index_receipt=rc))
    assert len({x['url']for x in candidates})==len(candidates)
    # Select a bounded reserve to cover production identity holds; stop at 100 in delivery.
    candidates=sorted(candidates,key=lambda x:(x['caption']['creator_label'],x['url']))[:180]
    selection_path=h.RUN/'selected-index.json'
    if selection_path.exists():
        previous=load(selection_path);assert previous['candidates']==candidates and previous['source_receipt']==rc
    else:save(selection_path,dict(at=d.now(),candidates=candidates,source_receipt=rc))
    museum=BASE['b5c2baba-848a-5b03-a368-f858b02f9738']['institution'];ready=[]
    for n,index in enumerate(candidates,1):
        dest=h.RUN/'objects'/(d.sha(index['url'].encode())+'.json')
        if dest.exists():result=load(dest)
        else:
            body,receipt=h.capture(index['url'])
            if receipt['status']!=200:result=dict(reason='native_http_'+str(receipt['status']),index=index,source_receipt=receipt)
            else:
                parsed,reason=aargauer_native(body,index)
                result=dict(index=index,source_receipt=receipt,parsed=parsed,reason=reason)
            save(dest,result)
        if result['source_receipt']['status']==200:
            saved_body=gzip.decompress((ROOT/result['source_receipt']['body_path']).read_bytes())
            parsed,reason=aargauer_native(saved_body,index)
            result=dict(result,parsed=parsed,reason=reason)
        if result['reason']:held.append(dict(source_url=index['url'],reason=result['reason']))
        else:
            parsed=result['parsed'];oid=parsed['native']['post_id']
            ready.append(dict(artwork_id=d.uid('aargauer/'+oid),slug=OP+'-aargauer-'+oid,source_record_id=oid,
                provider='aargauer-native',origin='verified_native_object',museum=museum,facts=parsed['facts'],source_receipt=result['source_receipt'],
                body_path=result['source_receipt']['body_path'],raw_source_record=dict(index=index,native=parsed['native'])))
        if n%10==0:print('Aargauer native objects',n,'/',len(candidates),'ready',len(ready),'held',len(held),flush=True)
    prepare_wave('aargauer-001',ready,held)


ORIGINAL_BODY=d.check_body
ORIGINAL_SCHEME=d.scheme
def check_body(row,cache):
    if row['provider']!='aargauer-native':return ORIGINAL_BODY(row,cache)
    rc=row['source_receipt'];raw=gzip.decompress((ROOT/row['body_path']).read_bytes())
    assert d.sha(raw)==rc['sha256'] and rc['status']==200
    parsed,reason=aargauer_native(raw,row['raw_source_record']['index'])
    assert not reason and parsed['facts']==row['facts'] and parsed['native']==row['raw_source_record']['native']
    assert parsed['native']['post_id']==row['source_record_id']
    ir=row['raw_source_record']['index']['index_receipt']
    indexraw=gzip.decompress((ROOT/ir['body_path']).read_bytes());assert d.sha(indexraw)==ir['sha256']


def delivery(phase,wave):
    configure(wave);d.check_body=check_body
    d.scheme=lambda row:'aargauer-object'if row['provider']=='aargauer-native'else ORIGINAL_SCHEME(row)
    if phase=='plan':d.plan()
    else:d.apply()


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['prior','aargauer','joconde','plan','apply','wikiart_links','wikiart_expanded','link_plan','link_apply','link_verify','audit']);ap.add_argument('--wave')
    args=ap.parse_args()
    if args.phase in ['plan','apply']:delivery(args.phase,args.wave)
    elif args.phase.startswith('link_'):link_delivery(args.phase,args.wave or 'wikiart-001')
    elif args.phase=='wikiart_expanded':wikiart_links(args.wave or 'wikiart-002',expanded=True)
    else:globals()[args.phase]()
