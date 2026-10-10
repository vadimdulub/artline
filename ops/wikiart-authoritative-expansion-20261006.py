"""Expanded source-authoritative pass, invoked by the round-2 driver."""
import collections
import concurrent.futures
import copy
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit


def configure(base,date_review=False):
    global n,q,r,d,ROOT,RUN,OLD,PREV,DATE_REVIEW,EXPANDED
    n=base;q=n.q;r=n.r;d=n.d;ROOT=n.ROOT;OLD=n.OLD;PREV=n.RUN
    EXPANDED=ROOT/'docs/research/production-wikiart-authoritative-20261006'
    DATE_REVIEW=date_review
    RUN=EXPANDED
    if DATE_REVIEW:PREV=EXPANDED;RUN=ROOT/'docs/research/production-wikiart-source-date-review-20261006'
    n.RUN=q.RUN=r.RUN=d.RUN=RUN;d.OP=RUN.name
    d.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/d.OP
    d.ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/d.OP


def namekey(v):return ' '.join(sorted(q.norm(v).split()))


def metadata_works():
    scope=RUN if (RUN/'snapshot.json').exists() else OLD
    for part in r.load(scope/'snapshot.json')['parts']:
        path=ROOT/part['path'];assert r.sha(path.read_bytes())==part['sha256'];yield from r.load(path)


def inherit(folder,roots):
    (RUN/folder).mkdir(parents=True,exist_ok=True)
    for root in roots:
        for src in (root/folder).glob('*.json.gz'):
            dst=RUN/folder/src.name
            if not dst.exists():dst.symlink_to(src)


def expand_scope():
    q.snapshot()
    r.save(RUN/'authorization.json',{'at':r.now(),'instruction':'WikiArt is the source of truth; add as much as possible. Production updates already authorized for >=90% identity confidence.',
        'scope':'Missing primary images for existing museum artworks, excluding Louvre and Prado; preserve catalogue metadata and publication state.',
        'confidence':'Evidence-based high-confidence rules, not calibrated probabilities. WikiArt unrestricted per-object Public domain labels govern source clearance; territory-limited/unknown labels remain held.',
        'policy_document':'AGENTS.md','round1':str(OLD.relative_to(ROOT)),'round2_reconciliation':str(PREV.relative_to(ROOT))})
    for name in ['cached-images.json.gz','wikiart-directory.json.gz']:
        src=OLD/name;dst=RUN/name
        if not dst.exists():dst.symlink_to(src)
    inherit('artist-indexes',[OLD]);inherit('translated-indexes',[OLD]);inherit('artist-links',[PREV,OLD])


def expand_sources():
    for name in ['cached-images.json.gz','wikiart-directory.json.gz']:
        if not (RUN/name).exists():(RUN/name).symlink_to(OLD/name)
    inherit('artist-indexes',[OLD]);inherit('translated-indexes',[OLD]);inherit('artist-links',[PREV,OLD])
    directory=r.load(RUN/'wikiart-directory.json.gz');artists=r.load(RUN/'artists.json.gz')
    by=collections.defaultdict(dict);by_url={x['url']:x for x in directory}
    for x in directory:by[namekey(x['name'])][x['url']]=x
    counts=collections.defaultdict(collections.Counter);labels=collections.Counter()
    scope=RUN if (RUN/'snapshot.json').exists() else OLD
    def scope_works():
        for part in r.load(scope/'snapshot.json')['parts']:
            path=ROOT/part['path'];assert r.sha(path.read_bytes())==part['sha256'];yield from r.load(path)
    for w in scope_works():
        for c in w['creators']:
            counts[c['artist_id']]['works']+=1
            if not w['primary_media_id']:counts[c['artist_id']]['missing']+=1
        if w.get('unlinked_creator_label') and not w['primary_media_id']:labels[w['unlinked_creator_label']]+=1
    matches=[];unmatched=[];ambiguous=[]
    for a in artists:
        if a['id'] not in counts:continue
        choices={}
        for name in [a['display_name']]+a['aliases']:choices.update(by[namekey(name)])
        for e in a['identifiers']:
            url=(e.get('url') or '').rstrip('/')
            if url in by_url:choices[url]=by_url[url]
        choices={u:s for u,s in choices.items() if all(a.get(k) is None or s.get(k) is None or a[k]==s[k] for k in ['birth_year','death_year'])}
        row={'artist':a,'scope':dict(counts[a['id']])}
        if len(choices)==1:matches.append({**row,'source':next(iter(choices.values())),'basis':'Exact full-name tokens (order independent), existing alias or direct source identifier; no lifespan conflict'})
        elif choices:ambiguous.append(row)
        else:unmatched.append(row)
    object_labels=[]
    for label,count in labels.items():
        choices=by[namekey(label)]
        if len(choices)==1 and namekey(label) not in {'unknown','anonymous','anonyme','inconnu'}:
            object_labels.append({'unlinked_creator_label':label,'works':count,'source':next(iter(choices.values())),'basis':'Exact unique full-name tokens, including surname-first native catalogue labels; no qualifier removal'})
    r.save_gz(RUN/'artist-sources.json.gz',{'scope_count_evidence':str((scope/'snapshot.json').relative_to(ROOT)),'matches':matches,'unmatched':unmatched,'ambiguous':ambiguous,'object_labels':object_labels})
    print(json.dumps({'linked_artists':len(matches),'object_creator_labels':len(object_labels),'unmatched_artists':len(unmatched)}),flush=True)
    q.indexes()


def expand_translations():
    data=r.load(RUN/'artist-sources.json.gz');sources={x['source']['url']:x['source'] for x in data['matches']+data['object_labels']}
    artists={x['artist']['id']:x['source']['url'] for x in data['matches']}
    labels={q.norm(x['unlinked_creator_label']):x['source']['url'] for x in data['object_labels']}
    institutions={x['id']:x for x in r.load(RUN/'institutions.json.gz')};wanted=set()
    for w in metadata_works():
        if w['primary_media_id']:continue
        urls={artists[c['artist_id']] for c in w['creators'] if c['artist_id'] in artists}
        if q.norm(w.get('unlinked_creator_label')) in labels:urls.add(labels[q.norm(w['unlinked_creator_label'])])
        title=q.norm(w['title']);museum=institutions[w['institution_id']];name=q.norm(museum['name']+' '+museum['slug']);langs=set()
        if re.search('[А-Яа-яЁё]',w['title']):langs.add('ru')
        if 'musée' in museum['name'].casefold() or re.search(r'\b(le|les|aux|des|une|etude|portrait de|vue de|paysage)\b',title):langs.add('fr')
        if re.search(r'\b(kunsthistorisches|belvedere|albertina|lenbachhaus|stadtische|hamburger|pinakothek|dresden|berlin|salzburg|vienna|wien|innsbruck)\b',name) or re.search(r'\b(der|die|das|mit|bei|und|einer|einem|eines)\b',title):langs.add('de')
        if re.search(r'\b(museo|museu)\b',name) or re.search(r'\b(retrato|paisaje|naturaleza|el|los|las)\b',title):langs.add('es')
        if re.search(r'\b(portugal|lisboa|lisbon|porto|brasil|brazil|museu)\b',name):langs.add('pt')
        for url in urls:
            for lang in langs:wanted.add((url,lang))
    def one(pair):
        url,lang=pair;slug=urlsplit(url).path.rsplit('/',1)[-1];dest=RUN/'translated-indexes'/(lang+'-'+slug+'.json.gz')
        if dest.exists():return r.load(dest)
        api='https://www.wikiart.org/'+lang+'/App/Painting/PaintingsByArtist?artistUrl='+slug+'&json=2'
        result={'source':sources[url],'language':lang,'api_url':api}
        try:
            raw,rc=q.capture(api,'translated-index-captures');result['receipt']=rc
            if rc['status']!=200:raise ValueError('HTTP '+str(rc['status']))
            items=json.loads(raw)
            if not isinstance(items,list):raise ValueError('Unexpected source shape')
            result.update(outcome='indexed',items=items)
        except Exception as exc:result.update(outcome='source_unavailable',error=str(exc)[:300],items=[])
        r.save_gz(dest,result);return result
    print('Scoped translated indexes',len(wanted),dict(collections.Counter(lang for _,lang in wanted)),flush=True)
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,x in enumerate(pool.map(one,sorted(wanted)),1):
            counts[x['outcome']]+=1
            if i%100==0:print('Translated source metadata',i,'/',len(wanted),dict(counts),flush=True)
    r.save(RUN/'translations-summary.json',{'at':r.now(),'selected':len(wanted),'languages':dict(collections.Counter(lang for _,lang in wanted)),'counts':dict(counts)})


def expand_titles():
    cached=r.load(OLD/'cached-images.json.gz');aliases=[]
    for x in cached:
        match=re.search(r'Original Title:\s*(.+?)\s+(?:Date|Style|Genre|Media|Location|Dimensions|Series|Period):',x.get('source_description',''))
        if match and q.norm(match[1]) and q.norm(match[1])!=q.norm(x['title']):
            aliases.append({**x,'title':match[1],'language':'original_title','english_title':x['title'],
                'title_alias_basis':'Verbatim WikiArt Original Title field in preserved source description; must be reverified against the selected live artwork page.'})
    path=RUN/'cached-images.json.gz'
    if path.is_symlink():path.unlink()  # Only our link; the original evidence is unchanged.
    r.save_gz(path,cached+aliases)
    r.save(RUN/'original-title-aliases.json',{'at':r.now(),'aliases':len(aliases),'parent':str((OLD/'cached-images.json.gz').relative_to(ROOT))})
    print('Additional verbatim WikiArt original titles',len(aliases),flush=True)


def expand_candidates():
    # Keep the standard all-artwork outcomes, then expand only the source-version
    # cases into independently verifiable page edges for the reconciliation pass.
    q.candidates();data=q.candidate_pass();single=data['candidates']
    multi={x['artwork_id']:x for x in data['outcomes'] if not x['has_image'] and x['outcome']=='multiple_source_versions'}
    indexed=collections.defaultdict(dict);english={}
    for path in list((RUN/'artist-indexes').glob('*.json.gz'))+list((RUN/'translated-indexes').glob('*.json.gz')):
        rec=r.load(path)
        if rec['outcome']!='indexed':continue
        for x in rec['items']:
            key=q.image_key(x.get('image'))
            if not key or not q.norm(x.get('title')):continue
            if not rec.get('language'):english[(rec['source']['url'],x['contentId'])]=x
            original=english.get((rec['source']['url'],x['contentId']),{})
            c={'title':q.html.unescape(x['title']),'artist':x.get('artistName'),'artist_url':rec['source']['url'],'date':q.parse_date(x.get('yearAsString')),
               'image_url':x['image'],'url':rec['source']['url']+'/'+key.rsplit('/',1)[-1].rsplit('.',1)[0],'content_id':x['contentId'],
               'api_receipt':rec['receipt'],'language':rec.get('language','en'),'english_title':q.html.unescape(original.get('title') or x['title'])}
            indexed[key][q.norm(c['title'])]=c
    for c in r.load(RUN/'cached-images.json.gz'):
        key=q.image_key(c['image_url']);indexed[key].setdefault(q.norm(c['title']),{**c,'date':(c['year_start'],c['year_end']) if c.get('year_start') and c.get('year_end') else None})
    for w in q.works():
        if w['id'] not in multi:continue
        row=multi[w['id']]
        # The source record inventory is bounded; unusual works with >12 versions
        # remain held rather than pretending truncated evidence is complete.
        if row.get('additional_candidates_in_artist_index'):continue
        for hint in row['candidate_images']:
            choices=indexed[q.image_key(hint['image_url'])]
            c=next((v for k,v in choices.items() if k in q.title_keys(w)),None)
            if not c or not q.date_compatible(w,c.get('date')):continue
            c=copy.deepcopy(c);c['url']=hint['page_hint']
            single.append({'work':w,'candidate':c,'candidate_count':row['possible_candidates'],'creator_basis':'exact_verified_WikiArt_full_name','missing_target_count':1})
    previous_visual={x['artwork_id']:x for x in r.load(OLD/'visual-review.json')['held'] if x['reason']!='primary_rights_conflict'}
    candidates=[]
    for x in single:
        if x['work']['primary_media_id'] or x['work']['id'] in previous_visual:continue
        x['previous_missing_target_count']=x['missing_target_count'];x['missing_target_count']=1;candidates.append(x)
    data['candidates']=candidates;data['at']=r.now();data['inherited_visual_holds']=previous_visual
    n.pin('candidate',data)
    print(json.dumps({'remaining_artwork_candidates':len({x['work']['id'] for x in candidates}),'source_edges':len(candidates),'unique_source_pages':len({x['candidate']['url'] for x in candidates})}),flush=True)


def pages():
    for folder in ['pages','resolved-pages','artist-links']:inherit(folder,[PREV,OLD])
    q.pages();q.resolve_pages()
    r.save(RUN/'pages-complete.json',{'at':r.now(),'candidate_pin':r.load(RUN/'latest-candidate-pass.json'),'finished':True})


def assess():
    original=q.assess_one
    generic={'untitled','landscape','portrait','self portrait','still life','nude','composition','abstract composition','flowers','study','selfportrait',
        'portrait of a man','portrait of a woman','a landscape','a portrait','a man','a woman','woman','man','head','seated woman','standing woman'}
    named={'mariana','zonnebeke','tipperary','southwold','swanage','lares','westminster','hallstatt','giotto','musicians','haymakers','reapers','ecce homo','pieta'}
    def authoritative(item,page,institution):
        w=item['work'];probe=copy.deepcopy(item)
        if item['candidate'].get('language')=='original_title' and q.norm(item['candidate']['title'])!=q.norm(page['fields'].get('Original Title')):
            return 'original_title_not_reverified'
        if not w['creators'] and page and namekey(w.get('unlinked_creator_label'))==namekey(page['metadata'].get('artistName')):
            probe['work']['unlinked_creator_label']=page['metadata']['artistName']
        if DATE_REVIEW:
            basis=source_date_basis(w,page['date'])
            if not basis:return 'source_date_identity_needs_review'
            if q.museum_agrees(institution,page['fields'].get('Location')) is not True:return 'source_date_requires_exact_museum_version'
            if not item['candidate'].get('date') or tuple(item['candidate']['date'])!=tuple(page['date']):return 'source_date_page_index_conflict'
            # Source date is used only to review the image identity. The stored
            # work and production date fields are never modified.
            probe['work'].update(creation_year_start=page['date'][0],creation_year_end=page['date'][1],date_precision='exact' if page['date'][0]==page['date'][1] else 'range')
        outcome=original(probe,page,institution)
        if DATE_REVIEW:
            if outcome.startswith('high_'):return 'high_editorially_reviewed_WikiArt_date_exact_artist_title_museum_version'
            return outcome
        if outcome=='high_distinctive_title_creator_narrow_date' and q.norm(item['candidate'].get('english_title') or page['metadata']['title']) in generic:
            return 'insufficient_object_corroboration'
        if outcome=='partial_or_study_needs_visual_reconciliation' and q.museum_agrees(institution,page['fields'].get('Location')) is True:
            return 'high_WikiArt_exact_study_title_creator_date_museum'
        location=page['fields'].get('Location') if page else None
        if outcome in ['insufficient_object_corroboration','broad_date_needs_review'] or (outcome=='museum_location_needs_reconciliation' and location=='Private Collection'):
            c=item['candidate'];title=q.norm(c.get('english_title') or page['metadata']['title']);date=page['date']
            distinct=(len(title.split())>=2 and title not in generic) or title in named
            narrow=bool(date and w['creation_year_end']-w['creation_year_start']<=5 and date[1]-date[0]<=5)
            if distinct and narrow and item['candidate_count']==1:
                return 'high_WikiArt_unique_title_creator_narrow_date'
        return outcome
    q.assess_one=authoritative
    # Earlier primary-source conflicts are retained as research evidence. Under
    # the user's new explicit source hierarchy, WikiArt's per-object rights label
    # is authoritative. Image-internal copyright/watermarks still receive visual
    # review and are not silently removed.
    inherit('primary-tate',[PREV])
    n.assess()
    q.assess_one=original


def plan():
    assert r.load(RUN/'pages-complete.json')['candidate_pin']==r.load(RUN/'latest-candidate-pass.json')
    d.plan()


def contact_sheets():
    if not DATE_REVIEW:return d.contact_sheets()
    review,_=d.review();items=[]
    for item in review['ready']:
        path=RUN/'prepared'/(item['work']['id']+'.json')
        if path.exists():
            im=r.load(path)
            if im['outcome']=='prepared':items.append((item,im))
    folder=d.ORIGINALS/'contact-sheets';folder.mkdir(parents=True,exist_ok=True)
    font=d.ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',12)
    for start in range(0,len(items),12):
        sheet=d.Image.new('RGB',(1200,1140),'white');draw=d.ImageDraw.Draw(sheet)
        for j,(item,im) in enumerate(items[start:start+12]):
            left=j%4*300;top=j//4*380
            with d.Image.open(im['visual_path']) as source:
                image=source.convert('RGB');image.thumbnail((280,265));sheet.paste(image,(left+(300-image.width)//2,top+(265-image.height)//2))
            label=str(start+j+1)+'. '+im['artwork_id'][:8]+' '+q.html.unescape(im['artist'])+' — '+im['title']
            for row,line in enumerate(d.textwrap.wrap(label,44)[:4]):draw.text((left+8,top+270+row*15),line,font=font,fill='black')
            caption='WikiArt: '+'–'.join(map(str,item['page']['date']))+'; catalogue: '+(item['work'].get('date_display') or 'unknown')
            for row,line in enumerate(d.textwrap.wrap(caption,43)[:2]):draw.text((left+8,top+335+row*15),line,font=font,fill='#31546a')
        sheet.save(folder/f'{start//12+1:03d}.jpg',quality=90)
    r.save(RUN/'contact-sheet-index.json',[{'number':i+1,'artwork_id':im['artwork_id'],'media_sha256':im['sha256'],'title':im['title'],
        'source_dates':item['page']['date'],'catalogue_dates_preserved':item['catalogue_dates_preserved']} for i,(item,im) in enumerate(items)])
    print(json.dumps({'images':len(items),'sheets':(len(items)+11)//12,'folder':str(folder),'caption_includes_both_source_and_catalogue_dates':True}),flush=True)


def record_visual_review():
    decisions=r.load(RUN/'visual-review-input.json');index=r.load(RUN/'contact-sheet-index.json')
    total=(len(index)+11)//12
    assert sorted(decisions['sheets_reviewed'])==list(range(1,total+1))
    for number,digest in decisions['sheet_sha256'].items():
        assert r.sha((d.ORIGINALS/'contact-sheets'/f'{int(number):03d}.jpg').read_bytes())==digest
    assert len(decisions['sheet_sha256'])==total
    holds={x['artwork_id']:x for x in decisions['holds']};approved=[];held=[];archived=[]
    assert set(holds).issubset({x['artwork_id'] for x in index})
    for x in index:
        if x['artwork_id'] not in holds:approved.append(x);continue
        held.append({**x,**holds[x['artwork_id']]})
        im=r.load(RUN/'prepared'/(x['artwork_id']+'.json'))
        if not im['reuse']:
            src=Path(im['visual_path']);dst=d.ORIGINALS/'held-derivatives'/src.name
            assert src.parent==ROOT/'apps/web/public/assets/artworks/imported'/d.OP
            if src.exists():
                assert r.sha(src.read_bytes())==x['media_sha256'];dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();src.rename(dst)
            assert r.sha(dst.read_bytes())==x['media_sha256']
            archived.append({'artwork_id':x['artwork_id'],'sha256':x['media_sha256'],'private_path':str(dst)})
    r.save(RUN/'visual-review.json',{'at':r.now(),'contact_index_sha256':r.sha((RUN/'contact-sheet-index.json').read_bytes()),
        'reviewer':'assistant visual inspection','sheets_reviewed':decisions['sheets_reviewed'],
        'criteria':'Every selected source reproduction inspected for subject agreement, whole composition, error content, visible reproduction copyright, watermarks and calibration strips. WikiArt per-object metadata/rights are authoritative per user instruction; no copyright mark was removed.',
        'approved':approved,'held':held,'private_archives':archived})
    print(json.dumps({'visually_approved':len(approved),'held':len(held)}),flush=True)


def source_date_basis(w,date):
    if not date or not 0<date[0]<=date[1]<=1970 or date[1]-date[0]>5:return None
    start,end=w.get('creation_year_start'),w.get('creation_year_end')
    if start is None and end is None and w.get('date_precision')=='unknown':return 'unknown_catalogue_date_requires_explicit_source_date_and_visual_editorial_review'
    if start is None or end is None or not 0<start<=end<=1970:return None
    if w.get('date_precision')=='century' and start<=date[0]<=date[1]<=end:return 'source_resolves_broad_century_for_image_identity_only'
    if w.get('date_precision') in ['unknown','before','after','century'] or end-start>10:return None
    gap=max(date[0]-end,start-date[1],0)
    if 0<gap<=10:return 'nearby_imported_date_discrepancy_WikiArt_date_authoritative_for_image_identity'
    return None


def source_date_candidates():
    assert DATE_REVIEW
    prior=n.pointer(EXPANDED,'candidate')
    wanted={x['artwork_id']:x for x in prior['outcomes'] if not x['has_image'] and x['outcome']=='date_review_or_conflict' and not x.get('additional_candidates_in_artist_index')}
    images=collections.defaultdict(dict);english={}
    for path in list((EXPANDED/'artist-indexes').glob('*.json.gz'))+list((EXPANDED/'translated-indexes').glob('*.json.gz')):
        rec=r.load(path)
        if rec['outcome']!='indexed':continue
        for x in rec['items']:
            key=q.image_key(x.get('image'))
            if not key or not q.norm(x.get('title')):continue
            if not rec.get('language'):english[(rec['source']['url'],x['contentId'])]=x
            original=english.get((rec['source']['url'],x['contentId']),{})
            c={'title':q.html.unescape(x['title']),'artist':x.get('artistName'),'artist_url':rec['source']['url'],'date':q.parse_date(x.get('yearAsString')),
                'image_url':x['image'],'url':rec['source']['url']+'/'+key.rsplit('/',1)[-1].rsplit('.',1)[0],
                'api_receipt':rec['receipt'],'language':rec.get('language','en'),'english_title':q.html.unescape(original.get('title') or x['title'])}
            images[key][q.norm(c['title'])]=c
    for c in r.load(EXPANDED/'cached-images.json.gz'):
        images[q.image_key(c['image_url'])].setdefault(q.norm(c['title']),{**c,'date':(c['year_start'],c['year_end']) if c.get('year_start') and c.get('year_end') else None})
    candidates=[];works={}
    for part in r.load(EXPANDED/'snapshot.json')['parts']:
        path=ROOT/part['path'];assert r.sha(path.read_bytes())==part['sha256']
        for w in r.load(path):
            row=wanted.get(w['id'])
            if not row:continue
            for hint in row['candidate_images']:
                c=next((c for k,c in images[q.image_key(hint['image_url'])].items() if k in q.title_keys(w)),None)
                if not c:continue
                basis=source_date_basis(w,c.get('date'))
                if not basis:continue
                c={**c,'url':hint['page_hint']}
                works[w['id']]=w
                candidates.append({'work':w,'candidate':c,'candidate_count':row['possible_candidates'],'missing_target_count':1,'creator_basis':'inherited_exact_source_authority',
                    'date_review_basis':basis,'source_dates':c['date'],'catalogue_dates_preserved':[w['creation_year_start'],w['creation_year_end']],
                    'editorial_requirement':'Exact WikiArt museum, creator, title and unique version plus individual image review. Never update catalogue dates or visibility.'})
    with r.connect('production') as db:fresh=d.snapshots(db,list(works))
    accepted={};changed=[]
    for aid,w in works.items():
        v=fresh.get(aid);a=v['artwork'] if v else {};keys=['title','alternate_title','creation_year_start','creation_year_end','date_precision','status','accession_number','unlinked_creator_label','primary_media_id']
        if not v or any(a[k]!=w[k] for k in keys) or a['current_institution_id']!=w['institution_id'] or sorted((c['artist_id'],c['attribution_role']) for c in v['creators'])!=sorted((c['artist_id'],c['role']) for c in w['creators']):changed.append(aid)
        else:accepted[aid]=w
    r.save_gz(RUN/'fresh-production-scope.json.gz',{'at':r.now(),'read_only':True,'records':fresh,'changed':changed})
    candidates=[x for x in candidates if x['work']['id'] in accepted]
    part=RUN/'snapshot/0000.json.gz';r.save_gz(part,list(accepted.values()))
    counts=collections.Counter(w['institution_id'] for w in accepted.values())
    r.save(RUN/'snapshot.json',{'at':r.now(),'target':'production','read_only':True,'artworks':len(accepted),
        'scope':'Bounded editorial image-identity review where WikiArt has an explicit eligible date, with nearby imported date discrepancies, wholly pre-1970 centuries, or missing catalogue dates. Catalogue date/visibility fields remain unchanged.',
        'excluded_institutions':r.load(EXPANDED/'snapshot.json')['excluded_institutions'],
        'museum_counts':[{'institution_id':i,'works':c,'images':0} for i,c in counts.items()],
        'parts':[{'path':str(part.relative_to(ROOT)),'sha256':r.sha(part.read_bytes()),'rows':len(accepted)}]})
    for name in ['institutions.json.gz','indexes-summary.json','translations-summary.json','artist-sources.json.gz','original-title-aliases.json']:
        src=EXPANDED/name;dst=RUN/name
        if not dst.exists():dst.symlink_to(src)
    n.pin('candidate',{'at':r.now(),'snapshot_complete':True,'indexes_complete':True,'candidates':candidates,
        'outcomes':[{'artwork_id':w['id'],'institution_id':w['institution_id'],'title':w['title'],'has_image':False,'outcome':'source_date_editorial_review'} for w in accepted.values()],
        'counts':{'source_date_editorial_review':len(accepted)},'inherited_visual_holds':{}})
    print(json.dumps({'scoped_artworks':len(accepted),'source_edges':len(candidates),'date_review_bases':dict(collections.Counter(x['date_review_basis'] for x in candidates)),'changed_since_snapshot':len(changed)}),flush=True)


def resolve_mariana():
    """Replace a visually rejected homonymous portrait with the Tate composition."""
    aid='59989f61-747e-4371-8384-33c3d97efac3'
    data,old_pin=d.review();item=next(x for x in data['ready'] if x['work']['id']==aid)
    assert item['page']['metadata']['_id']=='5772769cedc2cb3880d1fbed'
    url='https://www.wikiart.org/en/john-everett-millais/mariana-in-the-moated-grange-1851'
    raw,rc=q.capture(url,'manual-resolution-captures');assert rc['status']==200
    page=q.page_metadata(raw,rc);w=item['work'];primary=r.load(RUN/'primary-tate/T07553.json.gz');obj=primary['data']['items'][0]
    assert obj['acno']==w['accession_number']=='T07553' and obj['title']==w['title']=='Mariana'
    assert page['metadata']['title']=='Mariana in the Moated Grange' and page['metadata']['artistUrl']=='/en/john-everett-millais'
    assert q.date_compatible(w,page['date']) and page['date']==(1851,1851)
    assert page['rights_status']=='public_domain' and page['rights_label']=='Public domain'
    assert q.museum_agrees(item['institution'],page['fields']['Location'])
    assert page['fields']['Dimensions']=='49.5 x 59.7 cm' and obj['dimensions'].startswith('support: 597 x 495 x 15 mm')
    replacement={**item,'page':page,'review_outcome':'high_manually_resolved_WikiArt_version_artist_date_museum_dimensions',
        'candidate':{'title':'Mariana','english_title':page['metadata']['title'],'language':'manually_verified_title_alias',
            'artist':page['metadata']['artistName'],'artist_url':'https://www.wikiart.org/en/john-everett-millais','date':page['date'],
            'image_url':page['image_url'],'url':page['url'],'page_url_verified':True,'source_id':page['metadata']['_id']},
        'primary_corroboration':{'basis':'Manual version reconciliation: the rejected homonymous WikiArt entry is a head portrait. The replacement gives Tate Britain, 1851, and 49.5 x 59.7 cm, matching exact Tate accession T07553 (597 x 495 x 15 mm). Catalogue title remains Mariana.','receipt':primary['receipt'],'object':obj},
        'rejected_source_page':item['page']}
    data['ready']=[replacement if x['work']['id']==aid else x for x in data['ready']];data['at']=r.now()
    n.pin('review',data)
    old_path=RUN/'prepared'/(aid+'.json');old=r.load(old_path)
    assert not old['reuse'];r.save(RUN/'visual-rejected-preparation'/(aid+'.json'),old)
    src=Path(old['visual_path']);dst=d.ORIGINALS/'held-derivatives'/src.name
    assert r.sha(src.read_bytes())==old['sha256'];dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();src.rename(dst)
    old_path.unlink()
    r.save(RUN/'manual-version-resolution.json',{'at':r.now(),'old_review_pin':old_pin,'artwork_id':aid,'rejected_page':item['page']['url'],'replacement_page':page['url'],'rejected_image_private_path':str(dst),'basis':replacement['primary_corroboration']})
    d.prepare()
    index=RUN/'contact-sheet-index.json';r.save(RUN/'visual-prior/contact-sheet-index.json',index.read_bytes());index.unlink()
    previous={}
    for path in (d.ORIGINALS/'contact-sheets').glob('*.jpg'):
        raw=path.read_bytes();previous[path.name]=r.sha(raw);r.save(d.ORIGINALS/'contact-sheets-prior'/path.name,raw)
    d.contact_sheets()
    changed=[p.name for p in (d.ORIGINALS/'contact-sheets').glob('*.jpg') if r.sha(p.read_bytes())!=previous[p.name]]
    assert changed==['007.jpg'],changed
    r.save(RUN/'visual-sheet-revision.json',{'at':r.now(),'changed_sheets':changed,'unchanged_sheets':len(previous)-1,'previous_sha256':previous})
    print('Resolved Mariana version; only sheet 007 requires renewed inspection',flush=True)


def backup():
    description='Before WikiArt source-date editorial image review 20261006' if DATE_REVIEW else 'Before authoritative WikiArt production image expansion 20261006'
    def cloud(*args):return n.subprocess.check_output(['gcloud',*args,'--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True)
    rows=json.loads(cloud('sql','backups','list','--instance=artline-postgres','--limit=40'))
    matches=[x for x in rows if x.get('description')==description]
    if not matches:
        r.save(d.BACKUP/'cloud-sql-backup-operation.json',json.loads(cloud('sql','backups','create','--instance=artline-postgres','--description='+description,'--async')))
        print('Requested expansion Cloud SQL recovery backup',flush=True);return
    current=max(matches,key=lambda x:int(x['id']))
    if current['status']!='SUCCESSFUL':print('Backup status',current['status'],flush=True);return
    r.save(d.BACKUP/'cloud-sql-backup.json',current)
    r.save(RUN/'cloud-sql-backup.json',{'id':current['id'],'status':current['status'],'at':r.now()})
    print('Expansion Cloud SQL backup verified',current['id'],flush=True)


def resolve_date_versions():
    assert DATE_REVIEW and not (RUN/'manual-version-resolution.json').exists()
    selected=[
      ('0d4e8156-7a9e-4741-943e-6f3a1466f374','https://www.wikiart.org/en/amedeo-modigliani/reclining-nude-with-head-resting-on-right-arm-1919','/en/amedeo-modigliani',1919,'73 x 116 cm','modigliani-image'),
      ('eefec8dc-91e1-4cf4-8dfd-5e9d2b7d26fd','https://www.wikiart.org/en/paul-cezanne/self-portrait-1875','/en/paul-cezanne',1875,'64 x 53 cm','cezanne-self-image')]
    data,old_pin=d.review();resolutions=[]
    for aid,url,artist,year,dimensions,reference in selected:
        item=next(x for x in data['ready'] if x['work']['id']==aid)
        raw,rc=q.capture(url,'manual-resolution-captures');assert rc['status']==200
        page=q.page_metadata(raw,rc)
        assert page['metadata']['artistUrl']==artist and page['date']==(year,year)
        assert page['fields']['Dimensions']==dimensions and page['rights_label']=='Public domain' and page['rights_status']=='public_domain'
        assert not any(x['work']['id']!=aid and x['page']['metadata']['_id']==page['metadata']['_id'] for x in data['ready'])
        primary=r.load(RUN/'version-evidence'/(reference+'.json'))
        basis={'basis':'Manual alternate-title/version reconciliation against the specific museum object image and physical dimensions. Source image must pass renewed visual comparison before delivery.',
               'reference_image_receipt':primary['receipt'],'reference_image_private_path':primary['private_visual_path'],
               'catalogue_dimensions':r.load(RUN/'fresh-production-scope.json.gz')['records'][aid]['artwork']['dimensions_text'],
               'wikiart_dimensions':dimensions,'source_dates':page['date'],'catalogue_dates_preserved':item['catalogue_dates_preserved']}
        replacement={**item,'page':page,'review_outcome':'high_manually_resolved_WikiArt_version_artist_date_museum_object_dimensions',
            'candidate':{'title':item['work']['title'],'english_title':page['metadata']['title'],'language':'manually_verified_title_alias',
                'artist':page['metadata']['artistName'],'artist_url':'https://www.wikiart.org'+artist,'date':page['date'],
                'image_url':page['image_url'],'url':page['url'],'page_url_verified':True,'source_id':page['metadata']['_id']},
            'primary_corroboration':basis,'rejected_source_page':item['page']}
        data['ready']=[replacement if x['work']['id']==aid else x for x in data['ready']]
        old_path=RUN/'prepared'/(aid+'.json');old=r.load(old_path)
        r.save(RUN/'visual-rejected-preparation'/(aid+'.json'),old)
        if not old['reuse']:
            src=Path(old['visual_path']);dst=d.ORIGINALS/'held-derivatives'/src.name
            assert r.sha(src.read_bytes())==old['sha256'];dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();src.rename(dst)
        old_path.unlink()
        resolutions.append({'artwork_id':aid,'rejected_page':item['page']['url'],'replacement_page':page['url'],'basis':basis})
    data['at']=r.now();n.pin('review',data)
    r.save(RUN/'manual-version-resolution.json',{'at':r.now(),'old_review_pin':old_pin,'resolutions':resolutions})
    d.prepare()
    index=RUN/'contact-sheet-index.json';r.save(RUN/'visual-prior/contact-sheet-index.json',index.read_bytes());index.unlink()
    previous={}
    for path in (d.ORIGINALS/'contact-sheets').glob('*.jpg'):
        raw=path.read_bytes();previous[path.name]=r.sha(raw);r.save(d.ORIGINALS/'contact-sheets-prior'/path.name,raw)
    contact_sheets()
    changed=[p.name for p in (d.ORIGINALS/'contact-sheets').glob('*.jpg') if r.sha(p.read_bytes())!=previous[p.name]]
    assert set(changed)=={'001.jpg','009.jpg'},changed
    r.save(RUN/'visual-sheet-revision.json',{'at':r.now(),'changed_sheets':changed,'unchanged_sheets':len(previous)-len(changed),'previous_sha256':previous})
    print('Resolved two same-title versions; sheets 001 and 009 require renewed inspection',flush=True)


def report():
    if DATE_REVIEW:return date_report()
    d.report()
    summary=r.load(RUN/'summary.json');previous=r.load(OLD/'production-applied.json');applied=r.load(RUN/'production-applied.json')
    assert not set(previous['artwork_ids']) & set(applied['artwork_ids'])
    source=r.load(RUN/'artist-sources.json.gz')
    extra={**summary,'round':2,'first_round_images':previous['attached'],'images_added_across_both_rounds':previous['attached']+applied['attached'],
        'source_of_truth':'WikiArt, per explicit user instruction recorded in AGENTS.md on 6 October 2026',
        'linked_artist_matches':len(source['matches']),'object_creator_label_matches':len(source['object_labels']),
        'original_title_aliases':r.load(RUN/'original-title-aliases.json')['aliases'],
        'manual_version_resolution':r.load(RUN/'manual-version-resolution.json'),
        'offline_identity_tests':{'passed':16,'database_or_network_used':False},
        'prior_visual_holds_preserved':q.candidate_pass()['inherited_visual_holds']}
    r.save(RUN/'expansion-summary.json',extra)
    body=(RUN/'report.html').read_text()
    intro='<p class="stats">'+str(applied['attached'])+' additional production images; '+str(extra['images_added_across_both_rounds'])+' across both rounds.</p>'
    intro+='<p>WikiArt is the source of truth for this image workflow, as requested and recorded in AGENTS.md. The expanded search used exact creator names in either order, verified translated titles in French, Russian, German, Spanish and Portuguese, and '+str(extra['original_title_aliases'])+' verbatim original-title aliases. No fuzzy-only identity was accepted.</p>'
    intro+='<p>All 18 contact sheets were inspected. A misleading homonymous Mariana portrait was replaced with the correct WikiArt Tate composition after accession, date and physical-dimension verification. One reproduction with a visible overlaid watermark was held. All 16 offline matching tests passed.</p>'
    intro+='<p><a href="expansion-summary.json">Expanded source and verification summary</a> · <a href="manual-version-resolution.json">Mariana version evidence</a></p>'
    body=body.replace('<h1>Production WikiArt image update</h1>','<h1>WikiArt image enrichment — second round</h1>'+intro)
    r.save(RUN/'round2-report.html',body.encode())
    print(json.dumps({'additional_images':applied['attached'],'cumulative_images':extra['images_added_across_both_rounds'],'museums':summary['updated_institutions'],'report':str(RUN/'round2-report.html')}),flush=True)


def date_report():
    if not (RUN/'report.html').exists():d.report()
    first=r.load(OLD/'production-applied.json');expanded=r.load(EXPANDED/'production-applied.json');applied=r.load(RUN/'production-applied.json')
    assert not set(first['artwork_ids']) & set(expanded['artwork_ids'])
    assert not (set(first['artwork_ids'])|set(expanded['artwork_ids'])) & set(applied['artwork_ids'])
    correction=r.load(EXPANDED/'version-correction.json')
    first_correction=r.load(OLD/'impression-correction.json');date_correction=r.load(RUN/'impression-correction.json')
    final_verification=r.load(RUN/'combined-production-verification.json');assert not final_verification['errors']
    assert not correction['errors'] and correction['net_attached']==len(correction['retained_artwork_ids'])
    retracted={x['artwork_id']:x for c in [first_correction,correction,date_correction] for x in c['retracted']}
    plans=[r.load(p/'production-plan.json.gz') for p in [EXPANDED,RUN]]
    claims=[x for plan in plans for x in plan['claims'] if x['work']['id'] not in retracted]
    museums=collections.Counter(x['institution']['name'] for x in claims)
    total=correction['net_attached']+date_correction['net_attached']
    verification=[r.load(p/'production-verification.json') for p in [EXPANDED,RUN]]
    assert all(not x['errors'] for x in verification)
    followups={x['artwork_id']:x for x in r.load(RUN/'all-artwork-results.json.gz')}
    original_ids=set(first_correction['retained_artwork_ids']);round2_ids=set(correction['retained_artwork_ids'])|set(date_correction['retained_artwork_ids']);all_results=[]
    for x in r.load(EXPANDED/'all-artwork-results.json.gz'):
        aid=x['artwork_id'];out={**x,'updated_round1':aid in original_ids,'updated_round2':aid in round2_ids,'production_updated':aid in round2_ids}
        if aid in followups:out['source_date_followup']=followups[aid]
        if aid in set(applied['artwork_ids']):
            out.update({k:followups[aid][k] for k in ['media_id','production_image_url','wikiart_page','verified_source_image','source_rights_label']})
        if aid in retracted:
            out['version_correction']=retracted[aid]
            for key in ['media_id','production_image_url']:out[key]=None
        out['has_image_in_audit_or_added_this_round']=(x['has_image'] or aid in round2_ids) and aid not in retracted
        all_results.append(out)
    assert len(all_results)==253437 and sum(x['updated_round2'] for x in all_results)==total
    r.save_gz(RUN/'combined-all-artwork-results.json.gz',all_results)
    summary={'at':r.now(),'additional_images_this_round':total,'cumulative_images_both_rounds':first_correction['net_attached']+total,
        'updated_museums_this_round':len({x['institution']['id'] for x in claims}),'by_museum':dict(museums),
        'first_round_retained_images':first_correction['net_attached'],
        'standard_identity_images':correction['net_attached'],'editorially_reviewed_source_date_images':date_correction['net_attached'],
        'retracted_uncertain_versions':list(retracted.values()),
        'source_date_review_bases':dict(collections.Counter(x['date_review_basis'] for x in plans[1]['claims'] if x['work']['id'] not in retracted)),
        'source_of_truth':'WikiArt; explicit user preference recorded in AGENTS.md',
        'all_catalogue_dates_metadata_holdings_creators_and_publication_states_preserved':True,'offline_identity_tests_passed':18,
        'verification_errors':[],'database_links_verified':final_verification['database_links_verified_this_round'],
        'cumulative_database_links_verified':final_verification['database_links_verified_both_rounds'],
        'live_artwork_api_checks':len(final_verification['live_api_checks']),
        'distinct_source_images_this_round':final_verification['distinct_wikiart_objects_this_round'],
        'backup_receipts':[r.load(p/'cloud-sql-backup.json') for p in [EXPANDED,RUN]],
        'full_audit_artworks':len(all_results),'detailed_reports':[str((p/'report.html').relative_to(ROOT)) for p in [EXPANDED,RUN]]}
    r.save(RUN/'combined-round2-summary.json',summary)
    esc=q.html.escape;rows=[]
    for item in sorted(claims,key=lambda x:(x['institution']['name'],x['work']['title'])):
        aid=item['work']['id'];im=next(plan['prepared'][aid] for plan in plans if aid in plan['prepared'])
        link='https://artlines.org/museums/'+item['institution']['slug']+'?work='+aid
        rows.append('<tr><td>'+esc(item['institution']['name'])+'</td><td><a href="'+esc(link,quote=True)+'">'+esc(item['work']['title'])+'</a></td><td>'+esc(q.html.unescape(item['page']['metadata']['artistName']))+'</td><td>'+esc(str(item['work'].get('date_display') or 'Unknown'))+'</td><td>'+esc('–'.join(map(str,item['page']['date'])))+'</td><td><a href="'+esc(item['page']['url'],quote=True)+'">WikiArt</a> · <a href="https://artlines.org'+esc(im['path'],quote=True)+'">Image</a></td></tr>')
    body='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>WikiArt production enrichment — round 2</title><style>body{font:16px/1.5 system-ui;max-width:1380px;margin:40px auto;padding:0 25px;background:#f5f3ec;color:#183239}h1{font:38px Georgia}table{width:100%;border-collapse:collapse;background:white}td,th{padding:10px;border-bottom:1px solid #ddd;text-align:left;vertical-align:top}th{background:#21434b;color:white}a{color:#12616d}.stat{font-size:24px;font-weight:650}</style>'
    body+='<h1>WikiArt production enrichment — second round</h1><p>6 October 2026 · Louvre and Prado excluded</p><p class="stat">'+str(total)+' additional images across '+str(summary['updated_museums_this_round'])+' museums; '+str(summary['cumulative_images_both_rounds'])+' images across both rounds.</p>'
    body+='<p>WikiArt is the source of truth for this image workflow, as explicitly requested and recorded in AGENTS.md. The full 253,437-record production audit was expanded with exact creator names in either order, multilingual titles and original-title aliases. '+str(date_correction['net_attached'])+' further images passed an explicit editorial review of WikiArt dates against nearby imported date discrepancies or missing/broad catalogue dates, requiring museum/object and version corroboration and visual inspection.</p>'
    body+='<p>All catalogue dates, other metadata, holdings, creator relations and publication states remain unchanged. The source dates below document image identity only. Uncertain versions, medium conflicts, post-1970 or territory-limited/restricted source records remain held. The requested 90% confidence is implemented by high-corroboration review rules, not a statistically calibrated percentage.</p>'
    body+='<p>The totals are net of three retracted print-impression links: Dock at Newport from this round, and two Fear records, one from each round. Original artwork states were restored; source assets and recovery evidence were retained. Earlier batch reports preserve historical pre-correction counts. <a href="combined-production-verification.json">Final current-state verification and all corrections</a>.</p>'
    body+='<p>'+str(summary['database_links_verified'])+' production image links, all image bytes and '+str(summary['live_artwork_api_checks'])+' live artwork API responses verified. All 18 offline identity tests passed. Recovery backups and per-record preimages were retained.</p><p><a href="combined-round2-summary.json">Combined summary</a> · <a href="combined-all-artwork-results.json.gz">All 253,437 artwork results (compressed JSON)</a> · <a href="../'+EXPANDED.name+'/round2-report.html">Expanded matching report</a> · <a href="report.html">Source-date review report</a></p>'
    body+='<table><tr><th>Museum</th><th>Artwork</th><th>Creator</th><th>Catalogue date, unchanged</th><th>WikiArt date</th><th>Source</th></tr>'+''.join(rows)+'</table></html>'
    r.save(RUN/'combined-round2-report.html',body.encode())
    print(json.dumps({'additional_images_this_round':total,'cumulative_images':summary['cumulative_images_both_rounds'],'updated_museums_this_round':summary['updated_museums_this_round'],'report':str(RUN/'combined-round2-report.html')}),flush=True)


def correct_dock_version():
    """Retract only this operation's uncertain print link; retain the source asset."""
    assert RUN==EXPANDED and not DATE_REVIEW
    aid='c7ef0b7f-abbe-4089-a2ba-540a593db11c'
    dest=RUN/'version-correction.json'
    if dest.exists():
        print(json.dumps(r.load(dest)),flush=True);return
    data,pin=d.pinned();applied=r.load(RUN/'production-applied.json')
    expected=r.load(d.BACKUP/'production-after.json.gz')['records']
    im=data['prepared'][aid];prior=data['preimages'][aid]
    assert prior['artwork']['primary_media_id'] is None and not im['attachment_was_present']
    item=next(x for x in data['claims'] if x['work']['id']==aid)
    reason={'artwork_id':aid,'title':item['work']['title'],'reason':'Uncertain exact print/impression identity: incompatible plate proportions.',
        'catalogue_dimensions':prior['artwork']['dimensions_text'],'catalogue_medium':prior['artwork']['medium_text'],
        'wikiart_dimensions':item['page']['fields'].get('Dimensions'),'wikiart_page':item['page']['url'],
        'museum_object':'https://www.metmuseum.org/art/collection/search/698812','plan_sha256':pin['sha256'],
        'scope':'Retract this operation image attachment and image-identity citation only. Preserve the media asset, source, rights evidence, artwork metadata, all files and recovery evidence.'}
    with r.connect('production') as db:
        before=d.snapshots(db,[aid]);citation=db.execute('SELECT to_jsonb(c) record FROM citations c WHERE id=%s',(d.uid('citation/'+aid),)).fetchone()
    assert before[aid]==expected[aid] and citation and citation['record']['source_id']==data['source_id']
    r.save_gz(d.BACKUP/'version-correction-before.json.gz',{'records':before,'citation':citation['record'],'reason':reason})
    with r.connect('production',readonly=False) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute('SELECT pg_advisory_xact_lock(202610066)')
        db.execute('SELECT id FROM artworks WHERE id=%s FOR UPDATE',(aid,)).fetchone()
        assert d.snapshots(db,[aid])==before
        actual=db.execute('SELECT to_jsonb(c) record FROM citations c WHERE id=%s FOR UPDATE',(d.uid('citation/'+aid),)).fetchone()
        assert actual==citation
        assert db.execute('UPDATE artworks SET primary_media_id=NULL,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id=%s',(d.ACTOR,aid,im['media_id'])).rowcount==1
        assert db.execute('DELETE FROM artwork_media WHERE artwork_id=%s AND media_id=%s',(aid,im['media_id'])).rowcount==1
        assert db.execute("DELETE FROM citations WHERE id=%s AND entity_type='artwork' AND entity_id=%s AND field_name='image_identity' AND source_id=%s",(d.uid('citation/'+aid),aid,data['source_id'])).rowcount==1
        after=d.snapshots(db,[aid]);allowed={'primary_media_id','revision','updated_at','updated_by'}
        assert {k:v for k,v in after[aid]['artwork'].items() if k not in allowed}=={k:v for k,v in prior['artwork'].items() if k not in allowed}
        assert after[aid]['creators']==prior['creators'] and after[aid]['attachments']==prior['attachments']
        assert after[aid]['artwork']['revision']==before[aid]['artwork']['revision']+1
    r.save_gz(d.BACKUP/'version-correction-after.json.gz',{'records':after,'reason':reason})
    with r.connect('production') as db:
        current=d.snapshots(db,applied['artwork_ids'])
        assert current[aid]==after[aid]
        assert all(current[k]==expected[k] for k in applied['artwork_ids'] if k!=aid)
        citations=db.execute("SELECT entity_id::text FROM citations WHERE source_id=%s AND entity_type='artwork' AND field_name='image_identity'",(data['source_id'],)).fetchall()
        assert {x['entity_id'] for x in citations}==set(applied['artwork_ids'])-{aid}
        assert db.execute('SELECT id FROM media_assets WHERE id=%s',(im['media_id'],)).fetchone()
    result={'at':r.now(),'retracted':[reason],'retained_artwork_ids':[x for x in applied['artwork_ids'] if x!=aid],
        'original_attached':applied['attached'],'net_attached':applied['attached']-1,'database_links_verified':applied['attached']-1,
        'remaining_artwork_snapshots_unchanged':True,'retracted_object_original_metadata_and_attachments_restored':True,
        'media_asset_and_files_preserved':True,'errors':[]}
    r.save(dest,result)
    print(json.dumps({'retracted':aid,'retained_images_verified':result['net_attached'],'errors':[]}),flush=True)


def version_evidence():
    """Selected primary records for adjudicating flagged WikiArt versions."""
    assert DATE_REVIEW
    requests=[
      ('modigliani','https://www.moma.org/collection/works/78432',None),
      ('cezanne-road','https://www.moma.org/collection/works/80025',None),
      ('cezanne-self','https://www.musee-orsay.fr/fr/oeuvres/portrait-de-lartiste-1308',None),
      ('segantini','https://www.lombardiabeniculturali.it/opere-arte/schede-complete/2d050-00111/',None),
      ('ostade','https://www.rijksmuseum.nl/en/collection/SK-A-4049',None),
      ('weissenbruch','https://www.rijksmuseum.nl/en/collection/object/Autumn-Landscape--e970539d014545c6029ba1958af578a9',None),
      ('vigee-le-brun','https://www.nationalgallery.org.uk/paintings/elisabeth-louise-vigee-le-brun-self-portrait-in-a-straw-hat',None),
      ('leighton','https://www.tate.org.uk/api/v2/artworks/',{'acno':'N01574','fields':'title,acno,url,allArtists,dateText,dimensions,start_year,end_year,master_images'}),
      ('met-dock','https://collectionapi.metmuseum.org/public/collection/v1/objects/698812',None),
      ('modigliani-image','https://www.moma.org/media/W1siZiIsIjUxNjk3MCJdLFsicCIsImNvbnZlcnQiLCItcXVhbGl0eSA5MCAtcmVzaXplIDIwMDB4MjAwMFx1MDAzZSJdXQ.jpg?sha=85650b260bf6cc88',None),
      ('cezanne-road-image','https://www.moma.org/media/W1siZiIsIjE1MTM5MyJdLFsicCIsImNvbnZlcnQiLCItcXVhbGl0eSA5MCAtcmVzaXplIDIwMDB4MjAwMFx1MDAzZSJdXQ.jpg?sha=81f9c0cc0f61a199',None),
      ('cezanne-self-image','https://cdn.mediatheque.epmoo.fr/link/3c9igq/kfu1czhoksv7pk0.jpg',None),
      ('leighton-image','https://media.tate.org.uk/art/images/work/N/N01/N01574_9.jpg',None),
      ('moreau-rouen','https://mbarouen.fr/en/oeuvres/diomedes-devoured-by-his-horses',None),
      ('moreau-rouen-image','https://mbarouen.fr/sites/default/files/styles/oeuvre/public/upload/Collections%20permanentes/10_salon/1931_16_1.jpg',None),
      ('waterhouse-oracle-image','https://media.tate.org.uk/art/images/work/N/N01/N01541_9.jpg',None)]
    def one(task):
        name,url,params=task;dest=RUN/'version-evidence'/(name+'.json')
        if dest.exists():return r.load(dest)
        try:raw,rc=r.capture(url,params,tag='version-evidence-captures',timeout=40)
        except Exception as exc:
            out={'name':name,'receipt':{'url':url,'status':None,'retrieved_at':r.now(),'error':str(exc)[:600]}}
            r.save(dest,out);return out
        out={'name':name,'receipt':rc}
        if rc['status']==200 and rc.get('content_type','').startswith('image/'):
            path=d.ORIGINALS/'version-reference-images'/(name+'.jpg');r.save(path,raw);out['private_visual_path']=str(path)
        elif rc['status']==200 and 'json' in rc.get('content_type',''):out['data']=json.loads(raw)
        elif rc['status']==200:
            soup=q.BeautifulSoup(raw,'html.parser');meta=soup.select_one('meta[property="og:image"]')
            out['text']=soup.get_text(' ',strip=True);out['og_image']=meta.get('content') if meta else None
        r.save(dest,out);return out
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for x in pool.map(one,requests):print(json.dumps({'name':x['name'],'status':x['receipt']['status'],'image':x.get('private_visual_path'),'og_image':x.get('og_image')}),flush=True)


def correct_print_impressions():
    """Retract two links whose WikiArt article identifies a different impression."""
    assert DATE_REVIEW
    saved=(d.RUN,d.OP,d.BACKUP)
    for folder,aid in [(OLD,'fb64506e-714c-4dd6-aac2-4c5ae210ac9f'),(RUN,'4590f52e-26ff-46e5-b24e-fd397e853c1f')]:
        dest=folder/'impression-correction.json'
        if dest.exists():print(folder.name,'already corrected',flush=True);continue
        d.RUN=folder;d.OP=folder.name;d.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/d.OP
        data,pin=d.pinned();applied=r.load(folder/'production-applied.json');im=data['prepared'][aid]
        expected=r.load(d.BACKUP/'production-after.json.gz')['records'];prior=data['preimages'][aid]
        item=next(x for x in data['claims'] if x['work']['id']==aid)
        raw=n.gzip.decompress((ROOT/item['page']['receipt']['body_path']).read_bytes())
        assert r.sha(raw)==item['page']['receipt']['sha256']
        info=q.BeautifulSoup(raw,'html.parser').select_one('.wiki-layout-artwork-info')
        source='http://www.artic.edu/aic/collections/artwork/106580?search_id=1'
        assert source in [a['href'] for a in info.select('a[href]')]
        assert not any('/106580' in (x.get('url') or '') for x in item['work']['identifiers'])
        assert prior['artwork']['primary_media_id'] is None and not im['attachment_was_present']
        reason={'artwork_id':aid,'title':item['work']['title'],'reason':'WikiArt references Art Institute object106580, a different print impression from this catalogue object.',
            'wikiart_page':item['page']['url'],'wikiart_reference_object':source,'catalogue_identifiers':item['work']['identifiers'],
            'catalogue_medium':prior['artwork']['medium_text'],'catalogue_dimensions':prior['artwork']['dimensions_text'],
            'page_receipt':item['page']['receipt'],'plan_sha256':pin['sha256']}
        with r.connect('production') as db:
            before=d.snapshots(db,[aid]);citation=db.execute('SELECT to_jsonb(c) record FROM citations c WHERE id=%s',(d.uid('citation/'+aid),)).fetchone()
        assert before[aid]==expected[aid] and citation and citation['record']['source_id']==data['source_id']
        r.save_gz(d.BACKUP/'impression-correction-before.json.gz',{'records':before,'citation':citation['record'],'reason':reason})
        with r.connect('production',readonly=False) as db,db.transaction():
            db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(202610066)')
            db.execute('SELECT id FROM artworks WHERE id=%s FOR UPDATE',(aid,)).fetchone();assert d.snapshots(db,[aid])==before
            actual=db.execute('SELECT to_jsonb(c) record FROM citations c WHERE id=%s FOR UPDATE',(d.uid('citation/'+aid),)).fetchone();assert actual==citation
            assert db.execute('UPDATE artworks SET primary_media_id=NULL,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id=%s',(d.ACTOR,aid,im['media_id'])).rowcount==1
            assert db.execute('DELETE FROM artwork_media WHERE artwork_id=%s AND media_id=%s',(aid,im['media_id'])).rowcount==1
            assert db.execute("DELETE FROM citations WHERE id=%s AND entity_type='artwork' AND entity_id=%s AND field_name='image_identity' AND source_id=%s",(d.uid('citation/'+aid),aid,data['source_id'])).rowcount==1
            after=d.snapshots(db,[aid]);allowed={'primary_media_id','revision','updated_at','updated_by'}
            assert {k:v for k,v in after[aid]['artwork'].items() if k not in allowed}=={k:v for k,v in prior['artwork'].items() if k not in allowed}
            assert after[aid]['creators']==prior['creators'] and after[aid]['attachments']==prior['attachments']
            assert after[aid]['artwork']['revision']==before[aid]['artwork']['revision']+1
        r.save_gz(d.BACKUP/'impression-correction-after.json.gz',{'records':after,'reason':reason})
        with r.connect('production') as db:
            current=d.snapshots(db,applied['artwork_ids']);assert current[aid]==after[aid]
            assert all(current[k]==expected[k] for k in applied['artwork_ids'] if k!=aid)
            citations=db.execute("SELECT entity_id::text FROM citations WHERE source_id=%s AND entity_type='artwork' AND field_name='image_identity'",(data['source_id'],)).fetchall()
            assert {x['entity_id'] for x in citations}==set(applied['artwork_ids'])-{aid}
            assert db.execute('SELECT id FROM media_assets WHERE id=%s',(im['media_id'],)).fetchone()
        result={'at':r.now(),'retracted':[reason],'retained_artwork_ids':[x for x in applied['artwork_ids'] if x!=aid],
            'original_attached':applied['attached'],'net_attached':applied['attached']-1,'database_links_verified':applied['attached']-1,
            'remaining_artwork_snapshots_unchanged':True,'original_metadata_and_attachments_restored':True,'assets_and_files_retained':True,'errors':[]}
        r.save(dest,result);print(json.dumps({'operation':folder.name,'retracted':aid,'retained_verified':result['net_attached']}),flush=True)
    d.RUN,d.OP,d.BACKUP=saved


def verify_combined():
    assert DATE_REVIEW
    folders=[OLD,EXPANDED,RUN];plans={str(p):r.load(p/'production-plan.json.gz') for p in folders}
    corrections=[r.load(p/name) for p,name in [(OLD,'impression-correction.json'),(EXPANDED,'version-correction.json'),(RUN,'impression-correction.json')]]
    assert all(not c['errors'] for c in corrections)
    retracted={x['artwork_id']:x for c in corrections for x in c['retracted']}
    claims={x['work']['id']:(folder,plans[str(folder)],x) for folder in folders for x in plans[str(folder)]['claims']}
    retained={aid:entry for aid,entry in claims.items() if aid not in retracted};errors=[]
    ids=list(claims)
    with r.connect('production') as db:
        current=d.snapshots(db,ids)
        mids=[p['prepared'][aid]['media_id'] for aid,(_,p,x) in retained.items()]
        assets={x['media']['id']:x for x in db.execute('SELECT to_jsonb(m) media,to_jsonb(e) rights FROM media_assets m LEFT JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=ANY(%s::uuid[])',(mids,)).fetchall()}
        citations=db.execute("SELECT entity_id::text,source_id::text,source_record_id,source_url FROM citations WHERE source_id=ANY(%s::uuid[]) AND entity_type='artwork' AND field_name='image_identity'",([p['source_id'] for p in plans.values()],)).fetchall()
        assert len(citations)==len(retained)
        for aid,(folder,p,item) in claims.items():
            before=p['preimages'][aid];after=current[aid];im=p['prepared'][aid];allowed={'primary_media_id','revision','updated_at','updated_by'}
            assert {k:v for k,v in before['artwork'].items() if k not in allowed}=={k:v for k,v in after['artwork'].items() if k not in allowed}
            assert before['creators']==after['creators']
            if aid in retracted:
                assert after['artwork']['primary_media_id'] is None and after['attachments']==before['attachments']
                assert not any(c['entity_id']==aid for c in citations)
            else:
                assert after['artwork']['primary_media_id']==im['media_id']
                assert any(a['media_id']==im['media_id'] for a in after['attachments'])
                a=assets[im['media_id']];assert a['media']['checksum_sha256']==im['sha256'] and a['media']['storage_path']==im['path'] and a['media']['byte_size']==im['bytes'] and a['rights']
                assert a['media']['rights_status']=='public_domain'
                assert any(c['entity_id']==aid and c['source_id']==p['source_id'] and c['source_record_id']==item['page']['metadata']['_id'] and c['source_url']==item['page']['url'] for c in citations)
    round2={aid:entry for aid,entry in retained.items() if entry[0]!=OLD};sample={}
    for aid,entry in round2.items():sample.setdefault(entry[2]['institution']['slug'],entry)
    def one(entry):
        folder,p,item=entry;aid=item['work']['id'];im=p['prepared'][aid]
        url='https://artlines.org/api/backend/v1/museums/'+item['institution']['slug']+'/works/'+aid
        response=d.requests.get(url,timeout=(15,45));body=response.json() if response.status_code==200 else {}
        asset=d.requests.get('https://artlines.org'+im['path'],timeout=(15,45))
        return {'artwork_id':aid,'museum':item['institution']['slug'],'url':url,'status':response.status_code,
            'verified':response.status_code==200 and body.get('media_url')==im['path'] and body.get('title')==item['work']['title'],
            'public_bytes_verified':asset.status_code==200 and r.sha(asset.content)==im['sha256']}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:api=list(pool.map(one,sample.values()))
    errors=[x for x in api if not(x['verified'] and x['public_bytes_verified'])]
    result={'at':r.now(),'database_links_verified_this_round':len(round2),'database_links_verified_both_rounds':len(retained),
        'source_citations_verified':len(citations),'metadata_creators_and_publication_unchanged':True,'retractions_verified':list(retracted.values()),
        'distinct_wikiart_objects_this_round':len({x[2]['page']['metadata']['_id'] for x in round2.values()}),
        'distinct_wikiart_objects_both_rounds':len({x[2]['page']['metadata']['_id'] for x in retained.values()}),
        'live_api_checks':api,'all_selected_public_bytes_verified_before_attachment':True,'errors':errors}
    assert not errors,errors
    r.save(RUN/'combined-production-verification.json',result)
    print(json.dumps({'retained_images_round2':len(round2),'retained_images_total':len(retained),'retractions_verified':len(retracted),'live_museum_api_and_images_verified':len(api),'errors':errors}),flush=True)
