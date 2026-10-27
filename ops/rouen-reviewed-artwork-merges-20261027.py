"""Four exact Rouen inventory identities; preserve source disagreements and files."""
import importlib.util
import sys
from pathlib import Path
import requests
import exhibitions_common as c

s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('catalogue-reviewed-artwork-merges-20261027.py'))
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
m=a.m;E=a.E;B=m.B/'rouen-artworks';OP=m.OP+'-rouen-artworks-four'


def apply():
    assert c.load(E/'identity-deployment-verification.json')['passed']
    p=c.load(E/'rouen-four-fresh-preimages.json.gz');before=p['tables'];works={r['id']:r for r in before['artworks']}
    assert len(p['pairs'])==4 and len(works)==8 and not p['possible_references']
    mapping={x:y for k,x,y in p['pairs']}
    assert all(r['artwork_id']not in mapping for r in p['artist_key_artworks'])
    native={'blanche':('07290023052','1930.1.2'),'poussin':('000PE032619','975.1'),'robert':('000PE032681','SR 62'),'monet':('07290021551','909.1.33')}
    decisions=[]
    research=c.load(E/'rouen-five-identity-research.json.gz')
    for key,old,new in p['pairs']:
        x,y=works[old],works[new]
        assert x['status']!='archived' and y['status']!='archived'
        assert x['current_institution_id']==y['current_institution_id']=='f92766ec-41cf-42d1-9bb1-f333fe5d2980'
        left={(r['artist_id'],r['attribution_role'])for r in before['artwork_artists']if r['artwork_id']==old}
        right={(r['artist_id'],r['attribution_role'])for r in before['artwork_artists']if r['artwork_id']==new}
        assert left==right and len(left)==1
        ref,inv=native[key]
        if key!='monet':
            notice=c.load(m.D/'rouen-notices'/(ref+'.json.gz'))
            assert c.norm(notice['fields']["Numéro d'inventaire"])==c.norm(inv)
        assert any(c.norm(w['accession_number'])==c.norm(inv)for w in [x,y])
        assert any(r.get('source_record_id')==ref and r['entity_id']in[old,new]for r in research['citations']) or key=='monet'
        decisions.append(dict(key=key,alias=old,canonical=new,native_id=ref,accession=inv,
                              basis={'blanche':'Exact1930.1.2, Paul Valéry, same Jacques-Emile Blanche. Keep illustrated representative canonical and its supported1923 year; retain native full1923/02/02 and prior unverified parsing in citations/original row.',
                                     'poussin':'Exact975.1 and same Poussin. Official L’Orage and native Landscape with lightning-struck tree are the same circa1651 canvas, distinct from its calm-weather pendant.',
                                     'robert':'ExactSR62 and same Hubert Robert. This single canvas belongs to a dispersed decorative programme; SR63–65 stay distinct. Museum1773 and native circa1775/1773-or1775 remain separately preserved.',
                                     'monet':'Exact909.1.33,1894, Claude Monet, Seine at Port-Villez; native alternate Brume sur la Seine retained. Previously detached image/crop hold stays detached.'}[key]))
    for t in ['member_artwork_bookmarks','exhibition_entries','exhibition_objects','research_artwork_enrichments','artwork_places','curated_collection_items']:
        assert not before[t],('Unreviewed references',t)
    assert all(r['artwork_id']not in mapping for r in before['research_resolutions'])
    assert all(not r['possible_artwork_ids']for r in before['research_artwork_links'])
    B.mkdir(parents=True,exist_ok=True);B.chmod(0o700)
    c.save(B/'identity-decisions.json',dict(at=c.now(),decisions=decisions,
        source_urls=['https://mbarouen.fr/fr/oeuvres/l-orage-0','https://mbarouen.fr/fr/oeuvres/monuments-et-ruines-a-la-colonne','https://mbarouen.fr/fr/oeuvres/la-seine-a-port-villez','https://pop.culture.gouv.fr/notice/joconde/07290023052'],
        hagborg_hold='1911.6 physical identity likely exact, but linked artist profiles conflict: native1852–1925 versus Nationalmuseum7459 authority1852–1921. No joint-maker invention or person merge.'))
    changes=[]
    with c.connect(write=True)as db:
        m.acquire_locks(db)
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',(p['ids'],)).fetchall()
        actual=a.snapshot(db,p)
        for t in before:assert m.ordered(actual[t])==m.ordered(before[t]),('Changed preimage',t)
        assert m.ordered(m.rows(db,'artist_key_artworks','artwork_id',p['ids']))==m.ordered(p['artist_key_artworks'])
        assert not db.execute('SELECT 1 FROM research_artwork_links WHERE possible_artwork_ids && %s::uuid[] LIMIT 1',(p['ids'],)).fetchone()
        c.save(B/'locked-before.json.gz',dict(at=c.now(),plan=p,decisions=decisions))
        for old in before['artwork_location_assertions']:
            if old['artwork_id']not in mapping:continue
            target=mapping[old['artwork_id']];clone=dict(old,id=m.uid(OP+'/holding/'+old['id']),artwork_id=target);clone.pop('created_at')
            accepted=[r for r in before['artwork_location_assertions']if r['artwork_id']==target and r['claim_type']=='holding'and r['review_state']=='accepted'and r['superseded_by']is None]
            if old['claim_type']=='holding'and old['review_state']=='accepted'and old['superseded_by']is None and accepted:
                assert len(accepted)==1 and accepted[0]['institution_id']==old['institution_id'];clone['superseded_by']=accepted[0]['id']
            clone['evidence_note']=(old['evidence_note']or'')+'\nCanonical evidence copy. Immutable original '+old['id']+' retained. '+OP
            fields=list(clone);new=db.execute('INSERT INTO artwork_location_assertions('+','.join(fields)+')VALUES('+','.join(['%s']*len(fields))+')RETURNING to_jsonb(artwork_location_assertions)v',[clone[k]for k in fields]).fetchone()['v']
            changes.append(dict(table='artwork_location_assertions',key=new['id'],before=None,after=new))
        for t,col in [('external_identifiers','entity_id'),('citations','entity_id')]:
            for old in before[t]:
                if old[col]not in mapping:continue
                new=db.execute('UPDATE '+t+' SET '+col+'=%s WHERE id=%s RETURNING to_jsonb('+t+')v',(mapping[old[col]],old['id'])).fetchone()['v']
                assert all(new[k]==v for k,v in old.items()if k!=col)
                changes.append(dict(table=t,key=old['id'],before=old,after=new))
        for old in before['research_artwork_links']:
            if old['artwork_id']not in mapping:continue
            key='/'.join(old[k]for k in ['source_key','record_kind','research_record_id'])
            new=db.execute('UPDATE research_artwork_links SET artwork_id=%s WHERE source_key=%s AND record_kind=%s AND research_record_id=%s RETURNING to_jsonb(research_artwork_links)v',(mapping[old['artwork_id']],old['source_key'],old['record_kind'],old['research_record_id'])).fetchone()['v']
            assert all(new[k]==v for k,v in old.items()if k!='artwork_id')
            changes.append(dict(table='research_artwork_links',key=key,entity_id=new['artwork_id'],before=old,after=new))
        for key,alias,canonical in p['pairs']:
            x,y=works[alias],works[canonical]
            assert not x['primary_media_id'],'Unexpected old image needs attachment reconciliation'
            old=db.execute("UPDATE artworks SET status='archived',current_institution_id=%s,updated_at=now(),updated_by=%s,revision=revision+1 WHERE id=%s RETURNING to_jsonb(artworks)v",(x['current_institution_id'],m.EDITOR,alias)).fetchone()['v']
            new=db.execute('UPDATE artworks SET current_institution_id=%s,updated_at=now(),updated_by=%s,revision=revision+1 WHERE id=%s RETURNING to_jsonb(artworks)v',(y['current_institution_id'],m.EDITOR,canonical)).fetchone()['v']
            for original,current,allowed in [(x,old,{'status','updated_at','updated_by','revision'}),(y,new,{'updated_at','updated_by','revision'})]:
                assert all(current[k]==v for k,v in original.items()if k not in allowed)
                changes.append(dict(table='artworks',key=original['id'],before=original,after=current))
            redirect=db.execute("INSERT INTO slug_redirects(id,entity_type,entity_id,old_slug)VALUES(%s,'artwork',%s,%s)RETURNING to_jsonb(slug_redirects)v",(m.uid(OP+'/redirect/'+alias),canonical,x['slug'])).fetchone()['v']
            changes.append(dict(table='slug_redirects',key=redirect['id'],before=None,after=redirect))
        after=a.snapshot(db,p)
        for t in ['artwork_artists','artwork_media','research_resolutions']:
            assert m.ordered(after[t])==m.ordered(before[t])
        assert all(r in after['artwork_location_assertions']for r in before['artwork_location_assertions'])
        assert m.ordered(m.rows(db,'media_assets','id',[r['id']for r in p['media_assets']]))==m.ordered(p['media_assets'])
        assert len(after['external_identifiers'])==len(before['external_identifiers'])and len(after['citations'])==len(before['citations'])
        m.audit(db,changes,OP)
        c.save(B/'transaction-after.json.gz',dict(at=c.now(),operation=OP,changes=changes,after=after))
    verify()


def verify():
    p=c.load(E/'rouen-four-fresh-preimages.json.gz');tx=c.load(B/'transaction-after.json.gz')
    with c.connect()as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
        actual=a.snapshot(db,p)
        assert all(m.ordered(actual[t])==m.ordered(tx['after'][t])for t in actual)
        ids=[m.uid(OP+'/'+r['table']+'/'+r['key'])for r in tx['changes']]
        audits={str(r['id']):r for r in db.execute('SELECT id,before_json,after_json FROM audit_log WHERE id=ANY(%s::uuid[])',(ids,))}
        assert len(audits)==len(tx['changes'])
        assert all(audits[i]['before_json']==r['before']and audits[i]['after_json']==r['after']for i,r in zip(ids,tx['changes']))
        assert m.ordered(m.rows(db,'artist_key_artworks','artwork_id',p['ids']))==m.ordered(p['artist_key_artworks'])
        assert m.ordered(m.rows(db,'media_assets','id',[r['id']for r in p['media_assets']]))==m.ordered(p['media_assets'])
    out=[];session=requests.Session()
    for key,old,new in p['pairs']:
        for incoming in [old,new]:
            r=session.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/atlas/artworks/'+incoming,timeout=(10,35))
            assert r.status_code==200 and r.json()['id']==new,(incoming,r.status_code)
            out.append(dict(input_id=incoming,canonical_id=new,status=200))
    c.save(E/'rouen-four-artwork-verification.json',dict(at=c.now(),passed=True,merged_duplicate_artworks=4,atomic_audits=len(audits),changed_rows=len(tx['changes']),public=out,all_existing_images_creators_private_selections_source_dates_and_assertions_preserved=True))
    print('Four exact Rouen artwork identities merged and independently verified.',flush=True)


if __name__=='__main__':globals()[sys.argv[1]]()
