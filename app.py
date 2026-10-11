import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone

# Sayfa Ayarları
st.set_page_config(page_title="Albion BM Arbitraj V2", layout="wide")
st.title("🗡️ Albion Black Market Arbitraj Radarı - Pro Versiyon")

# Sol Panel (Filtreler ve Ayarlar)
st.sidebar.header("⚙️ Ayarlar")
max_data_age = st.sidebar.slider("Maksimum Veri Gecikmesi (Dakika)", min_value=5, max_value=300, value=45, step=5)
min_profit = st.sidebar.number_input("Minimum Net Kâr (Gümüş)", min_value=1000, value=10000, step=1000)
tax_rate = st.sidebar.slider("Pazar Vergisi (%)", min_value=0.0, max_value=10.0, value=6.5, step=0.1) 

st.sidebar.markdown("---")
st.sidebar.header("📦 Eşya Havuzu")
# Kullanıcının ekleme çıkarma yapabileceği dinamik alan
item_input = st.sidebar.text_area(
    "Taranacak Eşyalar (Virgülle ayırın):", 
    "T4_BAG,T5_BAG,T4_MAIN_SWORD,T5_MAIN_SWORD,T4_MAIN_AXE,T5_MAIN_AXE,T4_2H_SCYTHE_HELL,T5_2H_SCYTHE_HELL,T4_ARMOR_PLATE_SET1,T4_HEAD_LEATHER_SET1",
    height=150,
    help="Albion eşya ID'lerini virgülle ayırarak yazın."
)

LOCATIONS = "Black Market,Lymhurst,Bridgewatch,Martlock,Thetford,Fort Sterling"
BASE_URL = "https://www.albion-online-data.com/api/v2/stats/Prices"

def fetch_data(items, locations):
    url = f"{BASE_URL}/{items}?locations={locations}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Hatası: {e}")
        return None

def calculate_age_in_minutes(date_str):
    if date_str.startswith("0001"): 
        return 999999
    try:
        update_time = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - update_time
        return int(delta.total_seconds() / 60)
    except:
        return 999999

# Yenileme Butonu Cache Temizler
if st.button("🔄 Verileri Yenile"):
    st.cache_data.clear()

# Eşya listesini temizle (boşlukları al)
clean_items = ",".join([i.strip() for i in item_input.split(",") if i.strip()])

# Ana Ekran - Veri Çekimi
with st.spinner("Pazar verileri çekiliyor, lütfen bekle..."):
    raw_data = fetch_data(clean_items, LOCATIONS)

if raw_data:
    df = pd.DataFrame(raw_data)

    df['sell_age_mins'] = df['sell_price_min_date'].apply(calculate_age_in_minutes)
    df['buy_age_mins'] = df['buy_price_max_date'].apply(calculate_age_in_minutes)

    bm_data = df[df['city'] == 'Black Market'][['item_id', 'quality', 'buy_price_max', 'buy_age_mins']]
    bm_data = bm_data.rename(columns={'buy_price_max': 'bm_buy_price', 'buy_age_mins': 'bm_data_age'})

    other_cities = df[df['city'] != 'Black Market'][['item_id', 'city', 'quality', 'sell_price_min', 'sell_age_mins']]

    merged = pd.merge(other_cities, bm_data, on=['item_id', 'quality'])
    merged = merged[(merged['sell_price_min'] > 0) & (merged['bm_buy_price'] > 0)]
    merged = merged[(merged['sell_age_mins'] <= max_data_age) & (merged['bm_data_age'] <= max_data_age)]

    if not merged.empty:
        tax_multiplier = 1 - (tax_rate / 100)
        merged['net_profit'] = (merged['bm_buy_price'] * tax_multiplier) - merged['sell_price_min']
        merged['roi_percent'] = (merged['net_profit'] / merged['sell_price_min']) * 100

        profitable = merged[merged['net_profit'] >= min_profit].sort_values(by='net_profit', ascending=False)

        if not profitable.empty:
            st.success(f"🔥 {len(profitable)} adet kârlı rota bulundu!")
            
            display_df = profitable.copy()
            # Sayıları virgüllü formata çevirme (ör: 100,000)
            display_df['net_profit'] = display_df['net_profit'].astype(int).apply(lambda x: f"{x:,}")
            display_df['sell_price_min'] = display_df['sell_price_min'].astype(int).apply(lambda x: f"{x:,}")
            display_df['bm_buy_price'] = display_df['bm_buy_price'].astype(int).apply(lambda x: f"{x:,}")
            
            display_df['roi_percent'] = display_df['roi_percent'].round(2).astype(str) + "%"
            display_df['Veri Gecikmesi'] = "Şehir: " + display_df['sell_age_mins'].astype(str) + " dk | BM: " + display_df['bm_data_age'].astype(str) + " dk"
            
            display_df = display_df[['item_id', 'quality', 'city', 'sell_price_min', 'bm_buy_price', 'net_profit', 'roi_percent', 'Veri Gecikmesi']]
            display_df.columns = ['Eşya', 'Kalite', 'Alınacak Şehir', 'Şehir Fiyatı', 'BM Alış', 'Net Kâr', 'Kâr Oranı (ROI)', 'Veri Gecikmesi']

            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.warning(f"Belirlediğin net kâr marjına ({min_profit} gümüş) uygun güncel eşya bulunamadı.")
    else:
        st.error(f"Son {max_data_age} dakika içinde güncellenmiş ve eşleşen pazar verisi bulunamadı.")
