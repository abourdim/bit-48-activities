"""
Generate a beautiful standalone HTML ebook from micro:bit 58 activities.
Open in browser → Print to PDF (Ctrl+P) for perfect results.
"""
import re

# ── Parse activities from index.html ──
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

js_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
js = js_match.group(1) if js_match else ""

activities = []
mk_pattern = re.compile(
    r'mk\((\d+),"([^"]+)","(\w+)",\{([^}]+)\},\s*"([^"]+)",\s*\[([^\]]+)\],\s*"([^"]+)",\s*\[([^\]]*)\],\s*`([^`]*)`\s*,\s*`([^`]*)`\s*,\s*\[([^\]]*)\]\s*\)',
    re.DOTALL
)
for m in mk_pattern.finditer(js):
    aid = int(m.group(1))
    meta_str = m.group(4)
    diff_m = re.search(r'difficulty:(\d)', meta_str)
    time_m = re.search(r'time:"([^"]+)"', meta_str)
    chal_str = m.group(11)
    challenges = []
    for cm2 in re.finditer(r'\{t:"([^"]+)",d:(\d)\}', chal_str):
        challenges.append({"t": cm2.group(1), "d": int(cm2.group(2))})
    activities.append({
        "id": aid, "title": m.group(2), "part": m.group(3),
        "difficulty": int(diff_m.group(1)) if diff_m else 1,
        "time": time_m.group(1) if time_m else "",
        "v2": "v2:true" in meta_str, "ia": "ia:true" in meta_str,
        "goal": m.group(5), "needs": re.findall(r'"([^"]+)"', m.group(6)),
        "tip": m.group(7), "blocks": re.findall(r'"([^"]+)"', m.group(8)),
        "codeJS": m.group(9).strip(), "codePY": m.group(10).strip(),
        "challenges": challenges
    })
activities.sort(key=lambda a: a["id"])
print(f"Extracted {len(activities)} activities")

# ── LED Patterns ──
LED_ICONS = {
    "Heart":[0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,0,0,0,1,0,0],
    "SmallHeart":[0,0,0,0,0,0,1,0,1,0,0,1,1,1,0,0,0,1,0,0,0,0,0,0,0],
    "Happy":[0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,1,0,0,0,1,0,1,1,1,0],
    "Sad":[0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,1,1,1,0,1,0,0,0,1],
    "Flash":[0,0,1,0,0,0,1,1,0,0,1,1,1,1,1,0,0,1,1,0,0,0,1,0,0],
    "No":[1,0,0,0,1,0,1,0,1,0,0,0,1,0,0,0,1,0,1,0,1,0,0,0,1],
    "Yes":[0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,1,0,1,0,0,0,1,0,0,0],
    "Asleep":[0,0,0,0,0,1,1,0,1,1,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0],
    "Skull":[0,1,1,1,0,1,0,1,0,1,1,1,1,1,1,0,1,1,1,0,0,1,1,1,0],
    "ArrowNorth":[0,0,1,0,0,0,1,1,1,0,1,0,1,0,1,0,0,1,0,0,0,0,1,0,0],
    "Meh":[0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1],
    "Target":[0,0,1,0,0,0,1,1,1,0,1,1,0,1,1,0,1,1,1,0,0,0,1,0,0],
    "Square":[1,1,1,1,1,1,0,0,0,1,1,0,0,0,1,1,0,0,0,1,1,1,1,1,1],
    "SmallSquare":[0,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0,1,1,1,0,0,0,0,0,0],
    "Scissors":[1,0,0,0,1,0,1,0,1,0,0,0,1,0,0,0,1,0,1,0,1,0,0,0,1],
    "Duck":[0,1,1,0,0,1,1,1,0,0,0,1,1,1,1,0,1,1,1,0,0,0,0,0,0],
}

def detect_led(code):
    m = re.search(r'showIcon\(IconNames\.(\w+)\)', code)
    if m and m.group(1) in LED_ICONS: return LED_ICONS[m.group(1)]
    m = re.search(r'showLeds\s*\(\s*`([^`]+)`', code)
    if m:
        p = [1 if c=='#' else 0 for c in m.group(1) if c in '#.']
        if len(p)==25: return p
    return None

def led_html(pattern):
    if not pattern: return ""
    cells = ""
    for i in range(25):
        on = "on" if pattern[i] else ""
        cells += f'<div class="led {on}"></div>'
    return f'<div class="led-grid">{cells}</div>'

# ── Block detection ──
BLOCK_MAP = [
    (r'basic\.showString',"afficher texte","#1E90FF"),
    (r'basic\.showIcon',"montrer icone","#1E90FF"),
    (r'basic\.showNumber',"afficher nombre","#1E90FF"),
    (r'basic\.showLeds',"montrer LEDs","#1E90FF"),
    (r'basic\.clearScreen',"effacer ecran","#1E90FF"),
    (r'basic\.pause',"pause","#1E90FF"),
    (r'basic\.forever',"repeter","#00AA00"),
    (r'input\.onButtonPressed',"bouton","#D400D4"),
    (r'input\.onGesture',"geste","#D400D4"),
    (r'input\.onLogoEvent',"logo","#D400D4"),
    (r'input\.temperature',"temperature","#D400D4"),
    (r'input\.lightLevel',"lumiere","#D400D4"),
    (r'input\.soundLevel',"son V2","#D400D4"),
    (r'input\.compassHeading',"boussole","#D400D4"),
    (r'input\.acceleration',"acceleration","#D400D4"),
    (r'randint',"hasard","#9400D3"),
    (r'music\.playTone',"tonalite","#E63022"),
    (r'music\.startMelody',"melodie","#E63022"),
    (r'radio\.setGroup',"radio groupe","#E3008C"),
    (r'radio\.sendNumber',"radio envoyer","#E3008C"),
    (r'radio\.onReceived',"radio recu","#E3008C"),
    (r'pins\.analogReadPin',"lire analog.","#3BDDD4"),
    (r'pins\.digitalReadPin',"lire numer.","#3BDDD4"),
    (r'pins\.digitalWritePin',"ecrire numer.","#3BDDD4"),
    (r'pins\.analogWritePin',"ecrire analog.","#3BDDD4"),
    (r'pins\.servoWritePin',"servo","#3BDDD4"),
    (r'led\.plot',"allumer LED","#7600A8"),
    (r'led\.plotBarGraph',"graphique","#7600A8"),
    (r'game\.createSprite',"sprite","#7600A8"),
    (r'neopixel',"NeoPixel","#7B2D8E"),
    (r'bluetooth',"Bluetooth","#0082FB"),
    (r'sonar\.ping',"sonar","#00A4A6"),
    (r'huskylens',"HuskyLens IA","#D400D4"),
    (r'function\s+\w',"fonction","#3455DB"),
    (r'if\s*\(',"si/sinon","#00A4A6"),
    (r'for\s*\(',"boucle for","#00AA00"),
    (r'while\s*\(',"tant que","#00AA00"),
    (r'let\s+\w',"variable","#DC143C"),
]

def detect_blocks(code):
    seen = set()
    result = []
    for pat, label, color in BLOCK_MAP:
        if re.search(pat, code) and label not in seen:
            seen.add(label)
            result.append((label, color))
    return result

def esc(t):
    return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def diff_label(d):
    return {1:"Debutant",2:"Intermediaire",3:"Avance"}.get(d,"")

def diff_color(d):
    return {1:"#40BF4A",2:"#F7DF1E",3:"#DC143C"}.get(d,"#888")

# ── Generate HTML ──
out = []
out.append("""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Micro:bit - 58 Activites - Ebook</title>
<style>
@page { size: A4; margin: 1.5cm 1.8cm; }
@media print {
  .page-break { page-break-before: always; }
  .no-print { display: none; }
  body { font-size: 9pt; }
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; color: #1a1a2e; background: #fff; line-height: 1.5; font-size: 10pt; }

/* Cover */
.cover { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 90vh; text-align: center; padding: 2cm; }
.cover h1 { font-size: 3em; color: #1E90FF; margin-bottom: 0.2em; }
.cover h2 { font-size: 1.5em; color: #666; font-weight: 400; margin-bottom: 0.5em; }
.cover .subtitle { font-size: 1.1em; color: #999; margin-bottom: 2em; }
.cover .author { font-size: 1em; color: #aaa; margin-top: 2em; }

/* micro:bit board SVG */
.mb-board { width: 200px; height: 160px; margin: 1em auto; }

/* TOC */
.toc { padding: 1cm 0; }
.toc h2 { font-size: 1.8em; color: #1E90FF; margin-bottom: 0.5em; }
.toc h3 { font-size: 1.1em; color: #1E90FF; margin: 1em 0 0.3em; text-transform: uppercase; letter-spacing: 0.05em; }
.toc-entry { display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px dotted #ddd; font-size: 0.95em; }
.toc-entry .toc-id { color: #1E90FF; font-weight: 700; min-width: 2.5em; }
.toc-entry .toc-tags { color: #999; font-size: 0.8em; }

/* Activity page */
.activity { padding: 0.5cm 0; }
.act-header { display: flex; align-items: baseline; gap: 0.5em; margin-bottom: 0.3em; }
.act-num { font-size: 0.8em; color: #1E90FF; font-weight: 700; }
.act-title { font-size: 1.5em; color: #1E90FF; font-weight: 700; }
.act-meta { display: flex; gap: 0.5em; flex-wrap: wrap; margin-bottom: 0.8em; }
.meta-chip { display: inline-flex; align-items: center; gap: 3px; padding: 2px 10px; border-radius: 99px; font-size: 0.75em; font-weight: 600; border: 1.5px solid; }
.meta-chip.diff { border-color: var(--dc); color: var(--dc); }
.meta-chip.time { border-color: #ccc; color: #666; }
.meta-chip.v2 { border-color: #40BF4A; color: #40BF4A; }
.meta-chip.ia { border-color: #F7DF1E; color: #b8860b; }

/* Sections */
.sec-title { font-size: 0.85em; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #1E90FF; margin: 0.7em 0 0.3em; display: flex; align-items: center; gap: 0.3em; }
.sec-title::after { content: ""; flex: 1; height: 1px; background: #e0e0e0; }

/* Goal */
.goal { font-size: 1em; line-height: 1.6; margin-bottom: 0.5em; }

/* LED grid */
.led-grid { display: inline-grid; grid-template-columns: repeat(5,1fr); gap: 3px; padding: 8px; background: #111; border-radius: 8px; vertical-align: middle; }
.led { width: 16px; height: 16px; border-radius: 50%; background: #1a1a1a; }
.led.on { background: #ff1a1a; box-shadow: 0 0 6px #ff1a1a; }

/* Content row: LED + materials */
.content-row { display: flex; gap: 1em; align-items: flex-start; margin: 0.5em 0; }
.content-row .led-grid { flex-shrink: 0; }

/* Block chips */
.blocks-row { display: flex; flex-wrap: wrap; gap: 4px; margin: 0.3em 0; }
.block-chip { display: inline-block; padding: 3px 10px; border-radius: 5px; color: #fff; font-size: 0.75em; font-weight: 600; border-bottom: 2px solid rgba(0,0,0,0.2); font-family: system-ui, sans-serif; }

/* Steps */
.steps { margin: 0.3em 0; }
.step { display: flex; gap: 0.5em; margin-bottom: 0.2em; font-size: 0.9em; }
.step-num { width: 20px; height: 20px; border-radius: 50%; background: #1E90FF; color: #fff; font-size: 0.7em; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 1px; }

/* Tip */
.tip-box { padding: 8px 12px; border-radius: 8px; border: 1px dashed #FFD700; background: #FFFDE7; font-size: 0.85em; color: #8B6914; margin: 0.5em 0; }

/* Code */
.code-row { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin: 0.5em 0; }
.code-box { border-radius: 8px; padding: 8px 10px; font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace; font-size: 0.72em; line-height: 1.5; overflow-x: auto; white-space: pre; }
.code-box.js { background: #FFF8E1; border: 1px solid #F7DF1E; }
.code-box.py { background: #E8F0FE; border: 1px solid #306998; }
.code-label { font-size: 0.7em; font-weight: 700; margin-bottom: 3px; display: flex; align-items: center; gap: 4px; }
.code-label .badge { display: inline-block; padding: 1px 5px; border-radius: 3px; font-size: 0.8em; color: #fff; }
.badge.js-badge { background: #F7DF1E; color: #000; }
.badge.py-badge { background: #306998; color: #FFD43B; }

/* Syntax highlighting */
.kw { color: #0000FF; font-weight: 700; }
.str { color: #A31515; }
.cmt { color: #008000; font-style: italic; }
.num { color: #098658; }
.fn { color: #795E26; }

/* Challenges */
.challenge { display: flex; gap: 0.5em; align-items: flex-start; margin-bottom: 0.2em; font-size: 0.85em; }
.chal-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }

/* Materials */
.needs { display: flex; flex-wrap: wrap; gap: 4px; }
.need-chip { padding: 2px 8px; border-radius: 99px; font-size: 0.75em; border: 1px solid #ddd; color: #555; background: #f9f9f9; }

/* QR link */
.qr-link { font-size: 0.7em; color: #aaa; margin-top: 0.5em; }

/* Footer */
.page-footer { font-size: 0.7em; color: #bbb; text-align: center; margin-top: 1em; padding-top: 0.5em; border-top: 1px solid #eee; }

/* Print button */
.print-bar { position: fixed; top: 0; left: 0; right: 0; background: #1E90FF; color: white; padding: 10px 20px; text-align: center; z-index: 999; font-weight: 700; }
.print-bar button { background: white; color: #1E90FF; border: none; padding: 8px 20px; border-radius: 8px; font-weight: 700; cursor: pointer; margin-left: 10px; font-size: 1em; }
</style>
</head>
<body>

<div class="print-bar no-print">
  Micro:bit 58 Activites - Ebook
  <button onclick="window.print()">Imprimer / PDF</button>
</div>
""")

# ── Cover ──
out.append("""
<div class="cover">
  <svg class="mb-board" viewBox="0 0 200 160" xmlns="http://www.w3.org/2000/svg">
    <rect x="10" y="10" width="180" height="120" rx="14" fill="#333"/>
    <rect x="60" y="35" width="80" height="60" rx="4" fill="#111"/>
    <circle cx="35" cy="65" r="10" fill="#666"/><text x="35" y="69" text-anchor="middle" fill="#fff" font-size="10" font-weight="bold">A</text>
    <circle cx="165" cy="65" r="10" fill="#666"/><text x="165" y="69" text-anchor="middle" fill="#fff" font-size="10" font-weight="bold">B</text>
""")
# LED grid on cover (heart)
heart = [0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,0,0,0,1,0,0]
for i in range(25):
    x = 66 + (i%5)*14
    y = 41 + (i//5)*11
    color = "#ff1a1a" if heart[i] else "#220000"
    out.append(f'    <circle cx="{x}" cy="{y}" r="4" fill="{color}"/>')

out.append("""
    <circle cx="30" cy="140" r="8" fill="#FFD700"/><text x="30" y="143" text-anchor="middle" fill="#333" font-size="7">0</text>
    <circle cx="60" cy="140" r="8" fill="#FFD700"/><text x="60" y="143" text-anchor="middle" fill="#333" font-size="7">1</text>
    <circle cx="90" cy="140" r="8" fill="#FFD700"/><text x="90" y="143" text-anchor="middle" fill="#333" font-size="7">2</text>
    <circle cx="140" cy="140" r="8" fill="#FFD700"/><text x="140" y="143" text-anchor="middle" fill="#333" font-size="6">3V</text>
    <circle cx="170" cy="140" r="8" fill="#FFD700"/><text x="170" y="143" text-anchor="middle" fill="#333" font-size="5">GND</text>
  </svg>
  <h1>Micro:bit</h1>
  <h2>58 Activites Pratiques</h2>
  <div class="subtitle">Blocs &middot; JavaScript &middot; Python</div>
  <div class="subtitle">Du clignotement LED aux robots IA</div>
  <div class="author">Workshop DIY &mdash; abourdim</div>
</div>
""")

# ── TOC ──
out.append('<div class="page-break"></div>')
out.append('<div class="toc"><h2>Table des matieres</h2>')
cur_part = ""
for a in activities:
    if a["part"] != cur_part:
        cur_part = a["part"]
        out.append(f'<h3>{"Simple (1-22)" if cur_part=="simple" else "Avance (23-58)"}</h3>')
    tags = f'{"⭐"*a["difficulty"]} {a["time"]}'
    if a["v2"]: tags += " V2"
    if a["ia"]: tags += " IA"
    out.append(f'<div class="toc-entry"><span><span class="toc-id">#{a["id"]}</span> {esc(a["title"])}</span><span class="toc-tags">{tags}</span></div>')
out.append('</div>')

# ── Syntax highlighting (simple) ──
def hl_js(code):
    code = esc(code)
    code = re.sub(r'(\/\/[^\n]*)', r'<span class="cmt">\1</span>', code)
    code = re.sub(r'\b(function|let|var|const|if|else|while|for|return|true|false|new)\b', r'<span class="kw">\1</span>', code)
    code = re.sub(r'(\d+)', r'<span class="num">\1</span>', code)
    return code

def hl_py(code):
    code = esc(code)
    code = re.sub(r'(#[^\n]*)', r'<span class="cmt">\1</span>', code)
    code = re.sub(r'\b(def|if|elif|else|while|for|in|return|import|from|global|not|and|or|True|False)\b', r'<span class="kw">\1</span>', code)
    code = re.sub(r'(\d+)', r'<span class="num">\1</span>', code)
    return code

# ── Activity Pages ──
for a in activities:
    out.append('<div class="page-break"></div>')
    out.append('<div class="activity">')

    # Header
    dc = diff_color(a["difficulty"])
    out.append(f'<div class="act-header"><span class="act-num">#{a["id"]}</span><span class="act-title">{esc(a["title"])}</span></div>')

    # Meta chips
    out.append('<div class="act-meta">')
    out.append(f'<span class="meta-chip diff" style="--dc:{dc}">{"⭐"*a["difficulty"]} {diff_label(a["difficulty"])}</span>')
    out.append(f'<span class="meta-chip time">⏱ {a["time"]}</span>')
    out.append(f'<span class="meta-chip">{a["part"].capitalize()}</span>')
    if a["v2"]: out.append('<span class="meta-chip v2">V2</span>')
    if a["ia"]: out.append('<span class="meta-chip ia">🧠 IA</span>')
    out.append('</div>')

    # Goal
    out.append('<div class="sec-title">🎯 Objectif</div>')
    out.append(f'<div class="goal">{esc(a["goal"])}</div>')

    # LED + Materials
    led = detect_led(a["codeJS"])
    out.append('<div class="content-row">')
    if led:
        out.append(led_html(led))
    out.append('<div>')
    out.append('<div class="sec-title">🧰 Materiel</div>')
    out.append('<div class="needs">')
    for n in a["needs"]:
        out.append(f'<span class="need-chip">{esc(n)}</span>')
    out.append('</div></div></div>')

    # Blocks used
    blocks = detect_blocks(a["codeJS"])
    if blocks:
        out.append('<div class="sec-title">🧩 Blocs utilises</div>')
        out.append('<div class="blocks-row">')
        for label, color in blocks:
            out.append(f'<span class="block-chip" style="background:{color}">{esc(label)}</span>')
        out.append('</div>')

    # Steps
    if a["blocks"]:
        out.append('<div class="sec-title">📋 Etapes</div>')
        out.append('<div class="steps">')
        for i, b in enumerate(a["blocks"]):
            out.append(f'<div class="step"><span class="step-num">{i+1}</span><span>{esc(b)}</span></div>')
        out.append('</div>')

    # Tip
    out.append(f'<div class="tip-box">💡 {esc(a["tip"])}</div>')

    # Code side by side
    out.append('<div class="sec-title">💻 Code</div>')
    js_code = '\n'.join(a["codeJS"].split('\n')[:18])
    py_code = '\n'.join(a["codePY"].split('\n')[:18])
    if len(a["codeJS"].split('\n')) > 18: js_code += "\n// ..."
    if len(a["codePY"].split('\n')) > 18: py_code += "\n# ..."

    out.append('<div class="code-row">')
    out.append(f'<div><div class="code-label"><span class="badge js-badge">JS</span> JavaScript</div><div class="code-box js">{hl_js(js_code)}</div></div>')
    out.append(f'<div><div class="code-label"><span class="badge py-badge">PY</span> Python</div><div class="code-box py">{hl_py(py_code)}</div></div>')
    out.append('</div>')

    # Challenges
    if a["challenges"]:
        out.append('<div class="sec-title">🚀 Defis</div>')
        for ch in a["challenges"]:
            color = {1:"#40BF4A",2:"#F7DF1E",3:"#DC143C"}.get(ch["d"],"#888")
            text = re.sub(r'<[^>]+>', '', ch["t"])
            out.append(f'<div class="challenge"><span class="chal-dot" style="background:{color}"></span><span>{esc(text)}</span></div>')

    # QR link
    out.append(f'<div class="qr-link">📱 https://abourdim.github.io/bit-54-activities/?a={a["id"]}</div>')

    out.append(f'<div class="page-footer">Micro:bit &middot; 58 Activites &middot; Activite #{a["id"]}</div>')
    out.append('</div>')

out.append('</body></html>')

# Write
with open("ebook.html", "w", encoding="utf-8") as f:
    f.write('\n'.join(out))

print(f"HTML ebook generated: ebook.html ({len(activities)} activities)")
print("Open in browser -> Ctrl+P -> Save as PDF")
