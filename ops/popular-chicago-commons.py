"""Native Chicago identity with explicit CC0 reproduction evidence on Commons.

This narrowly handles Licensed-PD-Art files whose reproduction is CC0. It does
not infer image rights from artwork age, or accept an unlabelled museum image.
"""
import importlib.util,re
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('commons',Path(__file__).with_name('overnight-commons-images.py'))
common=importlib.util.module_from_spec(s);s.loader.exec_module(common);core=common.core
s=importlib.util.spec_from_file_location('native',Path(__file__).with_name('popular-chicago-verification.py'))
native=importlib.util.module_from_spec(s);s.loader.exec_module(native)
PROVIDER='popular-chicago-commons'
core.PROVIDERS[PROVIDER]='Art Institute of Chicago / Wikimedia Commons'
core.VERSION='popular-chicago-native-commons-cc0-v1'

def verify(im):
    raw=im['raw'];o=raw['museum_record'];facts=native.metadata(o,im['artist_evidence'],im['source_artist'])
    assert o.get('is_public_domain') is True and not o.get('copyright_notice'),'Museum artwork rights conflict'
    assert str(o['id'])==im['external_id'] and all(im[k]==facts[k] for k in ('title','work_type','accession_number','creation_year_start','creation_year_end'))
    page=raw['commons'];info=page['imageinfo'][0];meta=info['extmetadata']
    assert page['ns']==6 and info['mime']=='image/jpeg'
    wiki=page['revisions'][0]['slots']['main']['*']
    assert not re.search(r'\{\{\s*(copyvio|no permission|no source|delete|disputed|wrong license)',wiki,re.I)
    assert re.search(r'\{\{\s*Licensed-PD-Art\s*\|\s*PD-old-auto-1923\s*\|\s*Cc-zero\s*\|',wiki,re.I)
    assert int(re.search(r'\bdeathyear\s*=\s*(\d{4})',wiki).group(1))==im['source_artist']['death_date']
    assert not re.search(r'cc-by-nc|cc-by-nd|rights reserved|non-commercial',wiki,re.I)
    museum_url='https://www.artic.edu/artworks/'+im['external_id']
    credits=BeautifulSoup(meta['Credit']['value'],'html.parser')
    assert any(a.get('href','').rstrip('/')==museum_url for a in credits.find_all('a'))
    assert re.search(r'https://www\.artic\.edu/artworks/'+re.escape(im['external_id'])+r'(?!\d)',wiki)
    assert im['accession_number'] in page['title'] and native.norm(common.plain(meta['Artist']['value']))==native.norm(im['artist'])
    assert not meta.get('Restrictions',{}).get('value')
    qid=re.search(r'\|\s*wikidata\s*=\s*(Q\d+)\b',wiki).group(1)
    sdc=raw['structured_data'];assert common.ids(sdc,'P275')=={'Q6938433'}
    assert 'Q50423863' not in common.ids(sdc,'P6216'),'Structured copyright conflict'
    assert common.ids(sdc,'P6243')=={qid} and common.ids(sdc,'P180')=={qid}
    parsed=raw['rendered_licences']['parse']
    assert parsed['pageid']==page['pageid'] and parsed['revid']==page['revisions'][0]['revid']
    soup=BeautifulSoup(parsed['text']['*'],'html.parser')
    uris={common.canonical_licence_uri(n.get_text(strip=True)) for n in soup.select('.licensetpl_link')}
    assert uris=={native.CC0,common.PDM} and im['policy_url']==native.CC0 and im['rights_status']=='cc0'
    assert im['page']==info['descriptionurl'] and im['source_record_url']==museum_url
    assert im['source_image_url']==info['thumburl'] and urlparse(im['source_image_url']).hostname in ('upload.wikimedia.org','thumb.wikimedia.org')
    assert im['creator_credit'] and im['attribution_text']

def attach(db,im,target):
    verify(im)
    with db.transaction():
        rows=db.execute("""SELECT a.id::text,a.slug,a.title,a.accession_number,a.creation_year_start,a.creation_year_end,a.work_type,a.status,a.published_at,a.primary_media_id::text,i.slug institution_slug,
          ARRAY(SELECT ar.slug FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id AND aa.attribution_role='primary') artist_slugs
          FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id JOIN institutions i ON i.id=a.current_institution_id
          WHERE e.entity_type='artwork' AND e.scheme=%s AND e.external_id=%s FOR UPDATE OF a""",(im['scheme'],im['external_id'])).fetchall()
        assert len(rows)==1 and rows[0]['id']==im['target_ids'][target]
        row=rows[0];assert all(row[k]==im[k] for k in ('slug','title','accession_number','creation_year_start','creation_year_end','work_type','artist_slugs'))
        assert row['status']=='review' and row['published_at'] is None and row['institution_slug']==native.SLUG
        result=common.original_attach(db,im,target)
        if result=='attached':
            db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['media_id']))
            db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',('Exact current museum artwork ID, inventory and primary creator. Commons file explicitly links that museum object; same-revision rendered licences and structured data independently confirm CC0 for the reproduction and PDM for the depicted artwork.',im['media_id']))
        return result
core.attach=attach
