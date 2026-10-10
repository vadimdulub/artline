"""Pin NGA comparators, authority evidence and within-selection physical identity checks."""
import csv,gzip,hashlib,importlib.util,json,difflib
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-france-thirteenth-identity-v2-20261008.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
m=i.m;RUN=i.RUN

def main():
    dest=RUN/'final-object-context-001.json.gz';assert not dest.exists()
    rows=m.load(RUN/'native-candidates-001.json.gz')['rows'];ix=m.load(RUN/'native-identity-002.json.gz');deps={Path(__file__).resolve(),RUN/'native-candidates-001.json.gz',RUN/'native-identity-002.json.gz'}
    nga={};root=m.ROOT/'content/imports/nga-catalogue-20260909'
    for name in ['objects.csv','objects_text_entries.csv']:
        p=root/name;manifest=p.with_name(name+'.snapshot.json');meta=json.loads(manifest.read_text());assert i.ref(p)['sha256']==meta['sha256'];deps.update([p,manifest])
        with p.open(newline='',encoding='utf-8-sig') as stream:nga[name]=[v for v in csv.DictReader(stream) if v['objectid'] in ['173150','47788']]
    assert len(nga['objects.csv'])==2
    ctx=RUN/'object-context-001';p=ctx/'andre-francois-authority.html.gz';receipt=ctx/'andre-francois-authority.receipt.json';txt=ctx/'andre-francois-authority.txt';raw=gzip.decompress(p.read_bytes());meta=json.loads(receipt.read_text());assert meta['status']==200 and hashlib.sha256(raw).hexdigest()==meta['sha256'];assert all(v in txt.read_text() for v in ['1915','2005','François']);deps.update([p,receipt,txt])
    pairs=[]
    for j,a in enumerate(rows):
        for b in rows[j+1:]:
            x,y=a['facts'],b['facts'];same_inventory=a['institution_id']==b['institution_id'] and bool(m.acc(x['inventory'])&m.acc(y['inventory']))
            if not same_inventory and x['creator_label']!=y['creator_label']:continue
            score=difflib.SequenceMatcher(None,m.norm(x['title']),m.norm(y['title'])).ratio()
            if same_inventory or score>=.88:
                pairs.append(dict(numbers=[a['number'],b['number']],source_ids=[a['source_id'],b['source_id']],same_inventory=same_inventory,title_similarity=score,titles=[x['title'],y['title']],dimensions=[x['dimensions_text'],y['dimensions_text']],physical_descriptions=[x['source_fields'].get('Description'),y['source_fields'].get('Description')],subjects=[x['source_fields'].get('Precisions_sujets_representes'),y['source_fields'].get('Precisions_sujets_representes')]))
    m.save(dest,dict(at=m.now(),nga_comparators=nga,authority=dict(source_url=meta['url'],life_dates='1915–2005',application='Preserve André François as the object-level source name; replace conflicting source biography in the displayed maker label with an explicit conflict qualification. No new artist authority or biography.'),within_selection_pairs=pairs,dependencies=[i.ref(p) for p in sorted(deps)],policy='Comparison evidence only. Distinct depictions, original physical media, inscriptions and provenance establish individual objects; title similarity and inventory adjacency alone do not. Original source notices remain unchanged.'))
    print(json.dumps(dict(nga_object_rows=len(nga['objects.csv']),pairs=len(pairs))),flush=True)
if __name__=='__main__':main()
