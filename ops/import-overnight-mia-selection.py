#!/usr/bin/env python3
"""Import selected independent Mia objects for uniquely matched existing artists."""
import argparse,collections,importlib.util,json,uuid
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/'ops'/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
mia=module('mia','overnight-mia-images.py');guard=module('import_guard','import-overnight-met-selection.py');core=mia.core
print_review=module('print_review','overnight-distinct-print-review.py')
SOURCE='overnight-mia-selected-primary-20260915';INSTITUTION='minneapolis-institute-of-art'
def snapshot(db,records):return print_review.augment(db,records,guard.snapshot(db,records,INSTITUTION,['mia-object']))
def conflicts(records,state):return guard.conflicts(records,state,title_collision_review=print_review.allow)

def candidate(lead,reference):
    o=lead['object'];artist=lead['artist'];oid=lead['source_object_id'];aid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/night-selected-mia/'+oid));page='https://collections.artsmia.org/art/'+oid
    c={'artwork_id':aid,'slug':'night-mia-'+oid,'external_id':oid,'scheme':'mia-object','provider':'night-mia','title':lead['title'],
       **{k:lead[k] for k in ('date_display','creation_year_start','creation_year_end','date_precision','work_type','accession_number')},
       'creation_place_display':o.get('country') or None,'artist':artist['display_name'],'artist_id':artist['id'],'artist_slug':artist['slug'],'artist_slugs':[artist['slug']],'artist_qid':artist['qid'],
       'aliases':artist['aliases'],'roles':['primary'],'popular':artist['popular'],'page':page,'qid':None,'target_ids':{'local':aid}}
    url,facts=mia.source_match(c,o);credit=c['artist']+'; '+mia.NAME+'; '+(o.get('creditline') or '')+'; '+c['accession_number'];checked=lead['metadata_capture']['retrieved_at']
    keys=('id','title','classification','object_name','accession_number','artist','dated','life_date','medium','country','nationality','creditline','rights_type','restricted','image_copyright','image','public_access','Rights_Image_Display','Cache_Location','Primary_RenditionNumber','image_width','image_height')
    c['raw']={'object':{k:o[k] for k in keys if k in o},'metadata_capture':lead['metadata_capture'],'policy_captures':mia.capture_policy(reference),'image_mapping_evidence':json.loads((reference/'client-resource-evidence.json').read_text())}
    c.update(source_image_url=url,scope_evidence=facts,policy_url=mia.PDM,rights_status='public_domain',license_label='Public Domain Mark 1.0',checked_at=checked,
      creator_credit=credit,attribution_text=c['artist']+'. '+c['title']+'. '+credit+'. Public Domain Mark 1.0 ('+mia.PDM+'). Full-frame proportional resize and JPEG compression.',
      source_name=mia.NAME,source_record_url=page,image_url=url,image_license='Public Domain Mark 1.0',image_license_url=mia.PDM,rights_statement='Public Domain',creator=c['artist'],creation_date=c['date_display'],source_object_id=oid,rights_verified_at=checked,metadata_license=mia.CC0,
      medium_text=o.get('medium') or None,dimensions_text=o.get('dimension') or None)
    if lead.get('physical_object_review'):c['physical_object_review']=lead['physical_object_review']
    return c

def build(run,reference,limit):
    if (run/'plan.json').exists():return json.loads((run/'plan.json').read_text())
    rows=[]
    for lead in json.loads((reference/'source-leads.json').read_text()):
        rows.append(candidate(lead,reference))
    with mia.ro('postgres://localhost/artline') as db:state=snapshot(db,rows);selected,held=conflicts(rows,state)
    selected=[c for c in selected if not c['already_present']]
    if limit:selected=selected[:limit]
    for c in selected:
        for key in ('target_artist_id','already_present'):c.pop(key,None)
        c['institution_ids']={'local':state['institution_id']}
    backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915'/run.name
    core.save_new(backup/('local-selection-preimages-'+core.sha(core.encode(state))[:16]+'.json'),state)
    data={'at':core.now(),'records':selected,'held':held,'policy':'Official Mia source records and exact per-image Public Domain Mark; unique existing creator name/alias and non-conflicting source biography. Museum holdings, dates and type verified. All additions remain research candidates in review; no artist nationality inferred.'}
    core.save_new(run/'plan.json',data);core.save_new(run/'plan-manifest.json',{'sha256':core.sha((run/'plan.json').read_bytes()),'count':len(selected)})
    print('Mia selected',len(selected),'popular',sum(c['popular'] for c in selected),'types',dict(collections.Counter(c['work_type'] for c in selected)),'held',len(held),flush=True);return data

def apply(run,target):
    data=json.loads((run/'plan.json').read_text());assert core.sha((run/'plan.json').read_bytes())==json.loads((run/'plan-manifest.json').read_text())['sha256'];records=data['records']
    if not records:raise SystemExit('No selected records')
    dsn='postgres://localhost/artline' if target=='local' else core.cloud_dsn();backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915'/run.name;out=[]
    with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
        state=snapshot(db,records);selected,held=conflicts(records,state);iid=state['institution_id']
        preflight=backup/(target+'-import-preflight.json')
        if not preflight.exists():core.save_new(preflight,{'at':core.now(),'state':state,'held':held})
        if held:raise SystemExit('Target metadata conflicts; import requires review: '+str(len(held)))
        with db.transaction():
            db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,'Minneapolis Institute of Art: selected independently verified works','museum_api','https://new.artsmia.org/',%s) ON CONFLICT(slug) DO NOTHING",(SOURCE,mia.CC0));sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
        for start in range(0,len(selected),25):
            group=selected[start:start+25]
            with db.transaction():
                db.execute('SELECT pg_advisory_xact_lock(559220260915)')
                active=[c for c in group if not c['already_present']]
                if active:
                    collisions=db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND ((scheme='mia-object' AND external_id=ANY(%s)) OR canonical_url=ANY(%s))",([c['external_id'] for c in active],[c['page'] for c in active])).fetchall();assert not collisions,'Source identity appeared during import'
                with db.pipeline():
                    for c in group:
                        mia.source_match(c,c['raw']['object'])
                        if c['already_present']:out.append({'artwork_id':c['artwork_id'],'outcome':'already_present'});continue
                        aid=c['artwork_id'];checked=c['checked_at'];page=c['page']
                        db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,creation_place_display,current_institution_id,accession_number,status,research_candidate,created_by,updated_by)
                          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)""",(aid,c['slug'],c['title'],guard.norm(c['title']),c['date_display'],c['creation_year_start'],c['creation_year_end'],c['date_precision'],c['work_type'],c['medium_text'],c['dimensions_text'],c['creation_place_display'],iid,c['accession_number'],core.ACTOR,core.ACTOR))
                        db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary','Unique existing creator name/alias matched to the explicit museum Artist field; source biographical dates do not conflict.')",(aid,c['target_artist_id']))
                        db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'mia-object',%s,%s,%s,%s)",(aid,c['external_id'],page,sid,checked))
                        db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,iid,sid,page,'Official Minneapolis Institute of Art Collection record, accession '+c['accession_number']+'. Holding only; no current display claim.',checked))
                        evidence={'primary_record':c['raw']['object'],'metadata_capture':c['raw']['metadata_capture'],'metadata_license':mia.CC0,'creator_identity':{'existing_wikidata':c['artist_qid'],'existing_slug':c['artist_slug'],'museum_artist_field':c['scope_evidence']['source_creator']},'source_origin':c['creation_place_display'],'date_review':'Original source date and explicit uncertainty retained; no lifespan-derived creation dates.'}
                        if c.get('physical_object_review'):evidence['physical_object_review']=c['physical_object_review']
                        db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'official_object_identity',%s,%s,%s,%s,%s)",(aid,sid,c['external_id'],page,json.dumps(evidence,ensure_ascii=False),checked,core.ACTOR));out.append({'artwork_id':aid,'outcome':'inserted'})
            print(core.now(),target,'Mia metadata',len(out),'of',len(selected),flush=True)
        checked=db.execute("SELECT count(*) n,count(*) FILTER(WHERE status='review' AND published_at IS NULL AND research_candidate AND artline_has_selection_evidence(id)) ok FROM artworks WHERE id=ANY(%s::uuid[])",([c['artwork_id'] for c in records],)).fetchone();assert checked['n']==checked['ok']==len(records)
        path=run/(target+'-metadata-verified.json')
        if not path.exists():core.save_new(path,{'at':core.now(),'counts':checked,'records':out})
    if target=='local':
        for c in records:core.save_new(run/'selected/night-mia'/(c['artwork_id']+'.json'),c)
        core.save_new(run/'candidates.json',{'created_at':data['at'],'candidates':records,'production_metadata_pending':True})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','apply']);p.add_argument('--run',type=Path,required=True);p.add_argument('--reference',type=Path);p.add_argument('--limit',type=int,default=0);p.add_argument('--target',choices=['local','cloud'],default='local');a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
    if a.phase=='plan':build(a.run,a.reference or a.run,a.limit)
    else:apply(a.run,a.target)
