#!/usr/bin/env python3
"""Qualifiers and authority crosswalk validation over immutable museum captures."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('capture',Path(__file__).with_name('research-nationalmuseum-selected.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
x=c.x

def validate(code,number):
    delivery=x.BASE/code/f'round-{number:02d}'/'delivery';dest=delivery/'nationalmuseum-primary-v2-review.json'
    if dest.exists():return
    source=delivery/'nationalmuseum-primary-review.json';assert source.exists();out=[]
    for old in json.loads(source.read_text())['records']:
        e=dict(old);q=e['qid'];r=json.loads((delivery/'ready'/(q+'.json')).read_text())['record'];obj=e.get('object',{});makers=obj.get('makers',[])
        artists=[m for m in makers if m.get('RoleVoc',{}).get('LabelTxt')=='Artist'];others=[m for m in makers if m not in artists]
        names={x.r.norm(n) for n in x.r.labels(r['creator_entity'])};ids={str(v) for v in x.r.values(r['creator_entity'],'P2538')}
        exact=len(artists)==1 and (x.r.norm(re.sub(r'\s*\([^)]*\)\s*$','',artists[0].get('LinkLabelTxt',''))) in names or artists[0].get('ReferencedId') in ids)
        qualified=any(m.get('AttributionVoc',{}).get('LabelTxt') for m in artists)
        copy_roles=all(m.get('RoleVoc',{}).get('LabelTxt') in ('After','Copy after') for m in others)
        valid=bool(exact and not qualified and copy_roles and e.get('accession_match'))
        # Exact primary object ID + accession + maker authority are sufficient
        # even when the museum has not added a reciprocal Wikidata hyperlink.
        e['review']='primary_object_and_creator_corroborated' if valid else 'primary_review_required'
        e['creator_match']=bool(exact and not qualified and copy_roles)
        date=obj.get('date') or '';closed=not re.search(r'\b(?:after|before|since|until)\b',date,re.I)
        e['eligible_for_selected_image']=bool(valid and e.get('date_match') and closed and e.get('image_rights_corroborated') and not json.loads((delivery/'ready'/(q+'.json')).read_text())['image'])
        e['validation_v2']={'at':x.r.core.now(),'input_sha256':x.r.core.sha((delivery/'nationalmuseum-primary'/(q+'.json')).read_bytes()),'exact_maker_name_or_nationalmuseum_person_id':exact,'qualified_artist':qualified,'other_maker_roles_preserved':others,'closed_primary_date':closed,'rule':'Single unqualified maker; exact primary object accession and maker name/authority; copy-after relations preserved, not assigned as co-makers. No inference from a depicted person.'}
        x.save(delivery/'nationalmuseum-primary-v2'/(q+'.json'),e);out.append(e)
    x.save(dest,{'at':x.r.core.now(),'records':out,'counts':dict(collections.Counter(e['review'] for e in out))});print(code,number,'Nationalmuseum validated',len(out),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--country',required=True,choices=x.COUNTRIES);p.add_argument('--round',type=int,required=True);a=p.parse_args();validate(a.country,a.round)
