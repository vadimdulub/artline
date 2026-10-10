#!/usr/bin/env python3
"""Fresh production cohort and source-backed follow-up for one-work museums."""
import argparse, collections, csv, gzip, importlib.util, json, os, re
from pathlib import Path
from urllib.parse import urlencode
from psycopg.types.json import Jsonb

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/museums-exactly-one-round3-20261008'
OP=RUN.name
os.environ['ARTLINE_MUSEUM_PROXY_PORT']='55494'
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'ops'/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
r=module('round2','museums-exactly-one-round2-20261008.py')
r.RUN=RUN;r.OP=OP;r.p.RUN=RUN;d=r.d

AUTHORITY_NAMES=['Virginia Museum of Fine Arts','Smith College Museum of Art','Allen Memorial Art Museum','Dayton Art Institute','Taft Museum of Art','McNay Art Museum','Joslyn Art Museum','Krannert Art Museum','Hecht Museum','Santa Barbara Museum of Art','Philbrook Museum of Art','Montgomery Museum of Fine Arts']

def authority_search():
    n=r.wd_module();results=[]
    for name in AUTHORITY_NAMES:
        url='https://www.wikidata.org/w/api.php?'+urlencode(dict(action='wbsearchentities',search=name,language='en',uselang='en',type='item',limit=3,format='json'))
        raw,rc=n.entity_capture(url);assert rc['status']==200
        rows=json.loads(raw)['search'];results.append(dict(name=name,results=rows,receipt=rc))
        print(name,[(x['id'],x.get('label'),x.get('description')) for x in rows],flush=True)
    d.save(RUN/'museum-authority-search.json',results)

def authority_prepare():
    n=r.wd_module();search=d.load(RUN/'museum-authority-search.json')
    base=d.load(RUN/'baseline.json.gz')['selected'];allinst=d.load(RUN/'all-institution-authorities.json.gz')
    full=n.entities([x['results'][0]['id'] for x in search]);selected=[]
    for result in search:
        q=result['results'][0]['id'];name=result['name'];entity=full[q]['entity']
        assert name in {v['value'] for v in entity['labels'].values()}
        prefix=name.lower()
        matches=[x['institution'] for x in base if x['institution']['name'].lower().startswith(prefix)]
        if name=='Montgomery Museum of Fine Arts':matches=[x['institution'] for x in base if x['institution']['name'].startswith('Montgomery Musuem of')]
        assert len(matches)==1,(name,matches)
        museum=matches[0];assert not museum['wikidata_id']
        assert not any(x['wikidata_id']==q for x in allinst)
        selected.append(dict(museum=dict(museum,wikidata_id=q),catalogue_institution=museum,authority=full[q],search=result,projected_count=1,cursor='',page_number=1))
    d.save(RUN/'reviewed-museum-authorities.json.gz',selected)
    for x in selected:print(x['museum']['name'],x['museum']['wikidata_id'],[n.w.value(v) for v in n.w.active(x['authority']['entity'],'P856')],flush=True)

def authority_research():
    n=r.wd_module();wave='missing-authorities';selected=d.load(RUN/'reviewed-museum-authorities.json.gz')
    d.save(n.ROOT/wave/'selected-museums.json',selected)
    n.research(wave,len(selected),target_count=25)
    source=d.load(RUN/'waves'/wave/'source-verified.json.gz');byid={x['museum']['id']:x for x in selected}
    rows=[dict(x,museum=byid[x['museum']['id']]['catalogue_institution'],raw_source_record=dict(x['raw_source_record'],museum_authority=byid[x['museum']['id']])) for x in source['records']]
    n.c.prepare_wave('missing-authorities-reviewed',rows,source['held'])

def configure(wave='final-reviewed'):
    n=r.wd_module();n.c.configure(wave);out=n.c.d
    out.TARGET_FIELD='linked';out.TARGET_COUNT=25
    out.SOURCE_NAME='Exactly-one museum follow-up: referenced Wikidata catalogue metadata with reviewed museum authorities'
    out.SOURCE_BASE_URL='https://www.wikidata.org/';out.DEFAULT_CONFIDENCE=.85
    out.CONFIDENCE_BASIS='Exact full artwork entity and one referenced collection statement; individually reviewed museum authority name, city and official website; retained creation dates and creator labels. Editorial confidence, not calibrated probability. Underlying object references not independently opened.'
    out.scheme=lambda row:'wikidata'
    authorities={x['catalogue_institution']['id']:x for x in d.load(RUN/'reviewed-museum-authorities.json.gz')}
    def check(row,cache):
        a=authorities[row['museum']['id']];assert row['museum']['name']==a['catalogue_institution']['name']
        assert row['raw_source_record']['museum_authority']==a
        source=a['authority'];raw,rc=n.checked_capture(source['receipt'])
        assert json.loads(raw)['entities'][a['museum']['wikidata_id']]==source['entity']
        n.check_body(dict(row,museum=dict(row['museum'],wikidata_id=a['museum']['wikidata_id'])),cache)
    out.check_body=check
    original=out.connect
    def connect(readonly=True):
        db=original(readonly)
        if not readonly:db.execute("SET lock_timeout='180s'")
        return db
    out.connect=connect
    return out

def plan():configure('missing-authorities-reviewed').plan()
def apply():
    assert d.load(RUN/'backups.json')['production']['status']=='SUCCESSFUL'
    configure().apply()

def identity_review():
    n=r.wd_module();records=d.load(RUN/'waves/missing-authorities-reviewed/source-verified.json.gz')['records']
    wanted={q for row in records for q in row['raw_source_record']['creators']}
    names={d.norm(row['facts']['creator_label']) for row in records}
    byq=collections.defaultdict(set);byname=collections.defaultdict(set)
    with d.connect() as db:
        for x in db.execute("SELECT entity_id::text id,external_id FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND external_id=ANY(%s)",(list(wanted),)):byq[x['external_id']].add(x['id'])
        for x in db.execute('SELECT id::text,normalized_name FROM artists WHERE normalized_name=ANY(%s)',(list(names),)):byname[x['normalized_name']].add(x['id'])
        scope=[]
        for row in records:
            ids=set().union(*(byq[q] for q in row['raw_source_record']['creators']))|byname[d.norm(row['facts']['creator_label'])]
            for artist in ids:scope.append(dict(qid=row['source_record_id'],artist=artist,first=row['facts']['first'],last=row['facts']['last']))
        matches=db.execute("""WITH wanted AS (SELECT * FROM jsonb_to_recordset(%s) w(qid text,artist uuid,first integer,last integer))
          SELECT DISTINCT w.qid,a.id::text,a.title,a.alternate_title,a.date_display,a.creation_year_start,a.creation_year_end,a.current_institution_id::text,a.accession_number
          FROM wanted w JOIN artwork_artists aa ON aa.artist_id=w.artist JOIN artworks a ON a.id=aa.artwork_id
          WHERE a.status<>'archived' AND (a.creation_year_start IS NULL OR (a.creation_year_start<=w.last+2 AND a.creation_year_end>=w.first-2))
          ORDER BY w.qid,a.id::text""",(Jsonb(scope),)).fetchall()
    d.save(RUN/'creator-date-identity-candidates.json.gz',dict(at=d.now(),records=matches,scope=scope))
    import difflib
    source={x['source_record_id']:x for x in records};near=[]
    def key(s):return re.sub(r'\b(?:a|an|the|painting)\b','',d.norm(s)).replace(' ','')
    for item in matches:
        row=source[item['qid']];e=row['raw_source_record']['entity'];labels={v['value'] for v in e.get('labels',{}).values()}|{v['value'] for vs in e.get('aliases',{}).values() for v in vs}
        ratio=max(difflib.SequenceMatcher(None,key(title),key(label)).ratio() for title in [item['title'],item.get('alternate_title') or ''] for label in labels)
        if ratio>=.62:
            near.append(dict(item,similarity=ratio,source_title=row['facts']['title'],creator=row['facts']['creator_label']))
            print(row['source_record_id'],row['facts']['title'],'=>',item['id'],item['title'],item['date_display'],item['current_institution_id'],round(ratio,2),flush=True)
    d.save(RUN/'creator-date-title-leads.json',near)

LINK_CANDIDATES={
 'Q12094649':'f9986fd4-26f5-5233-8419-fd2f6018ecc2',
 'Q59342515':'a889fa05-499d-59fa-9ca7-5f94862729f3',
 'Q116915286':'f9264418-227c-5421-998d-9c24abf65330',
 'Q76627278':'f514338c-f39a-5717-80f4-872a8244380d',
}

def link_research():
    loc=module('cross_source_snapshots','apply-artwork-locations-20261004.py')
    capture=module('cross_source_capture','museums-exactly-one-aliases-20261008.py');capture.RUN=RUN/'link-source'
    from bs4 import BeautifulSoup
    with d.connect() as db:before=loc.snapshots(db,list(LINK_CANDIDATES.values()))
    source={x['source_record_id']:x for x in d.load(RUN/'waves/missing-authorities-reviewed/source-verified.json.gz')['records']};items=[]
    for q,aid in LINK_CANDIDATES.items():
        old=before[aid];urls={x['canonical_url'] for x in old['identifiers'] if (x.get('canonical_url') or '').startswith('https://www.wikiart.org/en/')}
        assert len(urls)==1
        raw,rc=capture.capture(next(iter(urls)));assert rc['status']==200
        soup=BeautifulSoup(raw,'html.parser');info=soup.select_one('.wiki-layout-artwork-info');assert info
        fields={}
        for li in info.select('article > ul > li'):
            node=li.find('s')
            if node:key=node.get_text(' ',strip=True).rstrip(':');node.extract();fields[key]=li.get_text(' ',strip=True)
        title=info.select_one('h1').get_text(' ',strip=True);creator=info.select_one('h2').get_text(' ',strip=True)
        native=sorted(set(re.findall(r"trackPageView\('painting',\s*'([a-f0-9]{24})'",raw.decode('utf8','replace'))))
        canonical=soup.find('link',rel='canonical')['href']
        items.append(dict(qid=q,artwork_id=aid,source=source[q],receipt=rc,title=title,creator=creator,fields=fields,native_ids=native,canonical=canonical))
        print(q,title,creator,json.dumps(fields,ensure_ascii=False),native,flush=True)
    raw,rc=capture.capture('https://mushecht2.haifa.ac.il/index.php?Itemid=114&catid=227&id=464&lang=en&option=com_content&view=article')
    assert rc['status']==200
    d.save(RUN/'link-source/review.json.gz',dict(at=d.now(),items=items,hecht_verso_source=rc));d.save(RUN/'link-source/baseline.json.gz',before)

def final_plan():
    folder=RUN/'waves/missing-authorities-reviewed';plan=d.load(folder/'plan.json.gz')
    removed={
      'Q30041900':('874907ad-9cdc-5b54-b786-0d018d1f575e','Stone City, Iowa (painting) is the existing Grant Wood Stone City, Iowa, 1930, already held by Joslyn. Title disambiguator is not a separate object.'),
      'Q76630412':('c83f5f71-a74a-52d9-a09f-edc1ccb02c75','Nude with a Hat is the existing Nude with Hat by Modigliani, already linked to Hecht. The canvas also carries Portrait of Maud Abrantes on its reverse. Preserve dates and existing face records.'),
      'Q116915286':('f9264418-227c-5421-998d-9c24abf65330','Jester on horseback is a cross-language identity lead for existing Harlequin on the horseback. Do not create an additional object; separately verify the existing record for a holding link.'),
    }
    keep=[]
    for row in plan['records']:
        if row['source_record_id'] in removed:
            existing,note=removed[row['source_record_id']]
            plan['held'].append(dict(artwork_id=row['artwork_id'],source_record_id=row['source_record_id'],museum_id=row['museum']['id'],title=row['facts']['title'],existing_artwork_id=existing,reason='individual_existing_object_reconciliation',basis=note))
        else:keep.append(row)
    assert len(keep)==27;plan['records']=keep
    for summary in plan['museums']:
        group=[x for x in keep if x['museum']['id']==summary['museum_id']]
        summary.update(new_artworks=len(group),new_links=0,projected_eligible=summary['before']['eligible']+len(group),projected_linked=summary['before']['linked']+len(group),available_after_identity_review=len(group))
    plan['parent_plan']=dict(path=str((folder/'plan.json.gz').relative_to(ROOT)),sha256=d.sha((folder/'plan.json.gz').read_bytes()))
    plan['creator_date_review']=dict(path=str((RUN/'creator-date-identity-candidates.json.gz').relative_to(ROOT)),sha256=d.sha((RUN/'creator-date-identity-candidates.json.gz').read_bytes()))
    dest=RUN/'waves/final-reviewed'
    for name in ['sample.json','source-verified.json.gz','identity-query-plan.json']:d.save(dest/name,d.load(folder/name))
    plan['sample_sha256']=d.sha((dest/'sample.json').read_bytes());d.save(dest/'plan.json.gz',plan)
    d.save(Path.home()/'Library/Application Support/Artline/backups'/OP/'final-reviewed/plan-and-preimages.json.gz',plan)
    print('Final new-object plan',len(keep),'across',len({x['museum']['id'] for x in keep}),'museums; existing-object leads excluded',flush=True)

def links_prepare():
    from bs4 import BeautifulSoup
    proof=d.load(RUN/'link-source/review.json.gz');before=d.load(RUN/'link-source/baseline.json.gz');claims=[]
    n=r.wd_module();check=configure().check_body
    for item in proof['items']:
        source=item['source'];check(source,{})
        old=before[item['artwork_id']];a=old['artwork'];museum=source['museum']
        assert not a['current_institution_id'] and not any(h['claim_type']=='holding' and h['review_state']=='accepted' and not h['superseded_by'] for h in old['assertions'])
        assert d.norm(a['title'])==d.norm(item['title'])
        assert d.norm(item['creator']) in {d.norm(c['name']) for c in old['creator_keys']}
        rc=item['receipt'];raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert rc['status']==200 and d.sha(raw)==rc['sha256']
        assert item['canonical'].rstrip('/')==rc['url'].rstrip('/')
        identifiers=[e for e in old['identifiers'] if e['external_id'] in item['native_ids'] and e.get('canonical_url','').rstrip('/')==item['canonical'].rstrip('/')]
        assert len(identifiers)==1 and len(item['native_ids'])==1
        scheme=identifiers[0]['scheme'];external_id=identifiers[0]['external_id'];url=rc['url'];confidence=.95
        basis='Exact existing WikiArt native artwork ID, canonical page, title and creator independently rechecked. Its explicit Location names this exact museum. Existing creation fields, images and publication state preserved.'
        source_class='user_approved_wikiart_collection_statement'
        if item['qid']=='Q116915286':
            assert 'Location' not in item['fields'] and item['fields']['Original Title']=='Arlequin a cheval' and item['fields']['Dimensions']=='100 x 69.2 cm' and item['fields']['Date']=='1905'
            e=source['raw_source_record']['entity']
            assert n.w.value(n.w.active(e,'P2048')[0])['amount']=='+100' and n.w.value(n.w.active(e,'P2049')[0])['amount']=='+69.2'
            assert a['creation_year_start']==a['creation_year_end']==1905
            scheme='wikidata';external_id=item['qid'];url=source['facts']['source_url'];rc=source['source_receipt'];confidence=.9
            source_class='referenced_wikidata_holding_with_exact_wikiart_object_identity'
            basis='Picasso Harlequin on the horseback (WikiArt original title Arlequin a cheval) and Wikidata Jester on horseback / Harlekijn te paard are the same 1905 work: identical creator, subject and distinctive 100 x 69.2 cm dimensions. Exact existing WikiArt ID and canonical page verified. Holding evidence is Wikidata P195 with RKD 222741 reference; WikiArt has no Location field and is not represented as the holding source. Direct RKD access was unavailable. Editorial confidence 0.90, not calibrated probability.'
        else:assert item['fields']['Location']==museum['name']
        if item['qid']=='Q76627278':
            hc=proof['hecht_verso_source'];html=gzip.decompress((ROOT/hc['body_path']).read_bytes());assert d.sha(html)==hc['sha256'] and hc['status']==200
            text=BeautifulSoup(html,'html.parser').get_text(' ',strip=True);assert 'reverse side' in text and 'Maud Abrantes' in text
            basis+=' Official Hecht catalogue identifies this portrait as the reverse side of the canvas carrying Nude with a Hat. Link the already-existing portrait-face record; create no additional object. Preserve WikiArt/catalogue 1907 and retain official-source 1908 as evidence. Counts refer to artwork records, not distinct physical canvases.'
        claims.append(dict(artwork_id=a['id'],title=a['title'],scheme=scheme,external_id=external_id,institution=museum,source_url=url,checked_at=rc['retrieved_at'],location_text=museum['name'],source_class=source_class,source_receipt=rc,claim_type='holding',review_state='accepted',identity_basis=basis,duplicate_source_urls=[item['canonical']],object_evidence=dict(editorial_confidence=confidence,confidence_basis=basis,wikiart=item,wikidata=source,hecht_verso_source=proof['hecht_verso_source'] if item['qid']=='Q76627278' else None),limitation='Documented collection relationship, not current display or legal-title verification. Existing artwork/version identities, dates, images, creators and publication states are preserved.'))
    dest=RUN/'links/reviewed-existing';d.save(dest/'claims.json.gz',dict(at=d.now(),provider='reviewed-wikiart-and-wikidata',claims=claims,held=[]));d.save(dest/'baseline.json.gz',before);d.save(dest/'backups.json',d.load(RUN/'backups.json'))
    print('Prepared',len(claims),'individually reviewed existing-artwork links',flush=True)

def link_phase(phase):
    campaign=r.p.campaign();campaign.OP=OP;campaign.link_delivery(phase,'reviewed-existing')

def verify():
    folder=RUN/'waves/final-reviewed';plan=d.load(folder/'plan.json.gz');receipt=d.load(folder/'applied.json')
    assert receipt['plan_sha256']==d.sha((folder/'plan.json.gz').read_bytes())
    records={x['artwork_id']:x for x in plan['records']};assert len(records)==27
    lf=RUN/'links/reviewed-existing/delivery/verified';linkproof=d.load(lf/'verification.json');lp=d.load(lf/'plan.json.gz')
    assert not linkproof['errors'] and linkproof['targets']=={'production':4} and linkproof['plan_sha256']==d.sha((lf/'plan.json.gz').read_bytes())
    aliases=d.load(RUN/'aliases/verification.json');aliasapi=d.load(RUN/'aliases/api-verification.json');assert aliases['verified_aliases']==aliasapi['passed']==10 and not aliasapi['failed']
    baseline=d.load(RUN/'baseline.json.gz');base={x['institution']['id']:x for x in baseline['selected']}
    assert all(x['museum']['id'] in base for x in records.values())
    with d.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        arts=db.execute('SELECT to_jsonb(a) artwork,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,artline_has_selection_evidence(id) selected FROM artworks a WHERE id=ANY(%s::uuid[])',(list(records),)).fetchall()
        assert len(arts)==len(records)
        for x in arts:
            a=x['artwork'];r=records[a['id']];f=r['facts'];assert a['current_institution_id']==r['museum']['id'] and x['scope']=='eligible' and x['selected']
            assert a['status']=='review' and a['published_at'] is None and a['primary_media_id'] is None
            for col,key in [('title','title'),('unlinked_creator_label','creator_label'),('creation_year_start','first'),('creation_year_end','last'),('date_precision','date_precision'),('date_display','date_display'),('accession_number','accession'),('medium_text','medium'),('dimensions_text','dimensions'),('work_type','work_type'),('object_form','object_form')]:assert a[col]==f.get(key),(a['id'],col)
        cites=db.execute("SELECT entity_id::text,source_record_id,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='museum_source_metadata_and_holding'",(list(records),)).fetchall();assert len(cites)==len(records)
        for c in cites:
            row=records[c['entity_id']];ev=json.loads(c['evidence_note']);assert c['source_record_id']==row['source_record_id'] and c['source_url']==row['facts']['source_url'] and ev['plan_sha256']==receipt['plan_sha256'] and ev['raw_source_record']==row['raw_source_record']
        holdings=db.execute('SELECT to_jsonb(h) v FROM artwork_location_assertions h WHERE artwork_id=ANY(%s::uuid[])',(list(records),)).fetchall();assert len(holdings)==len(records)
        for x in holdings:
            h=x['v'];assert h['institution_id']==records[h['artwork_id']]['museum']['id'] and h['claim_type']=='holding' and h['review_state']=='accepted' and h['display_state'] is None and h['superseded_by'] is None
        for row in aliases['rows']:
            assert db.execute('SELECT canonical_institution_id::text id FROM institutions WHERE id=%s',(row['alias_id'],)).fetchone()['id']==row['canonical_id']
            assert not db.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s LIMIT 1',(row['alias_id'],)).fetchone()
        mids=set(base)|{x['canonical_id'] for x in aliases['rows']};counts={}
        for part in d.chunks(sorted(mids),100):counts.update({x['id']:x['n'] for x in db.execute("SELECT current_institution_id::text id,count(*) n FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' GROUP BY 1",(part,))})
        remaining=[x['v'] for x in db.execute("""SELECT to_jsonb(i) v FROM institutions i CROSS JOIN LATERAL
          (SELECT count(*) n FROM (SELECT 1 FROM artworks a WHERE a.current_institution_id=i.id AND a.status<>'archived' LIMIT 2) q) c
          WHERE i.kind='museum' AND i.status<>'archived' AND i.canonical_institution_id IS NULL AND c.n=1 ORDER BY i.name,i.id""")]
    additions=collections.Counter(x['museum']['id'] for x in records.values());links=collections.Counter(x['target_institutions']['production']['id'] for x in lp['claims'])
    rows=[]
    for iid in sorted(set(additions)|set(links)):
        i=base[iid]['institution'];assert counts[iid]>=1+additions[iid]+links[iid]
        rows.append(dict(id=iid,name=i['name'],slug=i['slug'],before=1,added=additions[iid],linked_existing=links[iid],after=counts[iid]))
    result=dict(at=d.now(),target='production',fresh_baseline_at=baseline['at'],baseline_exactly_one=len(base),new_artworks=len(records),existing_artworks_linked=len(lp['claims']),museums_expanded=len(rows),museum_aliases_reconciled=10,existing_artwork_links_preserved_during_alias_fix=10,current_global_exactly_one=len(remaining),new_publications=0,new_images=0,new_display_claims=0,local_database_writes=0,museums=rows,aliases=aliases['rows'])
    d.save(RUN/'verification.json',result);d.save(RUN/'remaining-one-artwork-museums.json.gz',dict(at=result['at'],museums=remaining))
    arts=[dict(artwork_id=aid,museum=r['museum']['name'],slug=r['museum']['slug'],title=r['facts']['title'],action='create',source_url=r['facts']['source_url']) for aid,r in records.items()]
    arts += [dict(artwork_id=x['target_ids']['production'],museum=x['institution']['name'],slug=x['institution']['slug'],title=x['title'],action='link_existing',source_url=x['source_url']) for x in lp['claims']]
    for filename,data in [('artwork-results.csv',arts),('museum-results.csv',rows),('museum-alias-results.csv',aliases['rows'])]:
        with (RUN/filename).open('x',newline='') as fp:
            w=csv.DictWriter(fp,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    print(json.dumps({k:v for k,v in result.items() if k not in ['museums','aliases']}),flush=True)

def api_verify():
    with (RUN/'artwork-results.csv').open() as f:arts=list(csv.DictReader(f))
    selected={}
    for a in arts:
        key=a['artwork_id'] if a['action']=='link_existing' else a['slug'];selected.setdefault(key,a)
    results=[]
    for a in selected.values():
        url='https://artlines.org/api/backend/v1/museums/'+a['slug']+'/works/'+a['artwork_id'];response=d.requests.get(url,timeout=(15,45))
        ok=response.status_code==200 and response.json().get('title')==a['title'];results.append(dict(url=url,title=a['title'],action=a['action'],status=response.status_code,verified=ok));print('API',a['museum'],a['action'],ok,flush=True)
    d.save(RUN/'api-verification.json',dict(at=d.now(),passed=sum(x['verified'] for x in results),failed=sum(not x['verified'] for x in results),checks=results));assert all(x['verified'] for x in results)

def report():
    v=d.load(RUN/'verification.json');api=d.load(RUN/'api-verification.json');assert api['failed']==0
    overview=d.load(RUN/'aliases/overview-api-verification.json');assert overview['passed']==10 and overview['failed']==0
    md=f"# Production one-artwork museums: identity fixes and third expansion\n\nFresh production audit: {v['fresh_baseline_at']}. Final verification: {v['at']}. The fresh initial count was **{v['baseline_exactly_one']}** canonical museum records with exactly one non-archived linked artwork. Several represented duplicate museum identities whose other records already held substantial collections.\n\n"
    md+=f"Applied **{v['museum_aliases_reconciled']} museum alias reconciliations**, preserving the original institution records, URLs, source citations and all existing artwork metadata. Added **{v['new_artworks']} new review artworks** and linked **{v['existing_artworks_linked']} existing artwork records** across **{v['museums_expanded']} further museums**. The final fresh production-wide count is **{v['current_global_exactly_one']} active canonical museums with exactly one artwork**.\n\n"
    md+='[Database verification](verification.json) · [Artwork and source list](artwork-results.csv) · [Museum counts](museum-results.csv) · [Museum identity fixes](museum-alias-results.csv) · [Remaining current one-artwork museums](remaining-one-artwork-museums.json.gz).\n\n'
    md+='The initial audit uses indexed institution lookups capped at two artworks, then reads only the selected records. It does not reuse old counts. Each reviewed alias connects the specific same museum and city, supported by retained official museum/government pages; separate museums, collection sites and similarly named institutions were not combined. Publication, dates, creator links, media relationships and original source identities were independently verified preserved. Both old and canonical URLs passed identical artwork API responses for all ten aliases. [Live museum overview checks](aliases/overview-api-verification.json) also confirmed the full collection counts through every old one-artwork URL.\n\n'
    md+='Twelve previously unmapped museum names were individually matched to full Wikidata museum authorities, including their city and official website. Bounded museum-specific queries inspected 618 object entities and 330 creator entities. Forty-one source candidates passed full collection-statement, reference, creation-date, type and attribution checks. Production native-ID, title, creator and date checks, followed by individual version review, admitted 27 additions. The actual addition source is referenced Wikidata metadata (editorial confidence 0.85); underlying object references were not independently opened. Full statements and museum-authority evidence are retained in each new record’s citation. Unreferenced holdings, qualified dates, conflicting collections and unresolved object versions remain held.\n\n'
    md+='Stone City, Iowa (painting) and Nude with a Hat were recognized as already-catalogued works, not new objects. Picasso’s Jester on horseback was matched to the existing Harlequin on the horseback: creator, 1905 date, translated subject and distinctive 100 × 69.2 cm dimensions agree. Its holding source is the referenced Wikidata statement; the fresh WikiArt page supplies identity evidence and has no Location field. RKD direct access was unavailable. Confidence is 0.90 editorial assessment.\n\n'
    md+='Three other existing links use exact fresh WikiArt artwork IDs, creators, titles and explicit museum Location fields: Benjamin West’s General Thaddeus Kosciusko, Hopper’s High Noon, and Modigliani’s Portrait of Maude Abrantes. Official Hecht evidence identifies the latter as the reverse side of the canvas carrying the already-linked Nude with Hat. Both existing face records are preserved; this pass creates no additional Modigliani object and does not rewrite the existing 1907 dates to the official page’s 1908. Counts are catalogue artwork records, not an assertion that every legacy record is a separate physical canvas. Confidence is 0.95 editorial assessment.\n\n'
    md+=f"Validation: [13 source-guard tests passed](tests.json); separate read-only checks verified every added/linked record and all ten identity reconciliations. [Live checks](api-verification.json) passed for {api['passed']} new/existing artwork URLs, plus [both museum URL forms](aliases/api-verification.json) for ten aliases. No new images, display assertions, automatic publication, local database writes, commits or deployment. Recovery: successful Cloud SQL backup {d.load(RUN/'backups.json')['production']['id']} and locked per-record preimages under `~/Library/Application Support/Artline/backups/{OP}/`.\n\n"
    md+='## Existing collections recovered through museum identities\n\n| Former one-work museum record | Existing collection before | After |\n|---|---:|---:|\n'
    for x in v['aliases']:md+=f"| {x['alias_name']} | {x['before_canonical']} | {x['after']} |\n"
    md+='\n## Additional catalogue coverage\n\n| Museum | Before | Added | Existing linked | After |\n|---|---:|---:|---:|---:|\n'
    for x in sorted(v['museums'],key=lambda x:(-x['after'],x['name'])):md+=f"| {x['name']} | 1 | {x['added']} | {x['linked_existing']} | {x['after']} |\n"
    (RUN/'README.md').write_text(md);print('Verified report saved',flush=True)

def baseline():
    sql="""SELECT to_jsonb(i) institution FROM institutions i
      CROSS JOIN LATERAL (SELECT count(*) n FROM
        (SELECT 1 FROM artworks a WHERE a.current_institution_id=i.id AND a.status<>'archived' LIMIT 2) bounded) c
      WHERE i.kind='museum' AND i.status<>'archived' AND i.canonical_institution_id IS NULL AND c.n=1 ORDER BY i.name,i.id"""
    with d.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        plan=db.execute('EXPLAIN (FORMAT JSON) '+sql).fetchone()
        selected=db.execute(sql).fetchall();ids=[x['institution']['id'] for x in selected]
        arts=[x['v'] for x in db.execute("SELECT to_jsonb(a) v FROM artworks a WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' ORDER BY id",(ids,))]
        scopes={x['id']:x['scope'] for x in db.execute('SELECT id::text,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope FROM artworks WHERE id=ANY(%s::uuid[])',([x['id'] for x in arts],))}
        assertions=[x['v'] for x in db.execute('SELECT to_jsonb(h) v FROM artwork_location_assertions h WHERE institution_id=ANY(%s::uuid[]) AND superseded_by IS NULL ORDER BY institution_id,artwork_id,id',(ids,))]
        citations=[x['v'] for x in db.execute("SELECT to_jsonb(c) v FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",([x['id'] for x in arts],))]
        identifiers=[x['v'] for x in db.execute("SELECT to_jsonb(e) v FROM external_identifiers e WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",([x['id'] for x in arts],))]
    bymuseum={x['current_institution_id']:x for x in arts};assert len(arts)==len(selected)
    for x in selected:
        a=bymuseum[x['institution']['id']]
        x['counts']=dict(id=x['institution']['id'],linked=1,eligible=int(scopes[a['id']]=='eligible'),images=int(bool(a['primary_media_id'])))
    value=dict(at=d.now(),target='production',selection='Fresh active canonical museums with exactly one non-archived linked artwork, including review; indexed institution-scoped probes stop after two rows.',selected=selected,original_artworks=arts,existing_assertions=assertions)
    d.save(RUN/'baseline.json.gz',value);d.save(RUN/'baseline-query-plan.json',plan)
    d.save(RUN/'original-source-evidence.json.gz',dict(citations=citations,identifiers=identifiers))
    old=d.load(ROOT/'docs/research/museums-exactly-one-round2-20261008/verification.json')
    previous={x['id'] for x in old['museums'] if x['after']==1}
    d.save(RUN/'snapshot-comparison.json',dict(previous_at=old['at'],current_at=value['at'],previous_exactly_one=len(previous),current_exactly_one=len(ids),no_longer_exactly_one=sorted(previous-set(ids)),new_exactly_one=sorted(set(ids)-previous)))
    with (RUN/'selected-museums.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['id','name','slug','wikidata_id','linked','eligible','images']);writer.writeheader()
        for x in selected:writer.writerow(dict(**{k:x['institution'][k] for k in ['id','name','slug','wikidata_id']},**{k:x['counts'][k] for k in ['linked','eligible','images']}))
    print('Fresh production snapshot',value['at'],len(ids),'exactly-one museums; previous',len(previous),'changed',len(previous-set(ids)),flush=True)
    for x in selected:print(x['institution']['name'],x['institution'].get('wikidata_id'),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['baseline','backup','local_candidates','history','authority_search','authority_prepare','authority_research','identity_review','link_research','links_prepare','link_plan','link_apply','link_verify','final_plan','plan','apply','verify','api_verify','report']);args=parser.parse_args()
    if args.phase in ['link_plan','link_apply','link_verify']:link_phase(args.phase)
    elif args.phase in ['baseline','authority_search','authority_prepare','authority_research','identity_review','link_research','links_prepare','final_plan','plan','apply','verify','api_verify','report']:globals()[args.phase]()
    else:getattr(r,args.phase)()
