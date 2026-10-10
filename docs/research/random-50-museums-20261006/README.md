# Random fifty museums: production delivery

Verified 2026-10-06T19:22:52Z. Added **1,813 artworks** and linked **0 existing artworks** across **50 museums** in production. All 50 have at least 100 artworks with eligible pre-1971 creation dates; **28 have at least 200**. The lowest eligible count is **108**. New artworks remain in review.

The fifty museums were randomly selected without replacement from a 75-museum documented-capacity pool. The [sample and seed](sample.json) preserve the complete pool and algorithm. This pool uses verified prior museum research and the official French Joconde catalogue and is weighted toward French museums; it is not a representative worldwide sample. Existing collections larger than 200 were preserved.

[Museum counts](museum-results.csv) · [Every added or linked artwork and its source](artwork-results.csv) · [Database verification](verification.json) · [Pinned delivery plan and held candidates](plan.json.gz).

Primary object IDs, inventories, source creator labels, literal dates, collection custody and database duplicates were checked. Existing artwork metadata and images were preserved. No current-display claims, automatic publication, image downloads, application deployment or local database writes were made. All source bodies retain their original retrieval timestamps and SHA-256 hashes; reusing earlier evidence does not make its capture date current. Confidence is an editorial assessment, not a calibrated probability.

Production delivery ran atomically after locked version and identity checks, with preimages under `~/Library/Application Support/Artline/backups/random-50-museums-20261006/`. Verification used a separate read-only connection after commit. The 114 existing source-parser tests passed; this is not a 10-million-row performance benchmark. Counts include legacy records and do not newly prove every legacy entry is a distinct physical object.

| Museum | Eligible before | Added | Linked | Eligible after |
|---|---:|---:|---:|---:|
| Art Gallery of South Australia | 70 | 130 | 0 | 200 |
| château musées — Blois | 32 | 82 | 0 | 114 |
| Mauritshuis | 25 | 171 | 0 | 196 |
| musée Antoine Vivenel — Compiègne | 145 | 55 | 0 | 200 |
| musée barrois — Bar-le-Duc | 116 | 84 | 0 | 200 |
| musée Bertrand — Châteauroux | 105 | 30 | 0 | 135 |
| musée d'art et d'archéologie — Senlis | 241 | 10 | 0 | 251 |
| musée d'art et d'histoire — Saint-Brieuc | 135 | 45 | 0 | 180 |
| musée d'art et d'histoire — Saint-Lô | 107 | 30 | 0 | 137 |
| musée d'Art Moderne — Troyes | 162 | 38 | 0 | 200 |
| musée de la Loire — Cosne-Cours-sur-Loire | 97 | 100 | 0 | 197 |
| musée de la Princerie — Verdun | 163 | 29 | 0 | 192 |
| musée de l'hôtel Sandelin — Saint-Omer | 133 | 32 | 0 | 165 |
| musée des Augustins — Toulouse | 311 | 10 | 0 | 321 |
| musée des beaux-arts — Bordeaux | 1409 | 10 | 0 | 1419 |
| musée des beaux-arts — Caen | 630 | 10 | 0 | 640 |
| musée des beaux-arts — Chambéry | 434 | 10 | 0 | 444 |
| musée des beaux-arts — Dijon | 895 | 10 | 0 | 905 |
| musée des beaux-arts et d’archéologie — Troyes | 293 | 10 | 0 | 303 |
| musée des beaux-arts Jules Chéret — Nice | 97 | 37 | 0 | 134 |
| musée des beaux-arts — Lille | 966 | 10 | 0 | 976 |
| musée des beaux-arts — Lyon | 37 | 145 | 0 | 182 |
| musée des Beaux-Arts — Nantes | 1372 | 10 | 0 | 1382 |
| musée des beaux-arts — Nîmes | 172 | 21 | 0 | 193 |
| musée des Beaux-Arts — Pau | 512 | 10 | 0 | 522 |
| musée des beaux-arts — Rennes | 654 | 10 | 0 | 664 |
| musée des Beaux-Arts — Strasbourg | 202 | 10 | 0 | 212 |
| musée des beaux-arts — Tours | 588 | 10 | 0 | 598 |
| musée des civilisations de l'Europe et de la Méditerranée — Marseille | 75 | 65 | 0 | 140 |
| musée du temps — Besançon | 98 | 28 | 0 | 126 |
| musée Gallé-Juillet — Creil | 104 | 31 | 0 | 135 |
| musée Grobet-Labadié — Marseille | 255 | 10 | 0 | 265 |
| musée Hyacinthe Rigaud — Perpignan | 188 | 12 | 0 | 200 |
| musée Ingres Bourdelle — Montauban | 3458 | 10 | 0 | 3468 |
| musée Lambinet — Versailles | 406 | 10 | 0 | 416 |
| musée Louis Philippe — Eu | 32 | 94 | 0 | 126 |
| musée Maritime de l'Ile Tatihou — Saint-Vaast-la-Hougue | 99 | 11 | 0 | 110 |
| musée municipal — Soissons | 238 | 4 | 0 | 242 |
| musée national des châteaux de Malmaison et de Bois Préau — Rueil-Malmaison | 142 | 58 | 0 | 200 |
| musée national des châteaux de Versailles et de Trianon — Versailles | 2775 | 10 | 0 | 2785 |
| musée national du château de Compiègne — Compiègne | 270 | 10 | 0 | 280 |
| musée national du château de Fontainebleau — Fontainebleau | 255 | 10 | 0 | 265 |
| musée national du château de Pau — Pau | 101 | 28 | 0 | 129 |
| musée Thomas Henry — Cherbourg-en-Cotentin | 256 | 10 | 0 | 266 |
| Museo Civico e Pinacoteca — Foggia (FG) | 91 | 34 | 0 | 125 |
| National Gallery of Ireland | 68 | 131 | 0 | 199 |
| Pinacoteca Civica F. Podesti — Ancona (AN) | 80 | 28 | 0 | 108 |
| Tapisserie de Bayeux - MAHB musée d'art et d'histoire baron Gérard — Bayeux | 143 | 31 | 0 | 174 |
| The Icon Museum and Study Center | 158 | 19 | 0 | 177 |
| Tretyakov Gallery | 212 | 10 | 0 | 222 |
