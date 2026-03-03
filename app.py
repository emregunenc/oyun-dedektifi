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

# --- AKSİYON FONKSİYONLARI ---
def move_complete(game):
    if game not in st.session_state.completed: st.session_state.completed.append(game)
    verileri_kaydet()

def move_cancel(game):
    if game not in st.session_state.cancelled: st.session_state.cancelled.append(game)
    verileri_kaydet()

def undo_action(game, from_list):
    if from_list == "completed" and game in st.session_state.completed: st.session_state.completed.remove(game)
    elif from_list == "cancelled" and game in st.session_state.cancelled: st.session_state.cancelled.remove(game)
    if game not in st.session_state.backlog: st.session_state.backlog.append(game)
    verileri_kaydet()

# --- GÖRSEL TASARIM (Fixed Anchor CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #f9f9f9; }
    .cat-header { font-size: 0.85rem; font-weight: 700; color: #555; border-bottom: 1px solid #eee; margin-top: 12px; padding-bottom: 3px; }
    
    /* 🔴 SIDEBAR SABİT HİZALAMA */
    [data-testid="stSidebarUserContent"] {
        padding-left: 0.3rem !important;
        padding-right: 0.3rem !important;
    }
    
    /* Sütunların yan yana kalmasını zorla ve boşluğu kapat */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 0px !important;
    }
    
    /* ⚓ BUTON SÜTUNLARINA SABİT 30PX KELEPÇE */
    [data-testid="stSidebar"] [data-testid="column"]:nth-child(2),
    [data-testid="stSidebar"] [data-testid="column"]:nth-child(3) {
        flex: none !important;
        width: 30px !important;
        min-width: 30px !important;
    }
    
    /* İsim sütunu kalan tüm alanı alsın */
    [data-testid="stSidebar"] [data-testid="column"]:first-child {
        flex: 1 !important;
        min-width: 0 !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0px !important;
        color: #bbb !important;
        font-size: 16px !important;
        height: 28px !important;
        width: 28px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover { color: #ff4b4b !important; }
    
    .game-name-side { 
        font-size: 13px; 
        color: #333; 
        white-space: nowrap !important; 
        overflow: hidden !important; 
        text-overflow: ellipsis !important;
        display: block;
        line-height: 28px;
    }

    /* 🟢 + ARŞİVİME EKLE BUTONU (Yeşil & Oval) */
    div.stButton > button[key="main_add"] {
        background-color: #28a745 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 20px !important;
        padding: 0.5rem 1.5rem !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(40, 167, 69, 0.3) !important;
    }
    
    .badge-card { background:#fff; padding:10px; border-radius:10px; border-left: 5px solid #ddd; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏛️ Archive")
    
    active = [g for g in st.session_state.backlog if g not in st.session_state.completed and g not in st.session_state.cancelled]
    if active:
        st.markdown('<p class="cat-header">🎯 Oynanacaklar</p>', unsafe_allow_html=True)
        for g in active:
            c_txt, c_c, c_x = st.columns([1, 1, 1]) # CSS ile bunlar ezilecek, 1-1-1 yazabiliriz
            c_txt.markdown(f"<span class='game-name-side'>{g}</span>", unsafe_allow_html=True)
            if c_c.button("✓", key=f"c_{g}"): move_complete(g); st.rerun()
            if c_x.button("✕", key=f"x_{g}"): move_cancel(g); st.rerun()

    if st.session_state.completed:
        st.markdown('<p class="cat-header">✅ Bitenler</p>', unsafe_allow_html=True)
        for g in st.session_state.completed:
            c_txt, c_u = st.columns([1, 1])
            c_txt.markdown(f"<span class='game-name-side' style='color:#28a745;'>✦ {g}</span>", unsafe_allow_html=True)
            if c_u.button("↩", key=f"u_c_{g}"): undo_action(g, "completed"); st.rerun()

    if st.session_state.cancelled:
        st.markdown('<p class="cat-header">📁 Vazgeçilenler</p>', unsafe_allow_html=True)
        for g in st.session_state.cancelled:
            c_txt, c_u = st.columns([1, 1])
            c_txt.markdown(f"<span class='game-name-side' style='color:#aaa; text-decoration:line-through;'>✖ {g}</span>", unsafe_allow_html=True)
            if c_u.button("↩", key=f"u_v_{g}"): undo_action(g, "cancelled"); st.rerun()

# --- ANA AKIŞ ---
st.title("🏛️ Gamer's Archive")
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
oyun_adi = st.text_input("Oyun Ara:", placeholder="Hades, Elden Ring...")

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
            else: st.session_state.backlog.append(temiz_isim)
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