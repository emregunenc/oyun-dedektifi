import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
from howlongtobeatpy import HowLongToBeat
import re
import pickle
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Gamer's Archive", page_icon="🏛️", layout="centered")

# --- HAFIZA YÖNETİMİ ---
DB_FILE = "oyun_kutuphanem.pkl"

def verileri_kaydet():
    data = {'backlog': list(st.session_state.backlog), 'completed': list(st.session_state.completed), 'cancelled': list(st.session_state.cancelled)}
    with open(DB_FILE, 'wb') as f: pickle.dump(data, f)

def verileri_yukle():
    if 'backlog' not in st.session_state: st.session_state.backlog = []
    if 'completed' not in st.session_state: st.session_state.completed = []
    if 'cancelled' not in st.session_state: st.session_state.cancelled = []
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'rb') as f:
                data = pickle.load(f)
                st.session_state.backlog = list(data.get('backlog', []))
                st.session_state.completed = list(data.get('completed', []))
                st.session_state.cancelled = list(data.get('cancelled', []))
        except: pass

verileri_yukle()

# --- 🎯 AKSİYON MANTIĞI (URL Parametreleri İle Tıklama) ---
# Bu kısım ikonlara tıklandığında sayfanın en başında çalışır ve listeyi günceller.
params = st.query_params
if "act" in params:
    action = params["act"]
    game = params["game"]
    
    if action == "done" and game in st.session_state.backlog:
        st.session_state.completed.append(game)
    elif action == "drop" and game in st.session_state.backlog:
        st.session_state.cancelled.append(game)
    elif action == "undo_done" and game in st.session_state.completed:
        st.session_state.completed.remove(game)
    elif action == "undo_drop" and game in st.session_state.cancelled:
        st.session_state.cancelled.remove(game)
    
    if game not in st.session_state.backlog and action in ["undo_done", "undo_drop"]:
        st.session_state.backlog.append(game)
        
    verileri_kaydet()
    st.query_params.clear() # URL'i temizle
    st.rerun() # Sayfayı yenile

# --- 💉 GÖRSEL TASARIM (Custom Flexbox CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #f9f9f9; }
    .cat-header { font-size: 0.85rem; font-weight: 700; color: #555; border-bottom: 1px solid #eee; margin-top: 15px; padding-bottom: 3px; }
    
    /* 🔴 CUSTOM ROW: Kolon kullanmadan ikonları metne sabitleyen yapı */
    .game-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 0;
        gap: 10px;
    }
    .game-title {
        font-size: 13px;
        color: #333;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        flex-grow: 1;
    }
    .icon-group {
        display: flex;
        gap: 12px;
        flex-shrink: 0; /* İkonların mobilde daralmasını engeller */
    }
    .nano-icon {
        text-decoration: none !important;
        color: #bbb !important;
        font-size: 16px;
        font-weight: bold;
        transition: 0.2s;
    }
    .nano-icon:hover { color: #ff4b4b !important; }
    
    /* 🟢 ANA BUTON (Yeşil & Oval) */
    div.stButton > button[key="main_add"] {
        background-color: #28a745 !important; color: white !important; font-weight: bold !important;
        border-radius: 20px !important; padding: 0.5rem 1.5rem !important; border: none !important;
    }
    .badge-card { background:#fff; padding:10px; border-radius:10px; border-left: 5px solid #ddd; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# --- YAN PANEL (SIDEBAR) ---
with st.sidebar:
    st.title("🏛️ Archive")
    
    # 🎯 Oynanacaklar
    active = [g for g in st.session_state.backlog if g not in st.session_state.completed and g not in st.session_state.cancelled]
    if active:
        st.markdown('<p class="cat-header">🎯 Oynanacaklar</p>', unsafe_allow_html=True)
        for g in active:
            st.markdown(f"""
                <div class="game-row">
                    <span class="game-title">{g}</span>
                    <div class="icon-group">
                        <a href="/?act=done&game={g}" target="_self" class="nano-icon">✓</a>
                        <a href="/?act=drop&game={g}" target="_self" class="nano-icon">✕</a>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # ✅ Bitenler
    if st.session_state.completed:
        st.markdown('<p class="cat-header">✅ Bitenler</p>', unsafe_allow_html=True)
        for g in st.session_state.completed:
            st.markdown(f"""
                <div class="game-row">
                    <span class="game-title" style="color:#28a745;">✦ {g}</span>
                    <div class="icon-group">
                        <a href="/?act=undo_done&game={g}" target="_self" class="nano-icon">↩</a>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# --- ANA AKIŞ ---
st.title("🏛️ Gamer's Archive")
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
oyun_adi = st.text_input("Oyun Ara:", placeholder="Elden Ring, Hades...")

if st.button("Analiz Et", type="primary"):
    if oyun_adi:
        with st.spinner('Taranıyor...'):
            try:
                s_res = scraper.get(f"https://store.steampowered.com/api/storesearch/?term={oyun_adi}&l=turkish&cc=TR").json()
                if s_res and s_res['items']:
                    st.session_state.current_game = s_res['items'][0]
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
        
        is_in = temiz_isim in st.session_state.backlog
        if c_add.button("❌ Kaldır" if is_in else "➕ Arşivime Ekle", key="main_rem" if is_in else "main_add"):
            if is_in:
                st.session_state.backlog.remove(temiz_isim)
                if temiz_isim in st.session_state.completed: st.session_state.completed.remove(temiz_isim)
                if temiz_isim in st.session_state.cancelled: st.session_state.cancelled.remove(temiz_isim)
            else:
                st.session_state.backlog.append(temiz_isim)
            verileri_kaydet(); st.rerun()

        # Fiyatlar, Skorlar ve Süreler (Stabil Yapı)
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
        except: pass

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

        st.markdown("---")
        st.markdown('<p style="font-size:0.9rem; font-weight:bold;">⏳ HowLongToBeat Süreleri</p>', unsafe_allow_html=True)
        try:
            res = HowLongToBeat().search(re.sub(r'\(.*?\)|[:™®]', '', temiz_isim).strip())
            if res:
                b = max(res, key=lambda x: x.similarity)
                h1, h2, h3 = st.columns(3)
                h1.success(f"**Hikaye**\n\n{b.main_story} s.")
                h2.warning(f"**Ekstra**\n\n{b.main_extra} s.")
                h3.error(f"**%100**\n\n{b.completionist} s.")
        except: pass