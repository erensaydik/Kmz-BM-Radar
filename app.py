import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Albion BM Arbitraj Pro", layout="wide", initial_sidebar_state="expanded")
st.title("🗡️ Albion Black Market Arbitraj Radarı - Final+")

# --- KATEGORİ SÖZLÜĞÜ ---
CATEGORY_PREFIXES = {
    "Çantalar (Bags)": "_BAG",
    "Pelerinler (Capes)": "_CAPE",
    "Kılıçlar (Swords)": "_MAIN_SWORD",
    "Baltalar (Axes)": "_MAIN_AXE",
    "Gürzler (Maces)": "_MAIN_MACE",
    "Çekiçler (Hammers)": "_MAIN_HAMMER",
    "Yaylar (Bows)": "_2H_BOW",
    "Arbaletler (Crossbows)": "_2H_CROSSBOW",
    "Doğa Asaları (Nature Staffs)": "_MAIN_NATURESTAFF",
    "Ateş Asaları (Fire Staffs)": "_MAIN_FIRESTAFF",
    "Plaka Zırhlar (Plate Armors)": "_ARMOR_PLATE_SET1",
    "Deri Ceketler (Leather Jackets)": "_ARMOR_LEATHER_SET1",
    "Kumaş Cübbeler (Cloth Robes)": "_ARMOR_CLOTH_SET1",
    "Plaka Kasklar (Plate Helmets)": "_HEAD_PLATE_SET1",
    "Deri Başlıklar (Leather Hoods)": "_HEAD_LEATHER_SET1",
    "Kumaş Kukuletalar (Cloth Cowls)": "_HEAD_CLOTH_SET1",
    "Plaka Çizmeler (Plate Boots)": "_SHOES_PLATE_SET1",
    "Deri Ayakkabılar (Leather Shoes)": "_SHOES_LEATHER_SET1",
    "Kumaş Sandaletler (Cloth Sandals)": "_SHOES_CLOTH_SET1"
}

ALL_LOCATIONS = ["Lymhurst", "Bridgewatch", "Martlock", "Thetford", "Fort Sterling"]
QUALITIES = {"Normal": 1, "Good": 2, "Outstanding": 3, "Excellent": 4, "Masterpiece": 5}

# --- SOL PANEL (AYARLAR VE FİLTRELER) ---
st.sidebar.header("⚙️ Genel Ayarlar")
max_data_age = st.sidebar.slider("Maks. Veri Gecikmesi (Dk)", 5, 300, 60, 5)
min_profit = st.sidebar.number_input("Minimum Net Kâr (Gümüş)", min_value=0, value=5000, step=1000)
tax_rate = st.sidebar.slider("Pazar Vergisi (%)", 0.0, 10.0, 4.0, 0.1) 

st.sidebar.markdown("---")
st.sidebar.header("🗺️ Alım Şehirleri")
selected_cities = st.sidebar.multiselect(
    "Hangi şehirlerdeki fiyatlara bakılsın?",
    options=ALL_LOCATIONS,
    default=ALL_LOCATIONS
)
# API için lokasyonları birleştir (Black Market her zaman olmalı)
locations_param = "Black Market," + ",".join(selected_cities)

st.sidebar.markdown("---")
st.sidebar.header("📦 Eşya Taraması")

search_mode = st.sidebar.radio("Arama Modu", ("Kategori ve Seviye Seç (Otomatik)", "Manuel ID Gir (Gelişmiş)"))

items_list = []

if search_mode == "Kategori ve Seviye Seç (Otomatik)":
    selected_categories = st.sidebar.multiselect("Kategoriler:", list(CATEGORY_PREFIXES.keys()), default=["Çantalar (Bags)", "Kılıçlar (Swords)"])
    selected_tiers = st.sidebar.multiselect("Seviyeler (Tier):", ["T4", "T5", "T6", "T7", "T8"], default=["T4", "T5"])
    selected_enchants = st.sidebar.multiselect("Büyü (Enchant):", ["Düz (.0)", ".1", ".2", ".3", ".4"], default=["Düz (.0)", ".1"])
    selected_qualities_names = st.sidebar.multiselect("Kalite:", list(QUALITIES.keys()), default=["Normal", "Good"])
    
    selected_qualities = [QUALITIES[q] for q in selected_qualities_names]
    
    for cat in selected_categories:
        prefix = CATEGORY_PREFIXES[cat]
        for tier in selected_tiers:
            for enc in selected_enchants:
                suffix = "" if enc == "Düz (.0)" else f"@{enc.replace('.', '')}"
                items_list.append(f"{tier}{prefix}{suffix}")
    
    if items_list:
        st.sidebar.caption(f"Arka planda {len(items_list)} farklı eşya ID'si taranacak.")
else:
    manual_input = st.sidebar.text_area("Eşya ID'lerini virgülle ayırarak gir:", "T4_BAG,T4_BAG@1", height=150)
    items_list = [i.strip().upper() for i in manual_input.split(",") if i.strip()]
    selected_qualities = [1, 2, 3, 4, 5] # Manuel modda tüm kaliteleri getir

BASE_URL = "https://www.albion-online-data.com/api/v2/stats/Prices"

# --- YARDIMCI FONKSİYONLAR ---
def fetch_data_in_chunks(items_list, locs):
    # Çok fazla eşya seçildiğinde URL sınırına takılmamak için listeyi 100'erli gruplara böleriz
    chunk_size = 100
    all_data = []
    
    for i in range(0, len(items_list), chunk_size):
        chunk = items_list[i:i + chunk_size]
        items_str = ",".join(chunk)
        url = f"{BASE_URL}/{items_str}?locations={locs}"
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                all_data.extend(r.json())
        except:
            pass
    return all_data

def calc_age(date_str):
    if not date_str or date_str.startswith("0001"): return 999999
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        return int((datetime.now(timezone.utc) - dt).total_seconds() / 60)
    except:
        return 999999

# --- ANA İŞLEM ---
col1, col2 = st.columns([8, 2])
with col2:
    if st.button("🔄 Verileri Şimdi Yenile", use_container_width=True):
        st.cache_data.clear()

if not items_list or not selected_cities:
    st.info("👈 Lütfen sol menüden en az bir kategori/tier ve en az bir şehir seçin.")
    st.stop()

with st.spinner(f"{len(items_list)} eşya derinlemesine taranıyor..."):
    raw_data = fetch_data_in_chunks(items_list, locations_param)

if not raw_data:
    st.warning("Girdiğin kriterler için API'de hiç veri yok.")
    st.stop()

df = pd.DataFrame(raw_data)
if 'city' not in df.columns:
    st.warning("Beklenmeyen veri formatı geldi.")
    st.stop()

df['sell_age'] = df['sell_price_min_date'].apply(calc_age)
df['buy_age'] = df['buy_price_max_date'].apply(calc_age)

# Sadece seçilen kalitedeki ürünleri filtrele
df = df[df['quality'].isin(selected_qualities)]

bm_df = df[df['city'] == 'Black Market'][['item_id', 'quality', 'buy_price_max', 'buy_age']]
bm_df.rename(columns={'buy_price_max': 'bm_buy_price', 'buy_age': 'bm_age'}, inplace=True)

# Seçili şehirlerdeki satışları filtrele
other_df = df[df['city'].isin(selected_cities)][['item_id', 'city', 'quality', 'sell_price_min', 'sell_age']]

merged = pd.merge(other_df, bm_df, on=['item_id', 'quality'])
total_pairs = len(merged)

merged = merged[(merged['sell_price_min'] > 0) & (merged['bm_buy_price'] > 0)]
valid_prices = len(merged)

merged = merged[(merged['sell_age'] <= max_data_age) & (merged['bm_age'] <= max_data_age)]
age_passed = len(merged)

if not merged.empty:
    tax_multiplier = 1 - (tax_rate / 100)
    merged['net_profit'] = (merged['bm_buy_price'] * tax_multiplier) - merged['sell_price_min']
    merged['roi_percent'] = (merged['net_profit'] / merged['sell_price_min']) * 100

    final_df = merged[merged['net_profit'] >= min_profit].sort_values(by='net_profit', ascending=False)
    profit_passed = len(final_df)
else:
    final_df = pd.DataFrame()
    profit_passed = 0

# --- EKRANA BASTIRMA ---
if not final_df.empty:
    st.success(f"🔥 Toplam {profit_passed} kârlı arbitraj fırsatı bulundu!")
    
    # Veri gösterimi
    display_df = final_df.copy()
    display_df['net_profit'] = display_df['net_profit'].astype(int).apply(lambda x: f"{x:,} 🥈")
    display_df['sell_price_min'] = display_df['sell_price_min'].astype(int).apply(lambda x: f"{x:,} 🥈")
    display_df['bm_buy_price'] = display_df['bm_buy_price'].astype(int).apply(lambda x: f"{x:,} 🥈")
    
    # ROI'ye göre sıralama imkanı için ROI'yi float olarak bırakıp Streamlit'in Column Config'i ile formatlayalım
    display_df['roi_percent'] = display_df['roi_percent'].round(2)
    display_df['Gecikme (Şehir / BM)'] = display_df['sell_age'].astype(str) + " dk / " + display_df['bm_age'].astype(str) + " dk"
    
    display_df = display_df[['item_id', 'quality', 'city', 'sell_price_min', 'bm_buy_price', 'net_profit', 'roi_percent', 'Gecikme (Şehir / BM)']]
    display_df.columns = ['Eşya', 'Kalite', 'Satın Alınacak Şehir', 'Şehir Fiyatı', 'BM Alış Fiyatı', 'Net Kâr', 'Kâr Oranı (ROI) %', 'Gecikme (Şehir / BM)']

    st.dataframe(
        display_df, 
        use_container_width=True, 
        hide_index=True,
        # ROI kolonunu Streamlit içinde formatlayarak tablodaki oklarla sıralanabilir (sortable) bırakıyoruz
        column_config={
            "Kâr Oranı (ROI) %": st.column_config.NumberColumn(format="%.2f%%")
        }
    )
else:
    st.warning("Mevcut filtrelerine uygun kârlı bir sonuç bulunamadı!")

# --- VERİ ANALİZ PANELİ ---
with st.expander("📊 Arka Plan Analizi (Filtreleme Detayları)"):
    st.write(f"- 🧩 Seçilen Şehirlerdeki İlgili Eşya Verisi (Eşleşme): **{total_pairs}**")
    st.write(f"- 💰 Oyuncuların Girdiği Geçerli Fiyat Sayısı: **{valid_prices}**")
    st.write(f"- ⏳ Son {max_data_age} Dakika İçinde Güncellenmiş (Taze) Fiyatlar: **{age_passed}**")
    st.write(f"- 📈 Kâr Hedefine (Minimum {min_profit:,} gümüş) Ulaşan Fırsatlar: **{profit_passed}**")
