"""Capture forward city properties on the explicitly linked address nodes."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-italy-fourth-facts-20261008.py'));f=importlib.util.module_from_spec(z);z.loader.exec_module(f)
c=f.c;m=f.m;RUN=f.RUN;c.ROOT=RUN/'address-cities-001'
def main():
 source=RUN/'native-candidates-001.json.gz';rows=[r for r in m.load(source)['rows'] if 'html_museum_city_conflict' in r['issues']];uris=sorted({u for r in rows for u in r['facts']['root_fields'].get(f.a.LOC+'hasCulturalPropertyAddress',[])})
 query='SELECT DISTINCT ?s ?p ?o WHERE { VALUES ?s { '+' '.join('<'+v+'>' for v in uris)+' } VALUES ?p { <https://w3id.org/italia/onto/CLV/hasCity> <https://w3id.org/italia/onto/CLV/fullAddress> <https://w3id.org/italia/onto/CLV/hasStreetToponym> <http://www.w3.org/2000/01/rdf-schema#label> } ?s ?p ?o } ORDER BY ?s ?p ?o LIMIT 500'
 raw,receipt,rp,bp=c.fetch(c.ENDPOINT,dict(query=query,format='application/sparql-results+json'));triples=[{k:v['value'] for k,v in row.items()} for row in json.loads(raw)['results']['bindings']];assert len(triples)<500 and all(v['s'] in uris for v in triples)
 dest=RUN/'address-cities-001.json';m.save(dest,dict(at=m.now(),numbers=[r['number'] for r in rows],addresses=uris,triples=triples,receipt_reference=rp,body_reference=bp,script_reference=f.ref(Path(__file__).resolve()),source_reference=f.ref(source),policy='Only explicitly named forward address/city properties; no broad inverse-address traversal. This supplies missing HTML address context, never overrides contradictory city evidence.',database_writes=0));print(json.dumps(dict(addresses=uris,triples=triples),ensure_ascii=False))
if __name__=='__main__':main()
