import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
from howlongtobeatpy import HowLongToBeat
import re
import pickle
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Gamer's Archive", page_icon="🏛️", layout="centered")

# --- 📖 KISALTMA VE TAM İSABET SÖZLÜĞÜ ---
KISALTMALAR = {
    "hades": "Hades",
    "hades 2": "Hades II",
    "hades ii": "Hades II",
    "gta 5": "Grand Theft Auto V",
    "gta v": "Grand Theft Auto V",
    "rdr 2": "Red Dead Redemption 2",
    "gow": "God of War",
    "lol": "League of Legends",
    "cod": "Call of Duty",
    "fifa": "EA SPORTS FC 24"
}

# --- HAFIZA YÖNETİMİ ---
DB_FILE = "oyun_kutuphanem.pkl"

def verileri_kaydet():
    data = {
        'backlog': list(set(st.session_state.backlog)),
        'completed': list(set(st.session_state.completed)),
        'cancelled': list(set(st.session_state.cancelled))
    }
    with open(DB_FILE, 'wb') as f: pickle.dump(data, f)

def verileri_yukle():
    for key in ['backlog', 'completed', 'cancelled']:
        if key not in st.session_state: st.session_state[key] = []
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'rb') as f:
                data = pickle.load(f)
                st.session_state.backlog = list(set(data.get('backlog', [])))
                st.session_state.completed = list(set(data.get('completed', [])))
                st.session_state.cancelled = list(set(data.get('cancelled', [])))
        except: pass

verileri_yukle()

# --- 🎯 AKSİYON MANTIĞI (Mutual Exclusion) ---
params = st.query_params
if "act" in params:
    action, game = params["act"], params["game"]
    for k in ['backlog', 'completed', 'cancelled']:
        if game in st.session_state[k]: st.session_state[k].remove(game)
    if action == "done": st.session_state.completed.append(game)
    elif action == "drop": st.session_state.cancelled.append(game)
    elif "undo" in action: st.session_state.backlog.append(game)
    verileri_kaydet(); st.query_params.clear(); st.rerun()

# --- 💉 GÖRSEL TASARIM (Flexbox & Nano-Icon) ---
st.markdown("""
    <style>
    .stApp { background-color: #f9f9f9; }
    .cat-header { font-size: 0.85rem; font-weight: 700; color: #555; border-bottom: 1px solid #eee; margin-top: 15px; padding-bottom: 3px; }
    .game-row { display: flex; justify-content: space-between; align-items: center; padding: 5px 0; gap: 8px; }
    .game-title { font-size: 13px; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-grow: 1; }
    .icon-group { display: flex; gap: 12px; flex-shrink: 0; }
    .nano-icon { text-decoration: none !important; color: #bbb !important; font-size: 16px; font-weight: bold; }
    .nano-icon:hover { color: #ff4b4b !important; }
    
    div.stButton > button[key="main_add"] {
        background-color: #28a745 !important; color: white !important; font-weight: bold !important;
        border-radius: 20px !important; padding: 0.5rem 1.5rem !important; border: none !important;
    }
    .badge-card { background:#fff; padding:10px; border-radius:10px; border-left: 5px solid #ddd; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏛️ Archive")
    for label, list_key, icon_type in [("🎯 Oynanacaklar", "backlog", "active"), ("✅ Bitenler", "completed", "undo_done"), ("📁 Vazgeçilenler", "cancelled", "undo_drop")]:
        if st.session_state[list_key]:
            st.markdown(f'<p class="cat-header">{label}</p>', unsafe_allow_html=True)
            for g in sorted(st.session_state[list_key]):
                color = "#28a745" if list_key == "completed" else ("#aaa" if list_key == "cancelled" else "#333")
                strike = "text-decoration:line-through;" if list_key == "cancelled" else ""
                icons = f'<a href="/?act=done&game={g}" target="_self" class="nano-icon">✓</a><a href="/?act=drop&game={g}" target="_self" class="nano-icon">✕</a>' if icon_type == "active" else f'<a href="/?act={icon_type}&game={g}" target="_self" class="nano-icon">↩</a>'
                st.markdown(f'<div class="game-row"><span class="game-title" style="color:{color};{strike}">{g}</span><div class="icon-group">{icons}</div></div>', unsafe_allow_html=True)

# --- ANA AKIŞ ---
st.title("🏛️ Gamer's Archive")
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
oyun_input = st.text_input("Oyun Ara:", placeholder="hades, gta 5, gow...")

if st.button("Analiz Et", type="primary"):
    if oyun_input:
        with st.spinner('Taranıyor...'):
            arama_terimi = KISALTMALAR.get(oyun_input.lower().strip(), oyun_input)
            try:
                s_res = scraper.get(f"https://store.steampowered.com/api/storesearch/?term={arama_terimi}&l=turkish&cc=TR").json()
                if s_res and s_res['items']:
                    items = s_res['items']
                    # 💉 TAM İSABET FİLTRESİ: Hades II yerine Hades'i seçer
                    exact_match = next((i for i in items if i['name'].lower() == arama_terimi.lower()), None)
                    st.session_state.current_game = exact_match if exact_match else items[0]
                else: st.session_state.current_game = "NOT_FOUND"
            except: st.session_state.current_game = None

if 'current_game' in st.session_state and st.session_state.current_game:
    if st.session_state.current_game == "NOT_FOUND":
        st.error("Oyun bulunamadı!")
    else:
        o = st.session_state.current_game
        app_id, temiz_isim = o['id'], o['name']
        st.image(f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg", use_container_width=True)
        
        c_title, c_add = st.columns([2, 1.3])
        c_title.subheader(temiz_isim)
        
        is_anywhere = any(temiz_isim in st.session_state[k] for k in ['backlog', 'completed', 'cancelled'])
        if c_add.button("❌ Kaldır" if is_anywhere else "➕ Arşivime Ekle", key="main_rem" if is_anywhere else "main_add"):
            for k in ['backlog', 'completed', 'cancelled']:
                if temiz_isim in st.session_state[k]: st.session_state[k].remove(temiz_isim)
            if not is_anywhere: st.session_state.backlog.append(temiz_isim)
            verileri_kaydet(); st.rerun()

        # Fiyatlar, Skorlar ve Süreler
        c1, c2 = st.columns(2)
        try:
            kur = scraper.get("https://api.exchangerate-api.com/v4/latest/USD").json()['rates']['TRY']
            f_usd = o.get('price', {}).get('final', 0) / 100
            c1.markdown(f'<div class="badge-card" style="border-left-color:#1b2838"><b>Steam:</b><br>{f_usd*kur:.0f} TL <small>(${f_usd:.2f})</small></div>', unsafe_allow_html=True)
        except: pass
        try:
            ps_url = f"https://store.playstation.com/tr-tr/search/{temiz_isim.replace(' ', '%20')}"
            ps_price = BeautifulSoup(scraper.get(ps_url).text, 'html.parser').find(string=re.compile(r'\d+[,.]\d+\s?TL')).strip()
            c2.markdown(f'<div class="badge-card" style="border-left-color:#003087"><b>PS Store:</b><br>{ps_price}</div>', unsafe_allow_html=True)
        except: c2.markdown('<div class="badge-card"><b>PS Store:</b> N/A</div>', unsafe_allow_html=True)

        st.markdown("---")
        s1, s2 = st.columns(2)
        try:
            r_res = scraper.get(f"https://store.steampowered.com/appreviews/{app_id}?json=1&language=all").json()
            score = int((r_res['query_summary']['total_positive'] / r_res['query_summary']['total_reviews']) * 100)
            s1.markdown(f'<div class="badge-card" style="border-left-color:#28a745"><b>Steam Puanı:</b><br>%{score}</div>', unsafe_allow_html=True)
        except: pass
        try:
            m_url = f"https://www.metacritic.com/search/{temiz_isim.replace(' ', '%20')}/?category=13"
            meta = BeautifulSoup(scraper.get(m_url, timeout=10).text, 'html.parser').find("div", class_=re.compile(r'c-siteReviewScore')).text.strip()
            s2.markdown(f'<div class="badge-card" style="border-left-color:#ffcc33"><b>Metascore:</b><br>{meta}/100</div>', unsafe_allow_html=True)
        except: pass

        st.markdown('<p style="font-size:0.9rem; font-weight:bold;">⏳ HowLongToBeat Süreleri</p>', unsafe_allow_html=True)
        try:
            res = HowLongToBeat().search(re.sub(r'\(.*?\)|[:™®]', '', temiz_isim).strip())
            if res:
                b = max(res, key=lambda x: x.similarity)
                h1, h2, h3 = st.columns(3); h1.success(f"**Hikaye**\n\n{b.main_story} s."); h2.warning(f"**Ekstra**\n\n{b.main_extra} s."); h3.error(f"**%100**\n\n{b.completionist} s.")
        except: pass