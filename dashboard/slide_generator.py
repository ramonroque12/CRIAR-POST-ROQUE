# -*- coding: utf-8 -*-
"""
Slide Generator - Configurable version for Roque Dashboard
Usage: python slide_generator.py <config.json>
"""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont

FONTS_DIR = r"C:\Users\pc\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\bef85731-c665-4b4d-a10a-a1c20c9fab22\b6405610-b616-4fed-97fb-6f49f412426d\skills\canvas-design\canvas-fonts"

BG_DARK   = (6, 7, 16)
ACCENT    = (0, 200, 255)
ACCENT2   = (120, 80, 255)
WHITE     = (255, 255, 255)
GRAY      = (140, 145, 165)
GRID_LINE = (20, 24, 48)
W, H      = 1080, 1080
MARGIN    = 72

def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS_DIR, name), size)

def new_canvas():
    img = Image.new("RGB", (W, H), BG_DARK)
    return img, ImageDraw.Draw(img)

def draw_grid(draw):
    for x in range(0, W, 54):
        draw.line([(x,0),(x,H)], fill=GRID_LINE, width=1)
    for y in range(0, H, 54):
        draw.line([(0,y),(W,y)], fill=GRID_LINE, width=1)

def draw_gradient_bar(draw, x, y, w, h, c1, c2):
    for i in range(w):
        t = i / w
        r = int(c1[0]+(c2[0]-c1[0])*t)
        g = int(c1[1]+(c2[1]-c1[1])*t)
        b = int(c1[2]+(c2[2]-c1[2])*t)
        draw.line([(x+i,y),(x+i,y+h)], fill=(r,g,b))

def draw_accent_line(draw, x, y, length=140, color=ACCENT):
    draw.line([(x,y),(x+length,y)], fill=color, width=3)

def draw_tag(draw, x, y, text, f_small, bg=ACCENT, fg=BG_DARK):
    pad_x, pad_y = 20, 10
    bbox = draw.textbbox((0,0), text, font=f_small)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.rounded_rectangle([x,y,x+tw+pad_x*2,y+th+pad_y*2], radius=6, fill=bg)
    draw.text((x+pad_x, y+pad_y), text, fill=fg, font=f_small)
    return y+th+pad_y*2

def draw_corner_marks(draw):
    size, t, c = 24, 2, (40,45,75)
    draw.rectangle([MARGIN-2,MARGIN-2,MARGIN-2+size,MARGIN-2+t], fill=c)
    draw.rectangle([MARGIN-2,MARGIN-2,MARGIN-2+t,MARGIN-2+size], fill=c)
    draw.rectangle([W-MARGIN-size+2,MARGIN-2,W-MARGIN+2,MARGIN-2+t], fill=c)
    draw.rectangle([W-MARGIN-t+2,MARGIN-2,W-MARGIN+2,MARGIN-2+size], fill=c)
    draw.rectangle([MARGIN-2,H-MARGIN-t+2,MARGIN-2+size,H-MARGIN+2], fill=c)
    draw.rectangle([MARGIN-2,H-MARGIN-size+2,MARGIN-2+t,H-MARGIN+2], fill=c)
    draw.rectangle([W-MARGIN-size+2,H-MARGIN-t+2,W-MARGIN+2,H-MARGIN+2], fill=c)
    draw.rectangle([W-MARGIN-t+2,H-MARGIN-size+2,W-MARGIN+2,H-MARGIN+2], fill=c)

def wrap_text(text, font_obj, max_width, draw):
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = (current+" "+word).strip()
        bbox = draw.textbbox((0,0), test, font=font_obj)
        if bbox[2]-bbox[0] <= max_width:
            current = test
        else:
            if current: lines.append(current)
            current = word
    if current: lines.append(current)
    return lines

def draw_multiline(draw, lines, x, y, font_obj, color, line_gap=16):
    cy = y
    for line in lines:
        draw.text((x,cy), line, fill=color, font=font_obj)
        bbox = draw.textbbox((0,0), line, font=font_obj)
        cy += (bbox[3]-bbox[1])+line_gap
    return cy

def draw_slide_number(draw, num, total, f_tiny):
    txt = f"{num:02d} / {total:02d}"
    draw.text((W-MARGIN-80, H-MARGIN-20), txt, fill=GRAY, font=f_tiny)

def render_cover(s, cfg):
    img, draw = new_canvas()
    draw_grid(draw)
    draw_corner_marks(draw)
    f_tag  = font("InstrumentSans-Bold.ttf", 24)
    f_week = font("GeistMono-Regular.ttf", 26)
    f_head = font("BigShoulders-Bold.ttf", 106)
    f_sub  = font("WorkSans-Regular.ttf", 34)
    f_tiny = font("GeistMono-Regular.ttf", 22)
    f_pill = font("InstrumentSans-Regular.ttf", 22)

    draw_gradient_bar(draw, MARGIN, MARGIN, W-MARGIN*2, 5, ACCENT, ACCENT2)
    draw.text((MARGIN, MARGIN+30), f"SEMANA  {cfg.get('week','2026')} \u2014 MARKETING DIGITAL + IA", fill=GRAY, font=f_week)
    draw.text((W//2-220, 180), cfg.get('week','26').split('/')[0], fill=(13,15,32), font=font("BigShoulders-Bold.ttf", 520))

    tag_y = MARGIN+80
    draw_tag(draw, MARGIN, tag_y, "MARKETING DIGITAL + IA", f_tag, bg=ACCENT, fg=BG_DARK)

    cy = tag_y+90
    lines = s["headline"].split("\n")
    colors = [WHITE, WHITE, ACCENT]
    for i, line in enumerate(lines):
        draw.text((MARGIN, cy), line, fill=colors[min(i,2)], font=f_head)
        cy += 106

    draw_accent_line(draw, MARGIN, cy+8, length=80, color=ACCENT2)
    sub_lines = wrap_text(s["sub"], f_sub, W-MARGIN*2, draw)
    draw_multiline(draw, sub_lines, MARGIN, cy+36, f_sub, GRAY, line_gap=10)

    topics_y = H-MARGIN-160
    draw.text((MARGIN, topics_y), "NESTA SEMANA \u2192", fill=GRAY, font=f_tag)
    topics = cfg.get("cover_topics", [s["headline"].split("\n")[0] for s in cfg.get("slides",[])])
    tx, ty = MARGIN, topics_y+42
    for t in topics[:6]:
        bbox = draw.textbbox((0,0), t, font=f_pill)
        tw = bbox[2]-bbox[0]
        if tx+tw+32 > W-MARGIN:
            tx = MARGIN; ty += 36
        draw.rounded_rectangle([tx,ty,tx+tw+20,ty+30], radius=4, fill=(18,22,48))
        draw.text((tx+10, ty+5), t, fill=(100,110,160), font=f_pill)
        tx += tw+30

    draw_gradient_bar(draw, MARGIN, H-MARGIN-4, W-MARGIN*2, 4, ACCENT2, ACCENT)
    draw.text((MARGIN, H-MARGIN-36), "@roquetrafegopagoo", fill=(55,60,90), font=f_tiny)
    draw_slide_number(draw, 1, 8, f_tiny)
    return img

def render_standard(s, num, total=8):
    img, draw = new_canvas()
    draw_grid(draw)
    draw_corner_marks(draw)
    f_tag     = font("InstrumentSans-Bold.ttf", 22)
    f_head    = font("BigShoulders-Bold.ttf", 88)
    f_sub     = font("WorkSans-Regular.ttf", 32)
    f_stat    = font("BigShoulders-Bold.ttf", 110)
    f_stat_lb = font("InstrumentSans-Regular.ttf", 26)
    f_tiny    = font("GeistMono-Regular.ttf", 22)

    tag_color = tuple(s.get("tag_color", [0,200,255]))
    fg = WHITE if tag_color != ACCENT else BG_DARK

    draw_gradient_bar(draw, MARGIN, MARGIN, W-MARGIN*2, 4, ACCENT, ACCENT2)
    tag_y = MARGIN+28
    draw_tag(draw, MARGIN, tag_y, s["tag"], f_tag, bg=tag_color, fg=fg)
    draw.text((W-MARGIN-60, MARGIN+10), f"{num:02d}", fill=(35,40,70), font=font("BigShoulders-Bold.ttf", 140))

    head_y = tag_y+80
    cy = head_y
    for i, line in enumerate(s["headline"].split("\n")):
        draw.text((MARGIN, cy), line, fill=(WHITE if i<2 else ACCENT), font=f_head)
        cy += 90

    draw_accent_line(draw, MARGIN, cy+12, length=60, color=GRAY)

    if "stat" in s:
        stat_x = W-MARGIN-300
        draw.text((stat_x, head_y+20), s["stat"], fill=tag_color, font=f_stat)
        draw.text((stat_x, head_y+135), s.get("stat_label",""), fill=GRAY, font=f_stat_lb)

    sub_lines = wrap_text(s["sub"], f_sub, W-MARGIN*2, draw)
    draw_multiline(draw, sub_lines, MARGIN, cy+40, f_sub, GRAY, line_gap=10)

    draw_gradient_bar(draw, MARGIN, H-MARGIN-4, W-MARGIN*2, 4, ACCENT2, ACCENT)
    draw.text((MARGIN, H-MARGIN-36), "@roquetrafegopagoo", fill=(55,60,90), font=f_tiny)
    draw_slide_number(draw, num, total, f_tiny)
    return img

def render_cta(s, num, total=8):
    img, draw = new_canvas()
    for r in range(500, 0, -20):
        alpha = int(6*(1-r/500))
        glow = Image.new("RGB",(W,H),(0,0,0))
        gd = ImageDraw.Draw(glow)
        cx,cy_ = W//2, H//2
        gd.ellipse([cx-r,cy_-r,cx+r,cy_+r], fill=(0,40,80))
        img = Image.blend(img, glow, alpha/255)
        draw = ImageDraw.Draw(img)

    draw_grid(draw)
    draw_corner_marks(draw)

    f_tag    = font("InstrumentSans-Bold.ttf", 24)
    f_head   = font("BigShoulders-Bold.ttf", 96)
    f_sub    = font("WorkSans-Regular.ttf", 30)
    f_action = font("BigShoulders-Bold.ttf", 52)
    f_portal = font("BigShoulders-Bold.ttf", 48)
    f_tiny   = font("GeistMono-Regular.ttf", 22)

    draw_gradient_bar(draw, MARGIN, MARGIN, W-MARGIN*2, 5, ACCENT, ACCENT2)
    tag_y = MARGIN+28
    draw_tag(draw, MARGIN, tag_y, s["tag"], f_tag, bg=ACCENT, fg=BG_DARK)

    cy = tag_y+80
    colors = [WHITE, WHITE, ACCENT]
    for i, line in enumerate(s["headline"].split("\n")):
        draw.text((MARGIN, cy), line, fill=colors[min(i,2)], font=f_head)
        cy += 96

    draw_accent_line(draw, MARGIN, cy+10, length=80, color=GRAY)
    cy += 28

    actions = [
        ("CURTA", "para mais pessoas verem!", (0,200,255)),
        ("COMENTA", "o que voc\u00ea mais usa de IA.", (120,80,255)),
        ("SEGUE", "@roquetrafegopagoo", (0,200,120)),
    ]
    box_h, box_gap = 68, 14
    for i, (action, desc, color) in enumerate(actions):
        bx, by = MARGIN, cy+i*(box_h+box_gap)
        draw.rounded_rectangle([bx,by,W-MARGIN,by+box_h], radius=8, fill=(14,18,38))
        draw.rounded_rectangle([bx,by,bx+6,by+box_h], radius=3, fill=color)
        draw.text((bx+22, by+10), action, fill=color, font=f_action)
        bbox = draw.textbbox((0,0), action, font=f_action)
        draw.text((bx+22+bbox[2]-bbox[0]+16, by+22), desc, fill=GRAY, font=f_sub)

    cy += len(actions)*(box_h+box_gap)+24
    draw_gradient_bar(draw, MARGIN, cy, W-MARGIN*2, 5, ACCENT2, ACCENT)
    cy += 16
    draw.text((MARGIN, cy), "Acesse o arsenal completo \u2192", fill=GRAY, font=f_sub)
    cy += 40
    draw.text((MARGIN, cy), s.get("portal","agenciaroque.com.br"), fill=ACCENT, font=f_portal)

    draw_gradient_bar(draw, MARGIN, H-MARGIN-4, W-MARGIN*2, 4, ACCENT2, ACCENT)
    draw.text((MARGIN, H-MARGIN-36), "@roquetrafegopagoo", fill=(55,60,90), font=f_tiny)
    draw_slide_number(draw, num, num, f_tiny)
    return img

def generate(config_path):
    with open(config_path, encoding='utf-8') as f:
        cfg = json.load(f)

    out = cfg["output_dir"]
    os.makedirs(out, exist_ok=True)

    content_slides = cfg.get("slides", [])
    total = len(content_slides) + 2  # cover + content + cta

    cover_slide = {
        "headline": cfg.get("headline_cover", "MARKETING DIGITAL\nO QUE MUDOU\nESSA SEMANA"),
        "sub": cfg.get("sub_cover", "Acompanhe as novidades de Marketing Digital e Intelig\u00eancia Artificial."),
    }

    paths = []

    img = render_cover(cover_slide, cfg)
    p = os.path.join(out, "slide_01.png")
    img.save(p, "PNG", dpi=(300,300))
    paths.append(p)
    print(f"OK slide_01.png")

    for i, s in enumerate(content_slides):
        num = i+2
        img = render_standard(s, num, total)
        p = os.path.join(out, f"slide_{num:02d}.png")
        img.save(p, "PNG", dpi=(300,300))
        paths.append(p)
        print(f"OK slide_{num:02d}.png")

    cta_slide = {
        "tag": "AG\u00caNCIA ROQUE",
        "headline": "Achou \u00fatil?\nEnt\u00e3o faz\nalguma coisa:",
        "portal": "agenciaroque.com.br",
    }
    num = total
    img = render_cta(cta_slide, num, total)
    p = os.path.join(out, f"slide_{num:02d}.png")
    img.save(p, "PNG", dpi=(300,300))
    paths.append(p)
    print(f"OK slide_{num:02d}.png")

    print(json.dumps({"paths": paths}))
    return paths

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python slide_generator.py <config.json>")
        sys.exit(1)
    generate(sys.argv[1])
