import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone

# --- DİL SÖZLÜKLERİ VE ÇEVİRİLER ---
st.set_page_config(page_title="Albion BM Arbitraj Pro", layout="wide", initial_sidebar_state="expanded")

# Dil seçimi için sol üstte ufak bir buton
lang = st.sidebar.radio("🌐 Language / Dil", ("Türkçe", "English"))
is_tr = (lang == "Türkçe")

UI = {
    "title": "🗡️ Albion Black Market Arbitraj Radarı" if is_tr else "🗡️ Albion Black Market Arbitrage Radar",
    "settings": "⚙️ Genel Ayarlar" if is_tr else "⚙️ General Settings",
    "max_age": "Maks. Veri Gecikmesi (Dk)" if is_tr else "Max Data Age (Mins)",
    "min_profit": "Minimum Net Kâr (Gümüş)" if is_tr else "Minimum Net Profit (Silver)",
    "tax": "Pazar Vergisi (%)" if is_tr else "Market Tax (%)",
    "cities": "🗺️ Alım Şehirleri" if is_tr else "🗺️ Buy Cities",
    "cities_desc": "Hangi şehirlerdeki fiyatlara bakılsın?" if is_tr else "Which cities to scan for buying?",
    "items": "📦 Eşya Taraması" if is_tr else "📦 Item Scanner",
    "mode_auto": "Kategori ve Seviye Seç (Otomatik)" if is_tr else "Select Category & Tier (Auto)",
    "mode_manual": "Manuel ID Gir (Gelişmiş)" if is_tr else "Enter Manual IDs (Advanced)",
    "cats": "Kategoriler:" if is_tr else "Categories:",
    "tiers": "Seviyeler (Tier):" if is_tr else "Tiers:",
    "enchants": "Büyü (Enchant):" if is_tr else "Enchantments:",
    "quals": "Kalite:" if is_tr else "Quality:",
    "refresh": "🔄 Verileri Şimdi Yenile" if is_tr else "🔄 Refresh Data Now",
    "scanning": "Pazar derinliği taranıyor..." if is_tr else "Scanning market depth...",
    "found": "🔥 Karlı Rota Bulundu! Toplam {} fırsat listeleniyor." if is_tr else "🔥 Profitable Route Found! {} opportunities listed.",
    "not_found": "Mevcut filtrelerine uygun kârlı bir sonuç bulunamadı!" if is_tr else "No profitable results found for the current filters!"
}

# Eşya isimleri için çeviri haritası
ITEM_NAMES_TR = {
    "_BAG": "Çanta", "_CAPE": "Pelerin", "_MAIN_SWORD": "Kılıç", "_MAIN_AXE": "Balta",
    "_MAIN_MACE": "Gürz", "_MAIN_HAMMER": "Çekiç", "_2H_BOW": "Yay", "_2H_CROSSBOW": "Arbalet",
    "_MAIN_NATURESTAFF": "Doğa Asası", "_MAIN_FIRESTAFF": "Ateş Asası", "_ARMOR_PLATE_SET1": "Plaka Zırh",
    "_ARMOR_LEATHER_SET1": "Deri Ceket", "_ARMOR_CLOTH_SET1": "Kumaş Cübbe", "_HEAD_PLATE_SET1": "Plaka Kask",
    "_HEAD_LEATHER_SET1": "Deri Başlık", "_HEAD_CLOTH_SET1": "Kumaş Kukuleta", "_SHOES_PLATE_SET1": "Plaka Çizme",
    "_SHOES_LEATHER_SET1": "Deri Ayakkabı", "_SHOES_CLOTH_SET1": "Kumaş Sandalet"
}
ITEM_NAMES_EN = {
    "_BAG": "Bag", "_CAPE": "Cape", "_MAIN_SWORD": "Sword", "_MAIN_AXE": "Axe",
    "_MAIN_MACE": "Mace", "_MAIN_HAMMER": "Hammer", "_2H_BOW": "Bow", "_2H_CROSSBOW": "Crossbow",
    "_MAIN_NATURESTAFF": "Nature Staff", "_MAIN_FIRESTAFF": "Fire Staff", "_ARMOR_PLATE_SET1": "Plate Armor",
    "_ARMOR_LEATHER_SET1": "Leather Jacket", "_ARMOR_CLOTH_SET1": "Cloth Robe", "_HEAD_PLATE_SET1": "Plate Helmet",
    "_HEAD_LEATHER_SET1": "Leather Hood", "_HEAD_CLOTH_SET1": "Cloth Cowl", "_SHOES_PLATE_SET1": "Plate Boots",
    "_SHOES_LEATHER_SET1": "Leather Shoes", "_SHOES_CLOTH_SET1": "Cloth Sandals"
}

st.title(UI["title"])

# --- SOL PANEL ---
st.sidebar.markdown("---")
st.sidebar.header(UI["settings"])
max_data_age = st.sidebar.slider(UI["max_age"], 5, 300, 60, 5)
min_profit = st.sidebar.number_input(UI["min_profit"], min_value=0, value=5000, step=1000)
tax_rate = st.sidebar.slider(UI["tax"], 0.0, 10.0, 4.0, 0.1) 

st.sidebar.markdown("---")
st.sidebar.header(UI["cities"])
ALL_LOCATIONS = ["Lymhurst", "Bridgewatch", "Martlock", "Thetford", "Fort Sterling"]
selected_cities = st.sidebar.multiselect(UI["cities_desc"], ALL_LOCATIONS, default=ALL_LOCATIONS)
locations_param = "Black Market," + ",".join(selected_cities)

st.sidebar.markdown("---")
st.sidebar.header(UI["items"])
search_mode = st.sidebar.radio(UI["search_mode"], (UI["mode_auto"], UI["mode_manual"]))

items_list = []
QUALITIES = {"Normal": 1, "Good": 2, "Outstanding": 3, "Excellent": 4, "Masterpiece": 5}

if search_mode == UI["mode_auto"]:
    selected_categories = st.sidebar.multiselect(UI["cats"], list(ITEM_NAMES_TR.keys()), default=["_BAG", "_MAIN_SWORD"], format_func=lambda x: ITEM_NAMES_TR[x] if is_tr else ITEM_NAMES_EN[x])
    selected_tiers = st.sidebar.multiselect(UI["tiers"], ["T4", "T5", "T6", "T7", "T8"], default=["T4", "T5"])
    selected_enchants = st.sidebar.multiselect(UI["enchants"], ["Düz (.0)", ".1", ".2", ".3", ".4"], default=["Düz (.0)", ".1"])
    selected_qualities_names = st.sidebar.multiselect(UI["quals"], list(QUALITIES.keys()), default=["Normal", "Good"])
    selected_qualities = [QUALITIES[q] for q in selected_qualities_names]
    
    for prefix in selected_categories:
        for tier in selected_tiers:
            for enc in selected_enchants:
                suffix = "" if enc == "Düz (.0)" else f"@{enc.replace('.', '')}"
                items_list.append(f"{tier}{prefix}{suffix}")
else:
    manual_input = st.sidebar.text_area("ID (e.g. T4_BAG,T4_BAG@1):", "T4_BAG,T4_BAG@1", height=150)
    items_list = [i.strip().upper() for i in manual_input.split(",") if i.strip()]
    selected_qualities = [1, 2, 3, 4, 5]

BASE_URL = "https://www.albion-online-data.com/api/v2/stats/Prices"

# --- YARDIMCI FONKSİYONLAR ---
def fetch_data_in_chunks(items, locs):
    chunk_size, all_data = 100, []
    for i in range(0, len(items), chunk_size):
        try:
            r = requests.get(f"{BASE_URL}/{','.join(items[i:i + chunk_size])}?locations={locs}", timeout=15)
            if r.status_code == 200: all_data.extend(r.json())
        except: pass
    return all_data

def calc_age(date_str):
    if not date_str or date_str.startswith("0001"): return 999999
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        return int((datetime.now(timezone.utc) - dt).total_seconds() / 60)
    except: return 999999

# Çirkin ID'yi oyun içi isme çeviren sihirli fonksiyon
def format_item_name(item_id):
    tier_part = item_id[:2]
    tier_str = tier_part.replace("T", "Seviye ") if is_tr else tier_part.replace("T", "Tier ")
    
    enchant = ""
    base_id = item_id[2:]
    if "@" in item_id:
        parts = item_id.split("@")
        base_id = parts[0][2:]
        enchant = f" .{parts[1]}"
    
    name_dict = ITEM_NAMES_TR if is_tr else ITEM_NAMES_EN
    item_name = name_dict.get(base_id, base_id)
    return f"{tier_str} {item_name}{enchant}"

# --- ANA İŞLEM ---
col1, col2 = st.columns([8, 2])
with col2:
    if st.button(UI["refresh"], use_container_width=True): st.cache_data.clear()

if not items_list or not selected_cities: st.stop()

with st.spinner(UI["scanning"]):
    raw_data = fetch_data_in_chunks(items_list, locations_param)

if not raw_data: st.stop()
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

# --- EKRANA BASTIRMA ---
if not final_df.empty:
    st.success(UI["found"].format(len(final_df)))
    
    display_df = final_df.copy()
    # ID'leri okunabilir isimlere çevir
    display_df['item_id'] = display_df['item_id'].apply(format_item_name)
    
    display_df['net_profit'] = display_df['net_profit'].astype(int).apply(lambda x: f"{x:,} 🥈")
    display_df['sell_price_min'] = display_df['sell_price_min'].astype(int).apply(lambda x: f"{x:,} 🥈")
    display_df['bm_buy_price'] = display_df['bm_buy_price'].astype(int).apply(lambda x: f"{x:,} 🥈")
    display_df['roi_percent'] = display_df['roi_percent'].round(2)
    display_df['age_str'] = display_df['sell_age'].astype(str) + " / " + display_df['bm_age'].astype(str) + (" dk" if is_tr else " min")
    
    display_df = display_df[['item_id', 'quality', 'city', 'sell_price_min', 'bm_buy_price', 'net_profit', 'roi_percent', 'age_str']]
    
    if is_tr:
        display_df.columns = ['Eşya İsimleri', 'Kalite', 'Satın Alınacak Şehir', 'Şehir Fiyatı', 'BM Alış Fiyatı', 'Net Kâr', 'Kâr Oranı (ROI) %', 'Gecikme (Şehir / BM)']
    else:
        display_df.columns = ['Item Name', 'Quality', 'Buy City', 'City Price', 'BM Buy Price', 'Net Profit', 'ROI %', 'Age (City / BM)']

    st.dataframe(display_df, use_container_width=True, hide_index=True, column_config={display_df.columns[6]: st.column_config.NumberColumn(format="%.2f%%")})
else:
    st.warning(UI["not_found"])
