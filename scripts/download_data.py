#!/usr/bin/env python3

"""
Download the #30DayMapChallenge 2026 starter data for the Richmond, VA region.

Usage (from the repository root):

    python scripts/download_data.py               # everything except very large files
    python scripts/download_data.py --large       # also the multi-GB national noise raster
    python scripts/download_data.py --only elevation historic
    python scripts/download_data.py --list        # show what would be downloaded
    python scripts/download_data.py --dest D:/gis/30dmc/data

Files land in data/<category>/ (gitignored). Files that already exist are skipped,
so the script is safe to re-run after a failed or partial download.

Direct downloads use only the Python standard library. The Overture Maps extract
needs `pyarrow` (pip install pyarrow); if `geopandas` is also installed, each
Overture layer is written as a GeoPackage as well as GeoParquet.

Some sources need a login or an interactive portal; they are listed in
data/README.md under "Manual downloads" and printed at the end of each run.
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# City of Richmond plus Henrico and Chesterfield counties (lon/lat, WGS84)
BBOX = (-77.90, 37.20, -77.15, 37.80)

TNM = "https://prd-tnm.s3.amazonaws.com/StagedProducts"
NE = "https://naturalearth.s3.amazonaws.com"

TOPO_QUADS = [
    "VA_Richmond West_186497_1936_24000_geo.tif",
    "VA_Richmond_186498_1934_24000_geo.tif",
    "VA_Richmond_186500_1934_24000_geo.tif",
    "VA_Richmond_186501_1956_24000_geo.tif",
    "VA_Richmond_186502_1964_24000_geo.tif",
    "VA_Richmond_186503_1964_24000_geo.tif",
    "VA_Richmond_186504_1964_24000_geo.tif",
    "VA_Richmond_186505_1964_24000_geo.tif",
    "VA_Richmond_186506_1974_24000_geo.tif",
    "VA_Richmond_186508_1964_24000_geo.tif",
    "VA_Richmond_186509_1964_24000_geo.tif",
    "VA_Richmond_186510_1964_24000_geo.tif",
    "VA_Richmond_186511_1964_24000_geo.tif",
    "VA_Richmond_187558_1939_31680_geo.tif",
    "VA_Richmond_187559_1939_31680_geo.tif",
    "VA_Richmond_188530_1894_62500_geo.tif",
    "VA_Richmond_188531_1895_62500_geo.tif",
    "VA_Richmond_188532_1895_62500_geo.tif",
    "VA_Richmond_188533_1895_62500_geo.tif",
    "VA_Richmond_188534_1895_62500_geo.tif",
    "VA_Richmond_188537_1895_62500_geo.tif",
]

# (category, file name, [urls tried in order], days, large)
DOWNLOADS = [
    ("elevation", "USGS_13_n38w078.tif",
     [f"{TNM}/Elevation/13/TIFF/current/n38w078/USGS_13_n38w078.tif"],
     "5, 6, 14, 17, 22, 29", False),
    ("elevation", "USGS_1M_18_x28y416_VA_SouthamptonHenricoWMBG_2019_B19.tif",
     [f"{TNM}/Elevation/1m/Projects/VA_SouthamptonHenricoWMBG_2019_B19/TIFF/"
      "USGS_1M_18_x28y416_VA_SouthamptonHenricoWMBG_2019_B19.tif"],
     "5, 14, 17, 29", False),
    ("hydrography", "NHDPLUS_H_0208_HU4_20220324_GDB.zip",
     [f"{TNM}/Hydrography/NHDPlusHR/VPU/Current/GDB/NHDPLUS_H_0208_HU4_20220324_GDB.zip"],
     "26", False),
    *[("historic", name,
       [f"{TNM}/Maps/HistoricalTopo/GeoTIFF/VA/{urllib.parse.quote(name)}"],
       "6, 15", False) for name in TOPO_QUADS],
    ("historic", "mappinginequality.parquet",
     ["https://s3-west.nrp-nautilus.io/public-mappinginequality/mappinginequality.parquet"],
     "6, 15", False),
    ("osm", "virginia-latest.osm.pbf",
     ["https://download.geofabrik.de/north-america/us/virginia-latest.osm.pbf"],
     "1, 2, 3, 4, 12, 19, 20, 21, 23, 24", False),
    ("transit", "grtc_gtfs.zip",
     ["https://www.ridegrtc.com/wp-content/uploads/2025/02/gtfs.zip",
      "https://files.mobilitydatabase.org/mdb-3518/mdb-3518-202610100010/mdb-3518-202610100010.zip"],
     "24", False),
    ("census", "tl_2024_us_uac20.zip",
     ["https://www2.census.gov/geo/tiger/TIGER2024/UAC20/tl_2024_us_uac20.zip"],
     "9", False),
    ("census", "va_od_main_JT00_2022.csv.gz",
     ["https://lehd.ces.census.gov/data/lodes/LODES8/va/od/va_od_main_JT00_2022.csv.gz"],
     "13", False),
    ("census", "va_xwalk.csv.gz",
     ["https://lehd.ces.census.gov/data/lodes/LODES8/va/va_xwalk.csv.gz"],
     "13", False),
    ("noise", "CONUS_rail_road_and_aviation_noise_2020.zip",
     ["https://www.bts.gov/bts-net-storage/CONUS_rail_road_and_aviation_noise_2020.zip"],
     "11", True),
    ("boundaries", "ne_110m_admin_0_countries.zip",
     [f"{NE}/110m_cultural/ne_110m_admin_0_countries.zip"], "22", False),
    ("boundaries", "ne_110m_land.zip",
     [f"{NE}/110m_physical/ne_110m_land.zip"], "22", False),
    ("boundaries", "ne_110m_graticules_all.zip",
     [f"{NE}/110m_physical/ne_110m_graticules_all.zip"], "22", False),
    ("boundaries", "ne_50m_ocean.zip",
     [f"{NE}/50m_physical/ne_50m_ocean.zip"], "22", False),
    ("boundaries", "ne_10m_admin_1_states_provinces.zip",
     [f"{NE}/10m_cultural/ne_10m_admin_1_states_provinces.zip"], "22", False),
]

# Overture Maps layers clipped to BBOX: (theme, type, days)
OVERTURE_RELEASE = "2026-09-23.1"
OVERTURE_LAYERS = [
    ("places", "place", "1, 4, 19, 23"),
    ("buildings", "building", "3, 14, 17"),
    ("transportation", "segment", "2, 24"),
    ("base", "water", "26"),
    ("base", "infrastructure", "12"),
    ("base", "land_use", "3, 8, 9"),
    ("divisions", "division_area", "1, 3, 9"),
]

MANUAL = [
    ("Lidar point clouds (Day 14)", "https://apps.nationalmap.gov/lidar-explorer/",
     "Interactive tile picker and very large files. Draw a small area around downtown."),
    ("VBMP orthoimagery (Days 6, 14, 29)", "https://vgin.vdem.virginia.gov/",
     "VGIN's Virginia Base Mapping Program. Easiest to add as an imagery service in Pro."),
    ("Sanborn fire insurance maps (Days 6, 15)", "https://www.loc.gov/collections/sanborn-maps/",
     "Library of Congress scans, not georeferenced. Pick sheets by hand."),
    ("HOLC map, official download (Days 6, 15)", "https://dsl.richmond.edu/panorama/redlining/",
     "Mapping Inequality city page for Richmond. The script grabs a cloud copy of the full dataset instead."),
    ("EIA power plants (Day 12)", "https://atlas.eia.gov/",
     "U.S. Energy Atlas > Power Plants layer > Download (shapefile or CSV)."),
    ("City of Richmond open data (Days 1, 3, 4, 18)", "https://data.richmondgov.com/",
     "Browse for parcels, trees, 311 requests and crime points."),
    ("Night lights (Days 9, 12, 17, 29)", "https://ladsweb.modaps.eosdis.nasa.gov/",
     "NASA Black Marble (VNP46A4 annual). Needs a free NASA Earthdata login."),
    ("Sentinel-2 L2A scene (Day 29)", "https://browser.dataspace.copernicus.eu/",
     "Copernicus Browser. Needs a free Copernicus Data Space login."),
]


def download(urls, target):
    part = target.with_suffix(target.suffix + ".part")
    last_error = None
    for url in urls:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "30dmc-downloader"})
            with urllib.request.urlopen(request, timeout=60) as response, open(part, "wb") as out:
                total = int(response.headers.get("Content-Length") or 0)
                done = 0
                while chunk := response.read(1 << 20):
                    out.write(chunk)
                    done += len(chunk)
                    if total:
                        print(f"\r    {done / 1e6:,.0f} / {total / 1e6:,.0f} MB", end="", flush=True)
            print()
            part.replace(target)
            return None
        except Exception as error:
            last_error = f"{url}: {error}"
            part.unlink(missing_ok=True)
    return last_error


def overture(dest, release):
    try:
        import pyarrow.dataset as ds
        import pyarrow.fs as fs
        import pyarrow.parquet as pq
    except ImportError:
        return ["Overture: pyarrow is not installed (pip install pyarrow)"]

    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    s3 = fs.S3FileSystem(anonymous=True, region="us-west-2", proxy_options=proxy)
    xmin, ymin, xmax, ymax = BBOX
    clip = ((ds.field("bbox", "xmin") < xmax) & (ds.field("bbox", "xmax") > xmin)
            & (ds.field("bbox", "ymin") < ymax) & (ds.field("bbox", "ymax") > ymin))
    folder = dest / "overture"
    folder.mkdir(parents=True, exist_ok=True)
    errors = []
    for theme, kind, days in OVERTURE_LAYERS:
        target = folder / f"richmond_{kind}.parquet"
        print(f"  overture/{target.name}  (days {days})")
        if target.exists():
            print("    already downloaded")
        else:
            try:
                path = f"overturemaps-us-west-2/release/{release}/theme={theme}/type={kind}/"
                table = ds.dataset(path, filesystem=s3, format="parquet").to_table(filter=clip)
                pq.write_table(table, target)
                print(f"    {table.num_rows:,} features")
            except Exception as error:
                errors.append(f"Overture {kind}: {error}")
                continue
        error = to_geopackage(target)
        if error:
            errors.append(error)
    return errors


def to_geopackage(parquet):
    """Write a GeoPackage copy with nested columns flattened, if geopandas is available."""
    target = parquet.with_suffix(".gpkg")
    if target.exists():
        return None
    try:
        import geopandas as gpd
    except ImportError:
        return None
    try:
        frame = gpd.read_parquet(parquet)
        if "names" in frame:
            frame.insert(1, "name", frame["names"].map(lambda v: v.get("primary") if v else None))
        if "categories" in frame:
            frame.insert(2, "category", frame["categories"].map(lambda v: v.get("primary") if v else None))
        for column in frame.columns:
            if column != "geometry" and frame[column].dtype == object:
                frame[column] = frame[column].map(_flatten)
        frame.to_file(target, driver="GPKG", layer=parquet.stem)
        print(f"    wrote {target.name}")
    except Exception as error:
        target.unlink(missing_ok=True)
        return f"GeoPackage {target.name}: {error}"
    return None


def _flatten(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "tolist"):
        value = value.tolist()
    return json.dumps(value, default=lambda v: v.tolist() if hasattr(v, "tolist") else str(v))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--dest", type=Path, default=ROOT / "data", help="data folder (default: data/)")
    parser.add_argument("--only", nargs="+", metavar="CATEGORY",
                        help="only these categories (e.g. elevation historic overture)")
    parser.add_argument("--large", action="store_true", help="include multi-GB downloads")
    parser.add_argument("--list", action="store_true", help="list downloads and exit")
    parser.add_argument("--overture-release", default=OVERTURE_RELEASE)
    args = parser.parse_args()

    wanted = lambda category: not args.only or category in args.only
    errors = []
    for category, name, urls, days, large in DOWNLOADS:
        if not wanted(category):
            continue
        target = args.dest / category / name
        label = f"  {category}/{name}  (days {days})"
        if large and not args.large:
            print(f"{label}\n    skipped: large file, re-run with --large")
            continue
        print(label)
        if args.list:
            continue
        if target.exists():
            print("    already downloaded")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        error = download(urls, target)
        if error:
            print(f"    FAILED: {error}")
            errors.append(f"{category}/{name}: {error}")

    if wanted("overture"):
        if args.list:
            for _, kind, days in OVERTURE_LAYERS:
                print(f"  overture/richmond_{kind}.parquet  (days {days})")
        else:
            errors += overture(args.dest, args.overture_release)

    print("\nManual downloads (login or interactive portal):")
    for name, url, note in MANUAL:
        print(f"  - {name}: {url}\n      {note}")

    if errors:
        print(f"\n{len(errors)} download(s) failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
