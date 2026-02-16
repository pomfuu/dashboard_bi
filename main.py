import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard Keluhan Konsumen",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Kustom
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .insight-box {
        background-color: #f0f8ff;
        padding: 1rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
        border-radius: 0.3rem;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
        border-radius: 0.3rem;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
        border-radius: 0.3rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Cache data loading
@st.cache_data
def load_data():
    """Memuat dan memproses data keluhan konsumen"""
    # Coba load dari file lokal, jika tidak ada load dari URL
    try:
        # Untuk local development
        df = pd.read_csv('consumer_complaints.csv', low_memory=False)
    except FileNotFoundError:
        # Untuk Streamlit Cloud - ganti URL ini dengan link Google Drive/Dropbox Anda
        # Contoh: https://drive.google.com/uc?id=YOUR_FILE_ID&export=download
        data_url = st.secrets.get("DATA_URL", "")
        if data_url:
            st.info("📥 Memuat data dari cloud storage...")
            df = pd.read_csv(data_url, low_memory=False)
        else:
            st.error("❌ File data tidak ditemukan. Silakan upload 'consumer_complaints.csv' atau set DATA_URL di secrets.")
            st.stop()

    # Konversi kolom tanggal
    df['date_received'] = pd.to_datetime(df['date_received'], errors='coerce')
    df['date_sent_to_company'] = pd.to_datetime(df['date_sent_to_company'], errors='coerce')

    # Ekstrak fitur tanggal
    df['tahun'] = df['date_received'].dt.year
    df['bulan'] = df['date_received'].dt.month
    df['nama_bulan'] = df['date_received'].dt.strftime('%B')
    df['hari'] = df['date_received'].dt.day_name()
    df['kuartal'] = df['date_received'].dt.quarter

    # Hitung waktu respons
    df['waktu_respons_hari'] = (df['date_sent_to_company'] - df['date_received']).dt.days

    return df

# Muat data
with st.spinner('Memuat data...'):
    df = load_data()

# Header utama
st.markdown('<p class="main-header">📊 Dashboard Analisis Keluhan Konsumen</p>', unsafe_allow_html=True)
st.markdown("---")

# Filter di sidebar
st.sidebar.header("🎛️ Filter Data")

# Filter tahun
tahun_list = sorted(df['tahun'].dropna().unique())
tahun_terpilih = st.sidebar.multiselect(
    'Pilih Tahun',
    options=tahun_list,
    default=tahun_list[-3:] if len(tahun_list) >= 3 else tahun_list
)

# Filter produk
produk_list = sorted(df['product'].dropna().unique())
produk_terpilih = st.sidebar.multiselect(
    'Pilih Produk',
    options=produk_list,
    default=[]
)

# Terapkan filter
filtered_df = df.copy()
if tahun_terpilih:
    filtered_df = filtered_df[filtered_df['tahun'].isin(tahun_terpilih)]
if produk_terpilih:
    filtered_df = filtered_df[filtered_df['product'].isin(produk_terpilih)]

# Metrik Utama
st.header("📈 Metrik Utama")
col1, col2, col3, col4, col5 = st.columns(5)

total_keluhan = len(filtered_df)
tingkat_tepat_waktu = (filtered_df['timely_response'] == 'Yes').mean() * 100
tingkat_sengketa = (filtered_df['consumer_disputed_is'] == 'Yes').mean() * 100
rata_waktu_respons = filtered_df['waktu_respons_hari'].mean()
total_perusahaan = filtered_df['company'].nunique()

with col1:
    st.metric("Total Keluhan", f"{total_keluhan:,}")

with col2:
    st.metric("Respons Tepat Waktu", f"{tingkat_tepat_waktu:.1f}%")

with col3:
    st.metric("Tingkat Sengketa", f"{tingkat_sengketa:.1f}%")

with col4:
    st.metric("Rata-rata Waktu Respons", f"{rata_waktu_respons:.1f} hari")

with col5:
    st.metric("Total Perusahaan", f"{total_perusahaan:,}")

st.markdown("---")

# Tab untuk analisis berbeda
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Insight Utama",
    "📊 Analisis Tren",
    "🏢 Analisis Perusahaan",
    "📋 Pivot Tables",
    "💡 Rekomendasi Power BI"
])

with tab1:
    st.header("🔍 Insight Utama & Korelasi Multi-Dimensi")

    # KPI Section untuk single column analysis
    st.subheader("📊 KPI Utama (Single Column Analysis)")

    col1, col2, col3 = st.columns(3)

    produk_top = filtered_df['product'].value_counts()
    masalah_top = filtered_df['issue'].value_counts()
    state_top = filtered_df['state'].value_counts()

    with col1:
        st.markdown("**🏆 Top Produk Keluhan:**")
        st.metric(
            label=produk_top.index[0],
            value=f"{produk_top.values[0]:,} keluhan",
            delta=f"{(produk_top.values[0]/total_keluhan*100):.1f}% dari total"
        )
        st.markdown("**Top 5 Produk:**")
        for i in range(min(5, len(produk_top))):
            st.write(f"{i+1}. {produk_top.index[i]}: **{produk_top.values[i]:,}**")

    with col2:
        st.markdown("**⚠️ Top Masalah:**")
        st.metric(
            label=masalah_top.index[0],
            value=f"{masalah_top.values[0]:,} kasus",
            delta=f"{(masalah_top.values[0]/total_keluhan*100):.1f}% dari total"
        )
        st.markdown("**Top 5 Masalah:**")
        for i in range(min(5, len(masalah_top))):
            st.write(f"{i+1}. {masalah_top.index[i][:40]}...: **{masalah_top.values[i]:,}**")

    with col3:
        st.markdown("**🗺️ Top State:**")
        st.metric(
            label=state_top.index[0],
            value=f"{state_top.values[0]:,} keluhan",
            delta=f"{(state_top.values[0]/total_keluhan*100):.1f}% dari total"
        )
        st.markdown("**Top 5 States:**")
        for i in range(min(5, len(state_top))):
            st.write(f"{i+1}. {state_top.index[i]}: **{state_top.values[i]:,}**")

    st.markdown("---")

    # KORELASI 1: Produk vs Issue (2 kolom)
    st.subheader("1️⃣ Korelasi: Produk vs Jenis Masalah")

    top_5_products = produk_top.head(5).index
    top_8_issues = masalah_top.head(8).index

    produk_issue_data = filtered_df[
        filtered_df['product'].isin(top_5_products) &
        filtered_df['issue'].isin(top_8_issues)
    ].groupby(['product', 'issue']).size().reset_index(name='jumlah')

    fig1 = px.bar(
        produk_issue_data,
        x='product',
        y='jumlah',
        color='issue',
        title='Distribusi Masalah per Produk (Top 5 Produk vs Top 8 Masalah)',
        labels={'product': 'Produk', 'jumlah': 'Jumlah Keluhan', 'issue': 'Jenis Masalah'},
        barmode='stack',
        height=500
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("""
    <div class="insight-box">
    <b>💡 Insight Korelasi Produk-Masalah:</b><br>
    • Setiap produk memiliki pola masalah yang berbeda<br>
    • Identifikasi masalah dominan per produk untuk targeted solution<br>
    • Produk dengan masalah tersebar = perlu comprehensive improvement<br>
    • Produk dengan 1-2 masalah dominan = quick win opportunity
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # KORELASI 2: Channel vs Response (2 kolom)
    st.subheader("2️⃣ Korelasi: Channel vs Jenis Respons")

    channel_response_data = filtered_df.groupby(['submitted_via', 'company_response_to_consumer']).size().reset_index(name='jumlah')

    fig2 = px.bar(
        channel_response_data,
        x='submitted_via',
        y='jumlah',
        color='company_response_to_consumer',
        title='Jenis Respons per Channel Pengajuan',
        labels={'submitted_via': 'Channel', 'jumlah': 'Jumlah', 'company_response_to_consumer': 'Jenis Respons'},
        barmode='group',
        height=450
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    <div class="insight-box">
    <b>💡 Insight Korelasi Channel-Respons:</b><br>
    • Channel berbeda menghasilkan outcome yang berbeda<br>
    • Identifikasi channel paling efektif untuk "Closed with monetary relief"<br>
    • Web channel mungkin lebih terstruktur vs Phone yang lebih personal<br>
    • Gunakan untuk optimize channel strategy
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # KORELASI 3: State vs Produk (2 kolom)
    st.subheader("3️⃣ Korelasi: Geographic vs Produk")

    top_10_states = state_top.head(10).index
    top_6_products = produk_top.head(6).index

    state_product_data = filtered_df[
        filtered_df['state'].isin(top_10_states) &
        filtered_df['product'].isin(top_6_products)
    ].groupby(['state', 'product']).size().reset_index(name='jumlah')

    fig3 = px.bar(
        state_product_data,
        x='state',
        y='jumlah',
        color='product',
        title='Distribusi Produk per State (Top 10 States vs Top 6 Produk)',
        labels={'state': 'State', 'jumlah': 'Jumlah Keluhan', 'product': 'Produk'},
        barmode='stack',
        height=500
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("""
    <div class="insight-box">
    <b>💡 Insight Korelasi Geographic-Produk:</b><br>
    • Preferensi produk berbeda per region<br>
    • State tertentu mungkin punya masalah spesifik dengan produk tertentu<br>
    • Gunakan untuk regional marketing dan customer service strategy<br>
    • Alokasi specialist per region berdasarkan produk dominan
    </div>
    """, unsafe_allow_html=True)

with tab2:
    st.header("📊 Analisis Tren & Korelasi Temporal")

    # KPI Tren (single column)
    st.subheader("📈 KPI Tren Temporal")

    col1, col2, col3, col4 = st.columns(4)

    tren_tahunan = filtered_df.groupby('tahun').size()

    with col1:
        if len(tren_tahunan) > 1:
            yoy_growth = ((tren_tahunan.iloc[-1] - tren_tahunan.iloc[-2]) / tren_tahunan.iloc[-2]) * 100
            st.metric("Pertumbuhan YoY", f"{yoy_growth:+.1f}%",
                     delta=f"{'Naik' if yoy_growth > 0 else 'Turun'}")
        else:
            st.metric("Pertumbuhan YoY", "N/A")

    with col2:
        median_waktu = filtered_df['waktu_respons_hari'].median()
        st.metric("Median Waktu Respons", f"{median_waktu:.1f} hari",
                 delta=f"Target: <5 hari")

    with col3:
        respons_cepat = (filtered_df['waktu_respons_hari'] <= 3).sum()
        persen_cepat = (respons_cepat / total_keluhan * 100)
        st.metric("Respons Cepat (≤3 hari)", f"{persen_cepat:.1f}%",
                 delta=f"{respons_cepat:,} kasus")

    with col4:
        pola_bulanan = filtered_df.groupby('bulan').size()
        bulan_tertinggi_idx = pola_bulanan.idxmax()
        nama_bulan_dict = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'Mei', 6:'Jun',
                          7:'Jul', 8:'Agt', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Des'}
        st.metric("Bulan Puncak", nama_bulan_dict[int(bulan_tertinggi_idx)],
                 delta=f"{pola_bulanan.max():,} keluhan")

    st.markdown("---")

    # KORELASI 4: Tahun vs Produk (Multi-line chart)
    st.subheader("4️⃣ Korelasi: Tren Produk dari Waktu ke Waktu")

    top_5_products_trend = filtered_df['product'].value_counts().head(5).index

    tren_produk = filtered_df[filtered_df['product'].isin(top_5_products_trend)].groupby(['tahun', 'product']).size().reset_index(name='jumlah')

    fig_trend = px.line(
        tren_produk,
        x='tahun',
        y='jumlah',
        color='product',
        title='Evolusi Keluhan: Top 5 Produk per Tahun',
        labels={'tahun': 'Tahun', 'jumlah': 'Jumlah Keluhan', 'product': 'Produk'},
        markers=True,
        height=500
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("""
    <div class="insight-box">
    <b>💡 Insight Korelasi Temporal-Produk:</b><br>
    • Identifikasi produk dengan tren naik vs turun<br>
    • Produk dengan growth tajam perlu immediate action<br>
    • Produk dengan decline = success story, study best practices<br>
    • Gunakan untuk forecast dan resource planning per produk
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # KORELASI 5: Bulan vs Channel (Heatmap style)
    st.subheader("5️⃣ Korelasi: Pola Bulanan per Channel")

    bulan_channel = filtered_df.groupby(['bulan', 'submitted_via']).size().reset_index(name='jumlah')
    bulan_channel['nama_bulan'] = bulan_channel['bulan'].map({
        1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'Mei', 6:'Jun',
        7:'Jul', 8:'Agt', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Des'
    })

    fig_bulan_channel = px.bar(
        bulan_channel,
        x='nama_bulan',
        y='jumlah',
        color='submitted_via',
        title='Pola Channel Pengajuan per Bulan',
        labels={'nama_bulan': 'Bulan', 'jumlah': 'Jumlah Keluhan', 'submitted_via': 'Channel'},
        barmode='stack',
        height=450
    )
    st.plotly_chart(fig_bulan_channel, use_container_width=True)

    st.markdown("""
    <div class="insight-box">
    <b>💡 Insight Korelasi Temporal-Channel:</b><br>
    • Identifikasi seasonality per channel<br>
    • Web mungkin peak di bulan tertentu vs Phone di bulan lain<br>
    • Alokasi staffing per channel berdasarkan pola musiman<br>
    • Planning training dan resource berdasarkan forecast per channel
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # KORELASI 6: Waktu Respons vs Perusahaan (Box plot concept via bar)
    st.subheader("6️⃣ Korelasi: Waktu Respons per Perusahaan")

    top_10_companies_resp = filtered_df['company'].value_counts().head(10).index

    waktu_respons_company = filtered_df[
        (filtered_df['company'].isin(top_10_companies_resp)) &
        (filtered_df['waktu_respons_hari'].between(0, 30))
    ].groupby('company')['waktu_respons_hari'].agg(['mean', 'median']).reset_index()

    waktu_respons_company = waktu_respons_company.sort_values('mean', ascending=False)

    # Create grouped bar chart
    fig_waktu_comp = go.Figure()
    fig_waktu_comp.add_trace(go.Bar(
        x=waktu_respons_company['company'],
        y=waktu_respons_company['mean'],
        name='Rata-rata',
        marker_color='coral'
    ))
    fig_waktu_comp.add_trace(go.Bar(
        x=waktu_respons_company['company'],
        y=waktu_respons_company['median'],
        name='Median',
        marker_color='steelblue'
    ))

    fig_waktu_comp.update_layout(
        title='Perbandingan Waktu Respons: Rata-rata vs Median (Top 10 Perusahaan)',
        xaxis_title='Perusahaan',
        yaxis_title='Waktu Respons (hari)',
        barmode='group',
        height=500,
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig_waktu_comp, use_container_width=True)

    st.markdown("""
    <div class="insight-box">
    <b>💡 Insight Korelasi Waktu-Perusahaan:</b><br>
    • Gap besar antara mean & median = ada outliers (kasus ekstrem)<br>
    • Perusahaan dengan median rendah = konsisten cepat<br>
    • Perusahaan dengan mean tinggi tapi median rendah = ada kasus lambat yang perlu investigasi<br>
    • Target: mean & median keduanya <5 hari
    </div>
    """, unsafe_allow_html=True)

with tab3:
    st.header("🏢 Analisis Perusahaan")

    # INSIGHT 8: Perusahaan dengan Keluhan Terbanyak
    st.subheader("8️⃣ Perusahaan dengan Keluhan Terbanyak")

    perusahaan_top = filtered_df['company'].value_counts().head(15)

    fig10 = px.bar(
        x=perusahaan_top.values,
        y=perusahaan_top.index,
        orientation='h',
        title='Top 15 Perusahaan dengan Keluhan Terbanyak',
        labels={'x': 'Jumlah Keluhan', 'y': 'Perusahaan'}
    )
    fig10.update_traces(marker_color='crimson')
    fig10.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
    st.plotly_chart(fig10, use_container_width=True)

    perusahaan_teratas = perusahaan_top.index[0]
    keluhan_teratas = perusahaan_top.values[0]

    st.markdown(f"""
    <div class="warning-box">
    <b>⚠️ Insight Perusahaan:</b><br>
    • Perusahaan dengan keluhan terbanyak: <b>{perusahaan_teratas}</b> ({keluhan_teratas:,} keluhan)<br>
    • Ini mewakili <b>{(keluhan_teratas/total_keluhan*100):.1f}%</b> dari total keluhan<br>
    • Top 5 perusahaan menyumbang <b>{(perusahaan_top.head(5).sum()/total_keluhan*100):.1f}%</b> dari semua keluhan<br>
    • Perlu audit khusus untuk perusahaan-perusahaan ini
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # INSIGHT 9: Perbandingan Performa Perusahaan
    st.subheader("9️⃣ Perbandingan Performa Perusahaan")

    # Analisis top 10 perusahaan
    top_10_companies = perusahaan_top.head(10).index

    performa_perusahaan = filtered_df[filtered_df['company'].isin(top_10_companies)].groupby('company').agg({
        'timely_response': lambda x: (x == 'Yes').mean() * 100,
        'consumer_disputed_is': lambda x: (x == 'Yes').mean() * 100,
        'waktu_respons_hari': 'mean'
    }).reset_index()

    performa_perusahaan.columns = ['Perusahaan', 'Respons Tepat Waktu (%)', 'Tingkat Sengketa (%)', 'Rata-rata Waktu Respons (hari)']
    performa_perusahaan = performa_perusahaan.sort_values('Tingkat Sengketa (%)', ascending=False)

    # Tampilkan tabel
    st.dataframe(
        performa_perusahaan.style.background_gradient(subset=['Tingkat Sengketa (%)'], cmap='Reds')
                                 .background_gradient(subset=['Respons Tepat Waktu (%)'], cmap='Greens')
                                 .format({
                                     'Respons Tepat Waktu (%)': '{:.1f}%',
                                     'Tingkat Sengketa (%)': '{:.1f}%',
                                     'Rata-rata Waktu Respons (hari)': '{:.1f}'
                                 }),
        use_container_width=True
    )

    # Perusahaan terbaik dan terburuk
    perusahaan_terbaik = performa_perusahaan.loc[performa_perusahaan['Tingkat Sengketa (%)'].idxmin()]
    perusahaan_terburuk = performa_perusahaan.loc[performa_perusahaan['Tingkat Sengketa (%)'].idxmax()]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="success-box">
        <b>✅ Performa Terbaik:</b><br>
        <b>{perusahaan_terbaik['Perusahaan']}</b><br>
        • Tingkat Sengketa: {perusahaan_terbaik['Tingkat Sengketa (%)']:.1f}%<br>
        • Respons Tepat Waktu: {perusahaan_terbaik['Respons Tepat Waktu (%)']:.1f}%<br>
        • Waktu Respons: {perusahaan_terbaik['Rata-rata Waktu Respons (hari)']:.1f} hari
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="warning-box">
        <b>⚠️ Perlu Perbaikan:</b><br>
        <b>{perusahaan_terburuk['Perusahaan']}</b><br>
        • Tingkat Sengketa: {perusahaan_terburuk['Tingkat Sengketa (%)']:.1f}%<br>
        • Respons Tepat Waktu: {perusahaan_terburuk['Respons Tepat Waktu (%)']:.1f}%<br>
        • Waktu Respons: {perusahaan_terburuk['Rata-rata Waktu Respons (hari)']:.1f} hari
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # INSIGHT 10: Kombinasi Produk-Perusahaan
    st.subheader("🔟 Kombinasi Produk-Perusahaan Bermasalah")

    kombinasi = filtered_df.groupby(['product', 'company']).size().reset_index(name='jumlah')
    kombinasi_top = kombinasi.nlargest(15, 'jumlah')

    st.dataframe(
        kombinasi_top.style.background_gradient(subset=['jumlah'], cmap='OrRd')
                          .format({'jumlah': '{:,}'}),
        use_container_width=True
    )

    st.markdown(f"""
    <div class="insight-box">
    <b>💡 Insight Kombinasi:</b><br>
    • Kombinasi terburuk: <b>{kombinasi_top.iloc[0]['product']}</b> di <b>{kombinasi_top.iloc[0]['company']}</b><br>
    • Total keluhan kombinasi ini: <b>{kombinasi_top.iloc[0]['jumlah']:,}</b> kasus<br>
    • Perlu investigasi mendalam untuk kombinasi produk-perusahaan ini<br>
    • Focus group atau root cause analysis sangat direkomendasikan
    </div>
    """, unsafe_allow_html=True)

with tab4:
    st.header("📋 Analisis Pivot Tables")

    st.markdown("""
    Pivot table memberikan analisis multi-dimensi yang sangat berguna untuk melihat pola-pola tersembunyi dalam data.
    Setiap tabel di bawah dapat langsung di-copy ke Excel atau Power BI untuk analisis lebih lanjut.
    """)

    st.markdown("---")

    # PIVOT 1: Produk vs Tahun
    st.subheader("📊 Pivot 1: Tren Produk per Tahun")

    pivot_produk_tahun = pd.pivot_table(
        filtered_df,
        values='complaint_id',
        index='product',
        columns='tahun',
        aggfunc='count',
        fill_value=0,
        margins=True,
        margins_name='TOTAL'
    )

    # Ambil top 15 produk
    top_products = filtered_df['product'].value_counts().head(15).index
    pivot_produk_tahun_top = pivot_produk_tahun.loc[top_products]

    st.dataframe(
        pivot_produk_tahun_top.style.background_gradient(cmap='YlOrRd', axis=1)
                                    .format('{:,.0f}'),
        use_container_width=True,
        height=600
    )

    st.markdown("""
    <div class="insight-box">
    <b>💡 Insight Pivot 1:</b><br>
    • Tabel menunjukkan evolusi keluhan per produk dari tahun ke tahun<br>
    • Produk dengan pertumbuhan tinggi perlu investigasi mendalam<br>
    • Produk dengan tren menurun menunjukkan perbaikan kualitas<br>
    • Gunakan untuk forecast dan planning resource
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # PIVOT 2: State vs Produk
    st.subheader("🗺️ Pivot 2: Keluhan per State dan Produk")

    top_states = filtered_df['state'].value_counts().head(10).index
    top_products_state = filtered_df['product'].value_counts().head(8).index

    pivot_state_produk = pd.pivot_table(
        filtered_df[filtered_df['state'].isin(top_states) & filtered_df['product'].isin(top_products_state)],
        values='complaint_id',
        index='state',
        columns='product',
        aggfunc='count',
        fill_value=0,
        margins=True,
        margins_name='TOTAL'
    )

    st.dataframe(
        pivot_state_produk.style.background_gradient(cmap='Blues', axis=1)
                                .format('{:,.0f}'),
        use_container_width=True,
        height=500
    )

    st.markdown("""
    <div class="insight-box">
    <b>💡 Insight Pivot 2:</b><br>
    • Identifikasi kombinasi state-produk yang bermasalah<br>
    • Beberapa produk mungkin bermasalah di region tertentu saja<br>
    • Gunakan untuk strategi regional marketing dan customer service<br>
    • Alokasi resources berdasarkan hotspot geografis
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # PIVOT 3: Perusahaan vs Response Type
    st.subheader("🏢 Pivot 3: Jenis Respons per Perusahaan")

    top_companies_pivot = filtered_df['company'].value_counts().head(12).index

    pivot_company_response = pd.pivot_table(
        filtered_df[filtered_df['company'].isin(top_companies_pivot)],
        values='complaint_id',
        index='company',
        columns='company_response_to_consumer',
        aggfunc='count',
        fill_value=0,
        margins=True,
        margins_name='TOTAL'
    )

    st.dataframe(
        pivot_company_response.style.background_gradient(cmap='Greens', axis=1)
                                    .format('{:,.0f}'),
        use_container_width=True,
        height=500
    )

    st.markdown("""
    <div class="insight-box">
    <b>💡 Insight Pivot 3:</b><br>
    • Bandingkan bagaimana setiap perusahaan merespons keluhan<br>
    • Perusahaan dengan banyak "Closed with monetary relief" mungkin punya masalah sistemik<br>
    • "Closed with explanation" yang tinggi bisa menunjukkan komunikasi yang baik<br>
    • Gunakan untuk benchmark antar perusahaan
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # PIVOT 4: Issue vs Produk
    st.subheader("🔍 Pivot 4: Masalah per Jenis Produk")

    top_issues = filtered_df['issue'].value_counts().head(10).index
    top_products_issue = filtered_df['product'].value_counts().head(8).index

    pivot_issue_product = pd.pivot_table(
        filtered_df[filtered_df['issue'].isin(top_issues) & filtered_df['product'].isin(top_products_issue)],
        values='complaint_id',
        index='issue',
        columns='product',
        aggfunc='count',
        fill_value=0,
        margins=True,
        margins_name='TOTAL'
    )

    st.dataframe(
        pivot_issue_product.style.background_gradient(cmap='Reds', axis=1)
                                 .format('{:,.0f}'),
        use_container_width=True,
        height=500
    )

    st.markdown("""
    <div class="insight-box">
    <b>💡 Insight Pivot 4:</b><br>
    • Identifikasi masalah spesifik untuk setiap produk<br>
    • Produk tertentu mungkin punya masalah unik yang perlu solusi khusus<br>
    • Gunakan untuk product development dan quality improvement<br>
    • Prioritaskan perbaikan berdasarkan kombinasi issue-product tertinggi
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # PIVOT 5: Channel vs Timely Response
    st.subheader("📱 Pivot 5: Ketepatan Waktu Respons per Channel")

    pivot_channel_timely = pd.pivot_table(
        filtered_df,
        values='complaint_id',
        index='submitted_via',
        columns='timely_response',
        aggfunc='count',
        fill_value=0,
        margins=True,
        margins_name='TOTAL'
    )

    # Tambahkan persentase
    pivot_channel_timely['% Tepat Waktu'] = (
        pivot_channel_timely['Yes'] /
        (pivot_channel_timely['Yes'] + pivot_channel_timely['No']) * 100
    ).round(1)

    st.dataframe(
        pivot_channel_timely.style.background_gradient(subset=['Yes'], cmap='Greens')
                                  .background_gradient(subset=['No'], cmap='Reds')
                                  .background_gradient(subset=['% Tepat Waktu'], cmap='Blues')
                                  .format({'Yes': '{:,.0f}', 'No': '{:,.0f}', 'TOTAL': '{:,.0f}', '% Tepat Waktu': '{:.1f}%'}),
        use_container_width=True
    )

    st.markdown("""
    <div class="insight-box">
    <b>💡 Insight Pivot 5:</b><br>
    • Beberapa channel mungkin lebih efisien daripada yang lain<br>
    • Channel dengan % tepat waktu rendah perlu process improvement<br>
    • Alokasikan lebih banyak resource ke channel yang paling efisien<br>
    • Pertimbangkan automation untuk channel dengan volume tinggi
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # PIVOT 6: Kuartal vs Dispute Rate
    st.subheader("📅 Pivot 6: Tingkat Sengketa per Kuartal dan Tahun")

    pivot_kuartal_dispute = pd.pivot_table(
        filtered_df,
        values='complaint_id',
        index='kuartal',
        columns='tahun',
        aggfunc=lambda x: (filtered_df.loc[x.index, 'consumer_disputed_is'] == 'Yes').mean() * 100,
        fill_value=0
    )

    pivot_kuartal_dispute.index = ['Q' + str(int(x)) for x in pivot_kuartal_dispute.index]

    st.dataframe(
        pivot_kuartal_dispute.style.background_gradient(cmap='RdYlGn_r', axis=None)
                                   .format('{:.1f}%'),
        use_container_width=True
    )

    st.markdown("""
    <div class="insight-box">
    <b>💡 Insight Pivot 6:</b><br>
    • Identifikasi kuartal dengan tingkat sengketa tertinggi<br>
    • Pola musiman dalam kepuasan pelanggan<br>
    • Kuartal dengan performa buruk perlu analisis root cause<br>
    • Gunakan untuk perencanaan quality improvement program
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # PIVOT 7: Perusahaan vs Waktu Respons (Advanced)
    st.subheader("⏱️ Pivot 7: Statistik Waktu Respons per Perusahaan")

    top_companies_time = filtered_df['company'].value_counts().head(10).index

    pivot_company_time = filtered_df[filtered_df['company'].isin(top_companies_time)].groupby('company').agg({
        'waktu_respons_hari': ['mean', 'median', 'min', 'max', 'std'],
        'complaint_id': 'count'
    }).round(2)

    pivot_company_time.columns = ['Rata-rata (hari)', 'Median (hari)', 'Min (hari)', 'Max (hari)', 'Std Dev', 'Total Keluhan']
    pivot_company_time = pivot_company_time.sort_values('Rata-rata (hari)', ascending=False)

    st.dataframe(
        pivot_company_time.style.background_gradient(subset=['Rata-rata (hari)'], cmap='Reds')
                                .background_gradient(subset=['Total Keluhan'], cmap='Blues')
                                .format({
                                    'Rata-rata (hari)': '{:.1f}',
                                    'Median (hari)': '{:.1f}',
                                    'Min (hari)': '{:.0f}',
                                    'Max (hari)': '{:.0f}',
                                    'Std Dev': '{:.1f}',
                                    'Total Keluhan': '{:,.0f}'
                                }),
        use_container_width=True,
        height=450
    )

    st.markdown("""
    <div class="insight-box">
    <b>💡 Insight Pivot 7:</b><br>
    • Std Dev tinggi = inkonsistensi dalam waktu respons<br>
    • Perhatikan perusahaan dengan Max (hari) yang sangat tinggi<br>
    • Median lebih reliable daripada rata-rata untuk data dengan outliers<br>
    • Target: Rata-rata <5 hari, Std Dev <3 hari untuk konsistensi
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # PIVOT 8: Year-over-Year Comparison Matrix
    st.subheader("📈 Pivot 8: Perbandingan Year-over-Year (Top 10 Produk)")

    if len(tahun_terpilih) >= 2:
        top_10_products = filtered_df['product'].value_counts().head(10).index

        yoy_data = []
        for product in top_10_products:
            product_data = filtered_df[filtered_df['product'] == product].groupby('tahun').size()

            row_data = {'Produk': product}
            for tahun in sorted(tahun_terpilih):
                if tahun in product_data.index:
                    row_data[f'{int(tahun)}'] = int(product_data[tahun])
                else:
                    row_data[f'{int(tahun)}'] = 0

            # Hitung pertumbuhan
            tahun_sorted = sorted([int(t) for t in tahun_terpilih])
            if len(tahun_sorted) >= 2:
                nilai_awal = row_data.get(str(tahun_sorted[0]), 0)
                nilai_akhir = row_data.get(str(tahun_sorted[-1]), 0)

                if nilai_awal > 0:
                    pertumbuhan = ((nilai_akhir - nilai_awal) / nilai_awal) * 100
                    row_data['YoY Growth (%)'] = round(pertumbuhan, 1)
                else:
                    row_data['YoY Growth (%)'] = 0.0

            yoy_data.append(row_data)

        yoy_df = pd.DataFrame(yoy_data)
        yoy_df = yoy_df.set_index('Produk')

        st.dataframe(
            yoy_df.style.background_gradient(subset=[col for col in yoy_df.columns if col != 'YoY Growth (%)'], cmap='YlOrRd')
                        .background_gradient(subset=['YoY Growth (%)'], cmap='RdYlGn_r')
                        .format({col: '{:,.0f}' for col in yoy_df.columns if col != 'YoY Growth (%)'})
                        .format({'YoY Growth (%)': '{:+.1f}%'}),
            use_container_width=True,
            height=450
        )

        st.markdown("""
        <div class="insight-box">
        <b>💡 Insight Pivot 8:</b><br>
        • YoY Growth positif (merah) = keluhan meningkat, perlu perhatian<br>
        • YoY Growth negatif (hijau) = keluhan menurun, perbaikan berhasil<br>
        • Produk dengan growth >50% perlu urgent intervention<br>
        • Produk dengan decline >30% bisa dijadikan best practice
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Pilih minimal 2 tahun di filter untuk melihat analisis Year-over-Year")

    st.markdown("---")

    # Export Pivot Tables
    st.subheader("📥 Export Pivot Tables")

    st.markdown("""
    Semua pivot table di atas dapat di-export untuk analisis lebih lanjut di Excel atau Power BI.
    Gunakan fitur download di bawah untuk mendapatkan data dalam format CSV.
    """)

    col1, col2 = st.columns(2)

    with col1:
        # Export pivot produk-tahun
        csv_pivot1 = pivot_produk_tahun_top.to_csv().encode('utf-8')
        st.download_button(
            label="📊 Download Pivot Produk-Tahun",
            data=csv_pivot1,
            file_name=f'pivot_produk_tahun_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )

    with col2:
        # Export pivot company time
        csv_pivot7 = pivot_company_time.to_csv().encode('utf-8')
        st.download_button(
            label="⏱️ Download Pivot Waktu Respons",
            data=csv_pivot7,
            file_name=f'pivot_waktu_respons_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )

with tab5:
    st.header("💡 Rekomendasi untuk Power BI")

    st.markdown("""
    ## 📊 Panduan Implementasi Dashboard Power BI

    Berdasarkan analisis data keluhan konsumen, berikut adalah rekomendasi struktur dashboard Power BI:
    """)

    st.markdown("---")

    st.subheader("📌 Dashboard 1: Executive Summary")
    st.markdown("""
    **Tujuan:** Memberikan overview cepat untuk manajemen tingkat atas

    **Komponen:**
    1. **KPI Cards (4 kartu besar di atas)**
       - Total Keluhan
       - Tingkat Respons Tepat Waktu (target: >95%)
       - Tingkat Sengketa (target: <15%)
       - Rata-rata Waktu Respons (target: <5 hari)

    2. **Tren Line Chart**
       - Tren keluhan bulanan dengan forecast 3 bulan ke depan
       - Gunakan Power BI Analytics untuk menambahkan trend line

    3. **Top 5 Bar Charts (3 visualisasi)**
       - Top 5 Produk Bermasalah
       - Top 5 Perusahaan dengan Keluhan Terbanyak
       - Top 5 Jenis Masalah

    4. **Slicer/Filter:**
       - Tahun (dropdown)
       - Kuartal (dropdown)
       - Produk (multi-select)
    """)

    st.markdown("---")

    st.subheader("📌 Dashboard 2: Analisis Operasional")
    st.markdown("""
    **Tujuan:** Untuk tim operasional memantau performa harian

    **Komponen:**
    1. **Matriks Waktu Respons**
       - Heatmap: Hari vs Jam (kapan keluhan paling banyak masuk)
       - Gunakan conditional formatting

    2. **Funnel Chart**
       - Keluhan Masuk → Diproses → Diselesaikan → Sengketa
       - Identifikasi bottleneck

    3. **Tabel Detail Perusahaan**
       - Kolom: Perusahaan, Total Keluhan, % Tepat Waktu, % Sengketa, Avg Respons
       - Sort by worst performers
       - Conditional formatting untuk highlight masalah

    4. **Pie Chart Channel**
       - Distribusi channel pengajuan keluhan
       - Insight untuk alokasi resources
    """)

    st.markdown("---")

    st.subheader("📌 Dashboard 3: Analisis Geografis")
    st.markdown("""
    **Tujuan:** Memahami pola regional dan alokasi resources

    **Komponen:**
    1. **Filled Map / Shape Map**
       - Visualisasi keluhan per state
       - Color gradient berdasarkan volume keluhan

    2. **Bar Chart Horizontal**
       - Top 15 States dengan keluhan terbanyak
       - Drill-down capability ke city level (jika data tersedia)

    3. **Scatter Plot**
       - X-axis: Populasi State (jika data tersedia)
       - Y-axis: Jumlah Keluhan
       - Size: Tingkat Sengketa
       - Identifikasi outliers
    """)

    st.markdown("---")

    st.subheader("📌 Dashboard 4: Analisis Produk")
    st.markdown("""
    **Tujuan:** Deep dive ke performa produk

    **Komponen:**
    1. **Treemap**
       - Hierarki: Product → Sub-Product
       - Size: jumlah keluhan
       - Color: tingkat sengketa

    2. **Stacked Bar Chart**
       - Produk vs Jenis Masalah
       - Identifikasi masalah spesifik per produk

    3. **Line Chart Multi-Series**
       - Tren keluhan untuk top 5 produk
       - Identifikasi produk yang membaik/memburuk
    """)

    st.markdown("---")

    st.subheader("🎯 Measures & Calculations DAX yang Direkomendasikan")

    st.code("""
    // Total Keluhan
    Total Keluhan = COUNTROWS('Complaints')

    // Tingkat Respons Tepat Waktu
    Tingkat Respons Tepat Waktu =
    DIVIDE(
        CALCULATE(COUNTROWS('Complaints'), 'Complaints'[timely_response] = "Yes"),
        COUNTROWS('Complaints'),
        0
    ) * 100

    // Tingkat Sengketa
    Tingkat Sengketa =
    DIVIDE(
        CALCULATE(COUNTROWS('Complaints'), 'Complaints'[consumer_disputed] = "Yes"),
        COUNTROWS('Complaints'),
        0
    ) * 100

    // Rata-rata Waktu Respons
    Avg Waktu Respons = AVERAGE('Complaints'[waktu_respons_hari])

    // YoY Growth
    YoY Growth =
    VAR CurrentYear = CALCULATE([Total Keluhan])
    VAR PreviousYear = CALCULATE([Total Keluhan], DATEADD('Date'[Date], -1, YEAR))
    RETURN
    DIVIDE(CurrentYear - PreviousYear, PreviousYear, 0) * 100

    // Ranking Perusahaan
    Rank Perusahaan =
    RANKX(
        ALL('Complaints'[company]),
        [Total Keluhan],
        ,
        DESC,
        DENSE
    )

    // Status Indicator
    Status Respons =
    IF([Tingkat Respons Tepat Waktu] >= 95, "✅ Excellent",
        IF([Tingkat Respons Tepat Waktu] >= 85, "⚠️ Good",
            "❌ Needs Improvement"
        )
    )
    """, language="dax")

    st.markdown("---")

    st.subheader("🎨 Tips Desain Power BI")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Color Scheme:**
        - 🟢 Hijau: Performa baik, target tercapai
        - 🟡 Kuning: Warning, perlu perhatian
        - 🔴 Merah: Critical, urgent action
        - 🔵 Biru: Informasi netral, KPI utama

        **Font & Layout:**
        - Gunakan font Segoe UI (native Power BI)
        - Ukuran title: 16-18pt
        - Ukuran label: 10-12pt
        - White space yang cukup antar visual
        """)

    with col2:
        st.markdown("""
        **Best Practices:**
        - Maksimal 6-8 visualisasi per halaman
        - Gunakan bookmarks untuk different views
        - Implementasi drill-through pages
        - Mobile layout untuk executive
        - Row-level security untuk data sensitif
        - Refresh schedule: Daily at 6 AM
        """)

    st.markdown("---")

    st.subheader("📥 Export Data untuk Power BI")

    col1, col2, col3 = st.columns(3)

    with col1:
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data Lengkap (CSV)",
            data=csv,
            file_name=f'keluhan_konsumen_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )

    with col2:
        # Data agregat untuk dashboard
        agg_data = filtered_df.groupby(['tahun', 'product', 'company']).agg({
            'complaint_id': 'count',
            'timely_response': lambda x: (x == 'Yes').mean() * 100,
            'consumer_disputed_is': lambda x: (x == 'Yes').mean() * 100,
            'waktu_respons_hari': 'mean'
        }).reset_index()
        agg_data.columns = ['Tahun', 'Produk', 'Perusahaan', 'Total_Keluhan',
                           'Persen_Tepat_Waktu', 'Persen_Sengketa', 'Avg_Waktu_Respons']

        agg_csv = agg_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Download Data Agregat",
            data=agg_csv,
            file_name=f'agregat_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )

    with col3:
        # Data summary statistics
        summary = filtered_df.describe(include='all').to_csv().encode('utf-8')
        st.download_button(
            label="📈 Download Statistik Summary",
            data=summary,
            file_name=f'summary_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )

    st.markdown("---")

    st.subheader("🚀 Langkah Implementasi")

    st.markdown("""
    **Step-by-Step Guide:**

    1. **Persiapan Data**
       - Download data dari tombol di atas
       - Import ke Power BI Desktop
       - Buat relationship jika ada multiple tables

    2. **Data Modeling**
       - Buat Date table dengan DAX: `CALENDAR()`
       - Buat calculated columns untuk kategori waktu respons
       - Definisikan measures yang direkomendasikan

    3. **Visualisasi**
       - Mulai dari Executive Dashboard
       - Gunakan template atau theme konsisten
       - Test interactivity antar visual

    4. **Testing**
       - Validasi angka dengan data source
       - Test filter dan slicer
       - Check performance dengan large dataset

    5. **Publish**
       - Publish ke Power BI Service
       - Set up scheduled refresh
       - Configure sharing & permissions
       - Create mobile view

    6. **Monitoring & Iteration**
       - Collect user feedback
       - Monitor dashboard usage analytics
       - Iterate berdasarkan kebutuhan user
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p><b>Dashboard Analisis Keluhan Konsumen</b></p>
    <p>Dibuat dengan Streamlit & Plotly | Siap untuk Integrasi Power BI</p>
    <p>Data dapat di-refresh dan di-filter sesuai kebutuhan analisis</p>
</div>
""", unsafe_allow_html=True)

# Informasi di Sidebar
st.sidebar.markdown("---")
st.sidebar.info(f"""
**📊 Informasi Dataset:**
- Total Record: **{len(df):,}**
- Periode: **{df['date_received'].min().strftime('%d %b %Y')}** s/d **{df['date_received'].max().strftime('%d %b %Y')}**
- Record Terfilter: **{len(filtered_df):,}**
- Total Perusahaan: **{df['company'].nunique():,}**
- Total Produk: **{df['product'].nunique()}**
""")

st.sidebar.success("""
**✅ Fitur Dashboard:**
- Filter interaktif
- 10+ Insight mendalam
- Visualisasi sederhana
- Rekomendasi Power BI
- Export data CSV
""")