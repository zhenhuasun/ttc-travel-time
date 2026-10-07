#!/usr/bin/env python3
"""Render the home page, one page per city (cities/*.json), the 404 page, sitemap.xml and robots.txt.

Usage: python3 build_pages.py   (run build_data.py <city> first: figures come from sources/<city>.json)
"""

from __future__ import annotations

import hashlib
import html
import json
import unicodedata
from datetime import date
from pathlib import Path
from string import Template
from urllib.parse import quote

from cities import load_cities

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
SITE_URL = "https://zhenhuasun.github.io/ttc-travel-time/"
GITHUB_URL = "https://github.com/camilleroux/montpellier-temps-transport"
X_URL = "https://x.com/CamilleRoux"
LINKEDIN_URL = "https://www.linkedin.com/in/camilleroux"
BLUESKY_URL = "https://bsky.app/profile/camilleroux.com"
AUTHOR_URL = "https://www.camilleroux.com/"
SITE_NAME = "Within Tram Reach"
ANALYTICS = (
    '    <!-- Cloudflare Web Analytics (cookie-free). "spa": false: URL updates don\'t count as page views. -->\n'
    '    <script type="module" src="https://static.cloudflareinsights.com/beacon.min.js" '
    "data-cf-beacon='{\"token\": \"1904c17ed0624c0cab4d69ea1bacc5e7\", \"spa\": false}'></script>"
)
LICENCES = {
    "lo": ("Licence Ouverte 2.0", "https://www.etalab.gouv.fr/licence-ouverte-open-licence/"),
    "odbl": ("ODbL", "https://opendatacommons.org/licenses/odbl/1-0/"),
    "mobilites": ("Licence Mobilités", "https://wiki.lafabriquedesmobilites.fr/wiki/Licence_Mobilit%C3%A9s"),
    "ccby": ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/deed.fr"),
    "togl": ("Open Government Licence – Toronto", "https://open.toronto.ca/open-data-licence/"),
}
GEO_CREDITS = {
    "ban": '<a href="https://geo.api.gouv.fr/">municipal boundaries</a>, address search via the\n'
    '          <a href="https://adresse.data.gouv.fr/">Base Adresse Nationale</a>.',
    "photon": 'OpenStreetMap administrative boundaries, address search via\n'
    '          <a href="https://photon.komoot.io/">Photon</a> (komoot, OpenStreetMap data).',
}
ODBL_URL = "https://opendatacommons.org/licenses/odbl/1-0/"
MODE_LABEL_SHORT = {"tram": "Tram", "metro": "Subway", "metro+tram": "Subway and tram"}
MODE_NAMES = {"metro": "Subway", "rer": "RER", "train": "Train", "tram": "Tram", "funicular": "Funicular", "cable": "Cable car", "busway": "Busway", "bhns": "BHNS"}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

esc = html.escape


def text_color(background: str) -> str:
    """Black or white text, whichever reads best on a line colour (yellow lines need black)."""
    value = int(background.lstrip("#")[:6] or "888888", 16)
    luminance = 0.299 * (value >> 16) + 0.587 * ((value >> 8) & 255) + 0.114 * (value & 255)
    return "#111" if luminance > 150 else "#fff"


def line_badge(color: str, name: str) -> str:
    return f'<span class="line-badge" style="background:{color};color:{text_color(color)}">{esc(name)}</span>'


def thousands(value: int) -> str:
    """English thousands separator: 2445 → "2,445"."""
    return f"{value:,}"


def num(value: float) -> str:
    """English decimal point: 4.4 → "4.4"."""
    return f"{value:g}"


def short_hash(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()[:8] if path.exists() else "0"


def french_date(value: str, weekday: bool = False) -> str:
    day = date.fromisoformat(value[:10])
    text = f"{day.day} {MONTHS[day.month - 1]} {day.year}"
    return f"{WEEKDAYS[day.weekday()]} {text}" if weekday else text


def load_built_cities() -> list[dict]:
    """Cities whose data has been built, with their figures (sources/<city>.json)."""
    cities = []
    for city in load_cities():
        sources = ROOT / "sources" / f"{city['slug']}.json"
        if not sources.exists() or not (SITE / "data" / f"{city['slug']}.json").exists():
            print(f"  {city['slug']} skipped: run build_data.py {city['slug']} first")
            continue
        city["sources"] = json.loads(sources.read_text(encoding="utf-8"))
        city["stats"] = city["sources"]["stats"]
        cities.append(city)
    return cities


def json_ld(data: dict) -> str:
    body = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return '    <script type="application/ld+json">\n    ' + body.replace("\n", "\n    ") + "\n    </script>"


def head(*, title: str, description: str, url: str, base: str, image: str, image_alt: str, published: str, graph: list) -> str:
    """<head> content shared by every page: SEO, social previews, structured data."""
    redirect = (
        "    <script>\n"
        "      // Old github.io links: redirect to the site domain, keeping origin and destination.\n"
        f'      if (location.hostname.endsWith("github.io")) location.replace("{url}" + location.search);\n'
        "    </script>"
    )
    title_text = esc(title.split(" · ")[0])
    return "\n".join(
        [
            '    <meta charset="utf-8" />',
            '    <meta name="viewport" content="width=device-width, initial-scale=1" />',
            f"    <title>{esc(title)}</title>",
            f'    <meta name="description" content="{esc(description)}" />',
            redirect,
            f'    <link rel="canonical" href="{url}" />',
            '    <meta name="theme-color" content="#3aa70b" />',
            f'    <link rel="icon" href="{base}favicon.svg" type="image/svg+xml" />',
            f'    <link rel="icon" href="{base}favicon-32.png" type="image/png" sizes="32x32" />',
            f'    <link rel="apple-touch-icon" href="{base}apple-touch-icon.png" />',
            '    <meta name="author" content="Camille Roux" />',
            f'    <link rel="author" href="{AUTHOR_URL}" />',
            '    <meta property="og:type" content="website" />',
            '    <meta property="og:locale" content="en_US" />',
            f'    <meta property="og:site_name" content="{SITE_NAME}" />',
            f'    <meta property="og:title" content="{title_text}" />',
            f'    <meta property="og:description" content="{esc(description)}" />',
            f'    <meta property="og:url" content="{url}" />',
            f'    <meta property="og:image" content="{image}" />',
            '    <meta property="og:image:width" content="1200" />',
            '    <meta property="og:image:height" content="630" />',
            f'    <meta property="og:image:alt" content="{esc(image_alt)}" />',
            f'    <meta property="article:author" content="{AUTHOR_URL}" />',
            f'    <meta property="article:published_time" content="{published}T08:00:00+02:00" />',
            '    <meta name="twitter:card" content="summary_large_image" />',
            f'    <meta name="twitter:title" content="{title_text}" />',
            f'    <meta name="twitter:description" content="{esc(description)}" />',
            f'    <meta name="twitter:image" content="{image}" />',
            json_ld({"@context": "https://schema.org", "@graph": graph}),
            '    <link rel="preconnect" href="https://fonts.bunny.net" />',
            '    <link rel="stylesheet" href="https://fonts.bunny.net/css?family=inter:400,500,600,700,800" />',
        ]
    )


def header(base: str) -> str:
    return f"""    <header class="topbar">
      <nav class="topbar-inner" aria-label="Main navigation">
        <a class="brand" href="{base}"><img src="{base}favicon.svg" width="22" height="22" alt="" /> {SITE_NAME}</a>
        <div class="topbar-links">
          <a class="topbar-link" href="{base}{RANKINGS_DIR}/">🏆 Rankings</a>
          <a class="topbar-link" href="{AUTHOR_URL}" rel="author">camilleroux.com</a>
        </div>
      </nav>
    </header>"""


def footer(cities: list[dict], base: str, data_credit: str, geocoder: str = "ban") -> str:
    links = " · ".join(f'<a href="{base}{city["path"]}">{esc(city["name"])}</a>' for city in sorted(cities, key=lambda c: c["name"]))
    return f"""    <footer class="site-footer">
      <div class="footer-inner">
        <p class="footer-author">
          A project by <a href="{AUTHOR_URL}" rel="author">Camille Roux</a>, developer and co-founder of Human Coders,
          in Montpellier, based on the idea by Anthony Castrio and Jules Grandin. See
          <a href="{AUTHOR_URL}realisations/">his other projects</a> and his
          <a href="{AUTHOR_URL}veille/">weekly tech watch</a>.
        </p>
        <p class="footer-links">Cities: {links}</p>
        <p class="footer-links">
          <a href="{GITHUB_URL}" rel="noopener">Source code on GitHub</a> ·
          <a href="{GITHUB_URL}/issues" rel="noopener">Suggest a city or report an error</a> ·
          <a href="{base}rankings/">Rankings</a> ·
          <a href="{base}mentions-legales/">Legal notice and licenses</a>
        </p>
        <p class="footer-credits">
          Original idea: Anthony Castrio's <a href="https://castrio.me/nyc/">NYC Transit Time Cartogram</a>,
          later adapted to Paris by Jules Grandin
          (<a href="https://julesgrandin.github.io/paris-temps-transport/">C'est encore loin&nbsp;?</a>).
          {data_credit} Basemap © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>,
          {GEO_CREDITS[geocoder]}
          Computed data published under the <a href="{ODBL_URL}">ODbL</a> license, code under the MIT license.
        </p>
      </div>
    </footer>"""


X_ICON = (
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18.24 2.25h3.31l-7.23 8.26 8.5 11.24h-6.65l-5.21-6.82-5.97 '
    '6.82H1.68l7.73-8.84L1.25 2.25h6.83l4.71 6.23zm-1.16 17.52h1.83L7.08 4.13H5.12z"/></svg>'
)
LINKEDIN_ICON = (
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.13 '
    '1.45-2.13 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 4.9v6.29zM5.34 7.43a2.06 '
    '2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12zM7.12 20.45H3.56V9h3.56zM22.23 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 '
    '24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z"/></svg>'
)


def follow_note() -> str:
    """Under the list of cities: where the next ones are announced, and where to ask for one."""
    return f"""        <aside class="follow-card" aria-label="New cities">
          <div class="follow-text">
            <p class="follow-title">Follow new cities</p>
            <p>Every new city is announced on X and LinkedIn. Yours isn't there yet?
            <a href="{GITHUB_URL}/issues" rel="noopener">Suggest it on GitHub</a>.</p>
          </div>
          <div class="follow-actions">
            <a class="button follow-x" href="{X_URL}" rel="me noopener">{X_ICON} Follow on X</a>
            <a class="button follow-linkedin" href="{LINKEDIN_URL}" rel="me noopener">{LINKEDIN_ICON} Follow on LinkedIn</a>
          </div>
        </aside>"""


def faq_block(entries: list[tuple]) -> str:
    """Entries are (question, answer) or (question, answer, answer_html) when the visible answer carries links."""
    return "\n".join(
        f'        <details class="faq"><summary>{esc(entry[0])}</summary><p>{entry[2] if len(entry) > 2 else esc(entry[1])}</p></details>'
        for entry in entries
    )


def faq_schema(entries: list[tuple]) -> dict:
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": entry[0], "acceptedAnswer": {"@type": "Answer", "text": entry[1]}} for entry in entries
        ],
    }


def credits_entry(question: str) -> tuple:
    """« Who made this? »: the original authors first, then the author of these maps."""
    text = (
        "The idea comes from Anthony Castrio's NYC Transit Time Cartogram, later adapted to Paris by Jules Grandin "
        '("C\'est encore loin ?"). These maps are made by Camille Roux, developer and co-founder of Human '
        "Coders in Montpellier, who showcases his other projects and his weekly tech watch on camilleroux.com. The "
        "code is open on GitHub."
    )
    html_text = (
        'The idea comes from <a href="https://castrio.me/nyc/">NYC Transit Time Cartogram</a> by Anthony Castrio, later '
        'adapted to Paris by Jules Grandin (<a href="https://julesgrandin.github.io/paris-temps-transport/">C\'est encore '
        f'loin&nbsp;?</a>). These maps are made by <a href="{AUTHOR_URL}" rel="author">Camille Roux</a>, developer '
        f'and co-founder of Human Coders in Montpellier: see <a href="{AUTHOR_URL}realisations/">his other '
        f'projects</a> and <a href="{AUTHOR_URL}veille/">his weekly tech watch</a>. The code is open on '
        f'<a href="{GITHUB_URL}">GitHub</a>.'
    )
    return (question, text, html_text)


def author_schema() -> dict:
    return {
        "@type": "Person",
        "@id": AUTHOR_URL + "#me",
        "name": "Camille Roux",
        "url": AUTHOR_URL,
        "image": AUTHOR_URL + "content/images/size/w256h256/format/jpeg/2025/05/camillecouleur---lowres-2.jpg",
        "jobTitle": "Developer, co-founder of Human Coders",
        "worksFor": {"@type": "Organization", "name": "Human Coders", "url": "https://www.humancoders.com/"},
        "address": {"@type": "PostalAddress", "addressLocality": "Montpellier", "addressCountry": "FR"},
        "sameAs": [
            LINKEDIN_URL,
            X_URL,
            BLUESKY_URL,
            "https://mastodon.social/@camilleroux",
            "https://github.com/camilleroux",
        ],
    }


# « in France, in Belgium and in Quebec »: where the cities are, for the home page.
COUNTRY_IN = {"FR": "in France", "BE": "in Belgium", "CA": "in Quebec", "CH": "in Switzerland", "LU": "in Luxembourg"}


def city_count(cities: list[dict]) -> str:
    """« 27 French cities », then « 27 cities in France, in Belgium and in Quebec » once there are cities abroad."""
    countries = sorted({city["country"] for city in cities}, key=list(COUNTRY_IN).index)
    if countries == ["FR"]:
        return f"{len(cities)} French cities"
    places = [COUNTRY_IN[country] for country in countries]
    return f"{len(cities)} cities " + ", ".join(places[:-1]) + f" and {places[-1]}"


def city_card(city: dict, base: str, heading: str = "h3") -> str:
    stats = city["stats"]
    return f"""          <a class="city-card" href="{base}{city['path']}">
            <img src="{base}og/thumb-{city['slug']}.jpg" width="600" height="315" alt="" loading="lazy" />
            <span class="city-card-body">
              <{heading}>{esc(city['title'])}</{heading}>
              <span>{stats['within30']}% of {esc(city['railStations'])} within 30 min of downtown ({esc(stats['center'])}) · {esc(city['network'])} network</span>
            </span>
          </a>"""


def city_faq(city: dict) -> list[tuple]:
    stats, sources = city["stats"], city["sources"]
    name, rail = city["name"], city["railNoun"]
    lines = stats["lines"]
    headways = ", ".join(f"{MODE_NAMES.get(line['mode'], 'line').lower()} {line['name']}: {num(line['headway'])} min" for line in lines)
    fastest = min(lines, key=lambda line: line["headway"])
    period = sources["gtfs"].get("servicePeriod") or [None, None]
    fetched = sources["gtfs"].get("fetchedAt")
    return [
        (
            f"How long does it take to cross {name} by {rail}?",
            f"From downtown ({stats['center']}), {stats['within15']}% of {city['railStations']} are within 15 minutes and "
            f"{stats['within30']}% within 30 minutes, walking and waiting included. The farthest, {stats['farthestStation']}, "
            f"is about {stats['farthestMinutes']} minutes away.",
        ),
        (
            f"How frequent are the {rail} lines in {name}?",
            f"On a weekday during the day, the average interval between two services is {headways}. The most frequent "
            f"line is {fastest['name']}, with a service about every {num(fastest['headway'])} minutes.",
        ),
        (
            "Where do the timetables used come from?",
            f"From the scheduled timetables published by the {city['network']} network (GTFS format, {LICENCES[city['gtfsLicence']][0]})"
            + (f", downloaded on {french_date(fetched)}" if fetched else "")
            + (f" and valid until {french_date(period[1])}" if period[1] else "")
            + f". Travel times are for {french_date(sources['referenceDate'], weekday=True)}, between 7 a.m. and 8 p.m.",
        ),
        (
            f"Are buses included in {name}?",
            f"Yes, optionally: check \"{city['busLabel']}\" under the map. By default, only {rail} are shown. "
            "Waiting time at infrequent bus stops is capped at 15 minutes.",
        ),
        (
            "How are travel times calculated?",
            "For each trip: walk to the stop at 4.5 km/h, waiting time equal to half the interval between two "
            "services, scheduled time between stops, transfers with 1.5 minutes of walking"
            + (", plus 1 minute to reach the subway platform" if any(line["mode"] == "metro" for line in lines) else "")
            + '. No real-time data or disruptions: this is the city "on paper".',
        ),
        credits_entry(f"Who made this map of {name}?"),
    ]


def ranking_positions_block(cities: list[dict], city: dict) -> str:
    items = city_positions(cities, city["slug"], "../")
    if not items:
        return ""
    lines = "\n".join(f"          {item}" for item in items)
    return f"""        <h3 class="ranking-positions-title">🏆 {esc(city["name"])} in the rankings</h3>
        <ul class="ranking-positions">
{lines}
        </ul>
        <p class="section-link"><a href="../{RANKINGS_DIR}/">All French tram and subway rankings →</a></p>"""


def original_map(city: dict) -> str:
    """Paris had a map before this site: Jules Grandin's, which inspired it. It comes first, above this one."""
    original = city.get("originalMap")
    if not original:
        return ""
    return f"""        <aside class="original-map">
          <p>
            <strong>The original map is {esc(original["author"])}'s:</strong>
            <a href="{esc(original["url"])}">{esc(original["title"]).replace(" ?", "&nbsp;?")}</a>, in {esc(original["modes"])}, which
            inspired this whole site (itself part of Anthony Castrio's <a href="https://castrio.me/nyc/">NYC Transit Time Cartogram</a>).
            Go see it! This version starts from the {esc(city["network"])} timetables and adds
            {esc(original["adds"])}.
          </p>
        </aside>
"""


def render_city(template: Template, cities: list[dict], city: dict) -> str:
    url = SITE_URL + city["path"]
    base = "../"
    stats = city["stats"]
    rail_noun = city["railNoun"]
    description = (
        f"{rail_noun} travel-time map of {city['name']}: pick a starting point and the whole city is colored "
        f"by how long it takes to get there ({city['network']} network)."
    )
    faq = city_faq(city)
    graph = [
        {
            "@type": "WebApplication",
            "name": city["title"],
            "url": url,
            "description": description,
            "inLanguage": "en",
            "applicationCategory": "TravelApplication",
            "operatingSystem": "Web",
            "isAccessibleForFree": True,
            "image": f"{SITE_URL}og/{city['slug']}.jpg",
            "author": {"@id": AUTHOR_URL + "#me"},
            "spatialCoverage": {"@type": "Place", "name": city["metropole"]},
            "isBasedOn": ["https://castrio.me/nyc/", "https://julesgrandin.github.io/paris-temps-transport/"],
            "datePublished": city["published"],
            "dateModified": city["sources"]["builtAt"][:10],
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": SITE_NAME, "item": SITE_URL},
                {"@type": "ListItem", "position": 2, "name": city["name"], "item": url},
            ],
        },
        faq_schema(faq),
        author_schema(),
    ]
    fastest = min(stats["lines"], key=lambda line: line["headway"])
    tiles = [
        (f"{stats['within30']}%", f"of {city['railStations']} within 30 min of downtown ({stats['center']})"),
        (str(stats["railStations"]), city["railStations"]),
        (f"{num(fastest['headway'])} min", f"between services on line {fastest['name']}, the most frequent"),
        (f"{stats['farthestMinutes']} min", f"from downtown to {stats['farthestStation']}, the farthest station"),
    ]
    stat_tiles = "\n".join(f'          <div class="stat"><strong>{esc(value)}</strong><span>{esc(label)}</span></div>' for value, label in tiles)
    line_rows = "\n".join(
        f'            <tr><td>{line_badge(line["color"], line["name"])} '
        f'{esc(MODE_NAMES.get(line["mode"], ""))}</td><td>{line["stations"]}</td><td>~{num(line["headway"])} min</td></tr>'
        for line in stats["lines"]
    )
    # City switcher: the city name in the title opens a panel of real links (site/app.js), crawlable as well.
    items = "\n".join(
        f'            <a class="city-item{" current" if other["slug"] == city["slug"] else ""}" href="{base}{other["path"]}"'
        f'{" aria-current=\"page\"" if other["slug"] == city["slug"] else ""} data-name="{esc(other["name"].lower())}">'
        f'<img src="{base}og/thumb-{other["slug"]}.jpg" width="120" height="63" alt="" loading="lazy" />'
        f'<span><strong>{esc(other["name"])}</strong><small>{esc(MODE_LABEL_SHORT[other["kind"]])} · {esc(other["network"])}</small></span></a>'
        for other in sorted(cities, key=lambda item: item["name"])
    )
    rest = esc(city["title"][len(city["name"]):])
    headline = (
        f'<button id="cityTrigger" type="button" class="city-trigger" aria-haspopup="dialog" aria-expanded="false" '
        f'title="Switch city">{esc(city["name"])}<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 6l5 5 5-5"/></svg></button>'
        + "&nbsp;".join(rest.rsplit(" ", 1))
    )
    config = {
        "slug": city["slug"],
        "name": city["name"],
        "dataVersion": short_hash(SITE / "data" / f"{city['slug']}.json"),
        "defaultFrom": city["defaultFrom"],
        "railNoun": rail_noun,
        "railStations": city["railStations"],
        "busNoun": city["busNoun"],
        "geocoder": city["geocoder"],
        "searchBbox": city["osmBbox"],
    }
    feeds = " and ".join(f'<a href="{esc(feed["dataset"])}">GTFS {esc(feed["network"])}</a>' for feed in gtfs_feeds(city))
    data_credit = f'Timetables: {feeds} ({esc(city["metropole"])}).'

    values = {
        "head": head(
            title=f"{city['title']} · {city['titleSuffix']}",
            description=description,
            url=url,
            base=base,
            image=f"{SITE_URL}og/{city['slug']}.jpg?v={short_hash(SITE / 'og' / (city['slug'] + '.jpg'))}",
            image_alt=city["ogAlt"],
            published=city["published"],
            graph=graph,
        ),
        "header": header(base),
        "footer": footer(cities, base, data_credit, city["geocoder"]),
        "analytics": ANALYTICS,
        "base": base,
        "city_config": json.dumps(config, ensure_ascii=False).replace("</", "<\\/"),
        "city_items": items,
        "original_map": original_map(city),
        "headline": headline,
        "name": esc(city["name"]),
        "area": esc(city.get("area", "of the metro area")),
        "rail_noun": esc(rail_noun),
        "rail_label": esc(city["railLabel"]),
        "bus_label": esc(city["busLabel"]),
        "search_example": esc(city["searchExample"]),
        "network": esc(city["network"]),
        "stat_tiles": stat_tiles,
        "ranking_positions": ranking_positions_block(cities, city),
        "line_rows": line_rows,
        "faq_html": faq_block(faq),
        "follow": follow_note(),
        "other_cities": "\n".join(city_card(other, base) for other in cities if other["slug"] != city["slug"]),
        "styles_version": short_hash(SITE / "styles.css"),
        "app_version": short_hash(SITE / "app.js"),
    }
    return template.substitute(values)


def render_home(template: Template, cities: list[dict]) -> str:
    names = ", ".join(city["name"] for city in cities[:-1]) + f" and {cities[-1]['name']}"
    networks = ", ".join(f"{city['network']} ({city['name']})" for city in cities)
    description = f"Tram and subway travel-time maps for {names}: the city is colored by how long it takes to get there."
    faq = [
        (
            "Where do the travel times come from?",
            f"From the official scheduled timetables of each network ({networks}), published as open data in GTFS format. "
            "They cover an ordinary weekday, between 7 a.m. and 8 p.m.",
        ),
        (
            "Are the displayed times reliable?",
            'These are "on paper" averages: walk to the stop, waiting time equal to half the interval between '
            "two services, scheduled time between stops, and transfers. No real-time data or disruptions.",
        ),
        (
            "Are buses included?",
            "Yes, optionally on each map. By default, only trams, subways and guided transit are shown, "
            "to highlight the backbone of the network.",
        ),
        (
            "My city isn't there — why?",
            "It needs a tram or subway network with timetables published as open data. New cities are added "
            "over time: you can suggest one on GitHub, and each new city is announced on X "
            "and LinkedIn.",
            "It needs a tram or subway network with timetables published as open data. New cities are added "
            f'over time: you can <a href="{GITHUB_URL}/issues">suggest one on GitHub</a>, and each '
            f'new city is announced on <a href="{X_URL}">X</a> and <a href="{LINKEDIN_URL}">LinkedIn</a>.',
        ),
        credits_entry("Who made this site?"),
    ]
    graph = [
        {
            "@type": "WebSite",
            "@id": SITE_URL + "#site",
            "name": SITE_NAME,
            "url": SITE_URL,
            "description": description,
            "inLanguage": "en",
            "author": {"@id": AUTHOR_URL + "#me"},
        },
        {
            "@type": "ItemList",
            "name": "Travel-time maps by city",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": city["title"], "url": SITE_URL + city["path"]}
                for i, city in enumerate(cities)
            ],
        },
        faq_schema(faq),
        author_schema(),
    ]
    published = min(city["published"] for city in cities)
    values = {
        "head": head(
            title=f"{SITE_NAME} · Tram and subway travel times by city",
            description=description,
            url=SITE_URL,
            base="./",
            image=SITE_URL + "og/home.jpg?v=" + short_hash(SITE / "og" / "home.jpg"),
            image_alt=f"Tram and subway travel-time maps for {names}.",
            published=published,
            graph=graph,
        ),
        "header": header("./"),
        "footer": footer(cities, "./", "Timetables: GTFS feeds from each city's network (details in the legal notice)."),
        "analytics": ANALYTICS,
        "city_count": city_count(cities),
        "city_cards": "\n".join(city_card(city, "./", "h2") for city in cities),
        "city_links": "\n".join(
            f'          <a class="chip" href="./{city["path"]}">{esc(city["name"])}</a>'
            for city in sorted(cities, key=lambda city: unicodedata.normalize("NFD", city["name"]))
        ),
        "faq_html": faq_block(faq),
        "follow": follow_note(),
        "styles_version": short_hash(SITE / "styles.css"),
    }
    return template.substitute(values)


def gtfs_feeds(city: dict) -> list[dict]:
    """The feeds of a city: its main GTFS, then the extra ones merged into it (the REM next to the STM in Montréal)."""
    main = {
        "network": city.get("gtfsNetwork", city["network"]),
        "dataset": city["gtfsDataset"],
        "licence": city["gtfsLicence"],
        "fetchedAt": city["sources"]["gtfs"].get("fetchedAt"),
    }
    fetched = {extra["network"]: extra.get("fetchedAt") for extra in city["sources"].get("gtfsExtra", [])}
    extras = [{**extra, "fetchedAt": fetched.get(extra["network"])} for extra in city.get("gtfsExtra", [])]
    return [main, *extras]


def render_legal(cities: list[dict]) -> str:
    """Legal notice and the licence of every source."""
    rows = "\n".join(
        f'          <tr><td>{esc(city["name"])}</td><td><a href="{esc(feed["dataset"])}">GTFS {esc(feed["network"])}</a></td>'
        f'<td><a href="{LICENCES[feed["licence"]][1]}">{LICENCES[feed["licence"]][0]}</a></td>'
        f'<td>{french_date(feed["fetchedAt"]) if feed["fetchedAt"] else "—"}</td></tr>'
        for city in sorted(cities, key=lambda item: item["name"])
        for feed in gtfs_feeds(city)
    )
    rows += "".join(
        f'\n          <tr><td>{esc(city["city"])} (rankings)</td><td><a href="{esc(city["source"]["dataset"])}">GTFS {esc(city["network"])}</a></td>'
        f'<td><a href="{LICENCES[city["source"]["licence"]][1]}">{LICENCES[city["source"]["licence"]][0]}</a></td>'
        f'<td>{french_date(city["source"]["fetchedAt"])}</td></tr>'
        for city in load_rankings(cities)
        if city.get("externalUrl")
    )
    graph = [author_schema()]
    return f"""<!doctype html>
<html lang="en">
  <head>
{head(title=f"Legal notice and licenses · {SITE_NAME}", description="Publisher, hosting, audience measurement and data licenses used by Within Tram Reach.", url=SITE_URL + "mentions-legales/", base="../", image=SITE_URL + "og/home.jpg", image_alt="Within Tram Reach", published="2026-10-05", graph=graph)}
    <link rel="stylesheet" href="../styles.css?v={short_hash(SITE / 'styles.css')}" />
  </head>
  <body>
{header('../')}
    <main class="page">
      <nav class="breadcrumb" aria-label="Breadcrumb">
        <a href="../">{SITE_NAME}</a> <span aria-hidden="true">›</span> <span aria-current="page">Legal notice</span>
      </nav>
      <section class="section">
        <h1 class="page-title">Legal notice and licenses</h1>
        <h2>Publisher</h2>
        <p>This site is published personally by <a href="{AUTHOR_URL}" rel="author">Camille Roux</a>. Contact: via
        <a href="{AUTHOR_URL}contact/">the camilleroux.com contact page</a> or the project's <a href="{GITHUB_URL}/issues">GitHub issues</a>.</p>
        <h2>Hosting</h2>
        <p>GitHub, Inc. (GitHub Pages), 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, United States.
        Domain name managed by Cloudflare, Inc., 101 Townsend Street, San Francisco, CA 94107, United States.</p>
        <h2>Audience measurement and personal data</h2>
        <p>Traffic is measured with Cloudflare Web Analytics, with no cookies or personal identifiers. Trips are
        computed in your browser: no location or address is stored. Address search queries the Base Adresse Nationale API
        (adresse.data.gouv.fr) and, outside France, komoot's Photon API (photon.komoot.io, OpenStreetMap data).</p>
        <h2>Licenses</h2>
        <p>The code is published under the MIT license on <a href="{GITHUB_URL}">GitHub</a>. The computed data
        (<code>data/*.json</code>) are derived databases, published under the <a href="{ODBL_URL}">ODbL</a> license.
        Basemap and routes: © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>
        (ODbL). Municipal boundaries: <a href="https://geo.api.gouv.fr/">geo.api.gouv.fr</a> (Licence Ouverte) and, outside
        France, OpenStreetMap administrative boundaries (ODbL).</p>
        <table class="lines-table">
          <caption>Timetables used for each city</caption>
          <thead><tr><th scope="col">City</th><th scope="col">Source</th><th scope="col">License</th><th scope="col">Downloaded on</th></tr></thead>
          <tbody>
{rows}
          </tbody>
        </table>
      </section>
    </main>
{footer(cities, "../", "")}
{ANALYTICS}
  </body>
</html>
"""


def write_sources_readme(cities: list[dict]) -> None:
    lines = [
        "# Data provenance",
        "",
        "Generated by `build_pages.py` from the `sources/<city>.json` records.",
        "",
        "| City | Network | License | GTFS downloaded on | GTFS validity | Reference day |",
        "|---|---|---|---|---|---|",
    ]
    for city in sorted(cities, key=lambda item: item["name"]):
        gtfs = city["sources"]["gtfs"]
        period = gtfs.get("servicePeriod") or ["?", "?"]
        how = " (manual)" if gtfs.get("how") == "manual" else ""
        lines.append(
            f"| [{city['name']}]({city['slug']}.json) | {city['network']} | {LICENCES[city['gtfsLicence']][0]} | "
            f"{gtfs.get('fetchedAt', '?')[:10]}{how} | {period[0]} → {period[1]} | {city['sources']['referenceDate']} |"
        )
    (ROOT / "sources" / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


RANKINGS_DIR = "rankings"
MEDALS = ["🥇", "🥈", "🥉"]


def load_rankings(cities: list[dict]) -> list[dict]:
    """Figures read straight from the timetables (sources/rankings.json, written by tools/rankings.py).

    Cities with a map here, plus the ones that only take part in the rankings (`externalUrl`: their map is elsewhere).
    """
    path = ROOT / "sources" / "rankings.json"
    if not path.exists():
        return []
    published = {city["slug"] for city in cities}
    entries = json.loads(path.read_text(encoding="utf-8")).values()
    return [city for city in entries if city["slug"] in published or city.get("externalUrl")]


def ordinal(rank: int) -> str:
    if 10 <= rank % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(rank % 10, "th")
    return f"{rank}<sup>{suffix}</sup>"


def clock(seconds: int) -> str:
    """Time of night in French: 26:27 → « 2 h 27 »."""
    hours, minutes = divmod(seconds // 60, 60)
    return f"{hours % 24}&nbsp;h&nbsp;{minutes:02d}"


def competition_ranks(values: list[float]) -> list[int]:
    """Rank of each value (sorted, best first); equal values share a rank: 1, 2, 2, 4."""
    return [1 + sum(1 for other in values if other > value) for value in values]


def ranking_definitions(data: list[dict], base: str) -> list[dict]:
    """The five published rankings. Each row: its cells, the value it is ranked on, its city and mode."""

    def city_link(city: dict) -> str:
        if city.get("externalUrl"):
            return f'<a href="{esc(city["externalUrl"])}" rel="noopener" title="Jules Grandin\'s map">{esc(city["city"])}</a>'
        return f'<a href="{base}{city["path"]}">{esc(city["city"])}</a>'

    def line_label(line: dict, name: str) -> str:
        return f'{line_badge(line["color"], name)} {esc(MODE_NAMES[line["mode"]])}'

    lines = [(city, name, line) for city in data for name, line in city["lines"].items() if line["peakPassages"]]
    frequent = sorted(lines, key=lambda item: (-item[2]["peakPassages"], item[0]["city"], item[1]))
    stations = sorted(data, key=lambda city: (-city["busiestStation"]["passages"], city["city"]))
    longest = sorted(lines, key=lambda item: (-item[2]["endToEndMinutes"], item[0]["city"], item[1]))
    trips = sorted(data, key=lambda city: (-city["weekdayTrips"], city["city"]))
    night = sorted(
        (city for city in data if city.get("centre", {}).get("lastSaturday")),
        key=lambda city: (-city["centre"]["lastSaturday"]["seconds"], city["city"]),
    )

    def night_line(city: dict) -> str:
        last = city["centre"]["lastSaturday"]
        line = city["lines"].get(last["line"])
        return line_label(line, last["line"]) if line else esc(last["line"])

    def station_cell(city: dict) -> str:
        best = city["busiestStation"]
        if best["station"]:
            return esc(best["station"])
        tied = [esc(name) for name in best["tied"]]
        if len(tied) > 3:
            return f'<span class="muted">Tie between {len(tied)} stations</span>'
        return f'<span class="muted">Tied: {", ".join(tied[:-1])} and {tied[-1]}</span>'

    def line_rows(items: list, value, cells) -> list[dict]:
        return [
            {"city": city["slug"], "line": name, "mode": line["mode"], "value": value(line), "cells": cells(city, name, line)}
            for city, name, line in items
        ]

    return [
        {
            "slug": "dernier-tram-samedi-soir",
            "short": "The last Saturday tram",
            "title": "The last Saturday-night tram and subway, city by city",
            "question": "Where can you get home latest by tram or subway on a Saturday night?",
            "intro": "After the concert, the bar or the restaurant: until what time can you still catch a tram or a "
            "subway right downtown, on Saturday night into Sunday?",
            "method": "Last tram or subway service at the downtown station (the one on each map's central square), on "
            "Saturday night into Sunday, based on the scheduled timetables of an ordinary Saturday. "
            "Night buses are not counted.",
            "headers": ["City", "Downtown station", "Line", "Last service"],
            "valueCol": 3,
            "rows": [
                {"city": city["slug"], "mode": None, "value": city["centre"]["lastSaturday"]["seconds"],
                 "cells": [city_link(city), esc(city["centre"]["station"]), night_line(city), clock(city["centre"]["lastSaturday"]["seconds"])]}
                for city in night
            ],
            "podium": [(clock(city["centre"]["lastSaturday"]["seconds"]), esc(city["centre"]["station"]), esc(city["city"])) for city in night[:3]],
            "highlight": (
                clock(night[0]["centre"]["lastSaturday"]["seconds"]),
                f'last Saturday-night service at {esc(night[0]["centre"]["station"])} station ({esc(night[0]["city"])})',
            ),
            "position": lambda rank, total, city: (
                f'{ordinal(rank)} of {total} for the last Saturday-night tram: '
                f'{clock(city["centre"]["lastSaturday"]["seconds"])} at {esc(city["centre"]["station"])} station'
            ),
        },
        {
            "slug": "metro-tram-le-plus-frequent",
            "short": "The most frequent",
            "title": "France's most frequent subways and trams",
            "question": "A subway or tram every how many minutes?",
            "intro": "At rush hour, some lines run every couple of minutes, others every ten minutes. "
            "Here are the tram and subway lines where you wait the least.",
            "method": "Number of services between 8 and 9 a.m. on a weekday, at the busiest station and in the busiest "
            "direction of each line.",
            "headers": ["City", "Line", "Services 8 – 9 a.m.", "One service every"],
            "valueCol": 2,
            "byMode": True,
            "rows": line_rows(
                frequent,
                lambda line: line["peakPassages"],
                lambda city, name, line: [city_link(city), line_label(line, name), str(line["peakPassages"]), f'{num(line["peakHeadway"])} min'],
            ),
            "podium": [
                (f'{num(line["peakHeadway"])} min', f'{esc(MODE_NAMES[line["mode"]])} {esc(name)}', esc(city["city"]))
                for city, name, line in frequent[:3]
            ],
            "highlight": (
                f'{num(frequent[0][2]["peakHeadway"])} min',
                f'between two {MODE_NAMES[frequent[0][2]["mode"]].lower()} trains on line {esc(frequent[0][1])} in {esc(frequent[0][0]["city"])}',
            ),
            "position": lambda rank, total, city, name, line: (
                f'{ordinal(rank)} most frequent {MODE_NAMES[line["mode"]].lower()} out of {total}: line {esc(name)}, '
                f'a service every {num(line["peakHeadway"])} min at rush hour'
            ),
        },
        {
            "slug": "station-la-plus-desservie",
            "short": "The busiest station",
            "title": "The busiest tram or subway station in each city",
            "question": "Which station sees the most trains pass through?",
            "intro": "The hub of the network, where the lines cross: each city's station with the most trams and "
            "subways passing through during the day.",
            "method": "Tram and subway services (all lines, both directions) on a weekday, platforms sharing a name "
            "grouped together. When several stations on the same shared trunk are tied, none is singled out.",
            "headers": ["City", "Station", "Services per day"],
            "valueCol": 2,
            "rows": [
                {"city": city["slug"], "mode": None, "value": city["busiestStation"]["passages"],
                 "cells": [city_link(city), station_cell(city), thousands(city["busiestStation"]["passages"])]}
                for city in stations
            ],
            "podium": [
                (thousands(city["busiestStation"]["passages"]), esc(city["busiestStation"]["station"] or "—"), esc(city["city"]))
                for city in stations[:3]
            ],
            "highlight": (
                thousands(stations[0]["busiestStation"]["passages"]),
                f'services per day at {esc(stations[0]["busiestStation"]["station"] or "")} ({esc(stations[0]["city"])})',
            ),
            "position": lambda rank, total, city: (
                f'{ordinal(rank)} of {total} for busiest station: '
                + (esc(city["busiestStation"]["station"]) + ", " if city["busiestStation"]["station"] else "")
                + f'{thousands(city["busiestStation"]["passages"])} services per day'
            ),
        },
        {
            "slug": "ligne-la-plus-longue",
            "short": "The longest line",
            "title": "The longest tram and subway rides",
            "question": "How long from one terminus to the other?",
            "intro": "Some lines cross the whole metro area: here are the ones that take the longest to ride from "
            "end to end.",
            "method": "Scheduled time from one terminus to the other, on a weekday, on the longest of the line's regular "
            "trips (at least a third of the most common trip's services): the whole line, excluding partial services "
            "and exceptional runs.",
            "headers": ["City", "Line", "Trip", "Duration"],
            "valueCol": 3,
            "byMode": True,
            "rows": line_rows(
                longest,
                lambda line: line["endToEndMinutes"],
                lambda city, name, line: [city_link(city), line_label(line, name), esc(line["endToEnd"]), f'{line["endToEndMinutes"]} min'],
            ),
            "podium": [
                (f'{line["endToEndMinutes"]} min', f'{esc(MODE_NAMES[line["mode"]])} {esc(name)}', esc(city["city"]))
                for city, name, line in longest[:3]
            ],
            "highlight": (
                f'{longest[0][2]["endToEndMinutes"]} min',
                f'end to end on line {esc(longest[0][1])} in {esc(longest[0][0]["city"])}',
            ),
            "position": lambda rank, total, city, name, line: (
                f'{ordinal(rank)} longest {MODE_NAMES[line["mode"]].lower()} line out of {total}: '
                f'line {esc(name)}, {line["endToEndMinutes"]} min end to end'
            ),
        },
        {
            "slug": "reseau-le-plus-fourni",
            "short": "The most extensive network",
            "title": "France's most extensive tram and subway network",
            "question": "Which network runs the most trams and subways?",
            "intro": "The number of tram and subway trips scheduled each day: a simple measure of each network's "
            "service.",
            "method": "Number of tram and subway trips scheduled on a weekday, whatever their length.",
            "headers": ["City", "Network", "Trips per day"],
            "valueCol": 2,
            "rows": [
                {"city": city["slug"], "mode": None, "value": city["weekdayTrips"],
                 "cells": [city_link(city), esc(city["network"]), thousands(city["weekdayTrips"])]}
                for city in trips
            ],
            "podium": [(thousands(city["weekdayTrips"]), esc(city["network"]), esc(city["city"])) for city in trips[:3]],
            "highlight": (thousands(trips[0]["weekdayTrips"]), f'tram and subway trips per day in {esc(trips[0]["city"])}'),
            "position": lambda rank, total, city: (
                f'{ordinal(rank)} most extensive network out of {total}: {thousands(city["weekdayTrips"])} tram and '
                f'subway trips per day'
            ),
        },
    ]


def city_positions(cities: list[dict], slug: str, base: str) -> list[str]:
    """Where a city stands in each ranking (its best line for the line rankings), linked to its row."""
    data = load_rankings(cities)
    entry = next((city for city in data if city["slug"] == slug), None)
    if not entry:
        return []
    items = []
    for d in ranking_definitions(data, base):
        rows = d["rows"]
        query = ""
        if d.get("byMode"):
            # Compared with lines of the same mode (a tram cannot match a metro); rows are sorted, so the city's
            # first row is its best line.
            mode = next(row["mode"] for row in rows if row["city"] == slug)
            rows = [row for row in rows if row["mode"] == mode]
            query = f"?mode={mode}"
        ranks = competition_ranks([row["value"] for row in rows])
        index = next(i for i, row in enumerate(rows) if row["city"] == slug)
        if d.get("byMode"):
            name = rows[index]["line"]
            text = d["position"](ranks[index], len(rows), entry, name, entry["lines"][name])
        else:
            text = d["position"](ranks[index], len(rows), entry)
        items.append(f'<li><a href="{base}{RANKINGS_DIR}/{d["slug"]}/{query}#{slug}">{text}</a></li>')
    return items


def ranking_page(*, title: str, description: str, url: str, base: str, image_name: str, crumbs: list, cities: list, body: str) -> str:
    image = SITE / "og" / image_name
    image_url = f"{SITE_URL}og/{image_name}?v={short_hash(image)}" if image.exists() else SITE_URL + "og/home.jpg"
    graph = [
        {
            "@type": "Article",
            "headline": title,
            "description": description,
            "url": url,
            "inLanguage": "en",
            "author": {"@id": AUTHOR_URL + "#me"},
            "datePublished": date.today().isoformat(),
            "image": image_url,
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": name, "item": item} for i, (name, item) in enumerate(crumbs)
            ],
        },
        author_schema(),
    ]
    trail = " <span aria-hidden=\"true\">›</span> ".join(
        [f'<a href="{item.replace(SITE_URL, base) or "./"}">{esc(name)}</a>' for name, item in crumbs[:-1]]
        + [f'<span aria-current="page">{esc(crumbs[-1][0])}</span>']
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
{head(title=f"{title} · {SITE_NAME}", description=description, url=url, base=base, image=image_url, image_alt=title, published=date.today().isoformat(), graph=graph)}
    <link rel="stylesheet" href="{base}styles.css?v={short_hash(SITE / 'styles.css')}" />
  </head>
  <body>
{header(base)}
    <main class="page">
      <nav class="breadcrumb" aria-label="Breadcrumb">{trail}</nav>
{body}
    </main>
{footer(cities, base, "")}
    <script>{RANKING_SCRIPT}</script>
{ANALYTICS}
  </body>
</html>
"""


RANKING_SCRIPT = """
document.querySelectorAll("[data-filter]").forEach((button) => button.addEventListener("click", () => {
  const mode = button.dataset.filter;
  document.querySelectorAll("[data-filter]").forEach((b) => b.classList.toggle("active", b === button));
  document.querySelectorAll("#ranking tbody tr").forEach((row) => {
    row.hidden = mode && row.dataset.mode !== mode;
    const cell = row.querySelector(".rank");
    cell.textContent = mode ? row.dataset.modeRank : cell.dataset.rank;
  });
}));
const wanted = new URLSearchParams(location.search).get("mode");
if (wanted) document.querySelector(`[data-filter="${wanted}"]`)?.click();
if (location.hash) document.querySelector(location.hash)?.scrollIntoView();
document.querySelectorAll("[data-copy]").forEach((button) => button.addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(button.dataset.copy); button.textContent = "Link copied ✓"; } catch {}
}));
"""


def method_section(data: list[dict], base: str, method: str) -> str:
    dates = ", ".join(f'{esc(city["city"])} ({french_date(city["weekday"])})' for city in sorted(data, key=lambda c: c["city"]))
    paris = (
        " In Paris, these figures count the Île-de-France Mobilités metro and tram, excluding RER, Transilien, CDGVAL, "
        "Orlyval and the Montmartre funicular."
        if any(city["slug"] == "paris" for city in data)
        else ""
    )
    return f"""      <section class="section" aria-labelledby="method-title">
        <h2 id="method-title">Method</h2>
        <p>{esc(method)} These figures involve no trip computation: they are direct counts from the scheduled
        timetables published by each network (GTFS), for a Tuesday or Thursday during the school term. Only trams and
        subways are counted (no buses, busways, funiculars or cable cars); Rhônexpress and the OL Stadium shuttle
        are excluded in Lyon.{paris} Days used: {dates}.</p>
        <p>Sources and licenses: see the <a href="{base}mentions-legales/">legal notice</a>. Spotted an error?
        <a href="{GITHUB_URL}/issues">Report it on GitHub</a>.</p>
      </section>"""


def render_rankings(cities: list[dict]) -> dict[str, str]:
    """Pages of the rankings: the hub (/rankings/) and one page per ranking. Returns {path: html}."""
    data = load_rankings(cities)
    if not data:
        return {}
    hub_url = f"{SITE_URL}{RANKINGS_DIR}/"
    pages = {}

    hub_defs = ranking_definitions(data, "../")
    cards = "\n".join(
        f"""          <a class="ranking-card" href="./{d['slug']}/">
            <span class="ranking-card-question">{esc(d['question'])}</span>
            <ol>{"".join(f"<li><span>{MEDALS[i]}</span> <strong>{value}</strong> {label} · {sub}</li>" for i, (value, label, sub) in enumerate(d["podium"]))}</ol>
            <span class="ranking-card-link">See the full ranking →</span>
          </a>"""
        for d in hub_defs
    )
    highlights = "\n".join(
        f'          <div class="stat"><strong>{d["highlight"][0]}</strong><span>{d["highlight"][1]}</span></div>' for d in hub_defs
    )
    hub_description = (
        f"The most frequent subway, the busiest station, the longest line: trams and subways from "
        f"{len(data)} French cities compared using their official timetables."
    )
    pages[f"{RANKINGS_DIR}/index.html"] = ranking_page(
        title="French tram and subway rankings",
        description=hub_description,
        url=hub_url,
        base="../",
        image_name="rankings.jpg",
        crumbs=[(SITE_NAME, SITE_URL), ("Rankings", hub_url)],
        cities=cities,
        body=f"""      <section class="hero">
        <span class="chip">🏆 {len(data)} networks compared</span>
        <h1>Tram and subway rankings</h1>
        <p class="lede">Which subway runs most often, which station sees the most trains go by, which line takes the
        longest to ride, where can you get home latest on Saturday night? All figures come straight from the
        networks' official timetables.</p>
        <div class="stat-grid ranking-highlights">
{highlights}
        </div>
      </section>
      <section aria-label="Rankings">
        <div class="ranking-cards">
{cards}
        </div>
      </section>
{method_section(data, "../", "Each ranking details its own measurement.")}""",
    )

    defs = ranking_definitions(data, "../../")
    for d in defs:
        url = f"{hub_url}{d['slug']}/"
        podium = "\n".join(
            f'          <div class="podium-step step-{i + 1}"><span class="medal">{MEDALS[i]}</span><strong>{value}</strong>'
            f"<span>{label}</span><small>{sub}</small></div>"
            for i, (value, label, sub) in enumerate(d["podium"])
        )
        headers = "".join(f'<th scope="col">{esc(h)}</th>' for h in ["#", *d["headers"]])
        rows = d["rows"]
        ranks = competition_ranks([row["value"] for row in rows])
        mode_ranks = {}
        for mode in {row["mode"] for row in rows}:
            subset = [i for i, row in enumerate(rows) if row["mode"] == mode]
            for i, rank in zip(subset, competition_ranks([rows[i]["value"] for i in subset])):
                mode_ranks[i] = rank
        top = max(row["value"] for row in rows)
        seen = set()
        body_rows = []
        for i, row in enumerate(rows):
            cells = list(row["cells"])
            col = d["valueCol"]
            cells[col] = f'<span class="bar" style="width:{100 * row["value"] / top:.0f}%"></span><span class="bar-value">{cells[col]}</span>'
            anchor = f' id="{row["city"]}"' if row["city"] not in seen else ""
            seen.add(row["city"])
            mode = f' data-mode="{row["mode"]}" data-mode-rank="{mode_ranks[i]}"' if d.get("byMode") else ""
            body_rows.append(
                f'            <tr{anchor}{mode}><td class="rank" data-rank="{ranks[i]}">{ranks[i]}</td>'
                + "".join(f'<td{" class=\"bar-cell\"" if j == col else ""}>{cell}</td>' for j, cell in enumerate(cells))
                + "</tr>"
            )
        rows = "\n".join(body_rows)
        filters = (
            """        <div class="mode-filter" role="group" aria-label="Filter by mode">
          <button type="button" class="chip active" data-filter="">All</button>
          <button type="button" class="chip" data-filter="metro">Subway</button>
          <button type="button" class="chip" data-filter="tram">Tram</button>
        </div>
"""
            if d.get("byMode")
            else ""
        )
        page_url = f"{hub_url}{d['slug']}/"
        share_text = quote(f"{d['question']} French tram and subway rankings")
        share = f"""        <p class="share">Share:
          <a href="https://www.linkedin.com/sharing/share-offsite/?url={quote(page_url)}" rel="noopener">LinkedIn</a> ·
          <a href="https://x.com/intent/post?text={share_text}&amp;url={quote(page_url)}" rel="noopener">X</a> ·
          <a href="https://bsky.app/intent/compose?text={share_text}%20{quote(page_url)}" rel="noopener">Bluesky</a> ·
          <button type="button" class="link-button" data-copy="{page_url}">Copy link</button>
        </p>"""
        others = " · ".join(f'<a href="../{o["slug"]}/">{esc(o["short"])}</a>' for o in defs if o["slug"] != d["slug"])
        pages[f"{RANKINGS_DIR}/{d['slug']}/index.html"] = ranking_page(
            title=d["title"],
            description=f'{d["question"]} {d["intro"]}',
            url=url,
            base="../../",
            image_name=f"ranking-{d['slug']}.jpg",
            crumbs=[(SITE_NAME, SITE_URL), ("Rankings", hub_url), (d["short"], url)],
            cities=cities,
            body=f"""      <section class="hero">
        <span class="chip">🏆 Ranking · {len(data)} networks</span>
        <h1>{esc(d["question"])}</h1>
        <p class="lede">{esc(d["intro"])}</p>
        <div class="podium">
{podium}
        </div>
      </section>
      <section class="section" aria-labelledby="table-title">
        <h2 id="table-title">{esc(d["title"])}</h2>
        <p>{esc(d["method"])}</p>
{filters}        <div class="table-scroll">
        <table class="lines-table ranking-table" id="ranking">
          <thead><tr>{headers}</tr></thead>
          <tbody>
{rows}
          </tbody>
        </table>
        </div>
{share}
        <p class="section-link">Other rankings: {others} · <a href="../">all rankings</a></p>
      </section>
{method_section(data, "../../", d["method"])}""",
        )
    return pages


def render_404(cities: list[dict]) -> str:
    links = "\n".join(f'          <a class="chip" href="/{city["path"]}">{esc(city["name"])}</a>' for city in cities)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Page not found · {SITE_NAME}</title>
    <meta name="robots" content="noindex" />
    <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
    <link rel="stylesheet" href="https://fonts.bunny.net/css?family=inter:400,500,600,700,800" />
    <link rel="stylesheet" href="/styles.css?v={short_hash(SITE / 'styles.css')}" />
  </head>
  <body>
{header('/')}
    <main class="page">
      <section class="hero">
        <h1>End of the line!</h1>
        <p class="lede">This page doesn't exist. Pick a city to get back on track.</p>
        <nav class="city-switch" aria-label="Cities">
{links}
        </nav>
      </section>
    </main>
  </body>
</html>
"""


def main() -> None:
    cities = load_built_cities()
    city_template = Template((ROOT / "templates" / "city.html").read_text(encoding="utf-8"))
    for city in cities:
        page = SITE / city["path"] / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(render_city(city_template, cities, city), encoding="utf-8")
        print(f"Wrote {page.relative_to(ROOT)}")

    home_template = Template((ROOT / "templates" / "home.html").read_text(encoding="utf-8"))
    (SITE / "index.html").write_text(render_home(home_template, cities), encoding="utf-8")
    (SITE / "404.html").write_text(render_404(cities), encoding="utf-8")
    rankings = render_rankings(cities)
    for relative, html_page in rankings.items():
        (SITE / relative).parent.mkdir(parents=True, exist_ok=True)
        (SITE / relative).write_text(html_page, encoding="utf-8")
    (SITE / "mentions-legales").mkdir(exist_ok=True)
    (SITE / "mentions-legales" / "index.html").write_text(render_legal(cities), encoding="utf-8")
    write_sources_readme(cities)
    print("Wrote site/index.html, site/404.html")

    today = date.today().isoformat()
    urls = [f"  <url><loc>{SITE_URL}</loc><lastmod>{today}</lastmod></url>"]
    urls += [f"  <url><loc>{SITE_URL}{relative.removesuffix('index.html')}</loc><lastmod>{today}</lastmod></url>" for relative in rankings]
    urls += [
        f"  <url><loc>{SITE_URL}{city['path']}</loc><lastmod>{city['sources']['builtAt'][:10]}</lastmod></url>" for city in cities
    ]
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n",
        encoding="utf-8",
    )
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
    print("Wrote site/sitemap.xml, site/robots.txt")


if __name__ == "__main__":
    main()
