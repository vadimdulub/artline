#!/usr/bin/env python3
"""Deliver reviewed WikiArt reproductions for the expanded Prado catalogue."""
import argparse,importlib.util,json,gzip
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('expansion','ops/expand-prado-catalogue-20261006.py')
p=module('prado','ops/deliver-prado-wikiart-images-20261006.py');d=p.d;r=p.r;q=p.q
RUN=m.RUN/'wikiart-delivery';OP='prado-expansion-wikiart-20261006'
p.RUN=d.RUN=r.RUN=q.RUN=RUN;p.OP=d.OP=OP;r.PORT=55481
d.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
d.ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/OP

def select():
    plan=r.load(m.RUN/'production-plan.json.gz');by={x['accession']:x for x in plan['records']}
    leads=r.load(p.RESEARCH/'resolution-20261006/additional-artworks.json')['artworks'];ids=[by[x['accession']]['artwork_id']for x in leads]
    with r.connect('production')as db:
        fresh=d.snapshots(db,ids);institution=db.execute('SELECT to_jsonb(i) data FROM institutions i WHERE id=%s',(m.MUSEUM,)).fetchone()['data']
        counts=db.execute('SELECT count(*) works,count(primary_media_id) images FROM artworks WHERE current_institution_id=%s',(m.MUSEUM,)).fetchone()
    ready=[];held=[]
    for lead in leads:
        x=by[lead['accession']];aid=x['artwork_id'];a=fresh[aid]['artwork']
        if a['primary_media_id']:held.append({'artwork_id':aid,'reason':'existing_image_preserved'});continue
        assert a['current_institution_id']==m.MUSEUM
        if x['date']['review']or x['date']['last']is None:
            assert lead['accession']=='P002785'and lead['wikiart']['metadata']['year']=='1808-1812'
            date_note=' Individual image eligibility: WikiArt dates the same Colossus object 1808–1812; preserve the museum/catalogue open interval “Después de 1808” without filling its unknown end.'
        else:
            assert x['date']['last']<=1955;date_note=''
        source=lead.get('alternative_wikiart',lead['wikiart'])if lead['accession']=='P007767'else lead['wikiart']
        # The initial Chinchon URL depicts the Uffizi work; use the specifically
        # researched alternate only after source fields and composition review.
        if lead['accession']=='P007767':
            alternatives=[v for k,v in lead.items()if isinstance(v,dict)and v.get('url','').endswith('portrait-of-maria-teresa-of-ballabriga-countess-of-chinchon')]
            assert len(alternatives)==1;source=alternatives[0]
        assert source['public_domain_label']and source['rights_label']=='Public domain'
        rc=source['receipt'];key=r.sha(rc['url'].encode())
        body=next(f/'captures'/(key+'.html.gz')for f in(p.RESEARCH/'resolution-20261006',p.RESEARCH/'deep-research-20261006',p.RESEARCH/'delivery',p.RESEARCH/'round-2',p.RESEARCH)if(f/'captures'/(key+'.html.gz')).exists())
        assert r.sha(gzip.decompress(body.read_bytes()))==rc['sha256']
        page={'url':source['url'],'metadata':source['metadata'],'image_url':source['image_url'],'rights_label':source['rights_label'],'public_domain_label':True,'receipt':{**rc,'body_path':str(body.relative_to(ROOT))},'fields':source['attributes'],'date':q.parse_date(source['metadata'].get('year'))}
        work={**a,'institution_id':m.MUSEUM,'creators':[{'artist_id':c['artist_id'],'role':c['attribution_role']}for c in fresh[aid]['creators']]}
        ready.append({'work':work,'institution':institution,'page':page,'research':lead,'review_outcome':'Museum native object '+x['source_id']+', '+x['accession']+'; '+lead['note']+date_note,'pending_visual_review':True})
    r.save(RUN/'selection.json',{'at':r.now(),'authorization':'User explicitly requested all supported Prado paintings using museum or WikiArt sources; paintings-first scope confirmed. Existing WikiArt collection/image policy continues.','scope':'Missing images of selected Prado paintings; preserve metadata and publication state.','ready':ready,'held':held,'before_counts':counts})
    r.save_gz(RUN/'fresh-production-snapshot.json.gz',{'at':r.now(),'records':fresh})
    backup=r.load(m.BACKUP/'cloud-backup.json');assert backup['status']=='SUCCESSFUL';r.save(d.BACKUP/'cloud-sql-backup.json',backup);r.save(RUN/'cloud-sql-backup.json',{'id':backup['id'],'status':backup['status']})
    print('Selected',len(ready),'existing images preserved',len(held),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();commands={'select':select,'prepare':d.prepare,'sheets':d.contact_sheets,'visual':p.visual,'plan':p.plan,'upload':d.upload,'apply':d.apply,'verify':d.verify};parser.add_argument('command',choices=commands);commands[parser.parse_args().command]()
