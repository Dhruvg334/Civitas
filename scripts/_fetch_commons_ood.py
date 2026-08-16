import json
import urllib.parse
import urllib.request

for query in ["mountain landscape filetype:bitmap", "cat filetype:bitmap"]:
    params = {
        "action": "query", "generator": "search",
        "gsrsearch": query, "gsrlimit": "5", "gsrnamespace": "6",
        "prop": "imageinfo", "iiprop": "url|mime|size|extmetadata",
        "iiurlwidth": "960", "format": "json",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "CivitasDevProbe/0.1"})
    with urllib.request.urlopen(req, timeout=40) as r:
        d = json.load(r)
    print("===", query)
    for p in d.get("query", {}).get("pages", {}).values():
        ii = p.get("imageinfo", [{}])[0]
        if ii.get("mime") != "image/jpeg":
            continue
        meta = ii.get("extmetadata", {})
        print(json.dumps({
            "title": p["title"],
            "license": meta.get("LicenseShortName", {}).get("value", "?"),
            "url": ii.get("thumburl") or ii.get("url"),
        }, ensure_ascii=False))
