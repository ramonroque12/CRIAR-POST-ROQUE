# -*- coding: utf-8 -*-
"""
Slide Generator - Estilo TikTok Texto + Fundo (sem fotos)
3 estilos rotativos com VERDE como cor principal e contraste entre slides.
Formato: 1080x1350px (4:5 portrait)
"""
import os, sys, json, re
from PIL import Image, ImageDraw, ImageFont

FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

W, H   = 1080, 1350
MARGIN = 72

# ── Paleta verde ──────────────────────────────────────────────────────────────
GREEN       = (39, 211, 115)     # verde vivo
GREEN_DARK  = (22, 155, 75)      # verde médio
GREEN_DEEP  = (8,  52,  28)      # verde escuro (para bg pill em fundo escuro)
BLACK       = (10, 12, 16)       # quase preto
CHARCOAL    = (20, 26, 32)       # cinza azulado escuro
OFF_WHITE   = (238, 248, 242)    # branco esverdeado (fundo claro)
DARK_TEXT   = (14, 20, 24)       # texto escuro (para fundos claros)
WHITE       = (255, 255, 255)
GRAY_LIGHT  = (180, 195, 185)    # texto secundário em fundos escuros
GRAY_DARK   = (80, 95, 88)       # texto secundário em fundos claros

# Variantes de fundo para Style A (solid), alterna por slide
DARK_BG_VARIANTS = [
    (10,  12,  16),   # preto
    (8,   52,  28),   # verde escuro
    (18,  20,  30),   # azul-escuro
    (28,  16,   8),   # marrom escuro
    (6,   38,  48),   # verde-água escuro
]


# ── Helpers ───────────────────────────────────────────────────────────────────

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

def auto_size(text, base=90, max_chars=22):
    lines = text.split("\n")
    longest = max((len(l) for l in lines), default=1)
    if longest > max_chars:
        return max(52, int(base * max_chars / longest))
    return base

def draw_pill(draw, x, y, text, f, bg_color, text_color=WHITE,
              pad_x=28, pad_y=14, radius=None):
    """Desenha badge/pill arredondado. Retorna x final."""
    w_t = tw(draw, text, f)
    h_t = th(draw, text, f)
    x2  = x + w_t + pad_x * 2
    y2  = y + h_t + pad_y * 2
    r   = radius if radius is not None else (y2 - y) // 2
    draw.rounded_rectangle([x, y, x2, y2], radius=r, fill=bg_color)
    draw.text((x + pad_x, y + pad_y), text, fill=text_color, font=f)
    return x2

def ghost_number(img, num_str, accent, bg_color):
    """Número gigante semi-transparente decorativo no fundo."""
    try:
        f_ghost = fnt("BricolageGrotesque-Bold.ttf", 500)
        nd  = ImageDraw.Draw(img)
        nb  = nd.textbbox((0, 0), num_str, font=f_ghost)
        nx  = W - (nb[2] - nb[0]) + 40
        ny  = H - (nb[3] - nb[1]) - 60
        ar, ag, ab = accent
        br, bg_c, bb = bg_color
        gc = (
            min(255, int(br * 0.85 + ar * 0.18)),
            min(255, int(bg_c * 0.85 + ag * 0.18)),
            min(255, int(bb * 0.85 + ab * 0.18)),
        )
        nd.text((nx, ny), num_str, fill=gc, font=f_ghost)
    except Exception:
        pass


# ── STYLE A — SOLID BACKGROUND + HEADLINE GRANDE ─────────────────────────────

def render_solid(headline, sub="", bg_color=BLACK, accent=GREEN,
                 slide_num=1, total=1, show_swipe=True, cta_text=None):
    """
    Fundo sólido escuro + headline bold centralizada + ghost number decorativo.
    Ideal para: capa, notícias de destaque.
    """
    img  = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    # Linha de acento no topo (4px)
    draw.rectangle([0, 0, W, 6], fill=accent)

    # Número ghost no fundo
    ghost_number(img, str(slide_num).zfill(2), accent, bg_color)
    draw = ImageDraw.Draw(img)  # redraw sobre o ghost

    # Detecta se fundo é claro ou escuro
    br, bg_c, bb = bg_color
    brightness  = 0.299*br + 0.587*bg_c + 0.114*bb
    text_color  = DARK_TEXT if brightness > 160 else WHITE
    sub_color   = GRAY_DARK if brightness > 160 else GRAY_LIGHT

    f_handle = fnt("InstrumentSans-Regular.ttf", 28)
    f_tag    = fnt("InstrumentSans-Regular.ttf", 26)
    f_badge  = fnt("InstrumentSans-Regular.ttf", 25)

    # Handle + contador
    draw.text((MARGIN, 30), "@roquetrafegopagoo", fill=accent, font=f_handle)
    slide_tag = f"{slide_num}/{total}"
    draw.text((W - MARGIN - tw(draw, slide_tag, f_tag), 30),
              slide_tag, fill=sub_color, font=f_tag)

    # Badge de categoria
    ar, ag, ab = accent
    pill_bg = (max(0, br + int((ar-br)*0.18)), max(0, bg_c + int((ag-bg_c)*0.18)),
               max(0, bb + int((ab-bb)*0.18))) if brightness < 160 else GREEN_DEEP
    draw_pill(draw, MARGIN, 82, "MARKETING DIGITAL + IA", f_badge,
              bg_color=pill_bg, text_color=accent if brightness < 160 else WHITE)

    # ── Headline ──
    fsize = auto_size(headline, base=96, max_chars=20)
    fh    = fnt("BricolageGrotesque-Bold.ttf", fsize)
    lh    = fsize + 16

    lines     = headline.split("\n")
    f_sub     = fnt("InstrumentSans-Regular.ttf", 36)
    sub_lines = wrap(sub, f_sub, W - MARGIN * 2, draw)[:2] if sub else []

    block_h = len(lines) * lh
    if sub_lines:
        block_h += 32 + sum(th(draw, l, f_sub) + 8 for l in sub_lines)

    cy = max(200, (H - block_h) // 2 + 30)

    for line in lines:
        x = (W - tw(draw, line, fh)) // 2
        draw.text((x, cy), line, fill=text_color, font=fh)
        cy += lh

    if sub_lines:
        cy += 32
        for line in sub_lines:
            x = (W - tw(draw, line, f_sub)) // 2
            draw.text((x, cy), line, fill=sub_color, font=f_sub)
            cy += th(draw, line, f_sub) + 8

    # CTA button ou Deslize
    f_cta = fnt("BricolageGrotesque-Bold.ttf", 34)
    if cta_text:
        cta_w = tw(draw, cta_text, f_cta) + 90
        cta_h = 76
        cta_x = (W - cta_w) // 2
        cta_y = H - 140
        draw.rounded_rectangle([cta_x, cta_y, cta_x + cta_w, cta_y + cta_h],
                                radius=38, fill=accent)
        draw.text((cta_x + 45, cta_y + (cta_h - th(draw, cta_text, f_cta)) // 2),
                  cta_text, fill=DARK_TEXT, font=f_cta)
    elif show_swipe:
        f_sw  = fnt("InstrumentSans-Regular.ttf", 28)
        swipe = "Deslize para mais \u2192"
        draw.text(((W - tw(draw, swipe, f_sw)) // 2, H - 68),
                  swipe, fill=sub_color, font=f_sw)

    return img


# ── STYLE B — FUNDO CLARO + LISTA NUMERADA ───────────────────────────────────

def render_list(headline, items, category="NOVIDADES", slide_num=1, total=1):
    """
    Fundo OFF-WHITE + badge verde + headline bold dark + lista 01/02/03 em verde.
    Máximo contraste com slides escuros.
    """
    img  = Image.new("RGB", (W, H), OFF_WHITE)
    draw = ImageDraw.Draw(img)

    # Faixa verde no topo
    draw.rectangle([0, 0, W, 8], fill=GREEN)

    f_handle = fnt("InstrumentSans-Regular.ttf", 28)
    f_tag    = fnt("InstrumentSans-Regular.ttf", 26)
    f_badge  = fnt("InstrumentSans-Regular.ttf", 26)
    f_title  = fnt("BricolageGrotesque-Bold.ttf", 72)
    f_num    = fnt("BricolageGrotesque-Bold.ttf", 62)
    f_item   = fnt("InstrumentSans-Regular.ttf", 32)
    f_footer = fnt("InstrumentSans-Regular.ttf", 28)

    cy = 28

    # Handle + contador
    draw.text((MARGIN, cy), "@roquetrafegopagoo", fill=GREEN_DARK, font=f_handle)
    slide_tag = f"{slide_num}/{total}"
    draw.text((W - MARGIN - tw(draw, slide_tag, f_tag), cy),
              slide_tag, fill=GRAY_DARK, font=f_tag)
    cy += 64

    # Badge categoria
    draw_pill(draw, MARGIN, cy, category.upper(), f_badge,
              bg_color=GREEN, text_color=DARK_TEXT)
    cy += 70

    # Separador
    draw.line([(MARGIN, cy), (W - MARGIN, cy)], fill=(195, 220, 208), width=2)
    cy += 26

    # Headline
    lines = wrap(headline, f_title, W - MARGIN * 2, draw)[:3]
    for line in lines:
        draw.text((MARGIN, cy), line, fill=DARK_TEXT, font=f_title)
        cy += 82
    cy += 18

    draw.line([(MARGIN, cy), (W - MARGIN, cy)], fill=(195, 220, 208), width=2)
    cy += 34

    # Lista numerada
    num_col_w = tw(draw, "00", f_num) + 28
    for idx, item_text in enumerate(items[:4]):
        num_str = f"{idx + 1:02d}"

        # Número em verde
        draw.text((MARGIN, cy), num_str, fill=GREEN, font=f_num)

        # Texto do item (wrappado na coluna direita)
        item_lines = wrap(item_text, f_item, W - MARGIN - num_col_w - MARGIN, draw)[:2]
        num_h  = th(draw, num_str, f_num)
        item_h = sum(th(draw, l, f_item) + 6 for l in item_lines)
        iy     = cy + max(0, (num_h - item_h) // 2)

        for il in item_lines:
            draw.text((MARGIN + num_col_w, iy), il, fill=DARK_TEXT, font=f_item)
            iy += th(draw, il, f_item) + 6

        row_h = max(num_h, item_h) + 28
        cy   += row_h

        # Linha divisória entre itens
        if idx < len(items) - 1 and idx < 3:
            draw.line([(MARGIN + num_col_w, cy - 14),
                       (W - MARGIN, cy - 14)], fill=(210, 228, 218), width=1)

    # Footer escuro
    FOOT_H = 72
    draw.rectangle([0, H - FOOT_H, W, H], fill=CHARCOAL)
    fy = H - FOOT_H + (FOOT_H - th(draw, "A", f_footer)) // 2
    draw.text((MARGIN, fy), "@roquetrafegopagoo", fill=(195, 215, 205), font=f_footer)
    swipe = "Deslize \u2192" if slide_num < total else "agenciaroque.com.br"
    draw.text((W - MARGIN - tw(draw, swipe, f_footer), fy),
              swipe, fill=GREEN, font=f_footer)

    return img


# ── STYLE C — FUNDO ESCURO + DESTAQUE TIPOGRÁFICO ────────────────────────────

def render_impact(headline, highlight_word, detail="", category="DESTAQUE",
                  slide_num=1, total=1):
    """
    Fundo escuro cinza + badge verde + palavra-chave gigante em verde + headline.
    Funciona como 'slide de impacto' sem precisar de stat real.
    """
    img  = Image.new("RGB", (W, H), CHARCOAL)
    draw = ImageDraw.Draw(img)

    # Gradiente sutil
    for y_px in range(H):
        t   = y_px / H
        val = int(20 + t * 8)
        draw.line([(0, y_px), (W, y_px)],
                  fill=(val, int(val * 1.08), int(val * 1.04)))
    draw = ImageDraw.Draw(img)

    # Linha verde topo
    draw.rectangle([0, 0, W, 8], fill=GREEN)

    f_handle = fnt("InstrumentSans-Regular.ttf", 28)
    f_tag    = fnt("InstrumentSans-Regular.ttf", 26)
    f_badge  = fnt("InstrumentSans-Regular.ttf", 26)
    f_big    = fnt("BricolageGrotesque-Bold.ttf", 160)
    f_title  = fnt("BricolageGrotesque-Bold.ttf", 62)
    f_detail = fnt("InstrumentSans-Regular.ttf", 34)
    f_footer = fnt("InstrumentSans-Regular.ttf", 28)

    cy = 30

    # Handle + contador
    draw.text((MARGIN, cy), "@roquetrafegopagoo", fill=GREEN, font=f_handle)
    slide_tag = f"{slide_num}/{total}"
    draw.text((W - MARGIN - tw(draw, slide_tag, f_tag), cy),
              slide_tag, fill=GRAY_LIGHT, font=f_tag)
    cy += 68

    # Badge categoria
    draw_pill(draw, MARGIN, cy, category.upper(), f_badge,
              bg_color=GREEN_DEEP, text_color=GREEN)
    cy += 74

    # Separador
    draw.line([(MARGIN, cy), (W - MARGIN, cy)], fill=(40, 56, 48), width=1)
    cy += 32

    # Headline
    h_lines = wrap(headline, f_title, W - MARGIN * 2, draw)[:2]
    for line in h_lines:
        draw.text((MARGIN, cy), line, fill=WHITE, font=f_title)
        cy += 72
    cy += 20

    # Palavra de destaque gigante (verde)
    # Reduz se muito longa
    hw = tw(draw, highlight_word, f_big)
    if hw > W - MARGIN * 2:
        f_big2 = fnt("BricolageGrotesque-Bold.ttf", int(160 * (W - MARGIN*2) / hw))
    else:
        f_big2 = f_big

    draw.text((MARGIN, cy), highlight_word, fill=GREEN, font=f_big2)
    cy += th(draw, highlight_word, f_big2) + 18

    draw.line([(MARGIN, cy), (W - MARGIN, cy)], fill=(40, 56, 48), width=1)
    cy += 28

    # Detalhe/sub
    if detail:
        detail_lines = wrap(detail, f_detail, W - MARGIN * 2, draw)[:3]
        for dl in detail_lines:
            draw.text((MARGIN, cy), dl, fill=GRAY_LIGHT, font=f_detail)
            cy += th(draw, dl, f_detail) + 10

    # Footer
    FOOT_H = 72
    draw.rectangle([0, H - FOOT_H, W, H], fill=(8, 10, 12))
    fy = H - FOOT_H + (FOOT_H - th(draw, "A", f_footer)) // 2
    draw.text((MARGIN, fy), "@roquetrafegopagoo", fill=GRAY_LIGHT, font=f_footer)
    swipe = "Deslize \u2192" if slide_num < total else "agenciaroque.com.br"
    draw.text((W - MARGIN - tw(draw, swipe, f_footer), fy),
              swipe, fill=GREEN, font=f_footer)

    return img


# ── CTA SLIDE ─────────────────────────────────────────────────────────────────

def render_cta(num, total):
    """Slide final: chamada para ação (curtir, comentar, seguir)."""
    img  = Image.new("RGB", (W, H), BLACK)
    draw = ImageDraw.Draw(img)

    for y_px in range(H):
        t   = y_px / H
        val = int(10 + t * 6)
        draw.line([(0, y_px), (W, y_px)],
                  fill=(val, int(val + t * 5), int(val + t * 3)))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, 8], fill=GREEN)

    f_sm     = fnt("InstrumentSans-Regular.ttf", 26)
    f_big    = fnt("BricolageGrotesque-Bold.ttf", 112)
    f_mid    = fnt("BricolageGrotesque-Bold.ttf", 68)
    f_act    = fnt("BricolageGrotesque-Bold.ttf", 44)
    f_desc   = fnt("InstrumentSans-Regular.ttf", 30)
    f_url    = fnt("BricolageGrotesque-Bold.ttf", 38)
    f_footer = fnt("InstrumentSans-Regular.ttf", 28)

    draw.text((MARGIN, 30), "@roquetrafegopagoo", fill=GREEN, font=f_sm)

    cy = 108
    for line in ["ACHOU", "\u00daTIL?"]:
        draw.text(((W - tw(draw, line, f_big)) // 2, cy), line, fill=WHITE, font=f_big)
        cy += 122

    sub_txt = "Ent\u00e3o faz uma coisa:"
    draw.text(((W - tw(draw, sub_txt, f_mid)) // 2, cy + 4),
              sub_txt, fill=(150, 175, 160), font=f_mid)
    cy += 92

    draw.line([(MARGIN, cy), (W - MARGIN, cy)], fill=(35, 50, 42), width=1)
    cy += 30

    actions = [
        ("CURTA",   "para mais pessoas verem",        GREEN,           (8,  46, 24)),
        ("COMENTA", "sua opini\u00e3o aqui embaixo",  (55, 200, 255),  (6,  38, 52)),
        ("SEGUE",   "@roquetrafegopagoo",              (190, 230, 75),  (36, 44,  4)),
    ]

    for act, desc, fg, bg_c in actions:
        draw.rounded_rectangle([MARGIN, cy, W - MARGIN, cy + 72],
                                radius=12, fill=bg_c)
        draw.rounded_rectangle([MARGIN, cy, W - MARGIN, cy + 72],
                                radius=12, outline=fg, width=2)
        aw       = tw(draw, act, f_act)
        pill_end = MARGIN + aw + 46
        draw.rounded_rectangle([MARGIN, cy, pill_end, cy + 72],
                                radius=12, fill=fg)
        draw.text((MARGIN + 18, cy + (72 - th(draw, act, f_act)) // 2),
                  act, fill=DARK_TEXT, font=f_act)
        draw.text((pill_end + 20, cy + (72 - th(draw, desc, f_desc)) // 2),
                  desc, fill=(210, 228, 218), font=f_desc)
        cy += 84

    cy += 10
    draw.line([(MARGIN, cy), (W - MARGIN, cy)], fill=(32, 46, 38), width=1)
    cy += 26
    draw.text((MARGIN, cy), "agenciaroque.com.br", fill=GREEN, font=f_url)

    FOOT_H = 58
    draw.rectangle([0, H - FOOT_H, W, H], fill=(6, 8, 7))
    fy = H - FOOT_H + (FOOT_H - th(draw, "A", f_footer)) // 2
    draw.text((MARGIN, fy), "@roquetrafegopagoo", fill=(70, 90, 78), font=f_footer)
    rt = "Copyright \u00a9 2026"
    draw.text((W - MARGIN - tw(draw, rt, f_footer), fy), rt,
              fill=(55, 72, 62), font=f_footer)

    return img


# ── Lógica de escolha de estilo ───────────────────────────────────────────────

def _choose_style(slide_idx):
    """0 = SOLID dark, 1 = LIST light, 2 = IMPACT dark — garante contraste."""
    return slide_idx % 3


def _extract_highlight(headline, sub):
    """
    Extrai palavra/número de destaque para o slide IMPACT.
    Prioriza: percentual > número > palavra-chave de impacto > primeira palavra bold.
    """
    text = headline + " " + (sub or "")

    # Percentual
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*%', text)
    if m:
        return m.group(0).replace(',', '.')

    # Número com unidade marcante
    m = re.search(r'(\d+)\s*(?:vezes|bilh|milh|trilh)', text, re.IGNORECASE)
    if m:
        return m.group(1) + "x"

    # Palavras de impacto comuns no nicho
    impact_words = [
        "NOVO", "NOVA", "AGORA", "ALERTA", "TOP", "IA", "2026",
        "RECORD", "GRATIS", "FREE", "BOOM", "VIRAL",
    ]
    hl_upper = headline.upper()
    for w in impact_words:
        if w in hl_upper:
            return w

    # Fallback: primeira palavra em maiúsculo do headline
    words = headline.split()
    if words:
        first = re.sub(r'[^A-Za-zÀ-ú]', '', words[0]).upper()
        return first[:8] if first else "IA"

    return "IA"


def _make_list_items(headline, sub):
    """Divide sub em itens para o slide LIST."""
    if not sub:
        return [headline]
    # Tenta dividir por ". " ou "; "
    raw = re.split(r'[.;]\s+', sub)
    items = [it.strip() for it in raw if len(it.strip()) > 8]
    if len(items) >= 2:
        return items[:4]
    # Se não dividiu bem, divide em 2 pelo meio
    mid = len(sub) // 2
    # Acha o espaço mais próximo do meio
    left  = sub[:mid].rsplit(' ', 1)
    right = [sub[len(left[0]):].strip()] if left else [sub]
    parts = [left[0].strip()] + right
    return [p for p in parts if len(p) > 6][:3] or [sub]


# ── GERAÇÃO PRINCIPAL ─────────────────────────────────────────────────────────

def generate(config_path):
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)

    out = cfg["output_dir"]
    os.makedirs(out, exist_ok=True)

    slides = cfg.get("slides", [])
    total  = len(slides) + 2   # capa + conteúdos + cta
    paths  = []

    # ── Slide 1: CAPA (SOLID escuro) ──────────────────────────────────────────
    headline_cover = cfg.get("headline_cover", "A IA mudou tudo\nessa semana.\nVocê viu?")
    sub_cover      = cfg.get("sub_cover", "Resumo para quem trabalha com marketing digital.")

    img = render_solid(
        headline=headline_cover,
        sub=sub_cover,
        bg_color=BLACK,
        accent=GREEN,
        slide_num=1, total=total,
        show_swipe=True,
    )
    p = os.path.join(out, "slide_01.png")
    img.save(p, "PNG")
    paths.append(p)
    print("OK slide_01.png [CAPA SOLID DARK]")

    # ── Slides de conteúdo ────────────────────────────────────────────────────
    for i, s in enumerate(slides):
        num      = i + 2
        style    = _choose_style(i)   # 0=SOLID 1=LIST 2=IMPACT
        headline = s.get("headline", "").replace("\n", " ").strip()
        sub      = s.get("sub", "").strip()

        if style == 0:
            # SOLID escuro — varia o bg a cada conjunto de 3 slides
            bg_idx = (i // 3) % len(DARK_BG_VARIANTS)
            img    = render_solid(
                headline=headline,
                sub=sub,
                bg_color=DARK_BG_VARIANTS[bg_idx],
                accent=GREEN,
                slide_num=num, total=total,
                show_swipe=(num < total),
            )
            label = f"SOLID bg={DARK_BG_VARIANTS[bg_idx]}"

        elif style == 1:
            # LIST claro
            items = _make_list_items(headline, sub)
            img   = render_list(
                headline=headline,
                items=items,
                category="NOVIDADES",
                slide_num=num, total=total,
            )
            label = "LIST light"

        else:
            # IMPACT escuro — palavra-chave gigante
            highlight = _extract_highlight(headline, sub)
            img       = render_impact(
                headline=headline,
                highlight_word=highlight,
                detail=sub,
                category="DESTAQUE",
                slide_num=num, total=total,
            )
            label = f"IMPACT [{highlight}]"

        p = os.path.join(out, f"slide_{num:02d}.png")
        img.save(p, "PNG")
        paths.append(p)
        print(f"OK slide_{num:02d}.png [{label}]")

    # ── Último slide: CTA ─────────────────────────────────────────────────────
    img = render_cta(total, total)
    p   = os.path.join(out, f"slide_{total:02d}.png")
    img.save(p, "PNG")
    paths.append(p)
    print(f"OK slide_{total:02d}.png [CTA]")

    print(json.dumps({"paths": paths}))
    return paths


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python slide_generator_hollyfield.py <config.json>")
        sys.exit(1)
    generate(sys.argv[1])
