"""Five exact native-object duplicate pairs; no image or historical record deletion."""
import importlib.util
import json
from pathlib import Path

import requests
from psycopg.types.json import Jsonb
import exhibitions_common as c

s=importlib.util.spec_from_file_location('resume',Path(__file__).with_name('catalogue-deduplication-resume-20261027.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
E=m.E;B=m.B/'artworks/attempt-003';OP=m.OP+'-artworks-five-v3'


def snapshot(db,p):
    out={}
    for f in p['inbound_foreign_keys']:
        out[f['table_name']]=m.rows(db,f['table_name'],f['column_name'],p['ids'])
    out['artworks']=m.rows(db,'artworks','id',p['ids'])
    for t in ['citations','external_identifiers']:
        out[t]=[r['v']for r in db.execute('SELECT to_jsonb(t)v FROM '+t+" t WHERE entity_type='artwork'AND entity_id=ANY(%s::uuid[])",(p['ids'],))]
    slugs=[r['slug']for r in out['artworks']]
    out['slug_redirects']=[r['v']for r in db.execute("SELECT to_jsonb(t)v FROM slug_redirects t WHERE entity_type='artwork'AND(entity_id=ANY(%s::uuid[])OR old_slug=ANY(%s))",(p['ids'],slugs))]
    return out


def apply():
    assert c.load(E/'identity-deployment-verification.json')['passed']
    assert c.load(E/'artwork-five-attempt001-rollback-verification.json')['passed']
    assert c.load(E/'artwork-five-attempt002-rollback-verification.json')['passed']
    p=c.load(E/'artwork-five-fresh-preimages.json.gz');extra=c.load(E/'artwork-five-additional-preimages.json.gz')
    before=p['tables'];works={r['id']:r for r in before['artworks']};mapping={a:b for key,a,b in p['pairs']}
    assert len(mapping)==5 and len(works)==10 and not extra['tables']['research_artwork_possible_references']
    assert not any(r['artwork_id'] in mapping for r in extra['tables']['artist_key_artworks'])
    for key,alias,canonical in p['pairs']:
        old,new=works[alias],works[canonical]
        assert old['status']!='archived' and new['status']!='archived'
        assert c.norm(old['title'])==c.norm(new['title'])
        assert old['medium_text']==new['medium_text'] and old['dimensions_text']==new['dimensions_text']
        if key!='leventis-531':assert old['accession_number']==new['accession_number'] and old['date_display']==new['date_display']
        else:assert c.norm(old['accession_number'])=='aglg 531' and new['accession_number']=='531'
        old_creators={(r['artist_id'],r['attribution_role'])for r in before['artwork_artists']if r['artwork_id']==alias}
        new_creators={(r['artist_id'],r['attribution_role'])for r in before['artwork_artists']if r['artwork_id']==canonical}
        assert old_creators<=new_creators,'Creator conflict requires separate review'
        # Each pair has two independently retained source schemes for one native object.
        identifiers=[r for r in before['external_identifiers']if r['entity_id']in [alias,canonical]]
        assert len({r['scheme']for r in identifiers})==len(identifiers)
        assert all(r['canonical_url']for r in identifiers)
    for t in ['member_artwork_bookmarks','exhibition_entries','exhibition_objects','research_artwork_links','research_resolutions','research_artwork_enrichments','artwork_places']:
        assert not before[t],('Nonempty references require additional merge review',t)
    assert all(r['artwork_id']not in mapping for r in before['curated_collection_items'])
    B.mkdir(parents=True,exist_ok=True);B.chmod(0o700)
    c.save(B/'source-identity-decisions.json',dict(at=c.now(),pairs=p['pairs'],basis='Exact official object identifiers and compatible native inventory, title, creator, medium and measurements. LeventisAGLG531 has the corresponding prefixed/plain accession; the four Basel pairs retain separate native schemes but the same object IDs. Rodin preserves the exact cast7/12 and1942/43 foundry wording. No Basel host requests were made under its existing access hold.',canonical_choices='Preserve illustrated Leventis/Senecio records and the enriched native Basel records for the other three pairs.',preimages_sha256=c.sha((E/'artwork-five-fresh-preimages.json.gz').read_bytes())))
    changes=[]
    with c.connect(write=True)as db:
        m.acquire_locks(db)
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',(p['ids'],)).fetchall()
        actual=snapshot(db,p)
        for t in before:assert m.ordered(actual[t])==m.ordered(before[t]),('Changed preimage',t)
        assert not db.execute('SELECT 1 FROM research_artwork_links WHERE possible_artwork_ids && %s::uuid[] LIMIT 1',(p['ids'],)).fetchone()
        assert m.ordered(m.rows(db,'artist_key_artworks','artwork_id',p['ids']))==m.ordered(extra['tables']['artist_key_artworks'])
        c.save(B/'locked-before.json.gz',dict(at=c.now(),tables=actual,extra=extra))
        # Holding assertion identity is deliberately immutable. Preserve every
        # original row on its historical artwork, adding separately audited
        # canonical copies rather than retargeting or deleting the originals.
        for old in before['artwork_location_assertions']:
            if old['artwork_id']not in mapping:continue
            target=mapping[old['artwork_id']]
            cloned=dict(old,id=m.uid('canonical-assertion/'+old['id']),artwork_id=target)
            cloned.pop('created_at')
            active=[r for r in before['artwork_location_assertions']if r['artwork_id']==target and r['claim_type']=='holding'and r['review_state']=='accepted'and r['superseded_by']is None]
            if old['claim_type']=='holding'and old['review_state']=='accepted'and old['superseded_by']is None and active:
                assert len(active)==1 and active[0]['institution_id']==old['institution_id']
                cloned['superseded_by']=active[0]['id']
            cloned['evidence_note']=(old['evidence_note']or '')+'\nCanonical identity evidence copy; immutable original assertion '+old['id']+' retained. Operation: '+OP
            fields=list(cloned)
            new=db.execute('INSERT INTO artwork_location_assertions('+','.join(fields)+')VALUES('+','.join(['%s']*len(fields))+')RETURNING to_jsonb(artwork_location_assertions)v',[cloned[k]for k in fields]).fetchone()['v']
            assert all(new[k]==v for k,v in old.items()if k not in {'id','artwork_id','superseded_by','created_at','evidence_note'})
            changes.append(dict(table='artwork_location_assertions',key=new['id'],before=None,after=new))
        for t,col in [('external_identifiers','entity_id'),('citations','entity_id')]:
            for old in before[t]:
                if old[col]not in mapping:continue
                target=mapping[old[col]]
                allowed={col}
                new=db.execute('UPDATE '+t+' SET '+col+'=%s WHERE id=%s RETURNING to_jsonb('+t+')v',(target,old['id'])).fetchone()['v']
                assert all(new[k]==v for k,v in old.items()if k not in allowed)
                changes.append(dict(table=t,key=old['id'],before=old,after=new))
        # Legacy primary pointers sometimes predate artwork_media. Retain all
        # four existing media rows and expose every existing distinct view.
        attachments={(r['artwork_id'],r['media_id'])for r in before['artwork_media']}
        for key,alias,canonical in p['pairs']:
            for w in [works[canonical],works[alias]]:
                mid=w['primary_media_id']
                if not mid or (canonical,mid)in attachments:continue
                order=0 if mid==works[canonical]['primary_media_id'] else 10
                r=db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label)VALUES(%s,%s,%s,'Existing pre-reconciliation image; original source credit and rights retained')RETURNING to_jsonb(artwork_media)v",(canonical,mid,order)).fetchone()['v']
                changes.append(dict(table='artwork_media',key=canonical+'/'+mid,entity_id=canonical,before=None,after=r));attachments.add((canonical,mid))
            old=works[alias]
            archived=db.execute("UPDATE artworks SET status='archived',current_institution_id=%s,updated_at=now(),updated_by=%s,revision=revision+1 WHERE id=%s RETURNING to_jsonb(artworks)v",(old['current_institution_id'],m.EDITOR,alias)).fetchone()['v']
            assert all(archived[k]==v for k,v in old.items()if k not in {'status','updated_at','updated_by','revision'})
            changes.append(dict(table='artworks',key=alias,before=old,after=archived))
            can=works[canonical]
            holding=can['current_institution_id']or old['current_institution_id']
            updated=db.execute('UPDATE artworks SET current_institution_id=%s,updated_at=now(),updated_by=%s,revision=revision+1 WHERE id=%s RETURNING to_jsonb(artworks)v',(holding,m.EDITOR,canonical)).fetchone()['v']
            assert all(updated[k]==v for k,v in can.items()if k not in {'current_institution_id','updated_at','updated_by','revision'})
            changes.append(dict(table='artworks',key=canonical,before=can,after=updated))
            redir=db.execute("INSERT INTO slug_redirects(id,entity_type,entity_id,old_slug)VALUES(%s,'artwork',%s,%s)RETURNING to_jsonb(slug_redirects)v",(m.uid('artwork-redirect/'+alias),canonical,old['slug'])).fetchone()['v']
            changes.append(dict(table='slug_redirects',key=redir['id'],before=None,after=redir))
        after=snapshot(db,p)
        assert len(after['external_identifiers'])==len(before['external_identifiers']) and len(after['citations'])==len(before['citations'])
        assert m.ordered(after['artwork_artists'])==m.ordered(before['artwork_artists'])
        assert m.ordered(after['curated_collection_items'])==m.ordered(before['curated_collection_items'])
        assert all(r in after['artwork_location_assertions']for r in before['artwork_location_assertions'])
        assert m.ordered(m.rows(db,'media_assets','id',[r['id']for r in extra['tables']['media_assets']]))==m.ordered(extra['tables']['media_assets'])
        m.audit(db,changes,OP)
        c.save(B/'transaction-after.json.gz',dict(at=c.now(),operation=OP,changes=changes,after=after))
    verify()


def verify():
    p=c.load(E/'artwork-five-fresh-preimages.json.gz');tx=c.load(B/'transaction-after.json.gz');changes=tx['changes']
    with c.connect()as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        after=snapshot(db,p)
        for t in after:assert m.ordered(after[t])==m.ordered(tx['after'][t]),('Independent postimage mismatch',t)
        aa=db.execute('SELECT id,before_json,after_json FROM audit_log WHERE id=ANY(%s::uuid[])',([m.uid(OP+'/'+r['table']+'/'+r['key'])for r in changes],)).fetchall()
        audits={str(r['id']):r for r in aa};assert len(audits)==len(changes)
        assert all(audits[m.uid(OP+'/'+r['table']+'/'+r['key'])]['before_json']==r['before']and audits[m.uid(OP+'/'+r['table']+'/'+r['key'])]['after_json']==r['after']for r in changes)
        search=db.execute('SELECT count(*)n FROM artworks a JOIN artwork_search_documents s ON s.id=a.id WHERE a.id=ANY(%s::uuid[])AND a.status=s.status AND a.primary_media_id IS NOT DISTINCT FROM s.primary_media_id',(p['ids'],)).fetchone()['n'];assert search==10
    s=requests.Session();public=[]
    for key,alias,canonical in p['pairs']:
        for i in [alias,canonical]:
            r=s.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/atlas/artworks/'+i,timeout=(10,35));assert r.status_code==200,(i,r.status_code)
            value=r.json();assert value['id']==canonical,(i,value.get('id'),canonical)
            public.append(dict(input_id=i,canonical_id=canonical,status=200))
    c.save(E/'artwork-five-verification.json',dict(at=c.now(),passed=True,merged_duplicate_artworks=5,canonical_artworks=5,changed_rows=len(changes),atomic_audits=len(audits),public_old_and_canonical_UUID_routes=len(public),all_existing_media_retained=True,all_native_identifiers_and_citations_retained=True,original_duplicate_rows_retained_archived=True,source_assertions_and_private_selections_preserved=True,search_documents=search,public=public))
    print('Five physical artwork duplicates merged, all original UUIDs/source identifiers/images retained and independently verified.',flush=True)


if __name__=='__main__':
    import sys
    globals()[sys.argv[1]]()
