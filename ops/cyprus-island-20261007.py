#!/usr/bin/env python3
"""Island-wide Cyprus museum research and production identity audit."""
import argparse,collections,concurrent.futures,gzip,importlib.util,json,re,subprocess
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('nicosia',Path(__file__).with_name('nicosia-museums-20261007.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
h,d=n.h,n.d
R=n.REPO/'docs/research/cyprus-island-expansion-20261007'
B=Path.home()/'Library/Application Support/Artline/backups'/R.name
n.ROOT=R;n.BACKUP=B;h.RUN=R;h.BACKUP=B
SEEDS={
 'visitcyprus':'https://www.visitcyprus.com/discover-cyprus/culture/museums-galleries/',
 'antiquities':'https://www.culture.gov.cy/dmculture/da/da.nsf/DMLmuseums_en/DMLmuseums_en?OpenDocument=&print=',
 'north':'https://www.visitncy.com/discover/',
 'cvar':'https://cvar.severis.org/en/explore/collections-archives/paintings/?page=12',
 'makarios':'http://www.makariosfoundation.org.cy/',
 'dioptra':'https://dioptra.cyi.ac.cy/',
}
def page(url,key=None):
    path=R/'pages'/((key or h.sha(url.encode()))+'.json')
    if path.exists():return h.load(path)
    raw,rc=h.capture(url);soup=BeautifulSoup(raw,'html.parser')
    for t in soup(['script','style','noscript']):t.decompose()
    v=dict(url=url,receipt=rc,title=soup.title.get_text(' ',strip=True)if soup.title else None,text=soup.get_text('\n',strip=True),links=[dict(url=urljoin(url,a['href']),text=a.get_text(' ',strip=True))for a in soup.select('a[href]')])
    h.save(path,v);return v
def discovery():
    def one(item):
        key,url=item
        try:
            p=page(url,key);print(key,p['receipt']['status'],len(p['links']),'links',flush=True)
        except Exception as e:print(key,type(e).__name__,str(e),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:list(pool.map(one,SEEDS.items()))
def baseline():
    with d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        assert db.execute('SELECT current_database()name').fetchone()['name']=='artline'
        institutions=[x['v']for x in db.execute('SELECT to_jsonb(i)v FROM institutions i ORDER BY id')]
        places=[x['v']for x in db.execute("SELECT to_jsonb(p)v FROM places p WHERE country_code='CY' ORDER BY id")]
        ids=[i['id']for i in institutions if i['place_id']in {p['id']for p in places}]
        counts=db.execute("""SELECT i.id::text,i.name,i.slug,p.name city,p.country_code,count(a.id)artworks,
          count(a.id)FILTER(WHERE artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible')eligible
          FROM institutions i LEFT JOIN places p ON p.id=i.place_id LEFT JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived'
          WHERE i.id=ANY(%s::uuid[]) GROUP BY i.id,p.id ORDER BY i.name""",(ids,)).fetchall()
        schema=db.execute("SELECT table_name,column_name,data_type,is_nullable,column_default FROM information_schema.columns WHERE table_schema='public'AND table_name=ANY(%s) ORDER BY table_name,ordinal_position",(['places','institutions'],)).fetchall()
        constraints=db.execute("SELECT conrelid::regclass::text table_name,conname,pg_get_constraintdef(oid)definition FROM pg_constraint WHERE conrelid IN ('places'::regclass,'institutions'::regclass)ORDER BY conrelid,conname").fetchall()
    value=dict(at=h.now(),target='production',institutions=institutions,cyprus_places=places,cyprus_counts=counts,schema=schema,constraints=constraints,target_minimum=500,target_upper=1000)
    h.save(R/'production-baseline.json.gz',value)
    print('Production baseline',len(institutions),'institutions;',len(places),'Cyprus places;',len(counts),'Cyprus institutions',flush=True)
    for row in counts:print(row['name'],row['city'],row['artworks'],flush=True)
def backup():
    data=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791368721734','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True))
    assert data['status']=='SUCCESSFUL'and data['instance']=='artline-postgres'
    h.save(R/'production-backup.json',dict(at=h.now(),production=data,note='Existing full-instance recovery backup, freshly confirmed; transaction-specific preimages required before every write.'))
    print('Verified backup',data['id'],data['status'],flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['discovery','baseline','backup']);a=p.parse_args();globals()[a.phase]()
