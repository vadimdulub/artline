#!/usr/bin/env python3
"""Source-backed production expansion of a frozen exactly-one-artwork cohort."""
import argparse
import collections
import csv
import importlib.util
import json
import os
import gzip
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/museums-exactly-one-20261008'
os.environ.setdefault('ARTLINE_MUSEUM_PROXY_PORT', '55492')
spec = importlib.util.spec_from_file_location('delivery', ROOT / 'ops/museum-minimum-100-delivery-20261006.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


def campaign():
    s=importlib.util.spec_from_file_location('one_campaign',ROOT/'ops/all-museums-minimum-100-20261006.py')
    c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
    c.RUN=RUN
    c.OP='museums-exactly-one-20261008'
    c.BASE={x['institution']['id']:x for x in d.load(RUN/'baseline.json.gz')['selected']}
    return c


def wikiart_links():
    c=campaign()
    c.wikiart_links('wikiart',expanded=True)


def joconde():
    campaign().joconde()


def local_candidates():
    base={x['institution']['id']:x['institution'] for x in d.load(RUN/'baseline.json.gz')['selected']}
    with d.m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        rows=[]
        for part in d.chunks(list(base),100):
            rows.extend(db.execute("SELECT current_institution_id::text id,count(*) n FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' GROUP BY current_institution_id",(part,)).fetchall())
    d.save(RUN/'local-counts.json',rows)
    for row in sorted(rows,key=lambda x:-x['n']):
        if row['n']>1:print(row['n'],base[row['id']]['name'],flush=True)
    found=[]
    for path in sorted((ROOT/'docs/research/museum-expansion-20261006/native').glob('**/*plan.json.gz')):
        plan=d.load(path)
        if not isinstance(plan,dict):continue
        for row in plan.get('records',[]):
            iid=row.get('institution_id') or row.get('museum',{}).get('id')
            if iid in base:found.append(dict(plan_path=str(path.relative_to(ROOT)),plan_sha256=d.sha(path.read_bytes()),record=row))
    d.save(RUN/'local-research-candidates.json.gz',found)
    print('Retained reviewed plan candidates',len(found),flush=True)
    for path,n in collections.Counter(x['plan_path'] for x in found).items():print(n,path,flush=True)


def backup_receipt():
    raw=subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--limit=5','--format=json'],text=True)
    items=json.loads(raw)
    recent=next(x for x in items if x['status']=='SUCCESSFUL' and x['startTime'].startswith('2026-10-08'))
    value=dict(at=d.now(),production=recent,scope='Production only. Reuse completed Cloud SQL recovery point, with exact locked transaction preimages for this pass. No local database writes.')
    d.save(RUN/'backups.json',value)
    d.save(RUN/'links/wikiart-reviewed/backups.json',value)
    print('Successful Cloud SQL recovery point',recent['id'],recent['startTime'],flush=True)


def reviewed_source_records():
    inputs=d.load(RUN/'local-research-candidates.json.gz')
    base={x['institution']['id']:x['institution'] for x in d.load(RUN/'baseline.json.gz')['selected']}
    plans={}
    for item in inputs:
        path=item['plan_path']
        if path in plans:continue
        wave='fourteenth' if 'fourteenth' in path else 'thirteenth'
        s=importlib.util.spec_from_file_location('local_review_'+wave,ROOT/('ops/museum-expansion-france-'+wave+'-apply-20261008.py'))
        mod=importlib.util.module_from_spec(s);s.loader.exec_module(mod)
        plan,digest=mod.validate_plan()
        assert digest==item['plan_sha256']
        receipt=d.load(ROOT/path.replace('-plan.json.gz','-applied.json'))
        assert receipt['plan_sha256']==digest
        plans[path]=(plan,digest)
        print('Verified immutable source plan',wave,len(plan['records']),flush=True)
    out=[]
    for item in inputs:
        row=item['record'];plan,digest=plans[item['plan_path']]
        assert row in plan['records']
        f=row['facts'];dec=row['decision'];ref=dec['source_reference'];p=ROOT/ref['path']
        assert d.sha(p.read_bytes())==ref['sha256']
        capture=d.load(p);rc=dict(capture['receipt'],body_path=capture['body_path'])
        body=gzip.decompress((ROOT/capture['body_path']).read_bytes())
        assert d.sha(body)==rc['sha256'] and rc['status']==200
        assert next(v for v in json.loads(body)['data'] if v['Reference']==f['source_id'])==f['source_fields']
        assert dec['state']=='approved_review_only_addition' and dec['confidence']>=.8
        facts=dict(title=f['title'],creator_label=f['creator_label'],first=f['first'],last=f['last'],date_precision=f['date_precision'],date_display=f['date_display'],work_type=f['work_type'],object_form=f['object_form'],medium=f['medium'],dimensions=f['dimensions_text'],accession=f['inventory'],source_url=f['source_url'],holding_basis=dec['basis']+' '+dec['limitation'])
        out.append(dict(artwork_id=row['artwork_id'],slug=row['slug'],source_record_id=f['source_id'],museum=base[row['institution_id']],facts=facts,provider='joconde-reviewed',origin='reviewed_local_source_plan',alternate_native_urls=f['native_page_urls']+[f['source_fields']['Lien_site_associe']] if f['source_fields'].get('Lien_site_associe') else f['native_page_urls'],source_receipt=rc,body_path=capture['body_path'],raw_source_record=dict(source_fields=f['source_fields'],editorial_decision={k:dec[k] for k in ['state','confidence','basis','derived_fields','limitation']}),lineage=dict(plan_path=item['plan_path'],plan_sha256=digest,original_artwork_id=row['artwork_id'])))
    return out


def configure_additions():
    d.OP='museums-exactly-one-20261008-reviewed-french'
    d.RUN=RUN/'additions'
    d.BACKUP=Path.home()/'Library/Application Support/Artline/backups/museums-exactly-one-20261008/additions'
    d.TARGET_COUNT=200;d.TARGET_FIELD='linked'
    d.SOURCE_NAME='Joconde national catalogue: individually reviewed additions to production museums with one artwork, 8 October 2026'
    d.SOURCE_BASE_URL='https://pop.culture.gouv.fr'
    d.DEFAULT_CONFIDENCE=.9
    d.CONFIDENCE_BASIS='Individually reviewed official object, physical unit, inventory, creation and museum connection, with immutable source decisions retained. Fresh production identity checks; editorial assessment, not calibrated probability.'
    d.scheme=lambda row:'joconde-object'
    validated={row['artwork_id']:row for row in reviewed_source_records()}
    def check(row,cache):
        original=validated[row['lineage']['original_artwork_id']]
        for k in ['facts','raw_source_record','source_receipt','body_path','lineage','source_record_id']:
            assert row[k]==original[k],k
    d.check_body=check
    d.EXPECTED_MUSEUMS=len({r['museum']['id'] for r in validated.values()})
    return list(validated.values())


def additions_plan():
    rows=configure_additions()
    selected={r['museum']['id']:r['museum'] for r in rows}
    d.save(d.RUN/'sample.json',dict(selected=[{k:i[k] for k in ['id','name','slug']} for i in selected.values()],selection='Only museums in the frozen exactly-one production cohort; reuse individually reviewed official source records after fresh production identity checks.'))
    d.save(d.RUN/'source-verified.json.gz',dict(at=d.now(),records=rows,held=[]))
    d.plan()


def additions_apply():
    configure_additions()
    assert d.load(RUN/'backups.json')['production']['status']=='SUCCESSFUL'
    d.apply()


def wikidata_links():
    c=campaign()
    w=c.module('one_wikidata','minimum-100-wikidata-links-20261006.py')
    with d.connect() as db:
        institutions=[x['v'] for x in db.execute("SELECT to_jsonb(i) v FROM institutions i WHERE status<>'archived' AND canonical_institution_id IS NULL")]
    byq=collections.Counter(x.get('wikidata_id') for x in institutions)
    w.c.BASE={iid:x for iid,x in c.BASE.items() if x['institution'].get('wikidata_id') and byq[x['institution']['wikidata_id']]==1}
    w.main(target_count=200,output_root=RUN/'links/wikidata')


def wikidata_phase(phase):
    c=campaign()
    if phase=='link_plan':
        source=d.load(RUN/'links/wikidata/claims.json.gz')
        with d.connect() as db:
            scopes={x['id']:x['scope'] for x in db.execute('SELECT id::text,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope FROM artworks WHERE id=ANY(%s::uuid[])',([x['artwork_id'] for x in source['claims']],))}
        held=[dict(artwork_id=x['artwork_id'],source_url=x['source_url'],reason='Existing artwork creation scope requires separate review: '+scopes[x['artwork_id']]) for x in source['claims'] if scopes[x['artwork_id']]!='eligible']
        reviewed=dict(source,claims=[x for x in source['claims'] if scopes[x['artwork_id']]=='eligible'],held=source['held']+held)
        d.save(RUN/'links/wikidata-reviewed/claims.json.gz',reviewed)
        d.save(RUN/'links/wikidata-reviewed/baseline.json.gz',d.load(RUN/'links/wikidata/baseline.json.gz'))
        d.save(RUN/'links/wikidata-reviewed/backups.json',d.load(RUN/'backups.json'))
        print('Eligible existing Wikidata links',len(reviewed['claims']),'date holds',len(held),flush=True)
    c.link_delivery(phase,'wikidata-reviewed')


def verify_all():
    original=d.load(RUN/'baseline.json.gz')
    base={x['institution']['id']:x for x in original['selected']}
    planpath=RUN/'additions/plan.json.gz';plan=d.load(planpath);receipt=d.load(RUN/'additions/applied.json')
    assert receipt['plan_sha256']==d.sha(planpath.read_bytes())
    records={x['artwork_id']:x for x in plan['records']}
    assert all(x['action']=='create' and x['museum']['id'] in base for x in records.values())
    linkclaims=[]
    for name in ['wikiart-reviewed','wikidata-reviewed']:
        folder=RUN/'links'/name/'delivery/verified'
        proof=d.load(folder/'verification.json');pin=folder/'plan.json.gz';links=d.load(pin)
        assert not proof['errors'] and proof['plan_sha256']==d.sha(pin.read_bytes())
        assert proof['targets']=={'production':len(links['claims'])}
        for row in links['claims']:
            assert row['target_institutions']['production']['id'] in base
        linkclaims.extend(links['claims'])
    linkids=[x['target_ids']['production'] for x in linkclaims]
    assert len(set(linkids))==len(linkids) and set(linkids).isdisjoint(records)
    with d.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        rows=db.execute('SELECT to_jsonb(a) artwork,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,artline_has_selection_evidence(id) evidence FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id',(list(records),)).fetchall()
        assert len(rows)==len(records)
        for item in rows:
            art=item['artwork'];row=records[art['id']];f=row['facts']
            assert art['current_institution_id']==row['museum']['id'] and item['evidence'] and item['scope']=='eligible'
            assert art['status']=='review' and art['published_at'] is None and art['primary_media_id'] is None
            for col,key in [('title','title'),('unlinked_creator_label','creator_label'),('date_display','date_display'),('creation_year_start','first'),('creation_year_end','last'),('date_precision','date_precision'),('accession_number','accession'),('medium_text','medium'),('dimensions_text','dimensions'),('work_type','work_type'),('object_form','object_form')]:
                assert art[col]==f.get(key),(art['id'],col)
        citations=db.execute("SELECT entity_id::text,source_record_id,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND field_name='museum_source_metadata_and_holding'",(list(records),)).fetchall()
        assert len(citations)==len(records)
        for cit in citations:
            row=records[cit['entity_id']];ev=json.loads(cit['evidence_note'])
            assert cit['source_url']==row['facts']['source_url'] and cit['source_record_id']==row['source_record_id'] and ev['plan_sha256']==receipt['plan_sha256']
            assert ev['raw_source_record']==row['raw_source_record'] and ev['editorial_confidence']==.9
        assertions=db.execute('SELECT artwork_id::text,institution_id::text,claim_type,review_state,display_state,superseded_by FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[])',(list(records),)).fetchall()
        assert len(assertions)==len(records)
        for a in assertions:
            assert a['institution_id']==records[a['artwork_id']]['museum']['id'] and a['claim_type']=='holding' and a['review_state']=='accepted' and a['display_state'] is None and a['superseded_by'] is None
        currentlinks={x['id']:x['current_institution_id'] for x in db.execute('SELECT id::text,current_institution_id::text FROM artworks WHERE id=ANY(%s::uuid[])',(linkids,))}
        assert all(currentlinks[x['target_ids']['production']]==x['target_institutions']['production']['id'] for x in linkclaims)
        counts={}
        for part in d.chunks(list(base),100):
            counts.update({x['id']:x for x in db.execute("SELECT i.id::text,i.status,i.canonical_institution_id::text,count(a.id) linked,count(a.id) FILTER(WHERE artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible') eligible,count(a.primary_media_id) images FROM institutions i LEFT JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived' WHERE i.id=ANY(%s::uuid[]) GROUP BY i.id",(part,))})
    added=collections.Counter(x['museum']['id'] for x in records.values())
    linked=collections.Counter(x['target_institutions']['production']['id'] for x in linkclaims)
    museums=[]
    for iid,x in base.items():
        now=counts[iid];n=added[iid]+linked[iid]
        assert x['counts']['linked']==1
        if n:assert now['linked']>=1+n
        museums.append(dict(id=iid,name=x['institution']['name'],slug=x['institution']['slug'],before=1,added=added[iid],linked_existing=linked[iid],after=now['linked'],eligible=now['eligible'],images=now['images'],outside_this_pass_delta=now['linked']-1-n,outcome='expanded_by_this_pass' if n else 'no_approved_change_in_this_pass',authority_status=now['status'],canonical_institution_id=now['canonical_institution_id']))
    summary=dict(at=d.now(),target='production',baseline_museums=len(base),museums_expanded=sum(bool(x['added']+x['linked_existing']) for x in museums),new_artworks=len(records),existing_artworks_linked=len(linkclaims),verified_artworks=len(records)+len(linkclaims),museums_still_exactly_one=sum(x['after']==1 for x in museums),unexpanded_by_this_pass=sum(not(x['added']+x['linked_existing']) for x in museums),new_publications=0,new_images=0,new_display_claims=0,local_database_writes=0,additions_plan_sha256=receipt['plan_sha256'],museums=museums,limitations='Counts include review records. Other jobs may change the catalogue; outside_this_pass_delta is reported separately. Unexpanded museums need further source/identity research; source-pass exhaustion does not establish that they have no eligible works.')
    d.save(RUN/'verification.json',summary)
    with (RUN/'museum-results.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(museums[0]));writer.writeheader();writer.writerows(museums)
    artworks=[dict(artwork_id=aid,museum=row['museum']['name'],title=row['facts']['title'],action='create',source_url=row['facts']['source_url'],confidence=row['editorial_confidence']) for aid,row in records.items()]
    artworks.extend(dict(artwork_id=x['target_ids']['production'],museum=x['target_institutions']['production']['name'],title=x['title'],action='link',source_url=x['source_url'],confidence=x.get('object_evidence',{}).get('editorial_confidence')) for x in linkclaims)
    with (RUN/'artwork-results.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(artworks[0]));writer.writeheader();writer.writerows(artworks)
    md='# Exactly-one-artwork museums: production update\n\n'
    md+=f"Frozen selection: {original['at']}. {len(base)} active canonical museum records had exactly one non-archived linked artwork, including review records. Verified {summary['at']}: **{len(records)} new artworks and {len(linkclaims)} existing-artwork links across {summary['museums_expanded']} museums**. New artworks remain in review.\n\n"
    md+='[Every museum and its before/after count](museum-results.csv) · [Every added/linked artwork and source](artwork-results.csv) · [Independent production verification](verification.json).\n\n'
    md+='Additions reuse individually reviewed official Joconde object evidence captured on 8 October, with full immutable source-plan verification and fresh production identity checks. The source museum, physical unit, creator qualifications, literal dates, derived fields, inventory, materials and source labels are retained. The original source retrieval date is not replaced by the transfer date. Existing links use exact WikiArt object IDs/titles/creators and referenced Wikidata object/creator/museum identities. Confidence is editorial (0.90 additions, 0.95 WikiArt, 0.85 Wikidata), not calibrated probability; underlying Wikidata references were not independently opened.\n\n'
    md+='The 51 French addition holds require production title/version reconciliation. Five WikiArt leads remain held: three fresco details, one portrait version and one obsolete Palazzo Zevallos venue. The official [Gallerie d’Italia Naples page](https://gallerieditalia.com/en/naples/) documents continuation at the new venue after 2022. Twenty-two Wikidata link leads have unresolved or post-cutoff creation scope. The other source-level holds remain in their original claim files. Existing catalogue metadata, artist links, images and publication state were verified preserved for applied links. No current-display assertions or local database writes.\n\n'
    md+=f"This pass expanded {summary['museums_expanded']} of the {len(base)} selected museums. {summary['unexpanded_by_this_pass']} received no approved change in this pass and still need research. At verification, {summary['museums_still_exactly_one']} remained at exactly one artwork. Concurrent changes are explicit in the CSV and are excluded from this pass's delivery totals.\n\n"
    md+='Recovery: completed Cloud SQL backup '+str(d.load(RUN/'backups.json')['production']['id'])+'; exact preimages under `~/Library/Application Support/Artline/backups/museums-exactly-one-20261008/`. Application code, deployment, publication and images were not part of this update.\n\n'
    md+='| Museum | Before | Added | Linked | After |\n|---|---:|---:|---:|---:|\n'
    for x in sorted(museums,key=lambda v:(-(v['added']+v['linked_existing']),v['name'])):
        if x['added']+x['linked_existing']:md+=f"| {x['name'].replace('|','/')} | 1 | {x['added']} | {x['linked_existing']} | {x['after']} |\n"
    (RUN/'README.md').write_text(md)
    print(json.dumps({k:v for k,v in summary.items() if k!='museums'}),flush=True)


def link_phase(phase):
    c=campaign()
    if phase=='link_plan':
        source=d.load(RUN/'links/wikiart/claims.json.gz')
        held=[];approved=[]
        for row in source['claims']:
            reason=None
            if row['institution']['name']=='Palazzo Zevallos Stigliano':
                reason='Historical venue label: official Gallerie d’Italia documents relocation from Palazzo Zevallos to Via Toledo 177 in 2022. https://gallerieditalia.com/en/naples/; checked 2026-10-08.'
            elif row['title']=='Portrait of Giovanna Tornabuoni':
                reason='Named sitter has multiple portrait versions; Tokyo Fuji assignment needs exact-version comparison with the Thyssen portrait. Hold until native Fuji object identity is established.'
            elif row['institution']['name']=='Casa Giorgione, Castelfranco Veneto, Italy':
                reason='Fresco detail/component identities need review before attaching individual artwork records as museum holdings.'
            if reason:held.append(dict(artwork_id=row['artwork_id'],reason=reason,source_url=row['source_url']))
            else:approved.append(row)
        reviewed=dict(source,claims=approved,held=source['held']+held,editorial_review_at=d.now())
        d.save(RUN/'links/wikiart-reviewed/claims.json.gz',reviewed)
        d.save(RUN/'links/wikiart-reviewed/baseline.json.gz',d.load(RUN/'links/wikiart/baseline.json.gz'))
        print('Editorially selected links',len(approved),'held',len(held),flush=True)
    c.link_delivery(phase,'wikiart-reviewed')


def baseline():
    dest = RUN / 'baseline.json.gz'
    if dest.exists():
        value = d.load(dest)
    else:
        with d.connect() as db, db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            museums = [x['row'] for x in db.execute("SELECT to_jsonb(i) row FROM institutions i WHERE kind='museum' AND status<>'archived' AND canonical_institution_id IS NULL ORDER BY name,id")]
            counts = {}
            for part in d.chunks([x['id'] for x in museums], 100):
                counts.update({x['id']: x for x in db.execute("SELECT current_institution_id::text id,count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible,count(primary_media_id) images FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived' GROUP BY current_institution_id", (part,))})
            selected = [dict(institution=x, counts=counts[x['id']]) for x in museums if counts.get(x['id'], {}).get('linked') == 1]
            ids = [x['institution']['id'] for x in selected]
            works = [x['row'] for x in db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE current_institution_id=ANY(%s::uuid[]) AND status<>\'archived\' ORDER BY id', (ids,))]
            assertions = [x['row'] for x in db.execute("SELECT to_jsonb(h) row FROM artwork_location_assertions h WHERE institution_id=ANY(%s::uuid[]) AND superseded_by IS NULL ORDER BY institution_id,artwork_id,id", (ids,))]
            value = dict(at=d.now(), target='production', selection='Active canonical museums with exactly one non-archived linked artwork, including review records. Image, date eligibility and public visibility counts are separate.', selected=selected, original_artworks=works, existing_assertions=assertions)
        d.save(dest, value)
        RUN.mkdir(parents=True, exist_ok=True)
        with (RUN / 'selected-museums.csv').open('x', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['id','name','slug','wikidata_id','linked','eligible','images'])
            writer.writeheader()
            for x in selected:
                writer.writerow(dict(**{k:x['institution'][k] for k in ['id','name','slug','wikidata_id']}, **{k:x['counts'][k] for k in ['linked','eligible','images']}))
    print(json.dumps(dict(selected=len(value['selected']), with_wikidata=sum(bool(x['institution'].get('wikidata_id')) for x in value['selected']), assertions=len(value['existing_assertions']))), flush=True)
    for x in value['selected']:
        i=x['institution']
        print(i['id'], i['name'], i.get('wikidata_id'), flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase', choices=['baseline','wikiart_links','wikidata_links','joconde','local_candidates','backup_receipt','additions_plan','additions_apply','link_plan','link_apply','link_verify','wikidata_plan','wikidata_apply','wikidata_verify','verify_all'])
    args=parser.parse_args()
    if args.phase in ['wikidata_plan','wikidata_apply','wikidata_verify']:wikidata_phase(args.phase.replace('wikidata_','link_'))
    elif args.phase.startswith('link_'):link_phase(args.phase)
    else:globals()[args.phase]()
