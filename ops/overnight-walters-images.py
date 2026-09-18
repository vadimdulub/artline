#!/usr/bin/env python3
"""Match selected Walters objects to exact individually licensed museum donations."""
import argparse,collections,concurrent.futures,copy,csv,fcntl,importlib.util,json,re,time,uuid
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('walters_commons',ROOT/'ops/overnight-commons-images.py');commons=importlib.util.module_from_spec(s);s.loader.exec_module(commons);core=commons.core
core.VERSION='overnight-walters-exact-donation-v1';core.PROVIDERS['night-walters']='Walters Art Museum via Wikimedia Commons'
# Bypass no source controls: only documented public museum CSV and Commons APIs are used.
original_attach=commons.original_attach
norm=commons.norm
QUERY="""SELECT a.id::text artwork_id,a.slug,a.title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.accession_number,a.primary_media_id::text,a.current_institution_id::text,e.external_id,
 (SELECT jsonb_agg(DISTINCT p.external_id ORDER BY p.external_id) FROM artwork_artists aa JOIN external_identifiers p ON p.entity_type='artist' AND p.entity_id=aa.artist_id AND p.scheme='walters-person' WHERE aa.artwork_id=a.id) walters_people,
 (SELECT jsonb_agg(aa.attribution_role ORDER BY aa.attribution_role) FROM artwork_artists aa WHERE aa.artwork_id=a.id) roles
 FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='walters-object'
 WHERE a.status='review' AND a.work_type IN ('painting','watercolor') AND a.creation_year_start>=1000 AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' """
def ro(dsn):return psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on')
def source_match(c,o):
    if o.get('ObjectID')!=c['external_id']:raise ValueError('Museum object ID differs')
    if norm(o.get('Title'))!=norm(c['title']) or norm(o.get('AccessionNumber'))!=norm(c['accession_number']):raise ValueError('Current museum title or accession differs')
    if c['walters_people']!=o.get('Creators','').split('|') or c['roles']!=['primary'] or len(c['walters_people'])!=1:raise ValueError('Exact single source creator authority not verified')
    types=o.get('ObjectName','').casefold()
    if c['work_type']=='painting' and not any(t in types for t in ('paintings','panel painting','icons')):raise ValueError('Current source painting type not verified')
    if c['work_type']=='watercolor' and 'watercolors' not in types:raise ValueError('Current watercolor type not verified')
    if 'manuscript' in types or 'woodcut' in types or 'print' in types:raise ValueError('Source classification needs separate review')
    if 'Walters Art Museum' not in o.get('CreditLine','') or re.search(r'\b(?:loan|lent|deaccession)\b',o.get('CreditLine',''),re.I):raise ValueError('Current permanent holding not verified')
    m=re.fullmatch(r'\s*(?P<circa>(?:ca\.|c\.|circa|about)\s*)?(?P<lo>\d{4})(?:\s*[-–—/]\s*(?P<hi>\d{4}))?\s*',o.get('DateText',''),re.I)
    if not m:raise ValueError('Source date wording needs review')
    lo=int(m['lo']);hi=int(m['hi'] or m['lo']);precision=('circa' if lo==hi else 'circa_range') if m['circa'] else ('exact' if lo==hi else 'range')
    if (lo,hi,precision)!=(c['creation_year_start'],c['creation_year_end'],c['date_precision']) or not 1000<=lo<=hi<=1970:raise ValueError('Source date normalization differs')
    bounds=(int(o['DateBeginYear']),int(o['DateEndYear']))
    if not 1000<=bounds[0]<=lo<=hi<=bounds[1]<=1970:raise ValueError('Museum indexing interval conflicts or crosses cutoff')
    return {'source_year_start':lo,'source_year_end':hi,'source_date_text':o['DateText']}

def verify_file(c,page,rendered=None):
    if page.get('pageid')!=c['commons_file']['pageid']:raise ValueError('Commons page differs')
    info=page.get('imageinfo',[{}])[0];meta=info.get('extmetadata',{});field=lambda k:meta.get(k,{}).get('value','');wt=page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
    if re.search(r'\{\{\s*(?:copyvio|no permission|no source|delete|disputed|wrong license)',wt,re.I) or field('Restrictions'):raise ValueError('File rights dispute or restrictions')
    if '{{Walters Art Museum artwork' not in wt or '{{Walters Art Museum license|type=2D}}' not in wt:raise ValueError('Explicit institutional 2D donation provenance absent')
    if not re.search(r'^\|id\s*=\s*'+re.escape(c['external_id'])+r'\s*$',wt,re.M):raise ValueError('File museum object ID differs')
    if not re.search(r'^\|accession number\s*=\s*'+re.escape(c['accession_number'])+r'\s*$',wt,re.M):raise ValueError('File accession differs')
    if norm(commons.plain(field('ObjectName')))!=norm(c['title']):raise ValueError('File title differs')
    links=[a.get('href','') for a in commons.BeautifulSoup(field('Credit'),'html.parser').find_all('a')]
    if not any(re.fullmatch(r'https?://art\.thewalters\.org/detail/'+re.escape(c['external_id'])+r'/?',u) for u in links):raise ValueError('Exact official object link missing')
    label=field('LicenseShortName');uri=commons.canonical_licence_uri(field('LicenseUrl'))
    if not uri and rendered and rendered.get('pageid')==page['pageid'] and rendered.get('revid')==page.get('revisions',[{}])[0].get('revid'):uri=rendered['uri']
    if label=='Public domain' and field('Copyrighted')=='False' and uri==commons.PDM:status='public_domain'
    elif label=='CC0' and uri==commons.CC0:status='cc0'
    elif re.fullmatch(r'CC BY(?:-SA)? (?:1\.0|2\.0|2\.5|3\.0|4\.0)',label):
        code='by-sa' if 'BY-SA' in label else 'by';version=label.rsplit(' ',1)[-1]
        if uri!=f'https://creativecommons.org/licenses/{code}/{version}/':raise ValueError('Licence URI mismatch')
        status='cc_by_sa' if code=='by-sa' else 'cc_by'
    else:raise ValueError('Exact file licence is not approved')
    credit=commons.plain(field('Artist'))
    if not credit:raise ValueError('Creator credit missing')
    for key in ('Credit','Attribution'):
        extra=commons.plain(field(key))
        if extra and extra not in credit:credit+='; '+extra
    url=info.get('thumburl')
    if not url or urlparse(url).hostname not in ('upload.wikimedia.org','thumb.wikimedia.org'):raise ValueError('Unexpected final image host')
    return info,credit,label,uri,status,url

def project_file(page):
    # Keep rights/identity fields, not the museum's authored artwork description.
    projected=copy.deepcopy(page)
    for info in projected.get('imageinfo',[]):info.get('extmetadata',{}).pop('ImageDescription',None)
    wt=projected.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
    lines=['{{Walters Art Museum artwork']+[line for line in wt.splitlines() if re.match(r'^\|(?:id|accession number|artist|title)\s*=',line)]+['}}','{{Walters Art Museum license|type=2D}}']
    projected['revisions'][0]['slots']['main']['*']='\n'.join(lines)
    projected['projection_note']='Only original identity and licence lines retained; complete source capture remains pinned by API response checksum and page revision.'
    return projected

def select(run,dsn):
    path=run/'candidates.json'
    if path.exists():return json.loads(path.read_text())['candidates']
    leads=json.loads((run/'source-leads.json').read_text());accepted=[];held=[];metadata=json.loads((run/'art.csv.receipt.json').read_text())
    with (run/'creators.csv').open() as f:creators={r['id']:r for r in csv.DictReader(f)}
    with ro('postgres://localhost/artline') as db:
        inst=db.execute("SELECT id::text FROM institutions WHERE wikidata_id='Q210081' AND status<>'archived'").fetchall();assert len(inst)==1;iid=inst[0]['id']
        for c in leads:
            try:
                o=c['walters_object'];scope=source_match(c,o);ar=creators[c['walters_people'][0]]
                if re.search(r'\b(?:attributed|after|workshop|school|follower|circle|possibly|probably|anonymous)\b',ar['name'],re.I):raise ValueError('Source creator qualification needs review')
                life=re.search(r'(?<!\d)(\d{4})\s*[-–]\s*(\d{4})(?!\d)',ar.get('date',''))
                if life and int(life[1])==c['creation_year_start'] and int(life[2])==c['creation_year_end'] and life[1]!=life[2]:raise ValueError('Creation range repeats creator lifespan')
                source={k:o.get(k) for k in ('ObjectID','AccessionNumber','ObjectName','DateBeginYear','DateEndYear','DateText','Title','Dimensions','Medium','Classification','ResourceURL','CreditLine','Creators')}
                accepted.append({**{k:v for k,v in c.items() if k!='walters_object'},'provider':'night-walters','scheme':'walters-object','walters_object':source,'metadata_capture':metadata,'scope_evidence':scope,'target_ids':{'local':c['artwork_id']},'institution_ids':{'local':iid}})
            except (ValueError,KeyError) as e:held.append({'id':c['artwork_id'],'reason':str(e)})
        before=db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE a.id=ANY(%s::uuid[])',([c['artwork_id'] for c in accepted],)).fetchall();core.save_new(run/'local-before.json',before)
    core.save_new(path,{'created_at':core.now(),'candidates':accepted,'production_identity_pending':True});core.save_new(run/'source-held.json',held);print('Walters selected',len(accepted),'held',len(held),dict(collections.Counter(x['reason'] for x in held)),flush=True);return accepted

def attach(db,im,target):
    source_match(im,im['raw']['walters_object']);verify_file(im,im['raw']['commons_file'],im.get('rendered_licence_evidence'))
    with db.transaction():
        rows=db.execute(QUERY+' AND e.external_id=%s FOR UPDATE OF a',(im['external_id'],)).fetchall()
        if len(rows)!=1 or rows[0]['artwork_id']!=im['target_ids'][target] or any(rows[0][k]!=im[k] for k in ('title','date_display','date_precision','creation_year_start','creation_year_end','walters_people','roles')):raise ValueError('Target catalogue identity changed')
        row=rows[0];iid=im['institution_ids'][target]
        if row['primary_media_id'] and row['primary_media_id']!=im['media_id']:return 'existing_media_preserved'
        if row['current_institution_id'] not in (None,iid):raise ValueError('Existing holding conflict')
        holdings=db.execute("SELECT institution_id::text FROM artwork_location_assertions WHERE artwork_id=%s AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL",(row['artwork_id'],)).fetchall()
        if holdings and (len(holdings)!=1 or holdings[0]['institution_id']!=iid):raise ValueError('Existing holding assertion conflict')
        if not holdings:
            slug='overnight-walters-primary-images-20260915';db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,'Walters Art Museum: official collection dataset','museum_api','https://github.com/WaltersArtMuseum/api-thewalters-org',%s) ON CONFLICT(slug) DO NOTHING",(slug,commons.CC0));sid=db.execute('SELECT id FROM sources WHERE slug=%s',(slug,)).fetchone()['id']
            db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(row['artwork_id'],iid,sid,im['source_record_url'],'Current official dataset confirms museum credit line, exact object ID, accession, creator authority, type and creation date. Holding only; no current display claim.',im['checked_at']))
        result=original_attach(db,im,target)
        if result=='attached':db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
        return result
core.attach=attach

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=20);p.add_argument('--deadline',type=float,required=True);p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    lock=(a.run/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if not (a.run.parent/'backups.json').exists():raise SystemExit('Verified backups required')
    if not a.prepare_only:raise SystemExit('Production identity preflight required before enabling Walters uploads')
    rows=select(a.run,None);done={k for k,v in core.latest_events(a.run).items() if v['outcome'] in ('complete','prepared','manual_review','failed')};rows=[c for c in rows if c['artwork_id'] not in done][:a.limit];fetcher=core.Fetcher(a.run/'commons-evidence');render=core.Fetcher(a.run/'rendered-licences')
    for start in range(0,len(rows),20):
        if time.time()>=a.deadline:break
        group=rows[start:start+20];new=[c for c in group if not (a.run/'selected/night-walters'/(c['artwork_id']+'.json')).exists()]
        if new:
            params={'action':'query','pageids':'|'.join(str(c['commons_file']['pageid']) for c in new),'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main'}
            d=commons.api(fetcher,'commons.wikimedia.org',params);pages=d.get('query',{}).get('pages',{})
            for c in new:
                try:
                    page=pages.get(str(c['commons_file']['pageid']),{});rendered=commons.rendered_rights_uri(render,page);info,credit,label,uri,status,url=verify_file(c,page,rendered);checked=core.now();projected=project_file(page);verify_file(c,projected,rendered)
                    im=dict(c,page=info['descriptionurl'],source_image_url=url,raw={'walters_object':c['walters_object'],'metadata_capture':c['metadata_capture'],'commons_file':projected},rendered_licence_evidence=rendered,
                       policy_url=uri,rights_status=status,license_label=label,creator_credit=credit,checked_at=checked,source_name=core.PROVIDERS['night-walters'],source_record_url='https://art.thewalters.org/detail/'+c['external_id'],
                       image_url=url,image_license=label,image_license_url=uri,rights_statement=label,creator=c['artist'],creation_date=c['date_display'],source_object_id=c['external_id'],rights_verified_at=checked)
                    im['attribution_text']=f"{c['artist']}. {c['title']}. {credit}. {info['descriptionurl']}. {label} ({uri}). Full-frame proportional resize and JPEG compression."+(' This adaptation is shared under the same licence.' if status=='cc_by_sa' else '')
                    core.save_new(a.run/'selected/night-walters'/(c['artwork_id']+'.json'),im)
                except ValueError as exc:core.event(a.run,{'provider':'night-walters','artwork_id':c['artwork_id'],'external_id':c['external_id'],'outcome':'manual_review','reason':str(exc)})
        ready=[c for c in group if (a.run/'selected/night-walters'/(c['artwork_id']+'.json')).exists()]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            for future in [pool.submit(core.worker,'night-walters',ready[n::3],SimpleNamespace(run=a.run,prepare_only=True),None) for n in range(3) if ready[n::3]]:future.result()
        print(core.now(),'Walters checked',start+len(group),'of',len(rows),dict(core.COUNTS),flush=True)
if __name__=='__main__':main()
