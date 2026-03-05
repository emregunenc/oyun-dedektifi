import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
from howlongtobeatpy import HowLongToBeat
import re
import pickle
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Gamer's Archive v2.6", page_icon="🏛️", layout="centered")

# --- 📖 KISALTMALAR ---
KISALTMALAR = {
    "hades": "Hades", "hades 2": "Hades II", "gta 5": "Grand Theft Auto V",
    "rdr 2": "Red Dead Redemption 2", "gow": "God of War", "fifa": "EA SPORTS FC 24"
}

# --- HAFIZA YÖNETİMİ ---
DB_FILE = "oyun_kutuphanem_v5_17.pkl"

def verileri_kaydet():
    data = {
        'backlog_dict': st.session_state.backlog_dict,
        'completed': list(set(st.session_state.completed)),
        'categories': st.session_state.categories
    }
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
                data = pickle.load(f)
                for k, v in data.items(): st.session_state[k] = v
        except: pass

verileri_yukle()

# --- 🎯 AKSİYON MANTIĞI ---
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

params = st.query_params
if "act" in params:
    action, game = params["act"], params["game"]
    if action == "move_ui":
        kategori_degistir_dialog(game)
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

# --- 💉 GÖRSEL TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .cat-header { font-size: 0.85rem; font-weight: 800; color: #333; text-transform: uppercase; border-bottom: 2px solid #eee; margin-top: 25px; padding-bottom: 4px; }
    .completed-header { margin-top: 50px !important; } 
    .sub-cat-label { font-size: 11px; font-weight: 700; color: #999; text-transform: uppercase; margin-top: 18px; margin-bottom: 6px; }
    .game-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; transition: 0.15s; }
    .game-row:hover { background: #f1f3f7; border-radius: 6px; padding-left: 5px; }
    .game-title { font-size: 15px; font-weight: 800 !important; color: #000 !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-grow: 1; }
    .icon-group { display: flex; gap: 14px; flex-shrink: 0; padding-left: 10px; }
    .nano-icon { text-decoration: none !important; color: #ccc !important; font-size: 17px; }
    div.stButton > button[key="main_btn"] { background-color: #28a745 !important; color: white !important; border-radius: 12px !important; height: 45px !important; font-weight: 700 !important; }
    .badge-card { background:#fff; padding: 15px 20px; border-radius: 14px; border-left: 5px solid #eee; box-shadow: 0 4px 15px rgba(0,0,0,0.04); margin-bottom: 12px; font-size: 14px; display: flex; flex-direction: column; justify-content: center; min-height: 80px; }
    .badge-label { font-size: 11px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 4px; }
    .badge-value { font-size: 16px; font-weight: 800; color: #333; }
    .tag-badge { display: inline-block; background: #f0f2f6; color: #555; border-radius: 6px; padding: 2px 8px; font-size: 10px; font-weight: 700; margin-right: 5px; margin-bottom: 5px; text-transform: uppercase; }
    .section-divider { border-top: 1px solid #eee; margin: 25px 0 15px 0; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏛️ Archive")
    with st.expander("🛠️ Kategori Yönetimi"):
        new_cat = st.text_input("Yeni Ekle:", key="new_cat_in")
        if st.button("➕ Ekle", use_container_width=True) and new_cat:
            if new_cat not in st.session_state.categories:
                st.session_state.categories.append(new_cat); st.session_state.backlog_dict[new_cat] = []
                verileri_kaydet(); st.rerun()

    st.markdown('<p class="cat-header">🎯 OYNANACAKLAR</p>', unsafe_allow_html=True)
    for cat in st.session_state.categories:
        games = st.session_state.backlog_dict.get(cat, [])
        if games:
            st.markdown(f'<p class="sub-cat-label">{cat}</p>', unsafe_allow_html=True)
            for g in sorted(games):
                st.markdown(f'''
                    <div class="game-row">
                        <span class="game-title">{g}</span>
                        <div class="icon-group">
                            <a href="/?act=move_ui&game={g}" target="_self" class="nano-icon">⇄</a>
                            <a href="/?act=done&game={g}" target="_self" class="nano-icon">✓</a>
                            <a href="/?act=drop&game={g}" target="_self" class="nano-icon">✕</a>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)

    if st.session_state.completed:
        st.markdown('<p class="cat-header completed-header">✅ BİTENLER</p>', unsafe_allow_html=True)
        for g in sorted(st.session_state.completed):
            st.markdown(f'''
                <div class="game-row" style="padding: 2px 0;">
                    <span class="game-title" style="color:#28a745 !important;">{g}</span>
                    <div class="icon-group">
                        <a href="/?act=undo_done&game={g}" target="_self" class="nano-icon">↩</a>
                    </div>
                </div>
            ''', unsafe_allow_html=True)

# --- ANA AKIŞ ---
st.title("🏛️ Gamer's Archive")
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
oyun_in = st.text_input("Oyun Ara:", placeholder="outer worlds, hades, gow...")

if oyun_in:
    try:
        term = KISALTMALAR.get(oyun_in.lower().strip(), oyun_in)
        s_res = scraper.get(f"https://store.steampowered.com/api/storesearch/?term={term}&l=turkish&cc=TR").json()
        
        if s_res and s_res['items']:
            # Soundtrack ve DLC olmayan ilk 3 sonucu ayıkla
            all_results = [i for i in s_res['items'] if "soundtrack" not in i['name'].lower() and "dlc" not in i['name'].lower()]
            
            if all_results:
                # v2.6: İlk sonuç her zaman session_state'e otomatik atanır
                if 'last_query' not in st.session_state or st.session_state.last_query != term:
                    st.session_state.current_game = all_results[0]
                    st.session_state.last_query = term

                # Alternatif butonları göster (Eğer 1'den fazla sonuç varsa)
                if len(all_results) > 1:
                    st.markdown('<p style="font-size:0.8rem; font-weight:bold; color:#888; margin-bottom:5px;">Aradığın bu değil mi? Diğer seçenekler:</p>', unsafe_allow_html=True)
                    cols = st.columns(min(len(all_results), 3))
                    for idx, item in enumerate(all_results[:3]):
                        if cols[idx].button(item['name'], key=f"select_{item['id']}", use_container_width=True):
                            st.session_state.current_game = item
                            st.rerun()
    except: pass

# --- ANALİZ SONUCU ---
if 'current_game' in st.session_state and st.session_state.current_game and st.session_state.current_game != "NOT_FOUND":
    o = st.session_state.current_game
    app_id, temiz_isim = o['id'], o['name']
    st.image(f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg", use_container_width=True)
    
    try:
        details = scraper.get(f"https://store.steampowered.com/api/appdetails?appids={app_id}&l=turkish").json()
        if details[str(app_id)]['success']:
            data = details[str(app_id)]['data']
            genres = [g['description'] for g in data.get('genres', [])]
            if len(genres) < 5:
                extra = [c['description'] for c in data.get('categories', [])]
                genres.extend(extra)
            final_tags = genres[:5]
            tags_html = "".join([f'<span class="tag-badge">{t}</span>' for t in final_tags])
            st.markdown(f'<div style="margin-top: -10px; margin-bottom: 10px;">{tags_html}</div>', unsafe_allow_html=True)
    except: pass

    st.subheader(temiz_isim)
    
    existing_cat = next((c for c in st.session_state.categories if temiz_isim in st.session_state.backlog_dict.get(c, [])), None)
    c_cat, c_add = st.columns([1, 1])
    sel_cat = c_cat.selectbox("Kategori:", st.session_state.categories, index=st.session_state.categories.index(existing_cat) if existing_cat else 0, label_visibility="collapsed")
    
    if c_add.button("Güncelle" if existing_cat else "➕ Arşivime Ekle", key="main_btn", use_container_width=True):
        for c in list(st.session_state.backlog_dict.keys()):
            if temiz_isim in st.session_state.backlog_dict[c]: st.session_state.backlog_dict[c].remove(temiz_isim)
        if temiz_isim in st.session_state.completed: st.session_state.completed.remove(temiz_isim)
        st.session_state.backlog_dict.setdefault(sel_cat, []).append(temiz_isim)
        verileri_kaydet(); st.query_params.clear(); st.rerun()

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