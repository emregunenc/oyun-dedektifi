import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
from howlongtobeatpy import HowLongToBeat
import re
import pickle
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Gamer's Archive", page_icon="🏛️", layout="centered")

# --- AKILLI SÖZLÜK ---
SÖZLÜK = {
    "rdr": "Red Dead Redemption 2", "rdr2": "Red Dead Redemption 2",
    "tlou 2": "The Last of Us Part II", "tlou2": "The Last of Us Part II",
    "pes": "Pro Evolution Soccer", "gta 5": "Grand Theft Auto V",
    "gow": "God of War", "er": "Elden Ring"
}

def isim_duzelt(arama):
    arama_temiz = arama.lower().strip()
    return SÖZLÜK.get(arama_temiz, arama)

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

# --- GÖRSEL TASARIM (Mikro Butonlar) ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff !important; padding: 15px; border-radius: 12px; border: 2px solid #f0f2f6 !important; }
    .cat-header { font-size: 1.1rem; font-weight: 700; color: #1a1a1a !important; border-bottom: 2px solid #eee; margin-top: 15px; margin-bottom: 10px; }
    .played-text { color: #28a745 !important; font-weight: 600; font-size: 0.9rem; }
    .vazgecildi-text { color: #888 !important; text-decoration: line-through; font-size: 0.9rem; }
    
    /* 🔴 MİKRO BUTON TASARIMI (Undo ve Çarpı) */
    .stButton > button[key^="undo_"], .stButton > button[key^="cancel_"] { 
        padding: 0px !important; 
        height: 18px !important; 
        width: 18px !important; 
        min-height: 18px !important;
        min-width: 18px !important;
        font-size: 0.6rem !important; 
        line-height: 1 !important;
        border-radius: 50% !important; 
        background-color: transparent !important; 
        color: #bbb !important; 
        border: 1px solid #ddd !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .stButton > button[key^="undo_"]:hover, .stButton > button[key^="cancel_"]:hover {
        border-color: #ff4b4b !important;
        color: #ff4b4b !important;
    }
    </style>
""", unsafe_allow_html=True)

verileri_yukle()
if 'current_game' not in st.session_state: st.session_state.current_game = None

# --- YAN PANEL (SIDEBAR) ---
with st.sidebar:
    st.title("🏛️ Gamer's Archive")
    
    # 🎯 Oynanacaklar
    active = [g for g in st.session_state.backlog if g not in st.session_state.completed and g not in st.session_state.cancelled]
    if active:
        st.markdown('<p class="cat-header">🎯 Oynanacaklar</p>', unsafe_allow_html=True)
        for g in active:
            c1, c2 = st.columns([5, 1])
            with c1:
                if st.checkbox(g, key=f"tick_{g}"):
                    if g not in st.session_state.completed:
                        st.session_state.completed.append(g)
                        verileri_kaydet(); st.rerun()
            with c2:
                if st.button("✖", key=f"cancel_{g}"):
                    if g not in st.session_state.cancelled:
                        st.session_state.cancelled.append(g)
                        verileri_kaydet(); st.rerun()

    # ✅ Oynadıklarım
    if st.session_state.completed:
        st.markdown('<p class="cat-header">✅ Oynadıklarım</p>', unsafe_allow_html=True)
        for g in st.session_state.completed:
            c1, c2 = st.columns([5, 1])
            with c1: st.markdown(f"<p class='played-text'>✦ {g}</p>", unsafe_allow_html=True)
            with c2:
                if st.button("↩", key=f"undo_comp_{g}"):
                    st.session_state.completed.remove(g)
                    verileri_kaydet(); st.rerun()

    # 📁 Vazgeçtiklerim
    if st.session_state.cancelled:
        st.markdown('<p class="cat-header">📁 Vazgeçtiklerim</p>', unsafe_allow_html=True)
        for g in st.session_state.cancelled:
            c1, c2 = st.columns([5, 1])
            with c1: st.markdown(f"<p class='vazgecildi-text'>✖ {g}</p>", unsafe_allow_html=True)
            with c2:
                if st.button("↩", key=f"undo_canc_{g}"):
                    st.session_state.cancelled.remove(g)
                    verileri_kaydet(); st.rerun()

    st.markdown("---")
    if st.button("Tüm Verileri Sıfırla"):
        st.session_state.backlog = st.session_state.completed = st.session_state.cancelled = []
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

# --- ANA AKIŞ ---
st.title("🏛️ Gamer's Archive")
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
oyun_adi = st.text_input("Oyun adını yazın:", placeholder="Örn: rdr, pes, gta 5...")

if st.button("Analiz Et", type="primary"):
    if oyun_adi:
        arama_terimi = isim_duzelt(oyun_adi)
        with st.spinner(f'{arama_terimi} Arşivde Aranıyor...'):
            try:
                s_res = scraper.get(f"https://store.steampowered.com/api/storesearch/?term={arama_terimi}&l=turkish&cc=TR").json()
                if s_res and s_res['items']:
                    items = s_res['items']
                    o = items[0]
                    for item in items[:5]:
                        if item['name'].lower() == arama_terimi.lower(): o = item; break
                    st.session_state.current_game = o
                else: st.session_state.current_game = "NOT_FOUND"
            except: st.session_state.current_game = None

if st.session_state.current_game and st.session_state.current_game != "NOT_FOUND":
    o = st.session_state.current_game
    app_id, temiz_isim = o['id'], o['name']
    st.image(f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg", use_container_width=True)
    
    col_t, col_b = st.columns([1.8, 1])
    with col_t: st.subheader(f"🔍 {temiz_isim}")
    with col_b:
        is_in_backlog = temiz_isim in st.session_state.backlog
        if st.button("❌ Kaldır" if is_in_backlog else "➕ Arşive Ekle"):
            if is_in_backlog: 
                if temiz_isim in st.session_state.backlog: st.session_state.backlog.remove(temiz_isim)
                if temiz_isim in st.session_state.completed: st.session_state.completed.remove(temiz_isim)
                if temiz_isim in st.session_state.cancelled: st.session_state.cancelled.remove(temiz_isim)
            else: 
                if temiz_isim not in st.session_state.backlog: st.session_state.backlog.append(temiz_isim)
            verileri_kaydet(); st.rerun()

    c1, c2 = st.columns(2)
    try:
        kur_res = scraper.get("https://api.exchangerate-api.com/v4/latest/USD").json()
        kur = kur_res['rates']['TRY']
        f_usd = o.get('price', {}).get('final', 0) / 100
        c1.metric("Steam (Tahmini)", f"{f_usd * kur:.0f} TL", f"${f_usd:.2f}")
    except: c1.metric("Steam", "Kur Hatası")

    ps_url = f"https://store.playstation.com/tr-tr/search/{temiz_isim.replace(' ', '%20')}"
    ps_price = "Bulunamadı"
    try:
        ps_soup = BeautifulSoup(scraper.get(ps_url, timeout=10).text, 'html.parser')
        ps_find = ps_soup.find(string=re.compile(r'\d+[,.]\d+\s?TL'))
        if ps_find: ps_price = ps_find.strip()
    except: pass
    with c2:
        if ps_price != "Bulunamadı": st.metric("PS Store", ps_price)
        else: st.link_button("PS Fiyatı 🔗", ps_url)

    st.markdown("---")
    p1, p2 = st.columns(2)
    try:
        r_res = scraper.get(f"https://store.steampowered.com/appreviews/{app_id}?json=1&language=all").json()
        score = int((r_res['query_summary']['total_positive'] / r_res['query_summary']['total_reviews']) * 100)
        p1.metric("Steam Puanı", f"%{score}")
    except: p1.metric("Steam Puanı", "N/A")

    m_url = f"https://www.metacritic.com/search/{temiz_isim.replace(' ', '%20')}/?category=13"
    meta = "N/A"
    try:
        m_soup = BeautifulSoup(scraper.get(m_url, timeout=10).text, 'html.parser')
        m_find = m_soup.find("div", class_=re.compile(r'c-siteReviewScore'))
        if m_find: meta = m_find.text.strip()
    except: pass
    with p2:
        if meta != "N/A": st.metric("Metascore", f"{meta}/100")
        else: st.link_button("Metascore 🔍", m_url)

    st.markdown("---")
    st.markdown('<div class="hltb-header">⏳ HowLongToBeat Süreleri</div>', unsafe_allow_html=True)
    try:
        res = HowLongToBeat().search(re.sub(r'\(.*?\)|[:™®]', '', temiz_isim).strip())
        if res:
            b = max(res, key=lambda x: x.similarity)
            h1, h2, h3 = st.columns(3)
            h1.success(f"**Hikaye**\n\n{b.main_story} Sa.")
            h2.warning(f"**Ekstra**\n\n{b.main_extra} Sa.")
            h3.error(f"**%100**\n\n{b.completionist} Sa.")
    except: st.write("Veri alınamadı.")