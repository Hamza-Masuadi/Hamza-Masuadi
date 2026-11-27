"""Builds assets/profile.svg: the whole profile as one animated synthwave + glitch scene.

Live stats cards are downloaded and embedded as data URIs, because an SVG shown
through <img> on GitHub may not load anything from the network itself.
A GitHub Action re-runs this daily so the numbers stay current.

Run:  python3 scripts/make_art.py
"""
import base64
import os
import random
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "profile.svg")

# ------------------------------------------------------------------ content
USER = "Hamza-Masuadi"
NAME = "HAMZA MASUADI"
TAGLINE = "SOFTWARE ENGINEER"
TYPING = ["> software engineer", "> shipping web & mobile apps end to end", "> from database to app store"]
ABOUT = [
    "Building a multi-vendor marketplace: customer, seller,",
    "  courier and admin apps on one backend",
    "Shipping cross-platform mobile apps and the web apps next to them",
    "Owning the whole thing: APIs, databases, real-time, deploys",
    "Into AI coding tools and agent skills",
]
SIGNOFF = "THANKS FOR VISITING ✦"

# ------------------------------------------------------------------ palette
PINK, CYAN, YELLOW, TEXT = "#ff2bd6", "#00f0ff", "#ffe86b", "#e9dcff"
BG, BG2 = "#0d0221", "#1a0433"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

Q = "hide_border=true&disable_animations=true&bg_color=00000000&background=00000000"
CARDS = {
    "stats": f"https://github-readme-stats.vercel.app/api?username={USER}&show_icons=true&hide_rank=true&{Q}"
             f"&title_color=ff2bd6&icon_color=00f0ff&text_color=e9dcff&ring_color=ff2bd6",
    "streak": f"https://streak-stats.demolab.com?user={USER}&{Q}&ring=ff2bd6&fire=ffe86b"
              f"&currStreakNum=ffffff&sideNums=ffffff&currStreakLabel=00f0ff&sideLabels=e9dcff&dates=9d8cc4&stroke=3a1466",
}

W = 1200
rnd = random.Random(1984)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-art-builder"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    if b"<svg" not in data[:2000]:
        raise RuntimeError(f"not an SVG: {url}")
    # Cards that animate in start invisible; inside another image that animation may never
    # play, so freeze them in their finished state.
    text = data.decode("utf-8", "replace")
    text = re.sub(r"animation\s*:[^;'\"}]*;?", "", text)
    text = text.replace("stroke-dashoffset: 5000", "stroke-dashoffset: 0")
    text = re.sub(r"opacity\s*:\s*0\s*;", "opacity: 1;", text)  # elements that were waiting to fade in
    data = text.encode()
    return "data:image/svg+xml;base64," + base64.b64encode(data).decode()


def contributions():
    """Reads the public contribution calendar: {(row, col): (date, level, count)}."""
    url = f"https://github.com/users/{USER}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "profile-art-builder"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", "replace")
    cells = {}
    for m in re.finditer(r'data-date="([0-9-]+)" id="contribution-day-component-(\d+)-(\d+)" data-level="(\d)"', html):
        date, row, col, lvl = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        cells[(row, col)] = [date, lvl, 0]
    for m in re.finditer(r'for="contribution-day-component-(\d+)-(\d+)"[^>]*>([^<]*)', html):
        c = re.match(r"\s*([\d,]+) contribution", m.group(3))
        key = (int(m.group(1)), int(m.group(2)))
        if c and key in cells:
            cells[key][2] = int(c.group(1).replace(",", ""))
    if len(cells) < 300:
        raise RuntimeError("could not read the contribution calendar")
    m = re.search(r"([\d,]+)\s+contributions\s+in the last year", html)
    total = int(m.group(1).replace(",", "")) if m else sum(v[2] for v in cells.values())
    return cells, total


LEVEL = ["#1f0c3d", "#5c1b8a", "#a125b8", "#e62ccf", "#ff6ae6"]   # tops, quiet -> busy
SIDE = ["#170930", "#3d1260", "#6c1880", "#9c1d8c", "#b8329f"]    # front faces


def city_grid(cells, x0, front_y, width):
    """The contribution grid tilted in 3D: one block per day, busier days stand taller
    and the blocks rise out of the floor in a wave when the image loads."""
    MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    HGT = [0, 7, 16, 28, 44]
    depth, skew = 13, 7                  # each row further back sits higher and to the right
    cols = max(c for _, c in cells) + 1
    gw = (width - 6 * skew) / cols
    cw, cd = gw - 3.5, depth - 3
    slant = skew * cd / depth
    out, clips = [], []
    for r in range(7):                   # back row first so front rows overlap it
        ground = front_y - (6 - r) * depth
        clips.append(f'<clipPath id="crow{r}"><rect x="0" y="0" width="{W}" height="{ground + .5}"/></clipPath>')
        row = []
        for c in range(cols):
            if (r, c) not in cells:
                continue
            lvl = cells[(r, c)][1]
            x, h = x0 + c * gw + (6 - r) * skew, HGT[lvl]
            top = (f"{x:.1f},{ground - h - cd:.1f} {x + cw:.1f},{ground - h - cd:.1f} "
                   f"{x + cw - slant:.1f},{ground - h:.1f} {x - slant:.1f},{ground - h:.1f}")
            front = (f'<rect x="{x - slant:.1f}" y="{ground - h:.1f}" width="{cw:.1f}" height="{h}" fill="{SIDE[lvl]}"/>'
                     if h else "")
            glow = ' filter="url(#softglow)"' if lvl == 4 else ""
            flick = ""
            if lvl >= 3 and rnd.random() < .25:   # some busy towers glow on and off like windows
                flick = (f'<animate attributeName="opacity" values="1;.45;1" dur="{rnd.uniform(1.8, 3.5):.1f}s" '
                         f'begin="-{rnd.uniform(0, 3):.1f}s" repeatCount="indefinite"/>')
            body = (f'{front}<polygon points="{top}" fill="{LEVEL[lvl]}" stroke="#ff9de9" '
                    f'stroke-opacity="{.15 + lvl * .15:.2f}" stroke-width=".8"{glow}>{flick}</polygon>')
            if h:
                begin = 0.3 + c * 0.045 + (6 - r) * 0.03
                body = (f'<g transform="translate(0 {h})">{body}<animateTransform attributeName="transform" '
                        f'type="translate" values="0 {h};0 -3;0 0" keyTimes="0;.75;1" dur=".7s" '
                        f'begin="{begin:.2f}s" fill="freeze"/></g>')
            row.append(body)
        out.append(f'<g clip-path="url(#crow{r})">{"".join(row)}</g>')

    # month labels sit over the back row, so they follow its offset
    labels, last, last_col = [], None, -9
    label_y = front_y - 6 * depth - 62
    for c in range(cols):
        day = next((cells[(r, c)] for r in range(7) if (r, c) in cells), None)
        m = int(day[0][5:7])
        if m != last:
            if c - last_col >= 3 and c < cols - 2:
                labels.append(f'<text x="{x0 + c * gw + 6 * skew:.1f}" y="{label_y}" font-family="{MONO}" '
                              f'font-size="13" fill="#9d8cc4">{MONTHS[m - 1]}</text>')
                last_col = c
            last = m
    floor = (f'<line x1="{x0 - 10}" y1="{front_y + 1}" x2="{x0 + width + 10}" y2="{front_y + 1}" stroke="#ff9de9" '
             f'stroke-width="1.5" stroke-opacity=".6" filter="url(#softglow)"/>')
    return "".join(clips) + "".join(labels) + "".join(out) + floor


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def perspective_grid(top, bottom, n=9, dur=3.0):
    v = "".join(f'<line x1="{600 + (x - 600) * 0.04:.1f}" y1="{top}" x2="{x}" y2="{bottom}"/>'
                for x in range(-1800, W + 1801, 120))
    hl = []
    for i in range(n):
        b = f'dur="{dur}s" begin="-{i * dur / n:.3f}s" repeatCount="indefinite"'
        ease = 'calcMode="spline" keyTimes="0;1" keySplines=".55 0 1 .45"'
        hl.append(f'<line x1="0" x2="{W}" y1="{top}" y2="{top}">'
                  f'<animate attributeName="y1" values="{top};{bottom + 4}" {ease} {b}/>'
                  f'<animate attributeName="y2" values="{top};{bottom + 4}" {ease} {b}/>'
                  f'<animate attributeName="stroke-opacity" values=".1;1" {b}/></line>')
    return (f'<g stroke="url(#gridfade)" stroke-width="1.6" filter="url(#softglow)">{v}</g>'
            f'<g stroke="{PINK}" stroke-width="1.6" filter="url(#softglow)">{"".join(hl)}</g>')


def stars(y0, y1, n):
    return "".join(
        f'<circle cx="{rnd.randint(0, W)}" cy="{rnd.randint(y0, y1)}" r="{rnd.choice([.8, 1, 1.3])}" fill="#fff">'
        f'<animate attributeName="opacity" values="{rnd.uniform(.1, .4):.2f};1;{rnd.uniform(.1, .4):.2f}" '
        f'dur="{rnd.uniform(1.5, 4):.1f}s" repeatCount="indefinite"/></circle>' for _ in range(n))


def jitter(base, n=14, amp=10):
    vals = [f"{base} 0" if rnd.random() < .8 else f"{base + rnd.randint(-amp, amp)} {rnd.randint(-3, 3)}"
            for _ in range(n)]
    return ";".join(vals + [f"{base} 0"])


def glitch_title(text, x, y, size=30):
    t = f'font-family="{SANS}" font-weight="900" font-style="italic" font-size="{size}" letter-spacing="3"'
    return f'''<g>
<text x="{x}" y="{y}" {t} fill="{CYAN}" opacity=".8"><animateTransform attributeName="transform" type="translate" values="{jitter(-2, amp=8)}" dur="2.1s" calcMode="discrete" repeatCount="indefinite"/>{esc(text)}</text>
<text x="{x}" y="{y}" {t} fill="{PINK}" opacity=".8"><animateTransform attributeName="transform" type="translate" values="{jitter(2, amp=8)}" dur="1.7s" calcMode="discrete" repeatCount="indefinite"/>{esc(text)}</text>
<text x="{x}" y="{y}" {t} fill="#fff" filter="url(#softglow)">{esc(text)}</text>
</g>'''


def panel(x, y, w, h):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{BG}" fill-opacity=".86" '
            f'stroke="{PINK}" stroke-opacity=".55" stroke-width="1.5"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="3" rx="1.5" fill="url(#panelline)">'
            f'<animate attributeName="opacity" values=".5;1;.5" dur="3s" repeatCount="indefinite"/></rect>')


def build():
    imgs = {k: fetch(u) for k, u in CARDS.items()}
    cells, total = contributions()

    # ---- layout (y coordinates)
    HZ = 250                      # header horizon
    TYPE_Y = 470
    AB_Y, AB_H = 530, 300
    ST_Y = AB_Y + AB_H + 40       # stats panel
    ST_H = 310
    CT_Y = ST_Y + ST_H + 40       # contributions panel
    CT_H = 330
    FT_SKY = CT_Y + CT_H + 40     # footer sky starts
    FT_HZ = FT_SKY + 90           # footer horizon
    H = FT_HZ + 140

    mountains = ("M0 250 L90 205 L160 232 L250 180 L330 228 L420 196 L470 250 Z "
                 "M730 250 L800 210 L880 236 L960 178 L1040 224 L1120 196 L1200 222 L1200 250 Z")
    sun_stripes = "".join(
        f'<rect x="0" y="{200 + i * 14}" width="{W}" height="{2 + i * 1.4:.1f}">'
        f'<animate attributeName="y" values="{200 + i * 14};{214 + i * 14}" dur="2s" repeatCount="indefinite"/></rect>'
        for i in range(6))

    # name slices that jump sideways in short bursts
    sl_defs, sl = [], []
    for i, (y, h) in enumerate([(40, 16), (58, 12), (72, 18), (92, 10)]):
        steps = ["0 0"] * 20
        at = rnd.randint(2, 17)
        steps[at] = f"{rnd.choice([-30, -18, 22, 34])} 0"
        steps[at + 1] = f"{rnd.choice([-12, 10, 16])} 0"
        vals = ";".join(steps + ["0 0"])
        sl_defs.append(f'<clipPath id="sl{i}"><rect x="0" y="{y}" width="{W}" height="{h}"/></clipPath>')
        sl.append(f'<g clip-path="url(#sl{i})"><g><use href="#nm" fill="#fff"/>'
                  f'<animateTransform attributeName="transform" type="translate" values="{vals}" '
                  f'dur="{4 + i * .7:.2f}s" calcMode="discrete" repeatCount="indefinite"/></g></g>')

    # typing lines (monospace, forced width so the reveal and cursor line up)
    CH, FS = 14.4, 24
    typing = []
    for i, line in enumerate(TYPING):
        w = round(len(line) * CH)
        x0 = round(600 - w / 2)
        kt = 'keyTimes="0;0.1;0.27;0.32;1" dur="12s" begin="{b}s" repeatCount="indefinite"'.format(b=i * 4)
        typing.append(f'''<clipPath id="ty{i}"><rect x="{x0}" y="{TYPE_Y - 24}" height="34" width="0"><animate attributeName="width" values="0;{w};{w};0;0" {kt}/></rect></clipPath>
<g clip-path="url(#ty{i})"><text x="{x0}" y="{TYPE_Y}" font-family="{MONO}" font-size="{FS}" font-weight="600" fill="{PINK}" textLength="{w}" lengthAdjust="spacingAndGlyphs">{esc(line)}</text></g>
<rect x="{x0}" y="{TYPE_Y - 21}" width="12" height="27" fill="{CYAN}" opacity="{1 if i == 0 else 0}">
  <animate attributeName="x" values="{x0};{x0 + w + 3};{x0 + w + 3};{x0};{x0}" {kt}/>
  <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.32;0.33;1" dur="12s" begin="{i * 4}s" repeatCount="indefinite"/>
</rect>''')

    about = []
    yy = AB_Y + 110
    for line in ABOUT:
        cont = line.startswith("  ")
        if not cont:
            about.append(f'<text x="130" y="{yy}" font-family="{MONO}" font-size="20" fill="{CYAN}">▹</text>')
        about.append(f'<text x="160" y="{yy}" font-family="{SANS}" font-size="22" fill="{TEXT}">{esc(line.strip())}</text>')
        i = ABOUT.index(line)
        next_is_cont = i + 1 < len(ABOUT) and ABOUT[i + 1].startswith("  ")
        yy += 32 if next_is_cont else 46

    tears = "".join(
        f'<clipPath id="tear{j}"><rect x="0" y="-40" width="{W}" height="{rnd.randint(14, 34)}">'
        f'<animate attributeName="y" values="-40;-40;{rnd.randint(0, H)};-40;-40;{rnd.randint(0, H)};-40" '
        f'keyTimes="0;{a:.2f};{a + .01:.2f};{a + .02:.2f};{a + .4:.2f};{a + .41:.2f};1" dur="{6 + j}s" calcMode="discrete" repeatCount="indefinite"/>'
        f'</rect></clipPath>' for j, a in enumerate([rnd.uniform(.05, .5) for _ in range(3)]))

    defs = f'''
<clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
<filter id="softglow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="neon" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="5" result="b1"/><feGaussianBlur stdDeviation="14" in="SourceGraphic" result="b2"/><feMerge><feMergeNode in="b2"/><feMergeNode in="b1"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="noise"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="1"><animate attributeName="seed" values="1;2;3;4;5;6;7;8" dur=".8s" calcMode="discrete" repeatCount="indefinite"/></feTurbulence><feColorMatrix type="saturate" values="0"/></filter>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="2" fill="#000" opacity=".16"/></pattern>
<pattern id="flat" width="60" height="60" patternUnits="userSpaceOnUse">
  <path d="M60 0H0V60" fill="none" stroke="{PINK}" stroke-opacity=".13" stroke-width="1"/>
  <animateTransform attributeName="patternTransform" type="translate" values="0 0;0 60" dur="3s" repeatCount="indefinite"/>
</pattern>
<linearGradient id="gridfade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{PINK}" stop-opacity="0"/><stop offset=".25" stop-color="{PINK}" stop-opacity=".9"/><stop offset="1" stop-color="{PINK}"/></linearGradient>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset=".6" stop-color="#2a0a4a"/><stop offset="1" stop-color="#5b1067"/></linearGradient>
<linearGradient id="sky2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="#5b1067"/></linearGradient>
<linearGradient id="floor" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>
<linearGradient id="sun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{YELLOW}"/><stop offset=".55" stop-color="#ff6c9b"/><stop offset="1" stop-color="#c3137b"/></linearGradient>
<linearGradient id="panelline" x1="0" x2="1"><stop offset="0" stop-color="{PINK}" stop-opacity="0"/><stop offset=".5" stop-color="{CYAN}"/><stop offset="1" stop-color="{PINK}" stop-opacity="0"/></linearGradient>
<linearGradient id="midfade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".08" stop-color="#fff"/><stop offset=".92" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="midmask"><rect x="0" y="380" width="{W}" height="{FT_SKY - 380}" fill="url(#midfade)"/></mask>
<mask id="sunmask"><rect width="{W}" height="{H}" fill="#fff"/><g fill="#000">{sun_stripes}</g></mask>
<mask id="sunmask2"><rect width="{W}" height="{H}" fill="#fff"/><g fill="#000" transform="translate(0 {FT_HZ - 250})">{sun_stripes}</g></mask>
<text id="nm" x="600" y="100" text-anchor="middle" font-family="{SANS}" font-weight="900" font-style="italic" font-size="84" letter-spacing="6">{NAME}</text>
{"".join(sl_defs)}
{tears}'''

    bg = f'''<g id="bg">
<rect width="{W}" height="{H}" fill="{BG}"/>
<!-- header scene -->
<rect width="{W}" height="{HZ}" fill="url(#sky)"/>
{stars(0, 210, 60)}
<g mask="url(#sunmask)"><circle cx="600" cy="250" r="105" fill="url(#sun)" filter="url(#softglow)"/></g>
<path d="{mountains}" fill="#12032a" stroke="{PINK}" stroke-width="1.5" stroke-opacity=".7"/>
<rect y="{HZ}" width="{W}" height="150" fill="url(#floor)"/>
{perspective_grid(HZ, 400)}
<line x1="0" y1="{HZ}" x2="{W}" y2="{HZ}" stroke="#ff9de9" stroke-width="2" filter="url(#softglow)"/>
<!-- middle: flat grid flying past + stars -->
<g mask="url(#midmask)"><rect x="0" y="380" width="{W}" height="{FT_SKY - 380}" fill="url(#flat)"/></g>
{stars(420, FT_SKY - 20, 70)}
<!-- footer scene: second horizon -->
<rect y="{FT_SKY}" width="{W}" height="{FT_HZ - FT_SKY}" fill="url(#sky2)"/>
<g mask="url(#sunmask2)"><circle cx="600" cy="{FT_HZ}" r="80" fill="url(#sun)" filter="url(#softglow)"/></g>
<path d="{mountains}" transform="translate(0 {FT_HZ}) scale(1 .5) translate(0 -250)" fill="#12032a" stroke="{PINK}" stroke-width="1.5" stroke-opacity=".7"/>
<rect y="{FT_HZ}" width="{W}" height="{H - FT_HZ}" fill="url(#floor)"/>
{perspective_grid(FT_HZ, H, n=7, dur=2.4)}
<line x1="0" y1="{FT_HZ}" x2="{W}" y2="{FT_HZ}" stroke="#ff9de9" stroke-width="2" filter="url(#softglow)"/>
</g>'''

    cal_svg = city_grid(cells, 120, CT_Y + CT_H - 60, 960)
    content = f'''
<!-- name -->
<use href="#nm" fill="{CYAN}" opacity=".85" style="mix-blend-mode:screen"><animateTransform attributeName="transform" type="translate" values="{jitter(-4)}" dur="2.3s" calcMode="discrete" repeatCount="indefinite"/></use>
<use href="#nm" fill="{PINK}" opacity=".85" style="mix-blend-mode:screen"><animateTransform attributeName="transform" type="translate" values="{jitter(4)}" dur="1.9s" calcMode="discrete" repeatCount="indefinite"/></use>
<use href="#nm" fill="#fff" filter="url(#neon)"><animate attributeName="opacity" values="1;1;.35;1;.6;1;1" keyTimes="0;.82;.84;.86;.88;.9;1" dur="5s" repeatCount="indefinite"/></use>
{"".join(sl)}
<text x="600" y="140" text-anchor="middle" font-family="{MONO}" font-size="20" letter-spacing="8" fill="{YELLOW}" filter="url(#softglow)">{esc(TAGLINE)}</text>
<text x="28" y="34" font-family="{MONO}" font-size="12" fill="{PINK}">REC ●<animate attributeName="opacity" values=".8;.2" dur="1.2s" calcMode="discrete" repeatCount="indefinite"/></text>
<text x="1172" y="34" text-anchor="end" font-family="{MONO}" font-size="12" fill="{CYAN}" opacity=".6">CH-1984 · SIGNAL UNSTABLE</text>

<!-- typing -->
<rect x="270" y="{TYPE_Y - 34}" width="660" height="52" rx="26" fill="{BG}" fill-opacity=".88" stroke="{PINK}" stroke-opacity=".5"/>
{"".join(typing)}

<!-- about -->
{panel(80, AB_Y, 1040, AB_H)}
{glitch_title("▸ ABOUT", 120, AB_Y + 58)}
{"".join(about)}

<!-- stats -->
{panel(80, ST_Y, 1040, ST_H)}
{glitch_title("▸ STATS", 120, ST_Y + 58)}
<image href="{imgs["stats"]}" x="110" y="{ST_Y + 85}" width="420" height="200" preserveAspectRatio="xMinYMid meet"/>
<image href="{imgs["streak"]}" x="540" y="{ST_Y + 85}" width="560" height="200"/>

<!-- contributions -->
{panel(80, CT_Y, 1040, CT_H)}
{glitch_title("▸ CONTRIBUTIONS", 120, CT_Y + 58)}
<text x="1080" y="{CT_Y + 56}" text-anchor="end" font-family="{MONO}" font-size="18" fill="{YELLOW}" filter="url(#softglow)">{total:,} in the last year</text>
{cal_svg}
<g font-family="{MONO}" font-size="12" fill="#9d8cc4">
  <text x="{1080 - 5 * 18 - 48}" y="{CT_Y + CT_H - 22}" text-anchor="end">less</text>
  {"".join(f'<rect x="{1080 - (5 - i) * 18 - 40}" y="{CT_Y + CT_H - 33}" width="14" height="14" rx="3" fill="{c}"/>' for i, c in enumerate(["#1f0c3d", "#5c1b8a", "#a125b8", "#e62ccf", "#ff6ae6"]))}
  <text x="1080" y="{CT_Y + CT_H - 22}" text-anchor="end">more</text>
</g>

<!-- sign-off -->
<rect x="390" y="{FT_HZ + 50}" width="420" height="44" rx="6" fill="{BG}" fill-opacity=".85" stroke="{CYAN}" stroke-opacity=".6"/>
<text x="600" y="{FT_HZ + 79}" text-anchor="middle" font-family="{MONO}" font-size="16" letter-spacing="4" fill="{YELLOW}">{esc(SIGNOFF)}<animate attributeName="opacity" values="1;1;.3;1;1" keyTimes="0;.9;.92;.94;1" dur="4s" repeatCount="indefinite"/></text>
'''

    crt = (f'<g clip-path="url(#tear0)"><use href="#bg" transform="translate(-36 0)"/></g>'
           f'<g clip-path="url(#tear1)"><use href="#bg" transform="translate(28 0)"/></g>'
           f'<g clip-path="url(#tear2)"><use href="#bg" transform="translate(-20 0)"/></g>')
    overlay = (f'<rect width="{W}" height="{H}" filter="url(#noise)" opacity=".05"/>'
               f'<rect width="{W}" height="{H}" fill="url(#scan)"/>'
               f'<rect x="0" y="-80" width="{W}" height="80" fill="#fff" opacity=".04">'
               f'<animate attributeName="y" values="-80;{H}" dur="7s" repeatCount="indefinite"/></rect>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>{defs}</defs>
<g clip-path="url(#frame)">
{bg}
{crt}
{content}
{overlay}
</g>
</svg>'''


if __name__ == "__main__":
    svg = build()
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote assets/profile.svg ({len(svg) // 1024} KB)")
