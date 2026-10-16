"""Object/date/image checks and read-only production/local preflight."""
import hashlib,importlib.util,json
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-momus-apply-v2-20261011.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
c,m,RUN=a.c,a.m,a.RUN

def main():
    p,digest=a.validate_plan();checks=[];by={v['facts']['number']:v['facts'] for v in p['records']};ims={im['number']:im for im in p['images']}
    def check(name,condition):assert condition,name;checks.append(name)
    check('199unique native physical objects, each with explicit ContemporaryArt museum',len(by)==199 and len({f['inventory'] for f in by.values()})==199 and all(f['source_facts']['native']['momus_museum_s']=='Μουσείο Σύγχρονης Τέχνης' for f in by.values()))
    check('Native literal1967–1974period preserved over falsely narrow index years',all((by[n]['first'],by[n]['last'])==(1967,1974) for n in [7725,8005]))
    check('Literal creation dates recover records missing indexed dates',by[8793]['first']==1955 and by[14277]['first']==1912 and by[9439]['first']==1949)
    check('Period labels remain ranges, never midpoint years',(by[9653]['first'],by[9653]['last'])==(1940,1944) and (by[9093]['first'],by[9093]['last'])==(1950,1967))
    check('Multipart Tobacco work counts once and smaller version remains distinct',by[17784]['inventory']=='PD-0270/2013' and by[17785]['inventory']=='PD-0271/2013' and '1240' in by[17784]['dimensions_text'] and '380' in by[17785]['dimensions_text'])
    check('Aperghis figures retain different source heights and identities','108' in by[7460]['dimensions_text'] and '105' in by[7497]['dimensions_text'] and by[7460]['inventory']!=by[7497]['inventory'])
    check('No invented maker links or unsupported objectform',all(f['artist_id'] is None and a.metadata(v)['object_form'] is None for v in p['records'] for f in [v['facts']]))
    check('38images creationthrough1955 retainunknown native rights separately from approval',len(ims)==38 and all(x['last']<=1955 and x['rights_status']=='unknown' and x['rights_url'] is None for x in ims.values()))
    for im in ims.values():
        raw=Path(im['prepared_path']).read_bytes();assert len(raw)==im['bytes']<=100000 and hashlib.sha256(raw).hexdigest()==im['sha256']
        with Image.open(im['prepared_path']) as image,Image.open(im['original_reference']['path']) as source:
            assert image.format=='JPEG' and image.size==(im['width'],im['height']) and image.width<=source.width and image.height<=source.height
            assert abs(image.width/source.width-image.height/source.height)<.003
        assert a.sha(im['original_reference']['path'])==im['original_reference']['sha256']
    check('All original and derivative bytes/dimensions/full-frame proportions verified',True)
    qa=m.load(RUN/'editorial-final-review-002.json');check('All selected and prepared images visually reviewed',qa['source_frames_reviewed']==199 and qa['prepared_frames_reviewed']==38 and qa['all_prepared_frames_complete'])
    check('Old11 artworks remain excluded from selection',not {v['artwork_id'] for v in p['records']}&set(p['scoped_ids']))
    check('Backend classifies197eligible and2review; no automatic crossing-range eligibility',p['backend_date_classification']==dict(eligible=197,review=2))
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');a.preflight(db,p);check('Live production preflight and source/image duplicate guards passed',True)
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');old=m.load(RUN/'initial-scope-001.json.gz');check('Real local museum scope unchanged without fixtures',c.snapshot(db,old['scoped_ids'])==old['snapshot'] and c.counts(db)==old['counts'])
    m.save(RUN/'offline-tests-001.json',dict(at=m.now(),tests_passed=len(checks),exit_code=0,checks=checks,plan_sha256=digest,read_only=True,no_fixtures=True));print(json.dumps(dict(tests_passed=len(checks),plan_sha256=digest)),flush=True)

if __name__=='__main__':main()
