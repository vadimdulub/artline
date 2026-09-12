package main

import (
	"errors"
	"github.com/vadimdulub/artline/apps/server/internal/ingest"
)

// Reviewed exact-object image subset of the all-popular cycle, 11 September 2026.
// No masterpiece label or new artwork import is implied.
var popularCyclePicks = []coveragePick{
	{"cleveland", "128394", "Amedeo Modigliani", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "131819", "Anthony van Dyck", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "141929", "Bartolomé Esteban Murillo", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "128072", "Berthe Morisot", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "146469", "Bronzino", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "128392", "Camille Pissarro", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "95272", "Claude Monet", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "125104", "Edgar Degas", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "135336", "Édouard Manet", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "95259", "Eugène Delacroix", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "123490", "Francisco Goya", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "125949", "François Boucher", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "135512", "Georges Seurat", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "124796", "Giovanni Battista Tiepolo", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "137259", "Gustave Courbet", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "126769", "Henri Rousseau", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "135214", "Honoré Daumier", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "130163", "Jacques-Louis David", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "142298", "Jean-Auguste-Dominique Ingres", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "124078", "Jean-Baptiste-Camille Corot", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "146752", "Jean-François Millet", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "122166", "Jean-Honoré Fragonard", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "108555", "Nicolas Poussin", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "149410", "Paul Gauguin", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "151517", "Peter Paul Rubens", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "135480", "Pierre-Auguste Renoir", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "143278", "Piet Mondrian", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
	{"cleveland", "135299", "Vincent van Gogh", "All-popular cycle: museum painting selected for study; no masterpiece designation inferred."},
}
var popularCycleFacts = map[string]struct {
	Creator     string
	First, Last int
}{
	"128394": {"Amedeo Modigliani", 1917, 1918},
	"131819": {"Anthony van Dyck", 1623, 1625},
	"141929": {"Bartolomé Esteban Murillo", 1665, 1670},
	"128072": {"Berthe Morisot", 1873, 1873},
	"146469": {"Agnolo Bronzino", 1550, 1550},
	"128392": {"Camille Pissarro", 1879, 1879},
	"95272":  {"Claude Monet", 1888, 1888},
	"125104": {"Edgar Degas", 1890, 1900},
	"135336": {"Édouard Manet", 1871, 1872},
	"95259":  {"Eugène Delacroix", 1858, 1858},
	"123490": {"Francisco de Goya", 1819, 1819},
	"125949": {"François Boucher", 1740, 1749},
	"135512": {"Georges Seurat", 1883, 1884},
	"124796": {"Giovanni Battista Tiepolo", 1739, 1739},
	"137259": {"Gustave Courbet", 1863, 1863},
	"126769": {"Henri Rousseau", 1908, 1908},
	"135214": {"Honoré Daumier", 1868, 1873},
	"130163": {"Jacques-Louis David", 1775, 1785},
	"142298": {"Jean-Auguste-Dominique Ingres", 1833, 1843},
	"124078": {"Jean Baptiste Camille Corot", 1865, 1869},
	"146752": {"Jean-François Millet", 1846, 1847},
	"122166": {"Jean-Honoré Fragonard", 1780, 1789},
	"108555": {"Nicolas Poussin", 1625, 1627},
	"149410": {"Paul Gauguin", 1889, 1889},
	"151517": {"Peter Paul Rubens", 1634, 1644},
	"135480": {"Pierre-Auguste Renoir", 1885, 1895},
	"143278": {"Piet Mondrian", 1927, 1927},
	"135299": {"Vincent van Gogh", 1890, 1890},
}

func validatePopularCycleMetadata(x coverageEntry) error {
	f, ok := popularCycleFacts[x.Pick.Object]
	w := ingest.NormalizeCleveland(x.Raw)
	if !ok || w.ArtistName != f.Creator || w.First == nil || w.Last == nil || *w.First != f.First || *w.Last != f.Last || str(x.Raw, "type") != "Painting" {
		return errors.New("popular cycle source creator, type or dating changed; review required")
	}
	return nil
}
