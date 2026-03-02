import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
from howlongtobeatpy import HowLongToBeat
import re

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Oyun Dedektifi", page_icon="🎮", layout="centered")

# --- GÖRSEL DÜZENLEME ---
st.markdown("""
    <style>
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }
    </style>
""", unsafe_allow_html=True)

st.title("🎮 Oyun Dedektifi")

# --- KUR ÇEKME ---
scraper = cloudscraper.create_scraper()
try:
    kur_res = scraper.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5).json()
    canli_kur = kur_res['rates']['TRY']
except:
    canli_kur = 32.8

# --- YAN PANEL ---
st.sidebar.header("⚙️ Ayarlar")
kur_ayari = st.sidebar.number_input("Dolar Kuru (TL)", value=float(canli_kur), step=0.1)

# --- ARAMA ---
oyun_adi = st.text_input("Oyun adını yazın:", placeholder="Elden Ring")
analiz_butonu = st.button("Analiz Et", type="primary")

if analiz_butonu:
    if not oyun_adi:
        st.warning("Lütfen bir oyun adı girin.")
    else:
        with st.spinner('Veriler toplanıyor...'):
            # 1. STEAM VERİLERİ
            s_url = f"https://store.steampowered.com/api/storesearch/?term={oyun_adi}&l=turkish&cc=TR"
            try:
                s_res = scraper.get(s_url).json()
                if s_res and s_res['items']:
                    o = s_res['items'][0]
                    app_id = o['id']
                    temiz_isim = o['name']
                    
                    # Özel karakterleri temizle (HLTB araması için)
                    arama_ismi = re.sub(r'[^\w\s]', '', temiz_isim)
                    
                    f_usd = o.get('price', {}).get('final', 0) / 100
                    f_tl = f_usd * kur_ayari
                    
                    # Kapak Fotoğrafı
                    img_url = f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg"
                    st.image(img_url, use_container_width=True)
                    st.subheader(f"🔍 {temiz_isim}")
                    
                    # Fiyat ve Puan Kartları
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Dolar Fiyatı", f"${f_usd:.2f}")
                    col2.metric("Tahmini TL", f"{f_tl:.0f} TL")
                    
                    # Steam Puanı
                    r_res = scraper.get(f"https://store.steampowered.com/appreviews/{app_id}?json=1&language=all").json()
                    total = r_res.get('query_summary', {}).get('total_reviews', 1)
                    total = total if total > 0 else 1
                    oran = (r_res.get('query_summary', {}).get('total_positive', 0) / total) * 100
                    col3.metric("Steam Puanı", f"%{int(oran)}")

                    # Metacritic
                    m_res = scraper.get(f"https://www.metacritic.com/search/{oyun_adi}/?category=13")
                    soup = BeautifulSoup(m_res.text, 'html.parser')
                    score = soup.find("div", class_="c-siteReviewScore")
                    v_meta = score.text.strip() if score else "-"
                    col4.metric("Metascore", f"{v_meta}/100")

                    # --- HLTB BÖLÜMÜ ---
                    st.markdown("---")
                    st.write("### ⏳ Oynanış Süreleri (HowLongToBeat)")
                    
                    try:
                        # HLTB araması (Kademeli deneme)
                        results = HowLongToBeat().search(arama_ismi)
                        if not results:
                            results = HowLongToBeat().search(" ".join(arama_ismi.split()[:2]))
                        
                        if results:
                            best = max(results, key=lambda x: x.similarity)
                            c1, c2, c3 = st.columns(3)
                            c1.success(f"**Hikaye**\n\n {best.main_story} Saat")
                            c2.warning(f"**Ekstralar**\n\n {best.main_extra} Saat")
                            c3.error(f"**%100**\n\n {best.completionist} Saat")
                        else:
                            st.info("Süre bilgisi otomatik çekilemedi.")
                            st.markdown(f"[Buraya tıklayarak manuel bakabilirsiniz](https://howlongtobeat.com/?q={arama_ismi.replace(' ', '%20')})")
                    except Exception:
                        st.warning("HLTB servisi şu an cevap vermiyor.")
                else:
                    st.error("Oyun Steam'de bulunamadı!")
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")