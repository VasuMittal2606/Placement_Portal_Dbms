#!/usr/bin/env python3
"""Render the CampusHire entity-relationship diagram to er_diagram.jpg.

Pure matplotlib (no Graphviz): boxes are placed on a hand-tuned grid so the
layout stays readable, and relationships are drawn as crow's-foot connectors.

Usage:
    python tools/render_er_diagram.py
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "er_diagram.jpg"

# ---------------------------------------------------------------- palette
INK = "#0F172A"
TEAL = "#0D9488"
TEAL_LIGHT = "#14B8A6"
AMBER = "#B45309"
SLATE = "#64748B"
LINE = "#94A3B8"
PAPER = "#F8FAFC"

BOX_W = 18.5
HEADER_H = 4.0
ROW_H = 1.72
PAD_Y = 2.1

# type sizes (points); rows/boxes are sized to give these room
FS_TITLE = 19.5
FS_SUBTITLE = 9.6
FS_HEADER = 9.8
FS_ATTR = 7.3
FS_TYPE = 6.2
FS_TAG = 6.4
FS_CARD = 5.9
FS_LABEL = 6.2
FS_LEGEND = 7.3
# width of one point of text in data units (bold DejaVu Sans, empirical)
CHAR_UNITS = 0.0685


def header_fontsize(name: str) -> float:
    """Shrink the header slightly for long table names so it stays inside."""
    fit = (BOX_W - 1.8) / (CHAR_UNITS * max(len(name), 1))
    return min(FS_HEADER, fit)


def box_height(attrs: list[tuple[str, str, str]]) -> float:
    return HEADER_H + ROW_H * len(attrs) + PAD_Y


# ---------------------------------------------------------------- entities
# name: (cx, cy, [(tag, attribute, type), ...])
ENTITIES: dict[str, dict] = {
    "APP_USER": {
        "pos": (58, 86.5),
        "attrs": [
            ("PK", "user_id", "INT"),
            ("UK", "email", "VARCHAR(120)"),
            ("", "password_hash", "CHAR(64)"),
            ("", "full_name", "VARCHAR(100)"),
            ("", "role", "ENUM"),
            ("", "phone", "VARCHAR(15)"),
            ("", "is_active", "TINYINT(1)"),
        ],
    },
    "BRANCH": {
        "pos": (12, 70),
        "attrs": [
            ("PK", "branch_id", "INT"),
            ("UK", "branch_name", "VARCHAR(60)"),
        ],
    },
    "STUDENT": {
        "pos": (36, 66),
        "attrs": [
            ("PK", "student_id", "INT"),
            ("FK", "user_id", "INT"),
            ("UK", "roll_no", "VARCHAR(20)"),
            ("FK", "branch_id", "INT"),
            ("", "batch_year", "SMALLINT"),
            ("", "cgpa", "DECIMAL(4,2)"),
            ("", "backlogs", "INT"),
        ],
    },
    "RECRUITER": {
        "pos": (84, 76),
        "attrs": [
            ("PK", "recruiter_id", "INT"),
            ("FK", "user_id", "INT"),
            ("FK", "company_id", "INT"),
            ("", "designation", "VARCHAR(80)"),
        ],
    },
    "PLACEMENT_OFFICER": {
        "pos": (108, 86),
        "attrs": [
            ("PK", "officer_id", "INT"),
            ("FK", "user_id", "INT"),
            ("", "department", "VARCHAR(80)"),
        ],
    },
    "COMPANY": {
        "pos": (112, 62),
        "attrs": [
            ("PK", "company_id", "INT"),
            ("UK", "company_name", "VARCHAR(100)"),
            ("", "industry", "VARCHAR(80)"),
            ("", "website", "VARCHAR(150)"),
            ("", "location", "VARCHAR(100)"),
        ],
    },
    "JOB": {
        "pos": (108, 34),
        "attrs": [
            ("PK", "job_id", "INT"),
            ("FK", "company_id", "INT"),
            ("FK", "created_by", "INT"),
            ("", "job_title", "VARCHAR(100)"),
            ("", "ctc", "DECIMAL(12,2)"),
            ("", "min_cgpa", "DECIMAL(4,2)"),
            ("", "openings", "INT"),
            ("", "status", "ENUM"),
        ],
    },
    "SKILL": {
        "pos": (57, 56),
        "attrs": [
            ("PK", "skill_id", "INT"),
            ("UK", "skill_name", "VARCHAR(60)"),
        ],
    },
    "STUDENT_SKILL": {
        "pos": (24, 46.5),
        "attrs": [
            ("PK", "student_id", "INT"),
            ("PK", "skill_id", "INT"),
            ("", "proficiency", "ENUM"),
        ],
    },
    "JOB_SKILL": {
        "pos": (100, 14),
        "attrs": [
            ("PK", "job_id", "INT"),
            ("PK", "skill_id", "INT"),
            ("", "is_mandatory", "TINYINT(1)"),
        ],
    },
    "APPLICATION": {
        "pos": (52, 32),
        "attrs": [
            ("PK", "application_id", "INT"),
            ("FK", "job_id", "INT"),
            ("FK", "student_id", "INT"),
            ("", "status", "ENUM"),
            ("", "applied_at", "TIMESTAMP"),
        ],
    },
    "INTERVIEW": {
        "pos": (22, 17),
        "attrs": [
            ("PK", "interview_id", "INT"),
            ("FK", "application_id", "INT"),
            ("", "round_no", "INT"),
            ("", "interview_type", "ENUM"),
            ("", "scheduled_at", "DATETIME"),
            ("", "result", "ENUM"),
        ],
    },
    "OFFER": {
        "pos": (57, 10),
        "attrs": [
            ("PK", "offer_id", "INT"),
            ("FK", "application_id", "INT"),
            ("", "ctc", "DECIMAL(12,2)"),
            ("", "offer_date", "DATE"),
            ("", "status", "ENUM"),
        ],
    },
    "PLACEMENT": {
        "pos": (31, -4),
        "attrs": [
            ("PK", "placement_id", "INT"),
            ("FK", "student_id", "INT"),
            ("FK", "offer_id", "INT"),
            ("", "is_active", "TINYINT(1)"),
        ],
    },
    "PLACEMENT_REPORT_CACHE": {
        "pos": (5, 44),
        "attrs": [
            ("PK", "cache_id", "INT"),
            ("FK", "branch_id", "INT"),
            ("", "batch_year", "SMALLINT"),
            ("", "placement_rate", "DECIMAL(5,2)"),
            ("", "avg_ctc", "DECIMAL(12,2)"),
        ],
    },
    "AUDIT_LOG": {
        "pos": (77, 4),
        "attrs": [
            ("PK", "audit_id", "BIGINT"),
            ("", "table_name", "VARCHAR(50)"),
            ("", "action_type", "VARCHAR(20)"),
            ("", "record_id", "INT"),
            ("", "details", "VARCHAR(255)"),
        ],
    },
}

# (parent, child, label, parent_card, parent_text, child_card, child_text)
RELATIONS = [
    ("APP_USER", "STUDENT", "profile", "1", "1", "1", "0..1"),
    ("APP_USER", "RECRUITER", "profile", "1", "1", "1", "0..1"),
    ("APP_USER", "PLACEMENT_OFFICER", "profile", "1", "1", "1", "0..1"),
    ("BRANCH", "STUDENT", "enrols", "1", "1", "N", "0..N"),
    ("STUDENT", "STUDENT_SKILL", "possesses", "1", "1", "N", "0..N"),
    ("SKILL", "STUDENT_SKILL", "tagged in", "1", "1", "N", "0..N"),
    ("COMPANY", "RECRUITER", "employs", "1", "1", "N", "0..N"),
    ("COMPANY", "JOB", "publishes", "1", "1", "N", "0..N"),
    ("RECRUITER", "JOB", "posts", "1", "1", "N", "0..N"),
    ("JOB", "JOB_SKILL", "requires", "1", "1", "N", "0..N"),
    ("SKILL", "JOB_SKILL", "required by", "1", "1", "N", "0..N"),
    ("STUDENT", "APPLICATION", "submits", "1", "1", "N", "0..N"),
    ("JOB", "APPLICATION", "receives", "1", "1", "N", "0..N"),
    ("APPLICATION", "INTERVIEW", "schedules", "1", "1", "N", "0..N"),
    ("APPLICATION", "OFFER", "receives", "1", "1", "1", "0..1"),
    ("OFFER", "PLACEMENT", "converts into", "1", "1", "1", "0..1"),
    ("STUDENT", "PLACEMENT", "gets placed via", "1", "1", "1", "0..1"),
    ("BRANCH", "PLACEMENT_REPORT_CACHE", "summarised in", "1", "1", "N", "0..N"),
]


def geometry(name: str) -> tuple[float, float, float, float]:
    """Return (cx, cy, width, height) for an entity box."""
    ent = ENTITIES[name]
    cx, cy = ent["pos"]
    return cx, cy, BOX_W, box_height(ent["attrs"])


def boundary(cx: float, cy: float, w: float, h: float,
             toward: tuple[float, float]) -> tuple[float, float]:
    """Point where the segment centre -> toward leaves the rectangle."""
    tx, ty = toward
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    scales = []
    if dx:
        scales.append((w / 2) / abs(dx))
    if dy:
        scales.append((h / 2) / abs(dy))
    t = min(scales)
    return cx + dx * t, cy + dy * t


def draw_box(ax, name: str) -> None:
    cx, cy, w, h = geometry(name)
    x0, y0 = cx - w / 2, cy - h / 2

    ax.add_patch(mpatches.FancyBboxPatch(
        (x0, y0), w, h,
        boxstyle="round,pad=0,rounding_size=0.9",
        linewidth=1.1, edgecolor=INK, facecolor="white", zorder=3,
    ))
    # header band
    header = mpatches.FancyBboxPatch(
        (x0, y0 + h - HEADER_H), w, HEADER_H,
        boxstyle="round,pad=0,rounding_size=0.9",
        linewidth=0, facecolor=TEAL, zorder=4,
    )
    ax.add_patch(header)
    ax.add_patch(mpatches.Rectangle(
        (x0, y0 + h - HEADER_H), w, HEADER_H / 2,
        linewidth=0, facecolor=TEAL, zorder=4,
    ))
    ax.text(cx, y0 + h - HEADER_H / 2 + 0.05, name,
            ha="center", va="center", fontsize=header_fontsize(name),
            fontweight="bold", color="white", zorder=5)

    y = y0 + h - HEADER_H - 1.3
    for tag, attr, dtype in ENTITIES[name]["attrs"]:
        y -= ROW_H
        color = {"PK": TEAL, "FK": AMBER, "UK": "#7C3AED"}.get(tag, SLATE)
        if tag:
            ax.text(x0 + 0.9, y, tag, ha="left", va="center",
                    fontsize=FS_TAG, fontweight="bold", color=color, zorder=5)
        ax.text(x0 + 3.6, y, attr, ha="left", va="center",
                fontsize=FS_ATTR, color=INK, zorder=5)
        ax.text(x0 + w - 0.9, y, dtype, ha="right", va="center",
                fontsize=FS_TYPE, color=SLATE, zorder=5)


def edge_tangent(cx: float, cy: float, w: float, h: float,
                 px: float, py: float) -> tuple[float, float]:
    """Unit vector along the rectangle side that (px, py) lies on."""
    if abs(px - (cx - w / 2)) < 1e-3 or abs(px - (cx + w / 2)) < 1e-3:
        return (0.0, 1.0)
    return (1.0, 0.0)


def draw_cardinality(ax, point: tuple[float, float], outward: tuple[float, float],
                     tangent: tuple[float, float], many: bool) -> None:
    """Crow's foot (many) or tick (one), drawn strictly outside the box.

    The three prongs converge on an apex outside the rectangle and land on
    the border itself, so no mark can ever bleed inside a table box.
    """
    length, spread = 1.9, 0.85
    apex = (point[0] + outward[0] * length, point[1] + outward[1] * length)
    if many:
        for k in (-1, 0, 1):
            anchor = (point[0] + tangent[0] * spread * k,
                      point[1] + tangent[1] * spread * k)
            ax.plot([apex[0], anchor[0]], [apex[1], anchor[1]], color=INK,
                    linewidth=1.0, zorder=2, solid_capstyle="round")
    else:
        mid = (point[0] + outward[0] * 1.1, point[1] + outward[1] * 1.1)
        ax.plot([mid[0] + tangent[0] * 0.9, mid[0] - tangent[0] * 0.9],
                [mid[1] + tangent[1] * 0.9, mid[1] - tangent[1] * 0.9],
                color=INK, linewidth=1.2, zorder=2)


def draw_relation(ax, rel) -> None:
    parent, child, label, p_card, p_text, c_card, c_text = rel
    pcx, pcy, pw, ph = geometry(parent)
    ccx, ccy, cw, ch = geometry(child)

    p = boundary(pcx, pcy, pw, ph, (ccx, ccy))
    q = boundary(ccx, ccy, cw, ch, (pcx, pcy))

    ax.plot([p[0], q[0]], [p[1], q[1]], color=LINE,
            linewidth=1.1, zorder=1)

    dx, dy = q[0] - p[0], q[1] - p[1]
    norm = math.hypot(dx, dy) or 1.0
    d = (dx / norm, dy / norm)

    draw_cardinality(ax, p, d, edge_tangent(pcx, pcy, pw, ph, *p),
                     many=(p_card == "N"))
    draw_cardinality(ax, q, (-d[0], -d[1]),
                     edge_tangent(ccx, ccy, cw, ch, *q),
                     many=(c_card == "N"))

    # cardinality labels sit beyond the connector mark and are nudged off the
    # line, so they never land on the crow's-foot apex or the relationship text
    seg = math.hypot(q[0] - p[0], q[1] - p[1]) or 1.0
    off = min(5.8, max(1.9, 0.30 * seg))
    side = 1.0 if -d[1] >= 0 else -1.0
    # short connectors have no room for a sideways nudge
    nudge = 0.95 if seg >= 8.0 else 0.0
    nx, ny = -d[1] * side * nudge, d[0] * side * nudge

    ax.text(p[0] + d[0] * off + nx, p[1] + d[1] * off + ny, p_text,
            ha="center", va="center", fontsize=FS_CARD, color=SLATE,
            style="italic", zorder=6)
    ax.text(q[0] - d[0] * off + nx, q[1] - d[1] * off + ny, c_text,
            ha="center", va="center", fontsize=FS_CARD, color=SLATE,
            style="italic", zorder=6)

    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    if seg < 12.0:
        # tight gap: push the label to the side away from the cardinality text
        # so the two never cover each other
        mx += -d[1] * (-side) * 1.6
        my += d[0] * (-side) * 1.6
    ax.text(mx, my, label, ha="center", va="center", fontsize=FS_LABEL,
            color=INK, zorder=6,
            bbox=dict(boxstyle="round,pad=0.22", facecolor="white",
                      edgecolor="none", alpha=0.95))


def main() -> None:
    fig, ax = plt.subplots(figsize=(17.5, 14.2), dpi=170)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    ax.set_xlim(-5.5, 124.5)
    ax.set_ylim(-14.5, 99.5)
    ax.set_aspect("equal")
    ax.axis("off")

    for rel in RELATIONS:
        draw_relation(ax, rel)
    for name in ENTITIES:
        draw_box(ax, name)

    # ---- title and legend
    ax.text(-2, 97.2, "CampusHire — Entity Relationship Diagram",
            ha="left", va="center", fontsize=FS_TITLE, fontweight="bold",
            color=INK)
    ax.text(-2, 94.9,
            "College Placement Portal · MySQL 8 · 16 tables · 18 foreign keys · no views",
            ha="left", va="center", fontsize=FS_SUBTITLE, color=SLATE)

    ly = -12.8
    ax.text(-2, ly, "PK primary key", fontsize=FS_LEGEND, color=TEAL,
            fontweight="bold", ha="left", va="center")
    ax.text(12, ly, "FK foreign key", fontsize=FS_LEGEND, color=AMBER,
            fontweight="bold", ha="left", va="center")
    ax.text(26, ly, "UK unique key", fontsize=FS_LEGEND, color="#7C3AED",
            fontweight="bold", ha="left", va="center")

    # sample connectors: one (tick) and many (crow's foot)
    ax.plot([42, 47], [ly, ly], color=LINE, linewidth=1.1)
    ax.plot([46.2, 46.2], [ly - 1.0, ly + 1.0], color=INK, linewidth=1.3)
    ax.text(48, ly, "one", fontsize=FS_LEGEND, color=INK, ha="left", va="center")

    ax.plot([57, 62], [ly, ly], color=LINE, linewidth=1.1)
    for dy in (-1.15, 0.0, 1.15):
        ax.plot([62, 64.4], [ly, ly + dy], color=INK, linewidth=1.1)
    ax.text(65.4, ly, "many", fontsize=FS_LEGEND, color=INK, ha="left", va="center")

    fig.tight_layout(pad=0.4)
    fig.savefig(OUTPUT, format="jpg", dpi=170,
                facecolor=fig.get_facecolor(), bbox_inches="tight",
                pil_kwargs={"quality": 93, "optimize": True})
    plt.close(fig)
    print(f"written: {OUTPUT}")


if __name__ == "__main__":
    main()
