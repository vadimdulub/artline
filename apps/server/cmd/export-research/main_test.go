package main

import (
	"encoding/csv"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"testing"
)

func TestCSVUnicodeQuotesRangesAndBooleans(t *testing.T) {
	path := filepath.Join(t.TempDir(), "export.csv")
	f, err := os.Create(path)
	if err != nil {
		t.Fatal(err)
	}
	w := csv.NewWriter(f)
	rows := [][]string{header,
		{"Κωνσταντίνος Παρθένης", "Still life, \"flowers\"", "ca. 1930–1935", "Εθνική Πινακοθήκη", "Greece", "true"},
		{"Иван Айвазовский", "Волна\nWave", "1889", "State Russian Museum", "Russia", "false"},
	}
	if err = w.WriteAll(rows); err != nil {
		t.Fatal(err)
	}
	if err = f.Close(); err != nil {
		t.Fatal(err)
	}
	if err = verifyCSV(path, 2, 1); err != nil {
		t.Fatal(err)
	}
	if err = verifyCSV(path, 3, 1); err == nil {
		t.Fatal("accepted wrong row count")
	}
	for _, s := range []string{"=1+1", "  @SUM(A1)", "+123", "-danger"} {
		if safeCell(s) != "'"+s {
			t.Fatalf("unescaped: %q", s)
		}
	}
}

func TestImageValidation(t *testing.T) {
	root, err := filepath.EvalSymlinks(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	if err = os.Mkdir(filepath.Join(root, "assets"), 0700); err != nil {
		t.Fatal(err)
	}
	f, err := os.Create(filepath.Join(root, "assets", "valid.png"))
	if err != nil {
		t.Fatal(err)
	}
	if err = png.Encode(f, image.NewRGBA(image.Rect(0, 0, 2, 2))); err != nil {
		t.Fatal(err)
	}
	f.Close()
	if err = checkImage(root, "/assets/valid.png"); err != nil {
		t.Fatal(err)
	}
	for _, s := range []string{"https://example.org/image.jpg", "/assets/missing.jpg", "/assets/../../outside.jpg"} {
		if err = checkImage(root, s); err == nil {
			t.Fatalf("accepted %q", s)
		}
	}
	if err = os.WriteFile(filepath.Join(root, "assets", "broken.jpg"), []byte("not an image"), 0600); err != nil {
		t.Fatal(err)
	}
	if err = checkImage(root, "/assets/broken.jpg"); err == nil {
		t.Fatal("accepted broken image")
	}
}
