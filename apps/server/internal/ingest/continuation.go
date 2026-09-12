package ingest

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
)

// Pins the reviewed chunk inventory, including every chunk's own SHA. A changed
// source capture or mapping requires a new offline review and explicit pin.
var continuationPins = map[string]string{
	"popular-karlsruhe-next":     "47d96daa160e8a18f0913627fa1aa05d415dac448f1394eb284a2001e0c8a262",
	"popular-karlsruhe":          "46b6825d12ba204c94459093ca6e4e9a54df6e4c926cb291de4a215b53949a8b",
	"popular-poldi":              "2bf3171cf854d8d0583e00844e5776c6065c3c0f8a4ff285180fe7dfa53a86bb",
	"popular-athens-entombment":  "c655176ab0ac7b5f325148193a2360fbb5e99c514cf6810666a16d5c834771a2",
	"popular-nivaagaard":         "a13344de933b611bcebc727c991c98eb756799bce9b6c46528d98d53ac0e1595",
	"popular-repin":              "34c2ec816869cbd4bcf19602cd0450282ac5edf08516764f04a585b1aa6886cd",
	"popular-goulandris":         "d0af7c7823433f4011ba39e8121115a999795daa70e57fd04c0513031391da85",
	"popular-athens-national":    "fbc5e9b88451b7d6da0a2063598b8e815f35145858c4c6b862abb3d881f77cda",
	"popular-durer":              "b47d6629fdeae7be358c6591bc4898ed57f89f3aeda2678291e821625335fcae",
	"popular-ng-aliases":         "54473b21c76449a2fca0b7a4680c9025c51623136a684d047b1683e39820566e",
	"popular-caen":               "413201653d8e1eb845ed60b72979f6a0621293864727b95adf17d8ca20b2ba76",
	"popular-ng":                 "17c9659dc455168783bdeeafd0953f3e8399e9d4024cfae70c9c4608dbea6c55",
	"popular-marmottan-deposits": "ca91b8cb2758d6e8874bfe20ffc25272609af004f452893fcb428940a0c74a4d",
	"popular-marmottan":          "8f7566692154b458965396cb1e3fa356177c8dc06a6979cf08355e592716a47a",
	"icons-athens":               "000659a06cef548f86baf9f1c85c96679db5141b1515186fece05adedbab2809",
	"icons-kremlin":              "59f9160a1a2f062414ba7dca5b4761472611563e4cc5ec45eadc9a04ac5c83a6",
	"normandy-muma":              "36bfe3abad9271388956cbcec4007c99e534778b9ac15a8f6b761140304fb412",
	"normandy-rouen":             "720a8fe858f949cfb9650fd8d4c91f584f901e316b4a3e5cd0075c7c970f8a18",
	"normandy-joconde":           "fa7af96f17c95654ecefc43504df720bcf5ecfbc57bbc27b659cbec7e161ed4f",
	"rijks":                      "d5913c114ae310bc7594313ad772a465c6781c654379ec9730dc336ff54559c2",
	"smk":                        "5ca7c08c06568ffeec711ec88f5ec7f525ee178913dee45918d7000df67edd53",
	"chicago":                    "81312081696780d8a8d88912550b503662e33f2260fee1ac53397e4f53694621",
	"met":                        "f22eb07a9bb18759c61b374b174dd6aa0b3525c40427d93d48a44a838167872b",
	"cleveland":                  "8c81a8e14697f33186ac988b87ed63ffb98204abf021c0bda2e69bea95f0c136",
	"lombardia":                  "8c37745d13d8bbd71d18525d6ee88f10e732d3db560878d78f5fb72def6c228e",
	"joconde":                    "11fbca52b990c9bfe0d70de8735e4213b49e4b53b760b7aabb93b70daf705c55",
	"sirbec":                     "c82f2ab37036d3a9cb43c3fd647d71610727b45ff58a7f0f4ffe330b8bb89fc6",
	"pushkin-kamis":              "7217c61be299f9e3806608b052c4d42de5a45aaf9502647f9b1cd6cf734b46e0",
}

func continuationDirectory(source string) string {
	if source == "popular-karlsruhe-next" {
		return "docs/research/data-collection-20260911-2016/karlsruhe-next-v2"
	}
	if source == "popular-karlsruhe" {
		return "docs/research/popular-resume-20260911-1852/karlsruhe-v1"
	}
	if source == "popular-poldi" {
		return "docs/research/popular-resume-20260911-1852/poldi-v1"
	}
	if source == "popular-athens-entombment" {
		return "docs/research/popular-resume-20260911-1852/athens-entombment-v2"
	}
	if source == "popular-nivaagaard" {
		return "docs/research/popular-resume-20260911-1852/nivaagaard-v1"
	}
	if source == "popular-repin" {
		return "docs/research/popular-europe-session-20260911/repin-v1"
	}
	if source == "popular-goulandris" {
		return "docs/research/popular-europe-session-20260911/goulandris-v2"
	}
	if source == "popular-athens-national" {
		return "docs/research/popular-europe-session-20260911/athens-national-v3"
	}
	if source == "popular-durer" {
		return "docs/research/popular-europe-session-20260911/durer-v1"
	}
	if source == "popular-ng-aliases" {
		return "docs/research/popular-europe-session-20260911/ng-aliases-v1"
	}
	if source == "popular-caen" {
		return "docs/research/popular-europe-session-20260911/caen-v3"
	}
	if source == "popular-ng" {
		return "docs/research/popular-europe-session-20260911/ng-v2"
	}
	if source == "popular-marmottan-deposits" {
		return "docs/research/popular-artists-20260911/deposits-v1"
	}
	if source == "popular-marmottan" {
		return "docs/research/popular-artists-20260911/marmottan-v2"
	}
	if strings.HasPrefix(source, "icons-") {
		return "docs/research/icons-20260910/" + strings.TrimPrefix(source, "icons-") + "-v1"
	}
	if strings.HasPrefix(source, "normandy-") {
		return "docs/research/normandy-20260910/" + strings.TrimPrefix(source, "normandy-") + "-v1"
	}
	if source == "smk" || source == "rijks" {
		return "docs/research/europe-ui-20260910/" + source + "-v1"
	}
	if source == "cleveland" || source == "met" {
		return "docs/research/all-museums-20260910/" + source + "-v2"
	}
	if source == "met" || source == "cleveland" || source == "lombardia" || source == "chicago" {
		return "docs/research/all-museums-20260910/" + source + "-v1"
	}
	return "docs/research/catalogue-continuation-20260910/" + source + "-v3"
}

type continuationManifest struct {
	Source string
	Chunks []struct {
		File  string
		SHA   string `json:"sha256"`
		Works int
	}
}

func continuationBatch(manifest []byte, file string, data []byte) (europeanBatch, error) {
	var root continuationManifest
	var b europeanBatch
	if len(manifest) > 1<<20 || json.Unmarshal(manifest, &root) != nil || continuationPins[root.Source] != checksum(manifest) {
		return b, errors.New("unreviewed continuation manifest")
	}
	expected := ""
	works := 0
	for _, c := range root.Chunks {
		if c.File == file {
			if expected != "" {
				return b, errors.New("duplicate chunk")
			}
			expected = c.SHA
			works = c.Works
		}
	}
	if expected == "" || checksum(data) != expected || len(data) > 32<<20 || works < 1 || works > 500 {
		return b, errors.New("changed/oversize continuation chunk")
	}
	var m struct {
		Schema       int `json:"schema_version"`
		Source       string
		Painters     map[string]string
		Definitions  map[string]europeanDefinition
		Institutions []europeanInstitution
		Works        []europeanWork
	}
	icons := root.Source == "icons-athens" || root.Source == "icons-kremlin"
	if json.Unmarshal(data, &m) != nil || m.Schema != 2 || m.Source != root.Source || len(m.Works) != works || len(m.Definitions) != len(m.Institutions) || (!icons && len(m.Painters) < 1) || len(m.Painters) > 500 {
		return b, errors.New("invalid continuation structure")
	}
	host := map[string]string{"met": "www.metmuseum.org", "cleveland": "clevelandart.org", "lombardia": "www.lombardiabeniculturali.it", "chicago": "www.artic.edu", "joconde": "pop.culture.gouv.fr", "sirbec": "www.lombardiabeniculturali.it", "pushkin-kamis": "collection.pushkinmuseum.art"}[root.Source]
	country := map[string]string{"met": "US", "cleveland": "US", "lombardia": "IT", "chicago": "US", "joconde": "FR", "sirbec": "IT", "pushkin-kamis": "RU"}[root.Source]
	if root.Source == "smk" {
		host, country = "open.smk.dk", "DK"
	}
	if root.Source == "rijks" {
		host, country = "www.rijksmuseum.nl", "NL"
	}
	switch root.Source {
	case "popular-karlsruhe", "popular-karlsruhe-next":
		host, country = "www.kunsthalle-karlsruhe.de", "DE"
	case "popular-poldi":
		host, country = "museopoldipezzoli.it", "IT"
	case "popular-nivaagaard":
		host, country = "nivaagaard.dk", "DK"
	case "popular-repin":
		host, country = "rusmuseumvrm.ru", "RU"
	case "popular-goulandris":
		host, country = "goulandris.gr", "GR"
	case "popular-athens-national", "popular-athens-entombment":
		host, country = "www.nationalgallery.gr", "GR"
	case "popular-durer":
		host, country = "www.sammlung.pinakothek.de", "DE"
	case "popular-caen":
		host, country = "pop.culture.gouv.fr", "FR"
	case "popular-ng", "popular-ng-aliases":
		host, country = "www.nationalgallery.org.uk", "GB"
	case "popular-marmottan", "popular-marmottan-deposits":
		host, country = "www.marmottan.fr", "FR"
	case "icons-athens":
		host, country = "www.ebyzantinemuseum.gr", "GR"
	case "icons-kremlin":
		host, country = "collectiononline.kreml.ru", "RU"
	case "normandy-muma":
		host, country = "www.muma-lehavre.fr", "FR"
	case "normandy-rouen":
		host, country = "mbarouen.fr", "FR"
	case "normandy-joconde":
		host, country = "pop.culture.gouv.fr", "FR"
	}
	for key, q := range m.Painters {
		if key != q || !bulkQID.MatchString(q) {
			return b, errors.New("invalid authority crosswalk")
		}
	}
	for _, i := range m.Institutions {
		d, ok := m.Definitions[i.ID]
		if !ok || d.Host != host || i.Country != country || i.City == "" || d.Slug == "" || !strings.HasPrefix(i.ID, root.Source) {
			return b, errors.New("unapproved institution mapping")
		}
	}
	seen := map[string]bool{}
	for _, w := range m.Works {
		d, e := europeanWorkDate(w)
		validCreator := m.Painters[w.Painter] != "" && w.UnlinkedCreatorLabel == ""
		if icons && w.Painter == "" && len(strings.TrimSpace(w.UnlinkedCreatorLabel)) > 0 && len(w.UnlinkedCreatorLabel) <= 500 {
			validCreator = true
		}
		if icons && (w.ObjectForm != "icon" || w.WorkType != "painting" || w.CulturalContext == "" || len(w.CulturalContext) > 500) {
			return b, errors.New("icon form/medium/context requires explicit reviewed metadata")
		}
		if !icons && (w.UnlinkedCreatorLabel != "" || w.CulturalContext != "" || w.ObjectForm != "") {
			return b, errors.New("icon metadata outside reviewed adapter")
		}
		validHighlight := w.MuseumHighlightURL == "" || root.Source == "normandy-muma" && w.MuseumHighlightURL == "https://www.muma-lehavre.fr/fr/collections/oeuvres-commentees/incontournable"
		validRole := w.AttributionRole == "primary"
		if icons && w.Painter != "" {
			_, roleErr := europeanRole(w)
			validRole = roleErr == nil
		}
		if e != nil || catalog.CreationScope(d.First, d.Last, d.Precision) != "eligible" || w.Title == "" || w.ObjectID == "" || seen[w.URL] || !europeanAllowedURL(m.Definitions, w.Institution, w.URL) || !validCreator || !validHighlight || !validRole || w.Description == "" || len(w.Description) > 40000 {
			return b, fmt.Errorf("invalid continuation work %s", w.ObjectID)
		}
		if w.WorkType != "painting" && w.WorkType != "drawing" && w.WorkType != "print" {
			return b, errors.New("unsupported medium")
		}
		seen[w.URL] = true
	}
	return europeanBatch{SHA: expected, Version: "continuation-" + root.Source + "-" + expected, Path: continuationDirectory(root.Source) + "/" + file, SourceSlug: root.Source + "-research-20260910", SourceName: root.Source + " — selected museum catalogue metadata (review only)", Schema: 2, Works: works, Museums: len(m.Institutions), Painters: m.Painters, Definitions: m.Definitions, AllowUnlinkedCreators: icons}, nil
}

// No remote requests, image downloads, inferred highlights or publication. Each
// bounded chunk is atomic; a completed chunk's replay preserves editorial clears.
func ImportContinuation(ctx context.Context, pool *pgxpool.Pool, manifest []byte, file string, data []byte, apply bool) (EuropeanImportReport, error) {
	b, e := continuationBatch(manifest, file, data)
	if e != nil {
		return EuropeanImportReport{}, e
	}
	var id, status, sha string
	e = pool.QueryRow(ctx, `SELECT id::text,status,query_json->>'sha256' FROM import_jobs WHERE idempotency_key=$1`, b.Version).Scan(&id, &status, &sha)
	if e == nil {
		if status != "needs_review" || sha != b.SHA {
			return EuropeanImportReport{}, errors.New("existing import state conflict")
		}
		return EuropeanImportReport{Applied: apply, Snapshot: b.SHA, JobID: id, Warnings: []string{"Previously completed identical chunk: no database changes."}, Works: []EuropeanWorkResult{}}, nil
	}
	if !errors.Is(e, pgx.ErrNoRows) {
		return EuropeanImportReport{}, e
	}
	return importEuropeanBatch(ctx, pool, data, apply, b)
}
