#!/usr/bin/env python3
"""Two selected Met works about women’s artistic education; local review only."""
import argparse
import importlib.util
from pathlib import Path
import sys
sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('core',Path(__file__).with_name('add-islamic-world-images-20260925.py'))
core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
PARENT=core.ROOT/'docs/research/womens-rights-20260926'
core.CAMPAIGN='womens-rights-images-20260926'
core.SOURCE_LABEL='Women’s artistic education and professional access'
core.RUN=PARENT/'images'
core.BACKUP=core.DATA/'backups'/core.CAMPAIGN
core.ORIGINALS=core.DATA/'source-images'/core.CAMPAIGN
core.COUNTRIES={}
core.PROVIDERS={'met':core.PROVIDERS['met']}

def plan():
    records=[]
    policy=core.RUN/'captures/met-policy-web.txt'
    assert b'Creative Commons Zero' in policy.read_bytes()
    with core.connect() as db:
        institution=db.execute("SELECT to_jsonb(i) record FROM institutions i WHERE slug='the-met'").fetchone()['record']
        for oid,kind,reason in [
            (626348,'print','A newspaper engraving about a woman artist’s exclusion from the art market; Edward Skill after Emily Mary Osborn.'),
            (335183,'drawing','Two women pupils portrayed for Labille-Guiard’s self-portrait: artistic education and mentorship.')]:
            o=core.load(f'captures/met-{oid}.json'); receipt=core.load(f'captures/met-{oid}.receipt.json')
            assert core.sha((core.RUN/f'captures/met-{oid}.json').read_bytes())==receipt['sha256']
            assert o['isPublicDomain'] is True and o['primaryImage'] and o['objectEndDate']<=1970
            key='met-'+str(oid)
            c=dict(key=key,provider='met',object_id=str(oid),accession=o['accessionNumber'],title=o['title'],
                lo=o['objectBeginDate'],hi=o['objectEndDate'],date_display=o['objectDate'],precision='exact' if oid==626348 else 'circa_range',
                type=kind,country=None,culture=None,place_display=None,
                maker='Edward Skill (engraver), after Emily Mary Osborn' if oid==626348 else 'Adélaïde Labille-Guiard',
                url=o['objectURL'],image_url=o['primaryImage'],medium=o['medium'],dimensions=o['dimensions'],credit=o['creditLine'],
                reason=reason,object=o,capture=receipt,institution_id=institution['id'],artwork_id=core.uid(key),slug='womens-rights-'+key,
                scope_note='Museum creation date and range retained. Engraver, source artist and sitters remain distinct; no invented birthplace, nationality, biography or display claim.')
            assert not core.duplicate(db,c)
            assert not db.execute('SELECT id FROM artworks WHERE accession_number=%s',(c['accession'],)).fetchone()
            records.append(c)
    core.save(core.RUN/'plan.json',dict(records=records,institutions={'met':institution},country_preimages=[],
        policies={'met':dict(url=core.PROVIDERS['met']['policy'],sha256=core.sha(policy.read_bytes()),capture='captures/met-policy-web.txt',transport='web tool')},
        selection_bound='Two exact primary-source museum records, manually selected before image downloading.'))
    core.save(core.RUN/'plan-pin.json',dict(sha256=core.sha((core.RUN/'plan.json').read_bytes())))
    # The parent campaign’s validated dump predates every insertion in this run.
    core.save(core.RUN/'backup.json',(PARENT/'backup.json').read_bytes())

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['plan','prepare','apply','verify']);phase=p.parse_args().phase
    (globals().get(phase) or getattr(core,phase))()
