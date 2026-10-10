#!/usr/bin/env python3
"""Bounded deep research for a freshly audited production one-artwork cohort."""
import argparse, collections, gzip, importlib.util, json, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/museums-exactly-one-deep-20261008';OP=RUN.name

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'ops'/file)
    out=importlib.util.module_from_spec(spec);spec.loader.exec_module(out);return out
m=module('deep_round3','museums-exactly-one-round3-20261008.py')
os.environ['ARTLINE_MUSEUM_PROXY_PORT']='55495'
m.RUN=RUN;m.OP=OP;m.r.RUN=RUN;m.r.OP=OP;m.r.p.RUN=RUN;d=m.d

def baseline():
    m.baseline()
    with d.connect() as db:
        rows=db.execute("SELECT to_jsonb(i) institution,(SELECT count(*) FROM artworks a WHERE a.current_institution_id=i.id AND a.status<>'archived') linked FROM institutions i ORDER BY i.id").fetchall()
    d.save(RUN/'all-institution-authorities.json.gz',rows)
    m.r.backup()

def backup():m.r.backup()

def local_candidates():m.r.p.local_candidates()

def arco():
    a=module('deep_arco','minimum-100-arco-native-20261006.py')
    a.c.RUN=RUN;a.c.OP=OP;a.RUN=RUN/'arco';a.a.RUN=a.RUN
    a.c.BASE={x['institution']['id']:x for x in d.load(RUN/'baseline.json.gz')['selected']}
    a.c.d.connect=d.connect
    return a

def arco_select():
    a=arco();v=a.selection('italian-native',60,500)
    for x in v['museums']:print(x['museum']['name'],x['source_candidates'],x['selected'],flush=True)
    print('Selected',len(v['candidates']),'objects;',len(v['held']),'authority holds',flush=True)

def arco_research():arco().research('italian-native',60,500)


def finalize_native():
    for source,wave,strict in [('artefact-corrected','artefact-reviewed',True),('qagoma-corrected','qagoma-reviewed',False)]:
        folder=RUN/'waves'/source;plan=d.load(folder/'plan.json.gz');identity=d.load(RUN/'identity'/source/'discovery.json.gz');comparisons={x['key']for x in identity['comparisons']};life={x['key']for x in identity['life_conflicts']};keep=[]
        for row in plan['records']:
            key=row['source_record_id']
            if key in life or (strict and key in comparisons):
                plan['held'].append(dict(source_record_id=key,title=row['facts']['title'],museum_id=row['museum']['id'],reason='creator_date_object_identity_requires_individual_comparison',basis='Possible existing source-version records discovered through creator aliases and overlapping creation dates. Retain lead; do not create a duplicate or infer a link from similarity alone.'))
            else:keep.append(row)
        if not strict:
            leads=d.load(RUN/'identity'/source/'title-leads.json');assert not leads
        plan['records']=keep
        for summary in plan['museums']:
            rows=[r for r in keep if r['museum']['id']==summary['museum_id']]
            summary.update(new_artworks=sum(r['action']=='create'for r in rows),new_links=sum(r['action']=='link'for r in rows),projected_eligible=summary['before']['eligible']+len(rows),projected_linked=summary['before']['linked']+len(rows),available_after_identity_review=len(rows))
        plan['parent_plan']=dict(path=str((folder/'plan.json.gz').relative_to(ROOT)),sha256=d.sha((folder/'plan.json.gz').read_bytes()))
        plan['creator_date_review']=dict(path=str((RUN/'identity'/source/'discovery.json.gz').relative_to(ROOT)),sha256=d.sha((RUN/'identity'/source/'discovery.json.gz').read_bytes()))
        dest=RUN/'waves'/wave
        for name in ['sample.json','source-verified.json.gz','identity-query-plan.json']:d.save(dest/name,d.load(folder/name))
        plan['sample_sha256']=d.sha((dest/'sample.json').read_bytes());d.save(dest/'plan.json.gz',plan);d.save(Path.home()/'Library/Application Support/Artline/backups'/OP/wave/'plan-and-preimages.json.gz',plan)
        print(wave,len(keep),'reviewed new records across',len({r['museum']['id']for r in keep}),'museums',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase');args=p.parse_args();globals()[args.phase]()
