"""Individually selected Augustiner acquisitions from four museum annual reports."""
import gzip,hashlib,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-augustiner-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
# Report/PDF page identify the actual museum-owned physical acquisition.
# A print is one museum impression, never the artist's entire edition.
GROUPS=[('report2021',18,'''
eibner-muenster|Freiburg Münster mit Georgsbrunnen und Kornhaus|Friedrich Eibner|1868|watercolor|Aquarell
kirner-barbier|Beim Barbier|Johann Baptist Kirner|1832-1837|painting|Ölskizze
kirner-krug|Der zerbrochene Krug|Johann Baptist Kirner|~1834|drawing|Mischtechnik
kirner-pifferari|Pifferari mit Zuhörern vor einem Gebäude mit Marienbild|Johann Baptist Kirner|1834|watercolor|Aquarell
kirner-bahnwaerter|Salutierende Bahnwärter bei Einfahrt des Zuges|Johann Baptist Kirner|~1858|painting|Ölskizze
kirner-weinende|Weinende Italienerin, bei einem Überfall am Arm gehalten|Johann Baptist Kirner|?|painting|Ölskizze
kappis-regen|Ein Regenschauer zum Empfang, Gutach|Albert Kappis|1887|painting|Gemälde
'''),('report2021',19,'''
rembrandt-ratten|Der Rattengiftverkäufer|Rembrandt van Rijn|1632|print|Radierung
goya-selbst|Selbstbildnis (Titelblatt der Caprichos)|Francisco de Goya|1799|print|Radierung
liebermann-selbst|Selbstbildnis stehend, zeichnend|Max Liebermann|1913|print|Kaltnadelradierung
manuel-schletstatt|Schletstatt|Hans Rudolf Manuel|~1550|print|Kolorierter Holzschnitt
kieser-tod|Omnis dies, omnis hora, quam nihil sumus, ostendit (Tod und Allegorie der Zeit mit Ansicht von Freiburg)|Eberhard Kieser|1623-1624|print|Kupferstich
kieser-breisach|Bonus à bono (Breisach)|Eberhard Kieser|1623-1624|print|Kupferstich
merian-colmar|Colmar|Caspar Merian|1643|print|Kupferstich
seutter-freiburg|Plan de Ville et Chateaux de Fribourg/Grund=Riß der Stadt und Vestungen Freiburg|Matthäus Seutter|~1730|print|Kolorierter Kupferstich
seutter-breisach|Brisaci veteris/Alt Breysach (Plan und Ansicht Breisach)|Matthäus Seutter|~1730|print|Kolorierter Kupferstich
mayer-hufschmiede|Handwerkskundschaft der Freiburger Zünfte (hier: Hufschmiede) mit Stadtansicht|Peter Mayer|1786|print|Kupferstich
puettner-umgebung|Aus der Umgebung von Freiburg|Richard Püttner|1875|print|Kolorierter Holzstich
heuer-suggenthal|Suggenthal|Gustav Heuer/Gustav Kirmse, nach Max Roman|1901|print|Kolorierter Holzstich
philipp-schwabentor|Am Schwabentorplatz zu Freiburg im Breisgau|Helmuth Philipp|1967|print|Radierung
gruber-wegweiser|Entwurf für einen Wegweiser zum Seilbahn Restaurant Fritz Voegtlin|Ludwig Gruber|1932|watercolor|Aquarell
gruber-schauinsland|Schauinsland (Blick aus dem Fenster des Restaurants der Seilbahnstation)|Ludwig Gruber|1936|watercolor|Aquarell
gruber-osterhase|Osterhase im Schnee (Feldpostkarte)|Ludwig Gruber|1942|watercolor|Aquarell
gruber-jahreswechsel|Karikatur zum Jahreswechsel (Postkarte)|Ludwig Gruber|1942-1943|watercolor|Aquarell
meinig-schnee|Schwarzwaldlandschaft mit Schnee auf den Bergen|Walter Meinig|1953|watercolor|Aquarell
meinig-hof|Schwarzwaldlandschaft mit Hof und Blick auf den Feldberg|Walter Meinig|1954|watercolor|Aquarell
'''),('report2021',20,'''
kirner-kinder|Spielende Kinder|Johann Baptist Kirner|1838|painting|Gemälde
hoerr-frauen|Badende Frauen am Ufer eines Gewässers vor Ruinenkulisse|Joseph Hörr|1775|drawing|Federzeichnung
grandsire-himmelreich|Himmelreich (Forêt noire)|Pierre Eugène Grandsire|1840-1841|print|Kolorierter Holzstich
philippi-flamingos|Flamingos|Maria Philippi (Keramikerin)|~1953|print|Linolschnitt
schilbock-bruch|Schlupkothener Bruch (bei Wuppertal)|Ika Schilbock (Keramikerin)|1952|print|Linolschnitt
schilbock-lilie|Lilie|Ika Schilbock (Keramikerin)|1953|print|Linolschnitt
schilbock-schafgarbe|Schafgarbe|Ika Schilbock (Keramikerin)|~1953|print|Linolschnitt und Scherenschnitt
schilbock-toepfer|Töpfer mit Schüler an der Scheibe|Ika Schilbock (Keramikerin)|~1953|print|Linolschnitt
'''),('report2022current',18,'''
eisenlohr-selbst|Selbstbildnis als junger Mann|Friedrich Eisenlohr|~1825|drawing|Bleistiftzeichnung
gehri-speer|Männlicher Akt in Ausholbewegung zum Speerwurf|Hermann Gehri|1913|drawing|Graphitzeichnung
guiaud-muenster|Blick auf das Freiburger Münster durch die Münsterstraße mit Fischbrunnen|Jacques Guiaud|1844|watercolor|Aquarell
kirner-spinnrocken|Italienerin mit Spinnrocken und Kindern vor Gebirgslandschaft|Johann Baptist Kirner|1844|painting|Gemälde
kirner-schaefer|Schäfer mit Kind und Herde, daneben ein Hund|Johann Baptist Kirner|~1844|painting|Gemälde
kirner-strasse|Italienische Straßenszene mit Musikanten|Johann Baptist Kirner|1832-1837|drawing|Federzeichnung
kirner-mauer|Italienische Landschaft mit Gebäuden am Hang nah einer hohen Mauer|Johann Baptist Kirner|1832-1837|drawing|Federzeichnung
kirner-berghof|Hof eines italienischen Bergdorfes|Johann Baptist Kirner|1832-1837|drawing|Federzeichnung
morat-abbtei|Ansicht der ehemahligen Benedictiner Abbtei St: Trudpert im Münsterthal|Johann Martin Morat|~1842|painting|Gouache
morat-muensterthal|Ansicht des Münsterthals und Sankt Trudpert|Johann Martin Morat|~1842|painting|Gouache
morat-scharfenstein|Scharfenstein (Münstertal)|Johann Martin Morat|~1842|painting|Gouache
morat-felsen|Ansicht des Felsens, auf welchem das Habsburgische Schloss Scharfenstein gestanden|Johann Martin Morat|~1842|painting|Gouache
morat-staufen|Staufen (von Südosten mit Weinreben)|Johann Martin Morat|1840-1849|painting|Gouache
ramberg-venise|The merchant of Venise (Der Kaufmann von Venedig)|Johann Heinrich Ramberg|1787|drawing|Lavierte Federzeichnung
rose-jugend|Von Jugend auf die Freiburger Zeitung (Lachender Junge), Probedruck|Albert Rose|1920-1929|print|Farblithografie
'''),('report2022current',19,'''
rose-berichte|Noch rascher die Berichte – Noch reicher der Inhalt/Freiburger Zeitung (Zeitungsverkäufer und Telegraph)|Albert Rose|~1926|print|Farblithografie
rose-gesichtskreis|Die Freiburger Zeitung erweitert Ihren Gesichtskreis|Albert Rose|~1926|print|Farblithografie
rose-liegewiese|Mit der Schauinslandbahn auf die Liegewiese|Albert Rose|~1930|print|Farblithografie
rose-suedwestmark|Deutsche Südwestmark und 150 Jahre Freiburger Zeitung|Albert Rose|1934|print|Farblithografie
rose-scholle|Mit der Scholle verwachsen seit 150 Jahren. Freiburger Zeitung (Pflügender Bauer)|Albert Rose|1934|print|Farblithografie
rose-150|150 Jahre Freiburger Zeitung (Schriftplakat)|Albert Rose|1934|print|Farblithografie
rose-fasnet|Freiburger Fasnet (Taganrufer)|Albert Rose|1937|print|Farblithografie
rose-reisen|Gesellschaftsreisen der Freiburger Zeitung (Zug mit Reisenden), Plakatentwurf|Albert Rose|1930-1939|painting|Gouache
rose-menzenschwand|Sommer in Menzenschwand, 880-1400 Meter über dem Meeresspiegel, Plakatentwurf|Albert Rose|1930-1939|painting|Gouache
sandhaas-loretto|Die Loretto Kapelle zu Freiburg im Breisgau|Carl Sandhaas|~1820|print|Kreidelithografie
schreiber-munzingen|St. Martin, Munzingen|Guido Schreiber|1934|drawing|Feder, Kreide, Aquarell (Konvolutangabe)
schreiber-kirchzarten|Bei Kirchzarten|Guido Schreiber|1934|drawing|Feder, Kreide, Aquarell (Konvolutangabe)
schreiber-himmelreich|Im Himmelreich|Guido Schreiber|1934|drawing|Feder, Kreide, Aquarell (Konvolutangabe)
schreiber-berthold|Freiburg Brg. (Bertholdstraße nach Osten mit Universitätskirche)|Guido Schreiber|1945|drawing|Feder, Kreide, Aquarell (Konvolutangabe)
schreiber-rathaus|Freiburg (Brg). (Rathausplatz)|Guido Schreiber|1946|drawing|Feder, Kreide, Aquarell (Konvolutangabe)
schreiber-muenster|Freiburg (Münster inmitten Trümmern von Südwesten)|Guido Schreiber|1946|drawing|Feder, Kreide, Aquarell (Konvolutangabe)
schreiber-rathausgasse|Freiburg Brg. (Rathausgasse in Trümmern)|Guido Schreiber|1949|drawing|Feder, Kreide, Aquarell (Konvolutangabe)
wocher-maenner|Drei bärtige Männer in orientalischer Kleidung in Unterhaltung, der eine sitzend|Tiberius Wocher|1776|print|Radierung
'''),('report2022current',20,'''
jaquemot-rueckkehr|Rükkehr vom Badischen Landwirthschaftlichen Feste|Georges François Louis Jaquemot, nach J. B. Kirner|1849|print|Kupferstich mit historischem Rahmen aus Massivholz mit Vergoldung
rembrandt-kuh|Landschaft mit saufender Kuh|Rembrandt van Rijn|~1650|print|Radierung und Kaltnadel
vogel-georg|Porträt von Georg Himmelsbach|Hugo Vogel|1923|painting|Gemälde
biese-winter|Winter im Wald|Karl Biese|1903|drawing|Tempera über Bleistiftzeichnung
balder-kopf|Kopfbild Hermann Reich|Georg Balder|1840-1849|painting|Gemälde
balder-schulter|Schulterstück Hermann Reich|Georg Balder|1840-1849|painting|Gemälde
balder-familie|Familie Bernhard Reich|Georg Balder|1843|drawing|Teilaquarellierte Zeichnung
sandhaas-frau|Brustbild einer Frau mit Kopf- und Schultertuch|Carl Sandhaas|1830-1849|drawing|Zeichnung
sandhaas-mann|Brustbild eines Mannes mit Backenbart in schwarzem Rock|Carl Sandhaas|1830-1849|drawing|Zeichnung
schuster-gehoeft|Opfingen (Rückseite eines Gehöftes)|Karl Schuster|1924|watercolor|Aquarell
schuster-bach|Opfingen (Fachwerkhäuser am Bach)|Karl Schuster|1924|watercolor|Aquarell
schuster-hof|Opfingen (Bauernhaus mit Hof und angrenzenden Häusern)|Karl Schuster|1924|watercolor|Aquarell
baum-georg|Heiliger Georg zu Pferde als Drachentöter|Carl Baum|1938|print|Aquarellierte und übermalte Radierung
baum-reiter|Reiter in Lederhose vor Gebirgslandschaft|Carl Baum|1940|drawing|Zeichnung
baum-pferde|Pferde|Carl Baum|1950|painting|Gemälde
hofmann-maier|Ida Maier|Josefine Hofmann, geb. Maier|1885|painting|Gemälde
kirner-mueller|Miniaturbildnis Ida Müller, verh. Maier|Johann Baptist Kirner|~1843|watercolor|Aquarell
maier-siegel|Bildnis Sophie Lucia Siegel|Ida Maier|1848|drawing|Bleistiftzeichnung
'''),('report2023',18,'''
daumier-macaire|Robert Macaire Journaliste (aus Les Robert Macaires)|Honoré Daumier|1836-1838|print|Handkolorierte Lithografie
feuerbach-junger|Brustbild eines jungen Mannes im Profil nach links|Anselm Feuerbach|1849|painting|Gemälde
graessel-muehlenbach|Mühlenbacherin|Franz Xaver Gräßel|1892|painting|Gemälde
leiber-mann|Das Stufenalter des Mannes (Bilderbogen)|Ferdinand Leiber (Erfinder) / Gustav May Söhne (Verleger)|~1900|print|Chromolithografie
leiber-frau|Das Stufenalter der Frau (Bilderbogen)|Ferdinand Leiber (Erfinder) / Gustav May Söhne (Verleger)|~1900|print|Chromolithografie
morat-albbruck|Albbruck|Johann Martin Morat|1830-1850|painting|Gouache/Umrisslithografie
rose-ausstellung|Kunst Ausstellung Freiburg (Plakatentwurf)|Albert Rose|1934|drawing|Gouache/Bleistiftzeichnung
sandhaas-profil|Portrait eines Mannes im Dreiviertelprofil nach links|Carl Sandhaas|1830|drawing|Weiß gehöhte Bleistiftzeichnung
'''),('report2023',19,'''
vogel-emma|Porträt von Emma Himmelsbach|Hugo Vogel|1920-1929|painting|Gemälde
vogel-hermann|Porträt von Hermann Himmelsbach|Hugo Vogel|1920-1929|painting|Gemälde
lemire-greis|Greis betrachtet die Spiele der Jugend (Lukrez, Della natura delle cose, Buch 3)|Noël Le Mire (Kupferstecher/Radierer) / Charles-Nicolas Cochin (Inventor)|1754|print|Kupferstich und Radierung
lemire-fama|Allegorien der Malerei und der Fama|Noël Le Mire (Radierer) / Charles Eisen (Inventor)|1750-1800|print|Radierung
geyser-weisse|Portrait Christian Felix Weiße|Christian Gottlieb Geyser|1772|print|Kupferstich
chof-canopic|Kanope mit menschlichem Kopf im Kranz (Cul-de-Lampe, Voyage pittoresque, Band 1, zweiter Teil, Seite 146)|Pierre-Philippe Choffard (Kupferstecher) / Pierre-Adrien Pâris (Inventor)|1781|print|Kupferstich
cook-tailpiece|Tail Piece to the Artist’s Catalogue, 1761|Thomas Cook (Radierer/Stecher) / William Hogarth (Inventor)|1807|print|Radierung und Kupferstich
cook-time|To nature and your self appeal / Nor learn of others what to feel (The Time Smoking a Picture)|Thomas Cook (Radierer/Stecher) / William Hogarth (Inventor)|1809|print|Radierung und Kupferstich
'''),('report2023',20,'''
goltzius-curtius|Marcus Curtius zu Pferde (Römische Helden, Blatt 4)|Hendrick Goltzius|1586|print|Kupferstich
feuerbach-bacchisch|Bacchische Szene|Anselm Feuerbach|~1855|painting|Gemälde
hanemann-selbst|Selbstbildnis|Wilhelm Hanemann|1905|painting|Gemälde
hanemann-lotte|Bildnis Lotte Frank|Wilhelm Hanemann|1920|painting|Gemälde
hanemann-bluse|Frau mit weißblauer Bluse (Marie Hanemann?)|Wilhelm Hanemann|1919|painting|Gemälde
lugo-bach|Bach mit grüßendem Gnom|Emil Lugo|1887|drawing|Lavierte Federzeichnung
lugo-baumgruppe|Baumgruppe bei St. Salvator nah Prien am Chiemsee|Emil Lugo|1889|drawing|Federzeichnung
lugo-heimweg|Naechtlicher Heimweg|Emil Lugo|1895|drawing|Feder- und Pinselzeichnung
graf-droschke|Aus dem Bois de Boulogne (Elegantes Paar in Droschke)|Oskar Graf|1898|print|Vernis mou in Braun
'''),('report2024',31,'''
lang-frieden|Scheibenriss mit Wappenleerstelle und Allegorien des Friedens und des Gesetzes|Hans Caspar Lang d. Ä.|1594|drawing|Scheibenriss
ww-allianz|Scheibenriss einer runden Allianzscheibe mit Löwen- und Adlermotiv|Monogrammist WW|1596|drawing|Scheibenriss
sandhaas-josef|Josef Fidel Sandhaas (Schmied in Haslach)|Carl Sandhaas|1830-1839|watercolor|Aquarell
sandhaas-zaezilie|Zäzilie Sandhaas in Steinacher Tracht (Zweite Frau des Josef Fidel Sandhaas)|Carl Sandhaas|1830-1839|watercolor|Aquarell
sandhaas-karoline|Karoline Sandhaas (Tochter von Josef Fidel und Zäzilie Sandhaas)|Carl Sandhaas|1830-1839|watercolor|Aquarell
sandhaas-jugendlicher|Bildnis eines Jugendlichen|Carl Sandhaas|1831|watercolor|Aquarell
thoma-neptun|Zug des Neptun mit Nereide und Tritonen|Hans Thoma|~1880|drawing|Rötelzeichnung
thoma-exlibris|Exlibris Alice Koch - Frankfurt a. M.|Hans Thoma|1880|drawing|Federzeichnung
'''),('report2024',34,'''
duerr-leo|Porträt von Leo Blust|Marie Dürr-Grossmann|1884|painting|Gemälde
duerr-bertha|Porträt von Bertha Blust|Marie Dürr-Grossmann|1884|painting|Gemälde
zorn-burkheim|Burkheim|Ludwig Zorn|?|painting|Gemälde
zorn-donau|Junge Donau|Ludwig Zorn|1919|painting|Gemälde
zorn-feldberg|Feldberg im Winter|Ludwig Zorn|1903|painting|Gemälde
hagemann-holz|Holzschnitzer|Oskar Hagemann|1934|painting|Gemälde
schilling-caecilia|Santa Cäcilia|Franz Schilling|~1900|painting|Gemälde
hoch-italien|Italienische Landschaft|Franz Xaver Hoch|~1895|painting|Gemälde
thoma-blasien|Schwarzwaldpartie bei St. Blasien|Hans Thoma|1897|print|Ätzradierung
eisenlohr-vater|Porträt von Heinrich Eisenlohr (Vater der Künstlerin)|Eva Eisenlohr|1911|painting|Gemälde
eisenlohr-landschaft|Kleines Landschaftsbild|Eva Eisenlohr|?|painting|Gemälde
eisenlohr-halbakt|Halbakt im Freien|Eva Eisenlohr|~1913|painting|Gemälde
''')]
def sources():
 out={}
 for fn in ['native-discovery-001.json.gz','supplements-001.json.gz']:
  for v in m.load(RUN/fn)['rows']:
   if 'capture' in v and 'text' in v:out[v['key']]=dict(row=v,reference=ref(RUN/fn))
 return out
def date(code):
 if code=='?':return None,None,'unknown',None
 circa=code.startswith('~');ys=[int(v) for v in code.lstrip('~').split('-')];assert len(ys) in [1,2];a,b=ys[0],ys[-1];assert 100<=a<=b<=1970
 return a,b,('circa_range' if circa else 'range') if len(ys)==2 else ('circa' if circa else 'exact'),('um ' if circa else '')+'–'.join(map(str,ys))
def rows():
 src=sources();out=[]
 for key,pg,data in GROUPS:
  v=src[key]['row'];cap=v['capture'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert cap['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'];text=v['text'].split('\f')[pg-1]
  for line in data.strip().splitlines():
   nid,title,creator,dc,wt,medium=line.split('|');a,b,prec,display=date(dc);sid='augustiner/'+nid;issues=['unknown_creation_date_requires_review'] if a is None else [];note=f'Official {key} acquisition/gift list, PDF page {pg}, Augustinermuseum section. One individually named acquired physical artwork; accession date is not creation. '
   if wt=='print':note+='Museum impression only: no state/edition or lifetime-impression claim. Other institutions’ impressions are distinct physical objects. '
   if nid.startswith('schreiber-'):medium=None;note+='Media are listed collectively for the drawing group; exact medium of this individual drawing is not assigned. '
   if nid=='feuerbach-bacchisch':note+='Appendix specifies um1855; narrative PDF page4 instead1852/53 and public press leadc1853/54. Date conflict requires editorial hold, not silent preference. ';issues.append('creation_date_conflict')
   if nid=='graessel-muehlenbach':note+='Same title/maker/date repeated in2024p31; retained as one object, not two acquisitions.'
   if nid=='thoma-exlibris':note+='Original1880pen drawing only; separately mentioned1916reproduction is not this artwork.'
   if nid=='eisenlohr-landschaft':note+='Report explicitly not signed and not dated. Creator is source-attributed; no invented date.'
   f=dict(source_id=sid,native_id=nid,source_url=cap['receipt']['url']+'#page='+str(pg),source_retrieved_url=cap['receipt']['url'],title=title,titles=[title],creator_label=creator,identity_creator_labels=[creator],source_artist_fields=[creator],unidentified_creator=creator.startswith('Monogrammist'),source_fields={'ATTRIBUZIONI':creator,'museum_narrative':text,'editorial_note':note,'report':key,'pdf_page':pg,'date_literal':dc},inventory=None,normalized_inventory=None,alternative_inventories=[],date_display=display,first=a,last=b,date_precision=prec,work_type=wt,object_form=None,medium=medium,dimensions_text=None,description=text,physical_object_count='1',native_page_urls=[cap['receipt']['url']+'#page='+str(pg)],native_metadata_urls=[],artuk_url='',museum_qid=s.QID,issues=issues)
   out.append(dict(number=len(out)+1,source_id=sid,institution_id=s.IID,facts=f,issues=issues,version_note=note,source_capture=cap,source_record_reference=src[key]['reference'],retrieved_at=cap['receipt']['retrieved_at'],supplementary_source=[]))
 assert len({v['source_id'] for v in out})==len(out);return out,[]
def main():
 rs,holds=rows();m.save(RUN/'candidate-facts-001.json.gz',dict(at=m.now(),rows=rs,source_fact_holds=holds,parser_reference=ref(Path(__file__).resolve()),visual_review_reference=ref(RUN/'annual-report-visual-review-001.json'),policy='Selected individual art acquisitions only. Donors not creators. Qualified creator roles and title uncertainty retained. No unnamed groups,modern works,other museum sections,bulkillustration splitting or current display inference. Pending complete identity/version review.'));print(json.dumps(dict(candidates=len(rs),dated=sum(v['facts']['first'] is not None for v in rs))))
if __name__=='__main__':main()
