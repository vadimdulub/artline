#!/usr/bin/env python3
"""Attach reviewed primary museum images with both-target pinned object checks."""
import argparse,importlib.util,json,os
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('apply-greek-primary-images.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
m=a.m;CORE=a.CORE
PROVIDER=os.environ.get('ARTLINE_PRIMARY_PROVIDER','german');assert PROVIDER in ('german','nationalmuseum','nationalmuseum-commons','polish-commons','norwegian-commons','warsaw-reviewed','german-reviewed-v2','met-reviewed','identity-reviewed')

def configure(code,number):
    a.RUN=m.x.BASE/code/f'round-{number:02d}'/'delivery'/('primary-images' if PROVIDER=='german' else 'primary-images-'+PROVIDER)

def plan(code,number):
    configure(code,number)
    if (a.RUN/a.PLAN_NAME).exists():return
    prepared=json.loads((a.RUN/'preparation.json').read_text());qa=json.loads((a.RUN/'quality-review.json').read_text())
    assert qa.get('approved') is True and qa['contact_sheet_sha256']==prepared['contact_sheet_sha256']==CORE.sha((a.RUN/'contact-sheet.jpg').read_bytes())
    images=[];targets={t:[] for t in ('local','production')}
    for name,sha in prepared['prepared_hashes'].items():
        raw=(a.RUN/'prepared'/name).read_bytes();assert CORE.sha(raw)==sha;im=json.loads(raw)
        if im['key'] in qa.get('held_images',{}):continue
        assert im['key'] in qa['accepted'];images.append(im)
    for target in targets:
        with m.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION READ ONLY')
            for im in images:
                receipt=json.loads((a.RUN.parent/'applied'/target/(im['key']+'.json')).read_text());w=db.execute('SELECT to_jsonb(w) row FROM artworks w WHERE id=%s',(receipt['artwork_id'],)).fetchone()['row'];e=im['identity']['primary']
                assert w['status']=='review' and not w['published_at'] and not w['primary_media_id'] and w['creation_year_end'] is not None and w['creation_year_end']<=1970
                assert m.m.accession_key(w['accession_number'])==m.m.accession_key(e['object']['accession'])
                assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND entity_id=%s AND scheme='wikidata' AND external_id=%s",(w['id'],im['key'])).fetchone()
                record=json.loads((a.RUN.parent/'ready'/(im['key']+'.json')).read_text())['record']
                assert db.execute('SELECT 1 FROM artwork_artists WHERE artwork_id=%s AND artist_id=%s',(w['id'],receipt['artist_id'])).fetchone()
                creator=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND external_id=%s",(record['creator_qid'],)).fetchone()
                # The core import may have reused a closed, pre-existing person
                # identity that does not yet carry this Wikidata identifier.
                # Require the exact verified receipt's link; never fuzzy match
                # or introduce a new artist authority during image attachment.
                assert not creator or creator['entity_id']==receipt['artist_id']
                targets[target].append({'key':im['key'],'work':w})
        CORE.save_new(m.BACKUPS/m.x.CAMPAIGN/code/f'round-{number:02d}'/(a.RUN.name+'-'+target+'-preimages.json'),targets[target])
    CORE.save_new(a.RUN/a.PLAN_NAME,{'at':CORE.now(),'images':images,'targets':targets,'qa':qa});CORE.save_new(a.RUN/a.MANIFEST_NAME,{'plan_sha256':CORE.sha((a.RUN/a.PLAN_NAME).read_bytes()),'images':len(images)});print(code,number,'primary image plan',len(images),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);p.add_argument('--country',default='DE',choices=m.x.COUNTRIES);p.add_argument('--round',type=int,required=True);args=p.parse_args();assert 1<=args.round<=20;configure(args.country,args.round)
    plan(args.country,args.round) if args.command=='plan' else getattr(a,args.command)()
