import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
from howlongtobeatpy import HowLongToBeat
import re
import pickle
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Gamer's Archive", page_icon="🏛️", layout="centered")

# --- GENİŞLETİLMİŞ AKILLI SÖZLÜK (Kısaltma -> Resmi İsim) ---
SÖZLÜK = {
    # Eklediklerimiz
    "rdr": "Red Dead Redemption 2",
    "rdr2": "Red Dead Redemption 2",
    "tlou 2": "The Last of Us Part II",
    "tlou2": "The Last of Us Part II",
    "tlou": "The Last of Us Part I",
    "pes": "Pro Evolution Soccer",
    "gta 5": "Grand Theft Auto V",
    "gta v": "Grand Theft Auto V",
    "gow": "God of War",
    "gow r": "God of War Ragnarök",
    "er": "Elden Ring",
    "fifa": "EA SPORTS FC 24",
    "cod": "Call of Duty",
    "ac": "Assassin's Creed",
    "cp2077": "Cyberpunk 2077",
    "mc": "Minecraft",
    "f1": "F1 24",
    "re4": "Resident Evil 4",
    "witcher 3": "The Witcher 3: Wild Hunt"
}

def isim_duzelt(arama):
    arama_temiz = arama.lower().strip()
    return SÖZLÜK.get(arama_temiz, arama)

# --- HAFIZA DOSYA YOLU ---
DB_FILE = "oyun_kutuphanem.pkl"

def verileri_kaydet():
    data = {'backlog': st.session_state.backlog, 'completed': st.session_state.completed, 'cancelled': st.session_state.cancelled}
    with open(DB_FILE, 'wb') as f: pickle.dump(data, f)

def verileri_yukle():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'rb') as f:
            data = pickle.load(f)
            st.session_state.backlog = data.get('backlog', [])
            st.session_state.completed = data.get('completed', [])
            st.session_state.cancelled = data.get('cancelled', [])
    else:
        st.session_state.backlog = st.session_state.completed = st.session_state.cancelled = []

# --- GÖRSEL TASARIM (Android Renk Fix Dahil) ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff !important; padding: 15px; border-radius: 12px; border: 2px solid #f0f2f6 !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    [data-testid="stMetricValue"] { color: #1a1a1a !important; font-size: 1.8rem !important; font-weight: 800 !important; }
    [data-testid="stMetricLabel"] { color: #444444 !important; font-size: 1rem !important; font-weight: 600 !important; }
    .stButton>button { width: 100%; border-radius: 20px; font-weight: bold; }
    .hltb-header { font-size: 1.4rem; font-weight: 700; color: #ff8c00; margin-bottom: 10px; border-left: 5px solid #ff8c00; padding-left: 10px; }
    .cat-header { font-size: 1.1rem; font-weight: 700; color: #1a1a1a !important; border-bottom: 2px solid #eee; margin-top: 10px; }
    div[data-testid="stCheckbox"] label p { font-size: 1.25rem !important; color: #1a1a1a !important; font-weight: 600 !important; }
    .played-text { color: #28a745 !important; font-weight: bold; font-size: 1.1rem; }
    .vazgecildi-text { color: #888 !important; text-decoration: line-through; font-size: 1.0rem; }
    .stButton > button[key^="vaz_"] { padding: 0px !important; height: 22px !important; width: 22px !important; font-size: 0.7rem !important; border-radius: 50% !important; border: 1px solid #ddd !important; color: #999 !important; }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE BAŞLATMA ---
if 'backlog' not in st.session_state: verileri_yukle()
if 'current_game' not in st.session_state: st.session_state.current_game = None

# --- YAN PANEL (SIDEBAR) ---
with st.sidebar:
    st.title("🏛️ Gamer's Archive")
    active = [g for g in st.session_state.backlog if g not in st.session_state.completed and g not in st.session_state.cancelled]
    if active:
        st.markdown('<p class="cat-header">🎯 Oynanacaklar</p>', unsafe_allow_html=True)
        for g in active:
            c1, c2 = st.columns([5, 1])
            with c1:
                if st.checkbox(g, key=f"sb_{g}"): st.session_state.completed.append(g); verileri_kaydet(); st.rerun()
            with c2:
                if st.button("✖", key=f"vaz_{g}"): st.session_state.cancelled.append(g); verileri_kaydet(); st.rerun()

    if st.session_state.completed:
        st.markdown('<p class="cat-header">✅ Oynadıklarım</p>', unsafe_allow_html=True)
        for g in st.session_state.completed: st.markdown(f"<p class='played-text'>✦ {g}</p>", unsafe_allow_html=True)

    if st.session_state.cancelled:
        st.markdown('<p class="cat-header">📁 Vazgeçtiklerim</p>', unsafe_allow_html=True)
        for g in st.session_state.cancelled: st.markdown(f"<p class='vazgecildi-text'>✖ {g}</p>", unsafe_allow_html=True)

# --- ANA AKIŞ ---
st.title("🏛️ Gamer's Archive")
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
oyun_adi = st.text_input("Oyun adını yazın:", placeholder="Örn: rdr, tlou 2, pes...")

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

# --- VERİ GÖSTERİMİ ---
if st.session_state.current_game and st.session_state.current_game != "NOT_FOUND":
    o = st.session_state.current_game
    app_id, temiz_isim = o['id'], o['name']
    st.image(f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg", use_container_width=True)
    
    col_t, col_b = st.columns([1.8, 1])
    with col_t: st.subheader(f"🔍 {temiz_isim}")
    with col_b:
        is_in = temiz_isim in st.session_state.backlog
        if st.button("❌ Kaldır" if is_in else "➕ Arşive Ekle"):
            if is_in: 
                st.session_state.backlog.remove(temiz_isim)
                if temiz_isim in st.session_state.completed: st.session_state.completed.remove(temiz_isim)
                if temiz_isim in st.session_state.cancelled: st.session_state.cancelled.remove(temiz_isim)
            else: st.session_state.backlog.append(temiz_isim)
            verileri_kaydet(); st.rerun()

    c1, c2 = st.columns(2)
    try:
        kur = scraper.get("https://api.exchangerate-api.com/v4/latest/USD").json()['rates']['TRY']
        f_usd = o.get('price', {}).get('final', 0) / 100
        c1.metric("Steam (Tahmini)", f"{f_usd * kur:.0f} TL", f"${f_usd:.2f}")
    except: c1.metric("Steam", "Kur Alınamadı")

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

elif st.session_state.current_game == "NOT_FOUND":
    st.error("Oyun bulunamadı!")