import streamlit as st
import requests
import cloudscraper
from howlongtobeatpy import HowLongToBeat
import re
import pickle
import os
import json
from translations import TRANSLATIONS, COUNTRY_TO_LANG, get_lang_from_ip

# --- 🧪 KONFİGÜRASYON ---
STEAM_API_KEY = "E722F690EA2642D98FA54A973F703860"
ITAD_API_KEY = "fb00f3da8717cec28c29230c6751e795aaeec8d6"
RAWG_API_KEY = "d0cc05e711884b91911e36cb2f2e44cc"
IGDB_CLIENT_ID = "2bugrxp3scbr1l493je0fgex1mop4h"
IGDB_CLIENT_SECRET = "j400fdeqok9biwj8x879k980iuz8ue"

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Gamer's Archive v4.2", page_icon="🏛️", layout="centered")

# --- 📖 KISALTMALAR ---
KISALTMALAR = {
    "hades": "Hades", "hades 2": "Hades II", "gta 5": "Grand Theft Auto V",
    "rdr 2": "Red Dead Redemption 2", "gow": "God of War", "fifa": "EA SPORTS FC 24"
}

# --- 💾 VERİ YÖNETİMİ ---
DB_FILE = "oyun_kutuphanem_v5_17.pkl"

def verileri_kaydet():
    data = {
        'backlog_dict': st.session_state.backlog_dict,
        'completed': list(set(st.session_state.completed)),
        'categories': st.session_state.categories
    }
    with open(DB_FILE, 'wb') as f:
        pickle.dump(data, f)

def verileri_yukle():
    for key in ['backlog_dict', 'completed', 'categories']:
        if key not in st.session_state:
            if key == 'backlog_dict': st.session_state.backlog_dict = {"Genel": []}
            elif key == 'categories': st.session_state.categories = ["Genel", "RPG", "FPS", "Açık Dünya", "Vazgeçilenler"]
            else: st.session_state[key] = []
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'rb') as f:
                data = pickle.load(f)
                for k, v in data.items(): st.session_state[k] = v
        except: pass

verileri_yukle()

# --- 🌍 LOKALIZASYON ---
LOCALE_CONFIG = {
    "tr": {"cc": "TR", "lang": "turkish", "currency": "TRY", "symbol": "TL", "itad_country": "TR"},
    "de": {"cc": "DE", "lang": "german",  "currency": "EUR", "symbol": "€",  "itad_country": "DE"},
    "es": {"cc": "ES", "lang": "spanish", "currency": "EUR", "symbol": "€",  "itad_country": "ES"},
    "fr": {"cc": "FR", "lang": "french",  "currency": "EUR", "symbol": "€",  "itad_country": "FR"},
    "ja": {"cc": "JP", "lang": "japanese","currency": "JPY", "symbol": "¥",  "itad_country": "JP"},
    "en_uk": {"cc": "GB", "lang": "english", "currency": "GBP", "symbol": "£",  "itad_country": "GB"},
    "en": {"cc": "US", "lang": "english", "currency": "USD", "symbol": "$",  "itad_country": "US"},
}

def get_locale():
    return LOCALE_CONFIG.get(st.session_state.get("lang", "en"), LOCALE_CONFIG["en"])

# --- 🌍 DİL SİSTEMİ ---
if "lang" not in st.session_state:
    st.session_state.lang = get_lang_from_ip()

def T(key):
    return TRANSLATIONS[st.session_state.lang].get(key, TRANSLATIONS["en"].get(key, key))

# --- 🎯 EPIC GAMES FİYAT (ITAD v3) ---
def get_epic_price(game_name):
    clean_name = re.sub(r'\(.*?\)|[:™®]', '', game_name).strip()
    try:
        lookup = requests.get(
            "https://api.isthereanydeal.com/games/lookup/v1",
            params={"key": ITAD_API_KEY, "title": clean_name},
            timeout=5
        ).json()
        if not lookup.get('game'):
            return "N/A"
        game_id = lookup['game']['id']
        locale = get_locale()
        prices = requests.post(
            "https://api.isthereanydeal.com/games/prices/v3",
            params={"key": ITAD_API_KEY, "country": locale["itad_country"]},
            json=[game_id],
            timeout=5
        ).json()
        if prices and isinstance(prices, list):
            for item in prices:
                for deal in item.get('deals', []):
                    if deal.get('shop', {}).get('id') == 16:
                        amount = deal['price']['amount']
                        deal_currency = deal['price'].get('currency', locale['currency'])
                        if deal_currency == 'USD':
                            return f"${amount:.2f}"
                        else:
                            # USD karşılığını döviz kurundan hesapla
                            try:
                                kur = requests.get('https://api.exchangerate-api.com/v4/latest/USD').json()['rates'].get(deal_currency, 1)
                                usd = amount / kur
                                return f"{amount:.0f} {locale['symbol']} (${usd:.2f})"
                            except:
                                return f"{amount:.0f} {locale['symbol']}"
    except: pass
    return "N/A"

# --- 🎮 GAME PASS KONTROLÜ (Microsoft Catalog API) ---
def check_gamepass(game_name):
    try:
        r = requests.get(
            "https://catalog.gamepass.com/sigls/v2?id=fdd9e2a7-0fee-49f6-ad69-4354098401ff&language=tr-TR&market=TR",
            timeout=10
        )
        game_ids = [item['id'] for item in r.json() if 'id' in item]
        ids_str = ",".join(game_ids)
        r2 = requests.get(
            f"https://displaycatalog.mp.microsoft.com/v7.0/products?bigIds={ids_str}&market=TR&languages=tr-TR&MS-CV=DGU1mcuYo0WMMp",
            timeout=15
        )
        products = r2.json().get('Products', [])
        for p in products:
            if p.get('LocalizedProperties'):
                title = p['LocalizedProperties'][0]['ProductTitle']
                if game_name.lower() in title.lower():
                    return True
    except: pass
    return False

# --- 🎮 PS PLUS KONTROLÜ (Yerel JSON) ---
def check_psplus(game_name):
    try:
        with open("psplus_games.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        games = data.get("games", [])
        return any(game_name.lower() in g.lower() or g.lower() in game_name.lower() for g in games)
    except: pass
    return False

# --- PS LOCALE ---
PS_LOCALE = {
    "tr": ("TR", "tr", "tr-tr"),
    "de": ("DE", "de", "de-de"),
    "es": ("ES", "es", "es-es"),
    "fr": ("FR", "fr", "fr-fr"),
    "ja": ("JP", "ja", "ja-jp"),
    "en_uk": ("GB", "en", "en-gb"),
    "en": ("US", "en", "en-us"),
}

# --- 🎮 PS STORE FİYAT + MEVCUT MU (PlayStation Store API) ---
def get_ps_data(game_name):
    lang = st.session_state.get("lang", "en")
    country, lang_code, store_locale = PS_LOCALE.get(lang, ("US", "en", "en-us"))
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(
            f"https://store.playstation.com/store/api/chihiro/00_09_000/tumbler/{country}/{lang_code}/999/{requests.utils.quote(game_name)}?suggested_size=5&mode=game",
            headers=headers, timeout=10
        )
        links = r.json().get('links', [])
        skip_words = ['dlc', "friend's pass", 'upgrade', 'soundtrack']
        
        for l in links:
            name = l.get('name', '').lower()
            if game_name.lower() in name and not any(w in name for w in skip_words):
                price = l.get('default_sku', {}).get('display_price', '')
                ps_url = f"https://store.playstation.com/{store_locale}/search/{requests.utils.quote(game_name)}"
                if price:
                    return {"available": True, "price": price, "url": ps_url}
                else:
                    return {"available": True, "price": None, "url": ps_url}
    except: pass
    return {"available": False, "price": None, "url": None}

# --- 🎮 IGDB TOKEN ---
def get_igdb_token():
    if 'igdb_token' not in st.session_state:
        try:
            r = requests.post(
                "https://id.twitch.tv/oauth2/token",
                params={
                    "client_id": IGDB_CLIENT_ID,
                    "client_secret": IGDB_CLIENT_SECRET,
                    "grant_type": "client_credentials"
                },
                timeout=10
            )
            st.session_state.igdb_token = r.json().get('access_token')
        except:
            st.session_state.igdb_token = None
    return st.session_state.igdb_token

# --- 🖥️ IGDB PLATFORM BİLGİSİ ---
def get_igdb_platforms(game_name):
    try:
        token = get_igdb_token()
        if not token: return []
        r = requests.post(
            "https://api.igdb.com/v4/games",
            headers={
                "Client-ID": IGDB_CLIENT_ID,
                "Authorization": f"Bearer {token}",
                "Content-Type": "text/plain"
            },
            data=f'search "{game_name}"; fields platforms.name; limit 1;',
            timeout=10
        )
        results = r.json()
        if results:
            return [p['name'] for p in results[0].get('platforms', [])]
    except: pass
    return []

# --- ⭐ METACRITIC (IGDB API) ---
def get_metacritic(game_name):
    try:
        token = get_igdb_token()
        if not token: return "N/A"
        clean = re.sub(r'[™®]', '', game_name).strip()
        r = requests.post(
            "https://api.igdb.com/v4/games",
            headers={
                "Client-ID": IGDB_CLIENT_ID,
                "Authorization": f"Bearer {token}",
                "Content-Type": "text/plain"
            },
            data=f'search "{clean}"; fields name,aggregated_rating; limit 5;',
            timeout=10
        )
        results = r.json()
        if results:
            # En iyi isim eşleşmesini bul
            for game in results:
                if clean.lower() in game['name'].lower() or game['name'].lower() in clean.lower():
                    if game.get('aggregated_rating'):
                        return str(round(game['aggregated_rating']))
            # Eşleşme yoksa ilk sonucu dön
            if results[0].get('aggregated_rating'):
                return str(round(results[0]['aggregated_rating']))
    except: pass
    return "N/A"

# --- 🎯 AKSİYON MANTIĞI ---
@st.dialog("🎯 Oyun Yönetimi")  # dialog title translated at runtime
def kategori_degistir_dialog(game):
    st.write(f"**{game}**")
    current_cat = next((c for c in st.session_state.categories if game in st.session_state.backlog_dict.get(c, [])), "Genel")
    yeni_cat = st.selectbox(T("category_label"), st.session_state.categories, index=st.session_state.categories.index(current_cat))
    c_upd, c_rem = st.columns(2)
    if c_upd.button(T("update_button"), use_container_width=True):
        for c in list(st.session_state.backlog_dict.keys()):
            if game in st.session_state.backlog_dict[c]: st.session_state.backlog_dict[c].remove(game)
        st.session_state.backlog_dict.setdefault(yeni_cat, []).append(game)
        verileri_kaydet(); st.query_params.clear(); st.rerun()
    if c_rem.button(T("remove_button"), type="primary", use_container_width=True):
        for c in list(st.session_state.backlog_dict.keys()):
            if game in st.session_state.backlog_dict[c]: st.session_state.backlog_dict[c].remove(game)
        if game in st.session_state.completed: st.session_state.completed.remove(game)
        verileri_kaydet(); st.query_params.clear(); st.rerun()

params = st.query_params
if "act" in params:
    action, game = params["act"], params["game"]
    if action == "move_ui": kategori_degistir_dialog(game)
    elif action == "undo_done":
        if game in st.session_state.completed:
            st.session_state.completed.remove(game)
            st.session_state.backlog_dict.setdefault("Genel", []).append(game)
        verileri_kaydet(); st.query_params.clear(); st.rerun()
    else:
        for c in list(st.session_state.backlog_dict.keys()):
            if game in st.session_state.backlog_dict[c]: st.session_state.backlog_dict[c].remove(game)
        if game in st.session_state.completed: st.session_state.completed.remove(game)
        if action == "done": st.session_state.completed.append(game)
        verileri_kaydet(); st.query_params.clear(); st.rerun()

# --- 🎨 CSS TASARIM ---
st.markdown("""<style>
    .stApp { background-color: #fcfcfc; }
    .cat-header { font-size: 1.7rem; font-weight: 900; color: #111; text-transform: uppercase; border-bottom: 3px solid #eee; margin-top: 25px; padding-bottom: 4px; }
    .sub-cat-label { font-size: 11px; font-weight: 700; color: #999; text-transform: uppercase; margin-top: 18px; margin-bottom: 6px; }
    .game-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; transition: 0.15s; }
    .game-row:hover { background: #f1f3f7; border-radius: 6px; padding-left: 5px; }
    .game-title { font-size: 15px; font-weight: 800 !important; color: #000 !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-grow: 1; }
    .icon-group { display: flex; gap: 14px; flex-shrink: 0; padding-left: 10px; }
    .nano-icon { text-decoration: none !important; color: #ccc !important; font-size: 17px; }
    div.stButton > button[key="main_btn"] { background-color: #28a745 !important; color: white !important; border-radius: 12px !important; height: 45px !important; font-weight: 700 !important; }
    .badge-card { background:#fff !important; padding: 15px 15px; border-radius: 14px; border-left: 5px solid #eee; box-shadow: 0 4px 15px rgba(0,0,0,0.04); margin-bottom: 12px; font-size: 13px; min-height: 80px; display: flex; flex-direction: column; justify-content: center; }
    .badge-label { font-size: 10px; font-weight: 700; color: #999 !important; text-transform: uppercase; margin-bottom: 4px; }
    .badge-value { font-size: 14px; font-weight: 800; color: #333 !important; }
    .tag-badge { display: inline-block; background: #f0f2f6; color: #555; border-radius: 6px; padding: 2px 8px; font-size: 10px; font-weight: 700; margin-right: 5px; margin-bottom: 5px; text-transform: uppercase; }
    .gp-badge { background-color: #107c10; color: white !important; padding: 12px; border-radius: 12px; text-align: center; font-weight: 800; font-size: 12px; margin-bottom: 15px; text-transform: uppercase; }
    .gp-badge-no { background-color: #555; color: white !important; padding: 12px; border-radius: 12px; text-align: center; font-weight: 800; font-size: 12px; margin-bottom: 15px; text-transform: uppercase; }
    .ps-badge { background-color: #003087; color: white !important; padding: 12px; border-radius: 12px; text-align: center; font-weight: 800; font-size: 12px; margin-bottom: 15px; text-transform: uppercase; }
    .ps-badge-no { background-color: #555; color: white !important; padding: 12px; border-radius: 12px; text-align: center; font-weight: 800; font-size: 12px; margin-bottom: 15px; text-transform: uppercase; }
    .section-divider { border-top: 1px solid #eee; margin: 25px 0 15px 0; }
</style>""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    # --- 🌍 DİL SEÇİCİ (küçük, üstte) ---
    lang_options = {k: f"{v['flag']} {v['name']}" for k, v in TRANSLATIONS.items()}
    selected_lang = st.selectbox(
        "",
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=list(lang_options.keys()).index(st.session_state.lang),
        key="lang_selector",
        label_visibility="collapsed"
    )
    if selected_lang != st.session_state.lang:
        st.session_state.lang = selected_lang
        st.rerun()

    st.title("🏛️ Archive")

    st.markdown(f'<p class="cat-header">{T("to_play")}</p>', unsafe_allow_html=True)
    for cat in st.session_state.categories:
        games = st.session_state.backlog_dict.get(cat, [])
        if games:
            st.markdown(f'<p class="sub-cat-label">{cat}</p>', unsafe_allow_html=True)
            for g in sorted(games):
                st.markdown(f'''<div class="game-row"><a href="/?q={g}" target="_self" class="game-title" style="text-decoration:none;">{g}</a><div class="icon-group"><a href="/?act=move_ui&game={g}" target="_self" class="nano-icon">⇄</a><a href="/?act=done&game={g}" target="_self" class="nano-icon">✓</a><a href="/?act=drop&game={g}" target="_self" class="nano-icon">✕</a></div></div>''', unsafe_allow_html=True)
    if st.session_state.completed:
        st.markdown(f'<p class="cat-header" style="margin-top:50px;">{T("completed")}</p>', unsafe_allow_html=True)
        for g in sorted(st.session_state.completed):
            st.markdown(f'''<div class="game-row"><a href="/?q={g}" target="_self" class="game-title" style="text-decoration:line-through;color:#28a745 !important;font-size:15px !important;opacity:0.7;">{g}</a><div class="icon-group"><a href="/?act=undo_done&game={g}" target="_self" class="nano-icon">↩</a></div></div>''', unsafe_allow_html=True)

    # --- 🛠️ KATEGORİ YÖNETİMİ ---
    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
    with st.expander(T("category_management")):
        new_c = st.text_input(T("new_category"), key="new_cat_in")
        if st.button(T("add_button"), use_container_width=True) and new_c:
            if new_c not in st.session_state.categories:
                st.session_state.categories.append(new_c)
                st.session_state.backlog_dict[new_c] = []
                verileri_kaydet(); st.rerun()

    # --- 🎯 ÖNERİ SİSTEMİ ---
    with st.expander(T("recommendation_title")):
        PUAN_ARALIK = {
            "95+": (95, 100), "90-94": (90, 94), "85-89": (85, 89),
            "80-84": (80, 84), "75-79": (75, 79), "70-74": (70, 74), "60-69": (60, 69)
        }
        h = T("hours")
        SURE_ARALIK = {
            T("all_durations"): None,
            f"0-5 {h}": (0, 5), f"6-10 {h}": (6, 10), f"11-15 {h}": (11, 15),
            f"16-20 {h}": (16, 20), f"21-30 {h}": (21, 30), f"31-50 {h}": (31, 50), f"50+ {h}": (51, 999)
        }
        ETIKETLER = {
            "Singleplayer": 31, "Multiplayer": 7, "Co-op": 18, "RPG": 24,
            "Open World": 36, "Story Rich": 118, "Atmospheric": 13, "Horror": 16,
            "Sci-fi": 32, "Fantasy": 64, "Difficult": 49, "FPS": 30, "Sandbox": 37, "Funny": 4
        }

        puan_sec = st.multiselect(T("rec_score"), list(PUAN_ARALIK.keys()), max_selections=3, key="rec_puan")
        sure_sec = st.selectbox(T("rec_duration"), list(SURE_ARALIK.keys()), key="rec_sure")
        etiket_sec = st.multiselect(T("rec_tags"), list(ETIKETLER.keys()), max_selections=3, key="rec_etiket")

        if st.button(T("rec_button"), use_container_width=True, key="rec_btn"):
            if not puan_sec:
                st.warning(T("rec_no_results"))
            else:
                # Seçilen puan aralıklarını birleştir
                puan_min = min(PUAN_ARALIK[p][0] for p in puan_sec)
                puan_max = max(PUAN_ARALIK[p][1] for p in puan_sec)
                tag_ids = ",".join([str(ETIKETLER[e]) for e in etiket_sec]) if etiket_sec else None

                with st.spinner(T("rec_searching")):
                    try:
                        params = {
                            "key": RAWG_API_KEY,
                            "metacritic": f"{puan_min},{puan_max}",
                            "page_size": 15,
                            "ordering": "-metacritic",
                        }
                        if tag_ids: params["tags"] = tag_ids

                        r = requests.get("https://api.rawg.io/api/games", params=params, timeout=10).json()
                        results = r.get('results', [])

                        # Arşivdeki oyunları topla
                        tum_arsiv = set()
                        for cat_games in st.session_state.backlog_dict.values():
                            tum_arsiv.update([g.lower() for g in cat_games])
                        tum_arsiv.update([g.lower() for g in st.session_state.completed])

                        gosterilen = 0
                        for oyun in results:
                            if gosterilen >= 5: break
                            isim = oyun['name']
                            puan = oyun.get('metacritic', 'N/A')
                            arsivde = isim.lower() in tum_arsiv
                            isaretci = " ✅" if arsivde else ""

                            # Süre filtresi (HLTB) - Tüm Süreler seçiliyse atla
                            sure_aralik = SURE_ARALIK[sure_sec]
                            if sure_aralik is not None:
                                try:
                                    hltb_r = HowLongToBeat().search(isim)
                                    if hltb_r:
                                        sure = max(hltb_r, key=lambda x: x.similarity).main_story
                                        if sure and not (sure_aralik[0] <= sure <= sure_aralik[1]):
                                            continue
                                except: pass

                            st.markdown(f'''<div class="game-row" style="padding: 6px 0; border-bottom: 1px solid #f0f0f0;">
                                <span style="font-size:13px; font-weight:700; color:#000;">{isim}{isaretci}</span>
                                <span style="font-size:11px; color:#999; font-weight:600;">{puan}</span>
                            </div>''', unsafe_allow_html=True)
                            gosterilen += 1

                        if gosterilen == 0:
                            st.info(T("rec_no_results"))
                    except Exception as e:
                        st.error(T("rec_error"))

# --- ANA AKIŞ ---
st.markdown(f'<h2 style="margin-bottom:0.5rem;">🏛️ {T("app_title")}</h2>', unsafe_allow_html=True)
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
# Sidebar'dan tıklanınca ?q= parametresini al
q_param = st.query_params.get("q", "")
oyun_in = st.text_input(T("search_label"), value=q_param, placeholder=T("search_placeholder"))

if oyun_in:
    try:
        t = KISALTMALAR.get(oyun_in.lower().strip(), oyun_in)
        s_res = requests.get(f"https://store.steampowered.com/api/storesearch/?term={t}&l=turkish&cc=TR").json()
        if s_res and s_res['items']:
            all_r = [i for i in s_res['items'] if "soundtrack" not in i['name'].lower() and "dlc" not in i['name'].lower()]
            if all_r:
                # İsim benzerliğine göre sırala - tam eşleşme üste gelsin
                def isim_skoru(item):
                    isim = item['name'].lower().strip()
                    arama = t.lower().strip()
                    if isim == arama: return 0               # Tam eşleşme
                    if isim.startswith(arama + ' '): return 1 # Başlangıç eşleşmesi (Hades II)
                    if arama in isim: return 2               # İçeriyor
                    return 3                                  # Diğer
                all_r = sorted(all_r, key=isim_skoru)
                if 'last_query' not in st.session_state or st.session_state.last_query != t:
                    st.session_state.current_game = all_r[0]; st.session_state.last_query = t
                cols = st.columns(min(len(all_r), 3))
                for idx, item in enumerate(all_r[:3]):
                    if cols[idx].button(item['name'], key=f"sel_{item['id']}", use_container_width=True):
                        st.session_state.current_game = item; st.rerun()
    except: pass

if 'current_game' in st.session_state and st.session_state.current_game:
    o = st.session_state.current_game
    app_id, temiz_isim = o['id'], o['name']
    st.image(f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg", use_container_width=True)

    # Etiketler
    try:
        det = requests.get(f"https://store.steampowered.com/api/appdetails?appids={app_id}&l=turkish").json()
        if det[str(app_id)]['success']:
            data = det[str(app_id)]['data']
            tags = [g['description'] for g in data.get('genres', [])]
            if len(tags) < 5: tags.extend([c['description'] for c in data.get('categories', [])])
            tags_html = "".join([f'<span class="tag-badge">{t}</span>' for t in tags[:5]])
            st.markdown(f'<div style="margin-top: -10px; margin-bottom: 10px;">{tags_html}</div>', unsafe_allow_html=True)
    except: pass

    st.subheader(temiz_isim)

    # Arşive Ekle / Güncelle
    existing_cat = next((c for c in st.session_state.categories if temiz_isim in st.session_state.backlog_dict.get(c, [])), None)
    c_cat, c_add = st.columns([1, 1])
    sel_cat = c_cat.selectbox(T("category_label"), st.session_state.categories, index=st.session_state.categories.index(existing_cat) if existing_cat else 0, label_visibility="collapsed")
    if c_add.button(T("update_button") if existing_cat else T("add_to_archive"), key="main_btn", use_container_width=True):
        for c in list(st.session_state.backlog_dict.keys()):
            if temiz_isim in st.session_state.backlog_dict[c]: st.session_state.backlog_dict[c].remove(temiz_isim)
        st.session_state.backlog_dict.setdefault(sel_cat, []).append(temiz_isim)
        verileri_kaydet(); st.rerun()

    # Abonelikler (API ile)
    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    sub1, sub2 = st.columns(2)

    with st.spinner(""):
        gp = check_gamepass(temiz_isim)
        ps_data = get_ps_data(temiz_isim)
        psplus = check_psplus(temiz_isim)

    if gp:
        sub1.markdown(f'<div class="gp-badge">{T("gamepass_yes")}</div>', unsafe_allow_html=True)
    else:
        sub1.markdown(f'<div class="gp-badge-no">{T("gamepass_no")}</div>', unsafe_allow_html=True)

    if psplus:
        sub2.markdown(f'<div class="ps-badge">{T("psplus_yes")}</div>', unsafe_allow_html=True)
    elif ps_data["available"]:
        sub2.markdown(f'<div class="ps-badge-no">{T("psplus_no")}</div>', unsafe_allow_html=True)
    else:
        sub2.markdown(f'<div class="ps-badge-no">{T("psplus_no")}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # Mağaza Fiyatları
    st.markdown(f"<p style='font-size:11px;font-weight:800;color:#999;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px;'>💰 {T("prices_title")}</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    try:  # Steam
        locale = get_locale()
        kur_r = requests.get(f"https://api.exchangerate-api.com/v4/latest/USD").json()['rates']
        kur = kur_r.get(locale["currency"], 1)
        f_usd = o.get('price', {}).get('final', 0) / 100
        f_local = f_usd * kur
        if locale["currency"] == "USD":
            price_str = f"${f_usd:.2f}"
        elif locale["currency"] == "JPY":
            price_str = f"{f_local:.0f}{locale['symbol']} (${f_usd:.2f})"
        else:
            price_str = f"{f_local:.2f}{locale['symbol']} (${f_usd:.2f})"
        c1.markdown(f'<div class="badge-card" style="border-left-color:#1b2838"><span class="badge-label">Steam</span><span class="badge-value">{price_str}</span></div>', unsafe_allow_html=True)
    except: pass

    # PS Store fiyatı (API ile)
    ps_search_url = f"https://store.playstation.com/tr-tr/search/{requests.utils.quote(temiz_isim)}"
    if ps_data.get("price"):
        c2.markdown(f'<div class="badge-card" style="border-left-color:#003087"><span class="badge-label">PS Store</span><span class="badge-value">{ps_data["price"]}</span></div>', unsafe_allow_html=True)
    elif ps_data.get("available"):
        c2.markdown(f'<div class="badge-card" style="border-left-color:#003087"><span class="badge-label">PS Store</span><span class="badge-value"><a href="{ps_search_url}" target="_blank" style="color:#003087;text-decoration:none;font-size:13px;">Mağazada Gör →</a></span></div>', unsafe_allow_html=True)
    else:
        c2.markdown('<div class="badge-card" style="border-left-color:#003087"><span class="badge-label">PS Store</span><span class="badge-value">N/A</span></div>', unsafe_allow_html=True)

    # Epic Games fiyatı (ITAD)
    c3.markdown(f'<div class="badge-card" style="border-left-color:#333"><span class="badge-label">Epic Store</span><span class="badge-value">{get_epic_price(temiz_isim)}</span></div>', unsafe_allow_html=True)

    # Puanlar
    st.markdown(f"<p style='font-size:11px;font-weight:800;color:#999;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px;margin-top:10px;'>⭐ {T('scores_title')}</p>", unsafe_allow_html=True)
    s1, s2 = st.columns(2)
    try:
        r_r = requests.get(f"https://store.steampowered.com/appreviews/{app_id}?json=1&language=all").json()
        s1.markdown(f'<div class="badge-card" style="border-left-color:#28a745"><span class="badge-label">Steam Puanı</span><span class="badge-value">%{int((r_r["query_summary"]["total_positive"]/r_r["query_summary"]["total_reviews"])*100)} Olumlu</span></div>', unsafe_allow_html=True)
    except: pass

    # Metacritic (RAWG API ile)
    meta = get_metacritic(temiz_isim)
    s2.markdown(f'<div class="badge-card" style="border-left-color:#ffcc33"><span class="badge-label">Metascore</span><span class="badge-value">{meta}{"/100" if meta != "N/A" else ""}</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # HLTB
    st.markdown(f"<p style='font-size:11px;font-weight:800;color:#999;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px;'>⏱️ {T('duration_title')}</p>", unsafe_allow_html=True)
    try:
        hltb = HowLongToBeat().search(re.sub(r'\(.*?\)|[:™®]', '', temiz_isim).strip())
        if hltb:
            b = max(hltb, key=lambda x: x.similarity)
            def fmt_sure(s):
                try:
                    s = float(s)
                    if s <= 0: return "N/A"
                    frac = s % 1
                    if frac < 0.25: return f"{int(s)}h"
                    elif frac < 0.75: return f"{int(s)}.5h"
                    else: return f"{int(s)+1}h"
                except: return "N/A"
            h1, h2, h3 = st.columns(3)
            h1.success(f"**{T('main_story')}**\n{fmt_sure(b.main_story)}")
            h2.warning(f"**{T('extra')}**\n{fmt_sure(b.main_extra)}")
            h3.error(f"**{T('completionist')}**\n{fmt_sure(b.completionist)}")
    except: pass