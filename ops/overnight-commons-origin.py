"""Conservative original-provenance check, separate from per-file licensing.

An allowed origin is not a copyright licence. The exact Commons file must also
pass the existing licence, attribution and physical-object identity checks.
"""
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
INSTITUTIONAL_PORTALS={'artuk.org','culture.gouv.fr','cultureelerfgoed.nl','rkd.nl','webumenia.sk','vlaamsekunstcollectie.be','artinflanders.be','gallica.bnf.fr','parismuseescollections.paris.fr','royalcollection.org.uk','collection.nationalmuseum.se','hispanicsociety.emuseum.com','digitaltmuseum.no','digitaltmuseum.se'}
BLOCKED=re.compile(r'art500k|wikiart|wikipaintings|pinterest|pinimg|wallpaper|fineartamerica|wga\.hu|web gallery of art|blogspot|wordpress|tumblr|lofter|fbcdn|bridgeman|alamy|sotheby|bonhams|artcurial|arcadja|photo\.rmn\.fr|art\.rmngp\.fr|rmn\.orangelogicdns|nationalgalleryimages\.co\.uk|nationalgallery\.org\.uk|rusmuseum|pushkinmuseum\.art|artsandculture\.google|googleartproject|Google (?:Arts|Cultural Institute)|archive\.is|webshots|Yorck Project|DIRECTMEDIA|pubhist|the-athenaeum|allposters|allart\.biz|meisterdrucke|wahooart|art\.com|myartprints|artblart|artsy\.net',re.I)
def host(url):return (urlparse(url or '').hostname or '').removeprefix('www.')
def matches(domain,base):return bool(base) and (domain==base or domain.endswith('.'+base))
def verify(c,page):
 meta=page.get('imageinfo',[{}])[0].get('extmetadata',{});source=' '.join(meta.get(k,{}).get('value','') for k in ('Credit','Attribution'));plain=BeautifulSoup(source,'html.parser').get_text(' ',strip=True)
 if BLOCKED.search(source):raise ValueError('Original image provenance is a restricted source, commercial library, search/marketplace service or unverified mirror')
 if re.search(r'copied from an art book|repro from art book',plain,re.I):raise ValueError('Unidentified art-book reproduction conflicts with claimed photographic origin')
 if re.search(r'transferred from',plain,re.I) and not re.search(r'own work|own photo|self-photographed|photographie personnelle',plain,re.I):raise ValueError('File transfer attribution does not establish the original photographer')
 if re.search(r'digital processing|digitally desaturated|digital(?:ly)? colou?ri[sz]ed|processing done by',plain,re.I):raise ValueError('Image editor credit does not establish the original photograph provenance')
 if re.search(r'own work|own photo|self-photographed|User:|User%3A|photographie personnelle|eget foto|photo(?:graph)? by Szilas',source,re.I):return 'independent_photographer'
 domains={host(a.get('href','')) for a in BeautifulSoup(source,'html.parser').find_all('a')};domains.discard('');museum=host(c.get('website_url'))
 if any(matches(d,museum) for d in domains):return 'holding_institution_source'
 if any(matches(d,p) for d in domains for p in INSTITUTIONAL_PORTALS):return 'institutional_cultural_record'
 raise ValueError('Original image source is not independently established as an institution or identified photographer')
