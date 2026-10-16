# Map geometry

`countries.geojson` contains Natural Earth 1:50m admin-0 countries. It retains
country names, ISO codes, label positions/ranks, and geometry rounded to four
decimal places. Downloaded 16 October 2026 from:
https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson

Original SHA256: `3e458fc036ad0a66411f2c1e6cac49c5d7bfb81cb1123bc513b22511a2b7fdeb`.
Served size: 1,898,455 bytes; 242 country features.

Natural Earth data is public domain: https://www.naturalearthdata.com/about/terms-of-use/.
Modern boundaries and country labels provide orientation, not historical event
extent or precise creation sites. Country label coordinates in the Go evidence
projection remain the existing 1:110m gazetteer; display labels never change an
association or infer a catalogue place. No live tile or geocoding service is used.
