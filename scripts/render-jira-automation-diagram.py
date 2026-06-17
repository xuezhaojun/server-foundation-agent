#!/usr/bin/env python3
"""Render jira-automation-model.png — sharp diagram with auto-sized node boxes."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = "#f3f4f6"
STAGE_FILL = "#f9fafb"
STAGE_BORDER = "#9ca3af"
BOX_FILL = "#ffffff"
BOX_BORDER = "#d1d5db"
TEXT = "#111827"
ARROW = "#2563eb"

FONT_PATHS = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
]

STAGES: list[tuple[str, list[str]]] = [
    ("daily-bug-triage", ["New SF bugs", "Analyze + comment", "label agent-triaged"]),
    ("Human groom", ["Human reviews triage", "label issue-for-agent"]),
    (
        "jira-pipeline twice daily",
        ["Agent queue JQL", "Fix one issue", "Draft PR", "label agent-processed"],
    ),
]

PAD_X = 28
GAP = 36
STAGE_PAD = 24
STAGE_GAP = 48
TITLE_GAP = 18
BOX_H = 56
MARGIN = 32


@dataclass
class Node:
    label: str
    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def cx(self) -> int:
        return (self.x0 + self.x1) // 2

    @property
    def cy(self) -> int:
        return (self.y0 + self.y1) // 2

    @property
    def right(self) -> int:
        return self.x1

    @property
    def left(self) -> int:
        return self.x0


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def box_width(draw: ImageDraw.ImageDraw, label: str, font) -> int:
    tw, _ = text_size(draw, label, font)
    return tw + PAD_X * 2


def draw_arrowhead(draw: ImageDraw.ImageDraw, tip: tuple[int, int], angle: float) -> None:
    size = 12
    left = (
        tip[0] - size * math.cos(angle - math.pi / 6),
        tip[1] - size * math.sin(angle - math.pi / 6),
    )
    right = (
        tip[0] - size * math.cos(angle + math.pi / 6),
        tip[1] - size * math.sin(angle + math.pi / 6),
    )
    draw.polygon([tip, left, right], fill=ARROW)


def draw_line_arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    width: int = 3,
) -> None:
    draw.line([start, end], fill=ARROW, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    draw_arrowhead(draw, end, angle)


def draw_h_arrow(draw: ImageDraw.ImageDraw, x0: int, x1: int, y: int) -> None:
    draw_line_arrow(draw, (x0 + 6, y), (x1 - 6, y))


def layout_nodes(
    draw: ImageDraw.ImageDraw,
    font,
    stage_x: int,
    stage_w: int,
    labels: list[str],
    y_node: int,
) -> list[Node]:
    widths = [box_width(draw, label, font) for label in labels]
    inner_w = sum(widths) + GAP * (len(labels) - 1)
    x = stage_x + STAGE_PAD + max(0, (stage_w - STAGE_PAD * 2 - inner_w) // 2)
    nodes: list[Node] = []
    for label, w in zip(labels, widths, strict=True):
        nodes.append(Node(label, x, y_node, x + w, y_node + BOX_H))
        x += w + GAP
    return nodes


def main() -> None:
    title_font = load_font(24)
    node_font = load_font(20)

    # Size canvas from content — stage height fits title + one node row + padding
    probe = Image.new("RGB", (1, 1))
    probe_draw = ImageDraw.Draw(probe)
    _, title_h = text_size(probe_draw, "daily-bug-triage", title_font)
    h_stage = STAGE_PAD + title_h + TITLE_GAP + BOX_H + STAGE_PAD
    y_stage = MARGIN
    y_node = y_stage + STAGE_PAD + title_h + TITLE_GAP
    H = y_stage + h_stage + MARGIN
    W = 2800

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Measure stage widths from content
    stage_inner: list[int] = []
    for _, labels in STAGES:
        widths = [box_width(draw, label, node_font) for label in labels]
        stage_inner.append(sum(widths) + GAP * (len(labels) - 1) + STAGE_PAD * 2)

    total_w = sum(stage_inner) + STAGE_GAP * (len(STAGES) - 1)
    x = (W - total_w) // 2

    all_stage_nodes: list[list[Node]] = []
    stage_rects: list[tuple[int, int, int, int]] = []

    for (title, labels), inner_w in zip(STAGES, stage_inner, strict=True):
        stage_w = inner_w
        rect = (x, y_stage, x + stage_w, y_stage + h_stage)
        stage_rects.append(rect)
        all_stage_nodes.append(layout_nodes(draw, node_font, x, stage_w, labels, y_node))
        x += stage_w + STAGE_GAP

    # Stage backgrounds
    for (title, _), rect, nodes in zip(STAGES, stage_rects, all_stage_nodes, strict=True):
        draw.rounded_rectangle(rect, radius=14, fill=STAGE_FILL, outline=STAGE_BORDER, width=2)
        draw.text((rect[0] + STAGE_PAD, rect[1] + STAGE_PAD), title, fill=TEXT, font=title_font)

    # Inter-stage connectors (straight horizontal)
    for prev_nodes, next_nodes in zip(all_stage_nodes, all_stage_nodes[1:], strict=False):
        if not prev_nodes or not next_nodes:
            continue
        draw_h_arrow(draw, prev_nodes[-1].right, next_nodes[0].left, prev_nodes[-1].cy)

    # Intra-stage arrows
    for nodes in all_stage_nodes:
        for a, b in zip(nodes, nodes[1:], strict=False):
            draw_h_arrow(draw, a.right, b.left, a.cy)

    # Node boxes on top
    for nodes in all_stage_nodes:
        for node in nodes:
            draw.rounded_rectangle(
                (node.x0, node.y0, node.x1, node.y1),
                radius=10,
                fill=BOX_FILL,
                outline=BOX_BORDER,
                width=2,
            )
            tw, th = text_size(draw, node.label, node_font)
            draw.text(
                (node.cx - tw / 2, node.cy - th / 2),
                node.label,
                fill=TEXT,
                font=node_font,
            )

    out = Path(__file__).resolve().parent.parent / "docs/assets/jira-automation-model.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format="PNG", optimize=True)
    print(f"Wrote {out} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()
