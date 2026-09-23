#!/usr/bin/env python3
"""Prepare and apply verified language-only corrections to existing projections."""
import argparse,collections,copy,datetime,importlib.util,json,re,subprocess
from pathlib import Path
import mwparserfromhell as mw
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from book_language_review import field_text

spec=importlib.util.spec_from_file_location('capture',Path(__file__).with_name('review-book-languages-20260922.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
MANIFEST=r.ROOT/'ops/curated-book-languages-20260922.json'

def source_evidence(q):
    capture=r.read(r.RUN/'wikipedia'/(q+'.json'));page=capture['page'];entity=r.read(r.RUN/'entities'/(q+'.json'))
    assert page['pageprops']['wikibase_item']==q,(q,page['pageprops']['wikibase_item'])
    return {'wikipedia':{'url':'https://en.wikipedia.org/w/index.php?oldid='+str(page['revisions'][0]['revid']),'revision':page['revisions'][0]['revid'],'pageId':page['pageid'],'source':capture['receipt']},'wikidata':{'url':'https://www.wikidata.org/w/index.php?title='+q+'&oldid='+str(entity['entity']['lastrevid']),'revision':entity['entity']['lastrevid'],'P407':entity['entity'].get('claims',{}).get('P407',[]),'source':entity['receipt']}}

def prepare():
    manifest=r.read(MANIFEST);rows=r.read(r.RUN/'parsed-review.json');manual=manifest['manual'];selected=set(manifest['reviewedExplicitFields']);plan=[];index=[]
    for row in rows:
        q=row['qid'];wp=row['wikipedia'];new=None;basis=None
        if q in manual:
            review=manual[q];capture=r.read(r.RUN/'wikipedia'/(q+'.json'));text=capture['page']['revisions'][0]['slots']['main']['content']
            plain=re.sub(r'\s+',' ',mw.parse(text).strip_code())
            fields=' '.join(f['text'] for f in wp['fields'])
            assert review['evidenceText'].casefold() in (plain+' '+fields).casefold(),('Missing manual evidence',q,review['evidenceText'])
            new=sorted(review['languages']);basis=review['basis'];state='confirmed_manual_composition'
        elif q in selected:
            assert wp['state']=='explicit_language_field'
            new=wp['languages'];basis='Reviewed the explicit book-language field and article introduction for the matched work. Translated editions, settings and fictional languages do not establish the language of original composition.';state='confirmed_explicit_correction'
        elif not row['old'] and wp['state']=='explicit_language_field' and q not in manifest['holdEmptyExplicitFields']:
            new=wp['languages'];basis='The matched work has an explicit Wikipedia language field, reviewed with its introduction; fill the previously empty projection.';state='confirmed_missing_language'
        elif wp['state']=='explicit_language_field' and row['old']==wp['languages']:
            state='existing_language_corroborated'
        elif row['old'] and wp['state']=='explicit_language_field' and set(row['old'])<= {'Q1860','Q7976','Q7979','Q44676','Q323955','Q301383'} and wp['languages']==['Q1860']:
            state='existing_english_variety_retained'
        elif q in manifest['holdEmptyExplicitFields']:state='work_version_review'
        elif wp['state']=='explicit_language_field':state='language_difference_review'
        else:state=wp['state']
        entry={k:row[k] for k in ('bookId','qid','title','old','fresh')};entry.update(state=state,proposed=new,wikipedia={k:v for k,v in wp.items() if k!='lead'})
        index.append(entry)
        if new is not None and new!=row['old']:
            assert new and len(new)==len(set(new))
            proof=source_evidence(q)
            plan.append({'bookId':row['bookId'],'qid':q,'title':row['title'],'before':row['old'],'after':new,'review':{'version':manifest['version'],'meaning':manifest['meaning'],'basis':basis,'decision':state,**proof}})
    assert selected<={row['qid'] for row in rows} and manual.keys()<={row['qid'] for row in rows}
    summary={'audited':len(rows),'wikipediaCaptured':len(list((r.RUN/'wikipedia').glob('*.json'))),'changes':len(plan),'gapsFilled':sum(not v['before'] for v in plan),'languageMembershipsAdded':sum(len(set(v['after'])-set(v['before'])) for v in plan),'languageMembershipsRemoved':sum(len(set(v['before'])-set(v['after'])) for v in plan),'states':dict(collections.Counter(v['state'] for v in index))}
    r.save(r.RUN/'correction-plan.json',{'version':manifest['version'],'manifestSha256':r.sha(MANIFEST.read_bytes()),'summary':summary,'changes':plan})
    r.save(r.RUN/'review-index.json',index);print(json.dumps(summary,indent=2))

def connect(target,readonly=False):
    if target=='local':kwargs=psycopg.conninfo.conninfo_to_dict(r.DSN)
    else:
        value=subprocess.run(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319'],capture_output=True,text=True,check=True).stdout.strip()
        kwargs=psycopg.conninfo.conninfo_to_dict(value);kwargs.update(host='127.0.0.1',port='55433',sslmode='disable')
    return psycopg.connect(**kwargs,row_factory=dict_row,options='-c timezone=UTC'+(' -c default_transaction_read_only=on' if readonly else ''))

def projection_digest(row):
    row=copy.deepcopy(row);row.pop('projection_checksum',None)
    stamp=row['checked_at']
    if isinstance(stamp,str):stamp=datetime.datetime.fromisoformat(stamp.replace('Z','+00:00'))
    row['checked_at']=stamp.astimezone(datetime.timezone.utc).isoformat()
    return r.sha(r.encode(row))

def apply(target):
    plan=r.read(r.RUN/'correction-plan.json');changes=plan['changes'];stamp=r.sha(r.encode(plan))
    base=r.read(Path(r.read(r.RUN/('baseline-'+target+'-reference.json'))['path']));expected={v['book']['id']:v for v in base['books']}
    terms={q for v in changes for q in v['after']};term_rows=[]
    for q in sorted(terms):
        source=r.read(r.RUN/'language-entities'/(q+'.json'));entity=source['entity'];name=entity.get('labels',{}).get('en',{}).get('value')
        assert name
        term_rows.append({'key':q,'name':name,'evidence':{'sourceUrl':'https://www.wikidata.org/wiki/'+q,'revision':entity['lastrevid'],'source':source['receipt']}})
    for change in changes:
        for source in (change['review']['wikipedia']['source'],change['review']['wikidata']['source']):assert r.sha(Path(source['archive']).read_bytes())==source['archive_sha256']
    with connect(target) as db:
        for offset in range(0,len(changes),50):
            batch=changes[offset:offset+50];receipt=r.RUN/'applications'/target/(str(offset)+'.json')
            if receipt.exists():assert r.read(receipt)['planSha256']==stamp;continue
            ids=[v['bookId'] for v in batch]
            with db.transaction():
                db.execute('SELECT pg_advisory_xact_lock(202609220407)')
                books={v['id']:v for v in db.execute('SELECT id,source_id,source_checksum,status FROM book_records WHERE id=ANY(%s) ORDER BY id FOR SHARE',(ids,))}
                current={v['book_id']:v for v in db.execute('SELECT * FROM book_discovery WHERE book_id=ANY(%s) ORDER BY book_id FOR UPDATE',(ids,))}
                oldterms=db.execute("SELECT * FROM book_discovery_terms WHERE kind='language' AND key=ANY(%s)",(sorted(terms),)).fetchall()
                backup=r.BACKUP/(target+'-batch-'+str(offset)+'.json')
                if not backup.exists():r.save(backup,{'at':r.now(),'planSha256':stamp,'books':books,'discovery':current,'terms':oldterms})
                applied=[]
                for v in batch:
                    id=v['bookId'];book=books[id];old=current[id];pre=expected[id]
                    assert book['source_id']==v['qid'] and book['source_checksum']==old['book_checksum']
                    assert book['source_checksum']==pre['book']['source_checksum'] and book['status']==pre['book']['status']
                    if old['languages']==v['after'] and old['evidence'].get('languageReview')==v['review']:applied.append(id);continue
                    assert sorted(old['languages'])==v['before'],('Languages changed',id)
                    assert old['projection_checksum']==pre['discovery']['projection_checksum'],('Projection changed',id)
                    new=copy.deepcopy(old);new['languages']=v['after'];new['evidence']['languageReview']=v['review'];new['checked_at']=datetime.datetime.now(datetime.timezone.utc);new['projection_checksum']=projection_digest(new)
                    for term in term_rows:
                        if term['key'] in v['after']:db.execute("INSERT INTO book_discovery_terms(kind,key,name,evidence) VALUES('language',%s,%s,%s) ON CONFLICT DO NOTHING",(term['key'],term['name'],Jsonb(term['evidence'])))
                    result=db.execute('UPDATE book_discovery SET languages=%s,evidence=%s,checked_at=%s,projection_checksum=%s WHERE book_id=%s AND projection_checksum=%s',(new['languages'],Jsonb(new['evidence']),new['checked_at'],new['projection_checksum'],id,old['projection_checksum']))
                    assert result.rowcount==1;applied.append(id)
            r.save(receipt,{'at':r.now(),'planSha256':stamp,'books':applied,'backup':str(backup),'backupSha256':r.sha(backup.read_bytes())})
            print(target,'corrected',offset+len(batch),'of',len(changes),flush=True)
    verify(target)

def verify(target):
    plan=r.read(r.RUN/'correction-plan.json');changes={v['bookId']:v for v in plan['changes']};base=r.read(Path(r.read(r.RUN/('baseline-'+target+'-reference.json'))['path']))
    expected={v['book']['id']:v for v in base['books']}
    with connect(target,True) as db:
        after=db.execute('SELECT to_jsonb(b) book,to_jsonb(d) discovery FROM book_records b LEFT JOIN book_discovery d ON d.book_id=b.id ORDER BY b.id').fetchall()
        termkeys={v['key'] for v in db.execute("SELECT key FROM book_discovery_terms WHERE kind='language'")}
    def same_json(a,b):
        # jsonb timestamp strings depend on the connection timezone.
        return r.encode(a)==r.encode(b)
    for row in after:
        id=row['book']['id'];before=expected[id]
        for key,value in before['book'].items():
            if key=='imported_at':assert datetime.datetime.fromisoformat(value)==datetime.datetime.fromisoformat(row['book'][key])
            else:assert value==row['book'][key],('Base record modified',id,key)
        d=row['discovery'];pre=before['discovery'];assert d and d['book_checksum']==row['book']['source_checksum'];assert set(d['languages'])<=termkeys
        for key in ('book_checksum','woman_author_ids','top100','countries','regions'):assert d[key]==pre[key],('Unrelated projection modified',id,key)
        if id in changes:
            change=changes[id];assert d['languages']==change['after'];assert d['evidence']['languageReview']==change['review'];assert projection_digest(d)==d['projection_checksum']
            assert {k:v for k,v in d['evidence'].items() if k!='languageReview'}==pre['evidence']
        else:
            assert d['projection_checksum']==pre['projection_checksum'] and d['languages']==pre['languages'] and d['evidence']==pre['evidence']
    assert len(after)==len(expected)==10000
    result={'at':r.now(),'target':target,'booksChecked':len(after),'languagesCorrected':len(changes),'emptyLanguages':sum(not v['discovery']['languages'] for v in after),'statuses':dict(collections.Counter(v['book']['status'] for v in after)),'errors':[]}
    r.save(r.RUN/(target+'-verification.json'),result);print(json.dumps(result,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','apply','verify']);parser.add_argument('--target',choices=['local','production']);args=parser.parse_args()
    if args.phase=='prepare':prepare()
    else:assert args.target;globals()[args.phase](args.target)
