import json
import sys
import urllib.parse
import urllib.request

PICKS = {
    "pothole_road_damage": [
        "File:A pothole in Dilova Street in Kyiv.jpg",
        "File:Potholes in Bengaluru road.jpg",
        "File:Pothole in Villeray, Montréal.jpg",
        "File:Pothole on Huntington Creek Road.JPG",
    ],
    "water_leakage": [
        "File:2020 White Plains Water Main Break 20200810 (1).jpg",
        "File:Peacock Street water main break 986.jpg",
        "File:Water Main Break (17099358765).jpg",
        "File:Burst water main (geograph 2646387).jpg",
    ],
    "garbage_overflow": [
        "File:Garbage Overflow 1 2023-12-29.jpeg",
        "File:Overflowing Hamburg street garbage bin.jpg",
        "File:Overflowing garbage bin in Helsinki, Finland, 2019.jpg",
    ],
    "broken_streetlight": [
        "File:Street light 07092012..jpg",
        "File:Street light, Amsterdam.jpg",
        "File:Barcelona - Farola Avenida Gaudi.jpg",
    ],
    "fallen_tree": [
        "File:Fallen Tree in Dormer Place, Leamington Spa (1).jpg",
        "File:Fallen tree - 1C.jpg",
        "File:Fallen tree in greece.jpg",
    ],
}

titles = [t for ts in PICKS.values() for t in ts]
params = {
    "action": "query",
    "titles": "|".join(titles),
    "prop": "imageinfo",
    "iiprop": "url|mime|size|extmetadata",
    "iiurlwidth": "960",
    "format": "json",
}
url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={"User-Agent": "CivitasDevProbe/0.1"})
try:
    with urllib.request.urlopen(req, timeout=40) as r:
        d = json.load(r)
except Exception as exc:
    print("NETWORK-FAIL:", exc)
    sys.exit(1)

for p in d.get("query", {}).get("pages", {}).values():
    ii = p.get("imageinfo", [{}])[0]
    meta = ii.get("extmetadata", {})
    lic = meta.get("LicenseShortName", {}).get("value", "?")
    artist = (meta.get("Artist", {}).get("value", "?") or "?")[:40]
    print(json.dumps({
        "title": p["title"],
        "license": lic,
        "artist": artist,
        "mime": ii.get("mime"),
        "w": ii.get("width"), "h": ii.get("height"),
        "url": ii.get("url"),
        "thumburl": ii.get("thumburl"),
    }, ensure_ascii=False))
