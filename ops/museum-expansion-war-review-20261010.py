"""Item-level creation, version, medium and composition decisions after visual review."""
import collections,csv,importlib.util,json,re
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-war-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
SCOPE={10:'Uniform/political badge; no selected fine/decorative-art case established.',11:'Tactical battle diagram; no selected artistic-work case established.',44:'Tactical battle diagram; no selected artistic-work case established.',53:'Military commissioning pennant; no selected artistic-work case established.'}
HOLDS={31:'Title describes moving artillery; supplied image depicts a doorway and standing guard. Object/image identity unresolved.',65:'Title specifies artillery; supplied image shows two walking soldiers, one supported by the other. Source image/title association needs reconciliation.',71:'Title specifies surgery; supplied image shows an active battle with charging/fallen figures. Source image/title association needs reconciliation.',81:'Title specifies a meal; supplied image shows a long pack-animal convoy. Source image/title association needs reconciliation.',103:'One of three similarly titled Gerontas studies; all three image responses empty. Physical study/detail units cannot yet be reconciled.',104:'One of three similarly titled Gerontas studies; all three image responses empty. Named maker retained in research; physical study/detail units cannot yet be reconciled.',105:'One of three similarly titled Gerontas studies; all three image responses empty. Physical study/detail units cannot yet be reconciled.',123:'Title describes Otto; supplied image is a female portrait. Source object/image mismatch; do not relabel the woman or attach this image.',132:'Four photographs shown together under a plural collection label. Physical album/composite versus four separate objects is unresolved; do not inflate artwork count.',135:'Named Lord Byron portrait and supplied uniformed portrait require sitter/version corroboration; image alone does not resolve the identity.',169:'Source calls the three-dimensional Constantine bust a work by painter Thalia Flora-Karavia. Creator/object association unresolved; no automatic painter link.'}
DATE_CONFLICT={25:'Source creation field:20thcentury; description:Coronelli1690–1694. Plate/prototype versus actual impression/copy unresolved.',91:'Source creation field:20th–21stcentury; caption names an old Sanson map. Actual impression/reproduction creation unresolved.',150:'Source creation field:19th–20thcentury; caption names Jansson. Actual impression/reproduction creation unresolved.',163:'Source creation field:20thcentury; caption names VanKeulen. Actual impression/reproduction creation unresolved.'}
EVENT={121:'1919 describes the sitter office in the caption and repeats in the creation field; independent execution date is unresolved.',189:'1917–1918 identifies the commemorated conflict; actual medal manufacture date unresolved.',190:'1941–1945 identifies the commemorated campaign; actual medal manufacture date unresolved.',194:'1915 may identify the order/design rather than manufacture of this example; actual execution date unresolved.',195:'1914 identifies AutonomousEpirus; manufacture of this example remains unresolved.'}
CREATORS={19:'Μυλωνάς (museum caption; full identity unresolved)',46:'Wells (museum description)',57:'SCOTT (source label; photographer or prototype-artist role unresolved)',58:'Ν. Κεσανλλής (museum caption; identity unresolved; creator field differs)',98:'Bellin (museum description; title also reads Pellio)',99:'Mercator–Hondius (museum description)',115:'Andrew (museum caption), after Delacroix',121:'Γ. Σαμαρτζής (museum caption)',134:'Δ. Γεωργαντάς (museum caption; full identity unresolved)',147:'Woodville (museum caption; identity unresolved)',152:'Σ. Βέμπο (embroidery, per museum caption; design artist unresolved)',170:'Νικόλα (museum caption; full identity unresolved)'}

def date(row):
    n=row['number'];literal=row['fields']['Ημερομηνία δημιουργίας'];label=literal[0]
    if n in DATE_CONFLICT:return None,None,'unknown','Creation date unresolved (conflicting source/version evidence)',DATE_CONFLICT[n]
    if n in EVENT:return None,None,'unknown','Creation date unknown; source historical date retained as evidence',EVENT[n]
    if n==1:return 1700,1738,'range','1700–1738 (museum description; title: circa1700)','Museum description gives1700–1738; broad18thcentury creation field retained separately.'
    if n==2:return 1725,1725,'circa','Circa1725','Description explicitly says γύρω στο1725; retain approximate qualifier despite exact-looking date field.'
    if n==117:return 1928,1928,'exact','1928 (museum title and description)','Museum title and description explicitly identify execution year1928; broadlate19th–early20thfield retained separately. Not derived from depicted event or creator lifespan.'
    ranges={'18ος αιώνας':(1701,1800,'century','18th century'),'19ος αιώνας':(1801,1900,'century','19th century'),'20ός αιώνας':(1901,2000,'century','20th century (creation range crosses1970)'),'17ος - 19ος αιώνας':(1601,1900,'range','17th–19th century'),'19ος - 20ος αιώνας':(1801,2000,'range','19th–20th century (creation range crosses1970)'),'19ος - 20ός αιώνας':(1801,2000,'range','19th–20th century (creation range crosses1970)'),'Πρώιμος 20ός αιώνας':(1900,1930,'circa_range','Early20th century (source range1900–1930)')}
    if label in ranges:
        first,last,precision,display=ranges[label]
        if label=='Πρώιμος 20ός αιώνας':assert row['enrichment']['Χρονολογία']==['1900 - 1930']
        return first,last,precision,display,'Literal creation-century evidence, qualifiedrange retained; not an exactyear or a bound inferred from an artist lifespan.'
    match=re.fullmatch(r'(\d{4})(?: - (\d{4}))?',label);assert match,(n,label)
    first=int(match[1]);last=int(match[2] or first);return first,last,'exact' if first==last else 'range',str(first) if first==last else str(first)+'–'+str(last),'Source creation field; historical-event ambiguity reviewed separately.'

def main():
    dest=RUN/'editorial-source-decisions-001.json.gz';assert not dest.exists();source=m.load(RUN/'selected-source-records-001.json.gz')['rows'];visual=m.load(RUN/'visual-references-001.json');frames={x['number']:x for x in visual['rows']};assert len(frames)==189 and not visual['exact_duplicate_groups']
    out=[]
    for row in source:
        n=row['number'];f=row['fields'];title=f['Τίτλος'][0];description=f.get('Περιγραφή',[]);caption=description[0] if description else '';types=f.get('Τύπος',[]);creator=f.get('Δημιουργός',['ΑΓΝΩΣΤΟΣ'])[0];creator=None if creator=='ΑΓΝΩΣΤΟΣ' else creator;creator=CREATORS.get(n,creator)
        first,last,precision,display,date_note=date(row);old=row['index']['historical_source_match'];decision='existing_comparator' if old else 'scope_hold' if n in SCOPE else 'identity_hold' if n in HOLDS else 'proposed_review_artwork'
        notes=[date_note,'Greek literal title/description take precedence over inconsistent English translations. Both language versions retained as source evidence, not two makers.','One artwork/object composition per source record; depicted people or multiple medal views do not create extra records. Museum collection evidence does not establish current display.','189 decoded source frames and eight contact sheets reviewed. Six empty200image responses are unavailable, not placeholder artwork. Numeric sourceURL IDs are not asserted as inventory numbers.']
        if n in SCOPE:notes.append(SCOPE[n])
        if n in HOLDS:notes.append(HOLDS[n])
        if first is not None and last>1970:notes.append('Explicit editorial review: preserve the historical museum object as a review candidate with the supplied broad creation range. Pre1971eligibility is not established; do not count as numeric-date eligible or deliver its image. No invented narrower date.')
        if n in [13,89,151]:creator='Unidentified copyist';notes.append('Museum explicitly describes a copy; date and artist of a presumed prototype are not assigned to this object.')
        if n==115:title='Η σφαγή της Χίου — αντίγραφο από το έργο Delacroix';notes.append('Title restored from the complete Greek description because literal title contains emptyanglebrackets. Museum dates the copy to19thcentury; no exact prototypeyear assigned. Andrew is an unresolved copyist label, not a primary Delacroix link.')
        if n==121:title='Ιωάννης Θ. Ορφανίδης';notes.append('Sitter name recovered from complete Greek description; damaged emptyanglebrackets in title retained as evidence.')
        if n==86:title='Όλοι μαζί με μια καρδιά — Πίνδος';notes.append('Subject title recovered from complete Greek description; literal title has emptyanglebrackets.')
        if n in [3,4,124]:notes.append('Separate source compositions:3charging singleEvzone,4wide battle,124standingEvzone. Relatedsubjects and same artist do not establish a duplicate.')
        if n in [87,88]:notes.append('Distinct Constantine drawings:87frontalhead,88seatedsideview; do not merge by sitter/title.')
        if n in [107,108,109,110,111]:notes.append('Nurse studies differ in pose, figure count and composition; retain separate works.')
        if n in [139,140]:notes.append('Bursa139shows a treelined street/crowd;140isolatesstandingfigures. Different compositions.')
        if n in [145,161]:notes.append('145seatedfigures sketch;161two bust-length uniformed portraits. Distinct Mudanya compositions.')
        if n in [36,55,101]:notes.append('Supplied image visibly includes printed caption/margins; classify the held sheet as print while preserving source sketch terminology. Peike is not established as a maker.')
        if n==57:notes.append('Literal type is photograph and composition reproduces an illustrated militaryscene. Preserve photographic-reproduction classification; SCOTT is not automatically the photographer or direct painter of an original oilwork.')
        if n==58:notes.append('Caption Ν.Κεσανλλής and creatorfieldNikosKesanlis are not enough to distinguish homonymous artist identities. Keep qualified objectlabel without linking a modern artist authority.')
        if n==95:notes.append('Greek title/description give23×24cm; English title gives25×24cm. Retain bothclaims, no silent normalization of conflictingdimensions.')
        if n==133:notes.append('Visual review resolves scope: an artwork drawing of an aircraft and tent, not a technical airport plan. Preserve unknown medium and broad20thcenturydate.')
        if n==138:notes.append('No image available; named-creator drawing and source metadata retained as a review record subject to global counterpart review.')
        if n==149:notes.append('No image available. Distinct sailor-costume study retained under named creator;1821depicts costume, not artworkcreation.')
        if n==152:notes.append('Museum says embroidered byΣ.Βέμπο; classify textile and distinguish embroiderer from unresolved caricature designer.')
        if n in [184,185]:notes.append('Moderncast/replica context retained; no ancientoriginaldate or ancientmaker assigned.184explicitlycalledεκμαγείο;185replicaidentitystillqualified.')
        if n==194:notes.append('Greek title says άνευΞιφών, withoutswords; English withswords contradicts it. Preserve Greek and recordtranslationerror.')
        if old:notes.append('Comparator only: existing title/date/creator/status/primary/holding are preserved, including old medal event-date ambiguities.')
        kind='unknown';medium=None;form=None
        if any('χαλκογραφία' in x.lower() or x in ['Γκραβούρα','Χάρτης Γκραβούρα'] for x in types):kind='print';medium=types[0]
        if any(x in types for x in ['Ζωγρ.Πίνακας','Ελαιογραφία']):kind='painting';medium='Ελαιογραφία'
        if any(x in types for x in ['Ζωγραφικό σχέδιο/σκίτσο','Σκίτσο']):kind='drawing'
        if n in [36,38,39,40,43,55,101]:kind='print'
        if n in [19,20,21,22,26,27,28,29,30,31,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,102,103,104,105,128,129,130,133,149]:kind='drawing'
        if n in [115,116,117,118,119,120,121,123,124,125,134]:kind='drawing' if n==125 else 'painting'
        if n in [57,90,131,132]:kind='photograph'
        if 168<=n<=181 or n in [184,185]:kind='sculpture';form='cast replica' if n==184 else 'stele (replica identity to review)' if n==185 else None
        if n in [152,182]:kind='textile';medium='Κέντημα' if n==152 else None
        if n==183 or 186<=n<=195:kind='metalwork';medium='Αργυρός' if n==183 else None
        if 'ελαιογραφ' in caption.casefold():medium='Ελαιογραφία'
        for term in ['χρωματιστά κραγιόνια και κάρβουνο','κάρβουνο','καρβούνο','κραγιόνι','κραγιόν','μελάνι','μολύβι','Παστέλ']:
            if term in caption:medium=term;break
        dimensions=None
        dim=re.search(r'\(?\d+(?:[,.]\d+)?\s*[xXΧ]\s*\d+(?:[,.]\d+)?\)?\s*(?:εκ\.?|εκατοστά)',caption)
        if dim:dimensions=dim[0]
        if n==95:dimensions='23×24cm (Greek);25×24cm (English title), source discrepancy'
        if n==117:dimensions='024Χ056 (source units unspecified)'
        if n==118:dimensions='2×1.35 includingframe (source units unspecified)'
        candidate=decision=='proposed_review_artwork' and first is not None and last<=1955 and n in frames
        out.append(dict(number=n,source_id=row['source_id'],source_url=row['source_url'],native_url=None,title=title,title_source_literals=f['Τίτλος'],creator_label=creator,creator_source_literals=f.get('Δημιουργός',[]),artist_id=None,first=first,last=last,date_precision=precision,date_display=display,source_date_literal=f['Ημερομηνία δημιουργίας'],source_chronology=row['enrichment'].get('Χρονολογία',[]),work_type=kind,medium_text=medium,dimensions_text=dimensions,inventory=None,object_form=form,cultural_context=None,description_source=description,decision=decision,review_notes=notes,source_fields=f,aggregator_enrichment=row['enrichment'],creator_authorities=row['field_enrichment_links'].get('Δημιουργός',[]),source_receipt=row['receipt'],visual_reference=frames.get(n),source_image_reviewed=n in frames,image_candidate=candidate,image_hold_reason=None if candidate else 'Existing comparator, scope/identity hold, unknown/crossing creation date, or unavailable image; see explicitreviewnotes.',date_scope_review_required=first is None or last>1970,proposed_status='review',ready_to_apply=False,applied=False))
    new=[x for x in out if x['decision']=='proposed_review_artwork'];counts=dict(proposed=len(new),old_comparators=sum(x['decision']=='existing_comparator' for x in out),scope_holds=len(SCOPE),identity_holds=len(HOLDS),numeric_date_eligible=sum(x['last'] is not None and x['last']<=1970 for x in new),unknown_dates=sum(x['first'] is None for x in new),crossing_cutoff=sum(x['last'] is not None and x['last']>1970 for x in new),image_candidates=sum(x['image_candidate'] for x in new))
    m.save(dest,dict(at=m.now(),rows=out,counts=counts,dependencies=[c.ref(RUN/x) for x in ['selected-source-records-001.json.gz','visual-references-001.json','focused-context-001.json.gz','production-identity-001.json.gz']],script_reference=c.ref(Path(__file__).resolve()),policy='All195bilingualmetadatarecords read;189frames/eightcontacts and sevenfocusedsourceframes viewed. Proposals await focused globalcomposition comparison, creatoridentity, digitalfile/reproduction review and finalapproval by assistant under existinguserauthorization. No production write.'))
    with (RUN/'candidate-review-001.csv').open('x',encoding='utf-8-sig',newline='') as h:
        fields=['number','source_id','title','creator_label','first','last','date_display','work_type','medium_text','dimensions_text','decision','image_candidate','source_url'];w=csv.DictWriter(h,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(out)
    print(json.dumps(counts),flush=True)

if __name__=='__main__':main()
