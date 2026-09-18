#!/usr/bin/env python3
"""Review source-recorded painter country affiliations without publication.

Exact museum authority IDs only; names are not used to infer nationality.
Historical/uncertain country labels are held. Birthplace and collection location
are never substituted for source-recorded artist affiliation.
"""
import argparse,collections,csv,importlib.util,json,subprocess,re
from pathlib import Path
spec=importlib.util.spec_from_file_location('creators',Path(__file__).with_name('reconcile-creators-followup.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ROOT=m.ROOT;RUN=ROOT/'docs/research/overnight-countries-20260913/country-review-museums';BASE=RUN.parent
BACKUPS=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/overnight-countries-20260913')
ACTOR='local-european-research';FIELD='museum_country_review_20260913'
COUNTRIES={'American':'US','French':'FR','British':'GB','English':'GB','Scottish':'GB','Welsh':'GB','Italian':'IT','German':'DE','Dutch':'NL','Swiss':'CH','Austrian':'AT','Czech':'CZ','Spanish':'ES','Russian':'RU','Japanese':'JP','Belgian':'BE','Polish':'PL','Swedish':'SE','Canadian':'CA','Mexican':'MX','Irish':'IE','Hungarian':'HU','Australian':'AU','Danish':'DK','Argentinean':'AR','Argentine':'AR','Chinese':'CN','Cuban':'CU','Greek':'GR','Brazilian':'BR','Israeli':'IL','Norwegian':'NO','Romanian':'RO','Portuguese':'PT','Chilean':'CL','Indian':'IN','Venezuelan':'VE','Peruvian':'PE','Ukrainian':'UA','Turkish':'TR','Finnish':'FI','Colombian':'CO','Croatian':'HR','Slovenian':'SI','Serbian':'RS','Iranian':'IR','Icelandic':'IS','Bulgarian':'BG','Latvian':'LV','Lithuanian':'LT','Estonian':'EE','Georgian':'GE','Belarusian':'BY','Slovak':'SK','Indonesian':'ID','Algerian':'DZ','Uruguayan':'UY','New Zealander':'NZ'}
SOURCES=[('nga-constituent','content/imports/nga-catalogue-20260909/constituents.csv','constituentid','nationality','preferreddisplayname','beginyear','endyear'),('moma-person','content/imports/expanded-round2-20260913/moma-Artists.csv','ConstituentID','Nationality','DisplayName','BeginDate','EndDate')]

def nga_display_context(raw):
    """A flat nationality must not silently override a conflicting biography."""
    prefix=raw.get('displaydate','').split(',')[0].strip()
    explicit={code for word,code in COUNTRIES.items() if re.search(r'\b'+re.escape(word)+r'\b',prefix)}
    uncertain=bool(explicit and re.search(r'\?|\b(?:probably|possibly|or)\b',prefix,re.I))
    code=COUNTRIES.get(raw.get('nationality',''))
    return dict(display_prefix=prefix,explicit_codes=sorted(explicit),requires_review=uncertain or bool(explicit and explicit!={code}))

def save(name,data):m.r.core.save_new(RUN/name,data)
def read(name):return json.loads((RUN/name).read_text())
def museum_rows():
    result={};receipts={}
    for scheme,filename,key,nat,name,birth,death in SOURCES:
        path=ROOT/filename;raw=path.read_bytes();receipt=json.loads(path.with_suffix(path.suffix+'.snapshot.json').read_text());assert m.r.core.sha(raw)==receipt['sha256']
        with path.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        assert len({r[key] for r in rows})==len(rows)
        result[scheme]={r[key]:{'id':r[key],'name':r[name],'nationality':r[nat],'birth':int(r[birth]) if (r.get(birth) or '').lstrip('-').isdigit() and int(r[birth]) else None,'death':int(r[death]) if (r.get(death) or '').lstrip('-').isdigit() and int(r[death]) else None,'raw':r} for r in rows}
        receipts[scheme]={'path':filename,**receipt}
    return result,receipts

def plan():
    assert not (RUN/'plan.json').exists()
    artists=json.loads((BASE/'local-artists-baseline.json').read_text());configured={r['code'] for r in json.loads((BASE/'countries.json').read_text())};registries,receipts=museum_rows()
    entries=[];holds=[];reviewed=0
    for rec in artists:
        a=rec['row']
        if a['status']!='review' or a['entity_type']!='person' or not rec['artwork_count']:continue
        found=[];identity_conflict=False
        for ident in rec['authorities']:
            scheme=ident['scheme'];r=registries.get(scheme,{}).get(ident['id'])
            if not r:continue
            reviewed+=1;label=r['nationality'];code=COUNTRIES.get(label)
            if not label:continue
            reason=None
            if not code:reason='historical_ambiguous_or_unmapped_nationality'
            elif code not in configured:reason='country_not_yet_in_configured_taxonomy'
            elif any(r[k] is not None and a[k+'_year'] is not None and r[k]!=a[k+'_year'] for k in ('birth','death')):reason='source_person_biography_conflict'
            elif scheme=='nga-constituent' and nga_display_context(r['raw'])['requires_review']:reason='museum_nationality_display_biography_disagreement'
            if reason:
                if reason=='source_person_biography_conflict':identity_conflict=True
                holds.append({'slug':a['slug'],'scheme':scheme,'source_id':r['id'],'nationality':label,'reason':reason});continue
            url='https://www.nga.gov/artists/'+r['id'] if scheme=='nga-constituent' else 'https://www.moma.org/artists/'+r['id']
            found.append({'country_code':code,'source_scheme':scheme,'person_id':r['id'],'source_name':r['name'],'literal_nationality':label,'source_url':url,'source_record':r['raw'],'source_receipt':receipts[scheme]})
        if not found or identity_conflict:continue
        codes={x['country_code'] for x in found}
        # Disagreement may describe a legitimate migration or multiple national
        # affiliations, but it needs historical context before classification.
        if len(codes)>1:
            holds.append({'slug':a['slug'],'nationalities':[x['literal_nationality'] for x in found],'reason':'museum_sources_disagree_requires_country_context'});continue
        code=next(iter(codes));existing={c['country_code'] for c in rec['countries'] if c['relationship_type']=='cultural_affiliation'}
        if existing and code not in existing:
            holds.append({'slug':a['slug'],'existing_affiliations':sorted(existing),'proposed_country':code,'reason':'existing_cultural_affiliation_requires_crosscheck'});continue
        additions=[] if code in existing else [code]
        entries.append({'artist':a,'before_countries':rec['countries'],'authorities':rec['authorities'],'country_code':code,'additions':additions,'evidence':found,'operation':'verify_country_affiliation_preserve_review'})
    save('plan.json',entries);save('holds.json',holds)
    manifest={'at':m.r.core.now(),'sha256':m.r.core.sha((RUN/'plan.json').read_bytes()),'painters_reviewed':len(entries),'source_person_records_inspected':reviewed,'country_relationships_to_add':sum(len(e['additions']) for e in entries),'countries':dict(collections.Counter(e['country_code'] for e in entries)),'held_reasons':dict(collections.Counter(h['reason'] for h in holds)),'sources':receipts}
    save('manifest.json',manifest);print(json.dumps({k:v for k,v in manifest.items() if k!='sources'},indent=2),flush=True)

def load_plan():
    raw=(RUN/'plan.json').read_bytes();manifest=read('manifest.json');assert m.r.core.sha(raw)==manifest['sha256'];return manifest,json.loads(raw)

def selected(db,entries,lock=False):
    rows=db.execute("""SELECT to_jsonb(a) row,coalesce((SELECT jsonb_agg(to_jsonb(c) ORDER BY country_code,relationship_type) FROM artist_countries c WHERE c.artist_id=a.id),'[]') countries,
    coalesce((SELECT jsonb_agg(jsonb_build_object('scheme',scheme,'id',external_id) ORDER BY scheme,external_id) FROM external_identifiers WHERE entity_type='artist' AND entity_id=a.id),'[]') authorities
    FROM artists a WHERE slug=ANY(%s)"""+(' FOR UPDATE OF a' if lock else ''),([e['artist']['slug'] for e in entries],)).fetchall()
    assert len(rows)==len(entries);return {r['row']['slug']:r for r in rows}

def guard(entries,rows):
    for e in entries:
        now=rows[e['artist']['slug']]
        for key in ('display_name','normalized_name','birth_year','death_year','status','entity_type'):
            assert now['row'][key]==e['artist'][key],(key,e['artist']['slug'])
        expected=[{k:v for k,v in c.items() if k!='artist_id'} for c in e['before_countries']]
        actual=[{k:v for k,v in c.items() if k!='artist_id'} for c in now['countries']]
        assert actual==expected,('Country evidence changed',e['artist']['slug'])
        assert now['authorities']==e['authorities'],('Authority identity changed',e['artist']['slug'])
        assert now['row']['published_at'] is None

def preflight(target):
    manifest,entries=load_plan();rows={}
    with m.r.base.connect(target=='production') as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');db.execute("SET LOCAL statement_timeout='120s'")
        for start in range(0,len(entries),100):
            batch=entries[start:start+100];got=selected(db,batch);guard(batch,got);rows.update(got)
        assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND field_name=%s LIMIT 1",(FIELD,)).fetchone()
        counts=db.execute("SELECT (SELECT count(*) FROM artists) artists,(SELECT count(*) FROM artworks) artworks,(SELECT count(*) FROM artist_countries) country_relations,(SELECT count(*) FROM artists a WHERE status='review' AND NOT EXISTS(SELECT 1 FROM artist_countries c WHERE c.artist_id=a.id)) review_without_country").fetchone()
    BACKUPS.mkdir(parents=True,exist_ok=True);path=BACKUPS/('country-'+target+'-preimages.json')
    m.r.core.save_new(path,{'at':m.r.core.now(),'plan_sha256':manifest['sha256'],'rows':rows,'counts':counts})
    save(target+'-preflight.json',{'at':m.r.core.now(),'plan_sha256':manifest['sha256'],'rows':len(rows),'counts':counts,'preimages_sha256':m.r.core.sha(path.read_bytes())});print(target,'country preflight',len(rows),flush=True)

def backup_local():
    access=m.module('access','/tmp/artline-deploy-20260912/database_migration.py');BACKUPS.mkdir(parents=True,exist_ok=True);path=BACKUPS/'local-before.dump';assert not path.exists()
    subprocess.run(['pg_dump','--format=custom','--no-owner','--no-acl','--file',str(path)],env=access.environment(False),check=True)
    listed=subprocess.check_output(['pg_restore','--list',str(path)])
    m.r.core.save_new(BACKUPS/'local-backup-receipt.json',{'at':m.r.core.now(),'path':str(path),'bytes':path.stat().st_size,'sha256':m.r.core.sha(path.read_bytes()),'archive_entries':len(listed.splitlines())});print('Overnight local full backup verified',flush=True)

def apply(target):
    manifest,entries=load_plan()
    assert (BACKUPS/'local-backup-receipt.json').exists();assert json.loads((BACKUPS/'production-managed-backup.json').read_text())['status']=='SUCCESSFUL'
    for name in ('local','production'):assert read(name+'-preflight.json')['plan_sha256']==manifest['sha256']
    with m.r.base.connect(target=='production') as db:
        for start in range(0,len(entries),100):
            path=RUN/'applied'/target/f'{start//100+1:03d}.json'
            if path.exists():continue
            batch=entries[start:start+100];outcomes=[]
            with db.transaction():
                db.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE');db.execute("SET LOCAL statement_timeout='90s'");db.execute("SET LOCAL lock_timeout='10s'")
                db.execute('SELECT pg_advisory_xact_lock(2026090959)');db.execute('SELECT pg_advisory_xact_lock(559220260914)')
                rows=selected(db,batch,True);guard(batch,rows)
                db.execute("INSERT INTO sources(slug,name,source_type,base_url) VALUES('overnight-country-review-20260913','Museum authority country review','authority_data','https://www.nga.gov/') ON CONFLICT(slug) DO NOTHING")
                sid=db.execute("SELECT id FROM sources WHERE slug='overnight-country-review-20260913'").fetchone()['id']
                assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND field_name=%s AND entity_id=ANY(%s::uuid[]) LIMIT 1",(FIELD,[r['row']['id'] for r in rows.values()])).fetchone(),'Committed batch without receipt needs recovery inspection'
                with db.pipeline():
                    for e in batch:
                        row=rows[e['artist']['slug']]['row'];ev=e['evidence'][0]
                        for code in e['additions']:
                            note=f"{ev['source_scheme']} source records nationality '{ev['literal_nationality']}'. Exact source person ID {ev['person_id']}. Country mapped as cultural affiliation; not museum location, birthplace or an exclusive citizenship claim. Review retained."
                            db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,%s,'cultural_affiliation',false,%s)",(row['id'],code,note))
                        db.execute('UPDATE artists SET revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(ACTOR,row['id']))
                        m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=row['id'],field_name=FIELD,source_id=sid,source_record_id=ev['source_scheme']+':'+ev['person_id'],source_url=ev['source_receipt']['url'],evidence_note=json.dumps({'plan_sha256':manifest['sha256'],'country_code':e['country_code'],'evidence':e['evidence'],'review':'Country affiliation corroborated. Overall record remains in review.'},ensure_ascii=False,sort_keys=True),retrieved_at=ev['source_receipt']['retrieved_at'],created_by=ACTOR))
                        outcomes.append({'artist_id':row['id'],'slug':row['slug'],'country_code':e['country_code'],'added':e['additions']})
            m.r.core.save_new(path,{'at':m.r.core.now(),'plan_sha256':manifest['sha256'],'outcomes':outcomes});print(target,'country batch',start//100+1,len(batch),flush=True)

def verify(target):
    manifest,entries=load_plan();before=json.loads((BACKUPS/('country-'+target+'-preimages.json')).read_text());checked=[]
    with m.r.base.connect(target=='production') as db,db.transaction():
        db.execute('SET TRANSACTION READ ONLY')
        for start in range(0,len(entries),100):
            batch=entries[start:start+100];rows=selected(db,batch)
            cites=db.execute("SELECT entity_id::text,evidence_note FROM citations WHERE entity_type='artist' AND field_name=%s AND entity_id=ANY(%s::uuid[])",(FIELD,[r['row']['id'] for r in rows.values()])).fetchall();assert len(cites)==len(batch);cites={c['entity_id']:json.loads(c['evidence_note']) for c in cites}
            for e in batch:
                slug=e['artist']['slug'];now=rows[slug];old=before['rows'][slug];ignored={'revision','updated_at','updated_by'}
                assert {k:v for k,v in now['row'].items() if k not in ignored}=={k:v for k,v in old['row'].items() if k not in ignored},slug
                assert now['row']['revision']==old['row']['revision']+1 and now['row']['status']=='review'
                assert now['authorities']==old['authorities']
                expected={(c['country_code'],c['relationship_type']) for c in old['countries']}|{(code,'cultural_affiliation') for code in e['additions']}
                assert {(c['country_code'],c['relationship_type']) for c in now['countries']}==expected
                assert all(c in now['countries'] for c in old['countries'])
                assert cites[now['row']['id']]['plan_sha256']==manifest['sha256'] and cites[now['row']['id']]['evidence']==e['evidence']
                checked.append({'slug':slug,'country_code':e['country_code'],'added':e['additions']})
        counts=db.execute("SELECT (SELECT count(*) FROM artists) artists,(SELECT count(*) FROM artworks) artworks,(SELECT count(*) FROM artist_countries) country_relations,(SELECT count(*) FROM artists a WHERE status='review' AND NOT EXISTS(SELECT 1 FROM artist_countries c WHERE c.artist_id=a.id)) review_without_country").fetchone()
    assert counts['artists']==before['counts']['artists'] and counts['artworks']==before['counts']['artworks']
    assert counts['country_relations']==before['counts']['country_relations']+manifest['country_relationships_to_add']
    save(target+'-verification.json',{'at':m.r.core.now(),'plan_sha256':manifest['sha256'],'rows':checked,'counts':counts,'metadata_and_review_status_preserved':True});print(target,'countries verified',len(checked),'remaining without country',counts['review_without_country'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','backup-local','preflight','apply','verify']);p.add_argument('--target',choices=['local','production']);arg=p.parse_args()
    if arg.command=='plan':plan()
    elif arg.command=='backup-local':backup_local()
    else:globals()[arg.command](arg.target)
