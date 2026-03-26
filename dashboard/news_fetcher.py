# -*- coding: utf-8 -*-
"""
news_fetcher.py - Busca noticias sobre IA e Marketing Digital
Prioriza feeds RSS diretos de portais tech BR (com imagens reais).
Fallback: Google News RSS.
"""
import re, requests, random, unicodedata
from xml.etree import ElementTree
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Feeds RSS diretos de portais tech BR — incluem imagens nos itens
DIRECT_FEEDS = [
    "https://tecnoblog.net/feed/",
    "https://www.canaltech.com.br/rss/",
    "https://olhardigital.com.br/feed/",
    "https://www.tecmundo.com.br/rss.xml",
    "https://forbes.com.br/feed/",
]

# Palavras-chave para filtrar noticias relevantes do nicho
# Regra: pelo menos UMA keyword precisa estar no TITULO (mais restritivo)
TITLE_KEYWORDS = [
    "inteligência artificial", "inteligencia artificial",
    "chatgpt", "openai", "anthropic", "gemini", "copilot",
    "gpt-4", "gpt-5", "gpt4", "gpt5", "llm",
    "marketing digital", "tráfego pago", "trafego pago",
    "meta ads", "google ads", "tiktok ads",
    "deepseek", "deep seek", "claude ia", "perplexity",
    "sam altman", "jensen huang",
    "automação com ia", "ia no marketing", "ia para",
    "com ia", "usa ia", "de ia", "e ia", "por ia",
    " ia ", "(ia)", "ia:",
]

# Títulos que contenham essas palavras são ignorados mesmo que batam uma keyword curta
TITLE_BLOCKLIST = [
    "whatsapp", "samsung", "iphone", "android", "xiaomi", "motorola",
    "windows 11", "windows 10", "gasolina", "combustível", "celular",
    "notebook", "processador", "placa de vídeo", "monitor", "teclado",
]

# Google News RSS como complemento/fallback
GOOGLE_RSS = "https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
GOOGLE_QUERIES = [
    "inteligencia artificial marketing digital novidades",
    "ChatGPT OpenAI IA 2026",
    "Meta Google IA noticias semana",
]

NAMESPACES = {
    "media":   "http://search.yahoo.com/mrss/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc":      "http://purl.org/dc/elements/1.1/",
}

def _norm(s):
    """Normaliza string para comparação fuzzy (remove acentos, pontuação, lowercase)."""
    s = unicodedata.normalize('NFKD', (s or '').lower())
    s = re.sub(r'[^a-z0-9 ]', '', s)
    return re.sub(r' +', ' ', s).strip()

def clean_desc(desc, title=""):
    """Limpa lixo do final da descrição (site name, letra solta, 'O post', boilerplate, etc.)."""
    if not desc:
        return ""
    # Remove boilerplate do Forbes/portais no início
    desc = re.sub(r'^Forbes[^\n\.]{0,80}mundo\.?\s*', '', desc, flags=re.IGNORECASE).strip()
    desc = re.sub(r'^(Tecnoblog|Canaltech|TecMundo|Olhar Digital)[^\n\.]{0,60}\.?\s*', '', desc, flags=re.IGNORECASE).strip()
    # Remove 'O post...' ou 'O pos...' (corte no meio) que aparece no final de itens do Forbes
    desc = re.sub(r'\s+O pos\w*\b.*$', '', desc, flags=re.IGNORECASE).strip()
    # Remove letras/palavras soltas no final (ex: ". W", ", A")
    desc = re.sub(r'[\s,\.]+\b[A-Z]\b\s*$', '', desc).strip()
    # Remove nome do site no final (2+ espaços + palavra maiúscula curta)
    desc = re.sub(r'\s{2,}[A-Z][a-z]{2,30}(\s[A-Z][a-z]{2,20})*\s*$', '', desc).strip()
    # Remove se termina em preposição/artigo solto
    desc = re.sub(r'\s+(para|de|do|da|em|com|por|e|o|a|os|as|um|uma)\s*$', '', desc, flags=re.IGNORECASE).strip()
    # Garante que termina em pontuação decente ou palavra
    desc = re.sub(r'[,;\s]+$', '', desc).strip()
    return desc

def strip_html(text):
    text = re.sub(r'<[^>]+>', '', text or '')
    text = (text.replace('&nbsp;', ' ').replace('&amp;', '&')
                .replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
                .replace('&#8211;', '-').replace('&#8230;', '...'))
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_title(title):
    # Remove " - Nome do Site" suffix
    title = re.sub(r'\s*[-|]\s*[^-|]{3,40}$', '', title).strip()
    return title

def is_relevant(title, desc=""):
    title_lower = title.lower()
    # Bloqueia títulos de tech/hardware sem relação com IA/marketing
    if any(bl in title_lower for bl in TITLE_BLOCKLIST):
        # Só passa se tiver keyword forte explícita (não as genéricas de 2-3 chars)
        strong = ["inteligência artificial", "inteligencia artificial",
                  "chatgpt", "openai", "anthropic", "gemini", "copilot",
                  "gpt-4", "gpt-5", "gpt4", "gpt5", "llm", "deepseek",
                  "marketing digital", "meta ads", "google ads", "tiktok ads"]
        return any(kw in title_lower for kw in strong)
    return any(kw.lower() in title_lower for kw in TITLE_KEYWORDS)

_BAD_IMG_HOSTS = ("youtube.com", "youtu.be", "vimeo.com", "dailymotion.com",
                  "facebook.com", "twitter.com", "instagram.com")

def _is_valid_img_url(url):
    """Verifica se a URL e realmente uma imagem (nao embed de video etc)."""
    if not url or not url.startswith("http"):
        return False
    if any(h in url for h in _BAD_IMG_HOSTS):
        return False
    if any(url.lower().endswith(ext) for ext in (".gif", ".svg", ".ico", ".webm", ".mp4")):
        return False
    return True

def extract_image_from_item(item):
    """Tenta extrair URL de imagem de um item RSS (media:content, enclosure, etc)."""
    # Tenta media:content (Tecnoblog, Canaltech, etc.)
    mc = item.find(f"{{{NAMESPACES['media']}}}content")
    if mc is not None:
        url = mc.get("url", "")
        if _is_valid_img_url(url):
            return url

    # Tenta media:thumbnail
    mt = item.find(f"{{{NAMESPACES['media']}}}thumbnail")
    if mt is not None:
        url = mt.get("url", "")
        if _is_valid_img_url(url):
            return url

    # Tenta enclosure (imagem)
    enc = item.find("enclosure")
    if enc is not None:
        url = enc.get("url", "")
        if url and "image" in enc.get("type","").lower() and _is_valid_img_url(url):
            return url

    # Tenta <img src="..."> no description ou content:encoded
    for tag in ["description", f"{{{NAMESPACES['content']}}}encoded"]:
        text = item.findtext(tag, "")
        if not text:
            continue
        # Prefere data-src (lazy load) sobre src
        for attr in ["data-src", "src"]:
            m = re.search(rf'<img[^>]+{attr}=["\']([^"\']+)["\']', text, re.IGNORECASE)
            if m and _is_valid_img_url(m.group(1)):
                return m.group(1)

    return None

def get_og_image(url, timeout=7):
    """Scrapa og:image (ou imagem de artigo) de uma URL."""
    try:
        r = requests.get(url, timeout=timeout, headers=HEADERS, allow_redirects=True)
        if "google.com" in r.url:
            return None
        html = r.text[:60000]

        # Padrões meta og:image / twitter:image
        for pat in [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
        ]:
            m = re.search(pat, html, re.IGNORECASE)
            if m and _is_valid_img_url(m.group(1)):
                return m.group(1)

        # Fallback: busca imagens de artigo por dimensoes tipicas (Forbes, etc.)
        imgs = re.findall(
            r'https://[^\s"<>]+(?:860x484|1920x1080|1200x630|1200x800|768x432|800x450)[^\s"<>]*\.(?:jpg|jpeg|png|webp)',
            html, re.IGNORECASE
        )
        for img in imgs:
            if _is_valid_img_url(img):
                return img

    except Exception:
        pass
    return None

def fetch_from_direct_feeds(max_items=6):
    """Busca noticias nos feeds diretos dos portais tech."""
    seen, candidates = set(), []
    feeds = DIRECT_FEEDS[:]
    random.shuffle(feeds)

    for feed_url in feeds:
        try:
            r = requests.get(feed_url, timeout=10, headers=HEADERS)
            for prefix, uri in NAMESPACES.items():
                try:
                    ElementTree.register_namespace(prefix, uri)
                except:
                    pass
            root = ElementTree.fromstring(r.content)

            for item in root.iter("item"):
                title = clean_title(strip_html(item.findtext("title", "")))
                link  = item.findtext("link", "")
                desc  = strip_html(item.findtext("description", ""))[:600]
                desc  = clean_desc(desc, title)

                if not title or len(title) < 15:
                    continue
                if not is_relevant(title, desc):
                    continue
                key = title[:35].lower()
                if key in seen:
                    continue
                seen.add(key)

                # Tenta pegar imagem direto do RSS (instantaneo)
                img_url = extract_image_from_item(item)
                candidates.append({
                    "headline":   title,
                    "sub":        desc,
                    "image_url":  img_url,
                    "source_url": link,
                    "_need_scrape": (not img_url and bool(link) and "google.com" not in link),
                })

        except Exception as e:
            print(f"[FEED] Erro em {feed_url[:40]}: {e}")

    # Busca og:image em paralelo apenas para os que nao tem imagem do RSS
    need_scrape = [c for c in candidates if c.get("_need_scrape")]
    def _scrape(item):
        img = get_og_image(item["source_url"], timeout=5)
        item["image_url"] = img
        print(f"[{'IMG OK' if img else 'NO IMG'}] {item['headline'][:45]}")
        return item

    if need_scrape:
        with ThreadPoolExecutor(max_workers=8) as ex:
            list(ex.map(_scrape, need_scrape))

    # Loga os que já tinham imagem do RSS
    for c in candidates:
        if c.get("image_url") and not c.get("_need_scrape"):
            print(f"[RSS IMG] {c['headline'][:45]}")
        c.pop("_need_scrape", None)

    # Prioriza com imagem
    with_img    = [c for c in candidates if c.get("image_url")]
    without_img = [c for c in candidates if not c.get("image_url")]
    return (with_img + without_img)[:max_items]

def fetch_from_google_news(max_items=6):
    """Fallback: busca via Google News RSS com scraping paralelo de imagens."""
    seen, candidates = set(), []
    queries = random.sample(GOOGLE_QUERIES, min(2, len(GOOGLE_QUERIES)))

    for query in queries:
        if len(candidates) >= max_items * 2:
            break
        try:
            url = GOOGLE_RSS.format(q=requests.utils.quote(query))
            r = requests.get(url, timeout=12, headers=HEADERS)
            root = ElementTree.fromstring(r.content)

            for item in root.iter("item"):
                if len(candidates) >= max_items * 2:
                    break
                title = clean_title(strip_html(item.findtext("title", "")))
                link  = item.findtext("link", "")
                raw_desc = strip_html(item.findtext("description", ""))
                raw_desc = re.sub(r'\s{2,}[A-Z].{2,40}$', '', raw_desc).strip()
                desc = clean_desc(raw_desc[:400], title)

                if not title or len(title) < 15:
                    continue
                key = title[:35].lower()
                if key in seen:
                    continue
                seen.add(key)

                candidates.append({
                    "headline":   title,
                    "sub":        desc if desc != title else "",
                    "image_url":  None,
                    "source_url": link,
                })
        except Exception as e:
            print(f"[GNEWS] Erro: {e}")

    if not candidates:
        return []

    # Busca imagens em paralelo (timeout curto para não travar)
    def _fetch_img(item):
        link = item["source_url"]
        if link and "google.com" not in link:
            img = get_og_image(link, timeout=5)
            if img:
                item["image_url"] = img
                print(f"[GNEWS IMG OK] {item['headline'][:45]}")
            else:
                print(f"[GNEWS NO IMG] {item['headline'][:45]}")
        return item

    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(_fetch_img, candidates[:max_items * 2]))

    # Prioriza os com imagem
    with_img    = [it for it in results if it.get("image_url")]
    without_img = [it for it in results if not it.get("image_url")]
    return (with_img + without_img)[:max_items]

def fetch_news_batch(max_items=6, exclude_keys=None):
    """
    Busca noticias sobre IA/Marketing Digital.
    exclude_keys: set de chaves (headline[:35].lower()) ja mostradas — evita repeticao.
    """
    exclude_keys = exclude_keys or set()

    # Busca todos os artigos relevantes dos feeds diretos (com imagens em paralelo)
    print("[NEWS] Buscando nos feeds diretos...")
    items = fetch_from_direct_feeds(max_items * 3)

    if len(items) < max_items:
        print(f"[NEWS] {len(items)} nos feeds diretos. Complementando com Google News...")
        extra = fetch_from_google_news(pool_size - len(items))
        existing = {it["headline"][:35].lower() for it in items}
        for ex in extra:
            if ex["headline"][:35].lower() not in existing:
                items.append(ex)
                existing.add(ex["headline"][:35].lower())

    print(f"[NEWS] Pool total: {len(items)} noticias.")

    # Remove os ja mostrados
    fresh = [it for it in items if it["headline"][:35].lower() not in exclude_keys]
    print(f"[NEWS] Fresh (nao mostrados): {len(fresh)}")

    # Se nao tem suficientes, retorna o que tiver (sem restricao)
    if len(fresh) < max_items:
        print("[NEWS] Pool esgotado — retornando sem filtro de exclusao.")
        fresh = items

    # Prioriza artigos COM imagem (evita carrossel todo sem foto)
    with_img    = [it for it in fresh if it.get("image_url")]
    without_img = [it for it in fresh if not it.get("image_url")]
    random.shuffle(with_img)
    random.shuffle(without_img)
    prioritized = with_img + without_img

    return prioritized[:max_items]

def build_carousel_config(news_items, output_dir, date_str):
    """Converte lista de noticias no formato de config do slide generator."""
    if not news_items:
        return None

    cover_image = next((it["image_url"] for it in news_items if it.get("image_url")), None)

    slides = []
    for it in news_items:
        hl = it["headline"]
        # Quebra headline longa em ate 2 linhas
        if len(hl) > 50:
            words = hl.split()
            mid = max(3, len(words) // 2)
            hl = " ".join(words[:mid]) + "\n" + " ".join(words[mid:])

        sub = it.get("sub", "")
        hl_plain = hl.replace("\n", " ").strip()
        hl_norm  = _norm(hl_plain)

        if sub:
            sub_norm = _norm(sub)
            # Se sub começa igual ao título, zera
            if sub_norm[:len(hl_norm)] == hl_norm:
                sub = ""
            else:
                # Remove trecho final do sub que repete o título
                key = hl_norm[:35]
                idx = sub_norm.rfind(key)
                if idx > 15:
                    cut = int(idx * len(sub) / max(1, len(sub_norm)))
                    sub = sub[:cut].strip().rstrip(',').rstrip('.').strip()

        slides.append({
            "headline":  hl,
            "sub":       sub,
            "image_url": it.get("image_url"),
        })

    # AIDA covers — rotaciona a cada chamada (Attention → Interest → Desire → Action)
    AIDA_COVERS = [
        # A — Atenção
        {
            "headline": "A IA mudou tudo\nessa semana.\nVocê viu?",
            "sub":      "As notícias que todo mundo de marketing digital precisa saber. Deslize →",
        },
        # I — Interesse
        {
            "headline": "O que está\nmudando no mundo\nda IA agora.",
            "sub":      "Resumo semanal para quem trabalha com tráfego pago e marketing digital.",
        },
        # D — Desejo
        {
            "headline": "Quem entender\nisso agora vai\nficar à frente.",
            "sub":      "As novidades de IA que estão mudando o jogo do marketing digital em 2026.",
        },
        # A — Ação
        {
            "headline": "Para de perder\nnotícias de IA.\nVeja o resumo:",
            "sub":      "Tudo que aconteceu essa semana em IA e marketing digital — em menos de 2 min.",
        },
        # Variações extras
        {
            "headline": "Foi mais uma\nsemana insana\nno mundo da IA.",
            "sub":      "Aqui vai o resumo do que você não pode ter perdido.",
        },
        {
            "headline": "IA, marketing\ne dinheiro:\no que mudou?",
            "sub":      "As notícias da semana que impactam diretamente quem anuncia online.",
        },
        {
            "headline": "Essa semana\na IA surpreendeu\naté quem já sabia.",
            "sub":      "Novidades de ChatGPT, Meta, Google e mais — resumido para você agir.",
        },
        {
            "headline": "Você ainda\nestá competindo\ncom quem usa IA?",
            "sub":      "Veja o que os melhores gestores de tráfego estão usando essa semana.",
        },
    ]
    cover = random.choice(AIDA_COVERS)

    return {
        "headline_cover":  cover["headline"],
        "sub_cover":       cover["sub"],
        "cover_image_url": cover_image,
        "topic":           f"IA em Pauta - {date_str}",
        "week":            date_str,
        "output_dir":      output_dir,
        "slides":          slides,
    }

if __name__ == "__main__":
    import json
    news = fetch_news_batch(6)
    print("\n=== RESULTADO ===")
    for i, n in enumerate(news, 1):
        print(f"{i}. {n['headline'][:60]}")
        print(f"   sub: {n['sub'][:80]}")
        print(f"   img: {bool(n['image_url'])}")
