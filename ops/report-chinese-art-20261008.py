#!/usr/bin/env python3
"""Build a source-linked Chinese-art research register and conservative shortlist."""
import collections,csv,gzip,hashlib,html,importlib.util,json,re
from pathlib import Path

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-chinese-art-20261008.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

def highlights():
    pages={x['url']:x for x in r.load('museum-source-captures.json.gz') if x['status']=='captured'}
    pages.update({x['url']:x for x in r.load('supplementary-captures.json.gz') if 'evidence' in x})
    definitions=[
      ('Palace Museum, Beijing','https://www.dpm.org.cn/collection/paint/228226.html','Along the River during the Qingming Festival','张择端清明上河图卷','Zhang Zeduan','北宋',None,None,'新00087177','Handscroll; ink and light colour on silk','within_cutoff_source_period','Northern Song physical scroll, not a later Qingming composition or digital animation.'),
      ('Palace Museum, Beijing','https://www.dpm.org.cn/collection/paint/231315.html','Walking with a Staff on a Bridge over a Stream','文徵明溪桥策杖图轴','Wen Zhengming','明',None,None,'新00145960','Hanging scroll; ink on paper','within_cutoff_source_period','1924 in source is a remounting date, not creation.'),
      ('Palace Museum, Beijing','https://www.dpm.org.cn/collection/paint/257916.html','Walking by a Stream','唐寅《步溪图》轴','Tang Yin',None,None,None,'新00152327','Colour on silk','date_review','Source title and signed creator retained; no exact work date inferred from artist lifespan.'),
      ('Palace Museum, Beijing','https://www.dpm.org.cn/collection/paint/228354.html','A Thousand Li of Rivers and Mountains','王希孟千里江山图卷','Wang Ximeng','北宋; 1113 discussed as possible completion date',None,None,'新00146004','Handscroll; colour on silk','within_cutoff_source_period','Preserve source qualification of 1113; complete scroll and detail images are distinct views.'),
      ('Palace Museum, Beijing','https://www.dpm.org.cn/collection/paint/228200.html','The Night Revels of Han Xizai, Song copy','顾闳中韩熙载夜宴图卷','Anonymous Song copy after Gu Hongzhong','Southern Song copy, 1163–1224',1163,1224,'新00147326','Handscroll; colour on silk','within_cutoff_source_bounds','Museum explicitly identifies surviving object as a Song copy; do not assign original Five Dynasties creation date or primary authorship.'),
      ('Tianjin Museum','https://www.tjbwg.cn/cn/collectionInfo.aspx?Id=2379','Snow-Covered Scene and Cold Forest','宋 范宽 雪景寒林图轴','Fan Kuan','宋（960—1279）',960,1279,None,'Colour on silk','within_cutoff_source_bounds','Museum attribution preserved; no inferred exact creation year.'),
      ('Hunan Museum','https://web.hnmuseum.com/en/content/silk-painting-female-figure-dragon-and-phoenix-patterns','Silk painting with female figure, dragon and phoenix patterns',None,None,'Warring States period',None,None,None,'Silk painting','within_cutoff_source_period','1949 is excavation date; unnamed creator retained.'),
      ('Hunan Museum','https://web.hnmuseum.com/en/zuixintuijie/physical-exercise-chart-silk','Physical Exercise Chart on Silk',None,None,'Western Han Dynasty (206BC—25AD)',-206,25,None,'Colour on silk','within_cutoff_source_bounds','Source dynasty bounds retained as supplied; 1973 is excavation date, not creation. One chart with 44 figures, not 44 artworks.'),
      ('Shaanxi History Museum','https://en.sxhm.com/en/new/treasure/detail/18044.html','Mural: Polo Game',None,None,'Tang Dynasty (618–907)',618,907,None,'Mural painting','within_cutoff_source_bounds','Detached from west wall of Prince Zhanghuai tomb passage; 1971 is excavation date. Five measured panels are one recorded composition.'),
      ('Harvard Art Museums','https://harvardartmuseums.org/collections/object/204072','Eleven-Headed Guanyin',None,None,'dated to 985',985,985,'1943.57.14','Hanging scroll; ink and colour on silk','within_cutoff_source_bounds','Dunhuang portable banner, not a wall painting. Source permits personal/noncommercial uses; no general commercial image clearance inferred.'),
      ('Musée Guimet','https://www.guimet.fr/fr/nos-collections/chine-bouddhique-asie-centrale/mandala-des-cinq-jina','Mandala of the Five Jina','Mandala des cinq Jina',None,'Late 10th century; possibly consecrated 972–974',None,None,'MG 17780','Painting on silk, ink, gold','within_cutoff_source_period','Portable Dunhuang painting; RMN-Grand Palais / Richard Lambert photograph remains permission research.'),
      ('Tokyo National Museum','https://www.tnm.jp/modules/r_collection/index.php?colid=TA137&controller=dtl&id=11&lang=en&t=type_s','Red and White Cotton Rosemallow',None,'Li Di','Southern Song dynasty, 1197',1197,1197,'TA-137','Colour on silk','within_cutoff_source_bounds','Museum treats the paintings as a set. Do not split the set or infer current display.')]
    url='https://www.heritagemuseum.gov.hk/en/collections/highlight/chinese_painting.html'
    for title,year in [('A Desolate Border Fortress in the Moonlit Mountain',1962),('Plantain Trees',1962),('White Peacock',1969),('Tiger',1965),('Moonlight Over the Pond',1969),('Egrets and Willow',1969),('Simple Pleasures',1982),('Cicada and Bamboo',1985)]:
        definitions.append(('Hong Kong Heritage Museum',url,title,None,'Chao Shao-an',str(year),year,year,None,None,'within_cutoff_source_bounds' if year<=1970 else 'after_cutoff','Exact gallery caption. Post-1970 paintings are retained only in excluded research.'))
    out=[]
    for museum,url,title,original,creator,date,lo,hi,accession,medium,decision,note in definitions:
        assert url in pages, 'Missing primary capture: '+url
        text=pages[url]['source_text']
        assert (original or title) in text, 'Title not found in primary source: '+title
        if accession:assert accession in text
        if museum=='Hong Kong Heritage Museum':assert str(lo) in text
        row=r.candidate('selected-highlights',dict(original_title=original),pages[url]['evidence'],
            source_id=hashlib.sha256((url+'|'+title).encode()).hexdigest()[:20],title=title,museum=museum,
            source_url=url,creator_label=creator,date_display=date,year_start=lo,year_end=hi,accession_number=accession,
            medium=medium,source_type='mural painting' if 'Mural:' in title else 'painting',culture=None,
            image_url=None,image_license_url=None,image_rights_label='Exact reproduction still requires image review',credit=museum,identity_note=note)
        row['date_decision']=decision
        out.append(row)
    r.save('selected-highlights.json',out)
    return out

def main():
    local={(x['provider'],x['source_id']):x for x in r.load('candidates.json.gz')}
    records=[]
    for provider in ['cleveland','chicago','mia','met','npm','namoc','hkmoa','ashmolean']:
        for x in r.load(provider+'.json.gz')['records']:
            prior=local.get((provider,x['source_id']))
            if prior:
                for key in ['local_matches','local_match_decision']:x[key]=prior[key]
            else:x['local_match_decision']='not_audited'
            x['production_match_decision']='not_audited_proxy_unavailable'
            # Disallow eligibility inferred from missing/default dates or later-edition language.
            date=x.get('date_display') or ''
            if x.get('year_start')==0 or x.get('year_end')==0 or re.search(r'\b(?:undated|unknown|after|later cast|later print|reprint|printed later)\b',date,re.I):
                x['date_decision']='date_review'
            if provider=='mia':
                # Preserve source text and normalize only unambiguous single years/ranges.
                m=re.fullmatch(r'(\d{3,4})(?:\s*[-–]\s*(\d{3,4}))?',date)
                if m:
                    x['year_start']=int(m[1]);x['year_end']=int(m[2] or m[1])
                    x['date_decision']='within_cutoff_source_bounds' if x['year_end']<=1970 else 'after_cutoff' if x['year_start']>1970 else 'date_review'
                elif re.fullmatch(r'(?:early |mid-|late |first half of |second half of )?(?:[1-9]|1[0-9])(?:st|nd|rd|th) century',date,re.I):
                    x['date_decision']='within_cutoff_source_period'
            if provider=='hkmoa':
                x['culture']=None
                x['scope_note']='Chinese art / China-trade research. Source creator names retained; Chinese creator nationality is not inferred.'
            if not x['title']:x['decision']='missing_source_title_review'
            x['application_state']='research_only_not_imported'
            records.append(x)
    records+=highlights()
    keys=[(x['provider'],x['source_id']) for x in records];assert len(keys)==len(set(keys))
    for x in records:
        assert x['evidence']['status']==200 and x['source_id'] and x['source_url'].startswith('https://')
        assert x['current_display'] is None
        if x['date_decision']=='within_cutoff_source_bounds':assert -10000<=x['year_start']<=x['year_end']<=1970
        if x['date_decision']=='after_cutoff':assert x['year_start']>1970
    excluded=[x for x in records if x['date_decision']=='after_cutoff']
    candidates=[x for x in records if x['date_decision']!='after_cutoff']
    dated=[x for x in candidates if x['date_decision'].startswith('within_cutoff')]
    open_dated=[x for x in dated if x.get('image_url') and x.get('image_license_url')]
    priority=[x for x in open_dated if x['decision']=='research_candidate' and
        not re.search(r'\b(?:loan|lent|deaccession)\b',x.get('credit') or '',re.I)]
    for x in priority:x['next_action']='Exact-object/attribution and full-image visual review before download/attachment; preserve original status.'
    r.save('all-records.json.gz',records);r.save('in-scope-or-review.json.gz',candidates);r.save('excluded-post-1970.json',excluded)
    r.save('priority-image-candidates.json.gz',priority)
    fields=['provider','source_id','museum','title','creator_label','date_display','year_start','year_end','date_decision','accession_number','medium','source_url','image_url','image_rights_label','image_license_url','decision','local_match_decision']
    with (r.RUN/'artwork-register.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for x in records:writer.writerow({k:x.get(k) for k in fields})
    with (r.RUN/'priority-images.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for x in priority:writer.writerow({k:x.get(k) for k in fields})
    surfaces=[]
    for cave in r.load('dunhuang.json.gz')['records']:
        for s in cave['source_sections']:
            surfaces.append(dict(cave=cave['source_id'],title=s['title'],source_url=cave['source_url']+'#'+s['source_anchor'],
                source_description=s['description'],evidence=cave['evidence'],decision='Surface research; resolve scenes and paint layers before artwork import'))
    r.save('dunhuang-surfaces.json',surfaces)
    target_rows=[];captures=r.load('museum-source-captures.json.gz')
    for target in r.load('museum-targets.json'):
        observed=[x for x in captures if x['museum']==target['museum']]
        count=sum(x['museum']==target['museum'] for x in candidates)
        target_rows.append(dict(target,selected_records=count,captured_pages=sum(x['status']=='captured' for x in observed),
            capture_failures=[dict(url=x['url'],error=x['error']) for x in observed if x['status']!='captured'],
            coverage_status='individual_records_researched' if count else 'mural_surface_research' if 'Dunhuang' in target['museum'] else 'collection_or_discovery_leads_only'))
    r.save('museum-coverage.json',target_rows)
    summary=dict(at=r.now(),target_collections=len(target_rows),all_source_records=len(records),
        retained_candidates=len(candidates),excluded_post_1970=len(excluded),source_dated_within_cutoff=len(dated),
        unresolved_dates=sum(x['date_decision']=='date_review' for x in candidates),
        open_label_image_links=sum(bool(x.get('image_url') and x.get('image_license_url')) for x in candidates),
        open_label_and_within_cutoff=len(open_dated),priority_image_candidates=len(priority),
        npm_additional_open_tier_candidates=169,documented_mural_surfaces=len(surfaces),documented_mogao_caves=12,
        museums_with_individual_retained_records=len({x['museum'] for x in candidates}),
        by_museum=dict(collections.Counter(x['museum'] for x in candidates)),
        local_exact_matches=sum(x.get('local_match_decision')=='existing_exact_native_id_or_accession' for x in candidates),
        catalogue_writes=0,image_downloads=0,production_comparison='Unavailable: existing read-only proxy port 55519 refused connection; new-to-production counts are not claimed.')
    r.save('summary.json',summary)
    # Every persisted source capture is independently checked against its recorded digest.
    verified=0
    for p in (r.RUN/'captures').glob('*.json'):
        receipt=json.loads(p.read_text());raw=gzip.decompress(p.with_suffix('.body.gz').read_bytes())
        assert hashlib.sha256(raw).hexdigest()==receipt['sha256'];verified+=1
    r.save('verification.json',dict(at=r.now(),passed=True,unique_source_identities=len(keys),
        source_capture_checksums_verified=verified,source_title_checks='20 curated highlights checked against captured primary text',
        no_post_cutoff_priority=all(x['date_decision'].startswith('within_cutoff') for x in priority),
        catalogue_writes=0,image_downloads=0,production_not_audited=True))
    lines=['# Chinese paintings, scrolls, prints and murals — 8 October 2026','',
        f"Researched **{len(records):,} source records** and retained **{len(candidates):,} pre-1971 or unresolved-date candidates** from **{summary['museums_with_individual_retained_records']} museums**. **{len(excluded)} explicitly later works are excluded.** The wider coverage map tracks **{len(target_rows)} priority museums, galleries and mural sites**; it is not a claim that all are already represented in Artline.",'',
        f"Found **{len(priority)} priority image candidates** with source-backed pre-1971 dates/periods and open image labels, after omitting obvious loans and Cleveland part/ensemble records. Taipei contributes **169 additional records with open image tiers** whose attribution, date, view and resolution require selection. These counts describe research, not approved/visually reviewed attachments.",'',
        f"Separately documented **{len(surfaces)} painted surfaces in 12 Mogao caves**. Cave containers, walls, individual scenes, repainted layers and detached panels are kept distinct. Surfaces are not added to the artwork-record total.",'',
        '## Files','',
        '- [Artwork register](artwork-register.csv): every record, museum, source title/creator/date, object identity, source page, image URL, rights label and decision.',
        '- [Priority images](priority-images.csv): the conservatively dated open-image shortlist.',
        '- [Museum coverage](museum-coverage.json): all 34 target collections with actual research depth, failures and remaining gaps.',
        '- [Dunhuang surfaces](dunhuang-surfaces.json): cave/surface references and exact captured descriptions.',
        '- [Priority mural scenes](priority-mural-scenes.json): nine named scene leads, including the Nine-Coloured Deer, Mount Wutai and Medicine Buddha tableaux.',
        '- [Selected highlights](selected-highlights.json): 20 separately reviewed captions, including two explicit later-work exclusions.',
        '- `all-records.json.gz`, `in-scope-or-review.json.gz`, provider files and `captures/`: structured evidence and hashed source responses.',
        '- [Verification](verification.json), [summary](summary.json), and [read-only local audit](local-audit.json).','',
        '## Individual-record coverage','',
        '| Museum | Retained candidates |','|---|---:|']
    lines += [f"| {museum} | {count:,} |" for museum,count in sorted(summary['by_museum'].items(),key=lambda x:-x[1])]
    lines += ['', '## Selection and identity decisions','',
        '- Chinese art worldwide is included: scroll and album painting, ink landscapes, flowers/birds, portraiture, calligraphy, prints, ancient silk pictures and Buddhist/Daoist murals. Hong Kong China-trade records can have European makers; no Chinese nationality is invented.',
        '- Exact source dates are retained. Anonymous creators, traditional/qualified attributions, missing dates and unknown accessions remain unknown or qualified. Artist lifespans, excavation years, webpage dates and digital-resource dates are not creation years.',
        '- Palace Museum *Night Revels of Han Xizai* is explicitly a Song copy dated 1163–1224, not the lost Five Dynasties original. *A Thousand Li* retains the source\'s qualified discussion of 1113.',
        '- Shaanxi *Polo Game* is a Tang work excavated in 1971. Hunan\'s exercise chart was excavated in 1973; neither excavation date disqualifies the ancient artwork. The chart\'s 44 figures are one work.',
        '- The National Museum of China\'s *Founding Ceremony* page discusses the 1953 original, a 1972 copy and 1979 revision. Its reproduction is held for version resolution and is not included in the artwork shortlist.',
        '- Penn\'s Medicine Buddha panels and Nelson-Atkins\' transport sections must not inflate counts of complete mural compositions. Harvard and Guimet Dunhuang silk banners are portable paintings, not frescoes.',
        '- CC0/PDM labels come from the individual museum records. Taipei explicitly offers 1-megapixel CC0 and 6-megapixel CC BY 4.0 tiers; an image tier is not selected merely because the page has a preview. Other museum photographs retain unresolved permission status. WikiArt remains approved under existing project policy; this pass used museum records directly.',
        '- Holding evidence does not establish current display. No on-view claim was created. No candidate is automatically published.', '',
        '## Coverage gaps and limits','',
        'The deepest enumerated scans cover Cleveland, Chicago, Minneapolis, the Met, Taipei, NAMOC, Hong Kong Museum of Art and the Ashmolean. Additional exact highlights cover Beijing, Tianjin, Hunan, Shaanxi, Harvard, Guimet, Tokyo and Hong Kong Heritage Museum. Wider source/discovery coverage includes Shanghai, Liaoning, Nanjing, Zhejiang, Shanxi, Yongle Palace, Boston, Freer/Sackler, Princeton, San Francisco, British Museum, V&A, Cernuschi, ROM and Penn; these are not all import-ready.', '',
        'Some providers returned access restrictions, unavailable pages or timeouts; retrieval stopped at access restrictions. The Met capture is partial (63 accepted object records) after its API returned 403. Shanghai\'s search service did not return usable results. Liaoning/Nanjing and other dynamic or unavailable sites remain important gaps; a museum homepage does not count as artwork coverage.', '',
        'The local audit compared exact native object IDs and institution-scoped accession numbers. A missing local match does not prove a new production identity. The existing production proxy was unavailable, so production deduplication remains outstanding. No catalogue records, attachments, publication states or application code were changed; no images were downloaded, no commits or deployments made.', '',
        'This is a bounded research pass. Source result totals, captured candidates and actual catalogue additions are separate quantities. Research scripts are `ops/research-chinese-art-20261008.py`, `ops/research-chinese-museums-20261008.py` and `ops/report-chinese-art-20261008.py`.','']
    (r.RUN/'README.md').write_text('\n'.join(lines))
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
