#!/usr/bin/env python3
"""Verified native Wien reproductions and independently licensed Commons photos."""
import argparse,collections,importlib.util,json,re,time
from pathlib import Path
from types import SimpleNamespace
s=importlib.util.spec_from_file_location('photo',Path(__file__).with_name('research-popular-painting-photos.py'));photo=importlib.util.module_from_spec(s);s.loader.exec_module(photo)
s=importlib.util.spec_from_file_location('facts',Path(__file__).with_name('prepare-austrian-metadata.py'));facts=importlib.util.module_from_spec(s);s.loader.exec_module(facts)
m=photo.m;core=m.core
core.PROVIDERS.update({'austria-wien':'Wien Museum','austria-commons':'Wikimedia Commons'})
core.HOSTS.add('sammlung.wienmuseum.at')
original_attach=m.original_attach

def verify(im):
    if im['provider']=='austria-commons':
        m.entity_match(im,im['raw']['wikidata'],require_primary_image=False);photo.exact_photo(im,im['raw']['commons'],im['raw']['structured_data'])
        m.rights_and_identity(im,im['raw']['wikidata'],im['raw']['commons'],im['raw']['structured_data'],im.get('rendered_licence_evidence'))
        if m.origin.verify(im,im['raw']['commons'])!='independent_photographer':raise ValueError('Austrian museum-origin reproduction needs separate exact native rights review')
    elif im['provider']=='austria-wien':
        w,n=im['raw']['work'],im['raw']['official'];d,acc=facts.verify(w,n)
        matches=[i for i in n['images'] if i['preview_url']==im['source_image_url'] and i['license']]
        if len(matches)!=1:raise ValueError('Exact museum media identity or licence differs')
        source=matches[0];uri,label,status=source['license']
        if (uri,label,status)!=(im['policy_url'],im['license_label'],im['rights_status']):raise ValueError('Exact museum image rights differ')
        if source['credit'] not in im['attribution_text'] or source['caption']!=im['creator_credit']:raise ValueError('Required museum/photographer credit differs')
        if im['page']!=n['url'] or im['qid']!=w['qid'] or im['institution_qid']!='Q505873':raise ValueError('Source artwork identity differs')
        if im['creation_year_start']!=d['first'] or im['creation_year_end']!=d['last'] or im['accession_number']!=acc:raise ValueError('Catalogue dates or inventory require reconciliation')
    else:raise ValueError('Unsupported selected museum provider')

def attach(db,im,target):
    verify(im)
    with db.transaction():
        rows=db.execute("SELECT a.id::text,a.slug,a.title,a.work_type,a.creation_year_start,a.creation_year_end,a.current_institution_id::text FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata' WHERE e.external_id=%s",(im['qid'],)).fetchall()
        if len(rows)!=1 or rows[0]['id']!=im['target_ids'][target] or any(rows[0][k]!=im[k] for k in ('slug','title','work_type','creation_year_start','creation_year_end')):raise ValueError('Current catalogue artwork identity differs')
        if rows[0]['current_institution_id']!=im['institution_ids'][target]:raise ValueError('Current museum differs')
        out=original_attach(db,im,target)
        if out=='attached':
            db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
            db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,'Verified museum reproduction') ON CONFLICT DO NOTHING",(im['target_ids'][target],im['media_id']))
        return out
core.attach=attach

def candidates(run):
    path=run/'images-research/candidates.json'
    if path.exists():return json.loads(path.read_text())['candidates']
    plan=json.loads((run/'metadata-plan.json').read_text());records=json.loads((run/'metadata-input.json').read_text())['records'];byq={x['qid']:x for x in records};local=plan['targets']['local'];remote={x['qid']:x for x in plan['targets']['cloud']['records']};out=[];held=[]
    with facts.a.connect('local',True) as db:
        popular={x['artist_id'] for x in db.execute("SELECT artist_id::text FROM artist_discovery_selection WHERE is_popular=true").fetchall()}
    for state in local['records']:
        w=byq[state['qid']];q=w['qid'];other=remote.get(q)
        if not other or not w['date']['eligible'] or (state['existing'] and state['existing']['primary_media_id']) or (other['existing'] and other['existing']['primary_media_id']):continue
        if state['action']=='existing':
            old=state['existing'];d={'first':old['creation_year_start'],'last':old['creation_year_end'],'display':old['date_display'],'precision':old['date_precision']}
            if d['first'] is None or d['last'] is None or not 1000<=d['first']<=d['last']<=1970:continue
            title=old['title'];acc=old['accession_number']
        else:d=w['date'];title=w['title'];acc=w['accession']
        artist=local['artists'][state['artist_qid']];inst=local['institutions'][w['institution_qid']]
        c={'artwork_id':state['artwork_id'],'slug':state['slug'],'qid':q,'external_id':q,'scheme':'wikidata','title':title,'alternate_title':None,'accession_number':acc,'creation_year_start':d['first'],'creation_year_end':d['last'],'date_precision':d['precision'],'date_display':d['display'],'work_type':'painting','artist':artist['name'],'artist_slug':artist['slug'],'artist_qid':artist['qid'],'creators':[{'qid':w['creator_qid'],'name':artist['name'],'birth':w['creator_birth'],'death':w['creator_death']}],'popular':artist['id'] in popular,'institution_qid':w['institution_qid'],'institution_slug':inst['slug'],'museum':inst['name'],'country_code':'AT','website_url':inst['website_url'],'native_identifiers':[],'target_ids':{'local':state['artwork_id'],'cloud':other['artwork_id']},'institution_ids':{'local':state['institution_id'],'cloud':other['institution_id']}}
        if w.get('primary_wien') and any(i['license'] for i in w['primary_wien']['images']):
            n=w['primary_wien'];source=next(i for i in n['images'] if i['license']);uri,label,status=source['license'];c['provider']='austria-wien'
            small={k:w[k] for k in ('qid','creator_names','creator_birth','creator_death','accession')};c['selected']=dict(c,page=n['url'],source_image_url=source['preview_url'],policy_url=uri,rights_status=status,license_label=label,checked_at=core.now(),raw={'work':small,'official':n},creator_credit=source['caption'],attribution_text=source['credit']+' Licence: '+uri+' Full-frame proportional resize and JPEG compression.',source_name='Wien Museum',source_record_url=n['url'],image_url=source['preview_url'],image_license=label,image_license_url=uri,rights_statement=source['caption'],creator=artist['name'],creation_date=d['display'],source_object_id=n['object_id'],rights_verified_at=core.now())
            try:verify(c['selected'])
            except ValueError as exc:held.append({'qid':q,'reason':str(exc)});continue
        else:c['provider']='austria-commons'
        out.append(c)
    core.save_new(path,{'at':core.now(),'candidates':out,'held':held});print('Selected image gaps',len(out),dict(collections.Counter(c['provider'] for c in out)),flush=True);return out

def research_commons(c,entity,fetch,run):
    # Preserve every existing source rejection, then additionally require an
    # independently identified photographer for this museum research pass.
    original=photo.candidate_image
    def checked(*args):
        im=original(*args)
        if m.origin.verify(im,im['raw']['commons'])!='independent_photographer':raise ValueError('Native Austrian image origin needs exact museum media licence review')
        im['provider']='austria-commons';return im
    photo.candidate_image=checked
    try:return photo.research(c,entity,fetch,run,require_primary_image=False)
    finally:photo.candidate_image=original

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--provider',choices=['austria-wien','austria-commons'],required=True);p.add_argument('--limit',type=int,default=1000);a=p.parse_args();rows=candidates(a.run);run=a.run/'images-research';done=core.latest_events(run);rows=[c for c in rows if c['provider']==a.provider and c['artwork_id'] not in done];rows.sort(key=lambda c:(not c['popular'],c['museum'],c['artist'],c['title']));fetch=core.Fetcher(run/'metadata')
    for c in rows[:a.limit]:
        try:
            path=run/'selected'/c['provider']/(c['artwork_id']+'.json')
            if not path.exists():
                if c['provider']=='austria-wien':im=c['selected']
                else:
                    e=json.loads((a.run/'wikimedia/entities'/(c['qid']+'.json')).read_text())['entity'];im=research_commons(c,e,fetch,run)
                verify(im);core.save_new(path,im)
            core.worker(c['provider'],[c],SimpleNamespace(run=run,prepare_only=True),None)
        except (ValueError,KeyError,AssertionError) as exc:core.event(run,{'provider':c['provider'],'artwork_id':c['artwork_id'],'qid':c['qid'],'outcome':'manual_review','reason':str(exc)})
        except Exception as exc:
            core.event(run,{'provider':c['provider'],'artwork_id':c['artwork_id'],'qid':c['qid'],'outcome':'temporary_error','reason':type(exc).__name__+': '+str(exc)[:200]});print(core.now(),'Source paused',type(exc).__name__,flush=True);break
        counts=collections.Counter(e['outcome'] for e in core.latest_events(run).values());print(core.now(),'Austrian selected image results',dict(counts),flush=True)
if __name__=='__main__':main()
