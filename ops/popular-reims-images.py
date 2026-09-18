#!/usr/bin/env python3
"""Selected Reims paintings: exact museum record, CC BY media, public renditions.

Uses only image URLs already embedded in the public object page. The HD download
form is never submitted or bypassed. Its licensed preview must match the public
rendition in pixels, dimensions, photographer and object identity; otherwise hold.
No catalogue fields or publication states are changed.
"""
import argparse
import importlib.util
import io
import json
import re
import unicodedata
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup
from PIL import Image, ImageChops, ImageStat

spec = importlib.util.spec_from_file_location('reims_core', Path(__file__).with_name('enrich-artwork-images.py'))
core = importlib.util.module_from_spec(spec); spec.loader.exec_module(core)
HOST = 'https://musees-reims.fr'
LICENSE = 'https://creativecommons.org/licenses/by/2.0/fr/'
PROVIDER = 'popular-reims'
core.PROVIDERS[PROVIDER] = 'Musées de Reims'
core.HOSTS.add('musees-reims.fr')
core.VERSION = 'reims-exact-cc-by-2-fr-public-rendition-v1'


def norm(value):
    value = ''.join(c for c in unicodedata.normalize('NFKD', value).casefold() if not unicodedata.combining(c))
    return re.sub(r'[^\w]+', ' ', value).strip()


def parse_object(html, page, media_rights=True):
    if not re.fullmatch(re.escape(HOST) + r'/oeuvre/[a-z0-9-]+', page):
        raise ValueError('Unapproved museum object URL')
    soup = BeautifulSoup(html, 'html.parser')
    def one(selector, within=soup):
        hits = within.select(selector)
        if len(hits) != 1: raise ValueError('Missing or ambiguous source field: ' + selector)
        return hits[0]
    def field(label):
        nodes = [dt.find_next_sibling('dd') for dt in soup.select('#fiche-complete dt') if dt.get_text(' ', strip=True) == label]
        if not nodes or any(x is None for x in nodes): raise ValueError('Missing source field: ' + label)
        return nodes
    accession = field("Numéro d'inventaire")
    if len(accession) != 1: raise ValueError('Conflicting source accession')
    accession = accession[0].get_text(' ', strip=True)
    header = one('.oeuvre-fiche-partielle')
    artist = one('.informations-creation .auteur', header).get_text(' ', strip=True)
    painter = field('peintre')
    if len(painter) != 1: raise ValueError('Multiple or qualified painters require review')
    if norm(one('a strong', painter[0]).get_text(' ', strip=True)) != norm(artist):
        raise ValueError('Painter fields conflict')
    dates = [re.sub(r'\s+', ' ', x.get_text(' ', strip=True)) for x in painter[0].select('a[href*="ZoneCreation-EpoqueDatation="]')]
    # This field may contain movements as well as dates. Keep the source text;
    # only independently parse recognised date syntax, never artist life dates.
    dates = [x for x in dates if re.search(r'\d', x)]
    if not dates: raise ValueError('Creation date needs separate review')
    date = '; '.join(dates)
    if not media_rights:
        # Range qualifiers (entre/et/vers/fin) may sit outside the linked years.
        source_text = re.sub(r'\s+', ' ', painter[0].get_text(' ', strip=True))
        if 'Epoque, datation : ' in source_text:
            source_date = source_text.split('Epoque, datation : ', 1)[1]
            date = '; '.join(x.strip() for x in source_date.split(';') if re.search(r'\d', x))
    h = re.fullmatch(r'(?:vers )?(\d{4})', date)
    if h: lo = hi = int(h[1])
    elif date == '19e siècle': lo, hi = 1800, 1900
    elif date == '2e moitié 19e siècle': lo, hi = 1850, 1900
    elif date in ('4e quart 19e siècle', 'fin 19e siècle; 4e quart 19e siècle'): lo, hi = 1875, 1900
    elif (h := re.fullmatch(r'(?:entre |vers )(\d{4}); (?:et |vers )(\d{4})', date)):
        lo, hi = int(h[1]), int(h[2])
    else: raise ValueError('Unsupported creation interval')
    domain = field('Domaine')
    if len(domain) != 1 or domain[0].get_text(' ', strip=True) != 'peinture':
        raise ValueError('Authoritative classification is not painting')
    museum = one('.informations-generales a.musee', header)
    if museum.get('href') != 'fr/musees/musee-des-beaux-arts/' or museum.get_text(' ', strip=True) != 'Musée des Beaux-Arts':
        raise ValueError('Holding museum differs')
    if '(inv. ' + accession + ')' not in one('.informations-generales', header).get_text(' ', strip=True):
        raise ValueError('Holding accession conflicts')
    image = one('.oeuvre-fiche-image .oeuvre-image-1')
    src = urljoin(HOST + '/', one('img', image)['src'])
    if image.get('data-src') != one('img', image)['src']:
        raise ValueError('Displayed source image differs')
    credit = one('.oeuvre-credits', image).get_text(' ', strip=True)
    if not re.fullmatch(r'Domaine public Photo : [\wÀ-ÿ .’\'-]+', credit):
        raise ValueError('Image contains unresolved or restricted credit')
    photo_credit = credit.split('Photo : ', 1)[1]
    title = one('h1', header).get_text(' ', strip=True)
    titles = [dt.find_next_sibling('dd').get_text(' ', strip=True) for dt in soup.select('#fiche-complete dt')
              if dt.get_text(' ', strip=True) == 'Titre'] or [title]
    medium = field('Libellé')
    if len(medium) != 1: raise ValueError('Conflicting medium')
    if not media_rights:
        # For an independently licensed donated photograph, this page supplies
        # object facts only. Its current image/photographer confer no rights on
        # the older donated file and must never replace that file's own credit.
        return dict(page=page, title=title, titles=titles, artist=artist, accession_number=accession,
                    object_type='peinture', year_start=lo, year_end=hi, date_text=date,
                    medium=medium[0].get_text(' ', strip=True), museum='Musée des Beaux-Arts de Reims', country='FR',
                    reference_image_url=src, reference_photographer=photo_credit)
    downloads = one('#telecharger')
    cards = downloads.select('button.image-hd-card')
    if len(cards) != 1: raise ValueError('No unique explicitly licensed HD photograph')
    card = cards[0]
    links = downloads.select('.licence-ouverte a[href]')
    if len(links) != 1 or links[0]['href'] != LICENSE or links[0].get_text(' ', strip=True) != 'CC BY':
        raise ValueError('Exact image CC BY licence unavailable')
    if re.search(r'non.commercial|réservé|permission|interdit', downloads.get_text(' ', strip=True), re.I):
        raise ValueError('Conflicting download restriction')
    if card.get('data-oeuvre') != accession or card.get('data-numinventaire') != '(inv. ' + accession + ')':
        raise ValueError('Licensed image accession conflicts')
    if card.get('data-droits') != photo_credit or card.get('data-musee') != 'Musée des Beaux-Arts':
        raise ValueError('Licensed image credit or museum differs')
    if set(norm(card.get('data-oeuvreauteur', '')).split()) != set(norm(artist).split()):
        raise ValueError('Licensed image artist differs')
    title = one('h1', header).get_text(' ', strip=True)
    if norm(card.get('data-oeuvretitre', '')) != norm(title):
        raise ValueError('Licensed image title differs')
    hd_url = urljoin(HOST + '/', card.get('data-image', ''))
    if not re.fullmatch(re.escape(HOST) + r'/IMG/base/multimedia-hd/MBA/' + re.escape(accession) + r'\.P(?:\.\d+| \(\d+\))\.jpg', hd_url):
        raise ValueError('Licensed media is not this accession')
    thumb = one('img', card)
    thumb_url = urljoin(HOST + '/', thumb['src'])
    # The modal and inline previews may use different dimensions/cache suffixes,
    # but both must name the exact licensed HD photograph (including view number).
    stem = re.escape(Path(urlparse(hd_url).path).stem)
    for preview in (thumb_url, urljoin(HOST + '/', card.get('data-vignette', ''))):
        if not re.fullmatch(re.escape(HOST) + r'/local/cache-vignettes/L\d+xH\d+/' + stem + r'-[a-f0-9]+\.jpg\?\d+', preview):
            raise ValueError('Licensed image preview differs')
    for url in (src, thumb_url):
        if not re.fullmatch(re.escape(HOST) + r'/local/cache-vignettes/L\d+xH\d+/[A-Za-z0-9.() -]+\.jpg\?\d+', url):
            raise ValueError('Unapproved public image rendition')
    titles = [x.get_text(' ', strip=True) for x in field('Titre')]
    medium = field('Libellé')
    if len(medium) != 1: raise ValueError('Conflicting medium')
    return dict(page=page, title=title, titles=titles, artist=artist, accession_number=accession,
                object_type='peinture', year_start=lo, year_end=hi, date_text=date,
                medium=medium[0].get_text(' ', strip=True), museum='Musée des Beaux-Arts de Reims', country='FR',
                image_url=src, licensed_preview_url=thumb_url, licensed_hd_url=hd_url,
                licence_uri=LICENSE, photographer=photo_credit, image_credit=credit,
                source_object_id=card.get('data-notice'),
                basis='Exact photograph CC BY 2.0 France in museum download section; only the matching publicly embedded rendition is downloaded.')


def compare_renditions(display_bytes, licensed_preview_bytes):
    with Image.open(io.BytesIO(display_bytes)) as a, Image.open(io.BytesIO(licensed_preview_bytes)) as b:
        a.load(); b.load()
        aw, ah = a.size; bw, bh = b.size
        ratio_error = abs((aw / ah) / (bw / bh) - 1)
        a = a.convert('RGB').resize((96, 96), Image.Resampling.LANCZOS)
        b = b.convert('RGB').resize((96, 96), Image.Resampling.LANCZOS)
        mae = sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3
    if ratio_error > .025 or mae > 5:
        raise ValueError('Licensed preview and public photograph require visual reconciliation')
    return dict(display_sha256=core.sha(display_bytes), licensed_preview_sha256=core.sha(licensed_preview_bytes),
                display_dimensions=[aw, ah], preview_dimensions=[bw, bh], aspect_error=ratio_error,
                mean_rgb_absolute_error=mae, verified=True)


def verify_object_identity(im, obj, allow_narrower_dates=False):
    """Reuse exact catalogue identity checks across independently licensed photos."""
    if im['institution_slug'] != 'joconde-m0311' or im['country_code'] != 'FR' or im['scheme'] != 'european-joconde-m0311-object':
        raise ValueError('Existing institution or native source identity differs')
    if not any(x['scheme'] == im['scheme'] and x['external_id'] == im['external_id'] for x in im['identifiers']):
        raise ValueError('Existing source identifier absent')
    # Supplied catalogue accessions may also list historical inventory numbers.
    if obj['accession_number'] != im['accession_number'].split(';')[0].strip():
        raise ValueError('Exact current accession differs')
    known_titles = set(map(norm, [im['title'], *(im.get('alternate_title') or '').split(';'), *im['title'].split(';')]))
    if norm(obj['title']) not in known_titles or not set(map(norm, obj['titles'])) & known_titles:
        raise ValueError('Artwork title differs')
    if norm(obj['artist']) not in set(map(norm, im['artist_names'])) or im['roles'] != ['primary']:
        raise ValueError('Creator or attribution differs')
    if not all(isinstance(im[k], int) for k in ('creation_year_start', 'creation_year_end')) or not 1000 <= im['creation_year_start'] <= im['creation_year_end'] <= 1970:
        raise ValueError('Existing creation scope needs review')
    dates_agree = ((im['creation_year_start'] <= obj['year_start'] <= obj['year_end'] <= im['creation_year_end'])
                   if allow_narrower_dates else (obj['year_start'], obj['year_end']) == (im['creation_year_start'], im['creation_year_end']))
    if not dates_agree or not 1000 <= obj['year_start'] <= obj['year_end'] <= 1970 or im['work_type'] != 'painting':
        raise ValueError('Creation scope differs')


def verify(im):
    raw = im['raw']; capture = raw['capture']
    if core.sha(capture['html'].encode()) != capture['selected_fields_sha256']:
        raise ValueError('Source capture checksum differs')
    obj = parse_object(capture['html'], capture['url'])
    if obj != raw['object']: raise ValueError('Stored source fields differ from captured evidence')
    verify_object_identity(im, obj)
    if im['policy_url'] != LICENSE or im['rights_status'] != 'cc_by' or im['license_label'] != 'CC BY 2.0 France':
        raise ValueError('Exact image licence differs')
    if im['page'] != obj['page'] or im['source_record_url'] != obj['page'] or im['source_image_url'] != obj['image_url']:
        raise ValueError('Source page or exact image differs')
    match = raw['rendition_match']
    if not match['verified'] or match['aspect_error'] > .025 or match['mean_rgb_absolute_error'] > 5:
        raise ValueError('Image rendition identity unverified')
    if im.get('source_sha256') and im['source_sha256'] != match['display_sha256']:
        raise ValueError('Downloaded source image changed after verification')
    if obj['photographer'] not in im['creator_credit'] or obj['photographer'] not in im['attribution_text'] or LICENSE not in im['attribution_text']:
        raise ValueError('Required photographer or licence credit missing')
    if not capture['retrieved_at'] or not capture['response_sha256'] or not im['rights_verified_at']:
        raise ValueError('Retrieval evidence missing')


base_attach = core.attach

def attach(db, im, target):
    verify(im)
    return attach_verified(db, im, target)


def attach_verified(db, im, target):
    """Write only after the calling adapter has verified its exact image rights."""
    with db.transaction():
        row = db.execute("""SELECT a.id::text,a.slug,a.title,a.accession_number,a.work_type,a.creation_year_start,a.creation_year_end,
          a.status,a.published_at,a.current_institution_id::text,
          ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) artists,
          ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) roles
          FROM artworks a WHERE a.id=%s FOR UPDATE""", (im['target_ids'][target],)).fetchone()
        if not row or row['status'] != 'review' or row['published_at'] or row['current_institution_id'] != im['institution_ids'][target] or row['artists'] != im['artist_ids'][target] or row['roles'] != ['primary']:
            raise ValueError('Current target creator, institution or review status changed')
        if any(row[k] != im[k] for k in ('slug','title','accession_number','work_type','creation_year_start','creation_year_end')):
            raise ValueError('Current artwork identity changed')
        result = base_attach(db, im, target)
        if result == 'attached':
            db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s', (im['creator_credit'],im['attribution_text'],im['media_id']))
        return result

core.attach = attach


def main():
    p = argparse.ArgumentParser(); p.add_argument('--run', type=Path, required=True); a = p.parse_args()
    assert (a.run.parent/'backups.json').exists(), 'Backups required'
    policy = RobotFileParser(); policy.parse((a.run.parent/'probes/reims-robots.html').read_text().splitlines())
    fetch = core.Fetcher(a.run/'evidence')
    for c in json.loads((a.run/'candidates.json').read_text())['candidates']:
        if (a.run/'images'/PROVIDER/(c['artwork_id']+'.json')).exists(): continue
        try:
            capture = json.loads(Path(c['capture_path']).read_text()); obj = parse_object(capture['html'],capture['url'])
            urls = [obj['image_url'],obj['licensed_preview_url']]
            if not all(policy.can_fetch('Artline', u) for u in [capture['url'],*urls]): raise ValueError('Robots policy restricts resource')
            downloaded = [fetch.get(u,2_000_000)[0] for u in urls]
            match = compare_renditions(*downloaded)
            # Cache the explicitly licensed small preview for reproducible comparison.
            preview = a.run/'licensed-previews'/(c['artwork_id']+'.jpg'); core.save_new(preview,downloaded[1])
            im = dict(c, provider=PROVIDER, source_name='Musées de Reims', page=obj['page'], source_record_url=obj['page'],
                      source_object_id=obj['source_object_id'], source_image_url=obj['image_url'], policy_url=LICENSE,
                      rights_status='cc_by', license_label='CC BY 2.0 France', creator_credit='Photo: '+obj['photographer']+' / Musées de Reims',
                      attribution_text=f"{c['artist']}. {c['title']}. Musée des Beaux-Arts de Reims. Photo: {obj['photographer']}. CC BY 2.0 France ({LICENSE}). Full-frame proportional resize and JPEG compression.",
                      checked_at=core.now(), rights_verified_at=core.now(), creation_date=obj['date_text'],
                      raw={'capture':capture,'object':obj,'rendition_match':match})
            verify(im); core.save_new(a.run/'selected'/PROVIDER/(c['artwork_id']+'.json'),im)
            core.worker(PROVIDER,[im],SimpleNamespace(run=a.run,prepare_only=True),None)
            receipt = a.run/'images'/PROVIDER/(c['artwork_id']+'.json')
            if receipt.exists(): verify(json.loads(receipt.read_text()))
            print(core.now(), 'Verified museum image prepared:', c['title'], flush=True)
        except (ValueError,KeyError) as exc:
            core.event(a.run,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='manual_review',reason=str(exc)))
            print(core.now(),'Held:',c['title'],str(exc),flush=True)

if __name__ == '__main__': main()
