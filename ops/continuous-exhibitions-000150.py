#!/usr/bin/env python3
"""Bounded Moralis 1988 exact-object reconciliation; no supervisor changes."""
import fcntl
import json
import os
import subprocess
import sys
from pathlib import Path

import requests
from PIL import Image
from psycopg.types.json import Jsonb
import exhibitions_common as c
from historical_exhibitions_nga_histories_20261012 import normal

E = c.ROOT / 'docs/research/continuous-exhibitions-20261013/batches/000150'
R = Path.home() / 'Library/Application Support/Artline/continuous-exhibition-research/batches/000150'
D = Path.home() / 'Library/Application Support/Artline/source-metadata/continuous-exhibitions-20261013/000150'
B = Path.home() / 'Library/Application Support/Artline/backups/continuous-exhibitions-20261013/000150'
Q = E.parents[1] / 'source-queue.json'
OP = 'continuous-exhibitions-20261013-batch-000150'
ACTOR = 'local-european-research'
INSTANCE = 'artline-508319:europe-west1:artline-postgres'
EVENT = 'de830321-95f7-5793-8176-01976b549e5b'
OCC = '3f0baf88-64ed-590f-ba3c-77b340774d62'
ARTIST = '3b5fbd54-cae2-5e50-a0b3-f70eabf743cd'
SID = c.uid(OP + '/source/printed263-266')
API = 'https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/'
SPECS = [
    ('72cbb9d9-d22e-575f-8e3a-9222e19d0724', 'Π. 7704', 'Επιτύμβια σύνθεση Γ’', 'Funerary Composition III', '1958–1963', 'Oil on canvas', '150 × 150 cm', '43', 263, '57, 66',
     'Square composition with frontal standing woman holding a draped cloth above a reclining nude; blue central bodice, brown architectural background and round panels. Same distinctive hand, cloth and leg contours. Museum range 1958–1963 retained alongside unchanged main-catalogue year 1963.'),
    ('c2c56c00-f1c1-5eee-bda9-fbfa7c725724', 'Π. 7698', 'Ανάμνηση', 'Memory', '1963', 'Vinavyl glue on canvas', '63 × 81 cm', '49', 264, '66',
     'Horizontal dark composition with pale standing figure at left, vertical yellow line, pale horizontal panel at top right and small shell-like shape at lower right. Existing image from the separate artwork programme is reused, not counted as a new asset.'),
    ('9ea7dd39-9b8f-5c37-b48b-19dca857206a', 'Π. 7699', 'Επιτύμβια Σύνθεση Δ’', 'Funerary Composition IV', '1963', 'Vinavyl glue on canvas', '73 × 73 cm', '44', 265, '66',
     'Abstract frontal figure holding white cloth over reclining pale nude; blue bodice with two pale circles, divided oval face, white structural lines and right ochre rectangle. Distinct from V by cloth contours, face and divided lower rail. Catalogue 73 × 73 cm versus reproduction 550 × 600 pixel aspect retained as an unresolved dimension/framing discrepancy; identity secure, no image delivered.'),
    ('116c5d3b-ceb0-5d6f-9ba2-40ddcd5139fc', 'Π. 7700', 'Επιτύμβια Σύνθεση Ε’', 'Funerary Composition V', '1963', 'Vinavyl glue on canvas', '79 × 73 cm', '45', 265, '66',
     'Pale reclining nude with ochre necklace, diagonal white cloth held above, three round head/disc forms at top and bowl-like lower-right form. Distinct from IV by extended diagonal cloth, circle forms and necklace. Current WikiArt page confirms updated image URL; narrow source border preserved for research.'),
    ('fe1f45f8-9d53-5d94-993a-846407cb5061', 'Π. 7701', 'Επιτύμβια Σύνθεση Ζ’', 'Funerary Composition VII', '1963', 'Vinavyl glue on canvas', '79 × 73 cm', '46', 266, '66',
     'Single pale reclining headless-form nude with bent knees on dark ground, large pale oval within square at upper left, paired curved shapes at upper right and white rectangular furniture outlines. Same exact composition as accession-captioned museum reproduction.'),
    ('b52d94f6-9101-51ca-b189-ca21e94fe3ab', 'Π. 7697', 'Καλοκαίρι', 'Summer', '1968', 'Vinavyl glue on canvas', '106 × 70 cm', '67', 266, '66',
     'Tall black-and-white composition of two pale standing female forms with differently drawn hair and heads, geometric background and raised left arm; title, date and precise figure contours agree with accession-captioned catalogue image.')
]


def save(path, data):
    c.save(path, data)


def target(db):
    command = '/tmp/artline-cloud-sql-proxy --address 127.0.0.1 --port 55519 --gcloud-auth ' + INSTANCE
    ps = subprocess.check_output(['ps', '-axo', 'command'], text=True).splitlines()
    assert command in [x.strip() for x in ps]
    assert (db.info.host, db.info.port, db.info.dbname) == ('127.0.0.1', 55519, 'artline')
    t = db.execute('select current_database() database,current_user role').fetchone()
    assert t == dict(database='artline', role='artline_app')
    return dict(at=c.now(), instance=INSTANCE, port=55519, **t)


def snapshot(db, ids):
    result = {}
    for table in ['exhibitions', 'exhibition_entries', 'exhibition_occurrences', 'exhibition_participants', 'exhibition_source_records']:
        col = 'id' if table == 'exhibitions' else 'exhibition_id'
        result[table] = normal(db.execute('select * from '+table+' where '+col+'=%s order by id', (EVENT,)).fetchall())
    result['artworks'] = normal(db.execute('select * from artworks where id=any(%s::uuid[]) order by id', (ids,)).fetchall())
    result['artwork_artists'] = normal(db.execute('select * from artwork_artists where artwork_id=any(%s::uuid[]) order by artwork_id,artist_id', (ids,)).fetchall())
    mids = [w['primary_media_id'] for w in result['artworks'] if w['primary_media_id']]
    result['media_assets'] = normal(db.execute('select * from media_assets where id=any(%s::uuid[]) order by id', (mids,)).fetchall())
    for table in ['citations', 'external_identifiers']:
        result[table] = normal(db.execute("select * from "+table+" where entity_type='artwork' and entity_id=any(%s::uuid[]) order by id", (ids,)).fetchall())
    return result


def prepare():
    prev = c.load(E.parent / '000146/source-capture-verification.json')['reused_capture']
    assert c.sha(Path(prev['body_path']).read_bytes()) == prev['sha256']
    images = c.load(E/'identity-image-retrieval-verification.json')['images']
    assert len(images) == 6
    for item in images:
        assert c.sha(Path(item['path']).read_bytes()) == item['receipt']['sha256']
    objects = []
    for spec in SPECS:
        x = dict(zip(['artwork_id','accession','title','english_title','date_label','medium','dimensions','number','page','reference_pages','visual_basis'], spec))
        x['id'] = c.uid(OP+'/entry/'+x['accession'])
        x['citation'] = 'Γιάννης Μόραλης, ΕΠΜΑΣ, 1988, αρ. κατ. '+x['number']+', σ. '+x['reference_pages']+'.'
        x['pdf_page'] = x['page']+1
        x['source_artwork_id'] = 'national-gallery-athens/accession/'+x['accession']
        objects.append(x)
    with c.connect() as db:
        t = target(db)
        pre = snapshot(db, [x['artwork_id'] for x in objects])
        assert len(pre['exhibition_entries']) == 18
        assert pre['exhibitions'][0]['checklist_state'] == 'partial'
        assert pre['exhibitions'][0]['status'] == 'review'
        assert any(x['id']==OCC for x in pre['exhibition_occurrences'])
        assert any(x['artist_id']==ARTIST for x in pre['exhibition_participants'])
        assert len(pre['artworks']) == 6
        assert {str(x['artwork_id']) for x in pre['artwork_artists'] if str(x['artist_id'])==ARTIST} == {x['artwork_id'] for x in objects}
        collisions = []
        for obj in objects:
            rows = db.execute('select id,artwork_id,catalogue_number,source_artwork_id from exhibition_entries where exhibition_id=%s and (artwork_id=%s or catalogue_number=%s or source_artwork_id=%s)',
                              (EVENT,obj['artwork_id'],obj['number'],obj['source_artwork_id'])).fetchall()
            collisions.append(dict(artwork_id=obj['artwork_id'],rows=normal(rows)))
            assert not rows
            w = next(w for w in pre['artworks'] if w['id']==obj['artwork_id'])
            assert w['creation_year_end'] <= 1970 and w['status']=='review'
            cit = next(x for x in pre['citations'] if x['entity_id']==obj['artwork_id'])
            meta = json.loads(cit['evidence_note'])['metadata']
            obj['wikiart_native_id'] = str(meta['contentId'])
            obj['existing_citation_id'] = cit['id']
            obj['existing_source_page_url'] = cit['source_url']
            obj['collection_label_in_2011'] = 'Donated by the artist'
        prior_ops = db.execute('select id from audit_log where request_id=%s',(OP,)).fetchall()
        assert not prior_ops
    m = pre['media_assets'][0]
    local_image = c.ROOT/'apps/web/public'/m['storage_path'].lstrip('/')
    assert c.sha(local_image.read_bytes()) == m['checksum_sha256']
    with Image.open(local_image) as im:
        im.verify()
    assert local_image.stat().st_size<=100000
    reviewed_files = [D/('moralis-'+str(p)+'.png') for p in range(264,268)] + [D/'candidate-contact-sheet.jpg',local_image,
                      D/'9ea7dd39-9b8f-5c37-b48b-19dca857206a.jpg',D/'116c5d3b-ceb0-5d6f-9ba2-40ddcd5139fc.jpg']
    visual = dict(at=c.now(),reviewer='assistant actual image-tool inspection',
                  files=[dict(path=str(p),sha256=c.sha(p.read_bytes())) for p in reviewed_files],
                  method='Viewed all four full rendered catalogue pages and all six cells of the comparison contact sheet, including the reused Memory derivative. Individually inspected Composition IV for the aspect discrepancy and Composition V for its source border and distinct composition. No unsampled images claimed reviewed.',
                  objects=[dict(artwork_id=x['artwork_id'],accession=x['accession'],basis=x['visual_basis'],editorial_confidence=.99) for x in objects],
                  threshold=.90,confidence_note='Editorial assessment, not calibrated probability.',
                  unresolved_dimensions='Π.7699 physical dimensions 73 × 73 cm do not match reproduction pixel aspect; source facts preserved, no image uploaded.',passed=True)
    save(E/'visual-object-identity-verification.json',visual)
    save(E/'exact-link-duplicate-verification.json',dict(at=c.now(),rows=collisions,existing_entry_count=18,passed=True))
    source_pages = []
    for p in range(264,268):
        text = subprocess.check_output(['pdftotext','-f',str(p),'-l',str(p),'-layout',prev['body_path'],'-'],text=True)
        source_pages.append(dict(pdf_page=p,printed_page=p-1,text=text))
    save(D/'reviewed-source-text.json',source_pages)
    plan = dict(at=c.now(),operation=OP,target=t,event_id=EVENT,occurrence_id=OCC,source_id=SID,
                source=prev,source_native_id=prev['url']+'#artline-excerpt-printed-263-266',
                source_identity_note='URL fragment is an Artline page-range selector, not a provider-assigned identifier.',
                source_publication_year=2011,objects=objects,preimage=pre,comparison_images=images,
                source_pages=source_pages,visual_review_sha256=c.sha((E/'visual-object-identity-verification.json').read_bytes()),
                basis='The official 2011 museum catalogue lists each accession under Exhibitions with an explicit 1988 catalogue number. Distinctive reproduced compositions and existing WikiArt native identities establish the exact versions. Neither general bibliography nor nearby images alone are participation evidence.',
                main_catalogue_changes=False,checklist_complete=False,status='review')
    B.mkdir(parents=True,exist_ok=True);B.chmod(0o700)
    save(E/'immutable-plan.json',plan);save(B/'immutable-plan.json',plan)
    pin = c.sha((E/'immutable-plan.json').read_bytes())
    save(E/'plan-pin.json',dict(sha256=pin,backup=str(B/'immutable-plan.json')))
    save(E/'source-capture-verification.json',dict(at=c.now(),source=prev,checksum_verified=True,reviewed_pdf_pages=list(range(264,268)),
         reviewed_printed_pages=list(range(263,267)),original_1988_checklist_read=False,full_publication_uploaded=False,
         exact_urls_accessions_original_wording_preserved=True,passed=True))
    save(E/'candidate-review-verification.json',dict(at=c.now(),plan_sha256=pin,catalogue_objects_reviewed=8,exact_links_prepared=6,
         held=[dict(accession='Π. 7696',title='Young Woman',year=1962,number='47',printed_page=264,reason='Explicit 1988 citation, but no exact existing main artwork resolved in the canonical creator cohort. Broader authority/native-object reconciliation needed.'),dict(accession='Π. 2702',title='Nude',year=1962,printed_page=264,reason='1988 publication appears only under bibliography; explicit exhibition list omits 1988. No participation inferred.')],
         main_artwork_date_ranges_retained=['Π. 7704: museum 1958–1963; existing catalogue 1963'],
         images_prepared_for_upload=0,existing_public_image_reused=1,unillustrated_links=5,passed=True))
    print('Pinned six exact artwork links',pin)


def audit(db, table, kind, ident, pin):
    row = normal(db.execute('select * from '+table+' where id=%s',(ident,)).fetchone())
    db.execute("insert into audit_log(actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json) values(%s,'continuous_exhibition_insert',%s,%s,%s,%s,%s)",
               (ACTOR,kind,ident,OP,Jsonb(None),Jsonb(dict(record=row,plan_sha256=pin))))


def apply():
    p = c.load(E/'immutable-plan.json');pin=c.load(E/'plan-pin.json')['sha256']
    assert p['operation']==OP and c.sha((E/'immutable-plan.json').read_bytes())==pin==c.sha((B/'immutable-plan.json').read_bytes())
    assert c.sha(Path(p['source']['body_path']).read_bytes())==p['source']['sha256']
    with c.connect(write=True) as db:
        t=target(db)
        db.execute("select set_config('artline.actor_user_id',%s,true)",(ACTOR,))
        db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('select pg_advisory_xact_lock(2026101201)')
        existing=db.execute('select interpretation from exhibition_source_records where id=%s',(SID,)).fetchone()
        if existing:
            assert existing['interpretation']['plan_sha256']==pin and (B/'transaction-preimage.json').exists()
            print('Own previous commit found; verify without replay.');return
        before=snapshot(db,[x['artwork_id'] for x in p['objects']])
        assert before==p['preimage'],'Concurrent change detected; replan instead of overwriting.'
        txid=db.execute('select txid_current() id').fetchone()['id']
        pre=dict(at=c.now(),operation=OP,target=t,plan_sha256=pin,transaction_id=str(txid),rows=before,
                 selected_new_entry_ids=[x['id'] for x in p['objects']],locks=['artline-curated-ingestion',2026101201])
        save(B/'transaction-preimage.json',pre);save(E/'transaction-preimage.json',pre)
        save(E/'production-target-before-write.json',dict(**t,plan_sha256=pin,passed=True))
        ev=dict(operation=OP,plan_sha256=pin,transaction_id=str(txid),checked_at=p['at'],basis=p['basis'],
                source_sha256=p['source']['sha256'],source_publication_year=2011,exhibition_citation_year=1988,
                visual_review_sha256=p['visual_review_sha256'],checklistComplete=False,original_checklist_read=False,
                historicalParticipation=True,holdingClaim=False,currentDisplayClaim=False)
        rc=p['source']
        db.execute('insert into exhibition_source_records(id,exhibition_id,source_key,source_record_id,source_url,retrieved_at,capture_url,capture_sha256,source_payload,interpretation) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                   (SID,EVENT,OP,p['source_native_id'],rc['url'],rc['retrieved_at'],rc['body_path'],rc['sha256'],Jsonb(dict(objects=p['objects'],reviewed_pages=p['source_pages'],identity_note=p['source_identity_note'])),Jsonb(ev)))
        audit(db,'exhibition_source_records','exhibition_source_record',SID,pin)
        for x in p['objects']:
            assert not db.execute('select 1 from exhibition_entries where exhibition_id=%s and (artwork_id=%s or catalogue_number=%s or source_artwork_id=%s)',(EVENT,x['artwork_id'],x['number'],x['source_artwork_id'])).fetchone()
            evidence=dict(**ev,native_accession=x['accession'],printed_page=x['page'],pdf_page=x['pdf_page'],
                          original_exhibition_citation=x['citation'],english_title=x['english_title'],
                          collection_label_in2011=x['collection_label_in_2011'],collection_label_is1988_lender_claim=False,
                          lender_unknown=True,source_url=rc['url'],match_confidence=.99,visual_basis=x['visual_basis'],
                          existing_wikiart_native_id=x['wikiart_native_id'],existing_citation_id=x['existing_citation_id'])
            db.execute("""insert into exhibition_entries(id,exhibition_id,source_record_id,occurrence_id,artwork_id,source_artwork_id,
                catalogue_number,title_label,creator_label,date_label,medium_label,dimensions_label,participation,source_page,evidence,match_basis)
                values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'exhibited',%s,%s,%s)""",
                (x['id'],EVENT,SID,OCC,x['artwork_id'],x['source_artwork_id'],x['number'],x['title'],'Γιάννης Μόραλης',x['date_label'],x['medium'],x['dimensions'],
                 f"2011 printed p. {x['page']} (PDF {x['pdf_page']}); 1988 catalogue p. {x['reference_pages']}, no. {x['number']}",Jsonb(evidence),
                 'Accession-captioned museum exhibition-history entry and explicit 1988 catalogue number, corroborated by exact distinctive composition, creator, title and date/version.'))
            audit(db,'exhibition_entries','exhibition_entry',x['id'],pin)
    save(E/'commit-receipt.json',dict(at=c.now(),operation=OP,plan_sha256=pin,transaction_id=str(txid),independent_verification_pending=True))
    print('Transaction committed; independent verification required.')


def verify():
    p=c.load(E/'immutable-plan.json');pin=c.load(E/'plan-pin.json')['sha256'];pre=c.load(B/'transaction-preimage.json')
    assert c.sha((E/'immutable-plan.json').read_bytes())==pin==pre['plan_sha256']
    ids=[x['id'] for x in p['objects']];aids=[x['artwork_id'] for x in p['objects']]
    assert not {x['id'] for x in pre['rows']['exhibition_entries']}.intersection(ids)
    assert SID not in {x['id'] for x in pre['rows']['exhibition_source_records']}
    with c.connect() as db:
        db.execute('set transaction isolation level repeatable read, read only')
        t=target(db);after=snapshot(db,aids)
        src=next(x for x in after['exhibition_source_records'] if x['id']==SID)
        assert src['source_key']==OP and src['interpretation']['plan_sha256']==pin and src['capture_sha256']==p['source']['sha256']
        entries=[x for x in after['exhibition_entries'] if x['id'] in ids]
        assert len(entries)==6
        for x in p['objects']:
            e=next(e for e in entries if e['id']==x['id'])
            assert (e['artwork_id'],e['exhibition_id'],e['occurrence_id'],e['catalogue_number'],e['source_artwork_id'],e['source_record_id'])==(x['artwork_id'],EVENT,OCC,x['number'],x['source_artwork_id'],SID)
            assert e['evidence']['plan_sha256']==pin and e['evidence']['operation']==OP and e['participation']=='exhibited'
        reduced=dict(after);reduced['exhibition_entries']=[x for x in after['exhibition_entries'] if x['id'] not in ids]
        reduced['exhibition_source_records']=[x for x in after['exhibition_source_records'] if x['id']!=SID]
        assert reduced==pre['rows'],'Prior event relationships or main catalogue data changed.'
        audits=normal(db.execute("select * from audit_log where request_id=%s and action='continuous_exhibition_insert' order by id",(OP,)).fetchall())
        assert len(audits)==7 and all(x['before_json'] is None and x['after_json']['plan_sha256']==pin for x in audits)
    counts=dict(new_exhibitions=0,new_venue_stops=0,new_artists=0,new_catalogue_artworks=0,new_documentary_entries=0,
                new_artist_participation_links=0,new_exact_artwork_links=6,new_images=0,existing_records_enriched=1)
    save(E/'independent-database-verification.json',dict(at=c.now(),target=t,plan_sha256=pin,source=src,entries=entries,audits=audits,
         verified_counts=counts,prior_entries_preserved=18,main_artwork_and_media_records_unchanged=True,
         attribution='Six IDs absent under shared-lock transaction preimage; exact source and entry evidence plus audit history persist this plan checksum and operation. Verified through a new read-only connection; prior/concurrent jobs excluded.',passed=True))
    receipts=[];responses={}
    for suffix in ['', '/entries?limit=100']:
        url=API+'exhibitions/'+EVENT+suffix;r=requests.get(url,timeout=(15,45));r.raise_for_status();responses[suffix]=r.json()
        save(R/('public-detail.json' if not suffix else 'public-entries.json'),r.json())
        receipts.append(dict(url=url,status=r.status_code,sha256=c.sha(r.content)))
    detail=responses[''];items=responses['/entries?limit=100']['items'];selected=[x for x in items if x['id'] in ids]
    assert detail['entryCount']==24 and detail['checklistState']=='partial' and len(selected)==6
    assert any(x['id']==OCC for x in detail['venues'])
    assert any(x['artist_id']==ARTIST for x in detail['participants'])
    assert {x['id']:x['artworkId'] for x in selected}=={x['id']:x['artwork_id'] for x in p['objects']}
    assert sum(bool(x.get('image')) for x in selected)==1
    assets=[]
    for m in after['media_assets']:
        url='https://artlines.org'+m['storage_path'];r=requests.get(url,timeout=(15,45));r.raise_for_status()
        assert c.sha(r.content)==m['checksum_sha256'] and len(r.content)<=100000
        assets.append(dict(url=url,status=r.status_code,bytes=len(r.content),sha256=c.sha(r.content),existing_asset_reused=True))
    save(E/'independent-public-relationship-verification.json',dict(at=c.now(),plan_sha256=pin,receipts=receipts,
         exhibition_id=EVENT,venue_relationship_verified=True,artist_relationship_verified=True,
         exact_artwork_links_verified=6,entry_count_after=24,checklist_state='partial',illustrated_new_links=1,unillustrated_new_links=5,
         assets=assets,new_images=0,passed=True))
    backups=[dict(path=str(B/n),sha256=c.sha((B/n).read_bytes())) for n in ['immutable-plan.json','transaction-preimage.json']]
    assert backups[0]['sha256']==pin and backups[1]['sha256']==c.sha((E/'transaction-preimage.json').read_bytes())
    save(E/'backup-verification.json',dict(at=c.now(),files=backups,restoration_basis='Exact transaction preimages, new IDs and immutable insertion plan; no prior rows modified.',passed=True))
    print(json.dumps(counts))



def finalize():
    p=c.load(E/'immutable-plan.json');pin=c.load(E/'plan-pin.json')['sha256'];v=c.load(E/'independent-database-verification.json')
    assert v['passed'] and c.load(E/'independent-public-relationship-verification.json')['passed']
    next_task='Missing-image batch: inspect the five unillustrated Moralis works just linked in batch150 (catalogue nos.43,44,45,46,67), reusing exact-version visual evidence and current WikiArt source URLs. Recheck live media first to exclude concurrent artwork-programme images. Preserve Composition IV dimension/framing discrepancy and full-frame policy. Metadata continuation resumes at printed p.267 (PDF268), where 1974/1982 works are documentary-only candidates; original 1988 checklist remains partial.'
    evidence=str(E.relative_to(c.ROOT));reviews=c.load(E/'candidate-review-verification.json')
    with open(str(Q)+'.lock','a+') as fh:
        fcntl.flock(fh,fcntl.LOCK_EX)
        before=c.load(Q);after=json.loads(json.dumps(before));changed=[]
        for group in ['sources','supplemental_sources']:
            for i,x in enumerate(after[group]):
                if x['source_id']=='national_gallery_athens':
                    x['research_status']='batch150_six_moralis1988_exact_links_verified';x['last_checked_at']=c.now()
                    cursor=x.setdefault('cursor',{});cursor['next']=next_task;cursor['last_verified_batch']=150;cursor['last_plan_sha256']=pin
                    cursor['batch150']=dict(exhibition_id=EVENT,completed_native_accessions=[o['accession'] for o in p['objects']],
                        completed_catalogue_numbers=[o['number'] for o in p['objects']],entry_ids=[o['id'] for o in p['objects']],
                        source_pdf_url=p['source']['url'],source_pdf_sha256=p['source']['sha256'],reviewed_pdf_pages=list(range(264,268)),
                        reviewed_printed_pages=list(range(263,267)),resume_pdf_page=268,resume_printed_page=267,total_event_entries=24,
                        exact_link_count=6,new_images=0,existing_illustrated_link=1,source_evidence=evidence+'/source-capture-verification.json',
                        visual_evidence=evidence+'/visual-object-identity-verification.json',plan_sha256=pin,next=next_task)
                    for h in reviews['held']:
                        x.setdefault('holds',[]).append(dict(key='batch150-'+h['accession'],at=c.now(),**h,evidence=evidence+'/candidate-review-verification.json'))
                    x['holds'].append(dict(key='batch150-Π.7699-image-aspect',reason='Catalogue 73 × 73 cm versus source reproduction aspect 550 × 600. Exact work visually established; no image uploaded; retain discrepancy for full-frame image review.',evidence=evidence+'/visual-object-identity-verification.json'))
                    x.setdefault('evidence',[]).append(evidence+'/independent-database-verification.json');changed.append((group,i))
        assert len(changed)==1
        for group in ['sources','supplemental_sources']:
            for i,x in enumerate(before[group]):
                if (group,i) not in changed:assert after[group][i]==x
        for key in before:
            if key not in ['sources','supplemental_sources']:assert after[key]==before[key]
        raw=json.dumps(after,ensure_ascii=False,indent=2).encode();temp=Q.with_name(Q.name+'.batch150.tmp');temp.write_bytes(raw);os.replace(temp,Q)
        save(E/'queue-update-verification.json',dict(at=c.now(),before_sha256=c.sha(json.dumps(before,ensure_ascii=False,sort_keys=True).encode()),after_sha256=c.sha(Q.read_bytes()),
             changed_sources=['national_gallery_athens'],unrelated_entries_preserved=True,resume_pdf_page=268,passed=True))
    checkpoint=dict(at=c.now(),batch=150,stage='verified_complete',plan_sha256=pin,verified_counts=v['verified_counts'],
                    event_id=EVENT,entry_ids=[x['id'] for x in p['objects']],next_task=next_task,external_supervisor_unchanged=True,
                    holds=reviews['held']+['Five links remain unillustrated; research images were not uploaded.','Original 1988 checklist unread; selected object histories establish partial coverage only.','Prior provider, identity, date and version holds preserved.'])
    save(E/'CHECKPOINT.json',checkpoint);save(R/'CHECKPOINT.json',checkpoint)
    cp=c.load(E.parents[1]/'CHECKPOINT.json');processes=[]
    for role in ['supervisor','worker']:
        pid=cp[role+'_pid'];out=subprocess.check_output(['ps','-p',str(pid),'-o','pid=,ppid=,command='],text=True).strip()
        assert out and ('continuous-exhibition-research.py run' in out if role=='supervisor' else '000150' in out)
        processes.append(dict(role=role,pid=pid,command=out))
    save(E/'continuation-process-verification.json',dict(at=c.now(),processes=processes,supervisor_unchanged=True,
         new_supervisors_created=0,inherited_descriptors_closed=False,passed=True))
    lock=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/supervisor.lock'
    out=subprocess.check_output(['/usr/sbin/lsof',str(lock)],text=True)
    assert all(str(cp[role+'_pid']) in out for role in ['supervisor','worker'])
    save(E/'singleton-lock-verification.json',dict(at=c.now(),supervisor_pid=cp['supervisor_pid'],worker_pid=cp['worker_pid'],lsof=out,passed=True))
    before=c.load(E/'required-input-verification.json')
    unchanged=[x for x in before['inputs'] if x['path'].endswith(('continuous-exhibition-research.py','INFINITE_EXHIBITION_RESEARCH_PROMPT.md','GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'))]
    assert all(c.sha(Path(x['path']).read_bytes())==x['sha256'] for x in unchanged)
    save(E/'final-verification.json',dict(at=c.now(),batch=150,plan_sha256=pin,verified_counts=v['verified_counts'],
         discovered_candidate_objects=8,prepared_exact_links=6,imported_exact_links=6,independently_verified_exact_links=6,
         complete_checklist=False,public_entry_count=24,other_programme_changes_claimed=0,real_local_database_connections=0,
         protected_inputs_unchanged=unchanged,passed=True))
    print(next_task)


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['prepare','apply','verify','finalize']
    globals()[sys.argv[1]]()
