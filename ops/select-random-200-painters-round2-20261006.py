#!/usr/bin/env python3
"""Select independently identified works from the fixed research cohort.

Read-only production preflight. Plans are per painter, immutable and resumable.
Confidence labels are editorial thresholds, not calibrated probabilities.
"""
import argparse
import collections
import difflib
import importlib.util
import json
from pathlib import Path
import re
import uuid

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cohort_research',ROOT/'ops/random-200-painters-round2-20261006.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
r=m.r;q=m.q;RUN=m.RUN;BACKUP=m.BACKUP


def kind(medium):
    value=q.norm(medium)
    if re.search(r'\b(etching|aquatint|drypoint|woodcut|woodblock|lithograph|lithography|engraving|screenprint|linocut)\b',value):return 'print'
    if re.search(r'\b(oil|tempera|acrylic|gouache|encaustic)\b',value):return 'painting'
    if re.search(r'\b(watercolor|watercolour)\b',value):return 'watercolor'
    if re.search(r'\b(pencil|charcoal|graphite|chalk|crayon|pen|pastel)\b',value):return 'drawing'
    if re.search(r'\bfresco\b',value):return 'fresco'
    if re.search(r'\b(bronze|marble)\b',value):return 'sculpture'
    return 'unknown'


def normalized(value):
    return ' '.join(re.findall(r'[^\W_]+',q.norm(value)))


def source_date(page):
    """Visible Date preserves qualifiers sometimes omitted from gallery JSON."""
    visible=(page['fields'].get('Date') or '').split(';',1)[0].strip()
    return m.dates.creation_date(visible) or m.dates.creation_date(page['metadata'].get('year'))


def years_overlap(a,b):
    return all(x is not None for x in [a.get('creation_year_start'),a.get('creation_year_end'),b.get('creation_year_start'),b.get('creation_year_end')]) and max(a['creation_year_start'],b['creation_year_start'])<=min(a['creation_year_end'],b['creation_year_end'])


def indistinct_dates(a,b):
    return not all(x is not None for x in [a.get('creation_year_start'),a.get('creation_year_end'),b.get('creation_year_start'),b.get('creation_year_end')]) or years_overlap(a,b)


def snapshots(db,ids):
    if not ids:return {}
    rows=db.execute('''SELECT to_jsonb(a) artwork,
      COALESCE((SELECT jsonb_agg(to_jsonb(aa) ORDER BY artist_id,attribution_role) FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]') creators,
      COALESCE((SELECT jsonb_agg(to_jsonb(am) ORDER BY media_id) FROM artwork_media am WHERE am.artwork_id=a.id),'[]') attachments,
      COALESCE((SELECT jsonb_agg(to_jsonb(la) ORDER BY id) FROM artwork_location_assertions la WHERE la.artwork_id=a.id),'[]') locations
      FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',(ids,)).fetchall()
    return {x['artwork']['id']:x for x in rows}


def artist_plan(pair,db):
    artist=pair['artist'];aid=artist['id'];dest=RUN/'selections'/(aid+'.json.gz')
    if dest.exists():return r.load(dest)
    idx=r.load(RUN/'indexes'/(aid+'.json.gz'));eligible=[x for x in idx['items'] if not x['date'] or x['date']['creation_year_start']<=1970]
    paths=[RUN/'pages'/aid/(r.sha(x['url'].encode())+'.json.gz') for x in eligible]
    paths=[RUN/'page-retries'/aid/p.name if (RUN/'page-retries'/aid/p.name).exists() else p for p in paths]
    if not all(p.exists() for p in paths):return None
    records=[r.load(p) for p in paths]
    # Do not freeze a recoverable network failure into a selection while research continues.
    if any(x['outcome']!='captured' and not (RUN/'page-retries'/aid/p.name).exists() for p,x in zip(paths,records)):return None
    pages=[x['page'] for x in records if x['outcome']=='captured']
    works=r.load(RUN/'catalogue-works'/(aid+'.json.gz'))
    unlinked=[x['artwork'] for x in r.load(RUN/'expanded-creator-leads.json') if x['artist_id']==aid]
    aliases=collections.defaultdict(set)
    for path in (RUN/'translations').glob(aid+'-*.json.gz'):
        for item in r.load(path)['items']:
            aliases[q.image_key(item.get('image'))].add(normalized(item['title']))
    for p in pages:
        p['date']=source_date(p)
        p['date_evidence']='Visible artwork Date field, falling back to source gallery JSON only when unparseable.'
        p['identity_titles']=sorted(({normalized(p['title']),normalized(p['fields'].get('Original Title'))}|aliases[q.image_key(p['metadata']['image'])])-{''})
    names=collections.defaultdict(list);urls=collections.defaultdict(list);source_ids=collections.defaultdict(list)
    for w in works:
        for name in {normalized(w['title']),normalized(w['alternate_title'])}-{''}:names[name].append(w)
        for ident in w['identifiers']:
            if ident.get('canonical_url'):urls[ident['canonical_url']].append(w)
            if ident['scheme']=='wikiart-artwork':source_ids[ident['external_id']].append(w)
        for citation in w['citations']:
            if citation.get('source_url','').startswith('https://www.wikiart.org/') and citation['field_name'] in ['wikiart_featured_identity','regional_source_metadata','image_identity','creation_date','greek_image_identity']:
                urls[citation['source_url']].append(w)
        if w.get('existing_image_source'):urls[w['existing_image_source']].append(w)
    source_titles=collections.defaultdict(list);source_images=collections.defaultdict(list)
    for p in pages:
        for name in p['identity_titles']:source_titles[name].append(p)
        source_images[q.image_key(p['metadata']['image'])].append(p)
    unlinked_index=[x for x in r.load(RUN/'unlinked-index-entries.json.gz') if x['artist_id']==aid]
    rows=[{'action':'excluded' if x['date'] and x['date']['creation_year_start']>1970 else 'hold',
           'reason':'Explicit post-1970 source date' if x['date'] and x['date']['creation_year_start']>1970 else x['reason'],
           'record':{'index':x,'outcome':'unlinked_index_entry'}} for x in unlinked_index]
    for record in records:
        if record['outcome']!='captured':
            rows.append({'action':'hold','reason':'Source page unavailable','record':record});continue
        p=record['page'];meta=p['metadata'];date=p['date'] or {}
        row={'source_id':meta['_id'],'source_url':p['url'],'title':p['title'],'page':p,'artist_id':aid,
             'source_rights_label':p['rights_label'],'rights_status':p['rights_status']}
        def hold(reason,**extra):row.update(action='hold',reason=reason,**extra)
        if date.get('creation_year_start',0)>1970:
            row.update(action='excluded',reason='Artwork page explicitly dates creation after 1970');rows.append(row);continue
        direct={w['id']:w for w in urls[p['url']]+source_ids[meta['_id']]}
        exact={w['id']:w for name in p['identity_titles'] for w in names[name]}
        same_source_image=source_images[q.image_key(meta['image'])]
        related={other['metadata']['_id']:other for name in p['identity_titles'] for other in source_titles[name]
                 if other['metadata']['_id']!=meta['_id'] and indistinct_dates(date,other['date'] or {})}
        chosen=None;confidence=None;basis=None
        if len(direct)==1:
            chosen=next(iter(direct.values()));confidence=.99;basis='Existing exact WikiArt source ID or artwork-page citation, with the same primary creator.'
        elif direct:hold('Multiple existing records cite this exact source; object identity requires review',candidate_ids=sorted(direct))
        elif len(same_source_image)>1:hold('Multiple source records use the same reproduction',related_sources=[x['url'] for x in same_source_image])
        elif related:hold('Source title/version ambiguity at overlapping or unknown dates',related_sources=[x['url'] for x in related.values()])
        elif exact:
            dated=[w for w in exact.values() if years_overlap(date,w)]
            if len(dated)==1 and len(exact)==1:
                chosen=dated[0];confidence=.95;basis='Unique exact source title/translation, same primary creator and overlapping explicit creation dates; no competing source version.'
                common=next(name for name in p['identity_titles'] if chosen in names[name])
                if len(common)<10 or common in ['still life','self portrait','landscape','portrait','untitled','composition','flowers']:
                    chosen=None;hold('Generic title needs independent same-object evidence',candidate_ids=sorted(exact))
            else:hold('Existing same-title record requires date/version reconciliation',candidate_ids=sorted(exact))
        else:
            close=[]
            for name in p['identity_titles']:
                for other,old in names.items():
                    if not old or len(name)<=8 or len(other)<=8:continue
                    compatible=[w['id'] for w in old if indistinct_dates(date,w)]
                    if not compatible:continue
                    contained=min(len(name),len(other))>=18 and (name in other or other in name)
                    matcher=difflib.SequenceMatcher(None,name,other)
                    # Both quick ratios are upper bounds: reject only impossible matches.
                    similar=contained or (matcher.real_quick_ratio()>=.88 and matcher.quick_ratio()>=.88 and matcher.ratio()>=.88)
                    if similar:close.extend(compatible)
            unlinked_ids=[w['id'] for w in unlinked if normalized(w['title']) in p['identity_titles'] or normalized(w.get('alternate_title')) in p['identity_titles']]
            if close or unlinked_ids:hold('Possible existing translated/variant title or unlinked-creator record',candidate_ids=sorted(set(close+unlinked_ids)))
            elif re.search(r'\b(detail|fragment|reverse|verso|reproduction|after [a-z]|copy of)\b',normalized(p['title'])):
                hold('Detail, fragment, copy or alternate view needs object-level reconciliation')
            else:
                target=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://www.wikiart.org/artwork/'+meta['_id']))
                work={'id':target,'slug':'wikiart-'+meta['_id'],'title':p['title'],'alternate_title':p['fields'].get('Original Title'),
                      'normalized_title':q.norm(p['title']),'creation_year_start':date.get('creation_year_start'),
                      'creation_year_end':date.get('creation_year_end'),'date_display':date.get('date_display') or meta.get('year') or 'Unknown date',
                      'date_precision':date.get('date_precision','unknown'),'work_type':kind(p['fields'].get('Media')),
                      'medium_text':p['fields'].get('Media'),'dimensions_text':p['fields'].get('Dimensions')}
                row.update(action='create',artwork_id=target,work=work,confidence=.99,
                           identity_basis='Distinct artwork ID and reproduction on the exact sampled creator page and complete index; catalogue title/translation and version checks found no unresolved collision.')
        if chosen:
            if chosen['creators']!=[{'artist_id':aid,'attribution_role':'primary','attribution_note':chosen['creators'][0]['attribution_note']}]:
                hold('Existing attribution is shared, qualified or differs from the source creator',candidate_ids=[chosen['id']])
            elif not direct and (kind(p['fields'].get('Media'))=='print' or chosen['work_type']=='print'):
                hold('A print title and date do not securely identify an accessioned impression',candidate_ids=[chosen['id']])
            elif not direct and kind(p['fields'].get('Media')) not in ['unknown',chosen['work_type']] and chosen['work_type']!='unknown':
                hold('Explicit media conflicts with the existing object type',candidate_ids=[chosen['id']])
            else:
                row.update(action='existing',artwork_id=chosen['id'],confidence=confidence,identity_basis=basis,
                           has_image=bool(chosen['primary_media_id']),baseline=chosen['artwork'])
                # This is the non-Louvre/non-Prado museum enrichment pass.
                museum=next((i for i in r.load(RUN/'institutions.json') if i['id']==chosen['current_institution_id']),{})
                if re.search(r'louvre|prado',json.dumps(museum),re.I):row['image_hold']='Louvre/Prado excluded from this museum image pass'
        if row.get('action') in ['create','existing']:
            if date and date['creation_year_end']>1970:row['image_hold']='Date range crosses 1970; editorial scope review required'
            row['source_policy']='User-approved WikiArt source policy, 6 October 2026; actual rights labels preserved separately, including unknown labels.'
        rows.append(row)
    # Detect source identifiers outside the scoped artist and concurrent imports.
    active=[x for x in rows if x['action'] in ['create','existing']]
    global_ids=collections.defaultdict(set)
    if active:
        for x in db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikiart-artwork' AND external_id=ANY(%s)",([x['source_id'] for x in active],)).fetchall():global_ids[x['external_id']].add(x['entity_id'])
        actual=snapshots(db,[x['artwork_id'] for x in active])
        for row in active:
            target=row['artwork_id'];prior=actual.get(target)
            if global_ids[row['source_id']]-{target}:
                row.update(action='hold',reason='Source ID already belongs to another production record',candidate_ids=sorted(global_ids[row['source_id']]))
            elif row['action']=='create' and prior:row.update(action='hold',reason='Deterministic source artwork ID already exists outside the saved catalogue scope')
            elif row['action']=='existing' and (not prior or prior['artwork']!=row['baseline']):
                row.update(action='hold',reason='Existing record changed since the initial production snapshot; preserve concurrent work')
    else:actual={}
    target_counts=collections.Counter(x['artwork_id'] for x in rows if x['action'] in ['create','existing'])
    for row in rows:
        if row['action'] in ['create','existing'] and target_counts[row['artwork_id']]>1:
            row.update(action='hold',reason='More than one selected source resolves to the same target; choose exact version first')
    data={'operation':m.OP,'artist':artist,'source_artist':pair['source'],'rows':rows,
          'source_index_count':len(idx['items'])+len(unlinked_index),'source_excluded_after_1970':len(idx['items'])-len(eligible),
          'unlinked_creator_leads':unlinked,'counts':dict(collections.Counter(x['action'] for x in rows)),
          'baseline_counts':{'works':len(works),'images':sum(bool(w['primary_media_id']) for w in works)},
          'selection':'User-requested personal 200-painter research selection; new records remain review, separate from museum designations.',
          'confidence_note':'Editorial confidence threshold; percentages are not statistically calibrated.',
          'authorization_sha256':r.sha((RUN/'authorization.json').read_bytes()),'at':r.now()}
    r.save_gz(dest,data);pin=r.sha(dest.read_bytes())
    before={x['artwork_id']:actual[x['artwork_id']] for x in rows if x['action']=='existing'}
    r.save_gz(BACKUP/'selection-preimages'/(aid+'.json.gz'),{'plan_sha256':pin,'records':before})
    r.save(RUN/'selection-pins'/(aid+'.json'),{'sha256':pin})
    return data


def select():
    totals=collections.Counter();done=0
    with r.connect('production') as db:
        for pair in m.cohort():
            existed=(RUN/'selections'/(pair['artist']['id']+'.json.gz')).exists()
            result=artist_plan(pair,db)
            if result:
                done+=1;totals.update(result['counts'])
                if not existed:print('Selected',result['artist']['display_name'],result['counts'],flush=True)
    m.status('selection',painters=done,counts=dict(totals));print('Completed plans',done,'/ 200',dict(totals),flush=True)


if __name__=='__main__':select()
