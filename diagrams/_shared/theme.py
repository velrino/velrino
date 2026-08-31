"""Shared Graphviz theme and slide renderer for architecture diagrams.

Graphviz owns topology while this module keeps every portfolio diagram on the
same visual system: compact icon cards, quiet rounded panels, semantic flow
colors, and an exact 16:9 canvas with a consistent title band.
"""

from __future__ import annotations

import base64
import mimetypes
import shutil
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from diagrams import Cluster, Diagram, Edge, Node

LOGICAL_SIZE = (1920, 1080)
PNG_SCALE = 2
CANVAS_SIZE = tuple(dimension * PNG_SCALE for dimension in LOGICAL_SIZE)
HEADER_HEIGHT = 112
FRAME_MARGIN_X = 48
FRAME_MARGIN_BOTTOM = 40

BLUE = "#3b63f3"
PURPLE = "#8b5cf6"
ORANGE = "#ed8b00"
TEAL = "#0ea5b7"
GREEN = "#16a368"
RED = "#dc382d"
INK = "#211833"
MUTED = "#645b73"
PANEL_FILL = "#f6f7fb"
PANEL_LINE = "#d8dce8"
SANS = "Helvetica Neue, Helvetica, Arial, sans-serif"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf"
        if bold
        else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


FONT_TITLE = font(36 * PNG_SCALE, bold=True)
FONT_SUBTITLE = font(17 * PNG_SCALE)

GRAPH_ATTR = {
    "bgcolor": "white",
    "dpi": "192",
    "pad": "0.3",
    "nodesep": "0.42",
    "ranksep": "1.25",
    "splines": "spline",
    "newrank": "true",
    "compound": "true",
    "ordering": "out",
    "fontname": "Helvetica",
}
NODE_ATTR = {
    "fontname": "Helvetica",
    "fontcolor": INK,
}
EDGE_ATTR = {
    "color": BLUE,
    "fontcolor": MUTED,
    "fontname": "Helvetica",
    "fontsize": "12.5",
    "penwidth": "1.6",
    "arrowsize": "0.75",
    "labeldistance": "1.2",
}
CLUSTER_ATTR = {
    "style": "rounded,filled",
    "fillcolor": PANEL_FILL,
    "bgcolor": PANEL_FILL,
    "pencolor": PANEL_LINE,
    "penwidth": "1.2",
    "fontname": "Helvetica-Bold",
    "fontsize": "13",
    "fontcolor": MUTED,
    "labeljust": "r",
    "margin": "22",
}


def card(icon: type[Node], title: str, subtitle: str, **attrs: str) -> Node:
    """Create a compact icon card with a bold title and muted subtitle."""
    label = (
        f'<<font point-size="16"><b>{title}</b></font>'
        f'<br/><font point-size="12" color="{MUTED}">{subtitle}</font>>'
    )
    return icon(
        label,
        width="1.45",
        height="2.0",
        fixedsize="true",
        imagescale="true",
        imagepos="tc",
        labelloc="b",
        **attrs,
    )


def panel(title: str, **attrs: str) -> Cluster:
    return Cluster(title, graph_attr={**CLUSTER_ATTR, **attrs})


def flow(color: str = BLUE, label: str = "", **attrs: str) -> Edge:
    return Edge(color=color, label=label, **attrs)


def pulse(color: str, label: str = "", **attrs: str) -> Edge:
    """Render realtime, telemetry, fallback, or tunnel traffic as dashed."""
    return Edge(color=color, label=label, style="dashed", **attrs)


def frame_box(scale: int) -> tuple[int, int, int, int]:
    return (
        FRAME_MARGIN_X * scale,
        HEADER_HEIGHT * scale,
        (LOGICAL_SIZE[0] - FRAME_MARGIN_X) * scale,
        (LOGICAL_SIZE[1] - FRAME_MARGIN_BOTTOM) * scale,
    )


def write_slide_png(raw_output: Path, output: Path, title: str, subtitle: str) -> None:
    """Fit Graphviz below the title band on an exact 4K 16:9 canvas."""
    raw_png = raw_output.with_suffix(".png")
    left, top, right, bottom = frame_box(PNG_SCALE)
    frame = (right - left, bottom - top)
    with Image.open(raw_png) as source:
        fitted = ImageOps.contain(
            source.convert("RGB"), frame, method=Image.Resampling.LANCZOS
        )

    canvas = Image.new("RGB", CANVAS_SIZE, "white")
    canvas.paste(
        fitted,
        (left + (frame[0] - fitted.width) // 2, top + (frame[1] - fitted.height) // 2),
    )
    draw = ImageDraw.Draw(canvas)
    draw.text((42 * PNG_SCALE, 22 * PNG_SCALE), title, fill=INK, font=FONT_TITLE)
    draw.text(
        (44 * PNG_SCALE, 66 * PNG_SCALE), subtitle, fill=MUTED, font=FONT_SUBTITLE
    )
    canvas.save(output, quality=95)
    raw_png.unlink()


def svg_number(value: str) -> float:
    return float(
        "".join(
            character for character in value if character.isdigit() or character in ".-"
        )
    )


def write_portable_svg(
    raw_output: Path,
    output: Path,
    title_text: str,
    subtitle_text: str,
    aria_label: str,
) -> None:
    """Wrap Graphviz in a 16:9 SVG and inline icon files for portability."""
    raw_svg = raw_output.with_suffix(".svg")
    raw_root = ET.parse(raw_svg).getroot()
    svg_namespace = "http://www.w3.org/2000/svg"
    xlink_namespace = "http://www.w3.org/1999/xlink"
    ET.register_namespace("", svg_namespace)
    ET.register_namespace("xlink", xlink_namespace)

    for image in raw_root.iter(f"{{{svg_namespace}}}image"):
        href_key = f"{{{xlink_namespace}}}href"
        href = image.get(href_key) or image.get("href")
        if not href or href.startswith("data:"):
            continue
        icon_path = Path(href)
        if not icon_path.exists():
            continue
        mime_type = mimetypes.guess_type(icon_path.name)[0] or "image/png"
        encoded = base64.b64encode(icon_path.read_bytes()).decode("ascii")
        image.set(href_key, f"data:{mime_type};base64,{encoded}")
        image.attrib.pop("href", None)

    view_box = raw_root.get("viewBox")
    if view_box:
        _, _, raw_width, raw_height = map(float, view_box.split())
    else:
        raw_width = svg_number(raw_root.get("width", "1920"))
        raw_height = svg_number(raw_root.get("height", "1080"))

    left, top, right, bottom = frame_box(1)
    frame_width, frame_height = right - left, bottom - top
    scale = min(frame_width / raw_width, frame_height / raw_height)
    fitted_width = raw_width * scale
    fitted_height = raw_height * scale

    raw_root.set("x", f"{left + (frame_width - fitted_width) / 2:.2f}")
    raw_root.set("y", f"{top + (frame_height - fitted_height) / 2:.2f}")
    raw_root.set("width", f"{fitted_width:.2f}")
    raw_root.set("height", f"{fitted_height:.2f}")
    raw_root.set("preserveAspectRatio", "xMidYMid meet")

    outer = ET.Element(
        f"{{{svg_namespace}}}svg",
        {
            "width": str(LOGICAL_SIZE[0]),
            "height": str(LOGICAL_SIZE[1]),
            "viewBox": f"0 0 {LOGICAL_SIZE[0]} {LOGICAL_SIZE[1]}",
            "role": "img",
            "aria-label": aria_label,
        },
    )
    ET.SubElement(
        outer,
        f"{{{svg_namespace}}}rect",
        {"width": "100%", "height": "100%", "fill": "white"},
    )
    outer.append(raw_root)

    title = ET.SubElement(
        outer,
        f"{{{svg_namespace}}}text",
        {
            "x": "42",
            "y": "55",
            "fill": INK,
            "font-family": SANS,
            "font-size": "36",
            "font-weight": "700",
        },
    )
    title.text = title_text
    subtitle = ET.SubElement(
        outer,
        f"{{{svg_namespace}}}text",
        {"x": "44", "y": "82", "fill": MUTED, "font-family": SANS, "font-size": "17"},
    )
    subtitle.text = subtitle_text

    ET.ElementTree(outer).write(output, encoding="utf-8", xml_declaration=True)
    raw_svg.unlink()


def render_slide(
    *,
    root: Path,
    title: str,
    subtitle: str,
    aria_label: str,
    build_graph: Callable[[], None],
    asset_output: Path | None = None,
) -> None:
    """Build, frame, and optionally publish one architecture diagram."""
    raw_output = root / "architecture-raw"
    png_output = root / "architecture.png"
    svg_output = root / "architecture.svg"

    with Diagram(
        "",
        filename=str(raw_output),
        direction="LR",
        show=False,
        outformat=["png", "svg"],
        graph_attr=GRAPH_ATTR,
        node_attr=NODE_ATTR,
        edge_attr=EDGE_ATTR,
    ):
        build_graph()

    write_slide_png(raw_output, png_output, title, subtitle)
    write_portable_svg(raw_output, svg_output, title, subtitle, aria_label)

    if asset_output is not None:
        asset_output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(png_output, asset_output)

    print(f"Wrote {png_output} ({CANVAS_SIZE[0]}x{CANVAS_SIZE[1]})")
    print(f"Wrote {svg_output} (vector {LOGICAL_SIZE[0]}x{LOGICAL_SIZE[1]} viewBox)")
    if asset_output is not None:
        print(f"Published {asset_output}")
