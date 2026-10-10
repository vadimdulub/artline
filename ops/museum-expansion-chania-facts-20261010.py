"""Separate native claims, aggregator enrichment and physical-object evidence."""
import collections
import gzip
import importlib.util
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-chania-selected-20261010.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
m,RUN,q=s.m,s.RUN,s.q

def main():
    sources=m.load(RUN/'selected-source-records-001.json.gz')['rows'];rows=[]
    for src in sources:
        f=src['fields'];nf=src['native_fields']
        native=BeautifulSoup(gzip.decompress((m.ROOT/src['native_receipt']['body_path']).read_bytes()),'html.parser')
        table=[[q.clean(c.get_text(' ',strip=True))for c in tr.select('td')]for tr in native.select('table.jet-table tr')]
        table=[r for r in table if len(r)==2 and any(r)]
        main=native.select('h4.jet-listing-dynamic-field__content');body=native.select('h6.jet-listing-dynamic-field__content')
        assert len(main)==1,(src['number'],len(main))
        title=q.clean(main[0].get_text(' ',strip=True));desc=q.clean(body[0].get_text(' ',strip=True))if body else None
        agg_desc=f.get('Περιγραφή',[])
        rows.append(dict(number=src['number'],source_id=src['source_id'],role=src['role'],source_url=src['source_url'],native_url=src['native_url'],
            title=title,title_basis='native_object_page',aggregator_titles=f.get('Τίτλος',[]),title_agrees=not f.get('Τίτλος')or title in f['Τίτλος'],
            inventory_literal=nf['Κωδικός'],native_description=desc,aggregator_descriptions=agg_desc,description_agrees=desc in agg_desc,
            native_table_rows=table,source_material=nf.get('Υλικό'),source_dimensions=nf.get('Διαστάσεις'),
            source_provenance=nf.get('Προέλευση'),source_reference=nf.get('Βιβλιογραφική παραπομπή'),
            native_date_claim=nf.get('Χρονολόγηση'),native_unlabelled_claims=[v[1]for v in table if not v[0]],
            literal_temporal_coverage=f.get('Χρονική κάλυψη',[]),aggregator_enrichment=src['enrichment'],index_date=src['index'].get('index_date'),index_type=src['index'].get('index_type'),
            source_creator_labels=f.get('Δημιουργός',[]),painter_id=None,first=None,last=None,date_review='pending_editorial_claim_reconciliation',
            native_image_count=len(src['native_images']),source_fields=f,native_fields=nf,source_receipt=src['receipt'],native_receipt=src['native_receipt'],
            rights_links=src['rights_links'],proposed_status='review',ready_to_apply=False,applied=False,current_display_verified=False))
    codes=collections.defaultdict(list)
    for r in rows:codes[r['inventory_literal']].append(r['number'])
    m.save(RUN/'candidate-facts-001.json.gz',dict(at=m.now(),rows=rows,
        duplicate_literal_accessions={k:v for k,v in codes.items()if len(v)>1},
        source_reference=q.s.ref(RUN/'selected-source-records-001.json.gz'),script_reference=q.s.ref(Path(__file__).resolve()),
        policy='Native exact-looking years may encode period boundaries: compare item prose and period claims before assigning numeric creation dates. Preserve all conflicting dates and qualified identities. No artist inferred from depicted gods, mint authorities, findspots or archaeological excavators. Accessioned components can belong to one physical work.'))
    print(json.dumps(dict(rows=len(rows),title_disagreements=[r['number']for r in rows if not r['title_agrees']],description_disagreements=[r['number']for r in rows if not r['description_agrees']],duplicate_accessions={k:v for k,v in codes.items()if len(v)>1},image_counts=dict(collections.Counter(r['native_image_count']for r in rows))),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
