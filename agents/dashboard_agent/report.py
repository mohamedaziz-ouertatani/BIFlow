"""PDF snapshot generation from the dashboard layout.

Styled to echo the Audit Console design system (DESIGN.md): ink/muted-ink
neutrals, a single signal-cyan accent, hairline dividers instead of boxes,
and a mono/sans split where measured values (KPI numbers, trend points,
breakdown values) render in Courier and everything else in Helvetica.
"""

import io
from datetime import datetime, timezone
from typing import Any

from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

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


def _humanize(key: str) -> str:
    """Turns a snake_case layout key into a title-case section heading."""
    return key.replace("_", " ").title()


# Renders the dashboard layout (KPIs, trends, breakdowns, insights) as a
# multi-page PDF snapshot styled to match the live Audit Console dashboard.
def build_pdf(layout: dict[str, Any]) -> bytes:
    """Builds a PDF snapshot of the dashboard layout and returns its raw bytes.

    pageCompression=0 keeps the content stream uncompressed so tests (and
    anyone grepping the file) can find text directly in the raw bytes.
    """
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=LETTER, pageCompression=0)
    y = PAGE_HEIGHT - MARGIN
    page_number = 1

    def draw_footer() -> None:
        nonlocal page_number
        pdf.setStrokeColor(HAIRLINE)
        pdf.setLineWidth(0.75)
        pdf.line(MARGIN, MARGIN - 12, PAGE_WIDTH - MARGIN, MARGIN - 12)
        pdf.setFont("Courier", 8)
        pdf.setFillColor(INK_MUTED)
        pdf.drawString(MARGIN, MARGIN - 24, "BIFlow Audit Console")
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
        if y < MARGIN + FOOTER_RESERVE:
            draw_footer()
            pdf.showPage()
            y = PAGE_HEIGHT - MARGIN
        pdf.setFont(font, size)
        pdf.setFillColor(color)
        pdf.drawString(MARGIN + indent, y, text)
        y -= LINE_HEIGHT

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
    write_line("BIFlow Audit Console Report", font="Helvetica-Bold", size=18, color=INK)
    domain = layout.get("business_domain")
    if domain:
        write_line(f"Domain: {domain}", font="Courier-Bold", size=9, color=SIGNAL_CYAN)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    write_line(f"Generated {timestamp}", font="Courier", size=8, color=INK_MUTED)
    y -= LINE_HEIGHT * 0.3
    draw_rule(HAIRLINE_STRONG)
    y -= LINE_HEIGHT * 0.2

    # --- KPIs ---------------------------------------------------------------
    kpi_cards = layout.get("kpi_cards", [])
    if kpi_cards:
        write_section_label("KPIs")
        for card in kpi_cards:
            write_line(f"{card['label']}", font="Helvetica-Bold", size=11, color=INK)
            write_line(f"{card['value']}", font="Courier-Bold", size=13, color=SIGNAL_CYAN, indent=8)

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
        write_section_label("Trends")
        for metric, series in monthly_trends.items():
            write_line(_humanize(metric), font="Helvetica-Bold", size=10, color=INK)
            points_text = "   ".join(f"{point['month']}: {point['value']}" for point in series)
            for line in wrap_text(points_text, "Courier", 9, CONTENT_WIDTH - 8):
                write_line(line, font="Courier", size=9, color=INK_MUTED, indent=8)
            y -= LINE_HEIGHT * 0.2

    # --- Breakdowns -------------------------------------------------------
    category_breakdowns = layout.get("category_breakdowns", {})
    if category_breakdowns:
        write_section_label("Breakdowns")
        for key, points in category_breakdowns.items():
            write_line(_humanize(key), font="Helvetica-Bold", size=10, color=INK)
            for point in points:
                write_line(
                    f"{point['label']}: {point['value']}",
                    font="Courier",
                    size=9,
                    color=INK_MUTED,
                    indent=8,
                )
            y -= LINE_HEIGHT * 0.2

    # --- Insights -----------------------------------------------------------
    insights = layout.get("insights", [])
    if insights:
        write_section_label("Insights")
        for insight in insights:
            severity = insight.get("severity", "info")
            mark = SEVERITY_MARKS.get(severity, "[i]")
            color = SEVERITY_COLORS.get(severity, SIGNAL_CYAN)
            write_line(f"{mark} {insight['title']}", font="Helvetica-Bold", size=10, color=color)
            for line in wrap_text(insight["description"], "Helvetica", 9, CONTENT_WIDTH - 8):
                write_line(line, font="Helvetica", size=9, color=INK_MUTED, indent=8)
            y -= LINE_HEIGHT * 0.25
            draw_rule(HAIRLINE)

    draw_footer()
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
