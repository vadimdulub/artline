package member

import (
	"encoding/csv"
	"fmt"
	"net/http"
	"strings"
)

func studyCSVCell(s string) string {
	trimmed := strings.TrimLeft(s, " \t\r\n\v\f\uFEFF")
	if strings.ContainsAny(s[:min(len(s), 1)], "\t\r\n") || (len(trimmed) > 0 && strings.ContainsRune("=+-@", rune(trimmed[0]))) {
		return "'" + s
	}
	return s
}
func studyExport(w http.ResponseWriter, s Study, format string) error {
	if format != "csv" && format != "references" {
		return studyInputError("Choose CSV or references.")
	}
	if len(s.Records) == 0 {
		return studyInputError("Add records before exporting.")
	}
	ext := "txt"
	contentType := "text/plain; charset=utf-8"
	if format == "csv" {
		ext = "csv"
		contentType = "text/csv; charset=utf-8"
	}
	w.Header().Set("Content-Type", contentType)
	w.Header().Set("Content-Disposition", `attachment; filename="artline-study.`+ext+`"`)
	if format == "csv" {
		writer := csv.NewWriter(w)
		_ = writer.Write([]string{"Type", "Title", "Creator", "Date", "Source links", "Holding collection", "Medium", "Dimensions", "Note", "Personal record", "Captured at", "Date note", "Image credit", "Image rights label", "Image source"})
		for _, r := range s.Records {
			sources := []string{}
			for _, source := range r.Sources {
				sources = append(sources, source.Name+": "+source.URL)
			}
			row := []string{r.Kind, r.Title, r.Creator, r.Date, strings.Join(sources, "; "), r.Holding, r.Medium, r.Dimensions, r.Note, fmt.Sprint(r.Personal), r.CapturedAt.Format("2006-01-02")}
			row = append(row, r.DateNote)
			if r.Image != nil {
				row = append(row, r.Image.Credit, r.Image.License, r.Image.SourceURL)
			} else {
				row = append(row, "", "", "")
			}
			for i := range row {
				row[i] = studyCSVCell(row[i])
			}
			_ = writer.Write(row)
		}
		writer.Flush()
		return writer.Error()
	}
	fmt.Fprintf(w, "%s\nArtline study · %s\nCatalogue details are snapshots captured when added. Holdings do not establish current display. Images are not included.\n\n", s.Title, s.Role)
	for _, r := range s.Records {
		fmt.Fprintf(w, "%s. %s. %s.\n", r.Creator, r.Title, r.Date)
		for _, source := range r.Sources {
			fmt.Fprintf(w, "%s: %s\n", source.Name, source.URL)
		}
		if r.DateNote != "" {
			fmt.Fprintln(w, r.DateNote)
		}
		if r.Note != "" {
			fmt.Fprintf(w, "Note: %s\n", r.Note)
		}
		fmt.Fprintf(w, "Captured: %s\n\n", r.CapturedAt.Format("2006-01-02"))
	}
	return nil
}
