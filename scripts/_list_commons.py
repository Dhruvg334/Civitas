import json, glob, os

for f in sorted(glob.glob(r"C:\Users\NITUAG~1\AppData\Local\Temp\opencode\commons\*.json")):
    d = json.load(open(f, encoding="utf-8-sig"))
    print("===", os.path.basename(f))
    for p in d.get("query", {}).get("pages", {}).values():
        ii = p.get("imageinfo", [{}])[0]
        w, h = ii.get("width"), ii.get("height")
        if w and h and w >= 480 and h >= 300 and ii.get("mime") == "image/jpeg":
            print("  ", p["title"][:72], "|", w, "x", h, "|", ii.get("thumburl", "")[:110])

