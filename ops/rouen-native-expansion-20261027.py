"""Finite exact-object Rouen expansion, with conservative identity/source holds."""
import argparse
import collections
import gzip
import importlib.util
import json
import re
import shutil
from pathlib import Path

from psycopg.types.json import Jsonb
import requests
from bs4 import BeautifulSoup
import exhibitions_common as c

s=importlib.util.spec_from_file_location('resume',Path(__file__).with_name('catalogue-deduplication-resume-20261027.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
OP=m.OP+'-rouen-native-expansion';E=m.E/'native-expansion';D=m.D;B=m.B/'native-expansion'
ROUEN='f92766ec-41cf-42d1-9bb1-f333fe5d2980'


def aid(native):return m.uid('new-rouen-artwork/'+native)


def selection():
    return c.load(D/'rouen-expansion-final-research-selection-20261027.json.gz')


def image_selection():
    s=importlib.util.spec_from_file_location('preparation',Path(__file__).with_name('rouen-image-preparation-20261026.py'))
    prep=importlib.util.module_from_spec(s);s.loader.exec_module(prep)
    out=[];gaps=[]
    for r in selection()['selected']:
        path=D/'rouen-notices'/(r['native_id']+'.json.gz')
        if not path.exists():gaps.append(dict(native_id=r['native_id'],reason='No published image flag/current image notice'));continue
        n=c.load(path)
        if n['state']!='published_images' or not n['images']:gaps.append(dict(native_id=r['native_id'],reason=n['state']));continue
        facts=dict(n['fields']);soup=BeautifulSoup(gzip.decompress(Path(n['receipt']['body_path']).read_bytes()),'html.parser')
        facts['Millésime de création']=prep.field(soup,'Millésime de création')
        facts["Précisions sur l'auteur"]=prep.field(soup,"Précisions sur l'auteur")
        assert c.norm(facts['Titre'])==c.norm(r['facts']['title'])
        assert c.norm(facts["Numéro d'inventaire"])==c.norm(r['facts']['accession'])
        assert 'rouen' in c.norm(facts.get('Lieu de conservation'))
        out.append(dict(native_id=r['native_id'],artwork_id=aid(r['native_id']),title=r['facts']['title'],source_facts=r['facts'],notice_fields=facts,notice_receipt=n['receipt'],images=n['images'],actual_visual_review_required=True,exact_native_identity_basis='New exact object; source-native inventory/title and current POP notice agree; all existing Rouen inventory/title/native identifier collisions held before selection.'))
    c.save(D/'rouen-new-work-image-research-selection-20261027.json.gz',dict(at=c.now(),selected=out,held=gaps))
    print('Pinned',len(out),'new native works with published image views;',len(gaps),'without published usable notice views.',flush=True)


def plan():
    value=selection();selected=value['selected'];assert len(selected)==624
    ids=[aid(r['native_id'])for r in selected];natives=[r['native_id']for r in selected]
    assert len(set(ids))==624 and len(set(natives))==624
    with c.connect()as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        assert not m.rows(db,'artworks','id',ids)
        assert not db.execute("SELECT id FROM external_identifiers WHERE entity_type='artwork'AND(scheme='joconde-object'AND external_id=ANY(%s))",(natives,)).fetchall()
        source=db.execute("SELECT to_jsonb(s)v FROM sources s WHERE slug='joconde-m0729'").fetchone()['v']
        # Protect the entire preexisting Rouen work cohort and all image pointers.
        protected=[r['v']for r in db.execute('SELECT to_jsonb(a)v FROM artworks a WHERE current_institution_id=%s AND status<>\'archived\'',(ROUEN,))]
        assert len(protected)==1508
        # Pin the application CHECK constraints and all partial/unique indexes.
        constraints=db.execute("SELECT conrelid::regclass::text table_name,conname,pg_get_constraintdef(oid)definition FROM pg_constraint WHERE conrelid=ANY(%s::regclass[])",(['artworks','artwork_artists','artwork_location_assertions','external_identifiers','citations'],)).fetchall()
        indexes=db.execute("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public'AND tablename=ANY(%s)",(['artworks','artwork_artists','artwork_location_assertions','external_identifiers','citations'],)).fetchall()
        for r in selected:
            f=r['facts'];assert f['first']<=f['last']<=1989 and r['raw']['Code_Museofile']=='M0729'
            assert f['accession'] and f['title']
            a=r['canonical_artist_candidate']
            if a:
                live=db.execute('SELECT id::text,display_name,birth_year,death_year,status FROM artists WHERE id=%s',(a['id'],)).fetchone()
                assert all(live[k]==a[k]for k in live)
    B.mkdir(parents=True,exist_ok=True);B.chmod(0o700)
    assert shutil.disk_usage(B).free>15*1024**3
    p=dict(at=c.now(),selection=value,source=source,protected_existing_artworks=protected,constraints=constraints,indexes=indexes)
    c.save(B/'plan.json.gz',p)
    c.save(E/'plan-pin.json',dict(at=c.now(),path=str(B/'plan.json.gz'),sha256=c.sha((B/'plan.json.gz').read_bytes()),new_native_artworks=624,existing_creator_link_candidates=79,identity_or_current_notice_holds=15,new_artist_profiles=0))
    print('Pinned624 new pre1990 native objects; all1508 existing Rouen works protected.',flush=True)


def apply():
    path=B/'plan.json.gz';assert c.sha(path.read_bytes())==c.load(E/'plan-pin.json')['sha256'];p=c.load(path);selected=p['selection']['selected']
    for start in range(0,len(selected),50):
        number=start//50+1;batch=selected[start:start+50];operation=OP+'-b%03d'%number
        if(E/('batch-%03d-verification.json'%number)).exists():continue
        changes=[];ids=[aid(r['native_id'])for r in batch]
        with c.connect(write=True)as db:
            m.acquire_locks(db)
            assert not m.rows(db,'artworks','id',ids)
            assert not db.execute("SELECT id FROM external_identifiers WHERE entity_type='artwork'AND external_id=ANY(%s)",([r['native_id']for r in batch],)).fetchall()
            current=m.rows(db,'artworks','id',[r['id']for r in p['protected_existing_artworks']])
            assert m.ordered(current)==m.ordered(p['protected_existing_artworks']),'Existing work cohort changed; reconcile before continuing'
            c.save(B/('locked-before-%03d.json.gz'%number),dict(at=c.now(),operation=operation,new_artwork_preimages_absent=True,ids=ids,protected_existing_sha256=c.sha(json.dumps(m.ordered(current),sort_keys=True).encode())))
            for r in batch:
                f=r['facts'];native=r['native_id'];id=aid(native);artist=r['canonical_artist_candidate'];label=r['raw'].get('Auteur')or'Anonymous / maker not specified by source'
                desc='Ministry of Culture POP/Joconde native object '+native+'. Inventory: '+f['accession']+'. Source maker wording: '+label+'. Collection association only; current display and legal ownership are not asserted. Source date wording retained: '+f['date_display']+'.'
                work=db.execute("INSERT INTO artworks(id,slug,title,normalized_title,status,work_type,creation_year_start,creation_year_end,date_precision,date_display,medium_text,dimensions_text,accession_number,unlinked_creator_label,description_md,current_institution_id,current_location_text,location_checked_at,created_by,updated_by)VALUES(%s,%s,%s,%s,'review',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Rouen; musée des beaux-arts',now(),%s,%s)RETURNING to_jsonb(artworks)v",(id,'rouen-joconde-'+native.lower(),f['title'],c.norm(f['title']),f['work_type'],f['first'],f['last'],f['date_precision'],f['date_display'],f['medium'],f['dimensions'],f['accession'],label,desc,ROUEN,m.EDITOR,m.EDITOR)).fetchone()['v']
                ext=db.execute("INSERT INTO external_identifiers(id,entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)VALUES(%s,'artwork',%s,'joconde-object',%s,%s,%s,now())RETURNING to_jsonb(external_identifiers)v",(m.uid('new-rouen-native/'+native),id,native,f['source_url'],p['source']['id'])).fetchone()['v']
                citation=db.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)VALUES(%s,'artwork',%s,'native_catalogue_object_and_maker',%s,%s,%s,%s,now(),%s)RETURNING to_jsonb(citations)v",(m.uid('new-rouen-citation/'+native),id,p['source']['id'],native,f['source_url'],json.dumps(dict(operation=operation,native_record=r['raw'],interpreted_facts=f,canonical_artist_id=artist['id']if artist else None,artist_basis='Exact unique existing name/alias and both explicit source life years'if artist else'Unresolved or qualified maker label preserved literally; no canonical identity invented',scope='Pictorial work through1989; original numeric/century/quarter bounds preserved; physical components, custody/date/identity conflicts held',selection_sha256=c.load(E/'plan-pin.json')['sha256']),ensure_ascii=False),m.EDITOR)).fetchone()['v']
                holding=db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,institution_id,claim_type,context,review_state,source_id,source_url,checked_at,evidence_note)VALUES(%s,%s,%s,'holding','collection','accepted',%s,%s,now(),%s)RETURNING to_jsonb(artwork_location_assertions)v",(m.uid('new-rouen-holding/'+native),id,ROUEN,p['source']['id'],f['source_url'],f['holding_basis']+' Native reference '+native+'; original custody wording retained in the source citation.')).fetchone()['v']
                for t,obj in [('artworks',work),('external_identifiers',ext),('citations',citation),('artwork_location_assertions',holding)]:changes.append(dict(table=t,key=obj['id'],before=None,after=obj))
                if artist:
                    current=db.execute('SELECT display_name,birth_year,death_year,status FROM artists WHERE id=%s FOR SHARE',(artist['id'],)).fetchone()
                    assert all(current[k]==artist[k]for k in current)
                    link=db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,representative_order,attribution_note)VALUES(%s,%s,'primary',1,%s)RETURNING to_jsonb(artwork_artists)v",(id,artist['id'],'Exact source maker name/alias and both life years agree with the existing canonical artist. Original label and author precision retained in native citation.')).fetchone()['v']
                    changes.append(dict(table='artwork_artists',key=id+'/'+artist['id'],entity_id=id,before=None,after=link))
            m.audit(db,changes,operation)
            c.save(B/('transaction-after-%03d.json.gz'%number),dict(at=c.now(),operation=operation,changes=changes,ids=ids))
        verify_batch(number)


def verify_batch(number):
    tx=c.load(B/('transaction-after-%03d.json.gz'%number));changes=tx['changes']
    with c.connect()as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        for t in ['artworks','external_identifiers','citations','artwork_location_assertions']:
            expected={r['key']:r['after']for r in changes if r['table']==t}
            assert {r['id']:r for r in m.rows(db,t,'id',list(expected))}==expected,('Postimage mismatch',t)
        expected=[r['after']for r in changes if r['table']=='artwork_artists'];assert m.ordered(m.rows(db,'artwork_artists','artwork_id',tx['ids']))==m.ordered(expected)
        aa=db.execute('SELECT id,before_json,after_json FROM audit_log WHERE id=ANY(%s::uuid[])',([m.uid(tx['operation']+'/'+r['table']+'/'+r['key'])for r in changes],)).fetchall();aa={str(r['id']):r for r in aa};assert len(aa)==len(changes)
        assert all(aa[m.uid(tx['operation']+'/'+r['table']+'/'+r['key'])]['before_json']is None and aa[m.uid(tx['operation']+'/'+r['table']+'/'+r['key'])]['after_json']==r['after']for r in changes)
        n=db.execute('SELECT count(*)n FROM artworks a JOIN artwork_search_documents s ON s.id=a.id WHERE a.id=ANY(%s::uuid[])AND a.status=s.status AND s.title=a.title',(tx['ids'],)).fetchone()['n'];assert n==len(tx['ids'])
    c.save(E/('batch-%03d-verification.json'%number),dict(at=c.now(),passed=True,new_artworks=len(tx['ids']),canonical_creator_links=len(expected),atomic_audits=len(changes),search_documents=n))
    print('New Rouen object batch',number,'committed and independently verified:',len(tx['ids']),'works,',len(expected),'canonical makers.',flush=True)


def verify():
    p=c.load(B/'plan.json.gz');s=requests.Session();out=[]
    for r in p['selection']['selected']:
        id=aid(r['native_id']);receipt=E/'public'/(r['native_id']+'.json')
        if receipt.exists():out.append(c.load(receipt));continue
        response=s.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/atlas/artworks/'+id,timeout=(10,35));assert response.status_code==200,(r['native_id'],response.status_code)
        v=response.json();assert v['id']==id and v['title']==r['facts']['title']
        artist=r['canonical_artist_candidate']
        if artist:assert any(a['id']==artist['id']for a in v['creators'])
        row=dict(native_id=r['native_id'],artwork_id=id,status=200,canonical_artist_id=artist['id']if artist else None)
        c.save(receipt,row);out.append(row)
        if len(out)%50==0:print('New Rouen public artwork responses verified',len(out),'/624',flush=True)
    with c.connect()as db:
        assert m.ordered(m.rows(db,'artworks','id',[r['id']for r in p['protected_existing_artworks']]))==m.ordered(p['protected_existing_artworks'])
    c.save(E/'final-verification.json',dict(at=c.now(),passed=True,new_artworks=len(out),canonical_creator_links=sum(bool(r['canonical_artist_id'])for r in out),new_artist_profiles=0,existing_artworks_preserved=1508,all_public_artwork_responses=len(out),identity_or_current_notice_holds=15,unresolved_source_creator_labels_preserved=True,source_images_still_separate_reviewed_deliveries=True))
    print('All624 new source-native artworks and public responses independently verified; all1508 existing Rouen works preserved.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','apply','verify','image_selection']);a=p.parse_args();globals()[a.phase]()
