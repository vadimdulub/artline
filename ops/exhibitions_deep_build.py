#!/usr/bin/env python3
"""Assemble genuine local exhibition research; read-only catalogue crosswalks."""
import collections
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import exhibitions_common as c
from exhibitions_deep_local import DATA, eligible

TOPICS = {
    'Abstract Expressionism': r'\babstract expressionis[mt]\b',
    'Colour Field': r'\bcolou?r.field\b', 'Minimalism': r'\bminimalis[mt]\b',
    'Op art': r'\bop.art\b', 'Pop art': r'\bpop.art\b',
    'Constructivism': r'\bconstructivis[mt]\b', 'Bauhaus': r'\bbauhaus\b',
    'Geometric abstraction': r'\bgeometric(?:al)?\b',
    'Abstraction': r'\babstract(?:ion|ions)?\b', 'Colour': r'\bcolou?rs?\b',
    'Landscape': r'\blandscapes?\b', 'Portraiture': r'\bportraits?|portraiture\b',
    'Memory': r'\bmemory|memories\b', 'Identity': r'\bidentity|identities\b',
    'Nature': r'\bnature|natural world\b', 'Surrealism': r'\bsurreal(?:ism|ist)?\b',
    'Cubism': r'\bcubis[mt]\b', 'Impressionism': r'\bimpressionis[mt]\b',
    'Expressionism': r'\bexpressionis[mt]\b', 'Photography': r'\bphotograph(?:y|s|ic)?\b',
    'Printmaking': r'\bprints?|printmaking|etchings?|lithographs?\b',
    'Works on paper': r'\bpaper|drawings?|watercolou?rs?\b',
    'Sculpture': r'\bsculptures?\b', 'Collage': r'\bcollages?\b',
    'Politics': r'\bpolitic(?:s|al)\b', 'Spirituality': r'\bspiritual(?:ity)?\b',
    'Movement': r'\bmovement|motion\b', 'Material': r'\bmaterials?|texture\b',
    'Everyday life': r'\beveryday|daily life\b', 'Still life': r'\bstill.life\b',
    'The body': r'\bbody|bodies|figure|figurative\b',
}


def plain(s):
    text=s or ''
    return ' '.join((BeautifulSoup(text, 'html.parser').get_text(' ') if '<' in text else text).split())


def quote(s):
    words=plain(s).split()
    return ' '.join(words[:24]) + ('…' if len(words)>24 else '')


def build():
    paths=sorted((DATA/'shows').glob('*.json'))
    selected=[]
    accepted_path=DATA/'accepted.json'
    accepted=set(json.loads(accepted_path.read_text())) if accepted_path.exists() else None
    for path in paths:
        row=c.load(path)
        if row['show'] and not row['errors'] and eligible(row['show']) and (accepted is None or row['show']['internalID'] in accepted): selected.append(row)
    ids=[r['candidate']['id'] for r in selected]
    with c.connect() as db:
        links=db.execute('''SELECT DISTINCT p.source_person_id,p.artist_id::text,a.slug,a.display_name,
          m.storage_path portrait,m.attribution_text credit,m.license_label license,m.source_page_url source
          FROM exhibition_participants p JOIN artists a ON a.id=p.artist_id AND a.status<>'archived'
          LEFT JOIN media_assets m ON m.id=a.portrait_media_id
          WHERE p.exhibition_id=ANY(%s::uuid[]) AND p.source_person_id IS NOT NULL''',(ids,)).fetchall()
    identities=collections.defaultdict(dict)
    for l in links: identities[l['source_person_id']][l['artist_id']]=l
    artist_map={k:next(iter(v.values())) for k,v in identities.items() if len(v)==1}
    records=[]
    for saved in selected:
        original=saved['candidate'];s=saved['show'];payload=original['payload'];eid=original['id'];url=original['url']
        source_text=plain(s.get('description') or s.get('pressRelease'))
        topics=[key for key,pattern in TOPICS.items() if re.search(pattern,plain(s.get('description'))+' '+plain(s.get('pressRelease')),re.I)][:6]
        artists={a['internalID']:a for a in (s.get('artists') or [])+(s.get('artistsWithoutArtworks') or [])}
        for edge in s['artworksConnection']['edges']:
            for a in edge['node'].get('artists') or []: artists.setdefault(a['internalID'],a)
        participants=[]
        for aid,a in artists.items():
            match=artist_map.get(aid,{})
            participants.append(dict(id=c.uid('deep/artist/'+aid),sourceID=aid,name=a['name'],role='artist',
              artist_id=match.get('artist_id'),artist_slug=match.get('slug'),sourceURL='https://www.artsy.net/artist/'+a['slug'],
              birthday=a.get('birthday'),deathday=a.get('deathday'),nationality=a.get('nationality'),portrait=match.get('portrait'),
              imageCredit=match.get('credit'),imageLicense=match.get('license'),imageSource=match.get('source')))
        works=[]
        for edge in s['artworksConnection']['edges']:
            a=edge['node'];works.append(dict(id=c.uid('deep/entry/'+eid+'/'+a['internalID']),artworkId=None,
              title=a.get('title'),creator=a.get('artistNames'),date=a.get('date'),medium=a.get('medium'),catalogueNumber=None,
              participation='catalogued',sourcePage=None,sourceURL='https://www.artsy.net/artwork/'+a['slug'],provider='artsy',
              sourceCaption=None,image=None,imageCredit=None,imageLicense=None,imageSource=None,
              sourceArtworkID=a['internalID'],sourceArtistIDs=[x['internalID'] for x in a.get('artists') or []]))
        partner=payload.get('partner') or {};location=payload.get('location') or {}
        venues=[] if payload.get('isOnlineExclusive') else [dict(name=partner.get('name'),city=location.get('city') or payload.get('city'),country=location.get('country'),museum_slug=None,start_date=original['startDate'],end_date=original['endDate'])]
        names=[a['name'] for a in participants]
        artist_text=', '.join(names[:3])+(' and other artists' if len(names)>3 else '')
        overview=f"{len(works)} works are documented in the public exhibition list, with {artist_text}."
        media=collections.Counter(w['medium'] for w in works if w['medium'])
        if media: overview+=' Recorded media include '+', '.join(k for k,v in media.most_common(3))+'.'
        records.append(dict(id=eid,title=original['title'],alternateTitles=[],startDate=original['startDate'],endDate=original['endDate'],
          startYear=int(original['startDate'][:4]),endYear=int(original['endDate'][:4]),dates='',datePrecision='day',state='held',
          stateBasis='The source identifies a closed exhibition with historical dates. Artwork participation is documented by the public show listing.',
          format='online' if payload.get('isOnlineExclusive') else 'physical',checklistState='partial',entryCount=len(works),
          participantCount=len(participants),venueCount=len(venues),venues=venues,participants=participants,entries=works,
          sources=[dict(provider='artsy',source_record_id=s['internalID'],url=url,retrieved_at=saved['receipt']['retrieved_at'],interpretation={})],
          publications=[dict(kind='press_release',title='Exhibition description and curatorial text',url=s.get('pressReleaseUrl') or url,author=partner.get('name'),source_identifier=s['internalID'])],
          research=dict(overview=overview,excerpt=quote(source_text),excerptSource=url,concepts=topics,
            conceptBasis='Reading terms indexed from the source description and press release; these are not curator-assigned classifications.',
            publicListComplete=True,publicListTotal=len(works),scope='Complete public online list. A final physical exhibition checklist has not been established.',
            presenter=partner.get('name'),reviewedAt=saved['receipt']['retrieved_at'][:10]),featured=False))
    # Source identities already reconciled in the catalogue must stay reconciled.
    unique={}
    for row in records:
        previous=unique.get(row['id'])
        if previous:
            for key in ['entries','participants']:
                previous[key]=list({x['id']:x for x in previous[key]+row[key]}.values())
            previous['sources']+=row['sources'];previous['publications']+=row['publications']
            previous['entryCount']=len(previous['entries']);previous['participantCount']=len(previous['participants'])
            previous['research']['publicListTotal']=previous['entryCount']
            previous['research']['overview']=f"{previous['entryCount']} distinct works are documented across the reconciled public listings for this exhibition."
            previous['research']['scope']='Complete public lists from both reconciled source records. A final physical exhibition checklist has not been established.'
            previous['research']['concepts']=list(dict.fromkeys(previous['research']['concepts']+row['research']['concepts']))
        else: unique[row['id']]=row
    records=list(unique.values())
    # One illustrated museum study gives the archive a concrete, source-backed entrance.
    eid='cf8a5362-6ba5-5d02-9337-ee235a700cd2'
    detail=requests.get('http://127.0.0.1:8097/api/v1/exhibitions/'+eid,timeout=30);detail.raise_for_status();d=detail.json()
    response=requests.get('http://127.0.0.1:8097/api/v1/exhibitions/'+eid+'/entries',params={'limit':100},timeout=30);response.raise_for_status();works=response.json()
    assert not works['hasMore'] and len(works['items'])==works['total']
    d['entries']=works['items'];d['featured']=True
    # Fill missing captions only from already matched catalogue object identities.
    linked_ids=[entry['artworkId'] for entry in d['entries'] if entry.get('artworkId')]
    with c.connect() as db:
        captions=db.execute('''SELECT a.id::text,a.date_display,a.medium_text,
          (SELECT jsonb_agg(jsonb_build_object('name',p.display_name,'role',aa.attribution_role,'artist_id',p.id,'artist_slug',p.slug) ORDER BY p.display_name)
           FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id
           WHERE aa.artwork_id=a.id AND p.status<>'archived') creators
          FROM artworks a WHERE a.id=ANY(%s::uuid[]) AND a.status<>'archived' ''',(linked_ids,)).fetchall()
    caption_map={r['id']:r for r in captions}
    participant_artists={p.get('artist_id') for p in d['participants'] if p.get('artist_id')}
    for entry in d['entries']:
        caption=caption_map.get(entry.get('artworkId'))
        if not caption:continue
        entry['catalogueMetadataEvidence']=caption
        if not entry.get('creator') and caption.get('creators'):
            entry['creator']='; '.join((a['role'].replace('_',' ')+' ' if a['role']!='primary' else '')+a['name'] for a in caption['creators'])
        if not entry.get('date'):entry['date']=caption.get('date_display')
        if not entry.get('medium'):entry['medium']=caption.get('medium_text')
        for artist in caption.get('creators') or []:
            if artist['role']=='primary' and artist['artist_id'] not in participant_artists:
                d['participants'].append(dict(id=c.uid('deep/catalogue-artist/'+artist['artist_id']),name=artist['name'],role='artist',
                  artist_id=artist['artist_id'],artist_slug=artist['artist_slug'],evidence='Creator of an exactly matched exhibition artwork; existing catalogue attribution preserved.'))
                participant_artists.add(artist['artist_id'])
    d['participantCount']=len(d['participants'])
    source='https://www.clevelandart.org/exhibitions/picasso-and-paper';c.capture(source)
    d['research']=dict(overview='Paper served Picasso both as a surface for drawing and as a material to cut, fold, paste and construct. The exhibition follows those experiments across his career, connecting studies, prints, collages and paper sculptures with larger painting projects.',
      excerpt='',excerptSource=source,concepts=['Works on paper','Collage','Cubism','Sculpture'],conceptBasis='Editorial reading topics supported by the museum’s exhibition description.',
      publicListComplete=False,publicListTotal=len(d['entries']),scope='All associated Cleveland collection records retrieved. This is a partial exhibition checklist; works borrowed from other collections are not fully represented.',presenter='Cleveland Museum of Art / Royal Academy of Arts',reviewedAt=c.TODAY.isoformat())
    illustrated=[e for e in d['entries'] if e.get('image')]
    d['previewWorks']=illustrated[:3]
    records.append(d)
    result=dict(version=1,createdAt=c.now(),records=records)
    # Preserve the subsequent exact-object enrichment on repeat local builds.
    from exhibition_artworks_local import DATA as ARTWORK_DATA, assemble
    if (ARTWORK_DATA/'baseline.json.gz').exists():
        result,_,_=assemble(result)
        from exhibition_images_local import DATA as IMAGE_DATA, attach
        if (IMAGE_DATA/'selected.json.gz').exists():result=attach(result)
        records=result['records']
    destination=DATA/'review-corpus.json';tmp=destination.with_suffix('.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False));tmp.replace(destination)
    report=dict(exhibitions=len(records),completePublicLists=sum(r['research']['publicListComplete'] for r in records),sourceListings=len(selected),entries=sum(r['entryCount'] for r in records),
      participantConnections=sum(len(r['participants']) for r in records),
      artistConnections=sum(p['role']=='artist' for r in records for p in r['participants']),canonicalArtistConnections=sum(bool(p.get('artist_id')) for r in records for p in r['participants']),
      sourceDescriptions=len(records),withIndexedConcepts=sum(bool(r['research']['concepts']) for r in records),
      certifiedCompleteChecklists=0,localOnly=True,productionWrites=0,localCatalogueWrites=0)
    (DATA/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))


if __name__=='__main__':build()
