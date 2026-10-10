"""Preserve primary comparator records from previously captured official catalogues."""
import csv,gzip,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-france-twelfth-facts-20261008.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
m=f.m
def main():
    dest=f.RUN/'physical-comparison-context-001.json.gz';assert not dest.exists()
    cp=f.RUN/'identity-citations-001.json.gz';ip=f.RUN/'native-identity-001.json.gz';cs=m.load(cp)['citations'];ix=m.load(ip)
    ids={a['id'] for c in ix['comparisons'] for a in c['leads'] if a['title_similarity']>=.8}
    ids|={a['id'] for c in ix['comparisons'] for a in c['inventory_hits'] if a['relevant']}
    by={};deps={Path(__file__).resolve(),cp,ip};unresolved=[]
    for aid in sorted(ids):
        matches=[c for c in cs if c['entity_id']==aid and '/notice/joconde/' in c['source_url']]
        if not matches:unresolved.append(aid);continue
        for c in matches:
            sid=c['source_url'].rstrip('/').split('/')[-1];by.setdefault((aid,sid),c)
    rows={}
    for key,c in by.items():
        try:n=json.loads(c['evidence_note'])
        except (ValueError,TypeError):continue
        pn=n.get('body_path') or n.get('evidence_path')
        expected=n.get('source_receipt',{}).get('sha256') or n.get('source_response_sha256')
        if not pn or not expected:continue
        p=m.ROOT/pn;raw=gzip.decompress(p.read_bytes());assert hashlib.sha256(raw).hexdigest()==expected;deps.add(p)
        rr=[r for r in json.loads(raw)['data'] if r['Reference']==key[1]];assert len(rr)==1
        rows[key]=dict(existing_artwork_id=key[0],source_record_id=key[1],source_url=c['source_url'],literal_primary_record=rr[0],evidence_reference=f.ref(p),capture_kind='saved current official response')
    missing=set(by)-set(rows);p=m.ROOT/'content/imports/joconde-20260910/joconde.csv';manifest=p.with_name(p.name+'.snapshot.json')
    assert f.ref(p)['sha256']==json.loads(manifest.read_text())['sha256'];deps.update([p,manifest]);wanted={sid for _,sid in missing}
    with p.open(encoding='utf-8-sig',newline='') as fp:
        for r in csv.DictReader(fp,delimiter='|'):
            if r['Reference'] not in wanted:continue
            for key in missing:
                if key[1]==r['Reference']:rows[key]=dict(existing_artwork_id=key[0],source_record_id=key[1],source_url=by[key]['source_url'],literal_primary_record=r,evidence_reference=f.ref(p),capture_kind='pinned historical official metadata')
    assert set(rows)==set(by),(set(by)-set(rows))
    m.save(dest,dict(at=m.now(),rows=[rows[k] for k in sorted(rows)],unresolved_ids_without_object_primary_citation=unresolved,dependencies=[f.ref(p) for p in sorted(deps)],policy='Comparator evidence only. No existing catalogue, museum, image, date or publication changes. Source dates and inventories preserved literally; missing primary evidence is not a negative duplicate result.'))
    print(json.dumps(dict(records=len(rows),unresolved_ids=unresolved)),flush=True)
if __name__=='__main__':main()
