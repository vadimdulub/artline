package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/jpeg"
	"os"
	"path/filepath"
	"strings"
)

// contactSheet lays out unchanged full-frame thumbnails for human visual QA.
// Number/order mapping is saved separately; it never approves an image.
func contactSheet(root, input, prepared, output string) error {
	raw, err := os.ReadFile(input)
	if err != nil {
		return err
	}
	var selected []map[string]any
	if err = json.Unmarshal(raw, &selected); err != nil {
		return err
	}
	if len(selected) < 1 || len(selected) > 40 {
		return fmt.Errorf("invalid selection size")
	}
	canvas := image.NewRGBA(image.Rect(0, 0, 1200, ((len(selected)+4)/5)*260))
	draw.Draw(canvas, canvas.Bounds(), image.NewUniform(color.RGBA{238, 236, 230, 255}), image.Point{}, draw.Src)
	var index []map[string]any
	for n, entry := range selected {
		raw, err = os.ReadFile(filepath.Join(prepared, text(entry, "artwork_id")+".json"))
		if err != nil {
			return err
		}
		var receipt map[string]any
		if err = json.Unmarshal(raw, &receipt); err != nil {
			return err
		}
		raw, err = os.ReadFile(filepath.Join(root, "apps/web/public", strings.TrimPrefix(text(receipt, "path"), "/")))
		if err != nil {
			return err
		}
		if digest(raw) != text(receipt, "sha256") {
			return fmt.Errorf("image changed")
		}
		im, _, err := image.Decode(bytes.NewReader(raw))
		if err != nil {
			return err
		}
		tile := resize(im, 230)
		x, y := n%5*240+(240-tile.Bounds().Dx())/2, n/5*260+(260-tile.Bounds().Dy())/2
		draw.Draw(canvas, image.Rect(x, y, x+tile.Bounds().Dx(), y+tile.Bounds().Dy()), tile, image.Point{}, draw.Src)
		index = append(index, map[string]any{"position": n + 1, "row": n/5 + 1, "column": n%5 + 1, "key": entry["key"], "title": entry["title"], "artist": entry["artist"], "sha256": receipt["sha256"]})
	}
	var out bytes.Buffer
	if err = jpeg.Encode(&out, canvas, &jpeg.Options{Quality: 92}); err != nil {
		return err
	}
	if err = writeNew(output, out.Bytes()); err != nil {
		return err
	}
	raw, err = json.MarshalIndent(index, "", "  ")
	if err != nil {
		return err
	}
	return writeNew(output+".index.json", raw)
}
