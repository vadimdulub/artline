#!/usr/bin/env python3
"""Explicitly reviewed identities and source conflicts from the research session."""
import importlib.util
from pathlib import Path
import uuid
from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('primary', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(s)
s.loader.exec_module(p)
r = p.r
TRINITY_UPDATE = 'https://lavra.ru/lavra-news/kommentariy-namestnika-troitse-sergievoy-lavry-o-sostoyanii-ikony-svyatoy-troitsy-napisannoy-prepodo/'


def evidence(url, expected):
    raw, receipt = r.capture(url, tag='manual', timeout=45)
    assert receipt['status'] == 200
    soup = BeautifulSoup(raw, 'html.parser')
    for node in soup.select('script,style,nav,footer'):
        node.decompose()
    text = ' '.join(soup.get_text(' ', strip=True).split())
    for token in expected:
        assert token in text, ('Reviewed source content changed', token)
    return receipt, text


def main():
    index = p.Index()
    greek = index.institution('national-gallery-greece')
    tretyakov = index.institution('wikimedia-museum-q183334')
    reviewed = [
        ('03d32934-c867-5df7-a95e-3446c2f92ee4', greek, 'greek-gallery-object', 'Π.673',
         'https://www.nationalgallery.gr/en/artwork/santorini/',
         ['Maleas Konstantinos', 'Santorini, 1924 - 1928', 'Π.673', '75 x 107 cm'],
         'Title and named creator match; supplied 1928 lies within the museum 1924–1928 range. Exact official inventory Π.673. Date metadata preserved.', 'accepted'),
        ('02b0f1cc-ae7f-5ba3-b889-df8e37940139', greek, 'greek-gallery-object', 'Π.5446',
         'https://www.nationalgallery.gr/en/artwork/the-exodus-from-missolonghi/',
         ['Vryzakis Theodoros', 'The Exodus from Missolonghi, 1853', 'Π.5446', '169 x 127 cm'],
         'The existing Commons painting identity names Vryzakis and 1853. Sortie/Exodus and Messologhi/Missolonghi are reviewed title variants. Official original painting Π.5446; distinct 1855 lithograph Π.1318 explicitly excluded.', 'accepted'),
        ('8414e828-5984-543d-99fb-dbdf58a4ec3c', tretyakov, 'tretyakov-masterpiece', '8394',
         'https://my.tretyakov.ru/app/masterpiece/8394',
         ['Девочка с персиками', 'Серов Валентин', '1887', 'Инв.13011', '91 x 85'],
         'Russian title translated as Girl with Peaches; creator, 1887 and 91 × 85 cm corroborated by the museum-provided Google Arts & Culture record vgFS_-o4tXr4Rw and Tretyakov Gallery Magazine record 22796. Current official inventory 13011.', 'accepted'),
        ('d256e26f-c0a4-5030-bd9e-4c076b7b6f42', tretyakov, 'tretyakov-masterpiece', '8408',
         'https://my.tretyakov.ru/app/masterpiece/8408',
         ['Иван Грозный и сын его Иван 16 ноября 1581 года', 'Репин Илья', '1885', 'Инв.743', '199,5 x 254'],
         'Reviewed Russian/English title equivalence includes exact narrative date 16 November 1581, Ilya Repin and creation year 1885. Exact original painting inventory 743; no current display inferred.', 'accepted'),
        ('1bc60885-3b30-50ff-b94d-38eeac4e98fd', tretyakov, 'tretyakov-masterpiece', '8812',
         'https://my.tretyakov.ru/app/masterpiece/8812',
         ['Святая Троица', 'Андрей Рублев', 'Инв.13012', '141,5 x 114'],
         'Original Rublev Trinity identified by named creator, subject and museum inventory 13012. Museum dates 1422–1427 conflict with retained source range 1410–1420; no date correction. Museum collection association is separate from the documented Lavra loan and workshop location.', 'accepted'),
    ]
    claims = []
    for aid, institution, scheme, oid, url, tokens, basis, state in reviewed:
        receipt, text = evidence(url, tokens)
        obj = {'reviewed_tokens': tokens, 'manual_identity_review': basis}
        c = p.claim(index.by_id[aid], scheme, oid, institution, receipt, url, obj, basis)
        c['review_state'] = state
        if oid == '8812':
            update_receipt, update_text = evidence(TRINITY_UPDATE, ['19 сентября 2026', 'в реставрационной мастерской', 'Третьяковской галереи'])
            c['location_text'] = 'Trinity Lavra of St Sergius, conservation workshop (reported 19 September 2026)'
            c['object_evidence']['dated_physical_location_source'] = update_receipt
            c['limitation'] = 'Tretyakov museum collection association only. The original is on long-term loan to the Lavra and was reported in its conservation workshop on 19 September 2026, out of the cathedral iconostasis. This source does not support current public display. Original creation-date disagreement is preserved.'
        claims.append(c)

    # The museum page establishes the museum's own object, but the catalogue row
    # has a conflicting source date and museum. Preserve a review assertion.
    url = 'https://sis.modernamuseet.se/objects/3697/le-cerveau-de-lenfant'
    receipt, text = evidence(url, ['The Child\'s Brain', 'Giorgio de Chirico', 'NM 6068', '1914', '80 × 65'])
    institution = {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/museum-location/moderna-museet-stockholm')), 'slug': 'moderna-museet-stockholm', 'name': 'Moderna Museet', 'normalized_name': 'moderna museet', 'website_url': 'https://www.modernamuseet.se/stockholm/en/', 'kind': 'museum', 'status': 'review', 'wikidata_id': None, 'description': 'Museum identity documented by its official collection catalogue. Distinguish the original NM 6068 from the 1978 exhibition poster NMAFF 21/1978.'}
    c = p.claim(index.by_id['104fd15b-4795-5834-b4e2-9a02e2c7a314'], 'moderna-museet-object', '3697', institution, receipt, url,
                {'title': "The Child's Brain", 'creator': 'Giorgio de Chirico', 'museum_date': '1914', 'inventory': 'NM 6068', 'dimensions': '80 × 65 cm', 'catalogue_source_date': '1917', 'rejected_poster_object_id': '105413'},
                'Exact title and creator; reviewed official original-object identity. Source date and WikiArt museum attribution conflict, so the target remains in review.')
    c['review_state'] = 'review'
    c['limitation'] = 'Do not set a current museum until the conflicting WikiArt 1917 identity is reconciled with the museum original dated 1914. Object 105413 is a 1978 poster and is not this painting.'
    claims.append(c)

    url = 'https://www.searchculture.gr/aggregator/edm/pandektis_painters/000083-10442_85133?language=en'
    receipt, text = evidence(url, ['The Virgin, The Tree of Jesse', 'Poulakis', 'Byzantine Museum', 'Athina'])
    c = p.claim(index.by_id['1178e957-b105-5980-8615-713e62e0d833'], 'pandektis-artwork', '10442_85133', index.institution('byzantine-christian-museum-athens'), receipt, url,
                {'research_collection': 'National Hellenic Research Foundation, Pandektis', 'museum': 'Byzantine and Christian Museum, Athens', 'original_provenance': 'Zoodochos Pigi Kastellanon Kerkyras church', 'museum_inventory_lead': 'BXM 1575'},
                'Named Poulakis Tree of Jesse identity and museum documented by Greek national research aggregation; independent museum inventory confirmation remains required.')
    c['review_state'] = 'review'
    c['source_class'] = 'national_research_catalogue'
    c['limitation'] = 'Research catalogue museum association retained for review; current museum object and precise chronology still require reconciliation. No display claim.'
    claims.append(c)
    p.output('curated', claims, [])


if __name__ == '__main__':
    main()
