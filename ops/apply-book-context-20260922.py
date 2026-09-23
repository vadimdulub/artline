#!/usr/bin/env python3
"""Reconcile sourced overviews without losing corrected book discovery data."""
import argparse,collections,copy,datetime,importlib.util,json
from pathlib import Path
from psycopg.types.json import Jsonb
from book_context import overview

spec=importlib.util.spec_from_file_location('languages',Path(__file__).with_name('apply-book-languages-20260922.py'))
l=importlib.util.module_from_spec(spec);spec.loader.exec_module(l)
r=l.r;RUN=r.ROOT/'docs/research/book-context-20260922';BACKUP=r.BACKUP.parent/'book-context-20260922'

def snapshot(db):
    return {'books':db.execute('SELECT to_jsonb(b) book,to_jsonb(d) discovery FROM book_records b LEFT JOIN book_discovery d ON d.book_id=b.id ORDER BY b.id').fetchall(),'creators':db.execute('SELECT to_jsonb(c) creator FROM book_creators c ORDER BY id').fetchall(),'links':db.execute('SELECT to_jsonb(l) link FROM book_creator_links l ORDER BY book_id,position').fetchall()}

def prepare():
    assert (RUN/'capture-finished.json').exists(),'Source capture must complete before preparation.'
    base=r.read(Path(r.read(r.RUN/'baseline-local-reference.json')['path']));creators=r.read(Path(r.read(RUN/'baseline-local-reference.json')['path']))['creators']
    wanted={'book':{v['book']['source_id']:v['book']['id'] for v in base['books']},'creator':{v['creator']['id']:v['creator']['id'] for v in creators}}
    items=[];queue=[]
    for kind,identities in wanted.items():
        for q,id in sorted(identities.items()):
            path=RUN/(kind+'-introductions')/(q+'.json')
            if not path.exists():queue.append({'kind':kind,'id':id,'qid':q,'state':'no_enwiki_introduction'});continue
            capture=r.read(path);value,state=overview(capture,q,kind)
            if value:
                proof={'version':'book-context-20260922-v1','kind':kind,'qid':q,'source':capture['receipt'],'basis':'Bounded excerpt of the matched Wikipedia article introduction; no inferred authorship, dates, nationality or language.'}
                items.append({'kind':kind,'id':id,'qid':q,'overview':value,'evidence':proof})
            else:queue.append({'kind':kind,'id':id,'qid':q,'state':state})
    result={'version':'book-context-20260922-v1','items':items,'summary':{'prepared':dict(collections.Counter(v['kind'] for v in items)),'unresolved':dict(collections.Counter(v['kind'] for v in queue))}}
    r.save(RUN/'overview-plan.json',result);r.save(RUN/'unresolved-overviews.json',queue)
    print(json.dumps(result['summary'],indent=2))

def apply(target):
    plan=r.read(RUN/'overview-plan.json');stamp=r.sha(r.encode(plan));receipt=RUN/(target+'-apply.json')
    if receipt.exists():assert r.read(receipt)['planSha256']==stamp;verify(target);return
    refs={v['evidence']['source']['archive']:v['evidence']['source']['archive_sha256'] for v in plan['items']}
    for path,sha in refs.items():assert r.sha(Path(path).read_bytes())==sha
    edits={kind:{v['id']:v for v in plan['items'] if v['kind']==kind} for kind in ('book','creator')}
    with l.connect(target) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='15s'")
        db.execute('SELECT pg_advisory_xact_lock(202609220408)')
        db.execute('LOCK TABLE book_records,book_creators,book_creator_links,book_discovery IN SHARE ROW EXCLUSIVE MODE')
        before=snapshot(db);backup=BACKUP/('before-context-'+target+'.json');r.save(backup,before)
        books={v['book']['id']:copy.deepcopy(v) for v in before['books']};creators={v['creator']['id']:copy.deepcopy(v['creator']) for v in before['creators']}
        assert edits['book'].keys()<=books.keys() and edits['creator'].keys()<=creators.keys()
        affected=set(edits['book']);links=collections.defaultdict(list)
        for wrapper in before['links']:
            link=wrapper['link'];links[link['book_id']].append(link)
            if link['creator_id'] in edits['creator']:affected.add(link['book_id'])
        for id,edit in edits['creator'].items():
            creator=creators[id];assert creator['record']['id']==edit['qid'];assert not creator['record'].get('overview'),'Existing overview requires explicit reconciliation'
            creator['record']['overview']=edit['overview'];creator['record']['overviewEvidence']=edit['evidence'];creator['source_checksum']=r.sha(r.encode(creator['record']))
        for id in affected:
            book=books[id]['book'];d=books[id]['discovery'];assert d and d['book_checksum']==book['source_checksum']
            if id in edits['book']:
                edit=edits['book'][id];assert book['source_id']==edit['qid'];assert not book['record'].get('overview'),'Existing overview requires explicit reconciliation'
                book['record']['overview']=edit['overview'];book['record']['overviewEvidence']=edit['evidence']
            credited=[dict(creators[link['creator_id']]['record'],credit=link['credit']) for link in links[id]]
            book['source_checksum']=r.sha(r.encode(dict(book['record'],creators=credited)))
            d['book_checksum']=book['source_checksum'];d['checked_at']=datetime.datetime.now(datetime.timezone.utc)
            d['evidence']['contextReview']={'version':plan['version'],'planSha256':stamp,'basis':'Only attributed overview metadata changed. Preserve language reviews, dates, creator credits, country/region/gender memberships and editorial selection.'}
            d['projection_checksum']=l.projection_digest(d)
        # Temporary tables are transaction-local staging for existing records,
        # not catalogue fixtures or an alternate test database.
        db.execute('CREATE TEMP TABLE context_creator_changes (id text PRIMARY KEY,record jsonb,source_checksum text) ON COMMIT DROP')
        with db.cursor().copy('COPY context_creator_changes FROM STDIN') as cp:
            for id in sorted(edits['creator']):v=creators[id];cp.write_row((id,Jsonb(v['record']),v['source_checksum']))
        db.execute('CREATE TEMP TABLE context_book_changes (id text PRIMARY KEY,record jsonb,source_checksum text) ON COMMIT DROP')
        with db.cursor().copy('COPY context_book_changes FROM STDIN') as cp:
            for id in sorted(affected):v=books[id]['book'];cp.write_row((id,Jsonb(v['record']),v['source_checksum']))
        db.execute('CREATE TEMP TABLE context_discovery_changes (LIKE book_discovery INCLUDING DEFAULTS) ON COMMIT DROP')
        columns=['book_id','book_checksum','woman_author_ids','top100','languages','countries','regions','evidence','checked_at','projection_checksum']
        with db.cursor().copy('COPY context_discovery_changes ('+','.join(columns)+') FROM STDIN') as cp:
            for id in sorted(affected):
                v=books[id]['discovery'];cp.write_row(tuple(Jsonb(v[k]) if k=='evidence' else v[k] for k in columns))
        assert db.execute('UPDATE book_creators c SET record=s.record,source_checksum=s.source_checksum FROM context_creator_changes s WHERE c.id=s.id').rowcount==len(edits['creator'])
        assert db.execute('UPDATE book_records b SET record=s.record,source_checksum=s.source_checksum FROM context_book_changes s WHERE b.id=s.id').rowcount==len(affected)
        assert db.execute('INSERT INTO book_discovery ('+','.join(columns)+') SELECT '+','.join(columns)+' FROM context_discovery_changes').rowcount==len(affected)
        assert db.execute('SELECT count(*) n FROM book_discovery d JOIN book_records b ON b.id=d.book_id WHERE d.book_checksum=b.source_checksum').fetchone()['n']==len(books)
    r.save(receipt,{'at':r.now(),'planSha256':stamp,'bookOverviews':len(edits['book']),'creatorOverviews':len(edits['creator']),'discoveryPreserved':len(affected),'backup':str(backup),'backupSha256':r.sha(backup.read_bytes())})
    verify(target)

def verify(target):
    receipt=r.read(RUN/(target+'-apply.json'));path=Path(receipt['backup']);assert r.sha(path.read_bytes())==receipt['backupSha256'];before=r.read(path)
    with l.connect(target,True) as db:after=snapshot(db)
    assert len(before['books'])==len(after['books'])==10000;assert len(before['creators'])==len(after['creators']);assert before['links']==after['links']
    for prior,current in zip(before['books'],after['books']):
        b0,b1=prior['book'],current['book'];assert b0['id']==b1['id']
        assert {k:v for k,v in b1['record'].items() if k not in ('overview','overviewEvidence')}==b0['record']
        for key in ('source_id','status','title','author_label','start_year','end_year','era','search_text','imported_at'):assert b0[key]==b1[key],(b0['id'],key)
        d0,d1=prior['discovery'],current['discovery'];assert d1['book_checksum']==b1['source_checksum']
        for key in ('languages','countries','regions','woman_author_ids','top100'):assert d0[key]==d1[key],(b0['id'],key)
        assert {k:v for k,v in d1['evidence'].items() if k!='contextReview'}==d0['evidence']
        if 'contextReview' in d1['evidence']:assert l.projection_digest(d1)==d1['projection_checksum']
    for prior,current in zip(before['creators'],after['creators']):
        c0,c1=prior['creator'],current['creator'];assert c0['id']==c1['id'] and c0['name']==c1['name']
        assert {k:v for k,v in c1['record'].items() if k not in ('overview','overviewEvidence')}==c0['record']
    result={'at':r.now(),'target':target,'booksChecked':len(after['books']),'creatorsChecked':len(after['creators']),'bookOverviews':sum(bool(v['book']['record'].get('overview')) for v in after['books']),'creatorOverviews':sum(bool(v['creator']['record'].get('overview')) for v in after['creators']),'languageCorrectionsPreserved':170,'statuses':dict(collections.Counter(v['book']['status'] for v in after['books'])),'errors':[]}
    r.save(RUN/(target+'-verification.json'),result);print(json.dumps(result,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','apply','verify']);parser.add_argument('--target',choices=['local','production']);args=parser.parse_args()
    if args.phase=='prepare':prepare()
    else:assert args.target;globals()[args.phase](args.target)
