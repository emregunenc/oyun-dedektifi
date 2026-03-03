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
DB_FILE = "oyun_kutuphanem_v5_11.pkl"

def verileri_kaydet():
    data = {
        'backlog_dict': st.session_state.backlog_dict,
        'completed': list(set(st.session_state.completed)),
        'cancelled': list(set(st.session_state.cancelled)),
        'categories': st.session_state.categories
    }
    with open(DB_FILE, 'wb') as f: pickle.dump(data, f)

def verileri_yukle():
    for key in ['backlog_dict', 'completed', 'cancelled', 'categories']:
        if key not in st.session_state:
            if key == 'backlog_dict': st.session_state.backlog_dict = {"Genel": []}
            elif key == 'categories': st.session_state.categories = ["Genel", "RPG", "FPS", "Açık Dünya"]
            else: st.session_state[key] = []
    
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'rb') as f:
                data = pickle.load(f)
                for k, v in data.items(): st.session_state[k] = v
        except: pass

verileri_yukle()

# --- 💉 POP-UP (DIALOG) MANTIĞI ---
@st.dialog("🎯 Kategoriyi Güncelle")
def kategori_degistir_dialog(game):
    st.write(f"**{game}** için yeni uzmanlık alanı seçin:")
    
    # Mevcut kategoriyi tespit et
    current_cat = "Genel"
    for c in st.session_state.categories:
        if game in st.session_state.backlog_dict.get(c, []):
            current_cat = c
            break
            
    yeni_cat = st.selectbox("Hedef Kategori:", st.session_state.categories, 
                            index=st.session_state.categories.index(current_cat))
    
    if st.button("Değişikliği Uygula", use_container_width=True):
        # 💉 CERRAHİ TEMİZLİK: Oyunu tüm backlog kategorilerinden söküp al
        for c in list(st.session_state.backlog_dict.keys()):
            if game in st.session_state.backlog_dict[c]:
                st.session_state.backlog_dict[c].remove(game)
        
        # 💉 YENİ YUVA: Seçilen kategoriye yerleştir
        if yeni_cat not in st.session_state.backlog_dict:
            st.session_state.backlog_dict[yeni_cat] = []
        st.session_state.backlog_dict[yeni_cat].append(game)
        
        verileri_kaydet()
        # 🏁 PENCEREYİ KAPAT VE TAZELEN
        st.rerun()

# --- 🎯 AKSİYON MANTIĞI ---
params = st.query_params
if "act" in params:
    action, game = params["act"], params["game"]
    
    if action == "move_ui":
        kategori_degistir_dialog(game) 
    else:
        for c in list(st.session_state.backlog_dict.keys()):
            if game in st.session_state.backlog_dict[c]: st.session_state.backlog_dict[c].remove(game)
        if game in st.session_state.completed: st.session_state.completed.remove(game)
        if game in st.session_state.cancelled: st.session_state.cancelled.remove(game)

        if action == "done": st.session_state.completed.append(game)
        elif action == "drop": st.session_state.cancelled.append(game)
        elif "undo" in action: st.session_state.backlog_dict["Genel"].append(game)
        
        verileri_kaydet()
        st.query_params.clear()
        st.rerun()

# --- 💉 GÖRSEL TASARIM (Baz v5.7) ---
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .cat-header { font-size: 0.8rem; font-weight: 800; color: #444; text-transform: uppercase; letter-spacing: 1px; border-bottom: 2px solid #eee; margin-top: 20px; padding-bottom: 2px; }
    .sub-cat-label { font-size: 10px; font-weight: 700; color: #999; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 12px; margin-bottom: 2px; }
    .game-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; }
    .game-title { font-size: 13px; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-grow: 1; }
    .icon-group { display: flex; gap: 10px; flex-shrink: 0; }
    .nano-icon { text-decoration: none !important; color: #ccc !important; font-size: 15px; }
    
    div.stButton > button[key="main_btn"] { 
        background-color: #28a745 !important; color: white !important; font-weight: bold !important;
        border-radius: 12px !important; border: none !important; width: 100% !important; height: 42px !important;
    }
    .badge-card { background:#fff; padding: 15px 20px; border-radius: 14px; border-left: 5px solid #eee; box-shadow: 0 4px 15px rgba(0,0,0,0.04); margin-bottom: 12px; font-size: 14px; display: flex; flex-direction: column; justify-content: center; }
    .badge-label { font-size: 11px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 4px; }
    .badge-value { font-size: 16px; font-weight: 800; color: #333; }
    .section-divider { border-top: 1px solid #eee; margin: 25px 0 15px 0; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏛️ Archive")
    with st.expander("📁 Yeni Kategori"):
        new_cat = st.text_input("İsim:", key="new_cat_in")
        if st.button("Ekle", use_container_width=True) and new_cat:
            if new_cat not in st.session_state.categories:
                st.session_state.categories.append(new_cat)
                st.session_state.backlog_dict[new_cat] = []
                verileri_kaydet(); st.rerun()

    st.markdown('<p class="cat-header">🎯 Oynanacaklar</p>', unsafe_allow_html=True)
    for cat in st.session_state.categories:
        games = st.session_state.backlog_dict.get(cat, [])
        if games:
            st.markdown(f'<p class="sub-cat-label">{cat}</p>', unsafe_allow_html=True)
            for g in sorted(games):
                st.markdown(f'''
                    <div class="game-row">
                        <span class="game-title">{g}</span>
                        <div class="icon-group">
                            <a href="/?act=move_ui&game={g}" target="_self" class="nano-icon" title="Kategori Değiştir">⇄</a>
                            <a href="/?act=done&game={g}" target="_self" class="nano-icon">✓</a>
                            <a href="/?act=drop&game={g}" target="_self" class="nano-icon">✕</a>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)

    for label, key, act in [("✅ Bitenler", "completed", "undo_done"), ("📁 Vazgeçilenler", "cancelled", "undo_drop")]:
        if st.session_state[key]:
            st.markdown(f'<p class="cat-header">{label}</p>', unsafe_allow_html=True)
            for g in sorted(st.session_state[key]):
                color = "#28a745" if key == "completed" else "#bbb"
                st.markdown(f'<div class="game-row"><span class="game-title" style="color:{color};">{g}</span><div class="icon-group"><a href="/?act={act}&game={g}" target="_self" class="nano-icon">↩</a></div></div>', unsafe_allow_html=True)

# --- ANA AKIŞ ---
st.title("🏛️ Gamer's Archive")
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
oyun_in = st.text_input("Oyun Ara:", placeholder="hades, gow, rdr 2...")

if st.button("Analiz Et", type="primary"):
    if oyun_in:
        with st.spinner('Taranıyor...'):
            term = KISALTMALAR.get(oyun_in.lower().strip(), oyun_in)
            try:
                s_res = scraper.get(f"https://store.steampowered.com/api/storesearch/?term={term}&l=turkish&cc=TR").json()
                if s_res and s_res['items']:
                    items = s_res['items']
                    exact = next((i for i in items if i['name'].lower() == term.lower()), None)
                    st.session_state.current_game = exact if exact else items[0]
                else: st.session_state.current_game = "NOT_FOUND"
            except: st.session_state.current_game = None

if 'current_game' in st.session_state and st.session_state.current_game:
    o = st.session_state.current_game
    if o == "NOT_FOUND": st.error("Bulunamadı!")
    else:
        app_id, temiz_isim = o['id'], o['name']
        st.image(f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg", use_container_width=True)
        st.subheader(temiz_isim)
        
        # Oyun mevcut durumu
        existing_cat = next((c for c in st.session_state.categories if temiz_isim in st.session_state.backlog_dict.get(c, [])), None)
        is_anywhere = existing_cat or temiz_isim in st.session_state.completed or temiz_isim in st.session_state.cancelled
        
        c_cat, c_add = st.columns([1, 1])
        sel_cat = c_cat.selectbox("Kategori seçin:", st.session_state.categories, index=st.session_state.categories.index(existing_cat) if existing_cat else 0, label_visibility="collapsed")
        
        btn_label = "Kategoriyi Güncelle" if existing_cat else ("❌ Kaldır" if is_anywhere else "➕ Arşivime Ekle")
        
        if c_add.button(btn_label, key="main_btn"):
            for cat in list(st.session_state.backlog_dict.keys()):
                if temiz_isim in st.session_state.backlog_dict[cat]: st.session_state.backlog_dict[cat].remove(temiz_isim)
            if temiz_isim in st.session_state.completed: st.session_state.completed.remove(temiz_isim)
            if temiz_isim in st.session_state.cancelled: st.session_state.cancelled.remove(temiz_isim)
            
            if not (is_anywhere and btn_label == "❌ Kaldır"):
                if sel_cat not in st.session_state.backlog_dict: st.session_state.backlog_dict[sel_cat] = []
                st.session_state.backlog_dict[sel_cat].append(temiz_isim)
            verileri_kaydet(); st.rerun()

        # Metrikler ve HLTB
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
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
            score = int((r_res['query_summary']['total_positive'] / r_res['query_summary']['total_reviews']) * 100)
            s1.markdown(f'<div class="badge-card" style="border-left-color:#28a745"><span class="badge-label">Steam Puanı</span><span class="badge-value">%{score} Olumlu</span></div>', unsafe_allow_html=True)
        except: pass
        try:
            m_url = f"https://www.metacritic.com/search/{temiz_isim.replace(' ', '%20')}/?category=13"
            meta = BeautifulSoup(scraper.get(m_url, timeout=10).text, 'html.parser').find("div", class_=re.compile(r'c-siteReviewScore')).text.strip()
            s2.markdown(f'<div class="badge-card" style="border-left-color:#ffcc33"><span class="badge-label">Metascore</span><span class="badge-value">{meta}/100</span></div>', unsafe_allow_html=True)
        except: pass

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:0.95rem; font-weight:bold; color:#555;">⏳ Oynanış Süreleri (HLTB)</p>', unsafe_allow_html=True)
        try:
            res = HowLongToBeat().search(re.sub(r'\(.*?\)|[:™®]', '', temiz_isim).strip())
            if res:
                b = max(res, key=lambda x: x.similarity)
                h1, h2, h3 = st.columns(3); h1.success(f"**Main**\n{b.main_story}h"); h2.warning(f"**Extra**\n{b.main_extra}h"); h3.error(f"**100%**\n{b.completionist}h")
        except: pass