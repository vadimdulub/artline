#!/usr/bin/env python3
"""Exact Moronobu photograph using reviewed Getty and LoC creator authorities."""
import argparse
import importlib.util
import json
from pathlib import Path

s=importlib.util.spec_from_file_location('reviewed',Path(__file__).with_name('recover-local-chicago-reviewed-authorities-20261006.py'))
reviewed=importlib.util.module_from_spec(s);s.loader.exec_module(reviewed)
native,base,core=reviewed.native,reviewed.base,reviewed.core
RUN=core.ROOT/'docs/research/local-chicago-moronobu-image-20261006'
reviewed.RUN=native.RUN=base.RUN=RUN
AID='6718fc3e-8b27-4beb-9b22-259764bd447e'
ARTIST='a652bc8a-bd63-471f-b81d-846a7dbd1990'
QID='Q746217';ULAN='500118854';LCCN='n80040691'
core.VERSION='local-chicago-moronobu-getty-loc-identity-review-v1'
reviewed.BASIS='Exact existing Chicago artwork 130211 and inventory 1973.645.2; existing creator Q746217 explicitly links Chicago artist 35839, Getty ULAN 500118854 and LoC n80040691. Fresh independent Getty and LoC authorities corroborate the same creator and cross-reference one another. Differing birth-date assertions and the native unknown-birth marker are retained as biography uncertainty, without changing artist fields or creator links. Exact photograph-specific native CC0 grant separately verified; image-only local attachment preserves catalogue dates, holdings and review status.'


def captured(path,receipt,url):
    data=path.read_bytes()
    if json.loads(path.with_suffix('.receipt.json').read_bytes())!=receipt or receipt['url']!=url or core.sha(data)!=receipt['sha256'] or len(data)!=receipt['bytes']:
        raise ValueError('Pinned independent creator capture differs')
    return json.loads(data)


def review(c,o,person):
    rows=json.loads((RUN/'creator-identity-review.json').read_bytes())['images']
    if len(rows)!=1 or rows[0]['artwork_id']!=AID or rows[0]['decision']!='approved':raise ValueError('Individual Moronobu review absent')
    d=rows[0]
    if c['artwork_id']!=AID or c['external_id']!='130211' or c['roles']!=['primary'] or len(c['creator_links'])!=1 or len(c['creator_authorities'])!=1:
        raise ValueError('Exact existing object or unique primary creator differs')
    proof=c['creator_authorities'][0];ar=proof['artist_record']
    if ar['id']!=ARTIST or c['creator_links'][0]['artist_id']!=ARTIST or d['local_artist_id']!=ARTIST or d['existing_qid']!=QID:
        raise ValueError('Existing Moronobu creator identity differs')
    if [x['external_id'] for x in proof['artist_identifiers'] if x['scheme']=='wikidata']!=[QID]:raise ValueError('Existing creator QID differs')
    if (o['id'],o['artist_id'],person['id'])!=(130211,35839,35839) or d['native_object_id']!=130211 or d['native_person_id']!=35839:
        raise ValueError('Native object/person association differs')
    if core.sha(core.encode(o))!=d['native_object_sha256'] or core.sha(core.encode(person))!=d['native_person_sha256']:
        raise ValueError('Individually reviewed native evidence changed')
    url='https://www.wikidata.org/wiki/Special:EntityData/'+QID+'.json'
    entity=captured(RUN/'metadata/creator-authorities'/(core.sha(url.encode())+'.json'),d['wikidata_capture'],url)['entities'][QID]
    if entity['id']!=QID or any(value not in base.m.values(entity,prop) for prop,value in [('P6295','35839'),('P245',ULAN),('P244',LCCN),('P214','49697282')]):
        raise ValueError('Explicit existing creator crosswalks absent')
    getty=captured(RUN/'metadata/independent-creator/getty-500118854.json',d['getty_capture'],'https://vocab.getty.edu/ulan/'+ULAN+'.json')
    if getty.get('type')!='Person' or getty.get('id')!='http://vocab.getty.edu/ulan/'+ULAN:
        raise ValueError('Independent Getty authority identity differs')
    names={native.check.norm(x['content']) for x in getty['identified_by'] if x.get('type')=='Name'}
    local={native.check.norm(ar['display_name']),*(native.check.norm(x['alias']) for x in proof['artist_aliases'])}
    source={native.check.norm(person['title']),*(native.check.norm(x) for x in person.get('alt_titles') or [])}
    if person.get('is_artist') is not True or native.check.norm(ar['display_name']) not in names or not local.intersection(source):
        raise ValueError('Independent native and Getty creator names differ')
    if not any(x.get('id')=='http://id.loc.gov/authorities/names/'+LCCN and x.get('type')=='Person' for x in getty.get('equivalent',[])):
        raise ValueError('Getty-to-LoC creator crosswalk absent')
    loc=captured(RUN/'metadata/independent-creator/loc-n80040691.json',d['loc_capture'],'https://id.loc.gov/authorities/names/'+LCCN+'.json')
    matches=[x for x in loc if x.get('@id')=='http://id.loc.gov/authorities/names/'+LCCN]
    if len(matches)!=1:raise ValueError('Unique independent LoC authority absent')
    record=matches[0];ns='http://www.loc.gov/mads/rdf/v1#'
    labels={x.get('@value') for x in record.get(ns+'authoritativeLabel',[])}
    if d['loc_authoritative_label']!='Hishikawa, Moronobu, approximately 1618-approximately 1694' or d['loc_authoritative_label'] not in labels:
        raise ValueError('Independent LoC creator label differs')
    links={x.get('@id') for x in record.get(ns+'hasCloseExternalAuthority',[])}
    if not {'http://vocab.getty.edu/ulan/'+ULAN,'http://www.wikidata.org/entity/'+QID}.issubset(links):
        raise ValueError('LoC-to-Getty/Wikidata authority links absent')
    if d['biographical_uncertainty_marker']!='Japanese, (?)-1694' or d['qualification'] is not None:
        raise ValueError('Birth uncertainty was confused with creator attribution')
    return d,dict(wikidata_entity=entity,wikidata_capture=d['wikidata_capture'],getty_record=getty,getty_capture=d['getty_capture'],loc_record=record,loc_capture=d['loc_capture'])


reviewed.review=review

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['research','native_downloads','prepare','apply','verify']);a=p.parse_args()
    if a.phase=='research':reviewed.research()
    elif a.phase=='native_downloads':native.native_downloads()
    elif a.phase=='prepare':
        for path in (RUN/'selected'/native.PROVIDER).glob('*.json'):reviewed.verify_image(json.loads(path.read_bytes()))
        base.prepare(native.PROVIDER)
    elif a.phase=='apply':base.apply()
    else:reviewed.verify()
