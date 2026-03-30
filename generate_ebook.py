"""
Generate PDF ebook from micro:bit 58 activities
Extracts data from index.html and creates a professional workbook
"""
import re, json, textwrap
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                 Table, TableStyle, Preformatted, KeepTogether)
from reportlab.pdfgen import canvas

# ── Read and parse index.html ──
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Extract JS between <script> and </script>
js_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
js = js_match.group(1) if js_match else ""

# Extract activity data using mk() calls
activities = []
mk_pattern = re.compile(
    r'mk\((\d+),"([^"]+)","(\w+)",\{([^}]+)\},\s*"([^"]+)",\s*\[([^\]]+)\],\s*"([^"]+)",\s*\[([^\]]*)\],\s*`([^`]*)`\s*,\s*`([^`]*)`\s*,\s*\[([^\]]*)\]\s*\)',
    re.DOTALL
)

for m in mk_pattern.finditer(js):
    aid = int(m.group(1))
    title = m.group(2)
    part = m.group(3)
    meta_str = m.group(4)
    goal = m.group(5)
    needs_str = m.group(6)
    tip = m.group(7)
    blocks_str = m.group(8)
    code_js = m.group(9).strip()
    code_py = m.group(10).strip()
    chal_str = m.group(11)

    # Parse meta
    diff_m = re.search(r'difficulty:(\d)', meta_str)
    time_m = re.search(r'time:"([^"]+)"', meta_str)
    v2 = "v2:true" in meta_str
    ia = "ia:true" in meta_str

    difficulty = int(diff_m.group(1)) if diff_m else 1
    time_est = time_m.group(1) if time_m else "—"

    # Parse needs
    needs = re.findall(r'"([^"]+)"', needs_str)

    # Parse blocks
    blocks = re.findall(r'"([^"]+)"', blocks_str)

    # Parse challenges
    challenges = []
    for cm_match in re.finditer(r'\{t:"([^"]+)",d:(\d)\}', chal_str):
        challenges.append({"t": cm_match.group(1), "d": int(cm_match.group(2))})

    activities.append({
        "id": aid, "title": title, "part": part, "difficulty": difficulty,
        "time": time_est, "v2": v2, "ia": ia, "goal": goal, "needs": needs,
        "tip": tip, "blocks": blocks, "codeJS": code_js, "codePY": code_py,
        "challenges": challenges
    })

activities.sort(key=lambda a: a["id"])
print(f"Extracted {len(activities)} activities")

# ── Colors ──
BLUE = HexColor("#1E90FF")
DARK_BG = HexColor("#0a0f1e")
ACCENT = HexColor("#3b82f6")
GREEN = HexColor("#40BF4A")
ORANGE = HexColor("#f97316")
RED = HexColor("#DC143C")
PURPLE = HexColor("#7B48A0")
TEAL = HexColor("#00A4A6")
DARK_PANEL = HexColor("#1a2332")
LIGHT_TEXT = HexColor("#d0ddf0")
MUTED = HexColor("#8899aa")

# ── Styles ──
styles = getSampleStyleSheet()

styles.add(ParagraphStyle('BookTitle', parent=styles['Title'], fontSize=28, textColor=ACCENT,
                           spaceAfter=10, alignment=TA_CENTER, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle('BookSub', parent=styles['Normal'], fontSize=14, textColor=MUTED,
                           spaceAfter=30, alignment=TA_CENTER))
styles.add(ParagraphStyle('ActTitle', parent=styles['Heading1'], fontSize=16, textColor=ACCENT,
                           spaceBefore=0, spaceAfter=6, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle('SectionHead', parent=styles['Heading2'], fontSize=11, textColor=BLUE,
                           spaceBefore=10, spaceAfter=4, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle('Body', parent=styles['Normal'], fontSize=9, textColor=black,
                           spaceAfter=4, leading=13))
styles.add(ParagraphStyle('CodeStyle', parent=styles['Normal'], fontSize=8, fontName='Courier',
                           textColor=HexColor("#333333"), spaceAfter=4, leading=11,
                           leftIndent=10, backColor=HexColor("#f0f0f0")))
styles.add(ParagraphStyle('TipStyle', parent=styles['Normal'], fontSize=9, textColor=HexColor("#b8860b"),
                           spaceAfter=6, leading=12, leftIndent=15,
                           borderColor=HexColor("#ffd700"), borderWidth=1, borderPadding=5))
styles.add(ParagraphStyle('ChalStyle', parent=styles['Normal'], fontSize=9, textColor=HexColor("#444"),
                           spaceAfter=3, leading=12, leftIndent=15))
styles.add(ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=9, textColor=MUTED,
                           spaceAfter=8))
styles.add(ParagraphStyle('TOCEntry', parent=styles['Normal'], fontSize=10, textColor=black,
                           spaceAfter=3, leading=14))
styles.add(ParagraphStyle('TOCHead', parent=styles['Heading2'], fontSize=13, textColor=ACCENT,
                           spaceBefore=12, spaceAfter=6))
styles.add(ParagraphStyle('BlockChip', parent=styles['Normal'], fontSize=8, textColor=white))

# ── Helper ──
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def diff_stars(d):
    return "★" * d + "☆" * (3-d)

def diff_label(d):
    return {1:"Debutant",2:"Intermediaire",3:"Avance"}.get(d,"")

# ── Build PDF ──
output_path = "ebook-microbit-58-activities.pdf"
doc = SimpleDocTemplate(output_path, pagesize=A4,
                        topMargin=2*cm, bottomMargin=2*cm,
                        leftMargin=2*cm, rightMargin=2*cm)

story = []

# ── Cover Page ──
story.append(Spacer(1, 4*cm))
story.append(Paragraph("Micro:bit", styles['BookTitle']))
story.append(Paragraph("58 Activites Pratiques", styles['BookTitle']))
story.append(Spacer(1, 1*cm))
story.append(Paragraph("Du clignotement LED aux robots IA", styles['BookSub']))
story.append(Paragraph("Blocs + JavaScript + Python", styles['BookSub']))
story.append(Spacer(1, 2*cm))
story.append(Paragraph("Workshop DIY — abourdim", styles['BookSub']))
story.append(PageBreak())

# ── Table of Contents ──
story.append(Paragraph("Table des matieres", styles['BookTitle']))
story.append(Spacer(1, 0.5*cm))

# Simple section
current_part = ""
for a in activities:
    if a["part"] != current_part:
        current_part = a["part"]
        label = "SIMPLE (1-22)" if current_part == "simple" else "AVANCE (23-58)"
        story.append(Paragraph(f"<b>{label}</b>", styles['TOCHead']))

    tags = f"{diff_stars(a['difficulty'])} | {a['time']}"
    if a["v2"]: tags += " | V2"
    if a["ia"]: tags += " | IA"
    story.append(Paragraph(
        f"<b>#{a['id']}</b> — {esc(a['title'])}  <font color='#888888' size='8'>{tags}</font>",
        styles['TOCEntry']
    ))

story.append(PageBreak())

# ── Activity Pages ──
for a in activities:
    elements = []

    # Header
    tags = f"{diff_stars(a['difficulty'])} {diff_label(a['difficulty'])} | {a['time']}"
    if a["v2"]: tags += " | V2"
    if a["ia"]: tags += " | IA"

    elements.append(Paragraph(f"Activite #{a['id']}", styles['MetaStyle']))
    elements.append(Paragraph(esc(a['title']), styles['ActTitle']))
    elements.append(Paragraph(tags, styles['MetaStyle']))
    elements.append(Spacer(1, 4*mm))

    # Goal
    elements.append(Paragraph("🎯 Objectif", styles['SectionHead']))
    elements.append(Paragraph(esc(a['goal']), styles['Body']))

    # Needs
    elements.append(Paragraph("🧰 Materiel", styles['SectionHead']))
    needs_text = " • ".join(a['needs'])
    elements.append(Paragraph(esc(needs_text), styles['Body']))

    # Blocks / Steps
    if a['blocks']:
        elements.append(Paragraph("📋 Etapes (Blocs)", styles['SectionHead']))
        for i, b in enumerate(a['blocks']):
            elements.append(Paragraph(f"<b>{i+1}.</b> {esc(b)}", styles['Body']))

    # Tip
    elements.append(Paragraph(f"💡 {esc(a['tip'])}", styles['TipStyle']))

    # JavaScript Code
    elements.append(Paragraph("💻 JavaScript", styles['SectionHead']))
    # Wrap long lines
    code_lines = a['codeJS'].split('\n')
    code_text = '\n'.join(line[:90] for line in code_lines[:20])
    if len(code_lines) > 20: code_text += "\n// ..."
    elements.append(Preformatted(code_text, styles['CodeStyle']))

    # Python Code
    elements.append(Paragraph("🐍 Python", styles['SectionHead']))
    code_lines = a['codePY'].split('\n')
    code_text = '\n'.join(line[:90] for line in code_lines[:20])
    if len(code_lines) > 20: code_text += "\n# ..."
    elements.append(Preformatted(code_text, styles['CodeStyle']))

    # Challenges
    if a['challenges']:
        elements.append(Paragraph("🚀 Defis", styles['SectionHead']))
        for c in a['challenges']:
            stars = "★" * c['d']
            # Remove HTML tags from challenge text
            ct = re.sub(r'<[^>]+>', '', c['t'])
            elements.append(Paragraph(f"{stars} {esc(ct)}", styles['ChalStyle']))

    # QR Code link
    elements.append(Spacer(1, 4*mm))
    qr_url = f"https://abourdim.github.io/bit-54-activities/?a={a['id']}"
    elements.append(Paragraph(
        f"<font color='#888888' size='7'>📱 Ouvrir sur telephone : {qr_url}</font>",
        styles['Body']
    ))

    story.extend(elements)
    story.append(PageBreak())

# ── Build ──
# Page numbering
def add_page_number(canvas_obj, doc_obj):
    page_num = canvas_obj.getPageNumber()
    text = f"Micro:bit · 58 Activites — p.{page_num}"
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica', 7)
    canvas_obj.setFillColor(HexColor("#999999"))
    canvas_obj.drawCentredString(A4[0]/2, 1.2*cm, text)
    canvas_obj.restoreState()

doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
print(f"Ebook generated: {output_path}")
print(f"   {len(activities)} activities, {len(story)} elements")
