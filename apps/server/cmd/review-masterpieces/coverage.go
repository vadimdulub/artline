package main

import (
	"bytes"
	"context"
	"encoding/csv"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/catalog"
	"github.com/vadimdulub/artline/apps/server/internal/ingest"
)

const coverageVersion = "painter-coverage-images-100kb-v1"
const ngaRevision = "5cf4c649c65efff351e3dc2f2532292e2d2b4b6d" // official main, checked 10 Sep 2026
const ngaImageFeed = "https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/" + ngaRevision + "/data/published_images.csv"
const ngaPolicy = "https://www.nga.gov/artworks/free-images-and-open-access"
const commonsPolicy = "https://commons.wikimedia.org/wiki/Commons:Reuse_of_PD-Art_photographs"

type coveragePick struct{ Source, Object, Artist, Reason string }

// Explicit, bounded study selection. These choices NEVER become museum highlights
// or overwrite the owner's must-see list. Museum holdings remain separately sourced.
var coveragePicks = []coveragePick{
	{"nga", "52226", "Alfred Sisley", "Boulevard Heloise, Argenteuil: an Impressionist landscape selected for road, river and changing light; alternative to the SMK work with no permitted image."},
	{"commons-met", "437442", "Ilya Repin", "Garshin portrait: priority Russian painter and expressive literary portrait; independent file-specific Commons reproduction, not a Met image permission claim."},
	{"commons-met", "437671", "Paul Signac", "The Jetty at Cassis: selected for divided colour and harbour light; independent file-specific reproduction."},
	{"commons-met-highlight", "488319", "Wassily Kandinsky", "Improvisation 27: priority Russian-born artist and already-documented museum highlight; independent file-specific reproduction."},
	{"nga", "5", "Fra Angelico", "Early Florentine devotional painting: intimate figures, patterned textiles and gold; complements later Renaissance portraits."},
	{"nga", "9", "Masaccio", "Early Renaissance Madonna selected to study the transition toward weight, volume and naturalistic space."},
	{"nga", "41671", "Sandro Botticelli", "Giuliano de' Medici portrait: selected for Botticelli's distinctive profile and Medici-era portraiture."},
	{"nga", "24", "Sandro Botticelli", "Adoration of the Magi: selected for multi-figure composition and architectural setting."},
	{"nga", "432", "Giorgione", "Adoration of the Shepherds: selected for the relationship between Venetian landscape, light and devotional figures."},
	{"nga", "142008", "Giuseppe Arcimboldo", "Four Seasons in One Head: a distinctive composite portrait, suitable for comparing allegory and illusion."},
	{"nga", "46148", "Domenico Ghirlandaio", "Madonna and Child: a focused example of Ghirlandaio's Florentine devotional painting."},
	{"nga", "31", "Pietro Perugino", "Right panel of the Crucifixion ensemble; kept as the museum's panel record, not presented as the whole triptych."},
	{"nga", "46142", "Tintoretto", "Conversion of Saint Paul: selected to study dramatic movement and Venetian narrative painting."},
	{"nga", "32", "Vittore Carpaccio", "Flight into Egypt: selected for Venetian narrative and landscape detail."},
	{"nga", "56670", "Wassily Kandinsky", "Improvisation 31 (Sea Battle): priority Russian-born artist and an important example of abstraction retaining narrative cues."},
	{"nga", "52614", "Piet Mondrian", "Lozenge composition: a focused study of geometric abstraction and restricted colour."},
	{"nga", "61372", "Paul Klee", "New House in the Suburbs: selected to explore Klee's architectural and geometric imagery."},
	{"nga", "53588", "Marc Chagall", "Houses at Vitebsk: priority Eastern European setting and artist; image only if this specific reproduction is cleared."},
	{"nga", "46590", "Salvador Dalí", "Sacrament of the Last Supper: selected Surrealist religious composition; copyright gate still applies."},
	{"nga", "121052", "Diego Rivera", "Montserrat: selected early landscape to complement Rivera's better-known mural practice."},
	{"nga", "69660", "Joan Miró", "The Farm: selected to explore the transition between observed landscape and symbolic imagery."},
	{"nga", "55819", "Jackson Pollock", "Lavender Mist: selected action-painting comparison; not permission to copy a restricted image."},
	{"nga", "46528", "Pablo Picasso", "Pedro Mañach: early Picasso portrait; rights remain per-image, not inferred from its creation year."},
	{"nga", "106383", "Georges Braque", "Port of La Ciotat: selected early colour and landscape study before Cubism."},
	{"nga", "66422", "René Magritte", "The Blank Signature: selected for its figure-ground illusion; rights gate still applies."},
	{"met", "437671", "Paul Signac", "The Jetty at Cassis: selected to examine divided colour and harbour light."},
	{"met", "437442", "Ilya Repin", "Portrait of Vsevolod Garshin: priority Russian painter and a psychologically expressive literary portrait."},
	{"met", "437441", "Ilya Repin", "Portrait of a Boy: a second specific Repin reproduction checked for independent image permission."},
	{"met", "437821", "Tintoretto", "Miracle of the Loaves and Fishes: a Venetian narrative composition, as an alternative permitted image."},
	{"cleveland", "146023", "Piet Mondrian", "Field with Young Trees: contrasts Mondrian's earlier landscape painting with later abstraction."},
	{"cleveland", "135371", "Piet Mondrian", "Chrysanthemum: a focused natural-form study, distinct from Mondrian's geometric compositions."},
	{"cleveland", "124076", "Fra Angelico", "Coronation of the Virgin: a second devotional composition for comparison with the NGA Madonna."},
	{"smk", "KMS3272", "Alfred Sisley", "Waterworks at Bougival: a French Impressionist work held in a European museum, selected for river light and industrial landscape."},
}

type coverageEntry struct {
	Pick                                                                                        coveragePick
	Candidate                                                                                   candidate
	Accession, Page, ImageURL, ImagePage, Provider, Rights, License, LicenseURL, Policy, Credit string
	Retrieved                                                                                   time.Time
	Raw                                                                                         map[string]any
}
type coverageSelection struct {
	Version  string
	Created  time.Time
	Entries  []coverageEntry
	Deferred []string
}

func str(m map[string]any, k string) string { s, _ := m[k].(string); return s }
func schemeFor(s string) string {
	switch s {
	case "icons-athens-commons":
		return "european-icons-athens-object"
	case "popular-karlsruhe-next":
		return "european-popular-karlsruhe-next-museum-object"
	case "popular-karlsruhe":
		return "european-popular-karlsruhe-museum-object"
	case "popular-poldi":
		return "european-popular-poldi-museum-object"
	case "popular-nivaagaard":
		return "european-popular-nivaagaard-museum-object"
	case "pinakothek-durer-alte":
		return "european-popular-durer-alte-pinakothek-object"
	case "pinakothek-durer-gnm":
		return "european-popular-durer-germanisches-nationalmuseum-object"
	case "pinakothek-durer-augsburg":
		return "european-popular-durer-staatsgalerie-katharinenkirche-augsburg-object"
	case "pinakothek-alte":
		return "european-alte-object"
	case "pinakothek-neue":
		return "european-neue-object"
	case "chicago":
		return "european-chicago-art-institute-of-chicago-object"
	case "commons-met":
		return "european-met-the-met-object"
	case "commons-met-highlight":
		return "met-object"
	case "nga":
		return "european-nga-object"
	case "met":
		return "european-met-the-met-object"
	case "cleveland":
		return "european-cleveland-cleveland-museum-of-art-object"
	case "smk":
		return "european-smk-statens-museum-for-kunst-object"
	}
	return ""
}
func coverageCandidate(ctx context.Context, p *pgxpool.Pool, pick coveragePick) (coverageEntry, error) {
	if pick == athensIconPick {
		return athensIconCandidate(ctx, p)
	}
	x := coverageEntry{Pick: pick}
	if isPopularImagePick(pick) {
		var popular bool
		if err := p.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM artist_discovery_selection d JOIN artists a ON a.id=d.artist_id WHERE d.is_popular AND a.display_name=$1)`, pick.Artist).Scan(&popular); err != nil {
			return x, err
		}
		if !popular {
			return x, errors.New("selected artist is no longer popular")
		}
	}
	c := &x.Candidate
	e := p.QueryRow(ctx, `SELECT a.id::text,e.scheme,e.external_id,a.current_institution_id::text,e.source_id::text,a.title,p.display_name,a.primary_media_id IS NOT NULL,`+fingerprintSQL+`,a.accession_number,e.canonical_url
 FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id JOIN artwork_artists aa ON aa.artwork_id=a.id AND aa.attribution_role='primary' JOIN artists p ON p.id=aa.artist_id JOIN sources s ON s.id=e.source_id AND s.is_active
 WHERE e.entity_type='artwork' AND e.scheme=$1 AND e.external_id=$2 AND p.display_name=$3 AND p.status<>'archived' AND a.status='review'
 AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
 AND EXISTS(SELECT 1 FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.institution_id=a.current_institution_id AND l.claim_type='holding' AND l.review_state='accepted')`, schemeFor(pick.Source), pick.Object, pick.Artist).Scan(&c.ID, &c.Scheme, &c.Object, &c.Institution, &c.SourceID, &c.Title, &c.Artist, &c.HasImage, &c.Fingerprint, &x.Accession, &x.Page)
	if e == nil {
		for _, selected := range popularCyclePicks {
			if pick == selected {
				facts := popularCycleFacts[pick.Object]
				var matches bool
				e = p.QueryRow(ctx, `SELECT creation_year_start=$2 AND creation_year_end=$3 FROM artworks WHERE id=$1`, c.ID, facts.First, facts.Last).Scan(&matches)
				if e == nil && !matches {
					e = errors.New("popular cycle source and local creation dates differ")
				}
			}
		}
	}
	return x, e
}
func stageCoverage(ctx context.Context, p *pgxpool.Pool, root, out string) error {
	return stageCoveragePicks(ctx, p, root, out, coveragePicks)
}

func stageCoveragePicks(ctx context.Context, p *pgxpool.Pool, root, out string, picks []coveragePick) error {
	s := coverageSelection{Version: coverageVersion, Created: time.Now().UTC(), Entries: []coverageEntry{}, Deferred: []string{}}
	f := newFetcher()
	pending := []coverageEntry{}
	for _, pick := range picks {
		x, e := coverageCandidate(ctx, p, pick)
		if e != nil {
			s.Deferred = append(s.Deferred, pick.Source+":"+pick.Object+": database identity/holding/date review: "+e.Error())
			continue
		}
		if !x.Candidate.HasImage {
			pending = append(pending, x)
		}
	}
	// NGA's official independently published metadata feed, not a mirror/proxy of
	// its blocked website. Only selected exact object IDs are retained for images.
	feedPath := filepath.Join(root, "content/imports/painter-coverage-images-20260910/published_images.csv")
	feed, e := os.ReadFile(feedPath)
	ngaRows := map[string][]map[string]any{}
	ngaAt := time.Now().UTC()
	existingFeed := e == nil
	if existingFeed {
		b, err := os.ReadFile(feedPath + ".snapshot.json")
		if err != nil {
			return err
		}
		var snap struct {
			URL string    `json:"url"`
			SHA string    `json:"sha256"`
			At  time.Time `json:"retrieved_at"`
		}
		if err = json.Unmarshal(b, &snap); err != nil {
			return err
		}
		if snap.URL != ngaImageFeed || hash(feed) != snap.SHA || time.Since(snap.At) > 24*time.Hour || time.Until(snap.At) > 5*time.Minute {
			return errors.New("changed or stale NGA snapshot")
		}
		ngaAt = snap.At
	} else if errors.Is(e, os.ErrNotExist) {
		feed, e = f.get(ctx, ngaImageFeed, 100<<20)
		ngaAt = time.Now().UTC()
	} else {
		return e
	}
	if e != nil {
		s.Deferred = append(s.Deferred, "NGA official image metadata feed unavailable: "+e.Error())
	} else {
		if !existingFeed {
			if e = writeNew(feedPath, feed); e != nil {
				return e
			}
			if e = save(feedPath+".snapshot.json", map[string]any{"url": ngaImageFeed, "revision": ngaRevision, "retrieved_at": ngaAt, "sha256": hash(feed), "bytes": len(feed)}); e != nil {
				return e
			}
		}
		want := map[string]bool{}
		for _, x := range pending {
			if x.Pick.Source == "nga" {
				want[x.Pick.Object] = true
			}
		}
		r := csv.NewReader(bytes.NewReader(feed))
		h, e := r.Read()
		if e != nil {
			return e
		}
		for {
			v, e := r.Read()
			if e == io.EOF {
				break
			}
			if e != nil {
				return e
			}
			m := map[string]any{}
			for i, k := range h {
				m[k] = v[i]
			}
			if want[str(m, "depictstmsobjectid")] && str(m, "viewtype") == "primary" {
				ngaRows[str(m, "depictstmsobjectid")] = append(ngaRows[str(m, "depictstmsobjectid")], m)
			}
		}
	}
	for _, x := range pending {
		pick := x.Pick
		x.Retrieved = time.Now().UTC()
		x.Provider = map[string]string{"nga": "National Gallery of Art", "met": "The Metropolitan Museum of Art", "cleveland": "Cleveland Museum of Art", "smk": "Statens Museum for Kunst"}[pick.Source]
		switch pick.Source {
		case "commons-met", "commons-met-highlight":
			if e = stageCommons(ctx, f, &x); e != nil {
				s.Deferred = append(s.Deferred, pick.Source+":"+pick.Object+": "+e.Error())
				continue
			}
		case "nga":
			rows := ngaRows[pick.Object]
			if len(rows) != 1 {
				s.Deferred = append(s.Deferred, "nga:"+pick.Object+": primary image absent or ambiguous")
				continue
			}
			x.Raw = rows[0]
			x.Retrieved = ngaAt
			x.ImageURL = str(x.Raw, "iiifurl") + "/full/!600,600/0/default.jpg"
			x.Rights = "licensed"
			x.License = "NGA Open Access — unrestricted reuse"
			x.LicenseURL = ngaPolicy
			x.Policy = ngaPolicy
			x.ImagePage = x.Page
			x.Credit = x.Candidate.Artist + ". " + x.Candidate.Title + ". National Gallery of Art, Washington, " + x.Accession + "."
		case "met", "cleveland":
			raw := "https://collectionapi.metmuseum.org/public/collection/v1/objects/" + pick.Object
			if pick.Source == "cleveland" {
				raw = "https://openaccess-api.clevelandart.org/api/artworks/" + pick.Object
			}
			b, e := f.get(ctx, raw, 4<<20)
			if e != nil {
				s.Deferred = append(s.Deferred, pick.Source+":"+pick.Object+": "+e.Error())
				continue
			}
			x.Retrieved = time.Now().UTC()
			var m map[string]any
			if e = json.Unmarshal(b, &m); e != nil {
				return e
			}
			if pick.Source == "cleveland" {
				m, _ = m["data"].(map[string]any)
			}
			var w ingest.Work
			if pick.Source == "met" {
				w = ingest.NormalizeMet(m)
				x.Policy = "https://www.metmuseum.org/hubs/open-access"
			} else {
				w = ingest.NormalizeCleveland(m)
				x.Policy = "https://www.clevelandart.org/open-access"
			}
			if w.ID != pick.Object || w.Accession != x.Accession || strings.TrimSpace(w.Title) != strings.TrimSpace(x.Candidate.Title) || catalog.CreationScope(w.First, w.Last, w.Precision) != "eligible" {
				s.Deferred = append(s.Deferred, pick.Source+":"+pick.Object+": source identity/date changed")
				continue
			}
			x.Raw = m
			x.ImageURL = w.ImageURL
			x.ImagePage = w.URL
			x.Credit = w.Credit + ". " + x.Provider + "."
			x.Rights = w.Rights
			x.License = "CC0 1.0"
			x.LicenseURL = "https://creativecommons.org/publicdomain/zero/1.0/"
		case "smk":
			// Reuse today's already-reviewed, checksum-pinned selected source capture.
			dir := filepath.Join(root, "docs/research/europe-ui-20260910/smk-v1")
			mb, e := os.ReadFile(filepath.Join(dir, "manifest.json"))
			if e != nil {
				return e
			}
			if hash(mb) != "5ca7c08c06568ffeec711ec88f5ec7f525ee178913dee45918d7000df67edd53" {
				return errors.New("SMK manifest changed")
			}
			var manifest struct {
				Chunks []struct {
					File string
					SHA  string `json:"sha256"`
				}
			}
			if e = json.Unmarshal(mb, &manifest); e != nil {
				return e
			}
			for _, ch := range manifest.Chunks {
				if filepath.Base(ch.File) != ch.File {
					return errors.New("unsafe chunk")
				}
				cb, e := os.ReadFile(filepath.Join(dir, ch.File))
				if e != nil || hash(cb) != ch.SHA {
					return errors.New("SMK chunk mismatch")
				}
				var chunk struct {
					Works []struct {
						Raw map[string]any `json:"source_raw"`
					}
				}
				if e = json.Unmarshal(cb, &chunk); e != nil {
					return e
				}
				for _, w := range chunk.Works {
					if str(w.Raw, "object_number") == pick.Object {
						x.Raw = w.Raw
					}
				}
			}
			sb, e := os.ReadFile(filepath.Join(root, "content/imports/europe-smk-20260910/page-001.json.snapshot.json"))
			if e != nil {
				return e
			}
			var snap struct {
				At time.Time `json:"retrieved_at"`
			}
			if e = json.Unmarshal(sb, &snap); e != nil {
				return e
			}
			x.Retrieved = snap.At
			x.ImageURL = str(x.Raw, "image_iiif_id") + "/full/!700,700/0/default.jpg"
			x.ImagePage = x.Page
			x.Rights = "public_domain"
			x.License = "Public Domain Mark 1.0"
			x.LicenseURL = "https://creativecommons.org/publicdomain/mark/1.0/"
			x.Policy = x.LicenseURL
			x.Credit = x.Candidate.Artist + ". " + x.Candidate.Title + ". SMK, Copenhagen."
		}
		if e := validateCoverageEntry(x); e != nil {
			s.Deferred = append(s.Deferred, pick.Source+":"+pick.Object+": "+e.Error())
			continue
		}
		duplicate := false
		for _, existing := range s.Entries {
			if existing.Candidate.ID == x.Candidate.ID {
				duplicate = true
			}
		}
		if !duplicate {
			s.Entries = append(s.Entries, x)
		}
	}
	if e = save(out, s); e != nil {
		return e
	}
	b, e := os.ReadFile(out)
	if e != nil {
		return e
	}
	fmt.Printf("Staged %d selected images; %d deferrals. SHA256 %s. No image downloads or database writes.\n", len(s.Entries), len(s.Deferred), hash(b))
	return nil
}

func validateCoverageEntry(x coverageEntry) error {
	imageFocusAllowed := false
	for _, p := range imageFocusSMKPicks {
		if p == x.Pick {
			if err := validatePopularSMKMetadata(x); err != nil {
				return err
			}
			imageFocusAllowed = true
		}
	}
	for _, p := range smkMatissePicks {
		if p == x.Pick {
			if err := validatePopularSMKMetadata(x); err != nil {
				return err
			}
		}
	}
	for _, p := range popularCyclePicks {
		if p == x.Pick {
			if err := validatePopularCycleMetadata(x); err != nil {
				return err
			}
		}
	}
	for _, p := range popularSMKPicks {
		if p == x.Pick {
			if err := validatePopularSMKMetadata(x); err != nil {
				return err
			}
		}
	}
	allowedPick := isPopularImagePick(x.Pick) || x.Pick == athensIconPick || imageFocusAllowed
	for _, p := range coveragePicks {
		if p == x.Pick {
			allowedPick = true
		}
	}
	for _, p := range roundTwoPicks {
		if p == x.Pick {
			allowedPick = true
			if e := validateRoundTwoMetadata(x); e != nil {
				return e
			}
		}
	}
	c := x.Candidate
	if !allowedPick || c.Object != x.Pick.Object || c.Scheme != schemeFor(x.Pick.Source) || c.Artist != x.Pick.Artist || c.ID == "" || c.Fingerprint == "" || c.SourceID == "" || c.Institution == "" || time.Since(x.Retrieved) > 24*time.Hour || time.Until(x.Retrieved) > 5*time.Minute {
		return errors.New("invalid or stale selection/identity")
	}
	u, e := url.Parse(x.ImageURL)
	if e != nil || u.Scheme != "https" || u.User != nil || u.Port() != "" {
		return errors.New("no permitted image")
	}
	switch x.Pick.Source {
	case "icons-athens-commons":
		return validateAthensIcon(x)
	case "popular-karlsruhe", "popular-karlsruhe-next":
		return validateKarlsruhe(x)
	case "popular-poldi":
		return validatePoldiCommons(x)
	case "popular-nivaagaard":
		return validateNivaagaard(x)
	case "pinakothek-alte", "pinakothek-neue", "pinakothek-durer-alte", "pinakothek-durer-gnm", "pinakothek-durer-augsburg":
		return validatePinakothek(x)
	case "chicago":
		return validateChicago(x)
	case "commons-met", "commons-met-highlight":
		return validateCommons(x)
	case "nga":
		if str(x.Raw, "openaccess") != "1" || str(x.Raw, "viewtype") != "primary" || str(x.Raw, "depictstmsobjectid") != c.Object || !regexp.MustCompile(`^https://api\.nga\.gov/iiif/[a-f0-9-]{36}/full/!600,600/0/default\.jpg$`).MatchString(x.ImageURL) || str(x.Raw, "iiifurl") != "https://api.nga.gov/iiif/"+str(x.Raw, "uuid") || x.ImageURL != str(x.Raw, "iiifurl")+"/full/!600,600/0/default.jpg" || x.Rights != "licensed" || x.Policy != ngaPolicy || x.LicenseURL != ngaPolicy {
			return errors.New("NGA primary-image permission absent")
		}
	case "met", "cleveland":
		var w ingest.Work
		host := "images.metmuseum.org"
		policy := "https://www.metmuseum.org/hubs/open-access"
		if x.Pick.Source == "met" {
			w = ingest.NormalizeMet(x.Raw)
		} else {
			w = ingest.NormalizeCleveland(x.Raw)
			host = "openaccess-cdn.clevelandart.org"
			policy = "https://www.clevelandart.org/open-access"
		}
		if w.ID != c.Object || w.Accession != x.Accession || strings.TrimSpace(w.Title) != strings.TrimSpace(c.Title) || w.ImageURL != x.ImageURL || w.URL != x.ImagePage || u.Host != host || w.Rights != "cc0" || strings.TrimSpace(w.Copyright) != "" || x.Rights != "cc0" || x.Policy != policy || x.LicenseURL != "https://creativecommons.org/publicdomain/zero/1.0/" || catalog.CreationScope(w.First, w.Last, w.Precision) != "eligible" {
			return errors.New("museum per-image permission absent or identity conflict")
		}
	case "smk":
		if x.Raw["has_image"] != true || x.Raw["public_domain"] != true || str(x.Raw, "rights") != "https://creativecommons.org/publicdomain/mark/1.0/" || str(x.Raw, "object_number") != c.Object || str(x.Raw, "frontend_url") != x.Page || !regexp.MustCompile(`^https://iip\.smk\.dk/iiif/jp2/[A-Za-z0-9_.-]+/full/!700,700/0/default\.jpg$`).MatchString(x.ImageURL) || x.ImageURL != str(x.Raw, "image_iiif_id")+"/full/!700,700/0/default.jpg" || x.Rights != "public_domain" || x.Policy != str(x.Raw, "rights") || x.LicenseURL != x.Policy {
			return errors.New("SMK image permission/identity absent")
		}
	default:
		return errors.New("unapproved provider")
	}
	return nil
}

func applyCoverage(ctx context.Context, p *pgxpool.Pool, root, input, pin, out string, do bool) (err error) {
	b, e := os.ReadFile(input)
	if e != nil {
		return e
	}
	if len(pin) != 64 || hash(b) != pin {
		return errors.New("selection pin mismatch")
	}
	var s coverageSelection
	if e = json.Unmarshal(b, &s); e != nil {
		return e
	}
	if s.Version != coverageVersion || len(s.Entries) == 0 || len(s.Entries) > 50 || time.Since(s.Created) > 24*time.Hour || time.Until(s.Created) > 5*time.Minute {
		return errors.New("stale/invalid coverage selection")
	}
	seen := map[string]bool{}
	for _, x := range s.Entries {
		if seen[x.Candidate.ID] {
			return errors.New("duplicate work")
		}
		seen[x.Candidate.ID] = true
		if e = validateCoverageEntry(x); e != nil {
			return e
		}
	}
	if e = os.MkdirAll(filepath.Dir(out), 0755); e != nil {
		return e
	}
	f, e := os.OpenFile(out, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if e != nil {
		return e
	}
	defer f.Close()
	r := receipt{Version: coverageVersion, SelectionSHA: pin, Applied: do, Results: []result{}}
	defer func() {
		if e := json.NewEncoder(f).Encode(r); err == nil {
			err = e
		}
	}()
	fetch := newFetcher()
	for _, x := range s.Entries {
		c := x.Candidate
		res := result{Object: x.Pick.Source + ":" + c.Object, ArtworkID: c.ID, Title: c.Title, Artist: c.Artist}
		now, e := coverageCandidate(ctx, p, x.Pick)
		if e != nil || now.Candidate.Fingerprint != c.Fingerprint || now.Candidate.ID != c.ID || now.Candidate.SourceID != c.SourceID || now.Page != x.Page || now.Accession != x.Accession {
			return fmt.Errorf("target changed: %s: %v", res.Object, e)
		}
		if now.Candidate.HasImage {
			res.ImageOutcome = "existing_media_preserved"
			r.Results = append(r.Results, res)
			continue
		}
		if !do {
			res.ImageOutcome = "ready"
			r.Results = append(r.Results, res)
			continue
		}
		original, e := fetch.get(ctx, x.ImageURL, 4<<20)
		var data []byte
		if e == nil {
			data, res.Width, res.Height, res.Quality, e = compress(original)
		}
		if e != nil {
			res.ImageOutcome = "download_deferred"
			res.Error = e.Error()
			r.Results = append(r.Results, res)
			continue
		}
		res.Hash = hash(data)
		res.Bytes = len(data)
		res.Path = "/assets/artworks/imported/" + x.Pick.Source + "-study-" + res.Hash + ".jpg"
		path := filepath.Join(root, "apps/web/public", res.Path)
		if old, e := os.ReadFile(path); e == nil {
			if hash(old) != res.Hash {
				return errors.New("existing asset collision")
			}
		} else if errors.Is(e, os.ErrNotExist) {
			if e = writeNew(path, data); e != nil {
				return e
			}
		} else {
			return e
		}
		tx, e := p.Begin(ctx)
		if e != nil {
			return e
		}
		e = func() error {
			defer tx.Rollback(ctx)
			var fp string
			var current *string
			if e := tx.QueryRow(ctx, `SELECT `+fingerprintSQL+`,a.primary_media_id::text FROM artworks a JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artwork' JOIN sources s ON s.id=e.source_id AND s.is_active WHERE a.id=$1 AND a.status='review' AND e.scheme=$2 AND e.external_id=$3 AND e.source_id=$4 AND a.current_institution_id=$5 AND a.accession_number=$6 AND e.canonical_url=$7 FOR UPDATE OF a`, c.ID, c.Scheme, c.Object, c.SourceID, c.Institution, x.Accession, x.Page).Scan(&fp, &current); e != nil {
				return e
			}
			if fp != c.Fingerprint {
				return errors.New("concurrent edit: derivative left unattached")
			}
			if current != nil {
				res.ImageOutcome = "existing_media_preserved"
				return nil
			}
			evidence := jsonBytes(map[string]any{"object": x.Raw, "selection": x.Pick, "selection_kind": "editorial study selection, not a museum designation or owner must-see change", "source_snapshot_at": x.Retrieved, "selection_sha256": pin, "source_sha256": hash(original), "source_bytes": len(original), "derivative_sha256": res.Hash, "derivative_bytes": res.Bytes, "width": res.Width, "height": res.Height, "jpeg_quality": res.Quality, "transform": "Full source frame; aspect-preserving resize and JPEG compression; no AI or extra crop."})
			var mid string
			if e := tx.QueryRow(ctx, `INSERT INTO media_assets(storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by) VALUES('local',$1,$2,$3,'image/jpeg',$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,now(),$14,$15) RETURNING id::text`, res.Path, x.ImagePage, x.Provider, res.Width, res.Height, res.Bytes, res.Hash, c.Title+" — "+c.Artist, x.Rights, x.License, x.LicenseURL, c.Artist, x.Credit+" "+x.License+"; compressed study reproduction.", x.Retrieved, actor).Scan(&mid); e != nil {
				return e
			}
			if _, e = tx.Exec(ctx, `INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES($1,$2,$3,$4,$5,$6,'Exact source identity and explicit per-image reuse permission; editorial study selection only',$7,$8,$9)`, mid, c.SourceID, c.Object, hash(jsonBytes(x.Raw)), x.ImageURL, x.Policy, coverageVersion, x.Retrieved, evidence); e != nil {
				return e
			}
			if _, e = tx.Exec(ctx, `UPDATE artworks SET primary_media_id=$2,revision=revision+1,updated_at=now(),updated_by=$3 WHERE id=$1 AND primary_media_id IS NULL`, c.ID, mid, actor); e != nil {
				return e
			}
			if e = tx.Commit(ctx); e == nil {
				res.ImageOutcome = "attached"
			}
			return e
		}()
		if e != nil {
			res.Error = e.Error()
			r.Results = append(r.Results, res)
			return e
		}
		r.Results = append(r.Results, res)
		fmt.Printf("%s %s: %s (%d bytes)\n", res.Object, res.Artist, res.ImageOutcome, res.Bytes)
	}
	return nil
}
