#!/usr/bin/env python3
"""Export live catalogue statistics and research worksheets. Database access is read-only.

Production supplies research rows; local UUIDs are a separately timestamped
crosswalk. No ingestion, image downloads, authored descriptions or credentials
are included. CSV cells are literal text and existing snapshots are preserved.
"""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import quote, urlsplit, parse_qsl

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://artline-web-lpuqqlugnq-ew.a.run.app'
IMAGE_OK = """coalesce(ma.verified_at IS NOT NULL
 AND ma.rights_status IN ('public_domain','cc0','cc_by','cc_by_sa','licensed')
 AND nullif(trim(ma.alt_text),'') IS NOT NULL
 AND nullif(trim(ma.storage_path),'') IS NOT NULL,false)"""
PAINTED = "(w.work_type IN ('painting','fresco','watercolor') OR w.object_form IN ('icon','painted_panel','altarpiece','mural'))"
BLOCKED = ('art500k', 'reference-state.sqlite', 'reference-cache')

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def public_url(value):
    if not value:
        return ''
    try:
        p = urlsplit(value)
        if p.scheme not in ('https','http') or not p.hostname or p.username or p.password:
            return ''
        if p.hostname in ('localhost','127.0.0.1','::1') or p.hostname.endswith('.local'):
            return ''
        if any(x in value.lower() for x in BLOCKED):
            return ''
        if any(re.search(r'key|token|secret|signature|credential|authorization',k,re.I) for k,_ in parse_qsl(p.query)):
            return ''
        return value
    except ValueError:
        return ''

def cell(v):
    if v is None:
        return ''
    if isinstance(v,(dict,list)):
        v=json.dumps(v,ensure_ascii=False,separators=(',',':'),default=str)
    elif isinstance(v,bool):
        v='true' if v else 'false'
    else:
        v=str(v)
    if any(x in v.lower() for x in BLOCKED):
        raise ValueError('Private research marker in export field')
    if v.lstrip().startswith(('=','+','-','@')) or v.startswith(('\t','\r','\n')):
        return "'"+v
    return v

class Sheet:
    def __init__(self, root, name, fields):
        self.path=root/name; self.name=name; self.fields=fields; self.rows=0
        self.file=self.path.open('x',encoding='utf-8-sig',newline='')
        self.writer=csv.DictWriter(self.file,fieldnames=fields,extrasaction='raise')
        self.writer.writeheader()
    def add(self, record):
        self.writer.writerow({k:cell(record.get(k)) for k in self.fields}); self.rows+=1
    def close(self):
        self.file.close()
        with self.path.open(encoding='utf-8-sig',newline='') as f:
            r=csv.reader(f); assert next(r)==self.fields
            n=0
            for row in r:
                assert len(row)==len(self.fields), self.path.name
                assert all(not v.lstrip().startswith(('=','+','-','@')) for v in row)
                n+=1
            assert n==self.rows
        return dict(file=self.name,rows=self.rows,bytes=self.path.stat().st_size,
                    sha256=hashlib.sha256(self.path.read_bytes()).hexdigest())

def connect(dsn):
    return psycopg.connect(dsn,row_factory=dict_row,connect_timeout=15,
                          options='-c default_transaction_read_only=on')

def begin(db):
    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
    db.execute("SET LOCAL statement_timeout='180s'")
    assert db.execute("SHOW transaction_read_only").fetchone()['transaction_read_only']=='on'

def stats(db):
    out={'snapshot_at':str(db.execute('SELECT now() at').fetchone()['at'])}
    out['artist_status'] = db.execute('SELECT entity_type,status,count(*) n FROM artists GROUP BY 1,2 ORDER BY 1,2').fetchall()
    out['artwork_status'] = db.execute('SELECT status,count(*) n FROM artworks GROUP BY 1 ORDER BY 1').fetchall()
    out['painters'] = db.execute("""WITH counts AS (
      SELECT aa.artist_id,count(DISTINCT aa.artwork_id) n FROM artwork_artists aa
      JOIN artworks w ON w.id=aa.artwork_id AND w.status<>'archived' GROUP BY aa.artist_id)
      SELECT count(*) active_profiles,count(*) FILTER(WHERE a.entity_type='person') named_people,
       count(*) FILTER(WHERE coalesce(d.is_popular,false)) popular_profiles,
       count(*) FILTER(WHERE coalesce(c.n,0)>0) with_artworks,
       count(*) FILTER(WHERE coalesce(c.n,0)=0) without_artworks,
       count(*) FILTER(WHERE NOT EXISTS(SELECT 1 FROM artist_countries ac WHERE ac.artist_id=a.id
         AND ac.relationship_type='cultural_affiliation')) missing_cultural_country,
       count(*) FILTER(WHERE a.birth_year IS NULL) missing_birth_year,
       count(*) FILTER(WHERE a.death_year IS NULL) missing_death_year,
       count(*) FILTER(WHERE nullif(trim(a.biography_md),'') IS NULL) missing_biography,
       count(*) FILTER(WHERE NOT EXISTS(SELECT 1 FROM external_identifiers e
         WHERE e.entity_type='artist' AND e.entity_id=a.id)) without_authority_id
      FROM artists a LEFT JOIN counts c ON c.artist_id=a.id
      LEFT JOIN artist_discovery_selection d ON d.artist_id=a.id WHERE a.status<>'archived'""").fetchone()
    out['works_by_type'] = db.execute(f"""WITH popularity AS (
      SELECT DISTINCT aa.artwork_id FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id
      JOIN artist_discovery_selection d ON d.artist_id=a.id AND d.is_popular WHERE a.status<>'archived')
      SELECT w.work_type,count(*) active_artworks,
        count(*) FILTER(WHERE w.primary_media_id IS NULL) no_primary_image,
        count(*) FILTER(WHERE {IMAGE_OK}) displayable_image,
        count(*) FILTER(WHERE NOT ({IMAGE_OK})) no_displayable_image,
        count(*) FILTER(WHERE p.artwork_id IS NOT NULL) popular_artworks,
        count(*) FILTER(WHERE p.artwork_id IS NOT NULL AND w.primary_media_id IS NULL) popular_no_primary_image,
        count(*) FILTER(WHERE p.artwork_id IS NOT NULL AND NOT ({IMAGE_OK})) popular_no_displayable_image
      FROM artworks w LEFT JOIN media_assets ma ON ma.id=w.primary_media_id
      LEFT JOIN popularity p ON p.artwork_id=w.id WHERE w.status<>'archived'
      GROUP BY w.work_type ORDER BY active_artworks DESC""").fetchall()
    out['work_gaps'] = db.execute("""SELECT
       count(*) FILTER(WHERE current_institution_id IS NULL) no_recorded_institution,
       count(*) FILTER(WHERE nullif(trim(accession_number),'') IS NULL) no_accession,
       count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='review') date_requires_review,
       count(*) FILTER(WHERE NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=w.id)) no_linked_creator
      FROM artworks w WHERE w.status<>'archived'""").fetchone()
    out['country_counts'] = db.execute("""SELECT co.code,co.name,count(DISTINCT a.id) active_profiles,
       count(DISTINCT a.id) FILTER(WHERE d.is_popular) popular_profiles
      FROM artist_countries ac JOIN artists a ON a.id=ac.artist_id AND a.status<>'archived'
      JOIN countries co ON co.code=ac.country_code
      LEFT JOIN artist_discovery_selection d ON d.artist_id=a.id
      WHERE ac.relationship_type='cultural_affiliation' GROUP BY co.code,co.name ORDER BY active_profiles DESC,co.code""").fetchall()
    return out

PAINTER_PROPOSED = ['proposed_name','proposed_country_codes','country_evidence_url',
 'country_evidence_fact','proposed_birth_year','proposed_death_year','date_evidence_url',
 'proposed_artist_authority_url','proposed_artist_source_url','research_outcome','research_notes','checked_at']
WORK_PROPOSED = ['proposed_title','proposed_artist_slug','proposed_artist_name',
 'proposed_artist_authority_url','proposed_attribution_role','proposed_country_codes','country_evidence_url',
 'proposed_date_text','proposed_year_start','proposed_year_end','proposed_date_precision','date_evidence_url',
 'proposed_work_type','proposed_medium','proposed_dimensions','proposed_museum','proposed_museum_url',
 'proposed_museum_country_code','proposed_accession_number','proposed_source_object_id',
 'verified_source_name','verified_source_record_url','metadata_terms_url','proposed_image_url',
 'proposed_image_source_page_url','proposed_thumbnail_url','proposed_iiif_manifest_url',
 'proposed_image_license','proposed_image_license_url','image_rights_evidence_url','image_rights_fact',
 'image_attribution','image_creator_credit','proposed_image_width','proposed_image_height',
 'visual_match_verified','image_rights_result','research_outcome','research_notes','checked_at']

def related(db,kind,ids):
    auth=collections.defaultdict(list); urls=collections.defaultdict(set)
    for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type=%s AND entity_id=ANY(%s::uuid[]) ORDER BY scheme,external_id",(kind,ids)):
        if any(x in str(r).lower() for x in BLOCKED): continue
        auth[r['entity_id']].append(dict(scheme=r['scheme'],id=r['external_id'],url=public_url(r['canonical_url'])))
    for r in db.execute("SELECT DISTINCT c.entity_id::text,c.source_url FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type=%s AND c.entity_id=ANY(%s::uuid[]) AND s.is_active AND c.source_url IS NOT NULL",(kind,ids)):
        u=public_url(r['source_url'])
        if u: urls[r['entity_id']].add(u)
    return auth,urls

def export(root, db, local_ids, summary, batch_size):
    files=[]; artists={}; count_rows={}
    for r in db.execute(f"""SELECT aa.artist_id::text,count(DISTINCT w.id) artworks,
       count(DISTINCT w.id) FILTER(WHERE w.work_type='painting') paintings,
       count(DISTINCT w.id) FILTER(WHERE w.primary_media_id IS NULL) no_primary_image,
       count(DISTINCT w.id) FILTER(WHERE NOT ({IMAGE_OK})) no_displayable_image,
       count(DISTINCT w.id) FILTER(WHERE w.work_type='painting' AND NOT ({IMAGE_OK})) paintings_no_displayable_image
      FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id AND w.status<>'archived'
      LEFT JOIN media_assets ma ON ma.id=w.primary_media_id GROUP BY aa.artist_id"""):
        count_rows[r.pop('artist_id')]=r
    countries=collections.defaultdict(list); aliases=collections.defaultdict(list)
    for r in db.execute('SELECT artist_id::text,country_code,relationship_type,is_primary FROM artist_countries ORDER BY country_code,relationship_type'):
        countries[r.pop('artist_id')].append(r)
    for r in db.execute('SELECT artist_id::text,alias FROM artist_aliases ORDER BY alias'):
        aliases[r['artist_id']].append(r['alias'])
    fields=['artist_slug','production_artist_id','local_artist_id','artist_name','entity_type','status','popular','popularity_rank',
       'artline_artist_url','current_aliases','current_birth_year','current_death_year','current_date_display',
       'current_country_codes','current_country_relationships','geography_review_state','has_biography',
       'current_authority_ids','current_source_urls','artworks','paintings','no_primary_image','no_displayable_image',
       'paintings_no_displayable_image','research_gaps']+PAINTER_PROPOSED
    sheet=Sheet(root,'painters_research.csv',fields); gaps=Sheet(root,'painters_country_gaps.csv',fields)
    last=None
    while True:
        rows=db.execute("""SELECT a.id::text,a.slug,a.display_name,a.entity_type,a.status,a.birth_year,a.death_year,
         a.birth_display,a.death_display,a.timeline_display,a.geography_review_state,
         nullif(trim(a.biography_md),'') IS NOT NULL has_biography,
         coalesce(d.is_popular,false) popular,d.popularity_rank FROM artists a
         LEFT JOIN artist_discovery_selection d ON d.artist_id=a.id
         WHERE a.status<>'archived' AND (%s::uuid IS NULL OR a.id>%s::uuid) ORDER BY a.id LIMIT 1000""",(last,last)).fetchall()
        if not rows: break
        ids=[a['id'] for a in rows]; auth,sources=related(db,'artist',ids)
        for a in rows:
            aid=a['id']; codes=sorted({x['country_code'] for x in countries[aid] if x['relationship_type']=='cultural_affiliation'})
            counts=count_rows.get(aid,dict(artworks=0,paintings=0,no_primary_image=0,no_displayable_image=0,paintings_no_displayable_image=0))
            missing=[]
            if not codes: missing.append('country')
            if not auth[aid]: missing.append('authority')
            if a['birth_year'] is None: missing.append('birth_year')
            if a['death_year'] is None: missing.append('death_year')
            if not counts['artworks']: missing.append('no_linked_artworks')
            row=dict(artist_slug=a['slug'],production_artist_id=aid,local_artist_id=local_ids['artists'].get(a['slug']),
             artist_name=a['display_name'],entity_type=a['entity_type'],status=a['status'],popular=a['popular'],popularity_rank=a['popularity_rank'],
             artline_artist_url=SITE+'/artists/'+quote(a['slug']),current_aliases=aliases[aid],current_birth_year=a['birth_year'],
             current_death_year=a['death_year'],current_date_display=a['timeline_display'],current_country_codes=';'.join(codes),
             current_country_relationships=countries[aid],geography_review_state=a['geography_review_state'],has_biography=a['has_biography'],
             current_authority_ids=auth[aid],current_source_urls=sorted(sources[aid]),research_gaps=';'.join(missing),**counts)
            sheet.add(row)
            if not codes:gaps.add(row)
            artists[aid]=row
        last=ids[-1]
    assert sheet.rows==summary['painters']['active_profiles']
    assert gaps.rows==summary['painters']['missing_cultural_country']
    files.extend([sheet.close(),gaps.close()]); print('Painter inventory exported',len(artists),flush=True)
    inst={r['id']:r for r in db.execute('SELECT i.id::text,i.slug,i.name,i.website_url,i.wikidata_id,p.country_code FROM institutions i LEFT JOIN places p ON p.id=i.place_id')}
    selected={r['id'] for r in db.execute("""SELECT la.artwork_id::text id FROM artwork_location_assertions la
      JOIN sources s ON s.id=la.source_id JOIN institutions i ON i.id=la.institution_id
      WHERE la.claim_type='holding' AND la.review_state='accepted' AND la.superseded_by IS NULL
      AND s.is_active AND i.status<>'archived' AND length(trim(la.evidence_note))>0 AND la.checked_at<=now()
      UNION SELECT ci.artwork_id::text FROM curated_collection_items ci JOIN curated_collections cc ON cc.id=ci.collection_id
      LEFT JOIN sources s ON s.id=ci.source_id WHERE cc.status<>'archived' AND length(trim(ci.reason))>0
      AND (cc.curator_kind='owner' OR (s.is_active AND ci.source_url IS NOT NULL AND ci.checked_at<=now()))""")}
    identity_fields=['artwork_slug','production_artwork_id','local_artwork_id','status','artline_artwork_url','current_title',
      'current_artist_slugs','current_creator_relationships','current_unlinked_creator_label','current_country_codes',
      'popular','current_date_text','current_year_start','current_year_end','current_date_precision','date_scope',
      'current_work_type','current_object_form','current_medium','current_dimensions','current_museum_slug',
      'current_museum','current_museum_country_code','current_museum_url','current_accession_number',
      'current_authority_ids','current_source_urls','selection_evidence_recorded','current_image_url','image_state',
      'current_image_source_page_url','current_image_license','current_image_license_url','current_image_credit']
    task_fields=['task_id','priority','research_gaps']+identity_fields+WORK_PROPOSED
    identity=Sheet(root,'existing_artworks_index.csv',identity_fields)
    queue=Sheet(root,'artwork_research_queue.csv',task_fields)
    starter=Sheet(root,'START_HERE_images_100.csv',task_fields)
    starter_groups=collections.defaultdict(list); exported=0; last=None; tasks=collections.Counter()
    while True:
        rows=db.execute(f"""SELECT w.id::text,w.slug,w.title,w.status,w.unlinked_creator_label,w.date_display,
          w.creation_year_start,w.creation_year_end,w.date_precision,w.work_type,w.object_form,w.medium_text,w.dimensions_text,
          w.current_institution_id::text,w.accession_number,w.primary_media_id::text,
          artline_creation_scope(w.creation_year_start,w.creation_year_end,w.date_precision) date_scope,
          {IMAGE_OK} image_ok,{PAINTED} painted,
          ma.storage_path,ma.source_page_url,ma.license_label,ma.license_url,ma.creator_credit
         FROM artworks w LEFT JOIN media_assets ma ON ma.id=w.primary_media_id
         WHERE (%s::uuid IS NULL OR w.id>%s::uuid) ORDER BY w.id LIMIT 2000""",(last,last)).fetchall()
        if not rows:break
        ids=[w['id'] for w in rows]; auth,sources=related(db,'artwork',ids); makers=collections.defaultdict(list)
        for r in db.execute("SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,a.slug,a.display_name,a.status FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY a.slug,aa.attribution_role",(ids,)):
            makers[r['artwork_id']].append(r)
        for w in rows:
            wid=w['id']; creators=makers[wid]; living=[a for a in creators if a['artist_id'] in artists]
            popular=any(artists[a['artist_id']]['popular'] for a in living)
            codes=sorted({code for a in living for code in artists[a['artist_id']]['current_country_codes'].split(';') if code})
            institution=inst.get(w['current_institution_id'],{}); primary=next((a for a in living if a['attribution_role']=='primary'),None)
            page=SITE+'/artists/'+quote(primary['slug'])+'/works/'+wid if primary and w['status']!='archived' else ''
            imurl=(SITE+w['storage_path'] if w['storage_path'].startswith('/') else public_url(w['storage_path'])) if w['image_ok'] else ''
            row=dict(artwork_slug=w['slug'],production_artwork_id=wid,local_artwork_id=local_ids['artworks'].get(w['slug']),status=w['status'],
              artline_artwork_url=page,current_title=w['title'],current_artist_slugs=';'.join(sorted({a['slug'] for a in creators})),
              current_creator_relationships=[dict(artist_slug=a['slug'],name=a['display_name'],role=a['attribution_role']) for a in creators],
              current_unlinked_creator_label=w['unlinked_creator_label'],current_country_codes=';'.join(codes),popular=popular,
              current_date_text=w['date_display'],current_year_start=w['creation_year_start'],current_year_end=w['creation_year_end'],
              current_date_precision=w['date_precision'],date_scope=w['date_scope'],current_work_type=w['work_type'],current_object_form=w['object_form'],
              current_medium=w['medium_text'],current_dimensions=w['dimensions_text'],current_museum_slug=institution.get('slug'),
              current_museum=institution.get('name'),current_museum_country_code=institution.get('country_code'),current_museum_url=public_url(institution.get('website_url')),
              current_accession_number=w['accession_number'],current_authority_ids=auth[wid],current_source_urls=sorted(sources[wid]),selection_evidence_recorded=wid in selected,
              current_image_url=imurl,image_state='displayable_in_db' if w['image_ok'] else 'missing' if w['primary_media_id'] is None else 'attached_but_not_displayable',
              current_image_source_page_url=public_url(w['source_page_url']),current_image_license=w['license_label'],current_image_license_url=public_url(w['license_url']),current_image_credit=w['creator_credit'])
            identity.add(row)
            if w['status']=='archived' or w['date_scope']=='excluded' or not (w['painted'] or w['work_type']=='unknown'):
                continue
            missing=[]
            if not w['image_ok']:missing.append('image')
            if not codes:missing.append('painter_country')
            if w['date_scope']=='review':missing.append('creation_date')
            if w['work_type']=='unknown':missing.append('object_type')
            if not institution:missing.append('holding_institution')
            if wid not in selected:missing.append('selection_evidence')
            if not creators:missing.append('creator_identity')
            if not missing:continue
            priority=1 if popular and w['painted'] and 'image' in missing else 2 if any(c in ('RU','GR') for c in codes) else 3 if w['painted'] else 4
            task=dict(task_id=wid,priority=priority,research_gaps=';'.join(missing),**row); queue.add(task);tasks.update(missing)
            if priority==1 and page and wid in selected and w['date_scope']=='eligible':
                group=primary['slug']; starter_groups[group].append(task)
                starter_groups[group].sort(key=lambda r:(not bool(r['current_source_urls']),r['current_title'],r['artwork_slug']))
                starter_groups[group]=starter_groups[group][:100]
        last=ids[-1];exported+=len(rows)
        if exported%20000==0:print('Artwork index exported',exported,flush=True)
    assert identity.rows==sum(r['n'] for r in summary['artwork_status'])
    # Spread the starter across painters, rather than assigning the entire first job to one name.
    remaining=100
    while remaining and any(starter_groups.values()):
        for slug in sorted(starter_groups):
            if starter_groups[slug] and remaining:
                starter.add(starter_groups[slug].pop(0)); remaining-=1
    assert starter.rows>0
    files.extend([identity.close(),queue.close(),starter.close()])
    with (root/'artwork_research_queue.csv').open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f); batch=None
        for n,row in enumerate(reader):
            if n%batch_size==0:
                if batch:files.append(batch.close())
                (root/'batches').mkdir(exist_ok=True)
                batch=Sheet(root,f'batches/artwork_research_{n//batch_size+1:04d}.csv',task_fields)
            batch.add(row)
        if batch:files.append(batch.close())
    new_fields=['candidate_id','existing_artwork_slug','artist_slug','action','status']+WORK_PROPOSED
    files.append(Sheet(root,'new_artworks_template.csv',new_fields).close())
    dictionary=Sheet(root,'field_dictionary.csv',['file_group','column','instruction'])
    instructions={
      'candidate_id':'Assign a unique research proposal ID; this is not an Artline database UUID.',
      'existing_artwork_slug':'For an existing-object proposal, copy the known catalogue slug; otherwise leave empty.',
      'action':'new_artwork | enrich_existing | possible_duplicate | distinct_related_object | hold',
      'proposed_country_codes':'Semicolon-separated existing country codes; cultural affiliation of creator, not museum location. Cite country_evidence_url.',
      'proposed_image_url':'Direct independently sourced image URL for this exact object. Never a search-result URL.',
      'proposed_image_license':'PDM, CC0, CC BY, or CC BY-SA with version. Empty if unresolved.',
      'proposed_image_license_url':'Complete exact licence URI including version; generic site terms do not automatically license the image.',
      'research_outcome':'verified_image | verified_metadata_only | needs_review | not_found | blocked | out_of_scope',
      'image_rights_result':'approved | unresolved | restricted; a public URL alone is not permission.',
      'visual_match_verified':'true only after inspecting the actual candidate image against independent object evidence; otherwise false.',
      'proposed_attribution_role':'Use primary/attributed_to/workshop/circle_of/follower_of/formerly_attributed_to. Preserve an after relationship in research_notes for review; it is not an existing role enum. Do not turn a prototype artist into the copyist.',
      'metadata_terms_url':'Source metadata licence or reuse terms URL; keep separate from the image licence.',
      'proposed_date_precision':'Use exact/circa/range/circa_range/decade/century/before/after/unknown according to source evidence.',
      'checked_at':'Actual retrieval time in ISO 8601 UTC. Do not copy the export timestamp as a research timestamp.',
      'image_rights_fact':'Brief evidence explaining why the exact reproduction is covered, including underlying work where relevant.',
      'image_attribution':'Complete required photographer/artist/institution credit, licence and changes notice when applicable.',
    }
    for group,cols in [('painters',fields),('artworks',task_fields),('new_artworks',new_fields)]:
        for col in cols:
            editable=col.startswith('proposed_') or col in PAINTER_PROPOSED or col in WORK_PROPOSED
            text=instructions.get(col,('Fill only with sourced research; leave unknown values blank.' if editable else 'Existing catalogue context/identifier: preserve without overwriting; not freshly verified evidence.'))
            if group=='new_artworks' and col=='status':text='Set review; this proposal does not publish the record.'
            if group=='new_artworks' and col=='artist_slug':text='Copy an existing painter slug when independently matched; leave empty for a new or unresolved creator.'
            dictionary.add(dict(file_group=group,column=col,instruction=text))
    files.append(dictionary.close())
    summary['research_queue']={'rows':queue.rows,'gaps_overlapping':dict(tasks),'starter_rows':starter.rows,'batch_size':batch_size}
    return files

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--batch-size',type=int,default=250);a=p.parse_args()
    if not 1<=a.batch_size<=1000: p.error('batch size must be 1..1000')
    root=a.output.resolve(); root.mkdir(parents=True,exist_ok=False)
    spec=importlib.util.spec_from_file_location('images',ROOT/'ops/enrich-artwork-images.py'); images=importlib.util.module_from_spec(spec);spec.loader.exec_module(images)
    with connect('postgres://localhost/artline') as local:
        begin(local); local_summary=stats(local)
        local_ids={t:{r['slug']:r['id'] for r in local.execute('SELECT slug,id::text FROM '+t)} for t in ('artists','artworks')}
    print('Local read-only snapshot complete',flush=True)
    with connect(images.cloud_dsn()) as prod:
        begin(prod); production_summary=stats(prod)
        files=export(root,prod,local_ids,production_summary,a.batch_size)
        taxonomy=Sheet(root,'country_taxonomy.csv',['code','name','region_code','historical_note'])
        for r in prod.execute('SELECT code,name,region_code,historical_note FROM countries ORDER BY code'):taxonomy.add(r)
        files.append(taxonomy.close())
        redirects=Sheet(root,'canonical_redirects.csv',['entity_type','old_slug','canonical_slug'])
        for r in prod.execute("SELECT r.entity_type,r.old_slug,coalesce(a.slug,w.slug,i.slug) canonical_slug FROM slug_redirects r LEFT JOIN artists a ON r.entity_type='artist' AND a.id=r.entity_id LEFT JOIN artworks w ON r.entity_type='artwork' AND w.id=r.entity_id LEFT JOIN institutions i ON r.entity_type='institution' AND i.id=r.entity_id ORDER BY r.entity_type,r.old_slug"):
            redirects.add(r)
        files.append(redirects.close())
    allstats={'generated_at':now(),'production':production_summary,'local':local_summary,
      'definitions':{'active':'status is not archived; includes review records, not a publication claim.',
       'image':'A nonempty primary storage path passes the Go catalogue image gate (verified timestamp, accepted rights status, alt text). This is a DB check, not a fresh HTTP or legal audit.',
       'country':'Documented cultural affiliation. Multiple affiliations counted in each country, so country totals overlap.',
       'painting':'work_type=painting only; frescoes/watercolours and unknown types reported separately.',
       'research_queue':'Active painting/fresco/watercolor/painted-form or unknown-type records; date_scope != excluded; at least one image/country/date/type/holding/creator/selection gap. Unknowns need verification, not automatic eligibility.',
       'source':'Production supplies CSV rows. Local UUID crosswalk and local totals are a separate read-only snapshot. Counts matching do not prove whole-database parity.'}}
    (root/'statistics.json').write_text(json.dumps(allstats,ensure_ascii=False,indent=2,default=str)+'\n')
    sf=Sheet(root,'statistics.csv',['database','category','metric','value'])
    for target,summary in [('production',production_summary),('local',local_summary)]:
        for category in ('painters','work_gaps'):
            for key,value in summary[category].items():sf.add(dict(database=target,category=category,metric=key,value=value))
        for r in summary['works_by_type']:
            for key,value in r.items():
                if key!='work_type':sf.add(dict(database=target,category=r['work_type'],metric=key,value=value))
    files.append(sf.close())
    cf=Sheet(root,'statistics_by_country.csv',['database','code','name','active_profiles','popular_profiles'])
    for target,summary in [('production',production_summary),('local',local_summary)]:
        for r in summary['country_counts']:cf.add(dict(database=target,**r))
    files.append(cf.close())
    (root/'manifest.json').write_text(json.dumps(dict(created_at=now(),database_read_only=True,primary_source='production',
      private_research_used=False,encoding='UTF-8 BOM, RFC4180; empty cells unknown; JSON arrays in multivalue cells; formula-leading text escaped with apostrophe',
      files=files),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(production=production_summary['painters'],research_queue=production_summary['research_queue'],files=len(files))))

if __name__=='__main__':
    main()
