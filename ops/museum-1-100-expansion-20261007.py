#!/usr/bin/env python3
"""Expand the user's production museum cohort with 1–100 works toward 200."""
import argparse,collections,csv,gzip,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('previous_priority',Path(__file__).with_name('museum-1-10-priority-20261007.py'))
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
c=p.c;n=p.n
ROOT=c.RUN/'expansion-1-100-20261007';PREFIX='expand-1-100-';TARGET=200
BASE={x['institution']['id']:x for x in c.load(ROOT/'baseline.json.gz')['selected']}if(ROOT/'baseline.json.gz').exists()else{}
c.BASE.update(BASE)
arco=c.module('expanded_arco','minimum-100-arco-native-20261006.py')
arco_review=c.module('expanded_arco_review','museum-1-10-arco-review-20261007.py')
ORIGINAL_CHECK=c.check_body


def baseline():
    dest=ROOT/'baseline.json.gz'
    if dest.exists():print('Existing frozen baseline:',len(BASE),'museums');return
    with c.d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        museums=[x['v']for x in db.execute("SELECT to_jsonb(i)v FROM institutions i WHERE kind='museum'AND status<>'archived'AND canonical_institution_id IS NULL ORDER BY name")]
        counts={}
        for part in c.d.chunks([x['id']for x in museums],100):
            counts.update({x['id']:x for x in db.execute("SELECT current_institution_id::text id,count(*)linked,count(*)FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible')eligible,count(primary_media_id)images FROM artworks WHERE current_institution_id=ANY(%s::uuid[])AND status<>'archived'GROUP BY current_institution_id",(part,))})
        selected=[dict(institution=x,**{k:v for k,v in counts[x['id']].items()if k!='id'})for x in museums if 1<=counts.get(x['id'],{}).get('linked',0)<=100]
    value=dict(at=c.d.now(),target='production',target_artworks=TARGET,canonical_active_museums=len(museums),selected=selected,
        selection='All active canonical museum records with 1–100 non-archived linked artwork records, inclusive. Counts include review artworks; date eligibility, images and public visibility are separate.')
    c.save(dest,value)
    with(ROOT/'all-museums-1-100.csv').open('w',newline='')as f:
        writer=csv.DictWriter(f,fieldnames=['id','name','slug','wikidata_id','linked','eligible','images','target','gap']);writer.writeheader()
        for x in selected:writer.writerow(dict(**{k:x['institution'][k]for k in ['id','name','slug','wikidata_id']},**{k:x[k]for k in ['linked','eligible','images']},target=TARGET,gap=TARGET-x['linked']))
    print('Frozen production cohort:',len(selected),'museums; exactly 100:',sum(x['linked']==100 for x in selected),'current artworks:',sum(x['linked']for x in selected),flush=True)


def prepare(wave,records,held=None):
    c.configure(wave);selected={x['museum']['id']:x['museum']for x in records}
    c.save(c.d.RUN/'sample.json',dict(at=c.d.now(),selected=[{k:x[k]for k in ['id','name','slug']}for _,x in sorted(selected.items())],
        target=TARGET,selection='Frozen production cohort with 1–100 works; selected supported objects toward 200 per museum.'))
    c.save(c.d.RUN/'source-verified.json.gz',dict(at=c.d.now(),records=records,held=held or []))
    print('Prepared',wave,len(records),'records for',len(selected),'museums',flush=True)


def check_body(row,cache):
    provider=row['provider']
    if provider=='wikidata-catalogue':return n.check_body(row,cache)
    if provider=='arco-native':return arco.check_body(row,cache)
    if provider=='arco-native-priority':return arco_review.check_body(row,cache)
    return ORIGINAL_CHECK(row,cache)


def scheme(row):
    if row['provider']=='wikidata-catalogue':return'wikidata'
    if row['provider']=='aargauer-native':return'aargauer-object'
    return c.ORIGINAL_SCHEME(row)


def reuse(wave):
    ready={};held=[];lineage=[];conflicts=set()
    for path in sorted((c.RUN/'waves').glob('*/plan.json.gz')):
        if path.parent.name.startswith(PREFIX)or not(path.parent/'applied.json').exists():continue
        receipt=c.load(path.parent/'applied.json');assert c.d.sha(path.read_bytes())==receipt['plan_sha256']
        plan=c.load(path);ids={x['artwork_id']for x in plan.get('outside_target',[])if x['museum_id']in BASE}
        if not ids:continue
        source=c.load(path.parent/'source-verified.json.gz')
        lineage.append(dict(wave=path.parent.name,plan_sha256=receipt['plan_sha256'],source_records_outside_previous_quota=len(ids)))
        for row in source['records']:
            if row['artwork_id']not in ids or row['museum']['id']not in BASE:continue
            key=(scheme(row),row['source_record_id'])
            if key in conflicts:continue
            if key in ready and ready[key]['museum']['id']!=row['museum']['id']:
                held.append(dict(source_record_id=row['source_record_id'],reason='cross_wave_museum_identity_conflict'));ready.pop(key);conflicts.add(key);continue
            if key not in ready or row['source_receipt']['retrieved_at']>ready[key]['source_receipt']['retrieved_at']:ready[key]=row
    c.save(ROOT/wave/'reuse-lineage.json',lineage)
    prepare(wave,list(ready.values()),held)


def select(wave,limit):
    dest=n.ROOT/wave/'selected-museums.json'
    if dest.exists():return c.load(dest)
    p.BASE=BASE;institutions,counts=p.snapshot();byq=collections.Counter(x.get('wikidata_id')for x in institutions.values())
    history=n.index_history();selected=[];held=[]
    for iid,before in BASE.items():
        museum=institutions.get(iid);count=counts[iid]['linked']
        if not museum:held.append(dict(museum_id=iid,reason='authority_now_archived_or_canonical_alias'));continue
        if count>=TARGET:continue
        q=museum.get('wikidata_id')
        if not q:held.append(dict(museum_id=iid,reason='no_wikidata_authority_requires_native_source'));continue
        if byq[q]!=1:held.append(dict(museum_id=iid,reason='duplicate_live_museum_authority'));continue
        if re.search(r'horlivka|sevastopol|roerich.*moscow',museum['name'],re.I):held.append(dict(museum_id=iid,reason='historical_or_displaced_collection_requires_specific_review'));continue
        pages=history[iid]
        if len(pages)>=8:held.append(dict(museum_id=iid,reason='eight_bounded_metadata_pages_reviewed'));continue
        if pages and(not pages[-1]['capped']or not pages[-1]['selected_ids']):held.append(dict(museum_id=iid,reason='source_index_exhausted'));continue
        cursor=max(pages[-1]['selected_ids'])if pages else''
        selected.append(dict(museum=museum,projected_count=count,baseline_count=before['linked'],cursor=cursor,page_number=len(pages)+1,target_count=TARGET))
    selected=sorted(selected,key=lambda x:(x['projected_count']>=100,x['page_number'],-x['projected_count'],x['museum']['name']))[:limit]
    c.save(dest,selected);c.save(n.ROOT/wave/'expanded-source-outcomes.json',held)
    return selected


def delivery(phase,wave):
    c.configure(wave);c.d.TARGET_FIELD='linked';c.d.TARGET_COUNT=TARGET;c.d.DEFAULT_CONFIDENCE=0.85
    c.d.SOURCE_NAME='Museum 1–100 expansion: selected source-backed catalogue records';c.d.SOURCE_BASE_URL=None
    c.d.CONFIDENCE_BASIS='Verified source object identity, reviewed existing museum authority and explicit eligible creation dates. Actual primary catalogue or referenced Wikidata source is retained per object. Editorial assessment 0.85, not calibrated probability; no current-display claim.'
    c.d.check_body=check_body;c.d.scheme=scheme
    if phase=='plan':c.d.plan()
    else:c.d.apply()


def links_research(wave,qualified=False):
    p.BASE=BASE;institutions,counts=p.snapshot()
    byq=collections.Counter(x.get('wikidata_id')for x in institutions.values())
    selected={iid:dict(before,institution=institutions[iid])for iid,before in BASE.items()
        if iid in institutions and institutions[iid].get('wikidata_id')and byq[institutions[iid]['wikidata_id']]==1 and counts[iid]['linked']<TARGET
        and not re.search(r'horlivka|sevastopol|roerich.*moscow',institutions[iid]['name'],re.I)}
    w=c.module('expanded_existing_links','minimum-100-wikidata-links-20261006.py');w.c.BASE=selected
    w.main(qualified=qualified,target_count=TARGET,output_root=c.RUN/'links'/wave)
    c.save(c.RUN/'links'/wave/'museum-authority-review.json',dict(at=c.d.now(),target=TARGET,
        selected_museum_ids=sorted(selected),basis='Frozen 1–100 cohort; current active canonical museum with globally unique Wikidata authority; displaced/historical collections held.'))


def audit():
    p.BASE=BASE;institutions,counts=p.snapshot();expected={};new=links=0;waves=[]
    for path in sorted((c.RUN/'waves').glob(PREFIX+'*/applied.json')):
        receipt=c.load(path);pin=path.parent/'plan.json.gz';assert c.d.sha(pin.read_bytes())==receipt['plan_sha256'];plan=c.load(pin)
        new+=receipt['new_artworks'];links+=receipt['linked_artworks'];waves.append(path.parent.name)
        for row in plan['records']:assert row['artwork_id']not in expected;expected[row['artwork_id']]=row
    linkids=set();linkclaims=[]
    for path in sorted((c.RUN/'links').glob(PREFIX+'*/delivery/verified/verification.json')):
        check=c.load(path);pin=path.parent/'plan.json.gz';assert c.d.sha(pin.read_bytes())==check['plan_sha256']and not check['errors']
        plan=c.load(pin);assert check['targets']=={'production':len(plan['claims'])};linkclaims.extend(plan['claims']);linkids.update(x['target_ids']['production']for x in plan['claims'])
    links+=len(linkids)
    with c.d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');actual=[]
        for part in c.d.chunks(list(expected),500):actual.extend(db.execute('SELECT to_jsonb(a)artwork,artline_creation_scope(creation_year_start,creation_year_end,date_precision)scope,artline_has_selection_evidence(a.id)evidence FROM artworks a WHERE id=ANY(%s::uuid[])',(part,)))
        assert len(actual)==len(expected)
        for x in actual:
            art=x['artwork'];row=expected[art['id']];assert art['current_institution_id']==row['museum']['id']and x['evidence']
            if row['action']=='create':
                assert art['status']=='review'and art['published_at']is None and art['primary_media_id']is None and x['scope']=='eligible'
                for col,key in [('title','title'),('unlinked_creator_label','creator_label'),('date_display','date_display'),('creation_year_start','first'),('creation_year_end','last'),('date_precision','date_precision'),('accession_number','accession'),('medium_text','medium'),('dimensions_text','dimensions')]:assert art[col]==row['facts'][key]
            else:assert all(art[k]==v for k,v in row['before'].items()if k not in {'current_institution_id','updated_at','revision'})
        for part in c.d.chunks(linkclaims,500):
            actual={x['id']:x['current_institution_id']for x in db.execute('SELECT id::text,current_institution_id::text FROM artworks WHERE id=ANY(%s::uuid[])',([x['target_ids']['production']for x in part],))}
            assert all(actual[x['target_ids']['production']]==x['target_institutions']['production']['id']for x in part)
    rows=[dict(id=iid,name=b['institution']['name'],slug=b['institution']['slug'],before=b['linked'],**counts[iid],added_or_linked=counts[iid]['linked']-b['linked'],gap=max(0,TARGET-counts[iid]['linked']),authority_state='active_canonical'if iid in institutions else'changed_requires_review')for iid,b in BASE.items()]
    result=dict(at=c.d.now(),target='production',initial_museums_1_to_100=len(BASE),target_per_museum=TARGET,new_artworks=new,existing_artworks_linked=links,
        museums_expanded=sum(x['added_or_linked']>0 for x in rows),museums_above_100=sum(x['linked']>100 for x in rows),museums_at_least_200=sum(x['linked']>=TARGET for x in rows),museums_still_1_to_100=sum(1<=x['linked']<=100 for x in rows),waves=waves,museums=rows,
        status='in_progress'if any(x['gap']for x in rows)else'target_met',new_publications=0,new_images=0,new_display_claims=0,local_database_writes=0)
    c.save(ROOT/'audits'/(result['at'].replace(':','')+'.json.gz'),result);(ROOT/'progress.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    with(ROOT/'museum-progress.csv').open('w',newline='')as f:writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    md=f"# Museums with 1–100 artworks: production expansion\n\nFrozen production audit: {c.load(ROOT/'baseline.json.gz')['at']}. **{len(BASE):,} active canonical museum records** had 1–100 linked non-archived artworks, including exactly 100. Selected source-backed additions/links aim toward **200** each. This extends the prior requests; unknown identities, dates and source gaps remain explicit.\n\n"
    md+=f"Verified at {result['at']}: **{new:,} new artworks** and **{links:,} existing-artwork links** delivered by this expansion. **{result['museums_expanded']}** museums expanded; **{result['museums_above_100']}** exceed 100; **{result['museums_at_least_200']}** reach 200. **{result['museums_still_1_to_100']}** remain in the 1–100 range.\n\n"
    md+='[Complete initial museum list](all-museums-1-100.csv) · [Current museum counts](museum-progress.csv) · [Database audit](progress.json). Counts include review records; source eligibility and images are separate columns. New artworks remain in review. Existing dates, creator links, media and publication states are preserved. Holdings do not assert current display. Recovery preimages are under the Artline backups directory.\n'
    if(ROOT/'worker/status.json').exists():md+='\n[Continuation status](worker/status.json) · [Execution log](worker/worker.log). Source-pass exhaustion with remaining gaps is not completion.\n'
    (ROOT/'README.md').write_text(md);print(json.dumps({k:v for k,v in result.items()if k not in ['museums','waves']},ensure_ascii=False),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['baseline','reuse','research','plan','apply','audit','links_research','link_plan','link_apply','link_verify']);ap.add_argument('--wave');ap.add_argument('--museums',type=int,default=20);ap.add_argument('--qualified',action='store_true');args=ap.parse_args()
    if args.phase in ['baseline','audit']:globals()[args.phase]()
    else:
        assert args.wave and args.wave.startswith(PREFIX)
        if args.phase=='reuse':reuse(args.wave)
        elif args.phase=='links_research':links_research(args.wave,args.qualified)
        elif args.phase.startswith('link_'):c.link_delivery(args.phase,args.wave)
        elif args.phase=='research':
            p.ROOT=ROOT;n.entity_capture=p.retry_transport_capture;c.prepare_wave=prepare;select(args.wave,args.museums);n.research(args.wave,args.museums,target_count=TARGET)
        else:delivery(args.phase,args.wave)
