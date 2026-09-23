#!/usr/bin/env python3
"""Select source-verified Chicago additions and existing image gaps, resumably.

Input: a bounded, artist-by-artist capture under --run/chicago/artists.
Metadata-only reads; full database preimages live outside the repository.
"""
import argparse, collections, importlib.util, json, uuid
from pathlib import Path
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
check=module('chicago_check','popular-chicago-verification.py')
campaign=module('campaign','overnight-image-campaign.py');core=campaign.core
guard=module('guard','import-overnight-met-selection.py')
FIELDS='id,title,alt_titles,artist_id,artist_ids,artist_title,artist_display,artist_pivots,date_display,date_start,date_end,main_reference_number,artwork_type_title,classification_title,classification_titles,medium_display,dimensions,credit_line,is_public_domain,copyright_notice,image_id,department_title,fiscal_year_deaccession'
IMAGE_FIELDS='id,type,credit_line,iiif_url,artwork_ids,width,height'
SCHEMES=[check.SCHEME,'aic-object']
def backup_root(run):return Path.home()/'Library/Application Support/Artline/backups'/run.name
def batch(fetcher,endpoint,ids,fields,include=None):
    params={'ids':','.join(map(str,ids)),'fields':fields,'limit':100}
    if include:params['include']=include
    u='https://api.artic.edu/api/v1/'+endpoint+'?'+urlencode(params)
    d=fetcher.metadata(u)
    r=json.loads((fetcher.cache/(core.sha(u.encode())+'.receipt.json')).read_text())
    return d['data'],r
def snapshot(db,records):return guard.snapshot(db,records,check.SLUG,SCHEMES)
def main(run):
    if (run/'selection-report.json').exists():print('Pinned selection already complete; no changes');return
    summary=json.loads((run/'chicago-capture-summary.json').read_text())
    assert len(summary['artists'])==100 and summary['records']<=10000
    source=collections.defaultdict(list)
    for path in (run/'chicago/artists').glob('*.json'):
        d=json.loads(path.read_text())
        if d['match_count']!=1:continue
        assert d['total']>=len(d['works']) and (not d['complete'] or d['total']==len(d['works']))
        for o in d['works']:source[str(o['id'])].append((d,o))
    with campaign.read_only('postgres://localhost/artline') as db:
        existing=collections.defaultdict(list)
        rows=db.execute("""SELECT a.id::text artwork_id,a.slug,a.title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.accession_number,a.status,a.primary_media_id::text,a.current_institution_id::text,
          ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artist_ids,
          ARRAY(SELECT aa.attribution_role::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) roles,
          artline_has_selection_evidence(a.id) selected,e.scheme,e.external_id,e.canonical_url page,e.source_id::text
          FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork' AND e.scheme=ANY(%s)""",(SCHEMES,)).fetchall()
        for row in rows:existing[row['external_id']].append(row)
    core.save_new(backup_root(run)/'existing-chicago-before.json',rows)
    counts=collections.Counter();todo=[];held=[]
    for oid,links in source.items():
        if len(links)!=1:counts['multiple_popular_artist_associations']+=1;continue
        d,o=links[0];old=existing[oid]
        if old and all(x['primary_media_id'] for x in old):counts['existing_with_primary_image']+=1;continue
        if o.get('artwork_type_title') not in ('Painting','Drawing and Watercolor','Print'):counts['other_object_type']+=1;continue
        # Detailed primary artist roles and exact rights are checked below.
        todo.append((oid,d,o,old))
    f=campaign.BaseFetcher(run/'chicago/object-evidence');verified=[]
    for start in range(0,len(todo),100):
        group=todo[start:start+100];objects,receipt=batch(f,'artworks',[v[0] for v in group],FIELDS,'artist_pivots');idx={str(o['id']):o for o in objects}
        for oid,d,search,old in group:
            try:
                o=idx[oid];a=d['artist'];facts=check.metadata(o,a,d['source_artists'][0]);page='https://www.artic.edu/artworks/'+oid
                if old:
                    if len(old)!=1:raise ValueError('Existing native object identity is ambiguous')
                    v=old[0]
                    if (v['status']!='review' or not v['selected'] or v['artist_ids']!=[a['id']] or v['roles']!=['primary']
                            or any(v[k]!=facts[k] for k in ('creation_year_start','creation_year_end','work_type','accession_number'))
                            or check.norm(v['title'])!=check.norm(facts['title'])):
                        raise ValueError('Existing catalogue attribution, accession, dates or classification differ')
                    c={k:v[k] for k in ('artwork_id','slug','scheme','title','date_display','creation_year_start','creation_year_end','date_precision','work_type','accession_number','source_id')}
                    c['existing']=True
                else:
                    c=dict(artwork_id=str(uuid.uuid5(uuid.NAMESPACE_URL,page)),slug='chicago-'+oid,scheme=check.SCHEME,existing=False,**facts)
                c.update(external_id=oid,provider='chicago',page=page,qid=None,artist=a['display_name'],artist_slug=a['slug'],artist_slugs=[a['slug']],artist_qid=a['qid'],artist_id=a['id'],aliases=a['aliases'],roles=['primary'],popular=True,artist_authority=str(d['source_artists'][0]['id']),target_ids={'local':c['artwork_id']},source_artist=d['source_artists'][0],artist_evidence=a,source_object=o,metadata_capture=receipt,metadata_license=check.CC0)
                verified.append(c)
            except (ValueError,KeyError) as e:held.append({'source_object_id':oid,'reason':str(e)})
        print(core.now(),'Detailed museum metadata',min(start+100,len(todo)),'/',len(todo),'verified',len(verified),flush=True)
    verified.sort(key=lambda c:(c['work_type']!='painting',c['work_type']=='print',c['artist'],c['external_id']))
    new=[c for c in verified if not c['existing']]
    with campaign.read_only('postgres://localhost/artline') as db:state=snapshot(db,new);selected,conflicts=guard.conflicts(new,state)
    core.save_new(backup_root(run)/('local-selection-preimages-'+core.sha(core.encode(state))[:16]+'.json'),state)
    selected=[c for c in selected if not c['already_present']]
    for c in selected:
        c.pop('target_artist_id',None);c.pop('already_present',None)
    if (run/'plan.json').exists():
        pinned=json.loads((run/'plan.json').read_text())
        assert core.encode(pinned['records'])==core.encode(selected),'Pinned source selection changed'
    else:core.save_new(run/'plan.json',{'at':core.now(),'records':selected,'held':conflicts,'policy':'Exact native museum records, unqualified popular creator, bounded creation dates and accession/collection credit. Review status retained. Images are independently optional.'})
    core.save_new(run/'plan-manifest.json',{'sha256':core.sha((run/'plan.json').read_bytes()),'count':len(selected)})
    if not (run/'holding-deaccession-check.json').exists():
        holding=[]
        for c in selected:
            o=c['source_object'];assert 'fiscal_year_deaccession' in o and o['fiscal_year_deaccession'] is None
            holding.append({k:o[k] for k in ('id','title','fiscal_year_deaccession','main_reference_number','credit_line')})
        core.save_new(run/'holding-deaccession-check.json',{'at':core.now(),'records':holding,'captures':list({c['metadata_capture']['url']:c['metadata_capture'] for c in selected}.values()),'conflicts':[]})
    image_candidates=selected+[c for c in verified if c['existing']];approved=[];image_held=[]
    ids=sorted({c['source_object']['image_id'] for c in image_candidates if c['source_object'].get('image_id') and c['source_object'].get('is_public_domain') is True and not c['source_object'].get('copyright_notice')})
    resources={};image_receipts={}
    for start in range(0,len(ids),20):
        objects,r=batch(f,'images',ids[start:start+20],IMAGE_FIELDS)
        for im in objects:resources[im['id']]=im;image_receipts[im['id']]=r
        print(core.now(),'Exact image-resource rights',min(start+20,len(ids)),'/',len(ids),flush=True)
    for c in image_candidates:
        try:
            o=c['source_object'];im=resources.get(o.get('image_id'),{});url=check.image(o,im)
            checked=image_receipts[im['id']]['retrieved_at'];credit=c['artist']+'; Art Institute of Chicago; '+o['credit_line']
            c=dict(c,source_image_url=url,policy_url=check.CC0,rights_status='cc0',license_label='CC0 1.0',checked_at=checked,creator_credit=credit,attribution_text=c['artist']+'. '+c['title']+'. '+credit+'. CC0 1.0 ('+check.CC0+'). Full-frame proportional resize and JPEG compression.',source_name='Art Institute of Chicago',source_record_url=c['page'],image_url=url,image_license='CC0 1.0',image_license_url=check.CC0,rights_statement=im['credit_line'],creator=c['artist'],creation_date=c['date_display'],source_object_id=c['external_id'],rights_verified_at=checked,museum_policy_url='https://www.artic.edu/image-licensing',raw={**o,'verified_image_resource':im,'image_metadata_capture':image_receipts[im['id']],'object_metadata_capture':c['metadata_capture']})
            campaign.fresh_scope('chicago',c['raw'],c)
            approved.append(c)
        except ValueError as e:image_held.append({'source_object_id':c['external_id'],'artwork_id':c['artwork_id'],'reason':str(e)})
    core.save_new(run/'candidates.json',{'at':core.now(),'candidates':approved})
    for c in approved:core.save_new(run/'selected/chicago'/(c['artwork_id']+'.json'),c)
    core.save_new(run/'research-held.json',held)
    core.save_new(run/'image-rights-held.json',image_held)
    report={'at':core.now(),'popular_artists_requested':100,'native_artist_matches':sum(x['match_count']==1 for x in summary['artists']),'unique_museum_objects':len(source),'detailed_objects_checked':len(todo),'verified_new_artworks':len(selected),'new_types':dict(collections.Counter(c['work_type'] for c in selected)),'selected_cc0_images':len(approved),'new_works_with_images':sum(not c['existing'] for c in approved),'existing_image_gaps':sum(c['existing'] for c in approved),'new_metadata_only':len(selected)-sum(not c['existing'] for c in approved),'metadata_holds':dict(collections.Counter(c['reason'] for c in held)),'duplicate_or_version_holds':dict(collections.Counter(c['reason'] for c in conflicts)),'image_holds':dict(collections.Counter(c['reason'] for c in image_held)),**counts}
    core.save_new(run/'selection-report.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args();main(a.run)
