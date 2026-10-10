#!/usr/bin/env python3
"""Prioritize the user's frozen production set of museums with 1–10 works."""
import argparse,collections,csv,gzip,importlib.util,json,re,time
from pathlib import Path

s=importlib.util.spec_from_file_location('priority_native',Path(__file__).with_name('minimum-100-wikidata-catalogue-20261006.py'))
n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
c=n.c
ROOT=c.RUN/'priority-1-10-20261007'
BASE={x['institution']['id']:x for x in c.load(ROOT/'baseline.json.gz')['selected']}
# Keep the original campaign IDs/evidence layout while adding newly discovered
# authorities to this task's selection context. Never mutate the frozen baseline.
c.BASE.update(BASE)


ORIGINAL_CAPTURE=n.entity_capture
def retry_transport_capture(url):
    # Retry one interrupted transport, retaining successful immutable captures.
    # Source denials and HTTP rate limits keep the original stop/backoff policy.
    for attempt in range(2):
        try:return ORIGINAL_CAPTURE(url)
        except (n.requests.exceptions.ConnectionError,n.requests.exceptions.Timeout)as exc:
            c.save(ROOT/'transport-retries'/(c.d.sha(url.encode())+'-'+c.d.now().replace(':','')+'.json'),
                dict(at=c.d.now(),url=url,attempt=attempt+1,error=type(exc).__name__,message=str(exc)[:200],retry_delay_seconds=15 if attempt==0 else None))
            if attempt:raise
            print('Interrupted source transport; retrying once after 15 seconds',flush=True);time.sleep(15)


def snapshot():
    with c.d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        institutions={x['v']['id']:x['v']for x in db.execute("SELECT to_jsonb(i)v FROM institutions i WHERE status<>'archived'AND canonical_institution_id IS NULL")}
        counts={iid:dict(linked=0,eligible=0,images=0)for iid in BASE}
        for part in c.d.chunks(list(BASE),100):
            for x in db.execute("SELECT current_institution_id::text id,count(*)linked,count(*)FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible')eligible,count(primary_media_id)images FROM artworks WHERE current_institution_id=ANY(%s::uuid[])AND status<>'archived'GROUP BY current_institution_id",(part,)):
                counts[x['id']]={k:v for k,v in x.items()if k!='id'}
    return institutions,counts


def select(wave,limit):
    dest=n.ROOT/wave/'selected-museums.json'
    if dest.exists():return c.load(dest)
    institutions,counts=snapshot();byq=collections.Counter(x.get('wikidata_id')for x in institutions.values())
    history=n.index_history();selected=[];held=[]
    for iid,before in BASE.items():
        museum=institutions.get(iid);count=counts[iid]['linked']
        if not museum:held.append(dict(museum_id=iid,reason='authority_now_archived_or_canonical_alias'));continue
        if count>=100:continue
        q=museum.get('wikidata_id')
        if not q:held.append(dict(museum_id=iid,reason='no_wikidata_museum_authority_requires_other_source'));continue
        if byq[q]!=1:held.append(dict(museum_id=iid,reason='duplicate_live_museum_authority_requires_reconciliation'));continue
        if re.search(r'horlivka|sevastopol|roerich.*moscow',museum['name'],re.I):
            held.append(dict(museum_id=iid,reason='historical_or_displaced_collection_requires_specific_review'));continue
        cursor,reason=n.next_cursor(history[iid])
        if reason:held.append(dict(museum_id=iid,reason=reason));continue
        selected.append(dict(museum=museum,projected_count=count,priority_baseline_count=before['linked'],cursor=cursor,page_number=len(history[iid])+1))
    selected=sorted(selected,key=lambda x:(-x['projected_count'],x['museum']['name']))[:limit]
    c.save(dest,selected);c.save(n.ROOT/wave/'priority-source-outcomes.json',held)
    c.save(n.ROOT/wave/'priority-authority-snapshot.json.gz',dict(at=c.d.now(),institutions=institutions,counts=counts))
    return selected


def audit():
    institutions,counts=snapshot();rows=[]
    for iid,b in BASE.items():
        current=counts[iid];museum=institutions.get(iid,b['institution'])
        rows.append(dict(id=iid,name=museum['name'],slug=museum['slug'],wikidata_id=museum.get('wikidata_id'),before=b['linked'],
            **current,added_or_linked=current['linked']-b['linked'],gap=max(0,100-current['linked']),
            authority_state='active_canonical'if iid in institutions else'changed_requires_review',canonical_institution_id=None,canonical_name=None,canonical_linked=None))
    delivered=[];new=links=0;expected={}
    for path in sorted((c.RUN/'waves').glob('priority-1-10-*/applied.json')):
        receipt=c.load(path);plan_path=path.parent/'plan.json.gz';assert c.d.sha(plan_path.read_bytes())==receipt['plan_sha256']
        plan=c.load(plan_path);delivered.append(path.parent.name)
        new+=receipt['new_artworks'];links+=receipt['linked_artworks']
        for row in plan['records']:assert row['artwork_id']not in expected;expected[row['artwork_id']]=row
    linkids=set()
    for path in sorted((c.RUN/'links').glob('priority-1-10-*/delivery/verified/verification.json')):
        check=c.load(path);pin=path.parent/'plan.json.gz';assert c.d.sha(pin.read_bytes())==check['plan_sha256']and not check['errors']
        reviewed=c.load(pin);assert check['targets']=={'production':len(reviewed['claims'])}
        linkids.update(x['target_ids']['production']for x in reviewed['claims'])
    links+=len(linkids)
    with c.d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        actual=[]
        for part in c.d.chunks(list(expected),500):
            actual.extend(db.execute("SELECT to_jsonb(a) artwork,artline_creation_scope(creation_year_start,creation_year_end,date_precision)scope,artline_has_selection_evidence(a.id)evidence FROM artworks a WHERE id=ANY(%s::uuid[])",(part,)))
        assert len(actual)==len(expected)
        for item in actual:
            art=item['artwork'];row=expected[art['id']];assert art['current_institution_id']==row['museum']['id']and item['evidence']
            if row['action']=='create':
                assert art['status']=='review'and art['published_at']is None and art['primary_media_id']is None and item['scope']=='eligible'
                for col,key in [('title','title'),('unlinked_creator_label','creator_label'),('date_display','date_display'),('creation_year_start','first'),('creation_year_end','last'),('date_precision','date_precision'),('accession_number','accession')]:assert art[col]==row['facts'][key]
            else:
                assert all(art[k]==v for k,v in row['before'].items()if k not in {'current_institution_id','updated_at','revision'})
        aliases=db.execute("SELECT i.id::text,i.canonical_institution_id::text,c.name canonical_name,(SELECT count(*)FROM artworks a WHERE a.current_institution_id=c.id AND a.status<>'archived')canonical_linked FROM institutions i JOIN institutions c ON c.id=i.canonical_institution_id WHERE i.id=ANY(%s::uuid[])",(list(BASE),)).fetchall()
        byid={x['id']:x for x in rows}
        for alias in aliases:
            byid[alias['id']].update({k:v for k,v in alias.items()if k!='id'},authority_state='verified_canonical_alias')
        identity_receipt=ROOT/'institution-identities/applied.json'
        if identity_receipt.exists():
            receipt=c.load(identity_receipt);byalias={x['id']:x for x in aliases}
            for pair in receipt['pairs']:
                assert byalias[pair['alias']]['canonical_institution_id']==pair['canonical']
                ids=[x['id']for x in pair['artworks']]
                assert db.execute('SELECT count(*)n FROM artworks WHERE id=ANY(%s::uuid[])AND current_institution_id=%s',(ids,pair['canonical'])).fetchone()['n']==len(ids)
    result=dict(at=c.d.now(),target='production',initial_museums_1_to_10=len(BASE),new_artworks=new,existing_artworks_linked=links,
        museums_expanded=sum(x['added_or_linked']>0 for x in rows),museums_now_above_10=sum(x['linked']>10 for x in rows),
        museums_now_at_least_100=sum(x['linked']>=100 for x in rows),museums_still_1_to_10=sum(1<=x['linked']<=10 for x in rows),
        duplicate_museum_identities_reconciled=len(aliases),waves=delivered,museums=rows,status='in_progress'if any(x['gap']for x in rows if x['authority_state']=='active_canonical')else'target_met')
    c.save(ROOT/'audits'/(result['at'].replace(':','')+'.json.gz'),result)
    (ROOT/'progress.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    with(ROOT/'museum-progress.csv').open('w',newline='')as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    md=f"# Museums with 1–10 artworks: priority pass\n\nProduction snapshot: {c.load(ROOT/'baseline.json.gz')['at']}. **{len(BASE):,} active canonical museum records** had 1–10 non-archived linked artwork records. The broader campaign continues; this pass prioritizes these museum IDs toward 100 supported records each. Museum authority duplicates and source gaps remain explicit.\n\n"
    md+=f"Verified at {result['at']}: **{new:,} new artworks**, **{links:,} existing artworks linked** by this priority pass. **{result['museums_expanded']}** priority museums have grown since the snapshot; **{result['museums_now_above_10']}** now exceed 10 and **{result['museums_now_at_least_100']}** reach 100. **{result['museums_still_1_to_10']}** remain at 1–10. Counts include review records; eligible dates and existing image counts are reported separately.\n\n"
    md+='[Complete initial list](all-museums-1-10.csv) · [Production progress](museum-progress.csv) · [Audit detail](progress.json). New records remain in review with original dates, labels and source evidence. No new publication, images or display claims. Exact preimages are retained under the Artline backups directory.\n'
    if aliases:md+=f"\n**{len(aliases)} duplicate museum identities reconciled** to their existing canonical museums. Source names, old URLs and provenance remain; their canonical collection counts are separate CSV columns, not fabricated additions. [Identity evidence](institution-identities/plan.json.gz).\n"
    if(ROOT/'worker/status.json').exists():md+='\n[Continuation status](worker/status.json) · [Execution log](worker/worker.log). Source exhaustion with remaining gaps is not completion.\n'
    (ROOT/'README.md').write_text(md)
    print(json.dumps({k:v for k,v in result.items()if k not in ['museums','waves']},ensure_ascii=False),flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['research','plan','apply','audit']);ap.add_argument('--wave');ap.add_argument('--museums',type=int,default=10);args=ap.parse_args()
    if args.phase=='audit':audit();return
    assert args.wave and args.wave.startswith('priority-1-10-')
    if args.phase=='research':
        n.entity_capture=retry_transport_capture;select(args.wave,args.museums);n.research(args.wave,args.museums);return
    c.d.TARGET_FIELD='linked';c.d.DEFAULT_CONFIDENCE=0.85;c.d.SOURCE_NAME='Low-count museum priority: selected referenced Wikidata catalogue metadata';c.d.SOURCE_BASE_URL='https://www.wikidata.org/'
    c.d.CONFIDENCE_BASIS='Exact Wikidata painting/icon entity, single referenced collection statement, unique live museum authority, explicit pre-1971 creation date and retained creator labels. Editorial assessment 0.85, not calibrated probability; underlying referenced documents not independently verified.'
    old=c.ORIGINAL_SCHEME;c.ORIGINAL_SCHEME=lambda row:'wikidata'if row['provider']=='wikidata-catalogue'else old(row)
    c.check_body=n.check_body;c.delivery(args.phase,args.wave)


if __name__=='__main__':main()
