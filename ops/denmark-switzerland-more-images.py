#!/usr/bin/env python3
"""Bounded follow-up: existing DK/CH works, independently cleared pictures only."""
import argparse
import concurrent.futures
import importlib.util
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import quote,unquote,urljoin

spec=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('denmark-switzerland-museums.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
b,core=c.b,c.core
ROOT=c.ROOT
PRIOR=c.RUN
RUN=ROOT/'docs/research/denmark-switzerland-more-images-20260918'
BACKUP=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/denmark-switzerland-more-images-20260918')
b.RUN=RUN;b.BACKUP=BACKUP;b.SOURCE='denmark-switzerland-more-images-20260918'
save,load,connect,capture,uid=b.save,b.load,b.connect,b.capture,b.uid

LEADS={
 'basel-1077':'File:Hemessen-Selbstbildnis.jpg',
 'basel-969':'File:The Body of the Dead Christ in the Tomb by Hans Holbein d. J.-Kunstmuseum Basel.jpg',
 'basel-1207':'File:Senecio (Baldgreis), Klee 1080998.jpg',
 'basel-1569':'File:Équilibre de S. Taueber-Arp (Kunstmuseum, Bâle).jpg',
 'basel-40269':'File:Kirchner - Stafelalp, Rückkehr der Tiere, 1919, Inv. G 2017.10.jpg',
 'basel-1516':'File:Marc - Tierschicksale (Die Bäume zeigten ihre Ringe, die Tiere ihre Adern), 1913, Inv. 1739.jpg',
 'glyptotek-min-1753':'File:Claude Monet - Shadows on the Sea. The Cliffs at Pourville - Google Art Project.jpg',
 'hirschsprung-hammershoi-bedroom':'File:Vilhelm Hammershøi, Sovekammer, 1890, Den Hirschsprungske Samling.jpg',
 'hirschsprung-hammershoi-old-woman':'File:Vilhelm Hammershøi - An old woman - Google Art Project.jpg',
 'hirschsprung-johansen-silent-night':'File:Viggo Johansen - Glade jul - 1891.jpg',
 'mcba-interieur-aux-deux-verres-interior-with-two-glasses':'File:Intérieur aux deux verres.jpg',
 'mcba-les-tresseuses-de-paille-women-weaving-straw':'File:Ernest Biéler Les tresseuses de paille 1.jpg',
}

def audit():
    prior_plan=load(PRIOR/'metadata-plan.json');review=load(PRIOR/'metadata-review.json')
    result=dict(at=core.now(),prior_plan_sha256=core.sha((PRIOR/'metadata-plan.json').read_bytes()),targets={})
    assert result['prior_plan_sha256']==review['plan_sha256']
    for target in ('local','cloud'):
        selected=[p for p in prior_plan['targets'][target] if p['record']['key'] in review['selected_keys']]
        ids=[p.get('artwork_id') or p['work']['id'] for p in selected]
        with connect(target) as db:
            rows=db.execute('''SELECT to_jsonb(a) row,artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) date_scope,
              (SELECT jsonb_agg(to_jsonb(l) ORDER BY l.id) FROM artwork_location_assertions l WHERE l.artwork_id=a.id) locations,
              (SELECT jsonb_agg(to_jsonb(x) ORDER BY x.artist_id) FROM artwork_artists x WHERE x.artwork_id=a.id) artists
              FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',(ids,)).fetchall()
        assert len(rows)==47;byid={r['row']['id']:r for r in rows}
        records=[dict(record=p['record'],before=byid[p.get('artwork_id') or p['work']['id']]) for p in selected]
        result['targets'][target]=records
        save(BACKUP/(target+'-scoped-preimages.json'),records)
        print(target,'scoped',len(rows),'missing images',sum(r['row']['primary_media_id'] is None for r in rows),flush=True)
    save(RUN/'audit.json',result)

def file_evidence(soup):
    fields={}
    for tr in soup.select('tr'):
        cells=tr.find_all(['td','th'],recursive=False)
        if len(cells)!=2:continue
        label=cells[0].get_text(' ',strip=True)
        if len(label)>110:continue
        if label in ('Artist','Author','Date','Collection','Current location','Accession number','Source/Photographer','Source','Title','Notes','References') or label.startswith('Description'):
            fields[label]=cells[1].get_text(' ',strip=True)
    licenses=[]
    for t in soup.select('.licensetpl'):
        licenses.append(dict(text=t.get_text(' ',strip=True),links=[urljoin('https://commons.wikimedia.org',a['href']) for a in t.select('a[href]') if 'creativecommons.org/' in a['href']]))
    previews=[]
    for a in soup.select('.mw-filepage-other-resolutions a[href], .fullImageLink a[href]'):
        url=urljoin('https://commons.wikimedia.org',a['href']).split('?')[0]
        if not any(p['url']==url for p in previews):previews.append(dict(url=url,label=a.get_text(' ',strip=True)))
    return dict(fields=fields,licenses=licenses,previews=previews)

def research():
    out=[]
    for key,title in LEADS.items():
        try:
            soup,receipt=capture('https://commons.wikimedia.org/wiki/'+quote(title.replace(' ','_'),safe=':()'),'file-'+key)
            e=dict(key=key,title=title,receipt=receipt,**file_evidence(soup));out.append(e)
            print(key,json.dumps(e['fields'],ensure_ascii=False)[:2300],flush=True)
            print('LICENSES',json.dumps(e['licenses'],ensure_ascii=False)[:2200],flush=True)
        except Exception as error:
            out.append(dict(key=key,title=title,error=str(error)));print(key,str(error),flush=True)
    save(RUN/'file-evidence.json',out)

CHOICES={
 'basel-1077':('basel-1077-visitor','cc_by_sa','Paradise Chronicle; Kunstmuseum Basel','1361','Own photograph explicitly licensed CC BY-SA 4.0; inventory 1361 and native record 1077 match. Photo date 2021 is not the artwork creation year.'),
 'basel-969':('basel-969','public_domain','The Yorck Project / Zenodot Verlagsgesellschaft; Kunstmuseum Basel','318','Exact Basel inventory 318 and native object 969; individual Yorck reproduction explicitly public domain, distinct from the compilation licence.'),
 'basel-1207':('basel-1207','cc_by_sa','Sizzlipedia; Kunstmuseum Basel','Inv. 1569','Photographer Sizzlipedia explicitly releases own photograph under CC BY-SA 4.0. Description gives exact Basel inventory 1569 and 1922 work number 181.'),
 'basel-1482':('basel-1482','cc_by_sa','Kunstmuseum Basel; Wikimedia Commons upload by Maltaper','G 1986.15','Exact museum inventory and object 1482; file gives 1919, matching the primary record. Explicit file CC BY-SA 4.0 retained alongside original museum public-domain permission.'),
 'basel-40269':('basel-40269','public_domain','Kunstmuseum Basel; Schenkung Eberhard W. Kornfeld','G 2017.10','Exact museum inventory G 2017.10, native object 40269 and 1919 title. File Date is a 2017 photographic timestamp, not an artwork-date correction.'),
 'basel-1516':('basel-1516','public_domain','Kunstmuseum Basel; mit einem Sonderkredit der Basler Regierung erworben','1739','Full title, 1913 creation, museum source and inventory 1739 match primary object 1516. Per-image museum public-domain permission and Commons PD statement retained.'),
 'glyptotek-min-1753':('glyptotek-min-1753','public_domain','Ny Carlsberg Glyptotek / Google Art Project','MIN 1753','Exact MIN 1753, Monet, 1882, title, dimensions and museum; museum partner reproduction with individual public-domain statement.'),
 'hirschsprung-hammershoi-old-woman':('hirschsprung-hammershoi-old-woman','public_domain','The Hirschsprung Collection / Google Art Project','1886','Creator, An old woman, 1886 and Hirschsprung match the museum-authored caption; Google partner asset jgGGA9DKrq0a_A. Not the different work An old woman standing by a window.'),
 'hirschsprung-johansen-silent-night':('hirschsprung-johansen-silent-night','public_domain','The Hirschsprung Collection / Museernes Samlinger','205','Glade jul / Happy Christmas / Silent Night, Johansen 1891, inventory 205. Exact file is linked from the public selection directed by Hirschsprung photo policy; current upload source is the Danish museum register.'),
}

def backup_verify():
    request=load(BACKUP/'cloud-request.json');bid=request['backupContext']['backupId']
    cloud=json.loads(subprocess.check_output(['gcloud','sql','backups','describe',str(bid),'--instance=artline-postgres','--project=artline-508319','--format=json'],text=True))
    assert cloud['status']=='SUCCESSFUL'
    local=load(BACKUP/'local-verified.json');assert Path(local['path']).stat().st_size==local['bytes']
    save(RUN/'backups.json',dict(at=core.now(),local=local,cloud=cloud));print('Both backups verified',flush=True)

def select_preview(e):
    candidates=[]
    for p in e['previews']:
        m=re.match(r'([\d,]+) × ([\d,]+)',p['label'])
        if not m:continue
        w,h=[int(v.replace(',','')) for v in m.groups()]
        if 800<=max(w,h)<=1800 and p['url'].lower().endswith('.jpg'):
            candidates.append((abs(max(w,h)-1300),p['url']))
    assert candidates,'No adequately sized bounded published preview'
    return sorted(candidates)[0][1]

def selection():
    audit=load(RUN/'audit.json');out=[]
    evidence={e['key']:e for e in load(RUN/'file-evidence.json')+load(RUN/'extra-file-evidence.json')}
    for key,(filekey,rights,credit,needle,note) in CHOICES.items():
        e=evidence[filekey];assert not e.get('error')
        raw=(RUN/'captures'/('file-'+filekey+'.html')).read_bytes();assert core.sha(raw)==e['receipt']['sha256']
        soup=b.BeautifulSoup(raw,'html.parser');text=soup.get_text(' ',strip=True);assert needle in text
        template_text=' '.join(t['text'] for t in e['licenses'])
        if rights=='cc_by_sa':
            assert 'Creative Commons Attribution-Share Alike 4.0' in template_text
            policy='https://creativecommons.org/licenses/by-sa/4.0/';label='CC BY-SA 4.0'
        else:
            assert 'Public domain' in template_text
            policy='https://creativecommons.org/publicdomain/mark/1.0/';label='Public Domain Mark 1.0'
        selected=[p for p in audit['targets']['local'] if p['record']['key']==key];assert len(selected)==1
        r=selected[0]['record'];museum={'basel':'Kunstmuseum Basel','hirschsprung':'The Hirschsprung Collection','glyptotek':'Ny Carlsberg Glyptotek'}[r['museum']]
        assert core.sha((PRIOR/'captures'/(r['capture_key']+'.html')).read_bytes())==r['source']['sha256']
        im=dict(key=key,title=r['title'],artist=r['creator_label'],external_id=r['native_id'],provider='denmark-switzerland-followup',
            source_image_url=select_preview(e),page=e['receipt']['url'],policy_url=policy,rights_status=rights,license_label=label,creator_credit=credit,
            checked_at=core.now(),source_evidence_sha256=e['receipt']['sha256'],identity_basis=note,source_record=dict(r,collection_label=museum),
            rights_evidence=dict(file=e,primary_object=r['source'],review_note=note,footer_licenses_excluded=True),targets={})
        if r['museum']=='basel':
            label_txt='Bilddaten gemeinfrei - Kunstmuseum Basel'
            assert r['fields']['ObjDetailRightsTxt']['LabelTxt']==label_txt
            im['rights_evidence']['primary_image_rights']=dict(label=label_txt,terms=load(PRIOR/'captures/basel-image-use-terms.receipt.json'))
            im['rights_evidence']['delivery_route']='Independent publicly available Commons file; no request to the previously denied museum image route.'
        if r['museum']=='hirschsprung':
            im['rights_evidence']['museum_photo_policy']=load(PRIOR/'captures/index-hirschsprung-rights.receipt.json')
            im['rights_evidence']['supply_terms_scope']='Existing public reproduction, not an ordered museum photograph. File-specific public-domain origin evidence retained; no museum endorsement claimed.'
        im['attribution_text']=r['creator_label']+'. '+r['title']+' ('+r['date']['display']+'). '+credit+'. '+label+' ('+policy+'). '+im['page']+'. Accessed '+im['checked_at']+'. Full-frame proportional resize and JPEG compression; no crop or generated content.'
        if rights=='cc_by_sa':im['attribution_text']+=' This derivative remains available under CC BY-SA 4.0.'
        for target in ('local','cloud'):
            p=next(p for p in audit['targets'][target] if p['record']['key']==key)
            before=p['before'];assert before['date_scope']=='eligible' and before['row']['status']=='review' and before['row']['primary_media_id'] is None
            im['targets'][target]=dict(id=before['row']['id'],before=before['row'])
        im['artwork_id']=im['targets']['local']['id'];out.append(im)
    assert len(out)==9
    save(RUN/'image-selection-v2.json',out);save(BACKUP/'image-target-preimages-v2.json',out)
    print('Selected',len(out),'images; pin',core.sha((RUN/'image-selection-v2.json').read_bytes()),flush=True)

def ensure_source(db):
    sid=uid('source')
    db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,'Denmark and Switzerland — selected reproduction follow-up','collection_page','https://commons.wikimedia.org/') ON CONFLICT(slug) DO NOTHING",(sid,b.SOURCE))
    assert str(db.execute('SELECT id FROM sources WHERE slug=%s',(b.SOURCE,)).fetchone()['id'])==sid
    return sid
b.ensure_source=ensure_source

def upload():
    backup=load(RUN/'backups.json');assert backup['cloud']['status']=='SUCCESSFUL' and backup['local']['directory_verified']
    b.image_upload(adapter_version='denmark-switzerland-followup-v1',selection_name='image-selection-v2.json')

def held_report():
    audit=load(RUN/'audit.json');held=[]
    for p in audit['targets']['local']:
        r=p['record'];key=r['key'];before=p['before']
        if before['row']['primary_media_id'] or key in CHOICES:continue
        if before['date_scope']!='eligible':reason='Creation-date uncertainty retained; not automatically eligible for image selection.'
        elif key=='basel-1569':reason='Taeuber-Arp file describes Équilibre 1932, whereas the selected native object says 1934; exact-object reconciliation unresolved.'
        elif key=='hirschsprung-wegmann-jeanna-bauck':reason='Prior museum 1885 / Commons 1887 conflict remains unresolved.'
        elif key=='hirschsprung-hammershoi-bedroom':reason='Correct-work DR image lacks sufficiently specific reproduction-origin permission; alternate 1890 Interior belongs to Ordrupgaard, and Bedroom study is a separate private work.'
        elif key=='hirschsprung-syberg-woodland':reason='No exact-work rights-cleared reproduction found in selected search; 1916 Skovparti is a different work.'
        elif key.startswith('mcba-'):
            reason='No sufficiently documented commercially reusable exact-work photo selected. MCBA website permissions are restricted; no museum photo copied on artwork age alone.'
            if 'interieur-aux' in key:reason+=' Commons file explicitly has unknown reproduction source.'
            elif 'tresseuses' in key:reason+=' Commons lead traces only to Pinterest, not an established photographic source.'
            elif 'marquis' in key:reason+=' Commons public-domain assertion does not resolve MCBA-sourced photograph permission conflict.'
        else:reason='Primary museum source retains protected rights; no independently cleared exact-work reproduction selected.'
        held.append(dict(key=key,title=r['title'],reason=reason))
    assert len(held)==28
    save(RUN/'held.json',dict(at=core.now(),records=held,known_access_limits='No retries to previously denied Basel image server or Commons API; independently public Commons pages and thumbnails only.'))

def verify():
    audit=load(RUN/'audit.json');selection=load(RUN/'image-selection-v2.json');uploaded=load(RUN/'image-upload-summary.json')
    assert len(selection)==len(uploaded)==9
    bykey={i['key']:i for i in uploaded};result=dict(at=core.now(),targets={})
    ignore={'primary_media_id','revision','updated_at','updated_by'}
    for target in ('local','cloud'):
        pre=audit['targets'][target];ids=[p['before']['row']['id'] for p in pre]
        with connect(target) as db:
            rows=db.execute('''SELECT to_jsonb(a) row,
              (SELECT jsonb_agg(to_jsonb(l) ORDER BY l.id) FROM artwork_location_assertions l WHERE l.artwork_id=a.id) locations,
              (SELECT jsonb_agg(to_jsonb(x) ORDER BY x.artist_id) FROM artwork_artists x WHERE x.artwork_id=a.id) artists,
              to_jsonb(m) media,
              (SELECT jsonb_agg(to_jsonb(e)) FROM media_rights_evidence e WHERE e.media_id=m.id AND e.source_id=%s) evidence
              FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])''',(uid('source'),ids)).fetchall()
        assert len(rows)==47;byid={r['row']['id']:r for r in rows};changed=[]
        for p in pre:
            key=p['record']['key'];before=p['before'];after=byid[before['row']['id']]
            assert after['locations']==before['locations'] and after['artists']==before['artists']
            if key not in bykey:
                assert after['row']==before['row'];continue
            receipt=bykey[key];a=after['row'];media=after['media']
            assert {k:v for k,v in a.items() if k not in ignore}=={k:v for k,v in before['row'].items() if k not in ignore}
            assert a['primary_media_id']==receipt['media_id'] and a['revision']==before['row']['revision']+1
            assert a['status']=='review' and a['published_at'] is None and a['current_institution_id'] is None
            assert media['checksum_sha256']==receipt['sha256'] and media['byte_size']==receipt['bytes']<=100000
            assert len(after['evidence'])==1 and after['evidence'][0]['adapter_version']=='denmark-switzerland-followup-v1'
            assert after['evidence'][0]['evidence_json']['selection_sha256']==core.sha((RUN/'image-selection-v2.json').read_bytes())
            changed.append(dict(key=key,artwork_id=a['id'],title=a['title'],media_id=a['primary_media_id'],path=media['storage_path'],sha256=media['checksum_sha256'],bytes=media['byte_size'],rights_status=media['rights_status'],license_url=media['license_url']))
        result['targets'][target]=dict(new_images=len(changed),missing_images_after=sum(r['row']['primary_media_id'] is None for r in rows),unchanged_non_image_metadata=True,unchanged_artist_and_location_assertions=True,unchanged_other_artworks=38,records=sorted(changed,key=lambda r:r['key']))
        assert len(changed)==9 and result['targets'][target]['missing_images_after']==28
        print(target,'verified 9 images; all 47 works retain metadata, creator links and holding states',flush=True)
    assert result['targets']['local']['records']==result['targets']['cloud']['records']
    save(RUN/'verification.json',result)

def public_verify():
    site='https://artline-web-lpuqqlugnq-ew.a.run.app';uploaded=load(RUN/'image-upload-summary.json')
    def one(im):
        r=b.requests.get(site+im['path'],timeout=(10,45));r.raise_for_status()
        assert r.headers.get('Content-Type','').startswith('image/jpeg') and len(r.content)==im['bytes']<=100000 and core.sha(r.content)==im['sha256']
        return dict(key=im['key'],url=r.url,status=r.status_code,bytes=len(r.content),sha256=core.sha(r.content),verified=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(one,uploaded))
    save(RUN/'public-verification.json',dict(at=core.now(),images=rows));print('All',len(rows),'live image byte streams verified',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['audit','research','backup-verify','selection','upload','held','verify','public-verify']);args=p.parse_args()
    {'audit':audit,'research':research,'backup-verify':backup_verify,'selection':selection,'upload':upload,'held':held_report,'verify':verify,'public-verify':public_verify}[args.phase]()
