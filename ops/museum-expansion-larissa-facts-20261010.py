"""Keep literal native dates and media separate from index/enrichment shortcuts."""
import collections
import importlib.util
import json
import re
from pathlib import Path

spec=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-larissa-selected-20261010.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
m,RUN,q=s.m,s.RUN,s.q

def parse_date(text):
    if not text:return None,None,'unknown'
    match=re.fullmatch(r'(\d{4})(?:\s*[-–]\s*(\d{2}|\d{4}))?',text)
    if match:
        a=int(match[1]);b=int(match[2])if match[2]else a
        if b<100:b=a//100*100+b
        assert 1700<=a<=b<=1970,(text,a,b)
        return a,b,'source_numeric'
    assert text in {'before 1920','before 1934','After 1920'},text
    return None,None,'source_qualified_before'if text.startswith('before')else'source_open_after'

def main():
    sources=m.load(RUN/'selected-source-records-001.json.gz')['rows'];rows=[]
    for src in sources:
        nf=src['native_fields'];f=src['fields'];a,b,kind=parse_date(nf.get('Χρονολογία έργου'))
        assert f['Τίτλος']==[nf['Τίτλος έργου']]
        assert not f.get('Ημερομηνία')or f['Ημερομηνία']==[nf.get('Χρονολογία έργου')]
        rows.append(dict(number=src['number'],source_id=src['source_id'],source_url=src['source_url'],native_url=src['native_url'],role=src['role'],
            title=nf['Τίτλος έργου'],creator_label=nf.get('Καλλιτέχνης'),source_creator_labels=f.get('Δημιουργός',[]),painter_id=None,
            native_date_literal=nf.get('Χρονολογία έργου'),first=a,last=b,date_basis=kind,index_date=src['index'].get('index_date'),
            native_category=nf.get('Κατηγορία'),native_material=nf.get('Υλικό'),native_technique=nf.get('Τρόπος κατασκευής'),dimensions_text=nf.get('Διαστάσεις'),
            collection_literal=nf.get('Συλλογή'),native_depiction=nf.get('Απεικόνιση'),native_short_description=nf.get('Σύντομη περιγραφή'),
            native_description=src['native_description'],aggregator_descriptions=f.get('Περιγραφή',[]),native_artist_urls=src['native_artist_urls'],
            inventory_literal=None,inventory_basis='No explicit accession field; native image filenames are preserved as image evidence, not promoted to canonical accession.',
            native_images=src['native_images'],source_fields=f,native_fields=nf,aggregator_enrichment=src['enrichment'],
            source_receipt=src['receipt'],native_receipt=src['native_receipt'],rights_links=src['rights_links'],
            proposed_status='review',ready_to_apply=False,applied=False,current_display_verified=False))
    images=collections.defaultdict(list);names=collections.defaultdict(list)
    for row in rows:
        images[row['native_images'][0]['absolute_url']].append(row['number'])
        names[(row['title'],row['creator_label'])].append(row['number'])
    m.save(RUN/'candidate-facts-001.json.gz',dict(at=m.now(),rows=rows,same_native_image_url_groups=[ns for ns in images.values()if len(ns)>1],
        repeated_title_creator_groups=[dict(title=key[0],creator=key[1],numbers=ns)for key,ns in names.items()if len(ns)>1],
        source_reference=q.s.ref(RUN/'selected-source-records-001.json.gz'),script_reference=q.s.ref(Path(__file__).resolve()),
        policy='Dates from native object fields, including full ranges and before/after qualifiers. Null bounds for open intervals; no year inferred from artist lifespan or index date. Album pages, copy makers and physical support still require editorial review.'))
    groups=collections.defaultdict(list)
    for row in rows:groups[row['native_description']].append(row['number'])
    m.save(RUN/'description-review-groups-001.json.gz',dict(at=m.now(),groups=[dict(numbers=ns,description=desc)for desc,ns in groups.items()],policy='Identical complete descriptions can be reviewed once for all listed records; individual object fields/images remain separate. No claim of completed description review.'))
    print(json.dumps(dict(rows=len(rows),date_kinds=dict(collections.Counter(r['date_basis']for r in rows)),same_image_urls=[ns for ns in images.values()if len(ns)>1],repeated_title_creators=[ns for ns in names.values()if len(ns)>1]),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
