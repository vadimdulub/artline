package main

import (
	"image"
	"image/color"
	"image/png"
	"os"
	"path/filepath"
	"testing"
)

func TestAuditFileIntegrityAndContainment(t *testing.T) {
	root := t.TempDir()
	root, err := filepath.EvalSymlinks(root)
	if err != nil {
		t.Fatal(err)
	}
	dir := filepath.Join(root, "assets")
	if e := os.Mkdir(dir, 0700); e != nil {
		t.Fatal(e)
	}
	file := filepath.Join(dir, "unit-fixture.png")
	f, e := os.Create(file)
	if e != nil {
		t.Fatal(e)
	}
	img := image.NewRGBA(image.Rect(0, 0, 2, 3))
	img.Set(0, 0, color.RGBA{255, 0, 0, 255})
	if e = png.Encode(f, img); e != nil {
		t.Fatal(e)
	}
	f.Close()
	b, e := os.ReadFile(file)
	if e != nil {
		t.Fatal(e)
	}
	n := int64(len(b))
	w, h := 2, 3
	base := auditMedia{Kind: "local", Path: "/assets/unit-fixture.png", ExpectedBytes: &n, ExpectedHash: digest(b), Width: &w, Height: &h, Rights: "cc0", Evidence: true, Source: "https://example.invalid/test", License: "https://creativecommons.org/publicdomain/zero/1.0/"}
	m := base
	checkAuditMedia(root, &m)
	if !m.FileValid || !m.Decoded || len(m.Issues) != 0 {
		t.Fatalf("valid: %+v", m)
	}
	m = base
	m.ExpectedHash = "wrong"
	checkAuditMedia(root, &m)
	if m.FileValid {
		t.Fatal("wrong hash accepted")
	}
	m = base
	m.Path = "/assets/missing.png"
	checkAuditMedia(root, &m)
	if m.FileValid || m.Decoded {
		t.Fatal("missing file accepted")
	}
	outside := filepath.Join(t.TempDir(), "outside.png")
	if e = os.WriteFile(outside, b, 0600); e != nil {
		t.Fatal(e)
	}
	if e = os.Symlink(outside, filepath.Join(dir, "link.png")); e != nil {
		t.Fatal(e)
	}
	m = base
	m.Path = "/assets/link.png"
	checkAuditMedia(root, &m)
	if len(m.Issues) != 1 || m.Issues[0] != "path_outside_public" {
		t.Fatalf("symlink: %+v", m)
	}
}
