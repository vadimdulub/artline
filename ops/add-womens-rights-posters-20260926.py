#!/usr/bin/env python3
"""Six documented suffrage prints; preserve metadata without restricted images."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('core',Path(__file__).with_name('add-islamic-world-images-20260925.py'))
core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
core.CAMPAIGN='womens-rights-posters-20260926'
core.RUN=core.ROOT/'docs/research/womens-rights-20260926'
ROWS=[
 (967741,'the-prehistoric-argument','The Prehistoric Argument','NN29405',1909,1913,'Catharine Courtauld (design); Suffrage Atelier (publisher)','card, ink','H 140 mm, W 88 mm','A suffrage postcard challenging the idea that women belong only in domestic life.'),
 (454041,'the-anti-suffrage-society-as-dressmaker','The Anti-Suffrage Society As Dressmaker','50.82/1646',1909,1912,'Suffrage Atelier','card, ink','H 139 mm, W 89 mm','A pro-suffrage satire depicting opposition to women’s voting as an ill-fitting, outdated dress.'),
 (454039,'the-anti-suffrage-society-as-prophet','The Anti-Suffrage Society As Prophet','50.82/1645',1912,1913,'Catharine Courtauld (design); Suffrage Atelier (publisher)','card, ink','H 140 mm, W 88 mm','A pro-suffrage postcard satirising predictions that women’s voting would destroy the nation.'),
 (479072,'the-appeal-of-womanhood-we-want-the-vote-to-stop-the-white-slave-traffic','The appeal of womanhood, we want the vote to stop the white slave traffic','50.82/1068c',1912,1912,'Louise Jacobs (design); Suffrage Atelier','paper, ink','H 1010 mm, W 757 mm','A campaign poster linking voting rights with protection from sexual and economic exploitation. The historical title is retained.'),
 (480187,'white-slave-traffic-the-only-solution-woman-suffrage','White slave traffic the only solution, woman Suffrage','50.82/1054b',1912,1912,'Suffrage Atelier','paper',None,'Suffrage represented as protection against exploitation at work and in sexual commerce. The historical title is retained.'),
 (289091,'the-unwelcome-guest','The Unwelcome Guest','50.82/787',1909,1913,'Suffrage Atelier','card, ink','H 88 mm, W 140 mm','A pro-suffrage satirical postcard from the Suffrage Atelier’s campaign publications.'),
]

def plan():
    iid=core.uid('institution/london-museum')
    institution=dict(id=iid,slug='london-museum',name='London Museum',normalized_name=core.norm('London Museum'),kind='museum',status='review',website_url='https://www.londonmuseum.org.uk/')
    records=[]
    with core.connect() as db:
        assert not db.execute("SELECT 1 FROM institutions WHERE slug='london-museum'").fetchone()
        for oid,slug,title,accession,lo,hi,maker,medium,dimensions,description in ROWS:
            url=f'https://www.londonmuseum.org.uk/collections/v/object-{oid}/{slug}/'
            assert not db.execute('SELECT 1 FROM citations WHERE source_url=%s',(url,)).fetchone()
            records.append(dict(id=core.uid(str(oid)),slug='womens-rights-london-'+str(oid),title=title,normalized_title=core.norm(title),
                accession_number=accession,creation_year_start=lo,creation_year_end=hi,date_display=str(lo) if lo==hi else f'{lo}–{hi}',
                date_precision='exact' if lo==hi else 'range',work_type='print',unlinked_creator_label=maker,medium_text=medium,
                dimensions_text=dimensions,description_md=description,current_institution_id=iid,status='review',research_candidate=True,
                created_by=core.ACTOR,updated_by=core.ACTOR,source_url=url,source_record_id=str(oid)))
    captures={p.name:core.sha(p.read_bytes()) for p in (core.RUN/'captures').glob('london-web-batch*.txt')}
    assert len(captures)==2
    core.save(core.RUN/'posters-plan.json',dict(institution=institution,records=records,captures=captures,
        image_decision='No downloads: museum images are restricted or CC BY-NC, outside the current unrestricted-image workflow.',
        creator_note='Museum prose uses both Catherine and Catharine Courtauld. Object-level label retains Catharine; original spellings remain in captures. Collectives are named makers, not invented individual artists.'))
    core.save(core.RUN/'posters-pin.json',dict(sha256=core.sha((core.RUN/'posters-plan.json').read_bytes())))

def apply():
    p=core.load('posters-plan.json');assert core.sha((core.RUN/'posters-plan.json').read_bytes())==core.load('posters-pin.json')['sha256']
    b=core.load('backup.json');assert core.sha(Path(b['path']).read_bytes())==b['sha256']
    for name,digest in p['captures'].items():assert core.sha((core.RUN/'captures'/name).read_bytes())==digest
    sid=core.uid('source/london-museum')
    with core.connect(False) as db,db.transaction():
        db.execute('SELECT pg_advisory_xact_lock(559220260915)');db.execute('SELECT pg_advisory_xact_lock(20250907001)')
        db.execute("SET LOCAL lock_timeout='5s'")
        core.insert(db,'institutions',p['institution'])
        core.insert(db,'sources',dict(id=sid,slug=core.CAMPAIGN,name='London Museum — selected suffrage prints',source_type='collection_page',base_url='https://www.londonmuseum.org.uk/collections/'))
        for row in p['records']:
            c=dict(row);url=c.pop('source_url');oid=c.pop('source_record_id')
            assert not db.execute('SELECT 1 FROM citations WHERE source_url=%s',(url,)).fetchone()
            core.insert(db,'artworks',c)
            core.insert(db,'artwork_location_assertions',dict(artwork_id=c['id'],claim_type='holding',institution_id=p['institution']['id'],context='collection',
                source_id=sid,source_url=url,evidence_note='Museum object page identifies this accession as its permanent collection. No current display claim.',checked_at=core.now(),review_state='accepted'))
            core.insert(db,'citations',dict(entity_type='artwork',entity_id=c['id'],field_name='official_object_identity',source_id=sid,source_record_id=oid,
                source_url=url,evidence_note=json.dumps(dict(captures=p['captures'],creator_note=p['creator_note'],image_decision=p['image_decision']),ensure_ascii=False),retrieved_at=core.now(),created_by=core.ACTOR))
    core.save(core.RUN/'posters-applied.json',dict(records=len(p['records']),target='local',review_only=True,images_downloaded=0))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['plan','apply']);globals()[p.parse_args().phase]()
