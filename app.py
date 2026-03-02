import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
from howlongtobeatpy import HowLongToBeat
import re
import random

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Oyun Dedektifi Pro", page_icon="🎮", layout="centered")

# --- GÖRSEL TASARIM (Gelişmiş CSS) ---
st.markdown("""
    <style>
    /* Orijinal kutucuk yapısını koru ve geliştir */
    .stMetric { 
        background-color: #f8f9fb; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #eee; 
    }
    /* Yazı boyutlarını büyüt */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }
    .stButton>button { width: 100%; border-radius: 20px; font-weight: bold; }
    
    /* Özel Skor Renkleri */
    .score-green { color: #28a745 !important; }
    .score-orange { color: #fd7e14 !important; }
    .score-red { color: #dc3545 !important; }
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
oyun_adi = st.text_input("Oyun adını yazın:", placeholder="Örn: Hades, God of War, Elden Ring...")
analiz_butonu = st.button("Analiz Et", type="primary")

if analiz_butonu and oyun_adi:
    with st.spinner('Veriler cerrahi titizlikle taranıyor...'):
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
                
                st.image(f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg", use_container_width=True)
                st.subheader(f"🔍 {temiz_isim}")
                
                # --- FİYATLAR ---
                c1, c2 = st.columns(2)
                c1.metric("Steam (Tahmini TL)", f"{f_tl_steam:.0f} TL", f"${f_usd:.2f}")
                
                ps_price = "Bulunamadı"
                ps_url = f"https://store.playstation.com/tr-tr/search/{temiz_isim.replace(' ', '%20')}"
                try:
                    ps_res = scraper.get(ps_url, timeout=10)
                    ps_soup = BeautifulSoup(ps_res.text, 'html.parser')
                    ps_find = ps_soup.find(string=re.compile(r'\d+[,.]\d+\s?TL'))
                    if ps_find: ps_price = ps_find.strip()
                except: pass
                
                with c2:
                    if ps_price != "Bulunamadı":
                        st.metric("PS Store", ps_price)
                    else:
                        st.write("PS Store")
                        st.link_button("Fiyatı Gör 🔗", ps_url)

                # --- SKORLAR (Kutucuklar Korundu, Renkler Geldi) ---
                st.markdown("---")
                p1, p2 = st.columns(2)
                
                # Steam Puanı
                try:
                    r_res = scraper.get(f"https://store.steampowered.com/appreviews/{app_id}?json=1&language=all").json()
                    oran = int((r_res['query_summary']['total_positive'] / r_res['query_summary']['total_reviews']) * 100)
                    # Not: st.metric içinde HTML renk kullanılamadığı için alt yazıya renkli destek ekledik
                    durum = "Mükemmel" if oran >= 80 else "Ortalama" if oran >= 60 else "Zayıf"
                    p1.metric("Steam Kullanıcıları", f"%{oran}", durum)
                except: p1.metric("Steam Puanı", "N/A")

                # Metacritic
                meta_score = "N/A"
                m_url = f"https://www.metacritic.com/search/{temiz_isim.replace(' ', '%20')}/?category=13"
                try:
                    m_res = scraper.get(m_url, timeout=10)
                    m_soup = BeautifulSoup(m_res.text, 'html.parser')
                    m_find = m_soup.find("div", class_=re.compile(r'c-siteReviewScore'))
                    if m_find: 
                        meta_score = m_find.text.strip()
                        m_durum = "Kritik Başarı" if int(meta_score) >= 75 else "Karışık"
                        p2.metric("Metascore", f"{meta_score}/100", m_durum)
                    else:
                        p2.metric("Metascore", "🔍")
                        p2.link_button("Skora Git", m_url)
                except: p2.metric("Metascore", "N/A")

                # --- HLTB ---
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
                except: pass

            else:
                st.error("Oyun bulunamadı!")
        except Exception as e:
            st.error(f"Sistem Hatası: {e}")