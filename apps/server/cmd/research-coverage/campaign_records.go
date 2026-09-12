package main

import (
	"archive/tar"
	"compress/bzip2"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

// Streaming readers never extract archive paths and never retain a full foreign
// collection in memory. Only offline metadata is read; no media URLs are fetched.
func campaignRecords(root, source string, visit func(map[string]any) error) error {
	dir := filepath.Join(root, "content/imports/campaign-"+source+"-20260910")
	file := "objects.json"
	if source == "met" {
		file = "objects.csv"
	}
	if source == "chicago" {
		file = "metadata.tar.bz2"
	}
	path := filepath.Join(dir, file)
	if e := verify(path); e != nil {
		return e
	}
	if source == "met" {
		return csvRows(path, ',', func(row map[string]string) error {
			r := map[string]any{}
			for k, v := range row {
				r[k] = v
			}
			return visit(r)
		})
	}
	f, e := os.Open(path)
	if e != nil {
		return e
	}
	defer f.Close()
	if source == "chicago" {
		reader := tar.NewReader(io.LimitReader(bzip2.NewReader(f), 4<<30))
		for n := 0; n < 500000; n++ {
			h, e := reader.Next()
			if e == io.EOF {
				return nil
			}
			if e != nil {
				return e
			}
			if h.Typeflag != tar.TypeReg || !strings.Contains("/"+h.Name, "/artworks/") || !strings.HasSuffix(h.Name, ".json") {
				continue
			}
			if h.Size > 4<<20 {
				return fmt.Errorf("oversize artwork record")
			}
			var r map[string]any
			if e = json.NewDecoder(reader).Decode(&r); e != nil {
				return e
			}
			if e = visit(r); e != nil {
				return e
			}
		}
		return fmt.Errorf("archive entry cap reached")
	}
	d := json.NewDecoder(f)
	t, e := d.Token()
	if e != nil || t != json.Delim('[') {
		return fmt.Errorf("expected object array: %v", e)
	}
	for n := 0; d.More(); n++ {
		if n >= 100000 {
			return fmt.Errorf("source row cap reached")
		}
		var r map[string]any
		if e = d.Decode(&r); e != nil {
			return e
		}
		if e = visit(r); e != nil {
			return e
		}
	}
	if t, e = d.Token(); e != nil || t != json.Delim(']') {
		return fmt.Errorf("incomplete source array")
	}
	if _, e = d.Token(); e != io.EOF {
		return fmt.Errorf("trailing source data")
	}
	return nil
}

func str(r map[string]any, key string) string {
	if s, ok := r[key].(string); ok {
		return strings.TrimSpace(s)
	}
	return ""
}
func integer(r map[string]any, key string) int {
	if f, ok := r[key].(float64); ok && f == float64(int(f)) {
		return int(f)
	}
	return 0
}

func auditCampaign(root, source, out string) error {
	total := 0
	types := map[string]int{}
	samples := map[string][]map[string]any{}
	e := campaignRecords(root, source, func(r map[string]any) error {
		total++
		field := map[string]string{"met": "classification", "cleveland": "type", "chicago": "artwork_type_title", "lombardia": "ogtd"}[source]
		kind := str(r, field)
		types[kind]++
		if len(samples[kind]) < 2 {
			samples[kind] = append(samples[kind], r)
		}
		return nil
	})
	if e != nil {
		return e
	}
	if e = save(filepath.Join(out, "audit.json"), map[string]any{"source": source, "total": total, "types": types}); e != nil {
		return e
	}
	if e = save(filepath.Join(out, "samples.json"), samples); e != nil {
		return e
	}
	fmt.Printf("%s rows%d classifications%d; full counts saved in audit.json\n", source, total, len(types))
	return nil
}
