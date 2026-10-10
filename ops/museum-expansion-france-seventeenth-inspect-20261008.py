"""Display complete bounded subsets of the remaining comparison queue."""
import gzip,json,runpy,sys
from pathlib import Path
R=Path(__file__).resolve().parent.parent/'docs/research/museum-expansion-20261006/native/france-seventeenth-minimum-20261008'
def load(p):return json.load(gzip.open(p,'rt'))
def main():
    lo,hi=map(int,sys.argv[1:3]);mode=sys.argv[3] if len(sys.argv)>3 else 'remaining'
    t=load(R/'comparison-triage-001.json.gz');notes=runpy.run_path(str(R.with_name('france-fifteenth-minimum-20261008')/'working-notes-release-three-museums-001.py'))
    ix={a['number']:a for a in t['rows']};seen={}
    for row in load(R/'remaining-candidates-001.json.gz')['rows']:
        n=row['number']
        if not lo<=n<=hi:continue
        f=row['facts'];print('\n#',n,' | '.join(str(f.get(k)) for k in ['title','creator_label','inventory','medium','dimensions_text','date_display']))
        note=notes['SOURCE_NOTES'].get(n,notes['HOLDS'].get(n,''))
        for phrase in ['checks remain pending. ', 'supplemental native URLs, former maker and inventory checks remain pending. ', 'native display rooms are not imported as artworks/display assertions. ', 'Supplemental short-title, related inventory and physical comparisons pending before final additions. ', 'Supplemental translated short titles, native URLs and physical comparator audit remain pending. ', 'Supplemental physical version and native URL comparisons remain pending. ']:
            if phrase in note:note=note.split(phrase,1)[-1]
        print('Note:',note, 'Pending:',notes['PENDING'].get(n,''))
        repeated=[]
        for e in ix[n]['entries']:
            if mode!='all' and not e['needs_individual_review']:continue
            aid=e['existing_artwork_id'];a=t['existing_contexts'][aid]
            if aid in seen:repeated.append(seen[aid]);continue
            seq=len(seen)+1;seen[aid]=seq;print('COMP',seq,aid,','.join(e['comparison_kinds']))
            if a['primary_contexts']:
                for p in a['primary_contexts']:print(' | '.join(str(p['literal_primary_record'].get(k) or '') for k in ['Titre','Auteur','Numero_inventaire','Materiaux_techniques','Mesures','Millesime_de_creation','Periode_de_creation']))
            else:print(' | '.join(str(a['artwork'].get(k) or '') for k in ['title','unlinked_creator_label','creators','accession_number','medium_text','dimensions_text','date_display']))
        if repeated:print('Repeat comparator numbers:',','.join(map(str,repeated)))
if __name__=='__main__':main()
