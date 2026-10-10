"""Independent source, image and live backend checks; real databases read-only."""
import hashlib,importlib.util,json
from pathlib import Path
from PIL import Image
from psycopg.types.json import Jsonb
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-jewish-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
c,m,RUN=a.c,a.m,a.RUN

def main():
    dest=RUN/'offline-tests-001.json';assert not dest.exists();p,digest=a.validate_plan();checked=[];by={v['facts']['number']:v['facts'] for v in p['records']};ims={x['number']:x for x in p['images']}
    def check(name,condition):assert condition,name;checked.append(name)
    check('140physicalunitsretain143nonoverlappingsourceIDs',len(by)==140 and len({s for f in by.values() for s in f['source_ids']})==143)
    check('Duplicate slipper panel mergedacrosssubcollections',by[1021]['source_numbers']==[1021,1023] and 1023 not in by)
    check('Repeated dedication panel photos merged',by[1038]['source_numbers']==[1038,1039] and 1039 not in by)
    check('Canopy front and lining detail merged, frontprimary',by[1195]['source_numbers']==[1195,1194] and 1194 not in by and ims[1195]['verified_https_source_image_url'].endswith('web_DSC_7553_2005.37.jpg'))
    check('Bobbin scope and nearidentical cushion identityheld',1072 not in by and 1117 not in by)
    rows=m.load(RUN/'selected-source-records-002.json.gz')['rows'];excluded={x['number'] for x in rows if x['decision'] in ['external_collection_hold','photographic_surrogate_hold','post1970_depicted_event_hold']}
    check('ExternalIoanninaobjects, surrogates and1972cartoons excluded',len(excluded)==87 and not excluded&set(by))
    check('Five unresolved dates remainNULL',{n for n,f in by.items() if f['first'] is None}=={76,154,1038,1063,1115} and all(by[n]['last'] is None for n in [76,154,1038,1063,1115]))
    check('Conflicting textile date retainscrossing20thcentury',tuple(by[1053][k] for k in ['first','last','date_precision'])==(1901,2000,'century') and 1053 not in ims)
    check('Qualifiedliteralrange retains19thcenturyomittedbyindex',tuple(by[1021][k] for k in ['first','last'])==(1871,1930) and tuple(by[1107][k] for k in ['first','last'])==(1851,1950))
    check('1930s paintingnotexact1930',tuple(by[44][k] for k in ['first','last','date_precision'])==(1930,1939,'decade'))
    check('Source makerroles remainqualifiedwithoutfalseUnknown/Gillotlinks',all(f['artist_id'] is None for f in by.values()) and 'role unresolved' in by[71]['creator_label'] and all(f['inventory'] is None for f in by.values()))
    check('Imagesstrictlycreationthrough1955',all(x['first'] is not None and x['last']<=1955 for x in ims.values()) and not {48,76,154,185,192,1038,1053,1063,1115}&set(ims))
    check('131nativeimages retainactualrestrictedInCopyright',len(ims)==131 and all(x['rights_status']=='restricted' and x['rights_label']=='In Copyright (InC)' and x['verified_https_source_image_url'].startswith('https://artifacts.jewishmuseum.gr/wp-content/uploads/') for x in ims.values()))
    for im in ims.values():
        raw=Path(im['prepared_path']).read_bytes();assert len(raw)==im['bytes']<=100000 and hashlib.sha256(raw).hexdigest()==im['sha256']
        with Image.open(im['prepared_path']) as x,Image.open(im['original_reference']['path']) as src:
            x.load();src.load();assert x.format=='JPEG' and x.size==(im['width'],im['height']) and x.width<=src.width and x.height<=src.height and abs(x.width/src.width-x.height/src.height)<.003
        assert a.sha(im['original_reference']['path'])==im['original_reference']['sha256']
    check('All derivativehashesdimensionsproportions andarchivedoriginals verified',True)
    check('52sourcesbyteunchanged,79compressedwithoutcropping',sum(x['mode']=='source_bytes_unchanged' for x in ims.values())==52 and all(x['complete_source_frame'] for x in ims.values()))
    check('Eightoldprimaries andrecordsnotreplaced',len(p['before']['artworks'])==8 and len(p['before']['media_assets'])==8 and not {x['sha256'] for x in ims.values()}&{x['checksum_sha256'] for x in p['before']['media_assets']})
    check('FullpreparedvisualQAcompleted',m.load(RUN/'final-identity-review-001.json')['prepared_images_visual_qa']['prepared_sheets']==6)
    check('Objectformobeysobservednulloriconconstraint',all(a.metadata(v)['object_form'] is None for v in p['records']) and any(x['conname']=='artwork_object_form' for x in p['constraints']))
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');a.preflight(db,p);check('Livepreflightpreserves8old2798priorand4titlecounterparts',True)
        values=[dict(number=n,first=f['first'],last=f['last'],precision=f['date_precision']) for n,f in by.items()]
        classification=db.execute('SELECT number,artline_creation_scope(first,last,precision) scope FROM jsonb_to_recordset(%s) AS x(number int,first int,last int,precision text) ORDER BY number',(Jsonb(values),)).fetchall();counts={s:sum(x['scope']==s for x in classification) for s in ['eligible','review','excluded']};check('Backendclassifies134eligible6review0excluded',counts==dict(eligible=134,review=6,excluded=0))
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');old=m.load(RUN/'initial-scope-001.json.gz');check('Reallocalcatalogueunchanged',c.snapshot(db,old['scoped_ids'])==old['snapshot'] and c.counts(db)==old['counts'])
    m.save(dest,dict(at=m.now(),tests_passed=len(checked),exit_code=0,checks=checked,backend_classification=classification,plan_sha256=digest,read_only=True,no_fixtures=True,script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(tests_passed=len(checked),backend_scope=counts,plan_sha256=digest)),flush=True)

if __name__=='__main__':main()
