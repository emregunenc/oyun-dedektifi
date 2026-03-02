import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
from howlongtobeatpy import HowLongToBeat
import re
import random

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Oyun Dedektifi Pro", page_icon="🎮", layout="centered")

# --- GÖRSEL TASARIM ---
st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fb; padding: 15px; border-radius: 12px; border: 1px solid #eee; }
    .stButton>button { width: 100%; border-radius: 20px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🎮 Oyun Dedektifi Pro")

# --- GELİŞMİŞ SCRAPER AYARI ---
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

# --- KUR ÇEKME ---
try:
    kur_res = scraper.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5).json()
    canli_kur = kur_res['rates']['TRY']
except:
    canli_kur = 34.2

# --- ARAMA ---
oyun_adi = st.text_input("Oyun adını yazın:", placeholder="Elden Ring")
analiz_butonu = st.button("Analiz Et", type="primary")

if analiz_butonu and oyun_adi:
    with st.spinner('Siber bariyerler aşılıyor...'):
        # 1. STEAM VERİLERİ
        s_url = f"https://store.steampowered.com/api/storesearch/?term={oyun_adi}&l=turkish&cc=TR"
        try:
            s_res = scraper.get(s_url).json()
            if s_res and s_res['items']:
                o = s_res['items'][0]
                app_id = o['id']
                temiz_isim = o['name']
                
                f_usd = o.get('price', {}).get('final', 0) / 100
                f_tl_steam = f_usd * canli_kur
                
                st.image(f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg", width='stretch')
                st.subheader(f"🔍 {temiz_isim}")
                
                # --- FİYATLAR ---
                c1, c2 = st.columns(2)
                c1.metric("Steam (Tahmini TL)", f"{f_tl_steam:.0f} TL", f"${f_usd:.2f}")
                
                # PS Store (Agresif Mod)
                ps_price = "Bulunamadı"
                ps_url = f"https://store.playstation.com/tr-tr/search/{temiz_isim.replace(' ', '%20')}"
                try:
                    ps_res = scraper.get(ps_url, timeout=10)
                    ps_soup = BeautifulSoup(ps_res.text, 'html.parser')
                    ps_find = ps_soup.find(string=re.compile(r'\d+[,.]\d+\s?TL'))
                    if ps_find:
                        ps_price = ps_find.strip()
                except: pass
                
                with c2:
                    if ps_price != "Bulunamadı":
                        st.metric("PS Store", ps_price)
                    else:
                        st.write("PS Fiyatı (Manuel)")
                        st.link_button("Fiyatı Gör 🔗", ps_url)

                # --- SKORLAR & METACRITIC ---
                st.markdown("---")
                p1, p2 = st.columns(2)
                
                # Steam Puanı
                try:
                    r_res = scraper.get(f"https://store.steampowered.com/appreviews/{app_id}?json=1&language=all").json()
                    oran = (r_res['query_summary']['total_positive'] / r_res['query_summary']['total_reviews']) * 100
                    p1.metric("Steam Puanı", f"%{int(oran)}")
                except: p1.metric("Steam Puanı", "N/A")

                # Metacritic (Arama sonuçlarından skor çekme)
                meta_score = "Bulunamadı"
                m_url = f"https://www.metacritic.com/search/{temiz_isim.replace(' ', '%20')}/?category=13"
                try:
                    m_res = scraper.get(m_url, timeout=10)
                    m_soup = BeautifulSoup(m_res.text, 'html.parser')
                    m_find = m_soup.find("div", class_=re.compile(r'c-siteReviewScore'))
                    if m_find:
                        meta_score = m_find.text.strip()
                except: pass

                with p2:
                    if meta_score != "Bulunamadı":
                        st.metric("Metascore", f"{meta_score}/100")
                    else:
                        st.write("Metascore")
                        st.link_button("Skora Bak 🔍", m_url)

                # --- HLTB (SÜRELER) ---
                st.markdown("---")
                try:
                    hltb_query = re.sub(r'\(.*?\)|[:™®]', '', temiz_isim).strip()
                    results = HowLongToBeat().search(hltb_query)
                    
                    if results:
                        best = max(results, key=lambda x: x.similarity)
                        h1, h2, h3 = st.columns(3)
                        h1.success(f"**Hikaye**\n\n{best.main_story} S.")
                        h2.warning(f"**Ekstra**\n\n{best.main_extra} S.")
                        h3.error(f"**%100**\n\n{best.completionist} S.")
                    else:
                        st.write("⏳ Oynanış Süreleri")
                        st.link_button("HLTB'de Ara", f"https://howlongtobeat.com/?q={hltb_query.replace(' ', '%20')}")
                except:
                    st.write("⏳ Oynanış Süreleri")
                    st.link_button("HLTB'ye Git", "https://howlongtobeat.com/")

            else:
                st.error("Oyun bulunamadı!")
        except Exception as e:
            st.error(f"Hata: {e}")