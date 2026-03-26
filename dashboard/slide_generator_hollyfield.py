# -*- coding: utf-8 -*-
"""
Slide Generator - Estilo Hollyfield Agency
Foto full-bleed + gradiente escuro + texto branco overlay.
Formato: 1080x1350px (4:5 portrait)
"""
import os, sys, json, requests, io
from PIL import Image, ImageDraw, ImageFont

FONTS_DIR = r"C:\Users\pc\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\bef85731-c665-4b4d-a10a-a1c20c9fab22\b6405610-b616-4fed-97fb-6f49f412426d\skills\canvas-design\canvas-fonts"

W, H    = 1080, 1350
MARGIN  = 62
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Paleta de cores de acento para slides sem foto (rotativa por índice)
ACCENT_COLORS = [
    (30,  120, 255),   # azul
    (180,  40, 220),   # roxo
    (0,   180, 120),   # verde
    (220,  80,  30),   # laranja
    (220,  30,  80),   # vermelho
    (20,  160, 200),   # ciano
]


# ── helpers ───────────────────────────────────────────────────────────────────

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

def auto_size(headline, base=82, max_chars=24):
    longest = max((len(l) for l in headline.split("\n")), default=1)
    if longest > max_chars:
        return max(52, int(base * max_chars / longest))
    return base

def draw_shadow(draw, pos, text, font, color=(255,255,255), shadow=(0,0,0), offset=3):
    """Desenha texto com sombra para legibilidade."""
    x, y = pos
    for dx, dy in [(-offset, -offset), (offset, -offset),
                   (-offset,  offset), (offset,  offset),
                   (0, offset), (0, -offset)]:
        draw.text((x+dx, y+dy), text, fill=shadow, font=font)
    draw.text((x, y), text, fill=color, font=font)

def download_image(url):
    if not url:
        return None
    try:
        r = requests.get(url, timeout=12, headers=HEADERS, allow_redirects=True)
        if r.status_code != 200:
            print(f"[IMG] HTTP {r.status_code}: {url[:60]}")
            return None
        ct  = r.headers.get("Content-Type", "")
        ext = url.lower().split("?")[0]
        if "image" not in ct and not any(ext.endswith(e) for e in (".jpg",".jpeg",".png",".webp")):
            return None
        img = Image.open(io.BytesIO(r.content)).convert("RGB")
        ar  = img.width / max(img.height, 1)
        if ar > 2.5 or img.height < 100:
            print(f"[IMG] Rejeitado ratio={ar:.1f} h={img.height}")
            return None
        print(f"[IMG] OK {img.width}x{img.height}")
        return img
    except Exception as e:
        print(f"[IMG] Erro: {e} — {url[:60]}")
    return None

def cover_crop(photo, tw, th):
    src_r = photo.width / photo.height
    tgt_r = tw / th
    if src_r > tgt_r:
        new_h, new_w = th, int(src_r * th)
    else:
        new_w, new_h = tw, int(tw / src_r)
    photo = photo.resize((new_w, new_h), Image.LANCZOS)
    x = (new_w - tw) // 2
    y = (new_h - th) // 2
    return photo.crop((x, y, x + tw, y + th))

def make_photo_bg(photo, darken=0.48):
    """Foto full-bleed escurecida."""
    bg  = cover_crop(photo, W, H)
    ov  = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.blend(bg, ov, darken)

def make_gradient_bg(accent=(30, 80, 180)):
    """Fundo escuro com toque de cor — para slides sem foto."""
    bg = Image.new("RGB", (W, H))
    d  = ImageDraw.Draw(bg)
    ar, ag, ab = accent
    for y in range(H):
        t = y / H
        # parte superior escura com leve toque de cor
        r = int(10 + ar * 0.12 * (1 - t))
        g = int(10 + ag * 0.10 * (1 - t))
        b = int(22 + ab * 0.18 * (1 - t))
        d.line([(0, y), (W, y)], fill=(min(r,255), min(g,255), min(b,255)))
    return bg

def add_bottom_grad(img, grad_h=640, strength=245):
    """Gradiente preto na parte inferior para legibilidade."""
    mask  = Image.new("L", (W, H), 0)
    d     = ImageDraw.Draw(mask)
    for y in range(H - grad_h, H):
        t = (y - (H - grad_h)) / grad_h
        d.line([(0, y), (W, y)], fill=int(strength * (t ** 1.1)))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(black, img, mask)

def draw_top_bar(draw, f):
    """Handle e info no topo."""
    draw.text((MARGIN, 22), "@roquetrafegopagoo",   fill=(200, 200, 200), font=f)
    ct = "Marketing Digital + IA"
    draw.text(((W - tw(draw, ct, f)) // 2, 22),     fill=(200, 200, 200), font=f, text=ct)
    rt = "Copyright \u00a9 2026"
    draw.text((W - MARGIN - tw(draw, rt, f), 22),   fill=(200, 200, 200), font=f, text=rt)

def draw_accent_deco(img, accent, slide_num):
    """Para slides sem foto: barra vertical de acento + número decorativo."""
    draw = ImageDraw.Draw(img)
    ar, ag, ab = accent

    # Barra vertical grossa à esquerda (acento de cor)
    draw.rectangle([0, 0, 10, H], fill=(ar, ag, ab))

    # Número do slide em gigante no fundo (decorativo, semi-transparente)
    try:
        f_big_num = fnt("BricolageGrotesque-Bold.ttf", 420)
        num_str   = str(slide_num).zfill(2)
        # Desenha em overlay com cor escura (quase invisível mas texturiza)
        num_img  = Image.new("RGB", (W, H), (0, 0, 0))
        nd       = ImageDraw.Draw(num_img)
        nb       = nd.textbbox((0, 0), num_str, font=f_big_num)
        nx       = W - (nb[2]-nb[0]) - 20
        ny       = (H - (nb[3]-nb[1])) // 2 - 80
        nd.text((nx, ny), num_str, fill=(ar//6, ag//6, ab//6), font=f_big_num)
        img = Image.blend(img, num_img, 0.0)   # só textura mínima
        # Versão ligeiramente visível
        draw2 = ImageDraw.Draw(img)
        draw2.text((nx, ny), num_str, fill=(int(ar*0.08), int(ag*0.08), int(ab*0.12)), font=f_big_num)
    except Exception:
        pass

    # Linha colorida fina no topo
    draw3 = ImageDraw.Draw(img)
    draw3.rectangle([0, 0, W, 6], fill=(ar, ag, ab))
    return img


# ── COVER ─────────────────────────────────────────────────────────────────────
def render_cover(cfg, photo=None):
    if photo:
        bg = make_photo_bg(photo, darken=0.50)
    else:
        bg = make_gradient_bg(accent=(30, 80, 200))
        bg = draw_accent_deco(bg, (30, 80, 200), 1)

    bg   = add_bottom_grad(bg, grad_h=760, strength=250)
    draw = ImageDraw.Draw(bg)

    f_sm    = fnt("InstrumentSans-Regular.ttf", 22)
    f_sub   = fnt("InstrumentSans-Regular.ttf", 32)
    f_swipe = fnt("InstrumentSans-Regular.ttf", 26)

    draw_top_bar(draw, f_sm)

    headline  = cfg.get("headline_cover", "O que mudou\nno Marketing\nDigital essa semana.")
    sub       = cfg.get("sub_cover", "")
    fsize     = auto_size(headline, base=96, max_chars=20)
    fh        = fnt("BricolageGrotesque-Bold.ttf", fsize)
    lh        = fsize + 14

    lines     = headline.split("\n")
    sub_lines = wrap(sub, f_sub, W - MARGIN * 2, draw)[:2]

    block_h = (len(lines) * lh + 22
               + sum(th(draw, l, f_sub) + 10 for l in sub_lines) + 50)
    cy = H - block_h - 70

    for line in lines:
        x = (W - tw(draw, line, fh)) // 2
        draw_shadow(draw, (x, cy), line, fh, color=(255,255,255), shadow=(0,0,0), offset=3)
        cy += lh

    cy += 22
    for line in sub_lines:
        x = (W - tw(draw, line, f_sub)) // 2
        draw.text((x, cy), line, fill=(210, 210, 210), font=f_sub)
        cy += th(draw, line, f_sub) + 10

    swipe = "Deslize para mais \u2192"
    draw.text(((W - tw(draw, swipe, f_swipe)) // 2, H - 64),
              swipe, fill=(175, 175, 175), font=f_swipe)
    return bg


# ── CONTENT ───────────────────────────────────────────────────────────────────
def render_content(s, num, total, photo=None, accent=(30, 80, 200)):
    if photo:
        bg = make_photo_bg(photo, darken=0.42)
        bg = add_bottom_grad(bg, grad_h=680, strength=245)
    else:
        bg = make_gradient_bg(accent=accent)
        bg = draw_accent_deco(bg, accent, num)
        bg = add_bottom_grad(bg, grad_h=560, strength=220)

    draw = ImageDraw.Draw(bg)

    f_sm     = fnt("InstrumentSans-Regular.ttf", 22)
    f_footer = fnt("InstrumentSans-Regular.ttf", 24)
    f_sub    = fnt("InstrumentSans-Regular.ttf", 28)

    draw_top_bar(draw, f_sm)

    headline   = s.get("headline", "")
    sub        = s.get("sub", "")
    fsize      = auto_size(headline, base=84, max_chars=24)
    fh         = fnt("BricolageGrotesque-Bold.ttf", fsize)
    lh         = fsize + 12

    head_lines = wrap(headline, fh, W - MARGIN * 2, draw)[:3]
    sub_lines  = wrap(sub, f_sub, W - MARGIN * 2, draw)[:3]

    block_h = len(head_lines) * lh
    if sub_lines:
        block_h += 18 + sum(th(draw, l, f_sub) + 8 for l in sub_lines)

    FOOT_H = 56
    cy     = H - FOOT_H - block_h - 24

    # Linha de acento antes do headline
    ar, ag, ab = accent
    draw.rectangle([MARGIN, cy - 14, MARGIN + 60, cy - 8], fill=(ar, ag, ab))

    for line in head_lines:
        draw_shadow(draw, (MARGIN, cy), line, fh,
                    color=(255, 255, 255), shadow=(0, 0, 0), offset=2)
        cy += lh

    if sub_lines:
        cy += 14
        for line in sub_lines:
            draw.text((MARGIN, cy), line, fill=(205, 205, 205), font=f_sub)
            cy += th(draw, line, f_sub) + 8

    # Footer
    draw.rectangle([0, H - FOOT_H, W, H], fill=(8, 8, 14))
    fy = H - FOOT_H + 16
    draw.text((MARGIN, fy), "@roquetrafegopagoo", fill=(215, 215, 215), font=f_footer)
    swipe = "Deslize para mais \u2192" if num < total else "agenciaroque.com.br"
    draw.text((W - MARGIN - tw(draw, swipe, f_footer), fy),
              swipe, fill=(215, 215, 215), font=f_footer)
    return bg


# ── CTA ───────────────────────────────────────────────────────────────────────
def render_cta(num, total):
    bg   = make_gradient_bg(accent=(30, 80, 200))
    draw = ImageDraw.Draw(bg)

    # Barra de acento colorida no topo
    for x in range(W):
        t = x / W
        draw.line([(x, 0), (x, 8)], fill=(
            int(30 + 90*t), int(80 + 40*t), int(220 + 30*t)))

    f_sm     = fnt("InstrumentSans-Regular.ttf", 22)
    f_big    = fnt("BricolageGrotesque-Bold.ttf", 104)
    f_mid    = fnt("BricolageGrotesque-Bold.ttf", 70)
    f_act    = fnt("BricolageGrotesque-Bold.ttf", 46)
    f_desc   = fnt("InstrumentSans-Regular.ttf", 27)
    f_portal = fnt("BricolageGrotesque-Bold.ttf", 38)
    f_footer = fnt("InstrumentSans-Regular.ttf", 24)

    draw.text((MARGIN, 22), "@roquetrafegopagoo", fill=(130, 130, 170), font=f_sm)
    ct = "Marketing Digital + IA"
    draw.text(((W - tw(draw, ct, f_sm)) // 2, 22), ct, fill=(130, 130, 170), font=f_sm)

    cy = 96
    for line in ["ACHOU", "\u00daTIL?"]:
        draw.text(((W - tw(draw, line, f_big)) // 2, cy),
                  line, fill=(255, 255, 255), font=f_big)
        cy += 112

    sub = "Ent\u00e3o faz uma coisa:"
    draw.text(((W - tw(draw, sub, f_mid)) // 2, cy + 4),
              sub, fill=(175, 175, 220), font=f_mid)
    cy += 90

    draw.line([(MARGIN, cy), (W - MARGIN, cy)], fill=(50, 50, 120), width=1)
    cy += 26

    actions = [
        ("CURTA",   "para mais pessoas verem",       (220, 50,  90), (55, 10, 28)),
        ("COMENTA", "sua opini\u00e3o aqui embaixo", (90,  80, 240), (18, 15, 65)),
        ("SEGUE",   "@roquetrafegopagoo",             (30, 200, 120), (5,  48, 28)),
    ]
    for act, desc, fg, bg_c in actions:
        draw.rounded_rectangle([MARGIN, cy, W - MARGIN, cy + 68],
                                radius=12, fill=bg_c)
        draw.rounded_rectangle([MARGIN, cy, W - MARGIN, cy + 68],
                                radius=12, outline=fg, width=2)
        # Pill colorido — largura dinâmica baseada no texto
        aw = tw(draw, act, f_act)
        pill_end = MARGIN + aw + 40
        draw.rounded_rectangle([MARGIN, cy, pill_end, cy + 68],
                                radius=12, fill=fg)
        draw.text((MARGIN + 18, cy + 12), act, fill=(255, 255, 255), font=f_act)
        draw.text((pill_end + 18, cy + 18), desc, fill=(210, 210, 235), font=f_desc)
        cy += 78

    cy += 8
    draw.line([(MARGIN, cy), (W - MARGIN, cy)], fill=(40, 40, 80), width=1)
    cy += 22
    draw.text((MARGIN, cy), "Arsenal completo em:", fill=(110, 110, 160), font=f_desc)
    cy += 36
    draw.text((MARGIN, cy), "agenciaroque.com.br", fill=(80, 150, 255), font=f_portal)

    FOOT_H = 54
    draw.rectangle([0, H - FOOT_H, W, H], fill=(6, 6, 20))
    draw.line([(0, H - FOOT_H), (W, H - FOOT_H)], fill=(30, 30, 80), width=1)
    draw.text((MARGIN, H - FOOT_H + 15), "@roquetrafegopagoo",
              fill=(100, 100, 150), font=f_footer)
    rt = "Copyright \u00a9 2026"
    draw.text((W - MARGIN - tw(draw, rt, f_footer), H - FOOT_H + 15),
              rt, fill=(80, 80, 120), font=f_footer)
    return bg


# ── MAIN ──────────────────────────────────────────────────────────────────────
def generate(config_path):
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)

    out = cfg["output_dir"]
    os.makedirs(out, exist_ok=True)

    slides    = cfg.get("slides", [])
    total     = len(slides) + 2
    paths     = []
    used_urls = set()

    # Slide 1: Capa
    cover_url = cfg.get("cover_image_url") or ""
    cover_img = download_image(cover_url) if cover_url else None
    if cover_url:
        used_urls.add(cover_url)

    img = render_cover(cfg, cover_img)
    p   = os.path.join(out, "slide_01.png")
    img.save(p, "PNG")
    paths.append(p)
    print(f"OK slide_01.png ({'foto' if cover_img else 'gradiente'})")

    # Slides de conteudo
    for i, s in enumerate(slides):
        num    = i + 2
        url    = s.get("image_url") or ""
        photo  = None
        accent = ACCENT_COLORS[i % len(ACCENT_COLORS)]

        if url and url not in used_urls:
            photo = download_image(url)
            if photo:
                used_urls.add(url)

        img = render_content(s, num, total, photo=photo, accent=accent)
        p   = os.path.join(out, f"slide_{num:02d}.png")
        img.save(p, "PNG")
        paths.append(p)
        print(f"OK slide_{num:02d}.png ({'foto' if photo else 'gradiente cor=' + str(accent)})")

    # Ultimo slide: CTA
    img = render_cta(total, total)
    p   = os.path.join(out, f"slide_{total:02d}.png")
    img.save(p, "PNG")
    paths.append(p)
    print(f"OK slide_{total:02d}.png")

    print(json.dumps({"paths": paths}))
    return paths


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python slide_generator_hollyfield.py <config.json>")
        sys.exit(1)
    generate(sys.argv[1])
