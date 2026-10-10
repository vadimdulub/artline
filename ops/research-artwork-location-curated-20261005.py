#!/usr/bin/env python3
"""Manually reconciled Russian and Greek object identities; qualifications retained."""
import concurrent.futures
import importlib.util
from pathlib import Path
from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('primary', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r

# Local record, source slug, inventory, source metadata, identity qualification.
GREEK = [
    ('d0ee15db-ea57-5182-b210-573bc9d697c6', 'virgin-with-divine-infant-crucifixion', 'Π.9987', ['Parthenis Konstantinos', '1940 - 1942', '125 x 350 cm'], 'Exact composition, creator, date range and dimensions.', 'accepted'),
    ('13b77cd6-7de5-5f42-837c-f18df94eda9a', 'portrait-of-aristovouli-lopresti', 'Π.3225', ['Parthenis Konstantinos', '1933', '115 x 109,5 cm'], 'Exact named sitter and creator; 1933 agrees. WikiArt rounds width to 110 cm.', 'accepted'),
    ('91629918-9e33-55d3-a12c-2bb8495d5af2', 'middle-easterner-with-pipe', 'Π.4071', ['Gyzis Nikolaos', '1873', '40,5 x 31,5 cm'], 'Exact title, creator, approximate date and dimensions.', 'accepted'),
    ('453fa9f4-a8d3-5322-8ba4-4bbca98c00f7', 'the-riches-of-communication', 'Π.494', ['Parthenis Konstantinos', '1925', '79 x 174 cm'], 'Original Π.494 with dimensions in reversed order in WikiArt. Distinct smaller version Π.9993 at Coumantaros explicitly excluded.', 'accepted'),
    ('f3de1d33-3580-584c-91fd-54e4cfc3d024', 'gazing-at-peace-2', 'Π.6507', ['Parthenis Konstantinos', '1930 - 1938', '192 x 62 cm'], 'Exact title, creator and dimensions; supplied circa 1938 falls within museum range. Existing chronology unchanged.', 'accepted'),
    ('bdbc0c00-ec2a-5195-b184-2fd20cef2ab3', 'landscape-with-fir-trees-ischl', 'Κ.629', ['Parthenis Konstantinos', '1902', '32 x 43 cm'], 'Title specifies Ischl in museum record; creator, 1902 and dimensions agree.', 'accepted'),
    ('6ed891f5-4efc-533d-b80f-728d48c2a02f', 'battle-between-heracles-and-the-amazons', 'Π.6503', ['Parthenis Konstantinos', '1921 - 1927', '116 x 130,6 cm'], 'Creator, subject and date range agree; source dimensions 131 x 115 differ from current museum 116 x 130.6. Object identity needs reconciliation.', 'review'),
    ('cd013af7-4d17-5549-ae54-b96c6beecec9', 'the-slope', 'Π.458', ['Parthenis Konstantinos', '1908', '96 x 92 cm'], 'Exact title, creator, year and dimensions; other artist Yoldassis work with same title explicitly excluded.', 'accepted'),
    ('c50eb95b-3b6a-5a97-825c-e83374f2fd2d', 'landscape-from-kavala', 'Κ.621', ['Parthenis Konstantinos', '1904', '63,3 x 52 cm'], 'Exact named location, creator and circa 1904; WikiArt rounds 63.3 cm to 63. Existing metadata preserved.', 'accepted'),
    ('bf133e36-6bee-5b6f-a9b4-db5d32357ec5', 'portrait-of-miss-m-horsch', 'Π.496', ['Lytras Nikos', '1916-1917', '110 x 84 cm'], 'Mlle/Miss title variant; Nikos is the museum name for Nikolaos Lytras. Named sitter, date range and dimensions agree.', 'accepted'),
    ('88afebd4-5f9c-5c3f-aeea-76253f763425', 'the-virgin-mary', 'Π.6472', ['Parthenis Konstantinos', '1940 - 1942', '125 x 67 cm'], 'Exact title, creator, date range and dimensions.', 'accepted'),
    ('63dde63b-2fe4-5508-b1a9-2604584be6d4', 'still-life-with-acropolis-in-the-background', 'Π.6482', ['Parthenis Konstantinos', 'before 1931', '41 x 81 cm'], 'Exact distinctive title, creator and dimensions; current museum before-1931 wording differs from retained circa-1931 source. Chronology unchanged.', 'accepted'),
    ('f0ca4809-fec6-5829-b42a-43b771f916a0', 'the-slave-market', 'Π.553', ['Gyzis Nikolaos', '1873-1875', '72 x 50 cm'], 'Exact title, creator, approximate date range and dimensions.', 'accepted'),
    ('fc72288d-1398-5d7d-a77c-3bb9af94b0fd', 'the-apotheosis-of-athanasios-diakos', 'Π.6506', ['Parthenis Konstantinos', 'before 1933', '371 x 380 cm'], 'Title and creator agree; source has circa 1933 and 380 x 380, museum before 1933 and 371 x 380. Retain candidate pending dimensional/date reconciliation.', 'review'),
    ('44ee8a6d-00b3-5d99-8b00-cebab1c91b53', 'youths-enjoying-themselves-in-galatsi', 'Κ.512', ['Triantaphyllidis Theophrastos', '1935', '44 x 59 cm'], 'Triantafyllidis/Triantaphyllidis transliteration; exact title, year and dimensions, reversed in WikiArt.', 'accepted'),
    ('6852b198-7ffa-542c-8a4f-049efc3480b4', 'caique-at-spetses', 'Π.1818', ['Altamouras Ioannis', '1877', '29 x 39 cm'], 'Boat to Spetses/Caique at Spetses title translation and artist/year agree; no dimensions supplied in local source, so exact object variant remains in review.', 'review'),
    ('cde3d2d7-1813-53aa-8fa1-af351e6ab198', 'la-temperanza-woman-holding-a-knife', 'Π.6484', ['Parthenis Konstantinos', 'before 1938', '84,6 x 62,2 cm'], 'Exact distinctive title and creator. Museum before-1938 wording and dimensions slightly differ from circa-1938, 84.5 x 62; older museum donation catalogue confirms inventory 6484 and the latter measurements. Original fields preserved.', 'accepted'),
    ('23354afb-34b4-57b9-a824-b46445087f0e', 'the-little-church-of-cephalonia', 'Π.9985', ['Parthenis Konstantinos', '1920 - 1925', '115,2 x 130,6 cm'], 'Title, creator and dates agree; 130 x 118 source dimensions differ from 115.2 x 130.6 museum dimensions. Keep in review pending reconciliation.', 'review'),
]
RUSSIAN = [
    ('b0dd9420-4548-54c6-b89f-e78b93e7dac0', '8425', ['Лентулов Аристарх', 'Москва', '1913', 'Ж-865', '179 x 189'], 'Moscow/Москва title translation, Aristarkh Lentulov, 1913 and dimensions match; WikiArt reverses height and width.', 'accepted'),
    ('43c64375-baf7-5434-9f47-ea7650a1542c', '8891', ['Кустодиев Борис', 'Большевик', '1920', 'ЖС-27', '101 x 140,5'], 'The Bolshevik/Большевик title translation, Boris Kustodiev and 1920 agree; source rounds width from 140.5 to 141 cm.', 'accepted'),
    ('d3876576-1ca1-5b4d-98d9-66268ddd446f', '8774', ['Андрей Рублев', 'Апостол Павел из деисусного чина', 'Инв.12865', '160 x 108,5'], 'Zvenigorod Apostle Paul: title, set and historical attribution agree. Museum explains 2016–2017 research questioning Rublev attribution; dimensions differ from WikiArt 160 x 110. Preserve source attribution and retain review.', 'review'),
    ('b45eed32-d301-500b-8d3b-0c39f93e0c0d', '8773', ['Андрей Рублев', 'Архангел Михаил из деисусного чина', 'Инв.12864', '158 x 108'], 'Zvenigorod Archangel Michael: exact dimensions and set identity. Museum dates early fifteenth century and explains disputed Rublev attribution. Retain supplied 1414 and creator without endorsing a definitive attribution.', 'review'),
    ('ca18b48d-ba39-5cb8-8138-77a4d32fe787', '8772', ['Андрей Рублев', 'Спас, из Деисусного чина', 'Инв.12863', '158 x 105,5'], 'Zvenigorod Christ as Saviour: set and subject identify candidate; source rounds width to 106 cm. Museum discusses disputed Rublev attribution, retained explicitly for review.', 'review'),
]


def main():
    index = p.Index()
    jobs = []
    for aid, slug, inventory, tokens, basis, state in GREEK:
        jobs.append((aid, index.institution('national-gallery-greece'), 'greek-gallery-object', inventory, 'https://www.nationalgallery.gr/en/artwork/' + slug + '/', tokens + [inventory], basis, state))
    for aid, oid, tokens, basis, state in RUSSIAN:
        jobs.append((aid, index.institution('wikimedia-museum-q183334'), 'tretyakov-masterpiece', oid, 'https://my.tretyakov.ru/app/masterpiece/' + oid, tokens, basis, state))
    jobs.append(('4cbe01ca-b930-5983-82dc-db5af4b0336f', index.institution('state-russian-museum'), 'russian-museum-object', 'mikh-palace-zhneci', 'https://virtual.rusmuseumvrm.ru/mikh_palace/collection/russkoe_iskusstvo_pervoy_polovini_xix_veka/zhneci/index.php?lang=ru', ['Венецианов', 'Жнецы', '66,7', '52', '1909'], 'Reapers/Жнецы, Venetsianov, late-1820s and exact 66.7 x 52 cm agree with supplied 1825–1829 range. Current official museum catalogue documents accession in 1909. No present public display inferred from a virtual tour.', 'accepted'))

    def one(job):
        aid, museum, scheme, oid, url, tokens, basis, state = job
        path = r.RUN / 'curated-results-20261005' / (aid + '.json')
        if path.exists():
            return r.load(path)
        try:
            lead = r.load(r.RUN / 'wikiart-leads' / (aid + '.json'))
            assert lead['title'] == index.by_id[aid]['artwork']['title']
            assert lead['outcome'] == 'museum_lead_requires_corroboration'
            raw, receipt = r.capture(url, tag='curated-20261005', timeout=40)
            assert receipt['status'] == 200, 'HTTP ' + str(receipt['status'])
            soup = BeautifulSoup(raw, 'html.parser')
            for node in soup.select('script,style,nav,footer'):
                node.decompose()
            text = ' '.join(soup.get_text(' ', strip=True).split())
            for token in tokens:
                assert token in text, 'Source token absent: ' + token
            c = p.claim(index.by_id[aid], scheme, oid, museum, receipt, url, {'reviewed_tokens': tokens, 'secondary_identity_lead': lead, 'manual_identity_review': basis, 'source_explicit_on_view_main_building': 'On view Main Building' in text if scheme == 'greek-gallery-object' else False}, basis)
            c['review_state'] = state
            c['limitation'] += ' ' + basis
            result = {'artwork_id': aid, 'claim': c, 'reason': 'manually_reconciled_source'}
        except Exception as exc:
            result = {'artwork_id': aid, 'reason': 'source_or_identity_requires_review', 'detail': str(exc)[:400], 'source_url': url}
        r.save(path, result)
        return result

    claims, holds = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n, result in enumerate(pool.map(one, jobs), 1):
            if result.get('claim'):
                claims.append(result['claim'])
            else:
                holds.append(result)
            print('Curated identity checked', n, '/', len(jobs), result['reason'], flush=True)
    p.output('curated-20261005', claims, holds)


if __name__ == '__main__':
    main()
