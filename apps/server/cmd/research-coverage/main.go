// research-coverage collects metadata snapshots only. It never writes to a DB,
// downloads images, follows catalogue website links, or enables a connector.
package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"time"
)

const ngaRevision = "f088836026d09d0d25001814fba0f84d757ebe62"
const agent = "ArtlineMuseumResearch/1.0 (local metadata research; https://github.com/vadim-dulub/artline)"

type snapshot struct {
	URL       string    `json:"url"`
	SHA       string    `json:"sha256"`
	Bytes     int64     `json:"bytes"`
	Retrieved time.Time `json:"retrieved_at"`
}

func hashFile(path string) (string, int64, error) {
	f, e := os.Open(path)
	if e != nil {
		return "", 0, e
	}
	defer f.Close()
	h := sha256.New()
	n, e := io.Copy(h, f)
	return hex.EncodeToString(h.Sum(nil)), n, e
}

func save(path string, v any) error {
	b, e := json.MarshalIndent(v, "", "  ")
	if e != nil {
		return e
	}
	b = append(b, '\n')
	if old, e := os.ReadFile(path); e == nil {
		if string(old) == string(b) {
			return nil
		}
		return fmt.Errorf("refusing to change existing snapshot %s", path)
	} else if !errors.Is(e, os.ErrNotExist) {
		return e
	}
	f, e := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return e
	}
	defer f.Close()
	_, e = f.Write(b)
	return e
}

func fetch(ctx context.Context, path, rawURL string, limit int64) error {
	if b, e := os.ReadFile(path + ".snapshot.json"); e == nil {
		var s snapshot
		if e = json.Unmarshal(b, &s); e != nil {
			return e
		}
		h, n, e := hashFile(path)
		if e != nil {
			return e
		}
		if h != s.SHA || n != s.Bytes || s.URL != rawURL {
			return fmt.Errorf("cache identity mismatch %s", path)
		}
		log.Printf("Verified cached %s (%d bytes)", filepath.Base(path), n)
		return nil
	}
	if _, e := os.Stat(path); e == nil {
		return fmt.Errorf("unmanifested existing file %s; manual review required", path)
	}
	u, e := url.Parse(rawURL)
	if e != nil {
		return e
	}
	allowed := u.Host == "query.wikidata.org" || u.Host == "raw.githubusercontent.com" || u.Host == "data.culture.gouv.fr" || u.Host == "ministere-culture.s3.sbg.io.cloud.ovh.net" || campaignURL(u) || (u.Host == "www.dati.lombardia.it" && (u.Path == "/api/views/5gfm-gsfr.json" || u.Path == "/resource/5gfm-gsfr.json"))
	allowed = allowed || u.Host == "data.ng.ac.uk" && u.Path == "/es/public/_search"
	allowed = allowed || poldiCommonsAllowed(rawURL)
	if u.Scheme != "https" || !allowed || u.User != nil {
		return errors.New("source not allowlisted")
	}
	timeout := 55 * time.Second
	if limit > 100<<20 {
		timeout = 5 * time.Minute
	}
	client := &http.Client{Timeout: timeout, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	req, e := http.NewRequestWithContext(ctx, "GET", rawURL, nil)
	if e != nil {
		return e
	}
	req.Header.Set("User-Agent", agent)
	req.Header.Set("Accept", "application/json,text/csv,text/plain")
	resp, e := client.Do(req)
	if e != nil {
		return e
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return fmt.Errorf("HTTP %d %s (no automatic retry)", resp.StatusCode, u.Host)
	}
	if resp.ContentLength > limit {
		return errors.New("response exceeds byte budget")
	}
	if strings.Contains(resp.Header.Get("Content-Type"), "text/html") {
		return errors.New("unexpected HTML instead of metadata")
	}
	f, e := os.CreateTemp(filepath.Dir(path), ".metadata-*")
	if e != nil {
		return e
	}
	temp := f.Name()
	defer os.Remove(temp)
	n, e := io.Copy(f, io.LimitReader(resp.Body, limit+1))
	closeErr := f.Close()
	if e != nil {
		return e
	}
	if closeErr != nil {
		return closeErr
	}
	if n > limit {
		return errors.New("response exceeds byte budget")
	}
	if strings.HasSuffix(path, ".json") {
		b, e := os.ReadFile(temp)
		if e != nil {
			return e
		}
		if !json.Valid(b) {
			return errors.New("invalid source JSON")
		}
	}
	h, n, e := hashFile(temp)
	if e != nil {
		return e
	}
	// Link is atomic and refuses overwrite, including concurrent collectors.
	if e = os.Link(temp, path); e != nil {
		return e
	}
	if e = save(path+".snapshot.json", map[string]any{"url": rawURL, "sha256": h, "bytes": n, "retrieved_at": time.Now().UTC(), "last_modified": resp.Header.Get("Last-Modified"), "etag": resp.Header.Get("ETag")}); e != nil {
		return e
	}
	log.Printf("Saved %s (%d bytes)", filepath.Base(path), n)
	return nil
}

// M49 Europe plus separately labelled boundary/transcontinental candidates.
// Country classification is discovery scope, not proof of a venue in Europe.
var countries = strings.Fields("US AL AD AT BY BE BA BG HR CZ DK EE FI FR DE GR VA HU IS IE IT LV LI LT LU MT MD MC ME NL MK NO PL PT RO RU SM RS SK SI ES SE CH UA GB AX FO GG IM JE SJ GI CY TR AM AZ GE XK")

func directory(ctx context.Context, out string) error {
	type coverage struct {
		Country string `json:"country"`
		State   string `json:"state"`
		Error   string `json:"error,omitempty"`
	}
	result := []coverage{}
	for _, code := range countries {
		q := fmt.Sprintf(`SELECT DISTINCT ?museum ?museumLabel ?iso ?website ?place ?placeLabel ?coordinates ?closed ?parent WHERE {
    ?country wdt:P297 %q. ?museum wdt:P17 ?country; wdt:P31/wdt:P279* wd:Q207694.
    BIND(%q AS ?iso) OPTIONAL {?museum wdt:P856 ?website} OPTIONAL {?museum wdt:P131 ?place}
    OPTIONAL {?museum wdt:P625 ?coordinates} OPTIONAL {?museum wdt:P576 ?closed}
    OPTIONAL {?museum wdt:P361 ?parent}
    SERVICE wikibase:label {bd:serviceParam wikibase:language "en,fr,de,es,it"}
  } LIMIT 20001`, code, code)
		raw := "https://query.wikidata.org/sparql?" + url.Values{"query": {q}, "format": {"json"}}.Encode()
		e := fetch(ctx, filepath.Join(out, "wikidata-"+code+".json"), raw, 15<<20)
		if e != nil {
			log.Printf("Country %s deferred: %v", code, e)
			result = append(result, coverage{code, "failed", e.Error()})
			if strings.Contains(e.Error(), "HTTP 429") || strings.Contains(e.Error(), "HTTP 403") {
				for _, remaining := range countries[len(result):] {
					result = append(result, coverage{remaining, "not_requested", "source paused after access/rate-limit response"})
				}
				break
			}
		} else {
			result = append(result, coverage{Country: code, State: "retrieved"})
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(500 * time.Millisecond):
		}
	}
	return save(filepath.Join(out, "country-requests.json"), result)
}

func main() {
	mode := flag.String("mode", "directory", "directory or nga")
	root := flag.String("root", "../..", "Artline root for offline assembly")
	countryList := flag.String("countries", "", "Comma-separated scope for the one bounded basic-query retry")
	out := flag.String("out", "", "New snapshot directory; existing verified snapshots are reusable")
	flag.Parse()
	if *out == "" {
		log.Fatal("-out required")
	}
	if e := os.MkdirAll(*out, 0700); e != nil {
		log.Fatal(e)
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()
	switch *mode {
	case "capture-athens-followup":
		if e := captureAthensFollowup(ctx, *out); e != nil {
			log.Fatal(e)
		}
	case "capture-athens-icon-image":
		if e := fetch(ctx, filepath.Join(*out, "crucifixion-source.jpg"), athensIconCommonsThumb, 4<<20); e != nil {
			log.Fatal(e)
		}
	case "capture-athens-icon-commons":
		if e := fetch(ctx, filepath.Join(*out, "crucifixion.json"), poldiCommonsURL(athensIconCommonsFile), 2<<20); e != nil {
			log.Fatal(e)
		}
	case "capture-karlsruhe-next":
		if e := captureReviewedPages(ctx, *out, karlsruheNextPages); e != nil {
			log.Fatal(e)
		}
	case "assemble-karlsruhe-next":
		if e := assembleKarlsruheBatch(ctx, *root, *out, "popular-karlsruhe-next", karlsruheNextFacts); e != nil {
			log.Fatal(e)
		}
	case "assemble-karlsruhe":
		if e := assembleKarlsruhe(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "capture-karlsruhe":
		if e := captureReviewedPages(ctx, *out, karlsruhePages); e != nil {
			log.Fatal(e)
		}
	case "capture-poldi-commons":
		if e := capturePoldiCommons(ctx, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-poldi":
		if e := assemblePoldi(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "capture-poldi-notices":
		if e := captureReviewedPages(ctx, *out, []popularPage{
			{"robots.txt", "https://museopoldipezzoli.it/robots.txt"},
			{"piero-nicholas.html", "https://museopoldipezzoli.it/en/scopri/collezioni/capolavori/opera/san-nicola-da-tolentino/"},
			{"bellini-pietatis.html", "https://museopoldipezzoli.it/en/scopri/collezioni/capolavori/opera/imago-pietatis/"},
		}); e != nil {
			log.Fatal(e)
		}
	case "assemble-athens-entombment":
		if e := assemblePopularAthensBatch(ctx, *root, *out, true, true); e != nil {
			log.Fatal(e)
		}
	case "capture-athens-entombment":
		if e := captureReviewedPages(ctx, *out, []popularPage{{"entombment.html", "https://www.nationalgallery.gr/en/artwork/the-entombment-of-christ/"}}); e != nil {
			log.Fatal(e)
		}
	case "assemble-popular-durer":
		if e := assemblePopularDurer(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "capture-durer-pages":
		if e := captureDurerPages(ctx, *out); e != nil {
			log.Fatal(e)
		}
	case "capture-athens-preflight":
		if e := captureAthensPreflight(ctx, *out); e != nil {
			log.Fatal(e)
		}
	case "capture-athens-objects":
		if e := captureAthensObjects(ctx, *out); e != nil {
			log.Fatal(e)
		}
	case "capture-repin-notices":
		if e := captureRepinNotices(ctx, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-popular-repin":
		if e := assemblePopularRepin(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-popular-goulandris":
		if e := assemblePopularAthens(ctx, *root, *out, false); e != nil {
			log.Fatal(e)
		}
	case "assemble-popular-athens-national":
		if e := assemblePopularAthens(ctx, *root, *out, true); e != nil {
			log.Fatal(e)
		}
	case "capture-ng-aliases":
		if e := captureNGAliases(ctx, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-ng-aliases":
		if e := assembleNGCohort(ctx, *root, *out, filepath.Join(*root, "content/imports/popular-europe-session-20260911/ng-aliases"), "popular-ng-aliases", true); e != nil {
			log.Fatal(e)
		}
	case "assemble-popular-caen":
		if e := assemblePopularCaen(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "report-popular-session":
		if e := reportPopularSession(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "audit-popular-caen":
		if e := auditPopularCaen(*root, *out); e != nil {
			log.Fatal(e)
		}
	case "capture-popular-pages-preflight", "capture-popular-pages":
		if e := capturePopularPages(ctx, *out, *mode == "capture-popular-pages-preflight"); e != nil {
			log.Fatal(e)
		}
	case "capture-popular-ng":
		if e := capturePopularNG(ctx, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-popular-ng":
		if e := assemblePopularNG(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-popular-marmottan-deposits":
		if e := assemblePopularMarmottanPass(ctx, *root, *out, true); e != nil {
			log.Fatal(e)
		}
	case "assemble-popular-marmottan":
		if e := assemblePopularMarmottan(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "audit-normandy":
		if e := auditNormandy(*root, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-normandy-joconde":
		if e := assembleNormandyJoconde(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-normandy-muma", "assemble-normandy-rouen":
		if e := assembleNormandy(ctx, *root, strings.TrimPrefix(*mode, "assemble-normandy-"), *out); e != nil {
			log.Fatal(e)
		}
	case "capture-rijks":
		if e := captureRijks(ctx, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-rijks":
		if e := assembleRijks(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "capture-image-focus-smk":
		if e := captureImageFocusSMK(ctx, *out); e != nil {
			log.Fatal(e)
		}
	case "capture-smk":
		if e := captureSMK(ctx, *out); e != nil {
			log.Fatal(e)
		}
	case "capture-smk-matisse":
		if e := captureSMKMatisse(ctx, *out); e != nil {
			log.Fatal(e)
		}
	case "capture-nivaagaard":
		if e := captureNivaagaard(ctx, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-nivaagaard":
		if e := assembleNivaagaard(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-smk":
		if e := assembleSMK(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-chicago":
		if e := assembleChicago(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "campaign-chicago-ranges":
		if e := captureChicagoRanges(ctx, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-cleveland":
		if e := assembleCleveland(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-lombardia":
		if e := assembleLombardia(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-met":
		if e := assembleMet(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "audit-met", "audit-cleveland", "audit-chicago", "audit-lombardia":
		if e := auditCampaign(*root, strings.TrimPrefix(*mode, "audit-"), *out); e != nil {
			log.Fatal(e)
		}
	case "campaign-met", "campaign-cleveland", "campaign-chicago", "campaign-lombardia":
		if e := captureCampaign(ctx, strings.TrimPrefix(*mode, "campaign-"), *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-kamis":
		if e := assembleKamis(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-joconde":
		if e := assembleJoconde(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-sirbec":
		if e := assembleSirbec(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "pushkin-kamis":
		if e := capturePushkinKamis(ctx, *out); e != nil {
			log.Fatal(e)
		}
	case "sirbec":
		if e := fetch(ctx, filepath.Join(*out, "dataset.json"), "https://www.dati.lombardia.it/api/views/5gfm-gsfr.json", 1<<20); e != nil {
			log.Fatal(e)
		}
		query := url.Values{"$where": {"ogtd in ('dipinto','disegno','stampa','acquerello')"}, "$order": {"idk"}, "$limit": {"50000"}}
		if e := fetch(ctx, filepath.Join(*out, "objects.json"), "https://www.dati.lombardia.it/resource/5gfm-gsfr.json?"+query.Encode(), 150<<20); e != nil {
			log.Fatal(e)
		}
	case "joconde-audit":
		if e := jocondeAudit(*root, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-nga-images":
		if e := assembleSelectedImages(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-pushkin":
		if e := assemblePushkin(*root, *out); e != nil {
			log.Fatal(e)
		}
	case "pushkin-json":
		if e := fetchSmallRanges(ctx, filepath.Join(*out, "masterpieces.json"), "https://pushkinmuseum.art/json/masterpieces.json", 0); e != nil {
			log.Fatal(e)
		}
	case "nga-image-sample":
		if e := fetchSmallRanges(ctx, filepath.Join(*out, "published_images_prefix.csv"), "https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/"+ngaRevision+"/data/published_images.csv", 256<<10); e != nil {
			log.Fatal(e)
		}
	case "assemble-directory":
		if e := assembleDirectory(*root, *out); e != nil {
			log.Fatal(e)
		}
	case "directory-basic":
		for _, code := range strings.Split(*countryList, ",") {
			if !strings.Contains(" "+strings.Join(countries, " ")+" ", " "+code+" ") || len(code) != 2 {
				log.Fatal("invalid country")
			}
			q := fmt.Sprintf(`SELECT DISTINCT ?museum ?museumLabel ?iso ?website WHERE {
 {SELECT DISTINCT ?museum WHERE {?country wdt:P297 %q. ?museum wdt:P17 ?country; wdt:P31/wdt:P279* wd:Q207694} LIMIT 10001}
 BIND(%q AS ?iso) OPTIONAL {?museum wdt:P856 ?website}
 SERVICE wikibase:label {bd:serviceParam wikibase:language "en,fr,de,es,it"}
 } LIMIT 20001`, code, code)
			u := "https://query.wikidata.org/sparql?" + url.Values{"query": {q}, "format": {"json"}}.Encode()
			if e := fetch(ctx, filepath.Join(*out, "wikidata-"+code+".json"), u, 15<<20); e != nil {
				log.Printf("Basic retry %s failed: %v", code, e)
				if strings.Contains(e.Error(), "HTTP 429") || strings.Contains(e.Error(), "HTTP 403") {
					break
				}
			}
			select {
			case <-ctx.Done():
				return
			case <-time.After(time.Second):
			}
		}
	case "assemble-nga":
		if e := assembleNGA(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "nga-scale-audit":
		if e := ngaScaleAudit(*root, *out); e != nil {
			log.Fatal(e)
		}
	case "assemble-nga-scale":
		if e := assembleNGAScale(ctx, *root, *out); e != nil {
			log.Fatal(e)
		}
	case "joconde":
		if e := fetch(ctx, filepath.Join(*out, "joconde.csv"), "https://ministere-culture.s3.sbg.io.cloud.ovh.net/POP/joconde.csv", 1500<<20); e != nil {
			log.Fatal(e)
		}
	case "nga-images":
		if e := fetch(ctx, filepath.Join(*out, "published_images.csv"), "https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/"+ngaRevision+"/data/published_images.csv", 120<<20); e != nil {
			log.Fatal(e)
		}
	case "france":
		if e := fetch(ctx, filepath.Join(*out, "museofile.csv"), "https://ministere-culture.s3.sbg.io.cloud.ovh.net/POP/museofile.csv", 30<<20); e != nil {
			log.Fatal(e)
		}
	case "directory":
		if e := directory(ctx, *out); e != nil {
			log.Fatal(e)
		}
	case "nga":
		for _, file := range []string{"objects.csv", "constituents.csv", "objects_constituents.csv", "objects_terms.csv", "object_associations.csv", "objects_text_entries.csv"} {
			raw := "https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/" + ngaRevision + "/data/" + file
			if e := fetch(ctx, filepath.Join(*out, file), raw, 100<<20); e != nil {
				log.Fatal(e)
			}
		}
		if e := fetch(ctx, filepath.Join(*out, "data-dictionary.txt"), "https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/"+ngaRevision+"/documentation/Data%20Dictionary.txt", 100<<10); e != nil {
			log.Fatal(e)
		}
	default:
		log.Fatal("unknown mode")
	}
}
