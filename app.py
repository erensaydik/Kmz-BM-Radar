import streamlit as st
import pandas as pd
import asyncio
import aiohttp
from datetime import datetime, timezone

# --- SAYFA AYARLARI & DASHBOARD ---
st.set_page_config(page_title="Enlil God Tier BM", layout="wide", initial_sidebar_state="expanded")

lang = st.sidebar.radio("🌐 Language", ("Türkçe", "English"))
is_tr = (lang == "Türkçe")

st.title("👁️ Enlil Async - Cloud Optimized Radar")
st.markdown("*Bulutun sınırlarını aş. Piyasayı asenkron hızla süpür.*" if is_tr else "*Break the cloud limits. Sweep the market with async speed.*")

# --- KATEGORİLER VE ÇEVİRİLER ---
ITEM_NAMES_TR = {
    "_BAG": "Çanta", "_CAPE": "Pelerin", "_MAIN_SWORD": "Kılıç", "_MAIN_AXE": "Balta",
    "_MAIN_MACE": "Gürz", "_MAIN_HAMMER": "Çekiç", "_2H_BOW": "Yay", "_2H_CROSSBOW": "Arbalet",
    "_MAIN_NATURESTAFF": "Doğa Asası", "_MAIN_FIRESTAFF": "Ateş Asası", "_ARMOR_PLATE_SET1": "Plaka Zırh",
    "_ARMOR_LEATHER_SET1": "Deri Ceket", "_ARMOR_CLOTH_SET1": "Kumaş Cübbe", "_HEAD_PLATE_SET1": "Plaka Kask",
    "_HEAD_LEATHER_SET1": "Deri Başlık", "_HEAD_CLOTH_SET1": "Kumaş Kukuleta", "_SHOES_PLATE_SET1": "Plaka Çizme",
    "_SHOES_LEATHER_SET1": "Deri Ayakkabı", "_SHOES_CLOTH_SET1": "Kumaş Sandalet",
    "_2H_SCYTHE_HELL": "Infernal Scythe", "_2H_AXE": "Savaş Baltası"
}
ITEM_NAMES_EN = {
    "_BAG": "Bag", "_CAPE": "Cape", "_MAIN_SWORD": "Sword", "_MAIN_AXE": "Axe",
    "_MAIN_MACE": "Mace", "_MAIN_HAMMER": "Hammer", "_2H_BOW": "Bow", "_2H_CROSSBOW": "Crossbow",
    "_MAIN_NATURESTAFF": "Nature Staff", "_MAIN_FIRESTAFF": "Fire Staff", "_ARMOR_PLATE_SET1": "Plate Armor",
    "_ARMOR_LEATHER_SET1": "Leather Jacket", "_ARMOR_CLOTH_SET1": "Cloth Robe", "_HEAD_PLATE_SET1": "Plate Helmet",
    "_HEAD_LEATHER_SET1": "Leather Hood", "_HEAD_CLOTH_SET1": "Cloth Cowl", "_SHOES_PLATE_SET1": "Plate Boots",
    "_SHOES_LEATHER_SET1": "Leather Shoes", "_SHOES_CLOTH_SET1": "Cloth Sandals",
    "_2H_SCYTHE_HELL": "Infernal Scythe", "_2H_AXE": "Battleaxe"
}

# --- SOL PANEL (FİLTRELER) ---
st.sidebar.markdown("---")
max_data_age = st.sidebar.slider("Maks. Gecikme (Dk)" if is_tr else "Max Age (Mins)", 5, 500, 150, 5)
min_profit = st.sidebar.number_input("Minimum Net Kâr" if is_tr else "Min Net Profit", min_value=0, value=25000, step=5000)
tax_rate = st.sidebar.slider("Vergi (%)" if is_tr else "Tax (%)", 0.0, 10.0, 4.0, 0.1) 

ALL_LOCATIONS = ["Lymhurst", "Bridgewatch", "Martlock", "Thetford", "Fort Sterling"]
selected_cities = st.sidebar.multiselect("Şehirler" if is_tr else "Cities", ALL_LOCATIONS, default=["Lymhurst", "Martlock", "Fort Sterling"])
locations_param = "Black Market," + ",".join(selected_cities)

st.sidebar.markdown("---")
st.sidebar.header("📦 Enlil Arama Modülü" if is_tr else "📦 Enlil Search Module")

select_all = st.sidebar.checkbox("Tüm Eşyaları Seç (Sistemi Zorla)" if is_tr else "Select All Items (Push the System)")

if select_all:
    selected_categories = list(ITEM_NAMES_TR.keys())
    selected_tiers = ["T4", "T5", "T6", "T7", "T8"]
    selected_enchants = ["Düz (.0)", ".1", ".2", ".3", ".4"]
    selected_qualities = [1, 2, 3, 4, 5]
else:
    selected_categories = st.sidebar.multiselect("Kategoriler" if is_tr else "Categories", list(ITEM_NAMES_TR.keys()), default=["_BAG", "_2H_SCYTHE_HELL", "_MAIN_AXE"], format_func=lambda x: ITEM_NAMES_TR[x] if is_tr else ITEM_NAMES_EN[x])
    selected_tiers = st.sidebar.multiselect("Tier:", ["T4", "T5", "T6", "T7", "T8"], default=["T6", "T7", "T8"])
    selected_enchants = st.sidebar.multiselect("Enchant:", ["Düz (.0)", ".1", ".2", ".3", ".4"], default=["Düz (.0)", ".1", ".2"])
    QUALITIES_MAP = {"Normal": 1, "Good": 2, "Outstanding": 3, "Excellent": 4, "Masterpiece": 5}
    selected_qualities_names = st.sidebar.multiselect("Kalite" if is_tr else "Quality", list(QUALITIES_MAP.keys()), default=["Normal", "Good"])
    selected_qualities = [QUALITIES_MAP[q] for q in selected_qualities_names]

items_list = []
for prefix in selected_categories:
    for tier in selected_tiers:
        for enc in selected_enchants:
            suffix = "" if enc == "Düz (.0)" else f"@{enc.replace('.', '')}"
            items_list.append(f"{tier}{prefix}{suffix}")

BASE_URL = "https://www.albion-online-data.com/api/v2/stats/Prices"

# --- ASENKRON (ASYNC) BULUT MOTORU ---
async def fetch_url(session, url):
    try:
        # aiohttp ile tek thread üzerinden eşzamanlı bağlantı açıyoruz
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                return await response.json()
    except:
        pass
    return []

async def fetch_all_data_async(items, locs):
    chunk_size = 75
    urls = [f"{BASE_URL}/{','.join(items[i:i + chunk_size])}?locations={locs}" for i in range(0, len(items), chunk_size)]
    
    # Tüm URL'leri TCP havuzunda asenkron olarak fırlat
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
    
    # Gelen listeleri tek bir düz listede birleştir
    flat_data = [item for sublist in results for item in sublist]
    return flat_data

# Streamlit thread'i ile asenkron döngüyü çakışmadan çalıştırmak için sarmalayıcı (wrapper)
def get_data_sync(items, locs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    data = loop.run_until_complete(fetch_all_data_async(items, locs))
    loop.close()
    return data

# --- YARDIMCI FONKSİYONLAR ---
def calc_age(date_str):
    if not date_str or date_str.startswith("0001"): return 999999
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        return int((datetime.now(timezone.utc) - dt).total_seconds() / 60)
    except: return 999999

def format_item_name(item_id):
    tier_str = item_id[:2].replace("T", "Seviye " if is_tr else "Tier ")
    enchant = ""
    base_id = item_id[2:]
    if "@" in item_id:
        parts = item_id.split("@")
        base_id = parts[0][2:]
        enchant = f" .{parts[1]}"
    name_dict = ITEM_NAMES_TR if is_tr else ITEM_NAMES_EN
    return f"{tier_str} {name_dict.get(base_id, base_id)}{enchant}"

# --- TETİKLEME ---
col1, col2 = st.columns([8, 2])
with col2:
    if st.button("🚀 ASYNC ENLİL'İ BAŞLAT" if is_tr else "🚀 INITIATE ASYNC ENLIL", use_container_width=True): 
        st.cache_data.clear()

if not items_list or not selected_cities: st.stop()

with st.spinner(f"🔥 {len(items_list)} Eşya Asenkron Hızda Taranıyor..." if is_tr else f"🔥 Async Scanning {len(items_list)} items..."):
    # Asenkron motoru burada ateşliyoruz
    raw_data = get_data_sync(items_list, locations_param)

if not raw_data: 
    st.error("API yanıt vermedi. Albion Data Project sunucuları yoğun olabilir." if is_tr else "API didn't respond. Albion Data Project might be busy.")
    st.stop()

df = pd.DataFrame(raw_data)
if 'city' not in df.columns: st.stop()

df['sell_age'] = df['sell_price_min_date'].apply(calc_age)
df['buy_age'] = df['buy_price_max_date'].apply(calc_age)
df = df[df['quality'].isin(selected_qualities)]

bm_df = df[df['city'] == 'Black Market'][['item_id', 'quality', 'buy_price_max', 'buy_age']].rename(columns={'buy_price_max': 'bm_buy_price', 'buy_age': 'bm_age'})
other_df = df[df['city'].isin(selected_cities)][['item_id', 'city', 'quality', 'sell_price_min', 'sell_age']]

merged = pd.merge(other_df, bm_df, on=['item_id', 'quality'])
merged = merged[(merged['sell_price_min'] > 0) & (merged['bm_buy_price'] > 0) & (merged['sell_age'] <= max_data_age) & (merged['bm_age'] <= max_data_age)]

if not merged.empty:
    merged['net_profit'] = (merged['bm_buy_price'] * (1 - tax_rate / 100)) - merged['sell_price_min']
    merged['roi_percent'] = (merged['net_profit'] / merged['sell_price_min']) * 100
    final_df = merged[merged['net_profit'] >= min_profit].sort_values(by='net_profit', ascending=False)
else:
    final_df = pd.DataFrame()

# --- DASHBOARD METRİKLERİ ---
st.markdown("---")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Taranan Eşya" if is_tr else "Items Scanned", len(items_list))
m2.metric("Uygun Fırsat" if is_tr else "Opportunities", len(final_df))
m3.metric("Maksimum Kâr" if is_tr else "Max Profit", f"{int(final_df['net_profit'].max()):,} 🥈" if not final_df.empty else "0")
m4.metric("En Yüksek ROI" if is_tr else "Best ROI", f"% {final_df['roi_percent'].max():.1f}" if not final_df.empty else "0")
st.markdown("---")

# --- EKRANA BASTIRMA ---
if not final_df.empty:
    display_df = final_df.copy()
    display_df['item_id'] = display_df['item_id'].apply(format_item_name)
    display_df['net_profit'] = display_df['net_profit'].astype(int).apply(lambda x: f"{x:,} 🥈")
    display_df['sell_price_min'] = display_df['sell_price_min'].astype(int).apply(lambda x: f"{x:,} 🥈")
    display_df['bm_buy_price'] = display_df['bm_buy_price'].astype(int).apply(lambda x: f"{x:,} 🥈")
    display_df['age_str'] = display_df['sell_age'].astype(str) + " / " + display_df['bm_age'].astype(str) + (" dk" if is_tr else " min")
    
    display_df = display_df[['item_id', 'quality', 'city', 'sell_price_min', 'bm_buy_price', 'net_profit', 'roi_percent', 'age_str']]
    display_df.columns = ['Eşya İsimleri', 'Kalite', 'Satın Alınacak Şehir', 'Şehir Fiyatı', 'BM Alış Fiyatı', 'Net Kâr', 'Kâr Oranı (ROI) %', 'Gecikme (Şehir / BM)'] if is_tr else ['Item Name', 'Quality', 'Buy City', 'City Price', 'BM Buy Price', 'Net Profit', 'ROI %', 'Age (City / BM)']

    st.dataframe(display_df, use_container_width=True, hide_index=True, column_config={display_df.columns[6]: st.column_config.NumberColumn(format="%.2f%%")})
else:
    st.error("Şu anki piyasada kâr bulunamadı." if is_tr else "No profit found.")
