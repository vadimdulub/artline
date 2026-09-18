#!/usr/bin/env python3
"""Pinned Spanish catalogue delivery with backups, identity guards and review state."""
import argparse, base64, collections, csv, hashlib, importlib.util, json, re, subprocess, uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse
import psycopg, requests
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('research',ROOT/'ops/research-spain-deep.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
w=r.w;core=r.core;RUN=r.RUN
BACKUP=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/spain-deep-20260916')
SOURCE='spain-deep-research-20260916';ACTOR=core.ACTOR
SITE='https://artline-web-lpuqqlugnq-ew.a.run.app'
def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/spain-deep/'+key))
def host(url):return (urlparse(url or '').hostname or '').removeprefix('www.')
def acc(x):return re.sub(r'\d+',lambda z:str(int(z[0])),re.sub(r'[^A-Z0-9]','',(x or '').upper()))
def connect(target,ro=True):return psycopg.connect('postgresql://localhost/artline' if target=='local' else core.cloud_dsn(),autocommit=True,row_factory=dict_row,options='-c statement_timeout=120000 -c timezone=UTC'+(' -c default_transaction_read_only=on' if ro else ''))
def insert(db,table,data):return w.base.insert(db,table,data)
def primary(x):
    path=RUN/'primary-records'/(x['qid']+'.json')
    if not path.exists():return []
    # Retain captured primary pages as citations. Acceptance requires explicit
    # technical metadata validation in a separate review manifest.
    return [{k:v for k,v in p.items() if k!='text'} for p in json.loads(path.read_text())['captures']]

def plan():
    data=r.load('selected-metadata-final-v2.json');records=data['records'];museums=r.load('museum-authorities.json')['entities'];plans={}
    activities=r.load('spanish-activity-evidence.json')
    primary_review=r.load('primary-validation.json') if (RUN/'primary-validation.json').exists() else {}
    accepted=primary_review.get('records',{})
    primary_conflicts={v['qid']:v for v in primary_review.get('held',[]) if v.get('inventory_match') and v.get('title_match') and v.get('parsed',{}).get('creators') and not v.get('creator_match')}
    for target in ('local','production'):
        with connect(target) as db:
            artists=db.execute("SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,a.status,ARRAY(SELECT external_id FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata') qids, ARRAY(SELECT alias FROM artist_aliases x WHERE x.artist_id=a.id) aliases FROM artists a").fetchall()
            inst=db.execute("SELECT i.id::text,i.slug,i.name,i.website_url,i.wikidata_id,i.status,i.place_id::text,ARRAY(SELECT external_id FROM external_identifiers e WHERE e.entity_type='institution' AND e.entity_id=i.id AND e.scheme='wikidata') qids FROM institutions i").fetchall()
            artistplans={};instplans={};held=[]
            for x in records:
                q=x['creator_qid']
                if q in artistplans:continue
                exact=[a for a in artists if q in a['qids']];names={w.norm(t) for t in x['creator_names']}
                same=[a for a in artists if w.norm(a['display_name']) in names or names&{w.norm(t) for t in a['aliases']}]
                compatible=[a for a in same if not a['qids'] and a['status']!='archived' and ((a['birth_year']==x['birth'] and a['death_year']==x['death'] and x['birth'] is not None and x['death'] is not None) or w.norm(a['display_name'])==w.norm(x['creator_name']) and (not a['birth_year'] or not x['birth'] or a['birth_year']==x['birth']) and (not a['death_year'] or not x['death'] or a['death_year']==x['death']))]
                old=exact[0] if len(exact)==1 else compatible[0] if not exact and len(compatible)==1 else None
                # Conflicting short aliases do not make two separately sourced,
                # distinct full names/lifespans the same person.
                conflict=(len(exact)>1 or old and old['status']=='archived' or not old and any(w.norm(a['display_name'])==w.norm(x['creator_name']) for a in same))
                b,d=x['birth'],x['death'];basis='life' if b is not None and d is not None and b<=d else 'activity'
                dated=[v['date'] for v in records if v['creator_qid']==q and v['date']['eligible'] and v['date']['first'] is not None]
                first,last=(b,d) if basis=='life' else (min(v['first'] for v in dated),max(v['last'] for v in dated)) if dated else (None,None)
                description=x['creator_entity'].get('descriptions',{}).get('en',{}).get('value','')
                countries=[]
                if 'Q29' in x['creator_countries']:countries.append({'code':'ES','relationship':'cultural_affiliation','basis':'Explicit source P27 Spain association retained as cultural context; no modern legal citizenship asserted.'})
                elif re.search(r'\b(?:Spanish|Catalan|Valencian|Basque) (?:[\w-]+ ){0,4}(?:painter|artist)\b',description,re.I):countries.append({'code':'ES','relationship':'cultural_affiliation','basis':'Source authority describes: '+description+'. Regional cultural context; no modern citizenship inference.'})
                if q in activities:countries.append({'code':'ES','relationship':'active','basis':activities[q]['basis']+' Places: '+', '.join(z['name']+' ('+z['qid']+')' for z in activities[q]['locations'])})
                artistplans[q]={'qid':q,'id':old['id'] if old else uid('artist/'+q),'slug':old['slug'] if old else 'spain-painter-'+q.lower(),'name':old['display_name'] if old else x['creator_name'],'new':not bool(old),'preimage':old,'birth':b,'death':d,'first':first,'last':last,'basis':basis,'unlinked':bool(conflict or first is None or last is None),'countries':countries,'woman':x['creator_gender']==['Q6581072'],'receipt':x['creator_receipt'],'entity':x['creator_entity']}
            for x in records:
                q=x['institution_qid']
                if q in instplans:continue
                e=museums[q];exact=[i for i in inst if i['wikidata_id']==q or q in i['qids'] or w.MAPPING.get(i['slug'])==q]
                urls=set(host(s) for s in x['institution_websites']);names={w.norm(s) for s in w.labels(e)}
                same=[i for i in inst if w.norm(i['name']) in names or host(i['website_url']) in urls and host(i['website_url']) not in {'','cultura.gob.es','museosdeandalucia.es','museums.gov.il','gouv.fr'}]
                old=exact[0] if len(exact)==1 else same[0] if not exact and len(same)==1 else None
                if len(exact)>1 or not exact and len(same)>1:
                    instplans[q]={'qid':q,'id':None,'reason':'Ambiguous institution identity'};continue
                if old and old['status']=='archived':instplans[q]={'qid':q,'id':None,'reason':'Archived institution preserved'};continue
                # Unmapped non-museum collections remain provenance labels.
                new_ok=bool(urls-{''}) and bool(re.search(r'\b(?:museum|museo|museu|musée|gallery|galerie|galería|museen|pinacoteca|pinakothek)\b',w.label(e),re.I))
                if not old and not new_ok:instplans[q]={'qid':q,'id':None,'reason':'Institution type requires review'};continue
                instplans[q]={'qid':q,'id':old['id'] if old else uid('institution/'+q),'slug':old['slug'] if old else 'spain-research-museum-'+q.lower(),'name':old['name'] if old else x['institution_name'],'website_url':old['website_url'] if old else x['institution_websites'][0],'new':not bool(old),'preimage':old}
            artistids=[a['id'] for a in artistplans.values() if not a['new']];instids=[i['id'] for i in instplans.values() if i.get('id') and not i['new']]
            titlekeys=list({w.norm(s) for x in records for s in x['titles']});inventorykeys=list({s for x in records for s in x['accessions']})
            works=db.execute("""WITH selected AS MATERIALIZED (
              SELECT artwork_id id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])
              UNION SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s)
              UNION SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND (normalized_title=ANY(%s) OR accession_number=ANY(%s))
              UNION SELECT a.id FROM artwork_location_assertions la JOIN artworks a ON a.id=la.artwork_id WHERE la.institution_id=ANY(%s::uuid[]) AND la.superseded_by IS NULL AND (a.normalized_title=ANY(%s) OR a.accession_number=ANY(%s)))
              SELECT a.id::text,a.slug,a.title,a.alternate_title,a.accession_number,a.creation_year_start,a.creation_year_end,a.date_precision,a.status,a.revision,a.primary_media_id::text,a.current_institution_id::text,
              ARRAY(SELECT external_id FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata') qids,
              ARRAY(SELECT artist_id::text FROM artwork_artists WHERE artwork_id=a.id) artist_ids,
              ARRAY(SELECT source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id) source_urls,
              ARRAY(SELECT institution_id::text FROM artwork_location_assertions WHERE artwork_id=a.id AND claim_type='holding' AND superseded_by IS NULL) institution_ids
              FROM selected s JOIN artworks a ON a.id=s.id""",(artistids,[x['qid'] for x in records],instids,titlekeys,inventorykeys,instids,titlekeys,inventorykeys)).fetchall()
            states=[];claimed={}
            for x in records:
                q=x['qid'];ap=artistplans[x['creator_qid']];ip=instplans[x['institution_qid']];iid=ip.get('id');urls={u['url'] for u in x['object_urls']};names={w.norm(t) for t in x['titles']};accessions={acc(s) for s in x['accessions']}
                if q in primary_conflicts:
                    held.append({'qid':q,'reason':'Primary creator label requires manual reconciliation','primary':primary_conflicts[q]});continue
                if accepted.get(q,{}).get('source_years') and max(accepted[q]['source_years'])>1970:
                    held.append({'qid':q,'reason':'Primary creation date crosses or exceeds 1970; source conflict needs editorial review','primary':accepted[q]});continue
                exact=[a for a in works if q in a['qids']]
                peers=[a for a in works if iid and iid in [a['current_institution_id'],*a['institution_ids']]]
                byacc=[a for a in peers if a['accession_number'] and acc(a['accession_number']) in accessions]
                globaltitle=[a for a in works if ap['id'] in a['artist_ids'] and names&{w.norm(a['title']),w.norm(a['alternate_title'] or '')}]
                bytitle=[a for a in globaltitle if a in peers and (not a['accession_number'] or not accessions or acc(a['accession_number']) in accessions)]
                byurl=[a for a in works if urls&set(a['source_urls'])]
                found=exact or byurl or byacc or bytitle;reason=None
                if not found and globaltitle:reason='Same artist/title with different or unknown collection/inventory requires comparison'
                if len(found)>1:reason='Ambiguous existing physical object'
                old=found[0] if len(found)==1 else None
                if old and old['status']=='archived':reason='Archived object preserved'
                if old and old['qids'] and q not in old['qids']:reason='Different existing artwork authority'
                if old and old['artist_ids'] and ap['id'] not in old['artist_ids']:reason='Conflicting creator link'
                if old and old['id'] in claimed:reason='Two candidates resolve to one existing object'
                if reason:held.append({'qid':q,'reason':reason,'matches':[a['id'] for a in found]});continue
                if old:claimed[old['id']]=q
                states.append({'qid':q,'id':old['id'] if old else uid('artwork/'+q),'slug':old['slug'] if old else 'spain-artwork-'+q.lower(),'new':old is None,'preimage':old,'artist_qid':ap['qid'],'artist_id':None if ap['unlinked'] else ap['id'],'institution_qid':ip['qid'],'institution_id':iid,'primary_validation':x.get('native_primary_validation') or accepted.get(q),'primary_captures':primary(x)})
            # No two newly selected authorities may silently share an inventory.
            inventories=collections.defaultdict(list)
            for st in states:
                x=next(x for x in records if x['qid']==st['qid'])
                if st['new'] and st['institution_id'] and x['accession']:inventories[(st['institution_id'],acc(x['accession']))].append(st['qid'])
            collisions={q for qs in inventories.values() if len(qs)>1 for q in qs}
            states=[st for st in states if st['qid'] not in collisions];held.extend({'qid':q,'reason':'Selected authorities share institution accession'} for q in sorted(collisions))
            plans[target]={'states':states,'artists':artistplans,'institutions':instplans,'held':held}
            r.log('Plan',target,len(states),'works;',sum(st['new'] for st in states),'new;',len(held),'held')
    r.save('delivery-plan.json',{'at':core.now(),'metadata_sha256':core.sha((RUN/'selected-metadata-final-v2.json').read_bytes()),'targets':plans,'policy':'All new records review; holdings accepted only with separate primary validation. Existing descriptions, dates, creator links, images and publication status preserved.'})

def backup():
    BACKUP.mkdir(parents=True,exist_ok=True);dump=BACKUP/'local-before.dump'
    if not dump.exists():subprocess.run(['pg_dump','-h','127.0.0.1','-d','artline','-Fc','-f',str(dump)],check=True)
    subprocess.run(['pg_restore','--list',str(dump)],check=True,stdout=subprocess.DEVNULL)
    description='Before Spanish deep selected collection 20260916';rp=BACKUP/'cloud-backup-request.json'
    if not rp.exists():core.save_new(rp,subprocess.check_output(['gcloud','sql','backups','create','--instance=artline-postgres','--project=artline-508319','--description='+description,'--format=json']))
    backups=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--limit=50','--format=json']))
    cloud=next(x for x in backups if x.get('description')==description);assert cloud['status']=='SUCCESSFUL'
    if not (RUN/'backups.json').exists():r.save('backups.json',{'at':core.now(),'local':{'path':str(dump),'sha256':core.sha(dump.read_bytes()),'bytes':dump.stat().st_size},'production':cloud})
    plan=r.load('delivery-plan.json') if (RUN/'delivery-plan.json').exists() else {'targets':{}}
    for target,t in plan['targets'].items():
        if (BACKUP/(target+'-artwork-preimages.json')).exists():continue
        ids=[x['id'] for x in t['states'] if not x['new']]
        with connect(target) as db:preimages=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
        core.save_new(BACKUP/(target+'-artwork-preimages.json'),preimages)
    r.log('Recovery backups verified')

def refine_dates():
    path=RUN/'delivery-plan.json';original=RUN/'delivery-plan-before-primary-dates.json'
    if original.exists():assert r.load('delivery-plan.json').get('primary_date_refinement');return
    plan=r.load('delivery-plan.json');facts={x['qid']:x for x in r.load('selected-metadata-final-v2.json')['records']};changes=[]
    for target,t in plan['targets'].items():
        for st in t['states']:
            if not st['new'] or not st['primary_validation']:continue
            text=st['primary_validation'].get('source_date_display') or ''
            match=re.fullmatch(r'(?:(c\.|Cap a|Hacia|Circa)\s*)?(\d{4})(?:\s*[-–]\s*(\d{4}))?',text)
            if not match:continue
            first=int(match[2]);last=int(match[3] or match[2]);assert 1000<=first<=last<=1970
            precision=('circa_range' if match[3] else 'circa') if match[1] else ('range' if match[3] else 'exact')
            d={'first':first,'last':last,'precision':precision,'display':text,'eligible':True}
            source=facts[st['qid']]['date']
            if any(d[k]!=source[k] for k in ('first','last','precision')):
                st['applied_date']=d;changes.append({'target':target,'qid':st['qid'],'secondary_date_preserved':source,'applied_primary_date':d,'source':st['primary_validation']})
        for q,a in t['artists'].items():
            if not a['new'] or a['unlinked'] or a['basis']!='activity':continue
            dates=[st.get('applied_date',facts[st['qid']]['date']) for st in t['states'] if st['artist_qid']==q and st['artist_id']]
            dates=[d for d in dates if d['eligible'] and d['first'] is not None]
            if dates:a['first']=min(d['first'] for d in dates);a['last']=max(d['last'] for d in dates);a['activity_displays']=sorted({d['display'] for d in dates})
    plan['primary_date_refinement']={'at':core.now(),'source_plan_sha256':core.sha(path.read_bytes()),'new_record_date_changes':len(changes),'existing_dates_preserved':True}
    r.save('primary-date-application-review.json',changes);path.rename(original);r.save('delivery-plan.json',plan);r.log('Primary date/precision corrections for new records',len(changes)//2)

def access():
    for target in ('local','production'):
        with connect(target) as db:row=db.execute("SELECT current_database() database,current_setting('transaction_read_only') read_only").fetchone()
        assert row['database']=='artline' and row['read_only']=='on';r.log('Read-only access verified',target)

def cite(db,kind,ident,field,sid,q,url,evidence,when):
    db.execute('INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(kind,ident,field,sid,q,url,json.dumps(evidence,ensure_ascii=False),when,ACTOR))
def authority(db,kind,ident,q,sid,when,record=None):
    scheme=(record or {}).get('source_scheme','wikidata');external=(record or {}).get('source_record_id',q);url=(record or {}).get('source_url','https://www.wikidata.org/wiki/'+q)
    assert scheme!='wikidata' or re.fullmatch(r'Q\d+',q)
    old=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type=%s AND scheme=%s AND external_id=%s",(kind,scheme,external)).fetchall()
    if old:assert len(old)==1 and old[0]['entity_id']==ident;return
    insert(db,'external_identifiers',dict(entity_type=kind,entity_id=ident,scheme=scheme,external_id=external,canonical_url=url,source_id=sid,retrieved_at=when))

def apply(target,limit=0):
    plan=r.load('delivery-plan.json');pin=core.sha((RUN/'delivery-plan.json').read_bytes());t=plan['targets'][target];facts={x['qid']:x for x in r.load('selected-metadata-final-v2.json')['records']}
    backup=r.load('backups.json');assert backup['production']['status']=='SUCCESSFUL';assert core.sha(Path(backup['local']['path']).read_bytes())==backup['local']['sha256']
    qa=r.load('quality-review.json');assert qa['plan_sha256']==pin and qa['approved']
    manifest=RUN/'images/prepared-manifest.json';assert qa['images_sha256']==core.sha(manifest.read_bytes())
    images={x['qid']:x for x in json.loads(manifest.read_text()) if x['qid'] not in qa.get('held_images',{})}
    bucket=core.storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    counts=collections.Counter();confirmed_artists=set();confirmed_institutions=set()
    with connect(target,False) as db:
        with db.transaction():
            db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,'Spanish painters: selected museum and authority research','authority_data','https://www.wikidata.org/') ON CONFLICT(slug) DO NOTHING",(uid('source'),SOURCE));sid=str(db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id'])
        for st in (t['states'][:limit] if limit else t['states']):
            q=st['qid'];x=facts[q];ap=t['artists'][st['artist_qid']];ip=t['institutions'][st['institution_qid']];aid=st['id'];receipt=RUN/'applied'/target/(q+'.json')
            if receipt.exists():counts['already_applied']+=1;continue
            im=images.get(q)
            if im and not st['new']:
                old=st['preimage'];d=x['date']
                if old['primary_media_id'] or old['creation_year_start']!=d['first'] or old['creation_year_end']!=d['last']:im=None
            if im:
                content=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert core.sha(content)==im['sha256'] and len(content)<=100000
                blob=bucket.blob(im['path'].lstrip('/'))
                if not blob.exists():
                    blob.metadata={'sha256':im['sha256'],'license':im['license_label'],'wikidata':q};blob.cache_control='public,max-age=31536000,immutable';blob.upload_from_string(content,content_type='image/jpeg',if_generation_match=0)
                blob.reload();assert blob.size==len(content) and blob.md5_hash==base64.b64encode(hashlib.md5(content).digest()).decode()
            newartist=False;attached=False
            with db.transaction(), db.pipeline():
                db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(559220260916)')
                done=db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND field_name='spain_deep_identity'",(aid,sid)).fetchone()
                if done:counts['recovered_committed']+=1;continue
                if ip.get('id') and ip['id'] not in confirmed_institutions:
                    if ip['new']:db.execute("INSERT INTO institutions(id,slug,name,normalized_name,website_url,wikidata_id,kind,status) VALUES(%s,%s,%s,%s,%s,%s,'museum','review') ON CONFLICT(id) DO NOTHING",(ip['id'],ip['slug'],ip['name'],w.norm(ip['name']),ip['website_url'],ip['qid']))
                    assert db.execute("SELECT 1 FROM institutions WHERE id=%s AND status<>'archived'",(ip['id'],)).fetchone()
                    db.execute('INSERT INTO source_institutions(source_id,institution_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',(sid,ip['id']))
                if st['artist_id'] and st['artist_id'] not in confirmed_artists:
                    oldartist=db.execute('SELECT id,status FROM artists WHERE id=%s',(ap['id'],)).fetchone()
                    if not oldartist:
                        assert ap['new'];assert not db.execute('SELECT 1 FROM artists WHERE normalized_name=%s',(w.norm(ap['name']),)).fetchone()
                        fields=dict(id=ap['id'],slug=ap['slug'],display_name=ap['name'],sort_name=ap['name'],normalized_name=w.norm(ap['name']),entity_type='person',birth_year=ap['birth'],death_year=ap['death'],timeline_start_year=ap['first'],timeline_end_year=ap['last'],timeline_display=(str(ap['first'])+'–'+str(ap['last']) if ap['basis']=='life' else 'Documented works: '+str(ap['first'])+'–'+str(ap['last'])),timeline_basis=ap['basis'],status='review',created_by=ACTOR,updated_by=ACTOR)
                        if ap['basis']=='activity':
                            display='Documented works: '+('; '.join(ap['activity_displays']) if ap.get('activity_displays') else str(ap['first'])+'–'+str(ap['last']));fields.update(active_start_year=ap['first'],active_end_year=ap['last'],activity_display=display,timeline_display=display)
                        insert(db,'artists',fields);newartist=True
                        for alias in sorted(set(w.labels(ap['entity']))):db.execute("INSERT INTO artist_aliases(artist_id,alias,normalized_alias,alias_type) VALUES(%s,%s,%s,'alternate') ON CONFLICT DO NOTHING",(ap['id'],alias,w.norm(alias)))
                    else:assert oldartist['status']!='archived'
                    authority(db,'artist',ap['id'],ap['qid'],sid,ap['receipt']['retrieved_at'])
                    if not db.execute("SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=%s AND source_id=%s",(ap['id'],sid)).fetchone():
                        cite(db,'artist',ap['id'],'authority_identity_and_dates',sid,ap['qid'],'https://www.wikidata.org/wiki/'+ap['qid'],{'source_sha256':ap['receipt']['sha256'],'birth':ap['birth'],'death':ap['death'],'timeline_basis':ap['basis'],'existing_metadata_preserved':not ap['new']},ap['receipt']['retrieved_at'])
                        for c in ap['countries']:db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,%s,%s,false,%s) ON CONFLICT DO NOTHING",(ap['id'],c['code'],c['relationship'],c['basis']+' https://www.wikidata.org/wiki/'+ap['qid']))
                        if ap['woman']:db.execute("INSERT INTO artist_gender_evidence(artist_id,is_woman,basis,source_url,source_record_id,source_checksum,evidence_json,checked_at) VALUES(%s,true,'Explicit source P21 female statement; not inferred from name or portrait',%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",(ap['id'],'https://www.wikidata.org/wiki/'+ap['qid'],ap['qid'],ap['receipt']['sha256'],Jsonb({'claims':w.claims(ap['entity'],'P21'),'source_receipt':ap['receipt']}),ap['receipt']['retrieved_at']))
                old=db.execute('SELECT id::text,slug,status,revision,primary_media_id::text FROM artworks WHERE id=%s FOR UPDATE',(aid,)).fetchone()
                if st['new']:assert old is None
                else:assert old and all(old[k]==st['preimage'][k] for k in ('slug','status','revision','primary_media_id')),'Existing object changed since plan'
                media=None
                if im:
                    media=im['media_id'];db.execute("INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by) VALUES(%s,'local',%s,%s,'Wikimedia Commons','image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",(media,im['path'],im['page'],im['width'],im['height'],im['bytes'],im['sha256'],x['title']+' — '+x['creator_name'],im['rights_status'],im['license_label'],im['policy_url'],im['creator_credit'],im['attribution_text'],im['downloaded_at'],im['checked_at'],ACTOR))
                    db.execute('INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(media_id) DO NOTHING',(media,sid,q,core.sha(core.encode(im['raw'])),im['source_image_url'],im['policy_url'],'Exact object and creator authority, independent Commons identity, explicit file licence, source provenance and Spanish underlying-work chronology checked.','spain-deep-v1',im['checked_at'],Jsonb(im)));attached=True
                if st['new']:
                    d=st.get('applied_date',x['date']);accepted=bool(st['primary_validation'] and st['institution_id'])
                    insert(db,'artworks',dict(id=aid,slug=st['slug'],title=x['title'],normalized_title=w.norm(x['title']),alternate_title=next((s for s in x['titles'] if s!=x['title']),None),creation_year_start=d['first'],creation_year_end=d['last'],date_precision=d['precision'],date_display=d['display'],work_type='painting',current_institution_id=st['institution_id'] if accepted else None,accession_number=x['accession'],primary_media_id=media,status='review',research_candidate=True,unlinked_creator_label=None if st['artist_id'] else x['creator_name'],created_by=ACTOR,updated_by=ACTOR))
                    if st['artist_id']:insert(db,'artwork_artists',dict(artwork_id=aid,artist_id=st['artist_id'],attribution_role='primary',attribution_note='Unqualified named creator in source authority; evidence retained in review.'))
                    if st['institution_id']:insert(db,'artwork_location_assertions',dict(artwork_id=aid,claim_type='holding',institution_id=st['institution_id'],context='collection',source_id=sid,source_url=st['primary_validation']['url'] if accepted else 'https://www.wikidata.org/wiki/'+q,evidence_note='Primary museum technical record identity verified; current display is not asserted.' if accepted else 'Source P195 collection assertion retained for editorial review; no accepted holdings or display inferred.',checked_at=x['receipt']['retrieved_at'],review_state='accepted' if accepted else 'review'))
                elif media:db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(media,ACTOR,aid))
                if media:db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,'Selected licensed reproduction') ON CONFLICT DO NOTHING",(aid,media))
                authority(db,'artwork',aid,q,sid,x['receipt']['retrieved_at'],x)
                cite(db,'artwork',aid,'spain_deep_identity',sid,q,x.get('source_url','https://www.wikidata.org/wiki/'+q),{'source_sha256':x['receipt']['sha256'],'creator':x['creator_qid'],'secondary_date':x['date'],'applied_primary_date':st.get('applied_date'),'primary_review':st['primary_validation'],'title_unknown':x.get('title_unknown',False),'institution':x['institution_qid'],'institution_label':x['institution_name'],'accessions':x['accessions'],'review_only':True},x['receipt']['retrieved_at'])
                for page in st['primary_captures']:cite(db,'artwork',aid,'official_museum_record_capture',sid,q,page['receipt']['url'],page,page['receipt']['retrieved_at'])
            confirmed_artists.add(st['artist_id']);confirmed_institutions.add(ip.get('id'))
            result={'at':core.now(),'plan_sha256':pin,'qid':q,'target':target,'artwork_id':aid,'slug':st['slug'],'new_artwork':st['new'],'new_artist':newartist,'artist_id':st['artist_id'],'image_attached':attached,'media_id':media,'image_path':im['path'] if im else None,'status':'review' if st['new'] else st['preimage']['status']}
            core.save_new(receipt,result);counts['new_artworks' if st['new'] else 'existing_enriched']+=1;counts['new_artists']+=int(newartist);counts['images_attached']+=int(attached)
            if sum(counts.values())%25==0:r.log(target,dict(counts))
    r.save('delivery-'+target+('-canary' if limit else '')+'.json',{'at':core.now(),'counts':dict(counts),'plan_sha256':pin});r.log(target,'complete',dict(counts))

def verify():
    plan=r.load('delivery-plan.json');summary={};imageproofs={};parity={}
    facts={x['qid']:x for x in r.load('selected-metadata-final-v2.json')['records']}
    for target,t in plan['targets'].items():
        expected={st['id']:st for st in t['states']};receipts={x['artwork_id']:x for x in [json.loads(p.read_text()) for p in (RUN/'applied'/target).glob('*.json')]}
        with connect(target) as db:
            rows=db.execute("SELECT a.id::text,a.slug,a.title,a.creation_year_start,a.creation_year_end,a.date_precision,a.status,a.current_institution_id::text,a.primary_media_id::text,m.storage_path,m.checksum_sha256,m.byte_size,m.rights_status,(SELECT count(*) FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artwork' AND c.entity_id=a.id AND s.slug=%s AND c.field_name='spain_deep_identity') research_citations,(SELECT count(*) FROM artwork_location_assertions la JOIN sources s ON s.id=la.source_id WHERE la.artwork_id=a.id AND la.claim_type='display' AND s.slug=%s) new_display_claims FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id",(SOURCE,SOURCE,list(expected))).fetchall()
            assert len(rows)==len(expected) and len(receipts)==len(expected)
            for row in rows:
                st=expected[row['id']];rec=receipts[row['id']];assert row['research_citations']==1 and row['new_display_claims']==0
                if st['new']:
                    expected_date=st.get('applied_date',facts[st['qid']]['date']);assert row['status']=='review';assert (row['creation_year_start'],row['creation_year_end'],row['date_precision'])==(expected_date['first'],expected_date['last'],expected_date['precision'])
                else:assert row['status']==st['preimage']['status'];assert not st['preimage']['primary_media_id'] or row['primary_media_id']==st['preimage']['primary_media_id']
                if rec['image_attached']:
                    assert row['primary_media_id']==rec['media_id'] and row['byte_size']<=100000
                    assert db.execute('SELECT 1 FROM media_rights_evidence WHERE media_id=%s',(rec['media_id'],)).fetchone()
                    imageproofs[row['storage_path']]=row['checksum_sha256']
            preimages=json.loads((BACKUP/(target+'-artwork-preimages.json')).read_text());ignored={'primary_media_id','revision','updated_at','updated_by'}
            for pre in preimages:
                old=pre['row'];now=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s',(old['id'],)).fetchone()['row'];assert {k:v for k,v in old.items() if k not in ignored}=={k:v for k,v in now.items() if k not in ignored},'Existing catalogue content changed'
            artistplans={a['id']:a for a in t['artists'].values() if not a['unlinked'] and any(s['artist_id']==a['id'] for s in t['states'])}
            artists=db.execute("SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,a.timeline_start_year,a.timeline_end_year,a.timeline_basis,a.status,ARRAY(SELECT external_id FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata') qids FROM artists a WHERE a.id=ANY(%s::uuid[])",(list(artistplans),)).fetchall()
            assert len(artists)==len(artistplans)
            for a in artists:
                ap=artistplans[a['id']];assert ap['qid'] in a['qids']
                if ap['new']:
                    assert a['status']=='review' and (a['birth_year'],a['death_year'],a['timeline_start_year'],a['timeline_end_year'],a['timeline_basis'])==(ap['birth'],ap['death'],ap['first'],ap['last'],ap['basis'])
                else:assert all(a[k]==ap['preimage'][k] for k in ('slug','display_name','birth_year','death_year','status')),'Existing artist metadata changed'
            links=db.execute("SELECT a.id::text,a.unlinked_creator_label,ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) artists FROM artworks a WHERE a.id=ANY(%s::uuid[])",([s['id'] for s in t['states'] if s['new']],)).fetchall()
            for a in links:
                st=expected[a['id']];assert a['artists']==([st['artist_id']] if st['artist_id'] else [])
                assert a['unlinked_creator_label']==(None if st['artist_id'] else facts[st['qid']]['creator_name'])
            r.save('verified-artists-'+target+'.json',artists)
        r.save('verified-'+target+'.json',rows);summary[target]={'records':len(rows),'new_artworks':sum(x['new_artwork'] for x in receipts.values()),'new_artists':sum(x['new_artist'] for x in receipts.values()),'images_attached':sum(x['image_attached'] for x in receipts.values()),'existing_fields_preserved':len(preimages)}
        parity[target]={expected[row['id']]['qid']:{k:row[k] for k in ('title','creation_year_start','creation_year_end','date_precision','status','storage_path','checksum_sha256')} for row in rows if expected[row['id']]['new']}
    assert parity['local']==parity['production'],'New catalogue records differ between targets'
    def check_image(item):
        path,digest=item
        raw=(ROOT/'apps/web/public'/path.lstrip('/')).read_bytes();assert core.sha(raw)==digest
        res=requests.get(SITE+path,timeout=(10,45));res.raise_for_status();assert core.sha(res.content)==digest
        return {'url':SITE+path,'sha256':digest,'bytes':len(raw),'status':res.status_code}
    with ThreadPoolExecutor(max_workers=6) as pool:checks=list(pool.map(check_image,imageproofs.items()))
    r.save('final-verification.json',{'at':core.now(),'databases':summary,'public_images':checks,'review_only':True,'new_display_claims':0});r.log('Verified',summary,'public images',len(checks))

def smoke():
    plan=r.load('delivery-plan.json')['targets']['production'];facts={x['qid']:x for x in r.load('selected-metadata-final-v2.json')['records']}
    receipts={p.stem:json.loads(p.read_text()) for p in (RUN/'applied/production').glob('*.json')};selected={}
    # Cover delivered images, new creators, women, unknown dates, primary date
    # refinements and records discovered directly in museum catalogues.
    selectors=[lambda s:s['new'],lambda s:receipts[s['qid']]['image_attached'],lambda s:plan['artists'][s['artist_qid']]['new'],lambda s:plan['artists'][s['artist_qid']]['woman'],lambda s:facts[s['qid']]['date']['precision']=='unknown',lambda s:bool(s.get('applied_date')),lambda s:s['qid'].startswith('reina-')]
    for test in selectors:
        matches=[s for s in plan['states'] if s['qid'] in receipts and s['artist_id'] and test(s)]
        for s in matches[:2]:selected[s['qid']]=s
    assert selected
    checks=[]
    for q,s in selected.items():
        a=plan['artists'][s['artist_qid']];url=SITE+'/api/backend/v1/artists/'+a['slug']+'/works/'+s['id']
        res=requests.get(url,timeout=(10,50));res.raise_for_status();obj=res.json();rec=receipts[q]
        assert obj['id']==s['id'] and obj['status']==rec['status']
        if s['new']:
            d=s.get('applied_date',facts[q]['date']);assert obj['title']==facts[q]['title'];assert (obj.get('creation_year_start'),obj.get('creation_year_end'))==(d['first'],d['last'])
            assert obj.get('display') is None
        if rec['image_attached']:assert rec['image_path'] in obj['media_url']
        checks.append({'qid':q,'url':url,'status':res.status_code,'artwork_id':obj['id'],'review_status':obj['status'],'media_url':obj.get('media_url')})
    r.save('api-smoke'+('-canary' if len(receipts)<len(plan['states']) else '')+'.json',{'at':core.now(),'checks':checks,'bounded_reads':True});r.log('Production artwork API checks',len(checks))

def report():
    final=r.load('final-verification.json');plan=r.load('delivery-plan.json');selected=r.load('selected-metadata-final-v2.json');facts={x['qid']:x for x in selected['records']};t=plan['targets']['production'];states={x['qid']:x for x in t['states']};receipts={p.stem:json.loads(p.read_text()) for p in (RUN/'applied/production').glob('*.json')};ims={x['qid']:x for x in r.load('images/prepared-manifest.json')}
    rows=[]
    for q,x in facts.items():
        st=states.get(q);rec=receipts.get(q,{});im=ims.get(q,{});applied_date=st.get('applied_date',x['date']) if st else x['date']
        rows.append({'source_id':q,'artist':x['creator_name'],'artist_authority':x['creator_qid'],'title':x['title'],'date_display':applied_date['display'],'year_start':applied_date['first'],'year_end':applied_date['last'],'date_precision':applied_date['precision'],'secondary_source_date':x['date']['display'],'institution_source_label':x['institution_name'],'inventory':x['accession'],'source_url':x.get('source_url','https://www.wikidata.org/wiki/'+q),'official_record_urls':' | '.join(u['url'] for u in x['object_urls']),'delivery':'new_review_record' if rec.get('new_artwork') else 'existing_enriched' if rec else 'held_for_review','artwork_id':rec.get('artwork_id'),'artwork_url':SITE+'/artists/'+t['artists'][st['artist_qid']]['slug']+'/works/'+rec['artwork_id'] if rec and rec.get('artist_id') else '', 'image_uploaded_and_attached':rec.get('image_attached',False),'image_url':SITE+rec['image_path'] if rec.get('image_attached') else '', 'image_license':im.get('license_label') if rec.get('image_attached') else '', 'image_source':im.get('page') if rec.get('image_attached') else '', 'image_credit':im.get('creator_credit') if rec.get('image_attached') else '', 'holding_validated_from_primary':bool(st and st['primary_validation']),'status':rec.get('status','research_only')})
    with (RUN/'artwork-research-and-delivery.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    before={a['id']:a for a in r.load('artist-coverage.json')};artistrows=[]
    for q,a in t['artists'].items():
        delivered=[v for v in receipts.values() if v['artist_id']==a['id']]
        if not delivered:continue
        artistrows.append({'artist':a['name'],'authority_url':'https://www.wikidata.org/wiki/'+q,'artist_url':SITE+'/artists/'+a['slug'],'new_profile':any(v['new_artist'] for v in delivered),'birth_year':a['birth'],'death_year':a['death'],'timeline_basis':a['basis'],'country_relationships':'; '.join(c['relationship'] for c in a['countries']),'source_identifies_woman':a['woman'],'before_dated_paintings':before.get(a['id'],{}).get('paintings_through_1970'),'new_artworks':sum(v['new_artwork'] for v in delivered),'images_attached':sum(v['image_attached'] for v in delivered)})
    with (RUN/'artist-research-and-delivery.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(artistrows[0]));writer.writeheader();writer.writerows(artistrows)
    image_events=core.latest_events(RUN/'images');reasons=collections.Counter(x.get('reason') or x.get('error') for x in image_events.values() if x['outcome']!='prepared');primary=r.load('primary-capture-index.json');validation=r.load('primary-validation.json');db=final['databases']['production'];baseline=r.load('audit-summary.json')['countries']['ES'];newartistnames=sorted(a['artist'] for a in artistrows if a['new_profile']);museumcounts=collections.Counter(facts[q]['institution_name'] for q,rec in receipts.items() if rec['new_artwork']);unknown=sum(states[q].get('applied_date',facts[q]['date'])['precision']=='unknown' for q,rec in receipts.items() if rec['new_artwork']);titleunknown=sum(bool(facts[q].get('title_unknown')) for q,rec in receipts.items() if rec['new_artwork'])
    body=f'''# Spain: deep selected collection research — 16 September 2026

Completed delivery: **{db['new_artists']} new artist profiles, {db['new_artworks']} new artwork records, and {db['images_attached']} licensed images attached in production**. Both database results and every uploaded public image are checked in `final-verification.json`. All additions remain **review**; no records were published and no current-display assertions were added.

## Scope and evidence

- Audited the real local catalogue read-only: {baseline['associated_artist_records']} Spain-associated artist records; {baseline['artist_associated_works_anywhere']['paintings_through_1970']} dated paintings through 1970, including {baseline['artist_associated_works_anywhere']['paintings_through_1970_without_media']} without images. Institutional geography alone undercounts Spain: Prado, MNAC and Reina Sofía had incomplete place mapping. Their identity was considered independently.
- Resolved 126 priority artist identities, spanning medieval, Renaissance, Golden Age, eighteenth-century, nineteenth-century, regional, women and modern artists, plus artists explicitly active in Spain. Retained 2,291 bounded museum-connection discovery leads, at most 24 per artist; selected at most ten works per creator before image requests.
- Final museum-scoped selection: {len(facts)} records, including four directly verified Reina Sofía paintings omitted by secondary discovery. Unqualified authorship, current collection statements, object types, dates, inventory numbers and conflicting identities were reviewed separately.
- Captured official website responses for {primary['captured_objects']} selected objects. Some responses are landing pages and do not verify the object. {len(validation['records'])} technical object records passed explicit title/creator/inventory/type checks or direct manual primary review. Blocked and missing pages remain unresolved; a capture is not automatically a validated holding.
- New entries with unknown creation dates: {unknown}; explicitly unknown title: {titleunknown}. Unknown metadata stays unknown. Detailed source claims and unknowns remain in `selected-metadata-final-v2.json` and the retained source captures.
- Primary museum records refined the dates or precision of 24 new works; pre-existing dates were preserved. Nine Luis Tristán works retain an unlinked named creator label because an existing profile gives a conflicting death year (1640 versus the source authority's 1624); no duplicate artist profile or guessed reconciliation was created.
- Distinct artist identities and aliases were reconciled before writing. Federico de Madrazo y Kuntz was distinguished from Federico de Madrazo y Ochoa; Vicente Masip, Juan de Juanes and Vicente Macip Comes were not conflated. Identical generic titles were not used to merge works across museums.

## Delivered counts

| Target | New artists | New artworks | Images attached | Existing artwork fields verified preserved |
|---|---:|---:|---:|---:|
'''
    for target,stats in final['databases'].items():body+=f"| {target} | {stats['new_artists']} | {stats['new_artworks']} | {stats['images_attached']} | {stats['existing_fields_preserved']} |\n"
    body+='\nNew profiles: '+', '.join(newartistnames)+'.\n\nNew artwork records by source collection:\n\n'
    for name,count in museumcounts.most_common():body+=f'- {name}: {count}\n'
    body+='''
## Images and unresolved work

Visual review covered all 302 prepared reproductions. A final provenance audit withheld 209 Prado website reproductions without explicit donation evidence and one mixed commercial-mirror source before any upload. The prepared manifest is an evidence ledger, not an approval list; `quality-review.json` records the exclusions. One cross-museum duplicate discovered visually was excluded from record creation.

Each attached image has a pinned Commons revision, physical-object identity evidence, source provenance, licence URL, credits, source checksum and served-file checksum. Full-frame JPEG derivatives are at most 100,000 bytes; no images were generated or substituted. Conditional uploads preserve existing objects and bucket access settings.

Underlying artwork rights and reproduction rights were reviewed separately. The selected automated path conservatively held creators who died after 1945 or whose death date was unresolved; their metadata was retained. It does not claim that every later work is unusable. Prado website images without explicit donation evidence were held; identifiable independent photographs and explicitly licensed museum contributions were checked individually. See the [Prado reproduction information](https://www.museodelprado.es/en/legal-information), [Spanish copyright text](https://www.boe.es/buscar/act.php?id=BOE-A-1996-8930), and exact per-file evidence in `images/`.

Source-access restrictions, attribution ambiguities, multiple collection statements, missing dates, images without verifiable origins, and rights conflicts are documented, not silently resolved. This is a deep **bounded selection**, not an exhaustive inventory of Spanish art. Four priority artists had no qualifying result in secondary discovery; direct museum research recovered two of them. Ferrer Bassa's mural attribution and Margarita Manso's qualifying museum works remain separate research items.

## Files and recovery

- `artwork-research-and-delivery.csv`: every selected object, its source, delivery disposition, and image credit/link.
- `artist-research-and-delivery.csv`: delivered creator identities, dates, affiliations and added works/images.
- `delivery-plan.json`, `quality-review.json`, `applied/`: pinned plan, image review and per-record transaction receipts.
- `verified-local.json`, `verified-production.json`, `final-verification.json`: actual database and public-image proofs.
- `backups.json`: validated local full dump and successful managed Cloud SQL backup. Recovery files live under `/Users/vadimdulub/Library/Application Support/Artline/backups/spain-deep-20260916/`.

No test databases or real-catalogue test fixtures were created. Existing artwork titles, dates, descriptions, attributions and publication states were compared against preimages; existing images were preserved. No deployment, commit, Terraform apply, or deletion was performed. Operational queries were scoped by artist, institution or selected IDs; this research does not claim a 10-million-row load test.
'''
    (RUN/'README.md').write_text(body);r.save('report-summary.json',{'at':core.now(),'databases':final['databases'],'selected':len(facts),'unknown_date_new_artworks':unknown,'unknown_title_new_artworks':titleunknown,'image_review_reasons':dict(reasons),'new_artists':newartistnames});r.log('Research report and CSV ledgers written')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','backup','apply','verify','access','report','refine_dates','smoke']);p.add_argument('--target',choices=['local','production']);p.add_argument('--limit',type=int,default=0);a=p.parse_args();apply(a.target,a.limit) if a.phase=='apply' else globals()[a.phase]()
