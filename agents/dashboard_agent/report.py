"""PDF snapshot generation from the dashboard layout."""

import io
from typing import Any

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

PAGE_WIDTH, PAGE_HEIGHT = LETTER
MARGIN = 50
LINE_HEIGHT = 16


# Renders the dashboard layout (KPIs, comparisons, insights) as a one-page PDF snapshot.
def build_pdf(layout: dict[str, Any]) -> bytes:
    """Builds a PDF snapshot of the dashboard layout and returns its raw bytes.

    pageCompression=0 keeps the content stream uncompressed so tests (and
    anyone grepping the file) can find text directly in the raw bytes.
    """
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=LETTER, pageCompression=0)
    y = PAGE_HEIGHT - MARGIN

    def write_line(text: str, font: str = "Helvetica", size: int = 11) -> None:
        nonlocal y
        if y < MARGIN:
            pdf.showPage()
            y = PAGE_HEIGHT - MARGIN
        pdf.setFont(font, size)
        pdf.drawString(MARGIN, y, text)
        y -= LINE_HEIGHT

    title = "BIFlow Dashboard Report"
    domain = layout.get("business_domain")
    if domain:
        title += f" ({domain})"
    write_line(title, font="Helvetica-Bold", size=16)
    y -= LINE_HEIGHT / 2

    kpi_cards = layout.get("kpi_cards", [])
    if kpi_cards:
        write_line("KPIs", font="Helvetica-Bold", size=13)
        for card in kpi_cards:
            write_line(f"{card['label']}: {card['value']}")
            comparison = card.get("comparison")
            if comparison:
                write_line(
                    f"  {comparison['direction']} {comparison['pct_change']:+.1f}% "
                    f"vs {comparison['previous_month']}",
                    size=10,
                )
        y -= LINE_HEIGHT / 2

    insights = layout.get("insights", [])
    if insights:
        write_line("Insights", font="Helvetica-Bold", size=13)
        for insight in insights:
            write_line(f"[{insight['severity']}] {insight['title']}")
            write_line(f"  {insight['description']}", size=10)

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
