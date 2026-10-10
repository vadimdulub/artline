#!/usr/bin/env python3
"""Image-only local recovery from exact Academy Vienna native CC BY photographs."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlencode
import uuid

from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('local_recovery',Path(__file__).with_name('recover-local-commons-images-20261005.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
core=base.core
RUN=core.ROOT/'docs/research/local-academy-images-20261006'
base.RUN=RUN
HOST='collection.kunstsammlungenakademie.at'
IMAGE_HOST=HOST+'.zetcom.net'
PROVIDER='academy-vienna-native'
LICENCE='https://creativecommons.org/licenses/by/4.0/'
SOURCE_SLUG='academy-vienna-native-images-20261006'
SOURCE_ID=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/sources/'+SOURCE_SLUG))
core.HOSTS.update({HOST,IMAGE_HOST})
core.PROVIDERS[PROVIDER]='Paintings Gallery of the Academy of Fine Arts Vienna'
core.VERSION='local-academy-exact-native-cc-by-v1'


def norm(value):
    return ' '.join(re.findall(r'[^\W_]+',''.join(c for c in unicodedata.normalize('NFKD',str(value or '').casefold()) if not unicodedata.combining(c))))


def capture_html(fetcher,url):
    path=fetcher.cache/(core.sha(url.encode())+'.html')
    receipt_path=path.with_suffix('.receipt.json')
    if path.exists():
        body=path.read_bytes();receipt=json.loads(receipt_path.read_bytes())
        if core.sha(body)!=receipt['sha256']:raise ValueError('Cached native page changed')
        return body,receipt
    body,headers=fetcher.get(url,5_000_000)
    receipt=dict(url=url,retrieved_at=core.now(),sha256=core.sha(body),bytes=len(body),headers=headers,path=str(path.relative_to(core.ROOT)))
    core.save_new(path,body);core.save_new(receipt_path,receipt)
    return body,receipt


def native_check(c,entity,native,search,aliases,soup):
    # Validate the existing artwork authority without requiring a Commons image.
    base.original_entity_match(c,entity,require_primary_image=False)
    if c['roles']!=['primary'] or len(c['creators'])!=1:
        raise ValueError('Underlying work/creator rights need review')
    review=c.get('native_identity_review')
    if review and (review['artwork_id']!=c['artwork_id'] or review['qid']!=c['qid']
                   or review['artist_qid']!=c['creators'][0]['qid']
                   or review['native_snapshot_sha256']!=core.sha(core.encode(native))):
        raise ValueError('Pinned individual identity review differs')
    stored_accession=c['accession_number']
    inventory_review=review.get('inventory_reconciliation') if review else None
    accession=inventory_review['native'] if inventory_review else stored_accession
    if inventory_review and (inventory_review.get('stored')!=stored_accession
                             or not inventory_review.get('note') or accession==stored_accession):
        raise ValueError('Inventory reconciliation is not individually pinned')
    exact=[d for d in search['response']['docs'] if d.get('number_s')==accession]
    if search['response'].get('numFoundExact') is not True or search['response']['numFound']!=1 or len(exact)!=1:
        raise ValueError('Museum inventory lookup is not unique and exact')
    record=exact[0]
    if str(native.get('Id'))!=record['oid'] or native.get('ObjObjectNumberTxt')!=accession:
        raise ValueError('Native object and inventory differ')
    if stored_accession not in base.m.values(entity,'P217'):
        raise ValueError('Current authority does not corroborate stored inventory')
    if native.get('ObjCollectionTxt_en')!='Paintings Gallery' or native.get('ObjCategoryVoc',{}).get('LabelTxt_en')!='painting' or c['work_type']!='painting':
        raise ValueError('Native collection or object type differs')
    people=[x for x in native.get('ObjPersonRef',{}).get('Items',[]) if x.get('LinkLabelTxt')]
    shown=[x for x in people if x.get('RoleTxt_en')=='Shown person']
    reviewed_subjects=[]
    if shown:
        reviewed_subjects=sorted([dict(id=x['ReferencedId'],name=x.get('LinkLabelTxt_en') or x['LinkLabelTxt']) for x in shown],key=lambda x:x['id'])
        if (not review or review.get('shown_person_review')!=reviewed_subjects
                or any(x.get('AttributionTxt') or x.get('AttributionTxt_en') for x in shown)):
            raise ValueError('Depicted-person roles require individual review')
        people=[x for x in people if x.get('RoleTxt_en')!='Shown person']
    if len(people)!=1 or people[0].get('RoleTxt_en')!='Artist' or people[0].get('AttributionTxt') or people[0].get('AttributionTxt_en'):
        raise ValueError('Native attribution is missing, multiple or qualified')
    person=people[0]
    known={norm(v) for v in [c['artist'],*aliases]}
    if review:
        if review['native_artist_id']!=person['ReferencedId'] or review['native_artist']!=(person.get('LinkLabelTxt_en') or person['LinkLabelTxt']):
            raise ValueError('Reviewed native creator changed')
        known.add(norm(review['native_artist']))
    if norm(person.get('LinkLabelTxt_en') or person['LinkLabelTxt']) not in known:
        raise ValueError('Native artist name does not match existing artist or aliases')
    death=c['creators'][0]['death']
    if not death and review and review.get('native_lifetime_for_rights_only'):
        life=re.search(r'(?<!\d)(\d{4})[–—-](\d{4})(?!\d)',person.get('LifedatesTxt_en',''))
        if life:death=int(life[2])
    if not death or death+70>=2026:raise ValueError('Underlying work/creator rights need review')
    reviewed_unlabelled=[]
    shown_ids={x['ReferencedId'] for x in shown}
    if set(record.get('person_ss',[]))!={person['ReferencedId'],*shown_ids}:
        # Public records can contain additional person references whose display
        # name, role and attribution are all empty. Accept these only after an
        # individual pinned review, retaining the unexplained references as
        # evidence and requiring one matching artist in the rendered heading.
        pinned_refs=review.get('unlabelled_reference_review') if review else None
        extras=[p for p in native.get('ObjPersonRef',{}).get('Items',[]) if p['ReferencedId'] not in {person['ReferencedId'],*shown_ids}]
        current_refs=sorted([dict(id=p['ReferencedId'],source_name=p.get('PerLastNameTxt')) for p in extras],key=lambda p:p['id'])
        blank_fields=('LinkLabelTxt','LinkLabelTxt_en','RoleTxt','RoleTxt_en','AttributionTxt','AttributionTxt_en')
        displayed=soup.select('h1.CollectionItem-Title .CollectionItem-author')
        if (not pinned_refs or current_refs!=pinned_refs
                or any(p.get(k) for p in extras for k in blank_fields)
                or len(displayed)!=1 or norm(displayed[0].get_text(' ',strip=True))!=norm(person['LinkLabelTxt'])
                or set(record.get('person_ss',[]))!={person['ReferencedId'],*shown_ids,*(p['ReferencedId'] for p in extras)}):
            raise ValueError('Native search and object creator identities differ')
        reviewed_unlabelled=current_refs
    # A translation is permitted only within the same uniquely accessioned work.
    names={norm(x['value']) for x in entity.get('labels',{}).values()}
    names.update(norm(x['value']) for xs in entity.get('aliases',{}).values() for x in xs)
    titles={norm(native.get('ObjTitleTxt')),norm(native.get('ObjTitleTxt_en'))}
    if not titles&names and not review:raise ValueError('Native title/translation needs manual identity review')
    museum_dates=[]
    retained_date_discrepancies=[]
    for d in native.get('ObjDateGrp',[]):
        lo,hi=d.get('ObjDateFromTxt'),d.get('ObjDateToTxt')
        if lo or hi:
            if not str(lo or '').isdigit() or not str(hi or '').isdigit():raise ValueError('Unresolved native creation bounds')
            lo,hi=int(lo),int(hi)
            if lo>hi or not 1000<=lo<=hi<=1970:
                raise ValueError('Native date conflicts with existing pre-1971 record')
            if hi<c['creation_year_start'] or lo>c['creation_year_end']:
                discrepancy=dict(stored_bounds=[c['creation_year_start'],c['creation_year_end']],
                    native_bounds=[lo,hi],native_text=d.get('ObjDateTxt'))
                pinned=review.get('retained_date_discrepancies',[]) if review else []
                if discrepancy not in pinned:
                    raise ValueError('Native date conflicts with existing pre-1971 record')
                # Exact inventory, creator and independently reviewed title
                # identify the same physical artwork. Both creation intervals
                # are eligible. Preserve the disagreement, never rewrite dates.
                if not review.get('date_discrepancy_note') or not 1000<=c['creation_year_start']<=c['creation_year_end']<=1970:
                    raise ValueError('Date discrepancy lacks individual object review')
                retained_date_discrepancies.append(discrepancy)
            museum_dates.append([lo,hi])
    if review and review.get('retained_date_discrepancies',[])!=retained_date_discrepancies:
        raise ValueError('Pinned date discrepancies differ from the native record')
    source_years=[]
    for d in base.m.values(entity,'P571'):
        if isinstance(d,dict) and d.get('precision',0)>=9:
            match=re.match(r'^\+(\d+)-',d.get('time',''))
            if match:source_years.append(int(match[1]))
    reviewed_dates=[]
    if review and review.get('native_object_date_evidence'):
        evidence=review['native_object_date_evidence']
        texts={d.get(k) for d in native.get('ObjDateGrp',[]) for k in ('ObjDateTxt','ObjDateTxt_en') if d.get(k)}
        lo,hi=evidence['year_start'],evidence['year_end']
        if evidence['text'] not in texts or not isinstance(lo,int) or not isinstance(hi,int) or not 1000<=lo<=hi<=1970:
            raise ValueError('Reviewed native object date is not pinned to the published date field')
        if hi<c['creation_year_start'] or lo>c['creation_year_end']:
            raise ValueError('Reviewed native object date conflicts with the existing record')
        reviewed_dates.append([lo,hi])
    reviewed_authority_intervals=[]
    if review and review.get('authority_interval_review'):
        # Wikidata precision 7 means a historical century (1601–1700),
        # precision 8 a decade (1680–1689). Never use its representative
        # timestamp as an exact creation year or amend catalogue dates.
        evidence=review['authority_interval_review'];value=evidence['value']
        match=re.fullmatch(r'\+(\d+)-\d{2}-\d{2}T00:00:00Z',value.get('time',''))
        if (value not in base.m.values(entity,'P571') or not match
                or value.get('precision') not in (7,8) or value.get('before')!=0 or value.get('after')!=0
                or value.get('calendarmodel')!='http://www.wikidata.org/entity/Q1985727'):
            raise ValueError('Coarse object-date authority changed or is unsupported')
        year=int(match[1]);precision=value['precision']
        lo=((year-1)//100)*100+1 if precision==7 else (year//10)*10
        hi=lo+(99 if precision==7 else 9)
        if (evidence.get('bounds')!=[lo,hi] or not evidence.get('note') or not 1000<=lo<=hi<=1970
                or not 1000<=c['creation_year_start']<=c['creation_year_end']<=1970
                or hi<c['creation_year_start'] or lo>c['creation_year_end']):
            raise ValueError('Coarse source date is outside scope or conflicts')
        reviewed_authority_intervals.append(dict(value=value,bounds=[lo,hi]))
    if not museum_dates and not source_years and not reviewed_dates and not reviewed_authority_intervals:
        raise ValueError('No object-level source creation date corroboration')
    photograph_review=review.get('native_photograph_review') if review else None
    if photograph_review:
        if (photograph_review.get('field')!='ObjMultimediaRef' or not photograph_review.get('note')
                or native.get('ObjDescriptionTxt')!='beidseitig bemalte Leinwand'
                or 'verso' not in c['accession_number']):
            raise ValueError('Non-primary face lacks an individual two-sided-canvas review')
        media=[p for p in native.get('ObjMultimediaRef',{}).get('Items',[])
               if p.get('ReferencedId')==photograph_review.get('native_media_id')]
    else:
        media=native.get('ObjMultimediaMainImageRef',{}).get('Items',[])
    if len(media)!=1 or len(media[0].get('Multimedia',[]))!=1:raise ValueError('Primary image is not unique')
    owner=media[0];photo=owner['Multimedia'][0]
    allowed_mimes=('image/jpeg','image/tiff') if photograph_review else ('image/jpeg',)
    if owner.get('MulCCLizVoc',{}).get('LabelTxt')!='CC BY 4.0' or photo.get('license')!='CC BY 4.0' or photo.get('mime') not in allowed_mimes:
        raise ValueError('Exact primary photograph lacks an explicit approved licence')
    if photograph_review and (photograph_review.get('resource')!=photo.get('full')
                              or photograph_review.get('source_declared_mime')!=photo.get('mime')):
        raise ValueError('Reviewed verso photograph mapping changed')
    if not soup.find(string=lambda s:s and s.strip()=='CC BY 4.0'):
        raise ValueError('Rendered primary source does not display the licence')
    institution=owner.get('MulPhotocreditTxt_en','');photographer=owner.get('MulSourceTxt_en','')
    if not institution or not photographer:raise ValueError('Institution or photographer credit missing')
    if not re.fullmatch(r'multimedia/\d+/multimedia-\d+\.large\.jpg',photo['full']):
        raise ValueError('Unapproved native primary resource path')
    url='https://'+IMAGE_HOST+'/'+photo['full']
    if not photograph_review and (native.get('ObjURLImageTxt')!=url or native.get('DefaultImage')!=photo['full']):
        raise ValueError('Rendered primary photograph mapping differs')
    return url,institution+'; '+photographer,dict(native_id=native['Id'],accession=accession,
        native_artist_id=person['ReferencedId'],native_artist=person.get('LinkLabelTxt_en'),
        native_dates=museum_dates,authority_creation_years=source_years,
        individually_reviewed_native_dates=reviewed_dates,
        individually_reviewed_authority_intervals=reviewed_authority_intervals,
        inventory_reconciliation=inventory_review,
        individually_reviewed_verso_photograph=photograph_review,
        individually_reviewed_unlabelled_person_references=reviewed_unlabelled,
        individually_reviewed_shown_persons=reviewed_subjects,
        retained_date_discrepancies=retained_date_discrepancies,
        native_artist_lifetime=person.get('LifedatesTxt_en'),underlying_creator_death_evidence=death,
        date_policy='Existing catalogue dates retained; blank native dates are not filled from artist lifetimes.')


def verify_image(im):
    raw=im['raw'];receipt=raw['native_capture'];path=core.ROOT/receipt['path']
    if not path.resolve().is_relative_to(RUN.resolve()) or core.sha(path.read_bytes())!=receipt['sha256']:
        raise ValueError('Pinned official capture changed')
    soup=BeautifulSoup(path.read_bytes(),'html.parser')
    native=json.loads(soup.find('script',id='__NEXT_DATA__').string)['props']['pageProps']['data']['item']
    if native!=raw['native']:raise ValueError('Native evidence differs from captured page')
    url,credit,facts=native_check(im,raw['wikidata'],native,raw['inventory_search'],raw['artist_aliases'],soup)
    pinned=im['identity_evidence']
    required={'native_id','accession','native_artist_id','native_artist','native_dates','authority_creation_years','date_policy'}
    if url!=im['source_image_url'] or credit!=im['creator_credit'] or not required.issubset(pinned) or any(facts.get(k)!=v for k,v in pinned.items()):
        raise ValueError('Reviewed identity/image metadata changed')
    if receipt['url']!=im['page'] or im['page']!='https://'+HOST+'/de/collection/item/'+native['Id']+'/':
        raise ValueError('Native page identity changed')
    if (im['policy_url'],im['license_label'],im['rights_status'])!=(LICENCE,'CC BY 4.0','cc_by'):
        raise ValueError('Native image licence changed')
    if credit not in im['attribution_text'] or LICENCE not in im['attribution_text']:
        raise ValueError('Image licence and photo attribution missing')


def research(reviewed_only=False):
    candidates=json.loads((RUN/'candidates.json').read_bytes())['candidates']
    fetcher=core.Fetcher(RUN/'metadata');events=core.latest_events(RUN)
    reviews={r['artwork_id']:r for r in json.loads((RUN/'native-identity-review.json').read_bytes())['records']} if reviewed_only else {}
    with base.connect() as db:
        aliases=db.execute('''SELECT aa.artwork_id::text,al.alias FROM artwork_artists aa
            JOIN artist_aliases al ON al.artist_id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])''',
            ([c['artwork_id'] for c in candidates],)).fetchall()
    by_id={c['artwork_id']:[] for c in candidates}
    for row in aliases:by_id[row['artwork_id']].append(row['alias'])
    for c in candidates:
        aid=c['artwork_id'];out=RUN/'selected'/PROVIDER/(aid+'.json')
        if out.exists() or (reviewed_only and aid not in reviews) or (not reviewed_only and aid in events):continue
        if reviewed_only:c=dict(c,native_identity_review=reviews[aid])
        try:
            if not c['accession_number']:raise ValueError('Existing accession missing')
            entity_url='https://www.wikidata.org/wiki/Special:EntityData/'+c['qid']+'.json'
            entity=fetcher.metadata(entity_url)['entities'][c['qid']]
            base.original_entity_match(c,entity,require_primary_image=False)
            inventory=c.get('native_identity_review',{}).get('inventory_reconciliation',{}).get('native',c['accession_number'])
            query='number_txt:'+json.dumps(inventory)
            search_url='https://'+HOST+'/solr/published/select?'+urlencode(dict(q=query,fq='type:Object',rows=2,wt='json'))
            search=fetcher.metadata(search_url)
            if search['response']['numFound']!=1 or len(search['response']['docs'])!=1:
                raise ValueError('Native inventory search is not unique')
            native_id=search['response']['docs'][0]['oid']
            if not re.fullmatch(r'\d+',native_id):raise ValueError('Unexpected native identifier')
            page='https://'+HOST+'/de/collection/item/'+native_id+'/'
            body,receipt=capture_html(fetcher,page);soup=BeautifulSoup(body,'html.parser')
            native=json.loads(soup.find('script',id='__NEXT_DATA__').string)['props']['pageProps']['data']['item']
            url,credit,facts=native_check(c,entity,native,search,by_id[aid],soup)
            raw=dict(wikidata=entity,native=native,native_capture=receipt,inventory_search=search,
                inventory_capture=json.loads((fetcher.cache/(core.sha(search_url.encode())+'.receipt.json')).read_bytes()),
                wikidata_capture=json.loads((fetcher.cache/(core.sha(entity_url.encode())+'.receipt.json')).read_bytes()),
                artist_aliases=by_id[aid])
            im=dict(c,provider=PROVIDER,page=page,source_image_url=url,policy_url=LICENCE,rights_status='cc_by',
                license_label='CC BY 4.0',checked_at=core.now(),creator_credit=credit,raw=raw,identity_evidence=facts,
                attribution_text=f"{c['artist']}. {c['title']}. {c['accession_number']}. {credit}. {page}. CC BY 4.0 ({LICENCE}). Full-frame proportional resize and JPEG compression.")
            verify_image(im);core.save_new(out,im)
            core.event(RUN,dict(provider=PROVIDER,artwork_id=aid,outcome='rights_selected',native_id=native_id))
            print('Selected native photo:',c['artist'],c['title'],flush=True)
        except (ValueError,KeyError,TypeError,AttributeError) as error:
            core.event(RUN,dict(provider=PROVIDER,artwork_id=aid,outcome='manual_review',reason=str(error)[:400]))
        except Exception as error:
            core.event(RUN,dict(provider=PROVIDER,artwork_id=aid,outcome='source_error',reason=str(error)[:400]))
            raise
    print('Native rights-cleared images:',len(list((RUN/'selected'/PROVIDER).glob('*.json'))),flush=True)


def native_attach(db,im,target):
    if target!='local':raise ValueError('Only local image attachment is authorized')
    verify_image(im)
    with db.transaction():
        result=base.m.original_attach(db,im,target)
        if result=='attached':
            db.execute('''INSERT INTO sources(id,slug,name,source_type,base_url,terms_url)
                VALUES(%s,%s,%s,'collection_page',%s,%s) ON CONFLICT(slug) DO NOTHING''',
                (SOURCE_ID,SOURCE_SLUG,core.PROVIDERS[PROVIDER]+' — per-image CC BY 4.0','https://'+HOST+'/',LICENCE))
            sid=db.execute('SELECT id::text,base_url FROM sources WHERE slug=%s',(SOURCE_SLUG,)).fetchone()
            if sid!=dict(id=SOURCE_ID,base_url='https://'+HOST+'/'):raise ValueError('Source identity changed')
            db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',
                       (im['creator_credit'],im['attribution_text'],im['media_id']))
            db.execute('''UPDATE media_rights_evidence SET source_id=%s,source_record_id=%s,rights_basis=%s WHERE media_id=%s''',
                (SOURCE_ID,im['identity_evidence']['native_id'],
                 'Exact existing artwork authority, native museum inventory, unqualified creator and object-level creation evidence; individually reviewed museum photograph explicitly CC BY 4.0 with institution/photographer credit. Existing catalogue fields preserved.',im['media_id']))
        return result


base.m.attach=native_attach


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase',choices=['select','research','research-reviewed','prepare','apply','verify'])
    p.add_argument('--run-name',default=RUN.name)
    p.add_argument('--limit',type=int,default=80)
    p.add_argument('--exclude-run',type=Path)
    p.add_argument('--institution',default='wikimedia-museum-q414219')
    args=p.parse_args()
    if not re.fullmatch(r'local-academy-[a-z0-9-]+',args.run_name):p.error('Expected a local Academy operation name')
    if not 1<=args.limit<=100:p.error('Select 1–100 existing records per reviewed batch')
    if args.institution not in ('wikimedia-museum-q414219','academy-fine-arts-vienna-paintings-gallery'):
        p.error('Only existing Academy Vienna institution identities are supported')
    RUN=core.ROOT/'docs/research'/args.run_name
    base.RUN=RUN
    RUN.mkdir(parents=True,exist_ok=True)
    if args.phase=='select':base.select(args.limit,institution=args.institution,exclude_run=args.exclude_run)
    elif args.phase=='research':research()
    elif args.phase=='research-reviewed':research(True)
    elif args.phase=='prepare':
        for path in (RUN/'selected'/PROVIDER).glob('*.json'):verify_image(json.loads(path.read_bytes()))
        base.prepare(PROVIDER)
    elif args.phase=='apply':base.apply()
    else:
        for im in base.prepared():verify_image(im)
        base.verify()
