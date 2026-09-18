#!/usr/bin/env python3
"""Read-only semantic comparison of this research's delivered records.

UUIDs and mutation timestamps are not content identity. Compare stable slugs,
qualified creator relationships, cultural countries, physical metadata, images,
authorities and canonical redirects. Preserve differences for review.
"""
import argparse, importlib.util, json
from pathlib import Path

s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;BASE=m.x.BASE
SOURCE_PREFIX='overnight%' if m.x.SESSION_NAME=='overnight-countries-20260913' else m.x.SESSION_NAME+'%'
MEDIA_SOURCES=['overnight-country-images-20260913','overnight-dutch-met-images-20260913','overnight-greek-primary-images-20260913','overnight-tzanes-met-primary-20260913','overnight-cabral-selected-images-20260913','overnight-finnish-primary-selected-images-20260913','overnight-kmska-selected-images-20260913']

def snapshot(target,index):
    owned=index['targets'][target]
    with m.m.r.base.connect(target=='production') as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        db.execute("SET LOCAL statement_timeout='180s'")
        duplicates=db.execute("SELECT DISTINCT c.entity_type,c.source_record_id old_slug,c.entity_id::text canonical_id FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.field_name='duplicate_identity' AND s.slug LIKE %s",(SOURCE_PREFIX,)).fetchall()
        work_ids=set(owned['new_artwork_ids'])|set(owned.get('touched_artwork_ids',[]));artist_ids=set(owned['new_artist_ids'])|set(owned.get('touched_artist_ids',[]))
        for receipt_path in owned['receipt_paths']:
            receipt=json.loads((BASE/receipt_path).read_text())
            if isinstance(receipt,dict):
                if receipt.get('artwork_id'):work_ids.add(receipt['artwork_id'])
                if receipt.get('artist_id'):artist_ids.add(receipt['artist_id'])
        for kind,table,ids in [('artwork','artworks',work_ids),('artist','artists',artist_ids)]:
            olds=[r['old_slug'] for r in duplicates if r['entity_type']==kind]
            ids.update(r['canonical_id'] for r in duplicates if r['entity_type']==kind)
            ids.update(r['id'] for r in db.execute('SELECT id::text FROM '+table+' WHERE slug=ANY(%s)',(olds,)))
        works=db.execute("""SELECT w.id::text,w.slug,w.title,w.alternate_title,w.creation_year_start,w.creation_year_end,w.date_precision,w.date_display,w.work_type,w.object_form,w.medium_text,w.dimensions_text,w.accession_number,w.status,w.published_at,i.slug institution_slug,im.storage_path image_path,im.checksum_sha256 image_sha256,im.rights_status image_rights
            FROM artworks w LEFT JOIN institutions i ON i.id=w.current_institution_id LEFT JOIN media_assets im ON im.id=w.primary_media_id WHERE w.id=ANY(%s::uuid[]) ORDER BY w.slug""",(sorted(work_ids),)).fetchall()
        creators=db.execute("SELECT aa.artwork_id::text,a.id::text artist_id,a.slug,aa.attribution_role FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY a.slug,aa.attribution_role",(sorted(work_ids),)).fetchall()
        artist_ids.update(r['artist_id'] for r in creators)
        artists=db.execute("SELECT id::text,slug,display_name,birth_year,death_year,birth_display,death_display,entity_type,status,published_at FROM artists WHERE id=ANY(%s::uuid[]) ORDER BY slug",(sorted(artist_ids),)).fetchall()
        countries=db.execute("SELECT artist_id::text,country_code,relationship_type,is_primary FROM artist_countries WHERE artist_id=ANY(%s::uuid[]) ORDER BY country_code,relationship_type,is_primary",(sorted(artist_ids),)).fetchall()
        authorities=db.execute("SELECT entity_type,entity_id::text,scheme,external_id FROM external_identifiers WHERE (entity_type='artist' AND entity_id=ANY(%s::uuid[])) OR (entity_type='artwork' AND entity_id=ANY(%s::uuid[])) ORDER BY scheme,external_id",(sorted(artist_ids),sorted(work_ids))).fetchall()
        redirects=db.execute("SELECT r.entity_type,r.old_slug,coalesce(a.slug,w.slug) canonical_slug FROM slug_redirects r LEFT JOIN artists a ON r.entity_type='artist' AND a.id=r.entity_id LEFT JOIN artworks w ON r.entity_type='artwork' AND w.id=r.entity_id WHERE (r.entity_type='artist' AND r.entity_id=ANY(%s::uuid[])) OR (r.entity_type='artwork' AND r.entity_id=ANY(%s::uuid[])) ORDER BY r.entity_type,r.old_slug",(sorted(artist_ids),sorted(work_ids))).fetchall()
        image_query="""SELECT DISTINCT ma.id::text,ma.storage_path,ma.checksum_sha256,ma.byte_size,ma.width,ma.height,ma.alt_text,ma.rights_status,ma.license_label,ma.license_url,ma.creator_credit,ma.source_page_url,ma.verified_at IS NOT NULL verified FROM media_assets ma """
        if 'media_ids' in owned:images=db.execute(image_query+'WHERE ma.id=ANY(%s::uuid[]) ORDER BY ma.storage_path',(owned['media_ids'],)).fetchall();assert len(images)==len(owned['media_ids'])
        else:images=db.execute(image_query+'JOIN media_rights_evidence e ON e.media_id=ma.id JOIN sources s ON s.id=e.source_id WHERE s.slug=ANY(%s) ORDER BY ma.storage_path',(MEDIA_SOURCES,)).fetchall()
        active_media={r['id'] for r in db.execute("SELECT DISTINCT primary_media_id::text id FROM artworks WHERE primary_media_id=ANY(%s::uuid[]) AND status<>'archived'",([r['id'] for r in images],))}
        for r in images:r['active_primary']=r['id'] in active_media
    work_map={r.pop('id'):dict(r,creators=[],authorities=[]) for r in works}
    artist_map={r.pop('id'):dict(r,countries=[],authorities=[]) for r in artists}
    for r in creators:work_map[r['artwork_id']]['creators'].append(dict(slug=r['slug'],role=r['attribution_role']))
    for r in countries:artist_map[r.pop('artist_id')]['countries'].append(r)
    for r in authorities:
        dest=artist_map if r['entity_type']=='artist' else work_map
        dest[r['entity_id']]['authorities'].append(dict(scheme=r['scheme'],external_id=r['external_id']))
    for r in images:r.pop('id')
    return dict(artworks={r['slug']:r for r in work_map.values()},artists={r['slug']:r for r in artist_map.values()},redirects=redirects,images={r['storage_path']:r for r in images})

def main(index_path,phase,reuse_snapshots=False):
    root=BASE/'final-audit'/phase;dest=root/'semantic-parity.json';assert not dest.exists()
    index=json.loads(index_path.read_text());snapshots={}
    for target in ('local','production'):
        if reuse_snapshots:snapshots[target]=json.loads((root/(target+'-semantic-snapshot.json')).read_text())
        else:
            snapshots[target]=snapshot(target,index)
            CORE.save_new(root/(target+'-semantic-snapshot.json'),snapshots[target])
        print('Read-only semantic snapshot',target,len(snapshots[target]['artworks']),'artworks',flush=True)
    left=snapshots['local'];right=snapshots['production'];differences=[]
    for kind in ('artworks','artists','images'):
        for key in sorted(set(left[kind])|set(right[kind])):
            a=left[kind].get(key);b=right[kind].get(key)
            if a!=b:differences.append(dict(kind=kind,key=key,fields=[f for f in sorted(set(a or {})|set(b or {})) if (a or {}).get(f)!=(b or {}).get(f)],local=a,production=b))
    redirect_key=lambda r:(r['entity_type'],r['old_slug'],r['canonical_slug'])
    local_redirects={redirect_key(r) for r in left['redirects']};production_redirects={redirect_key(r) for r in right['redirects']}
    assert len(local_redirects)==len(left['redirects']) and len(production_redirects)==len(right['redirects'])
    if local_redirects!=production_redirects:differences.append(dict(kind='redirects',only_local=sorted(local_redirects-production_redirects),only_production=sorted(production_redirects-local_redirects)))
    result=dict(at=CORE.now(),phase=phase,matched=not differences,differences=differences,scope='Exact session receipt-owned rows, source-cited touched records and session duplicate identities; stable content fields, qualified creator links, cultural relationships, authority IDs, redirects and selected image metadata. Separately captured repeatable-read snapshots; not whole-database identity or simultaneous global snapshots.',counts={t:{k:len(v) for k,v in snap.items()} for t,snap in snapshots.items()},active_primary_images={t:sum(im['active_primary'] and im['verified'] and im['rights_status'] in ('public_domain','cc0','cc_by','cc_by_sa','licensed') for im in snap['images'].values()) for t,snap in snapshots.items()})
    CORE.save_new(dest,result);print('Semantic parity',result['matched'],'differences',len(differences),flush=True)
    assert not differences,'Preserved semantic differences require review before claiming synchronization'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session-index',type=Path,required=True);p.add_argument('--phase',required=True);p.add_argument('--reuse-snapshots',action='store_true');a=p.parse_args();assert all(c.isalnum() or c in '-_' for c in a.phase);main(a.session_index,a.phase,a.reuse_snapshots)
