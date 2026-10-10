"""Object, date, role and image decisions after153 authentic frames and nine sheets."""
import collections,csv,hashlib,importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-jewish-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
dates=c.module('dates','museum-expansion-jewish-dates-20261010.py')
MERGED={1021:[1021,1023],1038:[1038,1039],1195:[1195,1194]}
TITLES={44:'Moses with the Ten Commandments',46:'Landscape with houses and hills',48:'Composition with men and animals',71:'A street in Bethlehem',74:"Aaron’s tomb, Mount Hor",75:"Absalom’s tomb, near Jerusalem",76:'Cave of the School of the Prophets, Mount Carmel',77:'Djebel Sheich and Mount Hermon',79:'The plain of the Jordan and the Dead Sea',80:'The valley of Jehoshaphat and Brook Kedron',82:'Map of Judea, Samaria and Galilee',86:'Lady of Ioannina at the time of Ali Pasha',87:'Lake of Tiberias or the Sea of Galilee',144:'Liturgy on the banks of the Jordan',145:'Mount Carmel, looking towards the sea',147:'The Dead Sea',153:'The Mount of Olives',154:'Jerusalem in the seventeenth century (depicted period)',155:'The city of Nazareth',156:'The ford of the Kishon and the bay of Acre',157:'Three porters at Thessaloniki',158:'Jerusalem from the Mount of Olives',159:'Washing of feet in Jerusalem',173:'Woman in Sephardic costume',175:'The mosque over the graves of Abraham and the patriarchs',185:'Sketch of a girl',187:'The Gulf of Salonika — folding illustrated card',192:'Moses seated with the Tablets of the Law',1195:'Huppah — cherry-red embroidered marriage canopy'}

def main():
    dest=RUN/'editorial-source-decisions-001.json.gz';assert not dest.exists()
    rows=m.load(RUN/'selected-source-records-002.json.gz')['rows'];visual=m.load(RUN/'visual-references-001.json');frames={x['number']:x for x in visual['rows']};assert len(frames)==153 and not visual['unavailable']
    out=[]
    for row in rows:
        n=row['number'];f=row['fields'];decision=row['decision'];notes=[];first=last=None;precision='unknown';display='Creation date unknown';kind='unknown';creator=(f.get('Δημιουργός') or [None])[0];creator=None if creator in ['N/A','Unknown','-'] else creator;title=TITLES.get(n,f['Τίτλος'][0]);native=row.get('native',{});dimensions=native.get('format_literal');dimensions=None if dimensions in ['-','No measurements available','No measurements'] else dimensions
        if decision=='visual_review_candidate':
            first,last,precision,display,note=dates.date(row);notes.append(note);decision='proposed_review_artwork'
            kind='textile' if n>=1001 else 'painting' if n in [44,48] else 'watercolor' if n==46 else 'drawing' if n in [173,185] else 'sculpture' if n==192 else 'print'
            if n==1043:kind='metalwork';notes.append('One cloth belt with multiple silver dedicatory plaques, catalogued as a single composite object, not one artwork per plaque.')
            if n==1072:decision='scope_hold';notes.append('Only a roll of cream lace on a bobbin is visible; finished decorative work versus craft material is unresolved. No artwork added solely to increase count.')
            if n==1117:decision='identity_hold';notes.append('Very close match to1116: same description,40x54cm dimensions and nearidentical embroidery. Different nativefilename tokens84.124/84.125 are insufficient on their own to settle separatephysicalobjects versus rephotography/rotation. Keep1117held; notassertedmerged or deleted.')
            if n in [1023,1039,1194]:decision='merged_source_view'
            if creator:creator+=' (museum creator label; role not independently resolved)'
            if n in [71,144,147,157,159]:creator='Gillot (source label; printing or engraving role unresolved)';notes.append('The database alias Gillot points to Claude Gillot. No evidence identifies this late19thcentury print label with thatartist; do notcreate a falseartistlink.')
            if n in [1003,1018]:notes.append('Dr.AbrahamElijahdeCastro appears in sourcecreatorfield. Maker versus collector/donor role unresolved; noartistrecord orbiographycreated.')
            if n in [76]:notes.append('Museum1811 conflicts with the stated W.H.Bartlett attribution and official1809birth. Comparator1838/1841editions do not date thisphysicalimpression. Source1811preserved, actualdateNULL.')
            if n==154:notes.append('Seventeenthcentury is also the explicitlydepicted city period; waxed-cardboardmounted impression date remains unknown. Noimageageapproval.')
            if n in [1038,1039,1063,1115]:notes.append('Source1940/1945/1904 is labelledDedication, notCreate. Earliercloth, inscription and laterassembly maydiffer. Preserveas evidence, do notmakeanexactcreationyear.')
            if n in [1021,1023]:notes.append('Matching nativefiletoken80.135,525x370mm dimensions andexact composition establish one uncut embroideredslipperpanel acrossTextiles andDomesticArtifacts. BothsourceIDs retained.')
            if n in [1038,1039]:notes.append('Matching98.40filetoken,45.8x87.9cm measurements, dedicatoryinscription anddamage establish rephotographs ofonecurtainpanel.')
            if n in [1194,1195]:notes.append('Matching2005.37filetoken and249x245cm dimensions, sourcecanopydescription andvisiblecentralhole establishonehuppah:1194liningdetail,1195decoratedfront.1195chosenprimary.1196indexlead retainedforfuturecomparison; noextraartwork.')
            if n in [1025,1087,1088]:notes.append('Focusedcomparison showsdifferentcentralinscriptions, motifs, borders, proportions anddamage; similarstyle alone isnota duplicate.')
            if n in [1049,1050,1051,1052,1061,1120,1121,1122]:notes.append('Distinct namedphysicaltextiles withdifferentdimensions/shapes or motifs, preservingfullfilename componenttokens. Sharedprovenance does not automaticallymake them one physical object.')
            if n in [1026,1035,1049,1051,1052,1057,1074,1079,1081]:notes.append('Sourcephotograph showsfoldedtextile or partial/detail view. Complete suppliedimage retained, notdescribedas a completeunfoldedartwork.')
        if decision=='external_collection_hold':notes.append('Object-levelsubcollection identifiesMunicipalityMuseumofIoannina/SocietyforEpiroticStudies. JMGprovider/sourcecopyright doesnot establish JMGholding. No newJMGartworkorholding.')
        if decision=='photographic_surrogate_hold':notes.append('Archive photograph ofanartwork/building; picturedprototype date, creator orlocationdoes notestablish actualphotographcreation or originalworkholding. Noautomaticartworkduplication.')
        if decision=='post1970_depicted_event_hold':notes.append('Descriptionexplicitlyconcerns the1972Munichathletes murders; broad20thcenturyindexdoesnotestablishpre1971creation.')
        if decision=='unresolved_date_or_version_lead':notes.append('Capturedmetadata lead retained fordate, attribution andphysicalversionresearch; broadcenturyrange notautomaticallypre1971.')
        if decision=='existing_comparator':notes.append('Preserveexistingtitle,date,creator,media,status,sourceidentity andholdings unchanged. Existingmedal203sourcechronologyversus photographedpendant manufacture merits laterobject-levelreview; no silentchange.')
        notes+=['Museumholding isnot currentdisplay. SourceURL/filetokens are notverifiedaccessionnumbers. Originalunknownmaker andqualifieddating remain explicit.','All153selectedauthenticimages viewed on7contact sheets, plus twofocusedcomparison sheets. No images for11externalcollectionrecords,74photographicsurrogates,71otherunresolvedleads or1972cartoons.']
        medium=None
        if n==44:medium='Oil on canvas'
        elif n==46:medium='Watercolour and ink on cardboard'
        elif n==48:medium='Tempera on canvas'
        elif n in [173]:medium='Ink on paper'
        elif n==192:medium='Copper alloy on wooden base'
        elif n==154:medium='Engraving on waxed cardboard (museum description)'
        elif kind=='print':medium='Print on paper (museum description)'
        candidate=decision=='proposed_review_artwork' and first is not None and last<=1955
        out.append(dict(number=n,source_id=row['source_id'],source_url=row['source_url'],title=title,title_source_literals=f['Τίτλος'],creator_label=creator,creator_source_literals=f.get('Δημιουργός',[]),artist_id=None,first=first,last=last,date_precision=precision,date_display=display,source_date_literal=f.get('Ημερομηνία',[]),source_chronology=row['enrichment'].get('Χρονολογία',[]),work_type=kind,medium_text=medium,dimensions_text=dimensions,inventory=None,object_form=None,cultural_context=None,description_source=f.get('Περιγραφή',[]),decision=decision,source_numbers=MERGED.get(n,[n]),review_notes=notes,source_fields=f,aggregator_enrichment=row['enrichment'],native=native,creator_authorities=row['field_enrichment_links'].get('Δημιουργός',[]),source_receipt=row['receipt'],visual_reference=frames.get(n),source_image_reviewed=n in frames,image_candidate=candidate,image_hold_reason=None if candidate else 'Existingcomparator/mergedview/heldscope or creationafter1955/unknown/crossingdate.',date_scope_review_required=first is None or (last or 0)>1970,proposed_status='review',ready_to_apply=False,applied=False))
    selected=[x for x in out if x['decision']=='proposed_review_artwork'];counts=dict(metadata=len(rows),old=8,proposed=len(selected),source_records=sum(len(x['source_numbers']) for x in selected),numeric_date_eligible=sum(x['first'] is not None and x['last']<=1970 for x in selected),unknown_dates=sum(x['first'] is None for x in selected),crossing_dates=sum(x['first'] is not None and x['last']>1970 for x in selected),image_candidates=sum(x['image_candidate'] for x in selected),decisions=dict(collections.Counter(x['decision'] for x in out)))
    assert counts['proposed']==140 and counts['source_records']==143 and counts['image_candidates']==131 and counts['numeric_date_eligible']==134
    m.save(dest,dict(at=m.now(),rows=out,counts=counts,dependencies=[c.ref(RUN/f) for f in ['selected-source-records-002.json.gz','visual-references-001.json','production-identity-001.json.gz','production-identity-citations-001.json.gz','focused-date-context-001.json.gz']],focused_visuals=[dict(path=str(c.PROOF/(n+'.jpg')),sha256=hashlib.sha256((c.PROOF/(n+'.jpg')).read_bytes()).hexdigest()) for n in ['duplicate-review','similar-cushions']],script_reference=c.ref(Path(__file__).resolve()),date_parser_reference=c.ref(Path(__file__).with_name('museum-expansion-jewish-dates-20261010.py'))))
    with (RUN/'candidate-review-001.csv').open('x',encoding='utf-8-sig',newline='') as h:
        w=csv.DictWriter(h,fieldnames=['number','source_id','title','creator_label','first','last','date_display','work_type','decision','image_candidate','source_url'],extrasaction='ignore');w.writeheader();w.writerows(out)
    print(json.dumps(counts),flush=True)

if __name__=='__main__':main()
