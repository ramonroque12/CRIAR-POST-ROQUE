# -*- coding: utf-8 -*-
"""
news_fetcher.py - Busca noticias sobre Tráfego Pago + IA
Fontes: feeds RSS diretos + Google News RSS.
Filtro estrito: apenas artigos de marketing digital / IA aplicada.
Enriquecimento via Claude API: transforma headlines crus em slides PT-BR completos.
"""
import os, re, requests, random, unicodedata, json
from xml.etree import ElementTree
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Feeds RSS diretos — tech BR + IA + marketing digital
DIRECT_FEEDS = [
    "https://tecnoblog.net/feed/",
    "https://www.canaltech.com.br/rss/",
    "https://olhardigital.com.br/feed/",
    "https://www.tecmundo.com.br/rss.xml",
    "https://forbes.com.br/feed/",
    "https://resultadosdigitais.com.br/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
]

# Máximo de dias de idade para aceitar um artigo
MAX_AGE_DAYS = 10

# Palavras-chave FORTES — pelo menos UMA deve estar no TÍTULO para passar
# Removidas as genéricas curtas (" ia ", "de ia", etc.) que causavam falsos positivos
TITLE_KEYWORDS = [
    # IA — termos fortes e específicos
    "inteligência artificial", "inteligencia artificial",
    "chatgpt", "openai", "anthropic", "gemini", "copilot",
    "gpt-4", "gpt-5", "gpt4", "gpt5", "llm", "deepseek",
    "claude ai", "claude 3", "claude 4", "claude sonnet", "claude opus",
    "perplexity", "midjourney", "stable diffusion",
    "sam altman", "jensen huang", "grok", "mistral", "llama",
    # Plataformas de Tráfego Pago — termos fortes
    "meta ads", "facebook ads", "instagram ads",
    "google ads", "tiktok ads", "youtube ads",
    "performance max", "advantage+", "smart bidding",
    "tráfego pago", "trafego pago",
    # Marketing Digital + IA — combinações específicas
    "marketing digital", "ia no marketing", "ia para marketing",
    "automação com ia", "criativo com ia", "copy com ia",
    "anúncio com ia", "campanha com ia",
    # IA aplicada a negócios
    "ia generativa", "inteligência generativa",
    "agente de ia", "agentes de ia",
]

# Títulos com qualquer um desses termos são SEMPRE bloqueados
# independente de ter keyword de IA
TITLE_BLOCKLIST = [
    # Hardware / gadgets
    "power bank", "powerbank", "bateria", "carregador", "fone de ouvido", "headphone",
    "smartwatch", "tablet", "gpu", "placa de vídeo", "monitor", "teclado",
    "processador", "memória ram", "ssd", "hd externo", "impressora",
    "câmera fotográfica", "drone", "óculos vr", "realidade virtual",
    "mah", "wh ", "watts",
    # Celulares / marcas
    "samsung", "iphone", "android", "xiaomi", "motorola",
    "pixel ", "galaxy s", "one plus", "redmi",
    # OS / Software genérico
    "windows 11", "windows 10", "macos",
    # Crypto / finanças fora do nicho
    "bitcoin", "ethereum", "criptomoeda", "nft", "blockchain",
    # Conteúdo de entretenimento / lifestyle
    "netflix", "spotify", "steam", "playstation", "xbox", "nintendo",
    "gasolina", "combustível",
    # Termos de e-commerce / oferta / datas antigas
    "em oferta", "menor preço", "melhor custo", "vale a pena comprar",
    "fique sem", "não fique", "confira", "desconto",
    "black friday", "black friday 2024", "cyber monday",
    "prime day", "liquidação",
    # Política sem relação com marketing
    "trump nomeia", "trump anuncia", "governo federal", "senado", "câmara dos",
    "ministério", "presidente lula", "eleições",
    # Assuntos de RH/empregos genéricos sem tech
    "currículo opcional", "processo seletivo", "vaga de emprego",
]

# Queries para Google News RSS — focadas no nicho, variedade garante rotação
GOOGLE_QUERIES = [
    "ChatGPT OpenAI novidades 2026",
    "Claude Anthropic IA novidades",
    "Gemini Google IA marketing 2026",
    "Meta Ads inteligência artificial automação 2026",
    "Google Ads Performance Max IA 2026",
    "tráfego pago inteligência artificial 2026",
    "marketing digital IA ferramentas 2026",
    "OpenAI GPT lançamento novidade",
    "Meta AI ferramenta marketing digital",
    "TikTok Ads IA automação 2026",
]

NAMESPACES = {
    "media":   "http://search.yahoo.com/mrss/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc":      "http://purl.org/dc/elements/1.1/",
}

GOOGLE_RSS = "https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"


def _is_recent(item, max_days=MAX_AGE_DAYS):
    """Retorna True se o artigo foi publicado nos últimos max_days dias."""
    pub = item.findtext("pubDate", "") or item.findtext("{http://purl.org/dc/elements/1.1/}date", "")
    if not pub:
        return True  # sem data, aceita (benefício da dúvida)
    try:
        dt = parsedate_to_datetime(pub)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - dt
        return age.days <= max_days
    except Exception:
        return True


def _norm(s):
    s = unicodedata.normalize('NFKD', (s or '').lower())
    s = re.sub(r'[^a-z0-9 ]', '', s)
    return re.sub(r' +', ' ', s).strip()


def clean_desc(desc, title=""):
    if not desc:
        return ""
    desc = re.sub(r'^Forbes[^\n\.]{0,80}mundo\.?\s*', '', desc, flags=re.IGNORECASE).strip()
    desc = re.sub(r'^(Tecnoblog|Canaltech|TecMundo|Olhar Digital)[^\n\.]{0,60}\.?\s*', '', desc, flags=re.IGNORECASE).strip()
    desc = re.sub(r'\s+O pos\w*\b.*$', '', desc, flags=re.IGNORECASE).strip()
    desc = re.sub(r'[\s,\.]+\b[A-Z]\b\s*$', '', desc).strip()
    desc = re.sub(r'\s{2,}[A-Z][a-z]{2,30}(\s[A-Z][a-z]{2,20})*\s*$', '', desc).strip()
    desc = re.sub(r'\s+(para|de|do|da|em|com|por|e|o|a|os|as|um|uma)\s*$', '', desc, flags=re.IGNORECASE).strip()
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
    title = re.sub(r'\s*[-|]\s*[^-|]{3,40}$', '', title).strip()
    return title


def is_relevant(title, desc=""):
    """
    Retorna True SOMENTE se o título contiver pelo menos UMA keyword FORTE
    E NÃO contiver nenhuma palavra da blocklist.
    Filtro estrito: preferimos perder artigos bons a mostrar lixo.
    """
    title_lower = title.lower()
    title_norm  = _norm(title)

    # Bloqueia PRIMEIRO — se tem termo bloqueado, recusa sempre
    if any(bl in title_lower for bl in TITLE_BLOCKLIST):
        return False

    # Exige pelo menos UMA keyword forte no título
    return any(kw.lower() in title_lower for kw in TITLE_KEYWORDS)


_BAD_IMG_HOSTS = ("youtube.com", "youtu.be", "vimeo.com", "dailymotion.com",
                  "facebook.com", "twitter.com", "instagram.com")


def _is_valid_img_url(url):
    if not url or not url.startswith("http"):
        return False
    if any(h in url for h in _BAD_IMG_HOSTS):
        return False
    if any(url.lower().endswith(ext) for ext in (".gif", ".svg", ".ico", ".webm", ".mp4")):
        return False
    return True


def extract_image_from_item(item):
    mc = item.find(f"{{{NAMESPACES['media']}}}content")
    if mc is not None:
        url = mc.get("url", "")
        if _is_valid_img_url(url):
            return url

    mt = item.find(f"{{{NAMESPACES['media']}}}thumbnail")
    if mt is not None:
        url = mt.get("url", "")
        if _is_valid_img_url(url):
            return url

    enc = item.find("enclosure")
    if enc is not None:
        url = enc.get("url", "")
        if url and "image" in enc.get("type","").lower() and _is_valid_img_url(url):
            return url

    for tag in ["description", f"{{{NAMESPACES['content']}}}encoded"]:
        text = item.findtext(tag, "")
        if not text:
            continue
        for attr in ["data-src", "src"]:
            m = re.search(rf'<img[^>]+{attr}=["\']([^"\']+)["\']', text, re.IGNORECASE)
            if m and _is_valid_img_url(m.group(1)):
                return m.group(1)

    return None


def get_og_image(url, timeout=7):
    try:
        r = requests.get(url, timeout=timeout, headers=HEADERS, allow_redirects=True)
        if "google.com" in r.url:
            return None
        html = r.text[:60000]

        for pat in [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
        ]:
            m = re.search(pat, html, re.IGNORECASE)
            if m and _is_valid_img_url(m.group(1)):
                return m.group(1)

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
                if not _is_recent(item):
                    continue
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

    need_scrape = [c for c in candidates if c.get("_need_scrape")]
    def _scrape(item):
        img = get_og_image(item["source_url"], timeout=5)
        item["image_url"] = img
        print(f"[{'IMG OK' if img else 'NO IMG'}] {item['headline'][:45]}")
        return item

    if need_scrape:
        with ThreadPoolExecutor(max_workers=8) as ex:
            list(ex.map(_scrape, need_scrape))

    for c in candidates:
        if c.get("image_url") and not c.get("_need_scrape"):
            print(f"[RSS IMG] {c['headline'][:45]}")
        c.pop("_need_scrape", None)

    with_img    = [c for c in candidates if c.get("image_url")]
    without_img = [c for c in candidates if not c.get("image_url")]
    return (with_img + without_img)[:max_items]


def fetch_from_google_news(max_items=6):
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
                if not _is_recent(item):
                    continue
                title = clean_title(strip_html(item.findtext("title", "")))
                link  = item.findtext("link", "")
                raw_desc = strip_html(item.findtext("description", ""))
                raw_desc = re.sub(r'\s{2,}[A-Z].{2,40}$', '', raw_desc).strip()
                desc = clean_desc(raw_desc[:400], title)

                if not title or len(title) < 15:
                    continue
                if not is_relevant(title, desc):
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

    with_img    = [it for it in results if it.get("image_url")]
    without_img = [it for it in results if not it.get("image_url")]
    return (with_img + without_img)[:max_items]


def fetch_news_batch(max_items=6, exclude_keys=None):
    """
    Busca noticias recentes (últimos 10 dias) sobre IA + Tráfego Pago.
    exclude_keys: headlines já mostrados — nunca repete.
    Quando pool local esgota, busca queries Google News diferentes.
    """
    exclude_keys = exclude_keys or set()

    print("[NEWS] Buscando nos feeds diretos...")
    items = fetch_from_direct_feeds(max_items * 3)

    # Sempre complementa com Google News usando queries variadas
    print("[NEWS] Complementando com Google News...")
    extra = fetch_from_google_news(max_items * 2)
    existing = {it["headline"][:35].lower() for it in items}
    for ex in extra:
        key = ex["headline"][:35].lower()
        if key not in existing:
            items.append(ex)
            existing.add(key)

    print(f"[NEWS] Pool total: {len(items)} noticias relevantes.")

    # Filtra artigos já exibidos
    fresh = [it for it in items if it["headline"][:35].lower() not in exclude_keys]
    print(f"[NEWS] Fresh (nao mostrados): {len(fresh)}")

    # Double-check blocklist
    fresh = [it for it in fresh if is_relevant(it["headline"])]

    if len(fresh) < max_items:
        # Pool esgotado: busca mais queries Google News com rotação aleatória total
        print("[NEWS] Pool fresco insuficiente — buscando mais queries...")
        extra2 = fetch_from_google_news(max_items * 3)
        all_keys = {it["headline"][:35].lower() for it in fresh}
        for ex in extra2:
            key = ex["headline"][:35].lower()
            if key not in all_keys and key not in exclude_keys and is_relevant(ex["headline"]):
                fresh.append(ex)
                all_keys.add(key)

    random.shuffle(fresh)
    return fresh[:max_items]


def enrich_slides_with_ai(news_items):
    """
    Usa Claude para transformar notícias brutas em slides educativos e gerar
    legenda narrativa para o post. Retorna (news_items, ai_caption).
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("[ENRICH] ANTHROPIC_API_KEY não encontrada. Usando notícias brutas.")
        return news_items, ""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        news_text = "\n".join([
            f"{i+1}. {it['headline']}\n   {(it.get('sub') or '')[:200]}"
            for i, it in enumerate(news_items)
        ])

        prompt = f"""Você é uma agência de marketing digital de alto nível criando carrosséis virais para o Instagram @roquetrafegopago.

ESTILO: slides educativos, texto grande, sem fotos. Cada slide ENSINA algo prático — não repassa manchete.

Com base nas {len(news_items)} notícias abaixo, crie em PT-BR:

1) {len(news_items)} slides de carrossel, cada um com:
   - category: categoria em caps máx 3 palavras (ex: "META ADS", "IA NO TRAMPO", "OPENAI AGORA")
   - headline: frase de impacto em 5-8 palavras (pode usar \\n para quebrar em 2-3 linhas)
   - items: lista de 3-4 pontos explicativos, cada um com:
     - title: nome curto e direto, máx 4 palavras
     - desc: explicação prática em 1-2 frases de até 25 palavras. ENSINE o conceito, dê contexto real, use números quando existirem. Não repita o título.

2) Uma legenda narrativa para o post no Instagram com:
   - Abertura impactante em 1-2 linhas (gancho)
   - Para cada notícia: 1 parágrafo curto explicando o que mudou e o impacto prático para o gestor de tráfego
   - Fechamento com CTA (ex: "Salva esse post pra não esquecer. 👊")
   - NÃO inclua hashtags (serão adicionadas depois)
   - Tom: direto, especialista, sem exageros

REGRAS GERAIS:
- Sempre PT-BR mesmo se a notícia for em inglês
- Foco no IMPACTO PRÁTICO para gestores de tráfego pago e marketing digital
- Linguagem de quem está por dentro do mercado

Notícias:
{news_text}

Retorne APENAS JSON válido, sem markdown:
{{"caption":"...","slides":[{{"category":"...","headline":"...","items":[{{"title":"...","desc":"..."}}]}}]}}"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = message.content[0].text.strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        result   = json.loads(raw)
        enriched = result.get("slides", result) if isinstance(result, dict) else result
        ai_caption = result.get("caption", "") if isinstance(result, dict) else ""

        for i, item in enumerate(news_items):
            if i < len(enriched):
                item["headline"] = enriched[i].get("headline", item["headline"])
                item["sub"]      = enriched[i].get("sub", item.get("sub", ""))
                item["category"] = enriched[i].get("category", "MARKETING DIGITAL")
                item["items"]    = enriched[i].get("items", [])

        print(f"[ENRICH] {len(enriched)} slides enriquecidos com Claude.")
        return news_items, ai_caption

    except Exception as e:
        print(f"[ENRICH ERROR] {e}. Usando notícias brutas.")
        return news_items, ""


def build_carousel_config(news_items, output_dir, date_str, ai_caption=""):
    if not news_items:
        return None

    cover_image = next((it["image_url"] for it in news_items if it.get("image_url")), None)

    slides = []
    for it in news_items:
        hl = it["headline"]
        if len(hl) > 50:
            words = hl.split()
            mid = max(3, len(words) // 2)
            hl = " ".join(words[:mid]) + "\n" + " ".join(words[mid:])

        sub = it.get("sub", "")
        hl_plain = hl.replace("\n", " ").strip()
        hl_norm  = _norm(hl_plain)

        if sub:
            sub_norm = _norm(sub)
            if sub_norm[:len(hl_norm)] == hl_norm:
                sub = ""
            else:
                key = hl_norm[:35]
                idx = sub_norm.rfind(key)
                if idx > 15:
                    cut = int(idx * len(sub) / max(1, len(sub_norm)))
                    sub = sub[:cut].strip().rstrip(',').rstrip('.').strip()

        slides.append({
            "headline":  hl,
            "sub":       sub,
            "category":  it.get("category", "MARKETING DIGITAL"),
            "items":     it.get("items", []),
        })

    AIDA_COVERS = [
        {
            "headline": "Tráfego Pago +\nIA: o que mudou\nessa semana?",
            "sub":      "As notícias que todo gestor de tráfego precisa saber antes de rodar campanha. Deslize →",
        },
        {
            "headline": "Meta, Google e\nIA: resumo da\nsemana",
            "sub":      "O que está mudando no tráfego pago com inteligência artificial — e o que fazer agora.",
        },
        {
            "headline": "Quem entender\nisso agora vai\nescalar mais.",
            "sub":      "Novidades de IA que estão mudando o Meta Ads, Google Ads e o marketing digital em 2026.",
        },
        {
            "headline": "Para de perder\nnotícias de IA\ne tráfego pago.",
            "sub":      "Tudo que aconteceu essa semana — resumido para você agir em menos de 2 min.",
        },
        {
            "headline": "IA + Tráfego\nPago: o que os\ngestores top usam",
            "sub":      "Veja o que está funcionando essa semana nos anúncios com inteligência artificial.",
        },
        {
            "headline": "Meta Ads e IA:\no que mudou e\ncomo usar agora",
            "sub":      "As novidades da semana que impactam diretamente quem anuncia no Meta e Google.",
        },
        {
            "headline": "Essa semana a\nIA surpreendeu\naté os experts.",
            "sub":      "Novidades de ChatGPT, Meta, Google e mais — resumido para você tomar ação.",
        },
        {
            "headline": "Você ainda\nestá anunciando\nsem IA em 2026?",
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
        "ai_caption":      ai_caption,
    }


if __name__ == "__main__":
    import json
    news = fetch_news_batch(6)
    print("\n=== RESULTADO ===")
    for i, n in enumerate(news, 1):
        print(f"{i}. {n['headline'][:70]}")
        print(f"   sub: {n['sub'][:80]}")
        print(f"   img: {bool(n['image_url'])}")
