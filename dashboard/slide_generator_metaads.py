# -*- coding: utf-8 -*-
"""
Slide Generator — Meta Ads Fire
Estilo: fundo #0D0D14, laranja #FF6000, tipografia bold e impactante
Formato: 1080x1080px (quadrado para Meta Ads)
AIDA: Atenção / Interesse / Desejo / Ação
"""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont

FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
W, H = 1080, 1080
MARGIN = 60

# ── Paleta Fire Orange ─────────────────────────────────────────────────────────
DARK_BG    = (13,  13,  20)
DARK_CARD  = (22,  24,  34)
ORANGE     = (255,  96,   0)
ORANGE_DIM = ( 90,  35,   0)
ORANGE_GLW = ( 32,  14,   0)
WHITE      = (255, 255, 255)
GRAY       = (155, 160, 180)
DARK_TEXT  = (13,  13,  20)

AIDA_COLORS = {
    "ATENÇÃO":   (220,  40,  40),   # vermelho — urgência
    "INTERESSE": (255, 140,   0),   # laranja  — calor
    "DESEJO":    (255, 200,   0),   # dourado  — aspiração
    "AÇÃO":      (  0, 210, 120),   # verde    — conversão
}


def fnt(name, size):
    return ImageFont.truetype(os.path.join(FONTS_DIR, name), size)


def tw(draw, text, f):
    b = draw.textbbox((0, 0), text, font=f)
    return b[2] - b[0]


def th_font(draw, text, f):
    b = draw.textbbox((0, 0), text, font=f)
    return b[3] - b[1]


def wrap_text(text, f, max_w, draw):
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


def draw_bg_decoration(draw):
    """Grade diagonal sutil no fundo."""
    for i in range(-4, 16):
        x = i * 110
        draw.polygon(
            [(x, 0), (x + 60, 0), (x + 60 + H, H), (x + H, H)],
            fill=(16, 16, 26)
        )


def draw_top_bar(draw, slide_num, total):
    draw.rectangle([0, 0, W, 4], fill=ORANGE)
    f_h = fnt("InstrumentSans-Regular.ttf", 24)
    draw.text((MARGIN, 22), "@roquetrafegopagoo", fill=ORANGE, font=f_h)
    tag = f"{slide_num}/{total}"
    draw.text((W - MARGIN - tw(draw, tag, f_h), 22), tag, fill=GRAY, font=f_h)


def draw_bottom_bar(draw, slide_num, total):
    bar_y = H - 46
    bar_w = W - MARGIN * 2
    draw.rounded_rectangle([MARGIN, bar_y, MARGIN + bar_w, bar_y + 4],
                            radius=2, fill=(38, 28, 12))
    fill_w = int(bar_w * slide_num / max(total, 1))
    if fill_w > 0:
        draw.rounded_rectangle([MARGIN, bar_y, MARGIN + fill_w, bar_y + 4],
                                radius=2, fill=ORANGE)
    f_f = fnt("InstrumentSans-Regular.ttf", 20)
    draw.text((MARGIN, H - 32), "@roquetrafegopagoo", fill=(55, 42, 22), font=f_f)
    site = "META ADS"
    draw.text((W - MARGIN - tw(draw, site, f_f), H - 32), site, fill=(55, 42, 22), font=f_f)


def draw_card(draw, x, y, w, h):
    draw.rounded_rectangle([x - 2, y - 2, x + w + 2, y + h + 2],
                            radius=16, fill=ORANGE_GLW)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=DARK_CARD)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=14,
                            outline=ORANGE_DIM, width=1)


def draw_aida_badge(draw, aida_text, x, y):
    color = AIDA_COLORS.get(aida_text.upper(), ORANGE)
    f = fnt("InstrumentSans-Bold.ttf", 20)
    text_w = tw(draw, aida_text, f)
    px, py = 14, 7
    bw = text_w + px * 2
    bh = 20 + py * 2
    draw.rounded_rectangle([x, y, x + bw, y + bh], radius=bh // 2, fill=color)
    draw.text((x + px, y + py), aida_text, fill=DARK_TEXT, font=f)
    return bh


# ── Render: Capa ───────────────────────────────────────────────────────────────
def render_cover(cfg, out_path, slide_num, total):
    img = Image.new("RGB", (W, H), DARK_BG)
    draw = ImageDraw.Draw(img)

    draw_bg_decoration(draw)
    draw_top_bar(draw, slide_num, total)

    # Badge "META ADS CRIATIVO" centralizado
    f_badge = fnt("InstrumentSans-Bold.ttf", 18)
    badge_txt = "◆  META ADS CRIATIVO  ◆"
    bw = tw(draw, badge_txt, f_badge)
    bx = (W - bw) // 2
    by = 68
    draw.rounded_rectangle([bx - 14, by - 6, bx + bw + 14, by + 28],
                            radius=14, fill=(40, 16, 0))
    draw.rounded_rectangle([bx - 14, by - 6, bx + bw + 14, by + 28],
                            radius=14, outline=ORANGE_DIM, width=1)
    draw.text((bx, by), badge_txt, fill=ORANGE, font=f_badge)

    # Headline principal
    f_hl = fnt("BricolageGrotesque-Bold.ttf", 88)
    lines = cfg.get("headline_cover", "CRIATIVO\nMETA ADS").split("\n")
    y = 128
    for line in lines:
        lw = tw(draw, line, f_hl)
        draw.text(((W - lw) // 2, y), line, fill=WHITE, font=f_hl)
        y += 100

    # Linha laranja separadora
    draw.rectangle([MARGIN * 3, y + 8, W - MARGIN * 3, y + 12], fill=ORANGE)
    y += 28

    # Sub texto
    f_sub = fnt("InstrumentSans-Regular.ttf", 32)
    sub = cfg.get("sub_cover", "")
    sub_lines = wrap_text(sub, f_sub, W - MARGIN * 2, draw)
    for line in sub_lines[:2]:
        lw = tw(draw, line, f_sub)
        draw.text(((W - lw) // 2, y), line, fill=GRAY, font=f_sub)
        y += 44
    y += 18

    # Grid de benefícios (2 colunas x 3 linhas)
    topics = cfg.get("cover_topics", [])[:6]
    if topics:
        f_t = fnt("InstrumentSans-Bold.ttf", 24)
        cols = 2
        cell_w = (W - MARGIN * 2 - 12) // cols
        cell_h = 56
        for idx, tp in enumerate(topics):
            row = idx // cols
            col = idx % cols
            tx = MARGIN + col * (cell_w + 12)
            ty = y + row * (cell_h + 8)
            draw.rounded_rectangle([tx, ty, tx + cell_w, ty + cell_h],
                                    radius=10, fill=DARK_CARD)
            draw.rounded_rectangle([tx, ty, tx + cell_w, ty + cell_h],
                                    radius=10, outline=ORANGE_DIM, width=1)
            # Bolinha laranja
            dot_x = tx + 18
            dot_y = ty + cell_h // 2
            draw.ellipse([dot_x - 5, dot_y - 5, dot_x + 5, dot_y + 5], fill=ORANGE)
            draw.text((dot_x + 14, ty + (cell_h - 28) // 2), tp, fill=WHITE, font=f_t)

    draw_bottom_bar(draw, slide_num, total)
    img.save(out_path, "PNG")


# ── Render: Slide de conteúdo AIDA ────────────────────────────────────────────
def render_slide(slide, out_path, slide_num, total):
    img = Image.new("RGB", (W, H), DARK_BG)
    draw = ImageDraw.Draw(img)

    draw_bg_decoration(draw)
    draw_top_bar(draw, slide_num, total)

    y = 70

    # Badge AIDA ou tag
    aida = (slide.get("aida") or "").upper()
    tag  = slide.get("tag", "")
    tag_color_list = slide.get("tag_color")

    if aida and aida in AIDA_COLORS:
        badge_h = draw_aida_badge(draw, aida, MARGIN, y)
        y += badge_h + 18
    elif tag:
        color = tuple(tag_color_list) if tag_color_list else ORANGE
        f_tag = fnt("InstrumentSans-Bold.ttf", 20)
        tag_w = tw(draw, tag, f_tag)
        px, py = 14, 7
        bh = 20 + py * 2
        draw.rounded_rectangle([MARGIN, y, MARGIN + tag_w + px * 2, y + bh],
                                radius=bh // 2, fill=color)
        draw.text((MARGIN + px, y + py), tag, fill=DARK_TEXT, font=f_tag)
        y += bh + 18

    # Headline — aceita \n explícito + wrap automático
    f_hl = fnt("BricolageGrotesque-Bold.ttf", 80)
    headline = slide.get("headline", "")
    hl_lines = []
    for part in headline.split("\n"):
        wrapped = wrap_text(part, f_hl, W - MARGIN * 2, draw)
        hl_lines.extend(wrapped if wrapped else [part])

    accent_color = AIDA_COLORS.get(aida, WHITE)
    for i, line in enumerate(hl_lines[:3]):
        color = accent_color if i == 0 else WHITE
        draw.text((MARGIN, y), line, fill=color, font=f_hl)
        y += 94
    y += 8

    # Sub texto
    sub = slide.get("sub", "")
    if sub:
        f_sub = fnt("InstrumentSans-Regular.ttf", 33)
        sub_lines = []
        for part in sub.split("\n"):
            wrapped = wrap_text(part, f_sub, W - MARGIN * 2, draw)
            sub_lines.extend(wrapped if wrapped else [part])
        for line in sub_lines[:4]:
            draw.text((MARGIN, y), line, fill=GRAY, font=f_sub)
            y += 44
        y += 12

    # Stat box
    stat = (slide.get("stat") or "").strip()
    stat_label = (slide.get("stat_label") or "").strip()
    cta_text = (slide.get("cta") or "").strip()

    if aida == "AÇÃO" and cta_text:
        # CTA slide: botão laranja grande
        btn_y = max(y + 20, H - 200)
        btn_h = 80
        btn_w = W - MARGIN * 2
        draw.rounded_rectangle([MARGIN, btn_y, MARGIN + btn_w, btn_y + btn_h],
                                radius=btn_h // 2, fill=ORANGE)
        f_btn = fnt("BricolageGrotesque-Bold.ttf", 36)
        cta_w = tw(draw, cta_text, f_btn)
        draw.text(((W - cta_w) // 2, btn_y + (btn_h - 42) // 2),
                  cta_text, fill=DARK_TEXT, font=f_btn)

        # Ícone seta
        arrow = "→"
        f_arr = fnt("BricolageGrotesque-Bold.ttf", 36)
        arr_w = tw(draw, arrow, f_arr)
        draw.text((MARGIN + btn_w - arr_w - 24, btn_y + (btn_h - 42) // 2),
                  arrow, fill=DARK_TEXT, font=f_arr)

        # Texto urgência abaixo do botão
        if stat_label:
            f_urg = fnt("InstrumentSans-Regular.ttf", 24)
            urg_w = tw(draw, stat_label, f_urg)
            draw.text(((W - urg_w) // 2, btn_y + btn_h + 14),
                      stat_label, fill=GRAY, font=f_urg)

    elif stat:
        # Stat card
        card_y = max(y + 10, H - 200)
        card_h = 110
        draw_card(draw, MARGIN, card_y, W - MARGIN * 2, card_h)

        f_stat = fnt("BricolageGrotesque-Bold.ttf", 60)
        f_stl  = fnt("InstrumentSans-Regular.ttf", 24)
        stat_txt_w = tw(draw, stat, f_stat)
        stat_x = MARGIN + 24
        stat_y = card_y + (card_h - 68) // 2
        draw.text((stat_x, stat_y), stat, fill=ORANGE, font=f_stat)
        if stat_label:
            lbl_y = stat_y + 16
            lbl_x = stat_x + stat_txt_w + 20
            # Wrap label se necessário
            lbl_lines = wrap_text(stat_label, f_stl, W - MARGIN * 2 - stat_txt_w - 48, draw)
            for ll in lbl_lines[:2]:
                draw.text((lbl_x, lbl_y), ll, fill=GRAY, font=f_stl)
                lbl_y += 32

    draw_bottom_bar(draw, slide_num, total)
    img.save(out_path, "PNG")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: slide_generator_metaads.py <config.json>")
        sys.exit(1)

    cfg_path = sys.argv[1]
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)

    out_dir = cfg["output_dir"]
    os.makedirs(out_dir, exist_ok=True)

    slides_data = cfg.get("slides", [])
    total = len(slides_data) + 1  # +1 capa

    # Slide 0: capa
    cover_path = os.path.join(out_dir, "slide_00.png")
    render_cover(cfg, cover_path, 1, total)
    print(f"[OK] slide_00.png (capa)")

    # Slides de conteúdo
    for i, slide in enumerate(slides_data):
        fname = f"slide_{i + 1:02d}.png"
        fpath = os.path.join(out_dir, fname)
        render_slide(slide, fpath, i + 2, total)
        print(f"[OK] {fname}")

    print(f"[DONE] {total} slides → {out_dir}")


if __name__ == "__main__":
    main()
