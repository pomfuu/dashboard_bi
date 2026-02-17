# =============================================================================
# POWER BI PYTHON SCRIPT - Dashboard Keluhan Konsumen
# =============================================================================
# Cara pakai di Power BI Desktop:
#   1. Home → Get Data → Python script → paste script ini
#   2. Atau: Transform Data → Add Column → Python Script
#
# Dataset yang dihasilkan siap langsung dipakai sebagai:
#   - Stacked Bar Chart (Story 1 & 3)
#   - 100% Stacked Bar Chart (Story 2)
#   - KPI Card
# =============================================================================

import pandas as pd

# -----------------------------------------------------------------------------
# GANTI PATH INI dengan lokasi file CSV di komputer Anda
# Atau ganti dengan URL jika data di cloud
# -----------------------------------------------------------------------------
DATA_PATH = r"C:\dashboard_bi\consumer_complaints.csv"

df = pd.read_csv(DATA_PATH, low_memory=False)
df.columns = df.columns.str.lower().str.strip()

# Konversi tanggal
df['date_received']        = pd.to_datetime(df['date_received'],        errors='coerce')
df['date_sent_to_company'] = pd.to_datetime(df['date_sent_to_company'], errors='coerce')

# Tambah kolom waktu
df['tahun']           = df['date_received'].dt.year
df['bulan']           = df['date_received'].dt.month
df['kuartal']         = df['date_received'].dt.quarter
df['waktu_respons_hari'] = (df['date_sent_to_company'] - df['date_received']).dt.days


# =============================================================================
# TABLE 1: dispute_per_produk
# → Untuk Stacked Bar Chart "Produk Mana yang Paling Berbahaya?"
# Kolom: product | total | disputed | not_disputed | dispute_pct | risk_label
# =============================================================================
dispute_per_produk = (
    df.groupby('product')
    .agg(
        total            = ('complaint_id', 'count'),
        disputed         = ('consumer_disputed_is', lambda x: (x == 'Yes').sum()),
    )
    .reset_index()
)
dispute_per_produk['not_disputed']  = dispute_per_produk['total'] - dispute_per_produk['disputed']
dispute_per_produk['dispute_pct']   = (dispute_per_produk['disputed'] / dispute_per_produk['total'] * 100).round(1)

# Label risiko — threshold berdasarkan rata-rata industri (20.2%)
dispute_per_produk['risk_label'] = dispute_per_produk['dispute_pct'].apply(
    lambda x: 'KRITIS'   if x >= 22 else   # ≥ 22% = di atas rata-rata + 2pp
              'WASPADA'  if x >= 15 else   # 15–21.9% = mendekati/sekitar rata-rata
              'AMAN'                        # < 15% = di bawah rata-rata
)

# Sumber kolom consumer_disputed_is:
# - "Yes"  → konsumen secara resmi mengajukan sengketa setelah perusahaan merespons
# - "No"   → konsumen menerima respons perusahaan tanpa lanjut sengketa
# Overall dispute rate dataset ini: 20.2% (112,134 dari 555,957 keluhan)


# =============================================================================
# TABLE 2: respons_per_perusahaan
# → Untuk 100% Stacked Bar "Siapa yang Benar-Benar Menyelesaikan Masalah?"
# Kolom: company | company_response_to_consumer | count | pct
# =============================================================================
top10_companies = df['company'].value_counts().head(10).index.tolist()

respons_per_perusahaan = (
    df[df['company'].isin(top10_companies)]
    .groupby(['company', 'company_response_to_consumer'])
    .size()
    .reset_index(name='count')
)

total_per_company = respons_per_perusahaan.groupby('company')['count'].transform('sum')
respons_per_perusahaan['pct'] = (respons_per_perusahaan['count'] / total_per_company * 100).round(1)

# Kategori respons (untuk urutan & warna di Power BI):
response_order = {
    'Closed with monetary relief':     1,  # ← kompensasi finansial, terbaik bagi konsumen
    'Closed with non-monetary relief': 2,  # ← solusi non-uang (kredit, koreksi, dll)
    'Closed with explanation':         3,  # ← hanya penjelasan, tanpa solusi nyata
    'Closed without relief':           4,  # ← ditutup tanpa solusi apapun
    'In progress':                     5,  # ← belum selesai
    'Untimely response':               6,  # ← respons terlambat, terburuk
}
respons_per_perusahaan['response_order'] = (
    respons_per_perusahaan['company_response_to_consumer']
    .map(response_order)
    .fillna(7)
)


# =============================================================================
# TABLE 3: tren_produk_tahunan
# → Untuk Stacked Bar per Tahun "Apakah Masalah Makin Parah?"
# Kolom: tahun | product | jumlah | dispute_rate_pct
# =============================================================================
top5_products = df['product'].value_counts().head(5).index.tolist()

tren_produk_tahunan = (
    df[df['product'].isin(top5_products)]
    .groupby(['tahun', 'product'])
    .agg(
        jumlah       = ('complaint_id', 'count'),
        disputed_cnt = ('consumer_disputed_is', lambda x: (x == 'Yes').sum()),
    )
    .reset_index()
)
tren_produk_tahunan['dispute_rate_pct'] = (
    tren_produk_tahunan['disputed_cnt'] / tren_produk_tahunan['jumlah'] * 100
).round(1)


# =============================================================================
# TABLE 4: kpi_summary
# → Untuk KPI Cards di Power BI
# =============================================================================
total_keluhan        = len(df)
total_disputed       = (df['consumer_disputed_is'] == 'Yes').sum()
overall_dispute_rate = (total_disputed / total_keluhan * 100).round(1)
timely_rate          = (df['timely_response'] == 'Yes').mean() * 100
avg_response_days    = df['waktu_respons_hari'].mean()

kpi_summary = pd.DataFrame({
    'metric': [
        'Total Keluhan',
        'Total Bersengketa',
        'Dispute Rate (%)',
        'Timely Response (%)',
        'Avg Response Days',
        'Total Perusahaan',
        'Total Produk',
    ],
    'value': [
        total_keluhan,
        total_disputed,
        overall_dispute_rate,
        round(timely_rate, 1),
        round(avg_response_days, 1),
        df['company'].nunique(),
        df['product'].nunique(),
    ]
})


# =============================================================================
# OUTPUT — Power BI membaca semua DataFrame yang ada di scope ini
# Setiap DataFrame menjadi satu tabel di Power BI
# =============================================================================

# dispute_per_produk      → tabel utama Story 1
# respons_per_perusahaan  → tabel utama Story 2
# tren_produk_tahunan     → tabel utama Story 3
# kpi_summary             → KPI Cards

print("Script berhasil dijalankan.")
print(f"  dispute_per_produk     : {len(dispute_per_produk)} baris")
print(f"  respons_per_perusahaan : {len(respons_per_perusahaan)} baris")
print(f"  tren_produk_tahunan    : {len(tren_produk_tahunan)} baris")
print(f"  kpi_summary            : {len(kpi_summary)} baris")
