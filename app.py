import streamlit as st
import pandas as pd
import asyncio
import aiohttp
from datetime import datetime, timezone

# --- SAYFA AYARLARI & DASHBOARD ---
st.set_page_config(page_title="Enlil God Tier BM", layout="wide", initial_sidebar_state="expanded")

lang = st.sidebar.radio("🌐 Language", ("Türkçe", "English"))
is_tr = (lang == "Türkçe")

st.title("👁️ Enlil Async - Mega Cephanelik" if is_tr else "👁️ Enlil Async - Mega Arsenal")
st.markdown("*Piyasayı süpür. Yüzdeleri yok et. Kârı al.*" if is_tr else "*Sweep the market. Destroy the percentages. Take the profit.*")

# --- MEGA EŞYA SÖZLÜĞÜ (OYUNDAKİ NEREDEYSE HER ŞEY) ---
ITEM_NAMES_TR = {
    # Genel
    "_BAG": "Çanta", "_CAPE": "Normal Pelerin", 
    # Şehir Pelerinleri
    "_CAPEITEM_FW_MARTLOCK": "Martlock Pelerini", "_CAPEITEM_FW_LYMHURST": "Lymhurst Pelerini", 
    "_CAPEITEM_FW_THETFORD": "Thetford Pelerini", "_CAPEITEM_FW_FORTSTERLING": "Fort Sterling Pelerini", 
    "_CAPEITEM_FW_BRIDGEWATCH": "Bridgewatch Pelerini", "_CAPEITEM_FW_CAERLEON": "Caerleon Pelerini",
    # Kılıçlar
    "_MAIN_SWORD": "Tek El Kılıç", "_2H_SWORD": "Çift El Kılıç", "_2H_CLAYMORE": "Claymore", 
    "_2H_DUALSWORD": "Çifte Kılıç", "_MAIN_SCIMITAR_MORGANA": "Clarent Kılıcı", 
    "_2H_CLEAVER_HELL": "Carving Kılıcı", "_2H_DUALSCIMITAR_UNDEAD": "Galatine Pair", "_2H_CLAYMORE_AVALON": "Kingmaker",
    # Baltalar
    "_MAIN_AXE": "Savaş Baltası", "_2H_AXE": "Büyük Balta", "_2H_HALBERD": "Teber (Halberd)", 
    "_2H_SCYTHE_HELL": "Infernal Tırpan", "_2H_DUALAXE_KEEPER": "Ayı Pençesi (Bear Paws)", "_MAIN_AXE_AVALON": "Realmbreaker",
    # Gürzler ve Çekiçler
    "_MAIN_MACE": "Tek El Gürz", "_2H_MACE": "Ağır Gürz", "_2H_FLAIL": "Sabah Yıldızı", 
    "_MAIN_ROCKMACE_KEEPER": "Bedrock Gürzü", "_MAIN_HAMMER": "Çekiç", "_2H_HAMMER": "Büyük Çekiç", 
    "_2H_POLEHAMMER": "Sırıklı Çekiç", "_2H_RAM_KEEPER": "Grovekeeper",
    # Hançerler ve Mızraklar
    "_MAIN_DAGGER": "Tek El Hançer", "_2H_DAGGER": "Çifte Hançer", "_2H_CLAW": "Pençe (Claw)", 
    "_MAIN_DAGGER_HELL": "Kan Mektubu (Bloodletter)", "_2H_DAGGER_UNDEAD": "Deathgivers",
    "_MAIN_SPEAR": "Mızrak", "_2H_SPEAR": "Pike", "_2H_GLAIVE": "Glaive", "_2H_HARPOON_HELL": "Spirithunter",
    # Menzilli (Yay, Arbalet)
    "_2H_BOW": "Yay", "_2H_WARBOW": "Savaş Yayı", "_2H_LONGBOW": "Uzun Yay", "_2H_BOW_KEEPER": "Badon Yayı",
    "_MAIN_CROSSBOW": "Hafif Arbalet", "_2H_CROSSBOW": "Arbalet", "_2H_CROSSBOWLARGE": "Ağır Arbalet", 
    "_2H_DUALCROSSBOW_HELL": "Boltcasters", "_2H_REPEATINGCROSSBOW_UNDEAD": "Weeping Repeater",
    # Asalar (Büyü)
    "_MAIN_NATURESTAFF": "Doğa Asası", "_2H_NATURESTAFF": "Büyük Doğa Asası", "_2H_WILDSTAFF": "Vahşi Asa", 
    "_MAIN_FIRESTAFF": "Ateş Asası", "_2H_FIRESTAFF": "Büyük Ateş Asası", "_2H_INFERNOSTAFF": "Cehennem Asası", 
    "_MAIN_FROSTSTAFF": "Buz Asası", "_2H_FROSTSTAFF": "Büyük Buz Asası", "_2H_GLACIALSTAFF": "Buzul Asası", 
    "_MAIN_HOLYSTAFF": "Kutsal Asa", "_2H_HOLYSTAFF": "Büyük Kutsal Asa", "_2H_DIVINESTAFF": "İlahi Asa", 
    "_MAIN_CURSESTAFF": "Lanetli Asa", "_2H_DEMONICSTAFF": "İblis Asası",
    # İkinci El (Offhands)
    "_OFF_SHIELD": "Kalkan", "_OFF_TOWERSHIELD": "Kule Kalkanı", "_OFF_BOOK": "Büyü Kitabı", 
    "_OFF_ORB": "Küresi", "_OFF_TORCH": "Meşale", "_OFF_HORN": "Savaş Borusu",
    # Plaka Zırhlar
    "_HEAD_PLATE_SET1": "Asker Kaskı", "_ARMOR_PLATE_SET1": "Asker Zırhı", "_SHOES_PLATE_SET1": "Asker Çizmesi",
    "_HEAD_PLATE_SET2": "Şövalye Kaskı", "_ARMOR_PLATE_SET2": "Şövalye Zırhı", "_SHOES_PLATE_SET2": "Şövalye Çizmesi",
    "_HEAD_PLATE_SET3": "Gardiyan Kaskı", "_ARMOR_PLATE_SET3": "Gardiyan Zırhı", "_SHOES_PLATE_SET3": "Gardiyan Çizmesi",
    # Deri Zırhlar
    "_HEAD_LEATHER_SET1": "Paralı Asker Başlığı", "_ARMOR_LEATHER_SET1": "Paralı Asker Ceketi", "_SHOES_LEATHER_SET1": "Paralı Asker Ayakkabısı",
    "_HEAD_LEATHER_SET2": "Avcı Başlığı", "_ARMOR_LEATHER_SET2": "Avcı Ceketi", "_SHOES_LEATHER_SET2": "Avcı Ayakkabısı",
    "_HEAD_LEATHER_SET3": "Suikastçı Başlığı", "_ARMOR_LEATHER_SET3": "Suikastçı Ceketi", "_SHOES_LEATHER_SET3": "Suikastçı Ayakkabısı",
    # Kumaş Zırhlar
    "_HEAD_CLOTH_SET1": "Bilgin Kukuletası", "_ARMOR_CLOTH_SET1": "Bilgin Cübbesi", "_SHOES_CLOTH_SET1": "Bilgin Sandaleti",
    "_HEAD_CLOTH_SET2": "Ruhban Kukuletası", "_ARMOR_CLOTH_SET2": "Ruhban Cübbesi", "_SHOES_CLOTH_SET2": "Ruhban Sandaleti",
    "_HEAD_CLOTH_SET3": "Büyücü Kukuletası", "_ARMOR_CLOTH_SET3": "Büyücü Cübbesi", "_SHOES_CLOTH_SET3": "Büyücü Sandaleti",
}

ITEM_NAMES_EN = {
    "_BAG": "Bag", "_CAPE": "Normal Cape", 
    "_CAPEITEM_FW_MARTLOCK": "Martlock Cape", "_CAPEITEM_FW_LYMHURST": "Lymhurst Cape", 
    "_CAPEITEM_FW_THETFORD": "Thetford Cape", "_CAPEITEM_FW_FORTSTERLING": "Fort Sterling Cape", 
    "_CAPEITEM_FW_BRIDGEWATCH": "Bridgewatch Cape", "_CAPEITEM_FW_CAERLEON": "Caerleon Cape",
    "_MAIN_SWORD": "Broadsword", "_2H_SWORD": "2H Sword", "_2H_CLAYMORE": "Claymore", 
    "_2H_DUALSWORD": "Dual Swords", "_MAIN_SCIMITAR_MORGANA": "Clarent Blade", 
    "_2H_CLEAVER_HELL": "Carving Sword", "_2H_DUALSCIMITAR_UNDEAD": "Galatine Pair", "_2H_CLAYMORE_AVALON": "Kingmaker",
    "_MAIN_AXE": "Battleaxe", "_2H_AXE": "Greataxe", "_2H_HALBERD": "Halberd", 
    "_2H_SCYTHE_HELL": "Infernal Scythe", "_2H_DUALAXE_KEEPER": "Bear Paws", "_MAIN_AXE_AVALON": "Realmbreaker",
    "_MAIN_MACE": "Mace", "_2H_MACE": "Heavy Mace", "_2H_FLAIL": "Morning Star", 
    "_MAIN_ROCKMACE_KEEPER": "Bedrock Mace", "_MAIN_HAMMER": "Hammer", "_2H_HAMMER": "Great Hammer", 
    "_2H_POLEHAMMER": "Polehammer", "_2H_RAM_KEEPER": "Grovekeeper",
    "_MAIN_DAGGER": "Dagger", "_2H_DAGGER": "Dual Daggers", "_2H_CLAW": "Claws", 
    "_MAIN_DAGGER_HELL": "Bloodletter", "_2H_DAGGER_UNDEAD": "Deathgivers",
    "_MAIN_SPEAR": "Spear", "_2H_SPEAR": "Pike", "_2H_GLAIVE": "Glaive", "_2H_HARPOON_HELL": "Spirithunter",
    "_2H_BOW": "Bow", "_2H_WARBOW": "Warbow", "_2H_LONGBOW": "Longbow", "_2H_BOW_KEEPER": "Bow of Badon",
    "_MAIN_CROSSBOW": "Light Crossbow", "_2H_CROSSBOW": "Crossbow", "_2H_CROSSBOWLARGE": "Heavy Crossbow", 
    "_2H_DUALCROSSBOW_HELL": "Boltcasters", "_2H_REPEATINGCROSSBOW_UNDEAD": "Weeping Repeater",
    "_MAIN_NATURESTAFF": "Nature Staff", "_2H_NATURESTAFF": "Great Nature Staff", "_2H_WILDSTAFF": "Wild Staff", 
    "_MAIN_FIRESTAFF": "Fire Staff", "_2H_FIRESTAFF": "Great Fire Staff", "_2H_INFERNOSTAFF": "Infernal Staff", 
    "_MAIN_FROSTSTAFF": "Frost Staff", "_2H_FROSTSTAFF": "Great Frost Staff", "_2H_GLACIALSTAFF": "Glacial Staff", 
    "_MAIN_HOLYSTAFF": "Holy Staff", "_2H_HOLYSTAFF": "Great Holy Staff", "_2H_DIVINESTAFF": "Divine Staff", 
    "_MAIN_CURSESTAFF": "Cursed Staff", "_2H_DEMONICSTAFF": "Demonic Staff",
    "_OFF_SHIELD": "Shield", "_OFF_TOWERSHIELD": "Tower Shield", "_OFF_BOOK": "Spellbook", 
    "_OFF_ORB": "Eye of Secrets", "_OFF_TORCH": "Torch", "_OFF_HORN": "Mistcaller",
    "_HEAD_PLATE_SET1": "Soldier Helmet", "_ARMOR_PLATE_SET1": "Soldier Armor", "_SHOES_PLATE_SET1": "Soldier Boots",
    "_HEAD_PLATE_SET2": "Knight Helmet", "_ARMOR_PLATE_SET2": "Knight Armor", "_SHOES_PLATE_SET2": "Knight Boots",
    "_HEAD_PLATE_SET3": "Guardian Helmet", "_ARMOR_PLATE_SET3": "Guardian Armor", "_SHOES_PLATE_SET3": "Guardian Boots",
    "_HEAD_LEATHER_SET1": "Mercenary Hood", "_ARMOR_LEATHER_SET1": "Mercenary Jacket", "_SHOES_LEATHER_SET1": "Mercenary Shoes",
    "_HEAD_LEATHER_SET2": "Hunter Hood", "_ARMOR_LEATHER_SET2": "Hunter Jacket", "_SHOES_LEATHER_SET2": "Hunter Shoes",
    "_HEAD_LEATHER_SET3": "Assassin Hood", "_ARMOR_LEATHER_SET3": "Assassin Jacket", "_SHOES_LEATHER_SET3": "Assassin Shoes",
    "_HEAD_CLOTH_SET1": "Scholar Cowl", "_ARMOR_CLOTH_SET1": "Scholar Robe", "_SHOES_CLOTH_SET1": "Scholar Sandals",
    "_HEAD_CLOTH_SET2": "Cleric Cowl", "_ARMOR_CLOTH_SET2": "Cleric Robe", "_SHOES_CLOTH_SET2": "Cleric Sandals",
    "_HEAD_CLOTH_SET3": "Mage Cowl", "_ARMOR_CLOTH_SET3": "Mage Robe", "_SHOES_CLOTH_SET3": "Mage Sandals"
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

# BU TİK İŞARETLENDİĞİNDE SUNUCULAR YANAR
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
            if response.status == 200:
                return await response.json()
    except:
        pass
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

# --- TETİKLEME ---
col1, col2 = st.columns([8, 2])
with col2:
    if st.button("🚀 ASYNC ENLİL'İ BAŞLAT" if is_tr else "🚀 INITIATE ASYNC ENLIL", use_container_width=True): 
        st.cache_data.clear()

if not items_list or not selected_cities: st.stop()

with st.spinner(f"🔥 {len(items_list)} Eşya Asenkron Hızda Taranıyor (Bu biraz sürebilir)..." if is_tr else f"🔥 Async Scanning {len(items_list)} items..."):
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
else:
    final_df = pd.DataFrame()

# --- DASHBOARD METRİKLERİ ---
st.markdown("---")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Taranan Eşya" if is_tr else "Items Scanned", f"{len(items_list):,}")
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
