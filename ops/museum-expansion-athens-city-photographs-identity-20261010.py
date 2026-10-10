"""Bounded source/title/image and creator-authority research; no production writes."""
import importlib.util
import json
import re
import time
from pathlib import Path

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-athens-city-photographs-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
ARTCOLS='a.id::text,a.slug,a.title,a.normalized_title,a.alternate_title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.accession_number,a.current_institution_id::text,a.medium_text,a.dimensions_text,a.work_type,a.unlinked_creator_label,a.status,a.primary_media_id::text'
TERMS=['bakour','bakur','μπακουρ','μπακούρ','koutsap','kotsap','κουτσαπ','κοτσαπ']
TRANSLATIONS={}

def main():
    assert not(RUN/'production-identity-001.json.gz').exists()
    rows=m.load(RUN/'editorial-source-decisions-001.json.gz')['rows'];frames=m.load(RUN/'visual-references-001.json')['rows']
    titles=sorted({m.norm(t) for x in rows for t in [x['title'],x['original_title']]+TRANSLATIONS.get(x['number'],[]) if t})
    urls=sorted({x[k] for x in rows for k in ['source_url','native_url']});sids=[x['source_id'] for x in rows]
    creator_names=sorted({m.norm(n) for x in rows for n in x['creator_source_literals'] if n not in ['Άγνωστος Δημιουργός','Αγνώστου','Pinx R. A.','The New York Public LibraryDigital collections.','Eastman Kodak Co.']})
    params=dict(titles=titles,urls=urls,source_ids=sids,image_checksums=sorted({x['sha256'] for x in frames}),creator_names=creator_names,creator_stems=TERMS,translation_leads=TRANSLATIONS)
    plans={};timings={}
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        before=m.load(RUN/'production-initial-scope-001.json.gz');assert c.snapshot(db,before['scoped_ids'])==before['snapshot']
        def query(key,sql,args):
            plans[key]=db.execute('EXPLAIN (FORMAT JSON) '+sql,args).fetchone();start=time.monotonic();data=db.execute(sql,args).fetchall();timings[key]=dict(seconds=round(time.monotonic()-start,3),rows=len(data));print(json.dumps(dict(query=key,**timings[key])),flush=True);return data
        pattern='|'.join(re.escape(t) for t in TERMS);like=['%'+m.norm(t)+'%' for t in TERMS]
        artists=query('artists','SELECT id::text,display_name,normalized_name,slug,birth_year,death_year,status FROM artists WHERE normalized_name=ANY(%s) OR normalized_name LIKE ANY(%s) OR display_name ~* %s ORDER BY id',(creator_names,like,pattern))
        aliases=query('artist_aliases','SELECT aa.artist_id::text,aa.alias,a.display_name FROM artist_aliases aa JOIN artists a ON a.id=aa.artist_id WHERE aa.normalized_alias=ANY(%s) OR aa.normalized_alias LIKE ANY(%s) OR aa.alias ~* %s ORDER BY aa.artist_id,aa.alias',(creator_names,like,pattern))
        artist_ids=sorted({x['id'] for x in artists}|{x['artist_id'] for x in aliases});assert len(artist_ids)<=500
        linked=query('creator_scoped_works','SELECT DISTINCT artwork_id::text FROM artwork_artists WHERE artist_id=ANY(%s::uuid[]) ORDER BY artwork_id LIMIT10001'.replace('LIMIT10001','LIMIT 10001'),(artist_ids,));assert len(linked)<=10000
        exact=query('exact_titles','SELECT id::text FROM artworks WHERE normalized_title=ANY(%s) ORDER BY id LIMIT 10001',(titles,));assert len(exact)<=10000
        unlinked=query('unlinked_creators','SELECT id::text FROM artworks WHERE unlinked_creator_label ~* %s ORDER BY id LIMIT 10001',(pattern,));assert len(unlinked)<=10000
        sources=query('source_citations',"SELECT entity_id::text,source_url,source_record_id,field_name FROM citations WHERE entity_type='artwork' AND (source_url=ANY(%s) OR source_url LIKE 'https://portal.athenscitymuseum.gr/artworks/%%' OR source_url LIKE 'https://www.searchculture.gr/aggregator/edm/DigAthensMuseum/%%' OR (source_record_id=ANY(%s) AND source_url LIKE 'https://www.searchculture.gr/%%')) ORDER BY entity_id,source_url,source_record_id",(urls,sids))
        identifiers=query('source_identifiers',"SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR canonical_url LIKE 'https://portal.athenscitymuseum.gr/artworks/%%' OR canonical_url LIKE 'https://www.searchculture.gr/aggregator/edm/DigAthensMuseum/%%' OR (scheme='searchculture-edm' AND external_id=ANY(%s))) ORDER BY entity_id,scheme,external_id",(urls,sids))
        media=query('image_checksums','SELECT to_jsonb(x) row FROM media_assets x WHERE checksum_sha256=ANY(%s) OR source_page_url=ANY(%s) ORDER BY id',(params['image_checksums'],urls));media=[x['row'] for x in media];mids=[x['id'] for x in media]
        media_links=query('image_links','SELECT artwork_id::text,media_id::text,sort_order,view_label FROM artwork_media WHERE media_id=ANY(%s::uuid[]) ORDER BY artwork_id,media_id',(mids,))
        primary=query('primary_images','SELECT id::text FROM artworks WHERE primary_media_id=ANY(%s::uuid[]) ORDER BY id',(mids,))
        ids=sorted(set(before['scoped_ids'])|{x.get('artwork_id',x.get('id')) for x in linked+exact+unlinked+media_links+primary}|{x['entity_id'] for x in sources+identifiers});assert len(ids)<=20000
        arts=query('bounded_artworks','SELECT '+ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(ids,))
        links=query('bounded_artist_links','SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id,aa.attribution_role',(ids,))
        cites=query('bounded_citations',"SELECT to_jsonb(x) row FROM citations x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(ids,));cites=[x['row'] for x in cites]
    comparisons=[]
    for row in rows:
        rt={m.norm(t) for t in [row['title'],row['original_title']]+TRANSLATIONS.get(row['number'],[])}
        source_hits=[x for x in sources+identifiers if x.get('source_record_id',x.get('external_id'))==row['source_id'] or x.get('source_url',x.get('canonical_url')) in [row['source_url'],row['native_url']]]
        matches=[x for x in arts if rt&{m.norm(x[k]) for k in ['title','alternate_title'] if x[k]}]
        comparisons.append(dict(number=row['number'],source_id=row['source_id'],source_hits=source_hits,title_hits=matches,decision=row['decision']))
    state=dict(artists=artists,aliases=aliases,artist_ids=artist_ids,artwork_ids=ids,artworks=arts,creator_links=links,source_citations=sources,source_identifiers=identifiers,matching_media=media,matching_media_links=media_links,query_plans=plans,query_timings=timings,scoped_ids=before['scoped_ids'])
    m.save(RUN/'production-identity-001.json.gz',dict(at=m.now(),read_only=True,params=params,state=state,comparisons=comparisons,source_reference=c.ref(RUN/'editorial-source-decisions-001.json.gz'),script_reference=c.ref(Path(__file__).resolve()),limitation='Bounded source, literal/title-translation, creator/alias and image research. Returned IDs enriched in batches. No canonical accessions fabricated from thumbnail labels; those remain comparison evidence. Artist hits are not approved links. No exhaustive duplicate guarantee or10million-row performance claim.'))
    m.save(RUN/'production-identity-citations-001.json.gz',dict(at=m.now(),read_only=True,citations=cites))
    print(json.dumps(dict(artworks=len(ids),artists=len(artist_ids),citations=len(cites),source_hit_records=sum(bool(x['source_hits']) for x in comparisons),image_matches=len(media))),flush=True)

if __name__=='__main__':main()
