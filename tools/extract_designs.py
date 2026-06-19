"""Extract the design SVGs + critique verdicts from the design workflow output.

Writes each concept SVG to brand/designs/<id>.svg (unescaped) and prints a
one-line verdict summary. The SVGs are concept drafts; final print art is refit
per the art-director critiques (typography must not rely on a font being present).
"""
import html
import json
import os
import re
import sys

OUT = sys.argv[1]
DEST = "brand/designs"
os.makedirs(DEST, exist_ok=True)

with open(OUT) as f:
    data = json.load(f)
designs = (data.get("designs")
           or data.get("result", {}).get("designs")
           or [])

print(f"{len(designs)} designs\n")
for d in designs:
    svg = html.unescape(d.get("svg", "") or "")
    did = d.get("design_id", "design")
    path = os.path.join(DEST, f"{did}.svg")
    with open(path, "w") as f:
        f.write(svg if svg.strip().endswith("svg>") else svg)
    crit = d.get("critique") or {}
    valid = bool(re.search(r"<svg[\s>]", svg)) and "viewBox" in svg
    print(f"- {did:32s} {d.get('product',''):4s} "
          f"verdict={crit.get('verdict','?'):6s} svg_ok={valid} "
          f"bytes={len(svg)}")
