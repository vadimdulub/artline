#!/usr/bin/env python3
"""Two public-domain Barnes paintings by Horace Pippin, local review only."""
import argparse
import importlib.util
from pathlib import Path
import sys
sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('core',Path(__file__).with_name('add-islamic-world-images-20260925.py'))
core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
PARENT=core.ROOT/'docs/research/period-images-20260926'
core.CAMPAIGN='pippin-images-20260926';core.SOURCE_LABEL='Horace Pippin: earlier civil-rights context'
core.RUN=core.ROOT/'docs/research'/core.CAMPAIGN
core.BACKUP=core.DATA/'backups'/core.CAMPAIGN;core.ORIGINALS=core.DATA/'source-images'/core.CAMPAIGN
core.COUNTRIES={}
core.PROVIDERS={'barnes':{'name':'The Barnes Foundation','api':'https://collection.barnesfoundation.org/api/search',
    'policy':'https://www.barnesfoundation.org/collection/open-access-and-copyright','source_type':'collection_page'}}


def plan():
    for name in ['barnes-selected.json','barnes-selected.json.receipt.json','barnes-policy.html','barnes-policy.html.receipt.json']:
        core.save(core.RUN/'captures'/name,(PARENT/'captures'/name).read_bytes())
    # Public UI mapping: rights code 8 = Public Domain, not exclusive code 11.
    bundle=Path('/tmp/artline-barnes-bundle.js').read_bytes()
    assert b'8:{copy:"Public Domain",link:"https://creativecommons.org/publicdomain/mark/1.0/",type:"large"}' in bundle
    core.save(core.RUN/'captures/barnes-ui.js',bundle)
    policy=core.load('captures/barnes-policy.html.receipt.json')
    assert core.sha((core.RUN/'captures/barnes-policy.html').read_bytes())==policy['sha256']
    receipt=core.load('captures/barnes-selected.json.receipt.json')
    assert core.sha((core.RUN/'captures/barnes-selected.json').read_bytes())==receipt['sha256']
    hits=core.load('captures/barnes-selected.json')['hits']['hits']; assert len(hits)==2
    institution={'id':core.uid('institution/barnes'),'slug':'barnes-foundation','name':'The Barnes Foundation',
        'normalized_name':core.norm('The Barnes Foundation'),'kind':'foundation','status':'review',
        'website_url':'https://www.barnesfoundation.org/'}
    with core.connect() as db:
        assert not db.execute("SELECT 1 FROM institutions WHERE name ILIKE '%Barnes%'").fetchone()
        artist=db.execute("SELECT to_jsonb(a) record FROM artists a WHERE slug='horace-pippin-nga-25'").fetchone()
        assert artist and artist['record']['death_year']==1946
        records=[]
        for hit in hits:
            o=hit['_source'];oid=o['id'];assert oid in (5154,5156)
            assert o['people']=='Horace Pippin' and o['objRightsTypeId']=='8' and not o['copyright']
            assert o['displayDate']==('c. 1940' if oid==5154 else '1940')
            key='barnes-'+str(oid);url='https://collection.barnesfoundation.org/objects/'+str(oid)+'/'+o['title'].replace(' ','-')+'/'
            reason=('African American family life before the civil-rights era.' if oid==5154 else 'African American spirituality and the Gospel encounter across community boundaries, as discussed by the museum.')
            c={'key':key,'provider':'barnes','object_id':str(oid),'accession':o['invno'],'preset':'civil-rights','title':o['title'],
                'lo':1940,'hi':1940,'date_display':o['displayDate'],'precision':'circa' if oid==5154 else 'exact','type':'painting',
                'country':None,'culture':None,'place_display':None,'maker':None,'artist_id':artist['record']['id'],
                'url':url,'image_url':'https://d2r83x5xt28klo.cloudfront.net/'+str(oid)+'_'+o['imageSecret']+'_b.jpg',
                'medium':o['medium'],'dimensions':o['dimensions'],'credit':'Courtesy of the Barnes Foundation, Merion and Philadelphia, Pennsylvania; '+o['invno'],
                'reason':reason,'object':o,'capture':receipt,'institution_id':institution['id'],'artwork_id':core.uid(key),'slug':'period-'+key,
                'rights_status':'public_domain','license_label':'Public domain','license_url':'https://creativecommons.org/publicdomain/mark/1.0/',
                'rights_basis':'Barnes object rights code 8 is explicitly Public Domain in its public UI. Museum policy permits commercial and noncommercial reuse. No exclusive-license rights code.',
                'scope_note':'Original public display date retained. Supper Time uses c. 1940 as a circa date, not an exact claim; conflicting API beginDate=1935 with no endDate remains in source evidence. No invented uncertainty interval or manufacture location. Earlier context, not a claim that Pippin participated in the 1954–1968 movement.'}
            assert not core.duplicate(db,c)
            # Also detect catalogue records imported with a title but no institution.
            assert not db.execute('SELECT a.id FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=%s AND a.normalized_title=%s',(artist['record']['id'],core.norm(o['title']))).fetchone()
            records.append(c)
    core.save(core.RUN/'plan.json',{'records':records,'artist_preimages':[artist],'institutions_to_create':[institution],
        'country_preimages':[],'policies':{'barnes':policy},'selection_bound':'Two exact selected objects from the official Barnes API; image rights mapping and source metadata retained. No museum highlights or on-view assertions.'})
    core.save(core.RUN/'plan-pin.json',{'sha256':core.sha((core.RUN/'plan.json').read_bytes())})
    print('Pinned two Pippin paintings.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['plan','prepare','backup','apply','verify']);phase=p.parse_args().phase
    (globals().get(phase) or getattr(core,phase))()
