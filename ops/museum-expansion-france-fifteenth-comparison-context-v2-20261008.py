"""Preserve primary comparator records from previously captured official catalogues."""
import csv,gzip,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-france-fifteenth-facts-20261008.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
m=f.m
def main():
    dest=f.RUN/'physical-comparison-context-002.json.gz';assert not dest.exists()
    cp=f.RUN/'identity-citations-002.json.gz';ip=f.RUN/'native-identity-002.json.gz';cs=m.load(cp)['citations'];ix=m.load(ip)
    ids={a['id'] for c in ix['comparisons'] for key in ['leads','exact_title_hits','untitled_creator_hits','lexical_hits','object_alias_hits','related_inventory_hits'] for a in c[key]}
    ids|={a['id'] for c in ix['comparisons'] for a in c['inventory_hits'] if a['relevant']}
    by={};deps={Path(__file__).resolve(),cp,ip};unresolved=[];citations_by_entity={}
    for c in cs:
        if '/notice/joconde/' in c['source_url']:citations_by_entity.setdefault(c['entity_id'],[]).append(c)
    for aid in sorted(ids):
        matches=citations_by_entity.get(aid,[])
        if not matches:unresolved.append(aid);continue
        for c in matches:
            sid=c['source_url'].split('/notice/joconde/',1)[1].rstrip('/');by.setdefault((aid,sid),c)
    rows={};capture_misses=[]
    for key,c in by.items():
        try:n=json.loads(c['evidence_note'])
        except (ValueError,TypeError):continue
        if n.get('native_capture_reference'):
            p=f.checked(n['native_capture_reference']);bundle=m.load(p);f.body(bundle);deps.update([p,m.ROOT/bundle['body_path']])
            rr=[r for r in bundle['data'] if r['Reference']==key[1]]
            if len(rr)!=1:
                capture_misses.append(dict(existing_artwork_id=key[0],source_record_id=key[1],evidence_reference=f.ref(p),matching_records=len(rr)));continue
            assert rr[0]==n['facts']['source_fields']
            rows[key]=dict(existing_artwork_id=key[0],source_record_id=key[1],source_url=c['source_url'],literal_primary_record=rr[0],evidence_reference=f.ref(p),capture_kind='saved checked native API response');continue
        pn=n.get('body_path') or n.get('evidence_path')
        expected=n.get('source_receipt',{}).get('sha256') or n.get('source_response_sha256')
        if not pn or not expected:continue
        p=m.ROOT/pn;raw=gzip.decompress(p.read_bytes());assert hashlib.sha256(raw).hexdigest()==expected;deps.add(p)
        rr=[r for r in json.loads(raw)['data'] if r['Reference']==key[1]]
        if len(rr)!=1:
            capture_misses.append(dict(existing_artwork_id=key[0],source_record_id=key[1],evidence_reference=f.ref(p),matching_records=len(rr)));continue
        rows[key]=dict(existing_artwork_id=key[0],source_record_id=key[1],source_url=c['source_url'],literal_primary_record=rr[0],evidence_reference=f.ref(p),capture_kind='saved current official response')
    missing=set(by)-set(rows);p=m.ROOT/'content/imports/joconde-20260910/joconde.csv';manifest=p.with_name(p.name+'.snapshot.json')
    csv_reference=f.ref(p)
    assert csv_reference['sha256']==json.loads(manifest.read_text())['sha256'];deps.update([p,manifest]);wanted={sid for _,sid in missing}
    keys_by_source={}
    for key in missing:keys_by_source.setdefault(key[1],[]).append(key)
    with p.open(encoding='utf-8-sig',newline='') as fp:
        for r in csv.DictReader(fp,delimiter='|'):
            if r['Reference'] not in wanted:continue
            for key in keys_by_source[r['Reference']]:rows[key]=dict(existing_artwork_id=key[0],source_record_id=key[1],source_url=by[key]['source_url'],literal_primary_record=r,evidence_reference=csv_reference,capture_kind='pinned historical official metadata')
    unresolved_primary=[dict(existing_artwork_id=k[0],source_record_id=k[1],source_url=by[k]['source_url']) for k in sorted(set(by)-set(rows))]
    m.save(dest,dict(at=m.now(),rows=[rows[k] for k in sorted(rows)],unresolved_ids_without_object_primary_citation=unresolved,unresolved_primary_records=unresolved_primary,citation_capture_record_misses=capture_misses,dependencies=[f.ref(p) for p in sorted(deps)],policy='Comparator evidence only. No existing catalogue, museum, image, date or publication changes. Source dates and inventories preserved literally. A cited capture that does not contain its claimed record is recorded and cannot supply that record; checked historical official metadata may resolve it. Missing primary evidence is not a negative duplicate result.'))
    print(json.dumps(dict(records=len(rows),unresolved_without_primary=len(unresolved),unresolved_primary_records=len(unresolved_primary),citation_capture_record_misses=len(capture_misses))),flush=True)
if __name__=='__main__':main()
