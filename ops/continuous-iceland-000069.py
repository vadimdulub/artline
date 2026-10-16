#!/usr/bin/env python3
"""One bounded Iceland factual-metadata batch using established production ingestion."""
import csv, fcntl, gzip, importlib.util, inspect, json, os, re, subprocess, sys
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
def mod(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'ops'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=mod('base69','continuous-image-batch-000002.py')
h=mod('metadata69','india-300-delivery-20261011.py')
E=ROOT/'docs/research/continuous-production-20261011/batches/000069'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000069'
S=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000069'
OP='continuous-iceland-20261011-b000069';PHASE='iceland-paintings'
FIELD='continuous_iceland_object_evidence_b000069'
MUSEUM='National Gallery of Iceland';SLUG='national-gallery-of-iceland'
SCHEME='museum-native-listasafn-is';KEYS=['li-4863','li-1383','li-350','li-791']
h.OP=OP;h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
h.SCHEMES={'iceland':[SCHEME,'sarpur-object']}
h.museums=lambda:{MUSEUM:(SLUG,'https://www.listasafn.is/en/')}
MID=h.uid('museum/'+SLUG);NEW_ARTIST=h.uid('artist/sarpur-56534')
for p in [E,R,S,h.BACKUP]:p.mkdir(parents=True,exist_ok=True)
def save(name,value):
    p=E/name
    if p.exists():return h.load(p)
    h.save(p,value);return value
def target(write=False):
    assert os.environ.get('ARTLINE_SWISS_INDIA_PROXY_PORT','55519')=='55519'
    actual=subprocess.check_output(['gcloud','sql','instances','describe','artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=value(connectionName)'],text=True).strip()
    assert actual=='artline-508319:europe-west1:artline-postgres'
    return dict(base.target(write),connection_name=actual,helper='ops/india-300-delivery-20261011.py',local_catalogue_connections=0)
def object_data(key,english=False):
    rc=h.load(E/(key+('-english' if english else '')+'-capture.json'))
    raw=Path(rc['body_path']).read_bytes();assert rc['status']==200 and h.sha(raw)==rc['sha256']
    o=json.loads(BeautifulSoup(raw,'html.parser').select_one('#__NEXT_DATA__').string)['props']['pageProps']['content']
    assert o['meta']['uid']==key and o['sarpur']['slug']==key
    return o,rc
def fold(v):return h.norm(v).replace('ð','d').replace('þ','th')

def identity(db,rows,include_oeuvre=True):
    result=[]
    for r in rows:
        acc=r['accession_number'];forms=[acc,acc.replace('-',' '),acc.replace('-',''),acc.replace('Í','I'),acc.replace('Í','I').replace('-',' ')]
        urls=[r['source_url'],r['english_source_url']]
        native=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme=ANY(%s) AND external_id=ANY(%s)))",(urls,h.SCHEMES['iceland'],[r['source_id'],r['raw']['sarpur_object_id']]))]
        exact=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE accession_number=ANY(%s)',(forms,))]
        cit=[dict(x) for x in db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,))]
        titles=[dict(x) for x in db.execute('SELECT a.id::text,a.title,a.accession_number,a.unlinked_creator_label FROM artworks a WHERE a.normalized_title=ANY(%s) AND (EXISTS (SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id AND aa.artist_id=%s) OR a.unlinked_creator_label IS NOT NULL)',([h.norm(r['title']),h.norm(r['raw']['original_title'])],r['verified_artist_id']))]
        conflicts=[x for x in titles if not x['unlinked_creator_label'] or fold(x['unlinked_creator_label'])==fold(r['creator_label'])]
        assert not(native or exact or cit or conflicts),('Object collision',r['source_id'])
        result.append(dict(source_id=r['source_id'],native=native,global_accessions=exact,global_citations=cit,title_candidates=titles,conflicts=conflicts,decision='No exact object identity found'))
    return result

def no_collision(db,rows):
    identity(db,rows,False)
    assert not db.execute('SELECT id FROM institutions WHERE id=%s OR slug=%s OR website_url LIKE %s',(MID,SLUG,'%listasafn.is%')).fetchall()
    assert not db.execute("SELECT id FROM artists WHERE id=%s OR display_name ILIKE '%%kristj%%' OR normalized_name=ANY(%s)",(NEW_ARTIST,[h.norm('Kristján Davíðsson'),h.norm('Kristjan Davidsson')])).fetchall()
    assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artist' AND ((scheme='sarpur-artist' AND external_id='56534') OR external_id='500121993')").fetchall()
h.no_collision=no_collision

def new_artist():
    return dict(id=NEW_ARTIST,slug='kristjan-davidsson-b000069',display_name='Kristján Davíðsson',sort_name='Kristján Davíðsson',normalized_name=h.norm('Kristján Davíðsson'),birth_year=1917,death_year=2013,birth_display='1917',death_display='2013',birth_precision='exact',death_precision='exact',active_start_year=1946,active_end_year=1946,timeline_start_year=1946,timeline_end_year=1946,timeline_display='Documented selected work: 1946',timeline_basis='activity',status='review',created_by=h.ACTOR,updated_by=h.ACTOR)
h.NEW_ARTISTS=[new_artist()]
code=inspect.getsource(h.plan).replace('User: go ahead with India, add at least 300 artworks; broad museum coverage first. Minimum counts only new, distinct artwork records.','User authorized bounded continuous production batch 69: source-backed Iceland paintings and globally reconciled creator; new rows remain review.')
code=code.replace('artists=artists,existing_scope','artists=artists,new_artists=NEW_ARTISTS,existing_scope')
exec(compile(code,__file__,'exec'),h.__dict__)

def add_creator_evidence(db,p,digest):
    r=next(x for x in p['records'] if x['artist_id']==NEW_ARTIST);sid=h.uid('source/iceland/'+MUSEUM)
    evidence=dict(plan_sha256=digest,source_sha256=r['evidence']['sha256'],name=r['creator_label'],birth_year=1917,death_year=2013,native_artist_id='56534',global_reconciliation='All production names and aliases normalized including eth/thorn transliterations; no matching name, alias or ULAN 500121993 identity. See creator-global-reconciliation.json.',timeline_basis='Only selected documented work year 1946; not an inferred career span.',user_authorization='Continuous source-backed production enrichment',authority_source_capture=h.load(E/'creator-authority-capture.json'))
    h.batch_insert(db,'citations',[dict(id=h.uid('artist-citation/56534'),entity_type='artist',entity_id=NEW_ARTIST,field_name='continuous_iceland_creator_evidence_b000069',source_id=sid,source_record_id='56534',source_url=r['source_url'],evidence_note=json.dumps(evidence,ensure_ascii=False),retrieved_at=r['evidence']['retrieved_at'],created_by=h.ACTOR)])
    h.batch_insert(db,'external_identifiers',[dict(id=h.uid('artist-id/56534'),entity_type='artist',entity_id=NEW_ARTIST,scheme='sarpur-artist',external_id='56534',canonical_url=r['source_url'],source_id=sid,retrieved_at=r['evidence']['retrieved_at'])])
h.add_creator_evidence=add_creator_evidence
code=inspect.getsource(h.apply).replace("assert sum(not r['before'] for r in rows)>=300,'Minimum target must count new physical objects, not enrichments'","assert 1<=len(rows)<=50 and all(not r['before'] for r in rows)")
code=code.replace('india_minimum_300_museum_coverage_20261011',FIELD)
code=code.replace("load(RUN/'cloud-sql-backup.json')['status']=='SUCCESSFUL'","load(RUN/'local-recovery-verification.json')['status']=='VERIFIED'")
code=code.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  no_collision(db,rows)\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
code=code.replace('locked=dict(plan_sha256=digest,artworks=before,institutions=actual,artists=actualartists)','locked=dict(plan_sha256=digest,artworks=before,institutions=actual,artists=actualartists,new_artist_preimages=[],new_institution_preimages=[])')
code=code.replace("  batch_insert(db,'institutions',p['new_institutions'])","  batch_insert(db,'artists',p['new_artists'])\n  batch_insert(db,'institutions',p['new_institutions'])")
code=code.replace("  existing_keys={(e['scheme']", "  add_creator_evidence(db,p,digest)\n  existing_keys={(e['scheme']")
exec(compile(code,__file__,'exec'),h.__dict__)

def stage():
    if (E/PHASE/'plan-pin.json').exists():return
    save('production-target-before-plan.json',target())
    rows=[];creators=[];oeuvres={}
    with h.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        names=db.execute("SELECT id::text,display_name name,birth_year,death_year FROM artists WHERE status<>'archived' UNION SELECT a.id::text,al.alias name,a.birth_year,a.death_year FROM artists a JOIN artist_aliases al ON al.artist_id=a.id WHERE a.status<>'archived'").fetchall()
        inst=[x['v'] for x in db.execute('SELECT to_jsonb(i) v FROM institutions i')]
        matches=[x for x in inst if any(t in fold(x['name']) for t in ['iceland','islands','reykjav','listasafn']) or 'listasafn.is' in (x['website_url'] or '') or x['slug']==SLUG]
        assert not matches;save('institution-global-reconciliation.json',dict(at=h.now(),reviewed_institutions=len(inst),name_host_slug_matches=matches,new_id=MID,scope='Museum only created together with four verified collection objects.'))
        for key in KEYS:
            o,rc=object_data(key);en,erc=object_data(key,True);s=o['sarpur'];a=s['artists'][0]
            assert len(s['artists'])==1 and s['name']==o['title'] and s['objectID']==en['sarpur']['objectID']
            assert 'Málaralist / Olíumálverk' in s['category'] and re.fullmatch(r'\d{4}( - \d{4})?',s['year'])
            yrs=list(map(int,re.findall(r'\d{4}',s['year'])));assert max(yrs)<=1970
            exact={x['id']:x for x in names if fold(x['name'])==fold(a['name'])}
            variants={x['id']:x for x in names if (fold(a['name']).split()[-1] in fold(x['name']).split()) and x['birth_year']==a['birthYear'] and x['death_year']==a['deathYear']}
            candidate=exact or variants
            if key=='li-791':
                assert not candidate and not any('kristj' in fold(x['name']) or 'davidsson' in fold(x['name']) for x in names);aid=NEW_ARTIST
                assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artist' AND external_id='500121993'").fetchall()
            else:assert len(candidate)==1;aid=next(iter(candidate))
            creators.append(dict(source=a,matches=candidate,selected_artist_id=aid,action='new_review' if aid==NEW_ARTIST else 'existing',basis='Exact name/alias or surname with both life years; existing catalogue preserved.'))
            works=[x['v'] for x in db.execute('SELECT DISTINCT to_jsonb(a) v FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s ORDER BY v LIMIT 500',(aid,))];assert len(works)<500
            oeuvres[aid]=works
            factual={k:v for k,v in s.items() if k not in ['exhibitionText','description']}
            factual.update(original_title=en['title'] if en['title']!=o['title'] else None,sarpur_object_id=s['objectID'],source_image_reference=o['image'],source_image_downloaded=False)
            rows.append(dict(provider='iceland',source_id=key,source_url=rc['url'],english_source_url=erc['url'],museum=MUSEUM,title=o['title'],creator_label=a['name'],verified_artist_id=aid,date_display=s['year'],year_start=min(yrs),year_end=max(yrs),date_decision='eligible',accession_number=s['listasafnidId'],source_type='painting',medium='; '.join(s['material']),dimensions=s['size'],credit=s['donorComments'],raw=factual,evidence=rc,evidence_file=rc['body_path'],english_evidence=erc,identity_review='Exact official collection accession and Sarpur ID, creator, date and dimensions. Museum narrative retained only in private source capture; factual fields alone imported. No loan or current-display claim. Source 0-depth values remain verbatim dimension text, not inferred physical measurements.',creator_reconciliation=creators[-1],image_hold='Official terms section 5 requires permission; no source-specific Iceland extension or open image licence. No exact approved WikiArt alternative found. No image downloaded.'))
        checks=identity(db,rows)
        preserved=h.snapshot(db,[x['id'] for w in oeuvres.values() for x in w])
    save('creator-global-reconciliation.json',dict(at=h.now(),names_and_aliases_checked=len(names),records=creators,artworks_by_creator=oeuvres))
    save('global-identity-reconciliation.json',dict(at=h.now(),records=checks,review='All 17 works of the three existing creators inspected by title/date/dimensions/accession; distinct from selected works. The five Wegmann works are other portraits/beach scene; Kjarval works date 1926–1931; Nina works date 1950–1960.'))
    save('preserved-existing-before.json.gz',dict(artworks=preserved));h.save(h.BACKUP/'preserved-existing-before.json.gz',dict(artworks=preserved))
    h.save(E/PHASE/'source-records.json.gz',rows);h.plan(PHASE)
    p,pin=h.pinned(PHASE);assert len(p['records'])==4 and len(p['new_artists'])==1 and len(p['new_institutions'])==1 and len(p['artists'])==3
    save('prewrite-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=[dict(source_id=r['source_id'],source_sha256=r['evidence']['sha256'],english_sha256=r['english_evidence']['sha256'],title=r['title'],date=r['date_display'],inventory=r['accession_number'],creator=r['creator_label']) for r in p['records']],all_images_held=True))
    print('Pinned: 4 new paintings, 1 new review painter, 4 holdings; no image downloads')

def apply():
    p,pin=h.pinned(PHASE);ids=[r['artwork_id'] for r in p['records']]
    checked=target(True)
    with h.connect() as db:
        present=h.snapshot(db,ids)
        notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_type='artwork' AND field_name=%s AND entity_id=ANY(%s::uuid[])",(FIELD,ids)).fetchall()
        if present:
            assert len(present)==len(notes)==len(ids) and all(x['pin']==pin for x in notes)
            pre=h.load(h.BACKUP/PHASE/'locked-before.json.gz');assert pre['plan_sha256']==pin and pre['artworks']=={} and pre['new_artist_preimages']==[]
            note=db.execute("SELECT evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE entity_type='artist' AND entity_id=%s AND field_name='continuous_iceland_creator_evidence_b000069'",(NEW_ARTIST,)).fetchone();assert note['pin']==pin
            print('Own committed plan reconciled: no replay writes');return
    rc=h.load(E/'local-recovery-verification.json');assert rc['status']=='VERIFIED' and rc['plan_sha256']==pin
    for f in rc['files']:assert h.sha(Path(f['path']).read_bytes())==f['sha256']
    assert h.load(E/'prewrite-verification.json')['passed']
    save('production-target-before-metadata-write.json',checked);h.apply(PHASE)

if __name__=='__main__':
    with (R/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[sys.argv[1]]()
