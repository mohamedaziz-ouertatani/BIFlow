"""PDF snapshot generation from the dashboard layout.

Mirrors the dashboard's Telemetry Wall (DESIGN.md) on paper: a severity-sorted
Findings log first, then KPI telemetry sorted by attention (the highest
severity among insights that reference a KPI), then trends and breakdowns.
Print styling keeps the Mission Control conventions: ink/muted-ink neutrals,
one cyan accent, hairline dividers instead of boxes, amber for warnings, red
for critical or decreasing, and a mono/sans split where measured values
(KPI numbers, trend points, breakdown values) render in Courier and
everything else in Helvetica.
"""

import io
from datetime import datetime, timezone
from typing import Any

from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from shared.metrics import PERCENT_METRICS, format_percent

PAGE_WIDTH, PAGE_HEIGHT = LETTER
MARGIN = 50
LINE_HEIGHT = 16
FOOTER_RESERVE = 46
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN

INK = Color(16 / 255, 20 / 255, 26 / 255)
INK_MUTED = Color(92 / 255, 100 / 255, 112 / 255)
HAIRLINE = Color(0.84, 0.84, 0.86)
HAIRLINE_STRONG = Color(0.72, 0.72, 0.75)
SIGNAL_CYAN = Color(8 / 255, 145 / 255, 168 / 255)
STATUS_SUCCESS = Color(26 / 255, 122 / 255, 76 / 255)
STATUS_WARNING = Color(163 / 255, 105 / 255, 10 / 255)
STATUS_DANGER = Color(194 / 255, 58 / 255, 58 / 255)

SEVERITY_MARKS = {"info": "[i]", "warning": "[!]", "critical": "[x]"}
SEVERITY_COLORS = {"info": SIGNAL_CYAN, "warning": STATUS_WARNING, "critical": STATUS_DANGER}
DIRECTION_COLORS = {"increasing": STATUS_SUCCESS, "decreasing": STATUS_DANGER}
DIRECTION_MARKS = {"increasing": "^", "decreasing": "v"}
ATTENTION_RANK = {"critical": 3, "warning": 2, "info": 1, "none": 0}


def _format_value(metric: str, value: Any) -> str:
    """Formats a metric value for the PDF: rate KPIs as percentages, everything else as-is."""
    if metric in PERCENT_METRICS and isinstance(value, (int, float)):
        return format_percent(value)
    return f"{value}"


def _humanize(key: str) -> str:
    """Turns a snake_case layout key into a title-case section heading."""
    return key.replace("_", " ").title()


def _severity_of(insight: dict[str, Any]) -> str:
    """Collapses any unknown severity to "info", matching the dashboard."""
    severity = insight.get("severity", "info")
    return severity if severity in ("critical", "warning") else "info"


def _attention_for(kpi_name: str, insights: list[dict[str, Any]]) -> tuple[str, int]:
    """Returns (highest severity, finding count) among insights referencing a KPI."""
    level, count = "none", 0
    for insight in insights:
        if insight.get("related_kpi") != kpi_name:
            continue
        count += 1
        severity = _severity_of(insight)
        if ATTENTION_RANK[severity] > ATTENTION_RANK[level]:
            level = severity
    return level, count


def _findings_text(level: str, count: int) -> str:
    """Never renders "no findings" as healthy, same as the dashboard tiles."""
    return "No findings" if count == 0 else f"{count} {level}"


# Renders the dashboard layout (findings, KPI telemetry, trends, breakdowns) as
# a multi-page PDF snapshot mirroring the live Mission Control dashboard.
def build_pdf(layout: dict[str, Any]) -> bytes:
    """Builds a PDF snapshot of the dashboard layout and returns its raw bytes.

    pageCompression=0 keeps the content stream uncompressed so tests (and
    anyone grepping the file) can find text directly in the raw bytes.
    """
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=LETTER, pageCompression=0)
    # ReportLab's origin is the BOTTOM-left corner, so `y` starts at the top margin and decreases
    # as lines are written. The helpers below are closures that share `pdf`, `y` and `page_number`;
    # `nonlocal` lets them update those shared values.
    y = PAGE_HEIGHT - MARGIN
    page_number = 1

    def draw_footer() -> None:
        nonlocal page_number
        pdf.setStrokeColor(HAIRLINE)
        pdf.setLineWidth(0.75)
        pdf.line(MARGIN, MARGIN - 12, PAGE_WIDTH - MARGIN, MARGIN - 12)
        pdf.setFont("Courier", 8)
        pdf.setFillColor(INK_MUTED)
        pdf.drawString(MARGIN, MARGIN - 24, "BIFlow Mission Control")
        pdf.drawRightString(PAGE_WIDTH - MARGIN, MARGIN - 24, f"Page {page_number}")
        page_number += 1

    def write_line(
        text: str,
        font: str = "Helvetica",
        size: int = 11,
        color: Color = INK,
        indent: float = 0,
    ) -> None:
        nonlocal y
        # Out of room: stamp the footer, start a new page and reset the cursor to the top.
        if y < MARGIN + FOOTER_RESERVE:
            draw_footer()
            pdf.showPage()
            y = PAGE_HEIGHT - MARGIN
        pdf.setFont(font, size)
        pdf.setFillColor(color)
        pdf.drawString(MARGIN + indent, y, text)
        y -= LINE_HEIGHT

    # Greedy word wrap: add words while the line still fits in max_width (measured in the actual font);
    # `or not current` guarantees a single over-long word still gets its own line.
    def wrap_text(text: str, font: str, size: int, max_width: float) -> list[str]:
        words = str(text).split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if pdf.stringWidth(candidate, font, size) <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def draw_rule(color: Color, dashed: bool = False, indent: float = 0) -> None:
        nonlocal y
        # saveState/restoreState so the dash style set here doesn't leak into later drawing.
        pdf.saveState()
        pdf.setStrokeColor(color)
        pdf.setLineWidth(0.75)
        if dashed:
            pdf.setDash(2, 2)
        pdf.line(MARGIN + indent, y, PAGE_WIDTH - MARGIN, y)
        pdf.restoreState()
        y -= LINE_HEIGHT * 0.55

    def write_section_label(text: str) -> None:
        nonlocal y
        y -= LINE_HEIGHT * 0.3
        write_line(f"§ {text}", font="Courier-Bold", size=10, color=SIGNAL_CYAN)
        draw_rule(HAIRLINE)

    # --- Header -----------------------------------------------------------
    write_line("BIFlow Mission Control Report", font="Helvetica-Bold", size=18, color=INK)
    domain = layout.get("business_domain")
    if domain:
        write_line(f"Domain: {domain}", font="Courier-Bold", size=9, color=SIGNAL_CYAN)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    write_line(f"Generated {timestamp}", font="Courier", size=8, color=INK_MUTED)
    y -= LINE_HEIGHT * 0.3
    draw_rule(HAIRLINE_STRONG)
    y -= LINE_HEIGHT * 0.2

    insights = layout.get("insights", [])
    critical_count = sum(1 for i in insights if _severity_of(i) == "critical")
    warning_count = sum(1 for i in insights if _severity_of(i) == "warning")

    # --- Findings -----------------------------------------------------------
    if insights:
        write_section_label("Findings")
        summary = " · ".join(
            part
            for part in (
                f"{critical_count} critical" if critical_count else "",
                f"{warning_count} warning" if warning_count else "",
            )
            if part
        )
        write_line(summary or f"{len(insights)} logged", font="Courier", size=9, color=INK_MUTED)
        ranked = sorted(insights, key=lambda i: -ATTENTION_RANK[_severity_of(i)])
        for insight in ranked:
            severity = _severity_of(insight)
            mark = SEVERITY_MARKS[severity]
            color = SEVERITY_COLORS[severity]
            write_line(f"{mark} {insight['title']}", font="Helvetica-Bold", size=10, color=color)
            for line in wrap_text(insight["description"], "Helvetica", 9, CONTENT_WIDTH - 8):
                write_line(line, font="Helvetica", size=9, color=INK_MUTED, indent=8)
            related = insight.get("related_kpi")
            if related:
                month = insight.get("month")
                ref = f"KPI: {related}" + (f" · {month}" if month else "")
                write_line(ref, font="Courier", size=8, color=INK_MUTED, indent=8)
            y -= LINE_HEIGHT * 0.25
            draw_rule(HAIRLINE)

    # --- KPI telemetry ------------------------------------------------------
    kpi_cards = layout.get("kpi_cards", [])
    if kpi_cards:
        write_section_label("KPI telemetry")
        write_line("sorted by attention", font="Courier", size=8, color=INK_MUTED)
        # Sort by attention (highest severity first); the original index is the tie-breaker,
        # and it also gives each KPI a stable KPI·NN code regardless of the sorted order.
        wall = sorted(
            (
                (index, card, *_attention_for(card["name"], insights))
                for index, card in enumerate(kpi_cards)
            ),
            key=lambda item: (-ATTENTION_RANK[item[2]], item[0]),
        )
        for index, card, level, count in wall:
            code = f"KPI·{index + 1:02d}"
            findings_color = SEVERITY_COLORS.get(level, INK_MUTED)
            write_line(
                f"{code}  {_findings_text(level, count)}",
                font="Courier-Bold",
                size=8,
                color=findings_color,
            )
            write_line(f"{card['label']}", font="Helvetica-Bold", size=11, color=INK)
            write_line(_format_value(card["name"], card["value"]), font="Courier-Bold", size=13, color=SIGNAL_CYAN, indent=8)

            comparison = card.get("comparison")
            if comparison:
                direction = comparison["direction"]
                mark = DIRECTION_MARKS.get(direction, "-")
                color = DIRECTION_COLORS.get(direction, INK_MUTED)
                write_line(
                    f"{mark} {direction} {comparison['pct_change']:+.1f}% "
                    f"vs {comparison['previous_month']}",
                    font="Courier",
                    size=9,
                    color=color,
                    indent=8,
                )

            explanation = card.get("explanation")
            if explanation:
                draw_rule(HAIRLINE_STRONG, dashed=True, indent=8)
                write_line("FORMULA", font="Courier-Bold", size=8, color=SIGNAL_CYAN, indent=8)
                for line in wrap_text(explanation, "Courier-Oblique", 9, CONTENT_WIDTH - 8):
                    write_line(line, font="Courier-Oblique", size=9, color=INK_MUTED, indent=8)
                draw_rule(HAIRLINE_STRONG, dashed=True, indent=8)

            y -= LINE_HEIGHT * 0.25
            draw_rule(HAIRLINE)

    # --- Trends ---------------------------------------------------------------
    monthly_trends = layout.get("monthly_trends", {})
    if monthly_trends:
        write_section_label("Monthly trends")
        for metric, series in monthly_trends.items():
            write_line(_humanize(metric), font="Helvetica-Bold", size=10, color=INK)
            points_text = "   ".join(f"{point['month']}: {_format_value(metric, point['value'])}" for point in series)
            for line in wrap_text(points_text, "Courier", 9, CONTENT_WIDTH - 8):
                write_line(line, font="Courier", size=9, color=INK_MUTED, indent=8)
            y -= LINE_HEIGHT * 0.2

    # --- Breakdowns -------------------------------------------------------
    category_breakdowns = layout.get("category_breakdowns", {})
    if category_breakdowns:
        write_section_label("Category breakdowns")
        for key, points in category_breakdowns.items():
            # Breakdown keys look like '<kpi>_by_<dimension>': take what's before the last '_by_' to
            # recover the KPI name (used to format values, e.g. rates as percentages).
            metric = key.rpartition("_by_")[0] or key
            write_line(_humanize(key), font="Helvetica-Bold", size=10, color=INK)
            for point in points:
                write_line(
                    f"{point['label']}: {_format_value(metric, point['value'])}",
                    font="Courier",
                    size=9,
                    color=INK_MUTED,
                    indent=8,
                )
            y -= LINE_HEIGHT * 0.2

    draw_footer()
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
