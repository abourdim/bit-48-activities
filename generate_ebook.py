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

# ── Blocks Reference Section ──
story.append(Paragraph("Reference des Blocs MakeCode", styles['BookTitle']))
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("Tous les blocs utilises dans les 58 activites, avec leur code JavaScript et Python.", styles['Body']))
story.append(Spacer(1, 0.5*cm))

BLOCK_REF = [
    # Basic
    {"cat":"Base","color":"#1E90FF","blocks":[
        {"name":"afficher texte","desc":"Fait defiler un texte sur les 25 LEDs, lettre par lettre.","js":'basic.showString("Bonjour")',"py":'basic.show_string("Bonjour")'},
        {"name":"afficher nombre","desc":"Affiche un nombre sur les LEDs (defile si > 1 chiffre).","js":"basic.showNumber(42)","py":"basic.show_number(42)"},
        {"name":"montrer l'icone","desc":"Affiche une icone predefinie (coeur, sourire, eclair...).","js":"basic.showIcon(IconNames.Heart)","py":"basic.show_icon(IconNames.HEART)"},
        {"name":"montrer LEDs","desc":"Allume des LEDs specifiques sur la grille 5x5 avec un motif personnalise.","js":'basic.showLeds(`\n  # . # . #\n  . # . # .\n  # . # . #\n`)',"py":'basic.show_leds("""\n  # . # . #\n  . # . # .\n  # . # . #\n""")'},
        {"name":"effacer l'ecran","desc":"Eteint toutes les 25 LEDs.","js":"basic.clearScreen()","py":"basic.clear_screen()"},
        {"name":"pause","desc":"Attend un nombre de millisecondes (1000 ms = 1 seconde).","js":"basic.pause(1000)","py":"basic.pause(1000)"},
        {"name":"au demarrage","desc":"Code execute une seule fois quand la carte demarre.","js":"// Le code dans ce bloc s'execute au demarrage","py":"# Le code hors fonction s'execute au demarrage"},
    ]},
    # Loops
    {"cat":"Boucles","color":"#00AA00","blocks":[
        {"name":"repeter indefiniment","desc":"Boucle infinie : le code se repete sans fin. C'est le coeur de la plupart des programmes.","js":"basic.forever(function () {\n  // code ici\n})","py":"def on_forever():\n    # code ici\nbasic.forever(on_forever)"},
        {"name":"repeter N fois","desc":"Execute le code un nombre fixe de fois.","js":"for (let i = 0; i < 4; i++) {\n  // code\n}","py":"for i in range(4):\n    # code"},
        {"name":"tant que","desc":"Repete le code tant que la condition est vraie.","js":"while (condition) {\n  // code\n}","py":"while condition:\n    # code"},
    ]},
    # Input
    {"cat":"Entree","color":"#D400D4","blocks":[
        {"name":"quand bouton presse","desc":"Declenche du code quand on appuie sur A, B, ou A+B.","js":"input.onButtonPressed(Button.A, function () {\n  // code\n})","py":"def on_button_a():\n    # code\ninput.on_button_pressed(Button.A, on_button_a)"},
        {"name":"quand secouer","desc":"Declenche du code quand on secoue la carte (accelerometre).","js":"input.onGesture(Gesture.Shake, function () {\n  // code\n})","py":"def on_shake():\n    # code\ninput.on_gesture(Gesture.SHAKE, on_shake)"},
        {"name":"quand logo touche","desc":"Declenche du code quand on touche le logo dore (V2 uniquement).","js":"input.onLogoEvent(TouchButtonEvent.Pressed, function () {\n  // code\n})","py":"def on_logo():\n    # code\ninput.on_logo_event(TouchButtonEvent.PRESSED, on_logo)"},
        {"name":"temperature","desc":"Retourne la temperature mesuree par le processeur (approximative, en degC).","js":"input.temperature()","py":"input.temperature()"},
        {"name":"niveau de lumiere","desc":"Retourne le niveau de lumiere (0 = sombre, 255 = lumineux). Les LEDs servent de capteur.","js":"input.lightLevel()","py":"input.light_level()"},
        {"name":"niveau sonore (V2)","desc":"Retourne le niveau sonore ambiant (0-255) via le micro integre.","js":"input.soundLevel()","py":"input.sound_level()"},
        {"name":"direction boussole","desc":"Retourne l'angle de la boussole en degres (0-359). 0 = Nord.","js":"input.compassHeading()","py":"input.compass_heading()"},
        {"name":"acceleration","desc":"Retourne la force d'acceleration (mouvement). ~1024 au repos.","js":"input.acceleration(Dimension.Strength)","py":"input.acceleration(Dimension.STRENGTH)"},
    ]},
    # Logic
    {"cat":"Logique","color":"#00A4A6","blocks":[
        {"name":"si ... alors","desc":"Execute du code seulement si la condition est vraie.","js":"if (condition) {\n  // vrai\n}","py":"if condition:\n    # vrai"},
        {"name":"si ... alors ... sinon","desc":"Execute un code si vrai, un autre si faux. Permet de prendre des decisions.","js":"if (condition) {\n  // vrai\n} else {\n  // faux\n}","py":"if condition:\n    # vrai\nelse:\n    # faux"},
        {"name":"comparaison","desc":"Compare deux valeurs : egal (==), different (!=), plus grand (>), plus petit (<).","js":"if (x == 5) { }","py":"if x == 5:"},
        {"name":"et / ou / non","desc":"Combine des conditions : ET (les deux vraies), OU (au moins une), NON (inverse).","js":"if (a && b) { }\nif (a || b) { }","py":"if a and b:\nif a or b:"},
    ]},
    # Math
    {"cat":"Maths","color":"#9400D3","blocks":[
        {"name":"au hasard","desc":"Genere un nombre aleatoire entre min et max inclus.","js":"randint(1, 6)","py":"randint(1, 6)"},
        {"name":"operations","desc":"Addition (+), soustraction (-), multiplication (*), division (/), reste (%).","js":"let r = 10 + 5\nlet m = 10 % 3  // reste = 1","py":"r = 10 + 5\nm = 10 % 3  # reste = 1"},
        {"name":"min / max / abs","desc":"Minimum, maximum, valeur absolue.","js":"Math.min(a, b)\nMath.max(a, b)\nMath.abs(x)","py":"min(a, b)\nmax(a, b)\nabs(x)"},
    ]},
    # Variables
    {"cat":"Variables","color":"#DC143C","blocks":[
        {"name":"definir variable","desc":"Cree une variable et lui donne une valeur initiale.","js":"let score = 0","py":"score = 0"},
        {"name":"modifier variable","desc":"Change la valeur d'une variable existante.","js":"score += 1","py":"score += 1"},
        {"name":"variable globale (Python)","desc":"En Python, pour modifier une variable dans une fonction, il faut la declarer globale.","js":"// Pas necessaire en JS","py":"def on_shake():\n    global score\n    score += 1"},
    ]},
    # Music
    {"cat":"Musique","color":"#E63022","blocks":[
        {"name":"jouer tonalite","desc":"Joue une note a une frequence (Hz) pendant une duree (ms). Do=262, Re=294, Mi=330.","js":"music.playTone(262, 500)","py":"music.play_tone(262, 500)"},
        {"name":"jouer melodie","desc":"Joue une melodie predefinie (Dadadadum, Birthday, PowerUp...).","js":"music.startMelody(\n  music.builtInMelody(Melodies.Dadadadum),\n  MelodyOptions.Once\n)","py":"music.start_melody(\n    music.built_in_melody(Melodies.DADADADUM),\n    MelodyOptions.ONCE\n)"},
        {"name":"regler tempo","desc":"Change la vitesse de lecture de la musique (battements par minute).","js":"music.setTempo(120)","py":"music.set_tempo(120)"},
    ]},
    # Radio
    {"cat":"Radio","color":"#E3008C","blocks":[
        {"name":"definir groupe radio","desc":"Toutes les cartes sur le meme groupe peuvent communiquer. Chaque equipe choisit un numero different.","js":"radio.setGroup(7)","py":"radio.set_group(7)"},
        {"name":"envoyer nombre","desc":"Envoie un nombre par radio a toutes les cartes du meme groupe.","js":"radio.sendNumber(1)","py":"radio.send_number(1)"},
        {"name":"envoyer texte","desc":"Envoie un texte par radio.","js":'radio.sendString("salut")',"py":'radio.send_string("salut")'},
        {"name":"quand recu nombre","desc":"Declenche du code quand un nombre est recu par radio.","js":"radio.onReceivedNumber(function (n) {\n  basic.showNumber(n)\n})","py":"def on_received(n):\n    basic.show_number(n)\nradio.on_received_number(on_received)"},
    ]},
    # Pins
    {"cat":"Broches (Pins)","color":"#3BDDD4","blocks":[
        {"name":"lire analogique","desc":"Lit une valeur analogique (0-1023) sur une broche. Pour capteurs variables.","js":"pins.analogReadPin(AnalogPin.P0)","py":"pins.analog_read_pin(AnalogPin.P0)"},
        {"name":"lire numerique","desc":"Lit une valeur numerique (0 ou 1) sur une broche. Pour interrupteurs.","js":"pins.digitalReadPin(DigitalPin.P0)","py":"pins.digital_read_pin(DigitalPin.P0)"},
        {"name":"ecriture analogique","desc":"Ecrit une valeur (0-1023) sur une broche. Pour moteurs, LEDs variables.","js":"pins.analogWritePin(AnalogPin.P0, 512)","py":"pins.analog_write_pin(AnalogPin.P0, 512)"},
        {"name":"ecriture numerique","desc":"Ecrit 0 ou 1 sur une broche. Pour allumer/eteindre un composant.","js":"pins.digitalWritePin(DigitalPin.P0, 1)","py":"pins.digital_write_pin(DigitalPin.P0, 1)"},
        {"name":"servo ecrire","desc":"Positionne un servomoteur a un angle (0-180 degres).","js":"pins.servoWritePin(AnalogPin.P0, 90)","py":"pins.servo_write_pin(AnalogPin.P0, 90)"},
    ]},
    # LED
    {"cat":"LED","color":"#7600A8","blocks":[
        {"name":"allumer LED","desc":"Allume une LED specifique a la position (x, y) sur la grille 5x5.","js":"led.plot(2, 2)","py":"led.plot(2, 2)"},
        {"name":"eteindre LED","desc":"Eteint une LED specifique.","js":"led.unplot(2, 2)","py":"led.unplot(2, 2)"},
        {"name":"graphique barres","desc":"Affiche une valeur sous forme de barres sur les LEDs (0 a max).","js":"led.plotBarGraph(input.lightLevel(), 255)","py":"led.plot_bar_graph(input.light_level(), 255)"},
    ]},
    # Game
    {"cat":"Jeu (Sprites)","color":"#7600A8","blocks":[
        {"name":"creer sprite","desc":"Cree un point lumineux (sprite) deplacable sur l'ecran.","js":"let player = game.createSprite(2, 4)","py":"player = game.create_sprite(2, 4)"},
        {"name":"deplacer sprite","desc":"Change la position X ou Y d'un sprite.","js":"player.change(LedSpriteProperty.X, 1)","py":"player.change(LedSpriteProperty.X, 1)"},
        {"name":"collision","desc":"Verifie si deux sprites se touchent.","js":"if (sprite1.isTouching(sprite2)) { }","py":"if sprite1.is_touching(sprite2):"},
        {"name":"game over","desc":"Termine le jeu et affiche le score.","js":"game.gameOver()","py":"game.game_over()"},
    ]},
    # Functions
    {"cat":"Fonctions","color":"#3455DB","blocks":[
        {"name":"creer fonction","desc":"Definit un bloc de code reutilisable avec un nom. Evite de repeter du code.","js":"function maFonction() {\n  // code\n}","py":"def ma_fonction():\n    # code"},
        {"name":"appeler fonction","desc":"Execute le code de la fonction.","js":"maFonction()","py":"ma_fonction()"},
        {"name":"fonction avec parametre","desc":"Fonction qui accepte des valeurs en entree.","js":"function avancer(ms: number) {\n  // utiliser ms\n}","py":"def avancer(ms):\n    # utiliser ms"},
    ]},
]

for cat in BLOCK_REF:
    color = HexColor(cat["color"])
    story.append(Paragraph(f"<font color='{cat['color']}'><b>{cat['cat']}</b></font>", styles['SectionHead']))
    story.append(Spacer(1, 2*mm))

    for b in cat["blocks"]:
        elements = []
        # Block name as colored chip
        elements.append(Paragraph(f"<font color='{cat['color']}'><b>{esc(b['name'])}</b></font>", styles['Body']))
        elements.append(Paragraph(esc(b['desc']), styles['Body']))

        # Code examples side by side in a table
        js_code = b['js']
        py_code = b['py']
        code_table = Table(
            [[Preformatted(f"// JavaScript\n{js_code}", styles['CodeStyle']),
              Preformatted(f"# Python\n{py_code}", styles['CodeStyle'])]],
            colWidths=[8*cm, 8*cm]
        )
        code_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(code_table)
        elements.append(Spacer(1, 4*mm))
        story.append(KeepTogether(elements))

    story.append(Spacer(1, 4*mm))

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
