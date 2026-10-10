"""Bounded read-only identity search for selected Zongolopoulos objects and prepared images."""
import difflib
import importlib.util
import json
import re
import time
from pathlib import Path

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-zongolopoulos-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
# Search expansions only, not authority identifications or attribution changes.
ARTCOLS='a.id::text,a.slug,a.title,a.normalized_title,a.alternate_title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.accession_number,a.current_institution_id::text,a.medium_text,a.dimensions_text,a.work_type,a.unlinked_creator_label,a.status,a.primary_media_id::text'

def research_rows():
    return [dict(v,research_wave=wave) for root,wave in [(c.RESEARCH,'first'),(c.DATED,'dated')] for v in m.load(root/'editorial-source-decisions-001.json.gz')['rows']]

TRANSLATIONS={'Αλέξανδρος':['Alexander'],'Ποσειδώνας':['Poseidon'],'Προμηθέας':['Prometheus'],'Ποιητής':['Poet','The Poet'],'Μάνα Κύπρος':['Mother Cyprus'],'Άλογο':['Horse'],'Κατσίκα':['Goat'],'Ελιά':['Olive'],'Κυκλώπειο':['Cyclopean'],'Σύνθεση':['Composition'],'Μνημείο Ζαλόγγου':['Zalongo Monument'],'Αρχαιολογικόν Μουσείον Μαντίνειας':['Archaeological Museum of Mantineia','Archaeological Museum of Mantinea'],'Μυκήνες':['Mycenae'],'Νεκρή φύση':['Still Life'],'Ελένη':['Helen','Eleni'],'Παρέα μουσικών':['Group of Musicians'],'Εξοχική κατοικία':['Country House'],'Μανάβικο στην Κέρκυρα':['Greengrocer in Corfu'],'Μουράγιο Κέρκυρα':['Quay Corfu']}

def params():
    rows=research_rows();terms=['zongol','zoggol','zongop','paschalid','paskhalid','ζογγολ','ζογγόλ','ζογκολο','πασχαλ','πασχάλ']
    images=[v for root in [c.RESEARCH,c.DATED] for v in m.load(root/'visual-references-001.json')['rows']]
    urls=sorted({v['source_url']for v in rows})
    return dict(terms=terms,creator_pattern='|'.join(terms),normalized_patterns=['%'+m.norm(t)+'%'for t in terms],titles=sorted({m.norm(t)for v in rows for t in [v['title']]+TRANSLATIONS.get(v['title'],[])}),urls=urls,source_ids=[v['source_id']for v in rows],accession_keys=sorted({v['inventory_source_literal']for v in rows}),image_checksums=sorted({v['sha256']for v in images}),translation_leads=TRANSLATIONS,limits='Generic English Untitled/Abstract titles alone do not establish identity; named artist scopes and all literal Greek titles are searched. Unknown dates and export inventory strings are not normalized into assumed metadata.')

def queries(db,p):
    plans={};timings={}
    def query(key,sql,args):
        plans[key]=db.execute('EXPLAIN (FORMAT JSON) '+sql,args).fetchone();start=time.monotonic();rows=db.execute(sql,args).fetchall()
        timings[key]=dict(seconds=round(time.monotonic()-start,3),rows=len(rows));print(json.dumps(dict(query=key,**timings[key])),flush=True);return rows
    artists=query('artists','SELECT id::text,display_name,normalized_name,slug,birth_year,death_year FROM artists WHERE normalized_name LIKE ANY(%s) OR display_name ~* %s ORDER BY id',(p['normalized_patterns'],p['creator_pattern']))
    aliases=query('aliases','SELECT aa.artist_id::text,aa.alias,a.display_name FROM artist_aliases aa JOIN artists a ON a.id=aa.artist_id WHERE aa.normalized_alias LIKE ANY(%s) OR aa.alias ~* %s ORDER BY aa.artist_id,aa.alias',(p['normalized_patterns'],p['creator_pattern']))
    artist_ids=sorted({a['id'] for a in artists}|{a['artist_id'] for a in aliases})
    linked=query('artist_works','SELECT DISTINCT artwork_id::text FROM artwork_artists WHERE artist_id=ANY(%s::uuid[]) ORDER BY artwork_id LIMIT 100001',(artist_ids,));assert len(linked)<=100000
    unlinked=query('unlinked_labels','SELECT id::text FROM artworks WHERE unlinked_creator_label ~* %s ORDER BY id LIMIT 20001',(p['creator_pattern'],));assert len(unlinked)<=20000
    exact=query('exact_titles','SELECT id::text FROM artworks WHERE normalized_title=ANY(%s) ORDER BY id LIMIT 20001',(p['titles'],));assert len(exact)<=20000
    accession=query('literal_accessions','SELECT id::text FROM artworks WHERE accession_number=ANY(%s) ORDER BY id LIMIT 20001',(p['accession_keys'],));assert len(accession)<=20000
    cites=query('source_citations',"SELECT entity_id::text,source_url,field_name,source_record_id FROM citations WHERE entity_type='artwork' AND (source_url=ANY(%s) OR source_url LIKE 'https://%%zongolopoulos.gr/%%' OR source_url LIKE 'https://www.searchculture.gr/aggregator/edm/ZoggopoulosF/%%' OR (source_record_id=ANY(%s) AND source_url LIKE 'https://www.searchculture.gr/%%')) ORDER BY entity_id,source_url,field_name",(p['urls'],p['source_ids']))
    ex=query('source_identifiers',"SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR canonical_url LIKE 'https://%%zongolopoulos.gr/%%' OR canonical_url LIKE 'https://www.searchculture.gr/aggregator/edm/ZoggopoulosF/%%' OR (scheme='searchculture-edm' AND external_id=ANY(%s))) ORDER BY entity_id,scheme,external_id",(p['urls'],p['source_ids']))
    media=query('image_checksums','SELECT to_jsonb(x) row FROM media_assets x WHERE checksum_sha256=ANY(%s) ORDER BY id',(p['image_checksums'],));media=[x['row'] for x in media]
    mids=[x['id'] for x in media]
    media_links=query('matching_image_links','SELECT artwork_id::text,media_id::text,sort_order,view_label FROM artwork_media WHERE media_id=ANY(%s::uuid[]) ORDER BY artwork_id,media_id',(mids,))
    primary=query('matching_primary_images','SELECT id::text FROM artworks WHERE primary_media_id=ANY(%s::uuid[]) ORDER BY id',(mids,))
    scoped=m.load(RUN/'production-initial-scope-001.json.gz')['scoped_ids']
    ids=sorted(set(scoped)|{x.get('artwork_id',x.get('id')) for x in linked+unlinked+exact+accession+media_links+primary}|{x['entity_id'] for x in cites+ex});assert len(ids)<=120000
    artworks=query('bounded_artworks','SELECT '+ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(ids,))
    links=query('bounded_creator_links','SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id,aa.attribution_role',(ids,))
    return dict(artists=artists,aliases=aliases,artist_ids=artist_ids,artwork_ids=ids,artworks=artworks,creator_links=links,source_citations=cites,source_identifiers=ex,matching_media=media,matching_media_links=media_links,
        scoped_ids=scoped,query_plans=plans,query_timings=timings,limitation='Bounded one-off identity research. Source/title/artist scopes precede enrichment. Regex search of unlinked labels is not evidence of10million-row service performance; no application query/index changes.')

def compare(rows,state):
    out=[]
    for f in rows:
        titles={m.norm(t) for t in [f['title']]+TRANSLATIONS.get(f['title'],[])};hits=[]
        for a in state['artworks']:
            at={m.norm(a[k]) for k in ['title','alternate_title'] if a[k]};sim=1.0 if titles&at else 0.0
            if not sim:
                for t in titles:
                    for u in at:
                        d=difflib.SequenceMatcher(None,t,u)
                        if d.real_quick_ratio()>=.82 and d.quick_ratio()>=.82:sim=max(sim,d.ratio())
            if sim>=.82:hits.append(dict(a,title_similarity=round(sim,4),same_museum=a['id'] in state['scoped_ids']))
        sources=[v for v in state['source_citations']+state['source_identifiers'] if v.get('source_url',v.get('canonical_url')) in [f['source_url']] or v.get('source_record_id',v.get('external_id'))==f['source_id']]
        out.append(dict(number=f['number'],source_id=f['source_id'],title=f['title'],creator=f['creator_label'],date=f['date_display'],research_wave=f['research_wave'],decision=f['decision'],title_hits=hits,source_hits=sources))
    return out

def main():
    assert not (RUN/'production-identity-001.json.gz').exists();baseline=m.load(RUN/'baseline-verification-001.json');assert len(baseline['prior_production_ids'])==1584
    p=params();rows=research_rows()
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        before=m.load(RUN/'production-initial-scope-001.json.gz');assert c.snapshot(db,before['scoped_ids'])==before['snapshot']
        state=queries(db,p)
        citations=[v['row'] for v in db.execute("SELECT to_jsonb(x) row FROM citations x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
    comparisons=compare(rows,state)
    m.save(RUN/'production-identity-001.json.gz',dict(at=m.now(),read_only=True,params=p,state=state,comparisons=comparisons,research_references=[c.ref(root/'editorial-source-decisions-001.json.gz') for root in [c.RESEARCH,c.DATED]],script_reference=c.ref(Path(__file__).resolve())))
    m.save(RUN/'production-identity-citations-001.json.gz',dict(at=m.now(),read_only=True,citations=citations))
    print(json.dumps(dict(artworks=len(state['artwork_ids']),artists=len(state['artist_ids']),citations=len(citations),source_hit_works=sum(bool(x['source_hits']) for x in comparisons),image_checksum_hits=len(state['matching_media']))),flush=True)

if __name__=='__main__':main()
