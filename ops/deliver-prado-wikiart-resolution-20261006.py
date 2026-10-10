#!/usr/bin/env python3
"""Image-only continuation of the authorized Prado WikiArt delivery."""
import argparse, gzip, hashlib, importlib.util, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('prado',ROOT/'ops/deliver-prado-wikiart-images-20261006.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
d=p.d;r=p.r;q=p.q
RESEARCH=p.RESEARCH/'resolution-20261006';RUN=RESEARCH/'delivery';OP='prado-wikiart-resolution-20261006'
p.RUN=d.RUN=r.RUN=q.RUN=RUN;p.OP=d.OP=OP;r.PORT=55450
d.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
d.ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/OP

def select():
    decisions=r.load(RESEARCH/'identity-decisions.json')
    baseline=json.loads(gzip.decompress((RESEARCH/'production-snapshot.json.gz').read_bytes()))['records']
    with r.connect('production') as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        fresh=d.snapshots(db,list(baseline))
        institution=db.execute('SELECT to_jsonb(i) data FROM institutions i WHERE id=%s',(p.MUSEUM,)).fetchone()['data']
        eligibility={x['id']:x['scope']for x in db.execute('SELECT id::text,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope FROM artworks WHERE id=ANY(%s::uuid[])',(list(baseline),)).fetchall()}
    ready=[]
    for decision in decisions:
        if decision['outcome']!='selected_for_visual_review':continue
        aid=decision['artwork_id'];a=fresh[aid]['artwork']
        assert fresh[aid]==baseline[aid] and a['current_institution_id']==p.MUSEUM and not a['primary_media_id']
        assert decision['editorial_date_review']['eligible_before_1955'] is True
        assert decision['editorial_date_review']['evidence'] and decision['confidence']>=0.90
        assert a['creation_year_end'] is None or a['creation_year_end']<=1955
        source=r.load(RESEARCH/'pages'/(hashlib.sha256(decision['url'].encode()).hexdigest()+'.json'))
        rc=source['receipt'];key=r.sha(rc['url'].encode())
        body=next(f/'captures'/(key+'.html.gz')for f in(RESEARCH,p.RESEARCH/'deep-research-20261006',p.RESEARCH/'delivery',p.RESEARCH/'round-2',p.RESEARCH)if(f/'captures'/(key+'.html.gz')).exists())
        assert r.sha(gzip.decompress(body.read_bytes()))==rc['sha256']
        assert source['public_domain_label'] and source['rights_label'] in ('Public domain','Dominio público')
        page={'url':source['url'],'metadata':source['metadata'],'image_url':source['image_url'],
            'rights_label':source['rights_label'],'public_domain_label':source['public_domain_label'],
            'receipt':{**rc,'body_path':str(body.relative_to(ROOT))},'fields':source['attributes'],'date':q.parse_date(source['metadata'].get('year'))}
        work={**a,'institution_id':p.MUSEUM,'creators':[{'artist_id':c['artist_id'],'role':c['attribution_role']}for c in fresh[aid]['creators']]}
        ready.append({'work':work,'institution':institution,'page':page,'research':decision,
            'review_outcome':decision['reason'],'pending_visual_review':True})
    r.save_gz(RUN/'fresh-production-snapshot.json.gz',{'at':r.now(),'read_only':True,'records':fresh,'institution':institution})
    r.save(RUN/'selection.json',{'at':r.now(),'authorization':'User explicitly delegated source-conflict resolution on 6 October 2026; continuing authorized Prado image attachment. Individual evidence-based date eligibility reviews are recorded without changing catalogue dates.',
        'scope':'Existing production Prado records; missing primary images only. Preserve dates, creators, holdings, display and publication status.',
        'ready':ready,'held':[],'before_counts':{'works':len(fresh),'images':sum(bool(x['artwork']['primary_media_id'])for x in fresh.values())}})
    print('Selected',len(ready),'for visual review',flush=True)

def backup():
    description='Before Prado WikiArt resolved conflicts 20261006'
    def gc(*args):return json.loads(subprocess.check_output(['gcloud',*args,'--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True))
    matching=[x for x in gc('sql','backups','list','--instance=artline-postgres','--limit=50')if x.get('description')==description]
    if not matching:
        op=gc('sql','backups','create','--instance=artline-postgres','--description='+description,'--async')
        r.save(d.BACKUP/'cloud-sql-backup-operation.json',op);print('Recovery backup requested',flush=True);return
    current=max(matching,key=lambda x:int(x['id']))
    if current['status']!='SUCCESSFUL':print('Recovery backup',current['status'],flush=True);return
    r.save(d.BACKUP/'cloud-sql-backup.json',current);r.save(RUN/'cloud-sql-backup.json',{'id':current['id'],'status':current['status'],'at':r.now()})
    print('Recovery backup verified',current['id'],flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    commands={'select':select,'prepare':d.prepare,'sheets':d.contact_sheets,'visual':p.visual,'plan':p.plan,'backup':backup,'upload':d.upload,'apply':d.apply,'verify':d.verify}
    parser.add_argument('command',choices=commands);commands[parser.parse_args().command]()
