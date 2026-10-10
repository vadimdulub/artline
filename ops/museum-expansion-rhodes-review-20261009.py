"""Selected Rhodes physical artworks with edition, component and date qualifications."""
import collections,copy,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-rhodes-identity-v2-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);s=i.s;m=i.m;RUN=i.RUN;ref=s.ref;checked=s.checked
HOLDS={26:'Mallet Rhodes inventory4091 repeats the plate and narrative of selected4043; different dimensions alone do not settle separate impression versus duplicate documentation.',37:'Combined sheet4056 includes the harbour image selected as4030. Reconcile the whole sheet versus separately trimmed impression before adding a second representation.',67:'Catalogue1767 and specific edition1767 conflict with narrative publication range1776–1793. Edition/date identity needs clarification.',70:'Mallet Colossus4089 repeats selected4036. Separate impression versus duplicate documentation unresolved.',73:'Mayer4095 repeats selected4082 with identical narrative but larger dimensions. Verify separate impression rather than image/sheet measurement difference.',76:'Graecia4097 has circa1650 catalogue date but narrative identifies an Atlas Maior publication1662–1665. Physical edition unresolved.',84:'Le Brun4104 is potentially a further plate or impression of the Rhodes panorama represented by4070 and4105. Its boundary is less explicit; retain pending comparison.',105:'Soup-queue print4126 is dated1950 versus selected4124 dated1946. Shared series narrative and absent dimensions do not securely establish separate composition/impression.',115:'Demonstration4136 linocut has similar subject and date to4135; different dimensions may indicate another state/impression. Hold for visual/version reconciliation.'}
NOTES={
0:'Attica landscape1002 is the1948 tempera on paper,23×34.5cm. Other similarly titled Asteriadis landscapes remain distinct.',
2:'Lithograph4028 is a later copy of the Choiseul-Gouffier tower image, uncertain A.Lemonnier attribution; distinct from Weisbrod engraving4088. Source title names StNicholas while narrative identifies Naillac; retain that discrepancy.',
3:'Erotic Couple1003 is Arliotis1959 oil on cardboard,37×29cm.',
5:'Lithograph4029, qualified M.Podermans attribution, copies the1782 Kos-square image. The physical copy is early19th century, not the1782 prototype.',
6:'Harbour print4030 is plate106 of the1782 Choiseul-Gouffier publication, designed by Hilair and engraved by Varin. Combined sheet4056 remains held.',
7:'Patmos4031 is the1836 print designed by Harding after a Sinclair drawing and engraved by Finden, not a biblical-period object.',
8:'Rhodes4032 is the1833 Finden engraving after Turner/Page. Distinct from the original Turner drawing at Yale and later Duttenhofer version4092.',
9:'Rhodes4033 is the1856 Fischer print after Turner/Barry showing washerwomen; distinct from harbour composition4032. Posthumous publication date is retained.',
10:'StPeter rampart4034 is the1862 Trichon wood engraving after Flandins1844 drawing; the earlier drawing date does not date this impression.',
11:'Lero4035 is an1843 book illustration after Allan, distinct from his Rhodes-city plate4085 and the1841–1842 journey.',
13:'Colossus4036 is the historical print, not the lost ancient statue. Possible repeat4089 is held. Catalogue1683 and narrative citation1783 are preserved as conflicting date evidence.',
14:'Leros/Kalymnos/Kos4037 is one engraved map of three islands, not three artworks. Catalogue1683 and narrative citation1783 remain explicit.',
15:'Syros/Syrna/Paros4038 is one engraved map; catalogue1685 conflicts with narrative1785 citation. The erroneous depicted location of Syrna is part of the historical map.',
16:'Chios/Psara4039 is explicitly the German1686 impression, different from the French model; generic narrative citation1783 is retained as source inconsistency.',
17:'Skyros/Euboea4040 is one map, plate78/page177 of the European volume. Physical catalogue date1683 retained.',
18:'Samos4041 is explicitly the German1686 impression. The separate French-edition1783 citation does not replace its stated physical edition.',
19:'Karpathos4042 is a hand-coloured print, plate128/page289. Catalogue1683 and narrative1783 citation remain conflicting evidence.',
20:'Rhodes4043 is plate126/page285, not the island map4045 or Colossus4036. Possible repeat4091 is held; catalogue1683/narrative1783 conflict explicit.',
21:'Chios women4044 is a reversed German1686 impression based on an older Nicolay image. The1568 design is not its creation date.',
23:'Rhodes island map4045, plate125/page283, differs from the city-view4043. Catalogue1683 and narrative1783 citation retained.',
24:'Ikaria/Patmos4046 is explicitly the German1686 impression, one map with two islands, not the originalFrench edition.',
25:'Anonymous Colossus4047 is a1777or1778 print from the Middleton geography; ancient statue history does not date or identify its maker.',
27:'Anonymous map4048 is the1588 fifteenth Cosmographia edition, not the1544 first edition or an autograph by a named book illustrator.',
29:'Anonymous4049 is one1688 Dapper sheet with island map and city plan. Author Dapper is not asserted as engraver; no book-parent added.',
31:'Porro4051 is the1576 Karpathos book leaf/page118, distinct from Rhodes and Archipelago leaves.',
32:'Porro4052 is a later impression, probably1620, of the Rhodes leaf/page115. Distinct from the existing1576 Rhodes impression; the museum narrative qualifies the edition.',
33:'Anonymous4053 is a circa1880 reproduction of a Lindos view after Loffler. It is not the1865 model or the original travel drawing.',
34:'Anonymous4054 is an1857 Illustrated London News print of the1856 disaster; depicted event and object creation are separate.',
35:'Knights Street4055 is an1851 Wilmor engraving after Bartlett, not Witdoecks1828 view of the same street.',
38:'Roux4057 is a posthumous1804 harbour-map impression, not the1764 prototype or an original drawing.',
39:'Roux4058 is the separate1804 Astypalaia map, preserving the historical outline and soundings.',
40:'Roux4059 is the1804 Tilos harbour map, distinct from his Rhodes and Astypalaia maps.',
42:'Anonymous Nicosia4061 is the1713 Savonarola publication illustration after a1598 model. The author and earlier engraver are not asserted as its maker.',
43:'Tardieu4062 is an early19th-century map leaf of uncertain atlas origin. Retain the broad century envelope and qualifier.',
44:'Kastellos4063 is a1941 costume lithograph after Tarsouli with lithographic adaptation/execution by Grammatopoulos; one plate, distinct from Chalki/Tilos.',
45:'Chalki4064 is a1941 costume lithograph after Tarsouli, executed/adapted by Grammatopoulos; not an original painting.',
46:'Tilos costume4065 is a1941 lithograph after Tarsouli with Grammatopoulos lithographic contribution, distinct from the other costume plates.',
47:'Chios4066 is an1878 published wood engraving after Testevuide with Weber credit;1877 refers to the travel account, not this print.',
48:'Rhodes4092 is the circa1840 Duttenhofer engraving after the Turner/Page harbour design, distinct from1833 Finden4032 and Yale original drawing.',
49:'Weigel4067 is a circa1720 map of Ottoman European territories, one map including its decorative figures.',
50:'Anonymous Famagusta4068 retains the museums circa1595 date. The narrative contains inconsistent dates for the supposed book author, so that author is not converted into a maker or a firm publication claim.',
51:'Anonymous Cyprus4069 is a1588 Cosmographia edition woodcut after earlier mapping; not the1544 edition or a Pagani autograph.',
52:'Le Brun4070 is the1714 eastern-harbour panorama with Naillac tower at the left. Distinct from4105 with the western mole and tower at right; no complete panorama parent added.',
53:'Picquet4071 is an1853 map publication using an earlier cartographers work; creator lifespan does not override its physical edition date.',
54:'Knights Street4072 is one1828 lithograph after Witdoeck, Van Genk credit; separate from the later Bartlett view4055.',
55:'City in view4073 is an1828 Witdoeck/Van den Kerchhoven lithograph with ships and windmills, one plate from Monumens de Rhodes.',
56:'Approach4074 is a separate1828 Witdoeck/Van den Kerchhoven lithograph showing a Dutch-flagged ship and the island from the sea.',
57:'Colossus site4075 is an1828 Witdoeck/Montius lithograph of the traditionally supposed location. It does not establish the statues actual ancient position.',
58:'Coast4076 is a separate1828 Witdoeck/Van den Kerchhoven lithograph from Monumens de Rhodes, not the1830 text volume.',
59:'StNicholas4077 is an1828 Witdoeck/Delpierre lithograph of the fort; its15th-century construction is not the print date.',
60:'Anchored4078 is one1828 lithographic sheet by Van den Kerchhoven after Witdoeck. It combines geographically with4079/4080, which are separately inventoried plates; no larger parent artwork added.',
61:'City left4079 is a separate1828 sheet within the linked three-view panorama,24×31.7cm, not a crop of4078.',
62:'Continuation4080 is a separate1828 Witdoeck/Verbeyst lithographic plate,24×32.5cm, with the coast beyond the walls. It is not counted as a complete panorama.',
63:'Hassan Bey palace4081 is an1822 posthumous print after Cooper Willyams, with Stadler credit; not an original drawing or the earlier1796 book.',
64:'Mayer4082 is a print of the Lindos rock-cut colonnade from the1802–1805 publication. Possible repeat4095 held; not the1792 travel drawing.',
65:'Anonymous4083 is one1688 Dapper sheet with three related city representations. The images are not three artworks, and no complete book parent is added.',
66:'Allan4085 is the1843 Rhodes-city plate, distinct from Lero4035. Retain the sources incomplete title bracket without silently expanding it.',
69:'Weisbrod4088 is a separately engraved early19th-century copy of the tower image,26×38.5cm, distinct from Lemonnier lithograph4028. Source title and narrative identify different tower names.',
71:'Deroy4093 is the1863 Monde Illustre wood engraving after Spoll, published after the earthquake; source calendar-day discrepancies retained, no day precision inferred.',
72:'Salmon/Buckle4094 is the1840 harbour print after a Bartlett design, distinct from Turner/Finden and other harbour views.',
74:'Semertzidis5037 is the1967 ink-and-marker drawing,50×70cm. The portal groups it under painting, but its object narrative and medium identify a drawing.',
75:'Bartlett/Wallis4096 is the view from Monte Smith. Catalogue1841 and narrative1841–1842 publication range retained together.',
77:'Ortelius4098 is probably the1584 edition, not the1570 first atlas or the earlier Gastaldi model. Preserve the narrative edition qualification.',
78:'Graecia vetus4099 credits Vaugondy design and Elisabeth Haussard engraving. Plate inscription1752 and cited1757 Atlas Universel edition both remain explicit physical-date evidence.',
79:'Homann4100 is the1710 historical map, whose label credits father and son as designers. Preserve literal credit and evidence rather than infer a new authority attribution.',
80:'Speed4101 is the1627 Greece map, one sheet with cartouches, not an earlier Ortelius model.',
81:'Blaeu4102 is probably from the1640–1643 Latin edition; catalogue1640 retained in evidence and the narrative range/qualification remain explicit.',
82:'Semertzidis4138 is the1948 flute composition study, distinct from the explicitly reversed and revised1950 print4139 and the monumental oil in a private collection.',
83:'Wells4103 is the1712 printed map, not the1701 first atlas. The narrative only tentatively names John Smith as engraver; retain that qualification.',
85:'Le Brun4105 is the1714 western-mole panorama with Naillac tower at the right, distinct from4070 with tower at left. Potential4104 plate remains held.',
86:'Bartlett/Adlard4106 depicts Kastellorizo. Catalogue1841 and narrative1837 volume date conflict; retain1837–1841 as evidence interval, without selecting one edition.',
96:'Engonopoulos1200 is the1957 oil Orpheus,91×72cm, cello player in a red room; different Orpheus versions and dates require comparison.',
103:'Semertzidis4124 is the1946 soup-queue print, one of four separately inventoried occupation scenes. Shared group description does not create a parent artwork. The1950 same-title4126 is held.',
104:'Semertzidis4125 is the1946 hungry-child print, distinct from plural-child4127; dimensions are unknown, not invented.',
106:'Semertzidis4127 is the1946 hungry-children print, distinct from singular-child4125 and the queue subjects. Unknown dimensions retained.',
107:'Two Shepherds4128 is a1948 monotype,60×47cm, a separate preparatory study for the flute composition, not a crop of its finished canvas.',
108:'Shepherd4129 is a1948 print,46×38cm, different from the1944 tempera portrait mentioned in the narrative.',
109:'Pensive4130 is a1946 monotype,12.5×10cm; possible study for Peoples Court remains tentative, not a duplicate finished painting.',
110:'Partisan4131 is a1946 small print study,20×13cm, distinct from the large1946 Benaki oil and the earlier mountain drawing.',
111:'Ploughing4132 is a1946 linocut,46×59cm; the related Meletzis photograph is a separate work and does not supply authorship.',
112:'Argithea Gorge4133 is the circa1946 linocut,74×53cm; other studies and variants mentioned in the narrative are not added.',
113:'Mountains of Roumeli4134 is a1946 linocut with foreground trees, distinct from the specific Argithea Gorge4133 composition.',
114:'Demonstration4135 is the1946 linocut,20×28cm; the closely related square linocut4136 is held. Large etching4137 has a separate technique and size.',
116:'Demonstration4137 is the large1946 etching,34.5×63cm, distinct from the small linocut4135. Slogans and figures remain within one artwork.',
117:'Flute4139 is the1950 print: the source explicitly distinguishes its reversed composition and added spinning woman from1948 print4138 and the monumental oil.',
118:'Vlacha head4140 is a1947 etched study,40×35cm, a separate physical work for the flute composition, not an extracted digital detail.'}
CONFLICT_DATES={13:(1683,1783),14:(1683,1783),15:(1685,1785),19:(1683,1783),20:(1683,1783),23:(1683,1783),75:(1841,1842),78:(1752,1757),86:(1837,1841)}
def build():
 x=m.load(RUN/'production-identity-002.json.gz');assert x['rows']==i.f.rows();out=[]
 for row,c in zip(x['rows'],x['comparisons']):
  d=copy.deepcopy(row);d['comparison']=copy.deepcopy(c);f=d['facts'];n=d['number'];state=d['metadata_state'];note=''
  if c['source_hits']:state='already_catalogued';note='Existing exact native/SearchCulture object identity; no duplicate or metadata rewrite.'
  elif state=='outside_creation_scope':note='Explicit physical creation after1970; excluded from this addition.'
  elif state=='unknown_date_review_deferred':note='No dedicated creation date. Retain lead for individual scope/version review; no inferred year or quota placeholder.'
  elif n in HOLDS:state='editorial_version_or_date_hold';note=HOLDS[n]
  else:
   assert n in NOTES,n;state='approved_review_only_addition';note=NOTES[n];f['description_md']=note
   if n in CONFLICT_DATES:
    f['first'],f['last']=CONFLICT_DATES[n];f['date_precision']='range';f['date_display']=f"{f['first']}–{f['last']} (museum date evidence; see note)"
   if n in [32,77]:f['date_precision']='circa';f['date_display']='Probably '+f['date_display']+' (museum edition attribution)'
   if n==81:f.update(first=1640,last=1643,date_precision='circa_range',date_display='Probably 1640–1643 (museum edition attribution; catalogue1640)')
   if n in [44,45,46]:f['creator_label']='Αθηνά Ταρσούλη (σχέδιο), Κώστας Γραμματόπουλος (λιθογραφική προσαρμογή και εκτέλεση)'
   if n==74:f['work_type']='drawing'
  d['comparison_assessment']='See protected subject comparator assessment; source IDs, creators, physical versions and dates compared. Same title alone is not identity.';d.update(state=state,institution_id=s.IID,basis=note,confidence=.95 if state=='approved_review_only_addition'else None,limitation='Editorial confidence, not calibrated probability. Collection holding only, no current display, venue, custody or ownership claim. Literal source labels and conflicts preserved in evidence. No image or artist-authority attachment.');out.append(d)
 return out
if __name__=='__main__':
 ds=build();deps=[RUN/v for v in ['candidate-facts-001.json.gz','production-identity-002.json.gz','production-identity-citations-001.json.gz','production-initial-scope-001.json.gz','native-sample-001.json.gz','native-selection-001.json.gz','institution-reconciliation-001.json','subject-comparators-001.json.gz']];m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=ds,dependencies=[ref(v)for v in deps],reviewer_reference=ref(Path(__file__).resolve()),policy='Only reviewed selected physical artworks; retain explicit creator/date qualifications, shared-series boundaries and uncertain editions. Local catalogue read-only.'));print(json.dumps(dict(states=dict(collections.Counter(v['state']for v in ds)))),flush=True)
