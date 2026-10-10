"""Bounded source, accession, translated-title and image identity search for Kilkis."""
import importlib.util
import json
import re
import time
from pathlib import Path

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-kilkis-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
ARTCOLS='a.id::text,a.slug,a.title,a.normalized_title,a.alternate_title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.accession_number,a.current_institution_id::text,a.medium_text,a.dimensions_text,a.work_type,a.unlinked_creator_label,a.status,a.primary_media_id::text'
# Search translations are leads only, never replacement catalogue titles or mint/creator assignments.
TRANSLATIONS={
 'Πήλινο ομοίωμα παιδικής άμαξας με αναβάτη':['Terracotta model of a cart with rider','Terracotta toy horse and rider'],
 'Άγαλμα Απόλλωνα':['Statue of Apollo','Apollo Kitharoidos'],
 'Αγαλμάτιο Αφροδίτης':['Statuette of Aphrodite'],
 'Τμήμα γυμνού ανδρικού κορμού':['Fragment of a nude male torso','Male torso','Torso of a man'],
 'Χάλκινο ειδώλιο Λάρητα':['Bronze statuette of a Lar','Statuette of a Lar'],
 'Μαρμάρινη ανάγλυφη επιτύμβια στήλη':['Marble funerary relief','Funerary relief'],
 'Ερυθρόμορφη πελίκη':['Red-figure pelike','Red figure pelike'],
 'Χάλκινος κάνθαρος με ελικοειδείς λαβές':['Bronze kantharos'],
 'Χάλκινο ιλλυρικού τύπου κράνος':['Illyrian helmet','Bronze Illyrian helmet'],
 'Χρυσό ταινιωτό έλασμα':['Gold lamella'],
 'Ζευγάρι χάλκινων περικνημίδων':['Pair of bronze greaves','Bronze greaves'],
 'Ενεπίγραφη στήλη':['Inscribed stele'],
 'Χάλκινο ψέλιο':['Bronze bracelet'],
 'Χάλκινη περόνη':['Bronze pin'],
 'Χάλκινο δαχτυλίδι':['Bronze ring'],
 'Χρυσό περίαπτο':['Gold pendant'],
 'Ασημένια δραχμή Αλεξάνδρου':['Silver drachm of Alexander','Drachm of Alexander'],
 'Αργυρό δηνάριο Δομιτιανού/Περίαπτο':['Denarius of Domitian','Silver denarius of Domitian'],
 'Χάλκινη αμφικωνική χάντρα':['Bronze bead'],
 'Ενεπίγραφη και ανάγλυφη επιτύμβια στήλη':['Inscribed funerary relief'],
 'Οινοχόη':['Oinochoe','Oinochoe jug'],
 'Αμφορίσκος':['Amphoriskos'],
 'Μαρμάρινο λαρνακίδιο':['Marble sarcophagus','Small marble sarcophagus']}

def acc_variants(value):
    literal=re.sub(r'[^A-ZΑ-Ω0-9]','',(value or '').upper())
    roman=literal.translate(str.maketrans({'Ε':'E','Ν':'N','Μ':'M','Π':'P','Λ':'L','Κ':'K','Η':'H','Α':'A','Β':'B','Γ':'G','Δ':'D','Σ':'S','Τ':'T'}))
    return {v for v in [literal,roman,re.sub(r'^AEMK','',roman)] if v}

def params():
    rows=m.load(RUN/'source-review-001.json.gz')['rows']
    urls=sorted({u for v in rows for u in [v['source_url'],v.get('native_url'),(v.get('native_receipt') or {}).get('final_url')] if u})
    titles=sorted({m.norm(t) for v in rows for t in [v['title']]+v.get('aggregator_literal',{}).get('Τίτλος',[])+TRANSLATIONS.get(v['title'],[]) if t})
    accs=sorted({q for v in rows for q in acc_variants(v['inventory_literal'])})
    frames=m.load(RUN/'image-inputs-001.json')['rows'];oldframes=m.load(c.RESEARCH/'visual-references-001.json')['rows'];extra=m.load(RUN/'remaining-visual-references-001.json')['rows']
    return dict(titles=titles,urls=urls,source_ids=[v['source_id'] for v in rows],accession_keys=accs,image_checksums=sorted({v['sha256'] for v in frames+oldframes+extra}|{v['original_reference']['sha256'] for v in frames}),search_translations=TRANSLATIONS)

def queries(db,p):
    plans={};timings={}
    def query(key,sql,args):
        plans[key]=db.execute('EXPLAIN (FORMAT JSON) '+sql,args).fetchone();start=time.monotonic();rows=db.execute(sql,args).fetchall()
        timings[key]=dict(seconds=round(time.monotonic()-start,3),rows=len(rows));print(json.dumps(dict(query=key,**timings[key])),flush=True);return rows
    exact=query('exact_titles','SELECT id::text FROM artworks WHERE normalized_title=ANY(%s) ORDER BY id LIMIT20001'.replace('LIMIT20001','LIMIT 20001'),(p['titles'],));assert len(exact)<=20000
    accession=query('accessions',"SELECT id::text FROM artworks WHERE regexp_replace(upper(coalesce(accession_number,'')),'[^A-ZΑ-Ω0-9]','','g')=ANY(%s) ORDER BY id LIMIT 20001",(p['accession_keys'],));assert len(accession)<=20000
    cites=query('source_citations',"SELECT entity_id::text,source_url,field_name,source_record_id FROM citations WHERE entity_type='artwork' AND (source_url=ANY(%s) OR source_url LIKE 'https://www.efa-kilkis.gr/%%' OR source_url LIKE 'https://www.searchculture.gr/aggregator/edm/Efa_Kilkis_col/%%' OR (source_record_id=ANY(%s) AND source_url LIKE 'https://www.searchculture.gr/%%')) ORDER BY entity_id,source_url,field_name",(p['urls'],p['source_ids']))
    external=query('source_identifiers',"SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR canonical_url LIKE 'https://www.efa-kilkis.gr/%%' OR canonical_url LIKE 'https://www.searchculture.gr/aggregator/edm/Efa_Kilkis_col/%%' OR (scheme='searchculture-edm' AND external_id=ANY(%s))) ORDER BY entity_id,scheme,external_id",(p['urls'],p['source_ids']))
    media=query('matching_media',"SELECT to_jsonb(x) row FROM media_assets x WHERE checksum_sha256=ANY(%s) OR source_page_url=ANY(%s) OR source_page_url LIKE 'https://www.efa-kilkis.gr/%%' OR source_page_url LIKE 'https://www.searchculture.gr/aggregator/edm/Efa_Kilkis_col/%%' ORDER BY id",(p['image_checksums'],p['urls']));media=[x['row'] for x in media]
    mids=[x['id'] for x in media]
    image_links=query('matching_image_links','SELECT artwork_id::text,media_id::text,sort_order,view_label FROM artwork_media WHERE media_id=ANY(%s::uuid[]) ORDER BY artwork_id,media_id',(mids,))
    primaries=query('matching_primary_images','SELECT id::text FROM artworks WHERE primary_media_id=ANY(%s::uuid[]) ORDER BY id',(mids,))
    scoped=m.load(RUN/'production-initial-scope-001.json.gz')['scoped_ids']
    ids=sorted(set(scoped)|{x['id'] for x in exact+accession+primaries}|{x['entity_id'] for x in cites+external}|{x['artwork_id'] for x in image_links});assert len(ids)<=40000
    artworks=query('bounded_artworks','SELECT '+ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(ids,))
    links=query('bounded_creator_links','SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id,aa.attribution_role',(ids,))
    citations=query('bounded_full_citations',"SELECT to_jsonb(x) row FROM citations x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(ids,))
    return dict(artwork_ids=ids,artworks=artworks,creator_links=links,source_citations=cites,source_identifiers=external,matching_media=media,matching_media_links=image_links,scoped_ids=scoped,query_plans=plans,query_timings=timings),[x['row'] for x in citations]

def compare(rows,state):
    out=[]
    for f in rows:
        titles={m.norm(t) for t in [f['title']]+f.get('aggregator_literal',{}).get('Τίτλος',[])+TRANSLATIONS.get(f['title'],[]) if t};accessions=acc_variants(f['inventory_literal'])
        sources=[]
        for v in state['source_citations']+state['source_identifiers']:
            exact_id=v.get('source_record_id',v.get('external_id'))==f['source_id']
            exact_url=v.get('source_url',v.get('canonical_url')) in {u for u in [f['source_url'],f.get('native_url'),(f.get('native_receipt') or {}).get('final_url')] if u}
            if exact_id or (f['source_scheme']=='searchculture-edm' and exact_url):sources.append(v)

        matches=[]
        for a in state['artworks']:
            reasons=[]
            if titles & {m.norm(a[k]) for k in ['title','alternate_title'] if a[k]}:reasons.append('title_or_search_translation')
            if accessions & acc_variants(a['accession_number']):reasons.append('accession_key')
            if reasons:matches.append(dict(a,reasons=reasons))
        out.append(dict(number=f['number'],source_id=f['source_id'],title=f['title'],inventory=f['inventory_literal'],decision=f['decision'],source_hits=sources,comparison_hits=matches))
    return out

def main():
    assert not(RUN/'production-identity-001.json.gz').exists();assert len(m.load(RUN/'baseline-verification-001.json')['prior_production_ids'])==1782
    p=params();rows=m.load(RUN/'source-review-001.json.gz')['rows']
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');before=m.load(RUN/'production-initial-scope-001.json.gz');assert c.snapshot(db,before['scoped_ids'])==before['snapshot']
        state,citations=queries(db,p)
    comparisons=compare(rows,state)
    m.save(RUN/'production-identity-001.json.gz',dict(at=m.now(),read_only=True,params=p,state=state,comparisons=comparisons,source_reference=c.ref(RUN/'source-review-001.json.gz'),script_reference=c.ref(Path(__file__).resolve()),limitation='Bounded one-off global exact-source/accession/title/media search, followed by returned-ID enrichment. Generic English object nouns alone are not identity evidence. Accession normalization and strippedAEMKprefix are leads, not global unique identities. Book URL shared by multiple entries is not an exact object match without entry/inventory evidence. Recorded plans and timings are not a10million-row performance proof.'))
    m.save(RUN/'production-identity-citations-001.json.gz',dict(at=m.now(),read_only=True,citations=citations))
    print(json.dumps(dict(artworks=len(state['artwork_ids']),citations=len(citations),source_hit_rows=sum(bool(x['source_hits']) for x in comparisons),image_hits=len(state['matching_media']),comparison_rows=sum(bool(x['comparison_hits']) for x in comparisons))),flush=True)

if __name__=='__main__':main()
