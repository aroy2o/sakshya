# `india-districts.geojson` — source, license, and how it was built

**Source:** [datameet/maps](https://github.com/datameet/maps), `Districts/Census_2011/2011_Dist.shp`
(and its accompanying `.dbf`/`.shx`/`.prj`), fetched from
`https://raw.githubusercontent.com/datameet/maps/master/Districts/Census_2011/2011_Dist.shp`
on 2026-09-28.

Per that repo's `Districts/README.md`: district boundaries derived from taluk
boundaries (GeoCommons / Bhuvan Geoserver), India's external boundary from the
PC 2014 shapefile in the same repo, and names/extent from the Census of
India's 2011 Administrative Atlas.

**License:** [Creative Commons Attribution 2.5 India](http://creativecommons.org/licenses/by/2.5/in/)
(CC-BY 2.5 India) — attribution required, otherwise free to use, share, and
adapt, including commercially. Attribution: "District boundaries © Datameet
(datameet/maps), CC-BY 2.5 India."

An alternative candidate (`geohacker/india`) was considered and rejected —
its `district/` GeoJSON derives from GADM, whose own license restricts
redistribution/commercial use regardless of the wrapping repo's MIT badge.
Datameet's CC-BY 2.5 India terms are unambiguous and permissive, so that's
the source actually bundled here.

## How this file was produced

The upstream shapefile (10.2 MB `.shp`, 641 districts, nationwide) was
converted to GeoJSON and simplified for a web bundle:

```bash
# Convert shapefile -> GeoJSON (no GDAL needed)
npx shp2json 2011_Dist.shp -o 2011_Dist.raw.geojson

# Simplify geometry (Douglas-Peucker via mapshaper) and drop unused
# DBF columns, keeping only the fields the app's district-coverage join
# needs (src/utils/districtJoin.ts)
npx mapshaper 2011_Dist.raw.geojson \
  -simplify 8% keep-shapes \
  -filter-fields DISTRICT,ST_NM,ST_CEN_CD,DT_CEN_CD,censuscode \
  -o format=geojson precision=0.0001 force india-districts.geojson
```

Result: 1.4 MB, 641 features, properties `DISTRICT` / `ST_NM` (state name) /
`ST_CEN_CD` / `DT_CEN_CD` / `censuscode` (2011 Census codes).

`mapshaper -simplify` reported 867 self-intersections it couldn't fully
repair during simplification — acceptable for a fill/choropleth render at
national-to-district zoom levels (this app's only use of the file), but if a
future use needs topologically clean polygons (e.g. precise area
calculations), re-run the simplify step at a higher `-simplify` percentage
or repair with `mapshaper -clean`.

**Served, not bundled:** this file lives in `/public/data/` and is fetched
at runtime (`src/hooks/useDistrictBoundaries.ts`) rather than imported into
the JS bundle, so the Coverage tab is the only place that pays its ~1.4 MB
download cost, and it's browser-cacheable independent of app deploys.

**Join key:** `src/utils/districtJoin.ts` joins `GET /districts/geotag-coverage`
rows onto these polygons by normalized `DISTRICT` name — PRD §9's endpoint
doesn't document a shared numeric code. If backend-engineer's real response
includes Census district codes, switching the join to `censuscode` would be
more robust than name-matching; flagged in the Phase 5 plan as an open
question for Sync Point 1.
