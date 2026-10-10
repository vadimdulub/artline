"""Pin final corrections discovered during independent prose/date validation."""
import collections
import csv
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-chania-review-20261010.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
m,RUN,PROOF=r.m,r.RUN,r.PROOF
CREATORS={70:'Local workshop (source attribution; individual maker unknown)',90:'Cretan workshop (source attribution; imitation of North Apulian decoration is not an artist attribution)',
    95:'Kydonia workshop (source attribution)',96:'Local workshop (source attribution; individual maker unknown)',112:'Boeotian workshop (source attribution)',
    118:'Kydonia workshop (source attribution)',186:'Local workshop (source attribution; individual maker unknown)'}

def main():
    old=RUN/'editorial-source-decisions-001.json.gz';data=m.load(old);rows=data['rows'];corrections=[]
    for row in rows:
        n=row['number'];changes={}
        if n in CREATORS:changes['creator_label']=CREATORS[n]
        if n==118:changes['date_review']='Native dating field, not descriptive prose, states second half fourteenth century BCE; normalized century-half interval retains separate source 1350–1300 bounds.'
        if n==186:changes['work_type']='sculpture'
        if changes:
            corrections.append(dict(number=n,before={k:row[k]for k in changes},after=changes,basis='Re-read complete native description and native dating-field rows. Source 186 explicitly describes a surviving relief with two figures.'))
            row.update(changes)
    by={row['number']:row for row in rows}
    data.update(at=m.now(),supersedes=r.v.ref(old),script_reference=r.v.ref(Path(__file__).resolve()),corrections=corrections)
    m.save(RUN/'editorial-source-decisions-002.json.gz',data)
    old_units=RUN/'candidate-physical-units-001.json.gz';u=m.load(old_units)
    for row in u['rows']:
        row.update({key:value for key,value in by[row['number']].items()})
    u.update(at=m.now(),supersedes=r.v.ref(old_units),decisions_reference=r.v.ref(RUN/'editorial-source-decisions-002.json.gz'))
    m.save(RUN/'candidate-physical-units-002.json.gz',u)
    fields=['number','source_id','native_url','title','inventory_literal','role','decision','primary_number','work_type','creator_label','first','last','date_scope','date_review','image_candidate','image_hold_reason','editorial_note']
    with(RUN/'review-ledger-002.csv').open('x',encoding='utf-8-sig',newline='')as out:
        writer=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    m.save(RUN/'final-review-corrections-001.json',dict(at=m.now(),rows=corrections,policy='Preserve immutable first review. The002 decisions, physical units and ledger are canonical for this batch. No production changes or painter IDs.',script_reference=r.v.ref(Path(__file__).resolve())))
    print(dict(corrections=len(corrections),units=len(u['rows']),types=dict(collections.Counter(row['work_type']for row in u['rows'])),workshop_labels=sum('workshop'in row['creator_label']for row in u['rows'])))

if __name__=='__main__':main()
