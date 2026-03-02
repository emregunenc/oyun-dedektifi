import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
from howlongtobeatpy import HowLongToBeat
import re
import json

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Oyun Dedektifi Pro", page_icon="🎮", layout="wide")

# --- GÖRSEL TASARIM ---
st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fb; padding: 15px; border-radius: 12px; border: 1px solid #eee; }
    .stButton>button { width: 100%; border-radius: 20px; font-weight: bold; background-color: #00439c; color: white; height: 3.5em; }
    </style>
""", unsafe_allow_html=True)

st.title("🎮 Oyun Dedektifi Pro")

# --- GELİŞMİŞ SCRAPER ---
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
)

# --- KUR ÇEKME ---
try:
    kur_res = scraper.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5).json()
    canli_kur = kur_res['rates']['TRY']
except:
    canli_kur = 34.2

# --- ARAMA ---
oyun_adi = st.text_input("Oyun adını yazın:", placeholder="Örn: Hades, God of War...")
analiz_butonu = st.button("Analiz Et", type="primary")

if analiz_butonu and oyun_adi:
    with st.spinner('Epic sunucularına sızılıyor...'):
        # 1. STEAM VERİLERİ
        s_url = f"https://store.steampowered.com/api/storesearch/?term={oyun_adi}&l=turkish&cc=TR"
        try:
            s_res = scraper.get(s_url).json()
            if s_res and s_res['items']:
                # AKILLI EŞLEŞME
                items = s_res['items']
                o = items[0]
                for item in items[:5]:
                    if item['name'].lower() == oyun_adi.strip().lower():
                        o = item
                        break
                
                app_id = o['id']
                temiz_isim = o['name']
                f_usd = o.get('price', {}).get('final', 0) / 100
                f_tl_steam = f_usd * canli_kur
                
                # --- ÜST PANEL ---
                col_img, col_info = st.columns([1, 2])
                with col_img:
                    st.image(f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg", use_container_width=True)
                with col_info:
                    st.subheader(f"🔍 {temiz_isim}")
                    st.write(f"Steam Tahmini: **{f_tl_steam:.2f} TL**")

                # --- 💰 MAĞAZALAR ---
                st.markdown("### 💰 Fiyat Karşılaştırması")
                c1, c2, c3 = st.columns(3)
                
                c1.metric("Steam", f"{f_tl_steam:.0f} TL", f"${f_usd:.2f}")
                
                # PS Store
                ps_url = f"https://store.playstation.com/tr-tr/search/{temiz_isim.replace(' ', '%20')}"
                ps_price = "Bulunamadı"
                try:
                    ps_res = scraper.get(ps_url, timeout=7)
                    ps_soup = BeautifulSoup(ps_res.text, 'html.parser')
                    ps_find = ps_soup.find(string=re.compile(r'\d+[,.]\d+\s?TL'))
                    if ps_find: ps_price = ps_find.strip()
                except: pass
                with c2:
                    if ps_price != "Bulunamadı": st.metric("PS Store", ps_price)
                    else: st.link_button("PS Fiyatı 🔗", ps_url)

                # ✅ EPIC GAMES - GRAPHQL API METODU (Online Fix)
                epic_price = "Bulunamadı"
                epic_url = f"https://store.epicgames.com/tr/browse?q={temiz_isim.replace(' ', '%20')}"
                try:
                    # Epic'in gizli API hattına sorgu gönderiyoruz
                    graphql_url = "https://graphql.epicgames.com/graphql"
                    query = {
                        "query": "query searchStoreQuery($keywords: String, $locale: String, $country: String) { Catalog { searchStore(keywords: $keywords, locale: $locale, country: $country) { elements { title price(country: $country) { totalPrice { fmtPrice { intermediatePrice } } } } } } }",
                        "variables": {"keywords": temiz_isim, "locale": "tr", "country": "TR"}
                    }
                    e_res = scraper.post(graphql_url, json=query, timeout=10).json()
                    
                    # Gelen sonuçlar içinde arama yap
                    elements = e_res['data']['Catalog']['searchStore']['elements']
                    if elements:
                        # İlk sonucun fiyatını al
                        epic_price = elements[0]['price']['totalPrice']['fmtPrice']['intermediatePrice']
                except: pass

                with c3:
                    if epic_price != "Bulunamadı":
                        st.metric("Epic Games", epic_price)
                    else:
                        st.link_button("Epic Fiyatı 🔗", epic_url)

                # --- SKORLAR & SÜRELER ---
                st.markdown("---")
                p1, p2 = st.columns(2)
                try:
                    r_res = scraper.get(f"https://store.steampowered.com/appreviews/{app_id}?json=1&language=all").json()
                    oran = (r_res['query_summary']['total_positive'] / r_res['query_summary']['total_reviews']) * 100
                    p1.metric("Steam Puanı", f"%{int(oran)}")
                except: p1.metric("Steam Puanı", "N/A")

                # Metascore
                meta_score = "N/A"
                m_url = f"https://www.metacritic.com/search/{temiz_isim.replace(' ', '%20')}/?category=13"
                try:
                    m_res = scraper.get(m_url, timeout=10)
                    m_soup = BeautifulSoup(m_res.text, 'html.parser')
                    m_find = m_soup.find("div", class_=re.compile(r'c-siteReviewScore'))
                    if m_find: meta_score = m_find.text.strip()
                except: pass
                p2.metric("Metascore", f"{meta_score}/100" if meta_score != "N/A" else "N/A")

                # HLTB
                st.markdown("---")
                try:
                    h_query = re.sub(r'[^a-zA-Z0-9\s]', '', temiz_isim).strip()
                    results = HowLongToBeat().search(h_query)
                    if results:
                        best = max(results, key=lambda x: x.similarity)
                        h1, h2, h3 = st.columns(3)
                        h1.success(f"**Hikaye**\n{best.main_story} Sa.")
                        h2.warning(f"**Ekstra**\n{best.main_extra} Sa.")
                        h3.error(f"**%100**\n{best.completionist} Sa.")
                except: pass
            else:
                st.error("Oyun bulunamadı!")
        except Exception as e:
            st.error(f"Sistem hatası: {e}")