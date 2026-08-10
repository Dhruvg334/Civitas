import json, urllib.request, urllib.parse

TITLES = [
    # videos picked for the civic test set
    "File:Flood on the street.webm",
    "File:Zhengzhou streets during the flood 2021-07-20.webm",
    "File:Leaking roof.webm",
    "File:Water Dripping into a Bucket in a Derelict Apartment in Canada.webm",
    "File:Teto de gesso com infiltração.webm",
    # out-of-domain image controls (must NOT be classified as civic incidents)
    "File:Zugspitze, Zuspitzkamm, Ehrwalder Becken und Wettersteingebirge, 2021-03-10.jpg",
    "File:Cat 2007-04-29.jpg",
]

params = {
    "action": "query", "titles": "|".join(TITLES),
    "prop": "imageinfo", "iiprop": "url|mime|size|extmetadata",
    "format": "json",
}
url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={"User-Agent": "CivitasDevProbe/0.1"})
with urllib.request.urlopen(req, timeout=40) as r:
    d = json.load(r)
for p in d.get("query", {}).get("pages", {}).values():
    ii = p.get("imageinfo", [{}])[0]
    meta = ii.get("extmetadata", {})
    print(json.dumps({
        "title": p["title"],
        "license": meta.get("LicenseShortName", {}).get("value", "?"),
        "mime": ii.get("mime"),
        "size": ii.get("size", 0),
        "url": ii.get("url"),
    }, ensure_ascii=False))
