from __future__ import annotations

import html
import io
import json
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    XPreformatted,
)


def _display_time(value: str | None) -> str:
    if not value:
        return "Unknown time"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%d %b %Y, %H:%M UTC")
    except ValueError:
        return value


def _inline(nodes: list[dict] | None) -> str:
    parts: list[str] = []
    for node in nodes or []:
        node_type = node.get("type")
        if node_type == "hardBreak":
            parts.append("<br/>")
            continue
        if node_type != "text":
            parts.append(_inline(node.get("content")))
            continue
        value = html.escape(str(node.get("text", "")))
        for mark in node.get("marks", []):
            mark_type = mark.get("type")
            if mark_type == "bold":
                value = f"<b>{value}</b>"
            elif mark_type == "italic":
                value = f"<i>{value}</i>"
            elif mark_type == "underline":
                value = f"<u>{value}</u>"
            elif mark_type == "strike":
                value = f"<strike>{value}</strike>"
            elif mark_type == "code":
                value = f'<font name="Courier" backColor="#f1f5f9">{value}</font>'
            elif mark_type == "link":
                href = html.escape(str(mark.get("attrs", {}).get("href", "")), quote=True)
                if href.startswith(("http://", "https://", "mailto:")):
                    value = f'<link href="{href}" color="#4f46e5">{value}</link>'
        parts.append(value)
    return "".join(parts)


def _plain(nodes: list[dict] | None) -> str:
    values: list[str] = []
    for node in nodes or []:
        if node.get("type") == "text":
            values.append(str(node.get("text", "")))
        elif node.get("type") == "hardBreak":
            values.append("\n")
        else:
            values.append(_plain(node.get("content")))
    return "".join(values)


def _list_item(node: dict, styles: dict) -> ListItem:
    content = _flowables(node.get("content", []), styles)
    return ListItem(content or [Paragraph(" ", styles["BodyText"])], leftIndent=12)


def _table(node: dict, styles: dict) -> Table:
    rows = []
    for row in node.get("content", []):
        cells = []
        for cell in row.get("content", []):
            body = []
            for child in cell.get("content", []):
                if child.get("type") == "paragraph":
                    body.append(Paragraph(_inline(child.get("content")) or " ", styles["TableCell"]))
                else:
                    text = _plain([child]).strip()
                    if text:
                        body.append(Paragraph(html.escape(text), styles["TableCell"]))
            cells.append(body or Paragraph(" ", styles["TableCell"]))
        if cells:
            rows.append(cells)
    if not rows:
        rows = [[Paragraph(" ", styles["TableCell"])]]
    table = Table(rows, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8dee9")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _flowables(nodes: list[dict], styles: dict) -> list:
    story = []
    for node in nodes:
        node_type = node.get("type", "paragraph")
        if node_type == "paragraph":
            value = _inline(node.get("content"))
            story.append(Paragraph(value or " ", styles["BodyText"]))
        elif node_type == "heading":
            level = min(max(int(node.get("attrs", {}).get("level", 2)), 1), 3)
            story.append(Paragraph(_inline(node.get("content")) or " ", styles[f"Heading{level}"]))
        elif node_type in ("bulletList", "orderedList"):
            items = [_list_item(item, styles) for item in node.get("content", [])]
            if items:
                story.append(ListFlowable(
                    items,
                    bulletType="bullet" if node_type == "bulletList" else "1",
                    start="circle" if node_type == "bulletList" else "1",
                    leftIndent=18,
                    bulletFontName="Helvetica",
                ))
        elif node_type == "blockquote":
            value = "<br/>".join(
                _inline(child.get("content"))
                for child in node.get("content", [])
                if child.get("type") == "paragraph"
            )
            story.append(Paragraph(value or " ", styles["Quote"]))
        elif node_type == "codeBlock":
            story.append(XPreformatted(_plain(node.get("content")), styles["CodeBlock"]))
        elif node_type == "table":
            story.append(_table(node, styles))
        elif node_type == "horizontalRule":
            story.append(HRFlowable(width="100%", thickness=0.7, color=colors.HexColor("#d8dee9")))
        elif node_type == "image":
            alt = node.get("attrs", {}).get("alt") or "Image"
            story.append(Paragraph(f"[{html.escape(str(alt))}]", styles["Caption"]))
        elif node_type == "pageBreak":
            story.append(PageBreak())
        else:
            value = _plain(node.get("content")).strip()
            if value:
                story.append(Paragraph(html.escape(value), styles["BodyText"]))
        story.append(Spacer(1, 2.5 * mm))
    return story


def page_pdf(page: dict) -> bytes:
    try:
        document = json.loads(page.get("content_json") or "{}")
    except (TypeError, json.JSONDecodeError):
        document = {"type": "doc", "content": []}

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#667085"),
        spaceAfter=7 * mm,
    ))
    styles.add(ParagraphStyle(
        "Quote",
        parent=styles["BodyText"],
        leftIndent=10,
        borderColor=colors.HexColor("#4f46e5"),
        borderWidth=0,
        borderPadding=6,
        textColor=colors.HexColor("#475467"),
        italic=True,
    ))
    styles.add(ParagraphStyle(
        "CodeBlock",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8,
        leading=10,
        backColor=colors.HexColor("#f8fafc"),
        borderPadding=7,
    ))
    styles.add(ParagraphStyle("TableCell", parent=styles["BodyText"], fontSize=8.5, leading=11))
    styles["Title"].textColor = colors.HexColor("#172033")
    styles["Title"].spaceAfter = 4 * mm
    styles["BodyText"].fontSize = 10.5
    styles["BodyText"].leading = 15

    output = io.BytesIO()
    pdf = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=19 * mm,
        bottomMargin=18 * mm,
        title=page.get("title") or "FastWiki page",
        author=page.get("author_name") or page.get("created_by") or "FastWiki",
    )

    published = (
        f"Published {_display_time(page.get('published_at'))} · "
        f"Version {page.get('version', 1)} · "
        f"{page.get('author_name') or page.get('created_by') or 'Unknown author'}"
        if page.get("status") == "published"
        else f"Draft · Version {page.get('version', 1)} · {page.get('author_name') or page.get('created_by') or 'Unknown author'}"
    )
    story = [
        Paragraph(html.escape(page.get("title") or "Untitled page"), styles["Title"]),
        Paragraph(html.escape(published), styles["Meta"]),
        *_flowables(document.get("content", []), styles),
    ]

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#98a2b3"))
        canvas.drawString(20 * mm, 10 * mm, "FastWiki")
        canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    pdf.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
