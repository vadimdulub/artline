#!/usr/bin/env python3
"""Review exact, referenced collection statements against existing production objects."""
import argparse,collections,gzip,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('all-museums-minimum-100-20261006.py'))
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
loc=c.module('minimum_wd_delivery','apply-artwork-locations-20261004.py')
ROOT=c.RUN/'links/wikidata-001'


def value(claim):return claim.get('mainsnak',{}).get('datavalue',{}).get('value')
def active(entity,prop):return [x for x in entity.get('claims',{}).get(prop,[])if x.get('rank')!='deprecated']


def allowed_qualifiers(claim,receipt):
    """Past acquisition start dates and inventory numbers do not end custody."""
    qs=claim.get('qualifiers',{})
    if not qs or set(qs)-{'P580','P217'}:return False
    for snak in qs.get('P217',[]):
        if snak.get('snaktype')!='value' or not isinstance(snak.get('datavalue',{}).get('value'),str):return False
    for snak in qs.get('P580',[]):
        v=snak.get('datavalue',{}).get('value',{});match=re.fullmatch(r'\+(\d{4})-\d\d-\d\dT00:00:00Z',v.get('time',''))
        if snak.get('snaktype')!='value' or not match or not 100<=int(match[1])<int(receipt['retrieved_at'][:4]) or v.get('precision',0)<9 or v.get('before')or v.get('after'):return False
    return True


def main(qualified=False,target_count=100,output_root=None):
    global ROOT
    if output_root is not None:ROOT=Path(output_root)
    elif qualified:ROOT=c.RUN/'links/wikidata-002'
    byq=collections.defaultdict(list)
    for row in c.BASE.values():
        if row['institution'].get('wikidata_id'):byq[row['institution']['wikidata_id']].append(row['institution'])
    entities={};held=[]
    for path in sorted((c.ROOT/'docs/research/artwork-locations-20261004/wikidata-batches').glob('*.json')):
        data=c.load(path);rc=data['receipt'];raw=gzip.decompress((c.ROOT/rc['body_path']).read_bytes())
        assert rc['status']==200 and c.d.sha(raw)==rc['sha256']
        actual=json.loads(raw)['entities'];assert actual==data['entities']
        for q,e in actual.items():
            claims=active(e,'P195')
            if not any(isinstance(value(x),dict)and value(x).get('id')in byq for x in claims):continue
            qualifier_ok=allowed_qualifiers(claims[0],rc)if len(claims)==1 and qualified else len(claims)==1 and not claims[0].get('qualifiers')
            if len(claims)!=1 or not qualifier_ok or not claims[0].get('references'):
                held.append(dict(qid=q,reason='collection_multiple_qualified_or_without_reference'));continue
            mq=value(claims[0])['id']
            if len(byq[mq])!=1:
                held.append(dict(qid=q,reason='duplicate_museum_qid'));continue
            refs=claims[0]['references']
            if not any(x.get('snaks',{}).get('P854')or x.get('snaks',{}).get('P248')for x in refs):
                held.append(dict(qid=q,reason='collection_reference_missing_source'));continue
            entities[q]=dict(entity=e,source_receipt=rc,museum=byq[mq][0],collection_statement=claims[0])
    print('Referenced', 'permitted-qualifier' if qualified else 'unqualified', 'exact collection candidates',len(entities),flush=True)
    baseline={};mapped=collections.defaultdict(list)
    with c.d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        for part in c.d.chunks(list(entities),500):
            for x in db.execute("SELECT e.external_id,a.id::text FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id WHERE e.entity_type='artwork'AND e.scheme='wikidata'AND e.external_id=ANY(%s)AND a.status<>'archived'AND a.current_institution_id IS NULL",(part,)):
                mapped[x['external_id']].append(x['id'])
        for part in c.d.chunks([i for ids in mapped.values()for i in ids],500):baseline.update(loc.snapshots(db,part))
        artistids=sorted({x['artist_id']for snap in baseline.values()for x in snap['creators']})
        aq={x['entity_id']:x['external_id']for x in db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artist'AND scheme='wikidata'AND entity_id=ANY(%s::uuid[])",(artistids,))}
        counts={x['museum']['id']:0 for x in entities.values()}
        for museums in c.d.chunks(list(counts),100):
            counts.update({x['id']:x['n']for x in db.execute("SELECT current_institution_id::text id,count(*)n FROM artworks WHERE current_institution_id=ANY(%s::uuid[])AND status<>'archived'GROUP BY current_institution_id",(museums,))})
        if qualified:
            pending={x['artwork_id']:x['institution']['id']for x in c.load(c.RUN/'links/wikidata-001/claims.json.gz')['claims']}
            for part in c.d.chunks(list(pending),500):
                for x in db.execute('SELECT id::text FROM artworks WHERE id=ANY(%s::uuid[])AND current_institution_id IS NULL',(part,)):
                    if pending[x['id']]in counts:counts[pending[x['id']]]+=1
    claims=[];outside=[]
    for q,ids in sorted(mapped.items()):
        proof=entities[q];e=proof['entity'];museum=proof['museum'];reason=None
        if len(ids)!=1:held.append(dict(qid=q,reason='duplicate_existing_object_qid'));continue
        aid=ids[0];snap=baseline[aid];art=snap['artwork']
        if any(x['claim_type']=='holding'and x['review_state']=='accepted'and not x['superseded_by']for x in snap['assertions']):continue
        names={c.norm(x['value'])for x in e.get('labels',{}).values()}|{c.norm(x['value'])for values in e.get('aliases',{}).values()for x in values}
        if not (({c.norm(art['title']),c.norm(art.get('alternate_title'))}-{''})&names):reason='native_title_identity_requires_review'
        creators=active(e,'P170');creator_ids={value(x).get('id')for x in creators if isinstance(value(x),dict)}
        known={aq.get(x['artist_id'])for x in snap['creators']}-{None}
        if not creators or any(x.get('qualifiers')for x in creators)or len(creator_ids)!=len(creators)or known!=creator_ids or any(x['artist_id']not in aq for x in snap['creators']):reason=reason or 'exact_creator_qid_requires_review'
        inventories={str(value(x))for x in active(e,'P217')if isinstance(value(x),str)}
        inventories.update(x['datavalue']['value']for x in proof['collection_statement'].get('qualifiers',{}).get('P217',[]))
        if art['accession_number']and inventories and not c.acc(art['accession_number'])&set().union(*(c.acc(v)for v in inventories)):reason=reason or 'inventory_conflict'
        if art['work_type']=='print':reason=reason or 'print_impression_requires_native_inventory'
        if reason:held.append(dict(artwork_id=aid,qid=q,reason=reason));continue
        if counts[museum['id']]>=target_count:outside.append(dict(artwork_id=aid,museum_id=museum['id'],reason='museum_already_at_'+str(target_count)+'_in_planned_wave'));continue
        counts[museum['id']]+=1;url='https://www.wikidata.org/wiki/'+q;rc=proof['source_receipt']
        claims.append(dict(artwork_id=aid,title=art['title'],scheme='wikidata',external_id=q,institution=museum,source_url=url,checked_at=rc['retrieved_at'],
            location_text=museum['name'],source_class='wikidata_referenced_collection_statement',source_receipt=rc,claim_type='holding',review_state='accepted',
            identity_basis='Exact existing artwork Wikidata ID and original title/alias, exact creator Wikidata identities, single non-deprecated referenced collection statement, exact unique existing museum Wikidata ID, no inventory conflict. Collection qualifiers are '+('limited to past acquisition start dates and literal inventory numbers; no end dates or other custody qualifiers.'if qualified else'absent.'),
            object_evidence=dict(**proof,editorial_confidence=0.85,confidence_basis='Concordant object, creator and museum authorities plus an explicit referenced collection statement. Editorial assessment, not calibrated probability.',referenced_documents_independently_opened=False),
            limitation='Secondary-source collection evidence, retained with the actual Wikidata statement and its references. Underlying referenced documents are not independently verified by this operation. Original retrieval date retained; no current display, fresh physical-location observation or legal-ownership claim. Existing dates, images, creators and publication state preserved.'))
    c.save(ROOT/'claims.json.gz',dict(at=c.d.now(),provider='wikidata-referenced-collection',claims=claims,held=held,outside_target=outside))
    c.save(ROOT/'baseline.json.gz',baseline)
    print('Ready links',len(claims),'museums',len({x['institution']['id']for x in claims}),'holds',dict(collections.Counter(x['reason']for x in held)),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--qualified',action='store_true');args=ap.parse_args();main(args.qualified)
