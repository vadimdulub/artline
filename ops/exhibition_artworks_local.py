#!/usr/bin/env python3
"""Object-level exhibition research and local artwork records; no DB writes."""
import argparse
import collections
import copy
import json
import re
import time

from bs4 import BeautifulSoup
import exhibitions_common as c
from exhibitions_deep_local import DATA as BASE

DATA=BASE.parent/'exhibition-artworks-local-20261012'
FIELDS='''internalID slug title date artistNames medium dimensions { cm in }
exhibitionHistory literature provenance imageRights attributionClass { name }'''


def text(value):
    value=value or ''
    return BeautifulSoup(value,'html.parser').get_text('\n') if '<' in value else value


def collect():
    baseline=DATA/'baseline.json.gz'
    if not baseline.exists():c.save(baseline,c.load(BASE/'review-corpus.json'))
    corpus=c.load(baseline)
    ids=sorted({e['sourceArtworkID'] for r in corpus['records'] for e in r['entries'] if e.get('sourceArtworkID') and e['provider']=='artsy'})
    for start in range(0,len(ids),50):
        batch=ids[start:start+50];path=DATA/'artsy-batches'/f'{start//50:04d}.json.gz'
        if path.exists():continue
        query='query ArtlineExhibitedArtworkEvidence { artworks(ids:'+json.dumps(batch)+',first:100) { totalCount pageInfo{hasNextPage} edges{node{'+FIELDS+'}}}}'
        raw,receipt=c.capture('https://metaphysics-cdn.artsy.net/v2',{'query':query});payload=json.loads(raw)
        if payload.get('errors'):raise RuntimeError('Source field errors: '+json.dumps(payload['errors']))
        data=(payload.get('data') or {}).get('artworks')
        if not data or data['pageInfo']['hasNextPage']:raise RuntimeError('Incomplete source object page')
        rows=[e['node'] for e in data['edges']];returned={r['internalID'] for r in rows}
        if len(rows)!=len(returned) or not returned<=set(batch):raise RuntimeError('Source returned conflicting artwork IDs')
        c.save(path,dict(requested=batch,missing=sorted(set(batch)-returned),artworks=rows,receipt=receipt))
        print(json.dumps(dict(requested=min(start+50,len(ids)),total=len(ids),returned=len(rows),histories=sum(bool(r.get('exhibitionHistory')) for r in rows))),flush=True)
        time.sleep(.25)


def collect_museum():
    corpus=c.load(DATA/'baseline.json.gz')
    ids=sorted({e['evidence']['id'] for r in corpus['records'] for e in r['entries'] if e['provider']=='cleveland'})
    for native in ids:
        path=DATA/'cleveland'/f'{native}.json.gz'
        if path.exists():continue
        raw,receipt=c.capture(f'https://openaccess-api.clevelandart.org/api/artworks/{native}')
        row=json.loads(raw)['data']
        if row['id']!=native:raise RuntimeError('Museum object identity mismatch')
        c.save(path,dict(artwork=row,receipt=receipt))
        print(native,flush=True)


def history_match(history, exhibition):
    """Require title, venue and event year in one explicit object-history line.

    The work already belongs to this source event by exact native IDs. This adds
    the source's object-history assertion, not independent installation proof.
    Unrelated histories, online events and tentative/withdrawn loans do not qualify.
    """
    if exhibition['format']!='physical' or exhibition['state']!='held':return None
    title=c.norm(exhibition['title'])
    if len(title)<10 or len(title.split())<2:return None
    venues=[c.norm(v.get('name') or '') for v in exhibition['venues']]
    years={str(exhibition['startYear']),str(exhibition['endYear'])}
    for line in re.split(r'[\n;]+',text(history)):
        clean=' '+c.norm(line)+' '
        if re.search(r'\b(withdrawn|cancelled|canceled|proposed|planned|not exhibited|not shown|online|virtual)\b',clean):continue
        if ' '+title+' ' not in clean:continue
        if not any(len(venue)>=4 and ' '+venue+' ' in clean for venue in venues):continue
        if not years.intersection(re.findall(r'\b(?:19|20)\d{2}\b',line)):continue
        return line
    return None


def assemble(corpus):
    corpus=copy.deepcopy(corpus)
    source={};receipts={};requested=set();missing=set()
    for path in sorted((DATA/'artsy-batches').glob('*.json.gz')):
        batch=c.load(path);requested.update(batch['requested']);missing.update(batch['missing'])
        for row in batch['artworks']:
            source[row['internalID']]=row;receipts[row['internalID']]=batch['receipt']
    expected={e['sourceArtworkID'] for r in corpus['records'] for e in r['entries'] if e['provider']=='artsy'}
    if requested!=expected:raise RuntimeError('Complete selected object research before assembly')
    # Reuse a source creator identity only when a securely linked object's primary
    # catalogue creator matches that native creator's exact name. Never infer the
    # maker from an exhibition title or attach all show participants to a work.
    museum_creators={}
    crosswalk_path=DATA/'museum-creator-crosswalk-evidence.json'
    if crosswalk_path.exists():
        evidence=c.load(crosswalk_path);candidates=evidence['catalogueCandidates']
        if len(candidates)==1:
            a=candidates[0];description=evidence['sourceDescription']
            if c.norm(a['display_name'])==c.norm(description.split(' (')[0]) and str(a['birth_year']) in description and str(a['death_year']) in description:
                museum_creators[evidence['sourceCreatorID']]=dict(artist_id=a['id'],artist_slug=a['slug'],name=a['display_name'],role='primary')
    for exhibition in corpus['records']:
        for entry in exhibition['entries']:
            if entry['provider']!='cleveland':continue
            row=c.load(DATA/'cleveland'/f"{entry['evidence']['id']}.json.gz")['artwork']
            for artist in entry.get('catalogueMetadataEvidence',{}).get('creators') or []:
                if artist['role']!='primary':continue
                for native in row.get('creators',[]):
                    if native.get('role')=='artist' and c.norm(native['description'].split(' (')[0])==c.norm(artist['name']):
                        previous=museum_creators.get(native['id'])
                        if previous and previous['artist_id']!=artist['artist_id']:raise RuntimeError('Conflicting museum creator crosswalk')
                        museum_creators[native['id']]=artist
    objects={};promotions=[];museum_verified=0
    for exhibition in corpus['records']:
        people={p.get('sourceID'):p for p in exhibition['participants'] if p.get('sourceID')}
        for entry in exhibition['entries']:
            provider=entry['provider'];native=str(entry.get('sourceArtworkID') or entry.get('evidence',{}).get('id') or '')
            if not native:raise RuntimeError('Missing exact source artwork identity')
            local_id=c.uid('deep/artwork/'+provider+'/'+native);entry['localArtworkId']=local_id
            evidence=dict(kind='exhibition_listing',note='The artwork appears in the exhibition’s public online list. Physical installation is not independently established.',url=entry['sourceURL'])
            artists=[copy.deepcopy(people[artist]) for artist in entry.get('sourceArtistIDs',[]) if artist in people]
            row={};history=None;receipt=None;dimensions=None;attribution=None
            if provider=='artsy':
                row=source.get(native,{})
                receipt=receipts.get(native)
                history=history_match(row.get('exhibitionHistory'),exhibition)
                dimensions=(row.get('dimensions') or {}).get('cm') or (row.get('dimensions') or {}).get('in')
                attribution=(row.get('attributionClass') or {}).get('name')
                if history:
                    entry['participation']='exhibited'
                    evidence=dict(kind='object_exhibition_history',note='The source’s object exhibition history names this exhibition, venue and year. This is a source-reported participation record.',url=entry['sourceURL'],retrievedAt=receipt.get('retrieved_at'))
                    promotions.append(dict(exhibitionId=exhibition['id'],entryId=entry['id'],artworkId=local_id,matchedHistoryLine=history,receipt=receipt))
            elif provider=='cleveland':
                collected=c.load(DATA/'cleveland'/f'{native}.json.gz');row=collected['artwork'];receipt=collected['receipt']
                exhibition_ids={str(s['source_record_id']) for s in exhibition['sources'] if s['provider']=='cleveland'}
                histories=(row.get('exhibitions') or {}).get('current',[])
                matched=[h for h in histories if str(h.get('id')) in exhibition_ids]
                if not matched:raise RuntimeError('Museum participation needs an exact exhibition history ID')
                museum_verified+=1
                entry['participation']='exhibited'
                evidence=dict(kind='museum_object_history',note='The museum’s object record explicitly links this work to this exhibition. The record does not establish participation at every touring venue.',url=row['url'],retrievedAt=receipt.get('retrieved_at'))
                entry['date']=entry.get('date') or row.get('creation_date');entry['medium']=entry.get('medium') or row.get('technique')
                creators=[a for a in row.get('creators',[]) if a.get('role')=='artist']
                entry['creator']=entry.get('creator') or '; '.join(' '.join(filter(None,[a.get('qualifier'),a.get('extent'),a['description']])) for a in creators) or None
                dimensions=row.get('measurements')
                artists=[dict(id=c.uid('deep/catalogue-artist/'+a['artist_id']),name=a['name'],role=a['role'],artist_id=a['artist_id'],artist_slug=a['artist_slug']) for a in (entry.get('catalogueMetadataEvidence',{}).get('creators') or [])]
                known={a['artist_id'] for a in artists}
                for creator in creators:
                    matched_artist=museum_creators.get(creator['id'])
                    if matched_artist and not creator.get('qualifier') and not creator.get('extent') and matched_artist['artist_id'] not in known:
                        a=matched_artist
                        artists.append(dict(id=c.uid('deep/catalogue-artist/'+a['artist_id']),name=a['name'],role='artist',artist_id=a['artist_id'],artist_slug=a['artist_slug']))
                        known.add(a['artist_id'])
            entry['participationEvidence']=evidence
            obj=objects.get(local_id)
            if obj is None:
                obj={k:entry.get(k) for k in ['artworkId','title','creator','date','medium','provider','sourceCaption','image','imageCredit','imageLicense','imageSource']}
                obj.update(id=local_id,sourceArtworkID=native,sourceURL=(row.get('url') if provider=='cleveland' else None) or entry['sourceURL'],artists=artists,
                  dimensions=dimensions,attribution=attribution,sourceImageRights=row.get('imageRights'),appearances=[],localStudy=True,
                  identityBasis='This record follows the source’s identified object or edition. Other versions may have separate records.',
                  hasSourceExhibitionHistory=bool(row.get('exhibitionHistory')) or provider=='cleveland')
                objects[local_id]=obj
            else:
                known={a['id'] for a in obj['artists']}
                obj['artists'].extend(a for a in artists if a['id'] not in known)
            obj['appearances'].append(dict(id=entry['id'],exhibitionId=exhibition['id'],title=exhibition['title'],startDate=exhibition['startDate'],endDate=exhibition['endDate'],dates=exhibition['dates'],
              startYear=exhibition['startYear'],format=exhibition['format'],venues=[{k:v.get(k) for k in ['name','start_date','end_date']} for v in exhibition['venues'] if v.get('name')],participation=entry['participation'],evidence=evidence))
        exhibition['participationCounts']=dict(collections.Counter(e['participation'] for e in exhibition['entries']))
        exhibition['localArtworkCount']=len({e['localArtworkId'] for e in exhibition['entries']})
        known_people={p.get('artist_id') for p in exhibition['participants'] if p.get('artist_id')}
        for entry in exhibition['entries']:
            for artist in objects[entry['localArtworkId']]['artists']:
                if artist.get('artist_id') and artist['artist_id'] not in known_people:
                    person=copy.deepcopy(artist);person['role']='artist'
                    exhibition['participants'].append(person);known_people.add(artist['artist_id'])
        exhibition['participantCount']=len(exhibition['participants'])
    for obj in objects.values():
        obj['appearanceCount']=len(obj['appearances'])
        obj['appearances'].sort(key=lambda a:a['id'])
    corpus['artworks']=sorted(objects.values(),key=lambda a:a['id'])
    corpus['artworkResearchAt']=c.now()
    report=dict(exhibitions=len(corpus['records']),exhibitionsWithLocalArtworks=sum(bool(r['entries']) for r in corpus['records']),
      uniqueLocalArtworks=len(objects),artworkAppearances=sum(a['appearanceCount'] for a in objects.values()),
      sourceObjectsRequested=len(requested),sourceObjectsReturned=len(source),sourceObjectsUnavailable=sorted(missing),
      withObjectExhibitionHistories=sum(bool(a.get('exhibitionHistory')) for a in source.values()),
      newObjectHistoryParticipation=len(promotions),museumObjectHistoryParticipation=museum_verified,
      participation=dict(collections.Counter(e['participation'] for r in corpus['records'] for e in r['entries'])),
      sourceHistoryExhibitions=len({p['exhibitionId'] for p in promotions}),
      repeatedObjects=sum(a['appearanceCount']>1 for a in objects.values()),maxAppearances=max(a['appearanceCount'] for a in objects.values()),
      canonicalArtworkLinks=sum(bool(a['artworkId']) for a in objects.values()),localOnly=True,databaseWrites=0)
    report['artworksWithArtistConnections']=sum(bool(a['artists']) for a in objects.values())
    return corpus,report,promotions


def build():
    corpus,report,promotions=assemble(c.load(DATA/'baseline.json.gz'))
    # Keep subsequent image attachments when regenerating the local object corpus.
    from exhibition_images_local import DATA as IMAGE_DATA, attach
    if (IMAGE_DATA/'selected.json.gz').exists():corpus=attach(corpus)
    for path,payload in [(DATA/'review-corpus.json',corpus),(BASE/'review-corpus.json',corpus),(DATA/'report.json',report),(DATA/'participation-evidence.json',promotions)]:
        temp=path.with_suffix('.tmp');temp.write_text(json.dumps(payload,ensure_ascii=False,indent=2 if path.name!='review-corpus.json' else None));temp.replace(path)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['collect','collect-museum','build']);args=p.parse_args()
    {'collect':collect,'collect-museum':collect_museum,'build':build}[args.action]()
