package ingest

import (
	"context"
	"strings"

	"github.com/jackc/pgx/v5"
)

// These are present-day birth-place countries from Pantheon, NOT nationality or
// citizenship claims. Unmapped/historical names stay in the raw review record.
var birthCountries = map[string]string{
	"France": "FR western-europe", "Germany": "DE western-europe", "Austria": "AT western-europe", "Switzerland": "CH western-europe", "Belgium": "BE western-europe", "Netherlands": "NL western-europe", "Luxembourg": "LU western-europe",
	"Italy": "IT southern-europe", "Spain": "ES southern-europe", "Portugal": "PT southern-europe", "Greece": "GR southern-europe", "Croatia": "HR southern-europe", "Slovenia": "SI southern-europe", "Serbia": "RS southern-europe", "Bosnia and Herzegovina": "BA southern-europe", "North Macedonia": "MK southern-europe", "Albania": "AL southern-europe", "Montenegro": "ME southern-europe", "Malta": "MT southern-europe",
	"United Kingdom": "GB northern-europe", "Ireland": "IE northern-europe", "Denmark": "DK northern-europe", "Sweden": "SE northern-europe", "Norway": "NO northern-europe", "Finland": "FI northern-europe", "Iceland": "IS northern-europe", "Estonia": "EE northern-europe", "Latvia": "LV northern-europe", "Lithuania": "LT northern-europe",
	"Russia": "RU eastern-europe", "Ukraine": "UA eastern-europe", "Belarus": "BY eastern-europe", "Poland": "PL eastern-europe", "Czechia": "CZ eastern-europe", "Czech Republic": "CZ eastern-europe", "Slovakia": "SK eastern-europe", "Hungary": "HU eastern-europe", "Romania": "RO eastern-europe", "Bulgaria": "BG eastern-europe", "Moldova": "MD eastern-europe",
	"United States": "US northern-america", "Canada": "CA northern-america", "Mexico": "MX central-america", "Guatemala": "GT central-america", "Costa Rica": "CR central-america", "Nicaragua": "NI central-america", "Panama": "PA central-america", "Cuba": "CU caribbean", "Haiti": "HT caribbean", "Jamaica": "JM caribbean", "Dominican Republic": "DO caribbean", "Puerto Rico": "PR caribbean",
	"Brazil": "BR south-america", "Argentina": "AR south-america", "Uruguay": "UY south-america", "Chile": "CL south-america", "Colombia": "CO south-america", "Venezuela": "VE south-america", "Peru": "PE south-america", "Ecuador": "EC south-america", "Bolivia": "BO south-america", "Paraguay": "PY south-america",
	"China": "CN eastern-asia", "Japan": "JP eastern-asia", "South Korea": "KR eastern-asia", "North Korea": "KP eastern-asia", "Mongolia": "MN eastern-asia", "Taiwan": "TW eastern-asia",
	"India": "IN southern-asia", "Pakistan": "PK southern-asia", "Bangladesh": "BD southern-asia", "Sri Lanka": "LK southern-asia", "Nepal": "NP southern-asia", "Iran": "IR southern-asia", "Afghanistan": "AF southern-asia",
	"Indonesia": "ID south-eastern-asia", "Philippines": "PH south-eastern-asia", "Vietnam": "VN south-eastern-asia", "Thailand": "TH south-eastern-asia", "Malaysia": "MY south-eastern-asia", "Singapore": "SG south-eastern-asia", "Myanmar": "MM south-eastern-asia", "Cambodia": "KH south-eastern-asia",
	"Turkey": "TR western-asia", "Türkiye": "TR western-asia", "Armenia": "AM western-asia", "Georgia": "GE western-asia", "Azerbaijan": "AZ western-asia", "Israel": "IL western-asia", "Palestine": "PS western-asia", "Lebanon": "LB western-asia", "Syria": "SY western-asia", "Iraq": "IQ western-asia", "Cyprus": "CY western-asia", "Jordan": "JO western-asia",
	"Uzbekistan": "UZ central-asia", "Kazakhstan": "KZ central-asia", "Kyrgyzstan": "KG central-asia",
	"Egypt": "EG northern-africa", "Algeria": "DZ northern-africa", "Tunisia": "TN northern-africa", "Morocco": "MA northern-africa", "Sudan": "SD northern-africa", "South Africa": "ZA southern-africa", "Namibia": "NA southern-africa", "Nigeria": "NG western-africa", "Ghana": "GH western-africa", "Senegal": "SN western-africa", "Ethiopia": "ET eastern-africa", "Kenya": "KE eastern-africa", "Mozambique": "MZ eastern-africa", "Tanzania": "TZ eastern-africa", "Zimbabwe": "ZW eastern-africa", "Democratic Republic of the Congo": "CD middle-africa",
	"Australia": "AU australia-and-new-zealand", "New Zealand": "NZ australia-and-new-zealand",
}

func addBirthCountry(ctx context.Context, tx pgx.Tx, artist, name string) error {
	entry, ok := birthCountries[name]
	if !ok {
		return nil
	}
	parts := strings.Fields(entry)
	_, err := tx.Exec(ctx, `INSERT INTO countries(code,name,region_code) VALUES($1,$2,$3) ON CONFLICT(code) DO NOTHING`, parts[0], name, parts[1])
	if err != nil {
		return err
	}
	_, err = tx.Exec(ctx, `INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note)
 VALUES($1,$2,'birth',false,'Pantheon 2025 modern birth-place country; not nationality/citizenship. Review required.') ON CONFLICT DO NOTHING`, artist, parts[0])
	return err
}
