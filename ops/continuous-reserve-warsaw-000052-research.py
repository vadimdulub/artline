#!/usr/bin/env python3
"""Batch 52 evidence audit and bounded, resumable Warsaw metadata capture.

No database connector, storage upload, supervisor or image downloader is used.
Historical plans and UUIDs are read only. Re-running verifies saved captures.
"""
import csv
import datetime
import fcntl
import gzip
import hashlib
import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'docs/research/continuous-production-20261011/batches/000052'
R = Path.home() / 'Library/Application Support/Artline/continuous-research/batches/000052'
CAP = Path.home() / 'Library/Application Support/Artline/source-metadata/continuous-production-20261011/batches/000052'
FRENCH = ROOT / 'docs/research/french-printmaking-20261011'
RESERVE = ROOT / 'docs/research/printmaking-continuation-20261011/french-reserve'
PREVIOUS = E.parent / '000049'
REGISTRY = Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')
QUEUE = E.parent.parent / 'source-queue.json'


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    path = Path(path)
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


def save(path, value):
    path = Path(path)
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data, 'Immutable evidence differs: ' + str(path)
    else:
        with path.open('xb') as f:
            f.write(data)


def ref(path):
    path = Path(path)
    return dict(path=str(path), sha256=sha(path.read_bytes()), bytes=path.stat().st_size)


def inputs():
    if (E / 'required-input-reconciliation.json').exists():
        return
    files = [ROOT/'AGENTS.md', REGISTRY, ROOT/'docs/ARTLINE_IMAGE_USE.md',
             ROOT/'docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md', ROOT/'docs/LOCAL_DATA_LOCATIONS.md',
             E.parent.parent/'CHECKPOINT.json', QUEUE,
             E.parent/'000051/CHECKPOINT.json', E.parent/'000051/source-access-holds.json',
             E.parent/'000050/source-access-holds.json', PREVIOUS/'source-access-holds.json',
             ROOT/'docs/research/printmaking-continuation-20261011/README.md',
             ROOT/'docs/research/french-printmaking-20261011/README.md',
             ROOT/'docs/research/creators-deep-continuation-20261011/source-registry-review.json',
             ROOT/'ops/india-300-delivery-20261011.py', ROOT/'ops/continuous-french-reserve-batch-000001.py',
             ROOT/'ops/printmaking-continuation-20261011.py', ROOT/'ops/continuous-warsaw-batch-000048.py']
    registry = list(csv.DictReader(io.StringIO(REGISTRY.read_text())))
    queue = load(QUEUE)
    assert len(registry) == len(queue['sources']) == 111
    assert {x['source_id'] for x in registry} == {x['source_id'] for x in queue['sources']}
    save(CAP/'original-111-source-registry.json', registry)
    save(E/'source-queue-before.json', queue)
    save(E/'required-input-reconciliation.json', dict(at=now(), inputs=[ref(p) for p in files],
         registry_rows=111, complete_original_registry_used=True, supplementary_review_is_not_registry=True,
         precedence='Current user authorizes production only; local catalogue read-only. Bound worker executes one batch and does not modify or launch supervisor.',
         local_catalogue_connections=0, source_captures_directory=str(CAP)))
    inherited=load(E.parent/'000051/prior-receipt-reconciliation-verification.json')
    verified=[]
    for item in inherited['immutable_artifacts']:
        assert sha(Path(item['path']).read_bytes()) == item['sha256']
        verified.append(dict(item, verified=True))
    receipt=load(PREVIOUS/'batch-verification-receipt.json')
    assert sha((PREVIOUS/'batch-verification-receipt.json').read_bytes()) == inherited['receipt_sha256']
    production=load(PREVIOUS/'independent-production-verification.json')
    assert production['selection_sha256'] == receipt['selection_sha256']
    assert production['visual_review_sha256'] == receipt['visual_review_sha256']
    assert production['preimage_sha256'] == verified[0]['sha256']
    assert {r['id'] for r in production['rows']} == set(receipt['production_ids'])
    save(E/'prior-receipt-reconciliation-verification.json',dict(at=now(), prior_batch=49,
         receipt=ref(PREVIOUS/'batch-verification-receipt.json'), immutable_artifacts=verified,
         previous_delivery_attribution_checksums_match=True,
         saved_production_and_audit_evidence=[ref(PREVIOUS/f) for f in ['independent-production-verification.json','independent-audit-history-verification.json','independent-storage-verification.json','independent-resume-verification.json']],
         fresh_live_production_reconciliation=False, ambiguous_writes_replayed=False,
         no_prior_delivery_counted_in_this_batch=True,
         limitation='Authentication prevents live production citation, rights and drift checks. Reconcile live before any future write.'))


def reserve():
    if (E/'independent-reserve-evidence-verification.json').exists():
        return
    initial=load(FRENCH/'delivery-plan.json.gz')
    topup=load(FRENCH/'scope-topup/delivery-plan.json.gz')
    plan=load(RESERVE/'delivery-plan.json.gz')
    pin=load(RESERVE/'delivery-plan-pin.json')['sha256']
    assert sha((RESERVE/'delivery-plan.json.gz').read_bytes()) == pin
    ids=set(initial['eligible_reserve'])-{r['artwork_id'] for r in topup['rows']}
    assert len(ids)==188 and ids=={r['artwork_id'] for r in plan['rows']}
    prior=load(PREVIOUS/'french-reserve-live-reconciliation.json')
    assert prior['plan_sha256']==pin and set(prior['live_rows'])==ids and prior['unimported']==0
    citations={c['entity_id']:c for c in prior['source_citations']}
    assert set(citations)==ids and all(c['plan_sha256']==pin for c in citations.values())
    production=load(RESERVE/'production-verification.json')
    assert production['plan_sha256']==pin and production['new_artworks']==188 and not production['errors']
    held=dict(initial['held'])
    for p in (FRENCH/'cross-sheet-review').glob('*.json'):
        held.update(load(p).get('held',{}))
    records=[]
    sheet_hashes={}
    for r in plan['rows']:
        aid=r['artwork_id']; im=plan['images'][aid]
        source=ROOT/r['source_record_reference']
        assert sha(source.read_bytes())==r['source_record_sha256']
        obj=load(source)
        for key,rc_key in [('raw','receipt'),('manifest','manifest_receipt')]:
            rc=obj[rc_key]; body=gzip.decompress((ROOT/rc['body_path']).read_bytes())
            assert rc['status']==200 and sha(body)==rc['sha256'] and json.loads(body)==obj[key]
        assert obj['native_id']==r['native_id'] and obj['manifest']['id']==r['manifest_receipt']['url']
        assert any(x['id']==r['source_url'] for x in obj['manifest']['homepage'])
        visual=r['continuation_visual_evidence']; decision_path=ROOT/visual['decision_reference']
        assert sha(decision_path.read_bytes())==visual['decision_sha256']
        decision=load(decision_path); sheet_path=Path(str(decision_path).replace('/visual-decisions/','/visual-sheets/'))
        sheet=load(sheet_path); filename=sheet['sheet']
        if filename not in sheet_hashes: sheet_hashes[filename]=sha(Path(filename).read_bytes())
        assert sheet_hashes[filename]==decision['sheet_sha256']
        entry=next(x for x in sheet['images'] if x['artwork_id']==aid)
        assert aid in decision['approved'] and entry['sha256']==visual['image_sha256']==im['sha256']
        data=Path(im['local_path']).read_bytes()
        assert len(data)==im['bytes']<=100000 and sha(data)==im['sha256']
        with Image.open(io.BytesIO(data)) as image:
            image.load(); assert image.size==(im['width'],im['height'])
        assert abs(im['width']/im['height']-im['original_dimensions'][0]/im['original_dimensions'][1])<.01
        before=prior['live_rows'][aid]; art=before['artwork']
        assert citations[aid]['source_record_id']==r['native_id']
        assert art['accession_number']==r['accession_number'] and art['primary_media_id']==im['media_id']
        assert any(x['media_id']==im['media_id'] for x in before['attachments'])
        assert any(x['artist_id']==r['artist_id'] for x in before['creators'])
        assert art['status']=='review' and all(art[k]==v for k,v in r['date'].items())
        records.append(dict(artwork_id=aid,source_id=r['native_id'],accession=r['accession_number'],
            source_record=ref(source), source_capture_sha256=r['receipt']['sha256'],
            manifest_sha256=r['manifest_receipt']['sha256'], derivative_sha256=im['sha256'],
            bytes=im['bytes'],complete_decode=True,local_path=im['local_path'],
            prior_visual_decision=ref(decision_path),prior_sheet_sha256=decision['sheet_sha256'],
            prior_live_artwork_id=art['id'],prior_primary_media_id=art['primary_media_id'],
            prior_citation_plan_sha256=citations[aid]['plan_sha256'],
            date=r['date'],hold=held.get(aid),
            outcome='Previously delivered; excluded from new selection and batch increments'))
    save(E/'independent-reserve-evidence-verification.json',dict(at=now(),records=records,
        inspected=188,source_captures_checksum_verified=376,derivatives_fully_decoded=188,
        prior_visual_evidence_checksum_verified=188,new_selection_count=0,
        prior_live_reconciliation=ref(PREVIOUS/'french-reserve-live-reconciliation.json'),
        prior_live_checked_at=prior['at'],fresh_live_reconciliation=False,
        prior_campaign_plan_sha256=pin,prior_delivery_excluded=True,
        immutable_plans=[ref(p) for p in [FRENCH/'delivery-plan.json.gz',FRENCH/'scope-topup/delivery-plan.json.gz',RESERVE/'delivery-plan.json.gz']],
        physical_date_review_ids=['80082','80437','81054'],
        scope='Saved prior live evidence, original captures, files and visual decisions independently checked now. This is not a fresh production query. No supplement or historical plan mutation.'))
    print('Reserve evidence verified: 188 previously delivered; 0 selected.',flush=True)


def capture(key,url):
    receipt=CAP/(key+'.receipt.json'); body_path=CAP/(key+'.body.gz')
    if receipt.exists():
        rc=load(receipt); body=gzip.decompress(body_path.read_bytes())
        assert rc['url']==url and sha(body)==rc['sha256']
        return rc,body
    assert not body_path.exists(), 'Unreceipted capture requires recovery review'
    request=urllib.request.Request(url,headers={'User-Agent':'Artline bounded museum research/1.0','Accept':'application/json'})
    at=now()
    try:
        with urllib.request.urlopen(request,timeout=25) as response:
            data=response.read(2_000_001); assert len(data)<=2_000_000
            status=response.status; final=response.url; retry=response.headers.get('Retry-After')
    except urllib.error.HTTPError as error:
        data=error.read(100_000); status=error.code; final=error.url; retry=error.headers.get('Retry-After')
    except (urllib.error.URLError,TimeoutError):
        data=b'';status=None;final=url;retry=None
    CAP.mkdir(parents=True,exist_ok=True)
    with body_path.open('xb') as f:f.write(gzip.compress(data,mtime=0))
    rc=dict(url=url,final_url=final,status=status,retrieved_at=at,sha256=sha(data),bytes=len(data),
            body_path=str(body_path),retry_after=retry,attempts=1,retries=0,image_download=False)
    save(receipt,rc)
    print(key,status,len(data),flush=True)
    return rc,data


def warsaw():
    prior=next(x for x in load(E/'source-queue-before.json')['sources'] if x['source_id']=='national_museum_warsaw')
    assert prior['resume_cursor']['next_page_after_pending']==3
    url='https://cyfrowe-api.mnw.art.pl/api/search/Object/page/3?filter%5Bdepartment%5D%5B%5D=97306&filter%5Bphrase%5D=Ikona&maxPerPage=24'
    rc,body=capture('warsaw-icons-page3',url)
    if rc['status']!=200:
        save(E/'warsaw-access-result.json',dict(receipt=rc,stopped=True));return
    raw=json.loads(body);page=raw['data'];assert raw['status']==200
    assert page['paginatorDetails']['currentPage']==3 and len(page['items'])<=24
    processed=set(prior['resume_cursor']['processed_native_ids']);records=[];skipped=[]
    for item in page['items']:
        oid=str(item['id'])
        if oid in processed:skipped.append(oid);continue
        rc2,body2=capture('object-'+oid,'https://cyfrowe-api.mnw.art.pl/api/object/'+oid)
        if rc2['status']!=200:
            records.append(dict(source_id=oid,receipt=rc2,outcome='access_or_transport_hold'));break
        obj=json.loads(body2);assert obj['status']==200 and str(obj['data']['id'])==oid
        o=obj['data']
        records.append(dict(source_id=oid,source_url='https://cyfrowe.mnw.art.pl/pl/zbiory/'+oid,
            title=o['title'],accession=o['noEvidence'],creators=o['authors'],dates=o['createDates'],
            dimensions=o['dimensionText'],types=o['types'],materials=o['materials'],techniques=o['techniques'],
            owner=o['owner'],historical_numbers=o['extraNumPatterns'],copyrights=o['copyrights'],
            source_image_metadata=o['image'],receipt=rc2,
            outcome='Captured; editorial review and global live reconciliation required',
            selected_for_import=False,images_downloaded=0))
    if not (E/'warsaw-discovery.json').exists():
        save(E/'warsaw-discovery.json',dict(at=now(),source_id='national_museum_warsaw',page_receipt=rc,
            paginator=page['paginatorDetails'],records=records,skipped_previously_processed=skipped,
            selected_for_import=0,images_downloaded=0,live_reconciliation=False,
            raw_source_total_not_eligible_count=True,complete_museum_coverage=False))
    else:
        old=load(E/'warsaw-discovery.json');assert old['records']==records
    print('Warsaw captured',len(records),'objects; global reconciliation pending.',flush=True)


if __name__=='__main__':
    R.mkdir(parents=True,exist_ok=True)
    with (R/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        action=sys.argv[1]
        assert action in ['inputs','reserve','warsaw']
        globals()[action]()
