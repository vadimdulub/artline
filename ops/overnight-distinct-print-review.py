#!/usr/bin/env python3
"""Fail-closed checks for separately accessioned museum print impressions.

Only an explicit source-backed review can resolve an artist/title collision.
Native identifiers, accessions and all other duplicate guards still apply.
"""
import collections,re,unicodedata
SCHEMES={'met-object':('the-met','met'),'european-met-the-met-object':('the-met','met'),'european-nga-object':('national-gallery-of-art','nga'),'mia-object':('minneapolis-institute-of-art','mia')}
SCHEMES.update({'cleveland-object':('cleveland-museum-of-art','cleveland'),'european-cleveland-cleveland-museum-of-art-object':('cleveland-museum-of-art','cleveland')})
SCHEMES.update({'smk-object':('statens-museum-for-kunst','smk'),'european-smk-statens-museum-for-kunst-object':('statens-museum-for-kunst','smk')})
def norm(value):return ' '.join(re.findall(r'\w+',unicodedata.normalize('NFKD',str(value or '')).casefold()))
def key(provider,oid):return provider+':'+str(oid)
def augment(db,records,state):
    if not any(c.get('physical_object_review') for c in records):return state
    title_keys={(p['id'],norm(c['title'])) for c in records for p in state['artists'].get(c['artist_qid'],[])}
    ids=[w['id'] for w in state['works'] if any((aid,norm(w['title'])) in title_keys for aid in w['artist_ids'])]
    mapped=collections.defaultdict(set)
    for start in range(0,len(ids),500):
        rows=db.execute("""SELECT a.id::text,a.accession_number,a.title,a.work_type,i.slug museum,e.scheme,e.external_id
          FROM artworks a JOIN institutions i ON i.id=a.current_institution_id
          JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id
          WHERE a.id=ANY(%s::uuid[]) AND e.scheme=ANY(%s)""",(ids[start:start+500],list(SCHEMES))).fetchall()
        for row in rows:
            museum,provider=SCHEMES[row['scheme']]
            if row['museum']==museum and row['work_type']=='print' and row['accession_number']:mapped[row['id']].add(key(provider,row['external_id']))
    state['review_native_keys']={aid:sorted(keys) for aid,keys in mapped.items()};return state
def allow(c,collisions,prior,state):
    review=c.get('physical_object_review')
    if c['work_type']!='print' or not review or review.get('decision')!='distinct_accessioned_prints':return False
    provider=SCHEMES.get(c.get('scheme'),('',None))[1]
    if provider not in ('mia','cleveland','smk') or c['provider']!={'mia':'night-mia','cleveland':'night-cleveland','smk':'night-smk'}[provider]:return False
    if review.get('candidate_key')!=key(provider,c['external_id']) or norm(review.get('candidate_accession'))!=norm(c['accession_number']):return False
    proofs={p['key']:p for p in review.get('objects',[])}
    for old in collisions:
        keys=state.get('review_native_keys',{}).get(old['id'],[])
        if len(keys)!=1 or keys[0] not in proofs:return False
        proof=proofs[keys[0]]
        if proof.get('object_type')!='print' or not proof.get('source_url') or not proof.get('source_capture_sha256'):return False
        if norm(old['title'])!=norm(proof['title']) or norm(old['accession_number'])!=norm(proof['accession_number']):return False
        if keys[0]==review['candidate_key']:return False
    for old in prior:
        # Both records were independently verified by the same museum adapter.
        proof=proofs.get(key(provider,old['external_id']))
        if old['provider']!=c['provider'] or old['work_type']!='print' or not proof:return False
        if norm(proof['accession_number'])!=norm(old['accession_number']) or norm(old['accession_number'])==norm(c['accession_number']):return False
    return True
