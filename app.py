import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
from howlongtobeatpy import HowLongToBeat
import re
import pickle
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Gamer's Archive", page_icon="🏛️", layout="centered")

# --- 📖 KISALTMALAR ---
KISALTMALAR = {
    "hades": "Hades", "hades 2": "Hades II", "gta 5": "Grand Theft Auto V",
    "rdr 2": "Red Dead Redemption 2", "gow": "God of War", "fifa": "EA SPORTS FC 24"
}

# --- HAFIZA YÖNETİMİ ---
DB_FILE = "oyun_kutuphanem_v5_29.pkl"

def verileri_kaydet():
    data = {'backlog_dict': st.session_state.backlog_dict, 'completed': list(set(st.session_state.completed)), 'categories': st.session_state.categories}
    with open(DB_FILE, 'wb') as f: pickle.dump(data, f)

def verileri_yukle():
    for key in ['backlog_dict', 'completed', 'categories']:
        if key not in st.session_state:
            if key == 'backlog_dict': st.session_state.backlog_dict = {"Genel": []}
            elif key == 'categories': st.session_state.categories = ["Genel", "RPG", "FPS", "Açık Dünya", "Vazgeçilenler"]
            else: st.session_state[key] = []
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'rb') as f:
                d = pickle.load(f); [st.session_state.update({k: v}) for k, v in d.items()]
        except: pass

verileri_yukle()

# --- 💉 POP-UP (DIALOG) ---
@st.dialog("🎯 Oyun Yönetimi")
def kategori_degistir_dialog(game):
    st.write(f"**{game}** için yönetim paneli:")
    current_cat = next((c for c in st.session_state.categories if game in st.session_state.backlog_dict.get(c, [])), "Genel")
    yeni_cat = st.selectbox("Kategori:", st.session_state.categories, index=st.session_state.categories.index(current_cat))
    c_upd, c_rem = st.columns(2)
    if c_upd.button("✅ Güncelle", use_container_width=True):
        for c in list(st.session_state.backlog_dict.keys()):
            if game in st.session_state.backlog_dict[c]: st.session_state.backlog_dict[c].remove(game)
        st.session_state.backlog_dict.setdefault(yeni_cat, []).append(game)
        verileri_kaydet(); st.query_params.clear(); st.rerun()
    if c_rem.button("🗑️ Kaldır", type="primary", use_container_width=True):
        for c in list(st.session_state.backlog_dict.keys()):
            if game in st.session_state.backlog_dict[c]: st.session_state.backlog_dict[c].remove(game)
        if game in st.session_state.completed: st.session_state.completed.remove(game)
        verileri_kaydet(); st.query_params.clear(); st.rerun()

# --- 💉 GÖRSEL TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .cat-header { font-size: 0.85rem; font-weight: 800; color: #333; text-transform: uppercase; border-bottom: 2px solid #eee; margin-top: 25px; padding-bottom: 4px; }
    .sub-cat-label { font-size: 11px; font-weight: 700; color: #999; text-transform: uppercase; margin-top: 18px; margin-bottom: 6px; }
    .game-title { font-size: 15px; font-weight: 800 !important; color: #000 !important; }
    
    /* 🏷️ ETİKET ROZETLERİ (Pentatag Revision) */
    .tag-container { display: flex; flex-wrap: wrap; gap: 6px; margin-top: -10px; margin-bottom: 15px; }
    .tag-badge { 
        background-color: #f0f2f6; color: #555; padding: 2px 10px; border-radius: 8px; 
        font-size: 10px; font-weight: 700; border: 1px solid #e0e4e9; white-space: nowrap;
    }
    
    .badge-card { background:#fff; padding: 15px 20px; border-radius: 14px; border-left: 5px solid #eee; box-shadow: 0 4px 15px rgba(0,0,0,0.04); margin-bottom: 12px; font-size: 14px; display: flex; flex-direction: column; justify-content: center; min-height: 80px; }
    .badge-label { font-size: 11px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 4px; }
    .badge-value { font-size: 16px; font-weight: 800; color: #333; }
    .section-divider { border-top: 1px solid #eee; margin: 25px 0 15px 0; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR (v5.17 Baz Yapısı) ---
with st.sidebar:
    st.title("🏛️ Archive")
    st.markdown('<p class="cat-header">🎯 Oynanacaklar</p>', unsafe_allow_html=True)
    for cat in st.session_state.categories:
        games = st.session_state.backlog_dict.get(cat, [])
        if games:
            st.markdown(f'<p class="sub-cat-label">{cat}</p>', unsafe_allow_html=True)
            for g in sorted(games):
                st.markdown(f'<div style="display:flex; justify-content:space-between; padding:5px 0;"><span class="game-title">{g}</span><div style="display:flex; gap:12px;"><a href="/?act=move_ui&game={g}" target="_self" style="text-decoration:none; color:#ccc;">⇄</a></div></div>', unsafe_allow_html=True)

# --- ANA AKIŞ ---
st.title("🏛️ Gamer's Archive")
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
oyun_in = st.text_input("Oyun Ara:", placeholder="hades, gow...")

if st.button("Analiz Et", type="primary"):
    if oyun_in:
        with st.spinner('Derin Veri Analizi...'):
            term = KISALTMALAR.get(oyun_in.lower().strip(), oyun_in)
            try:
                s_res = scraper.get(f"https://store.steampowered.com/api/storesearch/?term={term}&l=turkish&cc=TR").json()
                if s_res and s_res['items']:
                    o = s_res['items'][0]
                    st.session_state.current_game = o
                    # 💉 ETİKET OPERASYONU: Steam sayfasından İLK 5 ETİKET
                    tag_page = scraper.get(f"https://store.steampowered.com/app/{o['id']}/?l=turkish").text
                    tag_soup = BeautifulSoup(tag_page, 'html.parser')
                    tags = [t.text.strip() for t in tag_soup.find_all('a', class_='app_tag')][:5]
                    st.session_state.current_tags = tags
                else: st.session_state.current_game = "NOT_FOUND"
            except: st.session_state.current_game = None

if 'current_game' in st.session_state and st.session_state.current_game and st.session_state.current_game != "NOT_FOUND":
    o = st.session_state.current_game
    app_id, temiz_isim = o['id'], o['name']
    st.image(f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg", use_container_width=True)
    
    # 🏷️ PENTATAG GÖSTERİMİ
    if 'current_tags' in st.session_state and st.session_state.current_tags:
        tag_html = "".join([f'<div class="tag-badge">{t}</div>' for t in st.session_state.current_tags])
        st.markdown(f'<div class="tag-container">{tag_html}</div>', unsafe_allow_html=True)
    
    st.subheader(temiz_isim)
    
    # Kategori ve Arşivleme (Baz Fonksiyonlar)
    existing_cat = next((c for c in st.session_state.categories if temiz_isim in st.session_state.backlog_dict.get(c, [])), None)
    c_cat, c_add = st.columns([1, 1])
    sel_cat = c_cat.selectbox("Kategori:", st.session_state.categories, index=st.session_state.categories.index(existing_cat) if existing_cat else 0, label_visibility="collapsed")
    if c_add.button("Güncelle" if existing_cat else "➕ Arşivime Ekle", key="main_btn", use_container_width=True):
        for c in list(st.session_state.backlog_dict.keys()):
            if temiz_isim in st.session_state.backlog_dict[c]: st.session_state.backlog_dict[c].remove(temiz_isim)
        st.session_state.backlog_dict.setdefault(sel_cat, []).append(temiz_isim)
        verileri_kaydet(); st.rerun()

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # Metrikler (2'li Sütun Baz Yapısı)
    c1, c2 = st.columns(2)
    try:
        kur = scraper.get("https://api.exchangerate-api.com/v4/latest/USD").json()['rates']['TRY']
        f_usd = o.get('price', {}).get('final', 0) / 100
        c1.markdown(f'<div class="badge-card" style="border-left-color:#1b2838"><span class="badge-label">Steam Türkiye</span><span class="badge-value">{f_usd*kur:.0f} TL</span></div>', unsafe_allow_html=True)
    except: pass
    try:
        ps_url = f"https://store.playstation.com/tr-tr/search/{temiz_isim.replace(' ', '%20')}"
        ps_price = BeautifulSoup(scraper.get(ps_url).text, 'html.parser').find(string=re.compile(r'\d+[,.]\d+\s?TL')).strip()
        c2.markdown(f'<div class="badge-card" style="border-left-color:#003087"><span class="badge-label">PS Store TR</span><span class="badge-value">{ps_price}</span></div>', unsafe_allow_html=True)
    except: c2.markdown('<div class="badge-card" style="border-left-color:#003087"><span class="badge-label">PS Store TR</span><span class="badge-value">N/A</span></div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)
    s1, s2 = st.columns(2)
    try:
        r_res = scraper.get(f"https://store.steampowered.com/appreviews/{app_id}?json=1&language=all").json()
        s1.markdown(f'<div class="badge-card" style="border-left-color:#28a745"><span class="badge-label">Steam Puanı</span><span class="badge-value">%{int((r_res["query_summary"]["total_positive"]/r_res["query_summary"]["total_reviews"])*100)} Olumlu</span></div>', unsafe_allow_html=True)
    except: pass
    try:
        m_url = f"https://www.metacritic.com/search/{temiz_isim.replace(' ', '%20')}/?category=13"
        meta = BeautifulSoup(scraper.get(m_url, timeout=10).text, 'html.parser').find("div", class_=re.compile(r'c-siteReviewScore')).text.strip()
        s2.markdown(f'<div class="badge-card" style="border-left-color:#ffcc33"><span class="badge-label">Metascore</span><span class="badge-value">{meta}/100</span></div>', unsafe_allow_html=True)
    except: s2.markdown('<div class="badge-card" style="border-left-color:#ffcc33"><span class="badge-label">Metascore</span><span class="badge-value">N/A</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.95rem; font-weight:bold; color:#555;">⏳ Oynanış Süreleri (HLTB)</p>', unsafe_allow_html=True)
    try:
        res = HowLongToBeat().search(re.sub(r'\(.*?\)|[:™®]', '', temiz_isim).strip())
        if res:
            b = max(res, key=lambda x: x.similarity)
            h1, h2, h3 = st.columns(3); h1.success(f"**Main**\n{b.main_story}h"); h2.warning(f"**Extra**\n{b.main_extra}h"); h3.error(f"**100%**\n{b.completionist}h")
    except: pass