# -*- coding: utf-8 -*-
"""
Slide Generator — Cyberpulse Noir
Estilo: fundo #111318, ciano neon #00D4FF, cards dark, BricolageGrotesque Bold
Formato: 1080x1350px (Instagram 4:5 portrait)
"""
import os, sys, json, re
from PIL import Image, ImageDraw, ImageFont

FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
W, H      = 1080, 1350
MARGIN    = 64

# ── Paleta Cyberpulse Noir ────────────────────────────────────────────────────
DARK_BG   = (17,  19,  24)    # #111318
DARK_CARD = (24,  29,  40)    # card background
CYAN      = (0,  212, 255)    # #00D4FF neon
CYAN_DIM  = (0,  100, 130)    # border sutil
CYAN_GLOW = (0,   35,  55)    # glow de fundo
WHITE     = (255, 255, 255)
GRAY_BLUE = (177, 201, 226)   # texto secundário
DARK_TEXT = (12,  14,  18)    # texto sobre botão ciano


def fnt(name, size):
    return ImageFont.truetype(os.path.join(FONTS_DIR, name), size)

def tw(draw, text, f):
    b = draw.textbbox((0, 0), text, font=f)
    return b[2] - b[0]

def th(draw, text, f):
    b = draw.textbbox((0, 0), text, font=f)
    return b[3] - b[1]

def wrap(text, f, max_w, draw):
    if not text:
        return []
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if tw(draw, test, f) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ── Componentes reutilizáveis ─────────────────────────────────────────────────

def draw_card(draw, x, y, w, h):
    """Card dark com borda ciano e glow sutil."""
    draw.rounded_rectangle([x-2, y-2, x+w+2, y+h+2], radius=16, fill=CYAN_GLOW)
    draw.rounded_rectangle([x, y, x+w, y+h],           radius=14, fill=DARK_CARD)
    draw.rounded_rectangle([x, y, x+w, y+h],           radius=14, outline=CYAN_DIM, width=1)


def draw_top_bar(draw, slide_num, total):
    """Linha ciano no topo + handle + contador."""
    draw.rectangle([0, 0, W, 4], fill=CYAN)
    f_h = fnt("InstrumentSans-Regular.ttf", 26)
    draw.text((MARGIN, 26), "@roquetrafegopagoo", fill=CYAN, font=f_h)
    tag = f"{slide_num}/{total}"
    draw.text((W - MARGIN - tw(draw, tag, f_h), 26), tag, fill=GRAY_BLUE, font=f_h)


def draw_bottom(draw, slide_num, total):
    """Barra de progresso + handle + site no rodapé."""
    bar_y = H - 52
    bar_w = W - MARGIN * 2
    draw.rounded_rectangle([MARGIN, bar_y, MARGIN+bar_w, bar_y+4], radius=2, fill=(38, 50, 68))
    fill = int(bar_w * slide_num / max(total, 1))
    if fill > 0:
        draw.rounded_rectangle([MARGIN, bar_y, MARGIN+fill, bar_y+4], radius=2, fill=CYAN)
    f_f = fnt("InstrumentSans-Regular.ttf", 22)
    draw.text((MARGIN, H-34), "@roquetrafegopagoo", fill=(55, 72, 95), font=f_f)
    site = "agenciaroque.com.br"
    draw.text((W-MARGIN-tw(draw, site, f_f), H-34), site, fill=(55, 72, 95), font=f_f)


# ── SLIDE 01: CAPA ────────────────────────────────────────────────────────────

def render_cover(headline, sub="", highlight="", slide_num=1, total=6):
    """
    Fundo escuro, headline grande com palavra em ciano, subtítulo,
    tag do perfil, botão ciano 'Deslize para ver →'.
    """
    img  = Image.new("RGB", (W, H), DARK_BG)
    draw = ImageDraw.Draw(img)

    draw_top_bar(draw, slide_num, total)

    f_pill  = fnt("InstrumentSans-Regular.ttf", 22)
    f_title = fnt("BricolageGrotesque-Bold.ttf", 88)
    f_sub   = fnt("InstrumentSans-Regular.ttf", 34)
    f_tag   = fnt("InstrumentSans-Regular.ttf", 26)
    f_btn   = fnt("BricolageGrotesque-Bold.ttf", 36)

    cy = 90

    # Pill "SLIDE 01/06"
    pill = f"SLIDE {slide_num:02d}/{total:02d}"
    pw   = tw(draw, pill, f_pill) + 32
    ph   = 34
    draw.rounded_rectangle([MARGIN, cy, MARGIN+pw, cy+ph], radius=8, fill=(28, 36, 52))
    draw.rounded_rectangle([MARGIN, cy, MARGIN+pw, cy+ph], radius=8, outline=CYAN_DIM, width=1)
    draw.text((MARGIN+16, cy+(ph-th(draw, pill, f_pill))//2), pill, fill=GRAY_BLUE, font=f_pill)
    cy += ph + 36

    # Headline com palavra em destaque ciano
    hl_text = headline.replace("\n", " ")
    lines   = wrap(hl_text, f_title, W - MARGIN*2, draw)
    hl_word = highlight.upper() if highlight else ""

    for line in lines[:3]:
        if hl_word and hl_word in line.upper():
            idx    = line.upper().find(hl_word)
            before = line[:idx]
            hl     = line[idx:idx+len(hl_word)]
            after  = line[idx+len(hl_word):]
            x      = MARGIN
            if before:
                draw.text((x, cy), before, fill=WHITE, font=f_title)
                x += tw(draw, before, f_title)
            draw.text((x, cy), hl, fill=CYAN, font=f_title)
            x += tw(draw, hl, f_title)
            if after:
                draw.text((x, cy), after, fill=WHITE, font=f_title)
        else:
            draw.text((MARGIN, cy), line, fill=WHITE, font=f_title)
        cy += 100
    cy += 14

    # Linha decorativa ciano
    draw.rounded_rectangle([MARGIN, cy, MARGIN+64, cy+3], radius=2, fill=CYAN)
    cy += 22

    # Subtítulo
    if sub:
        sub_lines = wrap(sub, f_sub, W-MARGIN*2, draw)[:3]
        for sl in sub_lines:
            draw.text((MARGIN, cy), sl, fill=GRAY_BLUE, font=f_sub)
            cy += 48
        cy += 16

    # Tag "Siga..."
    tag_txt = "Siga @roquetrafegopagoo para mais"
    draw.text((MARGIN, cy), tag_txt, fill=(85, 110, 145), font=f_tag)

    # Botão ciano
    btn     = "Deslize para ver \u2192"
    btn_w   = tw(draw, btn, f_btn) + 80
    btn_h   = 72
    btn_x   = MARGIN
    btn_y   = H - 160
    draw.rounded_rectangle([btn_x, btn_y, btn_x+btn_w, btn_y+btn_h], radius=36, fill=CYAN)
    draw.text((btn_x+40, btn_y+(btn_h-th(draw, btn, f_btn))//2), btn, fill=DARK_TEXT, font=f_btn)

    draw_bottom(draw, slide_num, total)
    return img


# ── SLIDES DE CONTEÚDO ────────────────────────────────────────────────────────

def render_content(headline, items, category="IA NO TRAMPO", slide_num=2, total=6):
    """
    Fundo escuro, dot ciano + categoria, headline bold branca,
    separador, cards dark com borda ciano e vertical accent.
    """
    img  = Image.new("RGB", (W, H), DARK_BG)
    draw = ImageDraw.Draw(img)

    draw_top_bar(draw, slide_num, total)

    f_cat    = fnt("BricolageGrotesque-Bold.ttf", 24)
    f_title  = fnt("BricolageGrotesque-Bold.ttf", 68)
    f_item_t = fnt("BricolageGrotesque-Bold.ttf", 32)
    f_item_d = fnt("InstrumentSans-Regular.ttf",  28)

    cy = 82

    # Dot + categoria
    DOT = 8
    draw.ellipse([MARGIN, cy+5, MARGIN+DOT*2, cy+5+DOT*2], fill=CYAN)
    draw.text((MARGIN+DOT*2+14, cy), category.upper(), fill=CYAN, font=f_cat)
    cy += 44

    # Headline
    hl_text = headline.replace("\n", " ")
    lines   = wrap(hl_text, f_title, W - MARGIN*2, draw)[:3]
    for line in lines:
        draw.text((MARGIN, cy), line, fill=WHITE, font=f_title)
        cy += 78
    cy += 6

    # Separador
    draw.rectangle([MARGIN, cy, W-MARGIN, cy+1], fill=(38, 52, 70))
    cy += 18

    # Calcular altura dos cards para preencher bem o espaço
    n         = len(items[:4])
    spacing   = 14
    avail     = H - cy - 90   # deixa 90px pro rodapé
    card_h    = min(180, (avail - spacing*(n-1)) // n)
    card_w    = W - MARGIN*2

    for idx, item in enumerate(items[:4]):
        draw_card(draw, MARGIN, cy, card_w, card_h)

        pad  = 18
        acc_x = MARGIN + pad
        txt_x = acc_x + 12   # após accent bar

        # Vertical accent bar ciano
        draw.rounded_rectangle([acc_x, cy+pad, acc_x+4, cy+card_h-pad],
                                radius=2, fill=CYAN)

        title = item.get("title", "")
        desc  = item.get("desc", "")

        title_y = cy + pad + 4
        draw.text((txt_x + 12, title_y), title, fill=WHITE, font=f_item_t)
        title_h = th(draw, title, f_item_t)

        if desc:
            desc_y = title_y + title_h + 8
            d_lines = wrap(desc, f_item_d, card_w - pad*2 - 28, draw)[:2]
            for dl in d_lines:
                draw.text((txt_x + 12, desc_y), dl, fill=GRAY_BLUE, font=f_item_d)
                desc_y += th(draw, dl, f_item_d) + 4

        cy += card_h + spacing

    draw_bottom(draw, slide_num, total)
    return img


# ── SLIDE CTA ─────────────────────────────────────────────────────────────────

def render_cta(slide_num=6, total=6):
    """
    CTA final: título grande com palavra ciano, 3 botões de ação,
    site em ciano.
    """
    img  = Image.new("RGB", (W, H), DARK_BG)
    draw = ImageDraw.Draw(img)

    draw_top_bar(draw, slide_num, total)

    f_big  = fnt("BricolageGrotesque-Bold.ttf", 112)
    f_sub  = fnt("InstrumentSans-Regular.ttf",   34)
    f_btn  = fnt("BricolageGrotesque-Bold.ttf",  38)
    f_btn2 = fnt("BricolageGrotesque-Bold.ttf",  34)
    f_bio  = fnt("InstrumentSans-Regular.ttf",   26)
    f_url  = fnt("BricolageGrotesque-Bold.ttf",  32)

    cy = 100

    # Título
    for word, color in [("FICOU", WHITE), ("PRA", WHITE), ("TRÁS?", CYAN)]:
        x = (W - tw(draw, word, f_big)) // 2
        draw.text((x, cy), word, fill=color, font=f_big)
        cy += 122

    cy += 8

    # Separador central
    sw = 80
    draw.rounded_rectangle([(W-sw)//2, cy, (W+sw)//2, cy+3], radius=2, fill=CYAN)
    cy += 24

    # Sub
    subs = [
        "Gestor que não usa IA em 2026",
        "já perdeu para a concorrência.",
    ]
    for s in subs:
        draw.text(((W-tw(draw, s, f_sub))//2, cy), s, fill=GRAY_BLUE, font=f_sub)
        cy += 48
    cy += 24

    btn_w = W - MARGIN * 2
    btn_h = 70

    # Botão primário: Portal Roque
    portal_txt = "Acesse o Portal Roque \u2192"
    draw.rounded_rectangle([MARGIN, cy, MARGIN+btn_w, cy+btn_h], radius=14, fill=CYAN)
    tx = MARGIN + (btn_w - tw(draw, portal_txt, f_btn)) // 2
    ty = cy + (btn_h - th(draw, portal_txt, f_btn)) // 2
    draw.text((tx, ty), portal_txt, fill=DARK_TEXT, font=f_btn)
    cy += btn_h + 6
    bio_txt = "link na bio"
    draw.text(((W - tw(draw, bio_txt, f_bio))//2, cy), bio_txt, fill=(85, 110, 145), font=f_bio)
    cy += 36

    # Botões outline
    for txt in ["COMENTA o que achou", "SEGUE @roquetrafegopagoo"]:
        draw.rounded_rectangle([MARGIN, cy, MARGIN+btn_w, cy+btn_h], radius=14, fill=(28, 36, 52))
        draw.rounded_rectangle([MARGIN, cy, MARGIN+btn_w, cy+btn_h], radius=14, outline=CYAN_DIM, width=1)
        tx = MARGIN + (btn_w - tw(draw, txt, f_btn2)) // 2
        ty = cy + (btn_h - th(draw, txt, f_btn2)) // 2
        draw.text((tx, ty), txt, fill=GRAY_BLUE, font=f_btn2)
        cy += btn_h + 12

    cy += 6
    draw.text(((W-tw(draw, "agenciaroque.com.br", f_url))//2, cy),
              "agenciaroque.com.br", fill=CYAN, font=f_url)

    draw_bottom(draw, slide_num, total)
    return img


# ── GERAÇÃO PRINCIPAL ─────────────────────────────────────────────────────────

def generate(config_path):
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)

    out = cfg["output_dir"]
    os.makedirs(out, exist_ok=True)

    slides = cfg.get("slides", [])
    total  = len(slides) + 2   # capa + conteúdo + cta
    paths  = []

    # Capa
    headline_cover = cfg.get("headline_cover", "IA muda tudo\nno tráfego pago")
    sub_cover      = cfg.get("sub_cover", "O que aconteceu essa semana e o que você precisa fazer.")
    highlight      = cfg.get("highlight_word", "IA")

    img = render_cover(headline_cover, sub_cover, highlight, slide_num=1, total=total)
    p   = os.path.join(out, "slide_01.png")
    img.save(p, "PNG")
    paths.append(p)
    print("OK slide_01.png [CAPA CYBERPULSE]")

    # Conteúdo
    for i, s in enumerate(slides):
        num      = i + 2
        headline = s.get("headline", "").replace("\n", " ").strip()
        items    = s.get("items", [])
        category = s.get("category", "IA NO TRAMPO")
        sub      = s.get("sub", "")

        if not items and sub:
            # fallback: gera items fictícios a partir do sub
            items = [{"title": "Resumo", "desc": sub[:80]}]

        img = render_content(headline, items, category, slide_num=num, total=total)
        p   = os.path.join(out, f"slide_{num:02d}.png")
        img.save(p, "PNG")
        paths.append(p)
        print(f"OK slide_{num:02d}.png [CONTENT | {category}]")

    # CTA
    img = render_cta(slide_num=total, total=total)
    p   = os.path.join(out, f"slide_{total:02d}.png")
    img.save(p, "PNG")
    paths.append(p)
    print(f"OK slide_{total:02d}.png [CTA]")

    print(json.dumps({"paths": paths}))
    return paths


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python slide_generator_cyberpulse.py <config.json>")
        sys.exit(1)
    generate(sys.argv[1])
