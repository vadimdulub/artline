#!/usr/bin/env python3
"""Individual decisions for the bounded 88-page Russell-Cotes follow-up."""
import collections,copy,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-russell-followup-research-20261007.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n);prior=n.prior;w=n.w;m=n.m;RUN=n.RUN
NOTES={
'sita':'One1880–1920 painted-marble murti, :135.26.82, with unknown sculptor. Tentative northern-India origin remains narrative only. Existing Jamini Roy Sita is V&A O82552/IS.49-1979, explicitly an opaque-watercolour painting on cardboard, not this sculpture.',
'princess-alexandra':'Native1872 marble SC64b by Prosper d’Epinay is distinct from Junck’s SC64a. Keep its literal caption name. The page does not securely specify this object’s exact physical type, so retain unknown rather than infer a bust from the artist’s biography.',
'victoria-princess-royal-1840-1901':'Native1858 marble bust SC64a by Ferdinand Junck. Sitter identification is explicitly likely. Existing same-title1858 Royal Collection RCIN407449 is a separate painting, documented by refreshed Q28017814, not this sculpture; preserve the older imported creator unchanged.',
'sir-henry-irving-study-for-the-golden-jubilee-picture':'Native1887 oil study BORGM01330 is a separate physical study, not the finished Golden Jubilee Picture or a full-event aggregate. Retain source Lockhard spelling; Lockhart creator variants were searched without adding an artist link.',
'sara-bernhardt-2':'Native1897 woodblock print :T8.8.2005.26 is the signed/dedicated museum impression. The1872–1949 Nicholson is distinguished from the older namesake1781–1844. Caption sitter1824–1923 remains source evidence and does not supply the print date. No edition size or printing state is invented.',
'ellen-terry-as-lady-macbeth':'Native1889 Batley etching BORGM00239 is the signed print, distinct from Sargent’s same-title1889 oil painting N02053. The1888 theatrical opening is not used as print creation. Medium is absent from the compact caption but the narrative explicitly identifies an etching.',
'the-sale-room-at-christies':'Native1905 Sidney Paget ink drawing :T9.1.2001.1 was produced for The Sphere. Count the drawing, not a newspaper issue or the Archer painting depicted in it. The1905 auction is corroborating context, not a substituted creation date.',
'the-bells':'Native1874 chromolithograph :T8.8.2005.9 is the inventoried print from Vanity Fair19December1874. Narrative says attributed to Carlo Pellegrini; preserve that qualification. Ilmari Aalto and Khnopff same-title records are different creators and physical works.',
'sir-henry-irving-as-beckett':'Native1890–1905 watercolor BORGM00723 retains its exact range and source Beckett spelling. The actor’s final role and death do not supply a guessed creation year. Duncan’s five existing artist-scoped records depict other subjects.',
'christ-pantocrator':'One Russian Orthodox icon RC186 with unknown attribution; explicit late19th-century date retains literal qualifier with enclosing1800–1899 bounds. The1898 Russian trip is acquisition context. Existing unknown-date Apsida13562 is a1503 ceiling wall painting at Saint Neophytos in Cyprus, not this portable wood/silver-gilt/enamel icon. Other exact-title records identify a Byzantine mosaic, Moskos1653 and Icon Museum L2023.2. Do not count the three icons mentioned in the historical letter as three records.',
'suspicion-a-maori-chief':'Goldie’s1906 oil-on-board BORGM00900 has an unidentified sitter. It is separate from the named Harata and Te Aho oil canvases BORGM00899/00901. Retain the native Māori title and unknown sitter, with no new artist profile or inferred ethnicity field.',
'a-maori-chieftainess':'Goldie’s1906 Harata Rewiri Tarapata oil canvas BORGM00899 is distinct from the other two selected portraits. The sitter’s1831–1913 lifespan and1840 treaty history are not creation dates. Source tribal/taonga context remains verbatim evidence.',
'te-aho-te-rangi-wharepu':'Goldie’s1907 oil canvas BORGM00901. The title’s1811–1910 sitter lifespan is separate; source approximate sitter-age narrative is not converted into another creation year. No claim that all Goldie portraits of this recurring sitter are one object.',
'the-crater-of-kilauea-island-of-hawaii':'Tavernier’s1885 oil canvas BORGM02088 is explicitly painted for the Russell-Cotes visit. It differs from Furneaux’s1883 crater BORGM00786 and1880–1881 lava painting BORGM00785 already added. Shared volcanic subjects and spelling variants do not merge them.',
'brother-of-the-artist':'Walker’scirca1930 bronze bust SC99 BORGM is explicitly of his brother. The current catalogue pool has other named sitter portraits and a studio scene. Preserve circa without fabricated bounds, and preserve the literal inventory’s trailing museum prefix.',
'an-italian-girls-head':'Godward’s1902 oil canvas BORGM00895 is distinct from his1898 Ethel BORGM00894 and existing1895 A Lady1496. All15 current creator-scoped works were compared; generic depictions of classical women alone are not duplicate identities.',
'an-autumn-idyl':'Grimshaw’s1885 urban autumn scene BORGM00934 is distinct from the existing1871 Dame Autumn and other named nocturnes. Existing exact-title An autumn idyll1974-0003-2 is by W.Paul Davis,1891. Preserve native heading Idyl and caption Idyll spellings in evidence.',
'ehrenbreitstein-from-coblenz-on-the-rhine':'Pyne’s1864 Rhine canvas BORGM01778 is distinct from his seven current creator-scoped British scenes. Turner’s influence and other paintings listed in the biography are not alternate identities or creation dates.',
'the-dawn-of-love':'Etty’s1828 oil-on-canvas-on-panel BORGM00768 has the documented original title Venus now wakes and wakens love and1828 exhibition. The33 creator-scoped records and exact-title1846 Thomas Brooks FA.241[O] do not identify this composition. Generic Etty nude studies remain separate unresolved objects; no such older record is changed.',
'a-wood-nymph':'Poetzelberger’s1886 oil panel BORGM01749. Native narrative uses Pötzelberger; both spellings were included in authority/unlinked searches. The1897 Secession and biography do not date this1886 object.',
'le-premier-ne-the-first-born':'Dyckmans’s1881 oil panel BORGM1994.52 is supported by the source’s object-specific1881 exhibition letter. The9 current creator-scoped records cover different titles and subjects. The1994 accession suffix is not a creation date.',
}
HOLDS={
'sir-frederick-leighton':'Caption1892 conflicts with narrative that small casts derive from the memorial after Leighton’s death; actual bronze casting date needs resolution.',
'lady-russell-cotes':'Probably Mossman attribution with circa1900 object date after stated1890 death requires copy/cast/attribution review.',
'blossoms':'Explicit copy after Moore’s1881 Tate original; the caption may describe prototype date rather than this commissioned copy.',
'woman-playing-a-lyre':'Caption1890 versus tentative Paris-period production and stated1900 move require date/biography reconciliation.',
'proserpine':'Source repeats a biography that attributes1898 Closing Era to Powers despite1873 death; confirm physical version and attribution before selection.',
'empress-eugenie-of-france':'Reduced copy by Winterhalter is distinct from original but same-sitter versions and physical copy date need a dedicated comparison.',
}

def reviewed_facts(row):
    f=copy.deepcopy(row['facts']);f.update(object_form=None,cultural_context=None)
    if f['source_id']=='the-bells':f['creator_label']='Attributed to Carlo Pellegrini'
    if f['source_id']=='princess-alexandra':f['work_type']='unknown'
    if f['source_id']=='christ-pantocrator':f.update(work_type='unknown',object_form='icon',cultural_context='Russian Orthodox Church')
    return f

def main():
    candidates=m.load(RUN/'native-candidates-003.json.gz');comps={r['source_id']:r for r in m.load(RUN/'native-comparisons-003.json.gz')['records']};rows=[]
    assert len(NOTES)==21 and set(NOTES)<=set(comps)
    for r in candidates['rows']:
        source=r['source_id'];d=dict(source_id=source,source_reference=r['source_reference'])
        if source in NOTES:
            assert r['state']=='candidate';c=comps[source];assert not c['inventory_hits'] and not c['source_hits'];page=w.checked_native_page(r['source_reference']);assert n.source_facts(page)==r['facts']
            d.update(state='approved_review_only_addition',confidence=0.95,facts=reviewed_facts(r),comparison=c,identity_note=NOTES[source],limitation='Editorial confidence, not calibrated. Native collection attribution is distinct from ownership, custody and current display. No image or publication approval; missing dimensions and unknown fields remain unknown.')
        elif source in HOLDS:d.update(state='hold_identity_or_source',reason=HOLDS[source])
        elif r['state']=='candidate':d.update(state='deferred_after_target',reason='Research candidate retained; no addition approved in this21-work target batch. Requires final identity/version review before any future addition.')
        else:d.update(state=r['state'],reason=r['reason'])
        rows.append(d)
    m.save(RUN/'native-editorial-002.json.gz',dict(at=m.now(),decisions=rows,selected_source_ids=sorted(NOTES),counts=dict(collections.Counter(r['state'] for r in rows)),source_review='Full selected narratives, relevant creator pools and all39 exact-title records individually reviewed. Source conflicts are retained; source pages are not automatic import approval.'))
    print(collections.Counter(r['state'] for r in rows))
if __name__=='__main__':main()
