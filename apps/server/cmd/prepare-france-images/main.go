// prepare-france-images downloads only a pinned, individually rights-reviewed
// selection. It cannot connect to a database, upload, publish, or discover files.
package main

import (
	"bytes"
	"crypto/sha1"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"image"
	"image/color"
	"image/jpeg"
	_ "image/png"
	"io"
	"math"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

func digest(b []byte) string { h := sha256.Sum256(b); return hex.EncodeToString(h[:]) }
func writeNew(path string, b []byte) error {
	if old, err := os.ReadFile(path); err == nil {
		if bytes.Equal(old, b) {
			return nil
		}
		return errors.New("immutable output differs: " + path)
	} else if !errors.Is(err, os.ErrNotExist) {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		return err
	}
	f, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return err
	}
	_, err = f.Write(b)
	ce := f.Close()
	if err != nil {
		return err
	}
	return ce
}

// The existing review-masterpieces full-frame bilinear reducer, kept local to
// this offline command so no public API or ingestion behaviour is changed.
func resize(src image.Image, edge int) *image.RGBA {
	b := src.Bounds()
	w, h := b.Dx(), b.Dy()
	scale := math.Min(1, float64(edge)/float64(max(w, h)))
	nw, nh := max(1, int(math.Round(float64(w)*scale))), max(1, int(math.Round(float64(h)*scale)))
	dst := image.NewRGBA(image.Rect(0, 0, nw, nh))
	sample := func(x, y int) [3]float64 {
		r, g, bv, a := src.At(b.Min.X+x, b.Min.Y+y).RGBA()
		white := uint32(65535) - a
		return [3]float64{float64(r+white) / 257, float64(g+white) / 257, float64(bv+white) / 257}
	}
	for y := 0; y < nh; y++ {
		sy := math.Max(0, (float64(y)+.5)*float64(h)/float64(nh)-.5)
		y0 := int(sy)
		y1 := min(h-1, y0+1)
		dy := sy - float64(y0)
		for x := 0; x < nw; x++ {
			sx := math.Max(0, (float64(x)+.5)*float64(w)/float64(nw)-.5)
			x0 := int(sx)
			x1 := min(w-1, x0+1)
			dx := sx - float64(x0)
			a, b, c, d := sample(x0, y0), sample(x1, y0), sample(x0, y1), sample(x1, y1)
			v := [3]uint8{}
			for k := range v {
				v[k] = uint8(math.Round((a[k]*(1-dx)+b[k]*dx)*(1-dy) + (c[k]*(1-dx)+d[k]*dx)*dy))
			}
			dst.SetRGBA(x, y, color.RGBA{v[0], v[1], v[2], 255})
		}
	}
	return dst
}
func compress(raw []byte) ([]byte, int, int, int, error) {
	cfg, format, err := image.DecodeConfig(bytes.NewReader(raw))
	if err != nil {
		return nil, 0, 0, 0, err
	}
	if (format != "jpeg" && format != "png") || cfg.Width < 1 || cfg.Height < 1 || cfg.Width > 10000 || cfg.Height > 10000 || int64(cfg.Width)*int64(cfg.Height) > 25_000_000 {
		return nil, 0, 0, 0, errors.New("unsupported image dimensions/format")
	}
	src, _, err := image.Decode(bytes.NewReader(raw))
	if err != nil {
		return nil, 0, 0, 0, err
	}
	for _, edge := range []int{1000, 900, 750, 600, 480} {
		im := resize(src, edge)
		for q := 88; q >= 58; q -= 5 {
			var out bytes.Buffer
			if err = jpeg.Encode(&out, im, &jpeg.Options{Quality: q}); err != nil {
				return nil, 0, 0, 0, err
			}
			if out.Len() <= 100000 {
				return out.Bytes(), im.Bounds().Dx(), im.Bounds().Dy(), q, nil
			}
		}
	}
	return nil, 0, 0, 0, errors.New("cannot meet 100000-byte image limit")
}
func text(m map[string]any, k string) string { v, _ := m[k].(string); return v }
func validate(entries []map[string]any) error {
	if len(entries) < 1 || len(entries) > 25 {
		return errors.New("selection must contain 1..25 images")
	}
	seen := map[string]bool{}
	idRE := regexp.MustCompile(`^[a-f0-9-]{36}$`)
	for _, e := range entries {
		id := text(e, "artwork_id")
		u, err := url.Parse(text(e, "source_image_url"))
		if err != nil {
			return err
		}
		if !idRE.MatchString(id) || seen[id] || u.Scheme != "https" || u.Host != "upload.wikimedia.org" || u.User != nil || u.RawQuery != "" || u.Fragment != "" || !strings.HasPrefix(u.Path, "/wikipedia/commons/") {
			return errors.New("unapproved/duplicate image identity or URL")
		}
		seen[id] = true
		if text(e, "identity_basis") == "" || text(e, "creator_credit") == "" || text(e, "source_evidence_sha256") == "" || text(e, "provider") != "france-commons" {
			return errors.New("missing reviewed evidence or credit")
		}
		uri := text(e, "policy_url")
		rights := text(e, "rights_status")
		valid := (rights == "public_domain" && uri == "https://creativecommons.org/publicdomain/mark/1.0/") || (rights == "cc0" && uri == "https://creativecommons.org/publicdomain/zero/1.0/")
		valid = valid || ((rights == "cc_by" || rights == "cc_by_sa") && regexp.MustCompile(`^https://creativecommons.org/licenses/by(?:-sa)?/(?:2\.0|2\.5|3\.0|4\.0)/$`).MatchString(uri))
		if !valid {
			return errors.New("unapproved explicit licence")
		}
		checked, err := time.Parse(time.RFC3339, text(e, "checked_at"))
		if err != nil || time.Since(checked) > 24*time.Hour || checked.After(time.Now().Add(5*time.Minute)) {
			return errors.New("stale rights review")
		}
	}
	return nil
}
func run(root, input, pin, out string) error {
	b, err := os.ReadFile(input)
	if err != nil {
		return err
	}
	if len(pin) != 64 || digest(b) != pin {
		return errors.New("reviewed selection hash mismatch")
	}
	var entries []map[string]any
	if err = json.Unmarshal(b, &entries); err != nil {
		return err
	}
	if err = validate(entries); err != nil {
		return err
	}
	client := &http.Client{Timeout: 45 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	for n, e := range entries {
		id := text(e, "artwork_id")
		receipt := filepath.Join(out, id+".json")
		if prior, err := os.ReadFile(receipt); err == nil {
			var old map[string]any
			if err = json.Unmarshal(prior, &old); err != nil {
				return err
			}
			p := text(old, "path")
			if !strings.HasPrefix(p, "/assets/artworks/imported/france-study-") {
				return errors.New("invalid cached path")
			}
			data, err := os.ReadFile(filepath.Join(root, "apps/web/public", strings.TrimPrefix(p, "/")))
			if err != nil || len(data) > 100000 || digest(data) != text(old, "sha256") {
				return errors.New("cached derivative mismatch")
			}
			fmt.Println(id, "existing-file-valid")
			continue
		}
		if n > 0 {
			time.Sleep(3 * time.Second)
		}
		req, err := http.NewRequest("GET", text(e, "source_image_url"), nil)
		if err != nil {
			return err
		}
		req.Header.Set("User-Agent", "ArtlineSelectedImageResearch/1.0 (bounded rights-reviewed museum research; https://github.com/vadim-dulub/artline)")
		resp, err := client.Do(req)
		if err != nil {
			return err
		}
		if resp.StatusCode != 200 {
			resp.Body.Close()
			return fmt.Errorf("source HTTP %d; stopped without retry; Retry-After=%s", resp.StatusCode, resp.Header.Get("Retry-After"))
		}
		raw, err := io.ReadAll(io.LimitReader(resp.Body, 8<<20+1))
		resp.Body.Close()
		if err != nil {
			return err
		}
		if len(raw) > 8<<20 {
			return errors.New("source exceeds bounded byte budget")
		}
		if expected := text(e, "commons_original_sha1"); expected != "" {
			got := sha1.Sum(raw)
			if hex.EncodeToString(got[:]) != expected {
				return errors.New("Commons original file changed since rights review")
			}
		}
		data, w, h, q, err := compress(raw)
		if err != nil {
			return err
		}
		hash := digest(data)
		path := "/assets/artworks/imported/france-study-" + hash + ".jpg"
		if err = writeNew(filepath.Join(root, "apps/web/public", strings.TrimPrefix(path, "/")), data); err != nil {
			return err
		}
		e["path"] = path
		e["sha256"] = hash
		e["bytes"] = len(data)
		e["width"] = w
		e["height"] = h
		e["jpeg_quality"] = q
		e["source_sha256"] = digest(raw)
		e["source_bytes"] = len(raw)
		e["downloaded_at"] = time.Now().UTC().Format(time.RFC3339)
		e["selection_sha256"] = pin
		e["transform"] = "Go full-frame proportional bilinear resize and JPEG compression; no crop, generated content or substitutions"
		e["response_headers"] = map[string]string{"content-type": resp.Header.Get("Content-Type"), "etag": resp.Header.Get("ETag"), "last-modified": resp.Header.Get("Last-Modified")}
		encoded, err := json.MarshalIndent(e, "", "  ")
		if err != nil {
			return err
		}
		if err = writeNew(receipt, append(encoded, '\n')); err != nil {
			return err
		}
		fmt.Printf("%s prepared %dx%d %d bytes\n", id, w, h, len(data))
	}
	return nil
}
func main() {
	root := flag.String("root", "../..", "Artline repository root")
	input := flag.String("input", "", "Pinned reviewed image selection")
	pin := flag.String("sha256", "", "Reviewed selection SHA-256")
	out := flag.String("out", "", "Immutable receipt directory")
	flag.Parse()
	if *input == "" || *out == "" {
		fmt.Fprintln(os.Stderr, "input/out required")
		os.Exit(1)
	}
	if err := run(*root, *input, *pin, *out); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
