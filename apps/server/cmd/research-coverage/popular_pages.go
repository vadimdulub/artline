package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Closed source list: no redirects, retries, unrestricted crawler or images.
type popularPage struct{ File, URL string }

func capturePopularPages(ctx context.Context, out string, preflight bool) error {
	pages := []popularPage{
		{"caen-robots.txt", "https://mba.caen.fr/robots.txt"},
		{"pinakothek-robots.txt", "https://www.sammlung.pinakothek.de/robots.txt"},
		{"caen-legal.html", "https://mba.caen.fr/mentions-legales"},
		{"pinakothek-usage.html", "https://www.sammlung.pinakothek.de/de/usage"},
	}
	if !preflight {
		pages = []popularPage{
			{"caen-perugino-marriage.html", "https://mba.caen.fr/oeuvre/le-mariage-de-la-vierge"},
			{"caen-perugino-jerome.html", "https://mba.caen.fr/oeuvre/saint-jerome-dans-le-desert"},
			{"caen-veronese-antony.html", "https://mba.caen.fr/oeuvre/la-tentation-de-saint-antoine"},
			{"caen-tintoretto-descent.html", "https://mba.caen.fr/oeuvre/la-descente-de-croix"},
			{"pinakothek-durer-self.html", "https://www.sammlung.pinakothek.de/de/artwork/Qlx2QpQ4Xq"},
			{"pinakothek-pissarro-street.html", "https://www.sammlung.pinakothek.de/de/artwork/PdxzrBExw5"},
			{"pinakothek-rubens-judgment.html", "https://www.sammlung.pinakothek.de/de/artwork/Dj4mkQbL5A"},
			{"pinakothek-rembrandt-self.html", "https://www.sammlung.pinakothek.de/de/artwork/y7GE1PmGPV"},
			{"pinakothek-vangogh-sunflowers.html", "https://www.sammlung.pinakothek.de/de/artwork/Y0GR9B7LRX"},
			{"pinakothek-durer-artist.html", "https://www.sammlung.pinakothek.de/de/artist/2y7GEnY4PV"},
			{"pinakothek-greco-artist.html", "https://www.sammlung.pinakothek.de/de/artist/zA0GO7VGdp"},
		}
	}
	return captureReviewedPages(ctx, out, pages)
}

func captureReviewedPages(ctx context.Context, out string, pages []popularPage) error {
	if len(pages) < 1 || len(pages) > 25 {
		return fmt.Errorf("reviewed page batch ceiling")
	}
	if _, err := os.Stat(filepath.Join(out, "source-paused.json")); err == nil {
		return fmt.Errorf("saved source pause needs review")
	}
	client := &http.Client{Timeout: 30 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	last := map[string]time.Time{}
	receipts := []snapshot{}
	for _, page := range pages {
		u, err := url.Parse(page.URL)
		if err != nil {
			return err
		}
		if u.Scheme != "https" || u.User != nil || u.Port() != "" || u.Host != "mba.caen.fr" && u.Host != "www.sammlung.pinakothek.de" && u.Host != "goulandris.gr" && u.Host != "www.nationalgallery.gr" && u.Host != "rusmuseumvrm.ru" && u.Host != "nivaagaard.dk" && u.Host != "museopoldipezzoli.it" && !karlsruhePageAllowed(page.URL) {
			return fmt.Errorf("unapproved museum route")
		}
		file := filepath.Join(out, page.File)
		if _, err = os.Stat(file + ".snapshot.json"); err == nil {
			if err = verify(file); err != nil {
				return err
			}
			b, err := os.ReadFile(file + ".snapshot.json")
			if err != nil {
				return err
			}
			var receipt snapshot
			if json.Unmarshal(b, &receipt) != nil || receipt.URL != page.URL {
				return fmt.Errorf("cached page URL mismatch")
			}
			receipts = append(receipts, receipt)
			continue
		}
		if wait := 11*time.Second - time.Since(last[u.Host]); wait > 0 {
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(wait):
			}
		}
		req, err := http.NewRequestWithContext(ctx, "GET", page.URL, nil)
		if err != nil {
			return err
		}
		req.Header.Set("User-Agent", agent)
		res, err := client.Do(req)
		last[u.Host] = time.Now()
		if err != nil {
			return err
		}
		b, readErr := io.ReadAll(io.LimitReader(res.Body, (3<<20)+1))
		res.Body.Close()
		if readErr != nil {
			return readErr
		}
		if res.StatusCode != 200 {
			_ = save(filepath.Join(out, "source-paused.json"), map[string]any{"url": page.URL, "status": res.StatusCode, "at": time.Now().UTC(), "next": "Review source response; do not bypass denied routes."})
			return fmt.Errorf("HTTP %d from %s", res.StatusCode, u.Host)
		}
		if len(b) > 3<<20 {
			return fmt.Errorf("source page byte budget")
		}
		if !strings.HasSuffix(page.File, ".txt") && !strings.Contains(res.Header.Get("Content-Type"), "text/html") {
			return fmt.Errorf("unexpected page content")
		}
		f, err := os.OpenFile(file, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		if err != nil {
			return err
		}
		_, err = f.Write(b)
		ce := f.Close()
		if err != nil {
			return err
		}
		if ce != nil {
			return ce
		}
		sha, n, err := hashFile(file)
		if err != nil {
			return err
		}
		receipt := snapshot{URL: page.URL, SHA: sha, Bytes: n, Retrieved: time.Now().UTC()}
		if err = save(file+".snapshot.json", receipt); err != nil {
			return err
		}
		receipts = append(receipts, receipt)
		fmt.Printf("Captured %s, %d bytes\n", page.File, n)
	}
	return save(filepath.Join(out, "capture.json"), map[string]any{"scope": "closed reviewed page list, factual research only; no image binaries or database writes", "pages": pages, "new_receipts": receipts})
}

func captureNivaagaard(ctx context.Context, out string) error {
	pages := []popularPage{
		{"robots.txt", "https://nivaagaard.dk/robots.txt"},
		{"public-domain.html", "https://nivaagaard.dk/en/fri-download/"},
	}
	for _, slug := range []string{"anguissola-sofonisba", "bellini-giovanni", "rijn-rembrandt-harmensz-van", "gentileschi-artemisia", "lucas-cranach-the-elder", "lorrain-claude"} {
		pages = append(pages, popularPage{slug + ".html", "https://nivaagaard.dk/en/the-collection/" + slug + "/"})
	}
	return captureReviewedPages(ctx, out, pages)
}

func captureDurerPages(ctx context.Context, out string) error {
	// Exact links inspected in the official 44-record artist page. Copies,
	// multipart/recto-verso units and open/disjunctive dates remain deferred.
	pages := []popularPage{}
	for _, id := range []string{"Y0GRY2XLRX", "Pdxz0KvGw5", "QrLWeqA4NO", "o5xrQgP47X", "k2xnBjAxPd", "02LAWJX4yk", "M0xyZ1VLpl", "8MLv2rZLz3"} {
		pages = append(pages, popularPage{"durer-" + id + ".html", "https://www.sammlung.pinakothek.de/de/artwork/" + id})
	}
	return captureReviewedPages(ctx, out, pages)
}

func captureAthensPreflight(ctx context.Context, out string) error {
	return captureReviewedPages(ctx, out, []popularPage{
		{"goulandris-robots.txt", "https://goulandris.gr/robots.txt"},
		{"nationalgallery-robots.txt", "https://www.nationalgallery.gr/robots.txt"},
		{"goulandris-visitor-terms.html", "https://goulandris.gr/en/visitor-terms"},
		{"goulandris-privacy.html", "https://goulandris.gr/en/privacy-policy"},
		{"goulandris-highlights.html", "https://goulandris.gr/en/collection/highlights"},
		{"goulandris-collection.html", "https://goulandris.gr/en/collection/works-of-art"},
		{"nationalgallery-peter.html", "https://www.nationalgallery.gr/en/artwork/st-peter/"},
	})
}

func captureAthensObjects(ctx context.Context, out string) error {
	pages := []popularPage{}
	for _, slug := range []string{
		"el-greco-the-holy-face", "kandinsky-wassily-both-striped",
		"klee-paul-dynamics-of-a-head", "monet-claude-rouen-cathedral-pink-dominant",
		"ernst-max-while-the-earth-sleeps", "bonnard-pierre-getting-out-of-the-bath",
		"miro-joan-the-grasshopper", "chagall-marc-portrait-of-elise-goulandris",
	} {
		pages = append(pages, popularPage{slug + ".html", "https://goulandris.gr/en/artwork/" + slug})
	}
	return captureReviewedPages(ctx, out, pages)
}

func captureRepinNotices(ctx context.Context, out string) error {
	// Published robots allow these factual collection paths for the declared
	// research client. Image/full-image paths are disallowed and never requested;
	// separate museum terms require written permission for reproductions.
	pages := []popularPage{
		{"robots.txt", "https://rusmuseumvrm.ru/robots.txt"},
		{"image-terms.html", "https://rusmuseumvrm.ru/terms/index.php?lang=en"},
	}
	for _, id := range []string{"zh_4056", "zh-4063", "zh-4045", "zh-4086", "zh_4050"} {
		pages = append(pages, popularPage{id + ".html", "https://rusmuseumvrm.ru/data/collections/painting/19_20/" + id + "/index.php?lang=en"})
	}
	return captureReviewedPages(ctx, out, pages)
}
