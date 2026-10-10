"""Generate the animated Raspberry Pi hero images for the profile README.

GitHub renders README images through <img>, which never runs JavaScript, so every
variant is static SVG markup animated with CSS only. Four files are written to
../assets: {wide, narrow} layout x {dark, light} theme. The README picks one with
<picture> media queries (viewport width + prefers-color-scheme).

Usage:  python scripts/gen_profile_svg.py            # animated files into assets/
        python scripts/gen_profile_svg.py --static DIR  # final frame, for screenshots
"""
from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# --- content --------------------------------------------------------------------------

# (gpio, physical pin, label, category); physical numbering matches the real 40-pin header
PINMAP = [
    ("GPIO2", 3, "C# · .NET 10 · Dapper", "core"),
    ("GPIO3", 5, "SQL Server · T-SQL", "core"),
    ("GPIO4", 7, "OnBase Workflow (cert.)", "ai"),
    ("GPIO17", 11, "VLM · OCR / IDP", "ai"),
    ("GPIO27", 13, "vLLM · telemetry", "ai"),
    ("GPIO22", 15, "Python · data analysis", "inf"),
    ("GPIO10", 19, "Java · Spring Boot", "core"),
    ("GPIO9", 21, "AWS GPU · CUDA · Linux", "inf"),
    ("GPIO11", 23, "Arduino · micro:bit", "mk"),
    ("GPIO5", 29, "Embedded Systems Tech", "mk"),
    ("GPIO6", 31, "Claude Code · Codex", "ai"),
]

POLICY = [
    ("# AI-first, not AI-authoritative", "muted"),
    ("conf < τ    → abstain → human", "red"),
    ("rules fail  → reject", "yellow"),
    ("else        → publish + trace", "green"),
    ("new model   → eval vs ground truth", "purple"),
]

PROMPT_USER = "jose@raspberrypi"

# --- themes ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str
    bar: str
    border: str
    fg: str
    muted: str
    dim: str
    green: str
    blue: str
    purple: str
    orange: str
    red: str
    yellow: str
    track: str
    fill_model: str
    fill_gate: str


DARK = Theme("dark", "#0d1117", "#161b22", "#30363d", "#e6edf3", "#8b949e", "#484f58",
             "#3fb950", "#79c0ff", "#d2a8ff", "#ffa657", "#ff7b72", "#e3b341",
             "#21262d", "#8957e5", "#2ea043")
LIGHT = Theme("light", "#ffffff", "#f6f8fa", "#d0d7de", "#1f2328", "#59636e", "#8c959f",
              "#1a7f37", "#0969da", "#8250df", "#bc4c00", "#cf222e", "#9a6700",
              "#eaeef2", "#8250df", "#2da44e")

# The board is a physical object: it looks the same in both themes.
SILK, CHIP_TEXT, PORT, DARK_PART = "#e6edf3", "#0d1117", "#c9d1d9", "#16191d"
RING = {"core": "#3fb950", "ai": "#a371f7", "mk": "#f0883e", "inf": "#58a6ff"}


def cat_color(t: Theme, cat: str) -> str:
    return {"core": t.green, "ai": t.purple, "mk": t.orange, "inf": t.blue}[cat]


# --- layouts --------------------------------------------------------------------------


@dataclass(frozen=True)
class Layout:
    name: str
    w: int
    h: int
    out_w: int          # intrinsic width the <img> renders at (scaled down by max-width:100%)
    font: int
    x0: int             # left text margin
    board_dx: int
    # y of the four prompts
    p1: int
    p2: int
    p3: int
    p4: int
    gate_cmd: str
    plot_cmd: str
    gpio_comment: str


WIDE = Layout("wide", 680, 636, 840, 11, 20, 0, 50, 330, 410, 602,
              "python3 gate_stats.py --source telemetry.db",
              "python3 abstain.py --plot confidence --synthetic",
              "# CR · MX · international remote")
NARROW = Layout("narrow", 400, 1000, 400, 12, 14, -6, 50, 568, 668, 960,
                "python3 gate_stats.py",
                "python3 abstain.py --synthetic",
                "# CR · MX · remote")

# --- building blocks ------------------------------------------------------------------


def fade(delay: float) -> str:
    return f'class="f" style="animation-delay:{delay:.2f}s"'


def prompt(t: Theme, lo: Layout, y: int, cmd: str, delay: float) -> str:
    return (
        f'<text x="{lo.x0}" y="{y}"><tspan fill="{t.green}">{PROMPT_USER}</tspan>'
        f'<tspan fill="{t.fg}">:</tspan><tspan fill="{t.blue}">~</tspan>'
        f'<tspan fill="{t.fg}"> $ {escape(cmd)}</tspan></text>\n'
        f'<rect class="cv" x="{lo.x0 - 2}" y="{y - lo.font - 2}" width="{lo.w - lo.x0}" '
        f'height="{lo.font + 7}" fill="{t.bg}" style="animation-delay:{delay:.2f}s"/>'
    )


def pin_x(col: int) -> int:
    return 62 + col * 14


def board(t: Theme, lo: Layout) -> str:
    holes = "".join(
        f'<circle cx="{x}" cy="{y}" r="6" fill="{t.bg}" stroke="#c9a227" stroke-width="2"/>'
        for x, y in [(36, 80), (36, 284), (364, 80), (300, 284)]
    )
    pins = []
    for col in range(20):
        for y, odd in ((76, False), (90, True)):
            n = col * 2 + (1 if odd else 2)
            fill, rx = ("#e3b341", 0) if n == 1 else ("#c9a227", 1.5)
            pins.append(f'<rect x="{pin_x(col) - 4}" y="{y - 4}" width="8" height="8" rx="{rx}" fill="{fill}"/>')
    rings = "".join(
        f'<circle cx="{pin_x((n - 1) // 2)}" cy="90" r="6.5" fill="none" stroke="{RING[cat]}" '
        f'stroke-width="2" {fade(1.6 + i * 0.3)}/>'
        for i, (_, n, _, cat) in enumerate(PINMAP)
    )
    return f"""<g class="bd" transform="translate({lo.board_dx} 0)">
<g {fade(1.0)}>
<rect x="20" y="64" width="360" height="236" rx="14" fill="#0e5c31" stroke="#0a4424"/>
<g fill="none" stroke="#17824a" stroke-width="1.5">
<path d="M220 185h15M220 170h15M220 200h15"/><path d="M185 150V112M195 150V112M175 150V112"/>
<path d="M150 205H110V180M150 195H120"/><path d="M280 185h50M280 175h50"/><path d="M200 220v40h30"/>
</g>
{holes}
<rect x="53" y="69" width="284" height="28" rx="2" fill="{DARK_PART}"/>
{''.join(pins)}
<text x="56" y="110" fill="{SILK}" opacity=".75">J8</text>
<rect x="40" y="122" width="62" height="42" rx="3" fill="#b8c0c8"/><text x="71" y="147" text-anchor="middle" fill="#30363d">Wi-Fi</text>
<rect x="148" y="150" width="72" height="72" rx="4" fill="#9aa4ad"/><rect x="154" y="156" width="60" height="60" rx="3" fill="#848e97"/>
<text x="184" y="182" text-anchor="middle" fill="{CHIP_TEXT}">JAHM</text><text x="184" y="198" text-anchor="middle" fill="{CHIP_TEXT}">C# SoC</text>
<rect x="235" y="160" width="46" height="52" rx="2" fill="{DARK_PART}"/><text x="258" y="190" text-anchor="middle" fill="{SILK}">SQL</text>
<rect x="328" y="116" width="64" height="44" rx="2" fill="{PORT}"/><rect x="340" y="128" width="46" height="8" fill="#1f6feb"/><rect x="340" y="140" width="46" height="8" fill="#1f6feb"/>
<rect x="328" y="166" width="64" height="44" rx="2" fill="{PORT}"/><rect x="340" y="178" width="46" height="8" fill="{DARK_PART}"/><rect x="340" y="190" width="46" height="8" fill="{DARK_PART}"/>
<rect x="328" y="218" width="64" height="58" rx="2" fill="{PORT}"/><rect x="342" y="232" width="40" height="30" rx="2" fill="{DARK_PART}"/>
<rect x="64" y="290" width="30" height="16" rx="5" fill="{PORT}"/><rect x="118" y="292" width="26" height="12" rx="2" fill="{PORT}"/>
<rect x="160" y="292" width="26" height="12" rx="2" fill="{PORT}"/><circle cx="222" cy="296" r="9" fill="{DARK_PART}"/>
<rect x="34" y="196" width="10" height="6" rx="1" fill="#ff5f57"/>
<rect class="bl" x="34" y="208" width="10" height="6" rx="1" fill="#3fb950"/>
<text x="50" y="203" fill="{SILK}" opacity=".7">PWR</text><text x="50" y="215" fill="{SILK}" opacity=".7">ACT</text>
<text x="40" y="250" fill="{SILK}">Raspberry Pi · Model JAHM v10.0</text>
<text x="40" y="266" fill="{SILK}" opacity=".6">© 2014–2026 JoseMoyaCR · CR/MX</text>
</g>
{rings}
</g>"""


def pin_table(t: Theme, lo: Layout) -> str:
    if lo is WIDE:
        x, y0, step, dot_x, label_x = 404, 82, 20, 490, 501
    else:
        x, y0, step, dot_x, label_x = 20, 334, 20, 108, 118
    rows = []
    for i, (gpio, n, label, cat) in enumerate(PINMAP):
        y, col = y0 + i * step, cat_color(t, cat)
        rows.append(
            f'<g {fade(1.6 + i * 0.3)}><text x="{x}" y="{y}" fill="{t.muted}" xml:space="preserve">{gpio:<6} ({n})</text>'
            f'<circle cx="{dot_x}" cy="{y - 4}" r="4" fill="{col}"/>'
            f'<text x="{label_x}" y="{y}" fill="{col}">{escape(label)}</text></g>'
        )
    return "\n".join(rows)


def gate_stats(t: Theme, lo: Layout) -> str:
    bar_y = lo.p2 + 14
    bar_w = lo.w - 2 * (lo.x0 + 4)
    gate_w = round(bar_w * 0.40, 1)
    x = lo.x0 + 4
    if lo is WIDE:
        labels = (
            f'<text x="{x}" y="{bar_y + 34}" fill="{t.green}">~40% resolved by gate + cache</text>'
            f'<text x="{x + bar_w}" y="{bar_y + 34}" text-anchor="end" fill="{t.purple}">rest → VLM · vLLM on A10G</text>'
        )
    else:
        labels = (
            f'<text x="{x}" y="{bar_y + 34}" fill="{t.green}">~40% resolved by gate + cache (no model)</text>'
            f'<text x="{x}" y="{bar_y + 52}" fill="{t.purple}">rest → VLM · vLLM on NVIDIA A10G</text>'
        )
    return f"""<g {fade(5.9)}>
<rect x="{x}" y="{bar_y}" width="{bar_w}" height="16" rx="3" fill="{t.track}"/>
<rect class="gr" x="{x}" y="{bar_y}" width="{bar_w}" height="16" rx="3" fill="{t.fill_model}" style="animation-delay:6s"/>
<rect class="gr" x="{x}" y="{bar_y}" width="{gate_w}" height="16" rx="3" fill="{t.fill_gate}" style="animation-delay:6.3s"/>
{labels}
</g>"""


def plot(t: Theme, lo: Layout) -> str:
    # Synthetic distribution (the prompt says --synthetic): accuracy grows with confidence.
    if lo is WIDE:
        left, right, top, bottom, ylab_x = 60, 380, 436, 560, 50
    else:
        left, right, top, bottom, ylab_x = 46, 386, lo.p3 + 20, lo.p3 + 132, 36
    span, height = right - left, bottom - top
    tau_x = round(left + 0.45 * span)
    rng = random.Random(7)
    points = []
    for i in range(46):
        c = 0.04 + rng.random() * 0.94
        a = min(0.98, max(0.05, c * 0.75 + 0.18 + (rng.random() - 0.5) * 0.28))
        points.append(
            f'<circle cx="{left + c * span:.1f}" cy="{bottom - a * (height - 8):.1f}" r="3.2" '
            f'fill="{t.red if c < 0.45 else t.green}" {fade(8.4 + i * 0.035)}/>'
        )
    if lo is WIDE:
        px, py, pstep = 408, 458, 22
    else:
        px, py, pstep = lo.x0 + 6, bottom + 46, 20
    colors = {"muted": t.muted, "red": t.red, "yellow": t.yellow, "green": t.green, "purple": t.purple}
    policy = "\n".join(
        f'<text x="{px}" y="{py + j * pstep}" fill="{colors[c]}" xml:space="preserve" {fade(10.4 + j * 0.3)}>{escape(s)}</text>'
        for j, (s, c) in enumerate(POLICY)
    )
    return f"""<g {fade(8.2)}>
<rect x="{left}" y="{top}" width="{tau_x - left}" height="{height}" fill="{t.red}" opacity=".08"/>
<path d="M{left} {top - 4}V{bottom}H{right}" fill="none" stroke="{t.dim}"/>
<text x="{left + 6}" y="{top + 14}" fill="{t.red}">abstain</text>
<text x="{right - 6}" y="{top + 14}" text-anchor="end" fill="{t.green}">publish</text>
<text x="{right}" y="{bottom + 16}" text-anchor="end" fill="{t.muted}">confidence →</text>
<text transform="translate({ylab_x} {bottom}) rotate(-90)" fill="{t.muted}">accuracy →</text>
</g>
{chr(10).join(points)}
<g {fade(10.1)}><path d="M{tau_x} {top}V{bottom}" stroke="{t.yellow}" stroke-dasharray="4 3"/>
<text x="{tau_x + 4}" y="{bottom + 14}" fill="{t.yellow}">τ</text></g>
{policy}"""


def gpio_out(t: Theme, lo: Layout) -> str:
    return (
        f'<g {fade(13.0)}><text x="{lo.x0}" y="{lo.p4 + 20}" xml:space="preserve">'
        f'<tspan fill="{t.fg}">"open_to_work"=</tspan><tspan fill="{t.green}">active</tspan>'
        f'<tspan fill="{t.muted}">   {escape(lo.gpio_comment)} </tspan>'
        f'<tspan class="bc" fill="{t.fg}">█</tspan></text></g>'
    )


def svg(t: Theme, lo: Layout, static: bool = False) -> str:
    w, h = lo.w, lo.h
    out_h = round(lo.out_w * h / w)
    static_css = ".f,.cv,.gr,.bl,.bc{animation:none!important;opacity:1;transform:none}.cv{display:none}" if static else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{lo.out_w}" height="{out_h}" role="img" aria-labelledby="t d">
<title id="t">jose@raspberrypi: pinout --engineer jahm</title>
<desc id="d">Animated terminal on a Raspberry Pi: GPIO pins light up with José Hernández Moya's stack, then quality-gate stats from production telemetry, a synthetic confidence/abstention plot and open_to_work = active.</desc>
<style>
text{{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;font-size:{lo.font}px}}
.bd text{{font-size:11px}}
.f{{opacity:0;animation:fi .5s ease forwards}}
.cv{{animation:ty 1s steps(36) forwards}}
.gr{{transform-box:fill-box;transform-origin:left;transform:scaleX(0);animation:gr 1.4s ease-out forwards}}
.bl{{animation:bl 1.1s steps(1) infinite}}
.bc{{animation:bc 1.1s steps(1) infinite}}
@keyframes fi{{to{{opacity:1}}}}
@keyframes ty{{to{{transform:translateX({w}px)}}}}
@keyframes gr{{to{{transform:scaleX(1)}}}}
@keyframes bl{{50%{{opacity:.12}}}}
@keyframes bc{{50%{{fill-opacity:0}}}}
@media (prefers-reduced-motion:reduce){{.f,.cv,.gr,.bl,.bc{{animation:none;opacity:1;transform:none}}.cv{{display:none}}}}
{static_css}
</style>
<defs><clipPath id="in"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="11"/></clipPath></defs>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{t.bg}"/>
<g clip-path="url(#in)">
<path d="M12.5 .5h{w - 25}a12 12 0 0 1 12 12v16H.5v-16a12 12 0 0 1 12-12z" fill="{t.bar}"/>
<circle cx="18" cy="14" r="5" fill="#ff5f57"/><circle cx="34" cy="14" r="5" fill="#febc2e"/><circle cx="50" cy="14" r="5" fill="#28c840"/>
<text x="{w // 2}" y="18" text-anchor="middle" fill="{t.muted}" style="font-size:11px">{PROMPT_USER}: ~</text>
{prompt(t, lo, lo.p1, "pinout --engineer jahm", 0.2)}
{board(t, lo)}
{pin_table(t, lo)}
{prompt(t, lo, lo.p2, lo.gate_cmd, 5.0)}
{gate_stats(t, lo)}
{prompt(t, lo, lo.p3, lo.plot_cmd, 7.6)}
{plot(t, lo)}
{prompt(t, lo, lo.p4, "gpioget open_to_work", 12.0)}
{gpio_out(t, lo)}
</g>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="none" stroke="{t.border}"/>
</svg>
"""


def main(argv: list[str]) -> None:
    static = len(argv) > 1 and argv[1] == "--static"
    out_dir = Path(argv[2]) if static and len(argv) > 2 else ASSETS
    out_dir.mkdir(parents=True, exist_ok=True)
    for lo in (WIDE, NARROW):
        for t in (DARK, LIGHT):
            name = f"rpi-{lo.name}-{t.name}.svg"
            (out_dir / name).write_text(svg(t, lo, static), encoding="utf-8", newline="\n")
            print(out_dir / name)


if __name__ == "__main__":
    main(sys.argv)
