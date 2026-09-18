#!/usr/bin/env python3
"""Read-only bounded export for further ChatGPT research, with literal CSV cells.

Run only after the final application/audit checkpoint. A named preview snapshot
can be generated independently; existing export evidence is never overwritten.
"""
import argparse,collections,csv,datetime,hashlib,importlib.util,json,zipfile
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;BASE=m.x.BASE;START='2026-09-13T18:59:34+00:00'
COUNTRY_CODES=tuple(m.x.COUNTRIES) if m.x.SESSION_NAME!='overnight-countries-20260913' else ('NL','GR','RU','FR','IT','ES','DE','AT','BE','FI','PT')

class CSV:
    def __init__(self,root,name,fields,split=None):
        self.root=root;self.name=name;self.fields=fields;self.split=split;self.rows=0;self.files=[];self.f=None;self.escaped=0
        self.open()
    def open(self):
        suffix=f'_{len(self.files)+1:03d}' if self.split else ''
        p=self.root/(self.name+suffix+'.csv');assert not p.exists();self.f=p.open('w',encoding='utf-8-sig',newline='');self.writer=csv.DictWriter(self.f,fieldnames=self.fields,extrasaction='raise');self.writer.writeheader();self.files.append(p)
    def cell(self,v):
        if v is None:return ''
        if isinstance(v,(dict,list)):v=json.dumps(v,ensure_ascii=False,separators=(',',':'),sort_keys=True)
        elif isinstance(v,bool):v='true' if v else 'false'
        else:v=str(v)
        if v.lstrip().startswith(('=','+','-','@')) or v.startswith(('\t','\r','\n')):self.escaped+=1;v="'"+v
        return v
    def add(self,row):
        if self.split and self.rows and self.rows%self.split==0:self.f.close();self.open()
        self.writer.writerow({k:self.cell(row.get(k)) for k in self.fields});self.rows+=1
    def finish(self):
        self.f.close();return dict(rows=self.rows,formula_escaped_cells=self.escaped,files=[dict(name=p.name,bytes=p.stat().st_size,sha256=CORE.sha(p.read_bytes())) for p in self.files])

def export(phase,max_pages=None,production_crosswalk=None,session_index_path=None,create_archive=True):
    root=BASE/'chatgpt-handoff'/phase;assert not root.exists(),'Preserve existing export evidence; use a new phase';root.mkdir(parents=True)
    result=dict(at=CORE.now(),phase=phase,partial_preview=bool(max_pages),policy='Read-only local catalogue snapshot with production UUID crosswalk. Database IDs may differ; stable slugs are the import key. Country affiliations are distinct from birthplace and museum country. Existing publication status and database date classification retained.',files={})
    session_path=Path(session_index_path) if session_index_path else BASE/'session-application-index-final.json'
    if session_index_path:assert session_path.exists(),'Explicit session index is missing; do not fall back to an older snapshot'
    elif not session_path.exists():session_path=BASE/'session-application-index.json'
    session_index=json.loads(session_path.read_text()) if session_path.exists() else None
    if m.x.SESSION_NAME!='overnight-countries-20260913':assert session_index is not None,'A new research session requires its own exact application-receipt index'
    own_new_ids=set(session_index['targets']['local']['new_artwork_ids']) if session_index else None
    session_verified_media=set(session_index['targets']['local'].get('media_ids',[])) & set(session_index['targets']['production'].get('media_ids',[])) if session_index else set()
    if session_index:result['session_membership']=dict(path=str(session_path),sha256=CORE.sha(session_path.read_bytes()),gross_new_artworks=session_index['gross_new_artworks'],basis='Exact local application receipt IDs, including later archived duplicates. Source citations can move to canonical records during consolidation and cannot alone identify gross additions.')
    local_only_media=set()
    for image_root in (BASE/'finland/primary-followup/images',BASE/'belgium/primary-triptych/images'):
        if (image_root/'verification-local.json').exists() and not (image_root/'verification-production.json').exists() and not (image_root/'verification.json').exists():
            local_only_media.update(im['media_id'] for im in json.loads((image_root/'application-plan-local.json').read_text())['images'])
    if production_crosswalk:
        raw=Path(production_crosswalk).read_bytes();crosswalk=json.loads(raw)
        prod_ids=dict(artists=crosswalk['artists'],artworks=crosswalk['artworks'],institutions={})
        result['production_crosswalk']=dict(path=str(production_crosswalk),sha256=CORE.sha(raw),scope=crosswalk.get('policy'),at=crosswalk.get('at'),incomplete=crosswalk.get('incomplete_artists'),not_queried=crosswalk.get('not_queried_artists'))
        result['policy']='Read-only local catalogue snapshot, with observed public production UUIDs. This public crosswalk is not a transactionally consistent production DB/FK audit. Archived, unlinked and unexposed remote records may lack IDs; blanks do not prove absence. Stable slugs are the import key. Country means documented cultural affiliation, not birthplace or museum country. Publication remains in review.'
    else:
        with m.m.r.base.connect(True) as prod,prod.transaction():
            prod.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');prod_ids={}
            for table in ('artists','artworks','institutions'):prod_ids[table]={r['slug']:r['id'] for r in prod.execute('SELECT slug,id::text FROM '+table)}
    artist_fields=['artist_slug','local_artist_id','production_artist_id','display_name','aliases','birth_year','death_year','birth_display','death_display','entity_type','status','geography_review_state','cultural_affiliation_codes','country_relationships','country_evidence_urls','authority_ids','artwork_count']
    work_fields=['artwork_slug','local_artwork_id','production_artwork_id','public_artwork_url','title','alternate_title','creator_names','unlinked_creator_label','research_candidate','artist_slugs','artist_country_codes','creator_roles','creation_year_start','creation_year_end','date_precision','date_display','cutoff_classification','work_type','object_form','medium_text','dimensions_text','institution_slug','institution_name','institution_country_code','institution_official_url','accession_number','authority_ids','source_object_urls','image_url','image_source_page_url','image_rights_status','image_verified_at','image_license','image_license_url','image_credit','image_sha256','status','created_this_session']
    work_fields+=['local_image_path','image_delivery_state']
    compact_fields=[k for k in work_fields if k not in ('alternate_title','medium_text','dimensions_text','image_source_page_url','image_license_url','image_credit','institution_official_url','image_sha256','local_image_path')]
    outputs={'painters':CSV(root,'painters_country_inventory',artist_fields),'country_gaps':CSV(root,'painters_country_gaps',artist_fields),'identity':CSV(root,'artwork_identity_index',compact_fields,25000),'new':CSV(root,'artworks_added_this_session',work_fields)}
    for code in COUNTRY_CODES:outputs[code]=CSV(root,'artworks_'+code,work_fields,20000)
    artist_index={};counts=collections.Counter();institutions={};last=None;pages=0;unmapped=collections.defaultdict(list)
    with m.m.r.base.connect(False) as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');db.execute("SET LOCAL statement_timeout='180s'")
        countries=db.execute('SELECT code,name,region_code,historical_note FROM countries ORDER BY code').fetchall();CORE.save_new(root/'country_taxonomy.json',countries)
        for row in db.execute("SELECT i.id::text,i.slug,i.name,i.website_url,i.wikidata_id,i.status,p.country_code FROM institutions i LEFT JOIN places p ON p.id=i.place_id"):
            institutions[row['id']]=row
        artist_last=None
        while True:
            rows=db.execute("SELECT to_jsonb(a) row FROM artists a"+(' WHERE a.id>%s::uuid' if artist_last else '')+' ORDER BY a.id LIMIT 500',(artist_last,) if artist_last else ()).fetchall()
            if not rows:break
            ids=[r['row']['id'] for r in rows];aliases=collections.defaultdict(list);relationships=collections.defaultdict(list);authorities=collections.defaultdict(list);evidence=collections.defaultdict(set)
            for r in db.execute('SELECT artist_id::text,alias FROM artist_aliases WHERE artist_id=ANY(%s::uuid[]) ORDER BY alias',(ids,)):aliases[r['artist_id']].append(r['alias'])
            for r in db.execute('SELECT artist_id::text,country_code,relationship_type,is_primary,note FROM artist_countries WHERE artist_id=ANY(%s::uuid[]) ORDER BY country_code,relationship_type',(ids,)):relationships[r.pop('artist_id')].append(r)
            for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY scheme,external_id",(ids,)):authorities[r.pop('entity_id')].append(r)
            for r in db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) AND field_name IN ('geography','geography_primary_authority','museum_country_review_20260913','smk_country_review_20260913') AND source_url IS NOT NULL",(ids,)):evidence[r['entity_id']].add(r['source_url'])
            numbers={r['artist_id']:r['n'] for r in db.execute("SELECT aa.artist_id::text,count(*) n FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) AND w.status<>'archived' GROUP BY aa.artist_id",(ids,))}
            for row in rows:
                a=row['row'];aid=a['id'];codes=sorted({c['country_code'] for c in relationships[aid] if c['relationship_type']=='cultural_affiliation'})
                artist_index[aid]=dict(slug=a['slug'],name=a['display_name'],codes=codes)
                rec={k:a.get(k) for k in artist_fields};rec.update(artist_slug=a['slug'],local_artist_id=aid,production_artist_id=prod_ids['artists'].get(a['slug']),aliases=aliases[aid],cultural_affiliation_codes=';'.join(codes),country_relationships=relationships[aid],country_evidence_urls=sorted(evidence[aid]),authority_ids=authorities[aid],artwork_count=numbers.get(aid,0))
                outputs['painters'].add(rec)
                if a['status']=='review' and not codes:outputs['country_gaps'].add(rec)
                if not rec['production_artist_id']:unmapped['artists'].append(a['slug'])
            artist_last=ids[-1]
        while True:
            rows=db.execute("SELECT to_jsonb(w) work,artline_creation_scope(w.creation_year_start,w.creation_year_end,w.date_precision) cutoff FROM artworks w"+(' WHERE w.id>%s::uuid' if last else '')+' ORDER BY w.id LIMIT 500',(last,) if last else ()).fetchall()
            if not rows:break
            ids=[r['work']['id'] for r in rows];makers=collections.defaultdict(list);authorities=collections.defaultdict(list);sources=collections.defaultdict(set);own_source_ids=set()
            for r in db.execute('SELECT artwork_id::text,artist_id::text,attribution_role FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artist_id,attribution_role',(ids,)):
                a=artist_index[r['artist_id']];makers[r['artwork_id']].append(dict(**a,role=r['attribution_role']))
            for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY scheme,external_id",(ids,)):authorities[r.pop('entity_id')].append(r)
            for r in db.execute("SELECT c.entity_id::text,c.source_url,s.slug source_slug FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artwork' AND c.entity_id=ANY(%s::uuid[]) AND c.source_url IS NOT NULL ORDER BY c.entity_id,c.source_url",(ids,)):
                url=r['source_url']
                if not url.split('?')[0].endswith(('.csv','.zip','.json')):sources[r['entity_id']].add(url)
                if r['source_slug'] in ('overnight-country-artworks-20260913','overnight-greek-primary-20260913','overnight-tzanes-met-primary-20260913','overnight-kmska-triptych-primary-20260913'):own_source_ids.add(r['entity_id'])
            mids=list({r['work']['primary_media_id'] for r in rows if r['work']['primary_media_id']});media={r['id']:r for r in db.execute('SELECT id::text,storage_path,delivery_url,source_page_url,rights_status,verified_at,alt_text,license_label,license_url,creator_credit,checksum_sha256 FROM media_assets WHERE id=ANY(%s::uuid[])',(mids,))} if mids else {}
            for row in rows:
                w=row['work'];aid=w['id'];cs=makers[aid];inst=institutions.get(w['current_institution_id'],{});im=media.get(w['primary_media_id'],{});codes=sorted({code for a in cs for code in a['codes'] if a['role'] in ('primary','attributed_to','workshop','circle_of','follower_of')})
                rec={k:w.get(k) for k in work_fields};created=(aid in own_new_ids) if own_new_ids is not None else (aid in own_source_ids and datetime.datetime.fromisoformat(w['created_at'])>=datetime.datetime.fromisoformat(START))
                rec.update(artwork_slug=w['slug'],local_artwork_id=aid,production_artwork_id=prod_ids['artworks'].get(w['slug']),creator_names='; '.join(a['name'] for a in cs),artist_slugs=';'.join(a['slug'] for a in cs),artist_country_codes=';'.join(codes),creator_roles=cs,cutoff_classification=row['cutoff'],institution_slug=inst.get('slug'),institution_name=inst.get('name'),institution_country_code=inst.get('country_code'),institution_official_url=inst.get('website_url'),authority_ids=authorities[aid],source_object_urls=sorted(sources[aid]),image_url=(m.SITE+im['storage_path'] if im.get('storage_path') else im.get('delivery_url')) if im.get('verified_at') and im.get('rights_status') in ('public_domain','cc0','cc_by','cc_by_sa','licensed') and (im.get('alt_text') or '').strip() else None,image_source_page_url=im.get('source_page_url'),image_rights_status=im.get('rights_status'),image_verified_at=im.get('verified_at'),image_license=im.get('license_label'),image_license_url=im.get('license_url'),image_credit=im.get('creator_credit'),image_sha256=im.get('checksum_sha256'),created_this_session=created)
                primary=next((a for a in cs if a['role']=='primary'),None)
                rec['local_image_path']=str(m.x.ROOT/'apps/web/public'/im['storage_path'].lstrip('/')) if im.get('storage_path') else None
                rec['image_delivery_state']=('local_and_production_verified_this_session' if w['primary_media_id'] in session_verified_media else 'existing_catalogue_image_delivery_not_rechecked_this_session') if rec['image_url'] else 'no_verified_delivery'
                if w['primary_media_id'] in local_only_media:rec['image_url']=None;rec['image_delivery_state']='local_only_production_pending_cloud_login'
                if w['status']!='archived' and primary and rec['production_artwork_id']:rec['public_artwork_url']=m.SITE+'/artists/'+primary['slug']+'/works/'+rec['production_artwork_id']
                outputs['identity'].add({k:rec[k] for k in compact_fields});counts[w['status']]+=1
                if created:outputs['new'].add(rec)
                if w['status']!='archived':
                    for code in COUNTRY_CODES:
                        if code in codes:outputs[code].add(rec)
                if not rec['production_artwork_id']:unmapped['artworks'].append(w['slug'])
            last=ids[-1];pages+=1
            if pages%20==0:print('Handoff exported',pages*500,'artworks',flush=True)
            if max_pages and pages>=max_pages:break
        redirects=db.execute("SELECT r.entity_type,r.entity_id::text,r.old_slug,CASE r.entity_type WHEN 'artist' THEN a.slug WHEN 'artwork' THEN w.slug WHEN 'institution' THEN i.slug END canonical_slug FROM slug_redirects r LEFT JOIN artists a ON r.entity_type='artist' AND a.id=r.entity_id LEFT JOIN artworks w ON r.entity_type='artwork' AND w.id=r.entity_id LEFT JOIN institutions i ON r.entity_type='institution' AND i.id=r.entity_id ORDER BY r.entity_type,r.old_slug").fetchall();CORE.save_new(root/'canonical_redirects.json',redirects)
    for k,v in outputs.items():result['files'][k]=v.finish()
    result.update(artwork_status_counts=dict(counts),missing_production_slug_crosswalk=dict(unmapped),institutions=len(institutions),painters=len(artist_index),csv_encoding='UTF-8 with BOM; RFC4180 quoting; JSON arrays in multivalue cells. Literal formula-leading values prefixed with a single apostrophe, counted per file. Do not treat that escape as part of source content.',source_url_caveat='Source URL lists include research evidence and may include creator pages; an exact museum physical-object ID must still be verified. Existing country assignments remain review evidence, not published facts.')
    CORE.save_new(root/'manifest.json',result)
    if not create_archive:
        print('Handoff snapshot complete; final packaging deferred',phase,result['artwork_status_counts'],flush=True)
        return
    archive=root.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(root.iterdir()):z.write(p,p.name)
        z.write(BASE/'chatgpt-handoff/RESEARCH_PROMPT.md','RESEARCH_PROMPT.md')
    CORE.save_new(root.parent/(phase+'-archive-receipt.json'),dict(at=CORE.now(),path=str(archive),sha256=CORE.sha(archive.read_bytes()),bytes=archive.stat().st_size));print('Handoff snapshot complete',phase,result['artwork_status_counts'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--phase',required=True);p.add_argument('--max-pages',type=int);p.add_argument('--production-crosswalk',type=Path);p.add_argument('--session-index',type=Path);p.add_argument('--no-archive',action='store_true');a=p.parse_args()
    assert a.phase and all(c.isalnum() or c in '-_' for c in a.phase);export(a.phase,a.max_pages,a.production_crosswalk,a.session_index,not a.no_archive)
