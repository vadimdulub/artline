#!/usr/bin/env python3
"""Build a reviewable campaign ledger from preserved evidence and verification."""
import argparse
import collections
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('campaign', ROOT / 'ops/italy-image-campaign.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def report(final=False, commercial_follow_up=False):
    campaign = c.load(c.RUN / 'campaign.json')
    start = datetime.fromisoformat(campaign['started_at'].replace('Z','+00:00'))
    minimum = datetime.fromisoformat(campaign['minimum_finish_at'].replace('Z','+00:00'))
    now = datetime.now(timezone.utc)
    follow_up = c.RUN / 'commercial-use-review-20260917'
    original_completion = None
    if commercial_follow_up:
        original_completion = c.load(follow_up / 'four-hour-completion.json')
        c.load(c.RUN / 'commercial-use-20260917-rights-hold' / 'verification.json')
        final = True
    elif (follow_up / 'prepared.json').exists():
        raise ValueError('Use --commercial-follow-up to preserve the original four-hour completion time')
    completed, all_candidates, latest_overall, visual_holds, rounds = {}, {}, {}, {}, []
    withdrawn_artworks = set()
    verified_by_round, fully_served_by_round, errors = {}, {}, []
    for run in sorted(c.RUN.glob('round-*')):
        if not (run / 'candidates.json').exists():
            continue
        candidates = c.load(run / 'candidates.json')['candidates']
        all_candidates.update({r['artwork_id']:r for r in candidates})
        latest = c.core.latest_events(run)
        for ident, event in latest.items():
            if event.get('outcome') == 'withdrawn_for_source_rights_review':
                withdrawn_artworks.add(ident)
            if event.get('at','') >= latest_overall.get(ident,{}).get('at',''):
                latest_overall[ident] = dict(event, round=run.name)
        if (run / 'visual-review.json').exists():
            for review in c.load(run / 'visual-review.json')['images']:
                if review['outcome']=='held':
                    visual_holds[review['artwork_id']] = dict(review, round=run.name)
        for p in (run / 'images').glob('*/*.json'):
            im = c.load(p)
            e = latest.get(im['artwork_id'], {})
            if e.get('outcome') != 'complete' or e.get('local') != 'attached' or e.get('cloud') != 'attached':
                continue
            completed[im['artwork_id']] = dict(im, receipt=str(p.relative_to(c.RUN)), round=run.name)
        checks = sorted(run.glob('verification-*.json'))
        verification = c.load(checks[-1]) if checks else None
        if verification:
            errors += [dict(e, round=run.name) for e in verification['errors']]
            if not verification['errors']:
                verified_by_round[run.name] = verification.get('completed_image_sha256s', {})
                if verification.get('served_checks_cover_every_completed_image'):
                    fully_served_by_round[run.name] = {
                        row['artwork_id'] for row in verification['public_checks']
                        if row.get('asset_sha256_matches') and row.get('preview_exact_media_rights_credit_and_status')}
        rounds.append({'round':run.name,'selected':len(candidates),
            'latest_outcomes':dict(collections.Counter(e['outcome'] for e in latest.values())),
            'verification':str(checks[-1].relative_to(c.RUN)) if checks else None})
    verified_completed = {ident for ident,im in completed.items()
                          if verified_by_round.get(im['round'],{}).get(ident)==im['sha256']}
    fully_served = {ident for ident,im in completed.items()
                    if ident in verified_completed and ident in fully_served_by_round.get(im['round'],set())}
    holds = [{'artwork_id':ident,'title':all_candidates[ident]['title'],
        'institution':all_candidates[ident]['institution_name'], **event,
        'visual_hold':visual_holds.get(ident)} for ident,event in latest_overall.items()
        if ident not in completed and event.get('outcome') in ('manual_review','failed','prepared','withdrawn_for_source_rights_review')]
    if final and (now < minimum or errors or set(completed)-verified_completed or set(completed)-fully_served):
        raise ValueError('Minimum duration and complete attachment verification required before final report')
    ledger = []
    for im in sorted(completed.values(), key=lambda r:(r['institution_name'],r['artist'],r['title'])):
        entry = {k:im.get(k) for k in ('artwork_id','title','artist','institution_name','institution_slug',
            'scope_basis','target_ids','media_id','path','sha256','bytes','width','height','rights_status',
            'license_label','policy_url','creator_credit','attribution_text','source_image_url','page','round','receipt')}
        entry['attribution_text'] = c.attachment_attribution(im)
        entry['creator_credit'] = im.get('creator_credit', im['artist'])
        ledger.append(entry)
    by_institution = dict(collections.Counter(r['institution_name'] for r in ledger))
    summary = {'reported_at':now.isoformat(), 'status':'complete' if final else 'ongoing',
        'started_at':campaign['started_at'], 'minimum_finish_at':campaign['minimum_finish_at'],
        'elapsed_seconds':int((now-start).total_seconds()), 'minimum_duration_satisfied':now>=minimum,
        'attached_in_both':len(completed), 'verified_in_both_and_storage':len(verified_completed),
        'verified_served_assets_and_exact_preview_credits':len(fully_served),
        'unique_selected_artworks':len(all_candidates), 'by_institution':by_institution,
        'italian_museum_attachments':sum(r['scope_basis']=='Italian museum identity' for r in ledger),
        'italian_artist_attachments_abroad':sum(r['scope_basis']!='Italian museum identity' for r in ledger),
        'derivative_bytes_total':sum(r['bytes'] for r in ledger),
        'max_derivative_bytes':max([r['bytes'] for r in ledger] or [0]),
        'verification_errors':errors,'rounds':rounds,
        'withdrawn_for_source_rights_review':len(withdrawn_artworks-set(completed)),
        'publication':'Artwork review status, source metadata and creator links preserved; no new artworks imported',
        'backups':'backups.json', 'image_credit_ledger':'image-credit-ledger.json', 'held_artworks':'held-artworks.json'}
    if original_completion:
        summary.update({'elapsed_seconds':original_completion['elapsed_seconds'],
            'campaign_completed_at':original_completion['reported_at'],
            'commercial_follow_up_at':now.isoformat(),
            'intended_use':'Public or potentially commercial app',
            'commercial_review':'commercial-use-review-20260917/README.md',
            'original_four_hour_completion':'commercial-use-review-20260917/four-hour-completion.json'})
    stamp=now.strftime('%Y%m%dT%H%M%SZ')
    c.save(c.RUN / 'checkpoints' / (stamp+'.json'), summary)
    for name, value in [('status.json',summary),('image-credit-ledger.json',ledger),('held-artworks.json',holds)]:
        (c.RUN/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    lines=['# Italy image research and uploads', '',
        f"Status: **{summary['status']}**. Updated {now.strftime('%Y-%m-%d %H:%M:%S UTC')}.", '',
        f"**{len(completed)} images attached to existing artworks in both local and production databases; {len(verified_completed)} verified against database preimages, image files and uploaded object checksums.**", '',
        '[Open the local image review gallery](GALLERY.html). It embeds the exact verified images with their source links, licences and credits.', '',
        (f"The four-hour campaign completed at {original_completion['reported_at']} after {original_completion['elapsed_seconds']} seconds. The counts here include the subsequent public/commercial-use review; that follow-up does not extend the recorded campaign duration."
         if original_completion else f"The run began at {campaign['started_at']} and completed at {now.strftime('%Y-%m-%dT%H:%M:%SZ')}, after {summary['elapsed_seconds']//60} minutes. The requested four-hour minimum was satisfied."
         if final else f"The run began at {campaign['started_at']} and must continue until at least {campaign['minimum_finish_at']}. Elapsed time at this checkpoint: {summary['elapsed_seconds']//60} minutes."), '',
        f"Scope: {summary['italian_museum_attachments']} attachments to Italian museum holdings and {summary['italian_artist_attachments_abroad']} to Italian artists' works held abroad. Artwork creation must be eligible through 1970 and existing selection evidence must be present.", '',
        '| Holding institution | Images attached |','|---|---:|']
    lines += [f'| {name} | {count} |' for name,count in sorted(by_institution.items())]
    lines += ['', 'Each attached file has an exact physical-object match, saved file-level licence and original-source evidence, visual review, photographer attribution where required, and a full-frame JPEG of at most 100,000 bytes. Review status, artwork metadata and creator links remain unchanged.', '',
        f"The verification records check local image bytes, GCS checksums, both database media/rights links and complete artwork/creator preimages. {len(fully_served)} attached images also have individual served-byte checks and exact authenticated preview checks for image URL, title, licence, credit and status. Preview access is not publication.", '',
        'Evidence: [image credits and source links](image-credit-ledger.json), [held records](held-artworks.json), [verification and round status](status.json), [backup receipts](backups.json). Original downloaded image bytes and database backups are stored in the dedicated Artline Library folders recorded in the receipts.', '',
        'Read the [research findings and remaining gaps](FINDINGS.md) for source-policy distinctions, object-identity conflicts, drawing priorities and verification limits.', '',
        'Cropped details, obstructing labels, conspicuous glare, conflicting identity or attribution, restricted source terms and missing licence evidence remain held. Catalogue PDF images are research evidence and are not cleared for upload.', '',
        'The in-app browser connection was unavailable. Source API captures, original catalogue sheets, local image inspection and served-asset/preview checks are recorded instead. No browser verification is claimed.', '']
    if summary['withdrawn_for_source_rights_review']:
        lines += [f"{summary['withdrawn_for_source_rights_review']} artworks have earlier image attachments held for source-policy conflicts or unresolved permission for the confirmed public/commercial use. Artwork records and research evidence were preserved, image rights returned to unresolved, and this campaign's public copies removed. These images are excluded from the totals above.", '']
        for policy in sorted((c.RUN/'institution-rights-holds').glob('*.json')):
            name=policy.stem
            verification=c.RUN/(name+'-rights-hold')/'verification.json'
            lines += [f"- [{name.title()} source policy](institution-rights-holds/{policy.name})" + (f" · [withdrawal verification]({name}-rights-hold/verification.json)" if verification.exists() else ' · withdrawal verification pending')]
        lines += ['']
    if original_completion:
        lines += ['The user confirmed **public or potentially commercial app** use. The follow-up retained 10 of the previously reported 59 images and withdrew 49 pending cultural-property reuse clearance. Read the [commercial-use review and per-image decisions](commercial-use-review-20260917/README.md).', '']
    (c.RUN/'README.md').write_text('\n'.join(lines))
    print(json.dumps({k:summary[k] for k in ('status','elapsed_seconds','attached_in_both','verified_in_both_and_storage','italian_museum_attachments','verification_errors')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--final',action='store_true')
    p.add_argument('--commercial-follow-up',action='store_true')
    a=p.parse_args();report(a.final,a.commercial_follow_up)
