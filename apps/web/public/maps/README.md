# Map geometry

`countries.geojson` contains Natural Earth 1:110m admin-0 countries, with only
name/ISO label properties retained. Downloaded 16 October 2026 from:
https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson

Original SHA256: `6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f`.

Natural Earth data is public domain: https://www.naturalearthdata.com/about/terms-of-use/.
Current geometry is an orientation layer, never a reconstruction of historical
boundaries. Small places and disputed boundaries require further research.
Country label coordinates from the same file are embedded in the Go geography
package. A label position is not an asserted creation site.
