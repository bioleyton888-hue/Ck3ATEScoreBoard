"""
Render the ATE Scoreboard's historical-house coats of arms to image files.

Reads ATE's own CoA definitions (pattern + colored emblems + named colours),
composites them the way CK3 does, and writes one PNG per house.

Colour model (verified empirically against the game's textures):
    start from color1, lerp toward color2 by the G channel,
    then lerp toward color3 by the B channel; alpha gives the shape.
Confirmed by rendering ce_sun.dds and checking it produces a recognisable sun.

Usage:  python scripts/render_coas.py [--size 128] [--out gfx/interface/ate_scoreboard]
"""

import argparse
import colorsys
import re
from pathlib import Path

import numpy as np
from PIL import Image

CK3 = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game")
ATE = Path(r"C:\Program Files (x86)\Steam\steamapps\workshop\content\1158310\3192256710")

PATTERN_DIRS = [CK3 / "gfx/coat_of_arms/patterns", ATE / "gfx/coat_of_arms/patterns"]
EMBLEM_DIRS = [
    CK3 / "gfx/coat_of_arms/colored_emblems",
    ATE / "gfx/coat_of_arms/colored_emblems",
    CK3 / "gfx/coat_of_arms/textured_emblems",
    ATE / "gfx/coat_of_arms/textured_emblems",
]
COLOR_FILES = [CK3 / "common/named_colors", ATE / "common/named_colors"]
# Our own Neomoor mod - home of House Ramsesovich. Searched first so our
# definitions win over anything with a colliding key.
NEO = Path(r"C:\Users\ni_c_\OneDrive\Documentos\proyectos\AteNeomoorCulture")

COA_DIRS = [NEO / "common/coat_of_arms/coat_of_arms",
            ATE / "common/coat_of_arms/coat_of_arms", CK3 / "common/coat_of_arms/coat_of_arms",
            ATE / "common/coat_of_arms/title_coat_of_arms", CK3 / "common/coat_of_arms/title_coat_of_arms"]

# The 15 scoreboard houses, in ladder order, mapped to their CoA definition keys.
#
# IMPORTANT: ATE does not key every dynasty by a `dynn_<name>` string. Many are
# keyed by NUMERIC id, with `dynn_X` living in the dynasty's `name = "..."` field
# as a loc key. House Clinton is `3802`, not `dynn_Clinton`. Searching by the
# CK2-era house name alone therefore misses them - resolve via the dynasty's
# name field (see scripts note below) rather than assuming the key.
#
# Three houses have no dynasty CoA of their own, so we fall back to the arms of
# the realm they ruled - defensible heraldry for a scoreboard of great houses:
#   Jacaranda -> k_mexico       (Kings of Mexico)
#   Nokona    -> k_comancheria  (Kings of Comancheria)
#   Yoder     -> k_dutchland    (Deitscherei; CK3's Deitscherei is ruled by
#                                House Lengacher, so Yoder has no arms of its own)
HOUSES = [
    ("talanque",   "house_california_talanque"),
    ("jacaranda",  "k_mexico"),
    ("royall",     "dynn_hcc_royall"),
    ("clinton",    "3802"),
    ("sully",      "dynn_centroamerica_sully"),
    ("abbas",      "dynn_california_abbas"),
    ("tlgunghung", "dynn_cascadia_tlgunghung"),
    ("nokona",     "k_comancheria"),
    ("mahonic",    "dynn_noreast_mahonic"),
    ("castel",     "dynn_canada_castel"),
    ("pitchstone", "dynn_gv_pitchstone"),
    ("yoder",      "k_dutchland"),
    ("tagotoka",   "dynn_california_tagotoka"),
    ("soady",      "dynn_canada_soady"),
    ("avondale",   "dynn_gv_avondale"),
    # Our own house, from the Neomoor mod. Sits below the CK2 board at a flat 500.
    ("ramsesovich", "dynn_ramsesovich"),
]


# --------------------------------------------------------------------------- colours

def load_named_colors():
    """Parse common/named_colors/*.txt into {name: (r, g, b)} 0-255."""
    colors = {}
    pat = re.compile(
        r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(hsv360|hsv|rgb)?\s*\{([^}]*)\}", re.I
    )
    for d in COLOR_FILES:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.txt")):
            text = f.read_text(encoding="utf-8-sig", errors="replace")
            for name, kind, body in pat.findall(text):
                nums = [float(x) for x in re.findall(r"-?\d*\.?\d+", body)]
                if len(nums) < 3:
                    continue
                a, b, c = nums[:3]
                kind = (kind or "rgb").lower()
                if kind == "hsv":
                    r, g, bl = colorsys.hsv_to_rgb(a, b, c)
                    rgb = (r * 255, g * 255, bl * 255)
                elif kind == "hsv360":
                    r, g, bl = colorsys.hsv_to_rgb(a / 360.0, b / 100.0, c / 100.0)
                    rgb = (r * 255, g * 255, bl * 255)
                else:
                    rgb = (a, b, c) if max(a, b, c) > 1.0 else (a * 255, b * 255, c * 255)
                colors.setdefault(name, tuple(float(v) for v in rgb))
    return colors


def resolve_color(token, named, default=(128, 128, 128)):
    """Resolve a colour token - a name, or an inline hsv{}/rgb{} form."""
    if token is None:
        return np.array(default, float)
    token = token.strip().strip('"')
    m = re.match(r"(hsv360|hsv|rgb)\s*\{([^}]*)\}", token, re.I)
    if m:
        kind, body = m.group(1).lower(), m.group(2)
        nums = [float(x) for x in re.findall(r"-?\d*\.?\d+", body)][:3]
        if len(nums) == 3:
            if kind == "hsv":
                r, g, b = colorsys.hsv_to_rgb(*nums)
                return np.array([r * 255, g * 255, b * 255], float)
            if kind == "hsv360":
                r, g, b = colorsys.hsv_to_rgb(nums[0] / 360, nums[1] / 100, nums[2] / 100)
                return np.array([r * 255, g * 255, b * 255], float)
            return np.array(nums if max(nums) > 1 else [n * 255 for n in nums], float)
    return np.array(named.get(token, default), float)


# --------------------------------------------------------------------------- parsing

def find_block(key):
    """Return the raw text of `key = { ... }` from the CoA files, brace-matched."""
    needle = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(key) + r"\s*=\s*\{")
    for d in COA_DIRS:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.txt")):
            text = f.read_text(encoding="utf-8-sig", errors="replace")
            m = needle.search(text)
            if not m:
                continue
            i = text.index("{", m.start())
            depth = 0
            for j in range(i, len(text)):
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                    if depth == 0:
                        return text[i + 1 : j], f.name
    return None, None


def split_subblocks(body, kind):
    """Yield the bodies of every `kind = { ... }` at this level."""
    out = []
    for m in re.finditer(re.escape(kind) + r"\s*=\s*\{", body):
        i = body.index("{", m.start())
        depth = 0
        for j in range(i, len(body)):
            if body[j] == "{":
                depth += 1
            elif body[j] == "}":
                depth -= 1
                if depth == 0:
                    out.append(body[i + 1 : j])
                    break
    return out


def strip_subblocks(body, kinds):
    """Remove nested blocks so top-level scalar lookups don't match inside them."""
    for kind in kinds:
        while True:
            m = re.search(re.escape(kind) + r"\s*=\s*\{", body)
            if not m:
                break
            i = body.index("{", m.start())
            depth = 0
            for j in range(i, len(body)):
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                    if depth == 0:
                        body = body[: m.start()] + body[j + 1 :]
                        break
            else:
                break
    return body


def scalar(body, key):
    """Fetch `key = value`, where value may be quoted, a name, or an inline colour."""
    m = re.search(
        re.escape(key) + r"\s*=\s*(\"[^\"]*\"|(?:hsv360|hsv|rgb)\s*\{[^}]*\}|[^\s{}]+)",
        body, re.I,
    )
    return m.group(1).strip() if m else None


def numbers(body, key, count):
    m = re.search(re.escape(key) + r"\s*=\s*\{([^}]*)\}", body)
    if not m:
        return None
    nums = [float(x) for x in re.findall(r"-?\d*\.?\d+", m.group(1))]
    return nums[:count] if len(nums) >= count else None


def parse_coa(key):
    body, source = find_block(key)
    if body is None:
        return None
    emblems = []
    for kind in ("colored_emblem", "textured_emblem"):
        for eb in split_subblocks(body, kind):
            instances = split_subblocks(eb, "instance") or [""]
            head = strip_subblocks(eb, ["instance"])
            for inst in instances:
                emblems.append({
                    "kind": kind,
                    "texture": (scalar(head, "texture") or "").strip('"'),
                    "colors": [scalar(head, f"color{i}") for i in (1, 2, 3)],
                    "position": numbers(inst, "position", 2) or [0.5, 0.5],
                    "scale": numbers(inst, "scale", 2) or [1.0, 1.0],
                    "depth": (lambda v: float(v) if v else 0.0)(scalar(inst, "depth")),
                })
    top = strip_subblocks(body, ["colored_emblem", "textured_emblem", "instance"])
    return {
        "source": source,
        "pattern": (scalar(top, "pattern") or "").strip('"'),
        "colors": [scalar(top, f"color{i}") for i in (1, 2, 3)],
        # CK3 draws higher depth FURTHER BACK - verified on dynn_california_tagotoka,
        # whose depth-17 full-canvas block otherwise covers the entire shield.
        "emblems": sorted(emblems, key=lambda e: -e["depth"]),
    }


# --------------------------------------------------------------------------- rendering

def locate(name, dirs):
    for d in dirs:
        p = d / name
        if p.is_file():
            return p
    return None


def recolor_pattern(img, c1, c2, c3):
    """
    Patterns encode colour slots in RGB: R is the c1 field, G overrides with c2,
    B overrides with c3. Verified against pattern_vertical_split_01.dds, which
    contains exactly [255,0,0] (colour 1) and [255,255,0] (colour 2).
    """
    arr = np.array(img.convert("RGBA")).astype(float)
    g = arr[..., 1:2] / 255.0
    b = arr[..., 2:3] / 255.0
    rgb = np.broadcast_to(c1, arr.shape[:2] + (3,)).copy()
    rgb = rgb * (1 - g) + c2 * g
    rgb = rgb * (1 - b) + c3 * b
    return np.dstack([rgb, arr[..., 3:4]])


def recolor_emblem(img, c1, c2, c3):
    """
    Emblems are alpha silhouettes, NOT RGB-masked like patterns. Every emblem
    checked (ce_sun, ce_antlers_attire, ce_block_02, ce_circle_mask,
    ce_buddhist_moon) reads R~0 G~0 B~128 on opaque pixels - that B~128 is a
    neutral baseline, not a colour-3 mask. Treating it as a mask blended every
    emblem halfway to grey, which is what washed out the first render pass.

    So: shape comes from alpha, colour from c1, with G blending toward c2 for
    the two-tone emblems that use it. B is ignored.
    """
    arr = np.array(img.convert("RGBA")).astype(float)
    g = arr[..., 1:2] / 255.0
    rgb = np.broadcast_to(c1, arr.shape[:2] + (3,)).copy()
    rgb = rgb * (1 - g) + c2 * g
    return np.dstack([rgb, arr[..., 3:4]])


def render(coa, named, size):
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    pc = [resolve_color(c, named, d) for c, d in
          zip(coa["colors"], [(200, 200, 200), (60, 60, 60), (140, 140, 140)])]
    ppath = locate(coa["pattern"], PATTERN_DIRS) if coa["pattern"] else None
    if ppath:
        arr = recolor_pattern(Image.open(ppath), *pc)
        canvas.alpha_composite(
            Image.fromarray(arr.astype(np.uint8), "RGBA").resize((size, size), Image.LANCZOS)
        )
    else:
        canvas.paste(tuple(int(v) for v in pc[0]) + (255,), (0, 0, size, size))

    for em in coa["emblems"]:
        epath = locate(em["texture"], EMBLEM_DIRS)
        if not epath:
            print(f"      ! missing emblem texture: {em['texture']}")
            continue
        src = Image.open(epath)
        if em["kind"] == "colored_emblem":
            ec = [resolve_color(c, named, d) for c, d in
                  zip(em["colors"], [(230, 230, 230), (40, 40, 40), (140, 140, 140)])]
            src = Image.fromarray(recolor_emblem(src, *ec).astype(np.uint8), "RGBA")
        else:
            src = src.convert("RGBA")

        sx, sy = em["scale"]
        w = max(1, int(round(abs(sx) * size)))
        h = max(1, int(round(abs(sy) * size)))
        src = src.resize((w, h), Image.LANCZOS)
        if sx < 0:
            src = src.transpose(Image.FLIP_LEFT_RIGHT)
        if sy < 0:
            src = src.transpose(Image.FLIP_TOP_BOTTOM)

        px, py = em["position"]
        layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        layer.paste(src, (int(round(px * size - w / 2)), int(round(py * size - h / 2))), src)
        canvas.alpha_composite(layer)

    return canvas


def placeholder(size):
    """Neutral shield for houses whose CoA CK3 generates at runtime."""
    img = Image.new("RGBA", (size, size), (72, 68, 62, 255))
    a = np.array(img)
    yy, xx = np.mgrid[0:size, 0:size]
    edge = (xx < 2) | (yy < 2) | (xx >= size - 2) | (yy >= size - 2)
    a[edge] = (140, 128, 96, 255)
    return Image.fromarray(a, "RGBA")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=128)
    ap.add_argument("--out", default="gfx/interface/ate_scoreboard")
    args = ap.parse_args()

    out = Path(__file__).resolve().parent.parent / args.out
    out.mkdir(parents=True, exist_ok=True)

    named = load_named_colors()
    print(f"loaded {len(named)} named colours\n")

    ok = missing = failed = 0
    for slug, key in HOUSES:
        dest = out / f"coa_{slug}.png"
        if key is None:
            placeholder(args.size).save(dest)
            print(f"  {slug:<12} placeholder (no authored CoA in ATE)")
            missing += 1
            continue
        coa = parse_coa(key)
        if coa is None:
            placeholder(args.size).save(dest)
            print(f"  {slug:<12} FAILED - key '{key}' not found")
            failed += 1
            continue
        render(coa, named, args.size).save(dest)
        print(f"  {slug:<12} {key}  ({coa['source']}, "
              f"pattern={coa['pattern'] or 'none'}, {len(coa['emblems'])} emblem(s))")
        ok += 1

    print(f"\n{ok} rendered, {missing} placeholder, {failed} failed -> {out}")


if __name__ == "__main__":
    main()
