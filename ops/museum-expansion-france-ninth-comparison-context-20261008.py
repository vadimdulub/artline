"""Extract primary physical-object comparisons from saved official metadata."""
import csv,gzip,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-france-ninth-facts-20261008.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
m=f.m
def main():
    dest=f.RUN/'physical-comparison-context-001.json.gz';assert not dest.exists()
    cp=f.RUN/'identity-citations-002.json.gz';cites=m.load(cp)['citations'];deps={Path(__file__).resolve(),cp};rows=[]
    def add(n,prefix,sid,record,path):
        matches=[c for c in cites if c['entity_id'].startswith(prefix) and (c['source_record_id']==sid or c['source_record_id'].endswith(':'+sid))]
        assert matches,(n,prefix,sid)
        c=matches[0];deps.add(path)
        rows.append(dict(candidate_number=n,existing_artwork_id=c['entity_id'],source_record_id=sid,citation_source_record_id=c['source_record_id'],source_url=c['source_url'],literal_primary_record=record,evidence_reference=f.ref(path)))
    specs=[('content/imports/joconde-20260910/joconde.csv','Reference','|',[(2,'b27a613b','M0205000737'),(6,'86d34906','M0205000393'),(22,'6e21b53a','M0205001285'),(122,'9ee3ddd8','07120004841')]),('content/imports/nga-catalogue-20260909/objects.csv','objectid',',',[(115,'99e05a2e','6540'),(146,'73a77338','39488')]),('content/imports/campaign-met-20260910/objects.csv','Object ID',',',[(144,'65edc058','687831')])]
    for filename,key,sep,targets in specs:
        path=m.ROOT/filename;manifest=path.with_name(path.name+'.snapshot.json');deps.add(manifest);assert f.ref(path)['sha256']==json.loads(manifest.read_text())['sha256']
        wanted={v[2]:v for v in targets};found=set()
        with path.open(encoding='utf-8-sig',newline='') as fp:
            for record in csv.DictReader(fp,delimiter=sep):
                sid=record[key]
                if sid in wanted:
                    assert sid not in found;found.add(sid);add(*wanted[sid],record,path)
        assert found==set(wanted),(filename,found,wanted)
    path=m.ROOT/'content/imports/campaign-cleveland-20260910/objects.json';manifest=path.with_name(path.name+'.snapshot.json');deps.add(manifest);assert f.ref(path)['sha256']==json.loads(manifest.read_text())['sha256']
    records=[v for v in json.loads(path.read_text()) if v['id']==154384];assert len(records)==1;add(7,'39798e5f','154384',records[0],path)
    for n,prefix,sid in [(70,'705b1ef4','M0650016695'),(290,'9fa6d613','00000055853')]:
        c=next(c for c in cites if c['entity_id'].startswith(prefix) and c['source_record_id']==sid);note=json.loads(c['evidence_note'])
        path=m.ROOT/note.get('body_path',note.get('evidence_path'));raw=gzip.decompress(path.read_bytes())
        expected=note['source_receipt']['sha256'] if 'source_receipt' in note else note['source_response_sha256'];assert hashlib.sha256(raw).hexdigest()==expected
        records=[v for v in json.loads(raw)['data'] if v['Reference']==sid];assert len(records)==1
        if 'raw_source_record' in note:assert records[0]==note['raw_source_record']
        add(n,prefix,sid,records[0],path)
    assert len(rows)==10
    m.save(dest,dict(at=m.now(),rows=sorted(rows,key=lambda v:v['candidate_number']),dependencies=[f.ref(p) for p in sorted(deps)],policy='Exact saved official source records resolve close physical-version comparisons only. No existing catalogue metadata, source labels, images or publication changed. Primary source chronology/format/measurements, collection and accession must distinguish impressions; separate IDs alone are insufficient.'))
    for row in sorted(rows,key=lambda v:v['candidate_number']):
        print(json.dumps(row,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
