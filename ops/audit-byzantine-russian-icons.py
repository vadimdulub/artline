#!/usr/bin/env python3
"""Read-only catalogue and existing-image audit; no downloads or database writes."""
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
import psycopg
from psycopg.rows import dict_row

CREATOR=r'(icon.painter|iconographer|иконопис|rublev|roublev|rublyov|ushakov|theophanes|tzanes|tzanès|tzafour|damaskin|klontz|akotant|andreas.ritzos|theodore.poulakis|skordil|theodore.apsevdis|joseph.chourri|minas.of.marathasa|\mdionysius\M|\mdionisius\M|\mdionisy\M)'
CONTEXT=r'(byzant|визант|βυζαντ|orthodox.icons|russian.icon|icon.painting.in.moscow)'
TITLE=r'(byzant|визант|βυζαντ|\micons?\M|икон|εικόν|εικον)'
# Explicit transliteration avoids locale-dependent non-ASCII case matching:
# the local and cloud databases have different locale behaviour.
UPPER='АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩΆΈΉΊΌΎΏ'
LOWER='абвгдеёжзийклмнопрстуфхцчшщъыьэюяαβγδεζηθικλμνξοπρστυφχψωάέήίόύώ'
DISCOVERY='''WITH candidates AS (
    SELECT a.id,a.slug,
        a.object_form='icon' explicit_icon,
        translate(coalesce(a.cultural_context,''),%(upper)s,%(lower)s) ~* %(context)s tradition_context,
        translate(concat_ws(' ',a.title,a.alternate_title),%(upper)s,%(lower)s) ~* %(title)s title_candidate,
        translate(coalesce(a.description_md,''),%(upper)s,%(lower)s) ~* %(text)s description_candidate,
        EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id AND aa.artist_id=ANY(%(artists)s::uuid[])) creator_candidate,
        EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme LIKE 'european-icons-%%') icon_source
    FROM artworks a)
    SELECT * FROM candidates WHERE explicit_icon OR tradition_context OR title_candidate OR description_candidate OR creator_candidate OR icon_source ORDER BY slug'''


def ro(dsn):
    return psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=180000')


def snapshot(db, slugs=None):
    people=[] if slugs is not None else db.execute("SELECT id::text,slug,display_name FROM artists WHERE concat_ws(' ',display_name,slug,biography_md) ~* %s ORDER BY slug",(CREATOR,)).fetchall()
    params={'context':CONTEXT,'title':TITLE,'text':r'(byzantine|post.byzant|russian.icons?|russian.icon.paint|византи|русск.{0,20}икон)',
        'artists':[p['id'] for p in people], 'upper':UPPER,'lower':LOWER}
    query=DISCOVERY
    if slugs is not None:
        query='SELECT id,slug FROM artworks WHERE slug=ANY(%(slugs)s::text[]) ORDER BY slug'
        params={'slugs':slugs}
    plan=db.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+query,params).fetchone()['QUERY PLAN']
    discovered=db.execute(query,params).fetchall();ids=[str(r['id']) for r in discovered]
    rows=[]
    for start in range(0,len(ids),200):
        batch=ids[start:start+200]
        rows.extend(db.execute('''SELECT a.id::text,a.slug,a.title,a.alternate_title,a.work_type,a.object_form,a.cultural_context,
            a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.medium_text,a.dimensions_text,
            a.unlinked_creator_label,a.description_md,a.creation_place_display,a.status,a.research_candidate,a.published_at,
            a.current_institution_id::text,a.accession_number,a.primary_media_id::text,
            artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) creation_scope,
            artline_has_selection_evidence(a.id) selection_evidence,
            (SELECT jsonb_build_object('slug',i.slug,'name',i.name) FROM institutions i WHERE i.id=a.current_institution_id) institution
            FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.slug''',(batch,)).fetchall())
    byid={r['id']:r for r in rows}
    for r in discovered:byid[str(r['id'])]['scope_flags']=[k for k,v in r.items() if k not in ('id','slug') and v]
    for r in rows:
        for field in ('creators','identifiers','citations','locations','secondary_media'):r[field]=[]
    for start in range(0,len(ids),200):
        batch=ids[start:start+200]
        groups={
            'creators':db.execute('''SELECT aa.artwork_id::text,p.id::text artist_id,p.slug,p.display_name,p.status,aa.attribution_role,aa.attribution_note,
                p.birth_year,p.death_year,p.biography_md,
                array(SELECT DISTINCT ac.country_code::text FROM artist_countries ac WHERE ac.artist_id=p.id ORDER BY ac.country_code::text) countries
                FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,p.slug,aa.attribution_role''',(batch,)).fetchall(),
            'identifiers':db.execute("SELECT entity_id::text artwork_id,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY scheme,external_id",(batch,)).fetchall(),
            'citations':db.execute("SELECT c.entity_id::text artwork_id,c.field_name,c.source_record_id,c.source_url,c.evidence_note,c.retrieved_at,s.slug source_slug,s.source_type FROM citations c LEFT JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artwork' AND c.entity_id=ANY(%s::uuid[]) ORDER BY c.entity_id,c.field_name,c.id",(batch,)).fetchall(),
            'locations':db.execute("SELECT artwork_id::text,claim_type,institution_id::text,source_url,checked_at,review_state,display_state,evidence_note,superseded_by::text FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,claim_type,id",(batch,)).fetchall(),
            'secondary_media':db.execute('SELECT artwork_id::text,media_id::text FROM artwork_media WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artwork_id,media_id',(batch,)).fetchall()}
        for key,values in groups.items():
            for value in values:byid[value['artwork_id']][key].append(value)
    media_ids=sorted({r['primary_media_id'] for r in rows if r['primary_media_id']}|{m['media_id'] for r in rows for m in r['secondary_media']})
    media=db.execute('''SELECT m.id::text,to_jsonb(m) asset,
        (SELECT jsonb_agg(to_jsonb(e)) FROM media_rights_evidence e WHERE e.media_id=m.id) rights_evidence
        FROM media_assets m WHERE m.id=ANY(%s::uuid[]) ORDER BY m.id''',(media_ids,)).fetchall()
    return {'at':core.now(),'discovery_mode':'bounded_slug_confirmation' if slugs is not None else 'broad_metadata_discovery',
        'discovery_creators':people,'records':rows,'media':media,'discovery_plan':plan}


def check_files(media):
    checked=[]
    for row in media:
        m=row['asset'];path=m.get('storage_path');item={'media_id':row['id'],'storage_path':path,'recorded_bytes':m.get('byte_size'),'rights_status':m.get('rights_status'),'issues':[]}
        if not row['rights_evidence']:item['issues'].append('no_rights_evidence_row')
        if m.get('rights_status') not in ('cc0','public_domain','cc_by','cc_by_sa'):item['issues'].append('rights_label_requires_individual_review')
        if not path or not path.startswith('/assets/'):item['issues'].append('no_local_asset_path')
        else:
            file=ROOT/'apps/web/public'/path.lstrip('/')
            if not file.is_file():item['issues'].append('local_file_missing')
            else:
                raw=file.read_bytes();item['actual_bytes']=len(raw);item['sha256']=hashlib.sha256(raw).hexdigest()
                if len(raw)>100000:item['issues'].append('exceeds_100000_bytes')
                if len(raw)!=m.get('byte_size') or item['sha256']!=(m.get('checksum_sha256') or '').strip():item['issues'].append('stored_size_or_hash_differs')
                try:
                    with Image.open(file) as im:
                        item['dimensions']=list(im.size);im.verify()
                    if item['dimensions']!=[m.get('width'),m.get('height')]:item['issues'].append('stored_dimensions_differ')
                except Exception:item['issues'].append('invalid_image_file')
        checked.append(item)
    return checked


def findings(r):
    out=[]
    if not r['creators'] and not r['unlinked_creator_label']:out.append('missing_creator_attribution')
    if r['creators'] and r['unlinked_creator_label']:out.append('linked_and_unlinked_creator_labels')
    if r['creation_scope']!='eligible':out.append('creation_scope_'+r['creation_scope'])
    if not r['medium_text']:out.append('medium_unrecorded')
    if not r['identifiers'] and not r['citations']:out.append('no_recorded_source_reference')
    if not r['primary_media_id']:out.append('no_primary_image')
    if not r['object_form'] and re.search(r'\bicons?\b|икон[аыуе]',str(r['cultural_context'] or '')+' '+r['title'],re.I):out.append('icon_form_needs_classification_review')
    if r['work_type']=='painting' and re.search(r'\bmosaic',str(r['medium_text'] or '')+' '+str(r['cultural_context'] or ''),re.I):out.append('mosaic_classified_as_painting')
    if r['current_institution_id'] and not any(l['claim_type']=='holding' and l['source_url'] and l['review_state']=='accepted' and not l['superseded_by'] for l in r['locations']):out.append('institution_without_current_source_backed_holding_assertion')
    if not r['selection_evidence']:out.append('no_accepted_selection_evidence')
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--phase',choices=['audit','contacts','cloud-confirm'],default='audit');a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
    if a.phase=='contacts':
        state=json.loads((a.run/'local-snapshot.json').read_text());media={m['id']:m['asset'] for m in state['media']}
        rows=[r for r in state['records'] if r['primary_media_id']];index=[]
        for start in range(0,len(rows),16):
            canvas=Image.new('RGB',(1440,1440),'white');draw=ImageDraw.Draw(canvas)
            for n,r in enumerate(rows[start:start+16]):
                m=media[r['primary_media_id']];path=ROOT/'apps/web/public'/m['storage_path'].lstrip('/')
                with Image.open(path) as source:tile=source.convert('RGB');tile.thumbnail((340,290))
                x=n%4*360;y=n//4*360;canvas.paste(tile,(x+(360-tile.width)//2,y))
                label=str(start+n+1)+' '+r['title'];draw.text((x+4,y+294),label[:48],fill='black');draw.text((x+4,y+311),label[48:95],fill='black')
                creator='; '.join(c['display_name'] for c in r['creators']) or r['unlinked_creator_label'] or 'Unlinked'
                draw.text((x+4,y+328),creator[:48],fill='black')
                index.append({'number':start+n+1,'slug':r['slug'],'title':r['title'],'artwork_id':r['id'],'path':m['storage_path'],'sha256':m['checksum_sha256'],'sheet':start//16+1})
            canvas.save(a.run/('contact-sheet-'+str(start//16+1)+'.jpg'),quality=90)
        core.save_new(a.run/'contact-index.json',index);print('Contact sheets for',len(rows),'existing images');return
    snapshots={}
    targets=[('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]
    if a.phase=='cloud-confirm':
        snapshots['local']=json.loads((a.run/'local-snapshot.json').read_text())
        targets=[targets[1]]
    for target,dsn in targets:
        slugs=[r['slug'] for r in snapshots['local']['records']] if a.phase=='cloud-confirm' else None
        with ro(dsn) as db:snapshots[target]=snapshot(db,slugs)
        core.save_new(a.run/(target+'-snapshot.json'),snapshots[target])
        print(target,'candidate records',len(snapshots[target]['records']),'media',len(snapshots[target]['media']),flush=True)
    local=snapshots['local'];files=check_files(local['media']);core.save_new(a.run/'image-file-audit.json',files)
    report={}
    for target,s in snapshots.items():
        rows=s['records'];report[target]={'candidates':len(rows),'explicit_icons':sum(r['object_form']=='icon' for r in rows),
            'with_primary_image':sum(bool(r['primary_media_id']) for r in rows),'without_linked_artist':sum(not r['creators'] for r in rows),
            'statuses':dict(collections.Counter(r['status'] for r in rows)),'creation_scopes':dict(collections.Counter(r['creation_scope'] for r in rows)),
            'scope_flags':dict(collections.Counter(f for r in rows for f in r['scope_flags'])),
            'findings':dict(collections.Counter(f for r in rows for f in findings(r))),
            'discovery_mode':s.get('discovery_mode','broad_metadata_discovery'),
            'discovery_execution_ms':s['discovery_plan'][0]['Execution Time']}
    cloud={r['slug']:r for r in snapshots['cloud']['records']};parity=[]
    fields=('title','creation_year_start','creation_year_end','date_precision','date_display','work_type','object_form','cultural_context','unlinked_creator_label','status','research_candidate','primary_media_id')
    for r in local['records']:
        other=cloud.get(r['slug']);changed=[k for k in fields if other and r[k]!=other[k]]
        if not other or changed:parity.append({'slug':r['slug'],'not_in_cloud_candidate_set':not bool(other),'fields':changed})
    local_slugs={r['slug'] for r in local['records']}
    parity.extend({'slug':r['slug'],'not_in_local_candidate_set':True} for r in snapshots['cloud']['records'] if r['slug'] not in local_slugs)
    core.save_new(a.run/'catalogue-parity.json',parity)
    core.save_new(a.run/'review-ledger.json',[{**r,'findings':findings(r)} for r in local['records']])
    report.update(at=core.now(),files_checked=len(files),max_actual_bytes=max((r.get('actual_bytes',0) for r in files),default=0),
        file_issues=dict(collections.Counter(i for r in files for i in r['issues'])),parity_differences=len(parity),
        scope_note='Broad catalogue discovery candidates, not an assertion that every matched work is Byzantine or a Russian icon. Creator/influence/title-only matches require object-level classification. All database connections are read-only.')
    core.save_new(a.run/'audit-summary.json',report);print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
