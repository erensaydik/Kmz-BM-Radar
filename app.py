import streamlit as st
import pandas as pd
import asyncio
import aiohttp
import plotly.express as px
from datetime import datetime, timezone

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Enlil God Tier BM", layout="wide", initial_sidebar_state="expanded")

lang = st.sidebar.radio("🌐 Language / Dil", ("Türkçe", "English"))
is_tr = (lang == "Türkçe")

st.title("👁️ Enlil V6 - Albion Analyser Killer" if is_tr else "👁️ Enlil V6 - The Analyser Killer")
st.markdown("*Piyasayı süpür. Grafiklerle analiz et. Kârı al ve çık.*" if is_tr else "*Sweep the market. Analyze with charts. Take the profit.*")

# --- MEGA EŞYA SÖZLÜĞÜ (TAM CEPHANELİK) ---
ITEM_NAMES_TR = {
    "_BAG": "Çanta", "_CAPE": "Normal Pelerin", 
    "_CAPEITEM_FW_MARTLOCK": "Martlock Pelerini", "_CAPEITEM_FW_LYMHURST": "Lymhurst Pelerini", 
    "_CAPEITEM_FW_THETFORD": "Thetford Pelerini", "_CAPEITEM_FW_FORTSTERLING": "Fort Sterling Pelerini", 
    "_CAPEITEM_FW_BRIDGEWATCH": "Bridgewatch Pelerini", "_CAPEITEM_FW_CAERLEON": "Caerleon Pelerini",
    "_MAIN_SWORD": "Tek El Kılıç", "_2H_SWORD": "Çift El Kılıç", "_2H_CLAYMORE": "Claymore", 
    "_2H_DUALSWORD": "Çifte Kılıç", "_MAIN_SCIMITAR_MORGANA": "Clarent Kılıcı", 
    "_2H_CLEAVER_HELL": "Carving Kılıcı", "_2H_DUALSCIMITAR_UNDEAD": "Galatine Pair", "_2H_CLAYMORE_AVALON": "Kingmaker",
    "_MAIN_AXE": "Savaş Baltası", "_2H_AXE": "Büyük Balta", "_2H_HALBERD": "Teber (Halberd)", 
    "_2H_SCYTHE_HELL": "Infernal Tırpan", "_2H_DUALAXE_KEEPER": "Ayı Pençesi (Bear Paws)", "_MAIN_AXE_AVALON": "Realmbreaker",
    "_MAIN_MACE": "Tek El Gürz", "_2H_MACE": "Ağır Gürz", "_2H_FLAIL": "Sabah Yıldızı", 
    "_MAIN_ROCKMACE_KEEPER": "Bedrock Gürzü", "_MAIN_HAMMER": "Çekiç", "_2H_HAMMER": "Büyük Çekiç", 
    "_2H_POLEHAMMER": "Sırıklı Çekiç", "_2H_RAM_KEEPER": "Grovekeeper",
    "_MAIN_DAGGER": "Tek El Hançer", "_2H_DAGGER": "Çifte Hançer", "_2H_CLAW": "Pençe (Claw)", 
    "_MAIN_DAGGER_HELL": "Kan Mektubu (Bloodletter)", "_2H_DAGGER_UNDEAD": "Deathgivers",
    "_MAIN_SPEAR": "Mızrak", "_2H_SPEAR": "Pike", "_2H_GLAIVE": "Glaive", "_2H_HARPOON_HELL": "Spirithunter",
    "_2H_BOW": "Yay", "_2H_WARBOW": "Savaş Yayı", "_2H_LONGBOW": "Uzun Yay", "_2H_BOW_KEEPER": "Badon Yayı",
    "_MAIN_CROSSBOW": "Hafif Arbalet", "_2H_CROSSBOW": "Arbalet", "_2H_CROSSBOWLARGE": "Ağır Arbalet", 
    "_2H_DUALCROSSBOW_HELL": "Boltcasters", "_2H_REPEATINGCROSSBOW_UNDEAD": "Weeping Repeater",
    "_MAIN_NATURESTAFF": "Doğa Asası", "_2H_NATURESTAFF": "Büyük Doğa Asası", "_2H_WILDSTAFF": "Vahşi Asa", 
    "_MAIN_FIRESTAFF": "Ateş Asası", "_2H_FIRESTAFF": "Büyük Ateş Asası", "_2H_INFERNOSTAFF": "Cehennem Asası", 
    "_MAIN_FROSTSTAFF": "Buz Asası", "_2H_FROSTSTAFF": "Büyük Buz Asası", "_2H_GLACIALSTAFF": "Buzul Asası", 
    "_MAIN_HOLYSTAFF": "Kutsal Asa", "_2H_HOLYSTAFF": "Büyük Kutsal Asa", "_2H_DIVINESTAFF": "İlahi Asa", 
    "_MAIN_CURSESTAFF": "Lanetli Asa", "_2H_DEMONICSTAFF": "İblis Asası",
    "_OFF_SHIELD": "Kalkan", "_OFF_TOWERSHIELD": "Kule Kalkanı", "_OFF_BOOK": "Büyü Kitabı", 
    "_OFF_ORB": "Büyü Küresi", "_OFF_TORCH": "Meşale", "_OFF_HORN": "Savaş Borusu",
    "_HEAD_PLATE_SET1": "Asker Kaskı", "_ARMOR_PLATE_SET1": "Asker Zırhı", "_SHOES_PLATE_SET1": "Asker Çizmesi",
    "_HEAD_PLATE_SET2": "Şövalye Kaskı", "_ARMOR_PLATE_SET2": "Şövalye Zırhı", "_SHOES_PLATE_SET2": "Şövalye Çizmesi",
    "_HEAD_PLATE_SET3": "Gardiyan Kaskı", "_ARMOR_PLATE_SET3": "Gardiyan Zırhı", "_SHOES_PLATE_SET3": "Gardiyan Çizmesi",
    "_HEAD_LEATHER_SET1": "Paralı Asker Başlığı", "_ARMOR_LEATHER_SET1": "Paralı Asker Ceketi", "_SHOES_LEATHER_SET1": "Paralı Asker Ayakkabısı",
    "_HEAD_LEATHER_SET2": "Avcı Başlığı", "_ARMOR_LEATHER_SET2": "Avcı Ceketi", "_SHOES_LEATHER_SET2": "Avcı Ayakkabısı",
    "_HEAD_LEATHER_SET3": "Suikastçı Başlığı", "_ARMOR_LEATHER_SET3": "Suikastçı Ceketi", "_SHOES_LEATHER_SET3": "Suikastçı Ayakkabısı",
    "_HEAD_CLOTH_SET1": "Bilgin Kukuletası", "_ARMOR_CLOTH_SET1": "Bilgin Cübbesi", "_SHOES_CLOTH_SET1": "Bilgin Sandaleti",
    "_HEAD_CLOTH_SET2": "Ruhban Kukuletası", "_ARMOR_CLOTH_SET2": "Ruhban Cübbesi", "_SHOES_CLOTH_SET2": "Ruhban Sandaleti",
    "_HEAD_CLOTH_SET3": "Büyücü Kukuletası", "_ARMOR_CLOTH_SET3": "Büyücü Cübbesi", "_SHOES_CLOTH_SET3": "Büyücü Sandaleti",
}
# İngilizce çevirileri basitleştirmek için aynı anahtarları İngilizceye uyarlayabilirsiniz, yer kaplamaması için TR üzerinden devam ediyoruz
ITEM_NAMES_EN = {k: k.replace("_", " ").title() for k in ITEM_NAMES_TR.keys()} 

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

select_all = st.sidebar.checkbox("🚨 Tüm Eşyaları Seç (Sistemi Zorla)" if is_tr else "🚨 Select All Items (Push the System)")

if select_all:
    selected_categories = list(ITEM_NAMES_TR.keys())
    selected_tiers = ["T4", "T5", "T6", "T7", "T8"]
    selected_enchants = ["Düz (.0)", ".1", ".2", ".3", ".4"]
    selected_qualities = [1, 2, 3, 4, 5]
    st.sidebar.warning("⚠️ Bütün cephanelik seçildi! Yüzlerce URL aynı anda ateşlenecek." if is_tr else "⚠️ All arsenal selected! Hundreds of URLs will be fired simultaneously.")
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
        async with session.get(url, timeout=20) as response:
            if response.status == 200: return await response.json()
    except: pass
    return []

async def fetch_all_data_async(items, locs):
    chunk_size = 75
    urls = [f"{BASE_URL}/{','.join(items[i:i + chunk_size])}?locations={locs}" for i in range(0, len(items), chunk_size)]
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
    return [item for sublist in results for item in sublist]

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

# --- TETİKLEME VE VERİ İŞLEME ---
col1, col2 = st.columns([8, 2])
with col2:
    if st.button("🚀 ENLİL V6'YI BAŞLAT" if is_tr else "🚀 INITIATE ENLIL V6", use_container_width=True): 
        st.cache_data.clear()

if not items_list or not selected_cities: st.stop()

with st.spinner(f"🔥 {len(items_list)} Eşya Asenkron Hızda Taranıyor..." if is_tr else f"🔥 Async Scanning {len(items_list)} items..."):
    raw_data = get_data_sync(items_list, locations_param)

if not raw_data: 
    st.error("API yanıt vermedi veya çok fazla istekten dolayı gecikti." if is_tr else "API didn't respond or delayed due to high volume.")
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
    
    # İsimleri Analiz İçin Şimdiden Çevir
    final_df['Eşya İsmi'] = final_df['item_id'].apply(format_item_name)
    final_df['Gecikme (Şehir/BM)'] = final_df['sell_age'].astype(str) + " / " + final_df['bm_age'].astype(str) + " dk"
else:
    final_df = pd.DataFrame()

# --- V6 ANALİZ VE GRAFİK ARAYÜZÜ ---
if not final_df.empty:
    st.markdown("---")
    
    # 1. GOD TIER FIRSAT BULUCU
    god_tier = final_df[(final_df['net_profit'] >= 100000) & (final_df['roi_percent'] >= 20.0)]
    
    colA, colB, colC, colD = st.columns(4)
    colA.metric("Uygun Fırsat Sayısı", len(final_df))
    colB.metric("Toplam Potansiyel Kâr", f"{int(final_df['net_profit'].sum()):,} 🥈")
    colC.metric("En Yüksek Tekil Kâr", f"{int(final_df['net_profit'].max()):,} 🥈")
    colD.metric("God Tier Fırsat Sayısı", len(god_tier), delta="ZENGİNLİK ALARMI" if len(god_tier) > 0 else "Normal Piyasa", delta_color="normal")
    
    if not god_tier.empty:
        st.success(f"👑 {len(god_tier)} ADET GOD TIER FIRSAT TESPİT EDİLDİ! (En az 100k Kâr ve %20 ROI)")
    
    # 2. İNTERAKTİF FIRSAT RADARI (PLOTLY)
    st.markdown("### 📊 Enlil Fırsat Radarı (Yatırım vs Kâr)" if is_tr else "### 📊 Enlil Opportunity Radar")
    
    fig = px.scatter(
        final_df, 
        x="sell_price_min", 
        y="net_profit", 
        size="roi_percent", 
        color="city", 
        hover_name="Eşya İsmi",
        hover_data={"sell_price_min": True, "net_profit": True, "roi_percent": ':.2f', "city": False},
        labels={
            "sell_price_min": "Şehirdeki Satış Fiyatı (Yatırım) 🥈",
            "net_profit": "Net Kâr 🥈",
            "roi_percent": "Kâr Oranı (ROI) %",
            "city": "Şehir"
        },
        template="plotly_dark",
        size_max=30
    )
    # Grafiği tam genişlikte çizdir
    st.plotly_chart(fig, use_container_width=True)

    # 3. VERİ TABLOSU
    st.markdown("### 📋 Arbitraj Listesi" if is_tr else "### 📋 Arbitrage List")
    
    display_df = final_df.copy()
    display_df['net_profit_str'] = display_df['net_profit'].astype(int).apply(lambda x: f"{x:,} 🥈")
    display_df['sell_price_min_str'] = display_df['sell_price_min'].astype(int).apply(lambda x: f"{x:,} 🥈")
    display_df['bm_buy_price_str'] = display_df['bm_buy_price'].astype(int).apply(lambda x: f"{x:,} 🥈")
    
    table_df = display_df[['Eşya İsmi', 'quality', 'city', 'sell_price_min_str', 'bm_buy_price_str', 'net_profit_str', 'roi_percent', 'Gecikme (Şehir/BM)']]
    table_df.columns = ['Eşya İsimleri', 'Kalite', 'Satın Alınacak Şehir', 'Şehir Fiyatı', 'BM Alış Fiyatı', 'Net Kâr', 'Kâr Oranı (ROI) %', 'Gecikme (Şehir / BM)']

    st.dataframe(table_df, use_container_width=True, hide_index=True, column_config={table_df.columns[6]: st.column_config.NumberColumn(format="%.2f%%")})
    
    # 4. CSV DIŞA AKTARMA (PREMIUM ÖZELLİK)
    st.markdown("---")
    csv_export = final_df[['Eşya İsmi', 'quality', 'city', 'sell_price_min', 'bm_buy_price', 'net_profit', 'roi_percent', 'sell_age', 'bm_age']].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Tüm Fırsatları Excel (CSV) Olarak İndir" if is_tr else "📥 Download All Opportunities as CSV",
        data=csv_export,
        file_name=f'enlil_arbitraj_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
        mime='text/csv',
    )

else:
    st.error("Şu anki piyasada kâr bulunamadı." if is_tr else "No profit found.")
