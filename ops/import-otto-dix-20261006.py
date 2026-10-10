#!/usr/bin/env python3
"""Pinned Otto Dix research import. Production only; never publishes records.

The default plan is read-only. Image delivery is a separate operation because
territorial PD and Fair Use labels do not establish unrestricted clearance.
"""
import argparse
import collections
import csv
import gzip
import html
import importlib.util
import json
from pathlib import Path
import re
import uuid

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('wikiart_research', ROOT/'ops/research-production-wikiart-images-20261006.py')
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)
r = q.r
OP = 'otto-dix-20261006'
RUN = ROOT/'docs/research'/OP
BACKUP = Path.home()/'Library/Application Support/Artline/backups'/OP
q.RUN = r.RUN = RUN
r.PORT = 55449
ACTOR = 'local-european-research'
ARTIST = '7d59e68f-9b32-49fc-9e1f-c16456d97267'
COLLECTION = '42c83e94-d1f2-539a-accb-b4e9ded61f06'


def uid(value):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, OP+'/'+value))


def current(db, ids):
    rows = db.execute('''SELECT to_jsonb(a) artwork,
      COALESCE((SELECT jsonb_agg(to_jsonb(aa) ORDER BY artist_id,attribution_role)
        FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') creators
      FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''', (ids,)).fetchall()
    return {x['artwork']['id']: x for x in rows}


def plan():
    pages = r.load(RUN/'wikiart-pages.json')
    baseline = r.load(RUN/'production-baseline.json')
    assert len(pages) == 129 and len(baseline['artists']) == 1
    assert baseline['artists'][0]['record']['id'] == ARTIST
    old = baseline['works']
    held = {
        13: 'Apotheosis may represent the same design as the accessioned NGA woodcut Apotheosa; exact impression/version unresolved.',
        49: 'Alternate Shock Troops source page may depict the same design as existing Stormtroops; retain without a duplicate import pending version review.',
        84: 'Weimar Berlin may be a panel/detail of Metropolis; composition review required before creating an independent artwork.',
        109: 'Second Sunrise page now dates the work 1913; probable duplicate of the other Sunrise entry.',
        113: 'Lustmurder may be related to existing Lust Murder I; undated source needs medium/version reconciliation.',
        115: 'Second Pregnant Woman is undated; reconcile against the 1919 entry before creating a second work.',
        120: 'Sex Murder may be a translated title or separate version of Lustmurder; identity unresolved.',
        127: 'Two undated Trenches entries require composition/version review.',
        128: 'Two undated Trenches entries require composition/version review.',
    }
    rows = []
    for n, record in enumerate(pages):
        assert record['outcome'] == 'captured'
        p = record['page']; meta = p['metadata']
        assert meta['artistUrl'] == '/en/otto-dix' and meta['artistName'] == 'Otto Dix'
        body = gzip.decompress((ROOT/p['receipt']['body_path']).read_bytes())
        assert r.sha(body) == p['receipt']['sha256']
        soup = q.BeautifulSoup(body, 'html.parser')
        rights = soup.select_one('.copyright-wrapper').get_text(' ', strip=True)
        title = html.unescape(meta['title'])
        row = {'index': n, 'page': p, 'title': title, 'source_id': meta['_id'],
               'source_url': p['url'], 'source_rights_label': rights,
               'rights_status': 'restricted', 'image_decision': 'pending_explicit_policy_choice'}
        if n in held:
            row.update(action='hold', reason=held[n]); rows.append(row); continue
        names = {q.norm(title), q.norm(p['fields'].get('Original Title'))} - {''}
        direct = [w for w in old if any(e.get('canonical_url') == p['url'] or
                  (e['scheme'] == 'wikiart-artwork' and e['external_id'] == meta['_id']) for e in w['identifiers'])]
        exact = [w for w in old if names & {q.norm(w['artwork']['title']), q.norm(w['artwork'].get('alternate_title'))}
                 and p['date'] and w['artwork']['creation_year_start'] is not None
                 and w['artwork']['creation_year_end'] is not None
                 and max(p['date'][0],w['artwork']['creation_year_start']) <= min(p['date'][1],w['artwork']['creation_year_end'])]
        matches = direct or exact
        assert len(matches) <= 1, 'Ambiguous target identity'
        if matches:
            w = matches[0]
            assert w['creators'] == [dict(w['creators'][0])] and w['creators'][0]['artist_id'] == ARTIST
            assert w['creators'][0]['attribution_role'] == 'primary'
            row.update(action='existing', artwork_id=w['artwork']['id'],
                       has_image=bool(w['artwork']['primary_media_id']),
                       identity_basis='Existing direct WikiArt identity' if direct else 'Unique exact title, creator, date and consistent source museum',
                       confidence=0.99 if direct else 0.98)
        else:
            date = p['date']
            assert date is None or date[1] <= 1970
            aid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://www.wikiart.org/artwork/'+meta['_id']))
            medium = p['fields'].get('Media')
            # Explicit material/technique only; WikiArt genre labels are not object types.
            kind = 'unknown'
            if medium:
                if re.search(r'\b(etching|aquatint|drypoint|woodcut|lithograph)\b',medium): kind='print'
                elif re.search(r'\boil\b',medium): kind='painting'
                elif re.search(r'\bwatercolor\b',medium): kind='watercolor'
            work = dict(id=aid, slug='wikiart-'+meta['_id'], title=title,
                        alternate_title=p['fields'].get('Original Title'), normalized_title=q.norm(title),
                        creation_year_start=date[0] if date else None,
                        creation_year_end=date[1] if date else None,
                        date_display=meta['year'] if date else 'Unknown date',
                        date_precision=('exact' if date[0]==date[1] else 'range') if date else 'unknown',
                        work_type=kind, medium_text=medium, dimensions_text=p['fields'].get('Dimensions'))
            row.update(action='create', artwork_id=aid, work=work, confidence=0.99,
                       identity_basis='Distinct source record on the exact Otto Dix artwork page and complete artist index')
            if n == 122:
                row['identity_basis'] += '; Turin source differs from the existing accessioned Chicago lithograph The Sailor; unknown date preserved'
        rows.append(row)
    links = []
    for row in r.load(RUN/'unlinked-dix-records.json'):
        c = next(x for x in row['citations'] if x['field_name']=='museum_holding_research')
        note = json.loads(c['evidence_note'])
        raw = gzip.decompress((ROOT/note['evidence_path']).read_bytes())
        assert r.sha(raw)==note['source_response_sha256']
        payload = json.loads(raw)
        records = payload['data']
        source = next(x for x in records if x['Reference']==note['object_id'])
        links.append({'artwork_id':row['artwork']['id'],'source':source,'citation':c,
                      'reason':'Official Joconde object identifies Dix Otto. Link creator only; retain the original object label, unknown fields and custody review.'})
    ids = [w['artwork']['id'] for w in old] + [x['artwork_id'] for x in links]
    newids = [x['artwork_id'] for x in rows if x['action']=='create']
    with r.connect('production') as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        before = current(db,ids)
        assert len(before)==len(ids)
        for w in old:
            assert before[w['artwork']['id']]['artwork']==w['artwork']
        assert not current(db,newids), 'Proposed artwork ID already exists'
        conflicts = db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikiart-artwork' AND external_id=ANY(%s)",
                               ([x['source_id'] for x in rows if x['action']=='create'],)).fetchall()
        assert not conflicts, 'Source identity exists outside scoped painter records'
        artist = db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s',(ARTIST,)).fetchone()['record']
        collection = db.execute('SELECT to_jsonb(c) record FROM curated_collections c WHERE id=%s',(COLLECTION,)).fetchone()['record']
        assert collection['curator_kind']=='owner' and collection['institution_id'] is None and collection['status']=='review'
        query='SELECT a.id FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s'
        query_plan=db.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+query,(ARTIST,)).fetchone()
    data={'operation':OP,'artist_id':ARTIST,'source_id':uid('source/wikiart'),'joconde_source_id':uid('source/joconde'),
          'rows':rows,'creator_links':links,'before':before,'artist_before':artist,
          'scope':'User-requested Otto Dix research selection. New records remain review; no accepted holding/display/publication inferred.',
          'counts':dict(collections.Counter(x['action'] for x in rows)),
          'unknown_date_new':sum(x['action']=='create' and x['work']['date_precision']=='unknown' for x in rows)}
    r.save(RUN/'metadata-plan.json',data)
    digest=r.sha((RUN/'metadata-plan.json').read_bytes())
    r.save(RUN/'metadata-plan-pin.json',{'sha256':digest})
    r.save(BACKUP/'metadata-preimages.json',{'plan_sha256':digest,'records':before,'artist':artist,'collection':collection})
    r.save(RUN/'painter-query-plan.json',query_plan)
    fields=['index','title','source_url','source_rights_label','action','artwork_id','reason']
    with (RUN/'wikiart-import-review.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    print(json.dumps({'counts':data['counts'],'unknown_date_new':data['unknown_date_new'],'creator_links':len(links),'plan_sha256':digest}))


def pinned():
    raw=(RUN/'metadata-plan.json').read_bytes();pin=r.load(RUN/'metadata-plan-pin.json')['sha256']
    assert r.sha(raw)==pin
    assert r.load(BACKUP/'metadata-preimages.json')['plan_sha256']==pin
    return json.loads(raw),pin


def apply():
    data,pin=pinned()
    assert not (RUN/'metadata-applied.json').exists(), 'Already applied; use verify'
    assert r.load(BACKUP/'cloud-backup.json')['status']=='SUCCESSFUL', 'Successful recovery backup required'
    for link in data['creator_links']:
        assert link['source']['Auteur']=='Dix Otto'
        assert '1891' in link['source']['Precisions_sur_l_auteur'] and '1969' in link['source']['Precisions_sur_l_auteur']
        assert q.norm(link['source']['Titre'])==q.norm(data['before'][link['artwork_id']]['artwork']['title'])
        assert not data['before'][link['artwork_id']]['creators']
    with r.connect('production',readonly=False) as db, db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute('SELECT pg_advisory_xact_lock(2026100607)')
        ids=list(data['before'])
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
        assert current(db,ids)==data['before'], 'Target changed after preflight'
        assert db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s FOR SHARE',(ARTIST,)).fetchone()['record']==data['artist_before']
        db.execute('SELECT id FROM curated_collections WHERE id=%s FOR UPDATE',(COLLECTION,))
        pos=db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s',(COLLECTION,)).fetchone()['n']
        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page','https://www.wikiart.org/')",
                   (data['source_id'],OP+'-wikiart','WikiArt Otto Dix research selection, 6 October 2026'))
        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page','https://pop.culture.gouv.fr/')",
                   (data['joconde_source_id'],OP+'-joconde','Joconde Otto Dix creator reconciliation, 6 October 2026'))
        for row in data['rows']:
            if row['action']=='hold':continue
            aid=row['artwork_id'];p=row['page']
            if row['action']=='create':
                w=row['work'];keys=['id','slug','title','alternate_title','normalized_title','date_display','creation_year_start','creation_year_end','date_precision','work_type','medium_text','dimensions_text']
                db.execute('''INSERT INTO artworks(id,slug,title,alternate_title,normalized_title,date_display,creation_year_start,
                  creation_year_end,date_precision,work_type,medium_text,dimensions_text,status,research_candidate,created_by,updated_by)
                  VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)''',tuple(w[k] for k in keys)+(ACTOR,ACTOR))
                db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",
                           (aid,ARTIST,'WikiArt explicitly identifies Otto Dix on the artwork page and artist index; retained as a review record.'))
                pos+=1
                db.execute('''INSERT INTO curated_collection_items(id,collection_id,artwork_id,position,reason,source_id,source_url,checked_at)
                  VALUES(%s,%s,%s,%s,%s,%s,%s,%s)''',(uid('selection/'+aid),COLLECTION,aid,pos,
                  'Personal Otto Dix research selection requested 6 October 2026. Not a museum masterpiece designation; unknown dates require review.',data['source_id'],p['url'],p['receipt']['retrieved_at']))
            exists=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikiart-artwork' AND external_id=%s",(row['source_id'],)).fetchall()
            if exists:assert exists==[{'entity_id':aid}]
            else:db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'wikiart-artwork',%s,%s,%s,%s)",
                            (aid,row['source_id'],p['url'],data['source_id'],p['receipt']['retrieved_at']))
            note=json.dumps({'plan_sha256':pin,'page':p,'rights_label':row['source_rights_label'],'identity_basis':row['identity_basis'],
                             'confidence':row['confidence'],'scope':data['scope'],'image_delivery':'Separate pending policy decision'},ensure_ascii=False)
            db.execute('''INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
              VALUES(%s,'artwork',%s,%s,'otto_dix_source_identity',%s,%s,%s,%s,%s)''',
              (uid('citation/'+row['source_id']),aid,data['source_id'],row['source_id'],p['url'],note,p['receipt']['retrieved_at'],ACTOR))
        for link in data['creator_links']:
            aid=link['artwork_id'];c=link['citation']
            db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",(aid,ARTIST,link['reason']))
            db.execute('UPDATE artworks SET revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s',(ACTOR,aid))
            db.execute('''INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
              VALUES(%s,'artwork',%s,%s,'otto_dix_creator_identity',%s,%s,%s,%s,%s)''',
              (uid('creator-citation/'+aid),aid,data['joconde_source_id'],link['source']['Reference'],c['source_url'],
               json.dumps({'plan_sha256':pin,'source':link['source'],'prior_citation':c,'scope':link['reason']},ensure_ascii=False),c['retrieved_at'],ACTOR))
        db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(COLLECTION,))
        newids=[x['artwork_id'] for x in data['rows'] if x['action']=='create']
        after=current(db,ids+newids)
        linkids={x['artwork_id'] for x in data['creator_links']}
        for aid,before in data['before'].items():
            if aid not in linkids:assert after[aid]==before
            else:
                allowed={'revision','updated_at','updated_by'}
                assert {k:v for k,v in before['artwork'].items() if k not in allowed}=={k:v for k,v in after[aid]['artwork'].items() if k not in allowed}
                assert len(after[aid]['creators'])==1 and after[aid]['creators'][0]['artist_id']==ARTIST
        for aid in newids:
            a=after[aid]['artwork']
            assert a['status']=='review' and a['published_at'] is None and a['current_institution_id'] is None and a['primary_media_id'] is None
        assert not db.execute("SELECT id FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[])",(newids,)).fetchall()
    r.save(BACKUP/'metadata-after.json',after)
    r.save(RUN/'metadata-applied.json',{'at':r.now(),'plan_sha256':pin,'created':len(newids),'creator_links_added':len(linkids),
       'new_artwork_ids':newids,'local_database_changed':False,'publication_changed':False})
    print('Committed production review metadata',len(newids),'new works;',len(linkids),'existing creator links')


def verify():
    data,pin=pinned();applied=r.load(RUN/'metadata-applied.json')
    assert applied['plan_sha256']==pin
    expected=r.load(BACKUP/'metadata-after.json')
    with r.connect('production') as db:
        assert current(db,list(expected))==expected
        rows=db.execute('''SELECT a.id::text,a.title,a.status,a.published_at,a.primary_media_id::text,
          artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) creation_scope,
          artline_has_selection_evidence(a.id) selected FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
          WHERE aa.artist_id=%s ORDER BY a.title,a.id''',(ARTIST,)).fetchall()
        citations=db.execute('SELECT count(*) n FROM citations WHERE source_id=ANY(%s::uuid[])',([data['source_id'],data['joconde_source_id']],)).fetchone()['n']
    r.save(RUN/'metadata-verification.json',{'at':r.now(),'plan_sha256':pin,'rows':rows,'citations':citations,'errors':[]})
    print(json.dumps({'production_otto_dix_records':len(rows),'images':sum(bool(x['primary_media_id']) for x in rows),'citations':citations,'errors':0}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['plan','apply','verify']);args=parser.parse_args()
    globals()[args.phase]()
