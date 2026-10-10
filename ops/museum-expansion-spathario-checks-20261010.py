"""Offline evidence checks and read-only backend classification; no database fixtures."""
import importlib.util,json
from pathlib import Path
from psycopg.types.json import Jsonb
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-spathario-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
c,m,RUN=a.c,a.m,a.RUN

def main():
    assert not(RUN/'offline-tests-001.json').exists();p,digest=a.validate_plan();checked=[];records=p['records'];by={v['facts']['number']:v['facts'] for v in records}
    def check(name,condition):assert condition,name;checked.append(name)
    check('Opposite police-puppet views share one artwork with bothsourceIDs',by[149]['source_ids']==['Mar_Spathareio/000223-69','Mar_Spathareio/000223-71'] and 125 not in by)
    check('Spit scene retains operating component without doublecount',by[24]['source_ids']==['Mar_Spathareio/000223-420','Mar_Spathareio/000223-421'] and 151 not in by)
    check('Paired papercraft serialnumbers remain one sheet each',all(len(by[n]['source_ids'])==1 and by[n]['work_type']=='print' for n in range(102,108)))
    check('Distinct skeletons and translatedManolopouloscharacters notcollapsed',all(n in by for n in [45,46,119,120]) and by[45]['title']!=by[46]['title'])
    check('Six literal19thcentury descriptions become centuries, not inventedyears',all((by[n]['first'],by[n]['last'],by[n]['date_precision'])==(1801,1900,'century') for n in [38,39,40,41,82,112]))
    unknown={n for n,f in by.items() if f['first'] is None}
    check('Conflicting performance dates and assemblage dates remain unknown',unknown=={23,25,93,110,111,146,149,150} and all(by[n]['last'] is None and by[n]['date_precision']=='unknown' for n in unknown))
    check('Unknown creations never receive image delivery',not unknown&{im['number'] for im in p['images']})
    check('Source-only publisher or frame roles do not become artistlinks',all(f['artist_id'] is None for f in by.values()) and 'publisher' in by[71]['creator_label'] and 'photographer unidentified' in by[110]['creator_label'])
    excluded=set(c.module('decision','museum-expansion-spathario-review-20261010.py').SCOPE)|{124}
    check('Utility and unresolved aircraft records excluded',not excluded&set(by))
    check('All images remain actualrestricted CC BY-NC-SA sourceJPEGs',all(im['rights_status']=='restricted' and im['rights_label']=='CC BY-NC-SA 4.0' and im['complete_source_frame'] and im['mode']=='source_bytes_unchanged' and im['last']<=1955 and im['bytes']<=100000 and a.sha(im['prepared_path'])==a.sha(im['original_reference']['path']) for im in p['images']))
    check('Oldsevenprimaries have no checksum replacement',not {im['sha256'] for im in p['images']}&{im['checksum_sha256'] for im in p['before']['media_assets']})
    check('Existing16catalogue identities disjoint from newIDs',not set(p['scoped_ids'])&{v['artwork_id'] for v in records} and len(p['before']['artworks'])==16)
    check('Objectform conforms to observedicon/null constraint',all(a.metadata(v)['object_form'] is None for v in records) and any(x['conname']=='artwork_object_form' and "'icon'" in x['definition'] for x in p['constraints']))
    later=m.load(RUN/'metadata-selection-001.json')['excluded'];check('294laterindexrecords notimported',len(later)==294 and not {x['source_id'] for x in later}&{s for v in records for s in v['facts']['source_ids']})
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');a.preflight(db,p)
        check('Livepreflight preserves16old and2683priorrecords',True)
        values=[dict(number=n,first=f['first'],last=f['last'],precision=f['date_precision']) for n,f in by.items()]
        classification=db.execute('SELECT number,artline_creation_scope(first,last,precision) scope FROM jsonb_to_recordset(%s) AS x(number int,first int,last int,precision text) ORDER BY number',(Jsonb(values),)).fetchall()
        counts={scope:sum(x['scope']==scope for x in classification) for scope in ['eligible','review','excluded']}
        check('Backendclassifies107eligible8review0excluded',counts==dict(eligible=107,review=8,excluded=0))
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');old=m.load(RUN/'initial-scope-001.json.gz');check('Reallocaldatabaseunchanged',c.snapshot(db,old['scoped_ids'])==old['snapshot'] and c.counts(db)==old['counts'])
    m.save(RUN/'offline-tests-001.json',dict(at=m.now(),tests_passed=len(checked),exit_code=0,checks=checked,backend_classification=classification,plan_sha256=digest,read_only=True,no_fixtures=True,script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(tests_passed=len(checked),backend_scope=counts,plan_sha256=digest)),flush=True)

if __name__=='__main__':main()
