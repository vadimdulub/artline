#!/usr/bin/env python3
"""Pinned object reconciliation for the second low-count painter delivery."""
import collections
import copy
import importlib.util
import itertools
import json
import re
import uuid
from pathlib import Path

spec = importlib.util.spec_from_file_location('delivery', Path(__file__).with_name('low-count-200-painters-round2-20261009.py'))
x = importlib.util.module_from_spec(spec)
spec.loader.exec_module(x)


def build():
    assert not (x.RUN/'source-identity-review.json').exists()
    plans = list(x.deliveries())
    rows = {row['qid']:row for plan,pin in plans for row in plan['rows']}
    byid = {row['artwork_id']:row for row in rows.values()}
    plan_for = {row['qid']:(plan,pin) for plan,pin in plans for row in plan['rows']}
    held = {}; distinct = {}; notes = {}; groups_review = []

    def hold(qid, reason, existing=None):
        row=rows[qid]; plan,pin=plan_for[qid]
        held[qid]=dict(qid=qid, artwork_id=row['artwork_id'], artist_id=row['artist_id'], artist=plan['pair']['artist']['display_name'],
            original_plan_sha256=pin, source_url=row['source_url'], inventories=x.identity_inventories(row),
            reason=reason, existing=existing or [], already_added=(x.RUN/'applied'/(row['artist_id']+'.json')).exists())

    def source_summary(row):
        return dict(qid=row['qid'], title=row['title'], creator_qid=row['painter_qid'], institution_id=row['institution_id'],
            inventories=x.identity_inventories(row), native_urls=row['native_urls'], artuk=x.n.vals(row['source_evidence'],'P1679'),
            images=row['source_image_names'], receipt=row['receipt'])

    def waive(a,b,reason):
        for left,right in ((a,b),(b,a)):
            distinct[left['artwork_id'],right['artwork_id']]=dict(artwork_id=left['artwork_id'],existing_id=right['artwork_id'],reason=reason,
                left=source_summary(left),right=source_summary(right),expected_existing=dict(title=right['title'],
                    accession_number=right['work']['accession_number'],current_institution_id=right['institution_id'],artist_ids=right['artist_ids']))

    # Ten existing museum objects: retain their existing catalogue identities.
    details=x.r.load(x.RUN/'inventory-conflict-details.json')
    false_nga={'Q74065554','Q74065574','Q74065562'}
    for item in details:
        if item['reason']!='Existing institution inventory': continue
        row=rows[item['qid']]
        if item['qid'] in false_nga:
            for old in item['existing']:
                inv=x.identity_inventories(row)[0]; other=old['accession_number']
                assert x.d.acc(inv)==x.d.acc(other) and re.findall(r'\d+',inv)!=re.findall(r'\d+',other)
                distinct[row['artwork_id'],old['id']]=dict(artwork_id=row['artwork_id'],existing_id=old['id'],
                    reason='Distinct NGA accession segments: '+inv+' versus '+other+'. Different titled works and creators. Removing punctuation must not concatenate numeric segments into a false identity.',
                    left=source_summary(row),right=old,expected_existing=dict(title=old['title'],accession_number=other,
                        current_institution_id=old['current_institution_id'],artist_ids=[a['id'] for a in old['creators']]))
        else:
            hold(item['qid'],'Existing museum inventory and compatible object title; no new object counted.',[a['id'] for a in item['existing']])

    # Two earlier additions conflict with source inventories of existing works.
    # Titles differ, so do not claim proven duplicates or rewrite either source.
    for item in x.r.load(x.RUN/'already-imported-inventory-audit.json')['conflicts']:
        hold(item['qid'],'Unresolved repeated source inventory at the same museum with the same creator but different title. Archive only this operation\'s new record pending object reconciliation; preserve the pre-existing record.',item['existing'])

    # Equivalent source records in this delivery: retain the native museum
    # source entity, with the duplicate source and title preserved in this audit.
    duplicate_pairs=[
        ('Q27505803','Q23932064'),('Q119712477','Q106657348'),('Q119141805','Q99665977'),
        ('Q119796282','Q106657356'),('Q119796284','Q104975669'),('Q119138246','Q105367841'),
        ('Q119908671','Q106657666'),('Q119908332','Q105369506'),('Q131591029','Q47517453'),
        ('Q119137669','Q106657574'),('Q119835729','Q106657583'),('Q119122739','Q106657661'),
        ('Q27576227','Q23933031'),('Q27516879','Q27946686'),('Q119957003','Q98148624'),
        ('Q119956938','Q98149761'),('Q119085876','Q104975146')]
    for reject,keep in duplicate_pairs:
        a,b=rows[reject],rows[keep]
        assert a['artist_id']==b['artist_id'] and a['institution_id']==b['institution_id']
        assert {x.d.acc(v) for v in x.identity_inventories(a)} & {x.d.acc(v) for v in x.identity_inventories(b)}
        hold(reject,'Duplicate source entity for the same museum object: accession, creator and title/translation identify the retained object.',[b['artwork_id']])
        groups_review.append(dict(decision='one object',held=source_summary(a),retained=source_summary(b)))
    for qid in ['Q119693971','Q119693976','Q119700006','Q119699922','Q119699927']:
        hold(qid,'Different titles share the same source inventory without an explicit face or component distinction. Withhold all ambiguous candidates; do not invent object identity.')

    # Identical generic titles across creators: distinct museum inventories,
    # creator identities and source object entities, with no shared reproduction.
    title_groups=collections.defaultdict(dict)
    for row in rows.values():
        if row['qid'] in held: continue
        for title in row['title_aliases']:title_groups[row['institution_id'],x.d.norm(title)][row['artwork_id']]=row
    pairs={}
    for group in title_groups.values():
        for a,b in itertools.combinations(group.values(),2):
            if a['artist_id']!=b['artist_id']:pairs[tuple(sorted((a['artwork_id'],b['artwork_id'])))]=(a,b)
    for a,b in pairs.values():
        ia={x.d.acc(v) for v in x.identity_inventories(a)}; ib={x.d.acc(v) for v in x.identity_inventories(b)}
        assert ia and ib and not ia&ib and not set(a['source_image_names'])&set(b['source_image_names'])
        assert not set(x.n.vals(a['source_evidence'],'P1679'))&set(x.n.vals(b['source_evidence'],'P1679'))
        waive(a,b,'Separate museum objects despite a generic shared title: different inventory numbers and creators, distinct source object identifiers; no shared source reproduction.')

    # Visual inspection of the two public-domain Commons reproductions resolves
    # a shared inventory typo without inferring which number is correct.
    a,b=rows['Q119685077'],rows['Q119831401']
    evidence=x.r.load(x.RUN/'arbuckle-image-preview-receipts.json')
    reason='Separate portraits verified visually against the source-linked Commons reproductions: Crawford is a vertical portrait with a white lace shawl and fur, Walton is a horizontal seated portrait with a tan bonnet and shawl. Distinct Art UK source object identifiers, titles and creators agree. The duplicated A0617 inventory remains an unresolved source error; no replacement inventory is invented.'
    waive(a,b,reason)
    for row in [a,b]:notes[row['artwork_id']]=dict(note=reason,evidence=evidence,source_inventory_uncertain=True)

    # Review repeated within-batch inventories after equivalent entities have
    # been removed. Faces and individually numbered album compositions remain
    # distinct works, without claiming distinct physical supports.
    inv_groups=collections.defaultdict(dict)
    for row in rows.values():
        if row['qid'] in held:continue
        for inv in x.identity_inventories(row):inv_groups[row['institution_id'],x.d.acc(inv)][row['qid']]=row
    for key,group in inv_groups.items():
        if len(group)<2:continue
        vals=list(group.values())
        if set(group)=={'Q119685077','Q119831401'}:continue
        artuk=[x.n.vals(row['source_evidence'],'P1679') for row in vals]
        assert all(len(v)==1 for v in artuk) and len({v[0] for v in artuk})==len(vals)
        if len(vals)==68 and all(row['title'].startswith('Album: Copies of Old Masters and other Paintings (') for row in vals):
            assert len({row['title'] for row in vals})==68
            note='Individually catalogued compositions within William Nicholson\'s album, inventory 1994.154. Each has a distinct source object identifier and explicit page/composition title. Count selected compositions, not 68 separate albums or physical supports. Preserve detail/copy labels exactly.'
        else:
            assert len(vals)==2 and any('verso' in row['title'].lower() for row in vals)
            assert any('recto' in row['title'].lower() for row in vals) or set(group)=={'Q119332252','Q119795061'}
            note='Separately catalogued compositions on a shared support. Preserve the source\'s explicit verso/recto wording and distinct source object identifiers. Do not infer a face label for an unlabelled title or count separate physical supports.'
        record=dict(inventory_key=key,note=note,objects=[source_summary(row) for row in vals])
        groups_review.append(record)
        for row in vals:notes[row['artwork_id']]=dict(note=note,related_qids=sorted(group))

    # Replace the third duplicate Beatrix object with one independently reviewed
    # NGA drawing. "Late" remains qualitative; bounds cover the full century.
    selected, source_holds, _=x.source_rows({'Q64537174'})
    assert len(selected)==1 and not source_holds,source_holds
    row=selected[0];pair=row.pop('pair');aid=row['artist_id'];qid=row['qid']
    wid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://www.wikidata.org/entity/'+qid))
    row['artwork_id']=wid
    row['work']=dict(id=wid,slug='wikidata-'+qid.lower(),title=row['title'],alternate_title=None,normalized_title=x.q.norm(row['title']),
        date_display=row['date_display'],creation_year_start=row['first'],creation_year_end=row['last'],date_precision=row['precision'],
        work_type=row['work_type'],object_form=row['object_form'],medium_text=row['medium'],dimensions_text=row['dimensions'],accession_number=row['accession'])
    assert row['first']==1801 and row['last']==1900 and row['date_display']=='late 19th century'
    row['uncertainty'].append('The source says late 19th century. Indexed bounds retain the whole stated century; no exact lower bound for late is invented.')
    row['date_qualifier_review']=dict(property=x.r.load(x.RUN/'entities/date-review/P4241.json.gz'),
        refinement=x.r.load(x.RUN/'entities/date-review/Q40719766.json.gz'),
        native_verification=dict(url='https://www.nga.gov/artworks/11308-sheet-sketches-recto',method='web tool text inspection',
            source_title='Sheet of Sketches [recto]',creator='Beatrix Godwin Whistler',date='late 19th century',inventory='1943.3.8809.a',wikidata='Q64537174',
            access_note='Web tool returned the museum record. A subsequent direct archival capture returned 403 and was stopped; no bypass or direct HTML archive is claimed.'))
    supplements=[dict(artist_id=aid,row=row)]
    counts=[]
    for plan,pin in plans:
        aid=plan['pair']['artist']['id'];effective=[row for row in plan['rows'] if row['qid'] not in held]
        effective += [v['row'] for v in supplements if v['artist_id']==aid]
        x.validate_plan(dict(plan,rows=effective))
        counts.append(dict(artist_id=aid,artist=plan['pair']['artist']['display_name'],effective=len(effective)))
    review=dict(at=x.r.now(),held=list(held.values()),distinct_pairs=list(distinct.values()),groups_review=groups_review,row_notes=notes,supplements=supplements,counts=counts,
        qualification_review_sha256=x.r.sha((x.RUN/'source-qualification-review.json').read_bytes()),original_plan_pins={p['pair']['artist']['id']:pin for p,pin in plans},
        scope='Source identity amendments only. Original 200-painter cohort and plans preserved. No original catalogue records changed. Corrections archive only records created by this operation; no deletion.')
    x.r.save(x.RUN/'source-identity-review.json',review)
    print(json.dumps(dict(held=len(held),already_added=sum(v['already_added'] for v in held.values()),effective=sum(v['effective'] for v in counts),minimum=min(v['effective'] for v in counts),distinct_pairs=len(distinct))),flush=True)


def repair():
    path=x.RUN/'source-identity-review.json';review=x.r.load(path);digest=x.r.sha(path.read_bytes())
    selected=[v for v in review['held'] if v['already_added']];ids=[v['artwork_id'] for v in selected]
    marker=x.m.uid('object-identity-quality-correction');actor='local-european-research'
    with x.r.connect('production',readonly=False) as db:
        with db.transaction():
            db.execute('SELECT pg_advisory_xact_lock(2026100607)')
            prior=db.execute('SELECT after_json FROM audit_log WHERE id=%s',(marker,)).fetchone()
            if not prior:
                db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) FOR UPDATE',(ids,)).fetchall()
                before=x.s.snapshots(db,ids);assert len(before)==len(ids)
                x.r.save_gz(x.BACKUP/'identity-correction-before.json.gz',before)
                for item in selected:
                    state=before[item['artwork_id']]; receipt=x.r.load(x.RUN/'applied'/(item['artist_id']+'.json'))
                    assert item['artwork_id'] in receipt['new_ids'] and receipt['plan_sha256']==item['original_plan_sha256']
                    assert state['artwork']['status']=='review' and not state['attachments'] and state['artwork']['primary_media_id'] is None
                    db.execute('UPDATE artworks SET status=%s,description_md=%s,updated_by=%s WHERE id=%s',('archived',item['reason']+' Reconciliation evidence: '+str(path.relative_to(x.ROOT)),actor,item['artwork_id']))
                result=dict(at=x.r.now(),review_sha256=digest,artwork_ids=ids,own_new_records_archived=len(ids),original_catalogue_records_changed=0,deleted_records=0)
                db.execute("INSERT INTO audit_log(id,actor_user_id,action,entity_type,entity_id,before_json,after_json) VALUES(%s,%s,'new_object_identity_correction','artwork',%s,%s,%s)",(marker,actor,ids[0],x.m.Jsonb(before),x.m.Jsonb(dict(result,decisions=selected))))
            else:
                result=prior['after_json'];result.pop('decisions',None)
                assert result['review_sha256']==digest and result['artwork_ids']==ids
        after=x.s.snapshots(db,ids)
        assert all(v['artwork']['status']=='archived' and not v['attachments'] for v in after.values())
    x.r.save_gz(x.BACKUP/'identity-correction-after.json.gz',after)
    x.r.save(x.RUN/'identity-correction.json',result)
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    import sys
    {'build':build,'repair':repair}[sys.argv[1]]()
