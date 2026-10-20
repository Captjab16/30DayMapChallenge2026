# Data

Source data for the 2026 challenge, centered on the Richmond, VA region (City of Richmond
plus Henrico and Chesterfield). Everything in this folder except this README is gitignored,
because several files are larger than GitHub's 100 MB limit.

## Download

From the repository root:

```bash
python scripts/download_data.py           # about 2.5 GB
python scripts/download_data.py --large   # adds the national noise raster (several GB)
python scripts/download_data.py --list    # see what it fetches
```

Re-running skips files you already have. The Overture layers need `pyarrow`
(`pip install pyarrow`); with `geopandas` installed too, each layer is also written as a
GeoPackage (`.gpkg`), which ArcGIS Pro and QGIS both open directly.

## What's here

| Folder | Contents | Source | Days |
|---|---|---|---|
| `elevation/` | 10 m DEM tile (`USGS_13_n38w078.tif`, covers 37 to 38 N, 77 to 78 W) and a 1 m DEM tile covering downtown and Libby Hill | USGS 3DEP | 5, 14, 17, 22, 29 |
| `hydrography/` | NHDPlus HR file geodatabase for HU4 0208 (Lower Chesapeake, which includes the James) | USGS | 26 |
| `historic/` | 21 USGS historical topo GeoTIFFs for Richmond (1894 to 1974), already georeferenced; `mappinginequality.parquet` (HOLC redlining polygons for every mapped city; filter to Richmond) | USGS topoView; Mapping Inequality via its cloud-native copy on Source Cooperative | 6, 15 |
| `osm/` | Geofabrik Virginia extract (`.osm.pbf`) | OpenStreetMap | 1, 2, 3, 4, 12, 19, 21, 23, 24 |
| `overture/` | Places, buildings, road segments, water, infrastructure (power lines), land use and boundaries clipped to the Richmond region | Overture Maps | 1, 2, 3, 4, 12, 14, 19, 23, 24, 26 |
| `transit/` | GRTC GTFS feed (includes the Pulse) | GRTC / Mobility Database | 24 |
| `census/` | 2020 Census urban areas; LODES 2022 Virginia commuting flows plus the block crosswalk (block lat/lon) | U.S. Census Bureau | 9, 13 |
| `noise/` | National Transportation Noise Map 2020, CONUS road + rail + aviation (`--large` only) | BTS | 11 |
| `boundaries/` | Natural Earth countries, land, ocean, graticules, states/provinces | Natural Earth | 22 |

## Manual downloads

These need a login or an interactive portal, so the script only prints the links.

| Data | Where | Note |
|---|---|---|
| Lidar point clouds (Day 14) | [USGS LidarExplorer](https://apps.nationalmap.gov/lidar-explorer/) | Large tiles; draw a small area around downtown |
| VBMP orthoimagery (Days 6, 14, 29) | [VGIN](https://vgin.vdem.virginia.gov/) | Easiest to add as an imagery service in Pro |
| Sanborn fire insurance maps (Days 6, 15) | [Library of Congress](https://www.loc.gov/collections/sanborn-maps/) | Scans, not georeferenced |
| HOLC map, official city download (Days 6, 15) | [Mapping Inequality](https://dsl.richmond.edu/panorama/redlining/) | Optional; the script already gets the full dataset |
| EIA power plants (Day 12) | [U.S. Energy Atlas](https://atlas.eia.gov/) | Power Plants layer > Download |
| City of Richmond layers (Days 1, 3, 4, 18) | [Richmond open data](https://data.richmondgov.com/) | Parcels, trees, 311, crime. If the link has moved, search rva.gov for "Open Data Portal" |
| Night lights (Days 9, 12, 17, 29) | [NASA LAADS DAAC](https://ladsweb.modaps.eosdis.nasa.gov/) | Black Marble VNP46A4 annual; free NASA Earthdata login |
| Sentinel-2 L2A scene (Day 29) | [Copernicus Browser](https://browser.dataspace.copernicus.eu/) | Free Copernicus Data Space login |

Put manual downloads in the matching folder (for example `imagery/` or `city/`); anything
under `data/` stays out of git.

## Terms and credits

### VBMP orthoimagery (VGIN)

Captured 19 October 2026 from the
[VBMP Most Recent Imagery and DEM Download](https://experience.arcgis.com/experience/3876523cde9a434197579e995a92d94c)
app (the "I agree to the above terms and conditions" box) and the
[imagery service's metadata](https://vginmaps.vdem.virginia.gov/arcgis/rest/services/VBMP_Imagery/MostRecentImagery_WGS/MapServer).

**What you agree to**

- The data is free and public. VGIN says all program data is "publicly available without
  charge."
- No accuracy guarantee: "all warranties regarding the accuracy of the map data and any
  representation or inferences derived there from are hereby expressly disclaimed."
- General information only (Code of Virginia § 54.1-402 C): don't use it to decide property
  lines or boundaries, flood plains, or to design or build improvements to real property.
- MrSID (`.sid`) files are meant for viewing and are "less ideal for analysis." The DEMs
  (`.img`) were made to produce the imagery and "may not be appropriate for all analysis
  tasks."

**Fine for this challenge:** making and sharing maps, using it as a basemap, and tracing or
interpreting what you see. **Don't:** present a map as showing exact property lines or flood
risk.

**How to credit it** (the service lists its copyright as "Virginia Geographic Information
Network (VGIN)"):

> Imagery: Virginia Base Mapping Program (VBMP), Virginia Geographic Information Network
> (VGIN), Virginia Department of Emergency Management, YEAR

Replace `YEAR` with the flight year in the tile name, for example `N16_6955_10.2025` is
2025. Richmond's most recent imagery is from 2022, 2023 or 2025.

**Not found:** the app's "GIS data usage" link
(<https://vgin.vdem.virginia.gov/pages/cl-vgin-data-usage>) asked for a sign-in and showed
nothing, and no formal license (such as Creative Commons) was found. If you plan to sell anything
made from the imagery, ask <vbmp@vdem.virginia.gov> first.
