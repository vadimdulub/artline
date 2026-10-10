#!/usr/bin/env python3
"""Cross-check the sixth delivery's frozen sample, proof, receipts and report."""
import ast,csv,hashlib,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('round_six',ROOT/'ops/run-random-200-round6-20261007.py');x=importlib.util.module_from_spec(sp);sp.loader.exec_module(x)
r=x.r;RUN=x.RUN

def csv_rows(name):
    with (RUN/name).open(newline='') as f:return list(csv.DictReader(f))

def main():
    proof=r.load(RUN/'final-verification.json');summary=r.load(RUN/'summary.json');pre=r.load(RUN/'production-preflight.json')
    assert proof['painters']==200 and proof['all_200_painter_outcomes_verified'] and not proof['errors'] and summary['complete']
    assert proof['new_review_records']==pre['new_review_records']==summary['totals']['created']
    assert proof['images_verified']==pre['images']==summary['totals']['images_added']
    assert summary['statuses']=={'production_verified':200}
    cohort=r.load(RUN/'cohort.json');frame=r.load(RUN/'sampling-frame.json')['frame']
    ordered=sorted(frame,key=lambda p:hashlib.sha256((cohort['seed']+'/'+p['artist']['id']).encode()).digest())
    assert ordered[:200]==cohort['painters']
    correction=r.load(RUN/'sampling-correction-audit.json')
    for name,digest in correction['initial_sha256'].items():assert r.sha((RUN/('initial-'+name)).read_bytes())==digest
    original=r.load(RUN/'initial-cohort.json')
    assert cohort['seed']==original['seed'] and correction['seed_unchanged']
    assert correction['final_cohort_sha256']==r.sha((RUN/'cohort.json').read_bytes())
    assert not {p['artist']['id'] for p in cohort['painters']}&set(correction['rejected_nonindividual_ids'])
    ids={p['artist']['id'] for p in cohort['painters']};urls={p['source']['url'] for p in cohort['painters']};assert len(ids)==len(urls)==200
    old=[p for folder in x.PRIOR_RUNS for p in r.load(folder/'cohort.json')['painters']]
    assert not ids&{p['artist']['id'] for p in old}
    assert not urls&({p['source']['url'] for p in old}|{'https://www.wikiart.org/en/otto-dix','https://www.wikiart.org/en/viking-art'})
    files={n:csv_rows(n) for n in ['painters.csv','source-dispositions.csv','new-review-records.csv','uploaded-images.csv','related-artwork-leads.csv','rejected-relationship-leads.csv']}
    assert len(files['painters.csv'])==200
    indexed=sum(len(r.load(RUN/'indexes'/(aid+'.json.gz'))['items']) for aid in ids)+len(r.load(RUN/'unlinked-index-entries.json.gz'))
    assert indexed==len(files['source-dispositions.csv'])==summary['totals']['source_entries']==sum(summary['source_dispositions'].values())
    for name,key in [('new-review-records.csv','new_review_records'),('uploaded-images.csv','images_verified')]:
        assert len(files[name])==len({row['artwork_id'] for row in files[name]})==proof[key]
    for folder in ['applied','verified','delivery-pins']:assert len(list((RUN/folder).glob('*.json')))==200
    assert len(list((RUN/'image-uploads').glob('*.json')))==proof['images_verified']
    assert len(files['related-artwork-leads.csv'])==summary['totals']['related_artwork_leads']
    assert sum(int(row['created']) for row in files['painters.csv'])==proof['new_review_records']
    assert sum(int(row['images_added']) for row in files['painters.csv'])==proof['images_verified']
    parsed=BeautifulSoup((RUN/'report.html').read_text(),'html.parser');assert len(parsed.select('tbody tr'))==200
    for link in parsed.select('a[href]'):assert (RUN/link['href']).is_file(),link['href']
    held=r.load(RUN/'manual-image-holds.json')['held_artwork_ids'];uploaded={v['artwork_id'] for v in files['uploaded-images.csv']};assert not set(held)&uploaded
    for row in files['uploaded-images.csv']:assert 0<int(row['bytes'])<=100000
    for name,digest in proof.get('concurrent_location_review_files',{}).items():assert r.sha((ROOT/name).read_bytes())==digest
    scripts=list((ROOT/'ops').glob('*random-200*round6*.py'))
    for p in scripts:ast.parse(p.read_text())
    result={'at':r.now(),'complete':True,'operation':x.m.OP,'painters':200,'seed':cohort['seed'],'overlap_with_previous_1000_or_otto_dix':0,'new_review_records':proof['new_review_records'],'images_uploaded_and_verified':proof['images_verified'],'source_entries':indexed,'related_work_leads':len(files['related-artwork-leads.csv']),'reviewed_source_notes_verified':proof['reviewed_source_notes_verified'],'reviewed_image_holds':summary['totals']['reviewed_image_holds'],'cloud_backup_id':r.load(x.BACKUP/'cloud-backup.json')['id'],'checks':['Frozen seeded ordering and prior-cohort exclusions','CSV totals and unique artwork IDs','Production preflight, proof and summary agree','All 200 applied and verified receipts','Every public image upload receipt','All HTML artifact links and outcome rows','Complete source-disposition accounting','Image-only holds are not attached'],'report_sha256':r.sha((RUN/'report.html').read_bytes()),'proof_sha256':r.sha((RUN/'final-verification.json').read_bytes()),'script_sha256':{str(p.relative_to(ROOT)):r.sha(p.read_bytes()) for p in scripts},'errors':[]}
    r.save(RUN/'report-verification.json',result);print(json.dumps({k:v for k,v in result.items() if k!='script_sha256'}),flush=True)
if __name__=='__main__':main()
