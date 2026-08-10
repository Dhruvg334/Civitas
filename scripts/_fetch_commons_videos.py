import json, urllib.request, urllib.parse

QUERIES = [
    "water leak filetype:video",
    "street flood filetype:video",
    "pothole filetype:video",
    "fallen tree storm filetype:video",
    "garbage street filetype:video",
    "broken streetlight filetype:video",
]

seen = set()
for q in QUERIES:
    params = {
        "action": "query", "generator": "search",
        "gsrsearch": q, "gsrlimit": "8", "gsrnamespace": "6",
        "prop": "imageinfo", "iiprop": "url|mime|size",
        "format": "json",
    }
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "CivitasDevProbe/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            d = json.load(r)
    except Exception as exc:
        print("FAIL", q, exc)
        continue
    print("=== ", q)
    for p in d.get("query", {}).get("pages", {}).values():
        ii = p.get("imageinfo", [{}])[0]
        size = ii.get("size", 0)
        mime = ii.get("mime", "")
        if "video" not in mime:
            continue
        key = p["title"]
        if key in seen:
            continue
        seen.add(key)
        print(f"  {key[:80]} | {mime} | {size//1024} KB | {ii.get('url','')[:100]}")
