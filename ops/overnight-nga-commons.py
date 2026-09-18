#!/usr/bin/env python3
"""Match existing NGA objects to individually CC0 museum donations on Commons."""
import argparse,collections,concurrent.futures,csv,fcntl,importlib.util,json,re,time,unicodedata
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode,urlparse
import psycopg
from psycopg.rows import dict_row
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('nga_core',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
core.VERSION='overnight-nga-museum-commons-cc0-v1';core.PROVIDERS['night-nga-commons']='National Gallery of Art via Wikimedia Commons';core.HOSTS.add('thumb.wikimedia.org')
CC0='https://creativecommons.org/publicdomain/zero/1.0/'
def norm(v):return ' '.join(re.findall(r'[^\W_]+',unicodedata.normalize('NFKD',str(v).casefold())))
def plain(v):return BeautifulSoup(v or '','html.parser').get_text(' ',strip=True)
def visible_title_variants(value):
    soup=BeautifulSoup(value or '','html.parser')
    for node in list(soup.select('[style], [hidden], .noprint')):
        if node.attrs is not None and (node.has_attr('hidden') or 'noprint' in node.get('class',[]) or re.search(r'display\s*:\s*none',node.get('style',''),re.I)):
            node.decompose()
    texts={norm(soup.get_text(' ',strip=True))}
    texts.update(norm(n.get_text(' ',strip=True)) for n in soup.select('[lang], i, .fn'))
    return texts-{''}
def ro(dsn):return psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on')

QUERY='''SELECT a.id::text artwork_id,a.slug,a.title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,
 a.accession_number,a.primary_media_id::text,e.scheme,e.external_id,e.source_id::text,
 (SELECT string_agg(p.display_name,'; ' ORDER BY p.display_name) FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id) artist,
 EXISTS(SELECT 1 FROM artwork_artists aa JOIN artist_discovery_selection d ON d.artist_id=aa.artist_id WHERE aa.artwork_id=a.id AND d.is_popular) popular
 FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='european-nga-object'
 WHERE a.status='review' AND a.creation_year_start>=1000 AND a.work_type IN ('painting','drawing','print','watercolor')
 AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' AND artline_has_selection_evidence(a.id) '''

def object_match(c,o):
    if str(o.get('objectid'))!=c['external_id'] or o.get('accessioned')!='1' or o.get('isvirtual')!='0':raise ValueError('Unconfirmed physical NGA holding')
    kinds={'painting':('painting',),'drawing':('drawing',),'print':('print',),'watercolor':('watercolor','drawing','painting')}
    if o.get('classification','').casefold() not in kinds[c['work_type']]:raise ValueError('Museum type conflict')
    if norm(o.get('title'))!=norm(c['title']):raise ValueError('Current NGA title differs')
    if not c['accession_number'] or norm(o.get('accessionnum'))!=norm(c['accession_number']):raise ValueError('Museum accession conflict')
    if not re.fullmatch(r'\d{4}',o.get('beginyear','')) or not re.fullmatch(r'\d{4}',o.get('endyear','')):raise ValueError('Museum date missing')
    lo,hi=int(o['beginyear']),int(o['endyear'])
    if not 1000<=lo<=hi<=1970 or hi<c['creation_year_start'] or lo>c['creation_year_end']:raise ValueError('Museum date conflict')

def select(run,dsn):
    path=run/'candidates.json'
    if path.exists():return json.loads(path.read_text())['candidates']
    files=json.loads((run/'commons-file-index.json').read_text())
    if not files.get('complete'):raise ValueError('Complete Commons filename index required')
    by_id=collections.defaultdict(list)
    for f in files['files']:
        match=re.search(r'\bNGA (\d+)\.(?:jpg|jpeg|png|tif|tiff)$',f['title'],re.I)
        if match:by_id[match[1]].append(f)
    with (run/'metadata/objects.csv').open() as f:objects={o['objectid']:o for o in csv.DictReader(f)}
    with (run/'metadata/nga-published-images.csv').open() as f:open_ids={o['depictstmsobjectid'] for o in csv.DictReader(f) if o['openaccess']=='1' and o['viewtype']=='primary'}
    source_receipt=json.loads((run/'metadata/objects.receipt.json').read_text())
    with ro('postgres://localhost/artline') as db:rows=db.execute(QUERY+' AND a.primary_media_id IS NULL ORDER BY popular DESC,(a.work_type=\'painting\') DESC,a.id').fetchall()
    accepted=[];held=[]
    for c in rows:
        if len(by_id.get(c['external_id'],[]))!=1:held.append({'id':c['artwork_id'],'reason':'No unique exact-file lead'});continue
        if c['external_id'] not in open_ids:held.append({'id':c['artwork_id'],'reason':'Current NGA open-image statement absent'});continue
        o=objects.get(c['external_id'],{})
        try:object_match(c,o)
        except ValueError as e:held.append({'id':c['artwork_id'],'reason':str(e)});continue
        if not c['artist']:held.append({'id':c['artwork_id'],'reason':'Catalogue creator unresolved'});continue
        fields=('objectid','accessioned','accessionnum','title','displaydate','beginyear','endyear','medium','attribution','creditline','classification','isvirtual','wikidataid')
        accepted.append(dict(c,provider='night-nga-commons',nga_object={k:o[k] for k in fields},nga_metadata_capture=source_receipt,
          commons_file=by_id[c['external_id']][0],target_ids={'local':c['artwork_id']}))
    with ro(dsn) as db:
        remote=db.execute(QUERY+' AND e.external_id=ANY(%s)',([c['external_id'] for c in accepted],)).fetchall();index=collections.defaultdict(list)
        for r in remote:index[r['external_id']].append(r)
        valid=[]
        for c in accepted:
            hits=index[c['external_id']]
            if len(hits)!=1 or any(hits[0][k]!=c[k] for k in ('slug','title','creation_year_start','creation_year_end','work_type','accession_number')):
                held.append({'id':c['artwork_id'],'reason':'Production object identity requires review'});continue
            if hits[0]['primary_media_id']:continue
            c['target_ids']['cloud']=hits[0]['artwork_id'];valid.append(c)
    core.save_new(path,{'created_at':core.now(),'candidates':valid});core.save_new(run/'held.json',held)
    for target,conn in [('local','postgres://localhost/artline'),('cloud',dsn)]:
        with ro(conn) as db:
            before=db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE a.id=ANY(%s::uuid[])',([c['target_ids'][target] for c in valid],)).fetchall();core.save_new(run/(target+'-before.json'),before)
    print('NGA independent candidates',len(valid),'held',len(held),'types',dict(collections.Counter(c['work_type'] for c in valid)),flush=True)
    return valid

def verify_file(c,page):
    if str(page.get('pageid'))!=str(c['commons_file']['pageid']):raise ValueError('Commons file identity mismatch')
    info=page.get('imageinfo',[{}])[0];meta=info.get('extmetadata',{});field=lambda k:meta.get(k,{}).get('value','')
    if field('LicenseShortName')!='CC0' or field('Restrictions'):raise ValueError('Exact Commons file is not unrestricted CC0')
    if not re.fullmatch(r'https?://creativecommons\.org/publicdomain/zero/1\.0(?:/(?:deed\.[a-z-]+|legalcode(?:\.[a-z-]+)?))?/?',field('LicenseUrl')):raise ValueError('Explicit CC0 URI absent')
    wt=page.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
    if re.search(r'\{\{\s*(?:copyvio|delete|no permission|wrong license|disputed)',wt,re.I):raise ValueError('File has unresolved rights dispute')
    identity=bool(re.search(r'https?://purl\.org/nga/collection/artobject/'+re.escape(c['external_id'])+r'(?!\d)',wt))
    if not identity:raise ValueError('Original NGA object URL missing from file record')
    if norm(c['nga_object']['title']) not in visible_title_variants(field('ObjectName')):raise ValueError('File title does not match current NGA title')
    if c['nga_object']['accessionnum'] not in wt:raise ValueError('File accession does not match NGA')
    if 'National Gallery of Art' not in plain(field('Credit')) or 'NGADC' not in wt:raise ValueError('Museum donation provenance absent')
    credit=plain(field('Artist'))+'; '+plain(field('Credit'))
    if not plain(field('Artist')):raise ValueError('Missing source image attribution')
    url=info.get('thumburl')
    if not url or urlparse(url).hostname not in {'upload.wikimedia.org','thumb.wikimedia.org'}:raise ValueError('Permitted Commons rendition missing')
    return info,credit,url

original_attach=core.attach
def attach(db,im,target):
    object_match(im,im['raw']['nga_object'])
    with db.transaction():
        rows=db.execute(QUERY+' AND e.external_id=%s',(im['external_id'],)).fetchall()
        if len(rows)!=1 or rows[0]['artwork_id']!=im['target_ids'][target] or any(rows[0][k]!=im[k] for k in ('title','creation_year_start','creation_year_end','work_type','accession_number')):raise ValueError('NGA catalogue identity changed')
        result=original_attach(db,im,target)
        if result=='attached':db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
        return result
core.attach=attach

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--limit',type=int,default=25);p.add_argument('--deadline',type=float,required=True);p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    lock=(a.run/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if not (a.run.parent/'backups.json').exists():raise SystemExit('Verified recovery backups required')
    if not a.prepare_only and (a.run/'candidates.json').exists() and json.loads((a.run/'candidates.json').read_text()).get('production_metadata_pending'):raise SystemExit('Production metadata import and target reconciliation required before uploading this expansion')
    dsn=None if a.prepare_only else core.cloud_dsn();rows=select(a.run,dsn);done=set()
    done={key for key,r in core.latest_events(a.run).items() if r.get('outcome') in (('complete','failed','manual_review','prepared') if a.prepare_only else ('complete','failed','manual_review'))}
    rows=[c for c in rows if c['artwork_id'] not in done][:a.limit];fetcher=core.Fetcher(a.run/'commons-evidence')
    for start in range(0,len(rows),50):
        if time.time()>=a.deadline:break
        group=rows[start:start+50];new=[c for c in group if not (a.run/'selected/night-nga-commons'/(c['artwork_id']+'.json')).exists()]
        if new:
            params={'action':'query','pageids':'|'.join(str(c['commons_file']['pageid']) for c in new),'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main','format':'json','maxlag':5}
            d=fetcher.metadata('https://commons.wikimedia.org/w/api.php?'+urlencode(params))
            if d.get('error'):raise RuntimeError('Commons requests pause: '+d['error'].get('code','unknown'))
            pages=d.get('query',{}).get('pages',{})
            for c in new:
                try:
                    page=pages.get(str(c['commons_file']['pageid']),{});info,credit,url=verify_file(c,page)
                    im=dict(c,page=info['descriptionurl'],source_image_url=url,raw={'nga_object':c['nga_object'],'nga_metadata_capture':c['nga_metadata_capture'],'commons_file':page},
                      policy_url=CC0,rights_status='cc0',license_label='CC0 1.0',creator_credit=credit,checked_at=core.now(),
                      source_name=core.PROVIDERS['night-nga-commons'],source_record_url='https://purl.org/nga/collection/artobject/'+c['external_id'],image_url=url,
                      image_license='CC0 1.0',image_license_url=CC0,rights_statement='CC0',creator=c['artist'],creation_date=c['date_display'],source_object_id=c['external_id'],rights_verified_at=core.now())
                    im['attribution_text']=f"{c['artist']}. {c['title']}. {credit}. {info['descriptionurl']}. CC0 ({CC0}). Full-frame proportional resize and JPEG compression."
                    core.save_new(a.run/'selected/night-nga-commons'/(c['artwork_id']+'.json'),im)
                except ValueError as e:core.event(a.run,{'provider':'night-nga-commons','artwork_id':c['artwork_id'],'external_id':c['external_id'],'outcome':'manual_review','reason':str(e)})
        ready=[c for c in group if (a.run/'selected/night-nga-commons'/(c['artwork_id']+'.json')).exists()]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            jobs=[pool.submit(core.worker,'night-nga-commons',ready[n::3],SimpleNamespace(run=a.run,prepare_only=a.prepare_only),dsn) for n in range(3) if ready[n::3]]
            for job in jobs:job.result()
        print(core.now(),'NGA matched chunk',start+len(group),'of',len(rows),dict(core.COUNTS),flush=True)

if __name__=='__main__':main()
