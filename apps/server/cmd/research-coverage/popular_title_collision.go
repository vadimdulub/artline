package main

// Empty optional translations must not match names erased by a C-locale
// alnum expression (notably Cyrillic icon titles). The NULLIF guards fail
// closed for empty comparison keys without treating unrelated icons as hits.
// Include literal title/alias matches so non-Latin titles retain a safe path.
const athensTitleCollisionSQL = `SELECT count(*) FROM artworks a
 WHERE (
  a.title=$1 OR (nullif($2,'') IS NOT NULL AND a.title=$2)
  OR lower(regexp_replace(a.title,'[^[:alnum:]]','','g')) IN
    (nullif(lower(regexp_replace($1,'[^[:alnum:]]','','g')),''),nullif(lower(regexp_replace($2,'[^[:alnum:]]','','g')),''))
  OR a.alternate_title=$1 OR (nullif($2,'') IS NOT NULL AND a.alternate_title=$2)
  OR lower(regexp_replace(a.alternate_title,'[^[:alnum:]]','','g')) IN
    (nullif(lower(regexp_replace($1,'[^[:alnum:]]','','g')),''),nullif(lower(regexp_replace($2,'[^[:alnum:]]','','g')),''))
 ) AND (EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id AND aa.artist_id=$3)
        OR NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=a.id))`
