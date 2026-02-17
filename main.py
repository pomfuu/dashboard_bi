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
        st.success("✅ Data dimuat dari file lokal")
    except FileNotFoundError:
        # Untuk Streamlit Cloud - load dari URL
        data_url = st.secrets.get("DATA_URL", "")
        if data_url:
            with st.spinner("📥 Memuat data dari cloud storage (ini mungkin memakan waktu beberapa menit)..."):
                try:
                    # Untuk Google Drive file besar, perlu tambahkan parameter confirm
                    # Deteksi jika URL dari Google Drive
                    if 'drive.google.com' in data_url:
                        # Extract file ID
                        if '/file/d/' in data_url:
                            file_id = data_url.split('/file/d/')[1].split('/')[0]
                        elif 'id=' in data_url:
                            file_id = data_url.split('id=')[1].split('&')[0]
                        else:
                            file_id = None

                        if file_id:
                            # Format URL dengan confirm untuk bypass virus scan warning
                            data_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"

                    df = pd.read_csv(data_url, low_memory=False)
                    st.success(f"✅ Data berhasil dimuat! Total baris: {len(df):,}")
                except Exception as e:
                    st.error(f"❌ Error saat memuat data dari cloud: {str(e)}")
                    st.info("💡 Pastikan link Google Drive sudah benar dan file dapat diakses publik.")
                    st.code(f"URL yang digunakan: {data_url}")
                    st.stop()
        else:
            st.error("❌ File data tidak ditemukan. Silakan upload 'consumer_complaints.csv' atau set DATA_URL di secrets.")
            st.info("📋 Untuk deployment, tambahkan DATA_URL di Streamlit Cloud Secrets.")
            st.stop()

    # Cek kolom yang ada dan mapping jika perlu
    # Beberapa dataset mungkin punya nama kolom dengan case berbeda
    df.columns = df.columns.str.lower().str.strip()

    # Konversi kolom tanggal (dengan pengecekan)
    if 'date_received' in df.columns:
        df['date_received'] = pd.to_datetime(df['date_received'], errors='coerce')
    elif 'date received' in df.columns:
        df['date_received'] = pd.to_datetime(df['date received'], errors='coerce')
    else:
        st.error(f"❌ Kolom tanggal tidak ditemukan. Kolom yang tersedia: {list(df.columns)}")
        st.stop()

    if 'date_sent_to_company' in df.columns:
        df['date_sent_to_company'] = pd.to_datetime(df['date_sent_to_company'], errors='coerce')
    elif 'date sent to company' in df.columns:
        df['date_sent_to_company'] = pd.to_datetime(df['date sent to company'], errors='coerce')

    # Ekstrak fitur tanggal
    df['tahun'] = df['date_received'].dt.year
    df['bulan'] = df['date_received'].dt.month
    df['nama_bulan'] = df['date_received'].dt.strftime('%B')
    df['hari'] = df['date_received'].dt.day_name()
    df['kuartal'] = df['date_received'].dt.quarter

    # Hitung waktu respons
    if 'date_sent_to_company' in df.columns:
        df['waktu_respons_hari'] = (df['date_sent_to_company'] - df['date_received']).dt.days
    else:
        df['waktu_respons_hari'] = 0

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
tab_main, tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⭐ 5 Chart Utama",
    "🚨 Executive Story",
    "🔍 Insight Utama",
    "📊 Analisis Tren",
    "🏢 Analisis Perusahaan",
    "📋 Pivot Tables",
    "💡 Rekomendasi Power BI"
])

with tab_main:
    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 60%, #1f77b4 100%);
                padding: 1.8rem 2rem; border-radius: 12px; margin-bottom: 1.5rem;'>
        <h1 style='color:white; margin:0; font-size:1.7rem; font-weight:700;'>
            ⭐ 5 Chart yang Paling Berbunyi
        </h1>
        <p style='color:#93c5fd; margin:0.4rem 0 0 0; font-size:0.95rem;'>
            Dipilih berdasarkan kedalaman insight, kejelasan cerita, dan relevansi untuk keputusan bisnis
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Pre-compute data ─────────────────────────────────────────────────────
    pc          = filtered_df['product'].value_counts()
    top8_p      = pc.head(8).index.tolist()
    top5_p      = pc.head(5).index.tolist()
    top10_co    = filtered_df['company'].value_counts().head(10).index.tolist()
    top5_co     = filtered_df['company'].value_counts().head(5).index.tolist()
    top5_st     = filtered_df['state'].value_counts().head(5).index.tolist()
    top5_iss    = filtered_df['issue'].value_counts().head(5).index.tolist()

    # ════════════════════════════════════════════════════════════════════════
    # CHART 1 — Stacked Bar Horizontal: Produk Berbahaya
    # ════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div style='display:flex; align-items:flex-start; gap:1rem; margin:1.2rem 0 0.2rem 0;'>
        <div style='background:#dc2626; color:white; border-radius:50%; min-width:2.2rem;
                    height:2.2rem; display:flex; align-items:center; justify-content:center;
                    font-weight:800; font-size:1rem; margin-top:2px;'>1</div>
        <div>
            <h3 style='margin:0; color:#1f2937; font-size:1.15rem;'>
                Produk Mana yang Paling "Berbahaya"?
            </h3>
            <p style='margin:0.2rem 0 0 0; color:#6b7280; font-size:0.88rem;'>
                Volume keluhan tinggi belum tentu masalah utama — lihat
                <b style='color:#dc2626;'>tingkat sengketa</b>-nya.
                Inilah produk yang benar-benar merugikan konsumen.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_c1a, col_c1b = st.columns([3, 2])
    with col_c1a:
        stk = filtered_df[filtered_df['product'].isin(top8_p)].copy()
        disp_cnt = (
            stk.groupby('product')['consumer_disputed_is']
            .apply(lambda x: (x == 'Yes').sum()).reset_index(name='disputed')
        )
        tot_cnt = stk['product'].value_counts().reset_index()
        tot_cnt.columns = ['product', 'total']
        sm = disp_cnt.merge(tot_cnt, on='product')
        sm['not_disputed']  = sm['total'] - sm['disputed']
        sm['dispute_pct']   = (sm['disputed'] / sm['total'] * 100).round(1)
        sm = sm.sort_values('dispute_pct', ascending=True)   # urut by dispute rate

        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            y=sm['product'], x=sm['not_disputed'], name='Tidak Bersengketa',
            orientation='h', marker_color='#bfdbfe',
            hovertemplate='%{y}<br>Tidak Bersengketa: %{x:,}<extra></extra>'
        ))
        fig1.add_trace(go.Bar(
            y=sm['product'], x=sm['disputed'], name='Bersengketa ⚠️',
            orientation='h', marker_color='#dc2626',
            customdata=sm['dispute_pct'],
            hovertemplate='%{y}<br>Bersengketa: %{x:,}<br>Dispute Rate: %{customdata:.1f}%<extra></extra>'
        ))
        # Annotasi dispute % di ujung bar
        for _, r in sm.iterrows():
            fig1.add_annotation(
                y=r['product'], x=r['total'] + sm['total'].max() * 0.01,
                text=f"<b>{r['dispute_pct']:.1f}%</b>",
                showarrow=False, xanchor='left', font=dict(size=10, color='#dc2626')
            )
        fig1.update_layout(
            barmode='stack', height=400,
            xaxis=dict(title='Jumlah Keluhan', showgrid=True, gridcolor='#f3f4f6'),
            yaxis=dict(title=''),
            legend=dict(orientation='h', y=1.08, x=1, xanchor='right'),
            plot_bgcolor='white', paper_bgcolor='white',
            margin=dict(l=10, r=80, t=30, b=40), font=dict(size=11)
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col_c1b:
        st.markdown("##### Peringkat Risiko")
        for _, r in sm.sort_values('dispute_pct', ascending=False).iterrows():
            p = r['dispute_pct']
            c = '#dc2626' if p >= 22 else '#f59e0b' if p >= 15 else '#16a34a'
            l = 'KRITIS' if p >= 22 else 'WASPADA' if p >= 15 else 'AMAN'
            st.markdown(f"""
            <div style='background:#f9fafb; border-left:4px solid {c};
                        padding:0.45rem 0.8rem; margin-bottom:0.35rem; border-radius:4px;'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <span style='font-size:0.78rem; font-weight:600; color:#374151;
                                 overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
                                 max-width:62%;'>{r['product'][:34]}</span>
                    <span style='background:{c}; color:white; border-radius:9999px;
                                 padding:0.1rem 0.45rem; font-size:0.68rem;
                                 font-weight:700; white-space:nowrap;'>{l} {p:.1f}%</span>
                </div>
                <div style='font-size:0.7rem; color:#9ca3af; margin-top:1px;'>
                    {r["disputed"]:,} dari {r["total"]:,} bersengketa
                </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("""<div style='font-size:0.72rem; color:#6b7280; margin-top:0.5rem;
                        border-top:1px solid #e5e7eb; padding-top:0.5rem;'>
            <b>Threshold:</b> KRITIS ≥22% | WASPADA ≥15% | AMAN &lt;15%<br>
            Rata-rata industri: <b>20.2%</b>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # CHART 2 — 100% Stacked Bar: Kualitas Respons per Perusahaan
    # ════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div style='display:flex; align-items:flex-start; gap:1rem; margin-bottom:0.2rem;'>
        <div style='background:#d97706; color:white; border-radius:50%; min-width:2.2rem;
                    height:2.2rem; display:flex; align-items:center; justify-content:center;
                    font-weight:800; font-size:1rem; margin-top:2px;'>2</div>
        <div>
            <h3 style='margin:0; color:#1f2937; font-size:1.15rem;'>
                Siapa yang Benar-Benar Menyelesaikan Masalah?
            </h3>
            <p style='margin:0.2rem 0 0 0; color:#6b7280; font-size:0.88rem;'>
                <b style='color:#d97706;'>100% Stacked Bar</b> — setiap bar = 100% keluhan per perusahaan.
                Hijau = kompensasi nyata, Merah = ditutup tanpa solusi. Mana yang dominan?
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    resp2 = (
        filtered_df[filtered_df['company'].isin(top10_co)]
        .groupby(['company', 'company_response_to_consumer'])
        .size().reset_index(name='count')
    )
    resp2['pct'] = (resp2['count'] / resp2.groupby('company')['count'].transform('sum') * 100).round(1)

    mon2  = resp2[resp2['company_response_to_consumer'].str.contains('monetary', case=False, na=False)]
    order2 = mon2.groupby('company')['pct'].sum().sort_values(ascending=False).index.tolist()
    for c in top10_co:
        if c not in order2: order2.append(c)

    resp_colors2 = {
        'Closed with monetary relief':     '#16a34a',
        'Closed with non-monetary relief': '#86efac',
        'Closed with explanation':         '#93c5fd',
        'Closed without relief':           '#f87171',
        'Closed':                          '#d1d5db',
        'In progress':                     '#fbbf24',
        'Untimely response':               '#dc2626',
    }
    fig2 = go.Figure()
    for rt in resp2['company_response_to_consumer'].unique():
        sub2 = resp2[resp2['company_response_to_consumer'] == rt]
        sub2 = sub2.set_index('company').reindex(order2).reset_index()
        fig2.add_trace(go.Bar(
            y=sub2['company'], x=sub2['pct'].fillna(0), name=rt,
            orientation='h', marker_color=resp_colors2.get(rt, '#e5e7eb'),
            hovertemplate='%{y}<br>' + rt + ': %{x:.1f}%<extra></extra>'
        ))
    fig2.update_layout(
        barmode='stack', height=420,
        xaxis=dict(title='Persentase (%)', ticksuffix='%', range=[0,100], showgrid=True, gridcolor='#f3f4f6'),
        yaxis=dict(title='', categoryorder='array', categoryarray=list(reversed(order2))),
        legend=dict(orientation='h', y=-0.3, x=0.5, xanchor='center', font=dict(size=9.5)),
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=10, r=10, t=20, b=110), font=dict(size=11)
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("""
    <div style='background:#f0fdf4; border-left:4px solid #16a34a;
                padding:0.6rem 1rem; border-radius:6px; font-size:0.85rem; margin-top:-0.5rem;'>
        <b>💡 Cara baca:</b> Diurutkan dari perusahaan yang <b>paling banyak memberi kompensasi finansial</b> (hijau tua) ke terendah.
        Perusahaan di bawah = lebih banyak menutup keluhan tanpa solusi nyata.
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # CHART 3 — Stacked Bar Vertikal: Tren Keluhan per Produk per Tahun
    # ════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div style='display:flex; align-items:flex-start; gap:1rem; margin-bottom:0.2rem;'>
        <div style='background:#7c3aed; color:white; border-radius:50%; min-width:2.2rem;
                    height:2.2rem; display:flex; align-items:center; justify-content:center;
                    font-weight:800; font-size:1rem; margin-top:2px;'>3</div>
        <div>
            <h3 style='margin:0; color:#1f2937; font-size:1.15rem;'>
                Tren Keluhan per Tahun — Komposisi Produk Bergeser?
            </h3>
            <p style='margin:0.2rem 0 0 0; color:#6b7280; font-size:0.88rem;'>
                <b style='color:#7c3aed;'>Stacked Bar vertikal</b> — bukan sekadar naik/turun total,
                tapi <b>produk mana yang mendorong kenaikan</b>?
                Drop 2016 = data belum lengkap (sebagian tahun).
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_c3a, col_c3b = st.columns([3, 2])
    with col_c3a:
        tren3 = (
            filtered_df[filtered_df['product'].isin(top5_p)]
            .groupby(['tahun', 'product']).size().reset_index(name='jumlah')
        )
        pal3 = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd']
        fig3 = go.Figure()
        for i, prod in enumerate(top5_p):
            sub3 = tren3[tren3['product'] == prod]
            fig3.add_trace(go.Bar(
                x=sub3['tahun'].astype(str), y=sub3['jumlah'],
                name=prod, marker_color=pal3[i % 5],
                hovertemplate='%{x} — ' + prod + '<br>%{y:,} keluhan<extra></extra>'
            ))
        # Annotasi total per tahun di atas bar
        totals3 = tren3.groupby('tahun')['jumlah'].sum().reset_index()
        for _, r in totals3.iterrows():
            fig3.add_annotation(
                x=str(int(r['tahun'])), y=r['jumlah'],
                text=f"<b>{int(r['jumlah']):,}</b>",
                showarrow=False, yshift=8, font=dict(size=9.5, color='#374151')
            )
        fig3.update_layout(
            barmode='stack', height=390,
            xaxis=dict(title='Tahun', showgrid=False),
            yaxis=dict(title='Jumlah Keluhan', showgrid=True, gridcolor='#f3f4f6'),
            legend=dict(orientation='h', y=1.08, x=1, xanchor='right', font=dict(size=9.5)),
            plot_bgcolor='white', paper_bgcolor='white',
            margin=dict(l=10, r=10, t=30, b=40), font=dict(size=11)
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col_c3b:
        st.markdown("##### Sinyal Tren per Produk")
        if len(filtered_df['tahun'].unique()) >= 2:
            yr_s   = sorted(filtered_df['tahun'].dropna().unique())
            yf, yl = yr_s[0], yr_s[-1]
            for prod in top5_p:
                sp   = filtered_df[filtered_df['product'] == prod]
                vf   = len(sp[sp['tahun'] == yf])
                vl   = len(sp[sp['tahun'] == yl])
                gr   = ((vl - vf) / vf * 100) if vf > 0 else 0
                arr  = '▲' if gr > 0 else '▼'
                col3 = '#dc2626' if gr > 10 else '#16a34a' if gr < -10 else '#f59e0b'
                lbl  = 'NAIK' if gr > 10 else 'TURUN' if gr < -10 else 'STABIL'
                st.markdown(f"""
                <div style='background:#f9fafb; border-left:4px solid {col3};
                            padding:0.45rem 0.8rem; margin-bottom:0.35rem; border-radius:4px;'>
                    <div style='font-size:0.78rem; font-weight:600; color:#374151;
                                overflow:hidden; text-overflow:ellipsis; white-space:nowrap;'
                    >{prod[:38]}</div>
                    <div style='display:flex; justify-content:space-between; margin-top:2px;'>
                        <span style='font-size:0.7rem; color:#9ca3af;'>
                            {vf:,} ({int(yf)}) → {vl:,} ({int(yl)})
                        </span>
                        <span style='color:{col3}; font-weight:700; font-size:0.78rem;'>
                            {arr} {abs(gr):.1f}% {lbl}
                        </span>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Pilih 2+ tahun untuk melihat sinyal tren.")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # CHART 4 — Bar Chart Horizontal: Top 5 Issue per Top Company
    # ════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div style='display:flex; align-items:flex-start; gap:1rem; margin-bottom:0.2rem;'>
        <div style='background:#0891b2; color:white; border-radius:50%; min-width:2.2rem;
                    height:2.2rem; display:flex; align-items:center; justify-content:center;
                    font-weight:800; font-size:1rem; margin-top:2px;'>4</div>
        <div>
            <h3 style='margin:0; color:#1f2937; font-size:1.15rem;'>
                Top 5 Perusahaan vs Top 5 Masalah — Di Mana Titik Panasnya?
            </h3>
            <p style='margin:0.2rem 0 0 0; color:#6b7280; font-size:0.88rem;'>
                <b style='color:#0891b2;'>Grouped Bar</b> — kombinasi perusahaan &times; jenis masalah.
                Identifikasi pasangan perusahaan-masalah yang paling kritis untuk ditindaklanjuti.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    heat_df = (
        filtered_df[
            filtered_df['company'].isin(top5_co) &
            filtered_df['issue'].isin(top5_iss)
        ]
        .groupby(['company', 'issue']).size().reset_index(name='jumlah')
    )
    # Potong nama issue agar tidak terlalu panjang
    heat_df['issue_short'] = heat_df['issue'].str[:35]
    heat_df['company_short'] = heat_df['company'].apply(
        lambda x: x.split('&')[0].split(',')[0].strip()[:22]
    )

    pal4 = ['#0891b2','#0e7490','#155e75','#164e63','#083344']
    fig4 = go.Figure()
    for i, comp in enumerate(top5_co):
        sub4 = heat_df[heat_df['company'] == comp]
        fig4.add_trace(go.Bar(
            x=sub4['jumlah'], y=sub4['issue_short'],
            name=comp.split('&')[0].split(',')[0].strip()[:22],
            orientation='h', marker_color=pal4[i % 5],
            hovertemplate='<b>%{fullText}</b><br>' + comp[:30] + '<br>%{x:,} keluhan<extra></extra>',
        ))
    fig4.update_layout(
        barmode='group', height=420,
        xaxis=dict(title='Jumlah Keluhan', showgrid=True, gridcolor='#f3f4f6'),
        yaxis=dict(title=''),
        legend=dict(orientation='h', y=1.08, x=1, xanchor='right', font=dict(size=9.5)),
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=10, r=10, t=30, b=50), font=dict(size=11)
    )
    st.plotly_chart(fig4, use_container_width=True)

    # Temukan kombinasi terburuk
    if len(heat_df) > 0:
        worst = heat_df.nlargest(1, 'jumlah').iloc[0]
        st.markdown(f"""
        <div style='background:#fef2f2; border-left:4px solid #dc2626;
                    padding:0.6rem 1rem; border-radius:6px; font-size:0.85rem; margin-top:-0.5rem;'>
            <b>🔴 Kombinasi paling kritis:</b>
            <b>{worst['company'][:40]}</b> dengan masalah <b>"{worst['issue'][:50]}"</b>
            — <b>{int(worst['jumlah']):,} keluhan</b>. Ini titik panas yang butuh tindakan segera.
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # CHART 5 — Line Chart: Tren Bulanan + Dispute Rate Overlay
    # ════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div style='display:flex; align-items:flex-start; gap:1rem; margin-bottom:0.2rem;'>
        <div style='background:#059669; color:white; border-radius:50%; min-width:2.2rem;
                    height:2.2rem; display:flex; align-items:center; justify-content:center;
                    font-weight:800; font-size:1rem; margin-top:2px;'>5</div>
        <div>
            <h3 style='margin:0; color:#1f2937; font-size:1.15rem;'>
                Tren Bulanan: Volume Keluhan vs Tingkat Sengketa
            </h3>
            <p style='margin:0.2rem 0 0 0; color:#6b7280; font-size:0.88rem;'>
                <b style='color:#059669;'>Dual-axis Line Chart</b> — apakah lonjakan volume
                <b>selalu diikuti naiknya dispute rate</b>? Jika ya, ada masalah sistemik.
                Jika tidak, ada bulan-bulan "berbahaya" tersembunyi.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    bulan_data = (
        filtered_df
        .groupby(['tahun', 'bulan'])
        .agg(
            jumlah      = ('complaint_id', 'count'),
            disputed    = ('consumer_disputed_is', lambda x: (x == 'Yes').sum())
        ).reset_index()
    )
    bulan_data['dispute_rate'] = (bulan_data['disputed'] / bulan_data['jumlah'] * 100).round(1)
    bulan_data['periode']      = bulan_data['tahun'].astype(str) + '-' + bulan_data['bulan'].astype(str).str.zfill(2)
    bulan_data = bulan_data.sort_values('periode')

    fig5 = go.Figure()
    # Bar volume (sumbu kiri)
    fig5.add_trace(go.Bar(
        x=bulan_data['periode'], y=bulan_data['jumlah'],
        name='Volume Keluhan', marker_color='#bfdbfe', opacity=0.7,
        yaxis='y1',
        hovertemplate='%{x}<br>Volume: %{y:,}<extra></extra>'
    ))
    # Line dispute rate (sumbu kanan)
    fig5.add_trace(go.Scatter(
        x=bulan_data['periode'], y=bulan_data['dispute_rate'],
        name='Dispute Rate %', mode='lines+markers',
        line=dict(color='#dc2626', width=2.5),
        marker=dict(size=4),
        yaxis='y2',
        hovertemplate='%{x}<br>Dispute Rate: %{y:.1f}%<extra></extra>'
    ))
    # Garis rata-rata dispute rate
    avg_dr = bulan_data['dispute_rate'].mean()
    fig5.add_hline(
        y=avg_dr, line_dash='dash', line_color='#f59e0b',
        annotation_text=f'Avg Dispute Rate: {avg_dr:.1f}%',
        annotation_position='top right', annotation_font_size=10,
        yref='y2'
    )
    fig5.update_layout(
        height=400,
        xaxis=dict(title='Periode (Tahun-Bulan)', showgrid=False,
                   tickangle=-45, nticks=20),
        yaxis =dict(title='Jumlah Keluhan', showgrid=True,
                    gridcolor='#f3f4f6', side='left'),
        yaxis2=dict(title='Dispute Rate (%)', overlaying='y', side='right',
                    showgrid=False, ticksuffix='%', range=[0, 40]),
        legend=dict(orientation='h', y=1.08, x=1, xanchor='right'),
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=10, r=60, t=30, b=80), font=dict(size=11),
        bargap=0.1
    )
    st.plotly_chart(fig5, use_container_width=True)

    # Temukan bulan dispute rate tertinggi
    worst_month = bulan_data.nlargest(1, 'dispute_rate').iloc[0]
    best_month  = bulan_data.nsmallest(1, 'dispute_rate').iloc[0]
    st.markdown(f"""
    <div style='background:#fffbeb; border-left:4px solid #f59e0b;
                padding:0.6rem 1rem; border-radius:6px; font-size:0.85rem; margin-top:-0.5rem;'>
        <b>⚠️ Bulan paling berbahaya:</b> <b>{worst_month['periode']}</b>
        — dispute rate <b>{worst_month['dispute_rate']:.1f}%</b>
        ({int(worst_month['disputed']):,} sengketa dari {int(worst_month['jumlah']):,} keluhan).
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>✅ Terbaik:</b> <b>{best_month['periode']}</b>
        — dispute rate hanya <b>{best_month['dispute_rate']:.1f}%</b>.
    </div>""", unsafe_allow_html=True)

    # ── Ringkasan 5 Takeaway ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🎯 5 Takeaway Utama untuk Presentasi")
    takeaways = [
        ("🔴", "#fef2f2", "#fca5a5", "#991b1b",
         "Mortgage = Produk Paling Berisiko",
         "Dispute rate 23.2% — tertinggi dari semua produk. Nilai transaksi besar membuat konsumen lebih gigih bersengketa. Butuh SOP penanganan khusus."),
        ("🟠", "#fffbeb", "#fcd34d", "#92400e",
         "72% Keluhan Ditutup Hanya dengan Penjelasan",
         "Dominasi 'Closed with explanation' menunjukkan mayoritas perusahaan tidak memberikan kompensasi nyata. Konsumen sering merasa tidak puas."),
        ("🟣", "#f5f3ff", "#c4b5fd", "#5b21b6",
         "Keluhan Naik 5.5x dari 2011 ke 2015",
         "Pertumbuhan masif dalam 4 tahun — bukan noise, ini sinyal struktural. Credit Reporting tumbuh paling cepat relatif terhadap baseline."),
        ("🔵", "#eff6ff", "#93c5fd", "#1e40af",
         "Bank of America Paling Banyak Keluhan (55,998)",
         "Top 5 perusahaan menyumbang ~35% dari semua keluhan. Konsentrasi ini memudahkan intervensi regulasi yang tepat sasaran."),
        ("🟢", "#f0fdf4", "#86efac", "#166534",
         "Ada Bulan-Bulan 'Tersembunyi' yang Dispute Rate Melonjak",
         "Volume rendah bukan berarti aman — beberapa bulan punya dispute rate tinggi meski volume kecil. Monitoring perlu berbasis rate, bukan hanya volume absolut."),
    ]
    col_tk = st.columns(5)
    for i, (icon, bg, border, tc, title, desc) in enumerate(takeaways):
        with col_tk[i]:
            st.markdown(f"""
            <div style='background:{bg}; border:1px solid {border}; border-radius:8px;
                        padding:0.9rem; height:100%; min-height:160px;'>
                <div style='font-size:1.4rem; margin-bottom:0.3rem;'>{icon}</div>
                <div style='font-weight:700; color:{tc}; font-size:0.8rem;
                            margin-bottom:0.4rem; line-height:1.3;'>{title}</div>
                <div style='color:#6b7280; font-size:0.73rem; line-height:1.4;'>{desc}</div>
            </div>""", unsafe_allow_html=True)

with tab0:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #1f2937 0%, #1f77b4 100%);
                padding: 2rem; border-radius: 12px; margin-bottom: 1.5rem;'>
        <h1 style='color: white; margin: 0; font-size: 1.8rem;'>🚨 Executive Story: Apa yang Paling Mendesak?</h1>
        <p style='color: #93c5fd; margin: 0.5rem 0 0 0; font-size: 1rem;'>
            3 temuan kritis yang membutuhkan tindakan segera — dirancang untuk Power BI & presentasi eksekutif
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── PRE-COMPUTE semua data yang dibutuhkan ──────────────────────────────
    produk_counts    = filtered_df['product'].value_counts()
    top5_prod        = produk_counts.head(5).index.tolist()
    top8_issues      = filtered_df['issue'].value_counts().head(8).index.tolist()
    top10_companies  = filtered_df['company'].value_counts().head(10).index.tolist()
    top10_states     = filtered_df['state'].value_counts().head(10).index.tolist()
    top6_prod        = produk_counts.head(6).index.tolist()

    dispute_by_product = (
        filtered_df.groupby('product')['consumer_disputed_is']
        .apply(lambda x: (x == 'Yes').mean() * 100)
        .reset_index()
        .rename(columns={'consumer_disputed_is': 'dispute_rate'})
    )
    volume_by_product = filtered_df['product'].value_counts().reset_index()
    volume_by_product.columns = ['product', 'volume']
    bubble_df = dispute_by_product.merge(volume_by_product, on='product')

    # ── STORY 1 ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
    <div style='display:flex; align-items:center; gap:0.6rem; margin-bottom:0.3rem'>
        <span style='background:#dc2626; color:white; border-radius:50%; width:2rem;
                     height:2rem; display:inline-flex; align-items:center;
                     justify-content:center; font-weight:bold; font-size:1rem;'>1</span>
        <h2 style='margin:0; color:#1f2937;'>Produk Mana yang Paling "Berbahaya"?</h2>
    </div>
    <p style='color:#6b7280; margin-bottom:1rem; margin-left:2.6rem;'>
        Volume keluhan tinggi belum tentu masalah utama — lihat <b>tingkat sengketa</b>-nya.
        Inilah produk yang benar-benar merugikan konsumen.
    </p>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns([3, 2])

    with col_l:
        # Stacked bar: volume + dispute rate per produk (top 8)
        top8_prod = produk_counts.head(8).index.tolist()
        stack_df = filtered_df[filtered_df['product'].isin(top8_prod)].copy()

        # Hitung disputed vs non-disputed
        disputed_cnt = (
            stack_df.groupby('product')['consumer_disputed_is']
            .apply(lambda x: (x == 'Yes').sum())
            .reset_index(name='disputed')
        )
        total_cnt = stack_df['product'].value_counts().reset_index()
        total_cnt.columns = ['product', 'total']
        stack_merged = disputed_cnt.merge(total_cnt, on='product')
        stack_merged['not_disputed'] = stack_merged['total'] - stack_merged['disputed']
        stack_merged['dispute_pct'] = (stack_merged['disputed'] / stack_merged['total'] * 100).round(1)
        stack_merged = stack_merged.sort_values('total', ascending=True)

        fig_story1 = go.Figure()
        fig_story1.add_trace(go.Bar(
            y=stack_merged['product'],
            x=stack_merged['not_disputed'],
            name='Tidak Bersengketa',
            orientation='h',
            marker_color='#93c5fd',
            hovertemplate='%{y}<br>Tidak Bersengketa: %{x:,}<extra></extra>'
        ))
        fig_story1.add_trace(go.Bar(
            y=stack_merged['product'],
            x=stack_merged['disputed'],
            name='Bersengketa ⚠️',
            orientation='h',
            marker_color='#dc2626',
            hovertemplate='%{y}<br>Bersengketa: %{x:,} (%{customdata:.1f}%)<extra></extra>',
            customdata=stack_merged['dispute_pct']
        ))
        fig_story1.update_layout(
            barmode='stack',
            title='Stacked Bar: Volume Keluhan & Porsi Sengketa per Produk',
            xaxis_title='Jumlah Keluhan',
            yaxis_title='',
            height=420,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=10, r=10, t=60, b=40),
            font=dict(size=12)
        )
        st.plotly_chart(fig_story1, use_container_width=True)

    with col_r:
        st.markdown("#### Peringkat Risiko Produk")
        risk_df = stack_merged.sort_values('dispute_pct', ascending=False)[['product', 'total', 'disputed', 'dispute_pct']]
        risk_df.columns = ['Produk', 'Total', 'Sengketa', 'Dispute %']

        for _, row in risk_df.iterrows():
            pct = row['Dispute %']
            color = '#dc2626' if pct >= 25 else '#f59e0b' if pct >= 15 else '#16a34a'
            label = 'KRITIS' if pct >= 25 else 'WASPADA' if pct >= 15 else 'AMAN'
            st.markdown(f"""
            <div style='background:#f9fafb; border-left: 4px solid {color};
                        padding: 0.5rem 0.8rem; margin-bottom:0.4rem; border-radius:4px;'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <span style='font-size:0.78rem; font-weight:600; color:#374151;
                                 max-width:65%; overflow:hidden; text-overflow:ellipsis;
                                 white-space:nowrap;'>{row['Produk'][:35]}</span>
                    <span style='background:{color}; color:white; border-radius:9999px;
                                 padding:0.1rem 0.5rem; font-size:0.7rem;
                                 font-weight:700;'>{label} {pct:.1f}%</span>
                </div>
                <div style='font-size:0.72rem; color:#6b7280; margin-top:2px;'>
                    {row['Sengketa']:,} dari {row['Total']:,} keluhan bersengketa
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── STORY 2 ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
    <div style='display:flex; align-items:center; gap:0.6rem; margin-bottom:0.3rem'>
        <span style='background:#d97706; color:white; border-radius:50%; width:2rem;
                     height:2rem; display:inline-flex; align-items:center;
                     justify-content:center; font-weight:bold; font-size:1rem;'>2</span>
        <h2 style='margin:0; color:#1f2937;'>Respons Perusahaan: Siapa yang Benar-Benar Menyelesaikan Masalah?</h2>
    </div>
    <p style='color:#6b7280; margin-bottom:1rem; margin-left:2.6rem;'>
        Membandingkan <b>jenis resolusi</b> antar perusahaan terbesar — apakah mereka menutup
        dengan solusi nyata atau hanya "dijelaskan" saja tanpa kompensasi?
    </p>
    """, unsafe_allow_html=True)

    resp_data = (
        filtered_df[filtered_df['company'].isin(top10_companies)]
        .groupby(['company', 'company_response_to_consumer'])
        .size()
        .reset_index(name='count')
    )
    total_per_company = resp_data.groupby('company')['count'].transform('sum')
    resp_data['pct'] = (resp_data['count'] / total_per_company * 100).round(1)

    # Urutkan perusahaan berdasarkan % monetary relief (paling bermasalah di atas)
    monetary = resp_data[resp_data['company_response_to_consumer'].str.contains('monetary', case=False, na=False)]
    monetary_rank = monetary.groupby('company')['pct'].sum().sort_values(ascending=False)
    company_order = monetary_rank.index.tolist()
    # Tambahkan perusahaan yang tidak ada monetary relief ke akhir
    for c in top10_companies:
        if c not in company_order:
            company_order.append(c)

    # Warna per jenis respons
    response_colors = {
        'Closed with monetary relief':     '#16a34a',
        'Closed with non-monetary relief': '#4ade80',
        'Closed with explanation':         '#93c5fd',
        'Closed without relief':           '#f87171',
        'In progress':                     '#fbbf24',
        'Untimely response':               '#dc2626',
    }
    all_responses = resp_data['company_response_to_consumer'].unique().tolist()
    colormap = {r: response_colors.get(r, '#d1d5db') for r in all_responses}

    fig_story2 = go.Figure()
    for resp_type in all_responses:
        sub = resp_data[resp_data['company_response_to_consumer'] == resp_type]
        # Pastikan urutan company konsisten
        sub = sub.set_index('company').reindex(company_order).reset_index()
        fig_story2.add_trace(go.Bar(
            y=sub['company'],
            x=sub['pct'].fillna(0),
            name=resp_type,
            orientation='h',
            marker_color=colormap[resp_type],
            hovertemplate='%{y}<br>' + resp_type + ': %{x:.1f}%<extra></extra>',
        ))

    fig_story2.update_layout(
        barmode='stack',
        title='100% Stacked Bar: Komposisi Jenis Respons per Perusahaan (Top 10)',
        xaxis=dict(title='Persentase (%)', ticksuffix='%', range=[0, 100]),
        yaxis=dict(title='', categoryorder='array', categoryarray=list(reversed(company_order))),
        height=480,
        legend=dict(orientation='h', yanchor='bottom', y=-0.35, xanchor='center', x=0.5, font=dict(size=10)),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=10, r=10, t=60, b=120),
        font=dict(size=11)
    )
    st.plotly_chart(fig_story2, use_container_width=True)

    st.markdown("""
    <div style='background:#fffbeb; border-left:4px solid #d97706;
                padding:0.8rem 1rem; border-radius:6px; margin-top:-0.5rem;'>
        <b>🔍 Cara membaca grafik ini:</b> Urutan dari atas = perusahaan dengan % <span style='color:#16a34a;font-weight:700'>
        monetary relief tertinggi</span> (paling sering memberi kompensasi).
        Dominasi warna <span style='color:#f87171;font-weight:700'>merah</span> = keluhan ditutup tanpa solusi nyata.
        Ini langsung bisa direplikasi di Power BI sebagai <i>100% Stacked Bar Chart</i>.
    </div>
    """, unsafe_allow_html=True)

    # ── STORY 3 ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
    <div style='display:flex; align-items:center; gap:0.6rem; margin-bottom:0.3rem'>
        <span style='background:#7c3aed; color:white; border-radius:50%; width:2rem;
                     height:2rem; display:inline-flex; align-items:center;
                     justify-content:center; font-weight:bold; font-size:1rem;'>3</span>
        <h2 style='margin:0; color:#1f2937;'>Tren Tahunan: Apakah Masalah Makin Parah?</h2>
    </div>
    <p style='color:#6b7280; margin-bottom:1rem; margin-left:2.6rem;'>
        Stacked bar per tahun menunjukkan <b>apakah komposisi produk bermasalah bergeser</b>
        — bukan sekadar naik/turun total volume.
    </p>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 2])

    with col_a:
        tren_prod = (
            filtered_df[filtered_df['product'].isin(top5_prod)]
            .groupby(['tahun', 'product'])
            .size()
            .reset_index(name='jumlah')
        )

        product_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        fig_story3 = go.Figure()
        for idx, prod in enumerate(top5_prod):
            sub = tren_prod[tren_prod['product'] == prod]
            fig_story3.add_trace(go.Bar(
                x=sub['tahun'].astype(str),
                y=sub['jumlah'],
                name=prod,
                marker_color=product_palette[idx % len(product_palette)],
                hovertemplate='%{x}<br>' + prod + ': %{y:,} keluhan<extra></extra>'
            ))

        fig_story3.update_layout(
            barmode='stack',
            title='Stacked Bar: Komposisi Keluhan per Produk & Tahun (Top 5 Produk)',
            xaxis_title='Tahun',
            yaxis_title='Jumlah Keluhan',
            height=420,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=10)),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=10, r=10, t=70, b=40),
            font=dict(size=12)
        )
        st.plotly_chart(fig_story3, use_container_width=True)

    with col_b:
        st.markdown("#### Sinyal Tren per Produk")
        # Hitung YoY growth tiap produk (tahun pertama vs terakhir)
        if len(filtered_df['tahun'].unique()) >= 2:
            tahun_sorted = sorted(filtered_df['tahun'].dropna().unique())
            yr_first, yr_last = tahun_sorted[0], tahun_sorted[-1]
            for prod in top5_prod:
                sub_prod = filtered_df[filtered_df['product'] == prod]
                v_first = len(sub_prod[sub_prod['tahun'] == yr_first])
                v_last  = len(sub_prod[sub_prod['tahun'] == yr_last])
                growth  = ((v_last - v_first) / v_first * 100) if v_first > 0 else 0
                arrow   = '▲' if growth > 0 else '▼'
                color   = '#dc2626' if growth > 10 else '#16a34a' if growth < -10 else '#f59e0b'
                label   = 'NAIK' if growth > 10 else 'TURUN' if growth < -10 else 'STABIL'
                st.markdown(f"""
                <div style='background:#f9fafb; border-left:4px solid {color};
                            padding: 0.5rem 0.8rem; margin-bottom:0.4rem; border-radius:4px;'>
                    <div style='font-size:0.78rem; font-weight:600; color:#374151;
                                overflow:hidden; text-overflow:ellipsis; white-space:nowrap;'
                    >{prod[:40]}</div>
                    <div style='display:flex; justify-content:space-between; margin-top:2px;'>
                        <span style='font-size:0.72rem; color:#6b7280;'>
                            {v_first:,} ({int(yr_first)}) → {v_last:,} ({int(yr_last)})
                        </span>
                        <span style='color:{color}; font-weight:700; font-size:0.78rem;'>
                            {arrow} {abs(growth):.1f}% {label}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Pilih lebih dari 1 tahun untuk melihat tren.")

    # ── RINGKASAN EKSEKUTIF ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📋 Ringkasan Eksekutif untuk Presentasi")

    # Hitung nilai dinamis untuk ringkasan
    most_dangerous = stack_merged.sort_values('dispute_pct', ascending=False).iloc[0]
    lowest_monetary_company = company_order[-1] if company_order else "-"
    highest_monetary_company = company_order[0] if company_order else "-"

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.markdown(f"""
        <div style='background:#fef2f2; border:1px solid #fca5a5;
                    border-radius:8px; padding:1rem; height:100%;'>
            <div style='font-size:1.5rem; margin-bottom:0.3rem;'>🔴</div>
            <div style='font-weight:700; color:#991b1b; margin-bottom:0.4rem;'>Produk Paling Berisiko</div>
            <div style='font-size:1.1rem; font-weight:600; color:#1f2937;
                        overflow:hidden; text-overflow:ellipsis;'>{most_dangerous['product']}</div>
            <div style='color:#6b7280; font-size:0.85rem; margin-top:0.3rem;'>
                {most_dangerous['dispute_pct']:.1f}% keluhan berakhir sengketa
                ({most_dangerous['disputed']:,} kasus)
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_s2:
        st.markdown(f"""
        <div style='background:#fffbeb; border:1px solid #fcd34d;
                    border-radius:8px; padding:1rem; height:100%;'>
            <div style='font-size:1.5rem; margin-bottom:0.3rem;'>⚠️</div>
            <div style='font-weight:700; color:#92400e; margin-bottom:0.4rem;'>Resolusi Terendah</div>
            <div style='font-size:1rem; font-weight:600; color:#1f2937;
                        overflow:hidden; text-overflow:ellipsis;'>{lowest_monetary_company}</div>
            <div style='color:#6b7280; font-size:0.85rem; margin-top:0.3rem;'>
                % monetary relief paling rendah dari top 10 perusahaan
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_s3:
        if len(filtered_df['tahun'].unique()) >= 2:
            total_growth = ((len(filtered_df[filtered_df['tahun'] == yr_last]) -
                             len(filtered_df[filtered_df['tahun'] == yr_first])) /
                            len(filtered_df[filtered_df['tahun'] == yr_first]) * 100)
            growth_color = '#991b1b' if total_growth > 0 else '#166534'
            growth_bg = '#fef2f2' if total_growth > 0 else '#f0fdf4'
            growth_border = '#fca5a5' if total_growth > 0 else '#86efac'
            growth_icon = '📈' if total_growth > 0 else '📉'
            growth_label = 'Volume Keluhan NAIK' if total_growth > 0 else 'Volume Keluhan TURUN'
        else:
            total_growth = 0
            growth_color, growth_bg, growth_border = '#374151', '#f9fafb', '#d1d5db'
            growth_icon, growth_label = '📊', 'Pilih 2+ tahun'

        st.markdown(f"""
        <div style='background:{growth_bg}; border:1px solid {growth_border};
                    border-radius:8px; padding:1rem; height:100%;'>
            <div style='font-size:1.5rem; margin-bottom:0.3rem;'>{growth_icon}</div>
            <div style='font-weight:700; color:{growth_color}; margin-bottom:0.4rem;'>{growth_label}</div>
            <div style='font-size:1.3rem; font-weight:700; color:{growth_color};'>
                {total_growth:+.1f}%
            </div>
            <div style='color:#6b7280; font-size:0.85rem; margin-top:0.3rem;'>
                {int(yr_first) if len(filtered_df["tahun"].unique()) >= 2 else "-"} →
                {int(yr_last) if len(filtered_df["tahun"].unique()) >= 2 else "-"}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#eff6ff; border-left:4px solid #1f77b4;
                padding:1rem 1.2rem; border-radius:6px; margin-top:1rem;'>
        <b>💡 Catatan untuk Power BI:</b> Ketiga chart di halaman ini (Stacked Bar Horizontal,
        100% Stacked Bar, dan Stacked Bar Vertikal per tahun) langsung dapat direplikasi
        di Power BI menggunakan tipe visual <i>"Stacked Bar Chart"</i> dan
        <i>"100% Stacked Bar Chart"</i> tanpa kustomisasi tambahan.
        Gunakan kolom <code>product</code>, <code>consumer_disputed_is</code>,
        <code>company_response_to_consumer</code>, dan <code>tahun</code> sebagai field utama.
    </div>
    """, unsafe_allow_html=True)

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