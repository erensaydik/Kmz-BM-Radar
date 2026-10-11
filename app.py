import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Albion BM Arbitraj Pro", layout="wide", initial_sidebar_state="expanded")
st.title("🗡️ Albion Black Market Arbitraj Radarı - Final Sürüm")

# --- KATEGORİ SÖZLÜĞÜ (Otomatik ID Üretimi İçin) ---
# Albion veri yapısına uygun temel ön ekler
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

# --- SOL PANEL (AYARLAR VE FİLTRELER) ---
st.sidebar.header("⚙️ Genel Ayarlar")
max_data_age = st.sidebar.slider("Maks. Veri Gecikmesi (Dk)", min_value=5, max_value=300, value=60, step=5, help="Verinin tazeliği. Düşük = güvenli, Yüksek = daha çok sonuç.")
min_profit = st.sidebar.number_input("Minimum Net Kâr (Gümüş)", min_value=0, value=5000, step=1000)
tax_rate = st.sidebar.slider("Pazar Vergisi (%)", min_value=0.0, max_value=10.0, value=4.0, step=0.1) 

st.sidebar.markdown("---")
st.sidebar.header("📦 Eşya Taraması")

# Arama Modu Seçimi
search_mode = st.sidebar.radio(
    "Nasıl arama yapmak istersin?",
    ("Kategori ve Seviye Seç (Otomatik)", "Manuel ID Gir (Gelişmiş)")
)

items_to_scan = ""

if search_mode == "Kategori ve Seviye Seç (Otomatik)":
    st.sidebar.markdown("*(ID bilmene gerek yok, otomatik oluşturulur)*")
    
    # Çoklu Kategori Seçimi
    selected_categories = st.sidebar.multiselect(
        "Kategoriler (Birden fazla seçebilirsin):",
        options=list(CATEGORY_PREFIXES.keys()),
        default=["Çantalar (Bags)", "Kılıçlar (Swords)"]
    )
    
    # Seviye (Tier) Seçimi
    selected_tiers = st.sidebar.multiselect(
        "Seviyeler (Tier):",
        options=["T4", "T5", "T6", "T7", "T8"],
        default=["T4", "T5"]
    )
    
    # Seçimlere göre ID'leri otomatik üret
    auto_ids = []
    for cat in selected_categories:
        prefix = CATEGORY_PREFIXES[cat]
        for tier in selected_tiers:
            auto_ids.append(f"{tier}{prefix}")
            # Opsiyonel: Büyülü (Enchanted) eşyaları da eklemek istersen buraları açabilirsin
            # auto_ids.append(f"{tier}{prefix}@1") 
            # auto_ids.append(f"{tier}{prefix}@2")
    
    items_to_scan = ",".join(auto_ids)
    
    # Üretilen ID'leri küçük bir not olarak göster
    if items_to_scan:
        st.sidebar.caption(f"Arka planda taranacak ID'ler: {items_to_scan[:50]}...")

else:
    # Eski Manuel Yöntem
    items_to_scan = st.sidebar.text_area(
        "Eşya ID'lerini virgülle ayırarak gir:", 
        "T4_BAG,T5_BAG,T4_2H_SCYTHE_HELL",
        height=150
    )


LOCATIONS = "Black Market,Lymhurst,Bridgewatch,Martlock,Thetford,Fort Sterling"
BASE_URL = "https://www.albion-online-data.com/api/v2/stats/Prices"

# --- YARDIMCI FONKSİYONLAR ---
@st.cache_data(ttl=30, show_spinner=False)
def fetch_data(items_str):
    url = f"{BASE_URL}/{items_str}?locations={LOCATIONS}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

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

clean_items = ",".join([i.strip().upper() for i in items_to_scan.split(",") if i.strip()])

if not clean_items:
    st.info("👈 Lütfen sol menüden taranacak kategorileri ve seviyeleri seçin.")
    st.stop()

with st.spinner("Pazar derinliği taranıyor..."):
    raw_data = fetch_data(clean_items)

# Hata Kontrolleri
if isinstance(raw_data, dict) and "error" in raw_data:
    st.error(f"Albion API'sine ulaşılamadı. Sunucu yanıtı: {raw_data['error']}")
    st.stop()
elif not raw_data:
    st.warning("Girdiğin kriterler için API'de hiç veri yok. Farklı kategori veya seviyeler seçmeyi dene.")
    st.stop()

# Veri İşleme
df = pd.DataFrame(raw_data)
if 'city' not in df.columns:
    st.warning("Beklenmeyen veri formatı geldi. Tekrar yenilemeyi dene.")
    st.stop()

df['sell_age'] = df['sell_price_min_date'].apply(calc_age)
df['buy_age'] = df['buy_price_max_date'].apply(calc_age)

bm_df = df[df['city'] == 'Black Market'][['item_id', 'quality', 'buy_price_max', 'buy_age']]
bm_df.rename(columns={'buy_price_max': 'bm_buy_price', 'buy_age': 'bm_age'}, inplace=True)
other_df = df[df['city'] != 'Black Market'][['item_id', 'city', 'quality', 'sell_price_min', 'sell_age']]

merged = pd.merge(other_df, bm_df, on=['item_id', 'quality'])

# Filtreleme Analizi İçin Sayaçlar
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
    st.success(f"🔥 Karlı Rota Bulundu! Toplam {profit_passed} fırsat listeleniyor.")
    
    display_df = final_df.copy()
    display_df['net_profit'] = display_df['net_profit'].astype(int).apply(lambda x: f"{x:,} 🥈")
    display_df['sell_price_min'] = display_df['sell_price_min'].astype(int).apply(lambda x: f"{x:,} 🥈")
    display_df['bm_buy_price'] = display_df['bm_buy_price'].astype(int).apply(lambda x: f"{x:,} 🥈")
    display_df['roi_percent'] = display_df['roi_percent'].round(2).astype(str) + "%"
    display_df['Gecikme (Şehir / BM)'] = display_df['sell_age'].astype(str) + " dk / " + display_df['bm_age'].astype(str) + " dk"
    
    display_df = display_df[['item_id', 'quality', 'city', 'sell_price_min', 'bm_buy_price', 'net_profit', 'roi_percent', 'Gecikme (Şehir / BM)']]
    display_df.columns = ['Eşya', 'Kalite', 'Satış Şehri', 'Şehir Fiyatı', 'BM Alış', 'Net Kâr', 'Kâr Oranı (ROI)', 'Gecikme (Şehir / BM)']

    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.warning("Mevcut filtrelerine uygun kârlı bir sonuç bulunamadı!")

# --- VERİ ANALİZ PANELİ ---
with st.expander("📊 Neden tablo boş veya az eşya çıkıyor? (Arka Plan Analizi)"):
    st.write(f"- 🧩 Seçtiğin kriterlerde API'den dönen toplam eşleşme: **{total_pairs}**")
    st.write(f"- 💰 Fiyatı '0' olmayan geçerli pazar verileri: **{valid_prices}**")
    st.write(f"- ⏳ Son **{max_data_age} dakika** içinde güncellenmiş (taze) veriler: **{age_passed}**")
    st.write(f"- 📈 Senin belirlediğin minimum **{min_profit:,} gümüş** kâr hedefini geçenler: **{profit_passed}**")
    
    if profit_passed == 0 and age_passed > 0:
        st.info("💡 **İPUCU:** Güncel veriler var ancak hiçbiri belirlediğin kâr marjına ulaşamıyor. Minimum kârı düşürürsen fırsatları görebilirsin.")
