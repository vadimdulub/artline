#!/usr/bin/env python3
"""Image-only native Chicago recovery through individually reviewed creator IDs."""
import argparse
import csv
import importlib.util
import json
import re
from pathlib import Path

s = importlib.util.spec_from_file_location('native', Path(__file__).with_name('recover-local-chicago-native-images-20261006.py'))
native = importlib.util.module_from_spec(s)
s.loader.exec_module(native)
base, core = native.base, native.core
RUN = core.ROOT / 'docs/research/local-chicago-reviewed-authorities-20261006'
native.RUN = base.RUN = RUN
core.VERSION = 'local-chicago-individual-creator-id-review-v1'
original_verify, original_attach = native.verify_image, native.attach
BASIS = 'Exact existing local Chicago artwork and inventory, explicit current Wikidata-to-Chicago creator ID and independently matching NGA constituent authority, plus individual source date/attribution review. All local biography fields, creator links, artwork dates and review status preserved. Exact native photograph and gallery-specific CC0 grant independently verified. Source qualifications retained in credits and accessible text.'


def review(c,o,person):
    rows = json.loads((RUN/'creator-identity-review.json').read_bytes())['images']
    matches = [x for x in rows if x['artwork_id']==c['artwork_id']]
    if len(matches)!=1 or matches[0]['decision']!='approved': raise ValueError('Individual creator identity remains held')
    value = matches[0]
    if len(c['creator_authorities'])!=1 or len(c['creator_links'])!=1 or c['roles']!=['primary']:
        raise ValueError('Unique existing primary creator absent')
    proof = c['creator_authorities'][0]; artist = proof['artist_record']
    if artist['id']!=value['local_artist_id'] or artist['id']!=c['creator_links'][0]['artist_id']:
        raise ValueError('Individually reviewed local creator changed')
    qids = [x['external_id'] for x in proof['artist_identifiers'] if x['scheme']=='wikidata']
    ngas = [x['external_id'] for x in proof['artist_identifiers'] if x['scheme']=='nga-constituent']
    if qids!=[value['existing_qid']] or ngas!=[value['existing_nga_id']]: raise ValueError('Existing independent creator identifiers differ')
    if o['id']!=value['native_object_id'] or person['id']!=value['native_person_id'] or o['artist_id']!=person['id']:
        raise ValueError('Reviewed native artwork/person association changed')
    if core.sha(core.encode(o))!=value['native_object_sha256'] or core.sha(core.encode(person))!=value['native_person_sha256']:
        raise ValueError('Individually reviewed source metadata changed')
    url = 'https://www.wikidata.org/wiki/Special:EntityData/'+qids[0]+'.json'
    path = RUN/'metadata/creator-authorities'/(core.sha(url.encode())+'.json')
    data = path.read_bytes(); rc = json.loads(path.with_suffix('.receipt.json').read_bytes())
    if rc!=value['wikidata_capture'] or rc['url']!=url or core.sha(data)!=rc['sha256'] or len(data)!=rc['bytes']:
        raise ValueError('Pinned creator crosswalk changed')
    entity = json.loads(data)['entities'][qids[0]]
    if entity['id']!=qids[0] or str(person['id']) not in base.m.values(entity,'P6295') or ngas[0] not in base.m.values(entity,'P2252'):
        raise ValueError('Explicit Chicago and NGA creator crosswalks absent')
    local_names = {native.check.norm(artist['display_name']),*(native.check.norm(x['alias']) for x in proof['artist_aliases'])}
    source_names = {native.check.norm(person['title']),*(native.check.norm(x) for x in person.get('alt_titles') or [])}
    if person.get('is_artist') is not True or not local_names.intersection(source_names): raise ValueError('Existing and native creator names do not match')
    nga_source = value['nga_source']; raw = (core.ROOT/nga_source['path']).read_bytes()
    if core.sha(raw)!=nga_source['sha256'] or len(raw)!=nga_source['bytes']: raise ValueError('Pinned NGA authority export changed')
    matches = [x for x in csv.DictReader(raw.decode().splitlines()) if x['constituentid']==ngas[0]]
    if matches!=[value['nga_row']] or matches[0]['wikidataid']!=qids[0] or matches[0]['constituenttype']!='individual':
        raise ValueError('Independent NGA constituent identity differs')
    if native.check.norm(matches[0]['forwarddisplayname']) not in local_names: raise ValueError('Independent NGA creator name differs')
    return value, dict(entity=entity,receipt=rc,nga_source=nga_source,nga_row=matches[0])


def facts(c,o,person):
    decision, authority = review(c,o,person)
    if str(o['id'])!=c['external_id'] or c['institution_slug']!=native.check.SLUG:
        raise ValueError('Existing native object or institution changed')
    if {x['external_id'] for x in c['identifiers'] if x['scheme'] in native.SCHEMES}!={c['external_id']}:
        raise ValueError('Existing native identifiers conflict')
    preferred = [p for p in o.get('artist_pivots',[]) if p.get('is_preferred') is True]
    if len(preferred)!=1 or preferred[0]['artist_id']!=person['id'] or preferred[0]['role_title']!='Artist':
        raise ValueError('Native primary artist relationship is not unique')
    if sum(p.get('role_title')=='Artist' for p in o['artist_pivots'])!=1 or any(p.get('role_title') not in ('Artist','Printer','Publisher') for p in o['artist_pivots']):
        raise ValueError('Additional source creator role needs review')
    display = o.get('artist_display') or ''
    biography_marker = decision.get('biographical_uncertainty_marker')
    if biography_marker:
        # An individually reviewed unknown birth year is distinct from an
        # uncertain creator attribution. Require the exact native name and
        # a narrowly formed nationality/lifespan suffix with matching death.
        match = re.fullmatch(r'[A-Za-z -]+, \(\?\)[–-](\d{4})', biography_marker)
        if (not match or not display.endswith(biography_marker) or person.get('death_date')!=int(match[1])
                or re.search(r'\b(after|attributed|workshop|studio|circle|follower|school|copy|formerly|possibly|manner|style|imitator)\b',biography_marker,re.I)):
            raise ValueError('Reviewed biographical uncertainty marker differs')
        display = display[:-len(biography_marker)].strip()
        if native.check.norm(display)!=native.check.norm(person['title']):
            raise ValueError('Biographical uncertainty conceals a different or qualified creator')
    if decision['qualification']:
        if decision['qualification'] not in display: raise ValueError('Individually reviewed source attribution qualification absent')
    elif re.search(r'\b(after|attributed|workshop|studio|circle|follower|school|copy|formerly|possibly|manner|style|imitator)\b|\?',display,re.I):
        raise ValueError('Unreviewed attribution qualification')
    typ = {'Painting':'painting','Drawing and Watercolor':'drawing','Print':'print'}.get(o.get('artwork_type_title'))
    lo,hi = o.get('date_start'),o.get('date_end');date = o.get('date_display') or ''
    if not typ or type(lo) is not int or type(hi) is not int or not 1000<=lo<=hi<1970 or not re.search(r'\d{3,4}',date):
        raise ValueError('Individually reviewed source type or date is outside scope')
    if re.search(r'\b(undated|unknown|before|after|possibly|or later|or earlier|n\.d\.|later|posthumous|reprint\w*|reissue\w*|restrike\w*)\b|\?',date,re.I):
        raise ValueError('Unreviewed open-ended creation or later-impression wording')
    for span in re.finditer(r'\b(\d{4})\s*[–—/-]\s*(\d{1,2})\b(?!\d)',date):
        first=int(span[1]);modulus=10**len(span[2]);last=first//modulus*modulus+int(span[2])
        if last<first:last+=modulus
        lo,hi=min(lo,first),max(hi,last)
    if not 1000<=lo<=hi<1970 or any(not lo<=int(y)<=hi for y in re.findall(r'\b(\d{4})\b',date)):
        raise ValueError('Source textual creation interval differs')
    accession=o.get('main_reference_number') or '';credit=o.get('credit_line') or ''
    if o.get('fiscal_year_deaccession') is not None or not re.fullmatch(r'\d{4}\.[\w.\-]+',accession):
        raise ValueError('Museum inventory or holding changed')
    if not re.search(r'\b(gift|collections?|funds?|purchase[ds]?|bequest|endowments?|acquisition|exchange)\b',credit,re.I) or re.search(r'\b(loans?|lent|lenders?|private collections?|promised|sold|deaccession\w*|returned)\b',credit,re.I):
        raise ValueError('Accepted museum holding not established')
    approx=bool(re.search(r'\b(?:c\.|ca\.)\s*\d|\b(circa|about|early|mid|late|probably)\b',date,re.I))
    precision=('circa' if lo==hi else 'circa_range') if approx else ('exact' if lo==hi else 'range')
    result=dict(title=o['title'],date_display=date,creation_year_start=lo,creation_year_end=hi,date_precision=precision,
        work_type=typ,accession_number=accession,medium_text=o.get('medium_display'),dimensions_text=o.get('dimensions'),
        creator_identity_review=decision,independent_creator_authority=authority)
    for k in ('accession_number','creation_year_start','creation_year_end','date_precision','work_type'):
        if c[k]!=result[k]: raise ValueError('Existing catalogue field differs from current source: '+k)
    if native.check.norm(c['title']) not in {native.check.norm(x) for x in [o['title'],*(o.get('alt_titles') or [])]} or native.check.norm(c['date_display'])!=native.check.norm(date):
        raise ValueError('Existing artwork title or date wording differs')
    return result


native.facts = facts


def verify_image(im):
    decision=im['raw']['native_facts']['creator_identity_review']
    if im['raw'].get('creator_identity_review_finalized') is not True or im['creator_credit']!=decision['creator_credit'] or decision['note'] not in im['attribution_text']:
        raise ValueError('Individually reviewed creator credit or source discrepancies omitted')
    if decision['alt_text'] and im.get('alt_text')!=decision['alt_text']: raise ValueError('Qualified source attribution omitted from accessible text')
    # The shared verifier expects its original plain credit format. Validate
    # every source/rights field with that format, after enforcing the actual
    # independently reviewed credit above. Native evidence is never altered.
    plain=im['artist']+'; Art Institute of Chicago'
    normalized=dict(im,creator_credit=plain,attribution_text=im['attribution_text'].replace(decision['creator_credit'],plain))
    original_verify(normalized)


native.verify_image = verify_image


def research():
    def research_verify(im):
        if im['raw'].get('creator_identity_review_finalized'): verify_image(im)
        else: original_verify(im)
    native.verify_image=research_verify
    try: native.research(True)
    finally: native.verify_image=verify_image
    for p in sorted((RUN/'selected'/native.PROVIDER).glob('*.json')):
        im=json.loads(p.read_bytes())
        if im['raw'].get('creator_identity_review_finalized'): verify_image(im);continue
        value=im['raw']['native_facts']['creator_identity_review']
        core.save_new(RUN/'history/before-creator-credit'/p.name,p.read_bytes())
        im['attribution_text']=im['attribution_text'].replace(im['creator_credit'],value['creator_credit'])+' '+value['note']
        im['creator_credit']=value['creator_credit']
        if value['alt_text']:im['alt_text']=value['alt_text']
        im['raw']['creator_identity_review_finalized']=True
        verify_image(im);p.write_bytes(core.encode(im))


def attach(db,im,target):
    verify_image(im)
    decisions=json.loads((RUN/'visual-review.json').read_bytes())['images']
    matches=[x for x in decisions if x['artwork_id']==im['artwork_id']]
    if len(matches)!=1 or matches[0]['decision']!='approved' or any(matches[0][k]!=im[k] for k in ('sha256','source_sha256')):
        raise ValueError('Exact source and derivative lack individual visual approval')
    result=original_attach(db,im,target)
    if result=='attached': db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',(BASIS,im['media_id']))
    return result


base.m.attach=attach


def verify():
    native.verify()
    checks=[]
    attached={x['artwork_id'] for x in json.loads((RUN/'apply-receipt.json').read_bytes())['receipts'] if x['result']=='attached'}
    with base.connect() as db:
        for im in base.prepared():
            verify_image(im)
            if im['artwork_id'] not in attached:
                private=base.ARCHIVE/'source-images'/RUN.name/'held-derivatives'/Path(im['path']).name
                if (core.ROOT/'apps/web/public'/im['path'].lstrip('/')).exists() or core.sha(private.read_bytes())!=im['sha256']:
                    raise ValueError('Unapproved derivative is not preserved privately')
                if db.execute('SELECT 1 FROM media_assets WHERE id=%s OR storage_path=%s',(im['media_id'],im['path'])).fetchone():
                    raise ValueError('Unapproved derivative unexpectedly attached')
                continue
            row=db.execute('SELECT rights_basis,source_record_id FROM media_rights_evidence WHERE media_id=%s',(im['media_id'],)).fetchone()
            if row!=dict(rights_basis=BASIS,source_record_id=im['external_id']): raise ValueError('Stored exact authority/rights basis differs')
            checks.append(dict(artwork_id=im['artwork_id'],creator_credit=im['creator_credit'],qualified=bool(im['raw']['native_facts']['creator_identity_review']['qualification'])))
    core.save_new(RUN/'creator-review-database-verification.json',dict(at=core.now(),passed=True,images=checks,
        existing_biography_fields_and_creator_links_preserved=True,source_qualifications_preserved=True))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['research','native_downloads','prepare','apply','verify'])
    p.add_argument('--run-name',default=RUN.name);a=p.parse_args()
    if not re.fullmatch('local-chicago-[a-z0-9-]+',a.run_name):p.error('Use a selected local Chicago review operation')
    RUN=core.ROOT/'docs/research'/a.run_name;native.RUN=base.RUN=RUN
    if a.phase=='research':research()
    elif a.phase=='native_downloads':native.native_downloads()
    elif a.phase=='prepare':
        for p in (RUN/'selected'/native.PROVIDER).glob('*.json'):verify_image(json.loads(p.read_bytes()))
        base.prepare(native.PROVIDER)
    elif a.phase=='apply':base.apply()
    else:verify()
