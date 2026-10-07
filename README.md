# TTC Travel Time — Toronto

Interactive travel-time map for **Toronto's subway and streetcars** (plus optional **bus**): pick a start point and the whole city is colored by how long it takes to get there, from the TTC's official scheduled timetables.

👉 **https://zhenhuasun.github.io/ttc-travel-time/**

Forked from [camilleroux/montpellier-temps-transport](https://github.com/camilleroux/montpellier-temps-transport) (interactive tram/metro travel-time maps for French, Belgian and Montréal networks) and adapted to a single city in English.

Features: heatmap and isochrones from a draggable start, click-to-destination with detailed itinerary (lines, transfers, walking), address search (Photon / OpenStreetMap) or station search, subway+tram or +bus, pan and zoom, share links.

## Run

```
python3 build.py --fetch            # download sources, compute the city, generate pages
python3 build.py --fetch --no-og    # without preview images (no Chrome/ImageMagick needed)

python3 -m http.server 8000 --directory site
```

Then open http://localhost:8000. `build.py` prints a control table at the end (reference day, data size, share of the network within 30 min, farthest station, frequencies).

Separate steps if needed: `fetch_data.py toronto`, `build_data.py toronto`, `build_pages.py`, `tools/render_og.py toronto|home` (Chrome and ImageMagick required), `node tools/check_trips.mjs toronto` probes trips from downtown to the termini and flags abnormal speeds.

Raw sources (`data/toronto/`: GTFS, OSM extracts) are not versioned: they stay local and `fetch_data.py toronto` re-downloads them. Only the computed site data (`site/data/toronto.json`) is versioned.

## Data provenance

Each build writes `sources/toronto.json` (versioned): URL of every source file, download date, size and SHA-256, GTFS validity period, reference day, excluded lines. `fetch_data.py` keeps download details in `data/toronto/manifest.json`. The license / download-date / GTFS-validity table is generated in [sources/README.md](sources/README.md).

City configuration lives in `cities/toronto.json` (GTFS URL, OpenStreetMap boundary, map center, display options); `cities.py` fills in the defaults.

## Data

- Schedules: TTC GTFS feed via [open.toronto.ca](https://open.toronto.ca/dataset/ttc-routes-and-schedules) (Toronto Open Government Licence)
- Municipal boundary, water and parks: © OpenStreetMap contributors (ODbL), via Overpass
- Address search in the browser: [Photon](https://photon.komoot.io/) (komoot, OpenStreetMap data)
- Audience measurement: Cloudflare Web Analytics (cookie-free)

## Model

Times come from GTFS schedules for a typical school-week Tuesday or Thursday, 7 a.m. to 8 p.m.:

- reference day = the most common service pattern among upcoming well-served Tuesdays and Thursdays;
- each inter-station duration = median of the scheduled durations;
- waiting = half the average headway at the stop (bounded between 1 and 15 min);
- transfer = 1.5 min walking + waiting for the next line; walking allowed between close stops (< 450 m);
- walking at 75 m/min (4.5 km/h) as the crow flies, no access penalty (surface stops).

No real-time data or disruptions.

## Licenses

- Code: MIT license (see [LICENSE](LICENSE)), inherited from the upstream project.
- Computed data (`site/data/*.json`, `sources/*.json`): derived databases published under [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/), as required by OpenStreetMap and the GTFS license.
- Legal notice and license of each source: https://zhenhuasun.github.io/ttc-travel-time/mentions-legales/

## Credits

Original idea: Anthony Castrio's [NYC Transit Time Cartogram](https://castrio.me/nyc/), adapted to Paris by Jules Grandin, then to 27 French/Belgian/Canadian cities by [Camille Roux](https://www.camilleroux.com/) — this fork keeps his build pipeline and map engine, reduced to Toronto and translated to English.
