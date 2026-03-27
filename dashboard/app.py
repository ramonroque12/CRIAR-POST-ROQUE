# -*- coding: utf-8 -*-
"""
Roque Content Hub - Dashboard de Publicação Automática
"""
import os, sys, json, sqlite3, subprocess, requests, threading, uuid
from flask import Flask, render_template, jsonify, request, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from news_fetcher import fetch_news_batch, build_carousel_config, enrich_slides_with_ai, fetch_and_enrich_with_web_search

# Rastreia headlines ja mostradas na sessao para evitar repeticao
_shown_headlines: set = set()
_SHOWN_MAX = 60  # reseta depois de 60 itens acumulados

# Jobs assíncronos de geração
_jobs: dict = {}

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
SLIDES_ROOT = os.path.join(BASE_DIR, "..", "slides")

# Carrega .env automaticamente se existir
_env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(_env_path):
    with open(_env_path, encoding="utf-8") as _ef:
        for _line in _ef:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())
DB_PATH            = os.path.join(BASE_DIR, "posts.db")
GENERATOR          = os.path.join(BASE_DIR, "slide_generator_cyberpulse.py")
GENERATOR_METAADS  = os.path.join(BASE_DIR, "slide_generator_metaads.py")

ZERNIO_KEY     = "sk_8ce15a5d1c7a69631d059f6b05db4107426d1c40b3d10ef587c5a19bd6cb2b6c"
INSTAGRAM_ID   = "69c407166cb7b8cf4c9ac812"
FACEBOOK_ID    = "69c406ff6cb7b8cf4c9ac7b7"
REDDIT_ID      = "69c407286cb7b8cf4c9ac85e"
THREADS_ID     = "69c5304f6cb7b8cf4ca00954"
TIKTOK_ID      = "69c58a976cb7b8cf4ca181cb"
ZERNIO_BASE    = "https://zernio.com/api/v1"

PLATFORM_IDS = {
    "instagram": INSTAGRAM_ID,
    "facebook":  FACEBOOK_ID,
    "reddit":    REDDIT_ID,
    "threads":   THREADS_ID,
    "tiktok":    TIKTOK_ID,
}

app = Flask(__name__, template_folder="templates")
app.config["TEMPLATES_AUTO_RELOAD"] = True
scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
scheduler.start()

# ── Themes ────────────────────────────────────────────────────────────────────
THEMES = [
    {
        "id": "meta_ia",
        "topic": "Meta Ads + IA: As novidades desta semana",
        "label": "META ADS + IA",
        "color": "#4267B2",
        "headline_cover": "META ADS + IA:\nO QUE MUDOU\nESSA SEMANA",
        "sub_cover": "Tudo que está mudando no Meta Ads com Inteligência Artificial e como isso afeta quem anuncia.",
        "cover_topics": ["Advantage+ IA","Copy Automática","Segmentação IA","Criativos IA","CPL -40%","Stack Completa"],
        "slides": [
            {"tag":"META ADS + IA","tag_color":[66,103,178],
             "headline":"Meta Ads cria\nanúncios sozinha\ncom IA",
             "sub":"Você manda o produto, a IA cria as imagens, os textos e testa tudo automaticamente. Não precisa mais fazer isso na mão.",
             "stat":"50+","stat_label":"anúncios gerados por IA"},
            {"tag":"ADVANTAGE+ IA","tag_color":[66,103,178],
             "headline":"Advantage+ testa\n150 criativos\nao mesmo tempo",
             "sub":"A IA da Meta distribui o orçamento para os anúncios que estão convertendo mais. Sem ajuste manual.",
             "stat":"150","stat_label":"criativos testados ao mesmo tempo"},
            {"tag":"COPY COM IA","tag_color":[66,103,178],
             "headline":"IA escreve o texto\ndo seu anúncio\nautomaticamente",
             "sub":"Novo recurso do Meta cria várias versões de copy para seu produto e testa qual converte mais antes de gastar todo o orçamento.",
             "stat":"+32%","stat_label":"mais cliques com copy gerada por IA"},
            {"tag":"SEGMENTAÇÃO IA","tag_color":[66,103,178],
             "headline":"Meta usa IA para\nencontrar quem\nquer comprar",
             "sub":"O Advantage+ Audience analisa comportamento e encontra compradores que você não teria encontrado com segmentação manual.",
             "stat":"+45%","stat_label":"mais conversões vs. segmentação manual"},
            {"tag":"CRIATIVOS IA","tag_color":[66,103,178],
             "headline":"Como fazer um\ncriativo em 5 min\ncom IA em 2026",
             "sub":"Stack: ChatGPT para o texto, Midjourney para a imagem, CapCut para o vídeo. Resultado profissional sem agência.",
             "stat":"5min","stat_label":"para criar um criativo completo"},
            {"tag":"RESULTADO REAL","tag_color":[66,103,178],
             "headline":"Afiliados estão\nreduzindo CPL com\nIA no Meta Ads",
             "sub":"Gestores que adotaram IA para criação de criativos e copy relatam redução significativa no custo por lead.",
             "stat":"-40%","stat_label":"menos custo por lead com IA"},
        ]
    },
    {
        "id": "google_ia",
        "topic": "Google Ads + IA: Performance Max e novidades",
        "label": "GOOGLE ADS + IA",
        "color": "#4285F4",
        "headline_cover": "GOOGLE ADS + IA:\nO QUE MUDOU\nESSA SEMANA",
        "sub_cover": "Performance Max, Smart Bidding e Gemini: como a IA está mudando o Google Ads e o que fazer agora.",
        "cover_topics": ["Performance Max","Smart Bidding","Gemini no Ads","AI Overview","+28% ROAS","4 ações hoje"],
        "slides": [
            {"tag":"GOOGLE ADS + IA","tag_color":[66,133,244],
             "headline":"Google Ads decide\nsozinho onde\ncolocar seu anúncio",
             "sub":"Com Performance Max, o Google distribui seu anúncio em busca, YouTube, Maps e Display automaticamente onde vai gerar mais vendas.",
             "stat":"+28%","stat_label":"mais retorno em média"},
            {"tag":"PERFORMANCE MAX","tag_color":[66,133,244],
             "headline":"Como configurar\nPerformance Max\ndo jeito certo",
             "sub":"Manda bons criativos, define a conversão correta e deixa a IA trabalhar. Quanto mais dados, mais rápido o Google aprende.",
             "stat":"90d","stat_label":"para IA otimizar completamente"},
            {"tag":"IA E LANCES","tag_color":[66,133,244],
             "headline":"Smart Bidding: IA\najusta seus lances\nem tempo real",
             "sub":"O Google analisa mais de 70 sinais por leilão: hora, dispositivo, localização e histórico. E ajusta o lance automaticamente.",
             "stat":"70+","stat_label":"sinais analisados por leilão"},
            {"tag":"BUSCA COM IA","tag_color":[66,133,244],
             "headline":"AI Overview muda\ncomo as pessoas\nencontram produtos",
             "sub":"O AI Overview do Google aparece antes dos anúncios normais. Quem não adaptar a estratégia vai perder visibilidade.",
             "stat":"25%","stat_label":"das buscas já mostram AI Overview"},
            {"tag":"GEMINI NO ADS","tag_color":[66,133,244],
             "headline":"Gemini IA está\ndentro do Google\nAds agora",
             "sub":"O Gemini sugere keywords, cria anúncios e gera relatórios de desempenho diretamente na plataforma. Sem sair do painel.",
             "stat":"3x","stat_label":"mais rápido criar campanhas"},
            {"tag":"DICA PRÁTICA","tag_color":[66,133,244],
             "headline":"4 ações para não\nficar para trás\nno Google Ads",
             "sub":"1. Ative Performance Max. 2. Use Smart Bidding com meta de ROAS. 3. Faça anúncios responsivos. 4. Alimente com dados de conversão.",
             "stat":"4","stat_label":"ações para implementar hoje"},
        ]
    },
    {
        "id": "ferramentas_ia",
        "topic": "5 Ferramentas de IA que todo afiliado precisa usar",
        "label": "FERRAMENTAS IA",
        "color": "#7850FF",
        "headline_cover": "5 FERRAMENTAS\nDE IA PARA\nAFILIADOS",
        "sub_cover": "As ferramentas que afiliados profissionais estão usando para criar criativos, textos e vídeos em escala com IA.",
        "cover_topics": ["ChatGPT copy","Midjourney imagens","Opus Clip vídeo","ElevenLabs voz","Perplexity nicho","R$260/mês tudo"],
        "slides": [
            {"tag":"FERRAMENTAS IA","tag_color":[120,80,255],
             "headline":"ChatGPT: escreve\ntodo o texto do\nseu anúncio",
             "sub":"Use o ChatGPT para criar headlines, copys, scripts de vídeo e e-mails. Descreva seu produto e peça 10 opções. Escolha a melhor.",
             "stat":"#1","stat_label":"ferramenta de copy com IA"},
            {"tag":"IA PARA IMAGENS","tag_color":[120,80,255],
             "headline":"Midjourney cria\nimagens de anúncio\nprofissionais",
             "sub":"Gere imagens de produto, banners e fotos de estilo de vida sem fotografia. Qualidade profissional por uma fração do custo.",
             "stat":"30s","stat_label":"para gerar uma imagem profissional"},
            {"tag":"IA PARA VÍDEO","tag_color":[120,80,255],
             "headline":"Opus Clip corta\nvídeos longos em\nclips virais",
             "sub":"Cola o link do seu vídeo longo e o Opus Clip encontra os melhores momentos, adiciona legenda e exporta no formato certo.",
             "stat":"10x","stat_label":"mais conteúdo com o mesmo vídeo"},
            {"tag":"IA PARA VOZ","tag_color":[120,80,255],
             "headline":"ElevenLabs faz\nnarração profissional\nsem gravar nada",
             "sub":"Digite o texto, escolha uma voz e baixe o áudio pronto. Perfeito para vídeos de anúncio, VSL e reels sem precisar aparecer.",
             "stat":"28","stat_label":"idiomas e centenas de vozes"},
            {"tag":"IA PARA PESQUISA","tag_color":[120,80,255],
             "headline":"Perplexity acha\nos melhores nichos\npara anunciar",
             "sub":"Pesquise tendências, concorrentes e o que as pessoas estão buscando. Mais rápido e completo que o Google para pesquisa de nicho.",
             "stat":"5min","stat_label":"para pesquisar um nicho completo"},
            {"tag":"STACK COMPLETA","tag_color":[120,80,255],
             "headline":"Quanto custa usar\ntodas essas\nferramentas de IA",
             "sub":"ChatGPT Plus: R$100/mês. Midjourney: R$50/mês. Opus Clip: R$80/mês. ElevenLabs: R$30/mês. Perplexity: Grátis. Total: R$260/mês.",
             "stat":"R$260","stat_label":"por mês para a stack completa"},
        ]
    },
    {
        "id": "tiktok_ia",
        "topic": "TikTok Ads + IA: Escale sem aparecer na câmera",
        "label": "TIKTOK ADS + IA",
        "color": "#FF0050",
        "headline_cover": "TIKTOK ADS + IA:\nESCALE SEM\nAPARECER",
        "sub_cover": "Como usar as ferramentas de IA do TikTok para criar anúncios profissionais sem aparecer na câmera.",
        "cover_topics": ["TikTok Symphony","Avatar Digital","CPM -35%","15-30s ideal","Script IA","3x engajamento"],
        "slides": [
            {"tag":"TIKTOK ADS + IA","tag_color":[255,0,80],
             "headline":"TikTok Symphony:\nIA que grava\nanúncios por você",
             "sub":"A suite de IA do TikTok cria um avatar digital com sua voz, faz a narração e adiciona legenda. Você não precisa aparecer nem gravar nada.",
             "stat":"100%","stat_label":"criativo feito por IA"},
            {"tag":"AVATAR DIGITAL","tag_color":[255,0,80],
             "headline":"Como criar um\navatar digital para\nseus anúncios",
             "sub":"No TikTok Symphony Studio, escolha um avatar pré-feito ou crie o seu. Escreva o roteiro e a IA apresenta o produto como um apresentador real.",
             "stat":"5min","stat_label":"para criar um vídeo de anúncio"},
            {"tag":"CUSTO NO TIKTOK","tag_color":[255,0,80],
             "headline":"TikTok Ads ainda\né mais barato que\nMeta Ads em 2026",
             "sub":"CPM médio no TikTok ainda é menor que no Meta, especialmente para públicos jovens de 18-35 anos. Oportunidade antes de todo mundo entrar.",
             "stat":"-35%","stat_label":"CPM vs. Meta Ads"},
            {"tag":"CONTEÚDO VIRAL","tag_color":[255,0,80],
             "headline":"O formato que\nmais converte no\nTikTok em 2026",
             "sub":"Vídeos de 15-30 segundos com problema + solução + CTA direto. IA cria 10 variações do mesmo vídeo para testar qual converte mais.",
             "stat":"15-30s","stat_label":"duração ideal de anúncio"},
            {"tag":"IA E SCRIPT","tag_color":[255,0,80],
             "headline":"Roteiro certo faz\no anúncio vender\nno TikTok",
             "sub":"Fórmula: 1. Chame atenção nos 3 primeiros segundos. 2. Mostre o problema. 3. Apresente a solução. 4. Faça o CTA. IA cria isso em segundos.",
             "stat":"3s","stat_label":"para prender atenção ou perder"},
            {"tag":"RESULTADOS","tag_color":[255,0,80],
             "headline":"Afiliados que\nestão faturando\ncom TikTok Ads",
             "sub":"Nicho de saúde, beleza e finanças têm os melhores resultados no TikTok. CPL baixo, público engajado e menos concorrência que no Meta.",
             "stat":"3x","stat_label":"mais engajamento vs. Meta"},
        ]
    },
    {
        "id": "automacao_ia",
        "topic": "Automação com IA: Gerencie mais sem contratar",
        "label": "AUTOMAÇÃO + IA",
        "color": "#00C878",
        "headline_cover": "AUTOMAÇÃO + IA:\nGERENCIE MAIS\nSEM CONTRATAR",
        "sub_cover": "Como afiliados profissionais estão usando IA para escalar campanhas sem aumentar a equipe.",
        "cover_topics": ["10x campanhas","Relatório 2min","30 criativos 1h","Presell 10min","Otimização auto","Rotina 30min"],
        "slides": [
            {"tag":"AUTOMAÇÃO + IA","tag_color":[0,200,120],
             "headline":"Como gerenciar\n10 campanhas com\n1 pessoa só",
             "sub":"Com as ferramentas certas de IA, um gestor consegue monitorar e otimizar 10x mais campanhas do que faria manualmente.",
             "stat":"10x","stat_label":"mais campanhas por pessoa"},
            {"tag":"IA E RELATÓRIOS","tag_color":[0,200,120],
             "headline":"IA cria relatório\nde resultados em\n2 minutos",
             "sub":"Cole os dados da campanha no ChatGPT e peça uma análise. Ele identifica o que está funcionando, o que não está e o que fazer.",
             "stat":"2min","stat_label":"para um relatório completo com IA"},
            {"tag":"CRIATIVOS EM ESCALA","tag_color":[0,200,120],
             "headline":"Como criar 30\ncriativos em 1 hora\ncom IA",
             "sub":"1. ChatGPT gera 10 textos diferentes. 2. Midjourney cria 10 imagens. 3. CapCut combina tudo em 10 vídeos. 30 criativos em 1 hora.",
             "stat":"30","stat_label":"criativos em 1 hora com IA"},
            {"tag":"PRESELL COM IA","tag_color":[0,200,120],
             "headline":"IA escreve sua\npresell do zero\nem 10 minutos",
             "sub":"Dê o link do produto para o ChatGPT e peça uma presell de 500 palavras. Revise, ajuste o tom e publique. Sem precisar ser copywriter.",
             "stat":"10min","stat_label":"para uma presell pronta com IA"},
            {"tag":"OTIMIZAÇÃO AUTO","tag_color":[0,200,120],
             "headline":"IA identifica qual\nanúncio vai escalar\nantes de você",
             "sub":"Ferramentas de IA analisam padrões de CTR, CPC e CVR para identificar criativos vencedores antes do orçamento acabar.",
             "stat":"48h","stat_label":"para IA identificar o criativo vencedor"},
            {"tag":"ROTINA IA","tag_color":[0,200,120],
             "headline":"Rotina diária de\n30 minutos com\nIA para afiliados",
             "sub":"Manhã: revisar dados com IA (10min). Tarde: criar 5 criativos com IA (15min). Noite: agendar posts e ajustar lances (5min).",
             "stat":"30min","stat_label":"rotina diária completa com IA"},
        ]
    },
    {
        "id": "youtube_ia",
        "topic": "YouTube Ads + IA: Scripts que vendem mais",
        "label": "YOUTUBE ADS + IA",
        "color": "#FF0000",
        "headline_cover": "YOUTUBE ADS + IA:\nSCRIPTS QUE\nVENDEM MAIS",
        "sub_cover": "Como usar IA para criar roteiros de vídeo, escalar criativos e reduzir o custo por lead no YouTube Ads.",
        "cover_topics": ["Script IA 3min","VSL com IA","Opus Clip cortes","3x mais rápido","CPV -25%","Formato ideal"],
        "slides": [
            {"tag":"YOUTUBE ADS + IA","tag_color":[255,0,0],
             "headline":"IA escreve o\nroteiro do seu\nvídeo de anúncio",
             "sub":"Ferramentas como ChatGPT e Claude criam o roteiro completo em minutos. O Opus Clip ainda corta os melhores trechos automaticamente.",
             "stat":"3x","stat_label":"mais rápido que fazer manual"},
            {"tag":"VSL COM IA","tag_color":[255,0,0],
             "headline":"Como criar uma VSL\nque converte usando\nsó IA e texto",
             "sub":"1. ChatGPT escreve o roteiro. 2. ElevenLabs faz a narração. 3. CapCut monta o vídeo com imagens do Midjourney. VSL pronta sem câmera.",
             "stat":"0h","stat_label":"de gravação necessária"},
            {"tag":"SCRIPT VENCEDOR","tag_color":[255,0,0],
             "headline":"Fórmula do script\nque mais converte\nno YouTube Ads",
             "sub":"Hook (5s) + Problema (15s) + Agitação (20s) + Solução (30s) + Prova social (20s) + CTA (10s). Total: 100 segundos. IA monta tudo.",
             "stat":"100s","stat_label":"estrutura do vídeo ideal"},
            {"tag":"TESTE A/B IA","tag_color":[255,0,0],
             "headline":"Como testar 5\nversões do mesmo\nvídeo com IA",
             "sub":"Mude apenas o hook nos primeiros 5 segundos. IA gera 5 opções de abertura diferentes. Teste todas com orçamento pequeno e escale a vencedora.",
             "stat":"5","stat_label":"variações do mesmo anúncio"},
            {"tag":"CUSTO POR VIEW","tag_color":[255,0,0],
             "headline":"Como reduzir CPV\nno YouTube Ads\ncom IA",
             "sub":"Vídeos com hook forte têm maior retenção e menor CPV. IA analisa os primeiros segundos do seu vídeo e sugere como melhorar o hook.",
             "stat":"-25%","stat_label":"CPV médio com hook otimizado por IA"},
            {"tag":"ESCALA YOUTUBE","tag_color":[255,0,0],
             "headline":"YouTube Ads em\ndólar: como escalar\npara mercado gringo",
             "sub":"Com IA para tradução e localização, afiliados brasileiros estão escalando campanhas em inglês para produtos com comissões em dólar.",
             "stat":"5x","stat_label":"comissão maior em produtos em dólar"},
        ]
    },
]

# ── Database ──────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS posts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            topic       TEXT NOT NULL,
            caption     TEXT,
            slide_dir   TEXT,
            image_urls  TEXT,
            status      TEXT DEFAULT "draft",
            platforms   TEXT DEFAULT '["instagram","facebook"]',
            scheduled_at TEXT,
            published_at TEXT,
            post_url    TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )''')
        for k, v in [("autopilot_enabled","false"),("autopilot_hour","19"),
                     ("autopilot_minute","00"),("theme_rotation","0")]:
            conn.execute("INSERT OR IGNORE INTO settings VALUES (?,?)", (k,v))
        conn.commit()

init_db()

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_setting(key, default=""):
    with get_db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default

def set_setting(key, value):
    with get_db() as conn:
        conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, str(value)))
        conn.commit()

def upload_image(file_path):
    """Upload image to catbox.moe and return public URL"""
    try:
        with open(file_path, "rb") as f:
            r = requests.post("https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": (os.path.basename(file_path), f, "image/png")},
                timeout=60)
        if r.status_code == 200 and r.text.strip().startswith("https://"):
            return r.text.strip()
    except Exception as e:
        print(f"[UPLOAD ERROR] {e}")
    return None

CAPTION_LIMITS = {
    "instagram": 2100,
    "tiktok":    2100,
    "threads":   480,
    "facebook":  60000,
    "reddit":    40000,
}

def _trim_caption(caption, limit):
    if len(caption) <= limit:
        return caption
    # Corta no último parágrafo completo antes do limite
    cut = caption[:limit].rfind("\n\n")
    if cut > limit // 2:
        return caption[:cut].strip() + "\n\n..."
    return caption[:limit - 3].strip() + "..."

def publish_to_zernio(image_urls, caption, platforms):
    headers = {
        "Authorization": f"Bearer {ZERNIO_KEY}",
        "Content-Type": "application/json"
    }

    platforms_payload = []
    for p in platforms:
        if p not in PLATFORM_IDS:
            continue
        limit = CAPTION_LIMITS.get(p, 2100)
        platforms_payload.append({
            "platform":  p,
            "accountId": PLATFORM_IDS[p],
            "content":   _trim_caption(caption, limit),
        })

    if not platforms_payload:
        return {"error": "No valid platforms selected"}

    payload = {
        "content": _trim_caption(caption, 2100),
        "mediaItems": [{"type": "image", "url": u} for u in image_urls],
        "platforms": platforms_payload,
        "publishNow": True
    }
    try:
        r = requests.post(f"{ZERNIO_BASE}/posts",
                         headers=headers, json=payload, timeout=180)
        print(f"[ZERNIO] Status: {r.status_code} | Response: {r.text[:300]}")
        return r.json()
    except Exception as e:
        print(f"[ZERNIO ERROR] {e}")
        return {"error": str(e)}

def build_caption(topic, slides=None, ai_caption=""):
    hashtags = (
        "#MarketingDigital #InteligenciaArtificial #TrafegoPago "
        "#MetaAds #GoogleAds #GoogleAds #AgenciaRoque"
    )
    footer = "📲 Siga @roquetrafegopagoo para mais!\n🔗 Portal completo: agenciaroque.com.br"
    if ai_caption and ai_caption.strip():
        return f"{ai_caption.strip()}\n\n{footer}\n\n{hashtags}"
    if slides:
        bullets = "\n".join(
            "👉 " + (s.get("headline","").replace("\n"," ")[:68])
            for s in slides if s.get("headline")
        )
        return f"{bullets}\n\n{footer}\n\n{hashtags}"
    return f"{footer}\n\n{hashtags}"

def do_generate(cfg_data):
    """Generate slides from a config dict. Accepts THEMES entry or news-based config."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(SLIDES_ROOT, f"post_{ts}")
    os.makedirs(out_dir, exist_ok=True)

    cfg = {**cfg_data,
           "week": datetime.now().strftime("%d/%m/%Y"),
           "output_dir": out_dir}
    cfg_path = os.path.join(out_dir, "config.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False)

    result = subprocess.run(
        [sys.executable, "-X", "utf8", GENERATOR, cfg_path],
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)

    slides = sorted([
        f for f in os.listdir(out_dir)
        if f.startswith("slide_") and f.endswith(".png")
    ])

    topic = cfg_data.get("topic", cfg_data.get("topic", "Carrossel IA"))
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO posts (topic, slide_dir, status, platforms) VALUES (?,?,?,?)",
            (topic, out_dir, "draft", '["instagram","facebook","tiktok","threads"]')
        )
        post_id = cur.lastrowid
        conn.commit()

    ai_caption = cfg_data.get("ai_caption", "")
    return post_id, slides, out_dir, ai_caption

def do_publish(post_id, platforms_override=None, caption_override=None):
    """Upload slides and publish via Zernio"""
    with get_db() as conn:
        post = conn.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    if not post:
        raise ValueError("Post not found")

    slide_dir = post["slide_dir"]
    files = sorted([
        os.path.join(slide_dir, f)
        for f in os.listdir(slide_dir)
        if f.startswith("slide_") and f.endswith(".png")
    ])

    image_urls = []
    for fp in files:
        url = upload_image(fp)
        if url:
            image_urls.append(url)

    if not image_urls:
        raise RuntimeError("Falha no upload das imagens.")

    if caption_override is not None and caption_override.strip():
        caption = caption_override
    else:
        # Tenta ler config.json do post para pegar slides e caption gerada por IA
        cfg_slides, ai_caption = None, ""
        try:
            cfg_path = os.path.join(post["slide_dir"], "config.json")
            with open(cfg_path, encoding="utf-8") as f:
                cfg = json.load(f)
            cfg_slides  = cfg.get("slides")
            ai_caption  = cfg.get("ai_caption", "")
        except Exception:
            pass
        caption = build_caption(post["topic"], slides=cfg_slides, ai_caption=ai_caption)
    platforms = platforms_override or json.loads(post["platforms"] or '["instagram","facebook","reddit","threads"]')
    resp      = publish_to_zernio(image_urls, caption, platforms)

    post_url = resp.get("post", {}).get("url", "")
    status   = "published" if "post" in resp else "failed"

    with get_db() as conn:
        conn.execute(
            "UPDATE posts SET status=?,image_urls=?,caption=?,published_at=?,post_url=? WHERE id=?",
            (status, json.dumps(image_urls), caption,
             datetime.now().isoformat(), post_url, post_id)
        )
        conn.commit()

    return {"status": status, "post_url": post_url, "image_urls": image_urls}

# ── Scheduler helpers ─────────────────────────────────────────────────────────
def publish_scheduled_job(post_id):
    with app.app_context():
        try:
            with get_db() as conn:
                row = conn.execute("SELECT caption FROM posts WHERE id=?", (post_id,)).fetchone()
            saved_caption = row["caption"] if row and row["caption"] else None
            result = do_publish(post_id, caption_override=saved_caption)
            print(f"[SCHEDULER] Post {post_id} → {result['status']}")
        except Exception as e:
            print(f"[SCHEDULER ERROR] Post {post_id}: {e}")

def autopilot_job():
    with app.app_context():
        try:
            idx = int(get_setting("theme_rotation", "0"))
            theme = THEMES[idx % len(THEMES)]
            set_setting("theme_rotation", idx + 1)
            post_id, _, _, _ = do_generate(theme)
            result = do_publish(post_id)
            print(f"[AUTOPILOT] Published post {post_id} → {result['status']}")
        except Exception as e:
            print(f"[AUTOPILOT ERROR] {e}")

def refresh_autopilot():
    try: scheduler.remove_job("autopilot")
    except: pass
    if get_setting("autopilot_enabled") == "true":
        h = int(get_setting("autopilot_hour", "19"))
        m = int(get_setting("autopilot_minute", "0"))
        scheduler.add_job(autopilot_job, "cron", day="*/2", hour=h, minute=m, id="autopilot")
        print(f"[AUTOPILOT] Activated every 2 days at {h:02d}:{m:02d}")

refresh_autopilot()

# ── Static: serve slide images ────────────────────────────────────────────────
@app.route("/slides/<path:filename>")
def serve_slide(filename):
    return send_from_directory(SLIDES_ROOT, filename)

# ── API Routes ────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    themes_json = json.dumps([{
        "id": t["id"], "topic": t["topic"],
        "label": t["label"], "color": t["color"],
        "headline_cover": t["headline_cover"]
    } for t in THEMES], ensure_ascii=False)
    return render_template("index.html", themes_json=themes_json)

@app.route("/api/themes")
def api_themes():
    return jsonify([{
        "id": t["id"], "topic": t["topic"],
        "label": t["label"], "color": t["color"],
        "headline_cover": t["headline_cover"],
        "slides": t["slides"]
    } for t in THEMES])

@app.route("/api/posts")
def api_posts():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM posts ORDER BY created_at DESC LIMIT 50").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/posts/<int:post_id>")
def api_post_detail(post_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    post = dict(row)
    # Lista os slides do diretório
    slide_dir = post.get("slide_dir", "")
    slides = []
    if slide_dir and os.path.isdir(slide_dir):
        slides = sorted([f for f in os.listdir(slide_dir) if f.startswith("slide_") and f.endswith(".png")])
    post["slide_files"]   = slides
    post["slide_dirname"] = os.path.basename(slide_dir) if slide_dir else ""
    # Lê slides do config.json para reconstruir legenda
    cfg_slides = []
    try:
        cfg_path = os.path.join(slide_dir, "config.json")
        with open(cfg_path, encoding="utf-8") as f:
            cfg = json.load(f)
        cfg_slides = cfg.get("slides", [])
    except Exception:
        pass
    post["cfg_slides"] = cfg_slides
    return jsonify(post)

@app.route("/api/fetch-topics", methods=["GET"])
def api_fetch_topics():
    """Busca noticias reais sobre IA/Marketing Digital, sem repetir as ja mostradas."""
    global _shown_headlines
    try:
        # Reseta historico se ficou muito grande
        if len(_shown_headlines) >= _SHOWN_MAX:
            _shown_headlines = set()
            print("[NEWS] Historico resetado.")

        date_str = datetime.now().strftime("%d/%m/%Y")

        # Web search + enriquecimento em uma chamada só
        news, ai_caption = fetch_and_enrich_with_web_search(
            max_items=6, exclude_keys=_shown_headlines
        )
        if not news:
            return jsonify({"error": "Nenhuma noticia encontrada"}), 500

        # Registra headlines para evitar repetição
        for it in news:
            _shown_headlines.add(it["headline"][:35].lower())

        cfg = build_carousel_config(news, "", date_str, ai_caption=ai_caption)
        result = {
            "id":              "news_live",
            "topic":           f"IA em Pauta - {date_str}",
            "label":           "NOTICIAS AO VIVO",
            "color":           "#FF5020",
            "headline_cover":  cfg["headline_cover"],
            "sub_cover":       cfg["sub_cover"],
            "cover_image_url": cfg.get("cover_image_url"),
            "slides":          cfg["slides"],
            "ai_caption":      cfg.get("ai_caption", ""),
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.json or {}

    if "topic_data" in data:
        cfg_data = data["topic_data"]
    else:
        theme_id = data.get("theme_id")
        cfg_data = next((t for t in THEMES if t["id"] == theme_id), THEMES[0])

    job_id = uuid.uuid4().hex[:10]
    _jobs[job_id] = {"status": "running"}

    def run():
        try:
            post_id, slides, slide_dir, ai_caption = do_generate(cfg_data)
            _jobs[job_id] = {
                "status":     "done",
                "post_id":    post_id,
                "slides":     slides,
                "slide_dir":  slide_dir,
                "topic":      cfg_data.get("topic", "Carrossel IA"),
                "ai_caption": ai_caption,
            }
        except Exception as e:
            _jobs[job_id] = {"status": "failed", "error": str(e)}

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"job_id": job_id})

@app.route("/api/generate/<job_id>", methods=["GET"])
def api_generate_status(job_id):
    job = _jobs.get(job_id)
    if not job:
        return jsonify({"status": "not_found"}), 404
    return jsonify(job)

@app.route("/api/publish/<int:post_id>", methods=["POST"])
def api_publish(post_id):
    data = request.json or {}
    platforms = data.get("platforms")
    caption   = data.get("caption") or None
    try:
        result = do_publish(post_id, platforms_override=platforms, caption_override=caption)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/schedule/<int:post_id>", methods=["POST"])
def api_schedule(post_id):
    data         = request.json or {}
    scheduled_at = data.get("scheduled_at")
    platforms    = data.get("platforms", ["instagram","facebook","reddit","threads"])
    caption      = data.get("caption") or None
    if not scheduled_at:
        return jsonify({"error": "scheduled_at required"}), 400

    with get_db() as conn:
        conn.execute("UPDATE posts SET status='scheduled', scheduled_at=?, platforms=?, caption=? WHERE id=?",
                     (scheduled_at, json.dumps(platforms), caption, post_id))
        conn.commit()

    run_at = datetime.fromisoformat(scheduled_at)
    scheduler.add_job(publish_scheduled_job, "date", run_date=run_at,
                      args=[post_id], id=f"post_{post_id}", replace_existing=True)
    return jsonify({"status": "scheduled", "scheduled_at": scheduled_at})

@app.route("/api/delete/<int:post_id>", methods=["DELETE"])
def api_delete(post_id):
    try: scheduler.remove_job(f"post_{post_id}")
    except: pass
    with get_db() as conn:
        conn.execute("DELETE FROM posts WHERE id=?", (post_id,))
        conn.commit()
    return jsonify({"ok": True})

@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    if request.method == "GET":
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM settings").fetchall()
        return jsonify({r["key"]: r["value"] for r in rows})

    data = request.json or {}
    with get_db() as conn:
        for k, v in data.items():
            conn.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (k, str(v)))
        conn.commit()

    if "autopilot_enabled" in data or "autopilot_hour" in data or "autopilot_minute" in data:
        refresh_autopilot()

    return jsonify({"ok": True})

# ── Meta Ads Criativo ─────────────────────────────────────────────────────────
def _build_fallback_ad_config(topic, cta):
    return {
        "topic": topic,
        "headline_cover": f"{topic[:18].upper()}\nMUDA\nTUDO",
        "sub_cover": f"A estratégia que está gerando resultados reais com {topic}.",
        "cover_topics": ["Método", "Resultado", "Suporte", "Garantia", "Acesso", "Comunidade"],
        "slides": [
            {"aida": "ATENÇÃO",
             "headline": "Você já tentou\nde tudo e não\nconseguiu?",
             "sub": f"A maioria falha porque não tem o método certo para {topic}.",
             "stat": "73%",
             "stat_label": "das pessoas erram por falta de estratégia"},
            {"aida": "INTERESSE",
             "headline": "Existe um caminho\nmais rápido\npara chegar lá",
             "sub": "Com a abordagem certa, os resultados chegam muito mais rápido.",
             "stat": "+5.000",
             "stat_label": "pessoas já transformaram seus resultados"},
            {"aida": "DESEJO",
             "headline": "Imagine ter\nos resultados\nque você quer",
             "sub": "Mais liberdade, mais retorno, mais confiança — tudo isso está ao seu alcance.",
             "stat": "30 dias",
             "stat_label": "para ver os primeiros resultados"},
            {"aida": "DESEJO",
             "headline": "Por que isso\nfunciona quando\noutros falham",
             "sub": "Baseado em dados reais, não em teoria. Método validado com resultados comprovados.",
             "stat": "★★★★★",
             "stat_label": "avaliação de clientes"},
            {"aida": "AÇÃO",
             "headline": "Não deixe\npara amanhã\no que muda hoje",
             "sub": "Vagas limitadas. Aproveite agora.",
             "stat": "",
             "stat_label": "Oferta por tempo limitado",
             "cta": cta or "Clique e saiba mais"},
        ],
        "ai_caption": (
            f"🔥 {topic}\n\n"
            "Você ainda está buscando resultados? A maioria das pessoas falha porque não tem o método certo.\n\n"
            "✅ Método comprovado\n✅ Resultados rápidos\n✅ Suporte completo\n\n"
            f"👉 {cta or 'Clique e saiba mais'}\n\n"
            "📲 Siga @roquetrafegopagoo para mais!\n🔗 agenciaroque.com.br"
        )
    }


def generate_ad_config_with_ai(topic, objective="", target="", cta=""):
    """Usa Claude para gerar config AIDA de slides para Meta Ads."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("[AD GEN] Sem ANTHROPIC_API_KEY — usando template padrão.")
        return _build_fallback_ad_config(topic, cta)

    cta_final = cta or "Clique e saiba mais"
    prompt = f"""Você é um especialista em copywriting para Meta Ads (Facebook/Instagram).
Gere um carrossel de 5 slides de conteúdo + 1 capa usando o framework AIDA.

TEMA/PRODUTO: {topic}
OBJETIVO/CTA: {objective or cta_final}
PÚBLICO-ALVO: {target or "Pessoas interessadas no tema"}

Retorne APENAS um JSON válido, sem markdown, sem explicações:
{{
  "topic": "título curto do criativo (máx 60 chars)",
  "headline_cover": "TÍTULO\\nEM 2-3\\nLINHAS",
  "sub_cover": "Subtítulo da capa em uma frase",
  "cover_topics": ["Benefício 1","Benefício 2","Benefício 3","Benefício 4","Benefício 5","Benefício 6"],
  "slides": [
    {{
      "aida": "ATENÇÃO",
      "headline": "Headline de\\n2-3 linhas\\nque choca",
      "sub": "Texto de apoio que agita o problema em 1-2 frases curtas.",
      "stat": "73%",
      "stat_label": "das pessoas cometem esse erro"
    }},
    {{
      "aida": "INTERESSE",
      "headline": "Por que isso\\ndestrói seus\\nresultados",
      "sub": "Explica a causa raiz do problema e por que a solução é relevante.",
      "stat": "+5.000",
      "stat_label": "já usam esse método"
    }},
    {{
      "aida": "DESEJO",
      "headline": "O que você\\nconquista\\ncom isso",
      "sub": "Benefícios concretos e o resultado que o público vai ter.",
      "stat": "30 dias",
      "stat_label": "para ver resultados reais"
    }},
    {{
      "aida": "DESEJO",
      "headline": "Por que funciona\\nquando outros\\nmétodos falham",
      "sub": "Diferencial único — o que torna este produto ou serviço diferente.",
      "stat": "★★★★★",
      "stat_label": "avaliação de clientes"
    }},
    {{
      "aida": "AÇÃO",
      "headline": "Não perca\\nessa\\noportunidade",
      "sub": "Urgência e benefício final. Por que agir agora.",
      "stat": "",
      "stat_label": "Oferta por tempo limitado",
      "cta": "{cta_final}"
    }}
  ],
  "ai_caption": "Legenda persuasiva completa para Instagram/Facebook com emojis, máximo 2000 caracteres, em português BR."
}}

REGRAS: use \\n para quebras; headlines max 3 linhas; sub max 2 frases diretas; dados plausíveis; tudo em PT-BR."""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2200,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = resp.content[0].text.strip()
        raw = re.sub(r'^```(?:json)?\n?', '', raw)
        raw = re.sub(r'\n?```$', '', raw)
        return json.loads(raw)
    except Exception as e:
        print(f"[AD GEN] Erro IA: {e} — usando fallback.")
        return _build_fallback_ad_config(topic, cta_final)


def do_generate_ad(topic, objective="", target="", cta=""):
    """Gera slides Meta Ads com IA e salva no banco."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(SLIDES_ROOT, f"ad_{ts}")
    os.makedirs(out_dir, exist_ok=True)

    cfg_data = generate_ad_config_with_ai(topic, objective, target, cta)
    cfg = {**cfg_data,
           "week": datetime.now().strftime("%d/%m/%Y"),
           "output_dir": out_dir}
    cfg_path = os.path.join(out_dir, "config.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False)

    result = subprocess.run(
        [sys.executable, "-X", "utf8", GENERATOR_METAADS, cfg_path],
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)

    slides = sorted([
        f for f in os.listdir(out_dir)
        if f.startswith("slide_") and f.endswith(".png")
    ])
    topic_str = cfg_data.get("topic", topic)
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO posts (topic, slide_dir, status, platforms) VALUES (?,?,?,?)",
            (f"[AD] {topic_str}", out_dir, "draft", '["instagram","facebook"]')
        )
        post_id = cur.lastrowid
        conn.commit()

    return post_id, slides, out_dir, cfg_data.get("ai_caption", "")


@app.route("/api/generate-ad", methods=["POST"])
def api_generate_ad():
    data      = request.json or {}
    topic     = (data.get("topic") or "").strip()
    objective = (data.get("objective") or "").strip()
    target    = (data.get("target") or "").strip()
    cta       = (data.get("cta") or "").strip()

    if not topic:
        return jsonify({"error": "Informe o tema do criativo"}), 400

    job_id = uuid.uuid4().hex[:10]
    _jobs[job_id] = {"status": "running"}

    def run():
        try:
            post_id, slides, slide_dir, ai_caption = do_generate_ad(topic, objective, target, cta)
            _jobs[job_id] = {
                "status":     "done",
                "post_id":    post_id,
                "slides":     slides,
                "slide_dir":  slide_dir,
                "topic":      topic,
                "ai_caption": ai_caption,
            }
        except Exception as e:
            _jobs[job_id] = {"status": "failed", "error": str(e)}

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"job_id": job_id})


if __name__ == "__main__":
    print("=" * 50)
    print("  ROQUE CONTENT HUB  ->  http://localhost:5000")
    print("=" * 50)
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=False, host="0.0.0.0", port=port, use_reloader=False)
