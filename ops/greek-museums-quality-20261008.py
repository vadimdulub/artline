#!/usr/bin/env python3
"""Resolve visual-QA findings using native Greek labels and object-level locations."""
import importlib.util, json
from pathlib import Path
spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('greek-museums-delivery-20261008.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)


def main():
    p=d.load(d.RUN/d.PLAN);idx=d.load(d.RUN/'greek-contact-index-v2.json');facts={f['artwork_id']:f for f in p['records']}
    changes={};evidence={}
    for number in [91,148,382]:
        f=facts[idx[number-1]['artwork_id']];assert f['raw']['title']['gr']=='Ζεύγος χρυσών ενωτίων'
        assert any(x['gr']=='Χρυσός'for x in f['raw']['materials'])
        changes[f['artwork_id']]=dict(title='A pair of gold earrings',normalized_title='a pair of gold earrings')
        evidence[f['artwork_id']]=dict(source=f['receipt'],source_url=f['source_url'],reason='Native Greek title, gold material and detailed description match the photographed earrings. The supplied English bronze-bracelet title is a conflicting translation, retained in original source evidence and audit.',native_title=f['raw']['title'],old_code=f['raw']['oldCode'])
    for number in [118,135,140]:
        f=facts[idx[number-1]['artwork_id']];s,rc=d.g.page(f['native_url']);text=d.g.clean(s)
        changes[f['artwork_id']]=dict(creation_year_start=None,creation_year_end=None,date_precision='unknown',date_display='Creation date unverified')
        evidence[f['artwork_id']]=dict(source=rc,source_url=f['native_url'],original_date=f['date_display'],reason='Visual/source discrepancy: legacy 1905 calendar strings may be serialization artifacts; native object pages provide no creation date. No replacement year inferred. Images withheld under the museum-source creation cutoff.',source_text=text)
    branch=[f for f in p['records']if f.get('raw',{}).get('collection')=='DigVarnava'and f['raw']['fields'].get('CurrentLocation')==['Διαδραστικό Αγροτικό Λαογραφικό Μουσείο Βαρνάβα']]
    assert len(branch)==13
    native_url=facts[idx[135-1]['artwork_id']]['native_url'];s,rc=d.g.page(native_url);text=d.g.clean(s)
    assert 'Διαδραστικό Αγροτικό Λαογραφικό Μουσείο Βαρνάβα'in text and'Ανδρούτσου 7 Βαρνάβας'in text
    parent=next(f['museum']for f in branch);mu=dict(id=d.uid('institution/interactive-agricultural-folklore-varnavas'),slug='interactive-agricultural-folklore-museum-varnavas',
        name='Interactive Agricultural and Folklore Museum of Varnavas',normalized_name='interactive agricultural and folklore museum of varnavas',kind='museum',status='review',place_id=parent['place_id'],website_url=rc['final_url'])
    for f in branch:
        changes.setdefault(f['artwork_id'],{})['current_institution_id']=mu['id']
        evidence.setdefault(f['artwork_id'],dict(source=f['receipt'],source_url=f['source_url']))['holding_correction']=dict(native_label=f['raw']['fields']['CurrentLocation'][0],source=f['receipt'],institution_source=rc,
            reason='The provider operates two museums. Exact object-level CurrentLocation identifies the Interactive Agricultural and Folklore Museum, overriding the broad Bread Museum repository label. Holding only, no on-view claim.')
    with d.connect()as db:
        assert not db.execute('SELECT 1 FROM institutions WHERE id=%s OR normalized_name=%s',(mu['id'],mu['normalized_name'])).fetchone()
        before={x['artwork']['id']:x for x in d.full_rows(db,list(changes))}
    assert len(before)==len(changes)and all(x['artwork']['primary_media_id']is None and x['artwork']['status']=='review'for x in before.values())
    plan=dict(at=d.now(),new_museum=mu,changes=changes,before=before,evidence=evidence)
    d.save(d.RUN/'quality-correction-plan.json.gz',plan);d.save(d.BACKUP/'quality-correction-preimages.json.gz',plan)
    with d.connect(readonly=False)as db,db.transaction():
        d.m.insert(db,'institutions',mu);d.m.audit_entry(db,'institution',mu['id'],None,mu,'insert')
        d.m.insert(db,'citations',dict(entity_type='institution',entity_id=mu['id'],field_name='greek_museum_identity_20261008',source_id=d.uid('source'),source_url=native_url,
            evidence_note=json.dumps(dict(receipt=rc,native_name='Διαδραστικό Αγροτικό Λαογραφικό Μουσείο Βαρνάβα',address='Ανδρούτσου 7 Βαρνάβας',source_text=text),ensure_ascii=False),retrieved_at=rc['retrieved_at'],created_by=d.ACTOR))
        for aid,change in changes.items():
            w=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s FOR UPDATE',(aid,)).fetchone()['row'];assert w==before[aid]['artwork']
            if 'current_institution_id'in change:
                old=db.execute("SELECT to_jsonb(l) row FROM artwork_location_assertions l WHERE artwork_id=%s AND claim_type='holding'AND review_state='accepted'AND superseded_by IS NULL FOR UPDATE",(aid,)).fetchone()['row']
                assert old['institution_id']==parent['id'];ev=evidence[aid];lid=d.uid('quality-holding/'+aid)
                new=dict(id=lid,artwork_id=aid,claim_type='holding',institution_id=mu['id'],context='collection',source_id=d.uid('source'),source_url=ev['source_url'],evidence_note=json.dumps(ev['holding_correction'],ensure_ascii=False)+' Editorial confidence 0.98, not a calibrated probability.',checked_at=rc['retrieved_at'],review_state='review')
                d.m.insert(db,'artwork_location_assertions',new)
                db.execute('UPDATE artwork_location_assertions SET superseded_by=%s WHERE id=%s',(lid,old['id']))
                d.m.audit_entry(db,'artwork_location_assertion',old['id'],old,dict(old,superseded_by=lid),'update')
                db.execute("UPDATE artwork_location_assertions SET review_state='accepted'WHERE id=%s",(lid,));d.m.audit_entry(db,'artwork_location_assertion',lid,None,dict(new,review_state='accepted'),'insert')
            update={k:v for k,v in change.items()if k!='current_institution_id'};update['updated_by']=d.ACTOR
            db.execute(d.sql.SQL('UPDATE artworks SET {},revision=revision+1,updated_at=now() WHERE id=%s').format(d.sql.SQL(',').join(d.sql.SQL('{}=%s').format(d.sql.Identifier(k))for k in update)),list(update.values())+[aid])
            after=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s',(aid,)).fetchone()['row'];assert all(after[k]==v for k,v in change.items())
            assert after['status']=='review'and after['published_at']is None and after['primary_media_id']is None
            d.m.audit_entry(db,'artwork',aid,w,after,'update')
            ev=evidence[aid];d.m.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name='greek_source_quality_resolution_20261008',source_id=d.uid('source'),source_url=ev['source_url'],evidence_note=json.dumps(ev,ensure_ascii=False),retrieved_at=ev['source']['retrieved_at'],created_by=d.ACTOR))
        after=d.full_rows(db,list(changes));d.save(d.BACKUP/'quality-correction-after.json.gz',after)
    d.save(d.RUN/'quality-corrections-applied.json',dict(at=d.now(),new_museum=mu,changes=changes,evidence=evidence,after=after))
    print('Quality corrections: 3 native-title repairs; 3 unverified creation dates; 13 object-level holdings reconciled',flush=True)


if __name__=='__main__':main()
