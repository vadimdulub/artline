"""Read-only supplied provenance and exact aliases for sparse comparison leads."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-france-fifteenth-facts-20261008.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
m=f.m;RUN=f.RUN
def main():
 dest=RUN/'sparse-comparison-context-001.json.gz';assert not dest.exists();p=RUN/'physical-comparison-context-002.json.gz';x=m.load(p);ids=x['unresolved_ids_without_object_primary_citation']
 native=['https://collections.louvre.fr/ark:/53355/cl010097192','https://collections.louvre.fr/ark:/53355/cl010109869']
 urls=sorted({z for u in native for v in [u,u.replace('/ark:','/en/ark:'),u.replace('/ark:','/fr/ark:'),u.replace('ark:','ark%3A')] for z in [v,v+'/',v+'.json',v.replace('https:','http:')]})
 inventories=['OA 427','OA427','OA 431','OA431','ECL 22279','ECL22279','ECL 22282','ECL22282']
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
  research=db.execute("SELECT l.artwork_id::text,r.raw_json FROM research_artwork_links l JOIN research_records r ON(r.snapshot_id,r.source_key,r.record_kind,r.source_record_id)=(l.snapshot_id,l.source_key,l.record_kind,l.research_record_id) WHERE l.artwork_id=ANY(%s::uuid[]) AND r.raw_json #> '{csv,cells}' IS NOT NULL ORDER BY l.artwork_id,r.source_record_id",(ids,)).fetchall()
  citations=db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND (source_url=ANY(%s) OR entity_id=ANY(%s::uuid[])) ORDER BY entity_id,id",(urls,ids)).fetchall()
  exact=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme ILIKE '%%louvre%%' AND external_id=ANY(%s))) ORDER BY entity_id,scheme,external_id",(urls,['cl010097192','cl010109869'])).fetchall()
  accessions=db.execute('SELECT id::text,title,accession_number,medium_text,dimensions_text FROM artworks WHERE accession_number=ANY(%s) ORDER BY id',(inventories,)).fetchall()
 m.save(dest,dict(at=m.now(),query_reference=f.ref(Path(__file__).resolve()),comparison_reference=f.ref(p),artwork_ids=ids,research_records=research,citations=[r['row'] for r in citations],query_urls=urls,query_inventories=inventories,native_identifier_hits=exact,exact_accession_hits=accessions,database_writes=0,policy='Supplied CSV context is provenance, not primary museum or identity evidence. Exact source aliases are discovery leads only. Existing catalogue remains unchanged.'))
 print(json.dumps(dict(artifact=f.ref(dest),research_records=len(research),citations=len(citations),native_identifier_hits=len(exact),exact_accession_hits=len(accessions))),flush=True)
if __name__=='__main__':main()
