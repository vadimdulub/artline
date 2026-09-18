#!/usr/bin/env python3
"""Capture primary evidence for already-selected Nationalmuseum objects only."""
import argparse, collections, importlib.util, json, re
from pathlib import Path
from urllib.parse import urljoin
s=importlib.util.spec_from_file_location('primary',Path(__file__).with_name('research-german-primary-objects.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
x=p.x

def capture(code,number):
    delivery=x.BASE/code/f'round-{number:02d}'/'delivery';dest=delivery/'nationalmuseum-primary-review.json'
    if dest.exists():return
    records=[]
    for ready in sorted((delivery/'ready').glob('*.json')):
        prepared=json.loads(ready.read_text());r=prepared['record'];ids=x.r.values(r['entity'],'P2539')
        if len(ids)!=1 or not re.fullmatch(r'\d+',str(ids[0])):continue
        out=delivery/'nationalmuseum-primary'/(r['qid']+'.json')
        if out.exists():records.append(json.loads(out.read_text()));continue
        e={'qid':r['qid'],'at':x.r.core.now(),'museum':'nationalmuseum','review':'primary_review_required','ready_sha256':x.r.core.sha(ready.read_bytes())}
        try:
            url='https://collection.nationalmuseum.se/en/collection/item/'+str(ids[0])+'/'
            soup,receipt=p.page(url,p.ROOT/'nationalmuseum',r['qid'])
            item=json.loads(soup.find('script',id='__NEXT_DATA__').string)['props']['pageProps']['data']['item']
            makers=item.get('ObjPersonRef',{}).get('Items',[])
            artist=[m for m in makers if m.get('RoleVoc',{}).get('LabelTxt')=='Artist']
            clean=lambda name:re.sub(r'\s*\([^)]*\)\s*$','',name or '')
            names={x.r.norm(n) for n in x.r.labels(r['creator_entity'])}
            creator_match=len(makers)==len(artist)==1 and x.r.norm(clean(artist[0].get('LinkLabelTxt'))) in names
            accession=item.get('ObjInventoryNumberTxt')
            accession_match=bool(r['accession']) and x.r.norm(accession or '')==x.r.norm(r['accession'])
            reciprocal=bool(soup.find('a',href=re.compile(r'(?:wikidata.org/(?:entity/|wiki/))'+re.escape(r['qid'])+r'$')))
            image=None
            for media in item.get('ObjMultimediaRef',{}).get('Items',[]):
                for rendition in media.get('Multimedia',[]):
                    if rendition.get('full')==item.get('DefaultImage'):
                        image={'url':urljoin(urljoin(url,'/'),rendition['full']),'rights':media.get('MulRightsTxt'),'credit':media.get('MulPhotocreditTxt'),'media_id':media.get('ReferencedId'),'metadata':media}
            rights=bool(image and image['rights']=='Public Domain, https://creativecommons.org/publicdomain/mark/1.0/')
            date=item.get('ObjDateMainTxt');years=[int(y) for y in re.findall(r'(?<!\d)(?:1\d{3}|20\d{2})(?!\d)',date or '')]
            compatible=bool(years and r['date']['first'] is not None and max(years)>=r['date']['first'] and min(years)<=r['date']['last'] and max(years)<=1970)
            obj={'title':item.get('ObjTitleMainTxt'),'creator':item.get('ObjPersonRefTxt'),'makers':makers,'accession':accession,'date':date,'date_group':item.get('ObjDateGroupTxt'),'image':image,'fields':item,'image_url':image['url'] if image else None,'rights':image['rights'] if image else None,'credit':image['credit'] if image else None}
            e.update(receipt=receipt,object=obj,creator_match=creator_match,accession_match=accession_match,reciprocal_object_identity=reciprocal,date_match=compatible,image_rights_corroborated=rights,eligible_for_selected_image=bool(creator_match and accession_match and reciprocal and compatible and rights and not prepared['image']),rights_basis='Exact default museum reproduction has its own explicit Public Domain Mark and photographer credit. Other gallery image licences are not inherited.')
            if creator_match and accession_match and reciprocal:e['review']='primary_object_and_creator_corroborated'
        except Exception as error:e['reason']=str(error)[:350]
        x.save(out,e);records.append(e);print(code,number,r['qid'],e['review'],'image',e.get('eligible_for_selected_image',False),flush=True)
    x.save(dest,{'at':x.r.core.now(),'records':records,'counts':dict(collections.Counter(e['review'] for e in records))})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--country',required=True,choices=x.COUNTRIES);ap.add_argument('--round',required=True,type=int);a=ap.parse_args();assert 1<=a.round<=20;capture(a.country,a.round)
