#!/usr/bin/env python3
"""Verify the exact Italy follow-up and regenerate its current review artifacts."""
import base64
import collections
import importlib.util
import json
from pathlib import Path
from bs4 import BeautifulSoup
import psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('review',ROOT/'ops/italy-commercial-use-review.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
c=r.c;OUT=r.OUT

def main():
    decisions=c.load(OUT/'image-decisions.json')
    keep=[x for x in decisions if x['commercial_review_decision']=='retain_with_licence_conditions']
    held=[x for x in decisions if x['commercial_review_decision']=='hold']
    withdrawal=c.load(c.RUN/(r.LABEL+'-rights-hold')/'verification.json')
    assert len(keep)==10 and len(held)==49 and len(withdrawal['storage'])==49
    assert all(x['object_absent'] and x['public_http_status']==404 for x in withdrawal['storage'])
    verification={'checked_at':c.core.now(),'retained':10,'new_holds':49,'errors':[],'rounds':[], 'metadata_preimages':{},'private_derivatives':[]}
    verified={}
    for label in sorted({x['round'] for x in keep}):
        path=sorted((c.RUN/label).glob('verification-*.json'))[-1];v=c.load(path)
        assert not v['errors'] and v['served_checks_cover_every_completed_image']
        assert v['checked_at']>c.load(OUT/'prepared.json')['checked_at']
        assert all(x['asset_sha256_matches'] and x['preview_exact_media_rights_credit_and_status'] for x in v['public_checks'])
        verified.update(v['completed_image_sha256s'])
        verification['rounds'].append(str(path.relative_to(c.RUN)))
    assert verified=={x['artwork_id']:x['sha256'] for x in keep}
    for target,dsn in [('local','postgres://127.0.0.1/artline'),('cloud',c.core.cloud_dsn())]:
        ids=[x['target_ids'][target] for x in decisions]
        with psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
            rows=db.execute('''SELECT a.id::text,a.primary_media_id::text,
                to_jsonb(a)-ARRAY['primary_media_id','revision','updated_at','updated_by'] metadata,
                coalesce((SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id,aa.attribution_role)
                FROM artwork_artists aa WHERE aa.artwork_id=a.id),'[]'::jsonb) creators
                FROM artworks a WHERE a.id=ANY(%s::uuid[])''',(ids,)).fetchall()
        lookup={x['id']:x for x in rows};assert len(lookup)==59
        for x in decisions:
            previous=next(z for z in c.load(c.RUN/x['round']/(target+'-before.json')) if z['local_id']==x['artwork_id'])
            now=lookup[x['target_ids'][target]]
            assert now['metadata']==previous['metadata'] and now['creators']==previous['creators']
            assert now['metadata']['status']=='review'
            assert now['primary_media_id']==(None if x in held else x['media_id'])
        verification['metadata_preimages'][target]={'artworks':59,'matched':True,'status':'review','read_only':True}
    for x in held:
        private=c.BACKUP/(r.LABEL+'-rights-hold')/'derivatives'/Path(x['path']).name
        assert private.exists() and c.core.sha(private.read_bytes())==x['sha256']
        assert not (ROOT/'apps/web/public'/x['path'].lstrip('/')).exists()
        verification['private_derivatives'].append({'artwork_id':x['artwork_id'],'path':str(private),'sha256':x['sha256']})
    c.save(OUT/'verification.json',verification)

    spec=importlib.util.spec_from_file_location('report',ROOT/'ops/italy-image-report.py')
    report=importlib.util.module_from_spec(spec);spec.loader.exec_module(report)
    report.report(commercial_follow_up=True)
    ledger=c.load(c.RUN/'image-credit-ledger.json')
    assert {x['sha256'] for x in ledger}=={x['sha256'] for x in keep}

    gallery=BeautifulSoup((r.PRIVATE/'before/GALLERY.html').read_text(),'html.parser')
    allowed={x['sha256']:x for x in keep};found=set()
    for article in gallery.find_all('article'):
        img=article.find('img');data=base64.b64decode(img['src'].split(',',1)[1]);sha=c.core.sha(data)
        if sha not in allowed:article.decompose();continue
        entry=allowed[sha];found.add(sha)
        assert entry['attribution_text'] in article.get_text()
        assert article.find('a',href=entry['policy_url'])
    assert found==set(allowed)
    gallery.h1.string='10 retained images'
    gallery.select_one('.intro').string='Five privately owned Poldi Pezzoli works and five Italian artists’ works abroad. Updated after review for public or potentially commercial app use. Catalogue records remain in review.'
    note=gallery.new_tag('p',attrs={'class':'intro'})
    note.string='49 images from public collections are held pending commercial-use clearance and are excluded from this gallery. Credits and licence conditions apply to each retained image.'
    gallery.header.append(note)
    (c.RUN/'GALLERY.html').write_text(str(gallery))
    gallery_check={'checked_at':c.core.now(),'images':10,'exact_embedded_sha256s':sorted(found),
        'held_images_embedded':0,'attribution_and_licence_links_verified':True,
        'sha256':c.core.sha((c.RUN/'GALLERY.html').read_bytes()),'browser_render_check':False}
    c.save(OUT/'gallery-check.json',gallery_check)
    for name in ['gallery-verification.json','gallery-content-check.json']:
        (c.RUN/name).write_text(json.dumps(gallery_check,indent=2)+'\n')

    cohort=c.load(OUT/'italian-holdings-recheck.json')['targets']['local']
    names={x['slug']:x['name'] for x in c.load(c.RUN/'local-audit.json')['institutions']}
    lines=['# Remaining Italian holding image gaps','',
        'Updated after the public/commercial-use review. Both databases agree on the original eligible, selected cohort. Existing unrelated images are not re-cleared by this count. [Read-only recheck](commercial-use-review-20260917/italian-holdings-recheck.json).','',
        '| Collection | Missing images | Paintings | Drawings | Prints | Frescoes | Added this run |','|---|---:|---:|---:|---:|---:|---:|']
    for slug,g in sorted(cohort['institutions'].items(),key=lambda kv:(-kv[1].get('missing_images',0),kv[0])):
        if not g.get('missing_images'):continue
        values=[g.get(k,0) for k in ['missing_images','painting_gaps','drawing_gaps','print_gaps','fresco_gaps','added_since_start']]
        lines.append('| '+names.get(slug,slug).replace('|','\\|')+' | '+' | '.join(map(str,values))+' |')
    lines+=['','The cohort has 2,437 remaining gaps: 678 paintings, 1,736 drawings, 22 prints and one fresco. Five newly retained Italian-holding images are at Poldi Pezzoli.','',
        'These counts support selective evidence review. Drawings require exact inventory and recto/verso identity; a study is a separate work. Creation eligibility, photographic copyright and permitted commercial reuse require separate evidence.','']
    (c.RUN/'REMAINING-GAPS.md').write_text('\n'.join(lines))

    findings=(r.PRIVATE/'before/FINDINGS.md').read_text()
    findings=findings.replace('The retained set contains **59 uploaded images**, linked to the same existing artworks in both databases: **54 Italian holdings and five Italian artists\' works abroad**.',
        'After the user confirmed public or potentially commercial app use, **10 uploaded images remain attached** in both databases: **five privately owned Poldi Pezzoli works and five Italian artists\' works abroad**. An additional **49 images were withdrawn pending commercial cultural-property reuse clearance**. The original four-hour completion reported 59; its timestamp and evidence are preserved in the [commercial follow-up](commercial-use-review-20260917/README.md).')
    findings=findings.replace('Read-only queries against those original IDs, in pages of 500, found the same results in local and production databases:',
        'Read-only queries against those original IDs, in pages of 500, found the same results in local and production databases after the commercial-use correction:')
    findings=findings.replace('| 84 | 138 |','| 84 | 89 |').replace('| 683 | 629 |','| 683 | 678 |')
    findings=findings.replace('[Read-only cohort recheck](italian-holdings-scope-recheck-20260917T0032.json)',
        '[Current read-only cohort recheck](commercial-use-review-20260917/italian-holdings-recheck.json)')
    start=findings.index('| Holding collection |');end=findings.index('\n\nThe Academy of Brera',start)
    findings=findings[:start]+'| Holding collection | Images retained |\n|---|---:|\n| Museo Poldi Pezzoli | 5 |\n| Academy of Fine Arts Vienna, Italian artists | 3 |\n| Metropolitan Museum, Italian artists | 2 |'+findings[end:]
    findings=findings.replace('The remaining 99 artworks stay held.',
        'Those 99 artworks stayed held at four-hour completion. The subsequent commercial-use review added 49 holds, so 148 artworks now have withdrawn campaign images (149 old media files, including the replaced Titian file).')
    findings=findings.replace('The [withdrawal recheck](withdrawn-media-recheck-20260917T0035.json) confirms',
        'The [original withdrawal recheck](withdrawn-media-recheck-20260917T0035.json) confirms')
    findings=findings.replace('Original evidence and private backups remain available.',
        'The [commercial withdrawal verification](commercial-use-20260917-rights-hold/verification.json) separately covers the added 49 holds. Original evidence and private backups remain available.')
    findings=findings.replace('before attachment. Segantini',
        'before its initial attachment; that image is now held for commercial reuse clearance. Segantini')
    findings=findings.replace('Institution-specific permission, a demonstrable prior release or a suitable independently licensed photograph must be established before selecting image bytes.',
        'Establish suitable photographic rights and any required cultural-property commercial permission before selecting image bytes. An independent photographer\'s licence alone does not settle a public collection\'s commercial concession requirements.')
    findings=findings.replace('The [source validation replay](source-proof-final-replay.json) checks all 59 retained source packages.',
        'The historical [source validation replay](source-proof-final-replay.json) checked all 59 source packages present at four-hour completion; it does not clear the subsequently held images for commercial use.')
    findings=findings.replace('The [archive verification](archives-recheck-20260917T0037.json) verifies all 59 original downloaded files,',
        'The historical [archive verification](archives-recheck-20260917T0037.json) verified those 59 original downloaded files,')
    findings=findings.replace('[Final delivery checks](all-images-final-verification.json)',
        '[Current delivery and preservation checks](commercial-use-review-20260917/verification.json)')
    (c.RUN/'FINDINGS.md').write_text(findings)
    c.save(OUT/'source-access-limitations.json',{'checked_at':c.core.now(),
        'met_policy_capture':'Direct capture of https://www.metmuseum.org/hubs/open-access failed the status/TLS/redirect guard. No alternate access attempt or successful raw capture is claimed. Retained Met images use the preserved object-specific native CC0 evidence reviewed in the original campaign.',
        'normattiva':'The linked current Code page returned an error in web browsing. Ministry guidance and the signed 2024 decree are preserved; no successful consolidated Code capture is claimed.'})
    c.save(OUT/'completion.json',{'checked_at':c.core.now(),'reviewed':59,'retained':10,'new_holds':49,
        'italian_holding_attachments':5,'italian_artists_abroad':5,'publication_status':'review',
        'original_campaign_duration_seconds':14411,'verification':'verification.json',
        'gallery':'../GALLERY.html','database_metadata_and_creator_changes':0})
    print('Commercial follow-up complete: 10 retained, 49 held; all 59 metadata preimages preserved.',flush=True)

if __name__=='__main__':main()
